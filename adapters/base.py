"""Common adapter interface for all graph platforms.

Phase 3 defines the contract. Phase 4 implements connect()/close()/ping() for
each platform. Loaders and query methods arrive in Phase 5/6.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class GraphAdapter(ABC):
    """Every platform implements the same logical operations."""

    name: str

    @abstractmethod
    def connect(self) -> None:
        """Open a client/session to the database."""

    @abstractmethod
    def close(self) -> None:
        """Close the client/session and release resources."""

    @abstractmethod
    def reset(self) -> None:
        """Drop benchmark graph data so loads are comparable."""

    @abstractmethod
    def create_schema(self) -> None:
        """Create labels/collections/edge definitions (no indexes)."""

    @abstractmethod
    def create_indexes(self) -> None:
        """Create indexes required by point/filtered lookups."""

    @abstractmethod
    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        """Insert nodes; return count inserted."""

    @abstractmethod
    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        """Insert relationships; return count inserted."""

    @abstractmethod
    def query_1hop(self, start_id: int) -> int:
        """Count neighbors exactly 1 hop from start_id via FOLLOWS."""

    @abstractmethod
    def query_2hop(self, start_id: int) -> int:
        """Count nodes reachable in exactly 2 hops via FOLLOWS."""

    @abstractmethod
    def query_3hop(self, start_id: int) -> int:
        """Count nodes reachable in exactly 3 hops via FOLLOWS."""

    @abstractmethod
    def point_lookup(self, node_id: int) -> Any:
        """Fetch a single node by id property."""

    @abstractmethod
    def filtered_lookup(self, lo: int, hi: int) -> int:
        """Count nodes with id in [lo, hi)."""

    @abstractmethod
    def aggregation(self) -> int:
        """Count relationships of the benchmark type (or equivalent)."""

    @abstractmethod
    def mixed_read(self, node_id: int) -> Any:
        """Read half of the mixed workload (point lookup semantics)."""

    @abstractmethod
    def mixed_write(self, src_id: int, dst_id: int) -> None:
        """Write half of the mixed workload (must be safe to repeat)."""

    def ping(self) -> bool:
        """Optional connectivity check; override in Phase 4 adapters."""
        raise NotImplementedError

    def footprint(self) -> dict[str, Any]:
        """Observable resource usage; override in adapters."""
        return {"stored_data_size": "not observable", "memory_usage": "not observable"}

    def indexed_properties(self) -> list[str]:
        """Properties that have indexes for filtered/point lookups."""
        return ["id"]

    def load_method(self) -> str:
        """Human-readable ingest method for the README."""
        return "driver batching"