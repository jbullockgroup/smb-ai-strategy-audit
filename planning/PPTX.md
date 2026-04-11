# Plan: Reinstate PowerPoint Generation

## Problem

PPTX generator exists but is disconnected: the orchestrator never calls it, all deliverable IDs reference old names, and 4 slide methods reference deleted deliverables. Fix the wiring so both decks generate from current synthesis output and appear in the webapp.

---

## Files to Modify (5 files)

| # | File | Change |
|---|------|--------|
| 1 | `strategy_factory/config.py` | Add 2 PPTX deliverable entries |
| 2 | `strategy_factory/generation/pptx_generator.py` | Remap IDs, delete dead slides, add closing slides, fix agenda/appendix/fallback text |
| 3 | `strategy_factory/progress_tracker.py` | Add `presentations/` to directory list |
| 4 | `strategy_factory/generation/orchestrator.py` | Call existing `_generate_presentations()` in `generate_all()` |
| 5 | `strategy_factory/webapp.py` | Show PPTX downloads in results sidebar |

---

## Step 1: `config.py` — Add PPTX deliverable entries

Add at end of `DELIVERABLES` dict (after `final_strategy_report_pdf`, line ~115):

```python
"executive_summary_deck": {
    "name": "Executive Summary Deck",
    "format": "pptx",
    "dependencies": ["ALL_MARKDOWN"],
    "tldr_guides": []
},
"full_findings_deck": {
    "name": "Full Findings Deck",
    "format": "pptx",
    "dependencies": ["ALL_MARKDOWN"],
    "tldr_guides": []
},
```

---

## Step 2: `pptx_generator.py` — Fix content, delete dead code

### 2a. Remap all 15 stale deliverable ID references

Find-and-replace across the file:

| Old ID | New ID |
|--------|--------|
| `01_tech_inventory` | `01_tools_audit` |
| `02_pain_points` | `02_daily_pain_points` |
| `04_maturity_assessment` | `05_readiness_assessment` |
| `06_quick_wins` | `03_action_plan` |
| `05_roadmap` | `04_simple_roadmap` |
| `09_roi_calculator` | `06_roi_snapshot` |
| `14_use_case_library` | (deleted — see 2b) |
| `07_vendor_comparison` | (deleted — see 2b) |
| `10_ai_policy` | (deleted — see 2b) |
| `15_change_management` | (deleted — see 2b) |

### 2b. Delete 4 dead slide methods and their call sites

Delete these methods entirely:
- `_add_use_case_library_slides()` (~line 871)
- `_add_vendor_comparison_slides()` (~line 967)
- `_add_governance_slides()` (~line 984)
- `_add_change_management_slides()` (~line 1002)

In `generate_full_findings()` (~lines 177-198), delete the sections that call them:

```python
# DELETE these 8 lines:
self._add_section_divider(prs, "AI Use Cases & Opportunities")
self._add_use_case_library_slides(prs, synthesis)
...
self._add_vendor_comparison_slides(prs, synthesis)
...
self._add_section_divider(prs, "Governance & Operations")
self._add_governance_slides(prs, synthesis)
...
self._add_section_divider(prs, "Change Management & Training")
self._add_change_management_slides(prs, synthesis)
```

### 2c. Add closing section to full findings

Replace the deleted sections with a closing section. In `generate_full_findings()`, after the ROI section (~line 189) and before the existing summary/next-steps block (~line 201), add:

```python
# Section: Putting It All Together
self._add_section_divider(prs, "Putting It All Together")
self._add_closing_slides(prs, synthesis)
```

Add new method:

```python
def _add_closing_slides(self, prs: Presentation, synthesis: SynthesisOutput) -> None:
    """Add closing summary slides from the closing deliverable."""
    slide = self._add_slide_with_title(prs, "Putting It All Together", "Key takeaways and recommendations")
    content = self._extract_content_section(synthesis, "07_closing")
    bullets = self._extract_bullets_from_content(content, max_bullets=6) or [
        "AI strategy provides clear competitive advantages",
        "Implementation roadmap offers structured approach",
        "Quick wins deliver immediate value",
        "Ongoing assessment ensures continued progress",
    ]
    self._add_bullets_to_slide(slide, bullets)
```

### 2d. Fix mermaid fallback text

In `_add_current_state_diagram_slide()` (~line 849), change:
```
"See mermaid_diagrams.md for architecture diagram"
```
to:
```
"See the Tools Audit deliverable for full technology inventory details"
```

In `_add_future_state_diagram_slide()` (~line 945), change:
```
"See mermaid_diagrams.md for future state diagram"
```
to:
```
"See the Roadmap deliverable for future state details"
```

### 2e. Fix agenda slide

In `_add_agenda_slide()` (~line 721), replace the agenda list with:

```python
agenda_items = [
    "Company Overview & Market Context",
    "Current State Assessment",
    "AI Maturity & Readiness Evaluation",
    "Strategic Roadmap & Quick Wins",
    "Financial Analysis & ROI",
    "Putting It All Together",
]
```

This removes "AI Use Cases & Opportunities", "Governance & Operations Framework", and "Change Management & Training Plan", and adds "Putting It All Together" to match the new closing section.

### 2f. Fix appendix slide

In `_add_appendix_slide()` (~line 1034), replace bullets with:

```python
bullets = [
    "Full deliverables available in markdown format",
    "Detailed action plan and readiness assessment",
    "Week-by-week implementation roadmap",
    "Cost-benefit analysis and ROI projections",
    "Research sources and citations",
]
```

---

## Step 3: `progress_tracker.py` — Add presentations directory

In `_ensure_directories()` (~line 150), add `presentations/` to the list:

```python
dirs = [
    self.output_dir,
    self.output_dir / "markdown",
    self.output_dir / "documents",
    self.output_dir / "presentations",
]
```

Note: `pptx_generator._get_output_path()` already does `mkdir(parents=True, exist_ok=True)`, so this is belt-and-suspenders.

---

## Step 4: `orchestrator.py` — Call PPTX generation

In `generate_all()` (~line 83):

1. Change `total_steps = 3` to `total_steps = 5`

2. After the PDF step (after line ~108), add:

```python
# Step 4: Generate executive summary PPTX
current_step += 1
self._report_progress("Generating executive summary deck", current_step / total_steps)
exec_paths = self._generate_presentations(company_slug, company_input, research, synthesis)
self.generated_files.update(exec_paths)

# Step 5: Generate full findings PPTX
current_step += 1
self._report_progress("Generating full findings deck", current_step / total_steps)
try:
    full_path = self.pptx_gen.generate_full_findings(
        company_slug=company_slug,
        company_input=company_input,
        research=research,
        synthesis=synthesis,
        mermaid_images={},
    )
    self.generated_files["full_findings_deck"] = full_path
except Exception as e:
    self._record_error("full_findings_pptx", str(e))
```

No new methods. Reuses the existing `_generate_presentations()` for the exec deck and calls `generate_full_findings()` directly for the full deck.

---

## Step 5: `webapp.py` — Show PPTX downloads

### 5a. In `results()` route (~line 1434), after the documents scan, add:

```python
presentations = []
pres_dir = output_dir / "presentations"
if pres_dir.exists():
    for pres_file in sorted(pres_dir.glob("*.pptx")):
        presentations.append({
            "name": pres_file.stem.replace("_", " ").title(),
            "filename": pres_file.name,
            "size": f"{pres_file.stat().st_size / 1024:.1f} KB",
            "icon": "📊",
        })
```

Pass `presentations` to `render_results_page()`.

### 5b. In `render_results_page()` (~line 1545), add `presentations` parameter.

After the documents download section (~line 1577), before the closing `</aside>`:

```python
if presentations:
    html += '<h3>Presentations</h3>\n'
    for pres in presentations:
        icon = pres.get("icon", "📊")
        html += f'<a href="/files/{company_slug}/presentations/{pres["filename"]}" class="download-btn" download>{icon} {pres["name"]}<span class="size">{pres["size"]}</span></a>\n'
```

No route changes needed — existing `/files/<company_slug>/<path:filepath>` already serves from the output directory.

---

## Implementation Order

1. `config.py` — add PPTX entries
2. `pptx_generator.py` — remap IDs, delete dead slides, add closing, fix text
3. `progress_tracker.py` — add directory
4. `orchestrator.py` — call PPTX generation
5. `webapp.py` — add downloads

## Verification

1. `python -m strategy_factory.main run "Test Company" --dry-run` — no import errors
2. Live run — check `output/test-company/presentations/` has both `.pptx` files
3. Webapp — "Presentations" section appears with working download links
