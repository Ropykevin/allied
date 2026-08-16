"""HTML and URL sanitization helpers."""

from __future__ import annotations

from urllib.parse import urlparse

import bleach
from markupsafe import Markup

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "ul",
    "ol",
    "li",
    "a",
    "h2",
    "h3",
    "h4",
    "blockquote",
    "code",
    "pre",
    "span",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel", "target"],
    "span": ["class"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

MAP_EMBED_HOSTS = {
    "www.google.com",
    "maps.google.com",
    "maps.googleapis.com",
    "www.openstreetmap.org",
    "openstreetmap.org",
}


def sanitize_html(value: str | None) -> Markup:
    """Allowlist-sanitize HTML for public rendering."""
    if not value:
        return Markup("")
    cleaned = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    cleaned = bleach.linkify(cleaned, parse_email=False)
    return Markup(cleaned)


def plain_text_to_html(value: str | None) -> Markup:
    """Escape plain text and convert newlines to <br>."""
    if not value:
        return Markup("")
    return sanitize_html(bleach.clean(value).replace("\n", "<br>"))


def safe_external_url(value: str | None) -> str | None:
    """Allow only http(s) absolute URLs (no javascript:/data:)."""
    if not value:
        return None
    raw = value.strip()
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        return None
    if not parsed.netloc:
        return None
    return raw


def safe_map_embed_url(value: str | None) -> str | None:
    """Allow https map embeds from known hosts only."""
    url = safe_external_url(value)
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None
    host = (parsed.hostname or "").lower()
    if host not in MAP_EMBED_HOSTS and not host.endswith(".google.com"):
        return None
    return url


def escape_pdf_text(value: str | None) -> str:
    """Escape text for ReportLab Paragraph markup."""
    if not value:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def normalize_phone(value: str | None) -> str:
    """Digits-only phone normalization for exact matching."""
    if not value:
        return ""
    return "".join(ch for ch in value if ch.isdigit())
