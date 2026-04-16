"""
Pydantic data models for the AI Strategy Factory.

These models define the structure for:
- Company information and context
- Research results
- Synthesis outputs
- Progress tracking state
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Enums
# ============================================================================

class DeliverableStatus(str, Enum):
    """Status of a deliverable in the pipeline."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CompanyInfoTier(str, Enum):
    """Tier of publicly available company information."""
    PUBLIC_LARGE = "public_large"       # Lots of public info (Fortune 500, etc.)
    PUBLIC_MEDIUM = "public_medium"     # Some public info (mid-market)
    PRIVATE_LIMITED = "private_limited" # Limited public info (private companies)
    STARTUP_STEALTH = "startup_stealth" # Very little public info (stealth startups)


# ============================================================================
# Input Models
# ============================================================================

class CompanyInput(BaseModel):
    """User-provided company information."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Company name")
    context: str = Field(default="", description="Free-form context about the company")

    # Optional structured fields (extracted from context or provided directly)
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    location: Optional[str] = None
    website: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    logo_path: Optional[str] = None
    audience: Optional[str] = Field(default=None, description="Business context profile ID for regional/cultural tailoring")


# ============================================================================
# Research Models
# ============================================================================

class SearchResult(BaseModel):
    """Single search result from Perplexity."""
    title: str
    url: str
    snippet: str
    date: Optional[str] = None
    last_updated: Optional[str] = None


class QueryResult(BaseModel):
    """Result of a single Perplexity query."""
    query: str
    model_used: str
    results: List[SearchResult]
    result_count: int
    timestamp: datetime
    cost_estimate: float = 0.0
    error: Optional[str] = None


class CompanyProfile(BaseModel):
    """Researched company profile."""
    description: str = ""
    business_model: str = ""
    products_services: List[str] = Field(default_factory=list)
    target_market: str = ""
    employee_estimate: Optional[int] = None
    headquarters: str = ""
    founded_year: Optional[int] = None
    funding_status: str = ""
    leadership: List[Dict[str, str]] = Field(default_factory=list)
    recent_news: List[Dict[str, str]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class IndustryContext(BaseModel):
    """Industry analysis results."""
    primary_industry: str = ""
    naics_code: Optional[str] = None
    market_size: str = ""
    growth_rate: str = ""
    key_trends: List[str] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class CompetitorProfile(BaseModel):
    """Profile of a competitor."""
    name: str
    description: str = ""
    ai_initiatives: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    market_position: str = ""


class TechLandscape(BaseModel):
    """Technology and AI landscape analysis."""
    company_tech_stack: List[str] = Field(default_factory=list)
    verified_tech_summary: str = Field(default="", description="Tech verified via DNS/HTTP, not inferred")
    company_ai_initiatives: List[str] = Field(default_factory=list)
    industry_ai_adoption_rate: str = ""
    industry_ai_use_cases: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_ai_tools: List[Dict[str, Any]] = Field(default_factory=list)
    ai_maturity_estimate: str = ""
    sources: List[str] = Field(default_factory=list)


class RegulatoryContext(BaseModel):
    """Regulatory and compliance context."""
    industry_regulations: List[str] = Field(default_factory=list)
    ai_regulations: List[str] = Field(default_factory=list)
    data_privacy_requirements: List[str] = Field(default_factory=list)
    compliance_considerations: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class ValidatedUserContext(BaseModel):
    """User context after validation against research."""
    original_context: str
    extracted_info: Dict[str, Any] = Field(default_factory=dict)
    validated_claims: List[str] = Field(default_factory=list)
    unverified_claims: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)


class ResearchOutput(BaseModel):
    """Complete research output for a company."""
    model_config = ConfigDict(extra="ignore")

    company_name: str
    research_timestamp: datetime
    information_tier: CompanyInfoTier = CompanyInfoTier.PUBLIC_MEDIUM

    # Research sections
    profile: CompanyProfile = Field(default_factory=CompanyProfile)
    industry: IndustryContext = Field(default_factory=IndustryContext)
    competitors: List[CompetitorProfile] = Field(default_factory=list)
    tech_landscape: TechLandscape = Field(default_factory=TechLandscape)
    regulatory: RegulatoryContext = Field(default_factory=RegulatoryContext)
    user_context: ValidatedUserContext = Field(default_factory=lambda: ValidatedUserContext(original_context=""))

    # Metadata
    raw_queries: Dict[str, QueryResult] = Field(default_factory=dict)
    total_cost: float = 0.0
    confidence_scores: Dict[str, float] = Field(default_factory=dict)


# ============================================================================
# Synthesis Models
# ============================================================================

class DeliverableContent(BaseModel):
    """Generated content for a single deliverable."""
    deliverable_id: str
    name: str
    format: str  # markdown, docx, pdf
    content: str = ""  # Raw content or path to file
    file_path: Optional[str] = None
    generated_at: Optional[datetime] = None
    synthesis_cost: float = 0.0
    error: Optional[str] = None


class SynthesisOutput(BaseModel):
    """Complete synthesis output."""
    company_name: str
    synthesis_timestamp: datetime
    deliverables: Dict[str, DeliverableContent] = Field(default_factory=dict)
    total_cost: float = 0.0


# ============================================================================
# Progress Tracking Models
# ============================================================================

class DeliverableProgress(BaseModel):
    """Progress state for a single deliverable."""
    status: DeliverableStatus = DeliverableStatus.PENDING
    file_path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0


class PhaseProgress(BaseModel):
    """Progress state for a pipeline phase."""
    name: str
    status: DeliverableStatus = DeliverableStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[str] = None


class PipelineState(BaseModel):
    """
    Complete pipeline state for a company.
    Saved to state.json for resumability.
    """
    model_config = ConfigDict(extra="ignore")
    # Identification
    company_name: str
    company_slug: str  # URL-safe version of company name
    output_dir: str

    # Input data
    input_data: CompanyInput

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Phase tracking
    current_phase: str = "research"
    phases: Dict[str, PhaseProgress] = Field(default_factory=dict)

    # Deliverable tracking
    deliverables: Dict[str, DeliverableProgress] = Field(default_factory=dict)

    # Cached data
    research_output: Optional[ResearchOutput] = None
    research_cache_path: Optional[str] = None

    # Cost tracking
    total_research_cost: float = 0.0
    total_synthesis_cost: float = 0.0
    total_cost: float = 0.0

    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# API Response Models
# ============================================================================

class GenerationProgress(BaseModel):
    """Progress update for frontend display."""
    company_name: str
    current_phase: str
    phase_progress: float  # 0-100
    overall_progress: float  # 0-100
    current_deliverable: Optional[str] = None
    completed_deliverables: List[str] = Field(default_factory=list)
    pending_deliverables: List[str] = Field(default_factory=list)
    estimated_time_remaining: Optional[int] = None  # seconds
    errors: List[str] = Field(default_factory=list)


class GenerationResult(BaseModel):
    """Final result of generation for frontend."""
    company_name: str
    success: bool
    output_dir: str
    deliverables: List[Dict[str, str]] = Field(default_factory=list)  # [{name, path, format}]
    total_cost: float = 0.0
    generation_time: float = 0.0  # seconds
    errors: List[str] = Field(default_factory=list)
