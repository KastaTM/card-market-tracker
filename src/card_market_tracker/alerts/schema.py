"""Exact independent CMTA SQLite outbox schema; no delivery or migration tables."""

import sqlite3
from functools import lru_cache

APPLICATION_ID = 0x434D5441
SCHEMA_VERSION = 1
OWNER = "card-market-tracker.alert-outbox"

STATEMENTS = (
    """CREATE TABLE outbox_metadata (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        owner TEXT NOT NULL CHECK(owner='card-market-tracker.alert-outbox'),
        schema_version INTEGER NOT NULL CHECK(schema_version=1)
    ) STRICT""",
    """CREATE TABLE alerts (
        alert_id TEXT PRIMARY KEY NOT NULL CHECK(length(alert_id)=69),
        destination_key TEXT NOT NULL CHECK(length(destination_key) BETWEEN 1 AND 64),
        event_id TEXT NOT NULL CHECK(length(event_id)=69),
        channel TEXT NOT NULL CHECK(channel='offline_preview'),
        policy_version TEXT NOT NULL CHECK(policy_version='discovery_reference_alert_v1'),
        renderer_version INTEGER NOT NULL CHECK(renderer_version=1),
        intent_json TEXT NOT NULL CHECK(length(CAST(intent_json AS BLOB)) BETWEEN 2 AND 65536),
        intent_sha256 TEXT NOT NULL CHECK(length(intent_sha256)=64),
        message_text TEXT NOT NULL CHECK(length(CAST(message_text AS BLOB)) BETWEEN 1 AND 4096),
        message_sha256 TEXT NOT NULL CHECK(length(message_sha256)=64),
        first_prepared_at TEXT NOT NULL CHECK(length(first_prepared_at)=27),
        state TEXT NOT NULL CHECK(state='pending'),
        UNIQUE(destination_key,event_id)
    ) STRICT""",
    """CREATE TABLE alert_evidence (
        alert_id TEXT NOT NULL REFERENCES alerts(alert_id) ON DELETE RESTRICT,
        comparison_id TEXT NOT NULL CHECK(length(comparison_id)=69),
        event_json TEXT NOT NULL CHECK(length(CAST(event_json AS BLOB)) BETWEEN 2 AND 16777216),
        journal_content_sha256 TEXT NOT NULL CHECK(length(journal_content_sha256)=64),
        event_sha256 TEXT NOT NULL CHECK(length(event_sha256)=64),
        PRIMARY KEY(alert_id,comparison_id)
    ) STRICT""",
    "CREATE INDEX evidence_by_comparison ON alert_evidence(comparison_id,alert_id)",
)


@lru_cache(maxsize=1)
def expected_inventory() -> tuple[tuple[object, ...], ...]:
    """Include exact normalized DDL and every implicit/explicit index."""
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
