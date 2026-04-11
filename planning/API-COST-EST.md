# API Cost Estimation Fix — Handoff Document

## The Problem

The UI reports **$0.0165** for a run that actually costs **$0.14** in API charges (about 8.5x under).

Actual billing breakdown for the Healing Roots Design audit (April 7, 2026):
- Perplexity: $0.06
- Gemini: $0.08
- **Total: $0.14**

Reported: $0.0165 (all from Perplexity; Gemini shows as $0.00)

## Root Causes

### Perplexity (reports $0.0165, actual $0.06)

1. **Hardcoded token counts** — `perplexity_client.py:290` calls `self._estimate_cost(model)` with no arguments, so it defaults to 500 input + 1000 output tokens per query. Real responses are much larger (~3,800 input + ~5,600 output per query).
2. **Pricing constants are correct** — `config.py:42-48` has the right per-token rates (Sonar: $1/1M in, $1/1M out).

### Gemini (reports $0.00, actual $0.08)

1. **Pricing constants are WRONG** — `gemini_client.py:43-44` has outdated prices:
   - Input: `$0.075/1M` — actual is **$0.30/1M** (4x too low)
   - Output: `$0.30/1M` — actual is **$2.50/1M** (8.3x too low)
2. **Token estimation (chars/4) is fine** — the approximation is reasonable. The real problem is the pricing rates.

### Neither API returns saved token counts

Both clients receive usage metadata in their API responses but discard it. You cannot retroactively get exact costs for past runs.

## The Formula

Using stored data (query text, result snippets, markdown output) with correct pricing produces results within 4% of actual billing.

### Perplexity: use actual text from API responses

For each query, count characters from the stored query text and result snippets:

```
input_tokens  = len(query_text) / 4
output_tokens = sum(len(snippet) for each result) / 4
cost_per_query = (input_tokens / 1M × $1.00) + (output_tokens / 1M × $1.00)
```

**No request fee** — token cost alone hits $0.0655 vs $0.06 actual (9% off). Adding the request fee overcounts.

Verified: 11 queries × actual text = $0.0655. Close enough.

### Gemini: use output text + empirical input ratio

We don't store the input prompt text, but we do store the output (markdown files). The input:output ratio is ~15:1 because each prompt includes full research context + prior deliverables:

```
output_tokens = len(response_text) / 4
input_tokens  = output_tokens × 15
cost_per_call = (input_tokens / 1M × $0.30) + (output_tokens / 1M × $2.50)
```

Verified: 8 deliverables × actual output = $0.08 (matches actual).

### Combined: $0.1455 vs $0.14 actual — within 4%.

## Changes to Implement

### 1. Fix Gemini pricing constants — `strategy_factory/synthesis/gemini_client.py`

Lines 43-44. Update to correct Gemini 2.5 Flash standard tier pricing:

```python
# BEFORE (wrong):
COST_PER_1M_INPUT = 0.075   # $0.075 per 1M input tokens
COST_PER_1M_OUTPUT = 0.30   # $0.30 per 1M output tokens

# AFTER (correct):
COST_PER_1M_INPUT = 0.30    # $0.30 per 1M input tokens
COST_PER_1M_OUTPUT = 2.50   # $2.50 per 1M output tokens
```

### 2. Fix Perplexity cost estimation — `strategy_factory/research/perplexity_client.py`

**`_estimate_cost` method (line 157)**: Change to accept actual text and calculate tokens from it:

```python
def _estimate_cost(self, model, query_text="", response_text=""):
    """Estimate cost from actual text content."""
    input_tokens = len(query_text) / 4
    output_tokens = len(response_text) / 4
    input_cost, output_cost = PERPLEXITY_COSTS.get(model, (0.001, 0.001))
    return (input_tokens / 1000 * input_cost) + (output_tokens / 1000 * output_cost)
```

**Call site (line ~289-291)**: Pass actual query and response text:

```python
# Build response text from snippets
response_text = " ".join(r.snippet for r in results if r.snippet)
query_str = params["query"]
if isinstance(query_str, list):
    query_str = " | ".join(query_str)
cost = self._estimate_cost(model, query_str, response_text)
```

## Files to Modify

| File | Change |
|------|--------|
| `strategy_factory/synthesis/gemini_client.py:43-44` | Fix pricing constants ($0.30/$2.50) |
| `strategy_factory/research/perplexity_client.py:157-167` | Accept actual text instead of hardcoded tokens |
| `strategy_factory/research/perplexity_client.py:289-291` | Pass actual query + response text to cost estimator |

## Pricing Reference (confirmed April 2026)

### Perplexity

| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| Sonar | $1.00 | $1.00 |
| Sonar Pro | $3.00 | $15.00 |
| Sonar Reasoning Pro | $2.00 | $8.00 |

- Citation tokens no longer charged for Sonar Pro and Sonar Reasoning Pro (as of April 2025)
- Per-request fee varies by search context size (not needed in formula — token cost alone is accurate)

### Gemini 2.5 Flash

| Tier | Input (per 1M) | Output (per 1M) |
|------|----------------|-----------------|
| Standard | $0.30 | $2.50 |
| Batch/Flex | $0.15 | $1.25 |

- Output pricing includes thinking tokens
- Context caching: $0.03/1M tokens
- Model used: `gemini-2.5-flash`

## Verification Data

From the Healing Roots Design run stored at `/output/healing-roots-design/`:

| Metric | Value |
|--------|-------|
| Perplexity queries | 11 (all Sonar) |
| Perplexity input chars | 15,221 |
| Perplexity output chars (snippets) | 246,906 |
| Gemini deliverables | 8 |
| Gemini output chars (markdown) | 45,229 |
| Research cache size | 94,351 bytes |
| Formula estimate: Perplexity | $0.0655 (actual: $0.06) |
| Formula estimate: Gemini | $0.08 (actual: $0.08) |
| Formula estimate: Total | $0.1455 (actual: $0.14) |
| Variance | 4% |

After implementing, verify with:
1. `python -m strategy_factory.main run "Test Company" --dry-run` — no crashes
2. Run a live test and compare against Perplexity/Gemini billing dashboards
