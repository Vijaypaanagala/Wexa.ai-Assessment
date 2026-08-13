"""Read Phase 2 prepared artifacts (never regenerate them)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from harness.config import DATA_DIR, MANIFEST_PATH, NODES_CSV, RELATIONSHIPS_CSV


@dataclass(frozen=True)
class PreparedDataset:
    """Metadata + node ids from Phase 2 outputs."""

    node_ids: tuple[int, ...]
    node_count: int
    relationship_count: int
    seed: int
    source_name: str
    source_page: str
    nodes_sha256: str
    relationships_sha256: str
    manifest_path: Path
    nodes_csv: Path
    relationships_csv: Path

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "source_page": self.source_page,
            "node_count": self.node_count,
            "relationship_count": self.relationship_count,
            "dataset_seed": self.seed,
            "nodes_sha256": self.nodes_sha256,
            "relationships_sha256": self.relationships_sha256,
            "nodes_csv": str(self.nodes_csv).replace("\\", "/"),
            "relationships_csv": str(self.relationships_csv).replace("\\", "/"),
        }


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Phase 2 manifest missing: {path}. "
            "Restore data/prepared/manifest.json before running the harness."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_node_ids(nodes_csv: Path = NODES_CSV) -> list[int]:
    if not nodes_csv.exists():
        raise FileNotFoundError(f"Phase 2 nodes CSV missing: {nodes_csv}")
    ids: list[int] = []
    with nodes_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "id" not in reader.fieldnames:
            raise ValueError(f"{nodes_csv} must have an 'id' column")
        for row in reader:
            ids.append(int(row["id"]))
    if not ids:
        raise ValueError(f"{nodes_csv} contains no node ids")
    return ids


def load_prepared_dataset(
    data_dir: Path = DATA_DIR,
    *,
    load_ids: bool = True,
) -> PreparedDataset:
    """Load Phase 2 outputs. Does not download or resample Pokec."""
    manifest_path = data_dir / "manifest.json"
    nodes_csv = data_dir / "nodes.csv"
    rels_csv = data_dir / "relationships.csv"
    manifest = load_manifest(manifest_path)
    sub = manifest["subsample"]
    arts = manifest["artifacts"]
    node_ids: tuple[int, ...] = ()
    if load_ids:
        node_ids = tuple(load_node_ids(nodes_csv))
        if len(node_ids) != int(sub["node_count"]):
            raise ValueError(
                f"nodes.csv count {len(node_ids)} != manifest node_count "
                f"{sub['node_count']}"
            )
    return PreparedDataset(
        node_ids=node_ids,
        node_count=int(sub["node_count"]),
        relationship_count=int(sub["relationship_count"]),
        seed=int(sub["seed"]),
        source_name=manifest["source"]["name"],
        source_page=manifest["source"]["page"],
        nodes_sha256=arts["nodes_csv"]["sha256"],
        relationships_sha256=arts["relationships_csv"]["sha256"],
        manifest_path=manifest_path,
        nodes_csv=nodes_csv,
        relationships_csv=rels_csv,
    )


def iter_relationship_rows(relationships_csv: Path = RELATIONSHIPS_CSV):
    """Yield relationship dicts for loaders (Phase 5). Read-only."""
    with relationships_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {
                "start_id": int(row["start_id"]),
                "end_id": int(row["end_id"]),
                "type": row.get("type", "FOLLOWS"),
            }


def iter_node_rows(nodes_csv: Path = NODES_CSV):
    with nodes_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {"id": int(row["id"])}
