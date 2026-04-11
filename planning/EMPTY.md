# Fix: Remove Empty Paragraph Gaps in Strategy Report DOCX

## Context

Generated DOCX strategy reports contain 26 empty Normal-style paragraphs in the body. Each renders with a visible line height (~14.7pt) plus spacing, creating gaps from noticeable (29pt) to huge (125pt / 1.7 inches). The user sees this most prominently after the readiness scorecard table, but it occurs throughout the document wherever standard tables, action cards, or roadmap cards appear.

**Root cause**: `_add_table()`, `_add_action_cards()`, and `_add_roadmap_cards()` use `doc.add_paragraph()` as spacers. These empty paragraphs carry inherited Normal style line height that can't be suppressed to zero.

## File to modify

`strategy_factory/generation/docx_generator.py`

## Changes

### 1. `_add_table()` — remove post-table empty paragraph (line 383)

**Remove**: `doc.add_paragraph()  # Add spacing after table`

No replacement needed. Tables have visible borders providing separation, and the next heading's `space_before` (18pt for H2) already provides adequate gap. Affects 5 locations: tools audit, time-wasters, readiness scorecard, monthly investment, and costs tables.

### 2. `_add_action_cards()` — eliminate spacer paragraphs (lines 665-756)

**Remove** the initial spacer (lines 667-669):
```python
spacer = doc.add_paragraph()
spacer.paragraph_format.space_before = Pt(0)
spacer.paragraph_format.space_after = Pt(6)
```

**Replace** the per-card spacer (lines 754-756) with conditional logic that only adds a minimal spacer between cards (not after the last one). For non-last cards, add a zero-height spacer:
```python
if row_idx < len(rows) - 1:
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(8)
    run = spacer.add_run()
    run.font.size = Pt(1)
    spacer.paragraph_format.line_spacing = Pt(1)
```

This reduces 5 empty paragraphs (each ~25pt) down to 3 zero-height spacers (each ~9pt) — from ~125pt to ~27pt total.

**Requires**: changing the loop from `for row_data in rows:` to `for row_idx, row_data in enumerate(rows):`

### 3. `_add_roadmap_cards()` — same pattern as action cards (lines 758-824)

**Remove** the initial spacer (lines 760-762).

**Replace** the per-card spacer (lines 822-824) with the same conditional zero-height spacer, using `enumerate` on rows.

## Summary of gap reduction

| Location | Before | After |
|----------|--------|-------|
| After standard tables (5 locations) | ~29pt each | 0pt (heading spacing handles it) |
| Action cards (4 cards) | ~125pt (5 empty paras) | ~27pt (3 zero-height paras) |
| Roadmap cards (per week group) | ~100pt (4 empty paras) | ~18pt (2-3 zero-height paras) |

## Verification

1. Run the pipeline for any existing company:
   ```bash
   source venv/bin/activate
   python -m strategy_factory.main run "Test Company" --skip-research --context "test, 10 employees"
   ```
   Or regenerate from existing synthesis data.

2. Open the generated DOCX and visually confirm:
   - No large gaps after the readiness scorecard table
   - Action cards have clean, even spacing between them
   - Roadmap cards have clean, even spacing
   - No empty paragraphs stacking between sections

3. Run the empty paragraph analysis script to confirm count dropped from 26 to ~9 (only the 3 inter-action-card + ~6 inter-roadmap-card zero-height spacers):
   ```python
   from docx import Document
   doc = Document('output/{company}/documents/final_strategy_report.docx')
   empties = sum(1 for p in doc.paragraphs if p.style.name == 'Normal' and not p.text.strip())
   print(f'Empty paragraphs: {empties}')
   ```
