# Plan: Derive Gemini Thinking Tokens from total_token_count Gap

## Context

The previous fix added `getattr(um, 'thoughts_token_count', 0)` but that attribute **does not exist** in `google-generativeai` v0.8.5. The library's `UsageMetadata` only has four fields: `prompt_token_count`, `candidates_token_count`, `total_token_count`, `cached_content_token_count`. Thinking tokens are embedded in the gap: `total - prompt - candidates`. Confirmed via live test: total (39) - prompt (9) - candidates (17) = 13 thinking tokens.

## File to Modify

`strategy_factory/synthesis/gemini_client.py` — lines 159–165 only.

## Change

Replace lines 159–165:

```python
# Use actual token counts from API response
um = response.usage_metadata
input_tokens = getattr(um, 'prompt_token_count', None) or self._count_tokens(prompt)
output_tokens = getattr(um, 'candidates_token_count', None) or self._count_tokens(content)
thinking_tokens = getattr(um, 'thoughts_token_count', 0) or 0

# Calculate cost (thinking tokens billed at output rate)
cost = self._estimate_cost(input_tokens, output_tokens + thinking_tokens)
```

With:

```python
# Use actual token counts from API response
um = response.usage_metadata
input_tokens = getattr(um, 'prompt_token_count', None) or self._count_tokens(prompt)
output_tokens = getattr(um, 'candidates_token_count', None) or self._count_tokens(content)

# Derive thinking tokens from gap (library v0.8.5 doesn't expose them directly)
total_tokens = getattr(um, 'total_token_count', 0) or 0
thinking_tokens = max(0, total_tokens - input_tokens - output_tokens)

# Calculate cost (thinking tokens billed at output rate)
cost = self._estimate_cost(input_tokens, output_tokens + thinking_tokens)
```

Everything else (tracking counters, cost summary) stays as-is — they already reference `thinking_tokens` correctly.

## Verification

Run a live audit and compare reported Gemini cost to actual billing.
