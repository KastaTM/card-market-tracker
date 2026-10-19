"""Exact journal-only SQLite identity and three-table schema, independent of captures."""

import sqlite3
from functools import lru_cache

APPLICATION_ID = 0x434D544A
SCHEMA_VERSION = 1
OWNER = "card-market-tracker.discovery-journal"

STATEMENTS = (
    """CREATE TABLE journal_metadata (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        owner TEXT NOT NULL CHECK(owner='card-market-tracker.discovery-journal'),
        schema_version INTEGER NOT NULL CHECK(schema_version=1)
    ) STRICT""",
    """CREATE TABLE comparisons (
        comparison_id TEXT PRIMARY KEY NOT NULL CHECK(length(comparison_id)=69),
        request_json TEXT NOT NULL CHECK(length(CAST(request_json AS BLOB)) BETWEEN 2 AND 1048576),
        result_json TEXT NOT NULL CHECK(length(CAST(result_json AS BLOB)) BETWEEN 2 AND 16777216),
        content_sha256 TEXT NOT NULL CHECK(length(content_sha256)=64),
        first_recorded_at TEXT NOT NULL CHECK(length(first_recorded_at)=27)
    ) STRICT""",
    """CREATE TABLE event_occurrences (
        comparison_id TEXT NOT NULL REFERENCES comparisons(comparison_id) ON DELETE RESTRICT,
        event_id TEXT NOT NULL CHECK(length(event_id)=69),
        ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 0 AND 999),
        event_json TEXT NOT NULL CHECK(length(CAST(event_json AS BLOB)) BETWEEN 2 AND 16777216),
        PRIMARY KEY(comparison_id,event_id), UNIQUE(comparison_id,ordinal)
    ) STRICT""",
    "CREATE INDEX occurrence_by_event ON event_occurrences(event_id,comparison_id)",
)


@lru_cache(maxsize=1)
def expected_inventory() -> tuple[tuple[object, ...], ...]:
    """Include implicit indexes and exact SQLite-normalized DDL in the inventory."""
    connection = sqlite3.connect(":memory:")
    try:
        for statement in STATEMENTS:
            connection.execute(statement)
        return tuple(
            tuple(row)
            for row in connection.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
            )
        )
    finally:
        connection.close()
