# Phase 3: Update Configuration & Orchestrator

## Context

Phase 1 (remove diagrams/presentations) and Phase 2 (rewrite 6 prompts + add closing section) are separate. Phase 3 wires up the new `07_closing` deliverable and updates the system instruction to reflect 2026 tool landscape — specifically adding Claude Cowork as the top recommendation and Perplexity, and removing the $50/month budget ceiling.

## Changes

### 1. `strategy_factory/config.py` — Add closing deliverable

Add `07_closing` entry to `DELIVERABLES` dict after `06_roi_snapshot`:

```python
"07_closing": {
    "name": "Putting It All Together",
    "format": "markdown",
    "dependencies": ["01_tools_audit", "02_daily_pain_points", "03_action_plan", "04_simple_roadmap", "05_readiness_assessment", "06_roi_snapshot"],
    "tldr_guides": []
},
```

No changes needed to `tldr_guides` mappings — they already reference the SMB guides from "Consulting Guides TLDR".

### 2. `strategy_factory/synthesis/orchestrator.py` — Two edits

**a) Add `07_closing` to `GENERATION_ORDER`** (line ~43):

```python
GENERATION_ORDER = [
    ["01_tools_audit", "02_daily_pain_points"],
    ["05_readiness_assessment", "03_action_plan"],
    ["04_simple_roadmap", "06_roi_snapshot"],
    ["07_closing"],
]
```

**b) Update system instruction** in `_get_system_instruction()` (lines 219-233):

Remove: `$50/month` ceiling line
Add: Cowork as #1 recommendation, Perplexity in tool list

```python
return """
You are an AI adoption coach creating practical, plain-English strategy reports for small business owners.

Guidelines:
- Write like you're explaining to a smart friend who isn't technical
- Be specific with tool names and prices (ChatGPT Plus $20/mo, Claude Pro $20/mo, Perplexity Pro $20/mo, Gemini free/$20/mo)
- If the business could only do ONE thing: recommend Claude Cowork (Max plan, $100-200/mo) — it's an agentic AI that handles multi-step work autonomously, perfect for non-technical owners
- Focus on what to DO, not frameworks or models
- Never recommend: Make.com, Zapier, complex automation platforms, anything requiring API knowledge
- Prefer: n8n for automation (if technical help available), native integrations in existing tools
- Use concrete examples: "Instead of spending 3 hours on proposals, spend 30 minutes"
- Total budget awareness: most clients are $150K-$2.5M revenue, owner-operated
- NO enterprise jargon, NO maturity models, NO governance frameworks
- Professional but accessible - this should read like expert advice, not a blog post
"""
```

### 3. `strategy_factory/synthesis/prompts/__init__.py` — Register closing prompt

Add import and mapping:

```python
from .closing import PROMPT as CLOSING_PROMPT

# Add to PROMPTS dict:
"07_closing": CLOSING_PROMPT,
```

> Note: `closing.py` doesn't exist yet — it's created in Phase 2 (item 11). This registration will fail at import time until that file exists.

## Verification

After Phase 2 creates `closing.py`:
```bash
python -c "from strategy_factory.synthesis.prompts import PROMPTS; print(list(PROMPTS.keys()))"
```
Should show all 7 deliverable IDs including `07_closing`.
