"""Only exact independently reviewed public digest candidates may be dismissed."""

import hashlib
import json
import runpy
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
