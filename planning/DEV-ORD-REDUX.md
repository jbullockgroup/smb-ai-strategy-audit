# DEV-ORD-REDUX: Fix Deliverable Sort Order & Strip Number Prefixes

## Problem

The webapp sorts markdown deliverables alphabetically by filename. Since files are named `01_tools_audit.md` through `08_executive_summary.md`, the executive summary always appears last in the sidebar. But the DOCX/PDF generators hardcode executive summary first. This display mismatch needs fixing.

## Why Not Renumber (the DELIV-ORDER.md plan)

The original plan renumbers every deliverable ID (01→08) across 7+ files, breaks backward compatibility with existing `output/` state files, and requires careful coordination — all to fix a display sort bug. This plan fixes the actual defect (the sort logic) in 2 files with zero breakage.

## Scope

| File | Change |
|------|--------|
| `strategy_factory/webapp.py` | Sort by config order + strip `^\d+_` from display name |
| `strategy_factory/server.py` | Same |

No other files change. No renumbering. No config changes. No generator changes. Existing output directories remain fully valid.

## Current Code

### webapp.py (lines 1346-1353)

```python
# Get markdown files
markdown_files = []
markdown_dir = output_dir / "markdown"
if markdown_dir.exists():
    for md_file in sorted(markdown_dir.glob("*.md")):
        markdown_files.append({
            "name": md_file.stem.replace("_", " ").replace("roi", "ROI").title().replace("Roi", "ROI"),
            "filename": md_file.name,
        })
```

### server.py (lines 34-42)

```python
# Read markdown files
markdown_files = []
if markdown_dir.exists():
    for md_file in sorted(markdown_dir.glob("*.md")):
        markdown_files.append({
            "name": md_file.stem.replace("_", " ").title(),
            "filename": md_file.name,
            "path": f"/markdown/{md_file.name}"
        })
```

### config.py (lines 51-119) — the source of truth for order

```python
DELIVERABLES = {
    "01_tools_audit":          {"name": "Where You Stand Today",          "format": "markdown", ...},
    "02_daily_pain_points":    {"name": "Where You're Losing Money",      "format": "markdown", ...},
    "03_action_plan":          {"name": "What To Do First",               "format": "markdown", ...},
    "04_simple_roadmap":       {"name": "Your Week-by-Week Plan",         "format": "markdown", ...},
    "05_readiness_assessment": {"name": "Your AI Readiness",              "format": "markdown", ...},
    "06_roi_snapshot":         {"name": "What It Costs & What You Save",  "format": "markdown", ...},
    "07_closing":              {"name": "Putting It All Together",        "format": "markdown", ...},
    "08_executive_summary":    {"name": "Executive Summary",              "format": "markdown", ...},
    "final_strategy_report":     {"name": "AI Strategy Report",       "format": "docx", ...},
    "final_strategy_report_pdf": {"name": "AI Strategy Report (PDF)", "format": "pdf",  ...},
}
```

Note: Python dicts preserve insertion order (3.7+), so the key order in `DELIVERABLES` defines the desired display order. Executive summary is currently last in this dict. **We need to move it to be first** — see Step 0 below.

## Implementation Steps

### Step 0: Move executive summary to first position in config.py

In `strategy_factory/config.py`, move the `"08_executive_summary"` entry to be the **first** key in the `DELIVERABLES` dict (before `"01_tools_audit"`). This is the only config change. The key name stays `08_executive_summary` — only its position in the dict changes.

This means the display order will be:
1. Executive Summary
2. Where You Stand Today (Tools Audit)
3. Where You're Losing Money (Daily Pain Points)
4. What To Do First (Action Plan)
5. Your Week-by-Week Plan (Simple Roadmap)
6. Your AI Readiness (Readiness Assessment)
7. What It Costs & What You Save (ROI Snapshot)
8. Putting It All Together (Closing)

### Step 1: Update webapp.py

At the top of the file, add `import re` if not already present.

Replace lines 1346-1353 with:

```python
# Get markdown files, ordered by DELIVERABLES config
markdown_files = []
markdown_dir = output_dir / "markdown"
if markdown_dir.exists():
    # Build display order from DELIVERABLES key order (markdown only)
    _md_order = [k for k, v in DELIVERABLES.items() if v.get("format") == "markdown"]
    md_map = {f.stem: f for f in markdown_dir.glob("*.md")}

    for deliverable_id in _md_order:
        if deliverable_id in md_map:
            md_file = md_map.pop(deliverable_id)
            display_name = re.sub(r'^\d+_', '', md_file.stem).replace("_", " ").replace("roi", "ROI").title().replace("Roi", "ROI")
            markdown_files.append({"name": display_name, "filename": md_file.name})

    # Catch any files not in DELIVERABLES (shouldn't happen, but safe)
    for md_file in sorted(md_map.values()):
        display_name = re.sub(r'^\d+_', '', md_file.stem).replace("_", " ").replace("roi", "ROI").title().replace("Roi", "ROI")
        markdown_files.append({"name": display_name, "filename": md_file.name})
```

The regex `re.sub(r'^\d+_', '', stem)` strips the leading `NN_` prefix:
- `08_executive_summary` → `executive_summary` → `"Executive Summary"`
- `01_tools_audit` → `tools_audit` → `"Tools Audit"`
- `06_roi_snapshot` → `roi_snapshot` → `"ROI Snapshot"`

The existing ROI casing fix (`.replace("roi", "ROI").title().replace("Roi", "ROI")`) is preserved.

### Step 2: Update server.py

Same pattern. Replace lines 34-42 with:

```python
# Read markdown files, ordered by DELIVERABLES config
markdown_files = []
if markdown_dir.exists():
    from strategy_factory.config import DELIVERABLES
    import re

    _md_order = [k for k, v in DELIVERABLES.items() if v.get("format") == "markdown"]
    md_map = {f.stem: f for f in markdown_dir.glob("*.md")}

    for deliverable_id in _md_order:
        if deliverable_id in md_map:
            md_file = md_map.pop(deliverable_id)
            display_name = re.sub(r'^\d+_', '', md_file.stem).replace("_", " ").title()
            markdown_files.append({
                "name": display_name,
                "filename": md_file.name,
                "path": f"/markdown/{md_file.name}"
            })

    for md_file in sorted(md_map.values()):
        display_name = re.sub(r'^\d+_', '', md_file.stem).replace("_", " ").title()
        markdown_files.append({
            "name": display_name,
            "filename": md_file.name,
            "path": f"/markdown/{md_file.name}"
        })
```

Note: server.py doesn't have the ROI special-casing that webapp.py has. Keep it consistent with its current simpler approach.

## What Does NOT Change

- Deliverable IDs (filenames on disk stay `01_tools_audit.md`, `08_executive_summary.md`, etc.)
- `generation/orchestrator.py` or `generation/markdown_generator.py` — file saving logic untouched
- `synthesis/` — no prompt or template changes
- Any `output/` directories — fully backward compatible
- The DOCX/PDF generation order — already correct (executive summary first)

## Verification

1. `python -m strategy_factory.webapp` → open a company results page
   - Sidebar shows deliverables in config key order with executive summary first
   - No number prefixes in display names (e.g. "Executive Summary" not "08 Executive Summary")
   - Click each link → content loads correctly
2. `python -m strategy_factory.server` → same checks for the static HTML output
3. `git diff` → only 3 files changed (config.py, webapp.py, server.py)
