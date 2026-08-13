"""Dataset loader tests — read-only against Phase 2 artifacts when present."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.config import MANIFEST_PATH, NODES_CSV
from harness.dataset import load_manifest, load_node_ids, load_prepared_dataset


@pytest.mark.skipif(not MANIFEST_PATH.exists(), reason="Phase 2 manifest not present")
def test_load_manifest_pokec() -> None:
    m = load_manifest()
    assert m["subsample"]["relationship_count"] >= 100_000
    assert m["subsample"]["seed"] == 42


@pytest.mark.skipif(not NODES_CSV.exists(), reason="Phase 2 nodes.csv not present")
def test_load_node_ids_count_matches_manifest() -> None:
    ds = load_prepared_dataset(load_ids=True)
    assert ds.node_count == len(ds.node_ids) == 350_480
    assert ds.relationship_count == 250_000


def test_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path / "missing.json")


def test_load_node_ids_from_temp(tmp_path: Path) -> None:
    p = tmp_path / "nodes.csv"
    p.write_text("id\n1\n2\n3\n", encoding="utf-8")
    assert load_node_ids(p) == [1, 2, 3]
