"""Immutable P8d versions, bounds and exact key sets."""

ACKNOWLEDGEMENT = "SYNTHETIC_HISTORICAL_DEMONSTRATION"
PROVIDER = "telegram"
MAX_INPUT_BYTES = 1_048_576
MAX_RECEIPT_BYTES = MAX_INPUT_BYTES
MAX_ENTRY_BYTES = 65_536
MAX_INTENT_BYTES = 65_536
MAX_EVIDENCE_BYTES = 262_144
MAX_MESSAGE_BYTES = 4096
MAX_ROUTE_BYTES = 2048
MAX_CONSENT_BYTES = 4096
MAX_BINDING_BYTES = 8192
MAX_ID = (1 << 52) - 1
STATES = frozenset(
    {"ready", "in_flight", "retryable", "confirmed", "permanent_failure", "uncertain"}
)
ROUTE_FIELDS = frozenset(
    "route_version provider destination_key bot_id chat_id chat_type operator_attested".split()
)
BINDING_FIELDS = frozenset(
    {
        "binding_version",
        "provider",
        "delivery_id",
        "alert_id",
        "destination_key",
        "signal_id",
        "watch_id",
        "revision",
        "cmt_id",
        "policy_version",
        "renderer_version",
        "message_sha256",
        "evidence_sha256",
        "entry_sha256",
        "intent_sha256",
        "source_alert_sha256",
        "route_sha256",
        "consent_sha256",
    }
)
CONSENT_FIELDS = frozenset(
    {
        "consent_version",
        "acknowledgement",
        "alert_id",
        "signal_id",
        "watch_id",
        "revision",
        "message_sha256",
        "evidence_sha256",
        "entry_sha256",
        "intent_sha256",
        "source_alert_sha256",
        "route_sha256",
    }
)
PREPARED_FIELDS = frozenset(
    {
        "authority_version",
        "operation",
        "binding",
        "binding_sha256",
        "entry_json",
        "intent_json",
        "evidence_json",
        "message_text",
        "route_json",
        "consent_json",
    }
)
ALERT_FIELDS = frozenset(
    {
        "alert_id",
        "destination_key",
        "signal_id",
        "policy_version",
        "renderer_version",
        "channel",
        "state",
        "intent",
        "intent_sha256",
        "message_text",
        "message_sha256",
        "first_prepared_at",
    }
)
