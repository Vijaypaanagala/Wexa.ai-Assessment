"""Deterministic workload generation tests."""

from __future__ import annotations

import pytest

from harness.config import BenchConfig
from harness.workload import build_workload_plan


def test_workload_plan_deterministic_same_seed() -> None:
    nodes = list(range(200))
    cfg = BenchConfig(
        workload_seed=42,
        read_iterations=20,
        start_node_count=15,
        mixed_op_pool_size=50,
        mixed_duration_seconds=30.0,
        mixed_concurrency=(1, 10, 40),
        warmup_iterations=5,
    )
    a = build_workload_plan(nodes, cfg)
    b = build_workload_plan(nodes, cfg)
    assert a.start_nodes == b.start_nodes
    assert a.point_lookup_ids == b.point_lookup_ids
    assert a.filter_ranges == b.filter_ranges
    assert a.mixed_op_pool == b.mixed_op_pool
    assert a.mixed_duration_seconds == 30.0


def test_workload_plan_changes_with_seed() -> None:
    nodes = list(range(200))
    a = build_workload_plan(nodes, BenchConfig(workload_seed=1, start_node_count=20))
    b = build_workload_plan(nodes, BenchConfig(workload_seed=2, start_node_count=20))
    assert a.start_nodes != b.start_nodes


def test_start_nodes_are_subset_of_population() -> None:
    nodes = [10, 20, 30, 40, 50, 60, 70, 80]
    plan = build_workload_plan(
        nodes,
        BenchConfig(
            workload_seed=7,
            start_node_count=5,
            read_iterations=5,
            mixed_op_pool_size=10,
        ),
    )
    assert set(plan.start_nodes).issubset(set(nodes))
    assert len(plan.start_nodes) == 5


def test_mixed_ops_respect_read_ratio_approximately() -> None:
    nodes = list(range(100))
    cfg = BenchConfig(
        workload_seed=42,
        mixed_op_pool_size=1000,
        mixed_read_ratio=0.8,
        read_iterations=10,
        start_node_count=10,
    )
    plan = build_workload_plan(nodes, cfg)
    reads = sum(1 for op in plan.mixed_op_pool if op.kind == "read")
    ratio = reads / len(plan.mixed_op_pool)
    assert 0.75 <= ratio <= 0.85


def test_mixed_op_at_is_deterministic_by_index() -> None:
    nodes = list(range(50))
    plan = build_workload_plan(
        nodes, BenchConfig(workload_seed=42, mixed_op_pool_size=100)
    )
    assert plan.mixed_op_at(0) == plan.mixed_op_at(0)
    assert plan.mixed_op_at(150) == plan.mixed_op_pool[50]


def test_filter_ranges_have_configured_width() -> None:
    nodes = list(range(500))
    cfg = BenchConfig(
        filter_width=25,
        read_iterations=12,
        start_node_count=10,
        mixed_op_pool_size=5,
    )
    plan = build_workload_plan(nodes, cfg)
    assert len(plan.filter_ranges) == 12
    for fr in plan.filter_ranges:
        assert fr.hi - fr.lo == 25


def test_empty_nodes_raise() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        build_workload_plan([], BenchConfig())


def test_same_plan_for_identical_logical_inputs_across_calls() -> None:
    """Simulates two platforms receiving the same plan inputs."""
    nodes = list(range(1000))
    cfg = BenchConfig(workload_seed=42, start_node_count=100, read_iterations=100)
    plans = [build_workload_plan(nodes, cfg) for _ in range(3)]
    assert plans[0].start_nodes == plans[1].start_nodes == plans[2].start_nodes
    assert len(plans[0].start_nodes) == 100
    assert len(plans[0].point_lookup_ids) == 100
