# P0.5b ownership and execution record

Date: 2026-10-14 Europe/Madrid. Authority: the archived
[Engineering Brief](P0_5B_CODEX_ENGINEERING_BRIEF.md), supplied by the user.
Only the Orchestrator accepts, integrates or closes phases. Merge is not authorized.

## Paths and shared state

Ownership was fixed before delegation. Lead alone owns Git, refs, commits, PR,
all repository edits, shared contracts, source fiches, roadmap and quality gates.
Specialists perform read-only analysis and return findings; no concurrent edits.
All specialists must read AGENTS/context and relevant authoritative contracts.

| Role / agent | Profile requested | Responsibility |
| --- | --- | --- |
| Lead `/root` | GPT-6.1 Sol; Medium mechanics, High licensing/integration | Git, documentation integration, serial probes, validation, publication |
| `integrations_data` | GPT-6.1 Sol / High | TCGdex source/model/REST correspondence, coverage, semantics; read-only |
| `security_rights` | GPT-6.1 Sol / High | eBay, Scrydex, GAME and Awin rights/field use; read-only |
| `architecture` | GPT-6.1 Sol / High | Proposed provenance boundary and TD-005; read-only |
| `qa_final` | GPT-6.1 Sol / High | Independent final-SHA detached checkout checks; no authorship |
| `reviewer_final` | GPT-6.1 Sol / High | Independent final-SHA review; distinct from QA and authors |

INTEGRATIONS/DATA, SEC and ARQ/DB-OWNER invocations explicitly requested
`gpt-6.1-sol/high` and were accepted. They returned read-only findings without
edits or direct probes. QA/REVIEWER acceptance and final results are recorded
in the external exact-candidate PR ledger. Accepted tool configuration
is observable, serving backend is not independently verified. Root is identified
as GPT-6-based Codex; its precise variant/client reasoning selection is unverified.
ChatGPT Phase Lead model is unobserved. No root switch or Astra escalation claimed.

## Baseline and preservation

Before edits, remote/status/branches/worktrees and `git fetch origin` were checked.
Initial clean checkout: `feat/p4a-offline-temporal-discovery`,
`c5ed228af831a2a6ed8a12c7072777d3908296a5`. Local main was `5175d5b`, behind;
P3a/P4a QA/reviewer detached worktrees and existing branches were preserved.
Fetched `origin/main`: `6385c952a9f2024c8b7bdb33d37fa21017029bd5`;
tree `8fa2abeb9f4e8991bab1b2895fc397f64bb39a19`; ordered parents
`734641a7ef920688677cdea6bc82f908a2856927` and
`c5ed228af831a2a6ed8a12c7072777d3908296a5`. Diff from initial HEAD is empty.
Branch `docs/p05b-real-source-qualification` was absent locally/remotely and
created from that verified baseline. No reset, force push or rebase.

Sandbox process creation failed before command execution. Automatically reviewed
elevated shell execution succeeded; this is an environment limit, not a source
failure. Read-only research and authorized workspace/Git operations use that path.

## Contract and requests

The supplied attachment contains the entire Engineering Brief, archived byte
for byte; SHA256 `144BE891A49F1C3520AD6FC2ACE296AF115D01F3B289120FF63B8800477B970C`.
It did not contain the separate Phase Contract. After an asynchronous request,
the user supplied the full contract as text in this conversation. Its complete
wording and twelve criteria are now [archived](P0_5B_REAL_SOURCE_QUALIFICATION_CONTRACT.md);
only table-spacing whitespace was normalized during transcription. UTF-8 file
SHA256 `2CB31B6B998FE7234D8D5FAEDE85FC84FBE73A9E0B5F2C07996481A7C8009CCE`.
Git newline normalization can change file bytes; this is the precommit file hash.
The earlier absence marker is replaced; no criteria were reconstructed/invented.

Only Lead may issue direct data requests. Shared budget: 12 total, 6/provider,
serial, <=15 seconds, <=256 KiB, no automatic retries or unchecked redirects.
Specialists may browse public documentation; no API, raw data-file or storefront
probe without a written preflight coordinated with Lead. No accounts, payments,
credentials, contact, subscription, accepted terms or runtime integration.
