#!/usr/bin/env python3
"""Run workloads for one platform (Phase 3/6)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import ADAPTERS  # noqa: E402
from harness.config import PLATFORMS  # noqa: E402
from harness.runner import run_platform  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark one platform")
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    adapter = ADAPTERS[args.platform]()
    if args.dry_run:
        payload = {
            "platform": adapter.name,
            "status": "dry_run",
            "indexed_properties": adapter.indexed_properties(),
            "load_method": adapter.load_method(),
            "footprint": adapter.footprint(),
        }
    else:
        payload = run_platform(adapter)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
