#!/usr/bin/env python3
"""Load identical dataset into one platform (Phase 5)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import ADAPTERS  # noqa: E402
from harness.config import PLATFORMS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Load benchmark dataset into a platform")
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    args = parser.parse_args()
    adapter_cls = ADAPTERS[args.platform]
    print(f"[phase-5-pending] load via {adapter_cls.name} ({adapter_cls})")


if __name__ == "__main__":
    main()
