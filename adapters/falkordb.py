"""FalkorDB — official falkordb Python client with Cypher workloads."""

from __future__ import annotations

from typing import Any, Sequence
from urllib.parse import urlparse

from falkordb import FalkorDB

from adapters.base import GraphAdapter
from adapters.errors import AdapterConnectionError, require_value
from harness.config import falkordb_config


def _parse_host_port(uri: str) -> tuple[str, int]:
    if "://" not in uri:
        uri = "redis://" + uri
    parsed = urlparse(uri)
    return parsed.hostname or "localhost", parsed.port or 6379


class FalkorDBAdapter(GraphAdapter):
    name = "falkordb"
    batch_size = 200

    def __init__(self) -> None:
        self.cfg = falkordb_config()
        self._client: FalkorDB | None = None
        self._graph = None

    def connect(self) -> None:
        if self._client is not None:
            return
        uri = require_value(self.name, "FALKORDB_URI", self.cfg.uri)
        host, port = _parse_host_port(uri)
        graph_name = self.cfg.extra.get("graph") or "cognodb_bench"
        kwargs: dict[str, Any] = {"host": host, "port": port}
        if self.cfg.user:
            kwargs["username"] = self.cfg.user
        if self.cfg.password:
            kwargs["password"] = self.cfg.password
        try:
            self._client = FalkorDB(**kwargs)
            self._graph = self._client.select_graph(graph_name)
            result = self._graph.query("RETURN 1")
            rows = getattr(result, "result_set", None) or []
            if not rows or int(rows[0][0]) != 1:
                raise AdapterConnectionError(self.name, "RETURN 1 smoke query failed")
        except AdapterConnectionError:
            self._client = None
            self._graph = None
            raise
        except Exception as exc:  # noqa: BLE001
            self._client = None
            self._graph = None
            raise AdapterConnectionError(
                self.name, "Failed to connect via official FalkorDB client", cause=exc
            ) from exc

    def close(self) -> None:
        if self._client is not None:
            try:
                conn = getattr(self._client, "connection", None)
                if conn is not None and hasattr(conn, "close"):
                    conn.close()
            except Exception:  # noqa: BLE001
                pass
        self._client = None
        self._graph = None

    def ping(self) -> bool:
        if self._graph is None:
            raise AdapterConnectionError(self.name, "Not connected; call connect() first")
        result = self._graph.query("RETURN 1")
        rows = getattr(result, "result_set", None) or []
        return bool(rows) and int(rows[0][0]) == 1

    def _graph_req(self):
        if self._graph is None:
            raise AdapterConnectionError(self.name, "Not connected; call connect() first")
        return self._graph

    def _query(self, cypher: str, params: dict[str, Any] | None = None) -> list[Any]:
        g = self._graph_req()
        result = g.query(cypher, params or {})
        return list(getattr(result, "result_set", None) or [])

    def reset(self) -> None:
        g = self._graph_req()
        name = g.name if hasattr(g, "name") else self.cfg.extra.get("graph", "cognodb_bench")
        try:
            g.delete()
        except Exception:  # noqa: BLE001
            self._query("MATCH (n) DETACH DELETE n")
        self._graph = self._client.select_graph(name) if self._client else None

    def create_schema(self) -> None:
        return None

    def create_indexes(self) -> None:
        try:
            self._query("CREATE INDEX FOR (p:Person) ON (p.id)")
        except Exception:  # noqa: BLE001
            pass

    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        total = 0
        batch: list[int] = []
        for row in rows:
            batch.append(int(row["id"]))
            if len(batch) >= self.batch_size:
                self._query(
                    "UNWIND $ids AS id MERGE (p:Person {id: id})",
                    {"ids": batch},
                )
                total += len(batch)
                batch = []
        if batch:
            self._query("UNWIND $ids AS id MERGE (p:Person {id: id})", {"ids": batch})
            total += len(batch)
        return total

    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        total = 0
        batch: list[dict[str, int]] = []
        for row in rows:
            batch.append({"s": int(row["start_id"]), "e": int(row["end_id"])})
            if len(batch) >= self.batch_size:
                self._query(
                    """
                    UNWIND $rows AS row
                    MATCH (a:Person {id: row.s}), (b:Person {id: row.e})
                    MERGE (a)-[:FOLLOWS]->(b)
                    """,
                    {"rows": batch},
                )
                total += len(batch)
                batch = []
        if batch:
            self._query(
                """
                UNWIND $rows AS row
                MATCH (a:Person {id: row.s}), (b:Person {id: row.e})
                MERGE (a)-[:FOLLOWS]->(b)
                """,
                {"rows": batch},
            )
            total += len(batch)
        return total

    def query_1hop(self, start_id: int) -> int:
        rows = self._query(
            "MATCH (s:Person {id: $id})-[:FOLLOWS]->(n) RETURN count(n)",
            {"id": int(start_id)},
        )
        return int(rows[0][0]) if rows else 0

    def query_2hop(self, start_id: int) -> int:
        rows = self._query(
            "MATCH (s:Person {id: $id})-[:FOLLOWS*2]->(n) RETURN count(n)",
            {"id": int(start_id)},
        )
        return int(rows[0][0]) if rows else 0

    def query_3hop(self, start_id: int) -> int:
        rows = self._query(
            "MATCH (s:Person {id: $id})-[:FOLLOWS*3]->(n) RETURN count(n)",
            {"id": int(start_id)},
        )
        return int(rows[0][0]) if rows else 0

    def point_lookup(self, node_id: int) -> Any:
        rows = self._query(
            "MATCH (p:Person {id: $id}) RETURN p.id",
            {"id": int(node_id)},
        )
        return {"id": rows[0][0]} if rows else None

    def filtered_lookup(self, lo: int, hi: int) -> int:
        rows = self._query(
            "MATCH (p:Person) WHERE p.id >= $lo AND p.id < $hi RETURN count(p)",
            {"lo": int(lo), "hi": int(hi)},
        )
        return int(rows[0][0]) if rows else 0

    def aggregation(self) -> int:
        rows = self._query("MATCH ()-[r:FOLLOWS]->() RETURN count(r)")
        return int(rows[0][0]) if rows else 0

    def mixed_read(self, node_id: int) -> Any:
        return self.point_lookup(node_id)

    def mixed_write(self, src_id: int, dst_id: int) -> None:
        self._query(
            """
            MERGE (a:Person {id: $src})
            MERGE (b:Person {id: $dst})
            MERGE (a)-[:FOLLOWS]->(b)
            """,
            {"src": int(src_id), "dst": int(dst_id)},
        )

    def footprint(self) -> dict[str, Any]:
        return {
            "instance": "Docker (docker-compose.yml)",
            "vCPU": 0.5,
            "RAM": "256 MB (mem_limit target)",
            "source": "https://docs.falkordb.com/getting-started/clients.html",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
        }

    def load_method(self) -> str:
        return "FalkorDB Cypher GRAPH.QUERY batched inserts"

    def indexed_properties(self) -> list[str]:
        return ["id"]
