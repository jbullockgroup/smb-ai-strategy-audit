# TRACK: Fix Cost Estimation Accuracy

## Context

The UI cost estimates are significantly off from actual API billing. Two sample runs confirmed the problem:

| Company | Stored Total | Actual Total | Perplexity (actual) | Gemini (actual) |
|---|---|---|---|---|
| Angela Kim Couture | $0.0859 | $0.13 | $0.05 | $0.08 |
| Healing Roots Design | $0.0165 | $0.14 | $0.04 | $0.10 |

Three root causes:
1. **Webapp doesn't track Gemini synthesis costs** — `webapp.py:run_pipeline()` never calls `tracker.add_cost()` for synthesis, so Gemini always shows $0.00
2. **Gemini uses char/4 token estimate** — the API response includes actual token counts (`usage_metadata.prompt_token_count`, `usage_metadata.candidates_token_count`) but the code ignores them
3. **Perplexity Search API returns no usage data** — `SearchCreateResponse` only has `id`, `results`, `server_time`. No token counts. The text-based estimation is unreliable (over-counted by 72% for one run, under-counted by 59% for another). The Perplexity Chat API does have `UsageInfo` with actual costs, but we are NOT switching APIs.

Goal: accurate costs within ~10% of actual, rounded to nearest cent.

---

## Changes (4 edits across 5 files)

### Change 1: Gemini — use actual `usage_metadata` from API response

**File:** `strategy_factory/synthesis/gemini_client.py`

**Location:** `generate()` method, lines 146-154

**Current code:**
```python
# Estimate tokens
input_tokens = self._count_tokens(prompt)
if system_instruction:
    input_tokens += self._count_tokens(system_instruction)
output_tokens = self._count_tokens(content)

# Calculate cost
cost = self._estimate_cost(input_tokens, output_tokens)
```

**Replace with:**
```python
# Use actual token counts from API response
um = response.usage_metadata
input_tokens = getattr(um, 'prompt_token_count', None) or self._count_tokens(prompt)
output_tokens = getattr(um, 'candidates_token_count', None) or self._count_tokens(content)

# Calculate cost
cost = self._estimate_cost(input_tokens, output_tokens)
```

**Why:** The Gemini API response object has `usage_metadata` with `prompt_token_count` and `candidates_token_count` — these are real token counts, not estimates. Keeps `len(text)//4` as fallback if metadata unavailable.

---

### Change 2: Webapp — track Gemini synthesis costs

**File:** `strategy_factory/webapp.py`

**Location:** `run_pipeline()` function, after line 2084

**Insert between** `synthesis_output = synthesis_orchestrator.synthesize(...)` (line 2084) and `file_paths = synthesis_orchestrator.save_deliverables(...)` (line 2085):

```python
        # Track synthesis costs
        synthesis_cost = synthesis_orchestrator.get_cost_summary()["total_cost"]
        if synthesis_cost > 0:
            tracker.add_cost(synthesis_cost, "synthesis")
```

**Why:** The CLI path (`main.py:581`) already calls `tracker.add_cost(cost_summary["total_cost"], "synthesis")`, but the webapp pipeline was missing this call entirely. This is why both sample runs showed $0.00 for Gemini.

---

### Change 3: Perplexity — switch to fixed per-query rate

**File A:** `strategy_factory/config.py`

**Location:** After the `PERPLEXITY_COSTS` dict (after line 48), add:

```python
# Calibrated per-query cost estimates (based on actual billing data, April 2026)
PERPLEXITY_QUERY_COSTS = {
    PerplexityModel.SONAR: 0.0045,
    PerplexityModel.SONAR_PRO: 0.025,
    PerplexityModel.SONAR_REASONING: 0.008,
    PerplexityModel.SONAR_REASONING_PRO: 0.015,
    PerplexityModel.SONAR_DEEP_RESEARCH: 0.015,
}
```

**Calibration basis:**
- Sonar: $0.0045/query (average of $0.005 actual Angela Kim / $0.004 actual Healing Roots, 11 queries each)
- Other models: proportionally scaled from token pricing ratios, erring slightly high per user preference

**File B:** `strategy_factory/research/perplexity_client.py`

**Location:** `_estimate_cost()` method, lines 157-169

**Current code:**
```python
def _estimate_cost(
    self,
    model: PerplexityModel,
    query_text: str = "",
    response_text: str = "",
) -> float:
    """Estimate cost from actual text content."""
    input_tokens = len(query_text) / 4
    output_tokens = len(response_text) / 4
    input_cost, output_cost = PERPLEXITY_COSTS.get(
        model, (0.001, 0.001)
    )
    return (input_tokens / 1000 * input_cost) + (output_tokens / 1000 * output_cost)
```

**Replace with:**
```python
def _estimate_cost(
    self,
    model: PerplexityModel,
    query_text: str = "",
    response_text: str = "",
) -> float:
    """Estimate cost using calibrated per-query rate."""
    from ..config import PERPLEXITY_QUERY_COSTS
    return PERPLEXITY_QUERY_COSTS.get(model, 0.0045)
```

**Why:** The Perplexity Search API (`client.search.create()`) returns `SearchCreateResponse` with only `id`, `results`, `server_time` — no token counts or cost data. Text-based estimation was unreliable. Fixed per-query rate based on actual billing is more accurate and predictable.

---

### Change 4: Round cost display to nearest cent

**File A:** `strategy_factory/webapp.py`
- Line 427: change `${total_cost:.4f}` to `${total_cost:.2f}`
- Line 1572: change `${total_cost:.4f}` to `${total_cost:.2f}`

**File B:** `strategy_factory/server.py`
- Line 427: change `${total_cost:.4f}` to `${total_cost:.2f}`

---

## Files Modified (summary)

| File | What changes |
|---|---|
| `strategy_factory/synthesis/gemini_client.py` | Lines 146-154: use `response.usage_metadata` for actual token counts |
| `strategy_factory/webapp.py` | After line 2084: add `tracker.add_cost()` for synthesis |
| `strategy_factory/webapp.py` | Lines 427, 1572: `:.4f` → `:.2f` |
| `strategy_factory/server.py` | Line 427: `:.4f` → `:.2f` |
| `strategy_factory/research/perplexity_client.py` | Lines 157-169: replace text-based estimate with fixed per-query rate |
| `strategy_factory/config.py` | After line 48: add `PERPLEXITY_QUERY_COSTS` dict |

## Expected Results After Fix

For a typical quick-mode run (11 Perplexity queries, 8 Gemini deliverables):
- Perplexity: 11 × $0.0045 = $0.05 (vs actual $0.04-$0.05)
- Gemini: actual token-based pricing (should be ~$0.08-$0.10)
- Total: ~$0.13-$0.15 (vs actual ~$0.13-$0.14)
- Display: `$0.14` not `$0.1400`

## Verification

1. `python -m strategy_factory.main run "Test" --dry-run` — no crashes
2. Open existing company results in webapp and server — confirm 2 decimal display
3. After a live run, compare UI cost against Perplexity/Gemini billing dashboards
