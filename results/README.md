# Results

- `sample/` — optional checked-in example outputs (after first real run)
- `runs/` — local benchmark outputs (gitignored)

JSON schema (Phase 3+):

```json
{
  "platform": "cognodb",
  "client_region": "ap-south-1",
  "dataset": {"nodes": 0, "relationships": 0, "seed": 42},
  "warmup_iterations": 20,
  "read_iterations": 100,
  "ingest": {
    "nodes_per_sec": null,
    "relationships_per_sec": null,
    "wall_seconds": null,
    "method": "..."
  },
  "traversals": {
    "hop_1": {"p50_ms": null, "p95_ms": null},
    "hop_2": {"p50_ms": null, "p95_ms": null},
    "hop_3": {"p50_ms": null, "p95_ms": null}
  },
  "lookups": {
    "point": {"p50_ms": null, "p95_ms": null},
    "filtered": {"p50_ms": null, "p95_ms": null},
    "indexed_properties": ["id"]
  },
  "aggregation": {"p50_ms": null, "p95_ms": null},
  "mixed": {
    "read_ratio": 0.8,
    "concurrency": {
      "1": {"qps": null},
      "10": {"qps": null},
      "40": {"qps": null}
    }
  },
  "footprint": {},
  "caveats": []
}
```
