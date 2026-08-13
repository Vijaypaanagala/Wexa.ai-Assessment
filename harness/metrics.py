"""Latency / throughput helpers. Percentiles are the reporting contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class LatencyStats:
    n: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    samples_ms: tuple[float, ...] = ()

    def to_dict(self, *, include_samples: bool = False) -> dict:
        d = {
            "n": self.n,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "mean_ms": self.mean_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
        }
        if include_samples:
            d["samples_ms"] = list(self.samples_ms)
        return d


@dataclass(frozen=True)
class ThroughputStats:
    operations: int
    wall_seconds: float
    ops_per_second: float

    def to_dict(self) -> dict:
        return asdict(self)


def percentiles_ms(
    samples_ms: Sequence[float],
    *,
    keep_samples: bool = False,
) -> LatencyStats:
    """Compute latency statistics from millisecond samples.

    Uses numpy's default linear percentile interpolation so results are stable
    across platforms for the same sample vector.
    """
    arr = np.asarray(samples_ms, dtype=float)
    if arr.size == 0:
        raise ValueError("no latency samples")
    samples_tuple = tuple(float(x) for x in arr) if keep_samples else ()
    return LatencyStats(
        n=int(arr.size),
        p50_ms=float(np.percentile(arr, 50)),
        p95_ms=float(np.percentile(arr, 95)),
        p99_ms=float(np.percentile(arr, 99)),
        mean_ms=float(arr.mean()),
        min_ms=float(arr.min()),
        max_ms=float(arr.max()),
        samples_ms=samples_tuple,
    )


def throughput(operations: int, wall_seconds: float) -> ThroughputStats:
    if operations < 0:
        raise ValueError("operations must be >= 0")
    if wall_seconds <= 0:
        raise ValueError("wall_seconds must be > 0")
    return ThroughputStats(
        operations=operations,
        wall_seconds=wall_seconds,
        ops_per_second=operations / wall_seconds,
    )


def summarize_latencies(
    batches: Iterable[Sequence[float]],
    *,
    keep_samples: bool = False,
) -> LatencyStats:
    flat: list[float] = []
    for batch in batches:
        flat.extend(batch)
    return percentiles_ms(flat, keep_samples=keep_samples)
