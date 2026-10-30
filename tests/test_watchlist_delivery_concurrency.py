"""P8d DB author tests: real processes, durable claims, crash and retry clocks."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from test_watchlist_delivery_storage import claim, outcome, prepared

from card_market_tracker.watchlist_delivery import storage
from card_market_tracker.watchlist_delivery.errors import DeliveryError

WORKER = r"""
import json,os,sys,time
from pathlib import Path
from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery.errors import DeliveryError
from card_market_tracker.telegram_delivery.transport import Receipt,TransportResult
config=json.loads(sys.argv[1]); root=Path(config['root']); name=config['name']
class Fake:
 def check_configuration(self): pass
 def validate_bot(self,*args,**kwargs):
  (root/(name+'.ready')).write_text('ready')
  deadline=time.monotonic()+10
  while not (root/'go').exists():
   if time.monotonic()>deadline: raise RuntimeError('barrier')
   time.sleep(.005)
 def send(self,*args,**kwargs):
  (root/(name+'.sent')).write_text('claimed before fake dispatch')
  if config.get('crash'): time.sleep(30)
  else: time.sleep(.15)
  return TransportResult('confirmed',receipt=Receipt(3,1,1,2))
app._transport_factory=lambda:Fake()
try:
 result=app.send(Path(config['ledger']),config['did'],watchlist_db=Path(config['watchlist']),journal_db=Path(config['journal']),outbox_db=Path(config['outbox']),manifest=config['manifest'])
 print(result['result'])
except DeliveryError as error:
 print(error.category)
"""


def wait_for(predicate: Any, seconds: float = 5) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("child checkpoint timeout")
        time.sleep(0.01)


def worker(
    context: dict[str, Any], root: Path, name: str, *, crash: bool = False
) -> subprocess.Popen[str]:
    source = context["source"]
    config = {
        "root": str(root),
        "name": name,
        "crash": crash,
        "ledger": str(context["ledger"]),
        "did": context["did"],
        "watchlist": str(source.watchlist),
        "journal": str(source.journal),
        "outbox": str(context["outbox"]),
        "manifest": source.manifest,
    }
    return subprocess.Popen(
        [sys.executable, "-B", "-c", WORKER, json.dumps(config)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_two_sender_processes_one_durable_claim_and_one_fake_send(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    storage._destination_validated(context["ledger"], "private")
    children = [worker(context, tmp_path, name) for name in ("a", "b")]
    try:
        wait_for(lambda: len(list(tmp_path.glob("*.ready"))) == 2)
        (tmp_path / "go").touch()
        wait_for(lambda: len(list(tmp_path.glob("*.sent"))) >= 1)
        with sqlite3.connect(context["ledger"]) as db:
            assert db.execute("SELECT count(*) FROM wtd_claims").fetchone() == (1,)
        outputs = [child.communicate(timeout=8) for child in children]
        assert all(child.returncode == 0 for child in children), outputs
        assert len(list(tmp_path.glob("*.sent"))) == 1
        assert any(out.strip() == "ok" for out, _ in outputs), outputs
        verified = storage.verify(context["ledger"])
        assert verified["counts"]["claims"] == verified["counts"]["results"] == 1
        assert storage.get(context["ledger"], context["did"])["delivery"]["state"] == "confirmed"
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=3)


def test_killed_sender_after_durable_claim_stays_blocked_until_quiesced_recovery(
    tmp_path: Path,
) -> None:
    context = prepared(tmp_path / "one")
    storage._destination_validated(context["ledger"], "private")
    child = worker(context, tmp_path, "crash", crash=True)
    try:
        wait_for(lambda: (tmp_path / "crash.ready").exists())
        (tmp_path / "go").touch()
        wait_for(lambda: (tmp_path / "crash.sent").exists())
        assert storage.get(context["ledger"], context["did"])["delivery"]["state"] == "in_flight"
        child.kill()
        child.communicate(timeout=3)
        assert storage.verify(context["ledger"])["counts"]["results"] == 0
        recovered = storage.recover(context["ledger"], context["did"], worker_quiesced=True)
        assert recovered["delivery"]["state"] == "uncertain"
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=3)


def test_valid_429_cooldown_inclusive_third_exhaustion_and_revalidation_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = prepared(tmp_path / "one")
    wall = ["2027-01-01T00:00:00.123456Z"]
    monkeypatch.setattr(storage, "_now", lambda: wall[0])
    for ordinal in (1, 2, 3):
        budget, claimed = claim(context)
        original_snapshot = claimed["delivery"]["attempts"][-1]["route_validated_at"]
        wall[0] = storage._after(wall[0], 1)
        final = storage._finish(
            context["ledger"],
            context["did"],
            claimed["_handle"],
            outcome("retryable", "rate_limited", 2),
            budget,
        )
        if ordinal < 3:
            assert final["state"] == "retryable"
            assert final["not_before"] == storage._after(wall[0], 2)
            with sqlite3.connect(context["ledger"]) as db:
                assert db.execute("SELECT operational_high_water FROM wtd_metadata").fetchone() == (
                    wall[0],
                )
            with pytest.raises(DeliveryError, match="retry_not_due"):
                claim(context)
            wall[0] = storage._after(wall[0], 2)
        else:
            assert (
                final["state"] == "permanent_failure"
                and final["last_error_category"] == "retry_exhausted"
            )
        current = storage.load_delivery(context["ledger"], context["did"])
        assert current["attempts"][-1]["route_validated_at"] == original_snapshot
        storage.verify(context["ledger"])


def test_postclaim_clock_rollback_overrides_accepted_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = prepared(tmp_path / "one")
    budget, claimed = claim(context)
    floor = claimed["delivery"]["updated_at"]
    monkeypatch.setattr(storage, "_now", lambda: "0001-01-01T00:00:00.000000Z")
    final = storage._finish(
        context["ledger"], context["did"], claimed["_handle"], outcome(), budget
    )
    assert final["state"] == "uncertain" and final["last_error_category"] == "clock_skew"
    assert final["updated_at"] == floor
    storage.verify(context["ledger"])


def test_real_process_incompatible_original_prepares_serialize(tmp_path: Path) -> None:
    from test_watchlist_delivery_storage import pipeline

    ledger = tmp_path / "shared.db"
    storage.initialize(ledger)
    storage.destination_add(ledger, "private", 1, 2, operator_private_owned=True)
    first = pipeline(tmp_path / "one", ledger=ledger, series="first")
    second = pipeline(
        tmp_path / "two", ledger=ledger, config={"target_price_minor": 1100}, series="second"
    )
    code = r"""
import json,sys,time
from pathlib import Path
from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery.errors import DeliveryError
c=json.loads(sys.argv[1]); root=Path(c['root']); (root/(c['name']+'.ready')).touch()
while not (root/'go').exists(): time.sleep(.005)
a=c['args']; a[:4]=[Path(p) for p in a[:4]]
try: print(app.prepare(*a,**c['consent'])['result'])
except DeliveryError as error: print(error.category)
"""
    children = []
    for name, context in (("first", first), ("second", second)):
        args = [str(value) if isinstance(value, Path) else value for value in context["args"]]
        config = {"root": str(tmp_path), "name": name, "args": args, "consent": context["consent"]}
        children.append(
            subprocess.Popen(
                [sys.executable, "-B", "-c", code, json.dumps(config)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        )
    try:
        wait_for(lambda: len(list(tmp_path.glob("*.ready"))) == 2)
        (tmp_path / "go").touch()
        results = [child.communicate(timeout=8) for child in children]
        assert all(child.returncode == 0 for child in children), results
        assert sorted(out.strip() for out, _ in results) == ["identity_conflict", "inserted"]
        assert storage.verify(ledger)["counts"]["deliveries"] == 1
        storage.backup(ledger, tmp_path / "healthy.db")
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=3)
