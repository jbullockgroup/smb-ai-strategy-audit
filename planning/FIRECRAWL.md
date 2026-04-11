# FIRECRAWL.md — Firecrawl Infrastructure Plan

**Purpose**: Self-contained handoff document. Creates the Firecrawl integration infrastructure: new files, data models, dependency, and optional API key wiring.

## Execution Order: Step 3 of 5

| Step | Plan | What it does |
|------|------|-------------|
| 1 | TLDR-FIX | Fix knowledge_loader.py (standalone) |
| 2 | PROMPTS-AGAIN | Restructure all 7 prompt formats |
| **3** | **FIRECRAWL (this plan)** | **Add Firecrawl infrastructure (new files, models, deps)** |
| 4 | RESEARCH-ENHANCEMENTS | Pipeline wiring + prompt content additions |
| 5 | EXEC-SUM | Add 8th deliverable |

**Prerequisites**: None for this plan specifically. Steps 1-2 can run before or after, but step 4 (RESEARCH-ENHANCEMENTS) must run after this plan because it wires these new files into the pipeline.

**Scope**: This plan ONLY creates infrastructure. It does NOT touch the pipeline orchestrator, context builder, result processor, or any prompt files. Those integrations are in RESEARCH-ENHANCEMENTS.

---

## File Change Summary

| File | Change |
|------|--------|
| `strategy_factory/models.py` | Add `SocialMediaPresence`, `BlogPresence`, `DigitalPresence` models; add field to `ResearchOutput` |
| `strategy_factory/research/firecrawl_client.py` | **NEW** — Firecrawl SDK wrapper |
| `strategy_factory/research/digital_presence_scanner.py` | **NEW** — Digital presence scanning logic |
| `strategy_factory/research/__init__.py` | Export `DigitalPresenceScanner` |
| `requirements.txt` | Add `firecrawl-py>=2.0.0` |
| `.env.example` | Add `FIRECRAWL_API_KEY` |
| `strategy_factory/main.py` | Optional key check + dry-run output |

---

## Part 1: New Data Models

### File: `strategy_factory/models.py`

**Add 3 new model classes** (insert after `ValidatedUserContext`, before `ResearchOutput`, ~line 154):

```python
class SocialMediaPresence(BaseModel):
    """Social media platform presence and activity."""
    platform: str                          # facebook, instagram, linkedin, twitter, youtube, tiktok
    url: Optional[str] = None
    found: bool = False
    follower_count: Optional[str] = None  # "1,200" if visible
    last_post_date: Optional[str] = None   # "2025-06-15" or "8 months ago"
    posting_frequency: Optional[str] = None # "2-3 posts/week", "inactive"
    activity_level: Optional[str] = None   # active, occasional, inactive


class BlogPresence(BaseModel):
    """Blog/content publishing analysis."""
    found: bool = False
    url: Optional[str] = None
    total_posts: Optional[int] = None
    last_post_date: Optional[str] = None
    posting_frequency: Optional[str] = None # "Monthly", "Irregular", "Inactive for 11 months"
    recent_titles: List[str] = Field(default_factory=list)
    activity_level: Optional[str] = None   # active, occasional, inactive


class DigitalPresence(BaseModel):
    """Complete digital presence scan results."""
    website_url: Optional[str] = None
    website_scraped: bool = False
    blog: BlogPresence = Field(default_factory=BlogPresence)
    social_media: List[SocialMediaPresence] = Field(default_factory=list)
    content_activity_summary: str = ""      # "Low — blog inactive for 11 months, minimal social posting"
    scan_timestamp: Optional[datetime] = None
    scan_cost_pages: int = 0               # Number of Firecrawl pages used
```

**Add field to `ResearchOutput`** (after `competitors` field, ~line 165):

```python
    digital_presence: Optional[DigitalPresence] = None
```

Note: RESEARCH-ENHANCEMENTS will also add fields to `ResearchOutput` after `competitors`. Both are `Optional` with `None` defaults — order doesn't matter as long as both are present.

---

## Part 2: Firecrawl Client

### New file: `strategy_factory/research/firecrawl_client.py`

```python
"""
Firecrawl API client for digital presence scanning.

Wraps the firecrawl-py SDK with error handling and credit tracking.
Optional dependency — pipeline works without it.
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class FirecrawlClient:
    """
    Thin wrapper around the Firecrawl Python SDK.

    Tracks page credits used per session for cost awareness.
    All methods return None/empty on failure — never raises.
    """

    def __init__(self, api_key: str):
        try:
            from firecrawl import Firecrawl
            self.client = Firecrawl(api_key=api_key)
            self.pages_used = 0
            self.available = True
        except ImportError:
            logger.warning("firecrawl-py not installed. Run: pip install firecrawl-py")
            self.client = None
            self.available = False
        except Exception as e:
            logger.warning(f"Firecrawl init failed: {e}")
            self.client = None
            self.available = False

    def find_website(self, company_name: str, industry: str = "") -> Optional[str]:
        """
        Search for company website URL.
        Uses 1 page credit.
        Returns URL string or None.
        """
        if not self.available:
            return None

        try:
            query = f"{company_name} official website"
            if industry:
                query += f" {industry}"
            results = self.client.search(query=query, limit=3)
            self.pages_used += 1

            if not results or not results.get("data"):
                return None

            for result in results["data"][:3]:
                url = result.get("url", "")
                # Prefer the most official-looking URL
                if url and not any(skip in url.lower() for skip in ["facebook.com", "yelp.com", "linkedin.com", "twitter.com", "instagram.com", "yellowpages", "angi.com", "bbb.org"]):
                    return url

            # Fallback to first result if all are social
            if results["data"]:
                return results["data"][0].get("url")

        except Exception as e:
            logger.warning(f"Firecrawl search failed for {company_name}: {e}")

        return None

    def map_site(self, url: str) -> List[str]:
        """
        Discover all URLs on the site.
        Uses 1 page credit.
        Returns list of URLs or empty list.
        """
        if not self.available:
            return []

        try:
            result = self.client.map(url=url, limit=100)
            self.pages_used += 1

            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "links" in result:
                return result["links"]

        except Exception as e:
            logger.warning(f"Firecrawl map failed for {url}: {e}")

        return []

    def scrape_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single page. Returns markdown + links.
        Uses 1 page credit.
        Returns dict with 'markdown', 'links' keys or None.
        """
        if not self.available:
            return None

        try:
            result = self.client.scrape(url, formats=["markdown", "links"])
            self.pages_used += 1
            return result

        except Exception as e:
            logger.warning(f"Firecrawl scrape failed for {url}: {e}")

        return None
```

---

## Part 3: Digital Presence Scanner

### New file: `strategy_factory/research/digital_presence_scanner.py`

```python
"""
Digital presence scanner using Firecrawl.

Scans a company's website, blog, and social media presence
to determine content activity levels for strategy reports.
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict

from ..models import (
    DigitalPresence,
    BlogPresence,
    SocialMediaPresence,
)
from .firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)

# Known social media platform URL patterns
SOCIAL_PLATFORMS = {
    "facebook": "facebook.com/",
    "instagram": "instagram.com/",
    "linkedin": "linkedin.com/",
    "twitter": "twitter.com/",
    "youtube": "youtube.com/",
    "tiktok": "tiktok.com/",
}

# Common blog URL patterns
BLOG_PATH_PATTERNS = [
    "/blog", "/blogs", "/news", "/articles", "/insights",
    "/resources", "/updates", "/content",
]


class DigitalPresenceScanner:
    """
    Scans a company's digital presence using Firecrawl.

    Credit budget per company: ~5-8 pages
    1. Search for website (1 page)
    2. Map site URLs (1 page)
    3. Scrape homepage (1 page)
    4. Scrape blog page (1 page)
    5. Scrape 1-3 social media profiles (1-3 pages)
    """

    def __init__(self, api_key: str):
        self.client = FirecrawlClient(api_key=api_key)

    def scan(self, company_name: str, industry: str = "") -> Optional[DigitalPresence]:
        """
        Run a complete digital presence scan.

        Returns DigitalPresence or None if Firecrawl unavailable.
        """
        if not self.client.available:
            return None

        presence = DigitalPresence(scan_timestamp=datetime.now())

        # Step 1: Find website
        website_url = self._find_website(company_name, industry)
        if not website_url:
            logger.info(f"No website found for {company_name}")
            return presence

        presence.website_url = website_url

        # Step 2: Map site to discover pages
        site_urls = self.client.map_site(website_url)

        # Step 3: Scrape homepage for social links
        homepage = self.client.scrape_page(website_url)
        presence.website_scraped = homepage is not None

        social_links = {}
        if homepage:
            social_links = self._extract_social_links(homepage, website_url)

        # Step 4: Find and scrape blog
        blog_url = self._discover_blog_url(site_urls, website_url)
        if blog_url:
            blog_data = self.client.scrape_page(blog_url)
            presence.blog = self._analyze_blog(blog_data, blog_url)
        else:
            presence.blog = BlogPresence(found=False)

        # Step 5: Scrape up to 3 social media profiles
        for platform, profile_url in list(social_links.items())[:3]:
            social_data = self.client.scrape_page(profile_url)
            presence.social_media.append(
                self._analyze_social_profile(platform, profile_url, social_data)
            )

        # Mark found platforms that we didn't scrape
        for platform, url in social_links.items():
            if not any(sm.platform == platform for sm in presence.social_media):
                presence.social_media.append(
                    SocialMediaPresence(platform=platform, url=url, found=True)
                )

        # Generate summary
        presence.content_activity_summary = self._summarize_activity(presence)
        presence.scan_cost_pages = self.client.pages_used

        return presence

    def _find_website(self, company_name: str, industry: str) -> Optional[str]:
        """Find company website URL via Firecrawl search."""
        return self.client.find_website(company_name, industry)

    def _discover_blog_url(self, site_urls: List[str], website_url: str) -> Optional[str]:
        """Find blog URL from sitemap/map results."""
        if not site_urls:
            return None

        for pattern in BLOG_PATH_PATTERNS:
            for url in site_urls:
                # Match URLs like example.com/blog, example.com/blog/page/2, etc.
                path_part = url.replace(website_url, "").lower()
                if path_part.startswith(pattern) or path_part == pattern:
                    # Return the base blog URL, not a pagination page
                    if "/page/" not in url and "/category/" not in url:
                        return url

        return None

    def _extract_social_links(self, homepage_data: dict, website_url: str) -> Dict[str, str]:
        """Extract social media profile links from homepage."""
        links = {}

        # Get links from Firecrawl response
        link_list = []
        if isinstance(homepage_data, dict):
            # Firecrawl returns links in different formats
            if "links" in homepage_data:
                link_list = homepage_data["links"]
            elif "metadata" in homepage_data and "links" in homepage_data["metadata"]:
                link_list = homepage_data["metadata"]["links"]

        # Also check markdown for URLs
        markdown = homepage_data.get("markdown", "") if isinstance(homepage_data, dict) else ""

        for platform, domain_pattern in SOCIAL_PLATFORMS.items():
            # Check structured links first
            for link in link_list:
                if isinstance(link, str) and domain_pattern in link.lower():
                    # Skip company page links on LinkedIn, skip feeds/feeds on others
                    if platform == "linkedin" and "/company/" in link.lower():
                        links[platform] = link
                    elif platform != "linkedin":
                        links[platform] = link
                    break

            # Fallback: regex search in markdown
            if platform not in links and markdown:
                url_pattern = rf'https?://(?:www\.)?{re.escape(domain_pattern)}[^\s\)"\'\]>]+'
                match = re.search(url_pattern, markdown, re.IGNORECASE)
                if match:
                    url = match.group(0).rstrip(".,;:")
                    # Skip share buttons and internal links
                    if "/sharer/" not in url and "/intent/" not in url:
                        links[platform] = url

        return links

    def _analyze_blog(self, blog_data: Optional[dict], blog_url: str) -> BlogPresence:
        """Parse blog page for post dates, titles, and frequency."""
        blog = BlogPresence(found=True, url=blog_url)

        if not blog_data:
            return blog

        markdown = blog_data.get("markdown", "") if isinstance(blog_data, dict) else ""
        if not markdown:
            return blog

        # Extract dates from markdown content
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{4}',
        ]

        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, markdown)
            dates_found.extend(matches)

        if dates_found:
            blog.last_post_date = dates_found[0]

            # Estimate total posts from date count
            blog.total_posts = len(dates_found)

            # Estimate frequency
            if len(dates_found) >= 2:
                blog.posting_frequency = self._estimate_frequency(dates_found)
            else:
                blog.posting_frequency = "Rarely"
        else:
            blog.posting_frequency = "Unknown"
            blog.total_posts = 0

        # Extract recent titles (look for heading patterns or link text)
        title_patterns = [
            r'^#+\s+(.+)$',           # Markdown headings
            r'\[(.+?)\]\(.+?\)',      # Markdown links
        ]
        titles = []
        for pattern in title_patterns:
            matches = re.findall(pattern, markdown, re.MULTILINE)
            for title in matches:
                title = title.strip()
                # Filter out navigation items and very short titles
                if len(title) > 15 and len(title) < 120:
                    titles.append(title)

        blog.recent_titles = list(dict.fromkeys(titles))[:5]  # Dedupe, keep order

        # Determine activity level
        blog.activity_level = self._classify_activity(blog.posting_frequency)

        return blog

    def _analyze_social_profile(self, platform: str, url: str, data: Optional[dict]) -> SocialMediaPresence:
        """Analyze social media profile page for activity data."""
        presence = SocialMediaPresence(platform=platform, url=url, found=True)

        if not data:
            presence.activity_level = "unknown"
            return presence

        markdown = data.get("markdown", "") if isinstance(data, dict) else ""
        if not markdown:
            presence.activity_level = "unknown"
            return presence

        # Extract follower/like counts
        follower_patterns = [
            r'([\d,]+(?:\.\d+)?)\s*(?:followers?|likes?|subscribers?|friends?)',
            r'([\d,]+(?:K|k|M|m)?)\s*(?:followers?|likes?)',
        ]
        for pattern in follower_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                presence.follower_count = match.group(1)
                break

        # Extract dates for last activity
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}',
            r'\d{4}-\d{2}-\d{2}',
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, markdown))

        if dates:
            presence.last_post_date = dates[0]

        # Determine activity level based on content length and dates
        if len(markdown) > 500 and dates:
            presence.activity_level = "active"
            presence.posting_frequency = "Regular"
        elif len(markdown) > 200:
            presence.activity_level = "occasional"
            presence.posting_frequency = "Occasional"
        else:
            presence.activity_level = "inactive"
            presence.posting_frequency = "Inactive"

        return presence

    def _estimate_frequency(self, dates: List[str]) -> str:
        """Estimate posting frequency from date list."""
        if len(dates) < 2:
            return "Unknown"
        # Simple heuristic: more dates in the markdown = more active
        count = len(dates)
        if count >= 10:
            return "Multiple times per week"
        elif count >= 5:
            return "Weekly"
        elif count >= 3:
            return "Bi-weekly"
        elif count >= 2:
            return "Monthly"
        return "Rarely"

    def _classify_activity(self, frequency: Optional[str]) -> str:
        """Classify activity level from frequency string."""
        if not frequency:
            return "unknown"
        freq = frequency.lower()
        if any(w in freq for w in ["multiple", "weekly", "bi-weekly"]):
            return "active"
        elif any(w in freq for w in ["monthly", "occasional"]):
            return "occasional"
        return "inactive"

    def _summarize_activity(self, presence: DigitalPresence) -> str:
        """Generate a one-line content activity summary."""
        parts = []

        # Blog status
        if presence.blog.found:
            freq = presence.blog.posting_frequency or "unknown"
            if presence.blog.activity_level == "inactive":
                parts.append("blog inactive")
            elif presence.blog.activity_level == "occasional":
                parts.append(f"blog updated {freq.lower()}")
            else:
                parts.append(f"blog active ({freq.lower()})")
        else:
            parts.append("no blog found")

        # Social status
        active_social = [sm for sm in presence.social_media if sm.activity_level == "active"]
        inactive_social = [sm for sm in presence.social_media if sm.activity_level in ("inactive", "unknown")]
        if active_social:
            platforms = ", ".join(sm.platform for sm in active_social)
            parts.append(f"active on {platforms}")
        if inactive_social:
            platforms = ", ".join(sm.platform for sm in inactive_social)
            parts.append(f"{platforms} inactive or minimal")

        if not parts:
            return "No digital presence data available"

        return "; ".join(parts).capitalize()
```

---

## Part 4: Module Export

### File: `strategy_factory/research/__init__.py`

Add to imports:
```python
from .digital_presence_scanner import DigitalPresenceScanner
```

Add to `__all__`:
```python
"DigitalPresenceScanner",
```

---

## Part 5: Dependencies & Config

### File: `requirements.txt`

Add at end:
```
firecrawl-py>=2.0.0
```

### File: `.env.example`

Add:
```
FIRECRAWL_API_KEY=fc-xxx  # Optional — enables digital presence scanning
```

### File: `strategy_factory/main.py`

In `_check_api_keys()`, add after the Gemini/Perplexity checks:
```python
if not os.getenv("FIRECRAWL_API_KEY"):
    logger.info("FIRECRAWL_API_KEY not set — digital presence scan will be skipped")
```

In `_dry_run()` output, add before Phase 1:
```
0. DIGITAL PRESENCE SCAN (optional)
   Tool: Firecrawl
   Pages: ~5-8 per company
   Est. Cost: Free tier covers 50-100 companies
```

---

## Verification

```bash
# 1. Import check
source venv/bin/activate
python -c "from strategy_factory.research.digital_presence_scanner import DigitalPresenceScanner; print('OK')"

# 2. Model check
python -c "from strategy_factory.models import DigitalPresence, BlogPresence, SocialMediaPresence; print('OK')"

# 3. Client init without key (should not crash)
python -c "from strategy_factory.research.firecrawl_client import FirecrawlClient; c = FirecrawlClient('test'); print('available:', c.available)"

# 4. Dry run
python -m strategy_factory.main run "Test Company" --dry-run
```
