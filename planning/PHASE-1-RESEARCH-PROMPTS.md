# Phase 1: Restructure Research Queries for SMB Targeting

## Why This Change

The research queries were designed for enterprise companies with public profiles — companies that have published tech stacks, press releases, C-suite bios, and AI strategy documents. For the actual target audience — established SMBs like the ones in Mountain BizWorks ScaleUp Cohort 14 — 5 of 10 Perplexity queries return near-zero results.

**ScaleUp WNC Cohort 14 example businesses:**
- Black Mountain Yarn Shop (retail, fiber arts)
- Clean Mountain Escapes (residential/vacation rental cleaning)
- Spice Witch (chili oils/crisps, food CPG)
- Healing Roots Design (permaculture landscape design)
- Light + Love Arts (children's art studio)
- Sarah Hearts (sewing notions, e-commerce/wholesale)
- Polygons Tile & Hardwood (tile showroom)
- Burris Chalmers Communications (nonprofit communications)
- Good People Technologies (systems/automation consulting)
- Green Go Cleaning Co. (eco-conscious cleaning)
- Habibi Village (gluten-free Lebanese flatbread)
- Kimberly Hodges Art & Design (nature-inspired home accents)
- The High Fiber (illustration and print studio)

**Eligibility:** $150K-$2.5M revenue, 2+ years in business, 1+ employee, WNC-based, growth-oriented.

**The core insight:** For SMBs, industry research IS company research. The current queries try to find out what a company's tech stack is. The right question is: "what does a local yarn shop's Tuesday look like, and what tools do similar shops use?" That's answerable. "Black Mountain Yarn Shop AI initiatives" is not.

**What fails today:**

| Current Query | Template | SMB Result |
|---|---|---|
| `company_overview` | "{company_name} company overview business model products services" | Near-zero. Local shops aren't on Crunchbase. |
| `company_details` | "{company_name} headquarters location employee count company size" | Maybe a location. "Headquarters" is enterprise language. |
| `recent_news` | "{company_name} latest news announcements developments" | Nothing. Local shops don't issue press releases. |
| `tech_stack` | "{company_name} tools software apps used daily operations" | Nothing. SMBs don't publish tech stacks. |
| `ai_initiatives` | "{company_name} AI artificial intelligence machine learning initiatives" | Zero. Guaranteed. |

Half the Perplexity budget is spent on queries that return nothing. The synthesis prompts then get `No technology landscape information available` in the context, and Gemini has to guess everything from scratch.

**The fix:** Pivot from company-specific enterprise queries to rich industry intelligence that the synthesis can map onto the business. Same 10 queries, same cost, dramatically better data. Gemini is an LLM — it can extract tool names, sentiment, and patterns from raw research snippets without us doing regex keyword matching in Python.

---

## Files to Modify (in order)

| # | File | What Changes |
|---|------|-------------|
| 1 | `strategy_factory/research/query_templates.py` | Replace all 10 query templates + update categories |
| 2 | `strategy_factory/research/model_selector.py` | Update `CATEGORY_MODELS` for new categories |
| 3 | `strategy_factory/research/orchestrator.py` | Update `PHASE_QUERIES` and phase name strings |
| 4 | `strategy_factory/research/result_processor.py` | Update query name references + SMB keyword list |

No model or context_builder changes needed. The existing Pydantic fields carry the data fine — new queries produce better raw results that flow through existing extraction into existing formatted text for Gemini. If structured fields (social media, reviews, sales channels) prove necessary after testing real output, they're a trivial follow-up.

---

## Step 1: Query Templates (`strategy_factory/research/query_templates.py`)

### 1a. Update `QueryCategory` enum (lines 15-21)

Replace:
```python
class QueryCategory(str, Enum):
    COMPANY_PROFILE = "company_profile"
    INDUSTRY = "industry"
    TECHNOLOGY = "technology"
    AI_INITIATIVES = "ai_initiatives"
    NEWS = "news"
```

With:
```python
class QueryCategory(str, Enum):
    COMPANY_DISCOVERY = "company_discovery"    # Phase 1: Find the business online
    INDUSTRY = "industry"                      # Phase 2: Industry intelligence
    AI_OPPORTUNITY = "ai_opportunity"          # Phase 3: AI opportunity mapping
```

### 1b. Replace all 10 template definitions (lines 47-148)

Delete all 10 current templates. Add these 10:

#### Phase 1 — Company Discovery (3 queries)

```python
COMPANY_PRESENCE = QueryTemplate(
    name="company_presence",
    category=QueryCategory.COMPANY_DISCOVERY,
    template='"{company_name}" {context} website services location Google business listing {industry}',
    recency_filter="year",
    priority=1,
    required_for_quick_mode=True,
    description="Find web presence, services, location, Google listing",
)

SOCIAL_REVIEWS = QueryTemplate(
    name="social_reviews",
    category=QueryCategory.COMPANY_DISCOVERY,
    template='"{company_name}" reviews Yelp Google Facebook Instagram customers {context}',
    recency_filter="year",
    priority=2,
    required_for_quick_mode=True,
    description="Find social media activity, customer reviews, reputation",
)

SALES_CHANNELS = QueryTemplate(
    name="sales_channels",
    category=QueryCategory.COMPANY_DISCOVERY,
    template='"{company_name}" Etsy Shopify online store wholesale farmers market e-commerce {industry}',
    recency_filter="year",
    priority=2,
    required_for_quick_mode=True,
    description="Find e-commerce presence, platforms, wholesale channels",
)
```

**Design notes:**
- Company name wrapped in quotes forces Perplexity to treat it as a literal phrase. This prevents "Black Mountain" energy company showing up for "Black Mountain Yarn Shop."
- `{context}` is injected directly into discovery queries to help disambiguate (e.g., "fiber arts" or "Black Mountain NC"). Users can pass `--context "fiber arts, Black Mountain NC"` for better results.
- `recency_filter="year"` for all discovery queries since business presence is relatively stable.
- These 3 queries replace 3 that returned nothing: `company_overview`, `company_details`, `recent_news`.

#### Phase 2 — Industry Intelligence (4 queries)

```python
INDUSTRY_OVERVIEW = QueryTemplate(
    name="industry_overview",
    category=QueryCategory.INDUSTRY,
    template='{industry} industry market size growth trends {current_year}',
    recency_filter="year",
    priority=1,
    required_for_quick_mode=True,
    description="Industry overview and market analysis",
)

INDUSTRY_CHALLENGES = QueryTemplate(
    name="industry_challenges",
    category=QueryCategory.INDUSTRY,
    template='{industry} small business challenges pain points operations problems {current_year}',
    recency_filter="year",
    priority=2,
    required_for_quick_mode=True,
    description="Industry challenges specific to small businesses",
)

INDUSTRY_TOOLS = QueryTemplate(
    name="industry_tools",
    category=QueryCategory.INDUSTRY,
    template='{industry} small business software tools apps commonly used {current_year}',
    recency_filter="year",
    priority=2,
    required_for_quick_mode=True,
    description="Common software and tools used in this industry",
)

INDUSTRY_OPERATIONS = QueryTemplate(
    name="industry_operations",
    category=QueryCategory.INDUSTRY,
    template='{industry} small business daily operations workflows customer interactions marketing {current_year}',
    recency_filter="year",
    priority=2,
    required_for_quick_mode=True,
    description="Daily workflows, customer interaction patterns, marketing channels",
)
```

**Design notes:**
- `INDUSTRY_OVERVIEW` is unchanged — it already works well for SMBs.
- `INDUSTRY_CHALLENGES` adds "small business" and "operations" to focus results.
- `INDUSTRY_TOOLS` replaces `tech_stack` (company-specific → industry-level). This is the query that tells synthesis "a yarn shop probably uses Shopify, QuickBooks, and Mailchimp."
- `INDUSTRY_OPERATIONS` is entirely new. It feeds the pain points and roadmap sections with real workflow descriptions.

#### Phase 3 — AI Opportunity (3 queries)

```python
INDUSTRY_AI_EXAMPLES = QueryTemplate(
    name="industry_ai_examples",
    category=QueryCategory.AI_OPPORTUNITY,
    template='{industry} AI automation examples small business case studies real implementations {current_year}',
    recency_filter="month",
    priority=1,
    required_for_quick_mode=True,
    description="Real AI automation examples for this industry",
)

INDUSTRY_AI_TOOLS = QueryTemplate(
    name="industry_ai_tools",
    category=QueryCategory.AI_OPPORTUNITY,
    template='{industry} AI tools small business affordable recommended {current_year}',
    recency_filter="month",
    priority=2,
    required_for_quick_mode=True,
    description="Recommended AI tools for the industry",
)

INDUSTRY_AI_TRENDS = QueryTemplate(
    name="industry_ai_trends",
    category=QueryCategory.AI_OPPORTUNITY,
    template='{industry} AI adoption trends small business owners using {current_month_year}',
    recency_filter="month",
    priority=1,
    required_for_quick_mode=True,
    description="SMB AI adoption trends in this industry",
)
```

**Design notes:**
- `INDUSTRY_AI_TOOLS` is unchanged — it already mentions "small business affordable."
- `INDUSTRY_AI_EXAMPLES` replaces `ai_initiatives` (company-specific → industry-level). "AI automation examples small business case studies" returns real stories like "how a cleaning company automated scheduling."
- `INDUSTRY_AI_TRENDS` replaces `industry_ai_adoption` with SMB-focused framing. Uses `recency_filter="month"` and `{current_month_year}` for freshness.

### 1c. Update `ALL_TEMPLATES` dict (lines 151-162)

Replace with:
```python
ALL_TEMPLATES: Dict[str, QueryTemplate] = {
    "company_presence": COMPANY_PRESENCE,
    "social_reviews": SOCIAL_REVIEWS,
    "sales_channels": SALES_CHANNELS,
    "industry_overview": INDUSTRY_OVERVIEW,
    "industry_challenges": INDUSTRY_CHALLENGES,
    "industry_tools": INDUSTRY_TOOLS,
    "industry_operations": INDUSTRY_OPERATIONS,
    "industry_ai_examples": INDUSTRY_AI_EXAMPLES,
    "industry_ai_tools": INDUSTRY_AI_TOOLS,
    "industry_ai_trends": INDUSTRY_AI_TRENDS,
}
```

---

## Step 2: Model Selector (`strategy_factory/research/model_selector.py`)

### Update `CATEGORY_MODELS` dict (lines 39-60)

Replace the entire dict:
```python
CATEGORY_MODELS: Dict[QueryCategory, Dict[ResearchMode, PerplexityModel]] = {
    QueryCategory.COMPANY_DISCOVERY: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR_PRO,
    },
    QueryCategory.INDUSTRY: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR_PRO,
    },
    QueryCategory.AI_OPPORTUNITY: {
        ResearchMode.QUICK: PerplexityModel.SONAR,
        ResearchMode.COMPREHENSIVE: PerplexityModel.SONAR_DEEP_RESEARCH,
    },
}
```

Removes old `NEWS`, `TECHNOLOGY`, `COMPANY_PROFILE`, `AI_INITIATIVES` entries. `AI_OPPORTUNITY` gets `SONAR_DEEP_RESEARCH` in comprehensive mode because AI opportunity discovery benefits from deeper research.

---

## Step 3: Orchestrator (`strategy_factory/research/orchestrator.py`)

### 3a. Update `PHASE_QUERIES` dict (lines 38-55)

Replace with:
```python
PHASE_QUERIES = {
    "company_discovery": [
        "company_presence",
        "social_reviews",
        "sales_channels",
    ],
    "industry_analysis": [
        "industry_overview",
        "industry_challenges",
        "industry_tools",
        "industry_operations",
    ],
    "ai_opportunity": [
        "industry_ai_examples",
        "industry_ai_tools",
        "industry_ai_trends",
    ],
}
```

### 3b. Update phase name strings in `research()` method

- Line ~105: `"initial_discovery"` → `"company_discovery"`
- Line ~118: Keep `"industry_analysis"` (unchanged)
- Line ~126: `"technology_landscape"` → `"ai_opportunity"`

### 3c. Cache compatibility

The `load_research_cache` method (line 248) stores results by name from the JSON file without validating against `PHASE_QUERIES`. Old cache files with keys like `company_overview` will load fine — they just won't be referenced by the new extraction methods. The result processor uses fallback lookups (see Step 4).

---

## Step 4: Result Processor (`strategy_factory/research/result_processor.py`)

Four targeted changes: update query name references in existing methods, update the tech keyword list, adjust SMB info tier detection, and fix confidence scoring.

### 4a. Update `INFO_TIER_INDICATORS` (lines 40-45)

Add SMB signals to `PUBLIC_MEDIUM`:
```python
INFO_TIER_INDICATORS = {
    CompanyInfoTier.PUBLIC_LARGE: [
        "publicly traded", "nyse", "nasdaq", "fortune 500", "s&p 500",
    ],
    CompanyInfoTier.PUBLIC_MEDIUM: [
        "founded", "headquarters", "ceo", "products",
        "google reviews", "yelp", "facebook page", "instagram",
    ],
    CompanyInfoTier.PRIVATE_LIMITED: [
        "private company", "privately held",
    ],
    CompanyInfoTier.STARTUP_STEALTH: [
        "stealth", "early-stage", "pre-launch",
    ],
}
```

SMBs with Google listings and Yelp reviews should map to `PUBLIC_MEDIUM`, not `PRIVATE_LIMITED`.

### 4b. Lower result-count thresholds in `detect_info_tier` (lines 81-88)

```python
# Fall back to result count heuristic (SMB-adjusted)
if total_results >= 15:
    return CompanyInfoTier.PUBLIC_LARGE
elif total_results >= 5:    # was >= 8
    return CompanyInfoTier.PUBLIC_MEDIUM
elif total_results >= 2:    # was >= 3
    return CompanyInfoTier.PRIVATE_LIMITED
else:
    return CompanyInfoTier.STARTUP_STEALTH
```

A local business with 2 results is normal, not "stealth."

### 4c. Update `extract_company_profile` query name lookups (lines 114-157)

Map new query names with backward-compat fallbacks. Reuse existing extraction helpers — no new methods needed:

```python
def extract_company_profile(self, company_name: str, results: Dict[str, QueryResult]) -> CompanyProfile:
    profile = CompanyProfile()
    sources = set()

    # Extract from company presence (backward compat: also check old query names)
    presence = results.get("company_presence") or results.get("company_overview")
    if presence and presence.results:
        profile.description = self._extract_first_paragraph(presence.results)
        profile.headquarters = self._extract_location(presence.results)
        profile.founded_year = self._extract_year(presence.results, "founded")
        profile.products_services = self._extract_products(profile.description) if profile.description else []
        sources.update(r.url for r in presence.results)

    # Also check company_details for backward compat
    details = results.get("company_details")
    if details and details.results:
        if not profile.employee_estimate:
            profile.employee_estimate = self._extract_employee_count([details])
        if not profile.headquarters:
            profile.headquarters = self._extract_location(details.results)
        if not profile.founded_year:
            profile.founded_year = self._extract_year(details.results, "founded")
        sources.update(r.url for r in details.results)

    # Extract from social/reviews — populate recent_news field for backward compat
    reviews = results.get("social_reviews") or results.get("recent_news")
    if reviews and reviews.results:
        profile.recent_news = self._extract_news(reviews.results)
        sources.update(r.url for r in reviews.results)

    profile.sources = list(sources)[:10]
    return profile
```

### 4d. Update `extract_tech_landscape` query name lookups (lines 193-240)

Map new query names with backward-compat fallbacks:

```python
def extract_tech_landscape(self, results: Dict[str, QueryResult]) -> TechLandscape:
    landscape = TechLandscape()
    sources = set()

    # industry_tools -> populate tech stack (repurposed for industry-level)
    tools = results.get("industry_tools") or results.get("tech_stack")
    if tools and tools.results:
        landscape.company_tech_stack = self._extract_technologies(tools.results)
        sources.update(r.url for r in tools.results)

    # industry_ai_examples -> replaces ai_initiatives
    ai_examples = results.get("industry_ai_examples") or results.get("ai_initiatives")
    if ai_examples and ai_examples.results:
        landscape.company_ai_initiatives = self._extract_ai_initiatives(ai_examples.results)
        sources.update(r.url for r in ai_examples.results)

    # industry_ai_trends -> replaces industry_ai_adoption
    trends = results.get("industry_ai_trends") or results.get("industry_ai_adoption")
    if trends and trends.results:
        landscape.industry_ai_adoption_rate = self._extract_adoption_rate(trends.results)
        sources.update(r.url for r in trends.results)

    # industry_ai_tools -> same purpose, check both old and new key
    ai_tools = results.get("industry_ai_tools") or results.get("ai_tools")
    if ai_tools and ai_tools.results:
        landscape.recommended_ai_tools = self._extract_tools(ai_tools.results)
        sources.update(r.url for r in ai_tools.results)

    # ai_use_cases -> backward compat only (removed from new queries)
    use_cases = results.get("ai_use_cases")
    if use_cases and use_cases.results:
        landscape.industry_ai_use_cases = self._extract_use_cases(use_cases.results)
        sources.update(r.url for r in use_cases.results)

    landscape.sources = list(sources)[:10]
    return landscape
```

### 4e. Update `_extract_technologies` keyword list (lines 489-504)

This is the one extraction change that actually matters. The current list has `"aws", "azure", "gcp", "kubernetes"` — those will never match SMB research results. Replace with SMB-relevant tools:

```python
def _extract_technologies(self, results: List[SearchResult]) -> List[str]:
    """Extract technology names (SMB-focused)."""
    tech_keywords = [
        # Accounting/Finance
        "quickbooks", "freshbooks", "xero", "wave accounting", "square",
        # Website/E-commerce
        "shopify", "squarespace", "wix", "wordpress", "woocommerce",
        "bigcartal", "etsy",
        # Productivity
        "google workspace", "g suite", "microsoft 365", "notion",
        "trello", "asana", "monday.com",
        # Marketing
        "mailchimp", "constant contact", "canva", "hootsuite",
        "buffer", "later",
        # Scheduling
        "calendly", "acuity", "bookedin", "square appointments",
        # POS/Retail
        "square", "toast", "lightspeed", "shopkeep", "vend",
        # CRM
        "hubspot", "salesforce", "zoho", "keap", "insightly",
    ]
    found = []
    for r in results:
        text = r.snippet.lower()
        for tech in tech_keywords:
            if tech in text and tech.title() not in found:
                found.append(tech.title())
    return found[:10]
```

### 4f. Update `_calculate_confidence` query names (lines 559-585)

```python
def _calculate_confidence(self, results: Dict[str, QueryResult]) -> Dict[str, float]:
    """Calculate confidence scores for each research section."""
    confidence = {}

    sections = {
        "profile": ["company_presence", "social_reviews"],
        "industry": ["industry_overview", "industry_challenges", "industry_tools"],
        "technology": ["industry_ai_examples", "industry_ai_tools"],
    }

    for section, queries in sections.items():
        total_results = 0
        for q in queries:
            if q in results:
                total_results += results[q].result_count

        # SMB-adjusted thresholds (lowered from enterprise levels)
        if total_results >= 8:
            confidence[section] = 0.9
        elif total_results >= 4:
            confidence[section] = 0.7
        elif total_results >= 1:
            confidence[section] = 0.5
        else:
            confidence[section] = 0.3

    return confidence
```

### 4g. Update `build_research_output` initial query filter (line 305)

Change:
```python
if name in ["company_overview", "company_details", "recent_news"]
```
To:
```python
if name in ["company_presence", "social_reviews", "sales_channels",
            "company_overview", "company_details", "recent_news"]
```

Include both old and new names so info tier detection works with either cached or fresh results.

---

## Backward Compatibility

Existing cached research (in `output/*/research_cache.json`) uses old query names as keys. The plan handles this two ways:

1. **Result processor uses fallback lookups.** `results.get("company_presence") or results.get("company_overview")` ensures old keys still produce output.
2. **Orchestrator cache loading is query-name-agnostic.** It iterates `data["results"].items()` and stores by whatever name exists.

Old caches will produce the same output they do today (missing SMB-quality data, but no crashes). Re-running research with the new queries produces better output.

**Known existing caches:** `black-mountain-yarn-shop`, `burris-chalmers-communications`, `healing-roots-design`.

---

## What We Deliberately Skip

**No new Pydantic model fields.** The existing `CompanyProfile.recent_news`, `TechLandscape.company_tech_stack`, and `IndustryContext.challenges` fields carry the data. Gemini receives formatted text, not structured models — it doesn't care whether "Active on Instagram, Facebook" lives in a `social_media: List[str]` field or arrives as a snippet in the description.

**No new extraction helper methods.** The existing `_extract_first_paragraph`, `_extract_news`, `_extract_technologies`, `_extract_ai_initiatives`, `_extract_list_items` handle the same patterns. The one change (`_extract_technologies` keyword list) fixes the only extractor that would actively miss SMB data.

**No context_builder changes.** The existing formatters (`_format_company_profile`, `_format_industry_context`, `_format_tech_landscape`) already surface whatever the extractors find. Better queries → better raw data → better extraction through existing code → better formatted context → better Gemini output.

If testing reveals that specific structured fields (social media platforms, review ratings, sales channels) would materially improve synthesis quality, those are a small follow-up: add fields to models.py, add extraction helpers, add context_builder sections. But ship the query fix first and measure.

---

## Implementation Order

All 4 steps are tightly coupled (templates → selector → orchestrator → processor) and should be done in one commit.

1. `query_templates.py` — Replace templates and categories
2. `model_selector.py` — Update category mapping
3. `orchestrator.py` — Update phase queries and names
4. `result_processor.py` — Update query name references, keyword list, thresholds

---

## Verification

1. **Dry run**: `python -m strategy_factory.main run "Black Mountain Yarn Shop" --dry-run` — verify pipeline still loads without errors.

2. **Live run**: Test with a real Cohort 14 company:
   ```bash
   python -m strategy_factory.main run "Black Mountain Yarn Shop" --context "fiber arts, yarn shop, Black Mountain NC"
   ```
   Check `research_cache.json` for:
   - All 10 new query names present
   - `company_presence` returns Google listing, website info
   - `social_reviews` returns reviews, social media links
   - `sales_channels` returns any e-commerce/platform data
   - `industry_tools` returns actual tool names (QuickBooks, Shopify, etc.)
   - `industry_operations` returns workflow descriptions
   - `industry_ai_examples` returns real automation stories
   - Confidence scores are >= 0.5 for all sections

3. **Backward compat**: Load an old `research_cache.json` and verify the pipeline produces valid output without errors.

4. **Synthesis quality check**: After synthesis runs, verify that Gemini output references specific tools, workflows, and AI examples from the research — not generic filler.

---

## What This Enables

The synthesis prompts (Phase 2) say things like "You're probably using QuickBooks for invoicing" and "Your industry typically uses Shopify, Calendly, and Mailchimp." Those statements are only credible if the research phase actually found those tools. This change gives the synthesis prompts the raw material they need to make specific, believable recommendations.

Without this change, the synthesis prompts will still work — but they'll be doing pure inference with no research data to anchor on, which is exactly the "generic output" problem the prompt rewrite is designed to fix.
