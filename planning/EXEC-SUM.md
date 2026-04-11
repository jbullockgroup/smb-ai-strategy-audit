# EXEC-SUM.md — Executive Summary Deliverable Implementation Plan

**Purpose**: Self-contained handoff document for a new agent session. Contains everything needed to add the executive summary as an 8th synthesis deliverable.

## Execution Order: Step 5 of 5

| Step | Plan | What it does |
|------|------|-------------|
| 1 | TLDR-FIX | Fix knowledge_loader.py (standalone) |
| 2 | PROMPTS-AGAIN | Restructure all 7 prompt formats |
| 3 | RESEARCH-ENHANCEMENTS | Expand existing Perplexity queries (EXPAND-CO), pipeline wiring, prompt content |
| **4** | **EXEC-SUM (this plan)** | **Add 8th deliverable** |

**Prerequisites**: Step 2 (PROMPTS-AGAIN) must be complete — the new prompt uses the restructured format. Steps 1 and 3 are independent of this plan.

## Why This Change

Both the DOCX and PDF generators currently produce a weak executive summary by extracting the first substantive line from 3 deliverables and listing them as bullet points:

- `docx_generator.py:630-659` — `_add_executive_summary_content()` pulls first line from `01_tools_audit`, `02_daily_pain_points`, `05_readiness_assessment`
- `pdf_generator.py:506-543` — `_build_executive_summary()` does the same thing

With the new prompts being restructured (see PROMPTS-AGAIN.md), there are no section-level executive summaries to extract from. Even before, the bullet-point approach was weak. The fix: add an 8th Gemini synthesis deliverable that reads all 7 completed sections and produces a compelling 300-500 word executive summary.

**Benefits**:
- Highest quality — Gemini synthesizes all content into a narrative
- Shows in the UI sidebar as a standalone markdown file
- Gets inserted as the first section of the DOCX/PDF reports
- Fits existing architecture perfectly (same pattern as `07_closing`)

---

## Architecture: How Deliverables Flow Through the System

Understanding this is essential for making the right changes:

1. **`config.py` DELIVERABLES dict** — Defines all deliverables with name, format, dependencies, and TLDR guides. Used by:
   - `synthesis/orchestrator.py` — determines what to generate and in what order
   - `progress_tracker.py` — initializes tracking for each deliverable

2. **`synthesis/prompts/__init__.py`** — Maps deliverable IDs to prompt strings. Each prompt file exports a `PROMPT = """..."""` variable.

3. **`synthesis/orchestrator.py` GENERATION_ORDER** — List of lists defining generation levels. Items in the same list can run in parallel. Each level waits for the previous one. The orchestrator iterates `target_deliverables` filtered against each level.

4. **`synthesis/context_builder.py`** — Builds the full Gemini prompt by combining research, TLDR guides, and previously generated deliverables (dependencies). The `register_deliverable()` method tracks what's been generated. The `build_full_prompt()` method assembles everything.

5. **`generation/markdown_generator.py`** — Saves deliverables by iterating `SynthesisOutput.deliverables.items()`. No config dependency — automatically picks up anything in the synthesis output.

6. **`generation/docx_generator.py`** and **`generation/pdf_generator.py`** — Build the final documents. Currently have hardcoded exec summary logic that needs to be replaced.

7. **`webapp.py`** — Discovers markdown files from the output directory (`{output_dir}/{company_slug}/markdown/*.md`). No config dependency — automatically shows any saved markdown file.

**Key insight**: Adding a new deliverable only requires changes to config, prompts, orchestrator order, and the two generators. Everything else (markdown saver, webapp, progress tracker) picks it up automatically.

---

## Files to Create

### 1. `strategy_factory/synthesis/prompts/executive_summary.py`

New file. Must export `PROMPT = """..."""`.

The prompt follows the same structural pattern being applied to all other prompts (see PROMPTS-AGAIN.md): `# Task: Generate`, `## Required Sections`, numbered sections, `## Output Format`.

```python
"""Prompt for Executive Summary — compelling overview of the full report."""

PROMPT = """
# Task: Generate Executive Summary

Based on the complete AI strategy analysis produced above, create a compelling executive summary that gives the business owner a clear picture of where they stand and what to do next. This is the first section the client will read — it must make them want to keep reading.

## Required Sections

### 1. The Big Picture (~200 words)

A flowing narrative that covers:
- Their single biggest AI opportunity (from the tools audit and pain points)
- Where they're losing the most time/money (from pain points)
- Their readiness level in plain terms (from the readiness assessment)
- What success looks like if they act (from the roadmap and ROI sections)

Write this as connected prose — no bullet points, no headers within this section. Be specific to this business. Use real numbers and tool names from the analysis. This section MUST contain a complete ~200-word narrative. Do NOT output just a heading.

### 2. What To Do This Week (~100 words)

The single most important first action, the tool to use, and how long it takes. One paragraph. Make it feel doable — like something they could start on Monday morning. Name the exact tool and the exact task. This section MUST contain a complete ~100-word paragraph. Do NOT leave it as just a heading.

### 3. The Bottom Line (~100 words)

Two sentences: what it costs per month and what they get back in time and money. Reference the ROI math from the cost section. End with one sentence about why acting now beats waiting — the gap between experimenting with AI and actually capturing value. This section MUST contain a complete ~100-word paragraph. Do NOT leave it as just a heading.

## Output Format
- Write in second person ("you", "your") throughout
- Be specific — name tools, dollar amounts, hours saved
- No jargon, no "digital transformation", no maturity models
- This is the first thing the client reads — make every word count
- Total length: 300-500 words
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
"""
```

---

## Files to Edit

### 2. `strategy_factory/synthesis/prompts/__init__.py`

**Current content** (read this file to verify):
```python
from .tech_inventory import PROMPT as TECH_INVENTORY_PROMPT
from .pain_points import PROMPT as PAIN_POINTS_PROMPT
from .quick_wins import PROMPT as QUICK_WINS_PROMPT
from .roadmap import PROMPT as ROADMAP_PROMPT
from .maturity_assessment import PROMPT as MATURITY_ASSESSMENT_PROMPT
from .roi_calculator import PROMPT as ROI_CALCULATOR_PROMPT
from .closing import PROMPT as CLOSING_PROMPT

PROMPTS = {
    "01_tools_audit": TECH_INVENTORY_PROMPT,
    "02_daily_pain_points": PAIN_POINTS_PROMPT,
    "03_action_plan": QUICK_WINS_PROMPT,
    "04_simple_roadmap": ROADMAP_PROMPT,
    "05_readiness_assessment": MATURITY_ASSESSMENT_PROMPT,
    "06_roi_snapshot": ROI_CALCULATOR_PROMPT,
    "07_closing": CLOSING_PROMPT,
}
```

**Add** at the end of imports:
```python
from .executive_summary import PROMPT as EXECUTIVE_SUMMARY_PROMPT
```

**Add** at the end of PROMPTS dict:
```python
"08_executive_summary": EXECUTIVE_SUMMARY_PROMPT,
```

### 3. `strategy_factory/config.py`

**Current DELIVERABLES dict** ends with `07_closing` and then two generation items (`final_strategy_report`, `final_strategy_report_pdf`). These are NOT synthesis deliverables — they're generation-phase outputs.

**Add** after the `"07_closing"` entry and before `"final_strategy_report"`:
```python
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
```

Note: depends on `07_closing` too, since closing already synthesizes everything. The exec summary should be the absolute last thing generated so it has access to the complete report.

### 4. `strategy_factory/synthesis/orchestrator.py`

**Current GENERATION_ORDER** (line ~40):
```python
GENERATION_ORDER = [
    ["01_tools_audit", "02_daily_pain_points"],
    ["05_readiness_assessment", "03_action_plan"],
    ["04_simple_roadmap", "06_roi_snapshot"],
    ["07_closing"],
]
```

**Add** a new level at the end:
```python
GENERATION_ORDER = [
    ["01_tools_audit", "02_daily_pain_points"],
    ["05_readiness_assessment", "03_action_plan"],
    ["04_simple_roadmap", "06_roi_snapshot"],
    ["07_closing"],
    ["08_executive_summary"],
]
```

### 5. `strategy_factory/generation/docx_generator.py`

**Two changes**:

**A. In `generate_strategy_report()`** (around line 94), replace:
```python
# Executive Summary
self._add_section(doc, "Executive Summary", 1)
self._add_executive_summary_content(doc, company_input, research, synthesis)
```
with:
```python
# Executive Summary
self._add_section(doc, "Executive Summary", 1)
self._add_subsection_from_deliverable(doc, synthesis, "08_executive_summary", "Overview", 2)
```

**B. Delete the entire `_add_executive_summary_content` method** (lines 630-659). This method is no longer called anywhere.

### 6. `strategy_factory/generation/pdf_generator.py`

**Two changes**:

**A. In `generate_strategy_report()`** (around line 198), find the line:
```python
story.extend(self._build_executive_summary(company_input, research, synthesis))
```
and replace with:
```python
story.extend(self._build_from_deliverable(synthesis, "08_executive_summary"))
```

**B. Delete the entire `_build_executive_summary` method** (lines 506-543). This method is no longer called anywhere. The existing `_build_from_deliverable` method already handles the markdown-to-PDF conversion.

---

## Files NOT Changed

These files automatically pick up the new deliverable with no changes needed:

- **`strategy_factory/generation/markdown_generator.py`** — iterates `SynthesisOutput.deliverables.items()`, not config
- **`strategy_factory/generation/orchestrator.py`** — already iterates all generation steps generically
- **`strategy_factory/progress_tracker.py`** — automatically tracks from DELIVERABLES config
- **`strategy_factory/webapp.py`** — discovers from saved markdown files in output directory
- **`strategy_factory/synthesis/context_builder.py`** — dependency system handles everything via `register_deliverable()` and `_get_dependencies()`

---

## Verification

After implementation, run the pipeline for a test company:
```bash
python -m strategy_factory.main run "Test Company" --dry-run
```

Check:
1. `output/test-company/markdown/08_executive_summary.md` exists with 300-500 words of flowing prose (not bullet points)
2. `output/test-company/documents/final_strategy_report.docx` — "Executive Summary" section contains the Gemini-generated narrative, not first-line extraction bullets
3. `output/test-company/documents/final_strategy_report.pdf` — same as above
4. Webapp sidebar shows "Executive Summary" as a clickable document
5. All 7 existing deliverables still generate correctly (no regressions)
6. The exec summary references specific tools, dollar amounts, and hours from the other sections
