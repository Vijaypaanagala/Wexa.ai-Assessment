#!/usr/bin/env python3
"""Phase 2 placeholder: download + seeded subsample of the public graph."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "data" / "prepared"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare benchmark dataset (Phase 2)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-relationships", type=int, default=250_000)
    args = parser.parse_args()
    PREPARED.mkdir(parents=True, exist_ok=True)
    print(
        f"[phase-2-pending] Will write nodes/relationships under {PREPARED} "
        f"(seed={args.seed}, target_rels={args.target_relationships})"
    )


if __name__ == "__main__":
    main()
