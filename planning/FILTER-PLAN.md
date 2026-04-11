# Fix: `_fix_malformed_tables` Destroying Valid Table Rows

## Problem

The `_fix_malformed_tables` function is **eating every other data row** in generated markdown tables. This produces output where table rows alternate between real data and `| --- | --- | --- |` placeholders.

**Root cause chain**:
1. Gemini outputs complete tables with all rows filled in — every cell has data.
2. `_fix_malformed_tables` walks line-by-line looking for table rows. Any line with multiple `|` characters that isn't already a separator gets treated as a "header candidate" (line 233 in gemini_client.py).
3. For each "header candidate," it checks if the next line is a malformed separator using: `len(next_line) > 200 and '-' in next_line` (line 244).
4. A data row in a 7-column table is easily 200+ characters. Data rows frequently contain dashes — prices like `$50-300/mo`, time ranges like `1-2 weeks`, hyphenated tool names. So a legitimate data row passes both checks.
5. When it matches, the function replaces that data row with `| --- | --- | --- | ...` (line 246) — permanently destroying the content.

**Secondary bug**: Lines 252-255 silently drop any line over 500 characters, which can eat legitimate table rows or paragraph content.

**Evidence in output files**:
- `01_tools_audit.md` — 4-column tables with alternating filled/dashed rows
- `03_action_plan.md` — 7-column tables with the same pattern

## Files to Modify

| File | Lines | What |
|------|-------|------|
| `strategy_factory/synthesis/gemini_client.py` | 222-260 | Primary fix |
| `strategy_factory/webapp.py` | 1389-1429 | Same function, same fix |

Both files contain independent copies of `_fix_malformed_tables` with the same bug. Both must be fixed.

## Current Buggy Code

**`gemini_client.py` lines 222-260:**
```python
def _fix_malformed_tables(self, content: str) -> str:
    """Fix malformed markdown tables with overly long separator rows."""
    import re
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this looks like a table header row (has multiple | chars)
        if line.count('|') >= 2 and not re.match(r'^\s*\|[\s\-:]+\|', line):
            # This might be a header row, count columns
            cols = [c.strip() for c in line.split('|')]
            cols = [c for c in cols if c]
            num_cols = len(cols)

            if num_cols >= 2:
                # Check if next line is a malformed separator
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # If separator line is too long (malformed), fix it
                    if len(next_line) > 200 and '-' in next_line:  # <-- BUG: matches data rows
                        # Create a proper separator
                        separator = '|' + '|'.join([' --- ' for _ in range(num_cols)]) + '|'
                        fixed_lines.append(line)
                        fixed_lines.append(separator)
                        i += 2
                        continue

        # Skip extremely long lines (likely malformed)
        if len(line) > 500:  # <-- BUG: silently drops legitimate long lines
            i += 1
            continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)
```

**`webapp.py` lines 1389-1429** — same logic, slightly different order (500-char check comes first), adds a "Table data not available" note after replacing rows.

## Fix

### 1. Replace the heuristic with a character-composition check

A real separator row (even a malformed/long one) is composed almost entirely of `|`, `-`, `:`, and spaces. A data row, no matter how long or dash-filled, contains letters, digits, and other characters.

Replace the condition `len(next_line) > 200 and '-' in next_line` with a function that checks character composition:

```python
def _is_separator_row(line: str) -> bool:
    """Check if a line is a (possibly malformed) table separator row.

    A separator row should be comprised almost entirely of |, -, :, and spaces.
    Data rows contain letters, digits, and punctuation that aren't separator characters.
    """
    stripped = line.strip()
    if not stripped:
        return False
    allowed = set('|-: ')
    non_allowed = sum(1 for c in stripped if c not in allowed)
    # Allow up to 5% other characters (e.g., from encoding artifacts)
    return non_allowed / len(stripped) < 0.05 and '-' in stripped and '|' in stripped
```

Then use it in place of the old check:
```python
if i + 1 < len(lines) and _is_separator_row(lines[i + 1]):
```

### 2. Remove the 500-char line deletion

Remove the block that silently skips lines over 500 characters:
```python
# DELETE THIS:
if len(line) > 500:
    i += 1
    continue
```

The separator fix above handles the actual problem. There is no justification for blanket deletion of long lines — it's just destroying content.

### 3. Apply to both files

**`gemini_client.py`**: Add `_is_separator_row` as a module-level helper, apply fixes 1 and 2.

**`webapp.py`**: Same separator check fix, remove the 500-char block. Keep the `*Table data not available in source document.*` note that the webapp version adds after replacing — that's a webapp-specific display concern.

## How to Verify

1. **Syntax check**: `python -m py_compile strategy_factory/synthesis/gemini_client.py` and same for webapp.py
2. **Dry run**: `python -m strategy_factory.main run "Test Company" --dry-run` — confirm no import errors
3. **Full pipeline test**: Run against a real company and inspect the generated markdown files in `output/`. Tables in `01_tools_audit.md` (4-column) and `03_action_plan.md` (7-column) should have all data rows intact with no `| --- | --- |` placeholders replacing actual data.
