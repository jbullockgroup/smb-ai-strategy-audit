"""
Query templates for Perplexity research.

Provides structured query templates for different research categories,
with temporal awareness and company context injection.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from ..temporal import TemporalContext, get_temporal_context


class QueryCategory(str, Enum):
    """Categories of research queries."""
    COMPANY_DISCOVERY = "company_discovery"    # Phase 1: Find the business online
    INDUSTRY = "industry"                      # Phase 2: Industry intelligence
    AI_OPPORTUNITY = "ai_opportunity"          # Phase 3: AI opportunity mapping


@dataclass
class QueryTemplate:
    """Represents a query template with metadata."""
    name: str
    category: QueryCategory
    template: str
    recency_filter: str  # day, week, month, year
    priority: int  # 1 = highest priority
    description: str


class QueryTemplates:
    """
    Repository of query templates for company research.
    
    Templates use placeholders:
    - {company_name}: Company name
    - {industry}: Company's industry (if known)
    - {context}: User-provided context
    - Temporal placeholders from TemporalContext
    """
    
    # Phase 1 — Company Discovery
    COMPANY_PRESENCE = QueryTemplate(
        name="company_presence",
        category=QueryCategory.COMPANY_DISCOVERY,
        template='"{company_name}" {location} services Google business profile LinkedIn Facebook Instagram TikTok YouTube social media posting frequency engagement advertising {industry} {context}',
        recency_filter="year",
        priority=1,

        description="Find web presence, services, location, social media activity, advertising, Google listing",
    )

    SOCIAL_REVIEWS = QueryTemplate(
        name="social_reviews",
        category=QueryCategory.COMPANY_DISCOVERY,
        template='"{company_name}" {location} customer reviews ratings feedback complaints praise themes Google Yelp Facebook {context}',
        recency_filter="year",
        priority=2,

        description="Find social media activity, customer reviews, reputation",
    )

    GOOGLE_REVIEWS = QueryTemplate(
        name="google_reviews",
        category=QueryCategory.COMPANY_DISCOVERY,
        template='"{company_name}" {location} Google reviews "Google Business" rating stars customer feedback experience {context}',
        recency_filter="year",
        priority=2,
        description="Find Google Business review details including ratings, themes, and customer sentiment",
    )

    SALES_CHANNELS = QueryTemplate(
        name="sales_channels",
        category=QueryCategory.COMPANY_DISCOVERY,
        template='"{company_name}" Etsy Shopify online store wholesale farmers market e-commerce {industry}',
        recency_filter="year",
        priority=2,

        description="Find e-commerce presence, platforms, wholesale channels",
    )

    BLOG_CONTENT = QueryTemplate(
        name="blog_content",
        category=QueryCategory.COMPANY_DISCOVERY,
        template='"{company_name}" {location} blog articles posts newsletter content topics expertise {industry} {context}',
        recency_filter="year",
        priority=3,
        description="Find blog posts, articles, and content themes published by the company",
    )

    COMPETITOR_DISCOVERY = QueryTemplate(
        name="competitor_discovery",
        category=QueryCategory.COMPANY_DISCOVERY,
        template='"{company_name}" {industry} {context} competitors similar companies alternatives market share {current_year}',
        recency_filter="year",
        priority=2,

        description="Discover specific competitors and alternatives in the market",
    )

    # Phase 2 — Industry Intelligence
    INDUSTRY_OVERVIEW = QueryTemplate(
        name="industry_overview",
        category=QueryCategory.INDUSTRY,
        template='{industry} industry market size growth trends {current_year}',
        recency_filter="year",
        priority=1,

        description="Industry overview and market analysis",
    )

    INDUSTRY_CHALLENGES = QueryTemplate(
        name="industry_challenges",
        category=QueryCategory.INDUSTRY,
        template='{industry} small business challenges pain points operations problems {current_year} {context}',
        recency_filter="year",
        priority=2,

        description="Industry challenges specific to small businesses",
    )

    INDUSTRY_TOOLS = QueryTemplate(
        name="industry_tools",
        category=QueryCategory.INDUSTRY,
        template='{industry} small business software tools apps commonly used {current_year}',
        recency_filter="year",
        priority=2,

        description="Common software and tools used in this industry",
    )

    INDUSTRY_OPERATIONS = QueryTemplate(
        name="industry_operations",
        category=QueryCategory.INDUSTRY,
        template='{industry} small business daily operations workflows customer interactions marketing {current_year}',
        recency_filter="year",
        priority=2,

        description="Daily workflows, customer interaction patterns, marketing channels",
    )

    # Phase 3 — AI Opportunity
    INDUSTRY_AI_EXAMPLES = QueryTemplate(
        name="industry_ai_examples",
        category=QueryCategory.AI_OPPORTUNITY,
        template='{industry} AI automation examples small business case studies real implementations {current_year} {context}',
        recency_filter="month",
        priority=1,

        description="Real AI automation examples for this industry",
    )

    INDUSTRY_AI_TOOLS = QueryTemplate(
        name="industry_ai_tools",
        category=QueryCategory.AI_OPPORTUNITY,
        template='{industry} AI tools small business affordable recommended {current_year}',
        recency_filter="month",
        priority=2,

        description="Recommended AI tools for the industry",
    )

    INDUSTRY_AI_TRENDS = QueryTemplate(
        name="industry_ai_trends",
        category=QueryCategory.AI_OPPORTUNITY,
        template='{industry} AI adoption trends small business owners using {current_month_year} {context}',
        recency_filter="month",
        priority=1,

        description="SMB AI adoption trends in this industry",
    )

    # All templates as a dictionary
    ALL_TEMPLATES: Dict[str, QueryTemplate] = {
        "company_presence": COMPANY_PRESENCE,
        "social_reviews": SOCIAL_REVIEWS,
        "google_reviews": GOOGLE_REVIEWS,
        "sales_channels": SALES_CHANNELS,
        "blog_content": BLOG_CONTENT,
        "competitor_discovery": COMPETITOR_DISCOVERY,
        "industry_overview": INDUSTRY_OVERVIEW,
        "industry_challenges": INDUSTRY_CHALLENGES,
        "industry_tools": INDUSTRY_TOOLS,
        "industry_operations": INDUSTRY_OPERATIONS,
        "industry_ai_examples": INDUSTRY_AI_EXAMPLES,
        "industry_ai_tools": INDUSTRY_AI_TOOLS,
        "industry_ai_trends": INDUSTRY_AI_TRENDS,
    }
    
    def __init__(self, temporal: Optional[TemporalContext] = None):
        """
        Initialize query templates with temporal context.
        
        Args:
            temporal: TemporalContext for date injection. Uses current date if not provided.
        """
        self.temporal = temporal or get_temporal_context()
    
    def get_template(self, name: str) -> Optional[QueryTemplate]:
        """Get a query template by name."""
        return self.ALL_TEMPLATES.get(name)
    
    def get_templates_by_category(self, category: QueryCategory) -> List[QueryTemplate]:
        """Get all templates for a category."""
        return [t for t in self.ALL_TEMPLATES.values() if t.category == category]
    
    def render_query(
        self,
        template: QueryTemplate,
        company_name: str,
        industry: str = "",
        context: str = "",
        **extra_vars,
    ) -> str:
        """
        Render a query template with all variables.
        
        Args:
            template: QueryTemplate to render.
            company_name: Company name.
            industry: Industry (optional).
            context: User context (optional).
            **extra_vars: Additional variables.
        
        Returns:
            Rendered query string.
        """
        variables = {
            "company_name": company_name,
            "industry": industry,
            "context": context,
            **extra_vars,
        }
        
        return self.temporal.inject(template.template, **variables)
    
    def render_all_queries(
        self,
        company_name: str,
        industry: str = "",
        context: str = "",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Render all queries for a company.

        Args:
            company_name: Company name.
            industry: Industry.
            context: User context.

        Returns:
            Dict mapping template name to rendered query and metadata.
        """
        templates = list(self.ALL_TEMPLATES.values())
        
        rendered = {}
        for template in templates:
            query = self.render_query(template, company_name, industry, context)
            rendered[template.name] = {
                "query": query,
                "category": template.category.value,
                "recency_filter": template.recency_filter,
                "priority": template.priority,
            }
        
        return rendered
    
    def get_queries_by_priority(
        self,
        company_name: str,
        industry: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Get queries sorted by priority.

        Args:
            company_name: Company name.
            industry: Industry.

        Returns:
            List of query dicts sorted by priority.
        """
        rendered = self.render_all_queries(company_name, industry)
        
        queries = [
            {"name": name, **data}
            for name, data in rendered.items()
        ]
        
        return sorted(queries, key=lambda x: x["priority"])
