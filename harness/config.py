"""Shared paths, platform env helpers, and benchmark configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data" / "prepared"
RESULTS_DIR = ROOT / "results" / "runs"
MANIFEST_PATH = DATA_DIR / "manifest.json"
NODES_CSV = DATA_DIR / "nodes.csv"
RELATIONSHIPS_CSV = DATA_DIR / "relationships.csv"

# Defaults matching assignment methodology
DEFAULT_WORKLOAD_SEED = 42
DEFAULT_WARMUP_ITERATIONS = 20
DEFAULT_READ_ITERATIONS = 100
DEFAULT_START_NODE_COUNT = 100
DEFAULT_MIXED_CONCURRENCY = (1, 10, 40)
DEFAULT_MIXED_READ_RATIO = 0.80
DEFAULT_MIXED_DURATION_SECONDS = 30.0
DEFAULT_MIXED_OP_POOL_SIZE = 10_000
DEFAULT_FILTER_WIDTH = 1_000


def _req(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


CLIENT_REGION = _req("CLIENT_REGION", "unspecified")


@dataclass(frozen=True)
class PlatformConfig:
    name: str
    kind: str  # "cloud" | "docker"
    uri: str
    user: str
    password: str
    extra: dict[str, str]


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

# Back-compat aliases used by Phase 1 stubs / scripts
WARMUP_ITERATIONS = DEFAULT_WARMUP_ITERATIONS
READ_ITERATIONS = DEFAULT_READ_ITERATIONS
MIXED_CONCURRENCY = DEFAULT_MIXED_CONCURRENCY
MIXED_READ_RATIO = DEFAULT_MIXED_READ_RATIO


@dataclass(frozen=True)
class BenchConfig:
    """Platform-agnostic measurement knobs (no credentials required)."""

    workload_seed: int = DEFAULT_WORKLOAD_SEED
    warmup_iterations: int = DEFAULT_WARMUP_ITERATIONS
    read_iterations: int = DEFAULT_READ_ITERATIONS
    start_node_count: int = DEFAULT_START_NODE_COUNT
    mixed_concurrency: tuple[int, ...] = DEFAULT_MIXED_CONCURRENCY
    mixed_read_ratio: float = DEFAULT_MIXED_READ_RATIO
    mixed_duration_seconds: float = DEFAULT_MIXED_DURATION_SECONDS
    mixed_op_pool_size: int = DEFAULT_MIXED_OP_POOL_SIZE
    filter_width: int = DEFAULT_FILTER_WIDTH
    client_region: str = field(default_factory=lambda: CLIENT_REGION)
    include_raw_samples: bool = False

    def __post_init__(self) -> None:
        if self.warmup_iterations < 0:
            raise ValueError("warmup_iterations must be >= 0")
        if self.read_iterations < 1:
            raise ValueError("read_iterations must be >= 1")
        if self.start_node_count < 1:
            raise ValueError("start_node_count must be >= 1")
        if not (0.0 <= self.mixed_read_ratio <= 1.0):
            raise ValueError("mixed_read_ratio must be in [0, 1]")
        if self.mixed_duration_seconds <= 0:
            raise ValueError("mixed_duration_seconds must be > 0")
        if self.mixed_op_pool_size < 1:
            raise ValueError("mixed_op_pool_size must be >= 1")
        if self.filter_width < 1:
            raise ValueError("filter_width must be >= 1")
        if any(c < 1 for c in self.mixed_concurrency):
            raise ValueError("mixed_concurrency values must be >= 1")

    def with_overrides(self, **kwargs: object) -> BenchConfig:
        return replace(self, **kwargs)  # type: ignore[arg-type]
