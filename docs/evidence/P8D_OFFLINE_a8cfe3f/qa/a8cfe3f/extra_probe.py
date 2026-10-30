"""Independent final-only fake qualification/scanner checks; no author tests imported."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib
import importlib.util
import io
import json
import os
import socket
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
HEAD = 'a8cfe3f4e9e2bc50558f3a9aee13a1fbd9bf6abd'
TREE = '820ddbdfc278ada9b2d713a1c0b834f5d59e5dbd'
RESULTS = []


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def rejects(action, category):
    try:
        action()
    except Exception as exc:
        actual = getattr(exc, 'category', str(exc))
        require(actual == category, 'expected fixed rejection ' + category + ', got ' + str(actual))
    else:
        raise AssertionError('missing rejection ' + category)


def case(name, action):
    started = time.perf_counter()
    try:
        action()
    except Exception as exc:
        RESULTS.append({'case':name,'status':'FAIL','exception':type(exc).__name__,
                        'detail':str(exc)[:240]})
    else:
        RESULTS.append({'case':name,'status':'PASS'})
    RESULTS[-1]['runtime_seconds'] = round(time.perf_counter()-started,3)


qa = module('independent_committed_qa', ROOT/'scripts/p8d_qa_probe.py')
qualification = module('independent_qualification', ROOT/'scripts/watchlist_telegram_qualification.py')
scanner = module('independent_scanner', ROOT/'scripts/check_secret_scan.py')


class Fake:
    def __init__(self):
        self.entered = []
        self.failure = False
    def check_configuration(self):
        pass
    def validate_destination(self, bot, chat, *, timeout):
        self.entered.append(('destination',timeout))
        if self.failure:
            raise RuntimeError('fake-provider-uncertainty')
    def validate_bot(self, bot, *, timeout):
        self.entered.append(('bot',timeout))
    def send(self, bot, chat, message, *, timeout):
        self.entered.append(('send',timeout))
        return object()


def scanner_exactness():
    accepted = 0
    for path, values in scanner._PUBLIC_DIGESTS.items():
        for value in values:
            expected = {'type':'Hex High Entropy String',
                        'hashed_secret':hashlib.sha1(value.encode('ascii')).hexdigest()}
            require(scanner._reviewed_public_candidate(path, expected), 'exact public digest denied')
            require(scanner._reviewed_public_candidate(path.replace('/','\\'), expected),
                    'Windows path normalization')
            for wrong in ('UNREVIEWED/'+path, './'+path, path+'.backup', path.upper()):
                require(not scanner._reviewed_public_candidate(wrong, expected),
                        'digest exception expanded beyond exact path')
            for kind in ('Base64 High Entropy String','Hex High Entropy String ',None):
                require(not scanner._reviewed_public_candidate(path, dict(expected,type=kind)),
                        'exception expanded to different detector')
            changed = hashlib.sha256(('independent-unreviewed-'+value).encode()).hexdigest()
            require(not scanner._reviewed_public_candidate(path, dict(expected,
                    hashed_secret=hashlib.sha1(changed.encode()).hexdigest())),
                    'unreviewed value passed scanner exception')
            accepted += 1
    require(accepted > 50, 'nontrivial exact path/type/value scanner matrix')
    # Independently derive both public P8d format vectors, then test only their exact paths.
    derived = set()
    for digit in ('0','f'):
        raw = b'CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\x00'+qa.canonical({
            'identity_version':1,'provider':'telegram','signal_id':'wsig1_'+digit*64}).encode('ascii')
        derived.add(hashlib.sha256(raw).hexdigest())
    for path in ('scripts/p8d_qa_probe.py','scripts/p8d_reviewer_probe.py',
                 'tests/test_watchlist_delivery_policy.py'):
        require(scanner._PUBLIC_DIGESTS[path] == derived, 'P8d exception equality to independent vectors')


def authorize_exact(directory):
    dossier = {'candidate_head':HEAD,'candidate_tree':TREE,
               'selection':{'delivery_id':'wtdl1_'+'7'*64,'revision':1}}
    value = {'version':1,'decision':qualification.DECISION,
             'authorization_reference':'FAKE_ONLY_QA/reference-1',
             'qualification_sha256':qualification._digest(dossier),
             'candidate_head':HEAD,'candidate_tree':TREE,'selection':dossier['selection'],
             'acknowledgement':qualification.ACK}
    valid = directory/'authorization-exact.json'
    qualification._exclusive(valid,value)
    qualification._authorize(dossier,valid)
    variants = [dict(value,decision='PENDING_NOT_AUTHORIZED'), dict(value,version=True),
                dict(value,candidate_head='f'*40),dict(value,candidate_tree='e'*40),
                dict(value,qualification_sha256='f'*64),dict(value,acknowledgement='yes'),
                dict(value,selection=dict(dossier['selection'],revision=2)),
                dict(value,authorization_reference='private raw sentinel with spaces'),
                dict(value,unexpected=True)]
    for index, changed in enumerate(variants):
        path = directory/f'authorization-negative-{index}.json'
        qualification._exclusive(path,changed)
        rejects(lambda path=path: qualification._authorize(dossier,path),
                'specific_operator_authorization_required')


def accounted_limits(directory):
    target = directory/'accounted-limits'
    target.mkdir()
    fake = Fake()
    budget = qualification.Budget(5)
    first = qualification.AccountedTransport(fake,target,'validate',[],budget)
    for _ in range(3):
        first.validate_destination(qa.BOT,qa.CHAT,timeout=10)
    second = qualification.AccountedTransport(fake,target,'send',[],budget)
    second.validate_bot(qa.BOT,timeout=10)
    second.validate_bot(qa.BOT,timeout=10)
    before = len(fake.entered)
    rejects(lambda: second.validate_bot(qa.BOT,timeout=10),'qualification_budget_exhausted')
    require(len(fake.entered)==before,'ninth metadata request dispatched')
    second.send(qa.BOT,qa.CHAT,'fake-content',timeout=10)
    third = qualification.AccountedTransport(fake,target,'send',[],qualification.Budget(5))
    rejects(lambda: third.send(qa.BOT,qa.CHAT,'fake-content',timeout=10),
            'qualification_budget_exhausted')
    counts = qualification._counters(qualification._events(target))
    require(counts['metadata_request_upper_bound']==8 and counts['send_attempt_upper_bound']==1,
            'cumulative durable8/1 cap')
    require(sum(kind=='send' for kind,_ in fake.entered)==1,'at most one fake native send')
    require(all(0<timeout<=5 for _,timeout in fake.entered),'client receives residual allowance')
    # Counter reserves remain durable even if native method fails and never completes.
    failed = directory/'accounted-failure'
    failed.mkdir()
    fake = Fake()
    fake.failure = True
    wrapped = qualification.AccountedTransport(fake,failed,'validate',[],qualification.Budget(5))
    try:
        wrapped.validate_destination(qa.BOT,qa.CHAT,timeout=10)
    except RuntimeError:
        pass
    else:
        raise AssertionError('fake native failure was swallowed')
    counts = qualification._counters(qualification._events(failed))
    require(counts['metadata_request_upper_bound']==2 and
            counts['successful_metadata_expected_requests']==0,'uncertain native method never refunds cap')


def reserve_expiry(directory):
    target = directory/'expiry'
    target.mkdir()
    fake = Fake()
    clock = [100.0]
    budget_module = importlib.import_module('card_market_tracker.watchlist_delivery.budget')
    with patch.object(budget_module.time,'monotonic',lambda:clock[0]):
        budget = qualification.Budget(1)
        wrapped = qualification.AccountedTransport(fake,target,'send',[],budget)
        original = wrapped._record
        def delayed_record(kind,payload):
            original(kind,payload)
            if kind=='method-reserved':
                clock[0]=100.81
        with patch.object(wrapped,'_record',delayed_record):
            rejects(lambda:wrapped.send(qa.BOT,qa.CHAT,'fake-content',timeout=.8),'deadline_exceeded')
    require(fake.entered==[],'expiry during durable reservation must prevent native dispatch')
    counts = qualification._counters(qualification._events(target))
    require(counts['send_attempt_upper_bound']==1 and counts['send_method_completions']==0,
            'expired reservation remains consumed across invocations')
    later = qualification.AccountedTransport(fake,target,'send',[],qualification.Budget(5))
    rejects(lambda:later.send(qa.BOT,qa.CHAT,'fake-content',timeout=1),'qualification_budget_exhausted')


def failure_markers_and_parser(directory):
    target = directory/'marker'
    target.mkdir()
    try:
        with qualification._locked(target):
            raise RuntimeError('intentional-local-crash')
    except RuntimeError:
        pass
    require((target/'active.json').is_file(),'ambiguous failed invocation lost durable active marker')
    try:
        with qualification._locked(target):
            raise AssertionError('reentered crash marker')
    except FileExistsError:
        pass
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = qualification.main(['--operation','validate','--directory',str(directory),
                                   '--private-raw-sentinel'])
    payload = json.loads(output.getvalue())
    require(code==1 and payload['error_category']=='invalid_arguments' and
            payload['live_status']=='LIVE_UNVERIFIED','fixed wrapper parser failure')
    require('private-raw-sentinel' not in output.getvalue() and str(directory) not in output.getvalue(),
            'wrapper parser leaked arguments/path')
    rejects(qualification._ensure_installed,'installed_wheel_required')


def genuine_fake_wrapper(directory):
    app = qualification.app
    manifest = json.loads((ROOT/'tests/fixtures/synthetic_manifest.json').read_text('utf-8'))
    src = qa.originals(directory/'wrapper-originals',manifest)
    ledger = directory/'wrapper-ledger.sqlite'
    qa.new_ledger(app,ledger)
    did = qa.prepare(app,ledger,src)['delivery']['delivery_id']
    manifest_path = directory/'wrapper-manifest.json'
    manifest_path.write_text(qa.canonical(manifest),encoding='ascii')
    evidence = directory/'wrapper-evidence'
    originals_before = src.fingerprints()
    # Sole fake-only substitution: editable checkout simulates installed-wheel
    # prerequisite. Actual _ensure_installed rejection is separately tested above.
    with patch.object(qualification,'_ensure_installed',lambda:None):
        dossier_response = qualification.preflight(evidence,ROOT,HEAD,TREE,ledger,
            src.watch,src.journal,src.outbox,manifest_path,did,timeout=5)
        dossier = qualification._read(evidence/'dossier.json')
        template = qualification._read(evidence/'authorization-template.json')
        require(template['decision']=='PENDING_NOT_AUTHORIZED','offline preflight created live authority')
        authorization = directory/'wrapper-fake-authorization.json'
        qualification._exclusive(authorization,{**template,'decision':qualification.DECISION,
            'authorization_reference':'FAKE_ONLY_QA_exact_selection'})
        native = importlib.import_module('card_market_tracker.telegram_delivery.transport')
        az = importlib.import_module('card_market_tracker.watchlist_alerts.storage')
        text = az.get(src.outbox,src.alerts[0],timeout=5)['alert']['message_text']
        fake = qa.FakePort(ledger,native.TransportResult('confirmed',
            receipt=native.Receipt(9011,1,qa.BOT,qa.CHAT)),text)
        with patch.object(app,'_transport_factory',lambda:fake):
            validated = qualification.remote(evidence,authorization,'validate',timeout=15)
            sent = qualification.remote(evidence,authorization,'send',timeout=15)
            rejects(lambda:qualification.remote(evidence,authorization,'send',timeout=15),
                    'qualification_budget_exhausted')
        require(fake.sends==1 and sent['durable_receipt_verified'] is True,'wrapper onefake send durable receipt')
        require(sent['request_counters']['metadata_request_upper_bound']==3 and
                sent['request_counters']['send_attempt_upper_bound']==1,'wrapper metadata/send accounting')
        require(all(row['live_status']=='LIVE_UNVERIFIED' for row in (dossier_response,validated,sent)),
                'fake qualification promoted live acceptance')
        # Repeated-send refusal deliberately retains active marker. Use a fresh
        # copied test evidence directory for read-only postflight/replay proof,
        # never clear a crashed operational marker or grant another send.
        proof = directory/'wrapper-proof'
        proof.mkdir()
        for path in evidence.glob('*.json'):
            if path.name!='active.json':
                (proof/path.name).write_bytes(path.read_bytes())
        after = qualification.postflight(proof,timeout=5)
        require(after['originals_unchanged'] is True,'separate offline postflight source proof')
        # Copy does not authorize a send: it retains cumulative send reservation.
        rejects(lambda:qualification.remote(proof,authorization,'send',timeout=15),
                'qualification_budget_exhausted')
        require(src.fingerprints()==originals_before,'qualification never wrote original DBs')
        require((evidence/'active.json').exists(),'failed repeatedsend did not retain conservative marker')
        require(qualification._digest(dossier)==dossier_response['qualification_sha256'],
                'public dossier commitment')


def blocked(*args,**kwargs):
    raise AssertionError('extra QA network tripwire')


def audit(event,args):
    if event.startswith('socket.'):
        raise AssertionError('extra QA socket audit tripwire')


sys.addaudithook(audit)
with qa.token_guard(),patch.object(socket.socket,'connect',blocked), \
        patch.object(socket,'getaddrinfo',blocked),patch.object(socket,'create_connection',blocked), \
        tempfile.TemporaryDirectory(prefix='extra-fixtures-',dir=Path(__file__).parent) as temporary:
    directory=Path(temporary)
    case('scanner_exact_path_detector_hash_all_reviewed_values_independent_P8d_vectors',scanner_exactness)
    case('qualification_exact_specific_authorization_closed_bindings',lambda:authorize_exact(directory))
    case('qualification_persisted_cumulative8metadata_1send_native_failure_no_refund',lambda:accounted_limits(directory))
    case('qualification_reserve_persistence_expiry_blocks_native_dispatch_durable_cap',lambda:reserve_expiry(directory))
    case('qualification_crash_marker_parser_redaction_installed_prerequisite',lambda:failure_markers_and_parser(directory))
    case('genuine_originals_fake_qualification_preflight_validate_send_receipt_postflight',lambda:genuine_fake_wrapper(directory))
result={'candidate':HEAD,'tree':TREE,'results':RESULTS,'live':'NOT_AUTHORIZED_NOT_RUN',
        'installed_precondition_simulated_for_one_fake_wrapper_case':True}
print(qa.canonical(result))
raise SystemExit(any(item['status']=='FAIL' for item in RESULTS))
