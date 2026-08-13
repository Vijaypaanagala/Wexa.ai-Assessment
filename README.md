# Graph Database Cloud Benchmark

Fair, reproducible comparison of **CognoDB Cloud** against peer graph databases on the **same dataset**, **same logical workloads**, and **equivalent resource limits**.

> Status: **Phase 2 complete** — SNAP soc-Pokec subsample ready. Metrics tables remain templates until Phases 5–7.

This repository is a take-home-style engineering benchmark: **methodology and honesty over declaring a winner**.

---

## Platforms under test

| Platform | Deployment | Query surface | Role in study |
|----------|------------|---------------|---------------|
| **CognoDB Cloud** (c0 free) | Managed cloud | Cypher / Bolt | Required baseline |
| **Neo4j AuraDB Free** | Managed cloud | Cypher / Bolt | Closest protocol peer |
| **Memgraph** | Docker, resource-capped | Cypher / Bolt | Low-footprint Cypher engine |
| **FalkorDB** | Docker, resource-capped | Cypher (RedisGraph lineage) | Tiny-footprint Cypher peer |
| **ArangoDB** | Docker, resource-capped | AQL (logical equivalents) | Non-Cypher control |

**Why this set:** four Cypher-compatible systems (including CognoDB) keep query semantics aligned; ArangoDB tests whether results hold when the language changes but the *logical* workload does not. Choosing credible peers is part of the evaluation.

---

## Resource parity (fairness)

CognoDB free tier is intentionally small. Every peer is sized to that budget (or the closest free/entry tier, documented honestly).

| Platform | vCPU | RAM | Storage | Notes |
|----------|------|-----|---------|-------|
| CognoDB Cloud c0 | **0.5** (burstable) | **256 MB** | **1 GB** | Advertised free tier; 200 connections |
| Neo4j Aura Free | Shared SaaS (not user-pinned) | Shared SaaS | Free-tier node/rel caps | **Closest free managed Neo4j**; exact CPU/RAM not configurable — caveat |
| Memgraph (Compose) | **0.5** | **256 MB** `mem_limit` | Host, dataset ≪ 1 GB | See `docker-compose.yml` |
| FalkorDB (Compose) | **0.5** | **256 MB** `mem_limit` | Host, dataset ≪ 1 GB | See `docker-compose.yml` |
| ArangoDB (Compose) | **0.5** | **256 MB** `mem_limit` | Host, dataset ≪ 1 GB | See `docker-compose.yml` |

**Fairness analysis (preliminary):**

- **Equal compute target:** 0.5 vCPU / 256 MB / ~1 GB for CognoDB + Docker peers.
- **Aura Free** cannot be pinned to 0.5/256; it remains in the study as the primary *managed* Cypher competitor, with shared-tenancy called out in caveats (not hidden).
- **Network:** CognoDB + Aura are remote; Memgraph/FalkorDB/ArangoDB are localhost. Latency tables must be read with RTT in mind; analysis will separate engine cost vs network where possible.
- Comparing a free tier to an uncapped paid tier is a methodology error — we do not do that.

---

## Dataset (Phase 2) — complete

| Field | Value |
|-------|-------|
| Source | [SNAP soc-Pokec](https://snap.stanford.edu/data/soc-Pokec.html) (`soc-pokec-relationships.txt.gz`) |
| Full SNAP graph | 1,632,803 nodes · 30,622,564 directed edges |
| Subsample method | Vitter Algorithm R reservoir sample; then sort by `(start_id, end_id)` |
| Seed | **42** |
| **Nodes** | **350,480** |
| **Relationships** | **250,000** |
| Schema | `(:Person {id})-[:FOLLOWS]->(:Person)` |
| Raw SHA-256 | `1a23e0ec8a4e497752125f6b3f01696fea7fcdb696fa61d1e822faf4d0d69b14` |
| nodes.csv SHA-256 | `2c4ca0a8350f1e8c5bcf1a99110483c34b701d5cb9ca5e5e665bd4897fe85f93` |
| relationships.csv SHA-256 | `562654a66d335eacefdb65eb0911cc0919a03091daf0e300b20f0e8ab0d4af45` |
| Manifest | [`data/prepared/manifest.json`](data/prepared/manifest.json) |

```powershell
py -3 data\prepare_dataset.py --seed 42 --target-relationships 250000
```

See [`data/README.md`](data/README.md) for citation and reproduce notes.

---

## Metrics (required)

Every platform will report:

| Category | Metric | Report |
|----------|--------|--------|
| Data loading | Ingest throughput | nodes/s, rels/s, wall-clock |
| Traversals | 1 / 2 / 3 hop | **p50** and **p95** latency (ms) |
| Lookups | Point + indexed/filtered | **p50** / **p95**; indexed properties listed |
| Aggregations | Count / group-by | **p50** / **p95** |
| Mixed workload | Concurrent R/W | QPS at concurrency **1 / 10 / 40**, 80/20 read/write |
| Footprint | Resource usage | Instance specs + observable size/memory, or “not observable” |

**Measurement defaults:** warm-up **20** iterations (discarded); read workloads **≥ 100** iterations; same client machine and `CLIENT_REGION` for all runs.

---

## Results matrix (templates — TBD)

### Ingest

| Platform | nodes/s | rels/s | wall (s) | Load method |
|----------|---------|--------|----------|-------------|
| CognoDB | — | — | — | Neo4j driver UNWIND batches |
| Neo4j Aura | — | — | — | Neo4j driver UNWIND batches |
| Memgraph | — | — | — | Neo4j driver UNWIND batches |
| FalkorDB | — | — | — | GRAPH.QUERY batches |
| ArangoDB | — | — | — | HTTP document/edge batches |

### Traversals (warm, ms)

| Platform | 1-hop p50 | 1-hop p95 | 2-hop p50 | 2-hop p95 | 3-hop p50 | 3-hop p95 |
|----------|-----------|-----------|-----------|-----------|-----------|-----------|
| CognoDB | — | — | — | — | — | — |
| Neo4j Aura | — | — | — | — | — | — |
| Memgraph | — | — | — | — | — | — |
| FalkorDB | — | — | — | — | — | — |
| ArangoDB | — | — | — | — | — | — |

### Lookups & aggregation (warm, ms)

| Platform | Point p50 | Point p95 | Filtered p50 | Filtered p95 | Indexed props | Agg p50 | Agg p95 |
|----------|-----------|-----------|--------------|--------------|---------------|---------|---------|
| CognoDB | — | — | — | — | `id` | — | — |
| Neo4j Aura | — | — | — | — | `id` | — | — |
| Memgraph | — | — | — | — | `id` | — | — |
| FalkorDB | — | — | — | — | `id` | — | — |
| ArangoDB | — | — | — | — | `id` | — | — |

### Mixed workload (QPS)

| Platform | c=1 | c=10 | c=40 | Mix |
|----------|-----|------|------|-----|
| CognoDB | — | — | — | 80% read / 20% write |
| Neo4j Aura | — | — | — | 80% read / 20% write |
| Memgraph | — | — | — | 80% read / 20% write |
| FalkorDB | — | — | — | 80% read / 20% write |
| ArangoDB | — | — | — | 80% read / 20% write |

### Footprint

| Platform | Specs | Stored size | Memory |
|----------|-------|-------------|--------|
| CognoDB | 0.5 vCPU / 256 MB / 1 GB | not observable | not observable |
| Neo4j Aura | Aura Free (shared) | not observable | not observable |
| Memgraph | 0.5 / 256 MB (Docker) | TBD | TBD |
| FalkorDB | 0.5 / 256 MB (Docker) | TBD | TBD |
| ArangoDB | 0.5 / 256 MB (Docker) | TBD | TBD |

---

## Methodology rules

1. Same prepared dataset bytes loaded everywhere.
2. Same logical queries (Cypher text shared among Bolt engines; AQL mapped 1:1 for ArangoDB).
3. Same client machine and region for all timed runs.
4. Warm-up before measurement; cold-start reported separately if included.
5. Automate via scripts under `scripts/` — no hand-timed stopwatch runs.
6. Record throttling, timeouts, dialect differences, and failed runs in **Caveats**.

---

## Repository layout

```
adapters/          # One adapter per platform (shared GraphAdapter interface)
harness/           # Config, metrics (p50/p95), workloads, runner
data/              # Dataset prep + prepared subsample
scripts/           # prepare → load → bench → run_all → plot
results/           # JSON outputs (schema documented)
charts/            # Figure output (Phase 7)
docker-compose.yml # Resource-capped Memgraph / FalkorDB / ArangoDB
.env.example       # Secrets template — copy to .env (never commit .env)
```

---

## Quick start (Phase 1)

```bash
# Python 3.11+
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # then fill secrets when accounts exist

# Smoke test (no database I/O)
python scripts/run_all.py --dry-run
python scripts/bench.py --platform cognodb --dry-run
```

Local Docker peers (Phases 4+):

```bash
docker compose up -d
```

**Secrets:** set `COGNODB_*`, `NEO4J_*`, etc. in `.env` only. Never commit passwords or connection URIs.

---

## Reproducibility roadmap

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | Skeleton, fairness docs, adapter stubs, dry-run CLI | **Done** |
| 2 | Seeded Pokec subsample + manifest | **Done** |
| 3 | Harness: warm-up, iterations, mixed concurrency | Pending |
| 4 | Live adapters + connectivity smoke tests | Pending |
| 5 | Loaders + ingest metrics | Pending |
| 6 | Full workload suite on all platforms | Pending |
| 7 | Charts, analysis, article | Pending |
| 8 | Public GitHub + submission email | Pending |

---

## Analysis (placeholder)

Numbers and root-cause discussion land after Phase 6. Expected themes: free-tier burst CPU, JVM vs native memory floors, cloud RTT vs localhost, Cypher planner differences, AQL traversal cost, and storage engine write paths.

---

## Caveats (living list)

- Aura Free CPU/RAM are **not** pin-identical to CognoDB c0; disclosed above.
- Docker peers run on the **client host** — lower RTT than managed cloud.
- 256 MB may force smaller batches or prevent some engines from starting; any limit change will be documented before results are published.
- Free-tier throttling / connection limits will be logged, not smoothed away.
- ArangoDB uses **logical** query equivalence, not identical Cypher strings.

---

## License

Benchmark code: MIT (see `LICENSE`). Dataset: subject to SNAP / source terms — cite Stanford SNAP when using Pokec.
