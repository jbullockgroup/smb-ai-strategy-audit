# Audit Investigation Report

## 1. Executive Summary shows as document 8 in sidebar (should be first)

**Root cause**: `webapp.py:1349` sorts markdown files alphabetically by filename. `08_executive_summary.md` sorts last. The PDF uses a hardcoded order starting with Executive Summary (`docx_generator.py:94`). The UI needs a custom sort order.

## 2. Executive Summary is empty (headings only)

**Root cause**: Gemini is truncating output. The executive summary depends on ALL 7 other deliverables (`config.py:100-104`). The `context_builder.py` includes each truncated to 3,000 chars (~21K chars of dependencies alone) plus research context and the prompt itself. Despite the prompt explicitly saying "This section MUST contain a complete narrative. Do NOT output just a heading," Gemini produced only headings with no body content. The total prompt is very large, and Gemini 2.5 Flash appears to be hitting output limits or or failing to follow multi-section instructions under heavy context.

## 3. Table rows with hyphens in UI (Tools Audit, Action Plan)

**Root cause**: Gemini outputs `| --- | --- | --- | --- |` as data rows in the markdown (see `01_tools_audit.md:16,18` and `03_action_plan.md:15,17`). The DOCX generator has explicit filtering for this pattern (`docx_generator.py:607-610` — skips rows where all cells are dashes). The webapp's `fix_malformed_tables()` function handles long/malformed separators but does NOT filter dash-only data rows. The markdown-to-HTML renderer faithfully renders the `---` cells.

## 4. "What's Still Manual" headline — user wants different wording

**Root cause**: Hard-coded in the prompt template at `tech_inventory.py:34`. The prompt literally tells the model to use that heading.

## 5. "Your #1 AI Opportunity" section is blank

**Root cause**: Same truncation pattern as Issue 2. In `01_tools_audit.md:36`, the heading appears with nothing below it. The prompt at `tech_inventory.py:46-49` explicitly instructs "This section MUST contain a complete paragraph. DO NOT output just a heading." Despite this, Gemini output was already ~800+ words by this point and truncated.

## 6. "Time Wasters and Bottlenecks" header appears in PDF but not UI

**Root cause**: This heading doesn't exist in the markdown. The DOCX generator adds it manually as a subsection title at `docx_generator.py:103`: `self._add_subsection(doc, synthesis, "02_daily_pain_points", "Time-Wasters & Bottlenecks", 2)`. The raw markdown uses different headings ("Your Time-Wasters Ranked", "Your Highest-Impact Workflows", etc.). So the PDF has a wrapper heading that the markdown doesn't.

## 7. Content Creation Gap is too generic

**Root cause**: The prompt at `pain_points.py:69-77` says "If digital presence or online activity data appears in the research context above, reference specific facts." The research for this company apparently didn't return specific content/posting data, so Gemini fell back to generic advice. The conditional "If..." phrasing lets Gemini off the hook.

## 8. "What Your Competitors Are Up To" section is blank (both UI and PDF)

**Root cause**: Same truncation pattern. Gemini output just the heading at `02_daily_pain_points.md:97` with no content below it. The prompt says "Never output a heading without writing the content." Despite this, Gemini stopped after the heading.

## 9. Section ordering: UI doesn't match PDF

**Root cause**:
- **UI**: Sorted alphabetically by filename: 01, 02, 03, 04, 05, 06, 07, 08
- **PDF** (`docx_generator.py:94-119`): Hardcoded order: Executive Summary (08), Where You Stand (01), Losing Money (02), Readiness (05), What To Do (03), Roadmap (04), ROI (06). The Closing (07) is not included at all.

## 10. "Month 3 and Beyond" is empty (both UI and PDF)

**Root cause**: Same truncation pattern. `04_simple_roadmap.md:68-69` shows the heading with no content. The prompt at `roadmap.py:38-44` says "Do NOT leave this section empty — write the full 2-3 paragraphs." Gemini produced only the heading.

## 11. Closing section: empty headings + not in PDF

**Root cause**:
- **Empty content**: Same truncation. `07_closing.md` shows "What This All Means" (line 9) and "Closing Thought" (line 14) as bare headings. The prompt says "This section MUST be a complete narrative. Do NOT output just a heading."
- **Not in PDF**: `docx_generator.py` simply doesn't include deliverable `07_closing` in the report. The PDF ends at "What It Costs & What You Save" (`06_roi_snapshot`).

---

## Summary: 4 Underlying Root Causes

1. **Gemini output truncation** (Issues 2, 5, 8, 10, 11): When prompts are large and request multiple sections, Gemini 2.5 Flash produces headings for later sections but skips body content. This happens despite explicit "do not output just a heading" instructions. The executive summary is worst affected because it has the largest context (all 7 prior deliverables as dependencies).

2. **UI sort order differs from PDF** (Issues 1, 9): The UI sorts files alphabetically; the PDF uses hardcoded order. Neither matches the other.

3. **No filtering of dash-only table rows in the UI** (Issue 3): The DOCX generator filters these out; the webapp does not.

4. **Hard-coded prompt text and missing DOCX sections** (Issues 4, 6, 11): "What's Still Manual" is in the prompt template. "Time-Wasters & Bottlenecks" is a DOCX-only wrapper heading. The closing deliverable isn't included in the PDF.
