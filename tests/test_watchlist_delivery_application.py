"""Author genuine-origin, consent, sealed-authority and conservative fake-send tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_watchlist_alert_source import TARGET
from test_watchlist_delivery_policy import content

from card_market_tracker.watchlist import application as watch_app
from card_market_tracker.watchlist import storage as watch_storage
from card_market_tracker.watchlist_alerts import application as outbox_app
from card_market_tracker.watchlist_alerts import storage as outbox_storage
from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery import policy, storage
from card_market_tracker.watchlist_delivery.budget import Budget
from card_market_tracker.watchlist_delivery.errors import DeliveryError
from card_market_tracker.watchlist_journal import application as journal_app
from card_market_tracker.watchlist_journal import storage as journal_storage


def originals(
    tmp_path: Path, *, priority: str = "normal", series: str = "first"
) -> tuple[Path, Path, Path, dict[str, Any], str]:
    tmp_path.mkdir(exist_ok=True)
    manifest = json.loads((Path(__file__).parent / "fixtures/synthetic_manifest.json").read_text())
    watch, journal, outbox = (
        tmp_path / (name + ".sqlite") for name in ("watch", "journal", "outbox")
    )
    watch_storage.initialize(watch)
    entry = watch_app.add(
        watch,
        manifest,
        TARGET,
        {"target_price_minor": 1000, "restock_enabled": True, "priority": priority},
        request_token="initial",
    )["entry"]
    journal_storage.initialize(journal)
    previous = None
    for ordinal, stock in enumerate(("OUT_OF_STOCK", "AVAILABLE"), 1):
        current = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"s{ordinal}",
            "cmt_id": TARGET,
            "series_key": series,
            "observed_at": f"2026-10-23T12:0{ordinal}:00Z",
            "currency": "EUR",
            "unit_price_minor": 900,
            "shipping_minor": 100,
            "stock": stock,
        }
        recorded = journal_app.record(
            journal,
            watch,
            manifest,
            entry["watch_id"],
            current,
            previous,
            revision=1,
            as_of=current["observed_at"],
        )
        previous = current
    outbox_storage.initialize(outbox)
    alert = outbox_app.enqueue(
        outbox, watch, journal, manifest, recorded["signal_ids"][0], "private"
    )["alert_id"]
    return watch, journal, outbox, manifest, alert


def ledger(tmp_path: Path) -> Path:
    path = tmp_path / "delivery.sqlite"
    app.initialize(path)
    app.destination_add(path, "private", 1, 2, operator_private_owned=True)
    return path


def consent(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "acknowledgement": review["acknowledgement"],
        **{
            "expected_" + key: review[key]
            for key in (
                "signal_id",
                "revision",
                "message_sha256",
                "evidence_sha256",
                "route_sha256",
                "binding_sha256",
            )
        },
    }


def prepared(tmp_path: Path) -> tuple[Path, tuple[Any, ...], str]:
    origins = originals(tmp_path / "originals")
    path = ledger(tmp_path)
    reviewed = app.review(path, *origins, "private")["review"]
    item = app.prepare(path, *origins, "private", **consent(reviewed))["delivery"]
    return path, origins, item["delivery_id"]


class Fake:
    def __init__(self, result: object = None) -> None:
        self.calls: list[str] = []
        self.result = result
        self.check = lambda: None

    def check_configuration(self) -> None:
        self.calls.append("configuration")

    def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float) -> None:
        self.calls.append("destination")

    def validate_bot(self, bot_id: int, *, timeout: float) -> None:
        self.calls.append("bot")

    def send(self, bot_id: int, chat_id: int, message_text: str, *, timeout: float) -> object:
        self.calls.append("send")
        self.check()
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def validate(path: Path, fake: Fake, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app, "_transport_factory", lambda: fake)
    app.destination_validate(path, "private")


def test_genuine_pipeline_consent_ancient_replay_sources_unchanged(tmp_path: Path) -> None:
    path, origins, did = prepared(tmp_path)
    source_bytes = [p.read_bytes() for p in origins[:3]]
    reviewed = app.review(path, *origins, "private")["review"]
    initial = app.get(path, did)
    assert app.prepare(path, *origins, "private", **consent(reviewed))["result"] == "replay"
    assert app.get(path, did) == initial
    assert app.recompute(path, *origins[:3], origins[3], did)["level"] == "origin-recompute"
    assert [p.read_bytes() for p in origins[:3]] == source_bytes


@pytest.mark.parametrize(
    "key",
    [
        "acknowledgement",
        "expected_signal_id",
        "expected_revision",
        "expected_message_sha256",
        "expected_evidence_sha256",
        "expected_route_sha256",
        "expected_binding_sha256",
    ],
)
def test_consent_every_expected_value_is_required(tmp_path: Path, key: str) -> None:
    origins = originals(tmp_path / "originals")
    path = ledger(tmp_path)
    args = consent(app.review(path, *origins, "private")["review"])
    args[key] = True if key == "expected_revision" else "incorrect"
    before = path.read_bytes()
    with pytest.raises(DeliveryError, match="consent_mismatch"):
        app.prepare(path, *origins, "private", **args)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "attack",
    [
        "dict",
        "counterfeit",
        "copy",
        "deepcopy",
        "mutation",
        "budget",
        "operation",
        "ledger",
        "deadline",
        "used",
    ],
)
def test_single_use_instance_content_operation_path_budget_authority(
    tmp_path: Path, attack: str
) -> None:
    origins = originals(tmp_path / "originals")
    path = ledger(tmp_path)
    budget = Budget()
    receipt: Any = app._issue(content(), budget, path, origins[:3], origins[3])
    operation = "prepare"
    if attack == "dict":
        receipt = content()
    elif attack == "counterfeit":
        receipt = app._Receipt(receipt.content_json)
    elif attack == "copy":
        receipt = copy.copy(receipt)
    elif attack == "deepcopy":
        receipt = copy.deepcopy(receipt)
    elif attack == "mutation":
        object.__setattr__(receipt, "content_json", receipt.content_json + " ")
    elif attack == "budget":
        budget = Budget()
    elif attack == "operation":
        operation = "claim"
    elif attack == "ledger":
        path = tmp_path / "missing.sqlite"
    elif attack == "deadline":
        budget._global_deadline += 5
    elif attack == "used":
        app._consume_receipt(receipt, budget, operation, path)
    with pytest.raises(DeliveryError, match="unsupported_evidence"):
        app._consume_receipt(receipt, budget, operation, path)


def test_expired_issued_authority_uses_original_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import card_market_tracker.watchlist_delivery.budget as budget_module

    origins = originals(tmp_path / "originals")
    path = ledger(tmp_path)
    budget = Budget()
    receipt = app._issue(content(), budget, path, origins[:3], origins[3])
    monkeypatch.setattr(budget_module.time, "monotonic", lambda: budget.global_deadline + 1)
    with pytest.raises(DeliveryError, match="storage_timeout"):
        app._consume_receipt(receipt, budget, "prepare", path)


def test_global_rw01_genuine_incompatible_originals_rejected_before_commit(tmp_path: Path) -> None:
    first = originals(tmp_path / "one")
    second = originals(tmp_path / "two", priority="high", series="different")
    path = ledger(tmp_path)
    reviewed = app.review(path, *first, "private")["review"]
    app.prepare(path, *first, "private", **consent(reviewed))
    reviewed_other = app.review(path, *second, "private")["review"]
    assert reviewed["watch_id"] == reviewed_other["watch_id"]
    assert reviewed["revision"] == reviewed_other["revision"]
    assert reviewed["signal_id"] != reviewed_other["signal_id"]
    before = path.read_bytes()
    with pytest.raises(DeliveryError, match="identity_conflict"):
        app.prepare(path, *second, "private", **consent(reviewed_other))
    assert path.read_bytes() == before
    assert app.verify(path)["counts"]["deliveries"] == 1
    app.backup(path, tmp_path / "healthy-backup.sqlite")


def test_claim_durable_before_fake_http_and_confirmed_replay_ignores_origins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult

    path, origins, did = prepared(tmp_path)
    fake = Fake(TransportResult("confirmed", receipt=Receipt(3, 1, 1, 2)))
    validate(path, fake, monkeypatch)
    fake.check = lambda: _assert_claim(path, did)
    sent = app.send(
        path,
        did,
        watchlist_db=origins[0],
        journal_db=origins[1],
        outbox_db=origins[2],
        manifest=origins[3],
    )
    assert sent["delivery"]["state"] == "confirmed"
    assert fake.calls.count("send") == 1
    monkeypatch.setattr(app, "_transport_factory", lambda: pytest.fail("replay imported transport"))
    for source in origins[:3]:
        source.unlink()
    assert app.send(path, did, manifest=object())["result"] == "replay"
    restored = tmp_path / "restored.sqlite"
    app.restore(path, restored)
    with pytest.raises(DeliveryError, match="send_quarantined"):
        app.send(restored, did)
    with pytest.raises(DeliveryError, match="send_quarantined"):
        app.send(restored, "wtdl1_" + "0" * 64)


def _assert_claim(path: Path, did: str) -> None:
    item = app.get(path, did)["delivery"]
    assert item["state"] == "in_flight" and item["attempt_count"] == 1


@pytest.mark.parametrize("missing", ["watch", "journal", "outbox"])
def test_missing_original_never_constructs_transport_or_claims(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    path, origins, did = prepared(tmp_path)
    fake = Fake()
    validate(path, fake, monkeypatch)
    origins[("watch", "journal", "outbox").index(missing)].unlink()
    monkeypatch.setattr(app, "_transport_factory", lambda: pytest.fail("must not import transport"))
    with pytest.raises(DeliveryError, match="storage_missing"):
        app.send(
            path,
            did,
            watchlist_db=origins[0],
            journal_db=origins[1],
            outbox_db=origins[2],
            manifest=origins[3],
        )
    assert app.get(path, did)["delivery"]["state"] == "ready"


@pytest.mark.parametrize(
    "outcome,category",
    [
        (None, "provider_invalid"),
        (RuntimeError("private-sentinel"), "network_uncertain"),
        (DeliveryError("transport_timeout"), "transport_timeout"),
    ],
)
def test_ambiguous_fake_http_persists_uncertain_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: object, category: str
) -> None:
    path, origins, did = prepared(tmp_path)
    fake = Fake(outcome)
    validate(path, fake, monkeypatch)
    response = app.send(
        path,
        did,
        watchlist_db=origins[0],
        journal_db=origins[1],
        outbox_db=origins[2],
        manifest=origins[3],
    )
    assert response["result"] == "error"
    assert response["error_category"] == category
    assert response["delivery"]["state"] == "uncertain"
    with pytest.raises(DeliveryError, match="delivery_blocked"):
        app.send(path, did)
    assert fake.calls.count("send") == 1


def test_aggregate_origin_scope_and_global_deadline_never_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import card_market_tracker.watchlist_delivery.budget as budget_module

    moment = [10.0]
    monkeypatch.setattr(budget_module.time, "monotonic", lambda: moment[0])
    budget = Budget(15, 30, started=8.0)
    assert budget.global_deadline == 23
    with budget.origins():
        assert budget.remaining() == 5
        moment[0] = 14.9
        assert budget.remaining() == pytest.approx(0.1)
    assert budget.global_deadline == 23
    with pytest.raises(DeliveryError, match="unsupported_evidence"):
        with budget.origins():
            pass
    with pytest.raises(AttributeError):
        budget.deadline = 100


def test_equivalent_original_copies_ignore_only_preview_preparation_clock(tmp_path: Path) -> None:
    first = originals(tmp_path / "one")
    second = originals(tmp_path / "two")
    path = ledger(tmp_path)
    reviewed = app.review(path, *first, "private")["review"]
    initial = app.prepare(path, *first, "private", **consent(reviewed))
    other_review = app.review(path, *second, "private")["review"]
    assert other_review == reviewed
    replay = app.prepare(path, *second, "private", **consent(other_review))
    assert replay["result"] == "replay" and replay["delivery"] == initial["delivery"]


def test_before_after_pair_includes_first_prepared_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    origins = originals(tmp_path / "originals")
    path = ledger(tmp_path)
    get_pair = outbox_storage._get_pair
    count = 0

    def changed(*args: Any, **kwargs: Any) -> Any:
        nonlocal count
        count += 1
        alert, evidence = get_pair(*args, **kwargs)
        if count == 3:
            alert["first_prepared_at"] = "2026-01-01T00:00:00.000000Z"
        return alert, evidence

    monkeypatch.setattr(outbox_storage, "_get_pair", changed)
    with pytest.raises(DeliveryError, match="recompute_mismatch"):
        app.review(path, *origins, "private")
    assert count == 3
    assert app.verify(path)["counts"]["deliveries"] == 0


def test_full_manifest_detached_before_original_callbacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    origins = originals(tmp_path / "originals")
    path = ledger(tmp_path)
    original = outbox_storage.verify
    seen = []
    shared = Budget()

    def mutate(*args: Any, **kwargs: Any) -> Any:
        assert kwargs["_budget"] is shared
        seen.append(shared)
        origins[3]["extra"] = "changed-after-detach"
        return original(*args, **kwargs)

    monkeypatch.setattr(outbox_storage, "verify", mutate)
    context = app._invocation_budget.set(shared)
    try:
        assert app.review(path, *origins, "private")["result"] == "ok"
    finally:
        app._invocation_budget.reset(context)
    assert seen == [shared]
    with pytest.raises(DeliveryError, match="invalid_shape"):
        app.review(path, *origins, "private")


def test_deferred_manifest_read_occurs_inside_aggregate_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, origins, did = prepared(tmp_path)
    fake = Fake()
    validate(path, fake, monkeypatch)
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(origins[3]))
    budget = Budget(15, 30)
    original = app._manifest_read
    seen = []

    def checked(source, supplied_budget) -> object:
        assert budget._origin_active
        assert budget.origin_seal[0] is not None
        assert supplied_budget is budget
        seen.append(source.path)
        return original(source, supplied_budget)

    monkeypatch.setattr(app, "_manifest_read", checked)
    context = app._invocation_budget.set(budget)
    try:
        response = app.send(
            path,
            did,
            watchlist_db=origins[0],
            journal_db=origins[1],
            outbox_db=origins[2],
            manifest=app._manifest_file(manifest_file, budget),
        )
    finally:
        app._invocation_budget.reset(context)
    assert response["error_category"] == "provider_invalid"
    assert seen == [manifest_file]


def test_combined_original_helpers_share_five_second_ceiling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import card_market_tracker.watchlist_delivery.budget as budget_module

    path, origins, did = prepared(tmp_path)
    validate(path, Fake(), monkeypatch)
    moment = [100.0]
    monkeypatch.setattr(budget_module.time, "monotonic", lambda: moment[0])
    shared = Budget(15, 30)
    seen = []
    verify = outbox_storage.verify
    recompute = outbox_app.recompute

    def slow_verify(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs["_budget"])
        result = verify(*args, **kwargs)
        moment[0] += 3
        return result

    def slow_recompute(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs["_budget"])
        moment[0] += 2.1
        return recompute(*args, **kwargs)

    monkeypatch.setattr(outbox_storage, "verify", slow_verify)
    monkeypatch.setattr(outbox_app, "recompute", slow_recompute)
    monkeypatch.setattr(
        app, "_transport_factory", lambda: pytest.fail("origins exceeded allowance")
    )
    context = app._invocation_budget.set(shared)
    try:
        with pytest.raises(DeliveryError, match="storage_timeout"):
            app.send(
                path,
                did,
                watchlist_db=origins[0],
                journal_db=origins[1],
                outbox_db=origins[2],
                manifest=origins[3],
            )
    finally:
        app._invocation_budget.reset(context)
    assert seen == [shared, shared]
    assert shared.global_deadline == 115
    assert app.get(path, did)["delivery"]["attempt_count"] == 0


def test_three_strict_rate_limits_manual_cooldown_and_exhaustion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from card_market_tracker.telegram_delivery.transport import TransportResult

    path, origins, did = prepared(tmp_path)
    fake = Fake(TransportResult("retryable", "provider_rate_limit", retry_after=1))
    moment = ["2027-01-01T00:00:00.000000Z"]
    monkeypatch.setattr(policy, "now", lambda: moment[0])
    monkeypatch.setattr(storage, "_now", lambda: moment[0])
    validate(path, fake, monkeypatch)
    options = {
        "watchlist_db": origins[0],
        "journal_db": origins[1],
        "outbox_db": origins[2],
        "manifest": origins[3],
    }
    for ordinal in range(1, 4):
        moment[0] = f"2027-01-01T00:00:0{ordinal}.000000Z"
        result = app.send(path, did, **options)
        assert result["delivery"]["attempt_count"] == ordinal
        assert result["delivery"]["state"] == ("retryable" if ordinal < 3 else "permanent_failure")
        assert result["error_category"] == ("rate_limited" if ordinal < 3 else "retry_exhausted")
        if ordinal < 3:
            with pytest.raises(DeliveryError, match="retry_not_due"):
                app.send(path, did, **options)
    assert fake.calls.count("send") == 3
    with pytest.raises(DeliveryError, match="delivery_blocked"):
        app.send(path, did, **options)


@pytest.mark.parametrize("commit_before_error", [False, True])
def test_result_commit_error_never_resends_or_fabricates_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, commit_before_error: bool
) -> None:
    from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult

    path, origins, did = prepared(tmp_path)
    fake = Fake(TransportResult("confirmed", receipt=Receipt(3, 1, 1, 2)))
    validate(path, fake, monkeypatch)
    finish = storage._finish
    count = 0

    def failing(*args: Any, **kwargs: Any) -> Any:
        nonlocal count
        count += 1
        if count == 1:
            if commit_before_error:
                finish(*args, **kwargs)
            raise DeliveryError("storage_io")
        return finish(*args, **kwargs)

    monkeypatch.setattr(storage, "_finish", failing)
    with pytest.raises(DeliveryError, match="local_commit_failed"):
        app.send(
            path,
            did,
            watchlist_db=origins[0],
            journal_db=origins[1],
            outbox_db=origins[2],
            manifest=origins[3],
        )
    item = app.get(path, did)["delivery"]
    assert item["state"] == ("confirmed" if commit_before_error else "uncertain")
    assert fake.calls.count("send") == 1
    assert item["attempt_count"] == 1


def test_postclaim_clock_rollback_conservatively_discards_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult

    path, origins, did = prepared(tmp_path)
    fake = Fake(TransportResult("confirmed", receipt=Receipt(3, 1, 1, 2)))
    moment = ["2027-01-01T00:00:00.000000Z"]
    monkeypatch.setattr(policy, "now", lambda: moment[0])
    monkeypatch.setattr(storage, "_now", lambda: moment[0])
    validate(path, fake, monkeypatch)
    fake.check = lambda: moment.__setitem__(0, "2026-01-01T00:00:00.000000Z")
    response = app.send(
        path,
        did,
        watchlist_db=origins[0],
        journal_db=origins[1],
        outbox_db=origins[2],
        manifest=origins[3],
    )
    assert response["error_category"] == "clock_skew"
    assert response["delivery"]["state"] == "uncertain"
    assert response["delivery"]["updated_at"] == "2027-01-01T00:00:00.000000Z"


def test_cli_manifest_multiple_hardlinks_rejected_without_ledger_change(tmp_path: Path) -> None:
    import os

    origins = originals(tmp_path / "origins")
    path = ledger(tmp_path)
    manifest = tmp_path / "manifest.json"
    alias = tmp_path / "manifest-alias.json"
    manifest.write_text(json.dumps(origins[3]), encoding="utf-8")
    os.link(manifest, alias)
    before = path.read_bytes()
    budget = Budget(5)
    token = app._invocation_budget.set(budget)
    try:
        with pytest.raises(DeliveryError, match="unsafe_destination"):
            app.review(path, *origins[:3], app._manifest_file(alias, budget), origins[4], "private")
    finally:
        app._invocation_budget.reset(token)
    assert path.read_bytes() == before
    assert app.verify(path)["counts"]["deliveries"] == 0


def test_cli_manifest_descriptor_replacement_rejected(tmp_path: Path, monkeypatch) -> None:
    import os

    origins = originals(tmp_path / "origins")
    path = ledger(tmp_path)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(origins[3]), encoding="utf-8")
    real_stat = app.file_paths._unsafe_stat
    reads = 0

    def replacing(target, *, file):
        nonlocal reads
        observed = real_stat(target, file=file)
        if Path(target) == manifest and file:
            reads += 1
            if reads >= 3:
                # Inject an inode substitution in the post-open pathname
                # readback. Windows may refuse real unlink of an open file.
                fields = list(observed)
                fields[1] += 1
                return os.stat_result(fields)
        return observed

    monkeypatch.setattr(app.file_paths, "_unsafe_stat", replacing)
    budget = Budget(5)
    token = app._invocation_budget.set(budget)
    try:
        with pytest.raises(DeliveryError, match="unsafe_destination"):
            app.review(
                path, *origins[:3], app._manifest_file(manifest, budget), origins[4], "private"
            )
    finally:
        app._invocation_budget.reset(token)
    assert reads >= 3


@pytest.mark.parametrize(
    "document,category",
    [
        ('{"version":1,"version":1}', "duplicate_key"),
        ('{"version":NaN}', "invalid_json"),
        (" " * 1048577, "input_limit"),
    ],
    ids=("duplicate-key", "nonfinite", "over-1MiB"),
)
def test_cli_manifest_checked_read_preserves_parser_errors(tmp_path, document, category):
    origins = originals(tmp_path / "origins")
    path = ledger(tmp_path)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(document, encoding="utf-8")
    budget = Budget(5)
    token = app._invocation_budget.set(budget)
    try:
        with pytest.raises(DeliveryError, match=category):
            app.review(
                path, *origins[:3], app._manifest_file(manifest, budget), origins[4], "private"
            )
    finally:
        app._invocation_budget.reset(token)
