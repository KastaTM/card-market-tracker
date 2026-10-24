"""Independent CMTQ v1 schema; exact SQL and object inventory are immutable."""

import sqlite3
from functools import lru_cache

APPLICATION_ID = 0x434D5451
SCHEMA_VERSION = 1
OWNER = "card-market-tracker.watchlist-journal"

STATEMENTS = (
    """CREATE TABLE wl_journal_metadata (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        owner TEXT NOT NULL CHECK(owner='card-market-tracker.watchlist-journal'),
        schema_version INTEGER NOT NULL CHECK(schema_version=1)
    ) STRICT""",
    """CREATE TABLE wl_journal_sequences (
        sequence_id TEXT PRIMARY KEY NOT NULL CHECK(length(sequence_id)=69),
        watch_id TEXT NOT NULL CHECK(length(watch_id)=69),
        revision INTEGER NOT NULL CHECK(revision BETWEEN 1 AND 2147483647),
        policy_version TEXT NOT NULL CHECK(policy_version='watchlist-rules-v1'),
        series_key TEXT NOT NULL CHECK(length(series_key) BETWEEN 1 AND 128),
        entry_json TEXT NOT NULL CHECK(length(CAST(entry_json AS BLOB)) BETWEEN 2 AND 65536),
        entry_digest TEXT NOT NULL CHECK(length(entry_digest)=64),
        head_eval_id TEXT NOT NULL CHECK(length(head_eval_id)=69),
        head_observed_at TEXT NOT NULL CHECK(length(head_observed_at) BETWEEN 20 AND 32),
        head_as_of TEXT NOT NULL CHECK(length(head_as_of) BETWEEN 20 AND 32),
        head_ordinal INTEGER NOT NULL CHECK(head_ordinal>=1),
        UNIQUE(watch_id,revision,policy_version,series_key),
        FOREIGN KEY(sequence_id,head_eval_id)
            REFERENCES wl_journal_evaluations(sequence_id,evaluation_id)
            DEFERRABLE INITIALLY DEFERRED
    ) STRICT""",
    """CREATE TABLE wl_journal_evaluations (
        evaluation_id TEXT PRIMARY KEY NOT NULL CHECK(length(evaluation_id)=69),
        sequence_id TEXT NOT NULL REFERENCES wl_journal_sequences(sequence_id),
        current_sample_id TEXT NOT NULL CHECK(length(current_sample_id) BETWEEN 1 AND 128),
        prior_eval_id TEXT CHECK(prior_eval_id IS NULL OR length(prior_eval_id)=69),
        snapshot_json TEXT NOT NULL CHECK(length(CAST(snapshot_json AS BLOB)) BETWEEN 2 AND 65536),
        result_json TEXT NOT NULL CHECK(length(CAST(result_json AS BLOB)) BETWEEN 2 AND 65536),
        observed_at TEXT NOT NULL CHECK(length(observed_at) BETWEEN 20 AND 32),
        as_of TEXT NOT NULL CHECK(length(as_of) BETWEEN 20 AND 32),
        persisted_at TEXT NOT NULL CHECK(length(persisted_at) BETWEEN 20 AND 32),
        ordinal INTEGER NOT NULL CHECK(ordinal>=1),
        UNIQUE(sequence_id,evaluation_id),
        UNIQUE(sequence_id,current_sample_id),
        UNIQUE(sequence_id,ordinal),
        FOREIGN KEY(sequence_id,prior_eval_id)
            REFERENCES wl_journal_evaluations(sequence_id,evaluation_id)
    ) STRICT""",
    """CREATE TABLE wl_journal_signals (
        signal_id TEXT PRIMARY KEY NOT NULL CHECK(length(signal_id)=70),
        sequence_id TEXT NOT NULL REFERENCES wl_journal_sequences(sequence_id),
        rule TEXT NOT NULL CHECK(rule IN ('price','restock')),
        from_eval_id TEXT NOT NULL CHECK(length(from_eval_id)=69),
        to_eval_id TEXT NOT NULL CHECK(length(to_eval_id)=69),
        body_json TEXT NOT NULL CHECK(length(CAST(body_json AS BLOB)) BETWEEN 2 AND 65536),
        UNIQUE(sequence_id,to_eval_id,rule),
        FOREIGN KEY(sequence_id,from_eval_id)
            REFERENCES wl_journal_evaluations(sequence_id,evaluation_id),
        FOREIGN KEY(sequence_id,to_eval_id)
            REFERENCES wl_journal_evaluations(sequence_id,evaluation_id)
    ) STRICT""",
    "CREATE INDEX wl_journal_sequences_by_watch "
    "ON wl_journal_sequences(watch_id,revision,sequence_id)",
    """CREATE INDEX wl_journal_evaluations_by_sequence
        ON wl_journal_evaluations(sequence_id,ordinal,evaluation_id)""",
    """CREATE INDEX wl_journal_signals_by_sequence
        ON wl_journal_signals(sequence_id,to_eval_id,rule,signal_id)""",
    """CREATE TRIGGER wl_journal_metadata_no_update BEFORE UPDATE ON wl_journal_metadata
        BEGIN SELECT RAISE(ABORT,'immutable_metadata'); END""",
    """CREATE TRIGGER wl_journal_metadata_no_delete BEFORE DELETE ON wl_journal_metadata
        BEGIN SELECT RAISE(ABORT,'immutable_metadata'); END""",
    """CREATE TRIGGER wl_journal_sequence_immutable BEFORE UPDATE ON wl_journal_sequences
        WHEN NEW.sequence_id!=OLD.sequence_id OR NEW.watch_id!=OLD.watch_id
          OR NEW.revision!=OLD.revision OR NEW.policy_version!=OLD.policy_version
          OR NEW.series_key!=OLD.series_key OR NEW.entry_json!=OLD.entry_json
          OR NEW.entry_digest!=OLD.entry_digest OR NEW.head_ordinal!=OLD.head_ordinal+1
          OR NEW.head_eval_id=OLD.head_eval_id
        BEGIN SELECT RAISE(ABORT,'immutable_sequence'); END""",
    """CREATE TRIGGER wl_journal_sequence_no_delete BEFORE DELETE ON wl_journal_sequences
        BEGIN SELECT RAISE(ABORT,'immutable_sequence'); END""",
    """CREATE TRIGGER wl_journal_evaluation_no_update BEFORE UPDATE ON wl_journal_evaluations
        BEGIN SELECT RAISE(ABORT,'immutable_evaluation'); END""",
    """CREATE TRIGGER wl_journal_evaluation_no_delete BEFORE DELETE ON wl_journal_evaluations
        BEGIN SELECT RAISE(ABORT,'immutable_evaluation'); END""",
    """CREATE TRIGGER wl_journal_signal_no_update BEFORE UPDATE ON wl_journal_signals
        BEGIN SELECT RAISE(ABORT,'immutable_signal'); END""",
    """CREATE TRIGGER wl_journal_signal_no_delete BEFORE DELETE ON wl_journal_signals
        BEGIN SELECT RAISE(ABORT,'immutable_signal'); END""",
)


@lru_cache(maxsize=1)
def expected_inventory() -> tuple[tuple[object, ...], ...]:
    """Derive SQLite normalization, including implicit indexes, independently of a file."""
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
