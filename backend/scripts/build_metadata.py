"""Build the bundled LeetCode metadata dataset.

Downloads the ``whiskwhite/leetcode-complete`` community dataset (JSONL) from
Hugging Face and trims it down to the fields the app stores, keyed by slug:

    { "<slug>": {"title": str, "difficulty": "Easy|Medium|Hard", "tags": [str, ...]}, ... }

Run from the repo root (or anywhere) with::

    python scripts/build_metadata.py

The output lands in ``app/data/leetcode_metadata.json``. This is the "refresh
occasionally" step referenced in the design docs — LeetCode has no stable
public REST API, so the metadata ships as a static file rather than a live
query.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

_FILES = ("train.jsonl", "validation.jsonl", "test.jsonl")
_BASE = "https://huggingface.co/datasets/whiskwhite/leetcode-complete/resolve/main/"
_OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "leetcode_metadata.json"

_KEYS = ("title", "difficulty", "topic_tags")


def _fetch_lines(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "leetsolv-web-build/0.1"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                yield line


def main() -> int:
    problems: dict[str, dict] = {}
    for name in _FILES:
        url = _BASE + name
        count = 0
        for line in _fetch_lines(url):
            rec = json.loads(line)
            slug = rec.get("title_slug")
            if not slug:
                continue
            problems[slug] = {
                "title": rec.get("title", ""),
                "difficulty": rec.get("difficulty", "Easy"),
                "tags": list(rec.get("topic_tags") or []),
            }
            count += 1
        print(f"{name}: {count} records", file=sys.stderr)

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(problems, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size = _OUT.stat().st_size
    print(f"wrote {_OUT} ({len(problems)} problems, {size:,} bytes)", file=sys.stderr)

    # Sanity-check the four slugs we actually import.
    known = [
        "remove-duplicates-from-sorted-array-ii",
        "valid-palindrome",
        "sort-colors",
        "merge-sorted-array",
    ]
    for slug in known:
        print(f"  {slug}: {problems.get(slug, 'MISSING')!r}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
