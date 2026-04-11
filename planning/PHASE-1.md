# Phase 1 Plan: Remove Features from Workflow

## Context

Per the RESOLUTION-OUTLINE.md, Phase 1 removes diagram generation and PPTX generation from the pipeline. Diagrams and presentations were previously stripped from the sidebar but still exist in the pipeline code and results page. Additionally, the progress percentage score currently counts all deliverables (including PPTX), so it needs to exclude those. The "Documents" heading in the results sidebar should be renamed to "Final Documents".

## Changes

### 1. Skip PPTX generation in `generation/orchestrator.py`

**File:** `strategy_factory/generation/orchestrator.py`

In `generate_all()`:
- Change `total_steps` from 4 to 3 (markdown, docx, pdf)
- Remove the PPTX step entirely (the call to `_generate_presentations`)
- Keep `_generate_presentations()` and `pptx_generator.py` as dead code for potential future use

Note: `generate_outputs_from_synthesis()` is defined but never called anywhere — no changes needed there.

### 2. Remove diagrams from results page in `webapp.py`

**File:** `strategy_factory/webapp.py`

Diagram generation doesn't happen in the pipeline (no mermaid step in `generate_all()`). The only diagram references are in the webapp results page. Remove:
- The "Diagrams" stat from the stats bar
- The "Diagrams" sidebar section
- The `mermaid_images` parameter from `render_results_page()` and its call site
- The diagram grid JS template
- The `show-diagrams` click handler in `RESULTS_SCRIPTS`
- The mermaid_images gathering code in the `results()` route

### 3. Remove presentations from results page in `webapp.py`

In `render_results_page()`:
- Remove the "Presentations" sidebar section
- Remove `presentations` parameter from function signature and call site
- Remove the presentations gathering code in the `results()` route

### 4. Rename "Documents" heading to "Final Documents"

In `render_results_page()`:
- Change `<h3>Documents</h3>` to `<h3>Final Documents</h3>`

### 5. Fix progress percentage to exclude PPTX

**File:** `strategy_factory/config.py`

- Remove `"executive_summary_deck"` entry from the DELIVERABLES dict

Progress is calculated as `completed / total * 100` using DELIVERABLES keys, so removing the entry automatically fixes the percentage. Remaining deliverables: 6 markdown + docx + pdf = 8.

### 6. Update progress bar message

**File:** `strategy_factory/webapp.py`

- Change `"Creating presentations and reports"` to `"Creating final documents"`

## Files Modified

| File | Change |
|------|--------|
| `strategy_factory/generation/orchestrator.py` | Remove PPTX step from `generate_all()`, change `total_steps` to 3 |
| `strategy_factory/webapp.py` | Remove diagrams/presentations from results page, rename "Documents" to "Final Documents", update progress message |
| `strategy_factory/config.py` | Remove `executive_summary_deck` from DELIVERABLES |

## Verification

1. `python -m strategy_factory.main run "Test Company" --dry-run` — should show no PPTX step
2. Run the webapp and verify results page: no "Diagrams" stat, no "Presentations" section, heading says "Final Documents"
3. Check that progress percentage counts 8 deliverables (6 markdown + docx + pdf)
