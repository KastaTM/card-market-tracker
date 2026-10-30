"""Only exact independently reviewed public digest candidates may be dismissed."""

import hashlib
import json
import runpy
from hashlib import sha1
from types import SimpleNamespace

import pytest

SCANNER = runpy.run_path("scripts/check_secret_scan.py")


def candidate(value, detector="Hex High Entropy String"):
    return {"type": detector, "hashed_secret": hashlib.sha1(value.encode()).hexdigest()}


def test_exact_path_detector_and_public_value_only():
    reviewed = SCANNER["_reviewed_public_candidate"]
    revision = SCANNER["_REVISION"]
    path = "docs/sources/P1B_REQUEST_LEDGER.json"
    assert reviewed(path, candidate(revision))
    assert reviewed(path.replace("/", "\\"), candidate(revision))
    assert not reviewed("another.json", candidate(revision))
    assert not reviewed("../" + path, candidate(revision))
    assert not reviewed(path, candidate("replacement-public-value"))
    assert not reviewed(path, candidate(revision, "Secret Keyword"))
    assert not reviewed(path, {"type": "Hex High Entropy String"})
    assert not reviewed(path, candidate(SCANNER["_BUNDLE"]))


@pytest.mark.parametrize(
    "path,value",
    [
        ("docs/sources/P1C_REQUEST_LEDGER.json", "_R1"),
        ("src/card_market_tracker/pinned_repository/approved_bundle_v2.json", "_PROJECTION"),
        ("tests/fixtures/pinned_repository_bundle_v2.json", "_R1"),
        ("src/card_market_tracker/pinned_repository/bundle_v2.py", "_BUNDLE_V2"),
        ("tests/fixtures/p5b_identity_vectors_v1.json", "_P5B_IDENTITY"),
    ],
)
def test_p1c_exceptions_are_exact_path_detector_value(path, value):
    reviewed = SCANNER["_reviewed_public_candidate"]
    digest = SCANNER[value]
    assert reviewed(path, candidate(digest))
    assert not reviewed("other/" + path, candidate(digest))
    assert not reviewed(path, candidate(digest, "Secret Keyword"))
    assert not reviewed(path, candidate(digest[:-1] + ("0" if digest[-1] != "0" else "1")))
    assert not reviewed("docs/sources/P1B_REQUEST_LEDGER.json", candidate(SCANNER["_R1"]))


@pytest.mark.parametrize("unknown", [False, True])
def test_scan_keeps_unknown_findings_failing_and_never_prints_values(monkeypatch, capsys, unknown):
    report = {
        "results": {
            "docs/sources/P1B_REQUEST_LEDGER.json": [candidate(SCANNER["_REVISION"])],
        }
    }
    if unknown:
        report["results"]["unreviewed.py"] = [candidate("private-value")]
    responses = iter(
        [
            SimpleNamespace(stdout=b"docs/sources/P1B_REQUEST_LEDGER.json\0"),
            SimpleNamespace(stdout=json.dumps(report)),
        ]
    )
    monkeypatch.setattr(SCANNER["subprocess"], "run", lambda *args, **kwargs: next(responses))
    assert SCANNER["main"]() == int(unknown)
    output = capsys.readouterr().out
    assert "private-value" not in output and SCANNER["_REVISION"] not in output
    assert ("FAIL" if unknown else "PASS") in output


@pytest.mark.parametrize(
    "path,key",
    [
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_BASE"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_TREE"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_PARENT1"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_PARENT2"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_OLDHEAD"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_OLDTREE"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_AUDIT"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_BRIEF"],
        ["docs/evidence/P8D_GATE_A/baseline.json", "_P8D_CONTRACT"],
        ["docs/evidence/P8D_GATE_B/design_probe.py", "_P8D_BASE"],
        ["docs/evidence/P8D_GATE_B/design_probe.py", "_P8D_TREE"],
        ["docs/evidence/P8D_GATE_B/design_probe.py", "_P8D_AUDIT"],
        ["docs/evidence/P8D_GATE_B/design_probe.py", "_P8D_BRIEF"],
        ["docs/evidence/P8D_GATE_B/design_probe.py", "_P8D_CONTRACT"],
        ["docs/evidence/P8D_GATE_B/design_probe.py", "_P8D_ORACLE_A"],
        ["docs/evidence/P8D_GATE_B/design_probe.py", "_P8D_ORACLE_B"],
        ["docs/evidence/P8D_REVIEWER/INITIAL_PROBE_RESULT.json", "_P8D_DESIGNHEAD"],
        ["docs/evidence/P8D_REVIEWER/INITIAL_PROBE_RESULT.json", "_P8D_DESIGNTREE"],
        ["docs/evidence/P8D_REVIEWER/MANIFEST_CORRECTIVE_PROBE_RESULT.json", "_P8D_DESIGNHEAD"],
        ["docs/evidence/P8D_REVIEWER/MANIFEST_CORRECTIVE_PROBE_RESULT.json", "_P8D_DESIGNTREE"],
        ["docs/evidence/P8D_REVIEWER/MANIFEST_GAP_PROBE_RESULT.json", "_P8D_DESIGNHEAD"],
        ["docs/evidence/P8D_REVIEWER/MANIFEST_GAP_PROBE_RESULT.json", "_P8D_DESIGNTREE"],
        ["scripts/p8d_qa_probe.py", "_P8D_ORACLE_A"],
        ["scripts/p8d_qa_probe.py", "_P8D_ORACLE_B"],
        ["scripts/p8d_reviewer_probe.py", "_P8D_ORACLE_A"],
        ["scripts/p8d_reviewer_probe.py", "_P8D_ORACLE_B"],
        ["tests/test_watchlist_delivery_policy.py", "_P8D_ORACLE_A"],
        ["tests/test_watchlist_delivery_policy.py", "_P8D_ORACLE_B"],
    ],
)
def test_p8d_exact_public_identifier_scope(path, key):
    value = SCANNER[key]
    candidate = {
        "type": "Hex High Entropy String",
        "hashed_secret": sha1(value.encode()).hexdigest(),
    }
    reviewed = SCANNER["_reviewed_public_candidate"]
    assert reviewed(path, candidate)
    assert not reviewed("unreviewed/" + path, candidate)
    assert not reviewed(path, {**candidate, "type": "Secret Keyword"})
    assert not reviewed(
        path, {**candidate, "hashed_secret": sha1(b"unknown-public-value").hexdigest()}
    )
