# Fix: Word Count Budgets Causing Section Truncation

## Problem

Gemini is truncating later sections in deliverables — writing full content for early sections, then outputting only headings for remaining sections. This happens across multiple deliverables despite "never output just a heading" rules in every prompt.

## Root Cause

Every prompt includes a `Total length: X-Y words` line in its mandatory rules. The model treats this as a **budget to spend** — it writes fully for early sections, exhausts the budget, then outputs bare headings for the rest. The "never output just a heading" rules are overridden by the word count target because the model resolves the conflict in favor of the hard number.

**Evidence:**

| Prompt | Word Target | Where it stops |
|--------|------------|---------------|
| `tech_inventory.py` | 800-1,000 | Writes ~800 words through "What to Automate", skips "Your #1 AI Opportunity" |
| `pain_points.py` | 1,400-1,800 | Writes ~1,800 words through "Content Creation Gap", skips last 2 sections |
| `roadmap.py` | 800-1,100 | Skips "Month 3 and Beyond" |
| `closing.py` | 400-600 | Writes "What This All Means", heads-only for other 2 |
| `executive_summary.py` | 300-500 | Writes 1 section, heads-only for other 2 |

Increasing `max_output_tokens` to 65K did not fix this — the model isn't hitting a token limit. It's self-limiting to match the word count.

The old prompts (before these word counts were added) said "create a comprehensive X document" and did not have this truncation problem.

## Implementation Plan

### Step 1: Remove `Total length:` lines from all 8 prompts

Delete the `Total length: X-Y words` line from the mandatory rules section in each file:

| # | File | Line | Text to remove |
|---|------|------|---------------|
| 1 | `strategy_factory/synthesis/prompts/tech_inventory.py` | 60 | `- Total length: 800-1,000 words` |
| 2 | `strategy_factory/synthesis/prompts/pain_points.py` | 107 | `- Total length: 1,400-1,800 words` |
| 3 | `strategy_factory/synthesis/prompts/quick_wins.py` | 64 | `- Total length: 700-900 words` |
| 4 | `strategy_factory/synthesis/prompts/roadmap.py` | 64 | `- Total length: 800-1,100 words` |
| 5 | `strategy_factory/synthesis/prompts/maturity_assessment.py` | 99 | `- Total length: 600-800 words` |
| 6 | `strategy_factory/synthesis/prompts/roi_calculator.py` | 64 | `- Total length: 500-700 words` |
| 7 | `strategy_factory/synthesis/prompts/closing.py` | 43 | `- Total length: 400-600 words` |
| 8 | `strategy_factory/synthesis/prompts/executive_summary.py` | 33 | `- Total length: 300-500 words` |

Each line is in the `## Mandatory rules` section at the bottom of each prompt's `PROMPT` string. Just delete the single line.

### Step 2: Bump `max_output_tokens` default

File: `strategy_factory/synthesis/gemini_client.py`, line 99

Change the default parameter from `8192` to `16384`:

```python
# Before
max_output_tokens: int = 8192,

# After
max_output_tokens: int = 16384,
```

The `generate_markdown()` method (line 293) calls `self.generate()` without overriding this, so fixing the default covers both paths.

### Step 3: Do NOT change per-section structural guidance

Lines like `(~350 words)` in section headings are fine. They tell the model *relative weight* between sections (section A should be bigger than section B). They don't cause the budget behavior because they're per-section, not a total budget.

## Files Modified (summary)

1. `strategy_factory/synthesis/prompts/tech_inventory.py` — remove total word count line
2. `strategy_factory/synthesis/prompts/pain_points.py` — remove total word count line
3. `strategy_factory/synthesis/prompts/quick_wins.py` — remove total word count line
4. `strategy_factory/synthesis/prompts/roadmap.py` — remove total word count line
5. `strategy_factory/synthesis/prompts/maturity_assessment.py` — remove total word count line
6. `strategy_factory/synthesis/prompts/roi_calculator.py` — remove total word count line
7. `strategy_factory/synthesis/prompts/closing.py` — remove total word count line
8. `strategy_factory/synthesis/prompts/executive_summary.py` — remove total word count line
9. `strategy_factory/synthesis/gemini_client.py` — change `max_output_tokens` from 8192 to 16384

## Verification

1. Run a dry-run to confirm prompts load without syntax errors:
   ```bash
   python -m strategy_factory.main run "Test Company" --dry-run
   ```
2. Run a live test against a sample company and check that all sections have body content (no bare headings):
   ```bash
   python -m strategy_factory.main run "Test Company"
   ```
3. Inspect the generated markdown files in `output/test-company/markdown/` — every `###` heading should have content below it
4. Spot-check output lengths to confirm the model isn't producing wildly long or short content without the word count guardrails
