"""Deterministic logical workloads — identical inputs for every platform."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal, Sequence

from harness.config import BenchConfig

OpKind = Literal["read", "write"]


@dataclass(frozen=True)
class FilterRange:
    lo: int
    hi: int


@dataclass(frozen=True)
class MixedOp:
    kind: OpKind
    node_id: int
    dst_id: int | None = None


@dataclass(frozen=True)
class WorkloadPlan:
    """Fully materialised, seed-derived workload inputs."""

    seed: int
    start_nodes: tuple[int, ...]
    point_lookup_ids: tuple[int, ...]
    filter_ranges: tuple[FilterRange, ...]
    mixed_op_pool: tuple[MixedOp, ...]
    mixed_duration_seconds: float
    read_iterations: int
    warmup_iterations: int
    mixed_read_ratio: float
    mixed_concurrency: tuple[int, ...]

    # Logical query descriptions (documentation / result metadata)
    logical_queries: dict[str, str]

    def mixed_op_at(self, index: int) -> MixedOp:
        """Deterministic op stream: index i always maps to the same MixedOp."""
        if not self.mixed_op_pool:
            raise ValueError("mixed_op_pool is empty")
        return self.mixed_op_pool[index % len(self.mixed_op_pool)]

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "start_node_count": len(self.start_nodes),
            "start_nodes_preview": list(self.start_nodes[:10]),
            "point_lookup_count": len(self.point_lookup_ids),
            "filter_range_count": len(self.filter_ranges),
            "mixed_op_pool_size": len(self.mixed_op_pool),
            "mixed_duration_seconds": self.mixed_duration_seconds,
            "read_iterations": self.read_iterations,
            "warmup_iterations": self.warmup_iterations,
            "mixed_read_ratio": self.mixed_read_ratio,
            "mixed_concurrency": list(self.mixed_concurrency),
            "logical_queries": self.logical_queries,
            "determinism_note": (
                "Mixed ops are drawn from a seeded pool by sequential index; "
                "duration controls how many ops complete (platform-dependent)."
            ),
        }


LOGICAL_QUERIES = {
    "hop_1": "COUNT neighbors at depth 1 via FOLLOWS from start_id",
    "hop_2": "COUNT nodes reachable at depth 2 via FOLLOWS from start_id",
    "hop_3": "COUNT nodes reachable at depth 3 via FOLLOWS from start_id",
    "point_lookup": "FETCH Person by id",
    "filtered_lookup": "COUNT Person WHERE id >= lo AND id < hi",
    "aggregation": "COUNT all FOLLOWS relationships",
    "mixed_read": "point lookup by id",
    "mixed_write": "upsert ephemeral FOLLOWS(src,dst) (idempotent / repeatable)",
}


def _sample_unique(rng: random.Random, population: Sequence[int], k: int) -> list[int]:
    if not population:
        raise ValueError("node population is empty")
    if k > len(population):
        # Repeat cyclically after shuffle for tiny test graphs
        base = list(population)
        rng.shuffle(base)
        out: list[int] = []
        while len(out) < k:
            out.extend(base)
        return out[:k]
    return rng.sample(list(population), k)


def build_workload_plan(
    node_ids: Sequence[int],
    config: BenchConfig | None = None,
) -> WorkloadPlan:
    """Build identical workloads for every platform from node ids + seed."""
    cfg = config or BenchConfig()
    if not node_ids:
        raise ValueError("node_ids must be non-empty")

    rng = random.Random(cfg.workload_seed)
    population = sorted(set(int(x) for x in node_ids))

    start_nodes = _sample_unique(rng, population, cfg.start_node_count)
    # Point lookups: independent sample of the same size as read iterations
    point_ids = _sample_unique(rng, population, cfg.read_iterations)

    # Filter windows: deterministic ranges anchored on sampled ids
    filter_ranges: list[FilterRange] = []
    anchors = _sample_unique(rng, population, cfg.read_iterations)
    for anchor in anchors:
        lo = int(anchor)
        hi = lo + cfg.filter_width
        filter_ranges.append(FilterRange(lo=lo, hi=hi))

    # Seeded mixed-op pool; timed runs consume pool[i % len] for i = 0,1,2,...
    mixed_pool: list[MixedOp] = []
    for _ in range(cfg.mixed_op_pool_size):
        if rng.random() < cfg.mixed_read_ratio:
            nid = population[rng.randrange(len(population))]
            mixed_pool.append(MixedOp(kind="read", node_id=nid))
        else:
            src = population[rng.randrange(len(population))]
            dst = population[rng.randrange(len(population))]
            mixed_pool.append(MixedOp(kind="write", node_id=src, dst_id=dst))

    return WorkloadPlan(
        seed=cfg.workload_seed,
        start_nodes=tuple(start_nodes),
        point_lookup_ids=tuple(point_ids),
        filter_ranges=tuple(filter_ranges),
        mixed_op_pool=tuple(mixed_pool),
        mixed_duration_seconds=cfg.mixed_duration_seconds,
        read_iterations=cfg.read_iterations,
        warmup_iterations=cfg.warmup_iterations,
        mixed_read_ratio=cfg.mixed_read_ratio,
        mixed_concurrency=tuple(cfg.mixed_concurrency),
        logical_queries=dict(LOGICAL_QUERIES),
    )


# Back-compat names from Phase 1 stub
WORKLOAD_NAMES = (
    "ingest",
    "hop_1",
    "hop_2",
    "hop_3",
    "point_lookup",
    "filtered_lookup",
    "aggregation",
    "mixed",
    "footprint",
)


@dataclass(frozen=True)
class DatasetSpec:
    """Legacy metadata shape; prefer harness.dataset.PreparedDataset."""

    source_name: str
    source_url: str
    node_count: int
    relationship_count: int
    seed: int
    node_label: str = "Person"
    rel_type: str = "FOLLOWS"
    id_property: str = "id"
