"""Ingest helpers: timed load of Phase 2 CSVs into an adapter."""

from __future__ import annotations

import time
from typing import Any, Iterator

from adapters.base import GraphAdapter
from harness.dataset import iter_node_rows, iter_relationship_rows, load_prepared_dataset


def _take(rows: Iterator[dict[str, Any]], limit: int | None) -> Iterator[dict[str, Any]]:
    if limit is None:
        yield from rows
        return
    for i, row in enumerate(rows):
        if i >= limit:
            break
        yield row


def ingest_dataset(
    adapter: GraphAdapter,
    *,
    reset: bool = True,
    max_nodes: int | None = None,
    max_relationships: int | None = None,
) -> dict[str, Any]:
    """Load prepared dataset; return ingest metrics block."""
    ds = load_prepared_dataset(load_ids=False)
    adapter.connect()
    try:
        if reset:
            adapter.reset()
        adapter.create_schema()
        adapter.create_indexes()

        node_rows = list(_take(iter_node_rows(ds.nodes_csv), max_nodes))
        t0 = time.perf_counter()
        nodes_loaded = adapter.load_nodes(node_rows)
        node_wall = time.perf_counter() - t0

        rel_rows = list(_take(iter_relationship_rows(ds.relationships_csv), max_relationships))
        # If max_nodes set, filter edges to loaded node set
        if max_nodes is not None:
            allowed = {int(r["id"]) for r in node_rows}
            rel_rows = [
                r
                for r in rel_rows
                if int(r["start_id"]) in allowed and int(r["end_id"]) in allowed
            ]

        t1 = time.perf_counter()
        rels_loaded = adapter.load_relationships(rel_rows)
        rel_wall = time.perf_counter() - t1
        total_wall = node_wall + rel_wall

        return {
            "workload": "ingest",
            "status": "ok",
            "method": adapter.load_method(),
            "nodes_loaded": nodes_loaded,
            "relationships_loaded": rels_loaded,
            "node_wall_seconds": node_wall,
            "relationship_wall_seconds": rel_wall,
            "wall_seconds": total_wall,
            "nodes_per_sec": nodes_loaded / node_wall if node_wall > 0 else None,
            "relationships_per_sec": rels_loaded / rel_wall if rel_wall > 0 else None,
            "indexed_properties": adapter.indexed_properties(),
            "dataset": {
                "manifest_nodes": ds.node_count,
                "manifest_relationships": ds.relationship_count,
                "nodes_sha256": ds.nodes_sha256,
                "relationships_sha256": ds.relationships_sha256,
            },
        }
    finally:
        adapter.close()
