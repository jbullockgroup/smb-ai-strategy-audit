# Plan: Create Closing Section

## Context

Part of the synthesis prompt restructuring (PHASE-2.md). The current deliverables lack a synthesizing closing section that ties everything together. This plan creates a new `closing.py` prompt that depends on all 6 other deliverables and produces a final "Putting It All Together" section.

## Target: 400-600 words

---

## Part 1: Create the Closing Prompt

### New file: `strategy_factory/synthesis/prompts/closing.py`

Section structure:
1. **What This All Means for [Company]** (~250 words) — Narrative synthesis connecting the dots: "Your biggest opportunity is X. You already have Y tools that can do Z. The quick wins are A, B, C. Here's what your first month looks like."
2. **Your One Next Step** (~100 words) — Single clear action for Monday morning. Named tool, specific task.
3. **Closing thought** (~100 words) — Encouraging but honest. Reference the AI value gap (88% use AI, only 5-8% capture value). This plan exists to close that gap.

This section goes LAST in generation order. Dependencies: all other 6 deliverables.

---

## Part 2: Update Configuration

### File: `strategy_factory/config.py`
- Add `07_closing` to DELIVERABLES dict with name "Putting It All Together", format "markdown", dependencies: ALL markdown deliverables

### File: `strategy_factory/synthesis/prompts/__init__.py`
- Import CLOSING_PROMPT from closing.py
- Add to PROMPTS dict: `"07_closing": CLOSING_PROMPT`

### File: `strategy_factory/synthesis/orchestrator.py`
- Add `07_closing` to GENERATION_ORDER as a new level after the existing 3 levels

---

## Verification

1. **Dry run**: `python -m strategy_factory.main run "Test Company" --dry-run` — verify pipeline recognizes new deliverable
2. **Live run**: Test with a real company and check:
   - Closing section appears and references the other sections
   - Word count falls within 400-600 range
   - Final DOCX compiles with the closing section included
