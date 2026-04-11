# Handoff: Fix Truncated Roadmap Silently Marked "Completed"

## Why This Exists

A bug was discovered during the Angela Kim Couture pipeline run. This file contains everything needed to understand the problem and implement the fix.

---

## Bug: Truncated Roadmap Silently Marked "Completed"

### What happened

The `04_simple_roadmap.md` file was generated with only 14 lines — a YAML front matter block, one intro paragraph, and an empty markdown table (header + separator row, **zero data rows**). Everything the prompt asked for was missing:

- No table data rows (should have 8-12 rows for weeks 1-4)
- No "Month 2: Build on What's Working" section (~200 words)
- No "Month 3 and Beyond" section (~150 words)
- No "Your Weekly Check-In" section (~100 words)
- No SUMMARY line

Despite this, `state.json` recorded the deliverable as `"status": "completed"` with `"error": null`.

### Root cause

The Gemini API returned truncated content without raising an exception. The `generate()` method in `gemini_client.py` just reads `response.text` and returns it — the response's `finish_reason` (which would say `MAX_TOKENS` when output was cut off) is never checked. There is **no completeness validation** anywhere in the pipeline.

The DOCX and PDF generators (`docx_generator.py`, `pdf_generator.py`) both have roadmap card builders (`_add_roadmap_cards` / `_build_roadmap_cards`) that require at least 3 table lines (header + separator + data). With only 2 lines, they produce nothing — so the roadmap section appears blank.

### Why Gemini truncated it

The roadmap prompt asks for the most content of any deliverable (~850+ words plus a 5-column table with 8-12 rows). `max_output_tokens` is hardcoded to 8192 at `gemini_client.py:99`. Gemini 2.5 Flash supports up to 65536 output tokens, so this cap is ~12% of capacity and is the most likely proximate cause of the truncation.

### The actual truncated file (for reference)

File: `output/angela-kim-couture/markdown/04_simple_roadmap.md`

```markdown
---
title: "Your Week-by-Week Plan"
deliverable_id: "04_simple_roadmap"
generated_at: "2026-04-09T22:25:22.288443"
generator: "AI Strategy Factory"
---

# Your First 30 Days

This plan focuses on getting you comfortable with AI tools that can immediately save you time and help you grow, without needing to be a tech wizard. We'll start with the most impactful tool first: an agentic AI that can handle multi-step tasks for you.

| # | Action | Tool (Price) | Time | What To Do |
| --- | --- | --- | --- | --- |
```

End of file. No data rows, no Month 2, no SUMMARY.

---

## Architecture Context

### Pipeline flow

```
main.py / server.py
  -> research/orchestrator.py (Perplexity queries)
  -> synthesis/orchestrator.py (generates all 8 deliverables)
       -> synthesis/gemini_client.py (API calls with retry)
       -> synthesis/context_builder.py (builds prompts with research)
       -> synthesis/prompts/*.py (8 prompt templates)
  -> generation/orchestrator.py
       -> generation/markdown_generator.py (saves .md files)
       -> generation/docx_generator.py (Word document)
       -> generation/pdf_generator.py (PDF document)
```

### All 8 prompts require a SUMMARY line

Every prompt file in `strategy_factory/synthesis/prompts/` ends with a mandatory rule:

> End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]

This gives us a reliable completeness marker as a belt-and-suspenders check.

---

## Fix Strategy

Three layers, each the smallest change that addresses one thing:

1. **Prevention** — raise the output token ceiling so Gemini doesn't run out of room.
2. **Authoritative detection** — check the SDK's `finish_reason` so we know when Gemini *did* stop early.
3. **Fallback detection + retry** — catch any remaining truncation via missing `SUMMARY:` marker, and retry once.

Total: ~10 lines changed across 2 files. No new methods, no regex, no YAML stripping.

---

## Implementation Plan

### Change 1: Raise `max_output_tokens`

**File**: `strategy_factory/synthesis/gemini_client.py` (line 99)

```python
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 16384,   # was 8192
    ) -> SynthesisResult:
```

Gemini 2.5 Flash supports up to 65536 output tokens. Bumping to 16384 gives the roadmap ample headroom. Cost impact: zero — output is billed per actual token produced, not per ceiling.

### Change 2: Check `finish_reason`

**File**: `strategy_factory/synthesis/gemini_client.py` (around line 146, inside the `try` block of `generate()`)

Right after `response = model.generate_content(...)` and before `content = response.text`, add:

```python
                # Detect truncation via finish_reason before reading text
                candidate = response.candidates[0] if response.candidates else None
                finish_reason = getattr(candidate, "finish_reason", None)
                finish_name = getattr(finish_reason, "name", str(finish_reason))
                if finish_name == "MAX_TOKENS":
                    raise RuntimeError(
                        f"Gemini stopped early: finish_reason={finish_name} "
                        f"(output hit max_output_tokens={max_output_tokens})"
                    )
```

Raising inside the `try` block lets the existing retry loop at `gemini_client.py:120` handle it automatically with backoff. If every retry also truncates, the final `SynthesisResult` returns with `error` populated — which `_generate_deliverable` already surfaces.

### Change 3: Fallback SUMMARY check + one retry

**File**: `strategy_factory/synthesis/orchestrator.py`

Two small edits.

**3a.** In `_generate_deliverable()`, after the `if result.error:` block (~line 208), add a fallback completeness check:

```python
        if result.content and "SUMMARY:" not in result.content:
            return DeliverableContent(
                deliverable_id=deliverable_id,
                name=deliverable_config.get("name", deliverable_id),
                format="markdown",
                error="Missing SUMMARY line — output likely truncated",
            )
```

This is the belt-and-suspenders: catches any truncation mode that slips past the `finish_reason` check (e.g., Gemini stops for a different reason but still returns incomplete text).

**3b.** In `synthesize()`, wrap the generation call (~lines 128-145) in a single retry:

```python
                # Generate deliverable (one retry on truncation/validation failure)
                content = self._generate_deliverable(
                    deliverable_id,
                    company_input,
                    research,
                )
                if content and content.error:
                    print(f"  Retrying {deliverable_id}: {content.error}")
                    content = self._generate_deliverable(
                        deliverable_id,
                        company_input,
                        research,
                    )

                if content and not content.error:
                    self.generated_content[deliverable_id] = content
                    self.context_builder.register_deliverable(
                        deliverable_id,
                        content.content
                    )
                else:
                    self._record_error(
                        deliverable_id,
                        content.error if content else "Unknown error"
                    )
```

Note: `gemini_client.generate()` already retries transient API errors via its own loop (`gemini_client.py:120`). This orchestrator-level retry is for a different condition — content-level truncation after a "successful" API call — so the two layers don't conflict.

---

## Files to Modify

| File | Change | LoC |
|---|---|---|
| `strategy_factory/synthesis/gemini_client.py` | Bump `max_output_tokens` default to 16384; check `finish_reason` for `MAX_TOKENS` and raise | ~8 |
| `strategy_factory/synthesis/orchestrator.py` | Add SUMMARY fallback check in `_generate_deliverable()`; add one retry in `synthesize()` | ~12 |

---

## Verification

1. **Prevention works**: Run the full pipeline for a test company. With `max_output_tokens=16384`, the roadmap should generate in full on the first try. Check `04_simple_roadmap.md` contains the full table, Month 2, Month 3, Weekly Check-In, and SUMMARY sections.
2. **Detection works**: Temporarily set `max_output_tokens=1024` and rerun. Expected behavior:
   - `finish_reason=MAX_TOKENS` check fires inside `generate()`
   - Existing client-level retry loop kicks in with backoff
   - If retries exhaust, orchestrator receives an `error`, prints `Retrying ...`, and tries once more
   - Deliverable ends up marked `failed` in `state.json` with a real error message — **not** silently `completed`
3. **DOCX/PDF**: Open the generated documents. The roadmap section should contain card-style content, not be blank.
4. **Web UI**: Run `python -m strategy_factory.server`, view the roadmap tab. It should contain the week-by-week table and subsequent sections.
