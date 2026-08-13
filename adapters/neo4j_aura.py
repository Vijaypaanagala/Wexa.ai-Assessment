"""Neo4j Aura Free — Bolt/Cypher via official neo4j driver."""

from __future__ import annotations

from typing import Any

from adapters.base import GraphAdapter
from adapters.bolt_common import bolt_smoke_return_1, close_bolt_driver, open_bolt_driver
from adapters.cypher_bolt import CypherBoltWorkloads
from adapters.errors import AdapterConnectionError
from harness.config import neo4j_aura_config


class Neo4jAuraAdapter(CypherBoltWorkloads, GraphAdapter):
    name = "neo4j_aura"
    index_dialect = "neo4j"

    def __init__(self) -> None:
        self.cfg = neo4j_aura_config()
        self._driver = None

    def connect(self) -> None:
        if self._driver is not None:
            return
        self._driver = open_bolt_driver(
            platform=self.name,
            uri=self.cfg.uri,
            user=self.cfg.user or "neo4j",
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
            "instance": "AuraDB Free",
            "vCPU": "shared (not user-configurable)",
            "RAM": "shared (not published as fixed GB for Free)",
            "limits": "up to 200,000 nodes and 400,000 relationships",
            "source": "https://support.neo4j.com/s/article/16094506528787-Support-resources-and-FAQ-for-Aura-Free-Tier",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
            "fairness_note": (
                "Dataset has 350,480 nodes which exceeds Aura Free's 200k node cap; "
                "production re-runs must subsample to ≤200k nodes for Aura or use a paid tier."
            ),
        }

    def load_method(self) -> str:
        return "official Neo4j Python driver UNWIND batching over Bolt"
