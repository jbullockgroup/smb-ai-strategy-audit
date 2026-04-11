# BOTH-FIX: DocX & PDF List and Card Formatting Fixes

## Context

Generated strategy documents have three formatting issues that need fixing in both DocX and PDF output. These are all formatting-only changes in the markdown-to-document conversion layer — no prompt, synthesis, or config changes needed.

**The three issues:**
1. Numbered lists lack spacing — items run together without line breaks before/after the list
2. Nested bullets appear inside numbered lists or inside other bullets — all nesting must be flattened
3. Card elements (action plan cards) lack spacing before/after them, making them visually run into surrounding content

---

## Files to Modify

| File | Methods to Change | Lines |
|------|-------------------|-------|
| `strategy_factory/generation/docx_generator.py` | `_convert_markdown_to_docx()` | ~488-519 |
| `strategy_factory/generation/docx_generator.py` | `_add_action_cards()` | ~628-716 |
| `strategy_factory/generation/pdf_generator.py` | `_convert_markdown()` | ~618-668 |
| `strategy_factory/generation/pdf_generator.py` | `_build_action_cards()` | ~692-768 |

---

## Fix 1: Numbered List Spacing — Line Breaks Before/After Each Numbered Item

### DocX (`docx_generator.py`, `_convert_markdown_to_docx()`)

**Current code** (lines ~496-501):
```python
# Handle numbered lists
numbered_match = re.match(r'^\d+\.\s+(.+)$', stripped)
if numbered_match:
    text = self._clean_markdown_text(numbered_match.group(1))
    self._add_formatted_paragraph(doc, text, style='List Number')
    i += 1
    continue
```

**What to do:**
- Add a `prev_was_numbered` tracking flag (initialized to `False` alongside the loop)
- When a numbered item is found and `prev_was_numbered` is `False` (transitioning INTO a numbered list), insert a spacer paragraph before the first numbered item
- Set `prev_was_numbered = True` after each numbered item
- When a non-numbered, non-bullet line is encountered and `prev_was_numbered` is `True` (transitioning OUT of a numbered list), insert a spacer paragraph after the list
- Reset `prev_was_numbered = False` on non-numbered lines

**Spacer paragraph pattern** (already used elsewhere in the file):
```python
spacer = doc.add_paragraph()
spacer.paragraph_format.space_before = Pt(0)
spacer.paragraph_format.space_after = Pt(6)
```

### PDF (`pdf_generator.py`, `_convert_markdown()`)

**Current code** (lines ~631-643):
```python
# Numbered lists
numbered_match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
if numbered_match:
    if not prev_was_bullet:
        flowables.append(Spacer(1, 4))
    num = numbered_match.group(1)
    text = self._clean_text(numbered_match.group(2))
    flowables.append(
        Paragraph(f"{num}. {self._inline_format(text)}", self.styles["bullet"])
    )
    prev_was_bullet = True
    i += 1
    continue
```

**What to do:**
- Already has `prev_was_bullet` tracking, but it conflates bullets and numbers
- Add a separate `prev_was_numbered` flag
- When first numbered item is hit (`prev_was_numbered == False`), insert `Spacer(1, 6)` before the item
- When transitioning away from numbered (`prev_was_numbered` goes from `True` to `False`), insert `Spacer(1, 6)` after the list
- Keep `prev_was_bullet` for bullet-only spacing

---

## Fix 2: No Bullets Inside Numbered Lists

### The Problem

When Gemini produces markdown like `1. Item\n   - Sub-bullet`, the sub-bullet matches the bullet regex and renders as a visible bullet point inside the numbered list. Bullets should never appear inside a numbered list.

### The Fix (Both Files)

Use the `prev_was_numbered` flag from Fix 1. When `prev_was_numbered` is `True` and a bullet match is found, render the line as a plain paragraph (strip the bullet marker, keep the text) instead of using the bullet style.

### DocX (`docx_generator.py`, `_convert_markdown_to_docx()`)

In the bullet handling block (~line 499), add a check before applying the bullet style:

```python
bullet_match = re.match(r'^[-*+]\s+(.+)$', stripped)
if bullet_match:
    text = self._clean_markdown_text(bullet_match.group(1))
    if prev_was_numbered:
        # Suppress bullet — render as plain text continuation
        self._add_formatted_paragraph(doc, text)
    else:
        self._add_formatted_paragraph(doc, text, style='List Bullet')
    i += 1
    continue
```

### PDF (`pdf_generator.py`, `_convert_markdown()`)

Same logic in the bullet handling block (~line 625):

```python
bullet_match = re.match(r"^[-*+]\s+(.+)$", stripped)
if bullet_match:
    text = self._clean_text(bullet_match.group(1))
    if prev_was_numbered:
        # Suppress bullet — render as plain paragraph
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

---

## Fix 3: Line Breaks Around Cards

### DocX (`docx_generator.py`, `_add_action_cards()`)

**Current code** (~line 640): The loop starts immediately with no spacer before the first card. Each card ends with (~line 724-726):
```python
# Gap between cards
spacer = doc.add_paragraph()
spacer.paragraph_format.space_before = Pt(0)
spacer.paragraph_format.space_after = Pt(6)
```

**What to do:**
- Add a spacer paragraph **before** the `for row_data in rows:` loop (same pattern, `space_after = Pt(6)`)
- Bump the existing inter-card spacer from `Pt(6)` to `Pt(10)`

### PDF (`pdf_generator.py`, `_build_action_cards()`)

**Current code** (~line 772-774): Each card already has spacers using named constants:
```python
flowables.append(Spacer(1, _GAP_BEFORE_TABLE))   # 12pt (line 54)
flowables.append(card)
flowables.append(Spacer(1, _GAP_AFTER_TABLE))     # 14pt (line 55)
```

**What to do:**
- These values (12pt before, 14pt after) are already adequate. No change needed for PDF cards.

---

## Execution Order

1. Apply Fixes 1 & 2 (list spacing + bullet suppression) to both generators — these share the `prev_was_numbered` flag
2. Apply Fix 3 (card spacing) to `docx_generator.py` only — PDF already has adequate spacing

---

## Verification

Run the pipeline and manually inspect the output documents:
```bash
source venv/bin/activate
python -m strategy_factory.main run "Test Company" --dry-run
```

Check the generated files in `output/test-company/documents/`:
- **Numbered lists**: Visible blank space above the first item and below the last item
- **No nesting**: Any sub-bullets in the source markdown render as flat top-level bullets
- **Cards**: Clear visual separation from the paragraphs above and below each card

If a real run is needed (dry-run produces placeholder content), use:
```bash
python -m strategy_factory.main run "Test Company"
```
