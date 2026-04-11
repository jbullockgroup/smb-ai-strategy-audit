# DOCX Styling Reference

Handoff document describing all styling decisions applied to the strategy report Word document
(`strategy_factory/generation/docx_generator.py`). Use this as the spec when implementing
equivalent styling in the PDF generator or any other output format.

---

## Color Palette

| Role | RGB | Hex | Usage |
|------|-----|-----|-------|
| Primary dark blue | `RGBColor(31, 78, 121)` | `#1F4E79` | Heading 1, title page company name |
| Primary medium blue | `RGBColor(68, 114, 196)` | `#4472C4` | Heading 2, Heading 3 |
| Body text | `RGBColor(64, 64, 64)` | `#404040` | Normal paragraphs |
| Subtitle/muted | `RGBColor(128, 128, 128)` | `#808080` | Title page subtitle line |

---

## Typography

All text uses **Arial** throughout. No serif fonts.

| Element | Font size | Bold | Color |
|---------|-----------|------|-------|
| Title page — company name | 28 pt | Yes | Primary dark blue |
| Title page — report title | 24 pt | No | Body text (#404040) |
| Title page — subtitle | 14 pt | No | Muted (#808080) |
| Heading 1 | 18 pt | Yes | Primary dark blue |
| Heading 2 | 14 pt | Yes | Primary medium blue |
| Heading 3 | 12 pt | Yes | Primary medium blue |
| Body / Normal | 11 pt | No | Body text (#404040) |
| Code (inline/block) | 10 pt | No | Default (Courier New) |

---

## Paragraph Spacing

Spacing values follow Word's model: the **gap between two adjacent paragraphs is the
maximum** of the first paragraph's `space_after` and the second paragraph's `space_before`
(they do not add together).

| Style | space_before | space_after | Notes |
|-------|-------------|-------------|-------|
| Heading 1 | 24 pt | 8 pt | Major section break — large gap above |
| Heading 2 | 18 pt | 10 pt | Subsection — noticeable gap above, 10pt below ensures breathing room before first bullet |
| Heading 3 | 12 pt | 8 pt | Minor heading — moderate gap above |
| Normal (body) | 8 pt | 6 pt | space_before ensures gap when paragraph follows a bullet list |
| List Bullet | 4 pt | 3 pt | Small gap between bullet items |
| List Number | 4 pt | 3 pt | Matches List Bullet |

### Why `space_before` on Normal matters
Without it, a regular paragraph following a bullet list gets only the bullets' 3 pt `space_after`
as the gap — looks cramped. With `space_before = 8 pt` on Normal, the gap becomes
`max(3, 8) = 8 pt` regardless of what came before.

---

## Pseudo-Heading Detection (Bold-Only Lines)

Markdown content frequently uses lines like `**Key Strengths:**` or `**Overview**` as visual
subheadings. These are NOT markdown headings (`##`) so they render as Normal paragraphs.
Without special handling they bunch up against the content that follows.

**Detection rule** (applied in `_convert_markdown_to_docx`):

```python
if re.match(r'^\*\*.+\*\*:?\s*$', stripped):
    para.paragraph_format.space_before = Pt(12)
```

A line that is entirely wrapped in `**...**` (with an optional trailing colon) gets
`space_before = 12 pt` added directly to the paragraph instance, overriding the style default.

**For PDF**: detect the same pattern and add equivalent top padding (≈17px at 96dpi, or 4.2mm).

---

## Table of Contents

The TOC is generated using a Word field code (OOXML), not static text. Key decisions:

- **Field instruction**: `TOC \o "1-1" \h \z \u`
  - `\o "1-1"` — only Heading 1 entries (major sections only, no subsections)
  - `\h` — entries are hyperlinks
  - `\z` — hides tab/page numbers in Web Layout view
  - `\u` — uses applied outline level
- **`w:dirty="true"`** on the begin field character — tells Word to refresh the TOC
  automatically on open, no manual update needed
- **TOC 1 style tab stop**: right-aligned at **8500 twips** (≈5.9 inches from left margin),
  leader = none (clean whitespace, no dots). Position was chosen to stay safely within
  the 6.0-inch text area produced by python-docx's default 1.25-inch margins.

**For PDF**: build a static TOC from the known section list (Heading 1 titles only).
Page numbers must be calculated after layout. Use a right-aligned tab equivalent.

---

## Document Structure

Sections rendered in the strategy report, in order:

1. **Title page** — company name, report title, subtitle, page break
2. **Table of Contents** — Word field, page break
3. **Executive Summary** (Heading 1) — intro paragraph + Key Findings (Heading 2) with bullets
4. **Company Overview** (Heading 1) — Company Profile (H2), Industry Context (H2)
5. **Current State Assessment** (Heading 1) — Technology Inventory (H2), Pain Point Analysis (H2)
6. **AI Maturity Assessment** (Heading 1) — Readiness Evaluation (H2)
7. **AI Use Cases & Opportunities** (Heading 1) — Department-Specific Use Cases (H2)
8. **Strategic Recommendations** (Heading 1) — Quick Wins (H2), Implementation Roadmap (H2), Vendor Analysis (H2)
9. **Financial Analysis** (Heading 1) — ROI Analysis (H2), License Consolidation (H2)
10. **Governance & Operations** (Heading 1) — AI Policy Framework (H2), Data Governance (H2)
11. **Change Management** (Heading 1) — Training & Adoption Plan (H2)
12. **Appendices** (Heading 1) — Appendix A: Prompt Library (H2), Appendix B: Glossary (H2)

Content for H2 subsections is pulled from synthesized markdown deliverables and converted
via `_convert_markdown_to_docx`.

---

## Markdown → Document Conversion Rules

These apply in both DOCX and should be replicated for PDF:

| Markdown pattern | Output |
|-----------------|--------|
| `# Heading` (level 1) | Skipped — top-level headings are added explicitly by the orchestrator |
| `## Heading` (level 2+) | Word Heading at that level (capped at level 4) |
| `- text` / `* text` | List Bullet style |
| `1. text` | List Number style |
| `**bold**` | Bold run |
| `*italic*` | Italic run |
| `` `code` `` | Courier New, 10 pt |
| ` ```code block``` ` | Courier New, 10 pt, per line |
| ` ```mermaid``` ` | Skipped entirely |
| `---` / `***` / `___` | Skipped (horizontal rules) |
| `\| table \|` | Word/PDF table (Table Grid style) |
| YAML front matter (`---` block at top) | Skipped |
| Empty lines | Skipped (spacing handled entirely by styles) |
| Lines > 2000 chars | Skipped (corruption guard) |
| Lines with >50 dashes and >50% dashes | Skipped (malformed table separator guard) |

---

## Tables

- Style: `Table Grid` (bordered)
- Header row: bold text
- A blank Normal paragraph is appended after every table to ensure spacing

---

## What Was NOT Changed (intentionally)

- **Table spacing** — already looked fine due to the blank paragraph after each table
- **Title page spacing** — uses explicit blank paragraphs for vertical centering, not styles
- **Markdown empty line handling** — blank lines are skipped; spacing is style-driven only
