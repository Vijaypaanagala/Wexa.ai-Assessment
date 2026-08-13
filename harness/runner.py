"""Platform-agnostic benchmark runner: warm-up, reads, mixed concurrency."""

from __future__ import annotations

import itertools
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from adapters.base import GraphAdapter
from harness.config import BenchConfig
from harness.dataset import PreparedDataset, load_prepared_dataset
from harness.metrics import LatencyStats, percentiles_ms, throughput
from harness.results import build_result_document, utc_now, workload_result
from harness.workload import MixedOp, WorkloadPlan, build_workload_plan


class BenchmarkRunner:
    """Drive workloads against any GraphAdapter using one WorkloadPlan."""

    def __init__(
        self,
        adapter: GraphAdapter,
        config: BenchConfig | None = None,
        *,
        node_ids: list[int] | tuple[int, ...] | None = None,
        dataset: PreparedDataset | None = None,
    ) -> None:
        self.adapter = adapter
        self.config = config or BenchConfig()
        self._dataset = dataset
        self._node_ids = tuple(node_ids) if node_ids is not None else None
        self._plan: WorkloadPlan | None = None

    def resolve_node_ids(self) -> tuple[int, ...]:
        if self._node_ids is not None:
            return self._node_ids
        if self._dataset is None:
            self._dataset = load_prepared_dataset(load_ids=True)
        self._node_ids = self._dataset.node_ids
        return self._node_ids

    def plan(self) -> WorkloadPlan:
        if self._plan is None:
            self._plan = build_workload_plan(self.resolve_node_ids(), self.config)
        return self._plan

    def run(
        self,
        *,
        include_mixed: bool = True,
        include_footprint: bool = True,
        connect: bool = False,
    ) -> dict:
        """Execute timed workloads.

        Parameters
        ----------
        connect:
            If True, call adapter.connect()/close(). Phase 3 tests use an
            in-memory fake already "connected"; Phase 4+ sets connect=True.
        """
        started = utc_now()
        cfg = self.config
        plan = self.plan()
        errors: list[dict[str, Any]] = []
        workloads: dict[str, Any] = {"_started_at_utc": started}

        if connect:
            self.adapter.connect()

        try:
            workloads["hop_1"] = self._run_hop(1, plan, errors)
            workloads["hop_2"] = self._run_hop(2, plan, errors)
            workloads["hop_3"] = self._run_hop(3, plan, errors)
            workloads["point_lookup"] = self._run_point_lookup(plan, errors)
            workloads["filtered_lookup"] = self._run_filtered_lookup(plan, errors)
            workloads["aggregation"] = self._run_aggregation(plan, errors)

            if include_mixed:
                workloads["mixed"] = self._run_mixed_all(plan, errors)

            footprint = self.adapter.footprint() if include_footprint else {}
        finally:
            if connect:
                self.adapter.close()

        dataset_dict = None
        if self._dataset is not None:
            dataset_dict = self._dataset.to_dict()
        elif self._node_ids is not None:
            dataset_dict = {
                "node_count": len(self._node_ids),
                "relationship_count": None,
                "note": "node_ids supplied directly (unit test / custom)",
            }

        status = "ok" if not errors else "completed_with_errors"
        return build_result_document(
            platform=self.adapter.name,
            config=cfg,
            dataset=dataset_dict,
            workload_plan=plan.to_dict(),
            workloads=workloads,
            status=status,
            errors=errors,
            footprint=footprint,
            notes=[
                "Harness Phase 3 measurement complete.",
                "Platform adapters and ingest metrics are Phase 4/5.",
            ],
        )

    # --- timed primitives -------------------------------------------------

    def _time_call(self, fn: Callable[[], Any]) -> tuple[float, Any, str | None]:
        t0 = time.perf_counter()
        try:
            result = fn()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return elapsed_ms, result, None
        except Exception as exc:  # noqa: BLE001 — collect per-op errors
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return elapsed_ms, None, f"{type(exc).__name__}: {exc}"

    def _measure_sequence(
        self,
        *,
        name: str,
        warmup_fns: list[Callable[[], Any]],
        measure_fns: list[Callable[[], Any]],
        errors: list[dict[str, Any]],
    ) -> dict:
        cfg = self.config
        for fn in warmup_fns:
            self._time_call(fn)

        samples: list[float] = []
        wall0 = time.perf_counter()
        for i, fn in enumerate(measure_fns):
            ms, _result, err = self._time_call(fn)
            samples.append(ms)
            if err:
                errors.append({"workload": name, "iteration": i, "error": err})
        wall = time.perf_counter() - wall0

        latency: LatencyStats | None = None
        if samples:
            latency = percentiles_ms(
                samples, keep_samples=cfg.include_raw_samples
            )
        status = "ok"
        if len([e for e in errors if e.get("workload") == name]) == len(measure_fns):
            status = "failed"
        elif any(e.get("workload") == name for e in errors):
            status = "partial"

        return workload_result(
            name=name,
            status=status,
            warmup_iterations=len(warmup_fns),
            measured_iterations=len(measure_fns),
            wall_seconds=wall,
            latency=latency,
            include_samples=cfg.include_raw_samples,
            errors=[e for e in errors if e.get("workload") == name],
        )

    def _run_hop(self, depth: int, plan: WorkloadPlan, errors: list) -> dict:
        name = f"hop_{depth}"
        query = {
            1: self.adapter.query_1hop,
            2: self.adapter.query_2hop,
            3: self.adapter.query_3hop,
        }[depth]

        starts = list(plan.start_nodes)
        # Cycle start nodes across warmup + measure iterations
        warmup_fns = [
            lambda i=i: query(starts[i % len(starts)])
            for i in range(plan.warmup_iterations)
        ]
        measure_fns = [
            lambda i=i: query(starts[i % len(starts)])
            for i in range(plan.read_iterations)
        ]
        return self._measure_sequence(
            name=name,
            warmup_fns=warmup_fns,
            measure_fns=measure_fns,
            errors=errors,
        )

    def _run_point_lookup(self, plan: WorkloadPlan, errors: list) -> dict:
        ids = list(plan.point_lookup_ids)
        warmup_fns = [
            lambda i=i: self.adapter.point_lookup(ids[i % len(ids)])
            for i in range(plan.warmup_iterations)
        ]
        measure_fns = [
            lambda i=i: self.adapter.point_lookup(ids[i % len(ids)])
            for i in range(plan.read_iterations)
        ]
        return self._measure_sequence(
            name="point_lookup",
            warmup_fns=warmup_fns,
            measure_fns=measure_fns,
            errors=errors,
        )

    def _run_filtered_lookup(self, plan: WorkloadPlan, errors: list) -> dict:
        ranges = list(plan.filter_ranges)
        warmup_fns = [
            lambda i=i: self.adapter.filtered_lookup(
                ranges[i % len(ranges)].lo, ranges[i % len(ranges)].hi
            )
            for i in range(plan.warmup_iterations)
        ]
        measure_fns = [
            lambda i=i: self.adapter.filtered_lookup(
                ranges[i % len(ranges)].lo, ranges[i % len(ranges)].hi
            )
            for i in range(plan.read_iterations)
        ]
        return self._measure_sequence(
            name="filtered_lookup",
            warmup_fns=warmup_fns,
            measure_fns=measure_fns,
            errors=errors,
        )

    def _run_aggregation(self, plan: WorkloadPlan, errors: list) -> dict:
        warmup_fns = [self.adapter.aggregation for _ in range(plan.warmup_iterations)]
        measure_fns = [self.adapter.aggregation for _ in range(plan.read_iterations)]
        return self._measure_sequence(
            name="aggregation",
            warmup_fns=warmup_fns,
            measure_fns=measure_fns,
            errors=errors,
        )

    def _run_mixed_all(self, plan: WorkloadPlan, errors: list) -> dict:
        by_conc: dict[str, Any] = {}
        for conc in plan.mixed_concurrency:
            by_conc[str(conc)] = self._run_mixed_level(plan, conc, errors)
        return {
            "workload": "mixed",
            "status": "ok",
            "mode": "timed",
            "duration_seconds_target": plan.mixed_duration_seconds,
            "read_ratio": plan.mixed_read_ratio,
            "op_pool_size": len(plan.mixed_op_pool),
            "concurrency": by_conc,
        }

    def _run_mixed_level(
        self,
        plan: WorkloadPlan,
        concurrency: int,
        errors: list[dict[str, Any]],
    ) -> dict:
        """Run mixed R/W for a fixed wall-clock duration at one concurrency."""
        if not plan.mixed_op_pool:
            raise ValueError("mixed_op_pool is empty")

        duration = plan.mixed_duration_seconds
        warm_n = plan.warmup_iterations
        for i in range(warm_n):
            self._exec_mixed_op(plan.mixed_op_at(i))

        samples: list[float] = []
        local_errors: list[dict[str, Any]] = []
        samples_lock = threading.Lock()
        op_counter = itertools.count()
        # Skip warm-up indices so measured stream continues deterministically
        for _ in range(warm_n):
            next(op_counter)

        deadline = time.perf_counter() + duration
        wall0 = time.perf_counter()

        def worker() -> None:
            while True:
                if time.perf_counter() >= deadline:
                    return
                idx = next(op_counter)
                op = plan.mixed_op_at(idx)
                ms, _result, err = self._time_call(lambda: self._exec_mixed_op(op))
                with samples_lock:
                    if err is None:
                        samples.append(ms)
                    else:
                        local_errors.append(
                            {
                                "workload": "mixed",
                                "concurrency": concurrency,
                                "iteration": idx,
                                "error": err,
                            }
                        )

        try:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [pool.submit(worker) for _ in range(concurrency)]
                for fut in as_completed(futures):
                    try:
                        fut.result()
                    except Exception as exc:  # noqa: BLE001
                        with samples_lock:
                            local_errors.append(
                                {
                                    "workload": "mixed",
                                    "concurrency": concurrency,
                                    "error": f"{type(exc).__name__}: {exc}",
                                    "traceback": traceback.format_exc(),
                                }
                            )
        except Exception as exc:  # noqa: BLE001
            local_errors.append(
                {
                    "workload": "mixed",
                    "concurrency": concurrency,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
            )

        wall = time.perf_counter() - wall0
        errors.extend(local_errors)

        successful = len(samples)
        failed = len(local_errors)
        total = successful + failed

        latency = (
            percentiles_ms(samples, keep_samples=self.config.include_raw_samples)
            if samples
            else None
        )
        thr = throughput(successful, wall) if wall > 0 and successful else None
        status = "ok"
        if total == 0 or (failed and successful == 0):
            status = "failed"
        elif failed:
            status = "partial"

        return workload_result(
            name="mixed",
            status=status,
            warmup_iterations=warm_n,
            measured_iterations=successful,
            wall_seconds=wall,
            latency=latency,
            throughput_stats=thr,
            concurrency=concurrency,
            errors=local_errors,
            include_samples=self.config.include_raw_samples,
            extra={
                "mode": "timed",
                "duration_seconds_target": duration,
                "duration_seconds_actual": wall,
                "total_operations": total,
                "successful_operations": successful,
                "failed_operations": failed,
                "qps": thr.ops_per_second if thr else 0.0,
                "read_ratio": plan.mixed_read_ratio,
            },
        )

    def _exec_mixed_op(self, op: MixedOp) -> Any:
        if op.kind == "read":
            return self.adapter.mixed_read(op.node_id)
        if op.dst_id is None:
            raise ValueError("write mixed op missing dst_id")
        self.adapter.mixed_write(op.node_id, op.dst_id)
        return None


def run_platform(
    adapter: GraphAdapter,
    config: BenchConfig | None = None,
    **kwargs: Any,
) -> dict:
    """Convenience entry point used by scripts/bench.py."""
    return BenchmarkRunner(adapter, config, **kwargs).run()
