"""In-memory GraphAdapter for unit tests — not a real database."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

from adapters.base import GraphAdapter


class FakeInMemoryAdapter(GraphAdapter):
    """Tiny directed graph used only by the Phase 3 test suite."""

    name = "fake_memory"

    def __init__(self) -> None:
        self.nodes: dict[int, dict[str, Any]] = {}
        self.edges: set[tuple[int, int]] = set()
        self.out: dict[int, set[int]] = defaultdict(set)
        self.connected = False
        self.call_counts: dict[str, int] = defaultdict(int)

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def reset(self) -> None:
        self.nodes.clear()
        self.edges.clear()
        self.out.clear()

    def create_schema(self) -> None:
        return None

    def create_indexes(self) -> None:
        return None

    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        for row in rows:
            self.nodes[int(row["id"])] = dict(row)
        return len(rows)

    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        n = 0
        for row in rows:
            src, dst = int(row["start_id"]), int(row["end_id"])
            if (src, dst) not in self.edges:
                self.edges.add((src, dst))
                self.out[src].add(dst)
                n += 1
        return n

    def _neighbors_at_depth(self, start_id: int, depth: int) -> set[int]:
        frontier = {start_id}
        reached: set[int] = set()
        for _ in range(depth):
            nxt: set[int] = set()
            for node in frontier:
                nxt.update(self.out.get(node, ()))
            frontier = nxt
            reached = nxt
        return reached

    def query_1hop(self, start_id: int) -> int:
        self.call_counts["query_1hop"] += 1
        return len(self._neighbors_at_depth(start_id, 1))

    def query_2hop(self, start_id: int) -> int:
        self.call_counts["query_2hop"] += 1
        return len(self._neighbors_at_depth(start_id, 2))

    def query_3hop(self, start_id: int) -> int:
        self.call_counts["query_3hop"] += 1
        return len(self._neighbors_at_depth(start_id, 3))

    def point_lookup(self, node_id: int) -> Any:
        self.call_counts["point_lookup"] += 1
        return self.nodes.get(node_id)

    def filtered_lookup(self, lo: int, hi: int) -> int:
        self.call_counts["filtered_lookup"] += 1
        return sum(1 for nid in self.nodes if lo <= nid < hi)

    def aggregation(self) -> int:
        self.call_counts["aggregation"] += 1
        return len(self.edges)

    def mixed_read(self, node_id: int) -> Any:
        self.call_counts["mixed_read"] += 1
        return self.point_lookup(node_id)

    def mixed_write(self, src_id: int, dst_id: int) -> None:
        self.call_counts["mixed_write"] += 1
        # Idempotent upsert
        self.nodes.setdefault(src_id, {"id": src_id})
        self.nodes.setdefault(dst_id, {"id": dst_id})
        if (src_id, dst_id) not in self.edges:
            self.edges.add((src_id, dst_id))
            self.out[src_id].add(dst_id)

    def footprint(self) -> dict[str, Any]:
        return {
            "instance": "fake_memory",
            "nodes": len(self.nodes),
            "relationships": len(self.edges),
            "stored_data_size": "n/a",
            "memory_usage": "n/a",
        }


def seed_line_graph(adapter: FakeInMemoryAdapter, n: int = 50) -> list[int]:
    """Load a directed line 0->1->...->n-1 plus a few skips for multi-hop."""
    ids = list(range(n))
    adapter.load_nodes([{"id": i} for i in ids])
    rels = [{"start_id": i, "end_id": i + 1, "type": "FOLLOWS"} for i in range(n - 1)]
    for i in range(0, n - 3, 5):
        rels.append({"start_id": i, "end_id": i + 3, "type": "FOLLOWS"})
    adapter.load_relationships(rels)
    return ids
