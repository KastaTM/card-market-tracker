# Watchlist v1

P5a implementation contract; phase acceptance belongs to the Orchestrator.
Producer: explicit local operator commands plus fully validated MANIFEST_V1.
Consumers: local CLI, separate watchlist storage and pure synthetic evaluator.
See [ADR-0012](../adr/0012-watchlist-offline-rules.md),
[storage](WATCHLIST_STORAGE_V1.md) and
[evaluation](WATCHLIST_SYNTHETIC_EVALUATION_V1.md). This document supplies no gate PASS.

## Identity

Only canonical lowercase UUIDv4 CMT IDs already present as `printing` or `sealed`
in a completely parsed [manifest](MANIFEST_V1.md) are targets. A valid-looking
missing UUID, set, base card, candidate, external ID, name or URL is rejected.
Public Python boundaries revalidate values; frozen/typed constructors confer no
authority. Add, update, enable/disable and evaluation reparse the full manifest,
including unrelated entities and bindings, before trusting target membership.

watch_id is `wlt1_` + lowercase SHA-256 hex of
`UTF8("CMT_WATCHLIST_V1" + NUL + cmt_id)`. The NUL is one byte 0x00, not the two
characters backslash and zero. This key identifies a watch entry, never a new
product. One CMT ID has one watch key; no hard delete or retarget exists.

The frozen identity includes target and parent closure. Printing commits its
cmt_id/kind/card_id/language/variant, the parent card's cmt_id/kind/set_id/
card_number, and the set's cmt_id/kind. Sealed commits cmt_id/kind/set_id/
language/sealed_type and the optional set's cmt_id/kind. Explicit null and
`unknown` stay exact. Localized names, release dates, external bindings and
unrelated entities do not affect the projection. Changed canonical relationships
or attributes under the same CMT ID cause `identity_conflict`, without overwrite.

The exact projection is `{version:1,target:{...},parents:[...]}`. Printing
parents are ordered card then set; sealed parents are a one-element set list or
empty list when set_id is null. identity_digest is the lowercase SHA-256 hex of
the canonical projection JSON, without a hash-domain prefix.

Canonical JSON uses sorted object keys, ASCII escapes, compact `,`/`:` separators
and allow_nan=False, encoded UTF-8. Digests compare these canonical bytes, not
Python's permissive bool/int equality. They do not authenticate curators.

## Configuration and commands

| Field | Contract |
| --- | --- |
| priority | `high`, `normal`, `low`; default `normal` |
| enabled | Exact boolean; default true |
| target_price_minor | Null or exact integer 1..1000000000, EUR cents |
| restock_enabled | Exact boolean; default false |
| max_age_seconds | Exact integer 1..604800; default 86400 |

At least one rule is configured: nonnull target price or restock_enabled=true.
Disabling preserves configured rules and history. There is no SQL, Python,
regex, formula or other executable rule input. Floats, bool-as-int, NaN,
infinity, coercion and unknown fields are rejected. JSON input uses the shared
1 MiB/depth16/nodes20000/string1024 limits and duplicate-key rejection.

Add expects revision 0 and produces revision 1. Every successful new mutation,
including enable/disable, records a complete immutable revision. New requests
with stale expected revision fail `revision_conflict` without mutation. Revisions
are exact integers 1..2147483647; expected revision is bounded likewise except
add's zero. Request tokens match `[A-Za-z0-9][A-Za-z0-9_.:-]*`, 1..128
characters, carry no secret and are not log fields. At the maximum revision no
further revision can be added.

Add/update input is the five-field configuration object, with omitted fields
receiving the listed defaults. Update replaces the complete effective config;
it is not a patch of current fields. Enable/disable retains the configuration at
the expected revision and changes only enabled.

Replay binds the canonical action, target, expected revision, frozen identity
and complete effective configuration. Same token and equivalent canonical
command returns original operation metadata without adding a revision. Different
content under an existing token fails `replay_conflict`. An older replay after
later updates returns the original revision and leaves the newer pointer intact.
All request/history/current changes commit atomically in the watchlist database.
The manifest read and DB commit are separate; no distributed atomicity is claimed.

Normalized command has exactly version1, action, cmt_id, watch_id,
canonical_identity, identity_digest, expected_revision and config. A revision
entry has exactly version1, cmt_id, watch_id, canonical_identity, identity_digest,
revision and the five effective configuration fields. Config has no nested
version field; fixed currency EUR is implicit in the target-price contract.

## Queries and operational boundary

Commands are explicit one-shot `cmt watchlist` init/add/get/list/update/enable/
disable/history/evaluate/verify/backup/restore. No implicit init, source scanning,
daemon, delivery, journal/outbox event or network call is authorized. Evaluation
binds a selected revision, validated manifest and explicit synthetic evidence;
it writes neither watchlist nor previous databases.

List orders high, normal, low, then watch_id. History is ascending revision.
Pages default to 100, maximum 1000 and 1 MiB encoded output. Keyset cursors bind
query filters, rejecting incompatible reuse; successive invocations have separate
snapshots. Versioned JSON stdout intentionally exposes preferences and canonical
identity, so protect saved output as local operator data. Errors/logs use fixed
categories and exclude raw payloads, paths, tokens, SQL and exception text.

Every command requires --watchlist-db; --timeout defaults2s, range greater than0
through5s. Add/update/enable/disable/evaluate require --manifest. Add uses
--cmt-id, --input config.json and --request-token (expected0 is implicit).
Update uses --watch-id, --input, --expected-revision and --request-token;
enable/disable use those flags without --input. Get/history use --watch-id;
get selects current in the CLI. List supports optional --priority and
--enabled true|false; list/history accept --limit and --cursor. Evaluate requires
--watch-id, --revision, --sample and --as-of, plus optional --previous.
Backup/restore use --watchlist-db as source and --destination as a new path.

Successful storage JSON has version1, operation and result=ok. Mutations add
action, entry and replayed (boolean); an old replay's entry is the original
operation revision. Get adds entry. List/history add entries and nullable
next_cursor; history items additionally expose action/request_token. Verify/
backup/restore add counts `{entries,revisions,requests}`. Init adds
schema_version1. Evaluation returns the policy's aggregate in result and CLI
adds operation=evaluate. JSON errors have version1, operation, result=error and
safe error_category. Exit0 is successful operation (including SKIPPED,
INDETERMINATE, NO_MATCH and replay); exit2 is invalid input/context/conflict,
exit1 is local storage/path/IO failure. No raw parser/SQL exception is returned.

Watchlist-specific categories are no_rules, invalid_timestamp, invalid_target,
unsupported_evidence, incompatible_context, future_sample, invalid_chronology,
replay_conflict, revision_conflict, already_exists, not_found and invalid_cursor;
shared catalog/input/storage categories remain valid. The cursor parser currently
reports malformed/incompatible cursors as invalid_field. Error categories carry
no diagnostic input values. Resource and missing/unsafe-path errors fail the
whole operation; they are not empty-query results.

Example using an operator-authored config file containing
`{"priority":"high","target_price_minor":3500,"restock_enabled":true}` and an
existing target from the synthetic manifest (the CMT ID below is a placeholder):

```text
cmt watchlist init --watchlist-db watchlist.sqlite
cmt watchlist add --watchlist-db watchlist.sqlite --manifest manifest.json --cmt-id <existing-printing-or-sealed-uuid> --input config.json --request-token demo-add-1
cmt watchlist list --watchlist-db watchlist.sqlite --enabled true --limit 100
cmt watchlist evaluate --watchlist-db watchlist.sqlite --manifest manifest.json --watch-id <returned-wlt1-key> --revision 1 --sample current.json --as-of 2026-10-23T12:00:00Z
```

Inputs are file paths; stdin (`--input -`) is not a supported JSON input mode.

## Compatibility

Major version 1 freezes identity, null/unknown, money, revision/replay and rule
semantics. Breaking changes require an explicit new contract and migration
decision. P0 through P8b schemas, identifiers and APIs remain unchanged.
