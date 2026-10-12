"""The single initial owned SQLite schema; no speculative migrations."""

import sqlite3
from functools import lru_cache

from card_market_tracker.catalog.validation import ERROR_CATEGORIES

APPLICATION_ID = 0x434D5431
SCHEMA_VERSION = 1
OWNER = "card-market-tracker"

_CATEGORIES = ",".join("'" + value + "'" for value in sorted(ERROR_CATEGORIES))
_CANDIDATES = "'missing_binding','unknown_variant','unknown_language'"

STATEMENTS = (
    """CREATE TABLE storage_metadata (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        owner TEXT NOT NULL CHECK (owner = 'card-market-tracker'),
        schema_version INTEGER NOT NULL CHECK (schema_version = 1)
    ) STRICT""",
    """CREATE TABLE entities (
        cmt_id TEXT PRIMARY KEY NOT NULL CHECK (length(cmt_id) = 36),
        kind TEXT NOT NULL CHECK (kind IN ('set','card','printing','sealed')),
        set_id TEXT REFERENCES entities(cmt_id),
        card_id TEXT REFERENCES entities(cmt_id),
        card_number TEXT CHECK (length(card_number) BETWEEN 1 AND 64),
        language TEXT CHECK (language IN ('es','en')),
        variant TEXT NOT NULL CHECK (variant IN ('normal','holo','reverse','unknown')),
        sealed_type TEXT
            CHECK (sealed_type IN ('booster_pack','box','bundle','collection','unknown')),
        CHECK (
            (kind = 'set' AND set_id IS NULL AND card_id IS NULL AND card_number IS NULL
                AND language IS NULL AND variant = 'unknown' AND sealed_type IS NULL)
            OR (kind = 'card' AND set_id IS NOT NULL AND card_id IS NULL
                AND card_number IS NOT NULL AND language IS NULL
                AND variant = 'unknown' AND sealed_type IS NULL)
            OR (kind = 'printing' AND set_id IS NULL AND card_id IS NOT NULL
                AND card_number IS NULL AND sealed_type IS NULL)
            OR (kind = 'sealed' AND card_id IS NULL AND card_number IS NULL
                AND variant = 'unknown' AND sealed_type IS NOT NULL)
        )
    ) STRICT""",
    "CREATE UNIQUE INDEX card_identity ON entities(set_id,card_number) WHERE kind='card'",
    """CREATE UNIQUE INDEX printing_identity
        ON entities(card_id,COALESCE(language,''),variant) WHERE kind='printing'""",
    """CREATE TRIGGER entity_parent_kinds BEFORE INSERT ON entities BEGIN
        SELECT CASE WHEN NEW.set_id IS NOT NULL AND
            COALESCE((SELECT kind FROM entities WHERE cmt_id=NEW.set_id),'') <> 'set'
            THEN RAISE(ABORT,'parent_kind') END;
        SELECT CASE WHEN NEW.card_id IS NOT NULL AND
            COALESCE((SELECT kind FROM entities WHERE cmt_id=NEW.card_id),'') <> 'card'
            THEN RAISE(ABORT,'parent_kind') END;
    END""",
    """CREATE TABLE batches (
        batch_id TEXT PRIMARY KEY NOT NULL CHECK (length(batch_id)=36),
        input_version INTEGER NOT NULL CHECK (input_version=1),
        resolver_version INTEGER NOT NULL CHECK (resolver_version=1),
        captured_at TEXT NOT NULL CHECK (length(captured_at)=27 AND substr(captured_at,-1)='Z'),
        first_persisted_at TEXT NOT NULL
            CHECK (length(first_persisted_at)=27 AND substr(first_persisted_at,-1)='Z'),
        fingerprint TEXT NOT NULL CHECK (length(fingerprint)=64),
        context_fingerprint TEXT NOT NULL CHECK (length(context_fingerprint)=64),
        input_count INTEGER NOT NULL CHECK (input_count BETWEEN 0 AND 1000),
        accepted_count INTEGER NOT NULL CHECK (accepted_count BETWEEN 0 AND 1000),
        candidate_count INTEGER NOT NULL CHECK (candidate_count BETWEEN 0 AND 1000),
        rejected_count INTEGER NOT NULL CHECK (rejected_count BETWEEN 0 AND 1000),
        result TEXT NOT NULL CHECK (result IN ('ok','empty','mixed')),
        CHECK (input_count=accepted_count+candidate_count+rejected_count),
        CHECK ((result='empty' AND input_count=0)
            OR (result='ok' AND input_count>0 AND input_count=accepted_count)
            OR (result='mixed' AND candidate_count+rejected_count>0))
    ) STRICT""",
    f"""CREATE TABLE records (
        batch_id TEXT NOT NULL REFERENCES batches(batch_id),
        record_index INTEGER NOT NULL CHECK (record_index BETWEEN 0 AND 999),
        status TEXT NOT NULL CHECK (status IN ('accepted','candidate','rejected')),
        category TEXT CHECK (category IN ({_CATEGORIES})),
        cmt_id TEXT REFERENCES entities(cmt_id),
        kind TEXT CHECK (kind IN ('set','card','sealed')),
        namespace TEXT CHECK (length(namespace) BETWEEN 1 AND 128),
        external_id TEXT CHECK (length(external_id) BETWEEN 1 AND 128),
        language TEXT CHECK (language IN ('es','en')),
        variant TEXT CHECK (variant IN ('normal','holo','reverse','unknown')),
        name TEXT CHECK (length(name) BETWEEN 1 AND 1024),
        set_namespace TEXT CHECK (length(set_namespace) BETWEEN 1 AND 128),
        set_external_id TEXT CHECK (length(set_external_id) BETWEEN 1 AND 128),
        set_language TEXT CHECK (set_language IN ('es','en')),
        card_number TEXT CHECK (length(card_number) BETWEEN 1 AND 64),
        release_date TEXT CHECK (length(release_date)=10),
        provider_updated_at TEXT
            CHECK (length(provider_updated_at)=27 AND substr(provider_updated_at,-1)='Z'),
        captured_at TEXT CHECK (length(captured_at)=27 AND substr(captured_at,-1)='Z'),
        provenance TEXT CHECK (provenance='synthetic'),
        PRIMARY KEY (batch_id,record_index),
        CHECK ((set_namespace IS NULL AND set_external_id IS NULL AND set_language IS NULL)
            OR (set_namespace IS NOT NULL AND set_external_id IS NOT NULL)),
        CHECK (kind IS NULL OR kind='card' OR card_number IS NULL),
        CHECK (kind IS NULL OR kind<>'card' OR
            (set_namespace IS NOT NULL AND card_number IS NOT NULL)),
        CHECK (kind IS NULL OR kind='card' OR variant='unknown'),
        CHECK (
            (status='rejected' AND category IS NOT NULL AND cmt_id IS NULL
                AND kind IS NULL AND namespace IS NULL AND external_id IS NULL
                AND language IS NULL AND variant IS NULL AND name IS NULL
                AND set_namespace IS NULL AND set_external_id IS NULL AND set_language IS NULL
                AND card_number IS NULL AND release_date IS NULL AND provider_updated_at IS NULL
                AND captured_at IS NULL AND provenance IS NULL)
            OR (status IN ('accepted','candidate') AND kind IS NOT NULL
                AND namespace IS NOT NULL AND external_id IS NOT NULL AND variant IS NOT NULL
                AND name IS NOT NULL AND captured_at IS NOT NULL
                AND provenance IS NOT NULL AND provenance='synthetic'
                AND ((status='accepted' AND category IS NULL AND cmt_id IS NOT NULL)
                    OR (status='candidate' AND category IS NOT NULL
                        AND category IN ({_CANDIDATES}) AND cmt_id IS NULL)))
        )
    ) STRICT""",
    """CREATE TRIGGER record_context BEFORE INSERT ON records BEGIN
        SELECT CASE WHEN NEW.captured_at IS NOT NULL AND
            NEW.captured_at <> (SELECT captured_at FROM batches WHERE batch_id=NEW.batch_id)
            THEN RAISE(ABORT,'capture_conflict') END;
        SELECT CASE WHEN NEW.status='accepted' AND
            COALESCE((SELECT kind FROM entities WHERE cmt_id=NEW.cmt_id),'') <>
                CASE WHEN NEW.kind='card' THEN 'printing' ELSE NEW.kind END
            THEN RAISE(ABORT,'target_kind') END;
        SELECT CASE WHEN NEW.status='accepted' AND NEW.kind IN ('card','sealed') AND
            (SELECT language FROM entities WHERE cmt_id=NEW.cmt_id) IS NOT NEW.language
            THEN RAISE(ABORT,'target_language') END;
        SELECT CASE WHEN NEW.status='accepted' AND NEW.kind='card' AND
            (SELECT variant FROM entities WHERE cmt_id=NEW.cmt_id) IS NOT NEW.variant
            THEN RAISE(ABORT,'target_variant') END;
        SELECT CASE WHEN NEW.record_index >=
            (SELECT input_count FROM batches WHERE batch_id=NEW.batch_id)
            THEN RAISE(ABORT,'record_index') END;
    END""",
    "CREATE INDEX record_order ON records(captured_at,batch_id,record_index)",
    "CREATE INDEX record_target ON records(cmt_id,captured_at,batch_id,record_index)",
    """CREATE INDEX candidate_context
        ON records(namespace,kind,external_id,language,variant,captured_at,batch_id,record_index)
        WHERE status='candidate'""",
)


def inventory(connection: sqlite3.Connection) -> tuple[tuple[str, str, str, str | None], ...]:
    """Exact owned objects, including SQLite-generated constraint indexes."""
    rows = connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"
    ).fetchall()
    return tuple((str(row[0]), str(row[1]), str(row[2]), row[3]) for row in rows)


@lru_cache(maxsize=1)
def expected_inventory() -> tuple[tuple[str, str, str, str | None], ...]:
    connection = sqlite3.connect(":memory:", autocommit=True)
    try:
        for statement in STATEMENTS:
            connection.execute(statement)
        return inventory(connection)
    finally:
        connection.close()
