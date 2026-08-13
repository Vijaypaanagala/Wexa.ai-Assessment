#!/usr/bin/env python3
"""Load the prepared Pokec subsample into one platform and print ingest metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import ADAPTERS  # noqa: E402
from adapters.errors import AdapterConnectionError  # noqa: E402
from harness.config import PLATFORMS  # noqa: E402
from harness.ingest import ingest_dataset  # noqa: E402
from harness.results import write_result_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Load benchmark dataset into a platform")
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    parser.add_argument("--no-reset", action="store_true")
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=None,
        help="Optional cap (e.g. 200000 for Aura Free node limit)",
    )
    parser.add_argument("--max-relationships", type=int, default=None)
    parser.add_argument("--write-json", type=Path, default=None)
    args = parser.parse_args()

    adapter = ADAPTERS[args.platform]()
    try:
        metrics = ingest_dataset(
            adapter,
            reset=not args.no_reset,
            max_nodes=args.max_nodes,
            max_relationships=args.max_relationships,
        )
    except AdapterConnectionError as exc:
        print(json.dumps({"platform": args.platform, "status": "error", "error": str(exc)}, indent=2))
        return 1
    except NotImplementedError as exc:
        print(
            json.dumps(
                {"platform": args.platform, "status": "not_implemented", "error": str(exc)},
                indent=2,
            )
        )
        return 2

    doc = {"platform": args.platform, "status": "ok", "ingest": metrics}
    if args.write_json:
        write_result_json(doc, args.write_json)
        doc["result_path"] = str(args.write_json)
    print(json.dumps(doc, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
