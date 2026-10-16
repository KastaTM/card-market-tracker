# Offline scoped capture Discovery

Use `cmt discover-scoped --db PATH --request REQUEST_JSON` for schema2 captures
already admitted with persisted scope. It does not initialize, migrate, repair,
acquire a source or change history. V1 retains its synthetic-only guard.

```json
{
  "version": 2,
  "context": {"namespace": "tcgdex_repository", "kind": "set", "language": "es"},
  "current": {"batch_id": "bd9cc4b8-eace-4567-8364-93cc4eccddc5", "selector": "swsh3"},
  "history": []
}
```

Select one exact persisted unit per batch and at most32 histories. Obtain selectors
and contexts from `cmt captures --db PATH --batch-id TOKEN`; no approximate
selection or wildcard null language. Paths inside scope are metadata never opened.
Scope, family and selected paths must match; every historical original captured_at
must precede current. Request indexes and observed admission claims are forbidden.

The licensed P1b package has four set/card ES/EN units and one fixed acquisition/
capture instant. Each history-free selection yields baseline without events after
all units/rows validate. A second import token retains that time and fails
chronology as history. Do not edit the package or clock to invent a transition.
A second real acquisition requires later authorization.

Positive examples use only synthetic `persist_capture` with producer_declared
scope. Complete empty units remain local declarations. Verified_local_pinned_bundle
means local reviewed-package equivalence, not independent truth or coverage.
No positive real provider transition has been demonstrated.

Success exits0: baseline/no_discoveries/discoveries. Invalid request, missing/
ambiguous unit, scope/chronology, incomplete/unsupported evidence exit2.
Storage/schema/corruption/lock/deadline/IO exit1. Errors have counts null/events
empty; never interpret failure as no discoveries. Partial/failed, selected rejects,
missing artifact/translation, legacy/schema1 cannot become complete empty evidence.

Read budget defaults to2 seconds (Python maximum5). A rollback-journal reader may
delay writer commit; whole-DB integrity work may exceed budgets as history grows.
Stalled OS/device calls remain outside deadline guarantees. Preserve journals;
investigate lock/corruption using the storage runbook and verified backups.
Discovery never repairs, resets, migrates or deletes journals.

Protect trusted local directories, stdout and backups. Stdout includes contracted
references/tokens/paths/frozen targets; stderr contains only allowlisted operation
counts/categories/correlation. cmp2/evt2 prove equality, not authenticity or
exactly-once delivery. No event store, alerts or identity promotion exist.

Build/install the wheel outside source and run that environment's Python with
`scripts/scoped_capture_discovery_smoke.py --mode installed --fixtures ABS_PATH`.
The harness checks installed import, socket denial, distinct seed/compare
processes, synthetic transitions, real baselines/equal-time error, v1 guard,
complete logical/schema nonmutation and backup/restore equivalence.

Compose uses `--mode compose`; Docker uses `--mode docker --image IMAGE --platform
linux/amd64` or linux/arm64 after the respective build. Fixtures are readonly,
network disabled, UID/GID10001, /data0700 and unique disposable volumes. Only the
harness-owned volume is removed. Never use a user DB or production volume.
All prior harnesses remain required. ARM64/QEMU is emulation, not Pi hardware or
electrical power-loss certification.
