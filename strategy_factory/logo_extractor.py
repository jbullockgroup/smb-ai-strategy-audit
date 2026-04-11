"""
Extract company logo from a website URL.
Checks <img> tags with "logo" in attributes, preferring header/homepage placement
and skipping gallery patterns, then falls back to apple-touch-icon.
"""

import io
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def extract_logo_from_url(url: str, save_dir: Path) -> Optional[str]:
    """
    Extract a company logo from a URL and save as PNG.

    Returns path to saved PNG file, or None if extraction failed.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Fetch homepage
    try:
        with httpx.Client(timeout=10, follow_redirects=True, headers=HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html = resp.text
            base_url = str(resp.url)
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(html, "lxml")
    logo_url = _find_logo_url(soup)

    if not logo_url:
        logger.info(f"No logo found on {url}")
        return None

    logo_url = urljoin(base_url, logo_url)

    # Download image with size guard
    image_bytes = _download_image(logo_url)
    if not image_bytes:
        return None

    # Convert to PNG and save
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / "company_logo.png"

    try:
        if logo_url.lower().endswith(".svg"):
            try:
                import cairosvg
            except ImportError:
                logger.warning("cairosvg not installed — cannot convert SVG logo. Install with: pip install cairosvg (requires system cairo)")
                return None
            cairosvg.svg2png(bytestring=image_bytes, write_to=str(save_path))
        else:
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(image_bytes))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.save(str(save_path), "PNG")
    except Exception as e:
        logger.warning(f"Failed to convert logo to PNG: {e}")
        return None

    logger.info(f"Logo extracted and saved to {save_path}")
    return str(save_path)


def _attrs_text(img) -> str:
    """Lowercase concatenation of an img tag's class, id, src, and alt."""
    return " ".join([
        " ".join(img.get("class", [])),
        img.get("id", ""),
        img.get("src", ""),
        img.get("alt", ""),
    ]).lower()


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


def _download_image(image_url: str) -> Optional[bytes]:
    """Download image with size guard (5 MB max)."""
    try:
        with httpx.Client(timeout=10, follow_redirects=True, headers=HEADERS) as client:
            with client.stream("GET", image_url) as resp:
                resp.raise_for_status()

                # Check content-length header if available
                content_length = resp.headers.get("content-length")
                if content_length and int(content_length) > MAX_IMAGE_BYTES:
                    logger.warning(f"Logo too large ({content_length} bytes), skipping")
                    return None

                # Stream with size cap
                chunks = []
                total = 0
                for chunk in resp.iter_bytes(chunk_size=8192):
                    total += len(chunk)
                    if total > MAX_IMAGE_BYTES:
                        logger.warning(f"Logo download exceeded {MAX_IMAGE_BYTES} bytes, aborting")
                        return None
                    chunks.append(chunk)

                return b"".join(chunks)
    except Exception as e:
        logger.warning(f"Failed to download logo from {image_url}: {e}")
        return None
