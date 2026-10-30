# Architecture decisions

P8d proposes [ADR0015](0015-manual-watchlist-telegram-delivery.md) for independent
manual historical synthetic Watchlist delivery. Phase Lead design acceptance
is pending; this entry does not adopt an implementation or close a phase.

P4a adds [ADR-0005](0005-offline-temporal-discovery.md): explicit offline
temporal windows, deterministic reference events, consistent snapshot read and
honestly attested empty capture scope, without schema changes.

Use `NNNN-short-title.md` with sequential IDs. Each ADR states Context, Decision, Alternatives, Consequences, Status, and Revisit conditions. `Accepted` means the engineering choice is adopted for its stated scope; it does not mean the P0 quality gates or phase were accepted. New significant decisions require review. Do not create ADRs for trivial edits or decisions assigned to future phases.

Copy [the template](TEMPLATE.md). Current decisions: [ADR-0001](0001-modular-application-boundary.md), [ADR-0002](0002-multiarch-validation.md).

P1a adds [ADR-0003](0003-catalog-identity.md): explicit curated catalog identity,
printing/language/variant granularity and conservative contextual resolution.

P3a adds [ADR-0004](0004-offline-observation-persistence.md): atomic offline
SQLite snapshots, versioned schema, conservative replay and safe recovery.

P1c: [ADR0008](0008-multi-revision-metadata-capture.md) separates acquisition identity, replay equivalence and reviewed semantic comparability.
