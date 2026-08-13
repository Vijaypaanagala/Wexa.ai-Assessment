#!/usr/bin/env python3
"""Aggregate published (or runs/) result JSON into summary CSV + matrix JSON."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_docs(directory: Path) -> list[dict]:
    docs = []
    for path in sorted(directory.glob("*.json")):
        if path.name in {"index.json", "matrix.json"}:
            continue
        docs.append(json.loads(path.read_text(encoding="utf-8")))
    return docs


def to_matrix(docs: list[dict]) -> dict:
    rows = {}
    for d in docs:
        wl = d["workloads"]
        rows[d["platform"]] = {
            "ingest": {
                "nodes_per_sec": wl["ingest"]["nodes_per_sec"],
                "relationships_per_sec": wl["ingest"]["relationships_per_sec"],
                "wall_seconds": wl["ingest"]["wall_seconds"],
                "method": wl["ingest"].get("method"),
            },
            "traversals_ms": {
                hop: {
                    "p50": wl[hop]["latency"]["p50_ms"],
                    "p95": wl[hop]["latency"]["p95_ms"],
                    "p99": wl[hop]["latency"]["p99_ms"],
                }
                for hop in ("hop_1", "hop_2", "hop_3")
            },
            "lookups_ms": {
                "point": {
                    "p50": wl["point_lookup"]["latency"]["p50_ms"],
                    "p95": wl["point_lookup"]["latency"]["p95_ms"],
                },
                "filtered": {
                    "p50": wl["filtered_lookup"]["latency"]["p50_ms"],
                    "p95": wl["filtered_lookup"]["latency"]["p95_ms"],
                },
                "indexed_properties": wl["ingest"].get("indexed_properties", ["id"]),
            },
            "aggregation_ms": {
                "p50": wl["aggregation"]["latency"]["p50_ms"],
                "p95": wl["aggregation"]["latency"]["p95_ms"],
            },
            "mixed_qps": {
                k: v["qps"] for k, v in wl["mixed"]["concurrency"].items()
            },
            "footprint": d.get("footprint", {}),
            "caveats": d.get("caveats", []),
        }
    return {"schema_version": 1, "platforms": rows}


def write_csv(docs: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "platform",
                "nodes_per_sec",
                "rels_per_sec",
                "ingest_wall_s",
                "hop1_p50",
                "hop1_p95",
                "hop1_p99",
                "hop2_p50",
                "hop2_p95",
                "hop2_p99",
                "hop3_p50",
                "hop3_p95",
                "hop3_p99",
                "point_p50",
                "point_p95",
                "filter_p50",
                "filter_p95",
                "agg_p50",
                "agg_p95",
                "mixed_qps_1",
                "mixed_qps_10",
                "mixed_qps_40",
            ]
        )
        for d in docs:
            wl = d["workloads"]
            w.writerow(
                [
                    d["platform"],
                    wl["ingest"]["nodes_per_sec"],
                    wl["ingest"]["relationships_per_sec"],
                    wl["ingest"]["wall_seconds"],
                    wl["hop_1"]["latency"]["p50_ms"],
                    wl["hop_1"]["latency"]["p95_ms"],
                    wl["hop_1"]["latency"]["p99_ms"],
                    wl["hop_2"]["latency"]["p50_ms"],
                    wl["hop_2"]["latency"]["p95_ms"],
                    wl["hop_2"]["latency"]["p99_ms"],
                    wl["hop_3"]["latency"]["p50_ms"],
                    wl["hop_3"]["latency"]["p95_ms"],
                    wl["hop_3"]["latency"]["p99_ms"],
                    wl["point_lookup"]["latency"]["p50_ms"],
                    wl["point_lookup"]["latency"]["p95_ms"],
                    wl["filtered_lookup"]["latency"]["p50_ms"],
                    wl["filtered_lookup"]["latency"]["p95_ms"],
                    wl["aggregation"]["latency"]["p50_ms"],
                    wl["aggregation"]["latency"]["p95_ms"],
                    wl["mixed"]["concurrency"]["1"]["qps"],
                    wl["mixed"]["concurrency"]["10"]["qps"],
                    wl["mixed"]["concurrency"]["40"]["qps"],
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate result JSON files")
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "results" / "published",
        help="Directory of per-platform JSON",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "results" / "published" / "summary.csv",
    )
    parser.add_argument(
        "--out-matrix",
        type=Path,
        default=ROOT / "results" / "published" / "matrix.json",
    )
    args = parser.parse_args()
    docs = load_docs(args.results)
    if not docs:
        raise SystemExit(f"No results in {args.results}")
    write_csv(docs, args.out_csv)
    matrix = to_matrix(docs)
    args.out_matrix.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    print(f"platforms={len(docs)} csv={args.out_csv} matrix={args.out_matrix}")


if __name__ == "__main__":
    main()
