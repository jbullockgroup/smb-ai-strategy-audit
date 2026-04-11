# Fix: Research Cache Collision & Stale Docs

## Context

Three writers overwrite the same `output/{slug}/research_cache.json` with incompatible schemas:

1. `ProgressTracker.save_research_output()` writes `ResearchOutput.model_dump_json()`
2. `ResearchOrchestrator.save_research_cache()` writes a custom `{timestamp, info_tier, results}` dict
3. `PerplexityClient._save_cache()` writes a hash-keyed `{query → CacheEntry}` dict (because `main.py:493` and `webapp.py:2027` pass `cache_dir=Path(tracker.output_dir)`)

In `main.py:501-502` (and `webapp.py` mirror), `tracker.save_research_output()` runs first, then `orchestrator.save_research_cache()` immediately clobbers it. On resume, `ProgressTracker.load_research_output()` parses the orchestrator's schema as `ResearchOutput` → crash.

Separately, `CLAUDE.md` and `docs/ARCHITECTURE.md` still reference the deleted `model_selector.py` and `ResearchMode`.

## Key observation

`ResearchOrchestrator.load_research_cache()` is **dead code** — nothing in the codebase calls it. Its paired `save_research_cache()` is a write-only ghost. Removing both eliminates one of the three writers entirely rather than routing around it.

## Changes

### 1. Delete the dead orchestrator cache methods (high severity)

**`strategy_factory/research/orchestrator.py`**
- Delete `save_research_cache()` (around line 236)
- Delete `load_research_cache()` (around line 272)
- Delete the `from datetime import datetime` / `json` imports if they become unused

**`strategy_factory/main.py`**
- Line 502: Delete `orchestrator.save_research_cache(Path(tracker.output_dir))`

**`strategy_factory/webapp.py`**
- Line 2033: Delete `research_orchestrator.save_research_cache(Path(tracker.output_dir))`

After this, only two writers remain: `ProgressTracker` and `PerplexityClient`.

### 2. Separate the two remaining writers' files

`ProgressTracker` keeps `research_cache.json` (matches existing `state.research_cache_path` values in live `state.json` files, minimizing migration friction). `PerplexityClient` moves to a distinct file.

**`strategy_factory/research/perplexity_client.py`**
- Line 96: `_load_cache` — change `self.cache_dir / "research_cache.json"` to `self.cache_dir / "query_cache.json"`
- Line 124: `_save_cache` — same rename
- Line 366: `clear_cache` — same rename

No changes needed in `ProgressTracker` — it already owns `research_cache.json` and keeps owning it.

### 3. Clean up stale docs (low severity)

- **`CLAUDE.md`** (verify current line numbers before editing — the file was recently modified):
  - Remove `--mode comprehensive` from Quick Commands
  - Remove `model_selector.py` from Architecture tree
  - Remove `model_selector.py` from Key Files list
- **`docs/ARCHITECTURE.md`** (~line 205): Remove `+ResearchMode mode` reference

## Migration note

Existing `output/{slug}/research_cache.json` files may currently hold whichever schema was written last (typically the orchestrator's). After this change:

- `ProgressTracker` will try to parse any pre-existing `research_cache.json` as `ResearchOutput` on resume. If the file was left by the old orchestrator writer, that parse will fail.
- `PerplexityClient._load_cache` is wrapped in a try/except that swallows errors, so it degrades gracefully to an empty cache on its first run after the rename.

**Recommended action for existing outputs**: for any in-flight company whose research phase is marked complete in `state.json`, either re-run research from scratch or manually delete `output/{slug}/research_cache.json` before resuming. Document this in the PR description.

## Verification

1. **Grep `research_cache.json`** — should now only appear in `progress_tracker.py` (the one remaining writer) and any historical output dirs.
2. **Grep `query_cache.json`** — should only appear in `perplexity_client.py`.
3. **Grep `model_selector`** — should return zero hits in active source files (git history OK).
4. **Grep `save_research_cache`/`load_research_cache`** — should return zero hits.
5. **End-to-end resume test** (reproduces the original bug):
   - Pick a cheap test company and run `python -m strategy_factory.main run "Test Co" --dry-run` end-to-end, OR if dry-run short-circuits before saving, use a real but minimal run.
   - Interrupt after research phase completes (or let it finish naturally).
   - Run `python -m strategy_factory.main resume "Test Co"` and confirm `load_research_output()` succeeds without a Pydantic validation error.
6. **Perplexity cache reuse test**: Run the same company twice in a row; confirm the second run reports cache hits (proves `query_cache.json` is being read back correctly across processes).
