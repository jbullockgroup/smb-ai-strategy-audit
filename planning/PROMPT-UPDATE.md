# Plan: Standardize Synthesis Prompt Heading Structure

## Context

The 8 synthesis prompts have inconsistent structure. Seven of them start with a plain-text role statement (no `#` heading), while the executive summary prompt starts with `# Task: Generate Executive Summary`. The old repo used `# Task: Generate [Name]` consistently across all prompts. The fix is simple: add an H1 task line to the 7 prompts that are missing it, matching the executive summary's existing pattern.

## What Changes

Add `# Task: Generate [Deliverable Name]` as the first line of each prompt, before the existing role statement. This matches the pattern the executive summary already uses and the old repo's structure.

No other changes to the prompts. The H2 (`## What to produce`), H3 sections (`### Section Name`), role statements, mandatory rules, and all content stay exactly as they are.

## Files to Modify

All files in `strategy_factory/synthesis/prompts/`:

### 1. `tech_inventory.py` (deliverable `01_tools_audit`)

**Add as first line:** `# Task: Generate Where You Stand Today`

### 2. `pain_points.py` (deliverable `02_daily_pain_points`)

**Add as first line:** `# Task: Generate Where You're Losing Money`

### 3. `quick_wins.py` (deliverable `03_action_plan`)

**Add as first line:** `# Task: Generate What To Do First`

### 4. `roadmap.py` (deliverable `04_simple_roadmap`)

**Add as first line:** `# Task: Generate Your Week-by-Week Plan`

### 5. `maturity_assessment.py` (deliverable `05_readiness_assessment`)

**Add as first line:** `# Task: Generate Your AI Readiness`

### 6. `roi_calculator.py` (deliverable `06_roi_snapshot`)

**Add as first line:** `# Task: Generate What It Costs & What You Save`

### 7. `closing.py` (deliverable `07_closing`)

**Add as first line:** `# Task: Generate Putting It All Together`

### 8. `executive_summary.py` (deliverable `08_executive_summary`)

**No change needed.** Already has `# Task: Generate Executive Summary`.

## Why This Is Safe

- The H1 is a prompt-level instruction. It does not appear in Gemini's output.
- All rendering systems (DOCX, PDF, web UI) handle heading levels dynamically.
- The executive summary already uses this pattern and works correctly.

## Verification

1. Run a full synthesis for a test company
2. Confirm the generated markdown files are unchanged in structure (still using `###` for sections)
3. Open the generated DOCX and PDF to confirm they render correctly
