# Fix: Reduce Executive Summary Input Bloat with SUMMARY Lines

## Problem

The executive summary depends on all 7 other deliverables. When building its prompt, `context_builder.py` truncates each dependency to 3,000 characters and appends them all. That's ~21,000 characters of dependency content alone, plus research context (company profile, industry, tech landscape), TLDR guides, temporal context, and system instructions. The total input is enormous.

This causes Gemini to produce truncated output — it writes content for the first section then outputs only headings for the remaining sections. This is separate from the word-count-budget truncation problem (covered in COUNTS.md). The executive summary has **two** problems: the word count budget AND input bloat. This plan addresses the input bloat.

**Why max_output_tokens doesn't help**: The model isn't hitting an output token limit. With massive input context, LLMs exhibit a "lost in the middle" behavior — they lose focus on instructions buried in large inputs. The executive summary prompt's "do not output just a heading" rules are at the bottom of a massive input that the model skims past.

**Historical context**: The original version of this system solved this by extracting just the lead sentence from each deliverable. Back then, each deliverable started with a summary sentence, so pulling the first line worked. Now the deliverables have different structures (thought experiments, tables, etc.) so first-line extraction would grab the wrong content.

## Approach

1. Add a mandatory rule to each of the 7 content prompts instructing the model to end its output with a `SUMMARY:` line — a single-sentence takeaway
2. Modify `context_builder.py` to extract those SUMMARY lines when building dependency context for the executive summary, with a fallback to first two paragraphs if a SUMMARY line is missing
3. The SUMMARY line stays visible in the final markdown output — it's a useful takeaway for readers, not just an extraction mechanism

## Changes

### 1. Add SUMMARY instruction to 7 prompt templates

Add one line to the mandatory rules section (the `## Mandatory rules` block) in each of these files:

- `strategy_factory/synthesis/prompts/tech_inventory.py`
- `strategy_factory/synthesis/prompts/pain_points.py`
- `strategy_factory/synthesis/prompts/quick_wins.py`
- `strategy_factory/synthesis/prompts/roadmap.py`
- `strategy_factory/synthesis/prompts/maturity_assessment.py`
- `strategy_factory/synthesis/prompts/roi_calculator.py`
- `strategy_factory/synthesis/prompts/closing.py`

Do NOT add to `executive_summary.py` — it consumes summaries, it doesn't produce one.

**The line to add** (as a bullet point in the mandatory rules list):

```
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
```

**What good summaries look like** (these are examples for the implementer, not to be added to prompts):

- **Tools Audit**: `SUMMARY: You already have 4 AI features turned off in tools you're paying for — activating them costs nothing and saves ~5 hours/week.`
- **Pain Points**: `SUMMARY: Answering calls and booking appointments manually costs you $12,000/year in lost leads — a voice AI agent fixes this for under $300/month.`
- **Action Plan**: `SUMMARY: Your highest-ROI move is activating Gemini in your Google Workspace this week — it takes 30 minutes and saves 2+ hours daily.`
- **Roadmap**: `SUMMARY: Following this plan puts 5 AI tools in daily use within 30 days, saving 10+ hours per week by month two.`
- **Readiness**: `SUMMARY: You scored 14/25 — ready to start but held back by disconnected tools and no measurement system.`
- **ROI**: `SUMMARY: For $80-150/month in tools, you'll recover 8-12 hours per week worth $600-900 at your hourly rate.`
- **Closing**: `SUMMARY: You have the plan, the tools, and the math — the only variable left is execution.`

### 2. Rewrite `format_dependencies_for_prompt` in `context_builder.py`

File: `strategy_factory/synthesis/context_builder.py`, lines 235-249

**Current code** (blunt truncation to 3,000 chars):

```python
def format_dependencies_for_prompt(self, dependencies: Dict[str, str]) -> str:
    """Format dependencies for inclusion in prompt."""
    if not dependencies:
        return ""

    sections = ["## Previously Generated Content\n"]

    for dep_id, content in dependencies.items():
        dep_name = DELIVERABLES.get(dep_id, {}).get("name", dep_id)
        # Truncate long content
        if len(content) > 3000:
            content = content[:3000] + "\n\n[Content truncated...]"
        sections.append(f"### {dep_name}\n{content}")

    return "\n\n".join(sections)
```

**Replace with** (SUMMARY extraction with paragraph fallback):

```python
def format_dependencies_for_prompt(self, dependencies: Dict[str, str]) -> str:
    """Format dependencies for inclusion in prompt, preferring SUMMARY lines."""
    if not dependencies:
        return ""

    sections = ["## Previously Generated Content\n"]

    for dep_id, content in dependencies.items():
        dep_name = DELIVERABLES.get(dep_id, {}).get("name", dep_id)

        # Look for SUMMARY: line
        summary_line = None
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith("SUMMARY:"):
                summary_line = stripped
                break

        if summary_line:
            sections.append(f"### {dep_name}\n{summary_line}")
        else:
            # Fallback: first two paragraphs
            paragraphs = content.split('\n\n')
            fallback = '\n\n'.join(paragraphs[:2])
            if len(fallback) > 800:
                fallback = fallback[:800] + "..."
            sections.append(f"### {dep_name}\n{fallback}")

    return "\n\n".join(sections)
```

**Why this works**:
- If the model produced a SUMMARY line (expected case), the executive summary gets ~100-200 chars per dependency instead of 3,000 — a ~10x reduction in dependency context
- If the model didn't produce one (edge case), the fallback grabs the first two complete paragraphs, capped at 800 chars — still a ~4x reduction and better than blunt character chopping
- The extraction is format-agnostic — it doesn't depend on section headings or prompt structure, just the `SUMMARY:` prefix

### 3. Files modified (summary)

1. `strategy_factory/synthesis/prompts/tech_inventory.py` — add SUMMARY rule to mandatory rules
2. `strategy_factory/synthesis/prompts/pain_points.py` — add SUMMARY rule to mandatory rules
3. `strategy_factory/synthesis/prompts/quick_wins.py` — add SUMMARY rule to mandatory rules
4. `strategy_factory/synthesis/prompts/roadmap.py` — add SUMMARY rule to mandatory rules
5. `strategy_factory/synthesis/prompts/maturity_assessment.py` — add SUMMARY rule to mandatory rules
6. `strategy_factory/synthesis/prompts/roi_calculator.py` — add SUMMARY rule to mandatory rules
7. `strategy_factory/synthesis/prompts/closing.py` — add SUMMARY rule to mandatory rules
8. `strategy_factory/synthesis/context_builder.py` — rewrite `format_dependencies_for_prompt` (lines 235-249)

## Verification

1. **Syntax check**:
   ```bash
   python -m py_compile strategy_factory/synthesis/context_builder.py
   ```

2. **Dry run** to confirm prompts load without import errors:
   ```bash
   python -m strategy_factory.main run "Test Company" --dry-run
   ```

3. **Live test** — run the full pipeline and verify:
   - Each of the 7 markdown files ends with a `SUMMARY:` line
   - The executive summary has complete content for all 3 sections (no bare headings)

4. **Fallback test** — temporarily remove a SUMMARY line from one deliverable's cached output and verify the context builder falls back to first two paragraphs without crashing
