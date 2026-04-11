# Plan: Update Configuration for New Deliverables

## Context

Part of the synthesis prompt restructuring (PHASE-2.md). After new prompts are written and the closing section is created, the pipeline configuration needs updating so the system knows about the new `07_closing` deliverable, its dependencies, and its place in generation order.

---

## Changes

### File: `strategy_factory/config.py`
- Add `07_closing` to DELIVERABLES dict with name "Putting It All Together", format "markdown", dependencies: ALL markdown deliverables

### File: `strategy_factory/synthesis/prompts/__init__.py`
- Import CLOSING_PROMPT from closing.py
- Add to PROMPTS dict: `"07_closing": CLOSING_PROMPT`

### File: `strategy_factory/synthesis/orchestrator.py`
- Add `07_closing` to GENERATION_ORDER as a new level after the existing 3 levels
- Update system instruction to include Claude Cowork reference and 2026 tool landscape

---

## Verification

1. `python -m strategy_factory.main run "Test Company" --dry-run` — verify pipeline recognizes all deliverables including `07_closing`
2. Check that generation order respects the dependency (closing runs last)
