"""Common adapter interface for all graph platforms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class GraphAdapter(ABC):
    """Every platform implements the same logical operations."""

    name: str

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def ping(self) -> bool:
        """Return True if a trivial round-trip succeeds."""

    @abstractmethod
    def reset(self) -> None:
        """Drop benchmark graph data so loads are comparable."""

    @abstractmethod
    def create_schema(self) -> None:
        """Labels/collections + indexes required by workloads."""

    @abstractmethod
    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        """Insert nodes; return count inserted."""

    @abstractmethod
    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        """Insert relationships; return count inserted."""

    @abstractmethod
    def hop(self, start_id: int, depth: int) -> int:
        """Return neighbor count at exactly `depth` hops (1, 2, or 3)."""

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
        """Read half of the mixed workload."""

    @abstractmethod
    def mixed_write(self, src_id: int, dst_id: int) -> None:
        """Write half of the mixed workload (must be safe to repeat)."""

    @abstractmethod
    def footprint(self) -> dict[str, Any]:
        """Observable resource usage; use 'not observable' where unknown."""

    def indexed_properties(self) -> list[str]:
        """Properties that have indexes for filtered/point lookups."""
        return ["id"]

    def load_method(self) -> str:
        """Human-readable ingest method for the README."""
        return "driver batching"