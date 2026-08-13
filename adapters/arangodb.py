"""ArangoDB — official python-arango driver with AQL logical equivalents."""

from __future__ import annotations

from typing import Any, Sequence

from arango import ArangoClient
from arango.exceptions import ArangoError

from adapters.base import GraphAdapter
from adapters.errors import AdapterConnectionError, require_value
from harness.config import arangodb_config


class ArangoDBAdapter(GraphAdapter):
    name = "arangodb"
    batch_size = 500

    def __init__(self) -> None:
        self.cfg = arangodb_config()
        self._client: ArangoClient | None = None
        self._sys = None
        self._db = None
        self._db_name = self.cfg.extra.get("db") or "cognodb_bench"

    def connect(self) -> None:
        if self._client is not None:
            return
        url = require_value(self.name, "ARANGO_URL", self.cfg.uri)
        user = self.cfg.user or "root"
        password = require_value(self.name, "ARANGO_PASSWORD", self.cfg.password)
        try:
            self._client = ArangoClient(hosts=url)
            self._sys = self._client.db("_system", username=user, password=password)
            cursor = self._sys.aql.execute("RETURN 1")
            rows = list(cursor)
            if not rows or int(rows[0]) != 1:
                raise AdapterConnectionError(self.name, "AQL RETURN 1 smoke query failed")
            if not self._sys.has_database(self._db_name):
                self._sys.create_database(self._db_name)
            self._db = self._client.db(
                self._db_name, username=user, password=password
            )
        except AdapterConnectionError:
            self.close()
            raise
        except (ArangoError, Exception) as exc:
            self.close()
            raise AdapterConnectionError(
                self.name, "Failed to connect via python-arango", cause=exc
            ) from exc

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:  # noqa: BLE001
                pass
        self._client = None
        self._sys = None
        self._db = None

    def ping(self) -> bool:
        if self._sys is None:
            raise AdapterConnectionError(self.name, "Not connected; call connect() first")
        rows = list(self._sys.aql.execute("RETURN 1"))
        return bool(rows) and int(rows[0]) == 1

    def _db_req(self):
        if self._db is None:
            raise AdapterConnectionError(self.name, "Not connected; call connect() first")
        return self._db

    def reset(self) -> None:
        db = self._db_req()
        for name in ("FOLLOWS", "Person"):
            if db.has_collection(name):
                db.delete_collection(name)

    def create_schema(self) -> None:
        db = self._db_req()
        if not db.has_collection("Person"):
            db.create_collection("Person")
        if not db.has_collection("FOLLOWS"):
            db.create_collection("FOLLOWS", edge=True)

    def create_indexes(self) -> None:
        db = self._db_req()
        person = db.collection("Person")
        try:
            person.add_hash_index(fields=["id"], unique=True)
        except Exception:  # noqa: BLE001
            pass

    def load_nodes(self, rows: Sequence[dict[str, Any]]) -> int:
        db = self._db_req()
        col = db.collection("Person")
        total = 0
        batch: list[dict[str, Any]] = []
        for row in rows:
            nid = int(row["id"])
            batch.append({"_key": str(nid), "id": nid})
            if len(batch) >= self.batch_size:
                col.insert_many(batch, overwrite=True, silent=True)
                total += len(batch)
                batch = []
        if batch:
            col.insert_many(batch, overwrite=True, silent=True)
            total += len(batch)
        return total

    def load_relationships(self, rows: Sequence[dict[str, Any]]) -> int:
        db = self._db_req()
        edges = db.collection("FOLLOWS")
        total = 0
        batch: list[dict[str, Any]] = []
        for row in rows:
            s, e = int(row["start_id"]), int(row["end_id"])
            batch.append(
                {
                    "_from": f"Person/{s}",
                    "_to": f"Person/{e}",
                    "type": "FOLLOWS",
                }
            )
            if len(batch) >= self.batch_size:
                edges.insert_many(batch, overwrite=False, silent=True)
                total += len(batch)
                batch = []
        if batch:
            edges.insert_many(batch, overwrite=False, silent=True)
            total += len(batch)
        return total

    def query_1hop(self, start_id: int) -> int:
        db = self._db_req()
        aql = """
        FOR v IN 1..1 OUTBOUND CONCAT('Person/', TO_STRING(@id)) FOLLOWS
        COLLECT WITH COUNT INTO c
        RETURN c
        """
        rows = list(db.aql.execute(aql, bind_vars={"id": int(start_id)}))
        return int(rows[0]) if rows else 0

    def query_2hop(self, start_id: int) -> int:
        db = self._db_req()
        aql = """
        FOR v IN 2..2 OUTBOUND CONCAT('Person/', TO_STRING(@id)) FOLLOWS
        COLLECT WITH COUNT INTO c
        RETURN c
        """
        rows = list(db.aql.execute(aql, bind_vars={"id": int(start_id)}))
        return int(rows[0]) if rows else 0

    def query_3hop(self, start_id: int) -> int:
        db = self._db_req()
        aql = """
        FOR v IN 3..3 OUTBOUND CONCAT('Person/', TO_STRING(@id)) FOLLOWS
        COLLECT WITH COUNT INTO c
        RETURN c
        """
        rows = list(db.aql.execute(aql, bind_vars={"id": int(start_id)}))
        return int(rows[0]) if rows else 0

    def point_lookup(self, node_id: int) -> Any:
        db = self._db_req()
        doc = db.collection("Person").get(str(int(node_id)))
        return {"id": doc["id"]} if doc else None

    def filtered_lookup(self, lo: int, hi: int) -> int:
        db = self._db_req()
        aql = """
        FOR p IN Person
          FILTER p.id >= @lo AND p.id < @hi
          COLLECT WITH COUNT INTO c
          RETURN c
        """
        rows = list(db.aql.execute(aql, bind_vars={"lo": int(lo), "hi": int(hi)}))
        return int(rows[0]) if rows else 0

    def aggregation(self) -> int:
        db = self._db_req()
        aql = """
        FOR e IN FOLLOWS
          COLLECT WITH COUNT INTO c
          RETURN c
        """
        rows = list(db.aql.execute(aql))
        return int(rows[0]) if rows else 0

    def mixed_read(self, node_id: int) -> Any:
        return self.point_lookup(node_id)

    def mixed_write(self, src_id: int, dst_id: int) -> None:
        db = self._db_req()
        person = db.collection("Person")
        edges = db.collection("FOLLOWS")
        s, d = int(src_id), int(dst_id)
        if not person.has(str(s)):
            person.insert({"_key": str(s), "id": s}, overwrite=True)
        if not person.has(str(d)):
            person.insert({"_key": str(d), "id": d}, overwrite=True)
        edges.insert(
            {"_from": f"Person/{s}", "_to": f"Person/{d}", "type": "FOLLOWS"},
            overwrite=False,
        )

    def footprint(self) -> dict[str, Any]:
        return {
            "instance": "Docker (docker-compose.yml)",
            "vCPU": 0.5,
            "RAM": "256 MB (mem_limit target)",
            "source": "https://docs.arango.ai/ecosystem/drivers/python/",
            "stored_data_size": "not observable",
            "memory_usage": "not observable",
        }

    def load_method(self) -> str:
        return "ArangoDB document/edge batch import over HTTP"

    def indexed_properties(self) -> list[str]:
        return ["id"]
