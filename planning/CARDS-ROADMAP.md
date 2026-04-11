# CARDS-ROADMAP.md — Roadmap Cards Instead of Bullets

Handoff file for the week-by-week plan card layout. A new agent can implement all changes from this file alone.

---

## Context

The "Your Week-by-Week Plan" section previously rendered as wall-to-wall nested bullets — hard to scan, hard to act on. The fix converts the First 30 Days portion into a 5-column markdown table that both generators detect and render as bordered cards.

The Month 2, Month 3, and Weekly Check-In sections remain as prose paragraphs.

---

## Files to Modify

| File | Purpose |
|------|---------|
| `strategy_factory/synthesis/prompts/roadmap.py` | Prompt template — tells Gemini to output a table |
| `strategy_factory/generation/docx_generator.py` | Word renderer — detects and renders roadmap cards |
| `strategy_factory/generation/pdf_generator.py` | PDF renderer — detects and renders roadmap cards |

---

## Change A: Prompt — Output a 5-column table

**File:** `strategy_factory/synthesis/prompts/roadmap.py`

The prompt must instruct Gemini to output the First 30 Days as a single markdown table with 5 columns:

```
| # | Action | Tool (Price) | Time | What To Do |
```

Each row has 4 data fields: action (with week context like "Week 1: ..."), specific tool + price, time estimate, and what to do. No bullet lists or sub-bullets in this section.

**Rules for the table:**
- Number rows sequentially (1, 2, 3...)
- Include the week context in the Action column ("Week 1: ...", "Week 2: ...")
- Every row must have a specific tool name and price
- Fill every cell. No empty cells.
- Cover all 4 weeks, 2-3 rows per week (8-12 rows total)
- If a task needs technical help, say so in the What To Do column

The current prompt already has this format. Verify it hasn't regressed.

---

## Change B: DocX — Detect and render roadmap cards

**File:** `strategy_factory/generation/docx_generator.py`

### Detection method

Add a static method `_is_roadmap_table` that returns True when the table has exactly 5 columns and the first header is "#":

```python
@staticmethod
def _is_roadmap_table(raw_headers: List[str]) -> bool:
    """Return True if this is the 5-column roadmap table."""
    return len(raw_headers) == 5 and raw_headers[0].strip() == "#"
```

This must be checked **before** the generic `_add_table` call but **after** the `_is_action_table` check (which tests for 7 columns with "#" header). Place it in `_process_markdown_table` around line 637:

```python
if headers and rows:
    if self._is_action_table(raw_headers):
        self._add_action_cards(doc, headers, rows)
    elif self._is_roadmap_table(raw_headers):
        self._add_roadmap_cards(doc, headers, rows)
    else:
        self._add_table(doc, headers, rows)
```

### Rendering method

Add `_add_roadmap_cards` that renders each row as a single-cell bordered table (card) with 3 lines:

1. **Title line:** `"{number}. {action}"` — bold, 11pt, dark blue
2. **Detail line:** `"Tool: {tool}     Time: {time}"` — 10pt, gray, bold labels
3. **Action line:** `"What to do: {what_to_do}"` — 10pt, gray, bold label

Each card:
- Uses `Table Grid` style for the 1x1 table
- Has light blue background (`#F5F9FC`)
- Is center-aligned
- Has 10pt vertical gap between cards

Row data indices: `0=#`, `1=Action`, `2=Tool(Price)`, `3=Time`, `4=What To Do`

The current code already has `_add_roadmap_cards` at line 748. Verify it matches this spec.

---

## Change C: PDF — Detect and render roadmap cards

**File:** `strategy_factory/generation/pdf_generator.py`

### Detection method

Same logic as DocX — static method `_is_roadmap_table`:

```python
@staticmethod
def _is_roadmap_table(raw_headers: List[str]) -> bool:
    """Return True if this is the 5-column roadmap table."""
    return len(raw_headers) == 5 and raw_headers[0].strip() == "#"
```

Called in `_flush_table` before the generic table builder, after the action table check:

```python
if self._is_roadmap_table(raw_headers):
    card_flowables = self._build_roadmap_cards(table_lines)
    flowables.extend(card_flowables)
    return
```

### Rendering method

Add `_build_roadmap_cards` that builds ReportLab card flowables. Each card is a single-column `Table` with 3 rows:

1. Title: `"{number}. {action}"` — Helvetica-Bold, 11pt, dark blue
2. Detail: `"<b>Tool:</b> {tool}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Time:</b> {time}"` — 10pt, gray
3. Action: `"<b>What to do:</b> {what_do}"` — 10pt, gray

TableStyle per card:
- Background: `CARD_BG` (`#F5F9FC`)
- Box border: 0.75pt `CARD_BORDER`
- Line below title row: 0.5pt `CARD_BORDER`
- Padding: 10pt left/right, 8pt top/bottom (first/last rows), 3pt inner

Spacing: `_GAP_BEFORE_TABLE` (12pt) before each card, `_GAP_AFTER_TABLE` (14pt) after.

The current code already has `_build_roadmap_cards` at line 790. Verify it matches this spec.

---

## Verification

1. Run the pipeline (skip research since we're testing rendering, not content):
   ```bash
   cd /Users/jeff/ai-strategy-factory
   source venv/bin/activate
   python -m strategy_factory.main run "Angela Kim Couture" --skip-research
   ```

2. Open the generated files:
   - `output/angela-kim-couture/documents/final_strategy_report.docx`
   - `output/angela-kim-couture/documents/final_strategy_report.pdf`

3. Check: "Your Week-by-Week Plan" section — First 30 Days should appear as bordered cards with numbered titles, not nested bullet points.

4. Also check the intermediate markdown to verify the table format:
   - `output/angela-kim-couture/markdown/04_simple_roadmap.md` — should contain a 5-column table in the First 30 Days section with headers `| # | Action | Tool (Price) | Time | What To Do |`

---

## Existing Output for Comparison

The current (pre-fix) output lives at:
- `output/angela-kim-couture/documents/final_strategy_report.docx`
- `output/angela-kim-couture/documents/final_strategy_report.pdf`
- `output/angela-kim-couture/markdown/04_simple_roadmap.md`

Keep these to compare before/after.
