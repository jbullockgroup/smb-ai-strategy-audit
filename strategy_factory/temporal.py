"""
Temporal utilities for date-aware prompts and queries.

All research and synthesis should be temporally aware to ensure
recommendations are current and forward-looking.
"""

from datetime import datetime, timedelta
from typing import Dict


class TemporalContext:
    """
    Provides consistent temporal context injection across all prompts and queries.

    Usage:
        temporal = TemporalContext()
        prompt = temporal.inject("Find AI trends for {current_year}")
        # Result: "Find AI trends for 2025"
    """

    def __init__(self, reference_date: datetime = None):
        """
        Initialize with a reference date (defaults to now).

        Args:
            reference_date: Optional datetime to use as reference.
                           Useful for testing or generating reports for specific dates.
        """
        self.now = reference_date or datetime.now()

    def get_context(self) -> Dict[str, str]:
        """
        Get all temporal context variables as a dictionary.

        Returns:
            Dict with all temporal placeholders and their values.
        """
        return {
            # Core date values
            "current_date": self.now.strftime("%Y-%m-%d"),
            "current_date_full": self.now.strftime("%B %d, %Y"),
            "current_date_formatted": self.now.strftime("%m/%d/%Y"),

            # Year and month
            "current_year": str(self.now.year),
            "current_month": self.now.strftime("%B"),
            "current_month_year": self.now.strftime("%B %Y"),

            # Quarter
            "current_quarter": f"Q{(self.now.month - 1) // 3 + 1}",
            "current_quarter_year": f"Q{(self.now.month - 1) // 3 + 1} {self.now.year}",

            # Fiscal year (assuming July start)
            "fiscal_year": f"FY{self.now.year}" if self.now.month >= 7 else f"FY{self.now.year - 1}",

            # Relative periods
            "last_month": (self.now - timedelta(days=30)).strftime("%B %Y"),
            "last_quarter": self._get_last_quarter(),
            "last_year": str(self.now.year - 1),

            # Date ranges for Perplexity
            "six_months_ago": (self.now - timedelta(days=180)).strftime("%m/%d/%Y"),
            "one_year_ago": (self.now - timedelta(days=365)).strftime("%m/%d/%Y"),
            "three_months_ago": (self.now - timedelta(days=90)).strftime("%m/%d/%Y"),

            # Natural language periods
            "recent_period": f"the past 6 months (since {(self.now - timedelta(days=180)).strftime('%B %Y')})",
            "recent_quarter": f"the past 3 months (since {(self.now - timedelta(days=90)).strftime('%B %Y')})",
        }

    def _get_last_quarter(self) -> str:
        """Calculate the previous quarter string."""
        current_quarter = (self.now.month - 1) // 3 + 1
        if current_quarter == 1:
            return f"Q4 {self.now.year - 1}"
        else:
            return f"Q{current_quarter - 1} {self.now.year}"

    def inject(self, template: str, **extra_vars) -> str:
        """
        Inject temporal context into a template string.

        Args:
            template: String with placeholders like {current_year}
            **extra_vars: Additional variables to inject

        Returns:
            String with all placeholders replaced

        Example:
            temporal.inject("AI trends in {current_year} for {company}")
        """
        context = self.get_context()
        context.update(extra_vars)

        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result

    def get_recency_filter(self, query_type: str) -> str:
        """
        Get appropriate Perplexity recency filter for query type.

        Args:
            query_type: Type of query (news, company_profile, industry_trends, etc.)

        Returns:
            Recency filter value (day, week, month, year)
        """
        recency_map = {
            "news": "week",
            "announcements": "week",
            "company_profile": "year",
            "leadership": "year",
            "funding": "year",
            "industry_trends": "month",
            "ai_landscape": "month",
            "ai_initiatives": "month",
            "competitor": "year",
            "regulations": "year",
            "market_size": "year",
            "tech_stack": "year",
        }
        return recency_map.get(query_type, "year")

    def get_date_filter(self, lookback_days: int = 365) -> Dict[str, str]:
        """
        Get date filter parameters for Perplexity API.

        Args:
            lookback_days: Number of days to look back

        Returns:
            Dict with search_after_date and search_before_date
        """
        after_date = (self.now - timedelta(days=lookback_days)).strftime("%m/%d/%Y")
        before_date = self.now.strftime("%m/%d/%Y")

        return {
            "search_after_date": after_date,
            "search_before_date": before_date
        }

    def format_for_prompt(self) -> str:
        """
        Generate a formatted temporal context block for prompts.

        Returns:
            Multi-line string describing the current temporal context.
        """
        return f"""## Current Date Context
Today's date is {self.now.strftime('%B %d, %Y')} ({self.now.strftime('%Y-%m-%d')}).
Current quarter: {self.get_context()['current_quarter_year']}

All recommendations should be:
- Current and forward-looking from this date
- Reference recent developments from {self.now.year}
- Consider trends and changes from {self.get_context()['recent_period']}
- Avoid referencing outdated tools, pricing, or market conditions"""


def get_temporal_context() -> TemporalContext:
    """
    Factory function to get a TemporalContext instance.

    Returns:
        TemporalContext initialized with current datetime.
    """
    return TemporalContext()
