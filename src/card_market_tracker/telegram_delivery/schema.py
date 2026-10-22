"""Exact independent CMTD v1 schema: immutable claims and outcome history."""

import sqlite3
from functools import lru_cache

APPLICATION_ID = 0x434D5444
SCHEMA_VERSION = 1
OWNER = "card-market-tracker.telegram-delivery"

STATEMENTS = (
    """CREATE TABLE delivery_metadata (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        owner TEXT NOT NULL CHECK(owner='card-market-tracker.telegram-delivery'),
        schema_version INTEGER NOT NULL CHECK(schema_version=1),
        send_quarantined INTEGER NOT NULL CHECK(send_quarantined IN (0,1))
    ) STRICT""",
    """CREATE TABLE destinations (
        alias TEXT PRIMARY KEY NOT NULL CHECK(length(alias) BETWEEN 1 AND 64),
        provider TEXT NOT NULL CHECK(provider='telegram'),
        bot_id INTEGER NOT NULL CHECK(bot_id BETWEEN 1 AND 4503599627370495),
        chat_id INTEGER NOT NULL CHECK(chat_id BETWEEN 1 AND 4503599627370495),
        chat_type TEXT NOT NULL CHECK(chat_type='private'),
        operator_attested_owner INTEGER NOT NULL CHECK(operator_attested_owner=1),
        validated_at TEXT CHECK(validated_at IS NULL OR length(validated_at)=27),
        route_sha256 TEXT NOT NULL CHECK(length(route_sha256)=64)
    ) STRICT""",
    """CREATE TABLE deliveries (
        delivery_id TEXT PRIMARY KEY NOT NULL CHECK(length(delivery_id)=69),
        alert_id TEXT NOT NULL CHECK(length(alert_id)=69),
        event_id TEXT NOT NULL CHECK(length(event_id)=69),
        provider TEXT NOT NULL CHECK(provider='telegram'),
        alias TEXT NOT NULL REFERENCES destinations(alias) ON DELETE RESTRICT,
        comparison_id TEXT NOT NULL CHECK(length(comparison_id)=69),
        intent_sha256 TEXT NOT NULL CHECK(length(intent_sha256)=64),
        message_sha256 TEXT NOT NULL CHECK(length(message_sha256)=64),
        event_sha256 TEXT NOT NULL CHECK(length(event_sha256)=64),
        journal_content_sha256 TEXT NOT NULL CHECK(length(journal_content_sha256)=64),
        alert_content_sha256 TEXT NOT NULL CHECK(length(alert_content_sha256)=64),
        evidence_content_sha256 TEXT NOT NULL CHECK(length(evidence_content_sha256)=64),
        route_sha256 TEXT NOT NULL CHECK(length(route_sha256)=64),
        state TEXT NOT NULL CHECK(state IN
            ('ready','in_flight','retryable','confirmed','permanent_failure','uncertain')),
        attempt_count INTEGER NOT NULL CHECK(attempt_count BETWEEN 0 AND 3),
        current_attempt_id TEXT REFERENCES delivery_attempts(attempt_id) ON DELETE RESTRICT,
        not_before TEXT CHECK(not_before IS NULL OR length(not_before)=27),
        created_at TEXT NOT NULL CHECK(length(created_at)=27),
        updated_at TEXT NOT NULL CHECK(length(updated_at)=27),
        UNIQUE(provider,alert_id),
        UNIQUE(provider,event_id),
        CHECK((state='in_flight' AND current_attempt_id IS NOT NULL) OR
            (state!='in_flight' AND current_attempt_id IS NULL)),
        CHECK((state='retryable' AND not_before IS NOT NULL) OR
            (state!='retryable' AND not_before IS NULL)),
        CHECK((state='ready' AND attempt_count=0) OR (state!='ready' AND attempt_count>0))
    ) STRICT""",
    """CREATE TABLE delivery_attempts (
        attempt_id TEXT PRIMARY KEY NOT NULL CHECK(length(attempt_id)=69),
        delivery_id TEXT NOT NULL REFERENCES deliveries(delivery_id) ON DELETE RESTRICT,
        ordinal INTEGER NOT NULL CHECK(ordinal BETWEEN 1 AND 3),
        claimed_at TEXT NOT NULL CHECK(length(claimed_at)=27),
        UNIQUE(delivery_id,ordinal)
    ) STRICT""",
    """CREATE TABLE delivery_attempt_results (
        attempt_id TEXT PRIMARY KEY NOT NULL REFERENCES delivery_attempts(attempt_id)
            ON DELETE RESTRICT CHECK(length(attempt_id)=69),
        state TEXT NOT NULL CHECK(state IN
            ('retryable','confirmed','permanent_failure','uncertain')),
        completed_at TEXT NOT NULL CHECK(length(completed_at)=27),
        error_category TEXT CHECK(error_category IS NULL OR
            length(error_category) BETWEEN 1 AND 64),
        retry_after INTEGER CHECK(retry_after IS NULL OR retry_after BETWEEN 1 AND 86400),
        not_before TEXT CHECK(not_before IS NULL OR length(not_before)=27),
        message_id INTEGER CHECK(message_id IS NULL OR message_id>0),
        accepted_at INTEGER CHECK(accepted_at IS NULL OR accepted_at BETWEEN 1 AND 253402300799),
        bot_id INTEGER CHECK(bot_id IS NULL OR bot_id BETWEEN 1 AND 4503599627370495),
        chat_id INTEGER CHECK(chat_id IS NULL OR chat_id BETWEEN 1 AND 4503599627370495),
        CHECK((state='confirmed' AND error_category IS NULL AND message_id IS NOT NULL
            AND accepted_at IS NOT NULL AND bot_id IS NOT NULL AND chat_id IS NOT NULL) OR
            (state!='confirmed' AND error_category IS NOT NULL AND message_id IS NULL
            AND accepted_at IS NULL AND bot_id IS NULL AND chat_id IS NULL)),
        CHECK((state='retryable' AND retry_after IS NOT NULL AND not_before IS NOT NULL) OR
            (state!='retryable' AND retry_after IS NULL AND not_before IS NULL))
    ) STRICT""",
    "CREATE INDEX deliveries_by_state ON deliveries(state,delivery_id)",
)


@lru_cache(maxsize=1)
def expected_inventory() -> tuple[tuple[object, ...], ...]:
    """Derive normalized exact DDL and implicit indexes from our own constants."""
    db = sqlite3.connect(":memory:")
    try:
        for statement in STATEMENTS:
            db.execute(statement)
        return tuple(
            tuple(row)
            for row in db.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
            )
        )
    finally:
        db.close()
