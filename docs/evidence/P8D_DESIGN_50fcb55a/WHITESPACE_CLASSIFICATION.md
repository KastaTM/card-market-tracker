# P8d archived Brief whitespace classification

Classification: FAIL_ARCHIVED_INPUT_MARKDOWN_HARD_BREAKS - RETAINED.
This is a documented technical classification, not a passing check, suppression,
rule exception or Phase Lead/Orchestrator waiver. Gate B remains unaccepted.

Affected immutable candidate:
50fcb55a0b0e467bcb9d94561412a0f3c6ebc8f9,
tree d8d3eac1580dbfb3fa6aafcf94d033a8781204e2.

Full-range command:
    git diff --check 9dda9fba0aa9646a67596657d4ae9a7088903808 50fcb55a0b0e467bcb9d94561412a0f3c6ebc8f9

Observed exit2, seven trailing-whitespace locations, all in the received
docs/phases/P8D_CODEX_ENGINEERING_BRIEF.md lines9-15. Each is two trailing
spaces used for Markdown hard breaks on metadata lines. The original file,
handoff working copy, archived Git blob and ZIP entry agree byte for byte:
SHA256ed08f263239a8d1e628bd5af1f7efa8fe3329df2901fb5ea03dbc6dae6352cb6.
No archived contract or Brief was rewritten to remove the finding.

Newly authored design-range command:
    git diff --check 1f3f9cabd9381e8f2833d89dcaf20961cffadac7 50fcb55a0b0e467bcb9d94561412a0f3c6ebc8f9

Observed exit0. Both results are retained in original P8D_GATE_B_VALIDATION.json.
Initial Ruff E501 and new-document EOF/link construction failures are retained
in the candidate validation history; they were corrected without rule suppression.
There is no claim full-range whitespace passes or mandatory product gates passed.
The Phase Lead decides whether the proposed design is accepted after inspection.

## Original checksum sidecar copied byte for byte

An additional publication-range whitespace check returned exit2 for the final
CR byte in P8D_DESIGN_FREEZE_50fcb55a.zip.sha256 line1. The original locally
generated checksum sidecar uses CRLF; its unchanged98bytes were copied with
Git hash-object rather than newline normalization. Classification:
FAIL_ARCHIVED_CHECKSUM_CRLF - RETAINED. The original sidecar SHA256 is
1ee321b7264de968cfd8e91b20d4c8823645f25681cd87bad1d941c09b021905.
This is separate from the seven received Brief Markdown hard breaks above.

The initial publication guard stopped before push; no remote evidence branch
was written by that failed command. This classification is appended in a later
documentation commit; original commit/artifacts remain preserved. No rule,
attribute or byte normalization suppresses either finding. Full-range checks
remain FAIL with these explicit archival observations; no gate waiver or
passing-whitespace claim follows. This does not authorize schema/writer,
definitive identities, Telegram calls or design acceptance.
