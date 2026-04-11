# WAVE 1-3: Config + Prompts + Pipeline Wiring

**Status**: Ready for implementation
**Merged as**: Single unit (these are tightly coupled — app won't run until all three land)
**Source**: Extracted from REFACTOR-PLAN.md

---

## Why These Three Are Bundled

Once `config.py` changes, the old 15-deliverable prompts are orphaned and the orchestrator will fail. Config + prompts + pipeline wiring must land together to keep the app functional.

---

## Step 1: Config — `strategy_factory/config.py`

### Replace DELIVERABLES dict

```python
DELIVERABLES = {
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
```

### Leave as dead code (removed in later waves)

The following are no longer referenced by the new DELIVERABLES but are still imported by other files. **Do not remove them yet** — they are cleaned up in Wave 4 (`CompanySize`, `SOW_*`) and Wave 6 (`TLDR_TOPIC_MAPPING`) alongside the files that import them.

- `CompanySize` enum — imported by `docx_generator.py` (removed in Wave 4)
- `SOW_PRICING_MULTIPLIERS` — imported by `docx_generator.py` (removed in Wave 4)
- `SOW_BASE_PRICING` — imported by `docx_generator.py` (removed in Wave 4)
- `TLDR_TOPIC_MAPPING` — imported by `knowledge_loader.py` (removed in Wave 6)

### Keep unchanged

`ResearchMode`, `PerplexityModel`, `PERPLEXITY_COSTS`, `RESEARCH_MODE_MODELS`, `GEMINI_MODEL`, `RETRY_CONFIG`, `QUALITY_DOMAINS`, all path constants.

---

## Step 2: Delete 9 Enterprise Prompt Files

From `strategy_factory/synthesis/prompts/`, delete:

| File | Reason |
|------|--------|
| `mermaid_diagrams.py` | No diagram deliverable |
| `vendor_comparison.py` | No vendor comparison |
| `license_consolidation.py` | No license management |
| `ai_policy.py` | No governance |
| `data_governance.py` | No governance |
| `prompt_library.py` | Jeff sells this separately |
| `glossary.py` | They can Google |
| `use_case_library.py` | Subsumed by pain points + action plan |
| `change_management.py` | No ADKAR for SMB |

---

## Step 3: Rewrite 6 Prompt Files

Each file keeps its existing filename, gets a complete content replacement. Each exports a single `PROMPT` string variable.

### Tone & Voice (applies to ALL prompts)

- Write for the owner, not a CTO or committee
- Concrete beats abstract: "spend 30 minutes instead of 3 hours" not "increase operational efficiency"
- Specific tools with prices: "ChatGPT Plus at $20/month" not "an AI platform"
- Action-oriented: "Do this, then this" not "Consider establishing a framework for"
- Budget-aware: Total spend under $150/month, individual tools under $50/month
- No jargon: No "digital transformation", "AI maturity", "governance framework", "change management"
- Professional but plain — readable by someone who doesn't know what an API is

### Tool Preferences (encode in ALL prompts where relevant)

**Primary AI tools (the 90% solution)**:
- ChatGPT Plus ($20/mo) — content creation, data analysis, image generation
- Claude Pro ($20/mo) — long-form writing, document analysis, proposals
- Gemini (free or $20/mo) — Google Workspace users, built-in sidebar
- Google AI Studio — for building automations (when technical help available)

**Automation**: n8n (preferred, charges per execution not per step)
**Voice AI**: Vapi, Retell, Elevenlabs — depending on use case

**NEVER recommend**: Make.com, Zapier, OpenClaw, Paperclip-style agent setups, anything requiring API knowledge, complex SaaS with enterprise pricing, Azure, AWS, Anthropic API direct

### `tech_inventory.py` — "Where You Stand Today"

- Prompt asks Gemini: What tools is this business probably using? What AI features are already built into those tools that they don't know about? What's still manual that shouldn't be?
- Sections: Your Current Tool Stack (table: tool, what you use it for, AI features you're not using), What's Still Manual (the low-hanging fruit), Your AI Opportunity Map
- Focus: Google Workspace, Microsoft 365, QuickBooks, social media tools, website platform, scheduling tools, CRM
- Anti-patterns: NO data infrastructure, NO compute readiness, NO enterprise platforms, NO "Integration Landscape"

### `pain_points.py` — "Where You're Losing Money"

- Prompt asks: Where are hours being wasted? Use the "500 new customers" thought experiment as a lens
- Sections: The "500 Customer" Test (what breaks first), Your Time-Wasters Ranked (hours/week lost), The 5 Boring Workflows (speed to lead, follow-up sequences, database reactivation, internal reporting, document processing — which ones apply), Content Creation Gap
- Anti-patterns: NO department matrices, NO ADKAR, NO cross-functional analysis, NO 2x2 prioritization

### `quick_wins.py` — "What To Do First"

- Prompt asks: 3-5 highest-impact things to do this month, ranked by impact
- For each: what tool, what it costs, what to do, what you get back (concrete: "Instead of 3 hours on proposals, spend 30 minutes")
- Tool preferences IN the prompt: ChatGPT/Claude/Gemini primary, n8n for automation (NOT Make/Zapier), Vapi/Retell/Elevenlabs for voice
- Anti-patterns: NO comparison matrices, NO escalation paths, NO success tracking dashboards, NO 10-item lists

### `roadmap.py` — "Your Week-by-Week Plan"

- Prompt asks: Week 1: do this. Week 2: add this. Month 2: add this.
- Sections: Your First 30 Days, Month 2, Month 3 and Beyond
- Anti-patterns: NO 5-phase transformation, NO Centers of Excellence, NO governance framework

### `maturity_assessment.py` — "Your AI Readiness"

- Prompt asks Gemini to infer readiness from available research data
- Two parts:
  1. Narrative: "You're in a common spot for a [industry] business at your size..."
  2. Scorecard: 5 questions each scored 0-3:
     1. Current AI adoption (are they using any AI tools?)
     2. Pain awareness (do they know where time is wasted?)
     3. Technical foundation (do they have basic digital tools?)
     4. Capacity for change (is the owner open to trying new things?)
     5. Budget alignment (can they invest $50-150/month?)
  - Total score: Not Ready (0-5), Ready to Start (6-9), Ready to Scale (10-15)
- Anti-patterns: NO BCG curve, NO 7 dimensions, NO radar charts, NO peer comparison

### `roi_calculator.py` — "What It Costs & What You Save"

- Prompt asks: Simple math — hours saved x hourly rate vs monthly tool costs
- Sections: Monthly Investment (tool costs in a table), Monthly Return (hours saved x rate), When You Break Even
- Anti-patterns: NO NPV, NO discount rates, NO sensitivity analysis, NO 3-year TCO

---

## Step 4: Update `strategy_factory/synthesis/prompts/__init__.py`

Replace all 15 imports with 6:

```python
from .tech_inventory import PROMPT as TECH_INVENTORY_PROMPT
from .pain_points import PROMPT as PAIN_POINTS_PROMPT
from .quick_wins import PROMPT as QUICK_WINS_PROMPT
from .roadmap import PROMPT as ROADMAP_PROMPT
from .maturity_assessment import PROMPT as MATURITY_ASSESSMENT_PROMPT
from .roi_calculator import PROMPT as ROI_CALCULATOR_PROMPT

PROMPTS = {
    "01_tools_audit": TECH_INVENTORY_PROMPT,
    "02_daily_pain_points": PAIN_POINTS_PROMPT,
    "03_action_plan": QUICK_WINS_PROMPT,
    "04_simple_roadmap": ROADMAP_PROMPT,
    "05_readiness_assessment": MATURITY_ASSESSMENT_PROMPT,
    "06_roi_snapshot": ROI_CALCULATOR_PROMPT,
}
```

---

## Step 5: Pipeline Wiring — `synthesis/orchestrator.py`

### Change GENERATION_ORDER to:

```python
GENERATION_ORDER = [
    ["01_tools_audit", "02_daily_pain_points"],
    ["05_readiness_assessment", "03_action_plan"],
    ["04_simple_roadmap", "06_roi_snapshot"],
]
```

### Rewrite `_get_system_instruction()`:

Replace the entire system instruction with:

```
You are an AI adoption coach creating practical, plain-English strategy reports for small business owners.

Guidelines:
- Write like you're explaining to a smart friend who isn't technical
- Be specific with tool names and prices (ChatGPT Plus $20/mo, Claude Pro $20/mo, Gemini free/$20/mo)
- Focus on what to DO, not frameworks or models
- Keep recommendations under $50/month unless there's a compelling reason
- Never recommend: Make.com, Zapier, complex automation platforms, anything requiring API knowledge
- Prefer: n8n for automation (if technical help available), native integrations in existing tools
- Use concrete examples: "Instead of spending 3 hours on proposals, spend 30 minutes"
- Total budget awareness: most clients are $150K-$2.5M revenue, owner-operated
- NO enterprise jargon, NO maturity models, NO governance frameworks
- Professional but accessible - this should read like expert advice, not a blog post
```

Remove the audience tone guidance injection from this method (audience context stays in user prompt only).

---

## Step 6: Context Builder — `synthesis/context_builder.py`

### Simplify `_load_tldr_knowledge()`:
- Remove the audience guide override logic — audiences no longer swap guides
- Always load from the 3 SMB guides based on deliverable config
- Keep the truncation logic

### Simplify audience injection in `build_full_prompt()`:
- Keep the audience context injection in user prompt
- It now serves as "cohort context" (e.g., "these are plumbers in NC")
- Remove the comment about double-injection since we removed the system instruction piece

### Simplify `build_full_prompt()`:
- Remove competitor-specific conditional (no vendor comparison deliverable)
- Remove regulatory conditional (no policy/governance deliverables)

---

## Files Changed in This Wave

| File | Action |
|------|--------|
| `strategy_factory/config.py` | Replace DELIVERABLES dict only (dead code stays) |
| `strategy_factory/synthesis/prompts/tech_inventory.py` | Complete rewrite |
| `strategy_factory/synthesis/prompts/pain_points.py` | Complete rewrite |
| `strategy_factory/synthesis/prompts/quick_wins.py` | Complete rewrite |
| `strategy_factory/synthesis/prompts/roadmap.py` | Complete rewrite |
| `strategy_factory/synthesis/prompts/maturity_assessment.py` | Complete rewrite |
| `strategy_factory/synthesis/prompts/roi_calculator.py` | Complete rewrite |
| `strategy_factory/synthesis/prompts/__init__.py` | Update to 6 imports |
| `strategy_factory/synthesis/orchestrator.py` | GENERATION_ORDER + system instruction |
| `strategy_factory/synthesis/context_builder.py` | Simplify guide loading + audience context |
| 9 prompt files | **Deleted** |

## Verification

```bash
# Should show 6 markdown deliverables + DOCX + PDF, no enterprise IDs
python -m strategy_factory.main run "Test Company" --dry-run

# Should import cleanly with 6 keys
python -c "from strategy_factory.synthesis.prompts import PROMPTS; print(len(PROMPTS), list(PROMPTS.keys()))"
```
