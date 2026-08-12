#!/usr/bin/env python3
"""Generate charts from results JSON (Phase 7)."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot benchmark results")
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("results/runs"),
        help="Directory of per-platform JSON result files",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("charts/out"),
        help="Output directory for PNG charts",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"[phase-7-pending] Will plot from {args.results} → {args.out}")


if __name__ == "__main__":
    main()
