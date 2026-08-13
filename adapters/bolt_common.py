"""Shared Bolt helpers for CognoDB, Neo4j Aura, and Memgraph (official neo4j driver)."""

from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from adapters.errors import AdapterConnectionError, require_value


def open_bolt_driver(
    *,
    platform: str,
    uri: str,
    user: str,
    password: str,
    require_password: bool = True,
) -> Any:
    require_value(platform, "URI", uri)
    if require_password:
        require_value(platform, "PASSWORD", password)

    # Memgraph default: no auth → empty user/password per official docs
    if user == "" and password == "":
        auth: Any = ("", "")
    else:
        auth = (user, password)

    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        driver.verify_connectivity()
        return driver
    except Neo4jError as exc:
        raise AdapterConnectionError(
            platform,
            f"Bolt connectivity failed for URI scheme/host from env (details omitted secrets)",
            cause=exc,
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise AdapterConnectionError(
            platform,
            "Failed to open Bolt driver / verify connectivity",
            cause=exc,
        ) from exc


def bolt_smoke_return_1(driver: Any, *, platform: str) -> bool:
    """Cypher equivalent of RETURN 1."""
    try:
        records, _summary, _keys = driver.execute_query("RETURN 1 AS n")
        if not records:
            raise AdapterConnectionError(platform, "RETURN 1 produced no records")
        value = records[0].data().get("n", records[0][0])
        return int(value) == 1
    except AdapterConnectionError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise AdapterConnectionError(platform, "Smoke query RETURN 1 failed", cause=exc) from exc


def close_bolt_driver(driver: Any | None) -> None:
    if driver is not None:
        driver.close()
