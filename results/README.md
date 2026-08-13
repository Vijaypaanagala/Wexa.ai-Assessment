# Results

- `runs/` — local timed outputs (gitignored). Written only after Phase 4+ adapters exist.
- No fake/sample benchmark numbers are committed.

## JSON schema (version 1)

Top-level document produced by `harness.runner.BenchmarkRunner`:

| Field | Type | Meaning |
|-------|------|---------|
| `schema_version` | int | Always `1` for Phase 3+ |
| `status` | string | `ok` \| `completed_with_errors` \| … |
| `platform` | string | Adapter name |
| `started_at_utc` / `finished_at_utc` | ISO-8601 | Wall-clock bounds |
| `client_region` | string | From `CLIENT_REGION` / config |
| `config` | object | Warm-up, iterations, seed, concurrency, read ratio |
| `dataset` | object | Phase 2 counts + checksums (when loaded) |
| `workload_plan` | object | Deterministic plan metadata (start-node preview, logical queries) |
| `workloads` | object | Per-workload timing blocks |
| `footprint` | object | Observable resources |
| `errors` | array | Per-iteration failures |
| `notes` | array | Human caveats |

### Per-workload block (`hop_*`, `point_lookup`, …)

| Field | Meaning |
|-------|---------|
| `workload` | Name |
| `status` | `ok` \| `partial` \| `failed` \| `not_run` |
| `warmup_iterations` | Discarded runs |
| `measured_iterations` | Timed runs (≥ 100 for reads in production config) |
| `wall_seconds` | Wall clock for the measured loop |
| `concurrency` | Set for mixed levels |
| `latency` | `n`, `p50_ms`, `p95_ms`, `p99_ms`, `mean_ms`, `min_ms`, `max_ms` |
| `throughput` | Optional `{operations, wall_seconds, ops_per_second}` |
| `qps` | Mixed level sustained queries/sec |
| `errors` | List of `{iteration, error, …}` |

### Mixed workload (timed)

Default duration is **30 seconds** per concurrency level (`mixed_duration_seconds`).

```json
"mixed": {
  "workload": "mixed",
  "mode": "timed",
  "duration_seconds_target": 30.0,
  "read_ratio": 0.8,
  "op_pool_size": 10000,
  "concurrency": {
    "1": {
      "total_operations": 1200,
      "successful_operations": 1198,
      "failed_operations": 2,
      "qps": 39.9,
      "duration_seconds_actual": 30.05,
      "latency": { "p50_ms": 1.2, "p95_ms": 3.4, "p99_ms": 5.1 }
    },
    "10": { "...": "..." },
    "40": { "...": "..." }
  }
}
```

This shape is intentionally table/chart-friendly: flatten `workloads.hop_1.latency.p50_ms` etc. in Phase 7.
