# Fix Issue #4: Bullet Points — Dashes vs. Bullets + Spacing

## Context

This is one of 9 issues identified in `REPORT-2.md` after auditing the Healing Roots Design PDF/DOCX output. Issue #4 covers three problems with how bullets render in the PDF:

1. **Dashes instead of bullets** — Bullets render as `- text` (ASCII dash) instead of `• text` (proper bullet character)
2. **Tight vertical spacing** — Only 7pt total gap between bullet items (4pt before + 3pt after) for 11pt font
3. **No group separation** — No spacer before/after bullet groups, so bullets run directly into headings and paragraphs

All changes are in **one file**: `strategy_factory/generation/pdf_generator.py`

## Changes

### Change 1: Replace dash with proper bullet character (line 614)

**Current:**
```python
Paragraph(f"- {self._inline_format(text)}", self.styles["bullet"])
```

**Change to:**
```python
Paragraph(f"\u2022  {self._inline_format(text)}", self.styles["bullet"])
```

### Change 2: Stop sanitizing real bullet characters (line 70)

**Current (line 70 in the `_SANITIZE` dict):**
```python
"\u2022": "-",    # bullet (we render bullets ourselves)
```

**Remove this line entirely.** The sanitizer currently replaces `•` with `-`. Since we're now using `\u2022` directly in Paragraph text, leaving this mapping in place would strip the bullets back out.

### Change 3: Increase bullet spacing (lines 340-341)

**Current:**
```python
spaceBefore=4,
spaceAfter=3,
```

**Change to:**
```python
spaceBefore=6,
spaceAfter=4,
```

This is inside the `"bullet"` ParagraphStyle definition within `_setup_styles()`.

### Change 4: Add spacer before bullet groups (lines 610-628)

Track whether the previous line was a bullet. When entering a bullet group from a non-bullet line, insert a small spacer (4pt) before the first bullet. No explicit spacer needed after — the `spaceAfter` on the last bullet plus the next element's `spaceBefore` handles it.

**Initialize the tracker** — add `prev_was_bullet = False` at line 527 alongside the other tracking variables:
```python
table_lines: List[str] = []
code_lines: List[str] = []
prev_was_bullet = False    # <-- add here
```

**Update the bullet_match block** (starting line 610):
```python
# Bullet points
bullet_match = re.match(r"^[-*+]\s+(.+)$", stripped)
if bullet_match:
    if not prev_was_bullet:
        flowables.append(Spacer(1, 4))
    text = self._clean_text(bullet_match.group(1))
    flowables.append(
        Paragraph(f"\u2022  {self._inline_format(text)}", self.styles["bullet"])
    )
    prev_was_bullet = True
    i += 1
    continue
```

**Update the numbered_match block** (starting line 619):
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

**Reset the tracker** — add `prev_was_bullet = False` in the regular paragraph block (around line 631), before the paragraph is appended, so any non-bullet/non-numbered line resets the state:
```python
# Regular paragraph
if stripped and len(stripped) <= 2000:
    # Skip dash-heavy lines (stray table separators)
    if stripped.count("-") > 50 and stripped.count("-") / len(stripped) > 0.5:
        i += 1
        continue

    prev_was_bullet = False    # <-- add here, before the paragraph logic

    formatted = self._inline_format(self._clean_text(stripped))
    ...
```

Also reset `prev_was_bullet = False` in the heading block (around line 606) and the empty-line handler (around line 589) so headings and blank lines break bullet groups properly.

## Key File Reference

| Location | What's there |
|----------|-------------|
| `pdf_generator.py:70` | `_SANITIZE` dict — remove `"\u2022": "-"` mapping |
| `pdf_generator.py:335-344` | `"bullet"` ParagraphStyle — bump spacing |
| `pdf_generator.py:525-527` | Loop variable initialization — add `prev_was_bullet` |
| `pdf_generator.py:610-616` | Bullet match block — new character + group spacer |
| `pdf_generator.py:619-628` | Numbered match block — group spacer |
| `pdf_generator.py:589` | Empty line handler — reset tracker |
| `pdf_generator.py:606` | Heading block — reset tracker |
| `pdf_generator.py:630` | Regular paragraph block — reset tracker |

## Verification

1. Run the CLI against an existing company with cached data:
   ```bash
   source venv/bin/activate
   python -m strategy_factory.main run "Healing Roots Design" --skip-research --skip-synthesis
   ```
2. Open the generated PDF at `output/healing-roots-design/documents/` and check:
   - Bullets use `•` not `-`
   - Spacing between items is comfortable (~10pt gap)
   - Bullet groups have a 4pt gap above them (separating from headings/paragraphs)
3. Spot-check the DOCX to confirm no regression (DOCX uses separate rendering logic, so these PDF-only changes should not affect it)
