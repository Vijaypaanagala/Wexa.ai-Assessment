"""Shared configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class PlatformConfig:
    name: str
    kind: str  # "cloud" | "docker"
    uri: str
    user: str
    password: str
    extra: dict[str, str]


def _req(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def cognodb_config() -> PlatformConfig:
    return PlatformConfig(
        name="cognodb",
        kind="cloud",
        uri=_req("COGNODB_URI"),
        user=_req("COGNODB_USER", "cognodb"),
        password=_req("COGNODB_PASSWORD"),
        extra={},
    )


def neo4j_aura_config() -> PlatformConfig:
    return PlatformConfig(
        name="neo4j_aura",
        kind="cloud",
        uri=_req("NEO4J_URI"),
        user=_req("NEO4J_USER", "neo4j"),
        password=_req("NEO4J_PASSWORD"),
        extra={},
    )


def memgraph_config() -> PlatformConfig:
    return PlatformConfig(
        name="memgraph",
        kind="docker",
        uri=_req("MEMGRAPH_URI", "bolt://localhost:7687"),
        user=_req("MEMGRAPH_USER"),
        password=_req("MEMGRAPH_PASSWORD"),
        extra={},
    )


def falkordb_config() -> PlatformConfig:
    return PlatformConfig(
        name="falkordb",
        kind="docker",
        uri=_req("FALKORDB_URI", "redis://localhost:6379"),
        user=_req("FALKORDB_USER"),
        password=_req("FALKORDB_PASSWORD"),
        extra={"graph": _req("FALKORDB_GRAPH", "cognodb_bench")},
    )


def arangodb_config() -> PlatformConfig:
    return PlatformConfig(
        name="arangodb",
        kind="docker",
        uri=_req("ARANGO_URL", "http://localhost:8529"),
        user=_req("ARANGO_USER", "root"),
        password=_req("ARANGO_PASSWORD"),
        extra={"db": _req("ARANGO_DB", "cognodb_bench")},
    )


CONFIGS = {
    "cognodb": cognodb_config,
    "neo4j_aura": neo4j_aura_config,
    "memgraph": memgraph_config,
    "falkordb": falkordb_config,
    "arangodb": arangodb_config,
}

PLATFORMS = tuple(CONFIGS.keys())

# Benchmark defaults (Phase 3 will honor these; documented in README)
WARMUP_ITERATIONS = 20
READ_ITERATIONS = 100
MIXED_CONCURRENCY = (1, 10, 40)
MIXED_READ_RATIO = 0.80
CLIENT_REGION = _req("CLIENT_REGION", "unspecified")
DATA_DIR = ROOT / "data" / "prepared"
RESULTS_DIR = ROOT / "results" / "runs"