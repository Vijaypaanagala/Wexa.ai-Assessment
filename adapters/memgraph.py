"""Memgraph — Bolt/Cypher via official neo4j driver."""

from __future__ import annotations

from typing import Any

from adapters.base import GraphAdapter
from adapters.bolt_common import bolt_smoke_return_1, close_bolt_driver, open_bolt_driver
from adapters.cypher_bolt import CypherBoltWorkloads
from adapters.errors import AdapterConnectionError
from harness.config import memgraph_config


class MemgraphAdapter(CypherBoltWorkloads, GraphAdapter):
    name = "memgraph"
    index_dialect = "memgraph"

    def __init__(self) -> None:
        self.cfg = memgraph_config()
        self._driver = None

    def connect(self) -> None:
        if self._driver is not None:
            return
        self._driver = open_bolt_driver(
            platform=self.name,
            uri=self.cfg.uri,
            user=self.cfg.user,
            password=self.cfg.password,
            require_password=False,
        )

    def close(self) -> None:
        close_bolt_driver(self._driver)
        self._driver = None

    def ping(self) -> bool:
        if self._driver is None:
            raise AdapterConnectionError(self.name, "Not connected; call connect() first")
        return bolt_smoke_return_1(self._driver, platform=self.name)

    def footprint(self) -> dict[str, Any]:
        return {
            "instance": "Docker (docker-compose.yml)",
            "vCPU": 0.5,
            "RAM": "256 MB (mem_limit target)",
            "source": "https://memgraph.com/docs/client-libraries/python",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
        }

    def load_method(self) -> str:
        return "official Neo4j Python driver UNWIND batching over Bolt"
