# Phase 2 Prompt Structure Investigation

Generated 2026-04-04 from truncation investigation.

---

## Truncation Investigation Report

### The Scale of the Problem

| Run | Files | Total Words | Avg Words/File |
|-----|-------|-------------|----------------|
| black-mountain-yarn-shop (old) | 15 | 34,018 | 2,268 |
| healing-roots-design (new) | 6 | 2,652 | 442 |

**Old runs produced ~13x more content per file.**

### Two Separate Problems Found

#### Problem 1: Hard Truncation (content cut off mid-generation)

Two files are **visibly truncated** -- they end mid-section with no closing:

- **`01_tools_audit.md`** (134 words) -- Ends after a table header row with NO table data. Just the header `| Tool | What You Use It For | AI Features You're Not Using Yet |` and then nothing. The prompt asked for 3 sections totaling 400-600 words. The model produced ~22% of the minimum and stopped mid-table.

- **`02_daily_pain_points.md`** (781 words) -- Ends with the header `### The Content Creation Gap` followed by nothing. The section header was written but the content beneath it was never generated.

#### Problem 2: Systematically Shorter Output

Even the "complete" files in the healing-roots run are short:
- `03_action_plan.md`: 532 words (prompt target ~500-800, so barely meeting minimum)
- `04_simple_roadmap.md`: 469 words
- `05_readiness_assessment.md`: 354 words
- `06_roi_snapshot.md`: 382 words

### Root Cause: Gemini 2.5 Flash Thinking Tokens

**This is the smoking gun.** `gemini_client.py:99` sets `max_output_tokens=8192`.

Gemini 2.5 Flash is a **thinking model** -- its internal reasoning tokens count against `max_output_tokens`. The model may spend 6,000-7,500 tokens "thinking" before it writes a single word of output, leaving only 500-2,000 tokens for the actual response.

Evidence:
- `01_tools_audit` at 195 output tokens means the model burned ~8,000 tokens on thinking and had almost nothing left for output
- The old prompts (pre-rewrite) produced files averaging 2,268 words, so the model WAS capable of generating more under the same `max_output_tokens=8192` limit -- which means the older prompts either triggered less thinking, or the model version changed its thinking behavior

The code never checks `response.candidates[0].finish_reason` to detect when output was cut short, so truncation happens silently and gets marked as "completed" in state.json.

### Why the Old Runs Didn't Have This Problem

The old runs used **the same `gemini-2.5-flash` model with the same `8192` token limit**, but the old prompts were **much more structured and specific** -- they had 6 detailed sections with explicit table formats, categories to cover, and markdown formatting instructions. The new prompts are shorter and more conversational ("Write like you're explaining to a smart friend").

More structured prompts appear to trigger less open-ended reasoning, meaning the model spends fewer thinking tokens and has more budget for actual output. The new conversational prompts likely trigger more internal deliberation, consuming the token budget before writing.

### Secondary Contributing Factors

1. **No finish_reason check** (`gemini_client.py:146`) -- `content = response.text` blindly takes whatever was produced. If `finish_reason` is `MAX_TOKENS`, the code should retry or flag it.

2. **Context builder truncation** (`context_builder.py:193-194`) -- TLDR guides capped at 5,000 chars, dependencies at 3,000 chars. This limits what the model has to work with, though it's unlikely the primary truncation cause.

3. **Thin research data** -- The healing-roots research completed in only 9 seconds (vs minutes for older runs), suggesting minimal research context was available for the model to work with.

---

## The Real Fix: Structured Prompts, Not Token Limits

The synthesis prompts -- the 6 files in `strategy_factory/synthesis/prompts/` that Phase 2 rewrites -- are where the fix belongs. Not just cranking up token limits.

Look at the evidence side by side:

**Old prompt** (`tech_inventory.py` before rewrite):
```
### 2. Current Technology Stack
Create a table with the following columns:
| Category | Tool/Platform | Purpose | AI-Ready | Data Integration |

Categories to include:
- Core Business Systems (ERP, CRM, etc.)
- Communication & Collaboration
- Data & Analytics
...
```

**New prompt** (current `tech_inventory.py`):
```
A table with 3 columns: Tool | What You Use It For | AI Features You're Not Using Yet

Focus on tools they almost certainly have:
- Google Workspace or Microsoft 365...
```

The old prompt gave the model an explicit schema with 6 categories and a 5-column table format. The model filled in blanks -- minimal thinking required. The new prompt is more conversational ("You're probably using..."), which forces the model to reason about what to include, burning thinking tokens before it writes a word.

Result: the old prompt reliably produced 1,957 words. The new one produced 134 words and stopped mid-table.

So the fix for Phase 4 isn't primarily about `max_output_tokens` or completeness instructions tacked onto prompts. It's about **rewriting the Phase 2 prompts with explicit structure** -- exact table schemas, named sections with bullet-point requirements, specific word counts per section. The old enterprise prompts had this right, they just used enterprise jargon. The new SMB prompts can keep the accessible tone but need the same structural scaffolding.

That said, bumping `max_output_tokens` from 8192 to something higher is still worth doing as a safety net -- but it shouldn't be the primary fix.

### What Needs to Happen

1. **Rewrite Phase 2 prompts with explicit structure** -- exact table schemas, named sections with bullet-point requirements, specific word counts per section. Keep the accessible SMB tone but add the structural scaffolding the old prompts had.

2. **Increase `max_output_tokens`** in `gemini_client.py:99` from `8192` to at least `32768` as a safety net (Gemini 2.5 Flash supports up to 65,536).

3. **Add finish_reason checking** after `response = model.generate_content(...)` -- detect `MAX_TOKENS` and either retry with a higher limit or flag the deliverable as truncated.

4. **Add completeness instructions** to prompts as planned in Phase 4 item 16.

5. **Consider word count targets** in Phase 4 item 17 -- the current prompts target 400-600 words, which produces files far shorter than the old runs' 1,500-3,700 word average.
