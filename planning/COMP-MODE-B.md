# COMP-MODE-B: Add Sonar Chat Completions API for Comprehensive Mode

Handoff document for implementing a distinct comprehensive research path using the Perplexity Sonar Chat Completions API.

---

## Context

### The Bug

Quick and Comprehensive research modes produce identical Perplexity results because the Search API (`client.search.create()`) doesn't accept a model parameter. The entire `model_selector.py` (165 lines) picks models that never reach the API. `perplexity_client.py:search()` accepts a `model` parameter but never adds it to the API call params dict (lines 224-228). Model only affects cost estimation (wrong), stored metadata (fictional), and cache keys (cosmetic).

### The Fix

- **Quick mode**: Keep existing Search API flow unchanged
- **Comprehensive mode**: New path using Sonar Chat Completions API (`client.chat.completions.create()`), which DOES accept a model parameter (sonar-pro, sonar-deep-research)

### Design Decision: Hybrid Processing

For comprehensive mode results, we use a hybrid approach:
1. Extract basic company facts (name, website, industry, description) from Sonar synthesized answers — minimal extraction
2. Pass raw Sonar synthesized answers + citations to Gemini as "Deep Research Findings" context
3. Gemini gets both structured data and rich synthesized research, producing better deliverables

---

## SDK Details

### Package

- `perplexityai>=0.1.0` in `requirements.txt`
- Imported as `from perplexity import Perplexity`

### Search API (current, quick mode)

```python
client = Perplexity(api_key=key)
response = client.search.create(query="...", max_results=10, max_tokens_per_page=1024, ...)
# response.results → list of {title, url, snippet, date, last_updated}
# No model parameter. No usage data.
```

### Sonar Chat Completions API (new, comprehensive mode)

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "..."}],
    model="sonar-pro",  # or "sonar-deep-research"
    max_tokens=4096,
    temperature=0.2,
    search_recency_filter="month",
    search_domain_filter=[...],
)
# response.choices[0].message.content → synthesized answer text
# response.citations → list of URL strings
# response.search_results → list of {title, url, date, snippet}
# response.usage → {prompt_tokens, completion_tokens, total_tokens, cost.total_cost}
```

**Key difference**: Search API returns raw ranked snippets. Sonar API returns a synthesized answer with citations. Fundamentally different response shapes.

---

## Current Architecture

### Pipeline Flow

```
Research (Perplexity) → Result Processor → Synthesis (Gemini) → Generation (local)
```

### Key Files

| File | Lines | Role |
|------|-------|------|
| `strategy_factory/config.py` | — | PerplexityModel enum, PERPLEXITY_COSTS, ResearchMode enum |
| `strategy_factory/models.py` | 286 | QueryResult, SearchResult, ResearchOutput, CompanyProfile, IndustryContext, TechLandscape |
| `strategy_factory/research/perplexity_client.py` | 368 | PerplexityClient with search(), _estimate_cost(), cache, retry logic |
| `strategy_factory/research/model_selector.py` | 165 | Dead code — picks models that never reach API |
| `strategy_factory/research/orchestrator.py` | 371 | Runs 3 phases of queries, calls client.search(), builds ResearchOutput |
| `strategy_factory/research/query_templates.py` | 286 | 11 QueryTemplate instances across 3 categories |
| `strategy_factory/research/result_processor.py` | 613 | Extracts structured data from search snippets |
| `strategy_factory/synthesis/context_builder.py` | 323 | Formats research into Gemini prompts |
| `strategy_factory/synthesis/orchestrator.py` | — | Generates 7+1 deliverables via Gemini |
| `strategy_factory/synthesis/gemini_client.py` | ~187 | Gemini API wrapper with cost tracking |

### Model Selector (Currently Dead Code)

`model_selector.py` maps QueryCategory × ResearchMode → PerplexityModel:

```python
QueryCategory.COMPANY_DISCOVERY: QUICK → SONAR, COMPREHENSIVE → SONAR_PRO
QueryCategory.INDUSTRY:           QUICK → SONAR, COMPREHENSIVE → SONAR_PRO
QueryCategory.AI_OPPORTUNITY:     QUICK → SONAR, COMPREHENSIVE → SONAR_DEEP_RESEARCH
```

After this fix, these mappings become real for comprehensive mode.

### Query Templates

11 templates across 3 categories. ALL have `required_for_quick_mode=True` (no filtering between modes currently). Templates use search-style keyword queries like `"{company_name}" {industry} website services location`.

### Data Flow Through Orchestrator

`orchestrator.py:_execute_phase()` (lines 178-237):
1. Get templates for phase
2. Filter by mode (currently no filtering — all run in both modes)
3. For each template: render query → select model → `client.search()` → store result
4. After all phases: `result_processor.build_research_output()` creates `ResearchOutput`

`context_builder.py:build_full_prompt()` (lines 265-322):
1. Build context dict with formatted profile, industry, tech_landscape
2. Add TLDR knowledge, user context, dependencies
3. Append prompt template
4. Returns full prompt string for Gemini

### ResearchOutput Structure (models.py lines 155-174)

```python
class ResearchOutput(BaseModel):
    company_name: str
    research_timestamp: datetime
    research_mode: ResearchMode
    information_tier: CompanyInfoTier
    profile: CompanyProfile                    # description, products, headquarters, etc.
    industry: IndustryContext                  # primary_industry, market_size, trends, challenges
    competitors: List[CompetitorProfile]
    tech_landscape: TechLandscape              # tech_stack, ai_tools, adoption_rate
    regulatory: RegulatoryContext
    user_context: ValidatedUserContext
    raw_queries: List[QueryResult]
    total_cost: float
    confidence_scores: Dict[str, float]
```

---

## Implementation Steps

### Step 0: TRACK.md Cost Fixes (independent, apply first)

These 5 edits fix cost estimation for quick mode. See `TRACK.md` for exact code.

1. **`strategy_factory/synthesis/gemini_client.py`** (~lines 146-154) — Use `response.usage_metadata.prompt_token_count` and `candidates_token_count` for actual token counts. Fallback to `len(text)//4`.

2. **`strategy_factory/webapp.py`** (after ~line 2084) — Add synthesis cost tracking:
   ```python
   synthesis_cost = synthesis_orchestrator.get_cost_summary()["total_cost"]
   if synthesis_cost > 0:
       tracker.add_cost(synthesis_cost, "synthesis")
   ```

3. **`strategy_factory/config.py`** (after PERPLEXITY_COSTS dict) — Add single constant:
   ```python
   PERPLEXITY_QUERY_COST = 0.0045  # Search API, calibrated from actual billing (April 2026)
   ```
   Note: Single constant, NOT a per-model dict. All Search API queries cost the same regardless of model_selector output.

4. **`strategy_factory/research/perplexity_client.py`** (~lines 157-169) — Replace `_estimate_cost()`:
   ```python
   def _estimate_cost(self, model, query_text="", response_text=""):
       from ..config import PERPLEXITY_QUERY_COST
       return PERPLEXITY_QUERY_COST
   ```

5. **`strategy_factory/webapp.py`** (lines ~427, ~1572) + **`strategy_factory/server.py`** (~line 427) — Change `${total_cost:.4f}` to `${total_cost:.2f}`

### Step 1: New Data Models

**File: `strategy_factory/models.py`**

Add after `QueryResult` (after line 88):

```python
class SonarResult(BaseModel):
    """Result from a Sonar Chat Completions API call."""
    query: str
    model_used: str
    content: str
    citations: List[str] = Field(default_factory=list)
    search_results: List[SearchResult] = Field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    actual_cost: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None
```

Add to `ResearchOutput` (after line 173):

```python
research_findings: Optional[Dict[str, str]] = None  # category → synthesized answer (comprehensive only)
```

### Step 2: Comprehensive Query Templates

**File: `strategy_factory/research/query_templates.py`**

Add field to `QueryTemplate` dataclass (line 23):

```python
comprehensive_template: str = ""  # Natural language prompt for Sonar
```

Add `comprehensive_template=` to all 11 QueryTemplate instances:

```python
COMPANY_PRESENCE = QueryTemplate(
    name="company_presence",
    category=QueryCategory.COMPANY_DISCOVERY,
    template='"{company_name}" {context} website blog services...',
    comprehensive_template=(
        'Research the company "{company_name}" comprehensively. {context} '
        'Find their website, services/products, location, social media presence '
        '(LinkedIn, TikTok, YouTube, Instagram), Google Business listing, and any advertising. '
        'Provide a structured summary of their complete web presence.'
    ),
    ...
)

SOCIAL_REVIEWS = QueryTemplate(
    ...,
    comprehensive_template=(
        'Find and analyze all customer reviews and social media activity for "{company_name}". {context} '
        'Look on Yelp, Google Reviews, Facebook, Instagram, and any other platforms. '
        'Summarize: overall sentiment, common praise, common complaints, and reputation themes.'
    ),
)

SALES_CHANNELS = QueryTemplate(
    ...,
    comprehensive_template=(
        'Research how "{company_name}" sells their products or services. '
        'Look for e-commerce platforms (Shopify, Etsy, WooCommerce), physical retail, wholesale, '
        'or other sales channels in the {industry} industry. Summarize their multi-channel sales strategy.'
    ),
)

COMPETITOR_DISCOVERY = QueryTemplate(
    ...,
    comprehensive_template=(
        'Identify the main competitors and alternatives to "{company_name}" in the {industry} space. {context} '
        'For each competitor, note: name, what they offer, their market positioning, and how they compare. '
        'Focus on {current_year} information.'
    ),
)

INDUSTRY_OVERVIEW = QueryTemplate(
    ...,
    comprehensive_template=(
        'Provide a comprehensive analysis of the {industry} industry as of {current_year}. '
        'Include: market size, growth rate, key segments, major players, and outlook. '
        'Focus on information relevant to small and medium businesses.'
    ),
)

INDUSTRY_CHALLENGES = QueryTemplate(
    ...,
    comprehensive_template=(
        'What are the top challenges facing small businesses in the {industry} industry as of {current_year}? {context} '
        'Focus on operational challenges, customer acquisition, staffing, technology adoption, and regulatory burden. '
        'Prioritize issues affecting businesses under $5M revenue.'
    ),
)

INDUSTRY_TOOLS = QueryTemplate(
    ...,
    comprehensive_template=(
        'What software, tools, and apps are most commonly used by small businesses in the {industry} industry '
        'as of {current_year}? Categorize by function: accounting, marketing, operations, customer management, '
        'scheduling, e-commerce. Include product names and approximate pricing.'
    ),
)

INDUSTRY_OPERATIONS = QueryTemplate(
    ...,
    comprehensive_template=(
        'Describe the typical daily operations and workflows of a small business in the {industry} industry. '
        'Include: customer interaction patterns, common workflows, marketing channels, '
        'inventory/supply chain patterns, and time-intensive tasks.'
    ),
)

INDUSTRY_AI_EXAMPLES = QueryTemplate(
    ...,
    comprehensive_template=(
        'Find real, concrete examples of AI automation being used by small businesses in the {industry} industry '
        'as of {current_year}. {context} Include: specific case studies, tools being used, results achieved '
        '(time saved, revenue gained), and lessons learned. Focus on implementations, not theory.'
    ),
)

INDUSTRY_AI_TOOLS = QueryTemplate(
    ...,
    comprehensive_template=(
        'What are the best AI tools currently recommended for small businesses in the {industry} industry? '
        'Include tools for: content creation, customer service, scheduling, marketing, operations, '
        'and any industry-specific AI applications. Note pricing and ease of use.'
    ),
)

INDUSTRY_AI_TRENDS = QueryTemplate(
    ...,
    comprehensive_template=(
        'Analyze current AI adoption trends among small business owners in the {industry} industry '
        'as of {current_month_year}. {context} Include: adoption rates, most popular applications, '
        'barriers to adoption, and emerging opportunities. Focus on practical, affordable solutions.'
    ),
)
```

Add method to `QueryTemplates` class (after `render_query()`):

```python
def render_comprehensive_query(self, template, company_name, industry="", context="", **extra_vars):
    """Render a comprehensive query template for Sonar."""
    if not template.comprehensive_template:
        return self.render_query(template, company_name, industry, context, **extra_vars)
    variables = {"company_name": company_name, "industry": industry, "context": context, **extra_vars}
    return self.temporal.inject(template.comprehensive_template, **variables)
```

### Step 3: New `sonar_query()` Method

**File: `strategy_factory/research/perplexity_client.py`**

Add import at top: `from ..models import SearchResult, QueryResult, SonarResult`

Add `sonar_query()` method to `PerplexityClient` (after `search()` method ends ~line 259):

```python
def sonar_query(
    self,
    query: str,
    model: PerplexityModel = PerplexityModel.SONAR_PRO,
    system_prompt: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.2,
    search_recency_filter: Optional[str] = None,
    search_domain_filter: Optional[List[str]] = None,
    cache_ttl_hours: int = 48,
) -> SonarResult:
    """Query the Sonar Chat Completions API with model selection."""
    # 1. Cache key
    cache_key = hashlib.md5(
        json.dumps({"query": query, "model": model.value, "type": "sonar"}).encode()
    ).hexdigest()

    if self.enable_cache:
        cached = self._get_cached(cache_key)
        if cached and isinstance(cached, SonarResult):
            return cached

    # 2. Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": query})

    # 3. Build params
    params = {
        "messages": messages,
        "model": model.value,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if search_recency_filter:
        params["search_recency_filter"] = search_recency_filter
    if search_domain_filter:
        params["search_domain_filter"] = search_domain_filter

    # 4. Execute with retry
    response = self._execute_sonar_with_retry(params)

    if response is None:
        return SonarResult(
            query=query, model_used=model.value, content="",
            error="All retries failed", timestamp=datetime.now(),
        )

    # 5. Parse response
    try:
        content = ""
        citations = []
        search_results = []
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        actual_cost = 0.0

        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content or ""

        if hasattr(response, 'citations') and response.citations:
            citations = response.citations

        if hasattr(response, 'search_results') and response.search_results:
            search_results = [
                SearchResult(
                    title=sr.title if hasattr(sr, 'title') else "",
                    url=sr.url if hasattr(sr, 'url') else "",
                    snippet=sr.snippet if hasattr(sr, 'snippet') else "",
                    date=str(sr.date) if hasattr(sr, 'date') and sr.date else None,
                )
                for sr in response.search_results
            ]

        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
            completion_tokens = getattr(usage, 'completion_tokens', 0) or 0
            total_tokens = getattr(usage, 'total_tokens', 0) or 0
            # Try to get actual cost from API
            cost_obj = getattr(usage, 'cost', None)
            if cost_obj:
                actual_cost = getattr(cost_obj, 'total_cost', 0.0) or 0.0

        # Fallback cost estimation if API doesn't provide it
        if actual_cost == 0.0:
            input_cost, output_cost = PERPLEXITY_COSTS.get(model, (0.001, 0.001))
            actual_cost = (prompt_tokens / 1000 * input_cost) + (completion_tokens / 1000 * output_cost)

        # Update tracking
        self.total_cost += actual_cost
        self.query_count += 1

        result = SonarResult(
            query=query, model_used=model.value, content=content,
            citations=citations, search_results=search_results,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            total_tokens=total_tokens, actual_cost=actual_cost,
            timestamp=datetime.now(),
        )

        # Cache
        if self.enable_cache:
            self._cache_result(cache_key, result, cache_ttl_hours)

        return result

    except Exception as e:
        return SonarResult(
            query=query, model_used=model.value, content="",
            error=f"Response parsing error: {e}", timestamp=datetime.now(),
        )
```

Add `_execute_sonar_with_retry()` helper (mirrors existing `_execute_with_retry()`):

```python
def _execute_sonar_with_retry(self, params: Dict[str, Any]):
    """Execute Sonar API call with retry logic."""
    max_retries = RETRY_CONFIG["max_retries"]
    delay = RETRY_CONFIG["initial_delay"]
    max_delay = RETRY_CONFIG["max_delay"]
    multiplier = RETRY_CONFIG["backoff_multiplier"]

    for attempt in range(max_retries + 1):
        try:
            self._rate_limit()
            response = self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            if attempt == max_retries:
                return None
            time.sleep(delay)
            delay = min(delay * multiplier, max_delay)
```

### Step 4: Hybrid Result Processing

**File: `strategy_factory/research/result_processor.py`**

Add new method:

```python
def extract_from_sonar_results(
    self,
    company_name: str,
    sonar_results: Dict[str, "SonarResult"],
    mode: ResearchMode,
    user_context: str = "",
) -> ResearchOutput:
    """
    Build ResearchOutput from Sonar Chat Completions results.

    Hybrid approach: extract basic structured data from synthesized
    answers, and package raw findings for Gemini context.
    """
    # 1. Build research_findings: category → formatted answer + citations
    research_findings = {}
    category_labels = {
        "company_presence": "company_discovery",
        "social_reviews": "company_discovery",
        "sales_channels": "company_discovery",
        "competitor_discovery": "company_discovery",
        "industry_overview": "industry_analysis",
        "industry_challenges": "industry_analysis",
        "industry_tools": "industry_analysis",
        "industry_operations": "industry_analysis",
        "industry_ai_examples": "ai_opportunity",
        "industry_ai_tools": "ai_opportunity",
        "industry_ai_trends": "ai_opportunity",
    }

    for query_name, result in sonar_results.items():
        if result.error:
            continue
        category = category_labels.get(query_name, query_name)
        if category not in research_findings:
            research_findings[category] = ""

        # Append this query's findings to the category
        entry = f"### {query_name.replace('_', ' ').title()}\n{result.content}\n"
        if result.citations:
            entry += "\nSources:\n" + "\n".join(f"- {c}" for c in result.citations[:10]) + "\n"
        research_findings[category] += entry + "\n"

    # 2. Extract basic company facts from company_discovery answers
    company_text = research_findings.get("company_discovery", "")
    profile = self._extract_basic_profile(company_text, company_name)

    # 3. Extract basic industry facts
    industry_text = research_findings.get("industry_analysis", "")
    industry = self._extract_basic_industry(industry_text)

    # 4. Extract basic tech/AI facts
    ai_text = research_findings.get("ai_opportunity", "")
    tech = self._extract_basic_tech(ai_text)

    # 5. Build raw_queries from Sonar results (for backward compat)
    raw_queries = [
        QueryResult(
            query=r.query,
            model_used=r.model_used,
            results=r.search_results,
            result_count=len(r.search_results),
            timestamp=r.timestamp,
            cost_estimate=r.actual_cost,
        )
        for r in sonar_results.values()
    ]

    return ResearchOutput(
        company_name=company_name,
        research_timestamp=datetime.now(),
        research_mode=mode,
        profile=profile,
        industry=industry,
        tech_landscape=tech,
        raw_queries=raw_queries,
        research_findings=research_findings,
        total_cost=sum(r.actual_cost for r in sonar_results.values()),
        confidence_scores={"sonar_mode": True},
    )
```

Add helper extraction methods (lightweight — not full result_processor parsing):

```python
def _extract_basic_profile(self, text: str, company_name: str) -> CompanyProfile:
    """Extract basic company facts from synthesized text."""
    profile = CompanyProfile(description=text[:500] if text else "")
    # Simple extraction — look for common patterns
    # Website: look for URLs
    # Industry: look for "industry" mentions
    # This is intentionally lightweight — the raw findings carry the real detail
    return profile

def _extract_basic_industry(self, text: str) -> IndustryContext:
    """Extract basic industry facts from synthesized text."""
    return IndustryContext()  # Populated minimally; research_findings carries the detail

def _extract_basic_tech(self, text: str) -> TechLandscape:
    """Extract basic tech facts from synthesized text."""
    return TechLandscape()  # Populated minimally; research_findings carries the detail
```

Modify `build_research_output()` to accept `sonar_results`:

```python
def build_research_output(self, company_name, mode, results, user_context="", sonar_results=None):
    if sonar_results and mode == ResearchMode.COMPREHENSIVE:
        return self.extract_from_sonar_results(company_name, sonar_results, mode, user_context)
    # ... existing code unchanged ...
```

### Step 5: Context Builder Extension

**File: `strategy_factory/synthesis/context_builder.py`**

Add method:

```python
def _format_research_findings(self, research: ResearchOutput) -> str:
    """Format comprehensive research findings for prompt."""
    if not research.research_findings:
        return ""

    sections = ["## Deep Research Findings\n"]
    sections.append(
        "The following are synthesized research findings from AI-powered "
        "deep research. Use these as authoritative context alongside the "
        "structured data above.\n"
    )

    category_labels = {
        "company_discovery": "Company Discovery Research",
        "industry_analysis": "Industry Analysis Research",
        "ai_opportunity": "AI Opportunity Research",
    }

    for category, content in research.research_findings.items():
        label = category_labels.get(category, category.replace("_", " ").title())
        sections.append(f"### {label}\n{content}")

    return "\n\n---\n\n".join(sections)
```

Modify `build_full_prompt()` (after line ~293, before TLDR knowledge section):

```python
# After tech_landscape section:
if research.research_findings:
    prompt_parts.append(f"\n{self._format_research_findings(research)}")
```

Modify `build_context()` — add `"research_findings"` to context dict:

```python
"research_findings": research.research_findings or {},
```

### Step 6: Orchestrator Mode Branching

**File: `strategy_factory/research/orchestrator.py`**

Add import: `from ..models import SonarResult`

Add instance variable in `__init__()`: `self.sonar_results: Dict[str, SonarResult] = {}`

Modify `_execute_phase()` (replace lines ~224-233):

```python
if self.mode == ResearchMode.QUICK:
    # Existing Search API path (unchanged)
    result = self.client.search(
        query=query,
        max_results=10,
        search_recency_filter=template.recency_filter,
        model=selection.model,
    )
    self.results[query_name] = result
else:
    # New Sonar Chat Completions path
    sonar_prompt = self.templates.render_comprehensive_query(
        template,
        company_name=company_name,
        industry=industry,
        context=context,
    )
    sonar_result = self.client.sonar_query(
        query=sonar_prompt,
        model=selection.model,
        search_recency_filter=template.recency_filter,
    )
    self.sonar_results[query_name] = sonar_result
```

Modify `research()` method (~line 135-140) — pass sonar_results to processor:

```python
output = self.result_processor.build_research_output(
    company_name=company_name,
    mode=self.mode,
    results=self.results,
    user_context=context,
    sonar_results=self.sonar_results if self.mode == ResearchMode.COMPREHENSIVE else None,
)
```

Update `save_research_cache()` and `load_research_cache()` to serialize/deserialize `sonar_results` alongside `results`.

---

## Files Modified Summary

| File | Step | Change |
|------|------|--------|
| `strategy_factory/synthesis/gemini_client.py` | 0 | Use `response.usage_metadata` for actual tokens |
| `strategy_factory/webapp.py` | 0 | Track synthesis costs, fix decimal display |
| `strategy_factory/server.py` | 0 | Fix decimal display |
| `strategy_factory/config.py` | 0 | Add `PERPLEXITY_QUERY_COST = 0.0045` |
| `strategy_factory/research/perplexity_client.py` | 0+3 | Fix `_estimate_cost()`, add `sonar_query()`, `_execute_sonar_with_retry()` |
| `strategy_factory/models.py` | 1 | Add `SonarResult`, add `research_findings` to `ResearchOutput` |
| `strategy_factory/research/query_templates.py` | 2 | Add `comprehensive_template` field + 11 NL prompts + `render_comprehensive_query()` |
| `strategy_factory/research/result_processor.py` | 4 | Add `extract_from_sonar_results()` + helpers, modify `build_research_output()` |
| `strategy_factory/synthesis/context_builder.py` | 5 | Add `_format_research_findings()`, extend `build_full_prompt()` |
| `strategy_factory/research/orchestrator.py` | 6 | Mode branching in `_execute_phase()`, pass `sonar_results` |

---

## Implementation Order

Steps 0-5 are backward-compatible (no existing behavior changes). Step 6 activates everything.

1. Step 0: TRACK.md cost fixes
2. Step 1: New models
3. Step 2: Comprehensive templates
4. Step 3: `sonar_query()` method
5. Step 4: Hybrid result processing
6. Step 5: Context builder extension
7. Step 6: Orchestrator branching (activation point)

---

## Verification

1. **Quick mode regression**: `python -m strategy_factory.main run "Test Co" --mode quick` — must behave identically to current
2. **Comprehensive mode**: `python -m strategy_factory.main run "Test Co" --mode comprehensive` — Sonar API called with correct models
3. **Cost accuracy**: Quick mode ~$0.05 (11 × $0.0045). Comprehensive uses actual Sonar API costs.
4. **Research findings**: `output/*/research_cache.json` should contain `sonar_results` section for comprehensive mode, `None` for quick
5. **Deliverable quality**: Comprehensive deliverables should show richer, more specific content than quick mode

---

## Potential Issues

1. **Sonar API latency**: sonar-deep-research can take 30-90 seconds per query. With 11 queries, comprehensive mode could take 5-15 minutes. Webapp SSE progress handles this but timeout values may need adjustment.
2. **Response parsing**: The SDK response shape for `chat.completions.create()` should be verified with a live test call before building production code. Use `hasattr()` checks generously (as shown in Step 3).
3. **Rate limits**: Sonar API may have different rate limits than Search API. Current 1-second interval may need to increase to 2-3 seconds for comprehensive mode.
4. **Prompt size**: 11 synthesized answers in research_findings could be 20K-40K tokens. Gemini 2.5 Flash has 1M context window, so this is fine.
5. **Fallback**: If sonar-deep-research fails, retry with sonar-pro. Model selector's `fallback_model` field can be used here.
