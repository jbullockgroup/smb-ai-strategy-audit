# Plan: Capture Gemini Thinking Tokens in Cost Calculation

## Context

The cost calculation consistently underestimates Gemini costs by 1.4x–3.4x because it ignores **thinking tokens**. Gemini 2.5 Flash is a "thinking" model — it generates internal reasoning tokens billed at the output rate ($2.50/1M). The API response's `usage_metadata` includes a `thoughts_token_count` field, but the code only reads `prompt_token_count` and `candidates_token_count`. This means every request's cost is calculated low, and the gap widens for complex deliverables that trigger more reasoning.

## File to Modify

`strategy_factory/synthesis/gemini_client.py` — all changes in this one file.

## Changes

### 1. Add thinking token tracking (line ~69)

Add a new counter alongside the existing ones:

```python
self.total_thinking_tokens = 0
```

### 2. Capture `thoughts_token_count` from API response (lines 157–168)

Replace:
```python
um = response.usage_metadata
input_tokens = getattr(um, 'prompt_token_count', None) or self._count_tokens(prompt)
output_tokens = getattr(um, 'candidates_token_count', None) or self._count_tokens(content)

# Calculate cost
cost = self._estimate_cost(input_tokens, output_tokens)

# Update tracking
self.total_cost += cost
self.total_input_tokens += input_tokens
self.total_output_tokens += output_tokens
```

With:
```python
um = response.usage_metadata
input_tokens = getattr(um, 'prompt_token_count', None) or self._count_tokens(prompt)
output_tokens = getattr(um, 'candidates_token_count', None) or self._count_tokens(content)
thinking_tokens = getattr(um, 'thoughts_token_count', 0) or 0

# Calculate cost (thinking tokens billed at output rate)
cost = self._estimate_cost(input_tokens, output_tokens + thinking_tokens)

# Update tracking
self.total_cost += cost
self.total_input_tokens += input_tokens
self.total_output_tokens += output_tokens
self.total_thinking_tokens += thinking_tokens
```

### 3. Include thinking tokens in cost summary (lines 323–333)

Add `total_thinking_tokens` to the summary dict:

```python
def get_cost_summary(self) -> Dict[str, Any]:
    """Get a summary of API usage and costs."""
    return {
        "total_cost": round(self.total_cost, 4),
        "total_input_tokens": self.total_input_tokens,
        "total_output_tokens": self.total_output_tokens,
        "total_thinking_tokens": self.total_thinking_tokens,
        "request_count": self.request_count,
        "avg_cost_per_request": round(
            self.total_cost / max(1, self.request_count), 4
        ),
    }
```

### 4. No changes needed elsewhere

- `SynthesisResult` dataclass: No change needed — it stores `completion_tokens` which remains the visible output tokens. The thinking tokens are an internal cost detail.
- `progress_tracker.py`: Only receives dollar amounts via `add_cost()`. No token-level dependency.
- `main.py` / `webapp.py`: Only read `cost_summary["total_cost"]`. No token-level dependency.

## Verification

1. Run a dry-run to confirm no syntax errors: `python -c "from strategy_factory.synthesis.gemini_client import GeminiClient; print('OK')"`
2. Run a live audit and compare the reported cost against actual billing. The reported Gemini cost should now be 1.5x–3x higher than before (matching actual spend), and the total should land much closer to real cost.
