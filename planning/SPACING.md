# SPACING.md — DocX/PDF Spacing Fixes

Handoff for fixing bullet/table spacing in DocX and PDF generation. A new agent can implement everything from this file alone.

---

## Context

The AI Strategy Factory generates strategy reports in DocX and PDF. The Angela Kim Couture report revealed that bullet groups and tables have no visual breathing room from surrounding text. This file covers the minimal set of changes to fix that.

The scope is **spacing only**. A separate rendering quirk (how sub-bullets under numbered lists are displayed) is noted at the bottom as optional — do not bundle it in unless the user asks.

Changes 1, 5, 6/7 from FORMAT-FIX.md are handled separately — do NOT touch those.

---

## Why this is a 3-number fix (not a state-machine rewrite)

The `List Bullet` and `List Number` styles are already customized in `_setup_styles` at `strategy_factory/generation/docx_generator.py:181-191`:

```python
# Customize List Bullet
if 'List Bullet' in styles:
    lb = styles['List Bullet']
    lb.paragraph_format.space_before = Pt(6)
    lb.paragraph_format.space_after = Pt(6)
```

Word combines adjacent paragraph spacing using `max(prev.space_after, next.space_before)`, not by summing. `Normal` is set to `space_before = Pt(8), space_after = Pt(6)`. So `Normal → List Bullet` currently produces `max(6, 6) = 6pt` — the same gap as between two Normal paragraphs, which is why bullet groups look squished into the surrounding text.

The built-in `List Bullet` style also has `contextualSpacing = 1` by default in Word's template, which suppresses `space_before`/`space_after` **between adjacent paragraphs of the same style**. So bumping the style's values makes the group-boundary gap larger without loosening the spacing *inside* a group.

The same logic applies to tables: the existing code at line 463 already overrides the preceding paragraph's `space_after` to `Pt(6)` — we just bump that number.

The PDF generator already tracks `prev_was_bullet` and adds a 4pt leading spacer (pdf_generator.py:627-632). It only needs a one-clause extension for the trailing gap.

---

## Files to Modify

| File | Change |
|------|--------|
| `strategy_factory/generation/docx_generator.py` | Bump 3 numbers (A1, A2, B) |
| `strategy_factory/generation/pdf_generator.py` | Add one `or` clause (C) |

---

## Change A — DocX: List style spacing

**File:** `strategy_factory/generation/docx_generator.py`
**Location:** `_setup_styles`, lines 181-191

### A1. `List Bullet`

**Current:**
```python
# Customize List Bullet
if 'List Bullet' in styles:
    lb = styles['List Bullet']
    lb.paragraph_format.space_before = Pt(6)
    lb.paragraph_format.space_after = Pt(6)
```

**Change to:**
```python
# Customize List Bullet
if 'List Bullet' in styles:
    lb = styles['List Bullet']
    lb.paragraph_format.space_before = Pt(12)
    lb.paragraph_format.space_after = Pt(10)
```

### A2. `List Number`

**Current:**
```python
# Customize List Number
if 'List Number' in styles:
    ln = styles['List Number']
    ln.paragraph_format.space_before = Pt(6)
    ln.paragraph_format.space_after = Pt(6)
```

**Change to:**
```python
# Customize List Number
if 'List Number' in styles:
    ln = styles['List Number']
    ln.paragraph_format.space_before = Pt(12)
    ln.paragraph_format.space_after = Pt(10)
```

**What this accomplishes:**
- `Normal → List Bullet` (and `Normal → List Number`): gap becomes `max(6, 12) = 12pt`, up from 6pt. Visible breathing room before the first item.
- `Heading → List Bullet`: gap becomes `max(heading.space_after, 12)`, unchanged or slightly larger for H3/H4 which had smaller space_after.
- `List Bullet → Normal` (and `List Number → Normal`): gap becomes `max(10, 8) = 10pt`, up from `max(6, 8) = 8pt`.
- **Within a group** (`List Bullet → List Bullet`): unchanged, because Word's built-in `List Bullet` style has `contextualSpacing = 1`, which suppresses the new values between same-style neighbors.

### Guardrail if within-group spacing looks loose

If you open the output and bullets inside a single group now have visible gaps between them, `contextualSpacing` is not set on the style in this template. Add it explicitly by appending to `_setup_styles` right after the `List Number` block:

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

for style_name in ('List Bullet', 'List Number'):
    if style_name in styles:
        pPr = styles[style_name].element.get_or_add_pPr()
        if pPr.find(qn('w:contextualSpacing')) is None:
            pPr.append(OxmlElement('w:contextualSpacing'))
```

This is a fallback, not the primary path. Do A1 and A2 first, check the output, and only add this block if within-group spacing regressed.

### Note on existing spacer-paragraph plumbing

Lines 509-512 (before numbered list) and 521-524 (after numbered list) insert empty spacer paragraphs. Do **not** remove them in this pass. They're redundant with the style-based spacing above but harmless, and removing them expands blast radius. Leave them for a future cleanup if the output looks correct.

---

## Change B — DocX: Gap before tables

**File:** `strategy_factory/generation/docx_generator.py`
**Location:** Lines 461-463, inside the table-opening branch

**Current code:**
```python
# Reduce gap on preceding paragraph before table
if last_para is not None:
    last_para.paragraph_format.space_after = Pt(6)
```

**Change to:**
```python
# Adjust gap on preceding paragraph before table
if last_para is not None:
    last_para.paragraph_format.space_after = Pt(12)
```

Also update the comment (`Reduce` → `Adjust`) since we're no longer always reducing.

**Caveat:** `last_para` only tracks headings and regular paragraphs (see lines 489 and 534 where it's assigned). If a bullet list or numbered list immediately precedes a table, `last_para` is stale and this branch does nothing for that case. Change A1/A2 covers bullet-list → table because `List Bullet.space_after = Pt(10)` applies automatically. This is a pre-existing limitation of the table path and is out of scope here.

---

## Change C — PDF: Trailing gap after bullet groups

**File:** `strategy_factory/generation/pdf_generator.py`
**Location:** Lines 658-661, regular paragraph handler

**Current code:**
```python
if prev_was_numbered:
    flowables.append(Spacer(1, 6))
prev_was_bullet = False
prev_was_numbered = False
```

**Change to:**
```python
if prev_was_numbered or prev_was_bullet:
    flowables.append(Spacer(1, 6))
prev_was_bullet = False
prev_was_numbered = False
```

**Why the PDF fix is different from DocX:** reportlab has no paragraph-style-level spacing with contextual awareness — flowables are flat. State tracking (`prev_was_bullet`) is the correct mechanism, and it already exists in this file (set at line 632). We're just making the trailing spacer trigger on it. No DocX-side state plumbing is needed because DocX has native paragraph styles.

The PDF generator already handles the **leading** gap before a bullet group at lines 627-628 (`if not prev_was_bullet: flowables.append(Spacer(1, 4))`). No change needed there.

---

## Verification

1. Run the pipeline, skipping research (we're testing rendering, not content):
   ```bash
   cd /Users/jeff/ai-strategy-factory
   source venv/bin/activate
   python -m strategy_factory.main run "Angela Kim Couture" --skip-research
   ```

2. Open the generated files:
   - `output/angela-kim-couture/documents/final_strategy_report.docx`
   - `output/angela-kim-couture/documents/final_strategy_report.pdf`

3. Spot-check these transitions:
   - **Before a bullet group** (paragraph → first bullet): visible gap, noticeably larger than line-to-line in a paragraph.
   - **Within a bullet group** (bullet → bullet): tight, no visible gap. If loose, apply the contextualSpacing fallback in Change A.
   - **After a bullet group** (last bullet → next paragraph): visible gap.
   - **Before a table** (paragraph → table): visible gap.
   - **Numbered list boundaries:** same checks; numbered lists use the same style treatment via A2.

## Existing Output for Comparison

Keep the pre-fix files at:
- `output/angela-kim-couture/documents/final_strategy_report.docx`
- `output/angela-kim-couture/documents/final_strategy_report.pdf`

for before/after comparison.

---

## Out of scope (do not bundle unless asked)

**Sub-bullets under numbered lists.** The current code at `docx_generator.py:498-500` renders a bullet immediately following a numbered list item as plain text:

```python
if prev_was_numbered:
    # Suppress bullet inside numbered list — render as plain text
    self._add_formatted_paragraph(doc, text)
```

The earlier draft of this handoff rewrote that branch to render sub-bullets as indented `List Bullet` paragraphs. That's a rendering behavior change, not a spacing fix, and it should be tracked and reviewed separately. If the user wants it, open a new handoff — do not slip it in here.
