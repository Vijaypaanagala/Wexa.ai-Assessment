"""BenchmarkRunner behaviour with FakeInMemoryAdapter (no real DB)."""

from __future__ import annotations

from harness.config import BenchConfig
from harness.runner import BenchmarkRunner, run_platform
from harness.workload import build_workload_plan
from tests.fakes import FakeInMemoryAdapter, seed_line_graph


def test_runner_produces_schema_and_percentiles(fake_adapter, tiny_config) -> None:
    node_ids = sorted(fake_adapter.nodes)
    runner = BenchmarkRunner(fake_adapter, tiny_config, node_ids=node_ids)
    doc = runner.run(include_mixed=True, connect=False)

    assert doc["schema_version"] == 1
    assert doc["platform"] == "fake_memory"
    assert doc["status"] in {"ok", "completed_with_errors"}
    assert doc["config"]["read_iterations"] == 10
    assert doc["config"]["mixed_duration_seconds"] == 0.2

    for name in ("hop_1", "hop_2", "hop_3", "point_lookup", "filtered_lookup", "aggregation"):
        wl = doc["workloads"][name]
        assert wl["measured_iterations"] == 10
        assert wl["warmup_iterations"] == 2
        assert wl["latency"]["n"] == 10
        assert wl["latency"]["p50_ms"] is not None
        assert wl["latency"]["p95_ms"] is not None
        assert wl["latency"]["min_ms"] <= wl["latency"]["p50_ms"]
        assert wl["wall_seconds"] is not None

    mixed = doc["workloads"]["mixed"]
    assert mixed["mode"] == "timed"
    assert mixed["duration_seconds_target"] == 0.2
    assert "1" in mixed["concurrency"]
    assert "2" in mixed["concurrency"]
    for level in mixed["concurrency"].values():
        assert level["mode"] == "timed"
        assert level["total_operations"] >= 1
        assert level["successful_operations"] >= 1
        assert level["failed_operations"] == 0
        assert level["qps"] is not None and level["qps"] > 0
        assert level["latency"]["p50_ms"] is not None
        assert level["latency"]["p95_ms"] is not None
        assert level["latency"]["p99_ms"] is not None
        assert level["duration_seconds_actual"] >= 0.15


def test_runner_warmup_invokes_adapter(fake_adapter, tiny_config) -> None:
    node_ids = sorted(fake_adapter.nodes)
    runner = BenchmarkRunner(fake_adapter, tiny_config, node_ids=node_ids)
    runner.run(include_mixed=False)
    # warmup(2) + measure(10) for hop_1
    assert fake_adapter.call_counts["query_1hop"] == 12
    assert fake_adapter.call_counts["aggregation"] == 12


def test_identical_plans_for_two_fake_platforms(tiny_config) -> None:
    a = FakeInMemoryAdapter()
    b = FakeInMemoryAdapter()
    ids = seed_line_graph(a, 30)
    seed_line_graph(b, 30)
    plan_a = build_workload_plan(ids, tiny_config)
    plan_b = build_workload_plan(ids, tiny_config)
    assert plan_a.start_nodes == plan_b.start_nodes
    assert plan_a.mixed_op_pool == plan_b.mixed_op_pool


def test_run_platform_convenience(fake_adapter, tiny_config) -> None:
    doc = run_platform(fake_adapter, tiny_config, node_ids=sorted(fake_adapter.nodes))
    assert doc["platform"] == "fake_memory"
    assert "hop_1" in doc["workloads"]


def test_mixed_concurrency_default_levels() -> None:
    adapter = FakeInMemoryAdapter()
    ids = seed_line_graph(adapter, 25)
    cfg = BenchConfig(
        warmup_iterations=1,
        read_iterations=5,
        start_node_count=5,
        mixed_duration_seconds=0.15,
        mixed_op_pool_size=32,
        mixed_concurrency=(1, 10, 40),
        mixed_read_ratio=0.8,
    )
    doc = BenchmarkRunner(adapter, cfg, node_ids=ids).run(include_mixed=True)
    assert set(doc["workloads"]["mixed"]["concurrency"]) == {"1", "10", "40"}
    for level in doc["workloads"]["mixed"]["concurrency"].values():
        assert "total_operations" in level
        assert "successful_operations" in level
        assert "failed_operations" in level
        assert "qps" in level


def test_live_adapter_requires_connection_before_query() -> None:
    from adapters.cognodb import CognoDBAdapter
    from adapters.errors import AdapterConnectionError

    ad = CognoDBAdapter()
    try:
        ad.query_1hop(1)
        raised = False
    except AdapterConnectionError:
        raised = True
    assert raised
