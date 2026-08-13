#!/usr/bin/env python3
"""Run workloads for one platform via the Phase 3 harness.

Real adapters are Phase 4. Use --dry-run for stub metadata, or tests/fakes
for local harness validation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import ADAPTERS  # noqa: E402
from harness.config import (  # noqa: E402
    DEFAULT_MIXED_CONCURRENCY,
    DEFAULT_MIXED_READ_RATIO,
    DEFAULT_READ_ITERATIONS,
    DEFAULT_WARMUP_ITERATIONS,
    PLATFORMS,
    BenchConfig,
)
from harness.results import default_result_path, write_result_json  # noqa: E402
from harness.runner import BenchmarkRunner  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark one platform (Phase 3 harness)")
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Print stub metadata only")
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP_ITERATIONS)
    parser.add_argument("--iterations", type=int, default=DEFAULT_READ_ITERATIONS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--mixed-duration",
        type=float,
        default=30.0,
        help="Mixed workload duration in seconds (default: 30)",
    )
    parser.add_argument("--read-ratio", type=float, default=DEFAULT_MIXED_READ_RATIO)
    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=list(DEFAULT_MIXED_CONCURRENCY),
        help="Mixed-workload concurrency levels (default: 1 10 40)",
    )
    parser.add_argument(
        "--write-result",
        action="store_true",
        help="Write JSON under results/runs/ (requires working Phase 4 adapter)",
    )
    args = parser.parse_args()

    adapter = ADAPTERS[args.platform]()
    if args.dry_run:
        payload = {
            "platform": adapter.name,
            "status": "dry_run",
            "phase": 3,
            "note": (
                "Phase 3 harness is ready. Platform adapters are Phase 4; "
                "no database connection attempted."
            ),
            "indexed_properties": adapter.indexed_properties(),
            "load_method": adapter.load_method(),
            "footprint": adapter.footprint(),
            "harness_defaults": {
                "warmup_iterations": args.warmup,
                "read_iterations": args.iterations,
                "workload_seed": args.seed,
                "mixed_concurrency": args.concurrency,
                "mixed_read_ratio": args.read_ratio,
                "mixed_duration_seconds": args.mixed_duration,
            },
        }
        print(json.dumps(payload, indent=2))
        return

    cfg = BenchConfig(
        workload_seed=args.seed,
        warmup_iterations=args.warmup,
        read_iterations=args.iterations,
        mixed_concurrency=tuple(args.concurrency),
        mixed_read_ratio=args.read_ratio,
        mixed_duration_seconds=args.mixed_duration,
    )
    try:
        doc = BenchmarkRunner(adapter, cfg).run(connect=True)
    except NotImplementedError as exc:
        print(
            json.dumps(
                {
                    "platform": adapter.name,
                    "status": "adapter_not_implemented",
                    "phase": 3,
                    "error": str(exc),
                    "note": "Implement Phase 4 adapters before timed runs.",
                },
                indent=2,
            )
        )
        sys.exit(2)

    if args.write_result:
        path = write_result_json(doc, default_result_path(adapter.name))
        doc["result_path"] = str(path)
    print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
