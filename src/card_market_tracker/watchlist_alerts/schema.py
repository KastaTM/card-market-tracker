"""Frozen independent CMTY schema and literal SQLite catalog expectations."""

APPLICATION_ID = 0x434D5459
SCHEMA_VERSION = 1
OWNER = "card-market-tracker.watchlist-alert-outbox"

STATEMENTS = (
    "CREATE TABLE watchlist_alert_metadata (\n"
    "    singleton INTEGER PRIMARY KEY NOT NULL CHECK(singleton=1),\n"
    "    owner TEXT NOT NULL CHECK(owner='card-market-tracker.watchlist-alert-outbox'),\n"
    "    schema_version INTEGER NOT NULL CHECK(schema_version=1)\n"
    ") STRICT",
    "CREATE TABLE watchlist_alerts (\n"
    "    alert_id TEXT PRIMARY KEY NOT NULL CHECK(length(alert_id)=70 AND length(CAST(alert_id AS "
    "BLOB))=70 AND substr(alert_id,1,6)='walt1_' AND substr(alert_id,7) NOT GLOB '*[^0-9a-f]*'),\n"
    "    destination_key TEXT NOT NULL CHECK(length(destination_key) BETWEEN 1 AND 64 AND "
    "length(CAST(destination_key AS BLOB))=length(destination_key) AND "
    "substr(destination_key,1,1) GLOB '[a-z]' AND destination_key NOT GLOB '*[^a-z0-9_-]*'),\n"
    "    signal_id TEXT NOT NULL CHECK(length(signal_id)=70 AND length(CAST(signal_id AS "
    "BLOB))=70 AND substr(signal_id,1,6)='wsig1_' AND substr(signal_id,7) NOT GLOB "
    "'*[^0-9a-f]*'),\n"
    "    policy_version TEXT NOT NULL CHECK(policy_version='watchlist_synthetic_alert_v1'),\n"
    "    renderer_version INTEGER NOT NULL CHECK(renderer_version=1),\n"
    "    channel TEXT NOT NULL CHECK(channel='offline_preview'),\n"
    "    state TEXT NOT NULL CHECK(state='pending'),\n"
    "    intent_json TEXT NOT NULL CHECK(length(CAST(intent_json AS BLOB)) BETWEEN 2 AND 65536),\n"
    "    intent_sha256 TEXT NOT NULL CHECK(length(intent_sha256)=64 AND length(CAST(intent_sha256 "
    "AS BLOB))=64 AND intent_sha256 NOT GLOB '*[^0-9a-f]*'),\n"
    "    message_text TEXT NOT NULL CHECK(length(CAST(message_text AS BLOB)) BETWEEN 1 AND "
    "4096),\n"
    "    message_sha256 TEXT NOT NULL CHECK(length(message_sha256)=64 AND "
    "length(CAST(message_sha256 AS BLOB))=64 AND message_sha256 NOT GLOB '*[^0-9a-f]*'),\n"
    "    first_prepared_at TEXT NOT NULL CHECK(length(first_prepared_at)=27 AND "
    "length(CAST(first_prepared_at AS BLOB))=27),\n"
    "    UNIQUE(destination_key,signal_id)\n"
    ") STRICT",
    "CREATE TABLE watchlist_alert_evidence (\n"
    "    alert_id TEXT PRIMARY KEY NOT NULL CHECK(length(alert_id)=70 AND length(CAST(alert_id AS "
    "BLOB))=70 AND substr(alert_id,1,6)='walt1_' AND substr(alert_id,7) NOT GLOB '*[^0-9a-f]*'),\n"
    "    evidence_json TEXT NOT NULL CHECK(length(CAST(evidence_json AS BLOB)) BETWEEN 2 AND "
    "262144),\n"
    "    evidence_sha256 TEXT NOT NULL CHECK(length(evidence_sha256)=64 AND "
    "length(CAST(evidence_sha256 AS BLOB))=64 AND evidence_sha256 NOT GLOB '*[^0-9a-f]*'),\n"
    "    FOREIGN KEY(alert_id) REFERENCES watchlist_alerts(alert_id) ON DELETE RESTRICT\n"
    ") STRICT",
    "CREATE INDEX watchlist_alerts_by_destination ON watchlist_alerts(destination_key,alert_id)",
    "CREATE TRIGGER watchlist_alert_metadata_no_update BEFORE UPDATE ON watchlist_alert_metadata "
    "BEGIN SELECT RAISE(ABORT,'immutable_metadata'); END",
    "CREATE TRIGGER watchlist_alert_metadata_no_delete BEFORE DELETE ON watchlist_alert_metadata "
    "BEGIN SELECT RAISE(ABORT,'immutable_metadata'); END",
    "CREATE TRIGGER watchlist_alerts_no_update BEFORE UPDATE ON watchlist_alerts BEGIN SELECT "
    "RAISE(ABORT,'immutable_alert'); END",
    "CREATE TRIGGER watchlist_alerts_no_delete BEFORE DELETE ON watchlist_alerts BEGIN SELECT "
    "RAISE(ABORT,'immutable_alert'); END",
    "CREATE TRIGGER watchlist_alert_evidence_no_update BEFORE UPDATE ON watchlist_alert_evidence "
    "BEGIN SELECT RAISE(ABORT,'immutable_evidence'); END",
    "CREATE TRIGGER watchlist_alert_evidence_no_delete BEFORE DELETE ON watchlist_alert_evidence "
    "BEGIN SELECT RAISE(ABORT,'immutable_evidence'); END",
)


def expected_inventory() -> tuple[tuple[object, ...], ...]:
    """Return literal expectations; SQLite normalization never rewrites the freeze."""
    rows = (
        ("index", "sqlite_autoindex_watchlist_alert_evidence_1", "watchlist_alert_evidence", None),
        ("index", "sqlite_autoindex_watchlist_alerts_1", "watchlist_alerts", None),
        ("index", "sqlite_autoindex_watchlist_alerts_2", "watchlist_alerts", None),
        ("table", "watchlist_alert_metadata", "watchlist_alert_metadata", STATEMENTS[0]),
        ("table", "watchlist_alerts", "watchlist_alerts", STATEMENTS[1]),
        ("table", "watchlist_alert_evidence", "watchlist_alert_evidence", STATEMENTS[2]),
        ("index", "watchlist_alerts_by_destination", "watchlist_alerts", STATEMENTS[3]),
        (
            "trigger",
            "watchlist_alert_metadata_no_update",
            "watchlist_alert_metadata",
            STATEMENTS[4],
        ),
        (
            "trigger",
            "watchlist_alert_metadata_no_delete",
            "watchlist_alert_metadata",
            STATEMENTS[5],
        ),
        ("trigger", "watchlist_alerts_no_update", "watchlist_alerts", STATEMENTS[6]),
        ("trigger", "watchlist_alerts_no_delete", "watchlist_alerts", STATEMENTS[7]),
        (
            "trigger",
            "watchlist_alert_evidence_no_update",
            "watchlist_alert_evidence",
            STATEMENTS[8],
        ),
        (
            "trigger",
            "watchlist_alert_evidence_no_delete",
            "watchlist_alert_evidence",
            STATEMENTS[9],
        ),
    )
    return tuple(sorted(rows, key=lambda row: (row[0], row[1])))
