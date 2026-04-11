"""
Configuration constants and settings for the AI Strategy Factory.
"""

from pathlib import Path
from enum import Enum
from typing import Dict

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
TLDR_GUIDES_DIR = PROJECT_ROOT / "Consulting Guides TLDR"
PROGRESS_DIR = PROJECT_ROOT / "progress"

# API Configuration
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_REQUEST_DELAY = 5  # seconds between requests

# Perplexity models and their use cases
class PerplexityModel(str, Enum):
    SONAR = "sonar"
    SONAR_PRO = "sonar-pro"
    SONAR_REASONING = "sonar-reasoning"
    SONAR_REASONING_PRO = "sonar-reasoning-pro"
    SONAR_DEEP_RESEARCH = "sonar-deep-research"

# Estimated costs per 1K tokens (input/output)
PERPLEXITY_COSTS = {
    PerplexityModel.SONAR: (0.001, 0.001),
    PerplexityModel.SONAR_PRO: (0.003, 0.015),
    PerplexityModel.SONAR_REASONING: (0.001, 0.005),
    PerplexityModel.SONAR_REASONING_PRO: (0.002, 0.008),
    PerplexityModel.SONAR_DEEP_RESEARCH: (0.002, 0.008),
}

# Calibrated per-query cost estimates (based on actual billing data, April 2026)
# Sonar: avg of $0.005 (Angela Kim) and $0.004 (Healing Roots) across 11 queries each
# Other models: proportionally scaled from token pricing ratios, erring slightly high
PERPLEXITY_QUERY_COSTS = {
    PerplexityModel.SONAR: 0.0045,
    PerplexityModel.SONAR_PRO: 0.025,
    PerplexityModel.SONAR_REASONING: 0.008,
    PerplexityModel.SONAR_REASONING_PRO: 0.015,
    PerplexityModel.SONAR_DEEP_RESEARCH: 0.015,
}

# Deliverable definitions — key order determines sidebar display order
DELIVERABLES = {
    "08_executive_summary": {
        "name": "Executive Summary",
        "format": "markdown",
        "dependencies": [
            "01_tools_audit", "02_daily_pain_points", "03_action_plan",
            "04_simple_roadmap", "05_readiness_assessment", "06_roi_snapshot",
            "07_closing"
        ],
        "tldr_guides": []
    },
    "01_tools_audit": {
        "name": "Where You Stand Today",
        "format": "markdown",
        "dependencies": [],
        "tldr_guides": ["smb-ai-playbook.md"]
    },
    "02_daily_pain_points": {
        "name": "Where You're Losing Money",
        "format": "markdown",
        "dependencies": [],
        "tldr_guides": ["smb-ai-value-playbook.md"]
    },
    "03_action_plan": {
        "name": "What To Do First",
        "format": "markdown",
        "dependencies": ["02_daily_pain_points"],
        "tldr_guides": ["ai-implementation-steps-smb.md"]
    },
    "04_simple_roadmap": {
        "name": "Your Week-by-Week Plan",
        "format": "markdown",
        "dependencies": ["03_action_plan"],
        "tldr_guides": ["ai-implementation-steps-smb.md"]
    },
    "05_readiness_assessment": {
        "name": "Your AI Readiness",
        "format": "markdown",
        "dependencies": ["01_tools_audit", "02_daily_pain_points"],
        "tldr_guides": ["smb-ai-playbook.md", "smb-ai-value-playbook.md"]
    },
    "06_roi_snapshot": {
        "name": "What It Costs & What You Save",
        "format": "markdown",
        "dependencies": ["03_action_plan"],
        "tldr_guides": ["smb-ai-value-playbook.md"]
    },
    "07_closing": {
        "name": "Putting It All Together",
        "format": "markdown",
        "dependencies": [
            "01_tools_audit", "02_daily_pain_points", "03_action_plan",
            "04_simple_roadmap", "05_readiness_assessment", "06_roi_snapshot"
        ],
        "tldr_guides": []
    },
    "final_strategy_report": {
        "name": "AI Strategy Report",
        "format": "docx",
        "dependencies": ["ALL_MARKDOWN"],
        "tldr_guides": []
    },
    "final_strategy_report_pdf": {
        "name": "AI Strategy Report (PDF)",
        "format": "pdf",
        "dependencies": ["ALL_MARKDOWN"],
        "tldr_guides": []
    },
}

# Quality domain list for research validation
QUALITY_DOMAINS = [
    "bloomberg.com", "reuters.com", "forbes.com", "wsj.com",
    "techcrunch.com", "crunchbase.com", "linkedin.com", "sec.gov",
    "mckinsey.com", "bcg.com", "deloitte.com", "gartner.com",
    "hbr.org", "mit.edu", "stanford.edu", "accenture.com"
]

# Retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay": 5,
    "max_delay": 60,
    "backoff_multiplier": 2
}
