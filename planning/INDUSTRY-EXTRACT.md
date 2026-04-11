# INDUSTRY-EXTRACT.md — Handoff: Fix Industry Detection

## Why This Change Is Needed

The industry fallback `"technology"` produces garbage research when no industry is provided. A landscaping/permaculture company called "Healing Roots Design" got queries about "technology industry market size" instead of landscaping/permaculture results. The research phase returned irrelevant data, and the resulting strategy documents were thin and wrong.

There are **two places** that hardcode the "technology" fallback:

1. `strategy_factory/research/orchestrator.py:98` — `industry = company_input.industry or "technology"`
2. `strategy_factory/research/query_templates.py:210` — `"industry": industry or "technology"`

The webapp form has **no industry field at all** — so every webapp run silently defaults to "technology."

## Resolution Flow

The cascade for determining industry:

1. **User provides industry in webapp form** → use it directly (no API call)
2. **Industry blank, context provided** → Perplexity extracts industry from company name + context
3. **Industry blank, no context** → Perplexity tries with just company name
4. **All fail** → empty string (queries become generic but not wrong)

**Audience context is excluded from detection.** The audience field is a profile ID (e.g., "mountain_bizworks_scaleup") pointing to a markdown file in `knowledge_base/audience/`. It describes the *cohort* (e.g., "WNC tourism-driven economy, craft/maker heritage, post-Helene recovery") — NOT the company's industry. Mixing it into industry detection would pollute the signal.

**Why empty string is the safe default:** The `{industry}` placeholder in query templates like `{industry} industry market size growth trends` becomes `industry market size growth trends` — generic but valid. "technology" would produce actively wrong results.

## Changes Required

### 1. `strategy_factory/webapp.py` — Add industry field to form

**Around line 869** (after the company name field, before the website field): Add an industry text input.

```html
<div class="form-group">
    <label for="industry">Industry</label>
    <input type="text" id="industry" name="industry"
           placeholder="e.g., landscaping, plumbing, restaurant">
    <small>Leave blank to auto-detect from company name and context.</small>
</div>
```

**Line ~1210** (in `start_analysis` route): Read the industry from the form POST data.

```python
industry = request.form.get('industry', '').strip()
```

**`run_pipeline` function**: The function signature and call site need to accept and pass `industry`:

- Add `industry` parameter to `run_pipeline` function signature (around line 1900)
- Add `industry=industry or None` to the `CompanyInput` construction (around line 1921)
- Pass `industry` through the `threading.Thread` call at the site where `run_pipeline` is invoked (around line 1289)

**Important:** Trace the full path from `start_analysis` → thread creation → `run_pipeline` → `CompanyInput` to make sure `industry` flows through every step.

### 2. `strategy_factory/research/orchestrator.py` — Add Perplexity auto-detection

**Line 98:** Replace the hardcoded fallback:

```python
# Before:
industry = company_input.industry or "technology"

# After:
industry = company_input.industry
if not industry:
    industry = self._detect_industry(company_input)
```

**New method `_detect_industry(self, company_input: CompanyInput) -> str`:**

Makes a single Perplexity `sonar` (cheapest model) call. The query should be something like:

> "What industry does {company_name} operate in? {context if provided}. Answer with just the industry name, one or two words max."

Implementation notes:
- Use `self.client` (the existing `PerplexityClient` instance) to make the call
- Use `PerplexityModel.SONAR` for cheapest cost (~$0.001)
- Parse the response to extract a short industry string from the search result snippets
- If the call fails or returns nothing useful, return `""` (empty string)
- Do NOT include audience context in this query — only company name and per-run context
- Keep max_results low (3-5 is plenty for this)
- The method should be robust: wrap in try/except, return `""` on any failure

**Where to place the method:** In the `ResearchOrchestrator` class, between `_execute_phase` and `_report_progress` (or anywhere logical within the class).

### 3. `strategy_factory/research/query_templates.py` — Remove second fallback

**Line 210:**

```python
# Before:
"industry": industry or "technology",

# After:
"industry": industry,
```

This ensures no other code path can re-introduce the "technology" default.

### 4. `strategy_factory/research/orchestrator.py` — Write detected industry back for resume

The detected industry must survive a resume. `state.json` persists the full `CompanyInput` (including its `industry` field) via Pydantic serialization. On resume, `main.py:319` loads `tracker.state.input_data` and re-runs research if incomplete — so if `industry` is still `None`, `_detect_industry` fires again (wasting a Perplexity call and risking an inconsistent result).

**Fix:** After detection, write the value back onto `company_input` so it gets persisted in `state.json`:

```python
# In research() method, after detection:
industry = company_input.industry
if not industry:
    industry = self._detect_industry(company_input)
    company_input.industry = industry  # ← write back for state.json persistence
```

No schema changes needed — `CompanyInput.industry` is already `Optional[str]` and `PipelineState.input_data` already serializes the full model.

## What NOT To Change

- Do NOT modify audience loader or audience flow — audience context stays out of industry detection
- Do NOT add keyword lists or industry taxonomies — Perplexity handles extraction
- Do NOT change any prompt files
- Do NOT change `requirements.txt` or SDK versions
- The `--industry` CLI flag already exists in `main.py` and works — no changes needed there

## Key Files Reference

| File | What to change |
|------|---------------|
| `strategy_factory/webapp.py` | Add industry form field, thread it through to `CompanyInput` |
| `strategy_factory/research/orchestrator.py` | Replace "technology" fallback with `_detect_industry()` method |
| `strategy_factory/research/query_templates.py` | Remove `"technology"` from line 210 |
| `strategy_factory/research/perplexity_client.py` | Read-only — use existing `search()` method for industry detection |
| `strategy_factory/models.py` | Read-only — `CompanyInput.industry` field already exists (Optional[str]) |

## Verification

```bash
# 1. Unit test the detection method
python -c "
from strategy_factory.models import CompanyInput
from strategy_factory.research.orchestrator import ResearchOrchestrator

orch = ResearchOrchestrator()

# Test with context
c = CompanyInput(name='Healing Roots Design', context='permaculture landscape design, Asheville NC')
print('With context:', repr(orch._detect_industry(c)))

# Test without context
c = CompanyInput(name='Healing Roots Design')
print('No context:', repr(orch._detect_industry(c)))
"

# 2. Dry run with explicit industry
python -m strategy_factory.main run "Healing Roots Design" \
  --industry "landscaping" \
  --context "permaculture landscape design, Asheville NC" \
  --dry-run

# 3. Dry run with auto-detect
python -m strategy_factory.main run "Healing Roots Design" \
  --context "permaculture landscape design, Asheville NC" \
  --dry-run

# 4. Dry run with no context (worst case)
python -m strategy_factory.main run "Some Unknown Company" --dry-run

# 5. Webapp — verify industry field appears
python -m strategy_factory.webapp
# Open http://localhost:8888, confirm industry field is in the form

# 6. Live end-to-end test
python -m strategy_factory.main run "Healing Roots Design" \
  --context "permaculture landscape design, Asheville NC"
# Check output/healing-roots-design/research_cache.json — industry queries should reference landscaping/permaculture, NOT technology
```
