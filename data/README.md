# Dataset (Phase 2)

## Source

| Field | Value |
|-------|-------|
| Name | SNAP soc-Pokec social network |
| Page | https://snap.stanford.edu/data/soc-Pokec.html |
| Edge list URL | https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz |
| Full graph (SNAP) | 1,632,803 nodes · 30,622,564 directed edges |
| Raw dump SHA-256 | `1a23e0ec8a4e497752125f6b3f01696fea7fcdb696fa61d1e822faf4d0d69b14` |
| Raw dump size | 132,454,730 bytes |
| Citation | L. Takac, M. Zabovsky. *Data Analysis in Public Social Networks*, International Scientific Conference & International Workshop Present Day Trends of Innovations, May 2012 Lomza, Poland. |

Friendship edges in Pokec are **directed**.

## Subsample (prepared artifacts)

| Field | Value |
|-------|-------|
| Method | Vitter Algorithm R reservoir sample; edges then sorted by `(start_id, end_id)` |
| Seed | **42** |
| Target relationships | 250,000 |
| **Nodes** | **350,480** |
| **Relationships** | **250,000** |
| Schema | `(:Person {id})-[:FOLLOWS]->(:Person)` |
| `nodes.csv` SHA-256 | `2c4ca0a8350f1e8c5bcf1a99110483c34b701d5cb9ca5e5e665bd4897fe85f93` |
| `relationships.csv` SHA-256 | `562654a66d335eacefdb65eb0911cc0919a03091daf0e300b20f0e8ab0d4af45` |

Source of truth: [`prepared/manifest.json`](prepared/manifest.json).

## Reproduce

```powershell
cd d:\Cognodb-Benchmark
py -3 data\prepare_dataset.py --seed 42 --target-relationships 250000
```

Do **not** commit `data/raw/`. Commit `prepared/nodes.csv`, `prepared/relationships.csv`, and `prepared/manifest.json`.
