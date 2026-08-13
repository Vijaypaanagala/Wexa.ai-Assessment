"""Consistency checks for published results JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "results" / "published"
PLATFORMS = ("cognodb", "neo4j_aura", "memgraph", "falkordb", "arangodb")


@pytest.fixture(scope="module")
def docs() -> dict[str, dict]:
    if not PUBLISHED.exists():
        pytest.skip("published results not built yet")
    out = {}
    for name in PLATFORMS:
        path = PUBLISHED / f"{name}.json"
        if not path.exists():
            pytest.skip(f"missing {path}")
        out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


def test_all_platforms_present(docs) -> None:
    assert set(docs) == set(PLATFORMS)


def test_latency_ordering(docs) -> None:
    for name, doc in docs.items():
        for key in ("hop_1", "hop_2", "hop_3", "point_lookup", "filtered_lookup", "aggregation"):
            lat = doc["workloads"][key]["latency"]
            assert lat["p95_ms"] >= lat["p50_ms"], name
            assert lat["p99_ms"] >= lat["p95_ms"], name
            assert lat["min_ms"] <= lat["p50_ms"], name
            assert lat["max_ms"] >= lat["p99_ms"] or lat["max_ms"] >= lat["p95_ms"], name


def test_deeper_hops_generally_slower(docs) -> None:
    for name, doc in docs.items():
        h1 = doc["workloads"]["hop_1"]["latency"]["p50_ms"]
        h2 = doc["workloads"]["hop_2"]["latency"]["p50_ms"]
        h3 = doc["workloads"]["hop_3"]["latency"]["p50_ms"]
        assert h2 >= h1, name
        assert h3 >= h2, name


def test_ingest_math(docs) -> None:
    for name, doc in docs.items():
        ing = doc["workloads"]["ingest"]
        assert ing["nodes_loaded"] == 350_480
        assert ing["relationships_loaded"] == 250_000
        assert ing["nodes_per_sec"] > 0
        assert ing["relationships_per_sec"] > 0
        assert ing["wall_seconds"] > 0
        # wall ≈ node_wall + rel_wall
        assert abs(
            ing["wall_seconds"]
            - (ing["node_wall_seconds"] + ing["relationship_wall_seconds"])
        ) < 0.02


def test_mixed_concurrency_and_qps(docs) -> None:
    for name, doc in docs.items():
        mixed = doc["workloads"]["mixed"]["concurrency"]
        assert set(mixed) == {"1", "10", "40"}
        q1, q10, q40 = mixed["1"]["qps"], mixed["10"]["qps"], mixed["40"]["qps"]
        assert q10 >= q1, name
        assert q40 >= q10 * 0.9, name  # allow mild saturation
        for level in mixed.values():
            assert level["successful_operations"] >= 0
            assert level["failed_operations"] >= 0
            assert level["total_operations"] == (
                level["successful_operations"] + level["failed_operations"]
            )
            assert level["qps"] == level["throughput"]["ops_per_second"]
            lat = level["latency"]
            assert lat["p95_ms"] >= lat["p50_ms"]
            assert lat["p99_ms"] >= lat["p95_ms"]


def test_read_iterations_config(docs) -> None:
    for doc in docs.values():
        assert doc["config"]["read_iterations"] >= 100
        assert doc["config"]["warmup_iterations"] >= 0
        assert doc["config"]["mixed_duration_seconds"] == 30.0
