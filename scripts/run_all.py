#!/usr/bin/env python3
"""Orchestrate load + bench across platforms (Phase 6/7)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import ADAPTERS  # noqa: E402
from harness.config import PLATFORMS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full benchmark suite")
    parser.add_argument(
        "--platform",
        choices=(*PLATFORMS, "all"),
        default="all",
        help="Single platform or all",
    )
    parser.add_argument("--dry-run", action="store_true", help="Phase 1 smoke: no DB I/O")
    args = parser.parse_args()

    targets = PLATFORMS if args.platform == "all" else (args.platform,)
    summary = []
    for name in targets:
        adapter = ADAPTERS[name]()
        entry = {
            "platform": name,
            "status": "dry_run" if args.dry_run else "not_implemented",
            "load_method": adapter.load_method(),
            "footprint": adapter.footprint(),
        }
        summary.append(entry)
        print(json.dumps(entry, indent=2))

    out = ROOT / "results" / "runs" / "phase1_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
