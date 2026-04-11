# TOKEN-REVERT.md — Handoff: Revert Token Limit Changes

## Why This Change Is Needed

Two changes from `planning/PHASE-2-4-TOKENS.md` broke the synthesis pipeline. The plan diagnosed truncated strategy documents as a token limit problem, but the real cause was bad research data (wrong industry fallback). The "fix" introduced a crash that kills all Gemini API calls.

### The Crash

`gemini_client.py:150` references `genai.types.FinishReason.MAX_TOKENS`, but this enum doesn't exist in `google-generativeai` v0.8.5 (confirmed via `hasattr` check — returns `False`). Every Gemini call hits an `AttributeError`, retries 3 times, then returns an empty `SynthesisResult`. The synthesis phase completes with 0 deliverables, and the final DOCX/PDF is boilerplate only.

### Why 8192 Tokens Is Sufficient

Evidence from the working old repo (`ai-strategy-factory-2`):

| Document | Output Tokens | % of 8192 |
|----------|--------------|-----------|
| 01_tech_inventory | ~3,821 | 47% |
| 02_pain_points | ~3,054 | 37% |
| 05_roadmap | ~4,654 | 57% |
| 06_quick_wins | ~5,398 | 66% |
| 11_data_governance | ~5,810 | 71% |
| 14_use_case_library | ~6,706 | 82% |
| **Average (15 docs)** | **~4,369** | **53%** |

The largest document used 82% of 8192. No truncation occurred. The current repo targets ~20 pages across 7 docs (vs 170 pages across 15), so 8192 is even more comfortable.

The Healing Roots audit showed truncation, but the documents were all under 1,314 output tokens (16% of budget) — they weren't hitting the ceiling. The model produced short responses because the research data was garbage ("technology" industry instead of "landscaping/permaculture").

## Changes Required

### File: `strategy_factory/synthesis/gemini_client.py`

**Change 1 — Line 99:** Revert `max_output_tokens` default

```python
# Current (broken):
max_output_tokens: int = 32768,

# Revert to:
max_output_tokens: int = 8192,
```

**Change 2 — Lines 148-151:** Remove the FinishReason truncation check entirely

Delete these 4 lines:
```python
                # Warn if response was cut off by token limit
                finish_reason = response.candidates[0].finish_reason
                if finish_reason == genai.types.FinishReason.MAX_TOKENS:
                    print(f"WARNING: Response truncated at token limit (max_output_tokens={max_output_tokens})")
```

After removal, the flow goes directly from `content = response.text` (line 146) to `# Estimate tokens` (line 153). This matches the working old repo exactly.

### No Other Files Need Changes

The `generate_markdown()` method passes through to `generate()` with no override on `max_output_tokens`, so changing the default in `generate()` covers all callers.

## What NOT To Change

- Do NOT change the industry fallback in `research/orchestrator.py:98` — that's a separate issue to be addressed in its own plan.
- Do NOT change any prompt files.
- Do NOT change `requirements.txt` or the SDK version.

## Verification

```bash
# 1. Confirm no import/crash issues
source venv/bin/activate
python -c "from strategy_factory.synthesis.gemini_client import GeminiClient; print('OK')"

# 2. Dry run (no API calls)
python -m strategy_factory.main run "Healing Roots Design" --dry-run

# 3. Live test with correct industry
python -m strategy_factory.main run "Healing Roots Design" --context "permaculture landscape design, sustainable landscaping, Punta Gorda FL, 30 employees"
```

After the live test, confirm:
- `output/healing-roots-design/markdown/` contains populated .md files (not empty)
- Each .md file has substantive content (not just headers)
- `output/healing-roots-design/documents/final_strategy_report.docx` has real content (not just boilerplate)
