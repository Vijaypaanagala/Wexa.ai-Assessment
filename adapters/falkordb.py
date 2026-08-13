"""FalkorDB stub — Phase 4."""

from __future__ import annotations

from typing import Any, Sequence

from adapters.base import GraphAdapter
from harness.config import falkordb_config


class FalkorDBAdapter(GraphAdapter):
    name = "falkordb"

    def __init__(self) -> None:
        self.cfg = falkordb_config()
        self._client = None

    def connect(self) -> None:
        raise NotImplementedError("Phase 4: FalkorDB adapter")

    def close(self) -> None:
        self._client = None

    def reset(self) -> None:
        raise NotImplementedError

    def create_schema(self) -> None:
        raise NotImplementedError

    def create_indexes(self) -> None:
        raise NotImplementedError

    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        raise NotImplementedError

    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        raise NotImplementedError

    def query_1hop(self, start_id: int) -> int:
        raise NotImplementedError

    def query_2hop(self, start_id: int) -> int:
        raise NotImplementedError

    def query_3hop(self, start_id: int) -> int:
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
            "instance": "Docker (resource-capped)",
            "vCPU": 0.5,
            "RAM": "256 MB",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
        }

    def load_method(self) -> str:
        return "FalkorDB Cypher GRAPH.QUERY batched inserts"
