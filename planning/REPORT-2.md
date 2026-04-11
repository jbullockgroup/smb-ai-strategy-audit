# Investigation Report: Healing Roots Design Audit Issues

## 1. Total Cost Display — Wrong Value

- **What's happening**: The UI shows `$0.0165` (the raw API cost from `state.json:total_cost`). The actual cost you're referring to is the **business investment cost** (~$190/mo or ~$14/mo however you're calculating it).
- **Root cause**: `webapp.py:1494` uses `${total_cost:.4f}` which pulls from `state.json:total_cost` — this is the **API processing cost** (Perplexity + Gemini), not the recommended tool investment. The `server.py:86` does the same thing.
- **Fix location**: The display formula at `webapp.py:1494` and `server.py:427` just needs to use the correct value. We need to clarify: should "Total Cost" show the API cost (currently $0.0165) or the recommended monthly tool investment from the ROI section?

## 2. Claude Max Overemphasis

- **Root cause**: `quick_wins.py:35-36` has Claude Pro and Claude Max as dedicated tool recommendations, and line 64 includes them in the "Use these tools" mandatory list. The Gemini model generating the content tends to lean into these recommendations.
- **Fix location**: `synthesis/prompts/quick_wins.py` lines 35-36 and 64 — need to rebalance the tool recommendations so Claude Max isn't the default/primary recommendation.

## 3. "(inferred)" in Tool Names

- **Root cause**: Not in the prompt itself — the prompt at `tech_inventory.py:30` says "infer based on industry and company size" but doesn't say to append "(inferred)". This is the AI generating that text on its own.
- **Fix location**: `synthesis/prompts/tech_inventory.py` — add a rule explicitly prohibiting "(inferred)" parentheses in tool names.

## 4. Bullet Points: Dashes vs. Bullets + Spacing

- **PDF**: `pdf_generator.py:614` renders bullets as `f"- {text}"` using a dash character instead of a proper bullet.
- **DOCX**: Uses `'List Bullet'` style which renders correctly in Word, but the source markdown uses dashes.
- **Spacing**: PDF bullet style (`pdf_generator.py:340-341`) has `spaceBefore=4, spaceAfter=3` — too tight. No line break before first item or after last item.
- **Fix locations**: `pdf_generator.py:614` (change dash to bullet character), style at lines 335-344 (increase spacing), and add gap logic before/after bullet groups.

## 5. "Your Top Actions This Month" Table Layout — Too Narrow Columns

- **PDF**: `pdf_generator.py:707` uses equal-width columns: `col_width = (6.5 * inch) / len(headers)`. With 7 columns, each gets ~0.93 inches — far too narrow for the text content.
- **DOCX**: `docx_generator.py:344` creates tables with `doc.add_table(rows=..., cols=...)` but sets no explicit column widths, leaving Word to auto-size (which results in tall, skinny cells).
- **Fix locations**: Both generators need either (a) weighted column widths based on content type, or (b) a different layout entirely (e.g., card-based layout, fewer columns, or a vertical list format).

## 6. "Already Paying" Column in Total Monthly Investment Table

- **Root cause**: Both `quick_wins.py:46-50` and `roi_calculator.py:14-18` include the "Already Paying?" column in their table templates.
- **Fix location**: Remove the "Already Paying?" column from both prompt templates.

## 7. Closing Section Missing from PDF

- **Root cause**: `pdf_generator.py:196-228` lists 7 sections but does NOT include `07_closing`. The section list stops at `06_roi_snapshot`.
- **Fix location**: Add the closing section after line 228 in `pdf_generator.py`.

## 8. Closing Section Missing from DOCX

- **Root cause**: Same issue. `docx_generator.py:94-119` lists 7 sections but does NOT include `07_closing`.
- **Fix location**: Add the closing section after line 119 in `docx_generator.py`.

## 9. DOCX: Excessive Blank Space in "What To Do First" Section

- **Root cause**: The section at `docx_generator.py:110-111` adds a heading "Priority Actions" then calls `_convert_markdown_to_docx()`. The markdown content starts with a paragraph, then a heading "Your Top Actions This Month", then a large table. The heading styles (lines 145-166) may have excessive `space_before`/`space_after`, and the table is likely being pushed to the next page due to not fitting on the current page.
- **Fix locations**: Check heading spacing in `docx_generator.py:145-166`, and potentially add table keep-with-next logic to prevent orphaned headings.

---

## Summary Priority Order

| # | Issue | Files to Change |
|---|-------|----------------|
| 1 | Total cost display | `webapp.py`, `server.py` |
| 2 | Claude Max overemphasis | `quick_wins.py` |
| 3 | "(inferred)" in tool names | `tech_inventory.py` |
| 4 | Bullet dashes + spacing (PDF) | `pdf_generator.py` |
| 5 | Table layout — narrow columns | `pdf_generator.py`, `docx_generator.py` |
| 6 | Remove "Already Paying" column | `quick_wins.py`, `roi_calculator.py` |
| 7 | Closing section missing (PDF) | `pdf_generator.py` |
| 8 | Closing section missing (DOCX) | `docx_generator.py` |
| 9 | DOCX blank space | `docx_generator.py` |

## Open Question

On issue #1: The $0.0165 shown in the UI is what the API calls actually cost to run the analysis. What should "Total Cost" represent — the API processing cost, the recommended monthly tool investment, or something else?
