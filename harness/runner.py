"""Orchestration stub — Phase 3 will implement warm-up, iterations, mixed load."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adapters.base import GraphAdapter


def run_platform(adapter: GraphAdapter) -> dict:
    """Placeholder return shape matching the results JSON schema."""
    return {
        "platform": adapter.name,
        "status": "not_implemented",
        "note": "Phase 3 will run warm-up, workloads, and emit percentiles here.",
        "metrics": {},
    }