# Persistible synthetic observation input v1

Status: adopted for implementation; gates pending. Refines ingestion v1 only at the new
write boundary; P1a capture remains optional and `cmt catalog` stays read-only.

## Input and composition

Local JSON has exactly `version`, `batch_id`, `captured_at`, `ingestion`.
`version` is integer 1, never bool. `batch_id` is canonical lowercase UUIDv4
allocated by the producer and preserved across retry. It is distinct from an
execution run ID. `ingestion` is the unchanged P1a synthetic adapter envelope;
the curated manifest is passed separately and completely validated.

Wrapper capture is required, zoned ISO instant and normalized to fixed
microsecond UTC `YYYY-MM-DDTHH:MM:SS.ffffffZ`. If the P1a envelope/observation
declares capture it must denote exactly the same instant, otherwise
`capture_conflict`; no precedence or inferred execution capture. Every admitted
observation receives this explicit capture. Optional provider-update instants
also normalize to the same UTC representation. Release dates remain ISO dates.
Null optional evidence is preserved, never guessed from names or other clocks.

Only provenance `synthetic` may pass. A documented/observed envelope or manually
constructed observation fails `synthetic_only` before DB access or retention.
Synthetic is a local declaration, not cryptographic proof or a source license.
No raw input, ignored provider extras, images, prices, stock or personal data is
retained. Existing strict 1 MiB/16-depth/20,000-node/1,024-character/1,000-record
limits apply; manifest limits remain 1,000 entities/2,000 bindings. Reference
tokens max 128; card number max 64; release date max 10; timestamp max 40.

The application binds each normalized item to its indexed resolver snapshot.
Length/index/reference/status/provenance disagreements fail globally; silent
zip truncation is forbidden. Accepted/candidate observations preserve `kind`,
complete contextual `reference`, `name`, optional contextual `set_reference`,
`card_number`, `release_date`, `provider_updated_at`, `captured_at`, `provenance`.
Accepted records also preserve the CMT target. Candidates preserve the exact
reference and fixed category without a target. Rejected records retain only
index, rejected status and an ingestion/resolver allowlisted category, even
when a rejected source observation was otherwise normalized.

## Python boundary

Frozen `PersistedRecord(index, status, category, cmt_id, observation)` and
`PersistenceBatch(version, batch_id, captured_at, manifest, records, entities)`
carry tuples and frozen P1a values. `observation` is null on rejection. Entities
are the sorted unique accepted targets and complete curated parent closure.
They do not include candidates. A dataclass constructor is not validation.

`build_batch(batch_id, captured_at, observations, manifest)` validates normalized
evidence and manifest, resolves, verifies alignment and strips rejected evidence.
`parse_persistence(document, manifest)` validates the wrapper and translates its
envelope before building. `validate_batch(batch)` independently reserializes and
parses the manifest, normalizes/revalidates evidence, verifies consecutive indexes
0..n-1, reruns resolution with safe RecordErrors, and compares every snapshot and
parent closure. The public repository always invokes `validate_batch` itself.
Manifest constructors, caller-supplied resolution IDs and caller-supplied hashes
cannot bypass this boundary. Public malformed objects fail safe fixed categories.

## Replay equivalence

`canonical_payload(batch)` contains input contract version 1, resolver context
version 1, required capture, every ordered record and duplicate, all admitted
metadata and exact nulls, safe indexed rejection categories, snapshot targets and
categories, accepted identity closure, and sorted validated manifest context.
Context includes every entity's canonical identity projection plus release date
and sealed type and every binding's exact reference and target. Manifest order,
localization names and binding audit reason are irrelevant to resolution and
excluded. Bindings/entities are sorted deterministically. Unrelated identity or
binding changes conservatively alter context; callers must use a new token.

SHA256 uses ASCII escaped canonical JSON, sorted object keys, compact separators,
finite values only. `fingerprint(batch)` hashes the complete canonical payload
excluding batch token; `context_fingerprint(batch)` hashes context alone.
Timestamps equivalent by instant compare equally. Input record order and repeated
records remain meaningful. Rejections intentionally compare only their safe
categories; changing one rejected raw payload to another with the same rejection
category is an equivalent non-retained input. Hashes never create product IDs.

An existing token with equal fingerprint yields replay: no new entities,
observations, batch or rejection rows and unchanged first-persistence timestamp.
An unequal fingerprint yields `replay_conflict` without mutations. A new token
can add history even if all field values match. Producer token loss/replacement
prevents automatic recognition of the earlier attempt.

## Results and errors

`WriteResult(result, batch_id, first_persisted_at, input_count, accepted_count,
candidate_count, rejected_count, committed_observations, committed_entities)`
is frozen. New-batch result is `empty` for zero input, `ok` for all accepted,
otherwise `mixed`; repeat is explicitly `replay`, including mixed retries.
Committed observations count accepted plus candidates only; committed entities
count newly projected IDs only. Rejected summaries are not observations.
Replay counts describe original processing but committed counts are zero.
Errors return no apparent committed success or attempted-as-committed counts.

CLI exit 0: ok/empty/replay; 3: newly committed mixed/candidates/all rejected;
2: invalid input, `synthetic_only`, `capture_conflict`, replay or identity conflict;
1: schema/lock/IO/corruption/operation timeout/unsafe backup destination failure.
Stdout JSON contains version, result and contracted result values. Fixed global
error output contains `{version:1,result:error,error_category,counts:null,committed:null}`.
New commands are `cmt persist --db --input --manifest`, `cmt observations --db`
with optional `--batch-id`, `--cmt-id` or `--candidate-reference PATH` and `--limit`,
and `cmt db init|verify|backup|restore --db` (copies use `--destination`). Existing P0/P1a
commands retain their codes. Logs contain only fixed categories/run ID/duration
and counts; never batch tokens, names, references, paths, SQL or exception text.
