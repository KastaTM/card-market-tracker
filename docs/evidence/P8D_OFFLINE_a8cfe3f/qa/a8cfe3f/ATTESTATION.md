# Final independent nonauthor QA attestation

Date:2026-10-30. Actor:/root/p8d_qa_independent.
Requested/selected profile:gpt-6.1-sol/high; effective backend is not independently observable.
Ownership:Lead-assigned nonauthor QA, distinct from BE/DB/CLI/transport authors and final REVIEWER.

Candidate HEAD:a8cfe3f4e9e2bc50558f3a9aee13a1fbd9bf6abd.
Candidate tree:820ddbdfc278ada9b2d713a1c0b834f5d59e5dbd.
**Scoped independent offline QA:PASS ?28/28 executed case groups, zero product findings.**
Committed independent probe22/22 PASS, exit0,31.296seconds.
Independent qualification/scanner supplement6/6 PASS, exit0,3.709seconds.
This attestation applies to these exact source bytes and these executed checks.
It grants no merge, phase acceptance, Orchestrator decision, live gate or closure.

## Exact candidate and clean-state proof

HEAD/tree were independently verified before and after both runs. Gitstatus was empty
before AND after; all444 tracked file SHA256 values remained identical.
The runner's before_after_identical=true, tracked_hashes_unchanged=true,
clean_before=true and clean_after=true. QA made NO TRACKED EDITS. All new code,
fixtures and reports were exclusively inside this assigned ignored directory.

Accepted frozen ADR0015/API/storage diff against50fcb55a produced no changed paths.
P5a/P5b/P8c/P8b source-module diff against9dda9fba produced no changed paths.
Raw comparison outputs are in preservation.json; complete tracked source hashes are
before.json/after.json. Runtime:3.13.15 (main, Sep  1 2026, 14:16:48) [MSC v.1944 64 bit (AMD64)]; SQLite3.53.1, Windows AMD64.

Historical e14 attestation, its22PASS/6PASS outcomes, and its transient concurrent
REVIEWER untracked-fixture observation remain preserved at ../ATTESTATION_E14.md
and adjacent original reports. This pristine corrected-candidate run supersedes
that cleanliness limitation; it does not rewrite the older observed result.
No historical failing author/QA/REVIEWER evidence was removed or reclassified.

## Reproduction and source-complete evidence

From C:/Projects/card-market-tracker-p8d:

    .venv/Scripts/python.exe -B .p8d-evidence/final/qa/a8cfe3f/run_final_qa.py

Equivalent individual runtime commands:

    .venv/Scripts/python.exe -B scripts/p8d_qa_probe.py --mode all
    .venv/Scripts/python.exe -B .p8d-evidence/final/qa/a8cfe3f/extra_probe.py

The committed probe is source-complete at the attested commit. The independent
additional runnable probe is extra_probe.py in this directory; it imports only
production code and this actor's own committed helpers, never author tests or
other reviewers' helpers. run_final_qa.py records command lines, exit codes,
wall runtimes, HEAD/tree/status, all tracked file digests and preservation diffs.
The full actual stdout and stderr are committed.stdout.json/committed.stderr.txt
and extra.stdout.json/extra.stderr.txt. executions.json and summary.json retain
machine-readable outcomes; before.json/after.json retain complete source hashes.

SHA256 of committed independent probe:
ca639d9e798a9d9077973b89c0e72b48d3f6cc4ba2234ba9dfbfa96c9976a6d0.
SHA256 of reviewed qualification wrapper:
07ba8fe9c5dfb85835657a0f29fdf3a1b5af2d3da0428f71e6fced11f47ec02d.
SHA256 of reviewed scanner:
3f143c541dba4415be7ca4ca46739472cb5de9551d2ac962a36bdc1ee4eb72c4.
SHA256 of extra_probe.py:
f97a310159c5f6bf2bb22f87f2715b43c009ad3bd4cf32ea0628aa667cf2c2f2.
SHA256 of run_final_qa.py:
d3e8768c94a789e18fa271a08115417dd410c2dd5c239bfadc34a6612bff8d85.

## Executed independent coverage

The original pipeline is genuine complete-manifest public P5a/P5b/P8c input,
not a mocked/hash-only authority. Five explicit historical checkpoints produce
two price-rule episodes in each independent original bundle. The stdlib byte
oracle is separate from product identity/canonical helpers and independently
reconstructs message/entry/intent/evidence/source/route/consent/binding commitments.

Executed committed groups:

- PASS: literal_identity_preimages_stdlib_oracle
- PASS: public_original_pipeline_ancient_replay_two_episodes
- PASS: public_consent_identity_privacy_source_nonmutation
- PASS: complete_pair_operational_stability_and_manifest_detachment_before_callbacks
- PASS: equivalent_independent_originals_replay_recompute
- PASS: rw01_genuine_incompatible_originals_rollback_verify_backup
- PASS: missing_original_vs_local_verify_complete_manifest_poison
- PASS: bounded_keyset_cursor_filter_strict_limits
- PASS: original_issued_receipt_forge_copy_mutation_budget_operation_expiry_reuse
- PASS: old_empty_restore_global_quarantine_unknown_and_new_deliveries
- PASS: provider_signal_dedup_across_genuine_alternate_preview_routes
- PASS: ancient_original_revision_after_newer_incompatible_latest
- PASS: negative_sql_calendar_bounds_rehashed_entry_restored_inventory
- PASS: fresh_process_cli_closed_json_exits_one_completion_privacy_import_token_network_denied
- PASS: fake_confirmed_durable_claim_unlocked_http_revalidation_replay_quarantine
- PASS: fake_native_outcome_matrix_uncertainty_and_no_resend
- PASS: valid429_exact_cooldown_thirdcap_event_watermark_historical_snapshot
- PASS: owner_handle_fencing_late_finalize_quiesced_recovery_no_resend
- PASS: same_budget_aggregate_origin_cap_postclaim_reserve_deadline
- PASS: postclaim_clock_rollback_overrides_provider_acceptance
- PASS: missing_original_unconfirmed_send_no_metadata_no_claim_no_dispatch
- PASS: two_real_sender_processes_one_durable_claim_one_fake_http_fresh_denied_replay

These include genuine same-watch/revision incompatible originals rejecting the
second prepare with complete rollback, healthy local verify and reopened backup;
equivalent original copies; exact ancient revision after incompatible newer head;
source-byte preservation; one-use private authority attacks before writer open;
old-empty/new/confirmed restore quarantine; native malformed/uncertain results;
valid429 inclusive cooldown/third lifetime cap and event watermark; historical
route snapshots; owner/recovery fencing; shared aggregate origins deadline and
reserved postclaim finalization; actual two sender processes/one durable claim,
one fake HTTP and one result; fresh confirmed replay with no originals and with
Telegram imports, token reads and socket events denied. Strict CLI/pagination/
DTO/error/logging/privacy and SQL semantic corruption checks also executed.

Executed independent supplementary groups:

- PASS: scanner_exact_path_detector_hash_all_reviewed_values_independent_P8d_vectors (0.003seconds)
- PASS: qualification_exact_specific_authorization_closed_bindings (0.112seconds)
- PASS: qualification_persisted_cumulative8metadata_1send_native_failure_no_refund (0.489seconds)
- PASS: qualification_reserve_persistence_expiry_blocks_native_dispatch_durable_cap (0.016seconds)
- PASS: qualification_crash_marker_parser_redaction_installed_prerequisite (0.008seconds)
- PASS: genuine_originals_fake_qualification_preflight_validate_send_receipt_postflight (2.691seconds)

The supplement independently checks every reviewed scanner path/detector/hash
pair and rejects changed path/type/value; it recomputes the P8d vector exceptions.
It checks exact specific authorization bindings, immutable pending preflight,
durable cumulative8metadata/1send counters across wrapper instances, reservation
retention after native failure, deadline expiry during durable reservation with
zero native dispatch, retained crash markers, parser redaction and the real
installed-wheel prerequisite rejection in an editable checkout.

A genuine public-source fake qualification runs preflight/validate/send/receipt
and separate offline source postflight with metadata3/send1, rejects repeat sends,
and keeps all statuses LIVE_UNVERIFIED. For that single case ONLY, the installed-
wheel prerequisite is explicitly simulated; this does not qualify an installed
artifact or grant live authorization. The actual editable-install refusal is
separately verified. Test evidence copies retain consumed send reservations;
no operational marker is cleared or new send authority created.

## Findings, limitations and authorization

No unresolved product defect was found in these executed final checks. No product
fix was authored or silently applied by QA. All source hashes stayed unchanged.
The supplement's fake transport never instantiates production TelegramTransport,
reads an actual token, or invokes a provider. All fixture stores were temporary.

This result does not replace full author tests/coverage, four final CI jobs,
thirteen installed harnesses or distinct final REVIEWER. Raw HTTP/TLS/DNS/body
parsing remains the unchanged P8b boundary; QA attacks normalized native outcomes,
not a real socket. Exhaustive ENOSPC/hot-journal/reparse and every crash instruction
window are not newly claimed by this supplement. Monotonic injection verifies
allowance accounting, not hard preemption of blocked kernel syscalls. Windows
directory fsync remains unsupported/disclosed. No physical Pi or electrical
power-loss durability claim is made. Future source changes invalidate affected
parts of this exact-candidate attestation and require an appropriate rerun.

**AC-WT20:BLOCKED ? LIVE_UNVERIFIED. No real Telegram authorization or call.**
P8d remains OPEN; only the Orchestrator accepts/merges/closes the phase.
