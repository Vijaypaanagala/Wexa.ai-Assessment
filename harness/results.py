"""Result document schema helpers for README / chart generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.config import BenchConfig, RESULTS_DIR
from harness.metrics import LatencyStats, ThroughputStats


SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def latency_payload(stats: LatencyStats, *, include_samples: bool = False) -> dict:
    return stats.to_dict(include_samples=include_samples)


def empty_latency() -> dict:
    return {
        "n": 0,
        "p50_ms": None,
        "p95_ms": None,
        "p99_ms": None,
        "mean_ms": None,
        "min_ms": None,
        "max_ms": None,
        "status": "not_run",
    }


def workload_result(
    *,
    name: str,
    status: str,
    warmup_iterations: int,
    measured_iterations: int,
    wall_seconds: float | None = None,
    latency: LatencyStats | None = None,
    throughput_stats: ThroughputStats | None = None,
    concurrency: int | None = None,
    errors: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
    include_samples: bool = False,
) -> dict:
    body: dict[str, Any] = {
        "workload": name,
        "status": status,
        "warmup_iterations": warmup_iterations,
        "measured_iterations": measured_iterations,
        "wall_seconds": wall_seconds,
        "concurrency": concurrency,
        "latency": latency_payload(latency, include_samples=include_samples)
        if latency is not None
        else empty_latency(),
        "errors": errors or [],
    }
    if throughput_stats is not None:
        body["throughput"] = throughput_stats.to_dict()
    if extra:
        body.update(extra)
    return body


def build_result_document(
    *,
    platform: str,
    config: BenchConfig,
    dataset: dict[str, Any] | None,
    workload_plan: dict[str, Any] | None,
    workloads: dict[str, Any],
    status: str,
    errors: list[dict[str, Any]] | None = None,
    footprint: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "platform": platform,
        "started_at_utc": workloads.pop("_started_at_utc", None),
        "finished_at_utc": utc_now(),
        "client_region": config.client_region,
        "config": {
            "workload_seed": config.workload_seed,
            "warmup_iterations": config.warmup_iterations,
            "read_iterations": config.read_iterations,
            "start_node_count": config.start_node_count,
            "mixed_concurrency": list(config.mixed_concurrency),
            "mixed_read_ratio": config.mixed_read_ratio,
            "mixed_duration_seconds": config.mixed_duration_seconds,
            "mixed_op_pool_size": config.mixed_op_pool_size,
            "filter_width": config.filter_width,
        },
        "dataset": dataset,
        "workload_plan": workload_plan,
        "workloads": workloads,
        "footprint": footprint or {},
        "errors": errors or [],
        "notes": notes
        or [
            "Actual timed results require Phase 4 adapters + Phase 5/6 runs.",
        ],
    }


def write_result_json(doc: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return path


def default_result_path(platform: str, results_dir: Path = RESULTS_DIR) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return results_dir / f"{platform}_{stamp}.json"
