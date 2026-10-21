# Suggested top-of-file addition to `docs/ROADMAP.md` — do not replace historic entries

## Orchestrator chat decision: P4c closed, P8a open (2026-10-20)

The supplied [P8a phase contract](phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md)
records the 00 — ORCHESTRATOR's declaration that P4c is ACCEPTED / PHASE CLOSED
in chat and opens P8a Offline Alert Outbox. The completed P4c merge is
[PR12](https://github.com/KastaTM/card-market-tracker/pull/12), `main`
`b89fff319a94e5eb6e4b7bdad944e879bad371f6`, tree
`8f62a1d85b375ee839dcd95e09a578cb643c85b6`, ordered parents
`de63457bd6de26874a30d2afd688dcd8901e01ff` and
`9fb53144dec521d0dde49c02d41022be831421c2`. Historical P4c
[main CI run](https://github.com/KastaTM/card-market-tracker/actions/runs/39462043464)
is not P8a gate evidence. The decision is attributed to the Orchestrator **chat**;
no public GitHub closure comment is invented.

P8a permits only a separate SQLite offline pending outbox, deterministic
per-destination+evt3 alert identity with per-cmp3 frozen evidence, exact origin
recomputation before enqueue, local verification/recovery and safe read-only
preview. No Telegram or other transport, state transitions, scheduling or new
source acquisition is authorized. Preserve capture schema2, journal schema1,
original fingerprints and exact R0/R1+synthetic constraints. P2/P6a and retail
Discovery remain BLOCKED; P5/P8b have not been opened. TD-001–TD-005 remain
OPEN. P8a implementation, PR, gates, acceptance and eventual closure are
separate future decisions; do not infer success from this planning note.
