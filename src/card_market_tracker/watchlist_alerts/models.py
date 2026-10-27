"""Frozen pure P8c versions, bounds and exact semantic key sets."""

VERSION = 1
POLICY_VERSION = "watchlist_synthetic_alert_v1"
RENDERER_VERSION = 1
CHANNEL = "offline_preview"
STATE = "pending"
MAX_INPUT_BYTES = 1_048_576
MAX_INTENT_BYTES = 65_536
MAX_EVIDENCE_BYTES = 262_144
MAX_MESSAGE_BYTES = 4096
MAX_RECEIPT_BYTES = 1_048_576
EVIDENCE_FIELDS = frozenset({"version", "signal", "predecessor", "current"})
SIGNAL_FIELDS = frozenset(
    {
        "version",
        "kind",
        "mode",
        "sequence_id",
        "rule",
        "from_evaluation_id",
        "to_evaluation_id",
        "signal_id",
    }
)
EVALUATION_FIELDS = frozenset(
    {
        "evaluation_id",
        "sequence_id",
        "ordinal",
        "predecessor_evaluation_id",
        "snapshot",
        "evaluation_result",
    }
)
INTENT_FIELDS = frozenset(
    {
        "version",
        "policy_version",
        "renderer_version",
        "channel",
        "state",
        "signal_id",
        "kind",
        "mode",
        "rule",
        "sequence_id",
        "watch_id",
        "revision",
        "cmt_id",
        "from_evaluation_id",
        "to_evaluation_id",
    }
)
PREPARED_FIELDS = frozenset(
    {
        "version",
        "alert_id",
        "destination_key",
        "signal_id",
        "policy_version",
        "renderer_version",
        "channel",
        "state",
        "intent_json",
        "intent_sha256",
        "evidence_json",
        "evidence_sha256",
        "message_text",
        "message_sha256",
    }
)
