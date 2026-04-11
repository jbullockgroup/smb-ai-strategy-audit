"""
Perplexity API client wrapper with retry logic and rate limiting.

Provides a robust interface for making Perplexity Search API calls
with automatic retries, exponential backoff, and cost tracking.
"""

import os
import time
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

from perplexity import Perplexity

from ..config import (
    RETRY_CONFIG,
    PERPLEXITY_COSTS,
    PerplexityModel,
    QUALITY_DOMAINS,
)
from ..models import SearchResult, QueryResult


@dataclass
class CacheEntry:
    """Represents a cached query result."""
    query_hash: str
    query: str
    result: QueryResult
    timestamp: datetime
    ttl_hours: int = 24


class PerplexityClient:
    """
    Wrapper for Perplexity Search API with retry logic and caching.
    
    Features:
    - Automatic retry with exponential backoff
    - Query result caching
    - Cost estimation and tracking
    - Rate limiting
    - Multi-query support
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True,
    ):
        """
        Initialize the Perplexity client.
        
        Args:
            api_key: Perplexity API key. If not provided, uses PERPLEXITY_API_KEY env var.
            cache_dir: Directory for caching query results.
            enable_cache: Whether to enable result caching.
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        self.client = Perplexity(api_key=self.api_key)
        self.enable_cache = enable_cache
        self.cache_dir = cache_dir
        self.cache: Dict[str, CacheEntry] = {}
        
        # Cost tracking
        self.total_cost = 0.0
        self.query_count = 0
        
        # Rate limiting
        self.last_request_time = 0.0
        self.min_request_interval = 1.0  # seconds between requests
        
        # Load cache from disk if available
        if self.cache_dir and self.enable_cache:
            self._load_cache()
    
    def _get_cache_key(self, query: str, **params) -> str:
        """Generate a cache key from query and parameters."""
        cache_data = {"query": query, **params}
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_dir:
            return
        
        cache_file = self.cache_dir / "research_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    for key, entry in data.items():
                        # Reconstruct QueryResult from dict
                        result_dict = entry["result"]
                        result_dict["timestamp"] = datetime.fromisoformat(result_dict["timestamp"])
                        results = [SearchResult(**r) for r in result_dict["results"]]
                        result_dict["results"] = results
                        
                        self.cache[key] = CacheEntry(
                            query_hash=key,
                            query=entry["query"],
                            result=QueryResult(**result_dict),
                            timestamp=datetime.fromisoformat(entry["timestamp"]),
                            ttl_hours=entry.get("ttl_hours", 24),
                        )
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        if not self.cache_dir:
            return
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / "research_cache.json"
        
        try:
            data = {}
            for key, entry in self.cache.items():
                result_dict = entry.result.model_dump()
                result_dict["timestamp"] = result_dict["timestamp"].isoformat()
                result_dict["results"] = [r.model_dump() for r in entry.result.results]
                
                data[key] = {
                    "query": entry.query,
                    "result": result_dict,
                    "timestamp": entry.timestamp.isoformat(),
                    "ttl_hours": entry.ttl_hours,
                }
            
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def _is_cache_valid(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is still valid."""
        age_hours = (datetime.now() - entry.timestamp).total_seconds() / 3600
        return age_hours < entry.ttl_hours
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _estimate_cost(
        self,
        model: PerplexityModel,
        query_text: str = "",
        response_text: str = "",
    ) -> float:
        """Estimate cost using calibrated per-query rate.

        The Perplexity Search API returns no token counts or cost data,
        so text-based estimation was unreliable. Fixed per-query rates
        calibrated from actual billing data are more accurate.
        """
        from ..config import PERPLEXITY_QUERY_COSTS
        return PERPLEXITY_QUERY_COSTS.get(model, 0.0045)
    
    def search(
        self,
        query: Union[str, List[str]],
        max_results: int = 10,
        max_tokens_per_page: int = 1024,
        country: Optional[str] = None,
        search_recency_filter: Optional[str] = None,
        search_after_date: Optional[str] = None,
        search_before_date: Optional[str] = None,
        search_domain_filter: Optional[List[str]] = None,
        use_quality_domains: bool = False,
        model: PerplexityModel = PerplexityModel.SONAR,
        cache_ttl_hours: int = 24,
    ) -> QueryResult:
        """
        Execute a Perplexity search query with retry logic.
        
        Args:
            query: Search query string or list of queries (max 5).
            max_results: Maximum number of results (1-20).
            max_tokens_per_page: Content extraction depth per page.
            country: ISO country code for regional results.
            search_recency_filter: Filter by recency (day, week, month, year).
            search_after_date: Only results after this date (MM/DD/YYYY).
            search_before_date: Only results before this date (MM/DD/YYYY).
            search_domain_filter: Allowlist or denylist of domains.
            use_quality_domains: If True, filter to quality domains.
            model: Perplexity model to use (for cost tracking).
            cache_ttl_hours: How long to cache results.
        
        Returns:
            QueryResult with search results and metadata.
        """
        # Build cache key
        cache_params = {
            "max_results": max_results,
            "country": country,
            "recency": search_recency_filter,
            "after": search_after_date,
            "before": search_before_date,
            "domains": search_domain_filter,
            "model": model.value,
        }
        query_str = query if isinstance(query, str) else "|".join(query)
        cache_key = self._get_cache_key(query_str, **cache_params)
        
        # Check cache
        if self.enable_cache and cache_key in self.cache:
            entry = self.cache[cache_key]
            if self._is_cache_valid(entry):
                return entry.result
        
        # Build request parameters
        params: Dict[str, Any] = {
            "query": query,
            "max_results": max_results,
            "max_tokens_per_page": max_tokens_per_page,
        }
        
        if country:
            params["country"] = country
        if search_recency_filter:
            params["search_recency_filter"] = search_recency_filter
        if search_after_date:
            params["search_after_date"] = search_after_date
        if search_before_date:
            params["search_before_date"] = search_before_date
        
        # Handle domain filtering
        if use_quality_domains and not search_domain_filter:
            params["search_domain_filter"] = QUALITY_DOMAINS[:20]
        elif search_domain_filter:
            params["search_domain_filter"] = search_domain_filter[:20]
        
        # Execute with retry
        result = self._execute_with_retry(params, model)
        
        # Cache result
        if self.enable_cache:
            self.cache[cache_key] = CacheEntry(
                query_hash=cache_key,
                query=query_str,
                result=result,
                timestamp=datetime.now(),
                ttl_hours=cache_ttl_hours,
            )
            self._save_cache()
        
        return result
    
    def _execute_with_retry(
        self,
        params: Dict[str, Any],
        model: PerplexityModel,
    ) -> QueryResult:
        """Execute a search with retry logic."""
        max_retries = RETRY_CONFIG["max_retries"]
        delay = RETRY_CONFIG["initial_delay"]
        max_delay = RETRY_CONFIG["max_delay"]
        backoff = RETRY_CONFIG["backoff_multiplier"]
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                
                response = self.client.search.create(**params)
                
                # Parse results
                results = []
                for r in response.results:
                    results.append(SearchResult(
                        title=r.title,
                        url=r.url,
                        snippet=r.snippet,
                        date=getattr(r, 'date', None),
                        last_updated=getattr(r, 'last_updated', None),
                    ))
                
                # Estimate cost from actual text
                response_text = " ".join(r.snippet for r in results if r.snippet)
                query_str = params["query"]
                if isinstance(query_str, list):
                    query_str = " | ".join(query_str)
                cost = self._estimate_cost(model, query_str, response_text)
                self.total_cost += cost
                self.query_count += 1

                return QueryResult(
                    query=query_str,
                    model_used=model.value,
                    results=results,
                    result_count=len(results),
                    timestamp=datetime.now(),
                    cost_estimate=cost,
                )
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} after error: {e}")
                    time.sleep(delay)
                    delay = min(delay * backoff, max_delay)
        
        # All retries failed
        query_str = params["query"]
        if isinstance(query_str, list):
            query_str = " | ".join(query_str)
            
        return QueryResult(
            query=query_str,
            model_used=model.value,
            results=[],
            result_count=0,
            timestamp=datetime.now(),
            cost_estimate=0.0,
            error=str(last_error),
        )
    
    def search_multi(
        self,
        queries: List[str],
        **kwargs,
    ) -> List[QueryResult]:
        """
        Execute multiple independent searches.
        
        Args:
            queries: List of search queries.
            **kwargs: Additional parameters passed to search().
        
        Returns:
            List of QueryResult objects.
        """
        results = []
        for query in queries:
            result = self.search(query, **kwargs)
            results.append(result)
        return results
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get a summary of API usage and costs."""
        return {
            "total_cost": round(self.total_cost, 4),
            "query_count": self.query_count,
            "avg_cost_per_query": round(self.total_cost / max(1, self.query_count), 4),
            "cache_hits": len([e for e in self.cache.values() if self._is_cache_valid(e)]),
        }
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        self.cache = {}
        if self.cache_dir:
            cache_file = self.cache_dir / "research_cache.json"
            if cache_file.exists():
                cache_file.unlink()
