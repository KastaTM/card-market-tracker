# Offline alert outbox SQLite storage v1

Authority: [P8a](../phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md),
[ADR-0010](../adr/0010-offline-alert-outbox.md) and the
[alert API](ALERT_OUTBOX_V1.md). Captures schema2, journal schema1 and
all historical Discovery identifiers remain unchanged.

## Ownership and physical schema

The independent file uses application_id `0x434D5441` (CMTA), user_version1,
owner `card-market-tracker.alert-outbox`, DELETE journal mode and synchronous FULL
for writes. Inventory must exactly equal `alerts.schema.expected_inventory()`,
including SQLite-normalized DDL and every explicit/implicit index. Unknown or
altered objects, owner, version or journal mode fail without migration or repair.

Exactly three STRICT tables exist. All listed fields are NOT NULL.

| Table | Fields and constraints |
| --- | --- |
| outbox_metadata | singleton INTEGER PRIMARY KEY CHECK=1; exact owner TEXT; schema_version INTEGER CHECK=1; exactly one row |
| alerts | alert_id TEXT PRIMARY KEY length69; destination_key TEXT length1..64; event_id TEXT length69; channel TEXT CHECK offline_preview; policy_version TEXT CHECK discovery_reference_alert_v1; renderer_version INTEGER CHECK1; intent_json TEXT bytes2..65536; intent_sha256 TEXT length64; message_text TEXT bytes1..4096; message_sha256 TEXT length64; first_prepared_at TEXT length27; state TEXT CHECK pending; UNIQUE(destination_key,event_id) |
| alert_evidence | alert_id TEXT FK alerts ON DELETE RESTRICT; comparison_id TEXT length69; event_json TEXT bytes2..16777216; journal_content_sha256 and event_sha256 TEXT length64; PRIMARY KEY(alert_id,comparison_id) |

Index `evidence_by_comparison(comparison_id,alert_id)` supports comparison lookup.
No transport, retry, lease, acknowledgement, scheduler or deletion API exists.
Pending means prepared for possible future delivery. It records no delivery fact.

CHECK constraints complement strict Python validation. All returned TEXT receives
SQL typeof/byte-length guards before materialization, including inventory and
metadata. Inventory stops at expected count+1. Integer cells have exact semantic
type/range checks; SQLite LENGTH/SQL limits, defensive mode, trusted_schema OFF,
FK ON and progress/busy callbacks also apply. Read operations use mode=ro,
query_only and one transaction snapshot; missing DB/row is storage_missing.

## Canonical content and atomic admission

Canonical JSON is finite ASCII escaped, sorted keys and compact separators:
`json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',', ':'),allow_nan=False)`.
Digests are lowercase SHA-256 of exact canonical ASCII intent/event bytes, and
exact UTF-8 message bytes. Alert identity is `alt1:` plus SHA-256 of canonical
`{"identity_version":1,"destination_key":DESTINATION,"event_id":EVT3}`.
Destination grammar is `[a-z][a-z0-9_-]{0,63}`; alt1/cmp3/evt3 suffixes are exactly
64 lowercase hex characters. The intrinsic intent includes no destination,
comparison ID, history, preparation clock, renderer-dependent identity or path.
Renderer version is integer1. Intrinsic policy/renderer versions are frozen in
the intent and row; policy/renderer changes require a later migration contract.

Public enqueue requires explicit capture, journal and initialized outbox paths,
one cmp3 and one destination. Application reads/validates one complete journal
pair, freezes its canonical bytes, rereads original captures and uses the existing
pure comparator. The complete result and comparison ID must match those exact
frozen bytes. Only then does it issue a private content-bound receipt binding
comparison ID, journal digest and every prepared row. Raw JSON, IDs, DTOs, digest
or a verified flag grant no authority. Storage consumes the sealed receipt and
independently reconstructs every row using full standalone-event grammar and
pure policy/renderer. This is an application boundary, not a signature against
privileged code already executing inside the process.

One BEGIN IMMEDIATE transaction inserts every new alert and window association.
Existing alerts require identical complete intrinsic fields, versions, canonical
intent and frozen message. Existing associations require identical full event
and journal digest. Different intrinsic content or evidence is conflict; the
whole operation rolls back, including any preceding inserts. No overwrite occurs.
One comparison has one journal digest across all alerts/destinations. Alert first
preparation UTC stamp `YYYY-MM-DDTHH:MM:SS.ffffffZ` is local insertion time, and
never substitutes captured_at/acquisition/first observation. Replay preserves
that stamp and every byte of intent/message/evidence. It reports alerts_new,
alerts_existing, associations_new, associations_existing and events. Result is
inserted if at least one alert or association was inserted, otherwise replay.
Baseline/no_discoveries validates the outbox read-only and reports all zero
counts with replay; it writes no alert, evidence, timestamp or placeholder.

Verification occurs before outbox commit, without a distributed transaction.
The receipt represents the verified captured/journal content at that prior read
snapshot. Existing immutable capture/journal evidence is the compatibility
assumption. No current source acquisition occurs.

## Read interfaces, limits and local verification

Every response has integer version1, operation and result. get returns alert:
alert_id,destination_key,event_id,channel,policy_version,renderer_version,intent
(decoded),intent_sha256,message_text,message_sha256,first_prepared_at,state.
preview returns alert_id,message_text,renderer_version,policy_version,channel,state;
it neither consumes pending state nor increments attempts. evidence-get returns
alert_id,comparison_id,event (complete decoded event including window history),
journal_content_sha256,event_sha256. One explicit event is capped at16MiB.

list_alerts returns summaries containing all stored scalar fields except full
intent/message. Optional destination filter uses strict alias grammar.
evidence-list returns comparison_id,journal_content_sha256,event_sha256 for one
existing alert. Both use items and next_cursor, default100, nonbool limit1..1000,
ascending alt1/cmp3 keysets and maximum1MiB complete canonical response. The cursor
is the final returned key only if more rows exist. One page is one snapshot;
concurrent inserts before/equal cursor are not revisited, and later keys can
appear on later pages. Pages do not share a global snapshot. No unbounded fetchall
or entire-history collection is used. Alert summaries validate intrinsic content
without loading event histories. Evidence summaries do not claim origin proof.

Local verify checks ownership/inventory, integrity_check(1), FK consistency,
strict duplicate-aware finite JSON, canonical equality, grammar, identities,
versions, digests, timestamps, pending state and reconstructed renderer output.
Every alert must have evidence. Each complete event must belong to its parent
alert/comparison and reproduce all frozen intrinsic fields; comparison digests
must agree. It visits all rows or fails, never returns partial PASS. Success
has level local and counts alerts/associations. Coherent privileged rewriting can
still pass. Application recompute separately checks one explicit association
against the supplied journal and original capture DB and verifies the prepared
alert/evidence. Missing/changed origins fail even if local verification passes.

One enqueue <=1000 events and <=16MiB canonical prepared envelope, with no partial
success or splitting to evade limits. Intent ceiling64KiB and message4096 UTF-8
bytes apply independently. Default budget2s, explicit maximum5s, finite nonbool
numeric input. Enqueue shares one Budget across admission, preparation and SQL;
backup/restore and other operations also keep one budget. Busy/progress handlers
and loops are cooperative; stalled OS/device IO has no hard latency guarantee.
No global disk quota or automatic retention is introduced.

## Paths and recovery

Reuse vetted persistence path checks: trusted local ancestor directories, regular
single-link files; reject traversal, UNC/device/ADS/reserved names, symlink,
junction/reparse points, hardlinks and unsafe sidecars. Application rejects
aliases between all three databases. Existing-file opens compare identity before
and after. This assumes trusted directories; hostile administrator races and
Windows ACL limitations remain TD-003.

Only explicit init reserves a new private file. Init, backup and restore never
overwrite an existing destination or existing destination sidecar. Failure cleanup
removes only its own exclusively reserved inode; sidecars are never manually
deleted. Backup holds a validated source read transaction, uses SQLite backup,
validates the destination and reopens/validates it before success. Restore uses
the same rules with a new destination. Both preserve messages, versions, digests,
pending state and first clocks. Three DB backups are independent; restore all
matching originals and recompute explicit associations before asserting origin
verification. A process-kill recovery test does not certify physical power loss.

## Fixed errors

OutboxError retains only its category. Existing scoped input categories,
invalid_profile and conflict exit2; input_limit is a contract failure exit2.
Local input_io, unsafe_destination, storage_missing, storage_schema,
storage_corrupt, storage_locked, storage_timeout, storage_io and
recompute_mismatch exit1. Unknown category becomes invalid_field. Corrupt stored
JSON/intent/evidence maps to storage_corrupt. SQLite primary BUSY/LOCKED maps to
storage_locked, CORRUPT/NOTADB/TOOBIG to storage_corrupt, INTERRUPT to
storage_timeout, remaining failures to storage_io. Rollback disables expired
progress/busy handlers before cleanup. Logs expose only allowlisted operation,
run ID, result/category, duration and bounded counters, never raw exceptions,
SQL, messages, references, destination aliases or paths. Protect explicit stdout,
DBs and backups as local evidence.
