# PPTX Removal — Implementation Handoff

## What & Why

Remove all PowerPoint (PPTX) generation functionality. The app currently generates two PPTX decks (`executive_summary_deck` and `full_findings_deck`) as part of the generation pipeline. After this change, the output will be limited to markdown files, a DOCX strategy report, and a PDF strategy report.

This also fixes the generation progress percentage shown in the sidebar company cards — the total deliverable count currently includes 2 PPTX items, so the percentage will be wrong once they're removed unless the config is updated.

## Progress Percentage — Key Detail

The sidebar progress percentage is calculated in `strategy_factory/progress_tracker.py` → `get_progress_summary()`:

```python
progress_percent = (completed / total_deliverables * 100)
```

Where `total_deliverables = len(self.state.deliverables)` and deliverables are initialized from `config.py:DELIVERABLES`. **No formula change is needed.** Simply removing the 2 PPTX entries from `DELIVERABLES` in `config.py` drops the total from 12 to 10, and the percentage auto-corrects.

Note: Existing `state.json` files for completed companies may still contain the PPTX deliverable entries. Those are historical and won't break anything — they'll just show a slightly off percentage for old runs. New runs will be correct.

---

## Files to Change (in recommended order)

### 1. DELETE `strategy_factory/generation/pptx_generator.py`
Remove the entire file (~1,009 lines).

### 2. EDIT `strategy_factory/config.py`
Remove two deliverable entries from `DELIVERABLES` dict (lines 116-127):
```python
    "executive_summary_deck": {
        "name": "Executive Summary Deck",
        "format": "pptx",
        "dependencies": ["ALL_MARKDOWN"],
        "tldr_guides": []
    },
    "full_findings_deck": {
        "name": "Full Findings Deck",
        "format": "pptx",
        "dependencies": ["ALL_MARKDOWN"],
        "tldr_guides": []
    },
```

### 3. EDIT `strategy_factory/generation/__init__.py`
- Line 9: Remove `from .pptx_generator import PowerPointGenerator, generate_executive_deck, generate_full_findings_deck`
- Lines 18-21: Remove `"PowerPointGenerator"`, `"generate_executive_deck"`, `"generate_full_findings_deck"` from `__all__`
- Update module docstring (line 2): remove "PPTX" mention

### 4. EDIT `strategy_factory/generation/orchestrator.py`
This file has the most PPTX references. Changes:
- Line 21: Remove `from .pptx_generator import PowerPointGenerator`
- Line 55: Remove `self.pptx_gen = PowerPointGenerator(output_dir=self.output_dir)`
- Line 83: Change `total_steps = 5` → `total_steps = 3` (was: markdown, docx, pdf, exec pptx, full pptx; now: markdown, docx, pdf)
- Lines 110-114: Remove Step 4 (executive summary PPTX generation)
- Lines 116-129: Remove Step 5 (full findings PPTX generation)
- Lines 169-191: Remove entire `_generate_presentations` method
- Line 250: Remove `".pptx": "pptx",` from format_map
- Lines 322-357 in `generate_outputs_from_synthesis`: Remove `skip_pptx` parameter, its docstring line, and the PPTX generation block
- Update class/module docstrings to remove PPTX mentions

### 5. EDIT `strategy_factory/models.py`
- Line 180: Change `format: str  # markdown, pptx, docx` → `format: str  # markdown, docx, pdf`

### 6. EDIT `strategy_factory/progress_tracker.py`
- Line 154: Remove `self.output_dir / "presentations",` from `_ensure_directories`

### 7. EDIT `strategy_factory/server.py`
- Lines 48-57: Remove presentations discovery block (the `presentations = []` / `pres_dir` / `pptx` glob)
- Lines 452-457: Remove presentations sidebar section (`if presentations:` block)
- Line 472: Update welcome text to remove "presentations and" or "presentations" mention

### 8. EDIT `strategy_factory/webapp.py`
- Lines 1435-1444: Remove presentations discovery block
- Line 1452: Remove `presentations=presentations` from `render_results_page()` call
- Line 1557: Remove `presentations=None` parameter from `render_results_page()` signature
- Lines 1590-1594: Remove the `if presentations:` rendering block

### 9. EDIT `strategy_factory/main.py`
- Lines 776-780: Remove presentations listing block (`pres_dir` / `pptx_files` / print)
- Line 123: Update `--skip-generation` help text from `"Skip final document generation (PPTX, DOCX)"` → `"Skip final document generation (DOCX, PDF)"`

### 10. EDIT `requirements.txt`
- Remove the line `python-pptx>=0.6.23`

### 11. EDIT `README.md`
- Remove PPTX-related lines (around lines 253, 439, 545)

### 12. EDIT `docs/ARCHITECTURE.md` (if it exists and has PPTX refs)
- Remove PPTX/presentation references

### 13. EDIT `strategy_factory/generation/markdown_generator.py`
- Line 138: Update docstring `"Useful for building presentations and reports."` → `"Useful for building reports."` (inside `extract_sections` method)

---

## Files NOT to Change
- `output/*/state.json` — historical data, leave as-is
- `output/*/research_cache.json` — historical data, leave as-is
- `.claude/document-creation-skills.md` — general reference doc, not project-specific

## Verification Steps
1. `python -c "from strategy_factory.config import DELIVERABLES; print(len(DELIVERABLES))"` → should print `10`
2. `python -c "from strategy_factory.generation import *"` → should not error
3. `python -m strategy_factory.main --help` → should work, no PPTX mentions
4. `python -c "from strategy_factory.generation.orchestrator import GenerationOrchestrator"` → should not error
5. Start webapp (`python -m strategy_factory.webapp`) and verify no PPTX/presentation references in UI
