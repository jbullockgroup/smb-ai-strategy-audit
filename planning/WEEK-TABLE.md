# Plan: One Table Per Week in "Your First 30 Days"

## Context

The roadmap deliverable (`04_simple_roadmap`) currently renders the First 30 Days as a single 5-column table covering all 4 weeks (8–12 rows). The downstream generators detect that table and render each row as a bordered card. This works, but the week structure is buried inside the Action column (`"Week 1: ..."` prefix), which makes it harder to see the week-by-week rhythm — especially in the DOCX/PDF where a 10-card vertical run loses its "this is Week 2" anchor.

Additionally, the 5th column header is drifting — the prompt says `What To Do`, but Gemini sometimes emits `Details`. This is cosmetic (the renderer uses index 4 regardless), but should be locked in while we're touching this file.

**Goal:** Each of the 4 weeks gets its own 5-column table under its own week heading. Cards then render grouped by week with a visible heading above each group. No change to card visuals.

## What's NOT changing (important)

The card detection and rendering code does not need changes:

- `DocxGenerator._is_roadmap_table` (`strategy_factory/generation/docx_generator.py:652`) triggers per-table on `len == 5 and headers[0] == "#"`. Four separate tables → four separate card groups.
- `DocxGenerator._add_roadmap_cards` (`strategy_factory/generation/docx_generator.py:749`) uses `row_data[4]` regardless of header text, so "What To Do" vs "Details" doesn't affect rendering.
- `PdfGenerator._is_roadmap_table` (`strategy_factory/generation/pdf_generator.py:718`) and `_build_roadmap_cards` (`strategy_factory/generation/pdf_generator.py:802`) behave identically.
- `_flush_table` flushes the buffered table when a non-table line (like an H4 heading) appears, so `#### Week 1` between two tables Just Works with existing line-by-line markdown parsing.

This is a **prompt-only change**. One file.

## Files to modify

| File | Purpose |
|------|---------|
| `strategy_factory/synthesis/prompts/roadmap.py` | Restructure "Your First 30 Days" instructions to emit 4 tables with week headings |

## Change: `strategy_factory/synthesis/prompts/roadmap.py`

Replace the current "Your First 30 Days" section of the prompt (lines ~12–31) with instructions that ask for **four separate tables**, one per week, each under its own `####` heading.

### New structure the prompt should request

```
### Your First 30 Days (~400 words)

#### Week 1: [short theme — 3-5 words]

| # | Action | Tool (Price) | Time | What To Do |
|---|--------|-------------|------|------------|
| 1 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step] |
| 2 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step] |

#### Week 2: [short theme]

| # | Action | Tool (Price) | Time | What To Do |
|---|--------|-------------|------|------------|
| 1 | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... |

#### Week 3: [short theme]

| # | Action | Tool (Price) | Time | What To Do |
...

#### Week 4: [short theme]

| # | Action | Tool (Price) | Time | What To Do |
...
```

### Rules the prompt must state

- Four tables total, one per week, under a `#### Week N: [theme]` heading.
- Each table is exactly 5 columns with headers `| # | Action | Tool (Price) | Time | What To Do |` — **use "What To Do" exactly**, never "Details" or other variants.
- Numbering **restarts at 1** in each week's table (Week 1 = 1,2,(3); Week 2 = 1,2,(3); etc.).
- 2–3 rows per week (8–12 total across all weeks).
- Drop the old `"Week 1: ..."` prefix from the Action column — the heading now carries the week label, so the Action column should be a clean verb-first phrase.
- Every row must have a specific tool name and price in the Tool column.
- No empty cells.
- If a task needs technical help, say so in the What To Do column.
- No bullet lists or sub-bullets in this section — only the four tables.

### Rules that stay unchanged

- Month 2, Month 3, Weekly Check-In sections remain as prose paragraphs (same word counts, same rules, same ROI feedback loop language).
- Mandatory rules at the bottom (no phases, no governance, write every section, summary line) stay as-is.

## Verification

1. Run the pipeline on the existing test company, skipping research to isolate the rendering change:
   ```bash
   cd /Users/jeff/ai-strategy-factory
   source venv/bin/activate
   python -m strategy_factory.main run "Angela Kim Couture" --skip-research
   ```

2. Check the intermediate markdown for the new structure:
   - `output/angela-kim-couture/markdown/04_simple_roadmap.md`
   - Should contain four `#### Week N: ...` headings, each followed by its own 5-column table with headers `| # | Action | Tool (Price) | Time | What To Do |`.
   - Numbering in each table should restart at 1.
   - No "Week N:" prefix inside the Action column.

3. Check the DOCX and PDF for the rendered result:
   - `output/angela-kim-couture/documents/final_strategy_report.docx`
   - `output/angela-kim-couture/documents/final_strategy_report.pdf`
   - The "Your Week-by-Week Plan → Your First 30 Days" section should now show four week headings, each with 2–3 bordered cards under it, instead of one long card run.
   - Card visuals (title color, shading, borders, spacing) should be identical to before.

4. Sanity-check that Month 2, Month 3, Weekly Check-In, and the SUMMARY line still render as full prose paragraphs — i.e., the prompt change didn't regress the other sections.

## Defaults I chose (flag if wrong)

- **Heading level:** `####` (H4) because the parent "Your First 30 Days" is `###` (H3) in the current prompt at roadmap.py:12.
- **Numbering:** restarts per table (1,2,3 each week) because each table is now a self-contained unit.
- **Action column:** drops the `"Week N:"` prefix since the heading carries the week label.
- **Header name:** locked to `What To Do`, explicitly forbidding `Details` and other drift.
