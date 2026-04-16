"""
Direct technology detection via DNS and HTTP inspection.

Detects a company's actual tech stack by checking:
- MX records for email provider (Google Workspace, Microsoft 365, etc.)
- HTTP response headers and meta tags for CMS and hosting
- DNS records for CDN and infrastructure

Zero API cost. Uses only DNS lookups and a single HTTP request.
"""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# MX record patterns → email provider
MX_PROVIDERS = [
    (["google.com", "googlemail.com", "aspmx.l.google.com"], "Google Workspace"),
    (["outlook.com", "microsoft.com", "protection.outlook.com"], "Microsoft 365"),
    (["zoho.com", "zohomail.com"], "Zoho Mail"),
    (["pphosted.com", "proofpoint.com"], "Proofpoint (email security)"),
    (["mimecast.com"], "Mimecast (email security)"),
    (["emailsrvr.com", "rackspace.com"], "Rackspace Email"),
    (["secureserver.net", "mailstore.secureserver.net"], "GoDaddy Email"),
    (["yahoodns.net"], "Yahoo Mail"),
    (["fastmail.com"], "Fastmail"),
]

# HTTP header/meta patterns → CMS
CMS_PATTERNS = {
    "wp-content": "WordPress",
    "wp-includes": "WordPress",
    "Shopify": "Shopify",
    "squarespace": "Squarespace",
    "wix.com": "Wix",
    "webflow": "Webflow",
    "ghost": "Ghost",
    "drupal": "Drupal",
    "joomla": "Joomla",
}

# Server header patterns → hosting/platform
SERVER_PATTERNS = {
    "cloudflare": "Cloudflare",
    "vercel": "Vercel",
    "netlify": "Netlify",
    "nginx": "Nginx",
    "apache": "Apache",
    "aws": "AWS",
    "ghs.googlehosted.com": "Google Sites",
}

# CNAME patterns → CRM/scheduling platform (strongest signal)
CRM_SCHED_CNAME_PATTERNS = {
    # CRM + Scheduling dual
    "dubsado": "Dubsado (CRM + Scheduling)",
    "honeybook": "HoneyBook (CRM + Scheduling)",
    "gohighlevel": "GoHighLevel (CRM + Scheduling)",
    "ghl": "GoHighLevel (CRM + Scheduling)",
    # Pure scheduling
    "calendly": "Calendly (Scheduling)",
    "acuityscheduling": "Acuity Scheduling",
    "setmore": "Setmore (Scheduling)",
    "mindbody": "Mindbody (Scheduling)",
    "vagaro": "Vagaro (Scheduling)",
    "booksy": "Booksy (Scheduling)",
    "fresha": "Fresha (Scheduling)",
    "styleseat": "StyleSeat (Scheduling)",
    "square": "Square Appointments (Scheduling)",
}

# Subdomains checked for CRM/scheduling CNAMEs
CRM_SCHED_SUBDOMAINS = ["portal", "booking", "schedule", "cal"]

# MX record patterns → CRM (reuses MX records already fetched for email detection)
# Microsoft Dynamics 365 excluded — overlaps with Microsoft 365 email MX.
CRM_MX_PATTERNS = [
    (["dubsado"], "Dubsado (CRM + Scheduling)"),
    (["hubspot", "hubspotemail"], "HubSpot CRM"),
    (["infusionsoft", "keap"], "Keap (formerly Infusionsoft)"),
    (["activecampaign"], "ActiveCampaign"),
    (["salesforce"], "Salesforce"),
    (["ghlconnect", "gohighlevel"], "GoHighLevel (CRM + Scheduling)"),
]

# HTML substring patterns → CRM/scheduling (fallback signal)
CRM_SCHED_HTML_PATTERNS = {
    # CRM
    "dubsado": "Dubsado (CRM + Scheduling)",
    "honeybook": "HoneyBook (CRM + Scheduling)",
    "hubspot": "HubSpot CRM",
    "hs-scripts": "HubSpot CRM",
    "salesforce": "Salesforce",
    "lightning.force.com": "Salesforce",
    "keap": "Keap",
    "infusionsoft": "Keap",
    "activecampaign": "ActiveCampaign",
    "pipedrive": "Pipedrive",
    "zoho": "Zoho CRM",
    "gohighlevel": "GoHighLevel (CRM + Scheduling)",
    # Scheduling
    "calendly": "Calendly (Scheduling)",
    "acuityscheduling": "Acuity Scheduling",
    "setmore": "Setmore (Scheduling)",
    "mindbody": "Mindbody (Scheduling)",
    "vagaro": "Vagaro (Scheduling)",
    "booksy": "Booksy (Scheduling)",
    "fresha": "Fresha (Scheduling)",
    "styleseat": "StyleSeat (Scheduling)",
    "square appointments": "Square Appointments (Scheduling)",
}


@dataclass
class TechDetectionResult:
    """Results from direct technology detection."""
    domain: str
    email_provider: Optional[str] = None
    mx_records: List[str] = field(default_factory=list)
    cms: Optional[str] = None
    crm: Optional[str] = None
    hosting: Optional[str] = None
    cdn: Optional[str] = None
    analytics: List[str] = field(default_factory=list)
    other_tech: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_tech_list(self) -> List[str]:
        """Return a flat list of detected technologies."""
        techs = []
        if self.email_provider:
            techs.append(self.email_provider)
        if self.cms:
            techs.append(self.cms)
        if self.crm:
            techs.append(self.crm)
        if self.hosting:
            techs.append(self.hosting)
        if self.cdn:
            techs.append(self.cdn)
        techs.extend(self.analytics)
        techs.extend(self.other_tech)
        return techs

    def to_summary(self) -> str:
        """Return a human-readable summary for prompt injection."""
        lines = []
        if self.email_provider:
            lines.append(f"- Email: {self.email_provider} (verified via MX records)")
        if self.cms:
            lines.append(f"- Website CMS: {self.cms} (verified via HTTP inspection)")
        if self.crm:
            lines.append(f"- CRM/Scheduling: {self.crm}")
        if self.hosting:
            lines.append(f"- Hosting/CDN: {self.hosting}")
        if self.analytics:
            lines.append(f"- Analytics: {', '.join(self.analytics)}")
        if self.other_tech:
            lines.append(f"- Other: {', '.join(self.other_tech)}")
        if not lines:
            return ""
        return "## Verified Tech Stack (detected directly, not inferred)\n" + "\n".join(lines)


def detect_tech(domain_or_url: str) -> TechDetectionResult:
    """
    Detect technologies used by a company from its domain.

    Args:
        domain_or_url: A domain name (e.g. "acme.com") or URL.

    Returns:
        TechDetectionResult with findings.
    """
    domain = _extract_domain(domain_or_url)
    result = TechDetectionResult(domain=domain)

    # Run MX lookup and HTTP inspection independently
    _detect_email_provider(domain, result)
    _detect_crm_cname(domain, result)
    _detect_web_tech(domain, result)

    return result


def _extract_domain(domain_or_url: str) -> str:
    """Extract bare domain from a URL or domain string."""
    if domain_or_url.startswith(("http://", "https://")):
        parsed = urlparse(domain_or_url)
        return parsed.netloc.lower().removeprefix("www.")
    return domain_or_url.lower().removeprefix("www.")


def _detect_email_provider(domain: str, result: TechDetectionResult) -> None:
    """Look up MX records to identify the email provider and CRM."""
    try:
        output = subprocess.run(
            ["dig", "+short", "MX", domain],
            capture_output=True,
            text=True,
            timeout=10,
        )
        mx_lines = [
            line.strip().rstrip(".").lower()
            for line in output.stdout.strip().split("\n")
            if line.strip()
        ]
        result.mx_records = mx_lines

    except FileNotFoundError:
        # dig not available, try nslookup
        try:
            output = subprocess.run(
                ["nslookup", "-type=MX", domain],
                capture_output=True,
                text=True,
                timeout=10,
            )
            result.mx_records = [output.stdout.lower()]
        except Exception as e:
            result.errors.append(f"MX lookup failed: {e}")
            return
    except Exception as e:
        result.errors.append(f"MX lookup failed: {e}")
        return

    # Match email provider
    for mx_line in result.mx_records:
        for patterns, provider in MX_PROVIDERS:
            if any(p in mx_line for p in patterns):
                result.email_provider = provider
                break
        if result.email_provider:
            break

    # Match CRM MX patterns (reuses same MX records)
    for mx_line in result.mx_records:
        for patterns, crm_name in CRM_MX_PATTERNS:
            if any(p in mx_line for p in patterns):
                result.crm = crm_name
                return


def _detect_crm_cname(domain: str, result: TechDetectionResult) -> None:
    """Check common subdomains for CNAMEs pointing to CRM/scheduling platforms.

    CNAME is the strongest signal and overrides any MX-based detection.
    """
    for subdomain in CRM_SCHED_SUBDOMAINS:
        fqdn = f"{subdomain}.{domain}"
        try:
            output = subprocess.run(
                ["dig", "+short", "CNAME", fqdn],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError:
            return  # no dig available, skip CNAME detection
        except Exception as e:
            result.errors.append(f"CNAME lookup failed for {fqdn}: {e}")
            continue

        cname = output.stdout.strip().lower()
        if not cname:
            continue
        for pattern, label in CRM_SCHED_CNAME_PATTERNS.items():
            if pattern in cname:
                result.crm = label
                return


def _detect_web_tech(domain: str, result: TechDetectionResult) -> None:
    """Inspect HTTP response to detect CMS, hosting, and analytics."""
    url = f"https://{domain}"
    try:
        with httpx.Client(timeout=10, follow_redirects=True, headers=HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except Exception as e:
        # Try www. prefix
        try:
            url = f"https://www.{domain}"
            with httpx.Client(timeout=10, follow_redirects=True, headers=HEADERS) as client:
                resp = client.get(url)
                resp.raise_for_status()
        except Exception as e2:
            result.errors.append(f"HTTP fetch failed: {e2}")
            return

    html = resp.text
    headers = {k.lower(): v.lower() for k, v in resp.headers.items()}

    # Detect CMS from HTML content
    html_lower = html.lower()
    for pattern, cms_name in CMS_PATTERNS.items():
        if pattern.lower() in html_lower:
            result.cms = cms_name
            break

    # Check meta generator tag — only use it if no CMS was detected yet,
    # or if it names a known CMS (plugins often set generator tags too)
    soup = BeautifulSoup(html, "lxml")
    generator = soup.find("meta", attrs={"name": "generator"})
    if generator and generator.get("content"):
        gen_content = generator["content"].strip()
        gen_lower = gen_content.lower()
        known_cms = ["wordpress", "shopify", "squarespace", "wix", "webflow",
                     "ghost", "drupal", "joomla", "hugo", "jekyll"]
        for cms in known_cms:
            if cms in gen_lower:
                result.cms = gen_content.split("/")[0].strip()
                break
        else:
            # Unknown generator — only override if nothing detected yet
            if not result.cms:
                result.cms = gen_content.split("/")[0].strip()

    # Detect hosting/CDN from headers
    server = headers.get("server", "")
    for pattern, host_name in SERVER_PATTERNS.items():
        if pattern in server:
            result.hosting = host_name
            break

    # Cloudflare detection via headers
    if "cf-ray" in headers or "cf-cache-status" in headers:
        result.cdn = "Cloudflare"
    elif headers.get("x-vercel-id"):
        result.hosting = "Vercel"
    elif headers.get("x-nf-request-id"):
        result.hosting = "Netlify"

    # Detect analytics from HTML
    if "google-analytics.com" in html_lower or "gtag" in html_lower or "googletagmanager" in html_lower:
        result.analytics.append("Google Analytics")
    if "hotjar" in html_lower:
        result.analytics.append("Hotjar")
    if "facebook.com/tr" in html_lower or "fbevents" in html_lower:
        result.analytics.append("Meta Pixel")
    if "plausible.io" in html_lower:
        result.analytics.append("Plausible Analytics")
    if "clarity.ms" in html_lower:
        result.analytics.append("Microsoft Clarity")

    # Detect CRM/scheduling from HTML (only if not already set by CNAME or MX)
    if result.crm is None:
        for pattern, crm_name in CRM_SCHED_HTML_PATTERNS.items():
            if pattern in html_lower:
                result.crm = crm_name
                break

    # Detect other notable tech
    if "recaptcha" in html_lower:
        result.other_tech.append("reCAPTCHA")
    if "stripe" in html_lower:
        result.other_tech.append("Stripe")
    if "intercom" in html_lower:
        result.other_tech.append("Intercom")
    if "mailchimp" in html_lower:
        result.other_tech.append("Mailchimp")
    if "crisp" in html_lower and "crisp.chat" in html_lower:
        result.other_tech.append("Crisp Chat")
    if "zendesk" in html_lower:
        result.other_tech.append("Zendesk")
    if "tawk.to" in html_lower:
        result.other_tech.append("Tawk.to")
