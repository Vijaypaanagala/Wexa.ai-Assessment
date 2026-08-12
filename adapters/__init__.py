"""Adapter registry — concrete drivers land in Phase 4/5."""

from __future__ import annotations

from adapters.base import GraphAdapter
from adapters.cognodb import CognoDBAdapter
from adapters.neo4j_aura import Neo4jAuraAdapter
from adapters.memgraph import MemgraphAdapter
from adapters.falkordb import FalkorDBAdapter
from adapters.arangodb import ArangoDBAdapter

ADAPTERS: dict[str, type[GraphAdapter]] = {
    "cognodb": CognoDBAdapter,
    "neo4j_aura": Neo4jAuraAdapter,
    "memgraph": MemgraphAdapter,
    "falkordb": FalkorDBAdapter,
    "arangodb": ArangoDBAdapter,
}

__all__ = ["ADAPTERS", "GraphAdapter"]