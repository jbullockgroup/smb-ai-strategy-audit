# Plan: Fix Token Limits & Truncation Detection

## Context

Part of the synthesis prompt restructuring (PHASE-2.md). Gemini 2.5 Flash uses excessive thinking tokens that leave little budget for actual output, causing truncated responses. This plan raises the output token ceiling and adds truncation detection so the system warns instead of silently accepting incomplete content.

---

## Changes

### File: `strategy_factory/synthesis/gemini_client.py`
- Change `max_output_tokens` default from 8192 to 32768 (line 99)
- After `content = response.text` (line 146), check `response.candidates[0].finish_reason` against `FinishReason.MAX_TOKENS` (enum, not string) and log a warning if matched

---

## Verification

1. **Truncation check**: Verify that if a response hits MAX_TOKENS, the system logs a warning instead of silently accepting truncated output
2. **Full run**: Confirm no deliverables are truncated mid-section with the higher token limit
