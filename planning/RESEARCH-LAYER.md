# Research Layer Realignment — Implementation Handoff

## Why This Change

Waves 1-6 transformed the app from 15 enterprise deliverables to 6 SMB ones. The synthesis/generation layers were fully updated. The research layer was never touched. This plan fixes that.

**Current problems:**
- `tech_stack` and `ai_tools` are excluded from quick mode but are needed by `01_tools_audit` and `06_roi_snapshot`
- 3 regulatory queries run in comprehensive mode (~$0.10/run) — no SMB deliverable uses the data
- 4 competitor/leadership/funding queries collect data that no surviving prompt references
- `industry_opportunities` returns macro growth trends irrelevant to SMB AI readiness
- Query templates use enterprise language ("CEO leadership team", "enterprise software", "GDPR CCPA")
- Model selector sends the most expensive model to competitors (now unused) instead of tech stack (now critical)

**After this change:**
- Both modes run the same 10 queries (the ones the 6 SMB deliverables actually need)
- Quick = all 10 on SONAR (~$0.05). Comprehensive = all 10 with better models (~$0.41)
- The mode distinction is purely about model quality, not query scope
- No wasted API spend on competitor/regulatory/leadership/funding/opportunities data

---

## Architecture Context for the Implementer

### How the research pipeline flows

```
CompanyInput
    │
    ▼
research/orchestrator.py     ← Runs queries in phases, filters by mode
    │
    ├── query_templates.py   ← Defines 18 QueryTemplates with category, priority, required_for_quick_mode
    ├── model_selector.py    ← Picks Perplexity model per query category + mode
    └── perplexity_client.py ← Calls Perplexity API
    │
    ▼
research/result_processor.py ← Extracts structured data from raw search results
    │
    ▼
ResearchOutput (Pydantic model)
    ├── profile: CompanyProfile
    ├── industry: IndustryContext
    ├── competitors: List[CompetitorProfile]     ← DEAD: no consumer
    ├── tech_landscape: TechLandscape
    ├── regulatory: RegulatoryContext             ← DEAD: no consumer
    └── user_context: ValidatedUserContext
    │
    ▼
synthesis/context_builder.py ← Formats research sections into prompt context
    │
    ▼
build_full_prompt() includes:
    - company_profile    ✓ used by prompts
    - industry_context   ✓ used by prompts
    - tech_landscape     ✓ used by prompts
    - competitors        ✗ formatted but NOT included in prompt
    - regulatory_context ✗ formatted but NOT included in prompt
```

### Which deliverables need which research

| Deliverable | company_profile | industry_context | tech_landscape | Dependencies |
|---|---|---|---|---|
| 01_tools_audit (Where You Stand Today) | Yes | Yes | **Yes — tech_stack is critical** | None |
| 02_daily_pain_points (Where You're Losing Money) | Yes | Yes | No | None |
| 03_action_plan (What To Do First) | Yes | Yes | No | 02 |
| 04_simple_roadmap (Your Week-by-Week Plan) | Yes | Yes | No | 03 |
| 05_readiness_assessment (Your AI Readiness) | Yes | Yes | **Yes — tech_stack + AI adoption** | 01, 02 |
| 06_roi_snapshot (What It Costs & What You Save) | Yes | Yes | **Yes — ai_tools is critical** | 03 |

**What NO deliverable needs:** competitors, regulatory, leadership, funding, industry_opportunities

### Current query templates (18 total)

**Quick mode runs these 8** (required_for_quick_mode=True):
1. `company_overview` — COMPANY_PROFILE
2. `company_details` — COMPANY_PROFILE
3. `recent_news` — NEWS
4. `industry_overview` — INDUSTRY
5. `industry_challenges` — INDUSTRY
6. `competitors_list` — COMPETITORS ← DEAD, no prompt uses it
7. `ai_initiatives` — AI_INITIATIVES
8. `industry_ai_adoption` — AI_INITIATIVES
9. `ai_use_cases` — AI_INITIATIVES

**Comprehensive adds these 10** (required_for_quick_mode=False):
10. `leadership` — LEADERSHIP ← DEAD
11. `funding_status` — FUNDING ← DEAD
12. `industry_opportunities` — INDUSTRY ← DEAD (macro trends, irrelevant to SMB AI readiness)
13. `competitor_ai` — COMPETITORS ← DEAD
14. `tech_stack` — TECHNOLOGY ← NEEDED by 01 and 05
15. `ai_tools` — AI_INITIATIVES ← NEEDED by 06
16. `industry_regulations` — REGULATORY ← DEAD
17. `ai_regulations` — REGULATORY ← DEAD
18. `data_privacy` — REGULATORY ← DEAD

---

## Implementation — 6 Files to Change

### File 1: `strategy_factory/research/query_templates.py`

**Remove 4 enum members** from `QueryCategory` (line ~15-25):
- `COMPETITORS`, `REGULATORY`, `LEADERSHIP`, `FUNDING`

**Delete 8 template constants** and their `ALL_TEMPLATES` entries:
- `LEADERSHIP` (line ~72-80)
- `FUNDING_STATUS` (line ~82-90)
- `INDUSTRY_OPPORTUNITIES` (line ~123-131)
- `COMPETITORS_LIST` (line ~133-142)
- `COMPETITOR_AI` (line ~144-152)
- `INDUSTRY_REGULATIONS` (line ~205-213)
- `AI_REGULATIONS` (line ~215-223)
- `DATA_PRIVACY` (line ~225-233)

**Change `required_for_quick_mode`** on 2 templates:
- `TECH_STACK` (line ~157): `False` → `True`
- `AI_TOOLS` (line ~197): `False` → `True`

**Rewrite 2 template strings** for SMB language:
- `TECH_STACK.template` (line ~159): `'{company_name} technology stack software platforms tools infrastructure'` → `'{company_name} tools software apps used daily operations {industry}'`
- `AI_TOOLS.template` (line ~199): `'{industry} recommended AI tools platforms enterprise software {current_year}'` → `'{industry} AI tools small business affordable recommended {current_year}'`

**Result:** 18 templates → 10. Both modes run all 10.

The 10 remaining templates:
1. `company_overview` — COMPANY_PROFILE, quick=True
2. `company_details` — COMPANY_PROFILE, quick=True
3. `recent_news` — NEWS, quick=True
4. `industry_overview` — INDUSTRY, quick=True
5. `industry_challenges` — INDUSTRY, quick=True
6. `tech_stack` — TECHNOLOGY, quick=True (was False)
7. `ai_initiatives` — AI_INITIATIVES, quick=True
8. `industry_ai_adoption` — AI_INITIATIVES, quick=True
9. `ai_use_cases` — AI_INITIATIVES, quick=True
10. `ai_tools` — AI_INITIATIVES, quick=True (was False)

---

### File 2: `strategy_factory/research/model_selector.py`

**Remove `CATEGORY_MODELS` entries** for deleted categories (lines ~39-76):
- `COMPETITORS`, `REGULATORY`, `LEADERSHIP`, `FUNDING`

**Reallocate models** for SMB priorities:
- `TECHNOLOGY` comprehensive: `SONAR_PRO` → `SONAR_DEEP_RESEARCH` (tech stack is the highest-value SMB research)
- `AI_INITIATIVES` comprehensive: `SONAR_DEEP_RESEARCH` → `SONAR_PRO` (no longer needs deep research)

**Keep unchanged:** `TIER_UPGRADES` dict, `select_model()` method, `_estimate_query_cost()`, `get_model_info()`

**Update docstring** (lines ~36-37) to remove references to "Competitive Intelligence" and "Regulatory Context".

The new `CATEGORY_MODELS` dict:
```python
CATEGORY_MODELS: Dict[QueryCategory, Dict[ResearchMode, PerplexityModel]] = {
    QueryCategory.COMPANY_PROFILE: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR_PRO,
    },
    QueryCategory.INDUSTRY: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR_PRO,
    },
    QueryCategory.TECHNOLOGY: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR_DEEP_RESEARCH,
    },
    QueryCategory.AI_INITIATIVES: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR_PRO,
    },
    QueryCategory.NEWS: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR,
    },
}
```

---

### File 3: `strategy_factory/research/orchestrator.py`

**Remove `PHASE_QUERIES` entries** (lines ~41-72):
- `company_deep_dive` (was: leadership, funding_status)
- `competitive_intelligence` (was: competitors_list, competitor_ai)
- `regulatory_context` (was: industry_regulations, ai_regulations, data_privacy)
- Remove `industry_opportunities` from `industry_analysis` phase

**New `PHASE_QUERIES`:**
```python
PHASE_QUERIES = {
    "initial_discovery": [
        "company_overview",
        "company_details",
        "recent_news",
    ],
    "industry_analysis": [
        "industry_overview",
        "industry_challenges",
    ],
    "technology_landscape": [
        "tech_stack",
        "ai_initiatives",
        "industry_ai_adoption",
        "ai_use_cases",
        "ai_tools",
    ],
}
```

**In `research()` method** (lines ~104-181), remove:
- The `company_deep_dive` conditional block (~lines 137-143, including the `info_tier` check for `PRIVATE_LIMITED`/`STARTUP_STEALTH`)
- The `competitive_intelligence` phase execution (~lines 149-151)
- The `regulatory_context` conditional block (~lines 157-160)

**Renumber progress percentages:**
- `initial_discovery`: 0.05 → 0.15
- Info tier detection: 0.15 → 0.25
- `industry_analysis`: 0.35 → 0.4
- `technology_landscape`: 0.65 → 0.7
- `audience_supplemental`: 0.88 → 0.85
- Processing: 0.9
- Complete: 1.0

**Keep `info_tier` detection** — still set on `ResearchOutput`, useful for future logic.

**Update class docstring** (lines ~30-38) to remove references to phases 2, 4, 6.

---

### File 4: `strategy_factory/research/result_processor.py`

**Remove these methods entirely:**
- `extract_competitors()` and helpers (`_extract_competitor_names`, `_extract_competitor_ai`)
- `extract_regulatory_context()` and helpers (`_extract_regulations`, `_extract_privacy_requirements`)

**In `extract_company_profile()`:** Remove the blocks that look up `results.get("leadership")` and `results.get("funding_status")`.

**In `extract_industry_context()`:** Remove the opportunities extraction block (the one that populates `industry.opportunities` from `results.get("industry_opportunities")`).

**In `build_research_output()`** (~line 406-419):
- Change `competitors=self.extract_competitors(results)` → `competitors=[]`
- Change `regulatory=self.extract_regulatory_context(results)` → `regulatory=RegulatoryContext()`

**In `_calculate_confidence()`:** Remove `competitors` and `regulatory` entries from the sections dict, add `ai_tools`.

**Keep imports** of `CompetitorProfile` and `RegulatoryContext` — needed for backward compatibility with cached JSON.

---

### File 5: `strategy_factory/synthesis/context_builder.py`

**Remove methods:**
- `_format_competitors()` (~lines 164-181)
- `_format_regulatory_context()` (~lines 216-234)

**In `build_context()`** (~lines 64-91):
- Remove `"competitors"` key (~line 77)
- Remove `"regulatory_context"` key (~line 79)

**In `_format_industry_context()`** (~lines 136-162):
- Remove the `if industry.opportunities:` block (~lines 158-160)

**In `_format_company_profile()`** (~lines 95-134):
- Remove `if profile.leadership:` block (~lines 117-122)
- Remove `if profile.funding_status:` block (~lines 124-125)

**No changes to `build_full_prompt()`** — it already only includes `company_profile`, `industry_context`, `tech_landscape` in `prompt_parts` (~lines 330-336). The competitors and regulatory keys were computed but never added to the prompt.

---

### File 6: `strategy_factory/research/__init__.py`

**Update module docstring** (lines ~3-11): Remove "Competitor intelligence" and "Regulatory context" from the feature bullets.

---

## Files NOT Changed (and why)

| File | Why no changes |
|---|---|
| `strategy_factory/models.py` | `ResearchOutput.competitors` and `ResearchOutput.regulatory` fields must stay with default factories for backward compat with old `research_cache.json` files. Same for `CompanyProfile.leadership`, `CompanyProfile.funding_status`, `IndustryContext.opportunities`. |
| `strategy_factory/config.py` | `ResearchMode` enum stays unchanged. `RESEARCH_MODE_MODELS` dict stays — it defines which Perplexity models are available per mode, and both SONAR/SONAR_PRO/SONAR_DEEP_RESEARCH are still needed. |
| `strategy_factory/research/perplexity_client.py` | No changes — it's a generic API client. |
| `strategy_factory/audience_loader.py` | No changes — audience queries are mode-agnostic and stay that way. |
| `strategy_factory/synthesis/orchestrator.py` | No changes — GENERATION_ORDER already updated in Waves 1-3. |
| `strategy_factory/synthesis/prompts/*.py` | No changes — the 6 SMB prompts are already SMB-focused. |

## Backward Compatibility

- **`models.py` fields stay:** `competitors`, `regulatory`, `leadership`, `funding_status`, `opportunities` all have default factories. Old `research_cache.json` files deserialize without error.
- **Old cache entries are harmless:** The orchestrator's `load_research_cache()` reconstructs results by name. Old caches will have entries like `"competitors_list"` that simply sit unused in `self.results`. The new `build_research_output()` hardcodes empty competitors/regulatory, so stale cached data is ignored.
- **No external consumers of `QueryCategory`:** Only used within `research/` and `model_selector.py`, both updated in this plan.

## Cost Impact

| Mode | Before | After | Change |
|------|--------|-------|--------|
| Quick | 8 queries, SONAR only (~$0.05) | 10 queries, SONAR only (~$0.052) | +$0.002 — but now collects data deliverables actually need |
| Comprehensive | 18 queries, mixed models (~$0.50) | 10 queries, mixed models (~$0.41) | -$0.09 — cuts dead queries, upgrades tech stack research |

## Verification

```bash
# 1. Import check — should print 10, no errors
python -c "from strategy_factory.research.query_templates import QueryTemplates; t = QueryTemplates(); print(len(t.ALL_TEMPLATES))"

# 2. Quick mode dry run — should include tech_stack and ai_tools
python -m strategy_factory.main run "Test Company" --mode quick --dry-run

# 3. Comprehensive mode dry run — should show same 10 queries, no dead phases
python -m strategy_factory.main run "Test Company" --mode comprehensive --dry-run

# 4. End-to-end quick mode
python -m strategy_factory.main run "Burris Chalmers Communications" --mode quick
# Verify: 6 markdown files, DOCX, PDF, PPTX all generated
# Verify: "Where You Stand Today" references specific tools (not generic guesses)

# 5. End-to-end comprehensive mode
python -m strategy_factory.main run "Burris Chalmers Communications" --mode comprehensive
# Verify: deeper tech stack data than quick mode
# Verify: research_cache.json has no competitor/regulatory/leadership/funding/opportunities entries
```
