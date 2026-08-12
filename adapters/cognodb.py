"""CognoDB Cloud — Neo4j Bolt/Cypher compatible (official neo4j driver)."""

from __future__ import annotations

from typing import Any, Sequence

from adapters.base import GraphAdapter
from harness.config import cognodb_config


class CognoDBAdapter(GraphAdapter):
    name = "cognodb"

    def __init__(self) -> None:
        self.cfg = cognodb_config()
        self._driver = None

    def connect(self) -> None:
        raise NotImplementedError("Phase 4: connect via neo4j.GraphDatabase.driver(bolt+s://...)")

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
            "instance": "c0 free tier",
            "vCPU": 0.5,
            "RAM": "256 MB",
            "disk": "1 GB",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
        }

    def load_method(self) -> str:
        return "official Neo4j Python driver UNWIND batching over Bolt"