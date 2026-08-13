"""Neo4j Aura Free stub — Phase 4."""

from __future__ import annotations

from typing import Any, Sequence

from adapters.base import GraphAdapter
from harness.config import neo4j_aura_config


class Neo4jAuraAdapter(GraphAdapter):
    name = "neo4j_aura"

    def __init__(self) -> None:
        self.cfg = neo4j_aura_config()
        self._driver = None

    def connect(self) -> None:
        raise NotImplementedError("Phase 4: Neo4j Aura adapter")

    def close(self) -> None:
        self._driver = None

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
            "instance": "AuraDB Free",
            "vCPU": "shared",
            "RAM": "shared",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
        }

    def load_method(self) -> str:
        return "official Neo4j Python driver UNWIND batching over Bolt"
