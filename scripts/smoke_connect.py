#!/usr/bin/env python3
"""Phase 4 connectivity smoke tests — RETURN 1 (or AQL equivalent) only.

Never prints secrets. Exit code 0 only if every selected platform passes.
"""

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


def smoke_one(name: str) -> dict:
    adapter_cls = ADAPTERS[name]
    adapter = adapter_cls()
    result: dict = {"platform": name, "status": "unknown", "smoke": "RETURN 1"}
    try:
        adapter.connect()
        ok = adapter.ping()
        result["status"] = "ok" if ok else "fail"
        result["ping"] = bool(ok)
    except AdapterConnectionError as exc:
        result["status"] = "error"
        result["error"] = str(exc)
    except NotImplementedError as exc:
        result["status"] = "not_implemented"
        result["error"] = str(exc)
    except Exception as exc:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            adapter.close()
        except Exception:  # noqa: BLE001
            pass
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test platform connectivity")
    parser.add_argument(
        "--platform",
        choices=(*PLATFORMS, "all"),
        default="all",
    )
    args = parser.parse_args()
    targets = PLATFORMS if args.platform == "all" else (args.platform,)

    rows = [smoke_one(name) for name in targets]
    print(json.dumps({"phase": 4, "results": rows}, indent=2))

    ok = all(r["status"] == "ok" for r in rows)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
