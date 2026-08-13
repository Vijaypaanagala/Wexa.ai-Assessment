#!/usr/bin/env python3
"""Orchestrate load + bench across platforms, or rebuild published artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import ADAPTERS  # noqa: E402
from harness.config import PLATFORMS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full benchmark suite or rebuild artifacts")
    parser.add_argument("--platform", choices=(*PLATFORMS, "all"), default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--publish-only",
        action="store_true",
        help="Rebuild results/published + charts without connecting to databases",
    )
    parser.add_argument("--skip-load", action="store_true")
    parser.add_argument("--skip-bench", action="store_true")
    args = parser.parse_args()

    if args.publish_only:
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_results.py")])
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "aggregate_results.py")])
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "plot_results.py")])
        print("Published results + charts refreshed.")
        return 0

    targets = PLATFORMS if args.platform == "all" else (args.platform,)
    if args.dry_run:
        summary = []
        for name in targets:
            adapter = ADAPTERS[name]()
            summary.append(
                {
                    "platform": name,
                    "status": "dry_run",
                    "load_method": adapter.load_method(),
                    "footprint": adapter.footprint(),
                }
            )
        print(json.dumps(summary, indent=2))
        return 0

    for name in targets:
        if not args.skip_load:
            rc = subprocess.call(
                [sys.executable, str(ROOT / "scripts" / "load.py"), "--platform", name]
            )
            if rc != 0:
                print(f"load failed for {name}", file=sys.stderr)
                return rc
        if not args.skip_bench:
            rc = subprocess.call(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "bench.py"),
                    "--platform",
                    name,
                    "--write-result",
                ]
            )
            if rc != 0:
                print(f"bench failed for {name}", file=sys.stderr)
                return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
