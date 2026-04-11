# DELIV-ORDER: Renumber Deliverable IDs to Match Display Order

## Why

The webapp sorts markdown files alphabetically by filename, while the PDF/DOCX use hardcoded section order. This creates a mismatch: the webapp shows executive summary last (`08_`) but the PDF shows it first. Renumbering the deliverable IDs so the numeric prefix matches the desired display order makes both systems consistent — alphabetical sort in the webapp will naturally produce the correct reading order.

## ID Mapping (Old → New)

| Old ID                     | New ID                     | Display Name               |
|----------------------------|----------------------------|----------------------------|
| `08_executive_summary`     | `01_executive_summary`     | Executive Summary          |
| `01_tools_audit`           | `02_tools_audit`           | Where You Stand Today      |
| `02_daily_pain_points`     | `03_daily_pain_points`     | Where You're Losing Money  |
| `05_readiness_assessment`  | `04_readiness_assessment`  | Your AI Readiness          |
| `03_action_plan`           | `05_action_plan`           | What To Do First           |
| `04_simple_roadmap`        | `06_simple_roadmap`        | Your Week-by-Week Plan     |
| `06_roi_snapshot`          | `07_roi_snapshot`          | What It Costs & What You Save |
| `07_closing`               | `08_closing`               | Putting It All Together    |

`final_strategy_report` and `final_strategy_report_pdf` stay unchanged — they are not markdown deliverables.

---

## Files to Modify (7 files)

### 1. `strategy_factory/config.py` (lines 51–119)

The `DELIVERABLES` dict. Rename all markdown deliverable keys and update every `dependencies` list to use the new IDs.

**New DELIVERABLES dict** (only markdown keys shown; `final_strategy_report` and `final_strategy_report_pdf` stay as-is):

```python
DELIVERABLES = {
    "01_executive_summary": {
        "name": "Executive Summary",
        "format": "markdown",
        "dependencies": [
            "02_tools_audit", "03_daily_pain_points", "04_readiness_assessment",
            "05_action_plan", "06_simple_roadmap", "07_roi_snapshot",
            "08_closing"
        ],
        "tldr_guides": []
    },
    "02_tools_audit": {
        "name": "Where You Stand Today",
        "format": "markdown",
        "dependencies": [],
        "tldr_guides": ["smb-ai-playbook.md"]
    },
    "03_daily_pain_points": {
        "name": "Where You're Losing Money",
        "format": "markdown",
        "dependencies": [],
        "tldr_guides": ["smb-ai-value-playbook.md"]
    },
    "04_readiness_assessment": {
        "name": "Your AI Readiness",
        "format": "markdown",
        "dependencies": ["02_tools_audit", "03_daily_pain_points"],
        "tldr_guides": ["smb-ai-playbook.md", "smb-ai-value-playbook.md"]
    },
    "05_action_plan": {
        "name": "What To Do First",
        "format": "markdown",
        "dependencies": ["03_daily_pain_points"],
        "tldr_guides": ["ai-implementation-steps-smb.md"]
    },
    "06_simple_roadmap": {
        "name": "Your Week-by-Week Plan",
        "format": "markdown",
        "dependencies": ["05_action_plan"],
        "tldr_guides": ["ai-implementation-steps-smb.md"]
    },
    "07_roi_snapshot": {
        "name": "What It Costs & What You Save",
        "format": "markdown",
        "dependencies": ["05_action_plan"],
        "tldr_guides": ["smb-ai-value-playbook.md"]
    },
    "08_closing": {
        "name": "Putting It All Together",
        "format": "markdown",
        "dependencies": [
            "02_tools_audit", "03_daily_pain_points", "04_readiness_assessment",
            "05_action_plan", "06_simple_roadmap", "07_roi_snapshot"
        ],
        "tldr_guides": []
    },
    # final_strategy_report and final_strategy_report_pdf remain unchanged
}
```

### 2. `strategy_factory/synthesis/orchestrator.py` (lines 40–46)

Update `GENERATION_ORDER` to use new IDs. The generation *sequence* stays the same (dependency-first), just the IDs change:

```python
GENERATION_ORDER = [
    ["02_tools_audit", "03_daily_pain_points"],
    ["04_readiness_assessment", "05_action_plan"],
    ["06_simple_roadmap", "07_roi_snapshot"],
    ["08_closing"],
    ["01_executive_summary"],
]
```

### 3. `strategy_factory/synthesis/prompts/__init__.py` (lines 17–26)

Update all keys in the `PROMPTS` dict. The prompt module imports at the top stay the same — only the dict keys change:

```python
PROMPTS = {
    "01_executive_summary": EXECUTIVE_SUMMARY_PROMPT,
    "02_tools_audit": TECH_INVENTORY_PROMPT,
    "03_daily_pain_points": PAIN_POINTS_PROMPT,
    "04_readiness_assessment": MATURITY_ASSESSMENT_PROMPT,
    "05_action_plan": QUICK_WINS_PROMPT,
    "06_simple_roadmap": ROADMAP_PROMPT,
    "07_roi_snapshot": ROI_CALCULATOR_PROMPT,
    "08_closing": CLOSING_PROMPT,
}
```

### 4. `strategy_factory/generation/docx_generator.py` (lines 94–119)

In `generate_strategy_report()`, update every `_add_subsection_from_deliverable` call's deliverable_id argument:

| Line | Old ID in call | New ID in call |
|------|----------------|----------------|
| 95   | `"08_executive_summary"` | `"01_executive_summary"` |
| 99   | `"01_tools_audit"` | `"02_tools_audit"` |
| 103  | `"02_daily_pain_points"` | `"03_daily_pain_points"` |
| 107  | `"05_readiness_assessment"` | `"04_readiness_assessment"` |
| 111  | `"03_action_plan"` | `"05_action_plan"` |
| 115  | `"04_simple_roadmap"` | `"06_simple_roadmap"` |
| 119  | `"06_roi_snapshot"` | `"07_roi_snapshot"` |

### 5. `strategy_factory/generation/pdf_generator.py` (lines 196–228)

In `generate_strategy_report()`, update every `_build_from_deliverable` call's deliverable_id argument — same mapping as docx_generator:

| Line | Old ID in call | New ID in call |
|------|----------------|----------------|
| 198  | `"08_executive_summary"` | `"01_executive_summary"` |
| 203  | `"01_tools_audit"` | `"02_tools_audit"` |
| 208  | `"02_daily_pain_points"` | `"03_daily_pain_points"` |
| 213  | `"05_readiness_assessment"` | `"04_readiness_assessment"` |
| 218  | `"03_action_plan"` | `"05_action_plan"` |
| 223  | `"04_simple_roadmap"` | `"06_simple_roadmap"` |
| 228  | `"06_roi_snapshot"` | `"07_roi_snapshot"` |

### 6. `CLAUDE.md`

Update the Deliverables table near the bottom of the file to reflect the new numbering:

```markdown
| ID | Name | Format | Dependencies |
|----|------|--------|-------------|
| 01_executive_summary | Executive Summary | markdown | 02–08 |
| 02_tools_audit | Where You Stand Today | markdown | — |
| 03_daily_pain_points | Where You're Losing Money | markdown | — |
| 04_readiness_assessment | Your AI Readiness | markdown | 02, 03 |
| 05_action_plan | What To Do First | markdown | 03 |
| 06_simple_roadmap | Your Week-by-Week Plan | markdown | 05 |
| 07_roi_snapshot | What It Costs & What You Save | markdown | 05 |
| 08_closing | Putting It All Together | markdown | 02–07 |
| final_strategy_report | AI Strategy Report | docx | ALL_MARKDOWN |
| final_strategy_report_pdf | AI Strategy Report (PDF) | pdf | ALL_MARKDOWN |
```

### 7. `README.md`

Update the deliverables table if one exists (grep showed no matches for old IDs, so this may not need changes — verify visually).

---

## Files NOT Modified

- **Prompt template files** (`tech_inventory.py`, `pain_points.py`, `quick_wins.py`, `roadmap.py`, `maturity_assessment.py`, `roi_calculator.py`, `closing.py`, `executive_summary.py`) — imported by Python module name, not by deliverable ID.
- **`webapp.py`** — uses `sorted(markdown_dir.glob("*.md"))` on line 1349. The new filenames sort correctly by default. No code change needed.
- **`server.py`** — same alphabetical sort pattern. No code change needed.
- **`pptx_generator.py`** — confirmed via grep: does not reference any deliverable IDs.
- **`progress_tracker.py`** — confirmed via grep: does not hardcode deliverable IDs.
- **`generation/orchestrator.py`** — uses `DELIVERABLES` from config dynamically, so config changes propagate automatically.

---

## Execution Order

Do these changes in this order to avoid broken intermediate states:

1. **config.py** first (source of truth for all IDs and dependencies)
2. **prompts/__init__.py** (maps IDs to prompt modules)
3. **synthesis/orchestrator.py** (GENERATION_ORDER)
4. **docx_generator.py** (hardcoded ID references)
5. **pdf_generator.py** (hardcoded ID references)
6. **CLAUDE.md** and **README.md** (documentation)

---

## Verification

After all edits, run these checks:

```bash
# 1. Config loads without import errors
python -c "from strategy_factory.config import DELIVERABLES; print('Config OK:', list(DELIVERABLES.keys()))"

# 2. Prompts map matches config keys
python -c "
from strategy_factory.config import DELIVERABLES
from strategy_factory.synthesis.prompts import PROMPTS
md_ids = {k for k,v in DELIVERABLES.items() if v.get('format') == 'markdown'}
assert set(PROMPTS.keys()) == md_ids, f'Mismatch: {set(PROMPTS.keys()) ^ md_ids}'
print('Prompt mapping OK')
"

# 3. All dependency references point to valid IDs
python -c "
from strategy_factory.config import DELIVERABLES
for did, cfg in DELIVERABLES.items():
    for dep in cfg.get('dependencies', []):
        if dep == 'ALL_MARKDOWN': continue
        assert dep in DELIVERABLES, f'{did} references missing dep {dep}'
print('Dependencies OK')
"

# 4. Dry run
python -m strategy_factory.main run "Test Company" --dry-run
```

---

## Implementation Notes

- The **display order** (filenames) is: 01 executive summary → 02 tools audit → 03 pain points → 04 readiness → 05 action plan → 06 roadmap → 07 ROI → 08 closing.
- The **generation order** is different: executive summary is generated *last* because it depends on everything else. This is handled by `GENERATION_ORDER` in the synthesis orchestrator, not by the filename numbering.
- Existing output files in `output/` directories will have the old filenames. These are not migrated — they'll be overwritten on the next run. If you need backward compatibility with existing state.json files, that would require a migration step not covered here.
