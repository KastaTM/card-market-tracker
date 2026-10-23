"""Independent CMTW v1 watchlist schema and exact owned inventory."""

import sqlite3
from functools import lru_cache

APPLICATION_ID = 0x434D5457
SCHEMA_VERSION = 1
OWNER = "card-market-tracker.watchlist"

STATEMENTS = (
    """CREATE TABLE watchlist_metadata (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        owner TEXT NOT NULL CHECK(owner='card-market-tracker.watchlist'),
        schema_version INTEGER NOT NULL CHECK(schema_version=1)
    ) STRICT""",
    """CREATE TABLE watchlist_entries (
        watch_id TEXT PRIMARY KEY NOT NULL CHECK(length(watch_id)=69),
        cmt_id TEXT NOT NULL UNIQUE CHECK(length(cmt_id)=36),
        identity_json TEXT NOT NULL CHECK(length(CAST(identity_json AS BLOB)) BETWEEN 2 AND 65536),
        identity_digest TEXT NOT NULL CHECK(length(identity_digest)=64),
        current_revision INTEGER NOT NULL CHECK(current_revision BETWEEN 1 AND 2147483647),
        priority_rank INTEGER NOT NULL CHECK(priority_rank BETWEEN 0 AND 2),
        enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
        FOREIGN KEY(watch_id,current_revision) REFERENCES watchlist_revisions(watch_id,revision)
            DEFERRABLE INITIALLY DEFERRED
    ) STRICT""",
    """CREATE TABLE watchlist_revisions (
        watch_id TEXT NOT NULL REFERENCES watchlist_entries(watch_id),
        revision INTEGER NOT NULL CHECK(revision BETWEEN 1 AND 2147483647),
        entry_json TEXT NOT NULL CHECK(length(CAST(entry_json AS BLOB)) BETWEEN 2 AND 65536),
        action TEXT NOT NULL CHECK(action IN ('add','update','enable','disable')),
        request_token TEXT NOT NULL UNIQUE CHECK(length(request_token) BETWEEN 1 AND 128),
        PRIMARY KEY(watch_id,revision),
        FOREIGN KEY(request_token) REFERENCES watchlist_requests(request_token)
            DEFERRABLE INITIALLY DEFERRED
    ) STRICT""",
    """CREATE TABLE watchlist_requests (
        request_token TEXT PRIMARY KEY NOT NULL CHECK(length(request_token) BETWEEN 1 AND 128),
        command_json TEXT NOT NULL CHECK(length(CAST(command_json AS BLOB)) BETWEEN 2 AND 65536),
        command_digest TEXT NOT NULL CHECK(length(command_digest)=64),
        watch_id TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision BETWEEN 1 AND 2147483647),
        UNIQUE(watch_id,revision),
        FOREIGN KEY(watch_id,revision) REFERENCES watchlist_revisions(watch_id,revision)
    ) STRICT""",
    "CREATE INDEX watchlist_by_priority ON watchlist_entries(priority_rank,watch_id)",
    """CREATE TRIGGER watchlist_identity_immutable BEFORE UPDATE ON watchlist_entries
        WHEN NEW.watch_id!=OLD.watch_id OR NEW.cmt_id!=OLD.cmt_id
          OR NEW.identity_json!=OLD.identity_json OR NEW.identity_digest!=OLD.identity_digest
          OR NEW.current_revision!=OLD.current_revision+1
        BEGIN SELECT RAISE(ABORT,'immutable_identity'); END""",
    """CREATE TRIGGER watchlist_entries_no_delete BEFORE DELETE ON watchlist_entries
        BEGIN SELECT RAISE(ABORT,'immutable_entry'); END""",
    """CREATE TRIGGER watchlist_revision_no_update BEFORE UPDATE ON watchlist_revisions
        BEGIN SELECT RAISE(ABORT,'immutable_revision'); END""",
    """CREATE TRIGGER watchlist_revision_no_delete BEFORE DELETE ON watchlist_revisions
        BEGIN SELECT RAISE(ABORT,'immutable_revision'); END""",
    """CREATE TRIGGER watchlist_request_no_update BEFORE UPDATE ON watchlist_requests
        BEGIN SELECT RAISE(ABORT,'immutable_request'); END""",
    """CREATE TRIGGER watchlist_request_no_delete BEFORE DELETE ON watchlist_requests
        BEGIN SELECT RAISE(ABORT,'immutable_request'); END""",
)


@lru_cache(maxsize=1)
def expected_inventory() -> tuple[tuple[object, ...], ...]:
    """SQLite's normalized DDL includes implicit indexes and every owned trigger."""
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
