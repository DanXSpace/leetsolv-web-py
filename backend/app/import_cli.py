"""One-time migration CLI: import ``~/.leetsolv/`` into leetsolv-web.

Reads leetsolv's ``questions.json`` + ``deltas.json``, enriches each problem
from the bundled LeetCode metadata, and writes the SQLite DB. Safe to run
repeatedly (idempotent by URL). Intended to run once against the real data,
after which the leetsolv CLI can be retired.

Usage (from ``backend/``)::

    python -m app.import_cli [--leetsolv-dir PATH]

The target DB respects ``LEETSOLV_DATABASE_URL`` (default ``sqlite:///./leetsolv.db``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.db import SessionLocal, init_db
from app.service import QuestionService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--leetsolv-dir",
        default=None,
        help="Directory holding questions.json + deltas.json (default: ~/.leetsolv)",
    )
    args = parser.parse_args(argv)

    src = Path(args.leetsolv_dir).expanduser() if args.leetsolv_dir else Path.home() / ".leetsolv"
    questions_path = src / "questions.json"
    deltas_path = src / "deltas.json"

    if not questions_path.exists():
        print(f"error: {questions_path} not found", file=sys.stderr)
        return 1

    questions_obj = json.loads(questions_path.read_text(encoding="utf-8"))
    deltas_obj = json.loads(deltas_path.read_text(encoding="utf-8")) if deltas_path.exists() else []

    init_db()
    with SessionLocal() as session:
        summary = QuestionService(session).import_leetsolv(questions_obj, deltas_obj)

    print(
        f"imported {summary['imported']} question(s), skipped {summary['skipped']}, "
        f"wrote {summary['deltas']} history row(s), enriched {summary['enriched']} row(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
