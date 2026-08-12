"""Logical workloads — same intent on every platform; adapters translate dialect."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSpec:
    """Filled by data/prepare_dataset.py (Phase 2)."""

    source_name: str
    source_url: str
    node_count: int
    relationship_count: int
    seed: int
    node_label: str = "Person"
    rel_type: str = "FOLLOWS"
    id_property: str = "id"


# Logical query contracts (implementations live in adapters)
# 1-hop:  MATCH (s:Person {id:$id})-[:FOLLOWS]->(n) RETURN count(n)
# 2-hop:  ...-[:FOLLOWS*2]->(n) or equivalent two-step expand
# 3-hop:  ...-[:FOLLOWS*3]->(n)
# point:  MATCH (p:Person {id:$id}) RETURN p
# filter: MATCH (p:Person) WHERE p.id >= $lo AND p.id < $hi RETURN count(p)
# agg:    MATCH ()-[r:FOLLOWS]->() RETURN count(r)
# mixed:  80% point lookup / 20% create ephemeral FOLLOWS then delete (or property touch)


WORKLOAD_NAMES = (
    "ingest",
    "hop_1",
    "hop_2",
    "hop_3",
    "point_lookup",
    "filtered_lookup",
    "aggregation",
    "mixed",
    "footprint",
)