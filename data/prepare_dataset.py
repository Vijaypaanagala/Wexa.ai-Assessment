#!/usr/bin/env python3
"""
Prepare a seeded SNAP soc-Pokec subsample for the benchmark.

Downloads the official relationship edge list, reservoir-samples a fixed number
of directed edges with a deterministic RNG seed, writes CSV artifacts, and emits
manifest.json with source metadata, counts, seed, and SHA-256 checksums.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import random
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PREPARED_DIR = ROOT / "data" / "prepared"

SOURCE_NAME = "SNAP soc-Pokec social network"
SOURCE_PAGE = "https://snap.stanford.edu/data/soc-Pokec.html"
SOURCE_FILE_URL = "https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz"
SOURCE_FILE_NAME = "soc-pokec-relationships.txt.gz"
SOURCE_CITATION = (
    "L. Takac, M. Zabovsky. Data Analysis in Public Social Networks, "
    "International Scientific Conference & International Workshop Present Day "
    "Trends of Innovations, May 2012 Lomza, Poland."
)
FULL_GRAPH_NODES = 1_632_803
FULL_GRAPH_EDGES = 30_622_564

DEFAULT_SEED = 42
DEFAULT_TARGET_RELS = 250_000
MIN_RELS = 100_000


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def download_source(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"Using cached download: {dest} ({dest.stat().st_size:,} bytes)")
        return
    print(f"Downloading {url}")
    print(f"  -> {dest}")
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        with urllib.request.urlopen(url, timeout=120) as resp, tmp.open("wb") as out:
            total = 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                total += len(chunk)
                if total % (20 * 1024 * 1024) < 1024 * 1024:
                    print(f"  ... {total / (1024 * 1024):.1f} MiB", flush=True)
        tmp.replace(dest)
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise
    print(f"Download complete: {dest.stat().st_size:,} bytes")


def iter_edges(gz_path: Path):
    """Yield (src, dst) int pairs from SNAP edge list (skip comments)."""
    with gzip.open(gz_path, "rt", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                src = int(parts[0])
                dst = int(parts[1])
            except ValueError as exc:
                raise ValueError(f"Bad edge at line {line_no}: {line!r}") from exc
            yield src, dst


def reservoir_sample_edges(
    gz_path: Path,
    k: int,
    seed: int,
) -> tuple[list[tuple[int, int]], int]:
    """
    Deterministic reservoir sample of k directed edges.

    Algorithm: Algorithm R (Vitter) with random.Random(seed).
    Returns (sampled_edges, edges_seen_in_source).
    """
    if k < MIN_RELS:
        raise ValueError(f"target relationships must be >= {MIN_RELS}, got {k}")

    rng = random.Random(seed)
    reservoir: list[tuple[int, int]] = []
    seen = 0

    print(f"Reservoir-sampling {k:,} edges (seed={seed}) from {gz_path.name} ...")
    for edge in iter_edges(gz_path):
        seen += 1
        if len(reservoir) < k:
            reservoir.append(edge)
        else:
            j = rng.randrange(seen)
            if j < k:
                reservoir[j] = edge
        if seen % 5_000_000 == 0:
            print(f"  scanned {seen:,} edges ...", flush=True)

    if seen < k:
        raise RuntimeError(
            f"Source only has {seen:,} edges; cannot sample {k:,}. "
            "Check the download."
        )

    # Stable order for reproducible CSV bytes: sort by (src, dst)
    reservoir.sort(key=lambda e: (e[0], e[1]))
    print(f"Scanned {seen:,} source edges; kept {len(reservoir):,} sampled edges.")
    return reservoir, seen


def write_csvs(
    edges: list[tuple[int, int]],
    nodes_path: Path,
    rels_path: Path,
) -> tuple[int, int]:
    node_ids = sorted({n for e in edges for n in e})
    nodes_path.parent.mkdir(parents=True, exist_ok=True)

    with nodes_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id"])
        for nid in node_ids:
            w.writerow([nid])

    with rels_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["start_id", "end_id", "type"])
        for src, dst in edges:
            w.writerow([src, dst, "FOLLOWS"])

    return len(node_ids), len(edges)


def write_manifest(
    path: Path,
    *,
    seed: int,
    target_relationships: int,
    node_count: int,
    relationship_count: int,
    source_edges_scanned: int,
    raw_path: Path,
    nodes_path: Path,
    rels_path: Path,
    method: str,
) -> dict:
    manifest = {
        "schema_version": 1,
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "name": SOURCE_NAME,
            "page": SOURCE_PAGE,
            "file_url": SOURCE_FILE_URL,
            "file_name": SOURCE_FILE_NAME,
            "citation": SOURCE_CITATION,
            "full_graph_nodes": FULL_GRAPH_NODES,
            "full_graph_edges": FULL_GRAPH_EDGES,
            "edges_scanned": source_edges_scanned,
            "raw_sha256": sha256_file(raw_path),
            "raw_bytes": raw_path.stat().st_size,
        },
        "subsample": {
            "method": method,
            "seed": seed,
            "target_relationships": target_relationships,
            "node_count": node_count,
            "relationship_count": relationship_count,
            "node_label": "Person",
            "relationship_type": "FOLLOWS",
            "id_property": "id",
            "directed": True,
        },
        "artifacts": {
            "nodes_csv": {
                "path": str(nodes_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(nodes_path),
                "bytes": nodes_path.stat().st_size,
            },
            "relationships_csv": {
                "path": str(rels_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(rels_path),
                "bytes": rels_path.stat().st_size,
            },
        },
        "reproduce": {
            "command": (
                f"python data/prepare_dataset.py "
                f"--seed {seed} --target-relationships {target_relationships}"
            ),
            "notes": [
                "Raw SNAP dump stays in data/raw/ (gitignored).",
                "CSV row order is sorted by (start_id, end_id) after sampling "
                "so artifact checksums are stable across machines.",
                "RNG is Python random.Random(seed) with Vitter's Algorithm R.",
            ],
        },
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_minimums(relationship_count: int, node_count: int) -> None:
    if relationship_count < MIN_RELS:
        raise SystemExit(
            f"FAIL: relationship_count={relationship_count} < required {MIN_RELS}"
        )
    if node_count < 1:
        raise SystemExit("FAIL: no nodes produced")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download SNAP soc-Pokec and write a seeded subsample"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--target-relationships",
        type=int,
        default=DEFAULT_TARGET_RELS,
        help=f"Number of directed edges to sample (>= {MIN_RELS})",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Use existing data/raw/soc-pokec-relationships.txt.gz only",
    )
    args = parser.parse_args(argv)

    if args.target_relationships < MIN_RELS:
        parser.error(f"--target-relationships must be >= {MIN_RELS}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = RAW_DIR / SOURCE_FILE_NAME
    if not args.skip_download:
        download_source(SOURCE_FILE_URL, raw_path)
    elif not raw_path.exists():
        raise SystemExit(f"--skip-download set but missing {raw_path}")

    method = (
        "Vitter Algorithm R reservoir sample of directed edges from "
        "soc-pokec-relationships.txt.gz; sample then sorted by (src, dst); "
        "node set = endpoints of sampled edges."
    )
    edges, scanned = reservoir_sample_edges(
        raw_path, args.target_relationships, args.seed
    )

    nodes_path = PREPARED_DIR / "nodes.csv"
    rels_path = PREPARED_DIR / "relationships.csv"
    manifest_path = PREPARED_DIR / "manifest.json"

    node_count, rel_count = write_csvs(edges, nodes_path, rels_path)
    verify_minimums(rel_count, node_count)

    manifest = write_manifest(
        manifest_path,
        seed=args.seed,
        target_relationships=args.target_relationships,
        node_count=node_count,
        relationship_count=rel_count,
        source_edges_scanned=scanned,
        raw_path=raw_path,
        nodes_path=nodes_path,
        rels_path=rels_path,
        method=method,
    )

    print()
    print("Phase 2 complete.")
    print(f"  nodes:          {node_count:,}")
    print(f"  relationships:  {rel_count:,}")
    print(f"  seed:           {args.seed}")
    print(f"  nodes sha256:   {manifest['artifacts']['nodes_csv']['sha256']}")
    print(f"  rels sha256:    {manifest['artifacts']['relationships_csv']['sha256']}")
    print(f"  raw sha256:     {manifest['source']['raw_sha256']}")
    print(f"  manifest:       {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
