# LOGO-EXTRACT.md — Implementation Handoff

## What We're Building

Add automatic logo extraction from a company website URL. When a user provides a URL on the main form (and doesn't manually upload a logo), the backend fetches the company's homepage, finds the logo, and places it into the PPTX/DOCX/PDF cover pages. Also add SVG drag-and-drop support.

**User decisions:**
- Logo extraction happens **silently on form submit** (no AJAX preview)
- SVG support uses **cairosvg** as a soft dependency (graceful error if missing)

---

## Architecture Overview

```
Form submit → webapp.py /start handler
                ├─ 1. Check for manual logo upload (existing, priority)
                ├─ 2. If no manual upload + website URL provided → extract_logo_from_url()
                └─ 3. Pass logo_path into pipeline as before
```

---

## Design Decisions

### Logo extraction strategies (ordered)
1. `<img>` with "logo" in class/id/src/alt — most reliable for actual logos
2. `apple-touch-icon` — usually 180x180, decent quality

**Dropped**: `og:image` and `twitter:image` — these are social sharing previews, often hero images or marketing banners, not logos.

### Error handling
- Logo extraction failure **never** blocks the pipeline
- If image can't be parsed/converted, return `None` and skip — no raw-bytes fallback
- cairosvg is a soft dependency: if missing, SVG upload returns a clear error message

### Download safety
- 10-second timeout on HTTP requests
- 5 MB max image download size (streamed with content-length check)

---

## Step-by-Step Implementation

### Step 1: Add dependencies to `requirements.txt`

```
# Logo extraction
beautifulsoup4>=4.12.0
lxml>=5.0.0
Pillow>=10.0.0
```

**Note:** `cairosvg` is NOT in requirements.txt — it's optional. Users who want SVG support install it manually along with system cairo (`brew install cairo`).

### Step 2: Create `strategy_factory/logo_extractor.py` (NEW FILE)

Single function: `extract_logo_from_url(url, save_dir) -> Optional[str]`

- Fetches homepage HTML
- Finds logo via `<img>` tag with "logo" in attributes, then apple-touch-icon fallback
- Downloads image with 5 MB size guard
- Converts to PNG via Pillow (or cairosvg for SVG if available)
- Returns path or None on any failure

### Step 3: Modify `strategy_factory/webapp.py`

- Add website URL field to form
- Add SVG to accepted upload types (soft dep on cairosvg)
- Read `website` from form in `/start` handler
- Auto-extract logo when no manual upload + website provided
- Pass `website` through to `run_pipeline` and `CompanyInput`

---

## Priority logic (must be preserved):
1. Manual logo upload always wins
2. Auto-extracted logo is fallback
3. No logo at all is fine — pipeline works either way

## Verification Checklist

1. `pip install -r requirements.txt` succeeds (beautifulsoup4, lxml, Pillow)
2. Enter company name + website URL (no manual logo) → submit → logo appears on PPTX/DOCX cover
3. Enter company name + website URL + drag-and-drop a logo → manual logo wins
4. Enter company name only → no logo, pipeline works fine
5. Drag-and-drop an SVG file with cairosvg installed → converts and appears in output
6. Drag-and-drop an SVG file without cairosvg → clear error message
7. Enter an invalid URL → graceful skip, no crash, pipeline continues
8. Website returns a 50 MB image → download aborted at 5 MB, pipeline continues
