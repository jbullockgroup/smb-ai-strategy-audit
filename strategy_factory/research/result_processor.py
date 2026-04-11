"""
Result processor for structuring Perplexity search results.

Transforms raw search results into structured data models
for use in the synthesis phase.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models import (
    QueryResult,
    SearchResult,
    CompanyProfile,
    IndustryContext,
    CompetitorProfile,
    TechLandscape,
    RegulatoryContext,
    ValidatedUserContext,
    ResearchOutput,
    CompanyInfoTier,
)
from .query_templates import QueryCategory


class ResultProcessor:
    """
    Processes raw Perplexity search results into structured models.
    
    Responsibilities:
    - Extract key information from search snippets
    - Structure data into Pydantic models
    - Detect company information availability tier
    - Validate and reconcile user-provided context
    """
    
    # Keywords for detecting information tier
    INFO_TIER_INDICATORS = {
        CompanyInfoTier.PUBLIC_LARGE: [
            "publicly traded", "nyse", "nasdaq", "fortune 500", "s&p 500",
        ],
        CompanyInfoTier.PUBLIC_MEDIUM: [
            "founded", "headquarters", "ceo", "products",
            "google reviews", "yelp", "facebook page", "instagram",
        ],
        CompanyInfoTier.PRIVATE_LIMITED: [
            "private company", "privately held",
        ],
        CompanyInfoTier.STARTUP_STEALTH: [
            "stealth", "early-stage", "pre-launch",
        ],
    }
    
    def __init__(self):
        """Initialize the result processor."""
        self.processed_count = 0
    
    def detect_info_tier(self, results: List[QueryResult]) -> CompanyInfoTier:
        """
        Detect the company's information availability tier.
        
        Args:
            results: Initial search results for the company.
        
        Returns:
            CompanyInfoTier indicating how much public info is available.
        """
        if not results:
            return CompanyInfoTier.PRIVATE_LIMITED
        
        # Combine all snippets for analysis
        all_text = " ".join(
            r.snippet.lower()
            for qr in results
            for r in qr.results
        )
        
        # Count results
        total_results = sum(qr.result_count for qr in results)
        
        # Check for tier indicators
        for tier, indicators in self.INFO_TIER_INDICATORS.items():
            for indicator in indicators:
                if indicator in all_text:
                    return tier
        
        # Fall back to result count heuristic (SMB-adjusted)
        if total_results >= 15:
            return CompanyInfoTier.PUBLIC_LARGE
        elif total_results >= 5:
            return CompanyInfoTier.PUBLIC_MEDIUM
        elif total_results >= 2:
            return CompanyInfoTier.PRIVATE_LIMITED
        else:
            return CompanyInfoTier.STARTUP_STEALTH
    
    def _extract_employee_count(self, results: List[QueryResult]) -> Optional[int]:
        """Extract employee count from search results."""
        all_text = " ".join(
            r.snippet.lower()
            for qr in results
            for r in qr.results
        )

        employee_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:employees|staff|team members)',
            r'(?:employs|has)\s*(?:about|approximately|over|more than)?\s*(\d{1,3}(?:,\d{3})*)',
            r'workforce of\s*(\d{1,3}(?:,\d{3})*)',
        ]

        for pattern in employee_patterns:
            match = re.search(pattern, all_text)
            if match:
                count_str = match.group(1).replace(",", "")
                try:
                    return int(count_str)
                except ValueError:
                    continue
        return None

    def extract_company_profile(
        self,
        company_name: str,
        results: Dict[str, QueryResult],
    ) -> CompanyProfile:
        """
        Extract company profile from search results.
        
        Args:
            company_name: Company name.
            results: Dict of query name to QueryResult.
        
        Returns:
            CompanyProfile with extracted information.
        """
        profile = CompanyProfile()
        sources = set()

        # Extract from company presence (backward compat: also check old query names)
        presence = results.get("company_presence") or results.get("company_overview")
        if presence and presence.results:
            profile.description = self._extract_first_paragraph(presence.results)
            profile.headquarters = self._extract_location(presence.results)
            profile.founded_year = self._extract_year(presence.results, "founded")
            profile.products_services = self._extract_products(profile.description) if profile.description else []
            sources.update(r.url for r in presence.results)

        # Also check company_details for backward compat
        details = results.get("company_details")
        if details and details.results:
            if not profile.employee_estimate:
                profile.employee_estimate = self._extract_employee_count([details])
            if not profile.headquarters:
                profile.headquarters = self._extract_location(details.results)
            if not profile.founded_year:
                profile.founded_year = self._extract_year(details.results, "founded")
            sources.update(r.url for r in details.results)

        # Extract from social/reviews — populate recent_news field for backward compat
        reviews = results.get("social_reviews") or results.get("recent_news")
        if reviews and reviews.results:
            profile.recent_news = self._extract_news(reviews.results)
            sources.update(r.url for r in reviews.results)

        profile.sources = list(sources)[:10]
        return profile
    
    def extract_industry_context(
        self,
        results: Dict[str, QueryResult],
    ) -> IndustryContext:
        """
        Extract industry context from search results.
        
        Args:
            results: Dict of query name to QueryResult.
        
        Returns:
            IndustryContext with industry analysis.
        """
        context = IndustryContext()
        sources = set()
        
        # Extract from industry overview
        overview = results.get("industry_overview")
        if overview and overview.results:
            context.primary_industry = self._extract_industry_name(overview.results)
            context.market_size = self._extract_market_size(overview.results)
            context.growth_rate = self._extract_growth_rate(overview.results)
            context.key_trends = self._extract_trends(overview.results)
            sources.update(r.url for r in overview.results)
        
        # Extract challenges
        challenges = results.get("industry_challenges")
        if challenges and challenges.results:
            context.challenges = self._extract_list_items(challenges.results, "challenge")
            sources.update(r.url for r in challenges.results)
        
        context.sources = list(sources)[:10]
        return context
    
    def extract_tech_landscape(
        self,
        results: Dict[str, QueryResult],
    ) -> TechLandscape:
        """
        Extract technology landscape from search results.
        
        Args:
            results: Dict of query name to QueryResult.
        
        Returns:
            TechLandscape with technology analysis.
        """
        landscape = TechLandscape()
        sources = set()

        # industry_tools -> populate tech stack (backward compat: also check old key)
        tools = results.get("industry_tools") or results.get("tech_stack")
        if tools and tools.results:
            landscape.company_tech_stack = self._extract_technologies(tools.results)
            sources.update(r.url for r in tools.results)

        # industry_ai_examples -> replaces ai_initiatives
        ai_examples = results.get("industry_ai_examples") or results.get("ai_initiatives")
        if ai_examples and ai_examples.results:
            landscape.company_ai_initiatives = self._extract_ai_initiatives(ai_examples.results)
            sources.update(r.url for r in ai_examples.results)

        # industry_ai_trends -> replaces industry_ai_adoption
        trends = results.get("industry_ai_trends") or results.get("industry_ai_adoption")
        if trends and trends.results:
            landscape.industry_ai_adoption_rate = self._extract_adoption_rate(trends.results)
            sources.update(r.url for r in trends.results)

        # industry_ai_tools -> same purpose, check both old and new key
        ai_tools = results.get("industry_ai_tools") or results.get("ai_tools")
        if ai_tools and ai_tools.results:
            landscape.recommended_ai_tools = self._extract_tools(ai_tools.results)
            sources.update(r.url for r in ai_tools.results)

        # ai_use_cases -> backward compat only (removed from new queries)
        use_cases = results.get("ai_use_cases")
        if use_cases and use_cases.results:
            landscape.industry_ai_use_cases = self._extract_use_cases(use_cases.results)
            sources.update(r.url for r in use_cases.results)

        landscape.sources = list(sources)[:10]
        return landscape
    
    def validate_user_context(
        self,
        user_context: str,
        research_results: Dict[str, QueryResult],
    ) -> ValidatedUserContext:
        """
        Validate user-provided context against research results.
        
        Args:
            user_context: User-provided context string.
            research_results: Results from research queries.
        
        Returns:
            ValidatedUserContext with validation results.
        """
        validated = ValidatedUserContext(original_context=user_context)
        
        if not user_context:
            return validated
        
        # Extract claims from user context
        # This is a simplified implementation - could use NLP for better extraction
        validated.extracted_info = {
            "raw_context": user_context,
        }
        
        # Compare with research results
        all_text = " ".join(
            r.snippet.lower()
            for qr in research_results.values()
            for r in qr.results
        ).lower()
        
        user_lower = user_context.lower()
        
        # Check for potential conflicts (simplified)
        if "employees" in user_lower:
            validated.unverified_claims.append("Employee count claim - verify against research")
        
        return validated
    
    def build_research_output(
        self,
        company_name: str,
        results: Dict[str, QueryResult],
        user_context: str = "",
    ) -> ResearchOutput:
        """
        Build complete research output from all results.
        
        Args:
            company_name: Company name.
            mode: Research mode used.
            results: All query results.
            user_context: User-provided context.
        
        Returns:
            Complete ResearchOutput model.
        """
        # Detect info tier from initial results
        initial_results = [
            r for name, r in results.items()
            if name in ["company_presence", "social_reviews", "sales_channels",
                        "company_overview", "company_details", "recent_news"]
        ]
        info_tier = self.detect_info_tier(initial_results)
        
        # Build all sections
        output = ResearchOutput(
            company_name=company_name,
            research_timestamp=datetime.now(),
            information_tier=info_tier,
            profile=self.extract_company_profile(company_name, results),
            industry=self.extract_industry_context(results),
            competitors=[],
            tech_landscape=self.extract_tech_landscape(results),
            regulatory=RegulatoryContext(),
            user_context=self.validate_user_context(user_context, results),
            raw_queries=results,
            total_cost=sum(r.cost_estimate for r in results.values()),
        )
        
        # Calculate confidence scores
        output.confidence_scores = self._calculate_confidence(results)
        
        self.processed_count += 1
        return output
    
    # Helper methods for extraction
    
    def _extract_first_paragraph(self, results: List[SearchResult]) -> str:
        """Extract first meaningful paragraph from results."""
        for r in results:
            if r.snippet and len(r.snippet) > 100:
                # Get first sentence or paragraph
                paragraphs = r.snippet.split("\n\n")
                if paragraphs:
                    return paragraphs[0][:500]
        return ""
    
    def _extract_location(self, results: List[SearchResult]) -> str:
        """Extract headquarters location."""
        patterns = [
            r'headquartered in ([^,.]+)',
            r'headquarters in ([^,.]+)',
            r'based in ([^,.]+)',
            r'located in ([^,.]+)',
        ]
        
        for r in results:
            text = r.snippet.lower()
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip().title()
        return ""
    
    def _extract_year(self, results: List[SearchResult], keyword: str) -> Optional[int]:
        """Extract a year associated with a keyword."""
        pattern = rf'{keyword}\s*(?:in)?\s*(\d{{4}})'
        
        for r in results:
            match = re.search(pattern, r.snippet.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_leadership(self, results: List[SearchResult]) -> List[Dict[str, str]]:
        """Extract leadership information."""
        leaders = []
        titles = ["ceo", "cto", "cfo", "coo", "founder", "president"]
        
        for r in results:
            text = r.snippet
            for title in titles:
                pattern = rf'({title})[,:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    leaders.append({
                        "title": match[0].upper(),
                        "name": match[1],
                    })
        
        return leaders[:5]  # Limit
    
    def _extract_funding(self, results: List[SearchResult]) -> str:
        """Extract funding status."""
        for r in results:
            text = r.snippet.lower()
            if "raised" in text or "funding" in text or "series" in text:
                # Get the sentence containing funding info
                sentences = r.snippet.split(".")
                for s in sentences:
                    if any(word in s.lower() for word in ["raised", "funding", "series", "valuation"]):
                        return s.strip()[:200]
        return ""
    
    def _extract_news(self, results: List[SearchResult]) -> List[Dict[str, str]]:
        """Extract recent news items."""
        news = []
        for r in results[:5]:
            news.append({
                "title": r.title,
                "url": r.url,
                "date": r.date or "",
            })
        return news
    
    def _extract_products(self, description: str) -> List[str]:
        """Extract products/services from description."""
        # Simple extraction - look for common patterns
        products = []
        patterns = [
            r'offers? ([^,.]+)',
            r'provides? ([^,.]+)',
            r'specializ(?:es|ing) in ([^,.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description.lower())
            products.extend(matches)
        
        return list(set(products))[:5]
    
    def _extract_industry_name(self, results: List[SearchResult]) -> str:
        """Extract primary industry name."""
        for r in results:
            if r.title:
                # Often the industry is in the title
                return r.title.split("-")[0].strip()[:50]
        return ""
    
    def _extract_market_size(self, results: List[SearchResult]) -> str:
        """Extract market size information."""
        patterns = [
            r'\$[\d.]+\s*(?:billion|million|trillion)',
            r'market (?:size|value)[^.]*\$[\d.]+',
        ]
        
        for r in results:
            for pattern in patterns:
                match = re.search(pattern, r.snippet.lower())
                if match:
                    return match.group(0)
        return ""
    
    def _extract_growth_rate(self, results: List[SearchResult]) -> str:
        """Extract growth rate information."""
        patterns = [
            r'(\d+(?:\.\d+)?%)\s*(?:growth|cagr|increase)',
            r'growing at (\d+(?:\.\d+)?%)',
        ]
        
        for r in results:
            for pattern in patterns:
                match = re.search(pattern, r.snippet.lower())
                if match:
                    return match.group(1)
        return ""
    
    def _extract_trends(self, results: List[SearchResult]) -> List[str]:
        """Extract key trends."""
        trends = []
        trend_keywords = ["trend", "emerging", "growing", "rising", "shift toward"]
        
        for r in results:
            sentences = r.snippet.split(".")
            for s in sentences:
                if any(kw in s.lower() for kw in trend_keywords):
                    trends.append(s.strip()[:150])
        
        return list(set(trends))[:5]
    
    def _extract_list_items(self, results: List[SearchResult], context: str) -> List[str]:
        """Extract list items from results."""
        items = []
        for r in results:
            sentences = r.snippet.split(".")
            for s in sentences:
                if len(s) > 20 and len(s) < 200:
                    items.append(s.strip())
        return list(set(items))[:5]
    
    def _extract_technologies(self, results: List[SearchResult]) -> List[str]:
        """Extract technology names (SMB-focused)."""
        tech_keywords = [
            # Accounting/Finance
            "quickbooks", "freshbooks", "xero", "wave accounting", "square",
            # Website/E-commerce
            "shopify", "squarespace", "wix", "wordpress", "woocommerce",
            "bigcartal", "etsy",
            # Productivity
            "google workspace", "g suite", "microsoft 365", "notion",
            "trello", "asana", "monday.com",
            # Marketing
            "mailchimp", "constant contact", "canva", "hootsuite",
            "buffer", "later",
            # Scheduling
            "calendly", "acuity", "bookedin", "square appointments",
            # POS/Retail
            "square", "toast", "lightspeed", "shopkeep", "vend",
            # CRM
            "hubspot", "salesforce", "zoho", "keap", "insightly",
            # Voice/Phone tools
            "twilio", "vapi",
            "retell", "trillet", "google voice",
        ]
        found = []
        for r in results:
            text = r.snippet.lower()
            for tech in tech_keywords:
                if tech in text and tech.title() not in found:
                    found.append(tech.title())
        return found[:10]
    
    def _extract_ai_initiatives(self, results: List[SearchResult]) -> List[str]:
        """Extract AI initiative descriptions."""
        initiatives = []
        for r in results:
            sentences = r.snippet.split(".")
            for s in sentences:
                if any(kw in s.lower() for kw in ["ai", "machine learning", "automation"]):
                    initiatives.append(s.strip()[:150])
        return list(set(initiatives))[:5]
    
    def _extract_adoption_rate(self, results: List[SearchResult]) -> str:
        """Extract AI adoption rate."""
        patterns = [
            r'(\d+(?:\.\d+)?%)\s*(?:adoption|using ai|implemented)',
            r'adoption rate of (\d+(?:\.\d+)?%)',
        ]
        
        for r in results:
            for pattern in patterns:
                match = re.search(pattern, r.snippet.lower())
                if match:
                    return match.group(1)
        return ""
    
    def _extract_use_cases(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Extract AI use cases."""
        use_cases = []
        for r in results[:5]:
            use_cases.append({
                "description": r.snippet[:200],
                "source": r.url,
            })
        return use_cases
    
    def _extract_tools(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Extract recommended AI tools."""
        tools = []
        tool_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is a|provides|offers)',
        ]
        
        for r in results:
            for pattern in tool_patterns:
                matches = re.findall(pattern, r.snippet)
                for match in matches:
                    tools.append({
                        "name": match,
                        "description": "",
                        "source": r.url,
                    })
        
        return tools[:5]
    
    def _calculate_confidence(self, results: Dict[str, QueryResult]) -> Dict[str, float]:
        """Calculate confidence scores for each research section."""
        confidence = {}

        sections = {
            "profile": ["company_presence", "social_reviews", "google_reviews"],
            "digital_presence": ["social_reviews", "google_reviews", "blog_content"],
            "industry": ["industry_overview", "industry_challenges", "industry_tools"],
            "technology": ["industry_ai_examples", "industry_ai_tools"],
        }

        for section, queries in sections.items():
            total_results = 0
            for q in queries:
                if q in results:
                    total_results += results[q].result_count

            # SMB-adjusted thresholds (lowered from enterprise levels)
            if total_results >= 8:
                confidence[section] = 0.9
            elif total_results >= 4:
                confidence[section] = 0.7
            elif total_results >= 1:
                confidence[section] = 0.5
            else:
                confidence[section] = 0.3

        return confidence
