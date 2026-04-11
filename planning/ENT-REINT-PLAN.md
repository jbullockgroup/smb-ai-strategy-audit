# Dual-Mode Feasibility Report: SMB + Enterprise

## What's Different Between the Two Repos

| Component | Current (SMB) | Old (Enterprise) |
|---|---|---|
| **Deliverables** | 7 markdown + docx/pdf | 15 markdown + pptx + docx/pdf + SOW |
| **Prompts** | 8 files, conversational tone ("You are an SMB AI strategist writing directly to a business owner") | 15 files, corporate tone ("Generate Technology Inventory & Data Infrastructure Assessment") |
| **Consulting Guides** | 13 SMB-focused guides (no `_TLDR` suffix, `.md`) | 11 enterprise guides (`_TLDR.md` suffix) from BCG, KPMG, McKinsey, Google Cloud |
| **Perplexity Queries** | 11 queries, 3 categories (discovery, industry, AI opportunity), SMB-focused keywords | 18 queries, 9 categories (profile, industry, competitors, tech, AI, regulatory, news, leadership, funding) |
| **Query Tone** | `"small business"`, `"Etsy Shopify"`, `"farmers market"` | `"enterprise software"`, `"GDPR CCPA"`, `"CEO leadership"` |
| **Config** | Simple deliverables, no topic mapping | Deliverables + `TLDR_TOPIC_MAPPING` + `CompanySize` enum + `SOW_PRICING` + framework extraction |
| **Knowledge Loader** | Simpler, no topic loading, no framework extraction | Has `load_for_topic()`, `extract_framework()`, `get_key_frameworks()` |

## What's the Same (Shared Infrastructure)

- Pipeline architecture: research -> synthesis -> generation
- Perplexity model selection (sonar/pro/deep-research)
- Gemini 2.5 Flash for synthesis
- Temporal context injection
- Progress tracking / resume
- DOCX and PDF generation
- Quality domain filtering
- Retry config

## Assessment: How Hard to Add Enterprise Mode?

**Moderate effort, no serious refactoring.** Here's why:

The codebase is already well-factored — the "mode-dependent" stuff lives in just a few places:

1. **`config.py`** — The `DELIVERABLES` dict determines everything downstream. You'd make it mode-aware (one dict for SMB, one for enterprise, selected at startup).

2. **`synthesis/prompts/`** — You'd add the enterprise prompt files back (15 files from the old repo). The `__init__.py` already maps deliverable IDs to prompts — just needs a mode switch.

3. **`research/query_templates.py`** — You'd need two `QueryTemplates` classes (or one class with two template sets). The enterprise version has 18 queries vs 11 for SMB.

4. **`Consulting Guides TLDR/`** — You'd need both sets of guides on disk. The enterprise guides already exist in the old repo. The loader just needs to know which directory/set to use.

5. **`knowledge_loader.py`** — Needs the enterprise version's `load_for_topic()`, `TLDR_TOPIC_MAPPING`, and framework extraction helpers restored.

6. **Generation phase** — The old repo had PPTX generation (executive summary deck + full findings presentation) and an SOW document. You removed those. You'd need to decide if enterprise mode includes those or just does DOCX/PDF like SMB.

## What Would Need to Change (the touchpoints)

The mode selection would flow through ~6 files:

| File | Change |
|---|---|
| `config.py` | Two `DELIVERABLES` dicts (or parameterized), two guide mappings |
| `models.py` | Add `company_mode: str = "smb"` to `CompanyInput` |
| `query_templates.py` | Enterprise template set alongside SMB set |
| `synthesis/prompts/__init__.py` | Load correct prompts based on mode |
| `knowledge_loader.py` | Restore topic loading + framework extraction for enterprise |
| `webapp.py` / `server.py` | Add mode selector to the form |
| `main.py` / CLI | Add `--mode enterprise` flag |

## Verdict

**Totally doable.** The architecture is clean enough that this is a "add a mode parameter and fork the content" job, not a "rewrite the pipeline" job. The hardest part isn't code — it's curating the content (prompts, guides, queries) for each mode. You already have both sets. The code changes are mostly wiring.

## Perplexity Query Comparison

### SMB Queries (11 total, 3 categories)

**Phase 1 — Company Discovery (4 queries):**
- `company_presence` — web presence, services, location, social media, advertising
- `social_reviews` — reviews on Yelp, Google, Facebook, Instagram
- `sales_channels` — Etsy, Shopify, online store, wholesale, farmers market
- `competitor_discovery` — competitors, similar companies, alternatives

**Phase 2 — Industry Intelligence (4 queries):**
- `industry_overview` — market size, growth trends
- `industry_challenges` — small business challenges, pain points
- `industry_tools` — small business software, apps
- `industry_operations` — daily operations, workflows, customer interactions

**Phase 3 — AI Opportunity (3 queries):**
- `industry_ai_examples` — AI automation examples, small business case studies
- `industry_ai_tools` — AI tools for small business, affordable
- `industry_ai_trends` — AI adoption trends, small business owners using

All 11 queries are `required_for_quick_mode=True`.

### Enterprise Queries (18 total, 9 categories)

**Company Profile (2 queries):**
- `company_overview` — business model, products, services
- `company_details` — headquarters, employee count, company size, founded year

**Industry (3 queries):**
- `industry_overview` — market size, growth trends
- `industry_challenges` — challenges, pain points
- `industry_opportunities` — growth areas, emerging trends

**Competitors (2 queries):**
- `competitors_list` — main competitors, alternatives
- `competitor_ai` — competitor AI adoption, initiatives

**Technology (1 query):**
- `tech_stack` — technology stack, platforms, tools, infrastructure

**AI Initiatives (4 queries):**
- `ai_initiatives` — company-specific AI projects
- `industry_ai_adoption` — industry-wide AI adoption rate
- `ai_use_cases` — industry-specific AI use cases, generative AI
- `ai_tools` — recommended AI tools, enterprise software

**Regulatory (3 queries):**
- `industry_regulations` — industry-specific regulations, compliance
- `ai_regulations` — AI-specific regulations, compliance
- `data_privacy` — GDPR, CCPA, compliance

**News (1 query):**
- `recent_news` — latest announcements, developments

**Leadership (1 query):**
- `leadership` — CEO, executives, management team

**Funding (1 query):**
- `funding_status` — investment, valuation, investors

Quick mode = 9 queries. Comprehensive = all 18.
