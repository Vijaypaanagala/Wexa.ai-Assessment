"""Unit tests for latency / throughput helpers."""

from __future__ import annotations

import pytest

from harness.metrics import percentiles_ms, summarize_latencies, throughput


def test_percentiles_basic() -> None:
    # 100 samples: 0..99
    samples = [float(i) for i in range(100)]
    stats = percentiles_ms(samples)
    assert stats.n == 100
    assert stats.min_ms == 0.0
    assert stats.max_ms == 99.0
    assert stats.mean_ms == pytest.approx(49.5)
    assert stats.p50_ms == pytest.approx(49.5)
    assert stats.p95_ms == pytest.approx(94.05)
    assert stats.p99_ms == pytest.approx(98.01)


def test_percentiles_single_sample() -> None:
    stats = percentiles_ms([12.5])
    assert stats.n == 1
    assert stats.p50_ms == 12.5
    assert stats.p95_ms == 12.5
    assert stats.min_ms == 12.5
    assert stats.max_ms == 12.5


def test_percentiles_empty_raises() -> None:
    with pytest.raises(ValueError, match="no latency samples"):
        percentiles_ms([])


def test_percentiles_keep_samples_optional() -> None:
    stats = percentiles_ms([1.0, 2.0, 3.0], keep_samples=True)
    assert stats.samples_ms == (1.0, 2.0, 3.0)
    d = stats.to_dict(include_samples=False)
    assert "samples_ms" not in d
    d2 = stats.to_dict(include_samples=True)
    assert d2["samples_ms"] == [1.0, 2.0, 3.0]


def test_throughput() -> None:
    t = throughput(200, 2.0)
    assert t.ops_per_second == pytest.approx(100.0)
    assert t.to_dict()["operations"] == 200


def test_throughput_rejects_non_positive_wall() -> None:
    with pytest.raises(ValueError):
        throughput(10, 0)
    with pytest.raises(ValueError):
        throughput(10, -1)


def test_summarize_latencies_flattens_batches() -> None:
    stats = summarize_latencies([[1.0, 2.0], [3.0, 4.0]])
    assert stats.n == 4
    assert stats.min_ms == 1.0
    assert stats.max_ms == 4.0
