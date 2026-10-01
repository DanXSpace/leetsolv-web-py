"""LeetCode URL parsing and normalization (port of leetsolv's urlparser)."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_PATH_RE = re.compile(r"^/problems/([^/]+)")


class UrlError(ValueError):
    """The input is not a supported, well-formed LeetCode problem URL."""


def parse_leetcode_url(raw: str) -> tuple[str, str]:
    """Return ``(slug, normalized_url)`` or raise :class:`UrlError`.

    Matches leetsolv's parser: host must be ``leetcode.com`` and the path must
    start with ``/problems/<slug>``. The normalized URL is the canonical
    ``https://leetcode.com/problems/<slug>/``.
    """
    raw = (raw or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host != "leetcode.com":
        raise UrlError(f"unsupported host {host!r}; expected leetcode.com")
    match = _PATH_RE.match(parsed.path or "")
    if not match:
        raise UrlError(f"not a LeetCode problem URL: {raw!r}")
    slug = match.group(1).strip()
    if not slug:
        raise UrlError(f"empty problem slug in {raw!r}")
    return slug, f"https://leetcode.com/problems/{slug}/"
