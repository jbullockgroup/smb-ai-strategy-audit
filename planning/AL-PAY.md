# Fix #6: Remove "Already Paying?" Column

## Context

Issue #6 from `REPORT-2.md` (Healing Roots Design Audit). The "Already Paying?" column in the Total Monthly Investment table is unnecessary and clutters the output. Both prompt templates that generate this table need the column removed.

## Files to Edit

1. `strategy_factory/synthesis/prompts/quick_wins.py` — lines 46-51
2. `strategy_factory/synthesis/prompts/roi_calculator.py` — lines 14-19 and line 23

## Changes

### 1. `strategy_factory/synthesis/prompts/quick_wins.py`

Remove the `Already Paying?` column from the markdown table template at lines 46-51.

**Before (lines 46-51):**
```
| Tool | Monthly Cost | What It Does | Already Paying? |
|------|-------------|--------------|-----------------|
| [Tool 1] | $X/mo | [One sentence] | [Yes/No] |
| [Tool 2] | $X/mo | [One sentence] | [Yes/No] |
| [Tool 3] | $X/mo | [One sentence] | [Yes/No] |
| **Total new cost** | **$X/mo** | | |
```

**After:**
```
| Tool | Monthly Cost | What It Does |
|------|-------------|--------------|
| [Tool 1] | $X/mo | [One sentence] |
| [Tool 2] | $X/mo | [One sentence] |
| [Tool 3] | $X/mo | [One sentence] |
| **Total new cost** | **$X/mo** | |
```

### 2. `strategy_factory/synthesis/prompts/roi_calculator.py`

Same table column removal at lines 14-19.

**Before (lines 14-19):**
```
| Tool | Monthly Cost | What It Does | Already Paying? |
|------|-------------|--------------|-----------------|
| [Tool 1] | $X/mo | [One sentence] | [Yes/No] |
| [Tool 2] | $X/mo | [One sentence] | [Yes/No] |
| [Tool 3] | $X/mo | [One sentence] | [Yes/No] |
| **Total new cost** | **$X/mo** | | |
```

**After:**
```
| Tool | Monthly Cost | What It Does |
|------|-------------|--------------|
| [Tool 1] | $X/mo | [One sentence] |
| [Tool 2] | $X/mo | [One sentence] |
| [Tool 3] | $X/mo | [One sentence] |
| **Total new cost** | **$X/mo** | |
```

Also **remove line 23** which references the removed column:
```
Note which tools they may already be paying for that have AI features included (no new cost).
```

## Verification

- No other files in the codebase reference "Already Paying" (confirmed during exploration).
- Run a dry-run to confirm prompts render correctly:
  ```bash
  python -m strategy_factory.main run "Test Company" --dry-run
  ```
