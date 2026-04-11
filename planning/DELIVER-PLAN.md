# Fix Deliverable Tracking in Webapp Pipeline

## Context

The webapp's `run_pipeline()` function never updates the progress tracker after the generation phase completes. This causes:
- **Dashboard stuck at 75%** — `final_strategy_report` (DOCX) and `final_strategy_report_pdf` (PDF) are generated on disk but never marked complete in `state.json`
- **Phase statuses always "pending"** — `start_phase()` and `complete_phase()` are never called for any of the three phases

The CLI path (`main.py`) does all of this correctly. The fix is to mirror that logic into the webapp path.

A detailed writeup of the original bug is in `DELIVERABLE-ERROR.md` at the project root.

---

## Key Architecture Facts

- `strategy_factory/progress_tracker.py` — Has `start_phase()`, `complete_phase()`, `complete_deliverable()` methods already implemented and working.
- `strategy_factory/generation/orchestrator.py` — `generate_all()` returns a `GenerationResult` with a `deliverables` list (each item is `{"name": str, "path": str, "format": str}`).
- `strategy_factory/config.py` — `DELIVERABLES` dict defines all tracked deliverables. Currently has 8 entries (6 markdown + 1 DOCX + 1 PDF).
- `strategy_factory/main.py` — The CLI path already does everything correctly (lines 500-656). Use it as the reference implementation.
- `DELIVERABLES` is already imported at module level in `webapp.py` (line 34). No import changes needed.

---

## Changes Required

### Change 1: `strategy_factory/webapp.py` — `run_pipeline()` (starts line 1765)

Add phase tracking for all three phases. Insert `tracker.start_phase()` before each phase and `tracker.complete_phase()` after. Also iterate the generation result to mark deliverables complete.

**Research phase** (~line 1790):

After `tracker = ProgressTracker(...)` and before the research queue message, add:
```python
tracker.start_phase("research")
```

After `research_orchestrator.save_research_cache(...)` and before the research-complete queue message, add:
```python
tracker.complete_phase("research", f"Completed research for {company_name}")
```

**Synthesis phase** (~line 1824):

Before the synthesis queue message, add:
```python
tracker.start_phase("synthesis")
```

After the `for d_id, path in file_paths.items():` loop (line 1851) and before the synthesis-complete queue message, add:
```python
tracker.complete_phase("synthesis", f"Generated {len(file_paths)} markdown deliverables")
```

**Generation phase** (~line 1859):

Before the generation queue message, add:
```python
tracker.start_phase("generation")
```

After `result = generation_orchestrator.generate_all(...)` (line 1887) and before the generation-complete queue message (line 1889), add:
```python
# Mark generation deliverables complete in tracker
for deliverable in result.deliverables:
    d_name = deliverable["name"]
    d_path = deliverable["path"]
    for d_id, config in DELIVERABLES.items():
        if config.get("name") == d_name:
            tracker.complete_deliverable(d_id, d_path)
            break

tracker.complete_phase("generation", f"Generated {len(result.deliverables)} files")
```

This reuses the exact same pattern from `main.py:631-637`.

**Error handling**: Wrap each phase in try/except and call `tracker.fail_phase(phase_name, str(e))` on failure, matching the pattern in `main.py:653-656`.

### Change 2: `strategy_factory/config.py` — Add missing PPTX deliverable

The generation orchestrator produces `executive_summary_deck` (PPTX) but it's not in `DELIVERABLES`, so it's invisible to tracking. Add this entry to the `DELIVERABLES` dict:

```python
"executive_summary_deck": {
    "name": "Executive Summary Deck",
    "format": "pptx",
    "dependencies": ["ALL_MARKDOWN"],
    "tldr_guides": []
},
```

Place it after the `final_strategy_report_pdf` entry (currently the last item).

---

## Verification

1. Run a new analysis via the webapp
2. Open `output/{company-slug}/state.json` and confirm:
   - All deliverables in `"deliverables"` show `"status": "completed"`
   - All 3 entries in `"phases"` show `"status": "completed"`
3. Dashboard shows 100%
4. Confirm files exist on disk for all tracked deliverables
5. Test the CLI path (`python -m strategy_factory.main run "Test Co"`) still works correctly
