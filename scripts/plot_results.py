#!/usr/bin/env python3
"""Plot charts from results/published/*.json into charts/."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "results" / "published"
DEFAULT_OUT = ROOT / "charts"


def _load_docs(results_dir: Path) -> list[dict]:
    skip = {"index.json", "matrix.json"}
    docs = []
    for path in sorted(results_dir.glob("*.json")):
        if path.name in skip:
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "platform" not in doc or "workloads" not in doc:
            continue
        docs.append(doc)
    return docs


def plot_all(results_dir: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = _load_docs(results_dir)
    if not docs:
        raise SystemExit(f"No result JSON files in {results_dir}")

    platforms = [d["platform"] for d in docs]
    written: list[Path] = []

    # 1) Ingest throughput
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(platforms))
    nodes = [d["workloads"]["ingest"]["nodes_per_sec"] for d in docs]
    rels = [d["workloads"]["ingest"]["relationships_per_sec"] for d in docs]
    w = 0.35
    ax.bar(x - w / 2, nodes, w, label="nodes/s")
    ax.bar(x + w / 2, rels, w, label="relationships/s")
    ax.set_xticks(x)
    ax.set_xticklabels(platforms, rotation=20, ha="right")
    ax.set_ylabel("Throughput")
    ax.set_title("Ingest throughput")
    ax.legend()
    fig.tight_layout()
    p = out_dir / "ingest_throughput.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    written.append(p)

    # 2) Hop latency p50
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for hop in (1, 2, 3):
        vals = [d["workloads"][f"hop_{hop}"]["latency"]["p50_ms"] for d in docs]
        ax.plot(platforms, vals, marker="o", label=f"{hop}-hop p50")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Traversal latency (p50)")
    ax.legend()
    fig.tight_layout()
    p = out_dir / "hop_latency_p50.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    written.append(p)

    # 3) Hop p95 grouped
    fig, ax = plt.subplots(figsize=(9, 4.5))
    width = 0.25
    for i, hop in enumerate((1, 2, 3)):
        vals = [d["workloads"][f"hop_{hop}"]["latency"]["p95_ms"] for d in docs]
        ax.bar(x + (i - 1) * width, vals, width, label=f"{hop}-hop p95")
    ax.set_xticks(x)
    ax.set_xticklabels(platforms, rotation=20, ha="right")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Traversal latency (p95)")
    ax.legend()
    fig.tight_layout()
    p = out_dir / "hop_latency_p95.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    written.append(p)

    # 4) Lookups + aggregation p50
    fig, ax = plt.subplots(figsize=(9, 4.5))
    metrics = [
        ("point_lookup", "point"),
        ("filtered_lookup", "filtered"),
        ("aggregation", "agg"),
    ]
    width = 0.25
    for i, (key, label) in enumerate(metrics):
        vals = [d["workloads"][key]["latency"]["p50_ms"] for d in docs]
        ax.bar(x + (i - 1) * width, vals, width, label=f"{label} p50")
    ax.set_xticks(x)
    ax.set_xticklabels(platforms, rotation=20, ha="right")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Lookup & aggregation latency (p50)")
    ax.legend()
    fig.tight_layout()
    p = out_dir / "lookup_agg_p50.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    written.append(p)

    # 5) Mixed QPS vs concurrency
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for d in docs:
        conc = d["workloads"]["mixed"]["concurrency"]
        xs = [int(k) for k in conc.keys()]
        ys = [conc[str(k)]["qps"] for k in xs]
        ax.plot(xs, ys, marker="o", label=d["platform"])
    ax.set_xlabel("Concurrency")
    ax.set_ylabel("QPS")
    ax.set_title("Mixed workload sustained QPS (80/20 R/W, 30s)")
    ax.set_xticks([1, 10, 40])
    ax.legend()
    fig.tight_layout()
    p = out_dir / "mixed_qps.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    written.append(p)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot benchmark results")
    parser.add_argument("--results", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    paths = plot_all(args.results, args.out)
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
