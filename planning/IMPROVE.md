# IMPROVE: Improve Research Queries

## Why This Change

Research queries for social media and reviews ask "does this exist?" not "what does it say?" Example: the `social_reviews` query sends `"{company_name}" reviews Yelp Google Facebook Instagram customers {context}` — this returns snippets about review existence, not review content. No dedicated blog query exists. Gemini then produces generic content creation recommendations because it has thin input to work with.

**Solution:** Improve 2 existing queries, add 2 new queries, wire up `location` for disambiguation, and format the raw results directly for Gemini in the context builder.

**Design principle:** Do in Python only what Python is reliably good at (regex for star ratings, string matching for platform names). Leave language understanding to the language model. No new models, no extraction layer — just better queries and direct formatting of raw results.

---

## Architecture (Current Pipeline, Unchanged)

```
Perplexity Search API → result_processor.py → ResearchOutput model
    → context_builder.py → Gemini API → 8 deliverables
```

The pipeline structure stays exactly the same. No new dependencies, no new APIs, no scrapers.

---

## Step 1 — Update `strategy_factory/research/query_templates.py`

**Improve `SOCIAL_REVIEWS` template** — keep platform names for disambiguation, add content terms for richer results:

Current:
```python
template='"{company_name}" reviews Yelp Google Facebook Instagram customers {context}',
```

New:
```python
template='"{company_name}" {location} customer reviews ratings feedback complaints praise themes Google Yelp Facebook {context}',
```

Key changes:
- Added content-oriented terms: `feedback`, `complaints`, `praise`, `themes` — steers Perplexity toward what reviews say, not just that they exist
- Kept platform names: `Google`, `Yelp`, `Facebook` — provides disambiguation so "Summit Plumbing" doesn't pull in "Summit Dental" reviews
- Added `{location}` — disambiguates companies with common names by city/state
- Removed `Instagram` — Instagram rarely hosts text reviews for SMBs; it's visual content

**Improve `COMPANY_PRESENCE` template** — add location, better social media detail:

Current:
```python
template='"{company_name}" {context} website blog services location Google business listing LinkedIn TikTok YouTube social media activity advertising {industry}',
```

New:
```python
template='"{company_name}" {location} services Google business profile LinkedIn Facebook Instagram TikTok YouTube social media posting frequency engagement advertising {industry} {context}',
```

Key changes:
- Added `{location}` for disambiguation
- Added "posting frequency" and "engagement" — shifts from "does this exist?" to "how active is it?"
- Changed "listing" to "profile" — modern terminology
- Added "Facebook" and "Instagram" explicitly — most common SMB platforms
- Removed "blog" and "website" — blog coverage handled by new dedicated query

**Add `GOOGLE_REVIEWS` template** (new — insert after `SOCIAL_REVIEWS`):

```python
GOOGLE_REVIEWS = QueryTemplate(
    name="google_reviews",
    category=QueryCategory.COMPANY_DISCOVERY,
    template='"{company_name}" {location} Google reviews "Google Business" rating stars customer feedback experience {context}',
    recency_filter="year",
    priority=2,
    description="Find Google Business review details including ratings, themes, and customer sentiment",
)
```

Dedicated query for Google Business reviews — the dominant review platform for local SMBs. The quoted `"Google Business"` forces Perplexity to prioritize Google-specific results. `{location}` disambiguates.

**Add `BLOG_CONTENT` template** (new — insert after `SALES_CHANNELS`):

```python
BLOG_CONTENT = QueryTemplate(
    name="blog_content",
    category=QueryCategory.COMPANY_DISCOVERY,
    template='"{company_name}" {location} blog articles posts newsletter content topics expertise {industry} {context}',
    recency_filter="year",
    priority=3,
    description="Find blog posts, articles, and content themes published by the company",
)
```

Fills a genuine gap — no current query covers content marketing. For most SMBs this returns nothing, which is itself useful data (signals a content gap that AI tools can fill).

**Add both to `ALL_TEMPLATES` dict:**

```python
ALL_TEMPLATES: Dict[str, QueryTemplate] = {
    "company_presence": COMPANY_PRESENCE,
    "social_reviews": SOCIAL_REVIEWS,
    "google_reviews": GOOGLE_REVIEWS,        # NEW
    "sales_channels": SALES_CHANNELS,
    "blog_content": BLOG_CONTENT,            # NEW
    "competitor_discovery": COMPETITOR_DISCOVERY,
    # ... rest unchanged ...
}
```

## Step 2 — Update `strategy_factory/research/orchestrator.py`

**Add `location` threading** — pass location from CompanyInput through to query rendering.

In `_execute_phase()`, add `location` parameter and pass it via `**extra_vars` (which `render_query` already accepts):

```python
def _execute_phase(
    self,
    phase: str,
    company_name: str,
    industry: str,
    context: str = "",
    location: str = "",  # ADD
) -> None:
    self.current_phase = phase
    queries = self.PHASE_QUERIES.get(phase, [])

    for i, query_name in enumerate(queries):
        template = self.templates.get_template(query_name)
        if not template:
            continue

        query = self.templates.render_query(
            template,
            company_name=company_name,
            industry=industry,
            context=context,
            location=location,  # ADD — uses existing **extra_vars
        )
        # ... rest unchanged ...
```

In `research()`, extract location and pass it to all three phase calls:

```python
location = company_input.location or ""  # ADD

self._execute_phase("company_discovery", company_name, industry, context, location)
# ... tier detection unchanged ...
self._execute_phase("industry_analysis", company_name, industry, context, location)
self._execute_phase("ai_opportunity", company_name, industry, context, location)
```

**Add new queries to `PHASE_QUERIES["company_discovery"]`:**

```python
PHASE_QUERIES = {
    "company_discovery": [
        "company_presence",
        "social_reviews",
        "google_reviews",      # NEW
        "sales_channels",
        "blog_content",        # NEW
        "competitor_discovery",
    ],
    # ... rest unchanged ...
}
```

This brings total queries from 11 to 13 (~18% increase in API cost, roughly $0.01-0.02 more per run).

## Step 3 — Update `strategy_factory/models.py`

Change `raw_queries` from a list to a dict so query results are accessible by name downstream:

Current:
```python
raw_queries: List[QueryResult] = Field(default_factory=list)
```

New:
```python
raw_queries: Dict[str, QueryResult] = Field(default_factory=dict)
```

This is the only model change. No new models.

## Step 4 — Update `strategy_factory/research/result_processor.py`

**One-line change** in `build_research_output()` — pass the dict directly instead of converting to list:

Current (line 330):
```python
raw_queries=list(results.values()),
```

New:
```python
raw_queries=results,
```

**Update `_calculate_confidence()`** to include new query names:

```python
sections = {
    "profile": ["company_presence", "social_reviews", "google_reviews"],
    "digital_presence": ["social_reviews", "google_reviews", "blog_content"],
    "industry": ["industry_overview", "industry_challenges", "industry_tools"],
    "technology": ["industry_ai_examples", "industry_ai_tools"],
}
```

No new extraction methods. No `DigitalPresence` model. The raw `QueryResult` objects already contain everything Gemini needs.

## Step 5 — Update `strategy_factory/synthesis/context_builder.py`

**Add `_format_digital_presence()` method** that reads directly from raw query results:

```python
import re

def _format_digital_presence(self, research: ResearchOutput) -> str:
    """Format digital presence data from raw query results for prompt."""
    sections = []
    raw = research.raw_queries

    # Google review rating (simple regex — the one thing worth extracting)
    google = raw.get("google_reviews")
    if google and google.results:
        rating_pattern = r'(\d+\.?\d*)\s*(?:stars?|/5|out of 5|-star)'
        for r in google.results:
            match = re.search(rating_pattern, r.snippet.lower())
            if match:
                sections.append(f"## Customer Reviews\nGoogle rating: {match.group(1)}/5")
                break

    # Raw review snippets — let Gemini interpret sentiment/themes
    review_snippets = []
    for key in ("social_reviews", "google_reviews"):
        qr = raw.get(key)
        if qr:
            for r in qr.results:
                text = r.snippet.strip()
                if len(text) > 20:
                    review_snippets.append(text[:300])
    if review_snippets:
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for s in review_snippets:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        formatted = "\n".join(f"- {s}" for s in unique[:8])
        sections.append(f"### What Customers Say\n{formatted}")

    # Social platforms (string matching — Python is good at this)
    company = raw.get("company_presence")
    if company and company.results:
        platform_map = {
            "facebook": "Facebook", "instagram": "Instagram",
            "tiktok": "TikTok", "youtube": "YouTube",
            "linkedin": "LinkedIn", "twitter": "Twitter/X",
            "x.com": "Twitter/X", "pinterest": "Pinterest",
            "nextdoor": "Nextdoor",
        }
        text = " ".join(r.snippet.lower() + " " + r.url.lower() for r in company.results)
        platforms = []
        for keyword, name in platform_map.items():
            if keyword in text and name not in platforms:
                platforms.append(name)
        if platforms:
            sections.append(f"## Social Media\nPlatforms: {', '.join(platforms)}")

        # Activity snippet
        activity_keywords = ["posts", "followers", "engagement", "active", "updates"]
        for r in company.results:
            for sentence in r.snippet.split("."):
                if any(kw in sentence.lower() for kw in activity_keywords):
                    sections.append(f"**Activity:** {sentence.strip()[:300]}")
                    break
            else:
                continue
            break

    # Blog presence
    blog = raw.get("blog_content")
    if blog and blog.results:
        topics = [r.title[:150] for r in blog.results[:5] if r.title and len(r.title) > 10]
        if topics:
            formatted = "\n".join(f"- {t}" for t in topics)
            sections.append(f"## Blog & Content\n{formatted}")
    else:
        sections.append("## Blog & Content\nNo significant blog or content marketing presence found.")

    return "\n\n".join(sections) if sections else ""
```

**Wire into `build_context()`** — add to the context dict:

```python
"digital_presence": self._format_digital_presence(research),
```

**Wire into `build_full_prompt()`** — insert between company profile and industry context:

```python
prompt_parts = [
    context["temporal_prompt"],
    f"\n# Company: {context['company_name']}",
    f"\n{context['company_profile']}",
    f"\n{context['digital_presence']}",  # ADD
    f"\n{context['industry_context']}",
    f"\n{context['tech_landscape']}",
]
```

## Step 6 — Update `strategy_factory/synthesis/prompts/pain_points.py`

The existing Content Creation Gap section (line 69-77) already has instructions to reference review data and digital presence. Strengthen the blog gap instruction:

In the Content Creation Gap section, after the existing line about `social_reviews` query, add:

```
If the research context includes a "Blog & Content" section that says "No significant blog or content marketing presence found", flag this explicitly as a gap that AI content tools can fill quickly — blog posts, email newsletters, and social content can be bootstrapped with AI in hours, not weeks.
```

This is a one-line prompt addition, not a structural change.

---

## Files Modified

| File | Change | Lines touched |
|------|--------|---------------|
| `strategy_factory/research/query_templates.py` | Improve 2 templates, add 2 new templates, update `ALL_TEMPLATES` | ~20 |
| `strategy_factory/research/orchestrator.py` | Thread `location` through, add 2 queries to `PHASE_QUERIES` | ~10 |
| `strategy_factory/models.py` | Change `raw_queries` type from `List` to `Dict` | 1 |
| `strategy_factory/research/result_processor.py` | Pass dict directly, update confidence sections | ~5 |
| `strategy_factory/synthesis/context_builder.py` | Add `_format_digital_presence()`, wire into context and prompt | ~50 |
| `strategy_factory/synthesis/prompts/pain_points.py` | One-line blog gap instruction | 2 |

Total: ~88 lines changed across 6 files. No new files. No new models. No new dependencies.

---

## What Gemini Gets (Example)

Before this change, Gemini receives:
```
## Company Overview
Smith Brothers Plumbing is a family-owned plumbing company...

## Industry: Plumbing
**Market Size:** $130 billion...
```

After this change, Gemini receives:
```
## Company Overview
Smith Brothers Plumbing is a family-owned plumbing company...

## Customer Reviews
Google rating: 4.2/5

### What Customers Say
- "Great communication and showed up on time. Fair pricing for the work done."
- "Called three times over two days before anyone got back to me. Disappointing."
- "Fixed our water heater in under an hour. Highly recommend for emergency calls."
- "They charged $150 just to come look at the problem. Seemed steep for a 15-minute visit."
- "Been using them for years. Always reliable and honest about what actually needs fixing."

## Social Media
Platforms: Facebook, Google Business
**Activity:** Facebook page updated monthly, primarily sharing seasonal plumbing tips

## Blog & Content
No significant blog or content marketing presence found.

## Industry: Plumbing
**Market Size:** $130 billion...
```

Gemini now has concrete customer feedback to work with. It can identify that responsiveness and pricing transparency are pain points, that emergency service is a strength, and that there's no content marketing — all without Python trying to pre-digest this data.

---

## Verification

1. **Full pipeline test:** Run for a real company and check:
   - `research_cache.json` contains `google_reviews` and `blog_content` query results
   - `research_cache.json` shows improved query text for `social_reviews` and `company_presence`
   - Queries include location when `company_input.location` is set
   - Generated `02_daily_pain_points.md` references specific customer feedback when review data is available
   - Generated deliverables mention content gaps when no blog results are found

---

## Potential Issues

- **Perplexity `site:` operator:** The queries deliberately avoid `site:` syntax because Perplexity's Search API may not support it reliably. The quoted `"Google Business"` phrase in the google_reviews template partially compensates by signaling intent to Perplexity.
- **Thin data for very small SMBs:** Many SMBs have no blog and limited reviews. The formatting method handles this gracefully — empty queries produce no section (or "No significant blog presence found" for blogs). Thin results are themselves useful data.
- **Location not always available:** `company_input.location` is optional and not currently collected by the webapp form. When empty, `{location}` renders as an empty string — harmless but provides no disambiguation. Location info from `{context}` partially compensates. Adding a location field to the webapp form is a separate, trivial enhancement.
- **Cost increase:** 13 queries instead of 11 (~18% more). At Sonar pricing this is roughly $0.01-0.02 more per company — negligible.
- **Cached research compatibility:** Old `research_cache.json` files won't have `google_reviews` or `blog_content` entries. The `raw_queries` dict defaults to empty, and `_format_digital_presence()` uses `.get()` on every key — missing queries produce no output, no crash. However, the `raw_queries` type change from `List` to `Dict` means old cache files with a list value will fail deserialization. Users should delete old cache and re-run research after upgrading.
- **`raw_queries` type change:** Any code that iterates `raw_queries` as a list (e.g. `for qr in research.raw_queries`) will break. Grep for `raw_queries` usage outside of `models.py` and `result_processor.py` before implementing. If other consumers exist, keep the list field and add a parallel `raw_queries_by_name: Dict[str, QueryResult]` field instead.
