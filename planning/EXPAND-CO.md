# EXPAND-CO: Expand COMPANY_PRESENCE Query Template

## Background

PERP-CALL.md proposed adding a new `ONLINE_PRESENCE` Perplexity query to capture digital presence signals (blog, LinkedIn, TikTok, YouTube, ad spend). After review, ~60% of that query overlapped with the 3 existing discovery queries (`company_presence`, `social_reviews`, `sales_channels`).

**Decision:** Expand the existing `COMPANY_PRESENCE` template instead of adding a 4th query. Same data, zero additional API cost, zero additional latency.

## What to Change

### File: `strategy_factory/research/query_templates.py`

The `COMPANY_PRESENCE` template is defined at lines 46-54 as a `QueryTemplate` dataclass.

#### Change 1: Expand the template string (line 49)

**Current:**
```python
template='"{company_name}" {context} website services location Google business listing {industry}',
```

**New:**
```python
template='"{company_name}" {context} website blog services location Google business listing LinkedIn TikTok YouTube social media activity advertising {industry}',
```

Added terms: `blog`, `LinkedIn`, `TikTok`, `YouTube`, `social media activity`, `advertising`

These are keyword-style terms — this is how all the other Perplexity query templates work in this file (e.g., `social_reviews` uses `reviews Yelp Google Facebook Instagram customers`). The Perplexity search engine uses these as search signals.

#### Change 2: Update the description (line 53)

**Current:**
```python
description="Find web presence, services, location, Google listing",
```

**New:**
```python
description="Find web presence, services, location, social media activity, advertising, Google listing",
```

### No Other Files Need Changes

- **`orchestrator.py`** — `PHASE_QUERIES` already includes `"company_presence"`. No new entry needed because we're expanding an existing query, not adding one.
- **`result_processor.py`** — Extracts description/location/year from results using regex patterns. Not dependent on query keywords.
- **`context_builder.py`** — Passes all research data to all 7 deliverable prompts automatically. No wiring needed.
- **`ALL_TEMPLATES` dict** — The `"company_presence"` key (line 150) still points to the same `COMPANY_PRESENCE` object. No re-registration needed.
- **Synthesis prompts** — All 7 prompts already receive full research context and will naturally incorporate any new digital presence data found.

## Verification

1. **Dry run:** `python -m strategy_factory.main run "Test Company" --dry-run` — confirm `company_presence` query renders with the new terms visible in the output.
2. **Live test:** `python -m strategy_factory.main run "A Real Company" --mode quick` — check `output/{company-slug}/research_cache.json` for `company_presence` key. Results should now include mentions of LinkedIn, YouTube, blog, or advertising where that data exists for the company.
3. **Synthesis check:** Open one of the generated markdown deliverables (especially `01_tools_audit.md`) and confirm digital presence data is referenced.

## Total Scope

1 file, 2 lines changed, zero new dependencies, zero new queries.
