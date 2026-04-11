# RESEARCH-ENHANCEMENTS.md — Merged Research & Prompt Enhancement Plan

**Purpose**: Self-contained handoff document. Merges two previously separate plans (ENHANCEMENTS and VOICE-AGENTS) into one coherent implementation that avoids all file collisions. Digital presence is handled by EXPAND-CO.md (expanding the existing `company_presence` query template to include blog, LinkedIn, TikTok, YouTube, and advertising signals) — no new query or Firecrawl dependency needed.

## Execution Order: Step 4 of 5

| Step | Plan | What it does |
|------|------|-------------|
| 1 | TLDR-FIX | Fix knowledge_loader.py (standalone) |
| 2 | PROMPTS-AGAIN | Restructure all 7 prompt formats |
| 3 | EXPAND-CO | Expand `company_presence` query to include blog, LinkedIn, TikTok, YouTube, advertising (1 file, 2 lines) |
| **4** | **RESEARCH-ENHANCEMENTS (this plan)** | **Pipeline wiring + all prompt content additions** |
| 5 | EXEC-SUM | Add 8th deliverable |

**Prerequisites**:
- Step 2 (PROMPTS-AGAIN) must be complete — this plan adds content to restructured prompts
- Step 3 (EXPAND-CO) must be complete — expands `company_presence` template with digital presence signals

---

## What This Plan Does

Five enhancements merged into one clean pipeline wiring job:

| # | Enhancement | Approach |
|---|------------|----------|
| 1 | Competitive intelligence (new query + prompt section) | New Perplexity query; Gemini extracts insights from raw research |
| 2 | Industry benchmarks & "why now" urgency | Prompt instructions tell Gemini to pull benchmarks from existing research |
| 3 | Fix context passthrough bug (`{context}` never passed to queries) | Bug fix in orchestrator |
| 4 | Review sentiment references in prompts | Prompt instructions tell Gemini to reference review data from `social_reviews` research |
| 5 | Voice agent mentions across 3 prompts + tech keyword detection | Keywords + prompt content |

**Design principle**: Research text already flows to Gemini. Rather than building a fragile regex extraction pipeline to parse structured data from unstructured search snippets, we add prompt instructions that tell Gemini what to look for. The LLM does the extraction better than regex can.

---

## File Change Summary

| File | Changes |
|------|---------|
| `strategy_factory/research/query_templates.py` | Add `COMPETITOR_DISCOVERY` template; add `{context}` to 3 templates |
| `strategy_factory/research/orchestrator.py` | Fix context passthrough bug; add competitor query to PHASE_QUERIES |
| `strategy_factory/research/result_processor.py` | Add voice/phone keywords to `_extract_technologies()` |
| `strategy_factory/synthesis/prompts/pain_points.py` | Add voice workflow, competitor section, urgency section, review refs, update word count |
| `strategy_factory/synthesis/prompts/quick_wins.py` | Add voice AI agent recommendation |
| `strategy_factory/synthesis/prompts/tech_inventory.py` | Add phone system and voice AI rows, add manual call-handling example |

**Files NOT changed** (verified no collision):
- `models.py` — no new models needed; Gemini extracts from raw research
- `config.py` — only EXEC-SUM touches this
- `synthesis/orchestrator.py` — only EXEC-SUM touches this
- `synthesis/context_builder.py` — no new formatters needed; raw research already passed through
- `prompts/__init__.py` — only EXEC-SUM touches this
- `knowledge_loader.py` — only TLDR-FIX touches this
- `main.py` — no changes from this plan

---

## Wave A: Research Layer

### Enhancement 3: Fix context passthrough bug

### File: `strategy_factory/research/orchestrator.py`

**Fix 1 — Add `context` parameter to `_execute_phase()` signature**:

Change from:
```python
def _execute_phase(
    self,
    phase: str,
    company_name: str,
    industry: str,
) -> None:
```
To:
```python
def _execute_phase(
    self,
    phase: str,
    company_name: str,
    industry: str,
    context: str = "",
) -> None:
```

**Fix 2 — Pass `context` to `render_query()`** inside `_execute_phase()`:

Change from:
```python
query = self.templates.render_query(
    template,
    company_name=company_name,
    industry=industry,
)
```
To:
```python
query = self.templates.render_query(
    template,
    company_name=company_name,
    industry=industry,
    context=context,
)
```

**Fix 3 — Update all 3 call sites** in `research()` to pass `context`:

- Line ~108: `self._execute_phase("company_discovery", company_name, industry, context)`
- Line ~125: `self._execute_phase("industry_analysis", company_name, industry, context)`
- Line ~129: `self._execute_phase("ai_opportunity", company_name, industry, context)`

### Enhancement 1: New competitor query

### File: `strategy_factory/research/query_templates.py`

**Add `COMPETITOR_DISCOVERY` template** (after `SALES_CHANNELS`, in Phase 1 — Company Discovery):

```python
COMPETITOR_DISCOVERY = QueryTemplate(
    name="competitor_discovery",
    category=QueryCategory.COMPANY_DISCOVERY,
    template='"{company_name}" {industry} {context} competitors similar companies alternatives market share {current_year}',
    recency_filter="year",
    priority=2,
    required_for_quick_mode=True,
    description="Discover specific competitors and alternatives in the market",
)
```

Add to `ALL_TEMPLATES` dict:
```python
"competitor_discovery": COMPETITOR_DISCOVERY,
```

**Add `{context}` to 3 existing templates** (if not already present in the template string):

- `INDUSTRY_CHALLENGES`: append ` {context}` to template string
- `INDUSTRY_AI_EXAMPLES`: append ` {context}` to template string
- `INDUSTRY_AI_TRENDS`: append ` {context}` to template string

### File: `strategy_factory/research/orchestrator.py`

**Add `competitor_discovery` to `PHASE_QUERIES`**:

```python
PHASE_QUERIES = {
    "company_discovery": [
        "company_presence",         # Expanded by EXPAND-CO (blog, LinkedIn, TikTok, YouTube, advertising)
        "social_reviews",
        "sales_channels",
        "competitor_discovery",   # ADD
    ],
    # ... rest unchanged
}
```

---

## Wave B: Voice Keywords (`result_processor.py`)

### File: `strategy_factory/research/result_processor.py`

### Enhancement 5: Voice/phone keywords

**In `_extract_technologies()`**, add voice/phone tools to the keyword list:

```python
# Voice/Phone tools
"smith.ai", "ruby", "davinci", "twilio", "bland ai", "vapi",
"retell", "google voice", "grasshopper", "ringcentral",
```

---

## Wave C: Prompt Layer

### IMPORTANT: This wave assumes PROMPTS-AGAIN has already been applied.

All prompts now use the `# Task: Generate` / `## Required Sections` / `## Output Format` format. The changes below add content to the restructured prompts.

### File: `strategy_factory/synthesis/prompts/pain_points.py`

This file gets the most changes. All changes go inside the `PROMPT = """..."""` string, within `## Required Sections`, before `## Output Format`.

**Change 1: Add 6th workflow to "Your Highest-Impact Workflows"**

After the existing 5 workflow analyses (Speed to Lead, Follow-Up, Database Reactivation, Internal Reporting, Document Processing), add:

```
6. **Phone & Call Management** — Are incoming calls going to voicemail? Are after-hours inquiries being lost? How much revenue walks out the door with every missed call?

ROI example: 62% of calls to small businesses go unanswered. A voice AI agent can handle after-hours inquiries, book appointments, and qualify leads 24/7 — one dental practice recovered $47k/year in missed-call revenue.
```

**Change 2: Modify "The Content Creation Gap" section**

Replace the existing Content Creation Gap section content with:

```
Where they're falling short (social, email, blog, reviews), opportunity cost, and why this is an easy win with AI.

If digital presence or online activity data appears in the research context above, reference specific facts: posting frequency, platform activity, or content gaps found during research.

If customer review data appears in the research (from the social_reviews query), reference it directly: mention specific complaint themes, praise themes, review volume, or ratings. Frame complaints as pain points that AI can address and praise as strengths to protect.

Note that content workflows can be set up quickly with the right prompting strategy — this is a good candidate for a training session.
```

**Change 3: Add "What Your Competitors Are Up To" section** (after Content Creation Gap, before `## Output Format`):

```
### What Your Competitors Are Up To (~100-150 words)

If the research context above mentions specific competitors or alternative businesses, write a brief competitive pressure section. For each named competitor (up to 3), mention:
- Their name and what they do
- Any AI or automation they appear to be using
- What this means for the reader (one sentence about the competitive gap)

If no specific competitors were found in research, write one paragraph about the general competitive pressure in this industry: "Your competitors are already adopting AI tools — [industry] businesses using AI report [specific benefit from research]. The gap between early adopters and wait-and-see businesses grows every quarter."
```

**Change 4: Add "Your Industry's AI Moment" section** (after Competitors section):

```
### Your Industry's AI Moment (~150-200 words)

Write 2-3 paragraphs about the current AI momentum in this industry. Use the research data about industry AI adoption rates, recent AI tool launches for this sector, and competitive shifts. Cover:
- What percentage of similar businesses are now using AI (cite from research if available)
- What's changed in the last 6-12 months (new tools, platform updates, customer expectations)
- Why waiting is now the riskier choice than experimenting

End with: "The businesses that figure this out in the next 90 days will have a 12-18 month head start on the ones still 'watching and waiting.'"

This section must be grounded in the research provided above. If specific adoption rates are available, use them. If not, reference the general trend that AI adoption among SMBs has doubled in the past year and that late adopters are falling behind.
```

**Change 5: Update total word count**

In `## Output Format`, change:
```
- Total length: 900-1,200 words
```
To:
```
- Total length: 1,400-1,800 words
```

This accounts for: phone workflow (+100), competitor section (+150), urgency section (+200), enhanced Content Creation Gap (+50), plus original content.

### File: `strategy_factory/synthesis/prompts/quick_wins.py`

**Add voice AI agent to tool recommendations** — in the Tool Recommendations section, after the existing tool list (Perplexity), add:

```
- **Voice AI Agent (Bland AI, Smith.ai, or similar)** — handles missed calls, books appointments, qualifies leads 24/7. $50-300/mo depending on call volume. Critical for any business that receives phone inquiries.
```

### File: `strategy_factory/synthesis/prompts/tech_inventory.py`

**Add to tool stack table** — in the explicit table template (added by PROMPTS-AGAIN), add 2 new rows after the existing 7:

```
| Phone system (landline, VoIP, Google Voice, RingCentral) | [usage] | [specific AI feature] | [concrete capability] |
| Voice AI / answering service | [usage] | [specific AI feature] | [concrete capability] |
```

Update the row count instruction from "7 rows" to "9 rows".

**Add to "What's Still Manual" examples** (if this section exists in the prompt):

```
- **Answering calls and booking appointments** — [X hours/week] — Voice AI agent handles scheduling, after-hours, and overflow
```

---

## Data Flow Summary

| Enhancement | Query | Extraction | Prompt Instructions |
|------------|-------|-----------|---------------------|
| 1. Competitors | `competitor_discovery` (NEW) | None — raw results flow to Gemini | "If the research context mentions specific competitors..." |
| 2. Benchmarks | existing queries | None — raw results flow to Gemini | "What percentage of similar businesses are now using AI (cite from research)" |
| 3. Local context | N/A — bug fix | N/A | N/A |
| 4. Reviews | `social_reviews` (existing) | None — raw results flow to Gemini | "If customer review data appears in the research..." |
| 5. Voice agents | N/A | voice keywords in `_extract_technologies()` | pain_points workflow + quick_wins tool + tech_inventory rows |

---

## Verification

1. **Context passthrough fix**: Run with `--context "Denver, Colorado"` and log rendered queries for `industry_challenges`, `industry_ai_examples`, `industry_ai_trends` — verify context string appears
2. **Competitive intelligence**: Run for a company with known competitors. Check `research_cache.json` for `competitor_discovery` results. Check `pain_points.md` for competitor mentions
3. **Review references**: Run for a company with visible reviews. Check `pain_points.md` Content Creation Gap section references review themes
4. **Industry urgency**: Check `pain_points.md` for "Your Industry's AI Moment" section grounded in research data
5. **Voice keywords**: Run for a company known to use RingCentral — verify detection in `_extract_technologies()`
6. **Digital presence**: Verify `company_presence` results include blog, social media, and advertising signals (from EXPAND-CO template expansion)
7. **pain_points.md**: Verify phone workflow, competitor section, urgency section, and enhanced Content Creation Gap all present
8. **quick_wins.md**: Verify voice AI agent in tool recommendations
9. **tech_inventory.md**: Verify phone system and voice AI rows in table
10. **Regression**: `python -m strategy_factory.main run "Test Company" --dry-run` completes without error
