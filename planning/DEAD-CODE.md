# Remove Dead Cost-Estimation Code from `model_selector.py`

## What to Remove

`strategy_factory/research/model_selector.py` contains unused cost-estimation code. `estimate_total_cost()` is never called anywhere. `_estimate_query_cost()` is only called inside it and to populate an `estimated_cost` field on `ModelSelection` that nothing reads (the orchestrator only uses `selection.model`). Remove:

1. `estimated_cost` field from `ModelSelection` dataclass (line 24)
2. `estimated_cost=...` arguments from `select_model()` returns (lines 94, 125)
3. `_estimate_query_cost` method (lines 179-187)
4. `estimate_total_cost` method (lines 149-177)
