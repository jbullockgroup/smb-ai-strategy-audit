# WAVE 4: Generation Layer Cleanup

**Status**: Ready after Wave 1-3 lands
**Depends on**: Wave 1-3 (config + prompts + pipeline must be in place)
**Source**: Extracted from REFACTOR-PLAN.md

---

## What This Wave Does

Removes mermaid diagram rendering and SOW generation from the pipeline. Keeps PPTX generation. Restructures DOCX and PDF generators to produce a single 15-20 page report from the 6 new SMB deliverables. Also removes the now-dead SOW/CompanySize constants from config.py (their only consumers are fixed in this wave).

---

## Step 1: Remove dead config constants — `strategy_factory/config.py`

These were left as dead code in Wave 1-3 because `docx_generator.py` still imported them. Now that we're fixing `docx_generator.py`, remove them together:

- `CompanySize` enum
- `SOW_PRICING_MULTIPLIERS`
- `SOW_BASE_PRICING`

---

## Step 2: `strategy_factory/generation/orchestrator.py`

### Remove from `generate_all()`:
- Mermaid diagram rendering step

### Remove from `_generate_documents()`:
- SOW generation

### Remove methods:
- `_render_mermaid()`
- `_extract_diagram_names()`

### Remove imports:
- `MermaidRenderer`

### Simplified `generate_all()` flow:

```python
def generate_all(self, ...):
    # Step 1: Save markdown files
    # Step 2: Generate PPTX presentation
    # Step 3: Generate DOCX strategy report
    # Step 4: Generate PDF strategy report
```

### Keep:
- `MarkdownGenerator` import and markdown saving
- `PowerPointGenerator` import and PPTX generation
- `DocxGenerator` import and DOCX generation
- `PDFGenerator` import and PDF generation

---

## Step 3: `strategy_factory/generation/docx_generator.py`

### Remove imports:
- `SOW_BASE_PRICING`, `SOW_PRICING_MULTIPLIERS`, `CompanySize` from `..config`

### Restructure `generate_strategy_report()` section mapping:

```python
# Executive Summary (1-2 pages)
self._add_section(doc, "Executive Summary", 1)
self._add_executive_summary_content(doc, company_input, research, synthesis)

# Where You Stand Today
self._add_section(doc, "Where You Stand Today", 1)
self._add_subsection_from_deliverable(doc, synthesis, "01_tools_audit", "Your Tool Stack & AI Opportunities", 2)

# Where You're Losing Money
self._add_section(doc, "Where You're Losing Money", 1)
self._add_subsection_from_deliverable(doc, synthesis, "02_daily_pain_points", "Time-Wasters & Bottlenecks", 2)

# Your AI Readiness
self._add_section(doc, "Your AI Readiness", 1)
self._add_subsection_from_deliverable(doc, synthesis, "05_readiness_assessment", "Readiness Assessment", 2)

# What To Do First
self._add_section(doc, "What To Do First", 1)
self._add_subsection_from_deliverable(doc, synthesis, "03_action_plan", "Priority Actions", 2)

# Your Week-by-Week Plan
self._add_section(doc, "Your Week-by-Week Plan", 1)
self._add_subsection_from_deliverable(doc, synthesis, "04_simple_roadmap", "Implementation Timeline", 2)

# What It Costs & What You Save
self._add_section(doc, "What It Costs & What You Save", 1)
self._add_subsection_from_deliverable(doc, synthesis, "06_roi_snapshot", "ROI Analysis", 2)
```

### Remove:
- `generate_statement_of_work()` and all SOW-related methods
- `_determine_company_size()` and CompanySize-related pricing logic
- `_add_sow_pricing()` and related helpers

### Update:
- `_add_executive_summary_content()` to distill the 6 SMB deliverables into 1-2 pages

---

## Step 4: `strategy_factory/generation/pdf_generator.py`

Same structural changes as docx_generator:
- Remove `CompanySize`/SOW imports
- Map to 6 new deliverables
- Remove SOW generation
- Update executive summary to reflect SMB content
- Remove CompanySize/pricing logic

---

## Files Changed in This Wave

| File | Action |
|------|--------|
| `strategy_factory/config.py` | Remove `CompanySize`, `SOW_PRICING_MULTIPLIERS`, `SOW_BASE_PRICING` |
| `strategy_factory/generation/orchestrator.py` | Remove mermaid/sow steps, keep pptx |
| `strategy_factory/generation/docx_generator.py` | Remove SOW imports, restructure to 6 sections |
| `strategy_factory/generation/pdf_generator.py` | Same restructuring as docx |

## Files Left As-Is (Not Deleted, Just Unused)

- `strategy_factory/generation/mermaid_renderer.py` — stays on disk, no longer called
- `strategy_factory/generation/pptx_generator.py` — stays in use (updated in Wave 6 if needed)

## Verification

```bash
# End-to-end test — should produce PPTX + DOCX + PDF with correct sections, no SOW
python -m strategy_factory.main run "Burris Chalmers Communications" --mode quick

# Check output structure
ls output/burris-chalmers-communications/
# Should see: markdown/ (6 files), presentations/ (1 .pptx), documents/ (1 .docx, 1 .pdf), NO mermaid_images/

# Check report content
# Should have: Executive Summary, 6 SMB sections
# Should NOT have: SOW, enterprise jargon
```
