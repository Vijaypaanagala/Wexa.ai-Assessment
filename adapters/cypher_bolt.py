"""Shared Cypher workload implementation for Bolt drivers (CognoDB / Aura / Memgraph)."""

from __future__ import annotations

from typing import Any, Sequence

from adapters.errors import AdapterConnectionError


class CypherBoltWorkloads:
    """Mixin expecting self._driver and self.name."""

    _driver: Any
    name: str
    index_dialect: str = "neo4j"  # "neo4j" | "memgraph"
    batch_size: int = 500

    def _require_driver(self) -> Any:
        if self._driver is None:
            raise AdapterConnectionError(self.name, "Not connected; call connect() first")
        return self._driver

    def _execute(self, cypher: str, **params: Any) -> list[Any]:
        driver = self._require_driver()
        records, _summary, _keys = driver.execute_query(cypher, parameters_=params)
        return list(records)

    def _scalar(self, cypher: str, key: str, **params: Any) -> Any:
        rows = self._execute(cypher, **params)
        if not rows:
            return None
        data = rows[0].data()
        return data.get(key, rows[0][0])

    def reset(self) -> None:
        # Batch delete to reduce memory spikes on tiny free tiers
        while True:
            rows = self._execute(
                "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(*) AS c"
            )
            deleted = int(rows[0].data().get("c", 0)) if rows else 0
            if deleted == 0:
                break

    def create_schema(self) -> None:
        # Labels/types are created implicitly on write for these engines.
        return None

    def create_indexes(self) -> None:
        if self.index_dialect == "memgraph":
            try:
                self._execute("CREATE INDEX ON :Person(id)")
            except Exception:
                # Index may already exist
                pass
            return
        self._execute(
            "CREATE INDEX person_id IF NOT EXISTS FOR (p:Person) ON (p.id)"
        )

    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        total = 0
        batch: list[dict[str, Any]] = []
        for row in rows:
            batch.append({"id": int(row["id"])})
            if len(batch) >= self.batch_size:
                self._execute(
                    "UNWIND $rows AS row MERGE (p:Person {id: row.id})",
                    rows=batch,
                )
                total += len(batch)
                batch = []
        if batch:
            self._execute(
                "UNWIND $rows AS row MERGE (p:Person {id: row.id})",
                rows=batch,
            )
            total += len(batch)
        return total

    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        total = 0
        batch: list[dict[str, Any]] = []
        for row in rows:
            batch.append(
                {"start_id": int(row["start_id"]), "end_id": int(row["end_id"])}
            )
            if len(batch) >= self.batch_size:
                self._execute(
                    """
                    UNWIND $rows AS row
                    MATCH (a:Person {id: row.start_id}), (b:Person {id: row.end_id})
                    MERGE (a)-[:FOLLOWS]->(b)
                    """,
                    rows=batch,
                )
                total += len(batch)
                batch = []
        if batch:
            self._execute(
                """
                UNWIND $rows AS row
                MATCH (a:Person {id: row.start_id}), (b:Person {id: row.end_id})
                MERGE (a)-[:FOLLOWS]->(b)
                """,
                rows=batch,
            )
            total += len(batch)
        return total

    def query_1hop(self, start_id: int) -> int:
        return int(
            self._scalar(
                "MATCH (s:Person {id: $id})-[:FOLLOWS]->(n) RETURN count(n) AS c",
                "c",
                id=int(start_id),
            )
            or 0
        )

    def query_2hop(self, start_id: int) -> int:
        return int(
            self._scalar(
                "MATCH (s:Person {id: $id})-[:FOLLOWS*2]->(n) RETURN count(DISTINCT n) AS c",
                "c",
                id=int(start_id),
            )
            or 0
        )

    def query_3hop(self, start_id: int) -> int:
        return int(
            self._scalar(
                "MATCH (s:Person {id: $id})-[:FOLLOWS*3]->(n) RETURN count(DISTINCT n) AS c",
                "c",
                id=int(start_id),
            )
            or 0
        )

    def point_lookup(self, node_id: int) -> Any:
        rows = self._execute(
            "MATCH (p:Person {id: $id}) RETURN p.id AS id",
            id=int(node_id),
        )
        return rows[0].data() if rows else None

    def filtered_lookup(self, lo: int, hi: int) -> int:
        return int(
            self._scalar(
                "MATCH (p:Person) WHERE p.id >= $lo AND p.id < $hi RETURN count(p) AS c",
                "c",
                lo=int(lo),
                hi=int(hi),
            )
            or 0
        )

    def aggregation(self) -> int:
        return int(
            self._scalar("MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS c", "c") or 0
        )

    def mixed_read(self, node_id: int) -> Any:
        return self.point_lookup(node_id)

    def mixed_write(self, src_id: int, dst_id: int) -> None:
        self._execute(
            """
            MERGE (a:Person {id: $src})
            MERGE (b:Person {id: $dst})
            MERGE (a)-[:FOLLOWS]->(b)
            """,
            src=int(src_id),
            dst=int(dst_id),
        )

    def indexed_properties(self) -> list[str]:
        return ["id"]
