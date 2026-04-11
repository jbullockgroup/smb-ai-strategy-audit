# Fix PPTX Generation & Mermaid Rendering

## Context

Running the pipeline for "Black Mountain Yarn Shop" produced:
- **No PowerPoint files** — the `presentations/` directory is empty
- **Placeholder mermaid diagrams** — "mmdc not available, creating placeholder" logged 5 times

Both errors are silently swallowed, so the pipeline reports completion with no visible indication of failure.

## Root Causes

### 1. PPTX: `IndexError: list index out of range` in `_add_table_to_slide`

**File:** `strategy_factory/generation/pptx_generator.py:601`

In `_add_roi_slide`, the ROI table from markdown has 5 columns (`Category | Year 1 | Year 2 | Year 3 | Total`), but the code truncates headers to 4 with `table["headers"][:4]` while keeping rows at full width with `table["rows"][:5]`. The table is created with 4 columns, then the code tries to write 5-column row data into it → `IndexError`.

Both `generate_executive_summary` and `generate_full_findings` hit this same crash, so zero PPTX files are produced. The `_generate_presentations` method catches the exception silently and records it, but the error is never printed to console.

### 2. Mermaid: `mmdc` CLI tool not installed

**File:** `strategy_factory/generation/mermaid_renderer.py:68-70`

`shutil.which("mmdc")` returns `None` because `@mermaid-js/mermaid-cli` is not installed globally. The renderer gracefully falls back to placeholder PNG images (via PIL) and `.mmd` text files.

## Fix Plan

### Fix 1: PPTX table column mismatch (pptx_generator.py)

**File:** `strategy_factory/generation/pptx_generator.py`

**Change at line ~601 (`_add_roi_slide`):** When passing extracted table data to `_add_table_to_slide`, also truncate each row to match the header count:

```python
# Before
self._add_table_to_slide(
    slide,
    table["headers"][:4],
    table["rows"][:5],
)

# After
headers = table["headers"][:4]
rows = [row[:len(headers)] for row in table["rows"][:5]]
self._add_table_to_slide(slide, headers, rows)
```

**Also harden `_add_table_to_slide` (line ~384-397):** Add a guard so mismatched row data never causes an IndexError regardless of caller:

```python
# In the data rows loop, truncate/pad each row to match num_cols
for row_idx, row_data in enumerate(rows):
    for col_idx in range(num_cols):
        cell = table.cell(row_idx + 1, col_idx)
        cell.text = str(row_data[col_idx]) if col_idx < len(row_data) else ""
```

### Fix 2: Install mermaid-cli for diagram rendering

Install `@mermaid-js/mermaid-cli` globally via npm so `mmdc` is available in PATH:

```bash
npm install -g @mermaid-js/mermaid-cli
```

This is the standard approach per the project's own documentation (the code is already written to use mmdc, it just needs to be installed).

## Files to Modify

1. `strategy_factory/generation/pptx_generator.py` — Fix `_add_roi_slide` and harden `_add_table_to_slide`

## Verification

1. Re-run the generation with the existing output data:
   ```bash
   python -c "..." # (reproduce script from investigation)
   ```
2. Confirm `presentations/executive_summary.pptx` and `presentations/full_findings.pptx` are created
3. After installing mmdc, confirm mermaid diagrams render as actual PNGs (not placeholders)
