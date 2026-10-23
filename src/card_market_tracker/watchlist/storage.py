"""Separate offline watchlist, atomic immutable revisions and verified recovery."""

import base64
import hashlib
import json
import math
import os
import sqlite3
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import cast

from ..persistence import sqlite_repository as paths
from ..persistence.errors import PersistenceError
from . import schema, validation
from .errors import WatchlistError

DEFAULT_TIMEOUT = 2.0
MAX_PAGE_BYTES = 1024 * 1024
MAX_CELL_BYTES = 65536
MAX_LIMIT = 1000
_CONFIG = ("priority", "enabled", "target_price_minor", "restock_enabled", "max_age_seconds")
_RANK = {"high": 0, "normal": 1, "low": 2}


class Budget:
    """A single cooperative deadline includes validation, SQL and recovery IO."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
            raise WatchlistError("invalid_field")
        self.deadline = time.monotonic() + timeout

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise WatchlistError("storage_timeout")
        return remaining

    def progress(self) -> int:
        return int(time.monotonic() >= self.deadline)


def _path(value: Path, *, new: bool = False) -> Path:
    try:
        target = paths._checked_path(value)
        exists = paths._exists(target)
        if new and exists:
            raise WatchlistError("unsafe_destination")
        if not new and not exists:
            raise WatchlistError("storage_missing")
        paths._check_sidecars(target, new=new)
        return target
    except PersistenceError as error:
        raise WatchlistError(error.category) from None
    except OSError:
        raise WatchlistError("storage_io") from None


def _execute(
    db: sqlite3.Connection, budget: Budget, sql: str, values: tuple[object, ...] = ()
) -> sqlite3.Cursor:
    db.execute(f"PRAGMA busy_timeout={max(1, int(budget.remaining() * 1000))}")
    return db.execute(sql, values)


@contextmanager
def _connect(path: Path, budget: Budget, *, writable: bool = False) -> Iterator[sqlite3.Connection]:
    db: sqlite3.Connection | None = None
    try:
        target = _path(path)
        before = target.lstat()
        db = sqlite3.connect(
            target.as_uri() + ("?mode=rw" if writable else "?mode=ro"),
            uri=True,
            autocommit=True,
            timeout=budget.remaining(),
        )
        after = paths._unsafe_stat(target, file=True)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise WatchlistError("unsafe_destination")
        db.row_factory = sqlite3.Row
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 2 * MAX_CELL_BYTES)
        db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 65536)
        db.set_progress_handler(budget.progress, 1000)
        db.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        _execute(db, budget, "PRAGMA trusted_schema=OFF")
        _execute(db, budget, "PRAGMA foreign_keys=ON")
        if _execute(db, budget, "PRAGMA foreign_keys").fetchone()[0] != 1:
            raise WatchlistError("storage_schema")
        if not writable:
            _execute(db, budget, "PRAGMA query_only=ON")
        yield db
        budget.remaining()
    except PersistenceError as error:
        raise WatchlistError(error.category) from None
    except sqlite3.Error as error:
        code = getattr(error, "sqlite_errorcode", 0) & 0xFF
        category = {
            sqlite3.SQLITE_BUSY: "storage_locked",
            sqlite3.SQLITE_LOCKED: "storage_locked",
            sqlite3.SQLITE_CORRUPT: "storage_corrupt",
            sqlite3.SQLITE_NOTADB: "storage_corrupt",
            sqlite3.SQLITE_TOOBIG: "storage_corrupt",
            sqlite3.SQLITE_INTERRUPT: "storage_timeout",
            sqlite3.SQLITE_CONSTRAINT: "storage_corrupt",
        }.get(code, "storage_io")
        raise WatchlistError(category) from None
    except OSError:
        raise WatchlistError("storage_io") from None
    finally:
        if db is not None:
            db.close()


def _rollback(db: sqlite3.Connection) -> None:
    db.set_progress_handler(None, 0)
    with suppress(sqlite3.Error):
        db.execute("PRAGMA busy_timeout=0")
        if db.in_transaction:
            db.execute("ROLLBACK")


@contextmanager
def _transaction(db: sqlite3.Connection, budget: Budget, *, write: bool = False) -> Iterator[None]:
    _execute(db, budget, "BEGIN IMMEDIATE" if write else "BEGIN")
    try:
        yield
        if write:
            _execute(db, budget, "COMMIT")
    finally:
        _rollback(db)


def _text(column: str, maximum: int = MAX_CELL_BYTES) -> str:
    # All identifiers are internal constants. Bound hostile cells before materialization.
    return (
        f"CASE WHEN typeof({column})='text' AND "
        f"length(CAST({column} AS BLOB)) BETWEEN 1 AND {maximum} THEN {column} END"
    )


def _integer(column: str) -> str:
    return f"CASE WHEN typeof({column})='integer' THEN {column} END"


def _schema(db: sqlite3.Connection, budget: Budget) -> None:
    if (
        _execute(db, budget, "PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
        or _execute(db, budget, "PRAGMA user_version").fetchone()[0] != schema.SCHEMA_VERSION
        or _execute(db, budget, "PRAGMA journal_mode").fetchone()[0] != "delete"
    ):
        raise WatchlistError("storage_schema")
    expected = schema.expected_inventory()
    query = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(_text(column, 32768) for column in ("type", "name", "tbl_name"))
        + ",CASE WHEN sql IS NULL THEN NULL ELSE "
        + _text("sql", 32768)
        + " END FROM sqlite_master ORDER BY type,name LIMIT ?",
        (len(expected) + 1,),
    )
    if tuple(tuple(row) for row in query) != expected:
        raise WatchlistError("storage_schema")
    rows = _execute(
        db,
        budget,
        "SELECT "
        + _integer("singleton")
        + ","
        + _text("owner", 128)
        + ","
        + _integer("schema_version")
        + " FROM watchlist_metadata LIMIT 2",
    )
    if [tuple(row) for row in rows] != [(1, schema.OWNER, schema.SCHEMA_VERSION)]:
        raise WatchlistError("storage_schema")


def _decode(raw: object, budget: Budget) -> object:
    from ..discovery.journal_errors import JournalError
    from ..discovery.journal_validation import decode_json

    if type(raw) is not str:
        raise WatchlistError("storage_corrupt")
    try:
        return decode_json(raw, maximum=MAX_CELL_BYTES, check=budget.remaining)
    except JournalError as error:
        category = "storage_timeout" if error.category == "storage_timeout" else "storage_corrupt"
        raise WatchlistError(category) from None


def _canonical(value: object, maximum: int = MAX_CELL_BYTES) -> str:
    raw = validation.canonical(value)
    if len(raw) > maximum:
        raise WatchlistError("input_limit")
    return raw


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _wid(cmt_id: str) -> str:
    return "wlt1_" + _digest("CMT_WATCHLIST_V1\0" + cmt_id)


def _config(entry: dict[str, object]) -> dict[str, object]:
    return {key: entry[key] for key in _CONFIG}


def _entry_row(
    db: sqlite3.Connection, budget: Budget, wid: str, revision: int
) -> tuple[dict[str, object], str, str] | None:
    row = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(_text(column) for column in ("entry_json", "action", "request_token"))
        + " FROM watchlist_revisions WHERE watch_id=? AND revision=?",
        (wid, revision),
    ).fetchone()
    if row is None:
        return None
    try:
        entry = validation.parse_entry(_decode(row[0], budget))
        action, request_token = row[1], validation.token(row[2])
        if (
            entry["watch_id"] != wid
            or entry["revision"] != revision
            or _canonical(entry) != row[0]
            or action not in ("add", "update", "enable", "disable")
        ):
            raise WatchlistError("storage_corrupt")
        return entry, action, request_token
    except WatchlistError as error:
        if error.category == "storage_timeout":
            raise
        raise WatchlistError("storage_corrupt") from None


def _current(db: sqlite3.Connection, budget: Budget, wid: str) -> dict[str, object] | None:
    row = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(_text(column) for column in ("cmt_id", "identity_json", "identity_digest"))
        + ","
        + ",".join(_integer(column) for column in ("current_revision", "priority_rank", "enabled"))
        + " FROM watchlist_entries WHERE watch_id=?",
        (wid,),
    ).fetchone()
    if row is None:
        return None
    if type(row[3]) is not int or not 1 <= row[3] <= 2147483647:
        raise WatchlistError("storage_corrupt")
    revision_row = _entry_row(db, budget, wid, row[3])
    if revision_row is None:
        raise WatchlistError("storage_corrupt")
    entry = revision_row[0]
    if (
        entry["cmt_id"] != row[0]
        or _canonical(entry["canonical_identity"]) != row[1]
        or entry["identity_digest"] != row[2]
        or _RANK[cast(str, entry["priority"])] != row[4]
        or int(cast(bool, entry["enabled"])) != row[5]
    ):
        raise WatchlistError("storage_corrupt")
    return entry


def _command(action: str, entry: dict[str, object], expected_revision: int) -> dict[str, object]:
    return {
        "version": 1,
        "action": action,
        "cmt_id": entry["cmt_id"],
        "watch_id": entry["watch_id"],
        "canonical_identity": entry["canonical_identity"],
        "identity_digest": entry["identity_digest"],
        "expected_revision": expected_revision,
        "config": _config(entry),
    }


def _verify(db: sqlite3.Connection, budget: Budget) -> dict[str, int]:
    _schema(db, budget)
    result = _execute(db, budget, "PRAGMA integrity_check(1)").fetchone()
    if result is None or result[0] != "ok":
        raise WatchlistError("storage_corrupt")
    if _execute(db, budget, "PRAGMA foreign_key_check").fetchone() is not None:
        raise WatchlistError("storage_corrupt")
    entries = revisions = requests = 0
    for row in _execute(db, budget, "SELECT " + _text("watch_id", 69) + " FROM watchlist_entries"):
        budget.remaining()
        try:
            wid = validation.validate_watch_id(row[0])
        except WatchlistError:
            raise WatchlistError("storage_corrupt") from None
        current = _current(db, budget, wid)
        if current is None:
            raise WatchlistError("storage_corrupt")
        previous: dict[str, object] | None = None
        count = 0
        for revision_row in _execute(
            db,
            budget,
            "SELECT "
            + _integer("revision")
            + " FROM watchlist_revisions WHERE watch_id=? ORDER BY revision",
            (wid,),
        ):
            budget.remaining()
            count += 1
            if revision_row[0] != count:
                raise WatchlistError("storage_corrupt")
            loaded = _entry_row(db, budget, wid, count)
            if loaded is None:
                raise WatchlistError("storage_corrupt")
            entry, action, request_token = loaded
            if (
                entry["cmt_id"] != current["cmt_id"]
                or entry["canonical_identity"] != current["canonical_identity"]
                or entry["identity_digest"] != current["identity_digest"]
                or (count == 1) != (action == "add")
            ):
                raise WatchlistError("storage_corrupt")
            if action in ("enable", "disable"):
                if previous is None:
                    raise WatchlistError("storage_corrupt")
                expected_config = {**_config(previous), "enabled": action == "enable"}
                if _config(entry) != expected_config:
                    raise WatchlistError("storage_corrupt")
            request = _execute(
                db,
                budget,
                "SELECT "
                + _text("command_json")
                + ","
                + _text("command_digest", 64)
                + ","
                + _text("watch_id", 69)
                + ","
                + _integer("revision")
                + " FROM watchlist_requests WHERE request_token=?",
                (request_token,),
            ).fetchone()
            expected_command = _canonical(_command(action, entry, count - 1))
            if (
                request is None
                or request[0] != expected_command
                or request[1] != _digest(expected_command)
                or request[2] != wid
                or request[3] != count
            ):
                raise WatchlistError("storage_corrupt")
            previous = entry
        if count != current["revision"]:
            raise WatchlistError("storage_corrupt")
        entries += 1
        revisions += count
        requests += count
    # Detect disconnected rows as well as missing links; FK alone does not prove bijection.
    for table, expected in (("watchlist_revisions", revisions), ("watchlist_requests", requests)):
        if _execute(db, budget, "SELECT COUNT(*) FROM " + table).fetchone()[0] != expected:
            raise WatchlistError("storage_corrupt")
    return {"entries": entries, "revisions": revisions, "requests": requests}


def write(
    path: Path,
    *,
    action: str,
    manifest: object,
    cmt_id: str,
    config: object,
    expected_revision: int,
    request_token: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    """Reparse full curated input, then commit current, history and replay as one unit."""
    budget = Budget(timeout)
    if type(action) is not str or action not in ("add", "update", "enable", "disable"):
        raise WatchlistError("invalid_field")
    expected = validation.validate_revision(expected_revision, allow_zero=True)
    if (action == "add") != (expected == 0):
        raise WatchlistError("invalid_field")
    request_token = validation.token(request_token)
    identity = validation.identity_projection(manifest, cmt_id)
    identity_json = _canonical(identity)
    identity_digest = _digest(identity_json)
    wid = _wid(cmt_id)
    supplied_config = None if action in ("enable", "disable") else validation.parse_config(config)
    if action in ("enable", "disable") and config is not None:
        raise WatchlistError("invalid_field")
    budget.remaining()
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _verify(db, budget)
            current = _current(db, budget, wid)
            if current is not None and current["canonical_identity"] != identity:
                raise WatchlistError("identity_conflict")
            if supplied_config is None:
                prior = _entry_row(db, budget, wid, expected)
                if prior is None:
                    raise WatchlistError(
                        "revision_conflict" if current is not None else "not_found"
                    )
                effective = {**_config(prior[0]), "enabled": action == "enable"}
            else:
                effective = supplied_config
            entry = validation.parse_entry(
                {
                    "version": 1,
                    "watch_id": wid,
                    "cmt_id": cmt_id,
                    "canonical_identity": identity,
                    "identity_digest": identity_digest,
                    **effective,
                    "revision": expected + 1,
                }
            )
            command_json = _canonical(_command(action, entry, expected))
            previous = _execute(
                db,
                budget,
                "SELECT "
                + _text("command_json")
                + ","
                + _text("watch_id", 69)
                + ","
                + _integer("revision")
                + " FROM watchlist_requests WHERE request_token=?",
                (request_token,),
            ).fetchone()
            if previous is not None:
                if previous[0] != command_json:
                    raise WatchlistError("replay_conflict")
                original = _entry_row(db, budget, cast(str, previous[1]), cast(int, previous[2]))
                if original is None:
                    raise WatchlistError("storage_corrupt")
                return {
                    "version": 1,
                    "operation": action,
                    "result": "ok",
                    "action": action,
                    "entry": original[0],
                    "replayed": True,
                }
            if action == "add":
                if current is not None:
                    raise WatchlistError("already_exists")
                _execute(
                    db,
                    budget,
                    "INSERT INTO watchlist_entries VALUES (?,?,?,?,?,?,?)",
                    (
                        wid,
                        cmt_id,
                        identity_json,
                        identity_digest,
                        1,
                        _RANK[cast(str, effective["priority"])],
                        int(cast(bool, effective["enabled"])),
                    ),
                )
            else:
                if current is None:
                    raise WatchlistError("not_found")
                if current["revision"] != expected:
                    raise WatchlistError("revision_conflict")
            _execute(
                db,
                budget,
                "INSERT INTO watchlist_revisions VALUES (?,?,?,?,?)",
                (
                    wid,
                    expected + 1,
                    _canonical(entry),
                    action,
                    request_token,
                ),
            )
            _execute(
                db,
                budget,
                "INSERT INTO watchlist_requests VALUES (?,?,?,?,?)",
                (
                    request_token,
                    command_json,
                    _digest(command_json),
                    wid,
                    expected + 1,
                ),
            )
            if action != "add":
                changed = _execute(
                    db,
                    budget,
                    "UPDATE watchlist_entries SET current_revision=?,priority_rank=?,enabled=? "
                    "WHERE watch_id=? AND current_revision=?",
                    (
                        expected + 1,
                        _RANK[cast(str, effective["priority"])],
                        int(cast(bool, effective["enabled"])),
                        wid,
                        expected,
                    ),
                )
                if changed.rowcount != 1:
                    raise WatchlistError("revision_conflict")
    return {
        "version": 1,
        "operation": action,
        "result": "ok",
        "action": action,
        "entry": entry,
        "replayed": False,
    }


def get(
    path: Path, watch_id: str, *, revision: int | None = None, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    budget = Budget(timeout)
    wid = validation.validate_watch_id(watch_id)
    selected = None if revision is None else validation.validate_revision(revision)
    with _connect(path, budget) as db, _transaction(db, budget):
        _verify(db, budget)
        if selected is None:
            entry = _current(db, budget, wid)
        else:
            row = _entry_row(db, budget, wid, selected)
            entry = None if row is None else row[0]
        if entry is None:
            raise WatchlistError("not_found")
    return {"version": 1, "operation": "get", "result": "ok", "entry": entry}


def verify(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    with _connect(path, budget) as db, _transaction(db, budget):
        counts = _verify(db, budget)
    return {"version": 1, "operation": "verify", "result": "ok", "counts": counts}


def _cursor(value: object, binding: dict[str, object]) -> object:
    if value is None:
        return None
    if type(value) is not str or not 1 <= len(value) <= 2048:
        raise WatchlistError("invalid_field")
    try:
        raw = base64.b64decode(value, altchars=b"-_", validate=True).decode("ascii")
        decoded: object = json.loads(raw)
        if type(decoded) is not dict:
            raise ValueError
        data = cast(dict[str, object], decoded)
        if set(data) != {"binding", "last"} or data["binding"] != binding:
            raise ValueError
        if _encode_cursor(binding, data["last"]) != value:
            raise ValueError
        return data["last"]
    except (ValueError, UnicodeError, RecursionError):
        raise WatchlistError("invalid_field") from None


def _encode_cursor(binding: dict[str, object], last: object) -> str:
    return base64.urlsafe_b64encode(
        _canonical({"binding": binding, "last": last}).encode()
    ).decode()


def _page_limit(limit: int) -> int:
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise WatchlistError("invalid_field")
    return limit


def list_entries(
    path: Path,
    *,
    priority: str | None = None,
    enabled: bool | None = None,
    cursor: str | None = None,
    limit: int = 100,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    size = _page_limit(limit)
    if priority is not None and (type(priority) is not str or priority not in _RANK):
        raise WatchlistError("invalid_field")
    if enabled is not None and type(enabled) is not bool:
        raise WatchlistError("invalid_field")
    binding: dict[str, object] = {
        "version": 1,
        "operation": "list",
        "priority": priority,
        "enabled": enabled,
    }
    marker = _cursor(cursor, binding)
    rank, wid = -1, ""
    if marker is not None:
        if type(marker) is not list or len(marker) != 2:
            raise WatchlistError("invalid_field")
        rank, wid = marker
        if type(rank) is not int or not 0 <= rank <= 2:
            raise WatchlistError("invalid_field")
        wid = validation.validate_watch_id(wid)
    parameters: tuple[object, ...] = (rank, rank, wid)
    sql = "SELECT " + _text("watch_id", 69) + "," + _integer("priority_rank")
    sql += " FROM watchlist_entries WHERE (priority_rank>? OR (priority_rank=? AND watch_id>?))"
    if priority is not None:
        sql += " AND priority_rank=?"
        parameters += (_RANK[priority],)
    if enabled is not None:
        sql += " AND enabled=?"
        parameters += (int(enabled),)
    sql += " ORDER BY priority_rank,watch_id LIMIT ?"
    parameters += (size + 1,)
    items: list[dict[str, object]] = []
    last: object = None
    next_cursor: str | None = None
    with _connect(path, budget) as db, _transaction(db, budget):
        _verify(db, budget)
        for row in _execute(db, budget, sql, parameters):
            budget.remaining()
            entry = _current(db, budget, cast(str, row[0]))
            if entry is None:
                raise WatchlistError("storage_corrupt")
            if len(items) == size:
                next_cursor = _encode_cursor(binding, last)
                break
            candidate = items + [entry]
            response: dict[str, object] = {
                "version": 1,
                "operation": "list",
                "result": "ok",
                "entries": candidate,
                "next_cursor": _encode_cursor(binding, [row[1], row[0]]),
            }
            if len(json.dumps(response, ensure_ascii=True, separators=(",", ":"))) > MAX_PAGE_BYTES:
                if not items:
                    raise WatchlistError("input_limit")
                next_cursor = _encode_cursor(binding, last)
                break
            items.append(entry)
            last = [row[1], row[0]]
    return {
        "version": 1,
        "operation": "list",
        "result": "ok",
        "entries": items,
        "next_cursor": next_cursor,
    }


def history(
    path: Path,
    watch_id: str,
    *,
    cursor: str | None = None,
    limit: int = 100,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    wid = validation.validate_watch_id(watch_id)
    size = _page_limit(limit)
    binding: dict[str, object] = {"version": 1, "operation": "history", "watch_id": wid}
    marker = _cursor(cursor, binding)
    last_revision = 0 if marker is None else validation.validate_revision(marker)
    items: list[dict[str, object]] = []
    next_cursor: str | None = None
    with _connect(path, budget) as db, _transaction(db, budget):
        _verify(db, budget)
        if _current(db, budget, wid) is None:
            raise WatchlistError("not_found")
        for row in _execute(
            db,
            budget,
            "SELECT "
            + _integer("revision")
            + " FROM watchlist_revisions WHERE watch_id=? AND revision>? ORDER BY revision LIMIT ?",
            (wid, last_revision, size + 1),
        ):
            budget.remaining()
            if len(items) == size:
                next_cursor = _encode_cursor(binding, last_revision)
                break
            loaded = _entry_row(db, budget, wid, cast(int, row[0]))
            if loaded is None:
                raise WatchlistError("storage_corrupt")
            entry, action, request_token = loaded
            item: dict[str, object] = {**entry, "action": action, "request_token": request_token}
            response: dict[str, object] = {
                "version": 1,
                "operation": "history",
                "result": "ok",
                "entries": items + [item],
                "next_cursor": _encode_cursor(binding, row[0]),
            }
            if len(json.dumps(response, ensure_ascii=True, separators=(",", ":"))) > MAX_PAGE_BYTES:
                if not items:
                    raise WatchlistError("input_limit")
                next_cursor = _encode_cursor(binding, last_revision)
                break
            items.append(item)
            last_revision = cast(int, row[0])
    return {
        "version": 1,
        "operation": "history",
        "result": "ok",
        "entries": items,
        "next_cursor": next_cursor,
    }


def _cleanup_reserved(path: Path, identity: tuple[int, int]) -> None:
    """Only our inode may be removed, and SQLite recovery evidence is retained."""
    with suppress(OSError, PersistenceError):
        information = paths._unsafe_stat(path, file=True)
        if (information.st_dev, information.st_ino) != identity:
            return
        if any(paths._exists(sidecar) for sidecar in paths._sidecars(path)):
            return
        path.unlink()


def initialize(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    target = _path(path, new=True)
    identity: tuple[int, int] | None = None
    completed = False
    try:
        identity = paths._reserve(target)
        with _connect(target, budget, writable=True) as db:
            information = target.lstat()
            if (information.st_dev, information.st_ino) != identity:
                raise WatchlistError("unsafe_destination")
            _execute(db, budget, "PRAGMA synchronous=FULL")
            with _transaction(db, budget, write=True):
                for statement in schema.STATEMENTS:
                    _execute(db, budget, statement)
                _execute(
                    db,
                    budget,
                    "INSERT INTO watchlist_metadata VALUES (?,?,?)",
                    (1, schema.OWNER, 1),
                )
                _execute(db, budget, f"PRAGMA application_id={schema.APPLICATION_ID}")
                _execute(db, budget, "PRAGMA user_version=1")
                _verify(db, budget)
        completed = True
        return {"version": 1, "operation": "init", "result": "ok", "schema_version": 1}
    except PersistenceError as error:
        raise WatchlistError(error.category) from None
    except OSError:
        raise WatchlistError("storage_io") from None
    finally:
        if not completed and identity is not None:
            _cleanup_reserved(target, identity)


def _publish(provisional: Path, destination: Path, identity: tuple[int, int]) -> None:
    """Expose only a verified complete file, atomically and without replacement."""
    target = _path(destination, new=True)
    information = paths._unsafe_stat(provisional, file=True)
    if (information.st_dev, information.st_ino) != identity:
        raise WatchlistError("unsafe_destination")
    if any(paths._exists(sidecar) for sidecar in paths._sidecars(provisional)):
        raise WatchlistError("unsafe_destination")
    # link() has exclusive create semantics on both supported operating systems.
    # Trusted directory ownership is required, as with every earlier storage owner.
    try:
        os.link(provisional, target)
    except FileExistsError:
        raise WatchlistError("unsafe_destination") from None
    provisional.unlink()


def _copy(source: Path, destination: Path, operation: str, timeout: float) -> dict[str, object]:
    budget = Budget(timeout)
    provisional: Path | None = None
    identity: tuple[int, int] | None = None
    completed = False
    try:
        target = _path(destination, new=True)
        with _connect(source, budget) as reader, _transaction(reader, budget):
            _verify(reader, budget)
            provisional = target.parent / (".cmt-watchlist-" + uuid.uuid4().hex + ".tmp")
            _path(provisional, new=True)
            identity = paths._reserve(provisional)
            with _connect(provisional, budget, writable=True) as writer:
                information = provisional.lstat()
                if (information.st_dev, information.st_ino) != identity:
                    raise WatchlistError("unsafe_destination")
                _execute(writer, budget, "PRAGMA synchronous=FULL")
                reader.execute("PRAGMA busy_timeout=0")
                writer.execute("PRAGMA busy_timeout=0")

                def progress(status: int, remaining: int, total: int) -> None:
                    budget.remaining()

                reader.backup(writer, pages=32, progress=progress, sleep=0.01)
                with _transaction(writer, budget):
                    counts = _verify(writer, budget)
        with _connect(provisional, budget) as reopened, _transaction(reopened, budget):
            if _verify(reopened, budget) != counts:
                raise WatchlistError("storage_corrupt")
        # fsync the complete verified inode before publishing its destination name.
        with provisional.open("r+b") as stream:
            os.fsync(stream.fileno())
        budget.remaining()
        _publish(provisional, target, identity)
        completed = True
        return {"version": 1, "operation": operation, "result": "ok", "counts": counts}
    except PersistenceError as error:
        raise WatchlistError(error.category) from None
    except OSError:
        raise WatchlistError("storage_io") from None
    finally:
        if not completed and identity is not None and provisional is not None:
            _cleanup_reserved(provisional, identity)


def backup(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "backup", timeout)


def restore(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "restore", timeout)
