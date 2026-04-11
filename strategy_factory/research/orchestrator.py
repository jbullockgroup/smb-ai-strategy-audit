"""
Research orchestrator for coordinating all research phases.

Manages the execution of research queries in the correct order,
handles progress tracking, and produces the final research output.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from ..config import PerplexityModel
from ..models import (
    CompanyInput,
    ResearchOutput,
    QueryResult,
    CompanyInfoTier,
)
from ..temporal import get_temporal_context, TemporalContext
from .perplexity_client import PerplexityClient
from .query_templates import QueryTemplates, QueryCategory, QueryTemplate
from .result_processor import ResultProcessor
from .tech_detector import detect_tech, TechDetectionResult


class ResearchOrchestrator:
    """
    Orchestrates the complete research pipeline for a company.

    Research phases:
    1. Initial Discovery - Basic company info to determine info tier
    2. Industry Analysis - Industry context and trends
    3. Technology Landscape - Tech stack and AI opportunities
    """

    # Query execution order by phase
    PHASE_QUERIES = {
        "company_discovery": [
            "company_presence",
            "social_reviews",
            "google_reviews",
            "sales_channels",
            "blog_content",
            "competitor_discovery",
        ],
        "industry_analysis": [
            "industry_overview",
            "industry_challenges",
            "industry_tools",
            "industry_operations",
        ],
        "ai_opportunity": [
            "industry_ai_examples",
            "industry_ai_tools",
            "industry_ai_trends",
        ],
    }
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        **kwargs,
    ):
        """
        Initialize the research orchestrator.

        Args:
            cache_dir: Directory for caching results.
            progress_callback: Callback for progress updates (phase, progress).
        """
        self.cache_dir = cache_dir
        self.progress_callback = progress_callback

        # Initialize components
        self.client = PerplexityClient(cache_dir=cache_dir)
        self.templates = QueryTemplates()
        self.result_processor = ResultProcessor()
        self.temporal = get_temporal_context()
        
        # Track state
        self.current_phase = ""
        self.results: Dict[str, QueryResult] = {}
        self.info_tier = CompanyInfoTier.PUBLIC_MEDIUM
        self.tech_detection: Optional[TechDetectionResult] = None
    
    def research(self, company_input: CompanyInput) -> ResearchOutput:
        """
        Execute the complete research pipeline.
        
        Args:
            company_input: Company input data.
        
        Returns:
            ResearchOutput with all research results.
        """
        company_name = company_input.name
        industry = company_input.industry
        if not industry:
            industry = self._detect_industry(company_input)
            company_input.industry = industry  # persist for resume
        context = company_input.context
        location = company_input.location or ""

        self._report_progress("Starting research", 0)

        # Phase 1: Company Discovery
        self._report_progress("company_discovery", 0.05)
        self._execute_phase(
            "company_discovery",
            company_name,
            industry,
            context,
            location,
        )

        # Detect info tier to adjust subsequent queries
        initial_results = [
            self.results[q]
            for q in self.PHASE_QUERIES["company_discovery"]
            if q in self.results
        ]
        self.info_tier = self.result_processor.detect_info_tier(initial_results)
        self._report_progress(f"Detected info tier: {self.info_tier.value}", 0.25)

        # Tech detection via DNS/HTTP (zero API cost)
        domain = self._resolve_domain(company_input, self.results)
        if domain:
            self._report_progress("tech_detection", 0.30)
            try:
                self.tech_detection = detect_tech(domain)
            except Exception as e:
                self._report_progress(f"Tech detection skipped: {e}", 0.30)

        # Phase 2: Industry Analysis
        self._report_progress("industry_analysis", 0.4)
        self._execute_phase("industry_analysis", company_name, industry, context, location)

        # Phase 3: AI Opportunity
        self._report_progress("ai_opportunity", 0.7)
        self._execute_phase("ai_opportunity", company_name, industry, context, location)

        # Build final output
        self._report_progress("Processing results", 0.9)
        output = self.result_processor.build_research_output(
            company_name=company_name,
            results=self.results,
            user_context=context,
        )
        
        # Update info tier in output
        output.information_tier = self.info_tier

        # Merge verified tech detection into tech landscape
        if self.tech_detection:
            verified = self.tech_detection.to_tech_list()
            if verified:
                # Prepend verified tech (deduplicated against inferred)
                existing_lower = {t.lower() for t in output.tech_landscape.company_tech_stack}
                new_tech = [t for t in verified if t.lower() not in existing_lower]
                output.tech_landscape.company_tech_stack = new_tech + output.tech_landscape.company_tech_stack
                output.tech_landscape.verified_tech_summary = self.tech_detection.to_summary()
        
        self._report_progress("Research complete", 1.0)
        
        return output

    @staticmethod
    def _resolve_domain(
        company_input: CompanyInput,
        results: Dict[str, QueryResult],
    ) -> Optional[str]:
        """
        Resolve the company's domain for tech detection.

        Checks (in order):
        1. Explicit website field on CompanyInput
        2. URLs found in company_presence search results
        3. Common domain patterns from the company name
        """
        # 1. Explicit website
        if company_input.website:
            return company_input.website

        # 2. Extract from search results — look for the company's own site
        presence = results.get("company_presence")
        if presence:
            company_lower = company_input.name.lower().replace(" ", "")
            for r in presence.results:
                try:
                    from urllib.parse import urlparse
                    host = urlparse(r.url).netloc.lower().removeprefix("www.")
                    # Skip social/review sites
                    skip = [
                        "facebook.com", "instagram.com", "linkedin.com",
                        "yelp.com", "google.com", "youtube.com", "tiktok.com",
                        "twitter.com", "x.com", "tripadvisor.com",
                    ]
                    if any(s in host for s in skip):
                        continue
                    # Heuristic: domain contains a significant part of the company name
                    name_parts = company_input.name.lower().split()
                    if any(part in host for part in name_parts if len(part) > 3):
                        return host
                except Exception:
                    continue

        # 3. Guess common patterns
        slug = company_input.name.lower().replace(" ", "")
        for tld in [".com", ".com.au", ".co", ".io", ".ai"]:
            candidate = slug + tld
            try:
                import subprocess
                out = subprocess.run(
                    ["dig", "+short", candidate],
                    capture_output=True, text=True, timeout=5,
                )
                if out.stdout.strip():
                    return candidate
            except Exception:
                break  # dig not available, stop guessing

        return None

    def _detect_industry(self, company_input: CompanyInput) -> str:
        """Detect company industry via a cheap Perplexity call.

        Returns a short industry string, or empty string on failure.
        """
        try:
            query = f"What industry does {company_input.name} operate in?"
            if company_input.context:
                query += f" Context: {company_input.context}."
            query += " Answer with just the industry name, one or two words max."

            result = self.client.search(
                query=query,
                max_results=3,
                model=PerplexityModel.SONAR,
            )

            if result.results:
                # Extract the industry from the first snippet
                snippet = result.results[0].snippet.strip()
                # Take first line, cap at reasonable length
                industry = snippet.split('\n')[0].strip().rstrip('.')
                if len(industry) > 50:
                    industry = ""
                return industry
            return ""
        except Exception:
            return ""

    def _execute_phase(
        self,
        phase: str,
        company_name: str,
        industry: str,
        context: str = "",
        location: str = "",
    ) -> None:
        """
        Execute all queries for a research phase.

        Args:
            phase: Phase name.
            company_name: Company name.
            industry: Industry.
            context: User-provided context.
            location: Company location for query disambiguation.
        """
        self.current_phase = phase
        queries = self.PHASE_QUERIES.get(phase, [])

        for i, query_name in enumerate(queries):
            template = self.templates.get_template(query_name)
            if not template:
                continue

            # Render query
            query = self.templates.render_query(
                template,
                company_name=company_name,
                industry=industry,
                context=context,
                location=location,
            )

            # Execute query
            result = self.client.search(
                query=query,
                max_results=10,
                search_recency_filter=template.recency_filter,
                model=PerplexityModel.SONAR,
            )
            
            # Store result
            self.results[query_name] = result
            
            # Update progress within phase
            phase_progress = (i + 1) / len(queries)
            self._report_progress(f"{phase}: {query_name}", None)
    
    def _report_progress(self, message: str, progress: Optional[float]) -> None:
        """Report progress to callback if set."""
        if self.progress_callback and progress is not None:
            self.progress_callback(message, progress)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for the research session."""
        return self.client.get_cost_summary()
    
    def save_research_cache(self, output_dir: Path) -> None:
        """
        Save research results to cache file.
        
        Args:
            output_dir: Directory to save cache.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_file = output_dir / "research_cache.json"
        
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "info_tier": self.info_tier.value,
            "results": {
                name: {
                    "query": r.query,
                    "model_used": r.model_used,
                    "result_count": r.result_count,
                    "cost_estimate": r.cost_estimate,
                    "results": [
                        {
                            "title": sr.title,
                            "url": sr.url,
                            "snippet": sr.snippet[:500],  # Truncate for storage
                            "date": sr.date,
                        }
                        for sr in r.results
                    ],
                }
                for name, r in self.results.items()
            },
        }
        
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
    
    def load_research_cache(self, cache_file: Path) -> bool:
        """
        Load research results from cache.
        
        Args:
            cache_file: Path to cache file.
        
        Returns:
            True if cache was loaded successfully.
        """
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            
            self.info_tier = CompanyInfoTier(data.get("info_tier", CompanyInfoTier.PUBLIC_MEDIUM.value))
            
            # Reconstruct results
            from ..models import SearchResult
            
            for name, result_data in data["results"].items():
                results = [
                    SearchResult(
                        title=r["title"],
                        url=r["url"],
                        snippet=r["snippet"],
                        date=r.get("date"),
                    )
                    for r in result_data["results"]
                ]
                
                self.results[name] = QueryResult(
                    query=result_data["query"],
                    model_used=result_data["model_used"],
                    results=results,
                    result_count=result_data["result_count"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    cost_estimate=result_data["cost_estimate"],
                )
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
            return False


def run_research(
    company_name: str,
    context: str = "",
    industry: str = "",
    cache_dir: Optional[Path] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> ResearchOutput:
    """
    Convenience function to run research for a company.

    Args:
        company_name: Company name.
        context: User-provided context.
        industry: Company industry.
        cache_dir: Cache directory.
        progress_callback: Progress callback.

    Returns:
        ResearchOutput with research results.
    """
    company_input = CompanyInput(
        name=company_name,
        context=context,
        industry=industry,
    )

    orchestrator = ResearchOrchestrator(
        cache_dir=cache_dir,
        progress_callback=progress_callback,
    )

    return orchestrator.research(company_input)
