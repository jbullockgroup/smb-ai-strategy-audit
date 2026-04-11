# IMPROVE-LOGO.md — Logo Extraction Fix

## Handoff Document

This file contains the full plan and context for fixing the logo extraction logic in the AI Strategy Factory. A new agent should be able to implement this from this document alone.

---

## The Problem

The logo extractor (`strategy_factory/logo_extractor.py`) has a **33% success rate** (1 of 3 companies). It fails because `_find_logo_url()` takes the **first** `<img>` tag with "logo" in any attribute, with no sense of where that image lives on the page.

### Specific Failure: Mountain BizWorks

When extracting from `https://www.mountainbizworks.org/`, the first `<img>` match was:

```
src=https://www.mountainbizworks.org/wp-content/uploads/2019/08/ugotour-01.svg
class=['img-fluid', 'logo-thumb', 'wp-post-image']
```

This is a **client's logo** in a partner gallery, not Mountain BizWorks' own logo. The CSS class `logo-thumb` triggered the "logo" keyword match. The file is an SVG, so when cairosvg (a soft dependency) isn't installed, the extraction silently returns None.

The real Mountain BizWorks logo doesn't have "logo" in any `<img>` attribute — it's in the header but uses different naming. Meanwhile, their `apple-touch-icon` (`cropped-mbw-favicon-1-180x180.png`) is genuine branding, but it's the last-resort fallback and was never reached because a (wrong) match was found first.

### Other Companies

- **Healing Roots Design** (`healingrootsdesign.com`) — Succeeded. Their site has a clean `<img>` with "logo" in the header.
- **Angela Kim Couture** (`angelakimcouture.com`) — Failed. Likely similar issue (no "logo" keyword on header image).

---

## Current Code

The only file that needs modification: **`strategy_factory/logo_extractor.py`**

Key function (lines 85-103):

```python
def _find_logo_url(soup: BeautifulSoup) -> Optional[str]:
    """Find logo URL from HTML, trying img tags then apple-touch-icon."""
    # Strategy 1: <img> with "logo" in class/id/src/alt
    for img in soup.find_all("img"):
        attrs_str = " ".join([
            " ".join(img.get("class", [])),
            img.get("id", ""),
            img.get("src", ""),
            img.get("alt", ""),
        ]).lower()
        if "logo" in attrs_str and img.get("src"):
            return img["src"]  # <-- Takes FIRST match, no filtering

    # Strategy 2: apple-touch-icon
    apple = soup.find("link", rel="apple-touch-icon")
    if apple and apple.get("href"):
        return apple["href"]

    return None
```

### Caller

Only called from `strategy_factory/webapp.py` at lines 1341-1344:

```python
if not logo_path_str and website:
    from strategy_factory.logo_extractor import extract_logo_from_url
    logo_dir = OUTPUT_DIR / company_slug / "logo"
    logo_path_str = extract_logo_from_url(website, logo_dir)
```

Not used from CLI (`main.py`). No tests currently exist for this module.

---

## Design: Two-Pass Filter

Replace the single first-match loop with a **two-pass approach**: first look for logo images in high-confidence locations (`<header>`, homepage links), then fall back to the current keyword match with gallery pattern exclusions. If neither pass finds a result, fall through to `apple-touch-icon`.

This fixes the problem with ~15 lines of change and no new helper functions.

### Why Two Passes Instead of Scoring

The candidates on SMB sites are typically 3-5 images. A weighted scoring system with 11 signals is machinery for a ranking problem that doesn't exist here. The real insight is just two rules:

1. **Prefer** images inside `<header>` or wrapped in `<a href="/">`
2. **Skip** images with known gallery classes (`wp-post-image`, `logo-thumb`, `client-logo`)

A two-pass filter expresses this directly and is easy to reason about.

---

## Implementation

### Step 1: Extract the attribute-string helper (lines 88-94)

The attribute concatenation logic is reused in both passes. Extract it to a small private function placed directly above `_find_logo_url`:

```python
def _attrs_text(img) -> str:
    """Lowercase concatenation of an img tag's class, id, src, and alt."""
    return " ".join([
        " ".join(img.get("class", [])),
        img.get("id", ""),
        img.get("src", ""),
        img.get("alt", ""),
    ]).lower()
```

### Step 2: Rewrite `_find_logo_url` body (lines 85-103)

Replace with:

```python
def _find_logo_url(soup: BeautifulSoup) -> Optional[str]:
    """Find logo URL from HTML using location-aware search with apple-touch-icon fallback."""
    # Pass 1: logo img inside <header> or linked to homepage — high confidence
    for img in soup.select("header img, a[href='/'] > img"):
        if "logo" in _attrs_text(img) and img.get("src"):
            return img["src"]

    # Pass 2: any img with "logo", skipping known gallery patterns
    gallery_markers = ("wp-post-image", "logo-thumb", "client-logo", "partner")
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or src.startswith("data:"):
            continue
        attrs = _attrs_text(img)
        if "logo" not in attrs:
            continue
        if any(marker in attrs for marker in gallery_markers):
            continue
        return src

    # Pass 3: apple-touch-icon fallback
    apple = soup.find("link", rel="apple-touch-icon")
    if apple and apple.get("href"):
        return apple["href"]

    return None
```

**Changes from the original:**
- Pass 1 is new — prefers header/homepage-linked logos
- Pass 2 is the original loop with gallery exclusions added and `data:` URI filtering
- Pass 3 (apple-touch-icon) is unchanged

### Step 3: Update module docstring (lines 1-4)

Change to:

```python
"""
Extract company logo from a website URL.
Checks <img> tags with "logo" in attributes, preferring header/homepage placement
and skipping gallery patterns, then falls back to apple-touch-icon.
"""
```

### Step 4: Add tests

Create `tests/test_logo_extractor.py` and `tests/__init__.py` (empty).

Tests use `BeautifulSoup(markup, "lxml")` directly — no HTTP mocking needed since `_find_logo_url` takes a soup object.

**Test cases:**

1. **Header logo beats gallery** — HTML with a header logo (inside `<header>`, class containing "logo") and gallery items with `logo-thumb wp-post-image`. Assert header logo's src is returned.

2. **Gallery items skipped, falls to apple-touch-icon** — Page with only gallery-style logo images (`wp-post-image` class), plus an `<link rel="apple-touch-icon">`. Assert returns the apple-touch-icon href.

3. **No img candidates → apple-touch-icon fallback** — Page with no `<img>` tags at all, but has `<link rel="apple-touch-icon">`. Assert returns the apple-touch-icon href.

4. **Mountain BizWorks regression** — Reproduce the actual MBW markup pattern: list of client logos with `logo-thumb` class, no "logo" keyword on the real header image. Assert the gallery items are skipped and apple-touch-icon is returned.

---

## What Does NOT Change

- `extract_logo_from_url` — the public function (lines 25-82). No changes.
- `_download_image` (lines 106-132) — untouched.
- SVG/cairosvg handling in `extract_logo_from_url` (lines 64-69) — untouched.
- `webapp.py` caller (lines 1341-1344) — untouched.
- No new dependencies. Only uses what's already installed: beautifulsoup4, lxml.

---

## Verification

1. **Unit tests**: `python -m pytest tests/test_logo_extractor.py -v` — all pass

2. **Manual regression — Mountain BizWorks** (previously failed):
   ```python
   from strategy_factory.logo_extractor import extract_logo_from_url
   from pathlib import Path
   result = extract_logo_from_url("https://www.mountainbizworks.org/", Path("/tmp/mbw-logo"))
   print(result)  # Should return a path now, not None
   ```

3. **Manual regression — Healing Roots Design** (previously succeeded):
   ```python
   result = extract_logo_from_url("https://www.healingrootsdesign.com/", Path("/tmp/hrd-logo"))
   print(result)  # Should still return a path
   ```

---

## Risks

| Risk | Mitigation |
|---|---|
| Pass 1 CSS selector misses unusual header markup | Pass 2 still catches it via keyword match with gallery filtering |
| Gallery marker list incomplete for non-WordPress sites | Easy to extend — just add strings to the tuple |
| `data:` URI filter is new behavior | These fail in `_download_image` anyway, so skipping early is strictly better |
