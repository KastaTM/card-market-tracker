# P5b engineering design freeze

Frozen before product implementation on 2026-10-24. Phase remains OPEN;
ADR-0013 and the new contracts remain PROPOSED pending implementation review.

The authorized baseline is `ddd5fe3bbc7e40947bd838f71ee25e7046ff1b7e`, tree
`f0eaf874e8671f75904ece1f618c283d7ff91536`; ordered parents are
`d1038df1625a9727b44760866266b7124bb1d91a` and
`02ab89677afe11901ea5a2b1b8826604ce543c2f`. Git status was clean before
extraction; all branches/worktrees were inspected and preserved. Live
`git ls-remote origin refs/heads/main` matched the authorized baseline.
Only `feat/p5b-watchlist-signal-journal` was created, from that exact commit.

The supplied ZIP SHA256 is
`74a4ba5330af7de78ca5cba68b50d99a1c124daf6fbd3f6223b1105ceffcafbf`.
All 18 listed SHA256 entries matched before edits. The opening contract is
retained byte for byte at its supplied relative path. The separate Downloads
brief is reference context; the version inside the ZIP is the versioned handoff.

## Exact identity bytes

The literal byte authority is
`tests/fixtures/p5b_identity_vectors_v1.json` (supplied SHA256
`db9633c1549ebbd2a792d3f187a50ae989070ad94819ba202e4a4568763105c9`).
Each `preimage_text`, encoded UTF-8, contains the complete domain, one actual
NUL byte and canonical JSON. This freezes exact bytes, including key order,
normalization and nulls; explanatory pretty-printed JSON is not a preimage.
The fixture and domains/objects in WATCHLIST_JOURNAL_V1 and WATCHLIST_SIGNAL_V1
are adopted as the engineering implementation target without changing P5a.
Canonical JSON uses sorted keys, ASCII escaping, compact separators and no NaN.
The two supplied stdlib oracles and their eight tests validate design only.

## Author boundaries and interfaces

- Engineering Lead: root CLI registration, journal CLI, logging allowlist,
  eleventh installed-process harness and CI wiring, docs and final integration.
- ARQ/BE: journal errors/models/identity/transitions/application and domain /
  application author tests; read-only P5a interfaces.
- DB-OWNER: journal schema/storage and storage author tests, including recovery.
- SEC/SRE: initial read-only threat and failure-mode review; no product authorship.
- Independent QA and a distinct REVIEWER: own probes against the frozen final
  commit/tree; neither may author product implementation.

`normalized_snapshot(entry,current,previous,as_of)` returns the exact evaluation
identity object, without a caller result. `validate_snapshot` reparses all fields
and returns the normalized snapshot plus a freshly calculated P5a result.
`check_append` enforces predecessor equality and chronology; `derive_signals`
recalculates P5a and returns the exact independently eligible rule bodies/IDs.
Only application.record admits public record requests from original manifest
and exact P5a revision. Storage._record_validated is a private integration
boundary and revalidates content and derives signals inside its write transaction.
No dataclass or public verified flag grants admission. This is a local application
boundary, not protection against privileged code executing private functions.

The DB-OWNER wrote literal DDL before storage implementation or file DB writes.
The reviewed `schema.py` SHA256 at freeze is
`c355083565098a25f92007ed568b62a3b5a2e87136f2c7bc85ce5deed9e20f31`.
Its `STATEMENTS` tuple is the complete frozen SQL inventory. An in-memory SQLite
normalization confirmed 23 objects: four STRICT tables, eleven indexes (three
explicit and eight implicit PK/UNIQUE) and eight triggers. Metadata has immutable
owner/version; sequences bind immutable revision entry and mutable head advancing
one ordinal; immutable evaluations bind per-sequence sample/link/ordinal; immutable
signals bind same-sequence from/to evaluations and unique to/rule. Composite FKs
prevent cross-sequence links; the sequence/head cycle is deferred. All JSON cells
are bounded to 65536 UTF-8 bytes. CMTQ/schema1 has no migrations. Exact SQL, checks,
nullability, keys and trigger bodies are versioned in that literal module; formatting
changes do not authorize semantic DDL changes. Deep verification compares the full
SQLite-normalized inventory, including implicit indexes, against this authority.
Ruff required splitting one long Python string into adjacent literals, preserving
the exact SQL bytes. After that source-only formatting correction, schema.py SHA256
is `055cc6f451ad555d453f5bee29c4e50c2fce00143504b0d8e8c287a45a342a84`.
The original preimplementation freeze and this formatting reconciliation remain
recorded separately; no SQL statement semantics changed.

One operation budget covers parsing, origin read, journal transaction, verification,
copy and output. Source revision admission precedes the independent SQLite commit;
the design assumes immutable validated P5a revisions, with no distributed commit.
