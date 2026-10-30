# Watchlist Telegram Delivery Storage v1 - proposed design

**Status: PROPOSED / NOT ACCEPTED.** Date: 2026-10-30. Gate B documentation
candidate. No product schema/writer or definitive identity implementation is
permitted by this document. Phase Lead design acceptance remains pending.
Authorities: [P8d contract](../phases/P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md),
[API v1](WATCHLIST_TELEGRAM_DELIVERY_V1.md), [ADR-0015](../adr/0015-manual-watchlist-telegram-delivery.md).
Only the Orchestrator accepts/closes phases.

MODEL PROFILE USED: DB-OWNER requested GPT-6.1 Sol/High; observable selection
`model=gpt-6.1-sol`, `reasoning_effort=high`; effective backend/effort unverified.
Exclusive authorship: this document. Author in-memory design probes below are
neither independent QA nor product gates or live authorization.

## 1. Separate owner, allocation and connection contract

Candidate owner `card-market-tracker.watchlist-telegram-delivery`, application_id
`0x434D545A` (CMTZ, decimal1129141338), user_version=1/schema_version=1.
2026-10-30 baseline `9dda9fba0aa9646a67596657d4ae9a7088903808` static source audit:
`rg -n 'APPLICATION_ID|OWNER =|application_id|434D545A|CMTZ' src docs/adr docs/data-contracts`.
Existing allocations: CMT1/0x434D5431/card-market-tracker;
CMTA/0x434D5441/card-market-tracker.alert-outbox;
CMTD/0x434D5444/card-market-tracker.telegram-delivery;
CMTJ/0x434D544A/card-market-tracker.discovery-journal;
CMTQ/0x434D5451/card-market-tracker.watchlist-journal;
CMTW/0x434D5457/card-market-tracker.watchlist;
CMTY/0x434D5459/card-market-tracker.watchlist-alert-outbox.
CMTZ has no prior source allocation; no private database inspection is claimed.
Adoption awaits acceptance. No migration or prior schema/writer/identity changes.

Existing URI mode=ro/query_only=ON/explicit BEGIN for reads; mode=rw and
BEGIN IMMEDIATE for writes. Init alone reserves a new private regular file.
Require DELETE journal mode, FULL synchronous writers, foreign_keys=ON verified,
trusted_schema=OFF, defensive mode, no extension loading. Limits LENGTH524288,
SQL_LENGTH65536; no WAL, ANALYZE, input SQL or automatic repair/migration.
Whole-history verification may legitimately time out; partial checking never
permits commit/send. Data SQL is parameterized. No transaction spans HTTP.

## 2. Literal proposed SQL

Each numbered sql fence is one ordered statement, UTF-8/LF, no final semicolon
or newline inside the entry. Future constants must reproduce these strings
exactly. No JSON extension or Python UDF. SQL checks supplement canonical JSON,
Gregorian UTC, semantic hash/original admission and exact Python type checks;
STRICT affinity does not authorize coercion or bool-as-int at public boundaries.

<!-- P8D_DDL_BEGIN -->

Statement 1:

```sql
CREATE TABLE wtd_metadata (
    singleton INTEGER PRIMARY KEY NOT NULL CHECK(singleton=1),
    owner TEXT NOT NULL CHECK(owner='card-market-tracker.watchlist-telegram-delivery'),
    schema_version INTEGER NOT NULL CHECK(schema_version=1),
    send_quarantined INTEGER NOT NULL CHECK(send_quarantined IN (0,1)),
    operational_high_water TEXT NOT NULL CHECK(typeof(operational_high_water)='text' AND length(CAST(operational_high_water AS BLOB))=27 AND operational_high_water GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z')
) STRICT
```

Statement 2:

```sql
CREATE TABLE wtd_destinations (
    destination_key TEXT PRIMARY KEY NOT NULL CHECK(typeof(destination_key)='text' AND length(CAST(destination_key AS BLOB)) BETWEEN 1 AND 64 AND length(destination_key)=length(CAST(destination_key AS BLOB)) AND substr(destination_key,1,1) GLOB '[a-z]' AND destination_key NOT GLOB '*[^a-z0-9_-]*'),
    provider TEXT NOT NULL CHECK(provider='telegram'),
    bot_id INTEGER NOT NULL CHECK(typeof(bot_id)='integer' AND bot_id BETWEEN 1 AND 4503599627370495),
    chat_id INTEGER NOT NULL CHECK(typeof(chat_id)='integer' AND chat_id BETWEEN 1 AND 4503599627370495),
    chat_type TEXT NOT NULL CHECK(chat_type='private'),
    operator_attested INTEGER NOT NULL CHECK(operator_attested=1),
    route_json TEXT NOT NULL CHECK(typeof(route_json)='text' AND length(CAST(route_json AS BLOB)) BETWEEN 2 AND 2048),
    route_sha256 TEXT NOT NULL CHECK(typeof(route_sha256)='text' AND length(CAST(route_sha256 AS BLOB))=64 AND route_sha256 NOT GLOB '*[^0-9a-f]*'),
    registered_at TEXT NOT NULL CHECK(typeof(registered_at)='text' AND length(CAST(registered_at AS BLOB))=27 AND registered_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),
    validated_at TEXT CHECK(validated_at IS NULL OR (typeof(validated_at)='text' AND length(CAST(validated_at AS BLOB))=27 AND validated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z')),
    UNIQUE(destination_key,route_sha256)
) STRICT
```

Statement 3:

```sql
CREATE TABLE wtd_watch_entries (
    watch_id TEXT NOT NULL CHECK(typeof(watch_id)='text' AND length(CAST(watch_id AS BLOB))=69 AND length(watch_id)=69 AND substr(watch_id,1,5)='wlt1_' AND substr(watch_id,6) NOT GLOB '*[^0-9a-f]*'),
    revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision BETWEEN 1 AND 2147483647),
    entry_json TEXT NOT NULL CHECK(typeof(entry_json)='text' AND length(CAST(entry_json AS BLOB)) BETWEEN 2 AND 65536),
    entry_sha256 TEXT NOT NULL CHECK(typeof(entry_sha256)='text' AND length(CAST(entry_sha256 AS BLOB))=64 AND entry_sha256 NOT GLOB '*[^0-9a-f]*'),
    PRIMARY KEY(watch_id,revision),
    UNIQUE(watch_id,revision,entry_sha256)
) STRICT
```

Statement 4:

```sql
CREATE TABLE wtd_deliveries (
    delivery_id TEXT PRIMARY KEY NOT NULL CHECK(typeof(delivery_id)='text' AND length(CAST(delivery_id AS BLOB))=70 AND length(delivery_id)=70 AND substr(delivery_id,1,6)='wtdl1_' AND substr(delivery_id,7) NOT GLOB '*[^0-9a-f]*'),
    provider TEXT NOT NULL CHECK(provider='telegram'),
    alert_id TEXT NOT NULL CHECK(typeof(alert_id)='text' AND length(CAST(alert_id AS BLOB))=70 AND length(alert_id)=70 AND substr(alert_id,1,6)='walt1_' AND substr(alert_id,7) NOT GLOB '*[^0-9a-f]*'),
    destination_key TEXT NOT NULL CHECK(typeof(destination_key)='text' AND length(CAST(destination_key AS BLOB)) BETWEEN 1 AND 64 AND length(destination_key)=length(CAST(destination_key AS BLOB)) AND substr(destination_key,1,1) GLOB '[a-z]' AND destination_key NOT GLOB '*[^a-z0-9_-]*'),
    signal_id TEXT NOT NULL CHECK(typeof(signal_id)='text' AND length(CAST(signal_id AS BLOB))=70 AND length(signal_id)=70 AND substr(signal_id,1,6)='wsig1_' AND substr(signal_id,7) NOT GLOB '*[^0-9a-f]*'),
    watch_id TEXT NOT NULL CHECK(typeof(watch_id)='text' AND length(CAST(watch_id AS BLOB))=69 AND length(watch_id)=69 AND substr(watch_id,1,5)='wlt1_' AND substr(watch_id,6) NOT GLOB '*[^0-9a-f]*'),
    revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision BETWEEN 1 AND 2147483647),
    cmt_id TEXT NOT NULL CHECK(typeof(cmt_id)='text' AND length(CAST(cmt_id AS BLOB))=36 AND length(cmt_id)=36 AND cmt_id NOT GLOB '*[^0-9a-f-]*'),
    policy_version TEXT NOT NULL CHECK(policy_version='watchlist_synthetic_alert_v1'),
    renderer_version INTEGER NOT NULL CHECK(renderer_version=1),
    intent_json TEXT NOT NULL CHECK(typeof(intent_json)='text' AND length(CAST(intent_json AS BLOB)) BETWEEN 2 AND 65536),
    evidence_json TEXT NOT NULL CHECK(typeof(evidence_json)='text' AND length(CAST(evidence_json AS BLOB)) BETWEEN 2 AND 262144),
    message_text TEXT NOT NULL CHECK(typeof(message_text)='text' AND length(CAST(message_text AS BLOB)) BETWEEN 1 AND 4096),
    consent_json TEXT NOT NULL CHECK(typeof(consent_json)='text' AND length(CAST(consent_json AS BLOB)) BETWEEN 2 AND 4096),
    binding_json TEXT NOT NULL CHECK(typeof(binding_json)='text' AND length(CAST(binding_json AS BLOB)) BETWEEN 2 AND 8192),
    intent_sha256 TEXT NOT NULL CHECK(typeof(intent_sha256)='text' AND length(CAST(intent_sha256 AS BLOB))=64 AND intent_sha256 NOT GLOB '*[^0-9a-f]*'),
    evidence_sha256 TEXT NOT NULL CHECK(typeof(evidence_sha256)='text' AND length(CAST(evidence_sha256 AS BLOB))=64 AND evidence_sha256 NOT GLOB '*[^0-9a-f]*'),
    message_sha256 TEXT NOT NULL CHECK(typeof(message_sha256)='text' AND length(CAST(message_sha256 AS BLOB))=64 AND message_sha256 NOT GLOB '*[^0-9a-f]*'),
    entry_sha256 TEXT NOT NULL CHECK(typeof(entry_sha256)='text' AND length(CAST(entry_sha256 AS BLOB))=64 AND entry_sha256 NOT GLOB '*[^0-9a-f]*'),
    source_alert_sha256 TEXT NOT NULL CHECK(typeof(source_alert_sha256)='text' AND length(CAST(source_alert_sha256 AS BLOB))=64 AND source_alert_sha256 NOT GLOB '*[^0-9a-f]*'),
    route_sha256 TEXT NOT NULL CHECK(typeof(route_sha256)='text' AND length(CAST(route_sha256 AS BLOB))=64 AND route_sha256 NOT GLOB '*[^0-9a-f]*'),
    consent_sha256 TEXT NOT NULL CHECK(typeof(consent_sha256)='text' AND length(CAST(consent_sha256 AS BLOB))=64 AND consent_sha256 NOT GLOB '*[^0-9a-f]*'),
    binding_sha256 TEXT NOT NULL CHECK(typeof(binding_sha256)='text' AND length(CAST(binding_sha256 AS BLOB))=64 AND binding_sha256 NOT GLOB '*[^0-9a-f]*'),
    prepared_at TEXT NOT NULL CHECK(typeof(prepared_at)='text' AND length(CAST(prepared_at AS BLOB))=27 AND prepared_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),
    UNIQUE(provider,signal_id),
    FOREIGN KEY(destination_key,route_sha256) REFERENCES wtd_destinations(destination_key,route_sha256) ON DELETE RESTRICT,
    FOREIGN KEY(watch_id,revision,entry_sha256) REFERENCES wtd_watch_entries(watch_id,revision,entry_sha256) ON DELETE RESTRICT
) STRICT
```

Statement 5:

```sql
CREATE TABLE wtd_state (
    delivery_id TEXT PRIMARY KEY NOT NULL REFERENCES wtd_deliveries(delivery_id) ON DELETE RESTRICT CHECK(typeof(delivery_id)='text' AND length(CAST(delivery_id AS BLOB))=70 AND length(delivery_id)=70 AND substr(delivery_id,1,6)='wtdl1_' AND substr(delivery_id,7) NOT GLOB '*[^0-9a-f]*'),
    state TEXT NOT NULL CHECK(state IN ('ready','in_flight','retryable','confirmed','permanent_failure','uncertain')),
    attempt_count INTEGER NOT NULL CHECK(typeof(attempt_count)='integer' AND attempt_count BETWEEN 0 AND 3),
    current_attempt_id TEXT CHECK(current_attempt_id IS NULL OR (typeof(current_attempt_id)='text' AND length(CAST(current_attempt_id AS BLOB))=70 AND length(current_attempt_id)=70 AND substr(current_attempt_id,1,6)='wtat1_' AND substr(current_attempt_id,7) NOT GLOB '*[^0-9a-f]*')),
    current_owner TEXT CHECK(current_owner IS NULL OR (typeof(current_owner)='text' AND length(CAST(current_owner AS BLOB))=64 AND current_owner NOT GLOB '*[^0-9a-f]*')),
    not_before TEXT CHECK(not_before IS NULL OR (typeof(not_before)='text' AND length(CAST(not_before AS BLOB))=27 AND not_before GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z')),
    updated_at TEXT NOT NULL CHECK(typeof(updated_at)='text' AND length(CAST(updated_at AS BLOB))=27 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),
    FOREIGN KEY(current_attempt_id) REFERENCES wtd_claims(attempt_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    CHECK((state='in_flight' AND current_attempt_id IS NOT NULL AND current_owner IS NOT NULL) OR (state!='in_flight' AND current_attempt_id IS NULL AND current_owner IS NULL)),
    CHECK((state='retryable' AND not_before IS NOT NULL AND attempt_count<3) OR (state!='retryable' AND not_before IS NULL)),
    CHECK((state='ready' AND attempt_count=0) OR (state!='ready' AND attempt_count>0))
) STRICT
```

Statement 6:

```sql
CREATE TABLE wtd_claims (
    attempt_id TEXT PRIMARY KEY NOT NULL CHECK(typeof(attempt_id)='text' AND length(CAST(attempt_id AS BLOB))=70 AND length(attempt_id)=70 AND substr(attempt_id,1,6)='wtat1_' AND substr(attempt_id,7) NOT GLOB '*[^0-9a-f]*'),
    delivery_id TEXT NOT NULL REFERENCES wtd_deliveries(delivery_id) ON DELETE RESTRICT CHECK(typeof(delivery_id)='text' AND length(CAST(delivery_id AS BLOB))=70 AND length(delivery_id)=70 AND substr(delivery_id,1,6)='wtdl1_' AND substr(delivery_id,7) NOT GLOB '*[^0-9a-f]*'),
    owner TEXT NOT NULL CHECK(typeof(owner)='text' AND length(CAST(owner AS BLOB))=64 AND owner NOT GLOB '*[^0-9a-f]*'),
    ordinal INTEGER NOT NULL CHECK(typeof(ordinal)='integer' AND ordinal BETWEEN 1 AND 3),
    claimed_at TEXT NOT NULL CHECK(typeof(claimed_at)='text' AND length(CAST(claimed_at AS BLOB))=27 AND claimed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),
    route_validated_at TEXT NOT NULL CHECK(typeof(route_validated_at)='text' AND length(CAST(route_validated_at AS BLOB))=27 AND route_validated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),
    UNIQUE(delivery_id,ordinal),
    UNIQUE(owner)
) STRICT
```

Statement 7:

```sql
CREATE TABLE wtd_results (
    attempt_id TEXT PRIMARY KEY NOT NULL REFERENCES wtd_claims(attempt_id) ON DELETE RESTRICT CHECK(typeof(attempt_id)='text' AND length(CAST(attempt_id AS BLOB))=70 AND length(attempt_id)=70 AND substr(attempt_id,1,6)='wtat1_' AND substr(attempt_id,7) NOT GLOB '*[^0-9a-f]*'),
    owner TEXT NOT NULL CHECK(typeof(owner)='text' AND length(CAST(owner AS BLOB))=64 AND owner NOT GLOB '*[^0-9a-f]*'),
    state TEXT NOT NULL CHECK(state IN ('confirmed','retryable','permanent_failure','uncertain')),
    completed_at TEXT NOT NULL CHECK(typeof(completed_at)='text' AND length(CAST(completed_at AS BLOB))=27 AND completed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),
    error_category TEXT CHECK(error_category IS NULL OR (error_category IN ('rate_limited','retry_exhausted','provider_rejection','network_uncertain','transport_timeout','transport_failure','provider_invalid','bot_mismatch','destination_mismatch','recovered','clock_skew','token_configuration','local_commit_failed','deadline_exceeded'))),
    retry_after INTEGER CHECK(retry_after IS NULL OR (typeof(retry_after)='integer' AND retry_after BETWEEN 1 AND 86400)),
    not_before TEXT CHECK(not_before IS NULL OR (typeof(not_before)='text' AND length(CAST(not_before AS BLOB))=27 AND not_before GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z')),
    message_id INTEGER CHECK(message_id IS NULL OR (typeof(message_id)='integer' AND message_id BETWEEN 1 AND 9223372036854775807)),
    accepted_at INTEGER CHECK(accepted_at IS NULL OR (typeof(accepted_at)='integer' AND accepted_at BETWEEN 1 AND 253402300799)),
    bot_id INTEGER CHECK(bot_id IS NULL OR (typeof(bot_id)='integer' AND bot_id BETWEEN 1 AND 4503599627370495)),
    chat_id INTEGER CHECK(chat_id IS NULL OR (typeof(chat_id)='integer' AND chat_id BETWEEN 1 AND 4503599627370495)),
    CHECK((state='confirmed' AND error_category IS NULL AND retry_after IS NULL AND not_before IS NULL AND message_id IS NOT NULL AND accepted_at IS NOT NULL AND bot_id IS NOT NULL AND chat_id IS NOT NULL) OR (state!='confirmed' AND error_category IS NOT NULL AND message_id IS NULL AND accepted_at IS NULL AND bot_id IS NULL AND chat_id IS NULL)),
    CHECK((state='retryable' AND error_category='rate_limited' AND retry_after IS NOT NULL AND not_before IS NOT NULL) OR (state='permanent_failure' AND error_category='retry_exhausted' AND retry_after IS NOT NULL AND not_before IS NULL) OR (state='permanent_failure' AND error_category='provider_rejection' AND retry_after IS NULL AND not_before IS NULL) OR (state='uncertain' AND error_category IN ('network_uncertain','transport_timeout','transport_failure','provider_invalid','bot_mismatch','destination_mismatch','recovered','clock_skew','token_configuration','local_commit_failed','deadline_exceeded') AND retry_after IS NULL AND not_before IS NULL) OR state='confirmed')
) STRICT
```

Statement 8:

```sql
CREATE INDEX wtd_deliveries_by_destination ON wtd_deliveries(destination_key,delivery_id)
```

Statement 9:

```sql
CREATE INDEX wtd_deliveries_by_watch ON wtd_deliveries(watch_id,revision,delivery_id)
```

Statement 10:

```sql
CREATE INDEX wtd_state_by_state ON wtd_state(state,delivery_id)
```

Statement 11:

```sql
CREATE TRIGGER wtd_metadata_update_guard BEFORE UPDATE ON wtd_metadata
WHEN NEW.singleton!=OLD.singleton OR NEW.owner!=OLD.owner OR NEW.schema_version!=OLD.schema_version OR NEW.send_quarantined<OLD.send_quarantined OR NEW.operational_high_water<OLD.operational_high_water
BEGIN SELECT RAISE(ABORT,'immutable_metadata'); END
```

Statement 12:

```sql
CREATE TRIGGER wtd_destinations_update_guard BEFORE UPDATE ON wtd_destinations
WHEN NEW.destination_key!=OLD.destination_key OR NEW.provider!=OLD.provider OR NEW.bot_id!=OLD.bot_id OR NEW.chat_id!=OLD.chat_id OR NEW.chat_type!=OLD.chat_type OR NEW.operator_attested!=OLD.operator_attested OR NEW.route_json!=OLD.route_json OR NEW.route_sha256!=OLD.route_sha256 OR NEW.registered_at!=OLD.registered_at OR NEW.validated_at IS NULL OR NEW.validated_at<coalesce(OLD.validated_at,OLD.registered_at) OR NEW.validated_at<(SELECT operational_high_water FROM wtd_metadata WHERE singleton=1)
BEGIN SELECT RAISE(ABORT,'immutable_route'); END
```

Statement 13:

```sql
CREATE TRIGGER wtd_destinations_insert_guard BEFORE INSERT ON wtd_destinations
WHEN NEW.validated_at IS NOT NULL OR NEW.registered_at<(SELECT operational_high_water FROM wtd_metadata WHERE singleton=1)
BEGIN SELECT RAISE(ABORT,'invalid_route_registration'); END
```

Statement 14:

```sql
CREATE TRIGGER wtd_destinations_insert_clock AFTER INSERT ON wtd_destinations
BEGIN UPDATE wtd_metadata SET operational_high_water=NEW.registered_at WHERE singleton=1; END
```

Statement 15:

```sql
CREATE TRIGGER wtd_destinations_validate_clock AFTER UPDATE ON wtd_destinations
BEGIN UPDATE wtd_metadata SET operational_high_water=NEW.validated_at WHERE singleton=1; END
```

Statement 16:

```sql
CREATE TRIGGER wtd_deliveries_insert_guard BEFORE INSERT ON wtd_deliveries
WHEN NEW.prepared_at<(SELECT operational_high_water FROM wtd_metadata WHERE singleton=1)
BEGIN SELECT RAISE(ABORT,'clock_skew'); END
```

Statement 17:

```sql
CREATE TRIGGER wtd_deliveries_insert_state AFTER INSERT ON wtd_deliveries
BEGIN
    INSERT INTO wtd_state(delivery_id,state,attempt_count,current_attempt_id,current_owner,not_before,updated_at) VALUES(NEW.delivery_id,'ready',0,NULL,NULL,NULL,NEW.prepared_at);
    UPDATE wtd_metadata SET operational_high_water=NEW.prepared_at WHERE singleton=1;
END
```

Statement 18:

```sql
CREATE TRIGGER wtd_state_insert_guard BEFORE INSERT ON wtd_state
WHEN NEW.state!='ready' OR NEW.attempt_count!=0 OR NEW.current_attempt_id IS NOT NULL OR NEW.current_owner IS NOT NULL OR NEW.not_before IS NOT NULL OR NEW.updated_at IS NOT (SELECT prepared_at FROM wtd_deliveries WHERE delivery_id=NEW.delivery_id) OR EXISTS(SELECT 1 FROM wtd_claims WHERE delivery_id=NEW.delivery_id)
BEGIN SELECT RAISE(ABORT,'invalid_initial_state'); END
```

Statement 19:

```sql
CREATE TRIGGER wtd_state_update_guard BEFORE UPDATE ON wtd_state
WHEN NEW.delivery_id!=OLD.delivery_id OR NOT (
    (OLD.state IN ('ready','retryable') AND NEW.state='in_flight' AND NEW.attempt_count=OLD.attempt_count+1 AND NEW.not_before IS NULL AND EXISTS(SELECT 1 FROM wtd_claims c WHERE c.attempt_id=NEW.current_attempt_id AND c.delivery_id=OLD.delivery_id AND c.owner=NEW.current_owner AND c.ordinal=NEW.attempt_count AND c.claimed_at=NEW.updated_at AND NOT EXISTS(SELECT 1 FROM wtd_results r WHERE r.attempt_id=c.attempt_id)))
    OR (OLD.state='in_flight' AND NEW.attempt_count=OLD.attempt_count AND NEW.current_attempt_id IS NULL AND NEW.current_owner IS NULL AND EXISTS(SELECT 1 FROM wtd_results r WHERE r.attempt_id=OLD.current_attempt_id AND r.owner=OLD.current_owner AND r.state=NEW.state AND r.completed_at=NEW.updated_at AND r.not_before IS NEW.not_before))
)
BEGIN SELECT RAISE(ABORT,'invalid_state_transition'); END
```

Statement 20:

```sql
CREATE TRIGGER wtd_claims_insert_guard BEFORE INSERT ON wtd_claims
WHEN NOT EXISTS(
    SELECT 1 FROM wtd_state s JOIN wtd_deliveries d ON d.delivery_id=s.delivery_id JOIN wtd_destinations x ON x.destination_key=d.destination_key JOIN wtd_watch_entries e ON e.watch_id=d.watch_id AND e.revision=d.revision AND e.entry_sha256=d.entry_sha256 JOIN wtd_metadata m ON m.singleton=1
    WHERE s.delivery_id=NEW.delivery_id AND m.send_quarantined=0 AND s.state IN ('ready','retryable') AND s.attempt_count<3 AND NEW.ordinal=s.attempt_count+1 AND s.current_attempt_id IS NULL AND s.current_owner IS NULL AND x.validated_at IS NOT NULL AND NEW.route_validated_at=x.validated_at AND NEW.claimed_at>=NEW.route_validated_at AND NEW.claimed_at>=s.updated_at AND NEW.claimed_at>=m.operational_high_water AND (s.not_before IS NULL OR NEW.claimed_at>=s.not_before) AND (SELECT count(*) FROM wtd_claims c WHERE c.delivery_id=s.delivery_id)=s.attempt_count
)
BEGIN SELECT RAISE(ABORT,'claim_refused'); END
```

Statement 21:

```sql
CREATE TRIGGER wtd_claims_insert_state AFTER INSERT ON wtd_claims
BEGIN
    UPDATE wtd_state SET state='in_flight',attempt_count=NEW.ordinal,current_attempt_id=NEW.attempt_id,current_owner=NEW.owner,not_before=NULL,updated_at=NEW.claimed_at WHERE delivery_id=NEW.delivery_id AND state IN ('ready','retryable') AND attempt_count=NEW.ordinal-1 AND current_attempt_id IS NULL AND current_owner IS NULL;
    SELECT CASE WHEN changes()!=1 THEN RAISE(ABORT,'stale_attempt') END;
    UPDATE wtd_metadata SET operational_high_water=NEW.claimed_at WHERE singleton=1;
END
```

Statement 22:

```sql
CREATE TRIGGER wtd_results_insert_guard BEFORE INSERT ON wtd_results
WHEN NOT EXISTS(
    SELECT 1 FROM wtd_claims c JOIN wtd_state s ON s.delivery_id=c.delivery_id JOIN wtd_metadata m ON m.singleton=1 JOIN wtd_deliveries d ON d.delivery_id=c.delivery_id JOIN wtd_destinations x ON x.destination_key=d.destination_key
    WHERE c.attempt_id=NEW.attempt_id AND c.owner=NEW.owner AND s.state='in_flight' AND s.current_attempt_id=c.attempt_id AND s.current_owner=NEW.owner AND s.attempt_count=c.ordinal AND NEW.completed_at>=c.claimed_at AND NEW.completed_at>=m.operational_high_water
    AND (NEW.state!='retryable' OR (c.ordinal<3 AND NEW.not_before IS (strftime('%Y-%m-%dT%H:%M:%S',substr(NEW.completed_at,1,19),printf('+%d seconds',NEW.retry_after)) || substr(NEW.completed_at,20))))
    AND (NEW.error_category IS NOT 'retry_exhausted' OR c.ordinal=3)
    AND (NEW.state!='confirmed' OR (NEW.bot_id=x.bot_id AND NEW.chat_id=x.chat_id))
)
BEGIN SELECT RAISE(ABORT,'stale_attempt'); END
```

Statement 23:

```sql
CREATE TRIGGER wtd_results_insert_state AFTER INSERT ON wtd_results
BEGIN
    UPDATE wtd_state SET state=NEW.state,current_attempt_id=NULL,current_owner=NULL,not_before=NEW.not_before,updated_at=NEW.completed_at WHERE current_attempt_id=NEW.attempt_id AND current_owner=NEW.owner AND state='in_flight';
    SELECT CASE WHEN changes()!=1 THEN RAISE(ABORT,'stale_attempt') END;
    UPDATE wtd_metadata SET operational_high_water=NEW.completed_at WHERE singleton=1;
END
```

Statement 24:

```sql
CREATE TRIGGER wtd_watch_entries_no_update BEFORE UPDATE ON wtd_watch_entries BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 25:

```sql
CREATE TRIGGER wtd_deliveries_no_update BEFORE UPDATE ON wtd_deliveries BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 26:

```sql
CREATE TRIGGER wtd_claims_no_update BEFORE UPDATE ON wtd_claims BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 27:

```sql
CREATE TRIGGER wtd_results_no_update BEFORE UPDATE ON wtd_results BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 28:

```sql
CREATE TRIGGER wtd_metadata_no_delete BEFORE DELETE ON wtd_metadata BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 29:

```sql
CREATE TRIGGER wtd_destinations_no_delete BEFORE DELETE ON wtd_destinations BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 30:

```sql
CREATE TRIGGER wtd_watch_entries_no_delete BEFORE DELETE ON wtd_watch_entries BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 31:

```sql
CREATE TRIGGER wtd_deliveries_no_delete BEFORE DELETE ON wtd_deliveries BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 32:

```sql
CREATE TRIGGER wtd_state_no_delete BEFORE DELETE ON wtd_state BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 33:

```sql
CREATE TRIGGER wtd_claims_no_delete BEFORE DELETE ON wtd_claims BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

Statement 34:

```sql
CREATE TRIGGER wtd_results_no_delete BEFORE DELETE ON wtd_results BEGIN SELECT RAISE(ABORT,'immutable_record'); END
```

<!-- P8D_DDL_END -->

## 3. Exact expected catalog

Expected 45 objects: 7 STRICT tables, 14 indexes, 24 triggers. Non-NULL SQL must equal its literal numbered statement byte for byte; implicit-index SQL is NULL. No views/sqlite_sequence/sqlite_stat/extra objects or semantic-equivalence tolerance.

| type | name | tbl_name | SQL authority |
| --- | --- | --- | --- |
| index | sqlite_autoindex_wtd_claims_1 | wtd_claims | NULL |
| index | sqlite_autoindex_wtd_claims_2 | wtd_claims | NULL |
| index | sqlite_autoindex_wtd_claims_3 | wtd_claims | NULL |
| index | sqlite_autoindex_wtd_deliveries_1 | wtd_deliveries | NULL |
| index | sqlite_autoindex_wtd_deliveries_2 | wtd_deliveries | NULL |
| index | sqlite_autoindex_wtd_destinations_1 | wtd_destinations | NULL |
| index | sqlite_autoindex_wtd_destinations_2 | wtd_destinations | NULL |
| index | sqlite_autoindex_wtd_results_1 | wtd_results | NULL |
| index | sqlite_autoindex_wtd_state_1 | wtd_state | NULL |
| index | sqlite_autoindex_wtd_watch_entries_1 | wtd_watch_entries | NULL |
| index | sqlite_autoindex_wtd_watch_entries_2 | wtd_watch_entries | NULL |
| index | wtd_deliveries_by_destination | wtd_deliveries | statement 8 |
| index | wtd_deliveries_by_watch | wtd_deliveries | statement 9 |
| index | wtd_state_by_state | wtd_state | statement 10 |
| table | wtd_claims | wtd_claims | statement 6 |
| table | wtd_deliveries | wtd_deliveries | statement 4 |
| table | wtd_destinations | wtd_destinations | statement 2 |
| table | wtd_metadata | wtd_metadata | statement 1 |
| table | wtd_results | wtd_results | statement 7 |
| table | wtd_state | wtd_state | statement 5 |
| table | wtd_watch_entries | wtd_watch_entries | statement 3 |
| trigger | wtd_claims_insert_guard | wtd_claims | statement 20 |
| trigger | wtd_claims_insert_state | wtd_claims | statement 21 |
| trigger | wtd_claims_no_delete | wtd_claims | statement 33 |
| trigger | wtd_claims_no_update | wtd_claims | statement 26 |
| trigger | wtd_deliveries_insert_guard | wtd_deliveries | statement 16 |
| trigger | wtd_deliveries_insert_state | wtd_deliveries | statement 17 |
| trigger | wtd_deliveries_no_delete | wtd_deliveries | statement 31 |
| trigger | wtd_deliveries_no_update | wtd_deliveries | statement 25 |
| trigger | wtd_destinations_insert_clock | wtd_destinations | statement 14 |
| trigger | wtd_destinations_insert_guard | wtd_destinations | statement 13 |
| trigger | wtd_destinations_no_delete | wtd_destinations | statement 29 |
| trigger | wtd_destinations_update_guard | wtd_destinations | statement 12 |
| trigger | wtd_destinations_validate_clock | wtd_destinations | statement 15 |
| trigger | wtd_metadata_no_delete | wtd_metadata | statement 28 |
| trigger | wtd_metadata_update_guard | wtd_metadata | statement 11 |
| trigger | wtd_results_insert_guard | wtd_results | statement 22 |
| trigger | wtd_results_insert_state | wtd_results | statement 23 |
| trigger | wtd_results_no_delete | wtd_results | statement 34 |
| trigger | wtd_results_no_update | wtd_results | statement 27 |
| trigger | wtd_state_insert_guard | wtd_state | statement 18 |
| trigger | wtd_state_no_delete | wtd_state | statement 32 |
| trigger | wtd_state_update_guard | wtd_state | statement 19 |
| trigger | wtd_watch_entries_no_delete | wtd_watch_entries | statement 30 |
| trigger | wtd_watch_entries_no_update | wtd_watch_entries | statement 24 |

Compare all four guarded sqlite_master columns ordered by type,name with
LIMIT(expected_count+1), rejecting extra rows. SQL cell cap32768 bytes; catalog
names/types/table names cap128 each. INTEGER PRIMARY KEY metadata has no
implicit index; other PK/UNIQUE autoindexes are literal above. Require strict=1
for all seven tables via PRAGMA table_list. Foreign_key_list/index_list are useful
diagnostics; literal SQL/inventory remain normative. Expected inventory must
never be derived from the untrusted database or silently regenerated on mismatch.

## 4. Immutable authority and guarded materialization

`wtd_watch_entries` commits one complete normalized P5a entry per
(watch_id,revision), globally across signals, aliases, routes, products and
series. Retain canonical ASCII full entry JSON (65536-byte P5b bound), including
CMT canonical identity/parent closure, identity_digest, watch/revision and all
configuration. Entry hash is plain canonical SHA256. Compare full bytes AND
hash. Under prepare's write lock, a different valid original entry for an
existing key is identity_conflict before any insertion/replay; malformed or
preexisting contradictory state is storage_corrupt. PK prevents partitioning by
alias/series; composite FK commits each delivery to the exact entry hash. No
orphan entry may commit: full fold requires at least one delivery per entry.
No update, overwrite, partial repair or delete exists. Genuine semantically
equivalent independent original copies are allowed.

Route JSON is the exact API version1 object: route_version, provider,
destination_key, bot_id, chat_id, chat_type='private', operator_attested=true.
Its digest uses CMT_WATCHLIST_TELEGRAM_ROUTE_V1. Immutable route projections and
canonical JSON must agree. registered_at is operational only; validated_at may
advance monotonically following equivalent bot/private-chat validation. Equal
validation timestamp is idempotent. No route rotation or deletion. Unvalidated
routes may be prepared offline but cannot claim. Operator attestation is local
trusted-host consent, not cryptographic human identity.

Delivery binding keys exactly: binding_version, provider, delivery_id, alert_id,
destination_key, signal_id, watch_id, revision, cmt_id, policy_version,
renderer_version, message_sha256, evidence_sha256, entry_sha256, intent_sha256,
source_alert_sha256, route_sha256, consent_sha256. binding_sha256 is outside the
object. Store complete canonical binding/consent/intent/evidence JSON and exact
message UTF-8; full entry is supplied by watch_entries. No clock, nonce, path,
token or mutable state enters identity. API consent keys/acknowledgement are
closed and must bind all exact historical content/route commitments.

Canonical means sorted keys/ensure_ascii=True/compact/no-NaN/strict types.
Route, consent and binding use SHA256(ASCII(domain)||byte0||canonical ASCII),
with domains CMT_WATCHLIST_TELEGRAM_ROUTE_V1,
CMT_WATCHLIST_TELEGRAM_CONSENT_V1 and CMT_WATCHLIST_TELEGRAM_BINDING_V1.
Entry/intent/evidence/source-alert hashes use plain canonical SHA256. Message
uses exact UTF-8 SHA256. wtdl1_ uses API's provider+genuine wsig1 identity domain;
UNIQUE(provider,signal_id) is independent of alert alias/route. First accepted
route/alert/consent/message/evidence binds that signal forever in this authority.
Any different semantic immutable binding conflicts, exact replay preserves
original prepared_at/history. Other genuine episodes have new signal identities.
No dedup/exactly-once guarantee across independent or cloned ledgers.

Source_alert_sha256 hashes the eleven semantic keys of the selected `_get_pair`
P8c `_alert` object, OMITTING only operational first_prepared_at: alert_id,
destination_key, signal_id, policy_version, renderer_version, channel, state,
intent, intent_sha256, message_text, message_sha256. Reconstruct the exact API
schema, including decoded intent and exact message string/hash.
Full twelve-key pair and exact evidence are compared before/after original
admission to detect replacement during an invocation, including timestamp.
Across independent equivalent sources, first_prepared_at may differ and is not
retained or compared by semantic replay/recompute/claim. P8d prepared_at is its
own initial operational time, projected as first_prepared_at in public delivery
DTOs. No source historical time is refreshed. Runtime reconstructs both P8c
results/transition/renderer, normalized complete entry and identities.

Before materializing ANY stored cell, SQL projects TEXT using
`CASE WHEN typeof(c)='text' AND length(CAST(c AS BLOB)) BETWEEN low AND high THEN c END`.
Required NULL is corruption. For nullable cells also return a small typeof/NULL
indicator so oversized/nontext input cannot masquerade as absent SQL NULL.
INTEGER uses the analogous typeof='integer'/range guard. No SELECT *, coercing
CAST-to-TEXT, unchecked fetchall or raw stored exception formatting. Guard
catalog cells before text decoding, even if constraints/triggers have been
externally disabled then restored. Stored faults are storage_corrupt; preserve
storage_timeout across adapters.

Runtime upper bounds: owner128/exact literal; provider8; policy64; state17;
error32; alias64; CMT UUID36; versioned IDs69/70; owner nonce/hash64; UTC27;
route2048; consent4096; binding8192; entry/intent65536; evidence262144;
message4096 UTF-8 bytes. Recheck exact literal checks/prefixes/calendar/UUID
syntax and lowercase hex after guarded projection. Metadata LIMIT2, selected
rows LIMIT2, claim/result rows LIMIT4; global histories use bounded keysets.
JSON has depth16/nodes20000/1MiB global cap plus tighter per-document caps;
strict canonical ASCII, no duplicate keys/NaN or bool-as-int. Budget checks
surround parsing and fold work. Public stdout/logs omit message/evidence/route
PII/receipt/owner; token/raw HTTP never enters any column or return value.

## 5. Transaction protocol and CAS

Storage consumes an application-issued private one-use receipt bound to exact
Python instance, complete source projection, operation, four distinct safe DB
paths, route/consent/binding, issuing Budget object and its unextended deadline.
Reject fake/copied/mutated/reused/cross-operation receipts before writable open;
consume once even if the writer fails. New attempts require fresh admission.
Runtime reconstructs derived fields from original material, never trusts a
caller DTO, digest or verified boolean. SQL cannot authenticate originals or
SHA256: this writer obligation and full retained fold precede commit.

Prepare: perform full original P5a/P5b/P8c admission, exact revision and complete
manifest checks outside ledger transaction. Read selected alert/evidence from
one verified P8c snapshot; recompute from originals and recheck complete selected
pair stability. Under BEGIN IMMEDIATE validate owned schema/integrity/FKs and
full retained semantic fold. Compare complete global (watch_id,revision) entry
BEFORE insertion or replay. Existing provider/signal binding compares all semantic
immutable fields; ignore new operational prepared_at, preserve old value.
Otherwise insert missing entry and immutable delivery; SQL trigger creates
ready/count0 cache. Postinsert independently reload/full fold/FK/deadline check
before one COMMIT. No INSERT OR IGNORE/REPLACE, upsert, half-pair fill or repair.
Conflict rolls back all rows, leaving old ledger healthy/verifiable/backupable.
Concurrent incompatible original bundles serialize on same global key.

Send first checks global quarantine BEFORE lookup/confirmed replay: every send,
including unknown post-backup IDs, is blocked if flag1. Healthy confirmed replay
checks local binding/receipt and returns without originals/token/transport/socket.
Unconfirmed send requires fresh original/consent/route revalidation, exact bot
preflight and residual budget. No SQL transaction spans metadata HTTP or send.

Claim: consume operation-bound fresh private receipt. BEGIN IMMEDIATE and full
fold check all retained global entry equality, binding/consent/route equality,
quarantine0, route validated, state ready/retryable, cooldown and count<3.
Create independent unpredictable attempt=`wtat1_`+64lowerhex and owner=64lowerhex
using separate secrets.token_hex(32) calls. Owner never appears in normal logs.
Copy the current validated_at into immutable claim.route_validated_at under this
same lock; insert contiguous ordinal=count+1. Snapshot is operational evidence,
excluded from route/binding/identity. SQL BEFORE guard requires exact equality
with current route.validated_at and claimed_at>=snapshot, and rechecks quarantine,
state/count/time/validation/FK entry; AFTER trigger atomically advances cache to
in_flight and current attempt/owner. Full fold/FK/deadline check; COMMIT BEFORE
sendMessage. Only after known successful commit, matching claim and positive
remaining reserved budget may one HTTP send start. No retry loop; at most one
sendMessage per manual invocation. Expiry after claim leaves in_flight or a
durable uncertain result; no absence-of-effect inference across a crash.

Finish: same Budget/private claimed handle binds owner/attempt/delivery/content,
operation and deadline; no caller-writable public finish API. BEGIN IMMEDIATE,
guarded full fold, select exact current delivery/attempt/owner. Insert one immutable
normalized result. BEFORE trigger CAS requires current in_flight/current attempt/
owner/count, matching claim, valid completion/outcome and no earlier result.
AFTER trigger changes cache and clears owner/attempt in the same statement;
changed-row count must equal1. Postfold/FK/deadline and COMMIT precede confirmed
output. Wrong owner/duplicate/stale finalization after recovery/terminal overwrite
aborts. Provider accepted with failed/unobservable local commit leaves blocked
in_flight or durable uncertain; never ready/retryable or a second HTTP request.
Durable confirmed receipt stores message_id/accepted_at/bot_id/chat_id, bound by
immutable claim/delivery to exact message and private route. No raw HTTP receipt.
Provider acceptance is not human-read proof.

Cache is wholly derived from immutable history; no API writes cache directly.
Its guard permits only transitions backed by corresponding inserted claim/result.
Claim/result/delivery/entry reject UPDATE/DELETE. Metadata only increases clock
watermark/quarantine; no clearing command. SQL guards are defense in depth,
not authentication against a privileged administrator with file access.

## 6. Complete history fold, retry and operational time

Fold every delivery in ordinal order (max3 claims): ready/count0,
updated_at=prepared_at; each claim is contiguous previous+1 and follows ready
or a valid earlier429 after persisted cooldown. Unfinished claim is final and
yields in_flight matching owner/attempt/count. Each finished claim has exactly
one owner-matching result. Terminal confirmed/permanent_failure/uncertain may
never have a successor claim. Cached state/count/updated_at/current owner/
current attempt/not_before must equal independent history fold. No orphan
entry/delivery/state/claim/result; full global entry map is rebuilt in
prepare/claim/verify using canonical complete bytes, not alias partitions.
Route/consent/binding/entry/receipt digests are all independently reconstructed.
Every claim retains route_validated_at: a guarded, calendar-valid UTC27 snapshot
of the latest equivalent route validation checked by its claim transaction.
Historical fold requires route.registered_at<=claim.route_validated_at<=claimed_at
and claim.route_validated_at<=current route.validated_at (which must be non-NULL
when claims exist). It MUST NOT require an old claimed_at>=current validated_at:
later equivalent revalidation can legitimately advance validated_at past old
claims. Only NEW claims compare against the current route validation. Immutable
snapshot permits deterministic local chronology validation without a separate
validation-event log; it records the checked precondition, not cryptographic
proof a remote request took place. Coherent privileged rewrite remains outside
authentication guarantees. Snapshot values do not alter route identity/digest.

| Normalized outcome | Result state/category | Receipt/retry/cooldown | Later claim |
| --- | --- | --- | --- |
| Accepted exact valid transport receipt | confirmed / NULL | receipt required, retry/cooldown NULL | never; local replay only |
| Valid explicit429 ordinal1 or2 | retryable / rate_limited | no receipt; retry_after1..86400; exact not_before=completed_at+retry_after | manual, at/after cooldown |
| Valid explicit429 ordinal3 | permanent_failure / retry_exhausted | no receipt; valid retry_after retained; not_before NULL | never |
| Valid permanent rejection per API mapping | permanent_failure / provider_rejection | receipt/retry/cooldown NULL | never |
| Ambiguous HTTP/network/local post-send or malformed success | uncertain / frozen uncertain category, or blocked in_flight if persistence fails | no receipt/retry/cooldown | never |
| Worker-quiesced recovery | uncertain / recovered, or clock_skew on rollback | no receipt/retry/cooldown | never |
| Postclaim UTC rollback | uncertain / clock_skew | clamped completion, no receipt/retry/cooldown | never |

API freezes normalized transport outcome mapping. Unchanged P8b TransportResult
exposes state/category/retry/Receipt, not raw HTTP status; only strict accepted
provider_rate_limit result means429. No retries inferred from strings/timeouts/
malformed retry_after. Third valid429 retains its retry_after as evidence but is
permanent_failure. SQL BEFORE result guard checks ordinal cap, exact owner/CAS,
route IDs and precise not_before arithmetic retaining microseconds using built-in
strftime on the whole-second prefix plus original suffix. Runtime independently
validates Gregorian parsing/timedelta/overflow. SQLite strftime overflow/null may
not become retryable; runtime classifies overflow uncertain/provider_invalid.

Closed stored uncertain categories: network_uncertain, transport_timeout,
transport_failure, provider_invalid, bot_mismatch, destination_mismatch,
token_configuration, local_commit_failed, deadline_exceeded, recovered,
clock_skew. Unknown exceptions map to network_uncertain before storage. Token
configuration normally fails before claim; afterclaim exceptions remain
conservative. No invalid/no-receipt200,408/409/425/5xx, TLS/lost response/timeout,
post-possible-send local commit failure becomes retryable. Uncertainty has no
reset/force/requeue or fabricated reconciliation receipt.

UTC format exactly YYYY-MM-DDTHH:MM:SS.ffffffZ (27 ASCII bytes), real Gregorian
year0001..9999, no offsets/leap seconds/short fractions. Parse calendar before
using lexical comparisons. operational_high_water is metadata, initialized on
init and advanced by route register/validate, delivery prepare, claim/result
triggers. It bounds persisted EVENT instants only: init, registered_at,
validated_at, prepared_at, claimed_at, completed_at and their cached/snapshotted
copies (state.updated_at and claim.route_validated_at). It is at least each
retained event instant; historical init time need not be retained separately.
It explicitly EXCLUDES future cooldown not_before, original as_of/observed_at/
P8c first_prepared_at and provider accepted_at. A valid retryable cooldown can
lie after high-water; neither writing nor verifying it advances high-water.
Current high-water is an UPPER bound for historic event instants; it becomes a
LOWER bound only for a newly persisted operational event. Historic claims or
completions are never required to be >=the current watermark.
Prepare/route mutations refuse now<high-water. Claim requires
now>=high-water/validated_at/state.updated_at; rollback fails clock_skew before
claim/send. Future high-water can conservatively block until wall UTC catches
up; no clock-reset command.

During finish, now<max(claimed_at,high-water) overrides provider receipt/retry:
persist uncertain/clock_skew with completed_at=max(now,claimed_at,high-water)
under same owner CAS. This is an explicitly clamped operational safety timestamp,
not an accepted receipt. Failure to persist leaves in_flight. Recover requires
specific ID and worker_quiesced=true (explicit operator attestation that worker
AND supervised child are stopped, never inferred from elapsed lease). Under
BEGIN IMMEDIATE/full fold select current owner/attempt and insert uncertain result through identical CAS, using max(now,claim,high-water);
category clock_skew if wall time regressed, otherwise recovered. No
quiescence flag is stored as fake transport evidence. Stale/changed state fails
stale_attempt or delivery_blocked without overwriting history. No implicit crash
recovery; time passing never re-enables a send.

## 7. Verify, original recompute and shared deadline

Local verify: one ro snapshot; owned header/version/schema exact inventory,
integrity_check/FKs, singleton/flags/high-water, SQL cell guards and canonical
JSON/calendar semantics. Recalculate P8c both full evaluations, signal
transition, intent/renderer/IDs, complete watch entry consistency, route/consent/
binding/all hashes and claim/result/cache fold. Cardinalities and uniqueness
must agree; no cached prior authority. Coherent privileged rewrite or active
cloned ledger can pass local consistency; trusted host/single authority remain
assumptions. Local verify never proves original authenticity.

Recompute selects explicit delivery and uses original safe P5a/P5b/P8c paths,
complete manifest, original exact revision and accepted P8c read-only recompute
route. Compare complete semantic projection, text/evidence/full entry/config,
route/consent/binding. Missing/different originals fail even if local verify
passes. No latest/hidden enqueue/source write/changed historical timestamps.
Complete selected pair before/after is stable, while source operational preview
timestamp may differ across independent copies. Four files have no atomic
distributed snapshot/commit; immutable originals/trusted directories assumed.

One invocation Budget covers parse, SQL waits/progress, origins, backup callbacks,
fold/JSON, filesystem, persistence and response: local default2/max5s; remote
validation/send default15/max30s. Send origins share ONE combined max5s scoped
ceiling of SAME Budget, never renewed per helper. Finalization reserve
min(0.5s,timeout/5); no claim/HTTP if remaining-reserve<=0. Transport receives
remaining-reserve. All helpers receive residual only. Expired handler disabled
and busy wait0 for best-effort rollback/close, never new business work.
Full verification may timeout with rollback; partial work never authorizes send.
Filesystem/SQLite/stdout syscalls have cooperative limits, not hard real-time.

## 8. Physical ownership, hot journals, backup and restore

Trusted local directory and private files: reject UNC/device/ADS/traversal/
reserved names, symlink/junction/reparse ancestors/leaf, nonregular files and
multiple hardlinks. Four DBs and manifest path must be distinct by normalized
name AND samefile/dev+ino; no implicit directories/init. Record dev/ino/nlink
before open, fstat and after operation; any replacement fails unsafe_destination.
Use nofollow where supported, private0600 reservation and trusted directory ACLs;
Windows mode bits alone are not access control. No source writer is called.

BEFORE writable SQLite open/recovery, read fixed100-byte header through a checked
regular descriptor: SQLite magic, sane page/file size, app ID bytes68..71=CMTZ,
user_version bytes60..63=1; recheck same inode/nlink1 before/after. Foreign DB
with hot journal never reaches SQLite writable recovery. Reject unsafe/foreign
ownership context and WAL/SHM or nonregular/link/reparse sidecars. Preserve
legitimate owned DELETE journal evidence for SQLite recovery only after preopen
checks; no deleting sidecars/VACUUM/repair to force open. SQLite cannot authenticate
a malicious replaced journal: trusted private directories/quiesced maintenance
remain assumptions. Read-only commands refuse recovery-needed stores, never
silently write. Postopen exact owner/schema/integrity/FK precede business work.

Init alone exclusively reserves O_CREAT|O_EXCL new regular private inode, no
existing target/sidecars. Transaction creates literal DDL, header PRAGMAs and
singleton(1,owner,1,0,init_utc), full-verifies empty ledger then COMMIT/fsync.
No default-path create/overwrite/old store opening. Failed reservation cleanup
only if reserved matching inode/nlink1/regular/nonreparse/no-sidecar is proved;
otherwise preserve residue. No prior owner writer/schema is reused.

Copy protocol uses online SQLite backup32-page chunks under shared Budget;
never raw active-file copy. Reserve private random provisional in NEW target
parent, keep target nonexistent, no overwrite/rename replacement. Verify source
in a consistent transaction (fold1). Provisional full fold2 and close/reopen
read-only fold3 independently rebuild hashes/full entry map/history; no loaded
object cache reuse. Compare complete canonical sorted logical rows/content digest
and counts/quarantine, not counts alone or changing SQLite page hashes. Logical
comparison includes metadata/routes/entries/deliveries/state/claims/results,
excluding ONLY intentional restore quarantine change. All three folds share one
unchanged Budget; deadline failure is failure.

Backup: source fold1, online copy to exclusive provisional, fold2 validates
identical source semantics and quarantine, close, reopen fold3. Fsync provisional
and parent where supported; recheck inode/sidecars; exclusively publish via
hardlink then provisional unlink, sync parent. Reopen final path owned header/
inode/schema/quarantine before success. Final readback can be a bounded validation
of already verified exact inode, not substitution for any independent full fold.

Restore: source fold1, online copy to PRIVATE provisional; BEGIN IMMEDIATE sets
send_quarantined=1, preserving high-water/data/history, COMMIT with FULL BEFORE
any final target exposure. Fold2 proves only flag changed and quarantine1; close,
fsync, fold3 reopen verifies full durable quarantined semantics. Only then
exclusive publication and final readback. Maintenance provisional is private,
not an active ledger path; no normal commands while maintenance runs. Every
valid snapshot at final destination is already quarantined. Even empty/old
backup blocks missing later deliveries and fresh preparations because global
flag checked by every send BEFORE replay/ID lookup and again under claim.
No unquarantine/force command exists. Read/verify/recompute/prepare inspection
may continue, send cannot. Never restore over existing ledger.

If link succeeds and provisional unlink fails, compensation may unlink final
name ONLY after both names proven regular/nonreparse/exact reserved dev+ino,
exact nlink2, absent sidecars under BOTH names, and immediate pre-unlink recheck.
Foreign replacement/additional hardlink/sidecar => leave evidence untouched.
Never delete foreign/residual recovery evidence. Provisional cleanup only known
reserved nlink1/nonreparse/regular/sidecar-free inode. Persistent refusal may
leave private residue for manual inspection. An error after publish may leave a
complete target; error never proves absence. Fsync failure prevents success;
unsupported directory fsync must be reported as platform limitation, not hidden.
Process/QEMU tests do not certify physical Pi power-loss durability.

## 9. Reproducible author design probes (memory only)

Run the following complete stdlib probe from this worktree. It reads this
Markdown, extracts only the delimited literal SQL and expected inventory table,
uses SQLite :memory:, imports no product package, creates no database file,
reads no token and makes no network/Telegram call. Synthetic shape-only rows
below deliberately do NOT claim original authenticity, valid P8c canonical
content, full product verification, concurrency or recovery durability.

```python
from pathlib import Path
import re
import sqlite3

raw = Path('docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md').read_text(encoding='utf-8')
section = raw.split('<!-- P8D_DDL_BEGIN -->', 1)[1].split('<!-- P8D_DDL_END -->', 1)[0]
statements = re.findall(r'^```sql\n(.*?)\n```$', section, re.M | re.S)
expected = []
for kind, name, table, authority in re.findall(r'^\| (table|index|trigger) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$', raw, re.M):
    authority = authority.strip()
    sql = None if authority == 'NULL' else statements[int(authority.split()[1])-1]
    expected.append((kind, name.strip(), table.strip(), sql))

def empty():
    db = sqlite3.connect(':memory:', isolation_level=None)
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA trusted_schema=OFF')
    for statement in statements:
        db.execute(statement)
    actual = list(db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'))
    assert actual == sorted(expected)
    assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    assert list(db.execute('PRAGMA foreign_key_check')) == []
    assert all(row[-1] == 1 for row in db.execute('PRAGMA table_list') if row[1].startswith('wtd_'))
    return db

def insert(db, table, values):
    keys = ','.join(values)
    marks = ','.join('?' for _ in values)
    db.execute(f'INSERT INTO {table}({keys}) VALUES({marks})', tuple(values.values()))

def stamp(second):
    return f'2026-10-30T00:00:{second:02d}.123456Z'

z = '0' * 64
did = 'wtdl1_' + z
watch = 'wlt1_' + z

def fixture():
    db = empty()
    insert(db, 'wtd_metadata', dict(singleton=1, owner='card-market-tracker.watchlist-telegram-delivery', schema_version=1, send_quarantined=0, operational_high_water=stamp(0)))
    insert(db, 'wtd_destinations', dict(destination_key='private', provider='telegram', bot_id=1, chat_id=2, chat_type='private', operator_attested=1, route_json='{}', route_sha256=z, registered_at=stamp(0), validated_at=None))
    db.execute('UPDATE wtd_destinations SET validated_at=?', (stamp(0),))
    insert(db, 'wtd_watch_entries', dict(watch_id=watch, revision=1, entry_json='{}', entry_sha256=z))
    row = dict(delivery_id=did, provider='telegram', alert_id='walt1_'+z, destination_key='private', signal_id='wsig1_'+z, watch_id=watch, revision=1, cmt_id='00000000-0000-4000-8000-000000000000', policy_version='watchlist_synthetic_alert_v1', renderer_version=1, intent_json='{}', evidence_json='{}', message_text='synthetic SQL design probe', consent_json='{}', binding_json='{}', prepared_at=stamp(0))
    row.update({key:z for key in ('intent_sha256','evidence_sha256','message_sha256','entry_sha256','source_alert_sha256','route_sha256','consent_sha256','binding_sha256')})
    insert(db, 'wtd_deliveries', row)
    return db

def claim(db, ordinal, second, validation=None):
    aid = 'wtat1_' + f'{ordinal:064x}'
    owner = f'{ordinal+100:064x}'
    snapshot = db.execute('SELECT validated_at FROM wtd_destinations WHERE destination_key=?',('private',)).fetchone()[0] if validation is None else validation
    insert(db, 'wtd_claims', dict(attempt_id=aid, delivery_id=did, owner=owner, ordinal=ordinal, claimed_at=stamp(second), route_validated_at=snapshot))
    return aid, owner

def result(db, pair, state, category, second, retry=None, not_before=None, receipt=False):
    insert(db, 'wtd_results', dict(attempt_id=pair[0], owner=pair[1], state=state, completed_at=stamp(second), error_category=category, retry_after=retry, not_before=not_before, message_id=3 if receipt else None, accepted_at=1 if receipt else None, bot_id=1 if receipt else None, chat_id=2 if receipt else None))

rejections = 0

def rejected(db, action):
    global rejections
    db.execute('SAVEPOINT negative')
    try:
        action()
    except sqlite3.IntegrityError:
        rejections += 1
    else:
        raise AssertionError('invalid SQL action accepted')
    finally:
        db.execute('ROLLBACK TO negative')
        db.execute('RELEASE negative')

with fixture() as db:
    assert db.execute('SELECT state,attempt_count FROM wtd_state').fetchone() == ('ready',0)
    rejected(db, lambda: insert(db,'wtd_watch_entries',dict(watch_id=watch,revision=1,entry_json='{"different":true}',entry_sha256='f'*64)))
    rejected(db, lambda: db.execute("UPDATE wtd_watch_entries SET entry_json='{}'"))
    rejected(db, lambda: db.execute('DELETE FROM wtd_deliveries'))
    rejected(db, lambda: db.execute("UPDATE wtd_state SET state='confirmed',attempt_count=1"))
    rejected(db, lambda: db.execute('UPDATE wtd_destinations SET bot_id=9'))
    rejected(db, lambda: db.execute('UPDATE wtd_destinations SET validated_at=NULL'))
    rejected(db, lambda: db.execute('UPDATE wtd_metadata SET operational_high_water=?',(stamp(0).replace('2026','2025'),)))
    first = claim(db,1,1)
    rejected(db, lambda: claim(db,2,2))
    rejected(db, lambda: result(db,(first[0],'f'*64),'confirmed',None,2,receipt=True))
    rejected(db, lambda: result(db,first,'retryable','rate_limited',2,retry=1,not_before=stamp(4)))
    rejected(db, lambda: result(db,first,'confirmed',None,0,receipt=True))
    result(db,first,'confirmed',None,2,receipt=True)
    assert db.execute('SELECT state,attempt_count,current_owner FROM wtd_state').fetchone() == ('confirmed',1,None)
    rejected(db, lambda: result(db,first,'uncertain','recovered',3))
    rejected(db, lambda: claim(db,2,3))
    rejected(db, lambda: db.execute("UPDATE wtd_results SET state='uncertain'"))

with fixture() as db:
    for ordinal,second in ((1,1),(2,3)):
        pair = claim(db,ordinal,second)
        result(db,pair,'retryable','rate_limited',second+1,retry=1,not_before=stamp(second+2))
        assert db.execute('SELECT operational_high_water FROM wtd_metadata').fetchone() == (stamp(second+1),)
        rejected(db, lambda: claim(db,ordinal+1,second+1))
    pair = claim(db,3,5)
    rejected(db, lambda: result(db,pair,'retryable','rate_limited',6,retry=1,not_before=stamp(7)))
    result(db,pair,'permanent_failure','retry_exhausted',6,retry=1)
    assert db.execute('SELECT state,attempt_count FROM wtd_state').fetchone() == ('permanent_failure',3)
    assert db.execute('SELECT retry_after,not_before FROM wtd_results WHERE attempt_id=?',(pair[0],)).fetchone() == (1,None)
    rejected(db, lambda: claim(db,4,7))

# Later equivalent revalidation must preserve the validity of older claims.
with fixture() as db:
    first = claim(db,1,1)
    result(db,first,'retryable','rate_limited',2,retry=1,not_before=stamp(3))
    db.execute('UPDATE wtd_destinations SET validated_at=?',(stamp(4),))
    old_claim = db.execute('SELECT claimed_at,route_validated_at FROM wtd_claims').fetchone()
    assert old_claim == (stamp(1),stamp(0))
    assert old_claim[0] < db.execute('SELECT validated_at FROM wtd_destinations').fetchone()[0]
    rejected(db, lambda: claim(db,2,5,validation=stamp(0)))  # stale validation snapshot
    rejected(db, lambda: claim(db,2,5,validation=stamp(6)))  # future/noncurrent snapshot
    rejected(db, lambda: db.execute('UPDATE wtd_claims SET route_validated_at=?',(stamp(4),)))
    second = claim(db,2,5)
    result(db,second,'confirmed',None,6,receipt=True)
    history = list(db.execute('SELECT x.registered_at,c.route_validated_at,c.claimed_at,x.validated_at FROM wtd_claims c JOIN wtd_deliveries d ON d.delivery_id=c.delivery_id JOIN wtd_destinations x ON x.destination_key=d.destination_key'))
    assert all(registered <= snapshot <= claimed and snapshot <= latest for registered,snapshot,claimed,latest in history)

uncertain = ('network_uncertain','transport_timeout','transport_failure','provider_invalid','bot_mismatch','destination_mismatch','token_configuration','local_commit_failed','deadline_exceeded','recovered','clock_skew')
for category in uncertain:
    with fixture() as db:
        pair = claim(db,1,1)
        result(db,pair,'uncertain',category,2)
        assert db.execute('SELECT state FROM wtd_state').fetchone() == ('uncertain',)
        rejected(db, lambda: claim(db,2,3))
with fixture() as db:
    pair = claim(db,1,1)
    rejected(db, lambda: result(db,pair,'permanent_failure','retry_exhausted',2,retry=1))
    result(db,pair,'permanent_failure','provider_rejection',2)
with fixture() as db:
    db.execute('UPDATE wtd_metadata SET send_quarantined=1')
    rejected(db, lambda: claim(db,1,1))
    rejected(db, lambda: db.execute('UPDATE wtd_metadata SET send_quarantined=0'))
print(sqlite3.sqlite_version, len(statements), len(expected), 'literal inventory/STRICT/integrity/FK matched; rejected',rejections,'invalid SQL actions; confirmed/all uncertain/permanent/three429 outcomes and historical validation snapshots coherent')
```

Probe execution/results below apply to these documentary SQL statements only.
NOT RUN here: product original-backed admission/materialization, genuine RW-01
independent sources/races, competing processes, private receipt enforcement,
HTTP/crash/fault injection, source-byte nonmutation, backups/restores/fsync,
platform/QEMU/Pi durability, CLI/installed harnesses, independent QA/REVIEWER.
Required future regressions include every one of those and hot foreign journals,
inode/link/reparse/sidecar substitution, ENOSPC/deadlines, three independent
folds, old-empty restore/global quarantine and token/socket-denied replay.

Superseded author design snapshot execution 2026-10-30 (before adding immutable
claim route-validation snapshots): Python3.13.15, SQLite3.53.1 (Windows AMD64),
34 statements /45 exact objects (7 STRICT tables,14 indexes,24 triggers),
integrity_check=ok, foreign_key_check empty, exact literal sqlite_master SQL
including implicit indexes matched. The prior version of the executable probe accepted confirmed, all11 uncertain
categories, permanent rejection and third429 exhausted outcomes, rejecting32
invalid SQL actions. This historical result does not attest the revised SQL.
Preserved prior console result:

    3.53.1 34 45 literal inventory/STRICT/integrity/FK matched; rejected 32 invalid SQL actions; confirmed/all uncertain/permanent/three429 outcomes coherent

Invocation (PowerShell, isolated worktree; executable is the existing original
worktree Python, read-only):

    @'
    from pathlib import Path
    import re
    raw = Path('docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md').read_text(encoding='utf-8')
    probes = re.findall(r'^```python\n(.*?)\n```$', raw, re.M | re.S)
    assert len(probes) == 1
    exec(compile(probes[0], '<P8d documentary SQL design probe>', 'exec'))
    '@ | & 'C:\Projects\card-market-tracker\.venv\Scripts\python.exe' -

Remove the four-space Markdown indentation before executing this command. No
product import, persisted database, token read or real HTTP was performed.
The initial oversized document-write command hit Windows process command-length
limit before process launch; it wrote no document/database. Subsequent bounded
commands wrote only this owned Markdown file. These are author design checks,
not independent QA, candidate CI, Gate B PASS or Phase Lead acceptance.

Current revised author execution 2026-10-30: Python3.13.15, SQLite3.53.1,
34 literal statements /45 objects (7 STRICT tables,14 indexes,24 triggers),
exact inventory/STRICT/integrity/FK matched. All prior outcome cases still passed.
New probe cases accepted equivalent revalidation AFTER an older claim while
preserving that claim's earlier immutable snapshot, rejected stale/future
validation snapshots and snapshot mutation, and proved future not_before did
not advance metadata high-water. Total35 invalid SQL actions rejected:

    3.53.1 34 45 literal inventory/STRICT/integrity/FK matched; rejected 35 invalid SQL actions; confirmed/all uncertain/permanent/three429 outcomes and historical validation snapshots coherent

Use the same documented extraction command; it executes the CURRENT embedded
probe. This supersedes the earlier32-action author's design snapshot for revised
SQL coherence only. No product schema/writer, persisted database, Telegram/token,
Git mutation or independent QA was performed. Gate B remains NOT ACCEPTED.
