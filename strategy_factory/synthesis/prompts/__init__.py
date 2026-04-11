"""
Prompt templates for deliverable synthesis.

Each prompt module exports a PROMPT string variable.
"""

from .tech_inventory import PROMPT as TECH_INVENTORY_PROMPT
from .pain_points import PROMPT as PAIN_POINTS_PROMPT
from .quick_wins import PROMPT as QUICK_WINS_PROMPT
from .roadmap import PROMPT as ROADMAP_PROMPT
from .maturity_assessment import PROMPT as MATURITY_ASSESSMENT_PROMPT
from .roi_calculator import PROMPT as ROI_CALCULATOR_PROMPT
from .closing import PROMPT as CLOSING_PROMPT
from .executive_summary import PROMPT as EXECUTIVE_SUMMARY_PROMPT

# Map deliverable IDs to prompts
PROMPTS = {
    "01_tools_audit": TECH_INVENTORY_PROMPT,
    "02_daily_pain_points": PAIN_POINTS_PROMPT,
    "03_action_plan": QUICK_WINS_PROMPT,
    "04_simple_roadmap": ROADMAP_PROMPT,
    "05_readiness_assessment": MATURITY_ASSESSMENT_PROMPT,
    "06_roi_snapshot": ROI_CALCULATOR_PROMPT,
    "07_closing": CLOSING_PROMPT,
    "08_executive_summary": EXECUTIVE_SUMMARY_PROMPT,
}


def get_prompt(deliverable_id: str) -> str:
    """Get the prompt template for a deliverable."""
    return PROMPTS.get(deliverable_id, "")
