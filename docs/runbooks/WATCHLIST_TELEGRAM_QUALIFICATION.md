# P8d qualification wrapper - offline preparation, live still unauthorized

This supplements the accepted historical [design runbook](WATCHLIST_TELEGRAM_DELIVERY.md).
The Phase Lead authorized implementation and fake-only offline gates, not real
Telegram. Do not run validate/send with a production client or real credentials
without the later exact-selection operator/Orchestrator decision.

The implementation helper is scripts/watchlist_telegram_qualification.py.
Its preflight/replay/postflight default2s/max5s; validation/send default15s/max30s.
One Budget covers parsing, Git/local checks, reservations, product and encoding.
The product alone performs the single aggregate5s original admission on send;
there is no additional pre-send source recompute/hash stage outside that ceiling.
Request allowances are reduced again AFTER durable reservation before native
transport, so a blocked filesystem write cannot grant a renewed network timeout.

## Offline preflight

Use an exact reviewed clean repository commit/tree and an installed wheel outside
checkout. Independently prepare one genuine historical synthetic selection using
the frozen P8d CLI, exact original paths/manifest, immutable private route and
specific reviewed content acknowledgement. Do not auto-init, select latest,
compose arbitrary text or treat P8b-T17 as current permission.

Run only the preflight operation at this stage with operator-supplied local paths:

    python scripts/watchlist_telegram_qualification.py --operation preflight --directory NEW_PRIVATE_DIRECTORY --candidate-repository REVIEWED_CHECKOUT --candidate-head EXACT_HEAD --candidate-tree EXACT_TREE --ledger-db LEDGER --watchlist-db WATCHLIST --journal-db JOURNAL --outbox-db OUTBOX --manifest MANIFEST --delivery-id WTDL1 --timeout 5

It independently recomputes originals, checks unused ready/count0/nonquarantined
ledger, records complete selection commitments and source hashes, and exclusively
creates private dossier.json plus authorization-template.json. The template says
PENDING_NOT_AUTHORIZED. Public output is redacted and LIVE_UNVERIFIED.
Original source paths, alias and any receipt remain private; stdout must not be
mistaken for a human signature or phase acceptance.

## Separate future authorization and one-shot limits

After all offline gates/reviews and draft product PR, submit the sanitized dossier
to the Phase Lead/operator. Authorization must explicitly match its exact candidate,
qualification hash, alert/signal/watch/revision and message/evidence/route/full
binding commitments and historical acknowledgement. The operator privately creates
a separate authorization file with the documented exact decision/reference.
Do not paste a token or chat/bot IDs into chat/PR. No such authorization exists now.

Only after that separate decision may an operator inject the token through
protected local environment and use wrapper operations validate then send.
The wrapper requires the matching authorization, unchanged candidate, exact local
ledger identity/selection and no quarantine before creating a native client.
Append-only exclusive/fsynced hash-chained reservations occur BEFORE each narrow
method:destination validation2 metadata, bot validation1, send1attempt.
Cumulative caps are8metadata/1send; request upper bounds are distinguished from
actual successful completion counts. Failed methods expose no exact HTTP count.
Failure/crash never resets reservations; an orphan active marker blocks reuse.
There is no force, marker-reset or resend command. Any additional real attempt
requires a new explicit operator/Orchestrator decision.

No live calls are shown as an executable sequence here; the accepted runbook
contains the inert target commands and their prerequisites. Never bypass wrapper
reservations by calling the product directly during qualification. Even valid429
consumes the sole qualification send permission despite product max3 behavior.

## Evidence after future confirmation

A durable native receipt/confirmed state and one claim are required. Independently
run the offline postflight operation to compare source bytes to the preflight
snapshot. This is a separate2s/max5s evidence operation, not another admission
allowance inside send.

    python scripts/watchlist_telegram_qualification.py --operation postflight --directory PRIVATE_DIRECTORY --timeout 5

Remove the token and use replay; it spawns a separate interpreter with token
lookup, Telegram imports and sockets denied. It needs no originals and checks
the same durable private receipt, one attempt, no quarantine and unchanged
cumulative request counts.

    python scripts/watchlist_telegram_qualification.py --operation replay --directory PRIVATE_DIRECTORY --timeout 5

The wrapper keeps LIVE_UNVERIFIED even after accepted receipt: independent QA/
REVIEWER inspect sanitized evidence and the Phase Lead/Orchestrator decide.
Fakes and instrumentation are not independent traffic capture or human-read proof.

Windows directory fsync remains unsupported by the used API; file fsync/private
ACLs and trusted ancestors remain required. Crash residue is evidence, not cleanup
permission. Privileged coherent rewrites or independently cloned authorities are
outside authentication/dedup guarantees. TD-001..TD-005 remain OPEN.
