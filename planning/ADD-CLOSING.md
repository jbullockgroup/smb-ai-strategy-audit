# Fix: Closing Section Missing from PDF and DOCX

## Problem

The `07_closing` ("Putting It All Together") deliverable is fully configured in the system, synthesized by Gemini during the synthesis phase, and saved as a markdown file — but both document generators **hardcode their section lists and omit it**. The generated PDF and DOCX reports end after the ROI section ("What It Costs & What You Save") with no closing/summary page.

This is purely a section-listing omission. No data is missing, no config is wrong — the closing content exists in `synthesis.deliverables["07_closing"]` at generation time but neither generator references it.

## Files to Change

Only two files. No config changes, no prompt changes, no new code needed.

### 1. `strategy_factory/generation/pdf_generator.py`

**Where**: The `generate()` method builds sections sequentially around lines 196–230. Each section follows the same pattern: `_h1()` for the heading, then `_build_from_deliverable(synthesis, "<id>")` for the content.

**Current state** (lines 225–230):
```python
        # What It Costs & What You Save
        story.extend(self._h1("What It Costs & What You Save"))
        story.extend(self._h2("ROI Analysis"))
        story.extend(self._build_from_deliverable(synthesis, "06_roi_snapshot"))

        doc.multiBuild(story)
```

**What to add**: Insert a new section block between line 228 and the `doc.multiBuild(story)` call:
```python
        # Putting It All Together
        story.extend(self._h1("Putting It All Together"))
        story.extend(self._build_from_deliverable(synthesis, "07_closing"))
```

Note: This section only uses `_h1`, not `_h2`, because the closing content has no subsection — it's a single narrative. Match the pattern of other single-subsection entries (the heading IS the section title).

### 2. `strategy_factory/generation/docx_generator.py`

**Where**: The `generate()` method builds sections sequentially around lines 93–123. Each section follows the same pattern: `_add_section()` for the heading, then `_add_subsection_from_deliverable()` for the content.

**Current state** (lines 117–123):
```python
        # What It Costs & What You Save
        self._add_section(doc, "What It Costs & What You Save", 1)
        self._add_subsection_from_deliverable(doc, synthesis, "06_roi_snapshot", "ROI Analysis", 2)

        # Save document
        output_path = self._get_output_path(company_slug, "final_strategy_report.docx")
        doc.save(output_path)
```

**What to add**: Insert a new section block between line 119 and the `# Save document` comment:
```python
        # Putting It All Together
        self._add_section(doc, "Putting It All Together", 1)
        self._add_subsection_from_deliverable(doc, synthesis, "07_closing", "Summary", 2)
```

## How the Existing Methods Work (for confidence)

Both generators have generic methods that just take a deliverable ID string:

- **PDF** (`_build_from_deliverable` at ~line 507): Looks up `synthesis.deliverables.get(deliverable_id)`, gets `.content`, converts markdown to ReportLab flowables. Returns `[Paragraph("[Content not available]", ...)]` if missing.
- **DOCX** (`_add_subsection_from_deliverable` at ~line 366): Looks up `synthesis.deliverables[deliverable_id]`, gets `.content`, converts markdown to docx paragraphs. Falls back to `[Content not available]` if missing.

No special-casing, no ID-specific logic — just a dictionary lookup. The `07_closing` key will work identically to every other key.

## Where `07_closing` Is Already Wired Up

For reference, confirming the data will be present at generation time:

- `config.py:58` — listed in `GENERATION_ORDER`
- `config.py:98` — defined in `DELIVERABLES` dict with name "Putting It All Together"
- `synthesis/orchestrator.py:44` — synthesized as the final level (depends on all other markdown deliverables)
- `synthesis/prompts/__init__.py:24` — prompt registered as `CLOSING_PROMPT`
- Individual markdown file is saved to `output/{slug}/markdown/07_closing.md` by the markdown generator

## Verification

1. **Import check** — confirm no syntax errors:
   ```bash
   python -c "from strategy_factory.generation.pdf_generator import PDFGenerator; from strategy_factory.generation.docx_generator import DOCXGenerator; print('imports OK')"
   ```

2. **Dry run** — confirm the pipeline still recognizes all deliverables:
   ```bash
   python -m strategy_factory.main run "Test Company" --dry-run
   ```

3. **Live test** (if you have API keys and an existing company with cached research/synthesis):
   ```bash
   python -m strategy_factory.main run "Healing Roots Design" --skip-research --skip-synthesis
   ```
   Then open the generated PDF and DOCX and confirm "Putting It All Together" appears as the final section.
