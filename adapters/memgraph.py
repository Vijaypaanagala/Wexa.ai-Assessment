"""Memgraph — Cypher/Bolt, Docker-capped to CognoDB free-tier resources."""

from __future__ import annotations

from typing import Any, Sequence

from adapters.base import GraphAdapter
from harness.config import memgraph_config


class MemgraphAdapter(GraphAdapter):
    name = "memgraph"

    def __init__(self) -> None:
        self.cfg = memgraph_config()
        self._driver = None

    def connect(self) -> None:
        raise NotImplementedError("Phase 4: neo4j driver → bolt://localhost:7687")

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def ping(self) -> bool:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError

    def create_schema(self) -> None:
        raise NotImplementedError

    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        raise NotImplementedError

    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        raise NotImplementedError

    def hop(self, start_id: int, depth: int) -> int:
        raise NotImplementedError

    def point_lookup(self, node_id: int) -> Any:
        raise NotImplementedError

    def filtered_lookup(self, lo: int, hi: int) -> int:
        raise NotImplementedError

    def aggregation(self) -> int:
        raise NotImplementedError

    def mixed_read(self, node_id: int) -> Any:
        raise NotImplementedError

    def mixed_write(self, src_id: int, dst_id: int) -> None:
        raise NotImplementedError

    def footprint(self) -> dict[str, Any]:
        return {
            "instance": "Docker (docker-compose.yml)",
            "vCPU": 0.5,
            "RAM": "256 MB (mem_limit)",
            "disk": "host-limited; sized for <1 GB dataset",
            "stored_data_size": "not observable (Phase 6)",
            "memory_usage": "not observable (Phase 6)",
            "fairness_note": "Localhost RTT vs cloud — disclosed in methodology.",
        }

    def load_method(self) -> str:
        return "official Neo4j Python driver UNWIND batching over Bolt"