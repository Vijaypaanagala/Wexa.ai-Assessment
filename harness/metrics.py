"""Latency / throughput helpers. Percentiles are the reporting contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass
class LatencyStats:
    samples_ms: list[float]
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    n: int

    def to_dict(self) -> dict:
        d = asdict(self)
        # Keep raw samples optional for large runs; README uses percentiles.
        d.pop("samples_ms", None)
        return d


@dataclass
class ThroughputStats:
    operations: int
    wall_seconds: float
    ops_per_second: float

    def to_dict(self) -> dict:
        return asdict(self)


def percentiles_ms(samples_ms: Sequence[float]) -> LatencyStats:
    arr = np.asarray(samples_ms, dtype=float)
    if arr.size == 0:
        raise ValueError("no latency samples")
    return LatencyStats(
        samples_ms=list(arr),
        p50_ms=float(np.percentile(arr, 50)),
        p95_ms=float(np.percentile(arr, 95)),
        p99_ms=float(np.percentile(arr, 99)),
        mean_ms=float(arr.mean()),
        n=int(arr.size),
    )


def throughput(operations: int, wall_seconds: float) -> ThroughputStats:
    if wall_seconds <= 0:
        raise ValueError("wall_seconds must be > 0")
    return ThroughputStats(
        operations=operations,
        wall_seconds=wall_seconds,
        ops_per_second=operations / wall_seconds,
    )


def summarize_latencies(batches: Iterable[Sequence[float]]) -> LatencyStats:
    flat: list[float] = []
    for batch in batches:
        flat.extend(batch)
    return percentiles_ms(flat)