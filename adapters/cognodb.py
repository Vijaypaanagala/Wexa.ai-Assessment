"""CognoDB Cloud — Bolt/Cypher via official neo4j driver."""

from __future__ import annotations

from typing import Any

from adapters.base import GraphAdapter
from adapters.bolt_common import bolt_smoke_return_1, close_bolt_driver, open_bolt_driver
from adapters.cypher_bolt import CypherBoltWorkloads
from adapters.errors import AdapterConnectionError
from harness.config import cognodb_config


class CognoDBAdapter(CypherBoltWorkloads, GraphAdapter):
    name = "cognodb"
    index_dialect = "neo4j"

    def __init__(self) -> None:
        self.cfg = cognodb_config()
        self._driver = None

    def connect(self) -> None:
        if self._driver is not None:
            return
        self._driver = open_bolt_driver(
            platform=self.name,
            uri=self.cfg.uri,
            user=self.cfg.user or "cognodb",
            password=self.cfg.password,
            require_password=True,
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
            "instance": "c0 free tier",
            "vCPU": 0.5,
            "RAM": "256 MB",
            "disk": "1 GB",
            "connections": 200,
            "source": "https://cognodb.com/",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
        }

    def load_method(self) -> str:
        return "official Neo4j Python driver UNWIND batching over Bolt"
