# REMOVE: Remove Comprehensive Mode

## Why This Change

Quick and Comprehensive modes produce identical results. Both run the same 11 queries through the same Perplexity Search API using the same Sonar Pro model. The `model` parameter is never sent to the API — it's only used for cost tracking metadata. `model_selector.py` (165 lines) is entirely dead code. All 11 query templates have `required_for_quick_mode=True`, so the mode filter in the orchestrator does nothing.

**Solution:** Remove mode selection entirely.

---

## Architecture (Current Pipeline, Unchanged)

```
Perplexity Search API → result_processor.py → ResearchOutput model
    → context_builder.py → Gemini API → 8 deliverables
```

The pipeline structure stays exactly the same. No new dependencies, no new APIs.

---

## Step 1.1 — Delete `strategy_factory/research/model_selector.py`

Delete the entire file. It's dead code — the model it selects is never sent to the Perplexity API.

**Why it's dead:** The Perplexity Search API (`client.search.create(**params)`) does not accept a `model` parameter. The model used is determined by the Perplexity API plan/tier, not per-request. The `model` parameter in `perplexity_client.py` is only used for cache keys (line 212), cost estimation (line 296), and metadata (line 303).

## Step 1.2 — Update `strategy_factory/research/__init__.py`

Remove:
- `from .model_selector import ModelSelector` (line 13)
- `"ModelSelector"` from `__all__` list (line 20)

## Step 1.3 — Update `strategy_factory/config.py`

Remove:
- `ResearchMode` enum class (lines 28-30)
- `RESEARCH_MODE_MODELS` dict (lines 32-39)

Keep:
- `PerplexityModel` enum — still used by `perplexity_client.py` for cost tracking
- `PERPLEXITY_COSTS` dict — still used for cost estimation

## Step 1.4 — Update `strategy_factory/models.py`

Remove:
- `ResearchMode` enum class (lines 21-24)
- `mode: ResearchMode` field from `CompanyInput` (line 52)
- `research_mode: ResearchMode` field from `ResearchOutput` (line 159)

Add backward compatibility for old `state.json` files:
```python
from pydantic import ConfigDict

class CompanyInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # ... rest of fields without mode

class ResearchOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # ... rest of fields without research_mode

class PipelineState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # ... rest unchanged
```

**Why:** Old `state.json` files contain `input_data.mode: "quick"` and `research_output.research_mode: "quick"`. Without `extra="ignore"`, loading these with Pydantic would raise validation errors.

## Step 1.5 — Update `strategy_factory/research/orchestrator.py`

Remove imports:
- `from ..config import ResearchMode` (keep `PerplexityModel`)
- `from .model_selector import ModelSelector`

In `__init__`:
- Remove `mode: ResearchMode = ResearchMode.QUICK` parameter
- Remove `self.mode = mode`
- Remove `self.model_selector = ModelSelector(mode=mode)`

In `_execute_phase`:
- Remove the mode-based query filter (lines 198-203):
  ```python
  # DELETE THIS BLOCK:
  if self.mode == ResearchMode.QUICK:
      queries = [
          q for q in queries
          if self.templates.get_template(q) and
          self.templates.get_template(q).required_for_quick_mode
      ]
  ```
  Since there's now only one mode, just run all queries in the phase list.

- Replace the model selection + search call. Change from:
  ```python
  selection = self.model_selector.select_model(
      template.category,
      info_tier=self.info_tier,
  )
  result = self.client.search(
      query=query,
      max_results=10,
      search_recency_filter=template.recency_filter,
      model=selection.model,
  )
  ```
  To:
  ```python
  result = self.client.search(
      query=query,
      max_results=10,
      search_recency_filter=template.recency_filter,
      model=PerplexityModel.SONAR,
  )
  ```

In `save_research_cache`:
- Remove `"mode": self.mode.value` from cache data dict (line ~260)

In `load_research_cache`:
- Remove `self.mode = ResearchMode(data["mode"])` (line ~302) — old cache files will still have this field, just ignore it

In `run_research` convenience function:
- Remove `mode: ResearchMode = ResearchMode.QUICK` parameter
- Remove `mode=mode` from `CompanyInput` construction
- Remove `mode=mode` from `ResearchOrchestrator` construction

## Step 1.6 — Update `strategy_factory/research/result_processor.py`

- Remove `from ..config import ResearchMode` import (line ~24)
- Remove `mode: ResearchMode` parameter from `build_research_output()` signature
- Remove `research_mode=mode` from `ResearchOutput()` constructor inside that method

## Step 1.7 — Update `strategy_factory/main.py`

- Remove `ResearchMode` from imports (line ~27)
- Remove `--mode` argument from the run subparser (lines ~103-109):
  ```python
  # DELETE:
  parser_run.add_argument(
      "--mode",
      choices=["quick", "comprehensive"],
      default="quick",
      help="Research mode: quick (~$0.05) or comprehensive (~$0.30-0.80)",
  )
  ```
- In `cmd_run`: Remove `mode = ResearchMode.QUICK if args.mode == "quick" ...` (line ~222), remove `mode=mode` passes
- In `_run_research`: Remove `mode: ResearchMode` parameter (line ~494), remove `mode=mode` from orchestrator construction
- In `cmd_resume`: Remove mode extraction and passes
- In `_dry_run`: Remove `mode: ResearchMode` parameter (line ~684), simplify cost estimates to single set
- Remove `--mode comprehensive` from help text / epilog examples

## Step 1.8 — Update `strategy_factory/webapp.py`

- Remove `ResearchMode` from import (line ~36)
- Remove Research Mode radio buttons from `HOME_CONTENT` template (lines ~953-967):
  ```html
  <!-- DELETE THIS ENTIRE BLOCK -->
  <label class="radio-option selected" id="mode-quick">
      <input type="radio" name="mode" value="quick" checked>
      Quick Research (~$0.02-0.15)
  </label>
  <label class="radio-option" id="mode-comprehensive">
      <input type="radio" name="mode" value="comprehensive">
      Comprehensive Research (~$0.31-0.90)
  </label>
  ```
- In `start_analysis()`: Remove `mode = request.form.get('mode', 'quick')` (line ~1297), remove `"mode": mode` from active_jobs dict
- In `run_pipeline()`: Remove `mode` parameter, remove `ResearchMode` logic, remove `mode=` from `CompanyInput` and `ResearchOrchestrator` construction
- Update thread start call to remove `mode` from args tuple

## Step 1.9 — Update `strategy_factory/research/query_templates.py`

- Remove `required_for_quick_mode: bool` field from `QueryTemplate` dataclass
- Remove `required_for_quick_mode=True` from all 11 template instantiations
- Remove `get_quick_mode_templates()` method
- Remove `get_comprehensive_templates()` method
- Simplify `render_all_queries()`: Remove `quick_mode` parameter, replace conditional with `templates = list(self.ALL_TEMPLATES.values())`
- Simplify `get_queries_by_priority()`: Remove `quick_mode` parameter and its pass-through

---

## Files Modified

| File | Change |
|------|--------|
| `strategy_factory/research/model_selector.py` | **DELETE** |
| `strategy_factory/research/__init__.py` | Remove ModelSelector export |
| `strategy_factory/config.py` | Remove ResearchMode enum, RESEARCH_MODE_MODELS dict |
| `strategy_factory/models.py` | Remove ResearchMode enum, remove mode fields, add ConfigDict(extra="ignore") |
| `strategy_factory/research/orchestrator.py` | Remove mode params, remove ModelSelector, hardcode Sonar model |
| `strategy_factory/research/query_templates.py` | Remove required_for_quick_mode field and mode methods |
| `strategy_factory/research/result_processor.py` | Remove mode param |
| `strategy_factory/main.py` | Remove --mode flag, remove mode logic |
| `strategy_factory/webapp.py` | Remove Research Mode UI, remove mode params |
| `strategy_factory/progress_tracker.py` | No changes needed (ConfigDict handles backward compat) |
| `strategy_factory/server.py` | No changes needed (static file server, no mode refs) |

**Note:** `COMP-MODE-B.md` (the comprehensive mode implementation spec) can be deleted or kept as historical reference — it is no longer relevant.

---

## Verification

1. **Dead code removal check:**
   ```bash
   grep -r "ResearchMode\|ModelSelector\|model_selector\|required_for_quick_mode" strategy_factory/
   ```
   Should return zero results in .py files.

2. **Dry run:**
   ```bash
   python -m strategy_factory.main run "Test Company" --dry-run
   ```
   Should work without `--mode` flag.

3. **Backward compatibility:** Resume an existing company with old `state.json` containing `mode` field — should load without error (ConfigDict extra="ignore" handles this).
