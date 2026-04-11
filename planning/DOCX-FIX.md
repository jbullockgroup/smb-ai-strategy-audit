# DOCX-FIX.md — Handoff Plan for DocX Generation Fixes

## Context

The AI Strategy Factory generates Word documents from markdown content. The DocX generator (`strategy_factory/generation/docx_generator.py`) has five formatting issues that need fixing. All five fixes are in a single file.

**How the pipeline works:**
1. Gemini generates markdown content (7 deliverables per company)
2. Markdown files are saved to `output/{company-slug}/markdown/`
3. `DocxGenerator` reads the markdown and converts it to a Word document using python-docx
4. The main conversion logic is `_convert_markdown_to_docx()` (lines 393-523) which parses markdown line-by-line
5. Tables go through `_process_markdown_table()` → `_add_table()`
6. The PDF generator (`pdf_generator.py`) already has proper table header styling — the DocX should match it

**Existing companies with output to test against:**
- `output/angela-kim-couture/`
- `output/healing-roots-design/`
- `output/mountain-bizworks/`

---

## File to Modify

**Single file:** `strategy_factory/generation/docx_generator.py`

All imports needed (`OxmlElement`, `qn`, `RGBColor`, `Pt`) are already present.

---

## Fix 1: H1 (`#`) Heading Markers Appearing as Literal Text

### Problem

The heading regex on line 476 is `r'^(#{2,6})\s+(.+)$'` — it only matches `##` through `######`. When Gemini outputs `# Heading`, it falls through to the regular paragraph handler (line 504) and renders as literal text `# Heading` in the DocX.

None of the *current* markdown files on disk use `#` headings (they use `##` or `###`), but Gemini can and does generate `#` headings in some runs. The fix is a defensive measure.

### Location

Line 476 and lines 482-484.

### Changes

**Line 476** — widen the regex to match H1:
```python
# BEFORE:
heading_match = re.match(r'^(#{2,6})\s+(.+)$', stripped)

# AFTER:
heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
```

**Lines 482-484** — map H1 to Word Heading 2 (H1 is reserved for document-level sections added by `_add_section()`):
```python
# BEFORE:
                word_level = min(level, 4)
                doc.add_heading(text, level=word_level)

# AFTER:
                # Map markdown H1 -> Word Heading 2 (H1 reserved for doc sections)
                word_level = 2 if level == 1 else min(level, 4)
                doc.add_heading(text, level=word_level)
```

---

## Fix 2: Table Header Styling — Add Background Color

### Problem

`_add_table()` (lines 352-359) only applies `run.bold = True` to header cells. No background color or text color. The PDF generator uses `TABLE_HEADER_BG = "#D6E4F0"` (light blue) with dark blue text. The DocX should match.

The pattern for cell shading already exists in `_add_action_cards()` at lines 641-644:
```python
shading = OxmlElement('w:shd')
shading.set(qn('w:fill'), 'F5F9FC')
shading.set(qn('w:val'), 'clear')
cell._tc.get_or_add_tcPr().append(shading)
```

### Location

Lines 352-359 in `_add_table()`.

### Changes

Replace the header styling block with background shading + dark blue text:
```python
        # Add headers
        header_row = table.rows[0]
        for i, header in enumerate(headers):
            cell = header_row.cells[i]
            cell.text = header
            # Bold + dark blue text
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True
                    run.font.color.rgb = RGBColor(31, 78, 121)
            # Light blue background (#D6E4F0) matching PDF
            shading = OxmlElement('w:shd')
            shading.set(qn('w:fill'), 'D6E4F0')
            shading.set(qn('w:val'), 'clear')
            cell._tc.get_or_add_tcPr().append(shading)
```

---

## Fix 3: Add Line Break Before Tables

### Problem

`_add_table()` adds a blank paragraph after the table (line 368) but nothing before it. Tables butt directly against preceding content.

### Location

Line 348 in `_add_table()`, before the table is created.

### Changes

Insert a small spacer paragraph before `table = doc.add_table(...)`:
```python
        # Add breathing room before table
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(0)
        spacer.paragraph_format.space_after = Pt(4)
```

---

## Fix 4: Reduce Large Blank Gaps Before Tables

### Problem

When a table follows a paragraph, the paragraph's default `space_after = Pt(6)` (Normal style) or `space_after = Pt(10)` (Heading 2) creates a visible gap. This gap appears before tables in every section of every company's DocX output. The user confirmed it's a universal problem across all deliverables, and it seems related to tables specifically.

### Location

Lines 399-517 in `_convert_markdown_to_docx()`. This requires tracking the last paragraph added and reducing its spacing when a table is about to start.

### Changes

**Step 1** — Add tracking variable after line 399 (`table_lines = []`):
```python
        last_para = None  # Track last paragraph for spacing adjustment before tables
```

**Step 2** — Line 484: Capture heading paragraph as `last_para`:
```python
# BEFORE:
                doc.add_heading(text, level=word_level)

# AFTER:
                last_para = doc.add_heading(text, level=word_level)
```

**Step 3** — Line 514: Capture regular paragraph as `last_para`:
```python
# BEFORE:
                para = self._add_formatted_paragraph(doc, stripped)

# AFTER:
                last_para = self._add_formatted_paragraph(doc, stripped)
```

**Step 4** — Line 458: When a table is first detected, reduce preceding paragraph's spacing:
```python
# BEFORE:
                in_table = True

# AFTER:
                in_table = True
                # Reduce gap on preceding paragraph before table
                if last_para is not None:
                    last_para.paragraph_format.space_after = Pt(2)
```

**How this works with Fix 3:** The preceding paragraph's `space_after` drops from 6pt to 2pt, then the 4pt spacer from Fix 3 provides clean minimal separation. Total gap: ~6pt instead of 10-16pt.

---

## Fix 5: Line Breaks Around Bullet Points — Increase Spacing

### Problem

`List Bullet` style uses `space_before = Pt(4)` / `space_after = Pt(3)`. `List Number` style is the same. This is too tight — items appear cramped.

### Location

Lines 183-191 in `_setup_styles()`.

### Changes

**List Bullet (lines 183-185):**
```python
# BEFORE:
        if 'List Bullet' in styles:
            lb = styles['List Bullet']
            lb.paragraph_format.space_before = Pt(4)
            lb.paragraph_format.space_after = Pt(3)

# AFTER:
        if 'List Bullet' in styles:
            lb = styles['List Bullet']
            lb.paragraph_format.space_before = Pt(6)
            lb.paragraph_format.space_after = Pt(6)
```

**List Number (lines 188-191):**
```python
# BEFORE:
        if 'List Number' in styles:
            ln = styles['List Number']
            ln.paragraph_format.space_before = Pt(4)
            ln.paragraph_format.space_after = Pt(3)

# AFTER:
        if 'List Number' in styles:
            ln = styles['List Number']
            ln.paragraph_format.space_before = Pt(6)
            ln.paragraph_format.space_after = Pt(6)
```

---

## Implementation Order

1. **Fix 5** (bullet spacing) — standalone style change, no dependencies
2. **Fix 1** (H1 regex) — standalone regex + mapping change
3. **Fix 2** (table header styling) — standalone in `_add_table()`
4. **Fix 3** (spacer before table) — standalone in `_add_table()`, do before Fix 4
5. **Fix 4** (gap reduction) — touches multiple locations in `_convert_markdown_to_docx()`, depends on Fix 3 being in place

---

## Verification

After implementing, regenerate a report to test:

```bash
# Test with an existing company (skip research/synthesis, just regenerate)
python -m strategy_factory.main run "Mountain Bizworks" --skip-research --skip-synthesis

# Or test with dry-run first
python -m strategy_factory.main run "Mountain Bizworks" --dry-run
```

**Check in the generated DocX:**
1. No `#` markers appear as literal text anywhere
2. Table headers show light blue background (`#D6E4F0`) with dark blue bold text
3. No large blank gaps before tables in any section
4. Bullet points have adequate breathing room between items
5. Consistent small spacing before and after all tables

**Test files to check against:**
- `output/mountain-bizworks/markdown/01_tools_audit.md` — has tables preceded by text
- `output/angela-kim-couture/markdown/03_action_plan.md` — has action card tables
- `output/healing-roots-design/markdown/05_readiness_assessment.md` — has varied heading levels

---

## Reference: Key Code Locations

| Item | File | Lines |
|------|------|-------|
| Heading regex | `docx_generator.py` | 476 |
| Heading level mapping | `docx_generator.py` | 482-484 |
| Table header styling | `docx_generator.py` | 352-359 |
| Spacer after table | `docx_generator.py` | 368 |
| Table detection | `docx_generator.py` | 448-467 |
| Main markdown parser | `docx_generator.py` | 393-523 |
| Style definitions | `docx_generator.py` | 137-206 |
| Cell shading pattern (existing) | `docx_generator.py` | 641-644 |
| PDF table header color (reference) | `pdf_generator.py` | 42, 846 |
