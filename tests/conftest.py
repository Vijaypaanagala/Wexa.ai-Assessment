"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from harness.config import BenchConfig
from tests.fakes import FakeInMemoryAdapter, seed_line_graph


@pytest.fixture
def tiny_config() -> BenchConfig:
    return BenchConfig(
        workload_seed=42,
        warmup_iterations=2,
        read_iterations=10,
        start_node_count=8,
        mixed_concurrency=(1, 2),
        mixed_read_ratio=0.8,
        mixed_duration_seconds=0.2,
        mixed_op_pool_size=64,
        filter_width=5,
        client_region="test",
    )


@pytest.fixture
def fake_adapter() -> FakeInMemoryAdapter:
    adapter = FakeInMemoryAdapter()
    seed_line_graph(adapter, n=40)
    return adapter
