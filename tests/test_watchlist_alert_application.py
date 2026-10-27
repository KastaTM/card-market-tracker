"""Author tests for original admission, transient authority, replay and recompute."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_watchlist_alert_domain import evidence
from test_watchlist_alert_source import sources

from card_market_tracker.watchlist import application as watchlist_app
from card_market_tracker.watchlist_alerts import application as app
from card_market_tracker.watchlist_alerts import policy, storage
from card_market_tracker.watchlist_alerts.errors import OutboxError
from card_market_tracker.watchlist_journal import storage as journal_storage


@pytest.mark.parametrize(
    "bad",
    [
        "dict",
        "counterfeit",
        "copy",
        "deepcopy",
        "content",
        "budget",
        "authority",
        "unicode",
        "oversize",
        "used_bool",
        "content_type",
    ],
)
def test_receipt_rejects_unsupported_ordinary_callers_before_writer(
    bad: str, tmp_path: Path
) -> None:
    budget = journal_storage.Budget()
    content = policy.prepare(evidence(), "local-preview")
    receipt: Any = app._issue(content, budget)
    if bad == "dict":
        receipt = content
    elif bad == "counterfeit":
        receipt = app._Receipt(receipt.content_json)
    elif bad == "copy":
        receipt = copy.copy(receipt)
    elif bad == "deepcopy":
        receipt = copy.deepcopy(receipt)
    elif bad == "content":
        object.__setattr__(receipt, "content_json", receipt.content_json + " ")
    elif bad == "budget":
        budget = journal_storage.Budget()
    elif bad == "authority":
        object.__setattr__(receipt, "_authority", (object(), id(receipt), "0" * 64, budget))
    elif bad == "unicode":
        object.__setattr__(receipt, "content_json", "é")
    elif bad == "oversize":
        object.__setattr__(receipt, "content_json", "x" * 1048577)
    elif bad == "used_bool":
        object.__setattr__(receipt, "_used", 0)
    elif bad == "content_type":
        object.__setattr__(receipt, "content_json", None)
    destination = tmp_path / "must-not-open.sqlite"
    with pytest.raises(OutboxError, match="unsupported_evidence"):
        storage._enqueue_verified(destination, receipt, budget)
    assert not destination.exists()


def test_receipt_one_use_and_expired_original_deadline() -> None:
    budget = journal_storage.Budget()
    row = policy.prepare(evidence(), "local-preview")
    receipt = app._issue(row, budget)
    assert app._consume_receipt(receipt, budget) == row
    with pytest.raises(OutboxError, match="unsupported_evidence"):
        app._consume_receipt(receipt, budget)
    receipt = app._issue(row, budget)
    budget.deadline = 0
    with pytest.raises(OutboxError, match="storage_timeout"):
        app._consume_receipt(receipt, budget)
    with pytest.raises(OutboxError, match="unsupported_evidence"):
        app._consume_receipt(receipt, journal_storage.Budget())


def test_original_pipeline_replay_recompute_and_local_only_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    watchlist, journal, manifest, watch_id, points = sources(tmp_path)
    outbox = tmp_path / "outbox.sqlite"
    storage.initialize(outbox)
    origin_before = watchlist.read_bytes(), journal.read_bytes()
    signal = points[-1]["signal_ids"][0]
    first = app.enqueue(outbox, watchlist, journal, manifest, signal, "local-preview")
    assert first["result"] == "recorded"
    key = first["alert_id"]
    alert = storage.get(outbox, key)["alert"]
    initial_bytes = outbox.read_bytes()
    assert (
        app.enqueue(outbox, watchlist, journal, manifest, signal, "local-preview")["result"]
        == "replayed"
    )
    assert outbox.read_bytes() == initial_bytes
    assert storage.get(outbox, key)["alert"] == alert
    assert app.recompute(outbox, watchlist, journal, manifest, key)["level"] == "origin-recompute"
    assert (watchlist.read_bytes(), journal.read_bytes()) == origin_before
    assert storage.verify(outbox)["counts"] == {"alerts": 1, "evidence": 1}

    # New preferences do not reinterpret this historical simulation or its bytes.
    watchlist_app.update(
        watchlist,
        manifest,
        watch_id,
        {"target_price_minor": 500},
        expected_revision=1,
        request_token="new",
    )
    assert (
        app.enqueue(outbox, watchlist, journal, manifest, signal, "local-preview")["result"]
        == "replayed"
    )
    assert outbox.read_bytes() == initial_bytes

    # Source disappearance does not grant replay authority from a healthy local ID.
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(OutboxError, match="storage_missing"):
        app.enqueue(outbox, watchlist, missing, manifest, signal, "local-preview")
    assert storage.preview(outbox, key)["message_text"] == alert["message_text"]
    assert outbox.read_bytes() == initial_bytes


@pytest.mark.parametrize("invalid", ["unrelated", "identity", "parsed", "extra"])
def test_full_manifest_invalid_on_replay_leaves_outbox_unchanged(
    tmp_path: Path, invalid: str
) -> None:
    from card_market_tracker.catalog.manifest import parse_manifest

    watchlist, journal, manifest, _, points = sources(tmp_path)
    outbox = tmp_path / "outbox.sqlite"
    storage.initialize(outbox)
    signal = points[-1]["signal_ids"][0]
    app.enqueue(outbox, watchlist, journal, manifest, signal, "local-preview")
    before = outbox.read_bytes()
    bad: Any = copy.deepcopy(manifest)
    if invalid == "unrelated":
        bad["entities"][1]["extra"] = "invalid"
    elif invalid == "identity":
        target = next(
            row
            for row in bad["entities"]
            if row["cmt_id"] == "541b9d13-9669-4973-8413-397bea14c045"
        )
        target["language"] = "en"
    elif invalid == "parsed":
        bad = parse_manifest(bad)
    else:
        bad["extra"] = True
    with pytest.raises(OutboxError):
        app.enqueue(outbox, watchlist, journal, bad, signal, "local-preview")
    assert outbox.read_bytes() == before


def test_manifest_detached_before_source_callbacks_and_exact_shared_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    watchlist, journal, manifest, _, points = sources(tmp_path)
    outbox = tmp_path / "outbox.sqlite"
    storage.initialize(outbox)
    original = journal_storage._verified_signal_bundle
    supplied = journal_storage.Budget()
    seen = []

    def mutate(path, signal_id, *, _budget):
        assert _budget is supplied
        manifest["extra"] = "mutated-after-freeze"
        seen.append(_budget)
        return original(path, signal_id, _budget=_budget)

    monkeypatch.setattr(journal_storage, "_verified_signal_bundle", mutate)
    saved = app.enqueue(
        outbox,
        watchlist,
        journal,
        manifest,
        points[-1]["signal_ids"][0],
        "local-preview",
        _budget=supplied,
    )
    assert saved["result"] == "recorded" and seen == [supplied]


def test_five_checkpoint_ancient_replay_keeps_full_frozen_evidence(tmp_path: Path) -> None:
    from card_market_tracker.watchlist_journal import application as journal_app

    watchlist, journal, manifest, watch_id, points = sources(tmp_path)
    outbox = tmp_path / "outbox.sqlite"
    storage.initialize(outbox)
    signal = points[-1]["signal_ids"][0]
    saved = app.enqueue(outbox, watchlist, journal, manifest, signal, "local-preview")
    original = storage.evidence_get(outbox, saved["alert_id"])
    previous = (
        json.loads(original["evidence_json"])
        if "evidence_json" in original
        else original["evidence"]
    )
    previous = previous["current"]["snapshot"]["current"]
    for ordinal, stock in enumerate(("AVAILABLE", "OUT_OF_STOCK", "AVAILABLE"), 3):
        current = dict(
            previous,
            sample_id=f"s{ordinal}",
            stock=stock,
            observed_at=f"2026-10-23T12:0{ordinal}:00Z",
        )
        result = journal_app.record(
            journal,
            watchlist,
            manifest,
            watch_id,
            current,
            previous,
            revision=1,
            as_of=current["observed_at"],
        )
        if ordinal == 5:
            assert result["signals_count"] == 2
        previous = current
    before = outbox.read_bytes()
    assert (
        app.enqueue(outbox, watchlist, journal, manifest, signal, "local-preview")["result"]
        == "replayed"
    )
    assert storage.evidence_get(outbox, saved["alert_id"]) == original
    assert outbox.read_bytes() == before


@pytest.mark.parametrize("operation", ["enqueue", "recompute"])
def test_origin_deadline_checked_immediately_after_get_before_parse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    from card_market_tracker.watchlist import storage as origin_storage
    from card_market_tracker.watchlist import validation as origin_validation

    watchlist, journal, manifest, _, points = sources(tmp_path)
    outbox = tmp_path / "outbox.sqlite"
    storage.initialize(outbox)
    signal = points[-1]["signal_ids"][0]
    saved = app.enqueue(outbox, watchlist, journal, manifest, signal, "local-preview")
    before = (watchlist.read_bytes(), journal.read_bytes(), outbox.read_bytes())
    budget = journal_storage.Budget()
    original_get = origin_storage.get
    original_parse = origin_validation.parse_entry
    returned = False
    origin_reads = 0
    parses_after_return = 0
    writer_calls = 0

    def expire_at_return(*args, **kwargs):
        nonlocal returned, origin_reads
        assert kwargs["revision"] == 1
        assert 0 < kwargs["timeout"] <= budget.remaining() + 0.01
        result = original_get(*args, **kwargs)
        origin_reads += 1
        budget.deadline = 0
        returned = True
        return result

    def counted_parse(value):
        nonlocal parses_after_return
        if returned:
            parses_after_return += 1
        return original_parse(value)

    def forbidden_writer(*args, **kwargs):
        nonlocal writer_calls
        writer_calls += 1
        raise AssertionError("deadline failure must precede writer")

    monkeypatch.setattr(origin_storage, "get", expire_at_return)
    monkeypatch.setattr(origin_validation, "parse_entry", counted_parse)
    # The previous accepted P5b helper keeps a bound import; observe that existing
    # path too without modifying its implementation.
    monkeypatch.setattr(app.journal_application, "parse_entry", counted_parse)
    monkeypatch.setattr(storage, "_enqueue_verified", forbidden_writer)
    with pytest.raises(OutboxError, match="storage_timeout"):
        if operation == "enqueue":
            app.enqueue(
                outbox, watchlist, journal, manifest, signal, "local-preview", _budget=budget
            )
        else:
            app.recompute(outbox, watchlist, journal, manifest, saved["alert_id"], _budget=budget)
    assert origin_reads == 1
    assert writer_calls == 0
    assert (watchlist.read_bytes(), journal.read_bytes(), outbox.read_bytes()) == before
    assert parses_after_return == 0
