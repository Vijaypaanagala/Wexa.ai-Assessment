"""Adapter registry — concrete drivers land in Phase 4. Stubs only for now."""

from __future__ import annotations

from adapters.arangodb import ArangoDBAdapter
from adapters.base import GraphAdapter
from adapters.cognodb import CognoDBAdapter
from adapters.falkordb import FalkorDBAdapter
from adapters.memgraph import MemgraphAdapter
from adapters.neo4j_aura import Neo4jAuraAdapter

ADAPTERS: dict[str, type[GraphAdapter]] = {
    "cognodb": CognoDBAdapter,
    "neo4j_aura": Neo4jAuraAdapter,
    "memgraph": MemgraphAdapter,
    "falkordb": FalkorDBAdapter,
    "arangodb": ArangoDBAdapter,
}

__all__ = ["ADAPTERS", "GraphAdapter"]
