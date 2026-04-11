# SUB-ITEMS.md — Fix Sub-Items Under Numbered Lists (Changes 6 & 7)

Handoff file for fixing how sub-items render under numbered lists. A new agent can implement all changes from this file alone.

---

## Context

The AI Strategy Factory generates strategy reports in DocX and PDF. When Gemini outputs numbered lists with sub-bullets (e.g. "1. Main point" followed by "- supporting detail"), the sub-items currently render as plain text with no indent and no bullet marker. They should render as indented bullets nested under their numbered parent.

This is a fix for both output formats. The problem is in the bullet handler's `prev_was_numbered` branch in each generator.

**What it looks like now:**
```
1. Main point
supporting detail without any formatting
```

**What it should look like:**
```
1. Main point
      • supporting detail (indented, with bullet marker)
```

---

## Files to Modify

| File | What to Change |
|------|----------------|
| `strategy_factory/generation/docx_generator.py` | Bullet handler, `prev_was_numbered` branch |
| `strategy_factory/generation/pdf_generator.py` | Bullet handler, `prev_was_numbered` branch |

---

## DocX Fix

**File:** `strategy_factory/generation/docx_generator.py`
**Location:** `_convert_markdown_to_docx`, bullet handler, lines 494-504

**Current code:**
```python
# Handle bullet points
bullet_match = re.match(r'^[-*+]\s+(.+)$', stripped)
if bullet_match:
    text = self._clean_markdown_text(bullet_match.group(1))
    if prev_was_numbered:
        # Suppress bullet inside numbered list — render as plain text
        self._add_formatted_paragraph(doc, text)
    else:
        self._add_formatted_paragraph(doc, text, style='List Bullet')
    i += 1
    continue
```

**Change only the `prev_was_numbered` branch** (lines 498-500). The full replacement:

```python
# Handle bullet points
bullet_match = re.match(r'^[-*+]\s+(.+)$', stripped)
if bullet_match:
    text = self._clean_markdown_text(bullet_match.group(1))
    if prev_was_numbered:
        # Sub-item under numbered list — render as indented bullet
        para = self._add_formatted_paragraph(doc, text, style='List Bullet')
        para.paragraph_format.left_indent = Inches(0.75)
    else:
        self._add_formatted_paragraph(doc, text, style='List Bullet')
    i += 1
    continue
```

**What changed:** The `prev_was_numbered` branch now uses `List Bullet` style with a deeper left indent (`0.75"`) instead of rendering as plain text. The `Inches` import is already used elsewhere in this file.

---

## PDF Fix

**File:** `strategy_factory/generation/pdf_generator.py`
**Location:** `_convert_markdown`, bullet handler, lines 619-634

**Current code:**
```python
# Bullet points
bullet_match = re.match(r"^[-*+]\s+(.+)$", stripped)
if bullet_match:
    text = self._clean_text(bullet_match.group(1))
    if prev_was_numbered:
        # Suppress bullet inside numbered list — render as plain paragraph
        flowables.append(Paragraph(self._inline_format(text), self.styles["body"]))
    else:
        if not prev_was_bullet:
            flowables.append(Spacer(1, 4))
        flowables.append(
            Paragraph(f"\u2022  {self._inline_format(text)}", self.styles["bullet"])
        )
        prev_was_bullet = True
    i += 1
    continue
```

**Change only the `prev_was_numbered` branch** (lines 623-625). The full replacement:

```python
# Bullet points
bullet_match = re.match(r"^[-*+]\s+(.+)$", stripped)
if bullet_match:
    text = self._clean_text(bullet_match.group(1))
    if prev_was_numbered:
        # Sub-item under numbered list — render as indented bullet
        sub_style = ParagraphStyle(
            "PDFSubBullet",
            parent=self.styles["bullet"],
            leftIndent=40,
        )
        flowables.append(
            Paragraph(f"\u2022  {self._inline_format(text)}", sub_style)
        )
    else:
        if not prev_was_bullet:
            flowables.append(Spacer(1, 4))
        flowables.append(
            Paragraph(f"\u2022  {self._inline_format(text)}", self.styles["bullet"])
        )
        prev_was_bullet = True
    i += 1
    continue
```

**What changed:** The `prev_was_numbered` branch creates a `ParagraphStyle` derived from the existing `"bullet"` style but with `leftIndent=40` (double the normal bullet's `leftIndent=20`) so sub-items are visually nested under their numbered parent. `ParagraphStyle` is already imported at line 16.

---

## Verification

1. Run the pipeline (skip research — we're testing rendering, not content):
   ```bash
   cd /Users/jeff/ai-strategy-factory
   source venv/bin/activate
   python -m strategy_factory.main run "Angela Kim Couture" --skip-research
   ```

2. Open the generated files:
   - `output/angela-kim-couture/documents/final_strategy_report.docx`
   - `output/angela-kim-couture/documents/final_strategy_report.pdf`

3. Check the fix: Find any numbered list that has sub-bullets (the action plan and readiness assessment sections typically have these). Sub-items should now:
   - Have a bullet marker (`•`)
   - Be indented to the right of their numbered parent
   - NOT appear as plain unformatted text

## Existing Output for Comparison

The current (pre-fix) output lives at:
- `output/angela-kim-couture/documents/final_strategy_report.docx`
- `output/angela-kim-couture/documents/final_strategy_report.pdf`

Keep these to compare before/after.
