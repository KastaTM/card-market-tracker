# DB author reported pre-fix failure

Source: /root/p8c_freeze_db's retained tool transcript, reported to Lead.
No original raw stdout/stderr file exists. This record does not pretend one did.
Earlier working implementation was uncommitted; final candidate includes fix.

Command: .venv/Scripts/python.exe -m pytest tests/test_watchlist_alert_concurrency.py -q -k foreign_hot --tb=short
Exit1;1failed,4deselected in0.47s.

test_foreign_hot_journal_is_not_recovered_by_wrong_outbox_writer
tests/test_watchlist_alert_concurrency.py:238:
    assert journal.exists()
E   AssertionError: assert False

The wrong outbox rejected foreign ownership only after SQLite writable-open
recovered/deleted the foreign hot journal. Bounded CMTY/version header+inode
precheck now precedes writable-open. Final author real-process tests and
independent reviewer probe pass; genuine owned crash recovery is preserved.
