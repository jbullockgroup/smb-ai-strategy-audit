# Fix Duplicate/Extra Headers in PDF and DOCX Reports

## Context

The PDF and DOCX generators add duplicate or fabricated headings that don't appear in the actual markdown content. The web UI renders correctly because it just displays the raw markdown as-is.

### What the user sees

**PDF — "Executive Summary" section:**
- H1: "Executive Summary" (from generator)
- H2: "Executive Summary" (duplicate — from markdown content's `# Executive Summary`)

**DOCX — "Executive Summary" section:**
- H1: "Executive Summary" (from generator)
- H2: "Overview" (fabricated — doesn't exist in content)
- H2: "Executive Summary" (duplicate — from markdown content's `# Executive Summary`)

**DOCX — "Putting It All Together" section:**
- H1: "Putting It All Together" (from generator)
- H2: "Summary" (fabricated — doesn't exist in content)
- H3: "What This All Means" (from markdown content's `### What This All Means`)

This pattern repeats across all sections in both documents, for both Mountain BizWorks and Angela Kim Couture.

### Root causes

1. **Both generators**: Markdown deliverables often start with an H1 (e.g., `# Executive Summary`) that duplicates the section heading already added by the generator. The generators demote this to H2 but still render it, creating a visible duplicate.
2. **DOCX generator**: `_add_subsection_from_deliverable()` adds a fabricated H2 sub-heading ("Overview", "Summary", "Priority Actions", etc.) that doesn't exist in the content.
3. **PDF generator**: Adds synthetic H2 sub-headings for sections 2-7 ("Your Tool Stack & AI Opportunities", "Time-Wasters & Bottlenecks", etc.) that also don't exist in the content.

### Why the web UI is unaffected

The webapp (`server.py` line 537) renders each markdown file independently with `markdown.markdown()` — it doesn't add any extra section headers. It just renders the markdown as-is, which looks natural since each deliverable is shown as a standalone document.

### Markdown content patterns (inconsistent across deliverables)

Some deliverables start with an H1, others don't. Examples from actual output:

| Deliverable | Mountain BizWorks | Angela Kim Couture |
|---|---|---|
| 08_executive_summary | `# Executive Summary` | `# Executive Summary` |
| 01_tools_audit | `# Where You Stand Today` | No H1, starts with plain text |
| 02_daily_pain_points | `# Where Mountain Bizworks is Losing Money` | (not checked) |
| 03_action_plan | `# What To Do First` | No H1, starts with `### ...` |
| 04_simple_roadmap | (not checked) | (not checked) |
| 05_readiness_assessment | No H1, starts with `### ...` | (not checked) |
| 06_roi_snapshot | No H1, starts with `### ...` | (not checked) |
| 07_closing | No H1, starts with `### What This All Means` | No H1, starts with `### What This All Means` |

The H1 is inconsistent because it comes from the Gemini model's synthesis. The fix must handle both cases (H1 present and absent).

## Files to Modify

1. `strategy_factory/generation/docx_generator.py`
2. `strategy_factory/generation/pdf_generator.py`

## Changes

**Design principle:** fix each problem at the smallest possible surface. Don't touch call sites that don't need changing, and don't thread new state through converters that are already complex state machines. Strip the leading H1 once, up front, before handing markdown to the converter.

### 1. DOCX: Stop emitting the fabricated subtitle

In `docx_generator.py`, `_add_subsection_from_deliverable()` (lines 376–397):

The `title` parameter is the fabricated heading ("Overview", "Summary", "Priority Actions", etc.). Delete the line that renders it:

```python
def _add_subsection_from_deliverable(
    self,
    doc: Document,
    synthesis: SynthesisOutput,
    deliverable_id: str,
    title: str,
    level: int,
) -> None:
    """Add subsection from a deliverable's content."""
    doc.add_heading(title, level=level)   # ← DELETE this line
    ...
```

The 8 call sites in `generate_strategy_report()` (lines 93–123) do not need to change — they still pass `title`, it's just ignored. `title` and `level` become dead parameters but leaving them in place keeps this diff to one line. They can be cleaned up later if desired.

### 2. DOCX: Strip the leading H1 before converting

Same method, `_add_subsection_from_deliverable()` (around line 391). After fetching `content` and before calling `_convert_markdown_to_docx`, strip the leading H1 with a one-line regex:

```python
content = synthesis.deliverables[deliverable_id].content
if not content:
    doc.add_paragraph("[Content not available]")
    return

# Strip a leading H1 — the generator already added the section heading,
# and some deliverables start with `# Title` while others don't.
content = re.sub(r'^\s*#[^\n]*\n?', '', content, count=1)

self._convert_markdown_to_docx(doc, content)
```

`re` is already imported at the top of the file. `_convert_markdown_to_docx` itself is not touched.

### 3. PDF: Remove the fabricated H2 subtitles

In `pdf_generator.py`, `generate_strategy_report()` (lines 200–235), delete the 6 `self._h2(...)` lines between `_h1()` and `_build_from_deliverable()`:

| Line | Delete |
|------|--------|
| 205 | `story.extend(self._h2("Your Tool Stack & AI Opportunities"))` |
| 210 | `story.extend(self._h2("Time-Wasters & Bottlenecks"))` |
| 215 | `story.extend(self._h2("Readiness Assessment"))` |
| 220 | `story.extend(self._h2("Priority Actions"))` |
| 225 | `story.extend(self._h2("Implementation Timeline"))` |
| 230 | `story.extend(self._h2("ROI Analysis"))` |

Executive Summary (line 201) and Putting It All Together (line 234) already skip the H2, so they're untouched.

### 4. PDF: Strip the leading H1 before converting

In `pdf_generator.py`, `_build_from_deliverable()` (lines 514–519), strip the leading H1 before calling `_convert_markdown`:

```python
def _build_from_deliverable(self, synthesis: SynthesisOutput, deliverable_id: str) -> list:
    """Convert a synthesis deliverable's markdown content to PDF flowables."""
    deliverable = synthesis.deliverables.get(deliverable_id)
    if not deliverable or not deliverable.content:
        return [Paragraph("[Content not available]", self.styles["body"])]
    # Strip a leading H1 — the generator already added the section heading,
    # and some deliverables start with `# Title` while others don't.
    content = re.sub(r'^\s*#[^\n]*\n?', '', deliverable.content, count=1)
    return self._convert_markdown(content)
```

`re` is already imported at the top of the file. `_convert_markdown` itself is not touched.

### Summary of touched lines

- `docx_generator.py`: 1 deletion (line 385) + 1 insertion (regex strip in `_add_subsection_from_deliverable`)
- `pdf_generator.py`: 6 deletions (synthetic H2 lines) + 1 modification to `_build_from_deliverable` (regex strip)

Total: ~10 lines of real change across 2 files. Both large markdown-converter methods are left untouched.

## Expected result after fix

For every section, the structure will be:
- **One H1**: The section title added by the generator (e.g., "Executive Summary")
- **Then the markdown content as-is**: Sub-headings (H2, H3) that are actually in the content, with no duplicates or fabricated headings

This matches what the web UI shows.

## Verification

1. Run the pipeline for a test company (use `--skip-research --skip-generation` to reuse existing data, or a full run)
2. Open the generated DOCX and PDF
3. For each section, confirm:
   - Exactly one H1 (the section title)
   - Content's own sub-headings (H2/H3) appear directly beneath
   - No duplicate "Executive Summary" under "Executive Summary"
   - No fabricated "Summary" H2 under "Putting It All Together"
   - No fabricated "Overview" H2 under "Executive Summary"
4. The structure should match what the web UI shows at `http://localhost:8888`
