"""BenchConfig validation tests."""

from __future__ import annotations

import pytest

from harness.config import (
    DEFAULT_MIXED_CONCURRENCY,
    DEFAULT_MIXED_DURATION_SECONDS,
    DEFAULT_READ_ITERATIONS,
    DEFAULT_WARMUP_ITERATIONS,
    BenchConfig,
    PLATFORMS,
)


def test_default_config_matches_methodology() -> None:
    cfg = BenchConfig()
    assert cfg.warmup_iterations == DEFAULT_WARMUP_ITERATIONS
    assert cfg.read_iterations == DEFAULT_READ_ITERATIONS
    assert cfg.read_iterations >= 100
    assert cfg.mixed_concurrency == DEFAULT_MIXED_CONCURRENCY
    assert cfg.mixed_read_ratio == 0.8
    assert cfg.mixed_duration_seconds == DEFAULT_MIXED_DURATION_SECONDS
    assert cfg.mixed_duration_seconds == 30.0
    assert cfg.workload_seed == 42


def test_platforms_registry() -> None:
    assert "cognodb" in PLATFORMS
    assert "neo4j_aura" in PLATFORMS
    assert len(PLATFORMS) == 5


def test_invalid_read_iterations() -> None:
    with pytest.raises(ValueError):
        BenchConfig(read_iterations=0)


def test_invalid_read_ratio() -> None:
    with pytest.raises(ValueError):
        BenchConfig(mixed_read_ratio=1.5)


def test_invalid_concurrency() -> None:
    with pytest.raises(ValueError):
        BenchConfig(mixed_concurrency=(1, 0, 40))


def test_invalid_duration() -> None:
    with pytest.raises(ValueError):
        BenchConfig(mixed_duration_seconds=0)
    with pytest.raises(ValueError):
        BenchConfig(mixed_duration_seconds=-1)


def test_with_overrides() -> None:
    cfg = BenchConfig().with_overrides(
        read_iterations=200, mixed_read_ratio=0.9, mixed_duration_seconds=15.0
    )
    assert cfg.read_iterations == 200
    assert cfg.mixed_read_ratio == 0.9
    assert cfg.mixed_duration_seconds == 15.0
    assert cfg.workload_seed == 42
