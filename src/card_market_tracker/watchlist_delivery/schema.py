"""Frozen CMTZ schema1; byte-exact accepted SQL and inventory."""

OWNER = "card-market-tracker.watchlist-telegram-delivery"
APPLICATION_ID = 0x434D545A
SCHEMA_VERSION = 1

STATEMENTS = (
    (
        "CREATE TABLE wtd_metadata (\n    singleton INTEGER PRIMARY KEY NOT"
        " NULL CHECK(singleton=1),\n    owner TEXT NOT NULL CHECK(owner='ca"
        "rd-market-tracker.watchlist-telegram-delivery'),\n    schema_versi"
        "on INTEGER NOT NULL CHECK(schema_version=1),\n    send_quarantined"
        " INTEGER NOT NULL CHECK(send_quarantined IN (0,1)),\n    operation"
        "al_high_water TEXT NOT NULL CHECK(typeof(operational_high_water)="
        "'text' AND length(CAST(operational_high_water AS BLOB))=27 AND op"
        "erational_high_water GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9]["
        "0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0"
        "-9]Z')\n) STRICT"
    ),
    (
        "CREATE TABLE wtd_destinations (\n    destination_key TEXT PRIMARY "
        "KEY NOT NULL CHECK(typeof(destination_key)='text' AND length(CAST"
        "(destination_key AS BLOB)) BETWEEN 1 AND 64 AND length(destinatio"
        "n_key)=length(CAST(destination_key AS BLOB)) AND substr(destinati"
        "on_key,1,1) GLOB '[a-z]' AND destination_key NOT GLOB '*[^a-z0-9_"
        "-]*'),\n    provider TEXT NOT NULL CHECK(provider='telegram'),\n   "
        " bot_id INTEGER NOT NULL CHECK(typeof(bot_id)='integer' AND bot_i"
        "d BETWEEN 1 AND 4503599627370495),\n    chat_id INTEGER NOT NULL C"
        "HECK(typeof(chat_id)='integer' AND chat_id BETWEEN 1 AND 45035996"
        "27370495),\n    chat_type TEXT NOT NULL CHECK(chat_type='private')"
        ",\n    operator_attested INTEGER NOT NULL CHECK(operator_attested="
        "1),\n    route_json TEXT NOT NULL CHECK(typeof(route_json)='text' "
        "AND length(CAST(route_json AS BLOB)) BETWEEN 2 AND 2048),\n    rou"
        "te_sha256 TEXT NOT NULL CHECK(typeof(route_sha256)='text' AND len"
        "gth(CAST(route_sha256 AS BLOB))=64 AND route_sha256 NOT GLOB '*[^"
        "0-9a-f]*'),\n    registered_at TEXT NOT NULL CHECK(typeof(register"
        "ed_at)='text' AND length(CAST(registered_at AS BLOB))=27 AND regi"
        "stered_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9]["
        "0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),\n   "
        " validated_at TEXT CHECK(validated_at IS NULL OR (typeof(validate"
        "d_at)='text' AND length(CAST(validated_at AS BLOB))=27 AND valida"
        "ted_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9"
        "]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z')),\n    U"
        "NIQUE(destination_key,route_sha256)\n) STRICT"
    ),
    (
        "CREATE TABLE wtd_watch_entries (\n    watch_id TEXT NOT NULL CHECK"
        "(typeof(watch_id)='text' AND length(CAST(watch_id AS BLOB))=69 AN"
        "D length(watch_id)=69 AND substr(watch_id,1,5)='wlt1_' AND substr"
        "(watch_id,6) NOT GLOB '*[^0-9a-f]*'),\n    revision INTEGER NOT NU"
        "LL CHECK(typeof(revision)='integer' AND revision BETWEEN 1 AND 21"
        "47483647),\n    entry_json TEXT NOT NULL CHECK(typeof(entry_json)="
        "'text' AND length(CAST(entry_json AS BLOB)) BETWEEN 2 AND 65536),"
        "\n    entry_sha256 TEXT NOT NULL CHECK(typeof(entry_sha256)='text'"
        " AND length(CAST(entry_sha256 AS BLOB))=64 AND entry_sha256 NOT G"
        "LOB '*[^0-9a-f]*'),\n    PRIMARY KEY(watch_id,revision),\n    UNIQU"
        "E(watch_id,revision,entry_sha256)\n) STRICT"
    ),
    (
        "CREATE TABLE wtd_deliveries (\n    delivery_id TEXT PRIMARY KEY NO"
        "T NULL CHECK(typeof(delivery_id)='text' AND length(CAST(delivery_"
        "id AS BLOB))=70 AND length(delivery_id)=70 AND substr(delivery_id"
        ",1,6)='wtdl1_' AND substr(delivery_id,7) NOT GLOB '*[^0-9a-f]*'),"
        "\n    provider TEXT NOT NULL CHECK(provider='telegram'),\n    alert"
        "_id TEXT NOT NULL CHECK(typeof(alert_id)='text' AND length(CAST(a"
        "lert_id AS BLOB))=70 AND length(alert_id)=70 AND substr(alert_id,"
        "1,6)='walt1_' AND substr(alert_id,7) NOT GLOB '*[^0-9a-f]*'),\n   "
        " destination_key TEXT NOT NULL CHECK(typeof(destination_key)='tex"
        "t' AND length(CAST(destination_key AS BLOB)) BETWEEN 1 AND 64 AND"
        " length(destination_key)=length(CAST(destination_key AS BLOB)) AN"
        "D substr(destination_key,1,1) GLOB '[a-z]' AND destination_key NO"
        "T GLOB '*[^a-z0-9_-]*'),\n    signal_id TEXT NOT NULL CHECK(typeof"
        "(signal_id)='text' AND length(CAST(signal_id AS BLOB))=70 AND len"
        "gth(signal_id)=70 AND substr(signal_id,1,6)='wsig1_' AND substr(s"
        "ignal_id,7) NOT GLOB '*[^0-9a-f]*'),\n    watch_id TEXT NOT NULL C"
        "HECK(typeof(watch_id)='text' AND length(CAST(watch_id AS BLOB))=6"
        "9 AND length(watch_id)=69 AND substr(watch_id,1,5)='wlt1_' AND su"
        "bstr(watch_id,6) NOT GLOB '*[^0-9a-f]*'),\n    revision INTEGER NO"
        "T NULL CHECK(typeof(revision)='integer' AND revision BETWEEN 1 AN"
        "D 2147483647),\n    cmt_id TEXT NOT NULL CHECK(typeof(cmt_id)='tex"
        "t' AND length(CAST(cmt_id AS BLOB))=36 AND length(cmt_id)=36 AND "
        "cmt_id NOT GLOB '*[^0-9a-f-]*'),\n    policy_version TEXT NOT NULL"
        " CHECK(policy_version='watchlist_synthetic_alert_v1'),\n    render"
        "er_version INTEGER NOT NULL CHECK(renderer_version=1),\n    intent"
        "_json TEXT NOT NULL CHECK(typeof(intent_json)='text' AND length(C"
        "AST(intent_json AS BLOB)) BETWEEN 2 AND 65536),\n    evidence_json"
        " TEXT NOT NULL CHECK(typeof(evidence_json)='text' AND length(CAST"
        "(evidence_json AS BLOB)) BETWEEN 2 AND 262144),\n    message_text "
        "TEXT NOT NULL CHECK(typeof(message_text)='text' AND length(CAST(m"
        "essage_text AS BLOB)) BETWEEN 1 AND 4096),\n    consent_json TEXT "
        "NOT NULL CHECK(typeof(consent_json)='text' AND length(CAST(consen"
        "t_json AS BLOB)) BETWEEN 2 AND 4096),\n    binding_json TEXT NOT N"
        "ULL CHECK(typeof(binding_json)='text' AND length(CAST(binding_jso"
        "n AS BLOB)) BETWEEN 2 AND 8192),\n    intent_sha256 TEXT NOT NULL "
        "CHECK(typeof(intent_sha256)='text' AND length(CAST(intent_sha256 "
        "AS BLOB))=64 AND intent_sha256 NOT GLOB '*[^0-9a-f]*'),\n    evide"
        "nce_sha256 TEXT NOT NULL CHECK(typeof(evidence_sha256)='text' AND"
        " length(CAST(evidence_sha256 AS BLOB))=64 AND evidence_sha256 NOT"
        " GLOB '*[^0-9a-f]*'),\n    message_sha256 TEXT NOT NULL CHECK(type"
        "of(message_sha256)='text' AND length(CAST(message_sha256 AS BLOB)"
        ")=64 AND message_sha256 NOT GLOB '*[^0-9a-f]*'),\n    entry_sha256"
        " TEXT NOT NULL CHECK(typeof(entry_sha256)='text' AND length(CAST("
        "entry_sha256 AS BLOB))=64 AND entry_sha256 NOT GLOB '*[^0-9a-f]*'"
        "),\n    source_alert_sha256 TEXT NOT NULL CHECK(typeof(source_aler"
        "t_sha256)='text' AND length(CAST(source_alert_sha256 AS BLOB))=64"
        " AND source_alert_sha256 NOT GLOB '*[^0-9a-f]*'),\n    route_sha25"
        "6 TEXT NOT NULL CHECK(typeof(route_sha256)='text' AND length(CAST"
        "(route_sha256 AS BLOB))=64 AND route_sha256 NOT GLOB '*[^0-9a-f]*"
        "'),\n    consent_sha256 TEXT NOT NULL CHECK(typeof(consent_sha256)"
        "='text' AND length(CAST(consent_sha256 AS BLOB))=64 AND consent_s"
        "ha256 NOT GLOB '*[^0-9a-f]*'),\n    binding_sha256 TEXT NOT NULL C"
        "HECK(typeof(binding_sha256)='text' AND length(CAST(binding_sha256"
        " AS BLOB))=64 AND binding_sha256 NOT GLOB '*[^0-9a-f]*'),\n    pre"
        "pared_at TEXT NOT NULL CHECK(typeof(prepared_at)='text' AND lengt"
        "h(CAST(prepared_at AS BLOB))=27 AND prepared_at GLOB '[0-9][0-9]["
        "0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]."
        "[0-9][0-9][0-9][0-9][0-9][0-9]Z'),\n    UNIQUE(provider,signal_id)"
        ",\n    FOREIGN KEY(destination_key,route_sha256) REFERENCES wtd_de"
        "stinations(destination_key,route_sha256) ON DELETE RESTRICT,\n    "
        "FOREIGN KEY(watch_id,revision,entry_sha256) REFERENCES wtd_watch_"
        "entries(watch_id,revision,entry_sha256) ON DELETE RESTRICT\n) STRI"
        "CT"
    ),
    (
        "CREATE TABLE wtd_state (\n    delivery_id TEXT PRIMARY KEY NOT NUL"
        "L REFERENCES wtd_deliveries(delivery_id) ON DELETE RESTRICT CHECK"
        "(typeof(delivery_id)='text' AND length(CAST(delivery_id AS BLOB))"
        "=70 AND length(delivery_id)=70 AND substr(delivery_id,1,6)='wtdl1"
        "_' AND substr(delivery_id,7) NOT GLOB '*[^0-9a-f]*'),\n    state T"
        "EXT NOT NULL CHECK(state IN ('ready','in_flight','retryable','con"
        "firmed','permanent_failure','uncertain')),\n    attempt_count INTE"
        "GER NOT NULL CHECK(typeof(attempt_count)='integer' AND attempt_co"
        "unt BETWEEN 0 AND 3),\n    current_attempt_id TEXT CHECK(current_a"
        "ttempt_id IS NULL OR (typeof(current_attempt_id)='text' AND lengt"
        "h(CAST(current_attempt_id AS BLOB))=70 AND length(current_attempt"
        "_id)=70 AND substr(current_attempt_id,1,6)='wtat1_' AND substr(cu"
        "rrent_attempt_id,7) NOT GLOB '*[^0-9a-f]*')),\n    current_owner T"
        "EXT CHECK(current_owner IS NULL OR (typeof(current_owner)='text' "
        "AND length(CAST(current_owner AS BLOB))=64 AND current_owner NOT "
        "GLOB '*[^0-9a-f]*')),\n    not_before TEXT CHECK(not_before IS NUL"
        "L OR (typeof(not_before)='text' AND length(CAST(not_before AS BLO"
        "B))=27 AND not_before GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9]"
        "[0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9]["
        "0-9]Z')),\n    updated_at TEXT NOT NULL CHECK(typeof(updated_at)='"
        "text' AND length(CAST(updated_at AS BLOB))=27 AND updated_at GLOB"
        " '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9"
        "]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),\n    FOREIGN KEY(c"
        "urrent_attempt_id) REFERENCES wtd_claims(attempt_id) ON DELETE RE"
        "STRICT DEFERRABLE INITIALLY DEFERRED,\n    CHECK((state='in_flight"
        "' AND current_attempt_id IS NOT NULL AND current_owner IS NOT NUL"
        "L) OR (state!='in_flight' AND current_attempt_id IS NULL AND curr"
        "ent_owner IS NULL)),\n    CHECK((state='retryable' AND not_before "
        "IS NOT NULL AND attempt_count<3) OR (state!='retryable' AND not_b"
        "efore IS NULL)),\n    CHECK((state='ready' AND attempt_count=0) OR"
        " (state!='ready' AND attempt_count>0))\n) STRICT"
    ),
    (
        "CREATE TABLE wtd_claims (\n    attempt_id TEXT PRIMARY KEY NOT NUL"
        "L CHECK(typeof(attempt_id)='text' AND length(CAST(attempt_id AS B"
        "LOB))=70 AND length(attempt_id)=70 AND substr(attempt_id,1,6)='wt"
        "at1_' AND substr(attempt_id,7) NOT GLOB '*[^0-9a-f]*'),\n    deliv"
        "ery_id TEXT NOT NULL REFERENCES wtd_deliveries(delivery_id) ON DE"
        "LETE RESTRICT CHECK(typeof(delivery_id)='text' AND length(CAST(de"
        "livery_id AS BLOB))=70 AND length(delivery_id)=70 AND substr(deli"
        "very_id,1,6)='wtdl1_' AND substr(delivery_id,7) NOT GLOB '*[^0-9a"
        "-f]*'),\n    owner TEXT NOT NULL CHECK(typeof(owner)='text' AND le"
        "ngth(CAST(owner AS BLOB))=64 AND owner NOT GLOB '*[^0-9a-f]*'),\n "
        "   ordinal INTEGER NOT NULL CHECK(typeof(ordinal)='integer' AND o"
        "rdinal BETWEEN 1 AND 3),\n    claimed_at TEXT NOT NULL CHECK(typeo"
        "f(claimed_at)='text' AND length(CAST(claimed_at AS BLOB))=27 AND "
        "claimed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9]"
        "[0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),\n  "
        "  route_validated_at TEXT NOT NULL CHECK(typeof(route_validated_a"
        "t)='text' AND length(CAST(route_validated_at AS BLOB))=27 AND rou"
        "te_validated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T"
        "[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'"
        "),\n    UNIQUE(delivery_id,ordinal),\n    UNIQUE(owner)\n) STRICT"
    ),
    (
        "CREATE TABLE wtd_results (\n    attempt_id TEXT PRIMARY KEY NOT NU"
        "LL REFERENCES wtd_claims(attempt_id) ON DELETE RESTRICT CHECK(typ"
        "eof(attempt_id)='text' AND length(CAST(attempt_id AS BLOB))=70 AN"
        "D length(attempt_id)=70 AND substr(attempt_id,1,6)='wtat1_' AND s"
        "ubstr(attempt_id,7) NOT GLOB '*[^0-9a-f]*'),\n    owner TEXT NOT N"
        "ULL CHECK(typeof(owner)='text' AND length(CAST(owner AS BLOB))=64"
        " AND owner NOT GLOB '*[^0-9a-f]*'),\n    state TEXT NOT NULL CHECK"
        "(state IN ('confirmed','retryable','permanent_failure','uncertain"
        "')),\n    completed_at TEXT NOT NULL CHECK(typeof(completed_at)='t"
        "ext' AND length(CAST(completed_at AS BLOB))=27 AND completed_at G"
        "LOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9]["
        "0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z'),\n    error_cate"
        "gory TEXT CHECK(error_category IS NULL OR (error_category IN ('ra"
        "te_limited','retry_exhausted','provider_rejection','network_uncer"
        "tain','transport_timeout','transport_failure','provider_invalid',"
        "'bot_mismatch','destination_mismatch','recovered','clock_skew','t"
        "oken_configuration','local_commit_failed','deadline_exceeded'))),"
        "\n    retry_after INTEGER CHECK(retry_after IS NULL OR (typeof(ret"
        "ry_after)='integer' AND retry_after BETWEEN 1 AND 86400)),\n    no"
        "t_before TEXT CHECK(not_before IS NULL OR (typeof(not_before)='te"
        "xt' AND length(CAST(not_before AS BLOB))=27 AND not_before GLOB '"
        "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:"
        "[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]Z')),\n    message_id INT"
        "EGER CHECK(message_id IS NULL OR (typeof(message_id)='integer' AN"
        "D message_id BETWEEN 1 AND 9223372036854775807)),\n    accepted_at"
        " INTEGER CHECK(accepted_at IS NULL OR (typeof(accepted_at)='integ"
        "er' AND accepted_at BETWEEN 1 AND 253402300799)),\n    bot_id INTE"
        "GER CHECK(bot_id IS NULL OR (typeof(bot_id)='integer' AND bot_id "
        "BETWEEN 1 AND 4503599627370495)),\n    chat_id INTEGER CHECK(chat_"
        "id IS NULL OR (typeof(chat_id)='integer' AND chat_id BETWEEN 1 AN"
        "D 4503599627370495)),\n    CHECK((state='confirmed' AND error_cate"
        "gory IS NULL AND retry_after IS NULL AND not_before IS NULL AND m"
        "essage_id IS NOT NULL AND accepted_at IS NOT NULL AND bot_id IS N"
        "OT NULL AND chat_id IS NOT NULL) OR (state!='confirmed' AND error"
        "_category IS NOT NULL AND message_id IS NULL AND accepted_at IS N"
        "ULL AND bot_id IS NULL AND chat_id IS NULL)),\n    CHECK((state='r"
        "etryable' AND error_category='rate_limited' AND retry_after IS NO"
        "T NULL AND not_before IS NOT NULL) OR (state='permanent_failure' "
        "AND error_category='retry_exhausted' AND retry_after IS NOT NULL "
        "AND not_before IS NULL) OR (state='permanent_failure' AND error_c"
        "ategory='provider_rejection' AND retry_after IS NULL AND not_befo"
        "re IS NULL) OR (state='uncertain' AND error_category IN ('network"
        "_uncertain','transport_timeout','transport_failure','provider_inv"
        "alid','bot_mismatch','destination_mismatch','recovered','clock_sk"
        "ew','token_configuration','local_commit_failed','deadline_exceede"
        "d') AND retry_after IS NULL AND not_before IS NULL) OR state='con"
        "firmed')\n) STRICT"
    ),
    ("CREATE INDEX wtd_deliveries_by_destination ON wtd_deliveries(destination_key,delivery_id)"),
    ("CREATE INDEX wtd_deliveries_by_watch ON wtd_deliveries(watch_id,revision,delivery_id)"),
    ("CREATE INDEX wtd_state_by_state ON wtd_state(state,delivery_id)"),
    (
        "CREATE TRIGGER wtd_metadata_update_guard BEFORE UPDATE ON wtd_met"
        "adata\nWHEN NEW.singleton!=OLD.singleton OR NEW.owner!=OLD.owner O"
        "R NEW.schema_version!=OLD.schema_version OR NEW.send_quarantined<"
        "OLD.send_quarantined OR NEW.operational_high_water<OLD.operationa"
        "l_high_water\nBEGIN SELECT RAISE(ABORT,'immutable_metadata'); END"
    ),
    (
        "CREATE TRIGGER wtd_destinations_update_guard BEFORE UPDATE ON wtd"
        "_destinations\nWHEN NEW.destination_key!=OLD.destination_key OR NE"
        "W.provider!=OLD.provider OR NEW.bot_id!=OLD.bot_id OR NEW.chat_id"
        "!=OLD.chat_id OR NEW.chat_type!=OLD.chat_type OR NEW.operator_att"
        "ested!=OLD.operator_attested OR NEW.route_json!=OLD.route_json OR"
        " NEW.route_sha256!=OLD.route_sha256 OR NEW.registered_at!=OLD.reg"
        "istered_at OR NEW.validated_at IS NULL OR NEW.validated_at<coales"
        "ce(OLD.validated_at,OLD.registered_at) OR NEW.validated_at<(SELEC"
        "T operational_high_water FROM wtd_metadata WHERE singleton=1)\nBEG"
        "IN SELECT RAISE(ABORT,'immutable_route'); END"
    ),
    (
        "CREATE TRIGGER wtd_destinations_insert_guard BEFORE INSERT ON wtd"
        "_destinations\nWHEN NEW.validated_at IS NOT NULL OR NEW.registered"
        "_at<(SELECT operational_high_water FROM wtd_metadata WHERE single"
        "ton=1)\nBEGIN SELECT RAISE(ABORT,'invalid_route_registration'); EN"
        "D"
    ),
    (
        "CREATE TRIGGER wtd_destinations_insert_clock AFTER INSERT ON wtd_"
        "destinations\nBEGIN UPDATE wtd_metadata SET operational_high_water"
        "=NEW.registered_at WHERE singleton=1; END"
    ),
    (
        "CREATE TRIGGER wtd_destinations_validate_clock AFTER UPDATE ON wt"
        "d_destinations\nBEGIN UPDATE wtd_metadata SET operational_high_wat"
        "er=NEW.validated_at WHERE singleton=1; END"
    ),
    (
        "CREATE TRIGGER wtd_deliveries_insert_guard BEFORE INSERT ON wtd_d"
        "eliveries\nWHEN NEW.prepared_at<(SELECT operational_high_water FRO"
        "M wtd_metadata WHERE singleton=1)\nBEGIN SELECT RAISE(ABORT,'clock"
        "_skew'); END"
    ),
    (
        "CREATE TRIGGER wtd_deliveries_insert_state AFTER INSERT ON wtd_de"
        "liveries\nBEGIN\n    INSERT INTO wtd_state(delivery_id,state,attemp"
        "t_count,current_attempt_id,current_owner,not_before,updated_at) V"
        "ALUES(NEW.delivery_id,'ready',0,NULL,NULL,NULL,NEW.prepared_at);\n"
        "    UPDATE wtd_metadata SET operational_high_water=NEW.prepared_a"
        "t WHERE singleton=1;\nEND"
    ),
    (
        "CREATE TRIGGER wtd_state_insert_guard BEFORE INSERT ON wtd_state\n"
        "WHEN NEW.state!='ready' OR NEW.attempt_count!=0 OR NEW.current_at"
        "tempt_id IS NOT NULL OR NEW.current_owner IS NOT NULL OR NEW.not_"
        "before IS NOT NULL OR NEW.updated_at IS NOT (SELECT prepared_at F"
        "ROM wtd_deliveries WHERE delivery_id=NEW.delivery_id) OR EXISTS(S"
        "ELECT 1 FROM wtd_claims WHERE delivery_id=NEW.delivery_id)\nBEGIN "
        "SELECT RAISE(ABORT,'invalid_initial_state'); END"
    ),
    (
        "CREATE TRIGGER wtd_state_update_guard BEFORE UPDATE ON wtd_state\n"
        "WHEN NEW.delivery_id!=OLD.delivery_id OR NOT (\n    (OLD.state IN "
        "('ready','retryable') AND NEW.state='in_flight' AND NEW.attempt_c"
        "ount=OLD.attempt_count+1 AND NEW.not_before IS NULL AND EXISTS(SE"
        "LECT 1 FROM wtd_claims c WHERE c.attempt_id=NEW.current_attempt_i"
        "d AND c.delivery_id=OLD.delivery_id AND c.owner=NEW.current_owner"
        " AND c.ordinal=NEW.attempt_count AND c.claimed_at=NEW.updated_at "
        "AND NOT EXISTS(SELECT 1 FROM wtd_results r WHERE r.attempt_id=c.a"
        "ttempt_id)))\n    OR (OLD.state='in_flight' AND NEW.attempt_count="
        "OLD.attempt_count AND NEW.current_attempt_id IS NULL AND NEW.curr"
        "ent_owner IS NULL AND EXISTS(SELECT 1 FROM wtd_results r WHERE r."
        "attempt_id=OLD.current_attempt_id AND r.owner=OLD.current_owner A"
        "ND r.state=NEW.state AND r.completed_at=NEW.updated_at AND r.not_"
        "before IS NEW.not_before))\n)\nBEGIN SELECT RAISE(ABORT,'invalid_st"
        "ate_transition'); END"
    ),
    (
        "CREATE TRIGGER wtd_claims_insert_guard BEFORE INSERT ON wtd_claim"
        "s\nWHEN NOT EXISTS(\n    SELECT 1 FROM wtd_state s JOIN wtd_deliver"
        "ies d ON d.delivery_id=s.delivery_id JOIN wtd_destinations x ON x"
        ".destination_key=d.destination_key JOIN wtd_watch_entries e ON e."
        "watch_id=d.watch_id AND e.revision=d.revision AND e.entry_sha256="
        "d.entry_sha256 JOIN wtd_metadata m ON m.singleton=1\n    WHERE s.d"
        "elivery_id=NEW.delivery_id AND m.send_quarantined=0 AND s.state I"
        "N ('ready','retryable') AND s.attempt_count<3 AND NEW.ordinal=s.a"
        "ttempt_count+1 AND s.current_attempt_id IS NULL AND s.current_own"
        "er IS NULL AND x.validated_at IS NOT NULL AND NEW.route_validated"
        "_at=x.validated_at AND NEW.claimed_at>=NEW.route_validated_at AND"
        " NEW.claimed_at>=s.updated_at AND NEW.claimed_at>=m.operational_h"
        "igh_water AND (s.not_before IS NULL OR NEW.claimed_at>=s.not_befo"
        "re) AND (SELECT count(*) FROM wtd_claims c WHERE c.delivery_id=s."
        "delivery_id)=s.attempt_count\n)\nBEGIN SELECT RAISE(ABORT,'claim_re"
        "fused'); END"
    ),
    (
        "CREATE TRIGGER wtd_claims_insert_state AFTER INSERT ON wtd_claims"
        "\nBEGIN\n    UPDATE wtd_state SET state='in_flight',attempt_count=N"
        "EW.ordinal,current_attempt_id=NEW.attempt_id,current_owner=NEW.ow"
        "ner,not_before=NULL,updated_at=NEW.claimed_at WHERE delivery_id=N"
        "EW.delivery_id AND state IN ('ready','retryable') AND attempt_cou"
        "nt=NEW.ordinal-1 AND current_attempt_id IS NULL AND current_owner"
        " IS NULL;\n    SELECT CASE WHEN changes()!=1 THEN RAISE(ABORT,'sta"
        "le_attempt') END;\n    UPDATE wtd_metadata SET operational_high_wa"
        "ter=NEW.claimed_at WHERE singleton=1;\nEND"
    ),
    (
        "CREATE TRIGGER wtd_results_insert_guard BEFORE INSERT ON wtd_resu"
        "lts\nWHEN NOT EXISTS(\n    SELECT 1 FROM wtd_claims c JOIN wtd_stat"
        "e s ON s.delivery_id=c.delivery_id JOIN wtd_metadata m ON m.singl"
        "eton=1 JOIN wtd_deliveries d ON d.delivery_id=c.delivery_id JOIN "
        "wtd_destinations x ON x.destination_key=d.destination_key\n    WHE"
        "RE c.attempt_id=NEW.attempt_id AND c.owner=NEW.owner AND s.state="
        "'in_flight' AND s.current_attempt_id=c.attempt_id AND s.current_o"
        "wner=NEW.owner AND s.attempt_count=c.ordinal AND NEW.completed_at"
        ">=c.claimed_at AND NEW.completed_at>=m.operational_high_water\n   "
        " AND (NEW.state!='retryable' OR (c.ordinal<3 AND NEW.not_before I"
        "S (strftime('%Y-%m-%dT%H:%M:%S',substr(NEW.completed_at,1,19),pri"
        "ntf('+%d seconds',NEW.retry_after)) || substr(NEW.completed_at,20"
        "))))\n    AND (NEW.error_category IS NOT 'retry_exhausted' OR c.or"
        "dinal=3)\n    AND (NEW.state!='confirmed' OR (NEW.bot_id=x.bot_id "
        "AND NEW.chat_id=x.chat_id))\n)\nBEGIN SELECT RAISE(ABORT,'stale_att"
        "empt'); END"
    ),
    (
        "CREATE TRIGGER wtd_results_insert_state AFTER INSERT ON wtd_resul"
        "ts\nBEGIN\n    UPDATE wtd_state SET state=NEW.state,current_attempt"
        "_id=NULL,current_owner=NULL,not_before=NEW.not_before,updated_at="
        "NEW.completed_at WHERE current_attempt_id=NEW.attempt_id AND curr"
        "ent_owner=NEW.owner AND state='in_flight';\n    SELECT CASE WHEN c"
        "hanges()!=1 THEN RAISE(ABORT,'stale_attempt') END;\n    UPDATE wtd"
        "_metadata SET operational_high_water=NEW.completed_at WHERE singl"
        "eton=1;\nEND"
    ),
    (
        "CREATE TRIGGER wtd_watch_entries_no_update BEFORE UPDATE ON wtd_w"
        "atch_entries BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_deliveries_no_update BEFORE UPDATE ON wtd_deli"
        "veries BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_claims_no_update BEFORE UPDATE ON wtd_claims B"
        "EGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_results_no_update BEFORE UPDATE ON wtd_results"
        " BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_metadata_no_delete BEFORE DELETE ON wtd_metada"
        "ta BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_destinations_no_delete BEFORE DELETE ON wtd_de"
        "stinations BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_watch_entries_no_delete BEFORE DELETE ON wtd_w"
        "atch_entries BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_deliveries_no_delete BEFORE DELETE ON wtd_deli"
        "veries BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_state_no_delete BEFORE DELETE ON wtd_state BEG"
        "IN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_claims_no_delete BEFORE DELETE ON wtd_claims B"
        "EGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
    (
        "CREATE TRIGGER wtd_results_no_delete BEFORE DELETE ON wtd_results"
        " BEGIN SELECT RAISE(ABORT,'immutable_record'); END"
    ),
)

_EXPECTED = (
    ("index", "sqlite_autoindex_wtd_claims_1", "wtd_claims", None),
    ("index", "sqlite_autoindex_wtd_claims_2", "wtd_claims", None),
    ("index", "sqlite_autoindex_wtd_claims_3", "wtd_claims", None),
    ("index", "sqlite_autoindex_wtd_deliveries_1", "wtd_deliveries", None),
    ("index", "sqlite_autoindex_wtd_deliveries_2", "wtd_deliveries", None),
    ("index", "sqlite_autoindex_wtd_destinations_1", "wtd_destinations", None),
    ("index", "sqlite_autoindex_wtd_destinations_2", "wtd_destinations", None),
    ("index", "sqlite_autoindex_wtd_results_1", "wtd_results", None),
    ("index", "sqlite_autoindex_wtd_state_1", "wtd_state", None),
    ("index", "sqlite_autoindex_wtd_watch_entries_1", "wtd_watch_entries", None),
    ("index", "sqlite_autoindex_wtd_watch_entries_2", "wtd_watch_entries", None),
    ("index", "wtd_deliveries_by_destination", "wtd_deliveries", STATEMENTS[7]),
    ("index", "wtd_deliveries_by_watch", "wtd_deliveries", STATEMENTS[8]),
    ("index", "wtd_state_by_state", "wtd_state", STATEMENTS[9]),
    ("table", "wtd_claims", "wtd_claims", STATEMENTS[5]),
    ("table", "wtd_deliveries", "wtd_deliveries", STATEMENTS[3]),
    ("table", "wtd_destinations", "wtd_destinations", STATEMENTS[1]),
    ("table", "wtd_metadata", "wtd_metadata", STATEMENTS[0]),
    ("table", "wtd_results", "wtd_results", STATEMENTS[6]),
    ("table", "wtd_state", "wtd_state", STATEMENTS[4]),
    ("table", "wtd_watch_entries", "wtd_watch_entries", STATEMENTS[2]),
    ("trigger", "wtd_claims_insert_guard", "wtd_claims", STATEMENTS[19]),
    ("trigger", "wtd_claims_insert_state", "wtd_claims", STATEMENTS[20]),
    ("trigger", "wtd_claims_no_delete", "wtd_claims", STATEMENTS[32]),
    ("trigger", "wtd_claims_no_update", "wtd_claims", STATEMENTS[25]),
    ("trigger", "wtd_deliveries_insert_guard", "wtd_deliveries", STATEMENTS[15]),
    ("trigger", "wtd_deliveries_insert_state", "wtd_deliveries", STATEMENTS[16]),
    ("trigger", "wtd_deliveries_no_delete", "wtd_deliveries", STATEMENTS[30]),
    ("trigger", "wtd_deliveries_no_update", "wtd_deliveries", STATEMENTS[24]),
    ("trigger", "wtd_destinations_insert_clock", "wtd_destinations", STATEMENTS[13]),
    ("trigger", "wtd_destinations_insert_guard", "wtd_destinations", STATEMENTS[12]),
    ("trigger", "wtd_destinations_no_delete", "wtd_destinations", STATEMENTS[28]),
    ("trigger", "wtd_destinations_update_guard", "wtd_destinations", STATEMENTS[11]),
    ("trigger", "wtd_destinations_validate_clock", "wtd_destinations", STATEMENTS[14]),
    ("trigger", "wtd_metadata_no_delete", "wtd_metadata", STATEMENTS[27]),
    ("trigger", "wtd_metadata_update_guard", "wtd_metadata", STATEMENTS[10]),
    ("trigger", "wtd_results_insert_guard", "wtd_results", STATEMENTS[21]),
    ("trigger", "wtd_results_insert_state", "wtd_results", STATEMENTS[22]),
    ("trigger", "wtd_results_no_delete", "wtd_results", STATEMENTS[33]),
    ("trigger", "wtd_results_no_update", "wtd_results", STATEMENTS[26]),
    ("trigger", "wtd_state_insert_guard", "wtd_state", STATEMENTS[17]),
    ("trigger", "wtd_state_no_delete", "wtd_state", STATEMENTS[31]),
    ("trigger", "wtd_state_update_guard", "wtd_state", STATEMENTS[18]),
    ("trigger", "wtd_watch_entries_no_delete", "wtd_watch_entries", STATEMENTS[29]),
    ("trigger", "wtd_watch_entries_no_update", "wtd_watch_entries", STATEMENTS[23]),
)


def expected_inventory() -> tuple[tuple[str, str, str, str | None], ...]:
    """Return exact inventory including all implicit indexes."""
    return _EXPECTED
