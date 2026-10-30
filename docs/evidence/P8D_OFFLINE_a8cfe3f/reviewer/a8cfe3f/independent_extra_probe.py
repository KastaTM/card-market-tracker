"""Independent final reviewer extras: qualification and scanner, fake-only."""
from pathlib import Path
import contextlib,hashlib,importlib.util,json,subprocess,sys,tempfile
from unittest.mock import patch
ROOT=Path.cwd();REPORT=ROOT/'.p8d-evidence/final/reviewer/a8cfe3f';CHECKS=[]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load('own_reviewer',ROOT/'scripts/p8d_reviewer_probe.py')
q=load('qualification',ROOT/'scripts/watchlist_telegram_qualification.py')
scan=load('scanner',ROOT/'scripts/check_secret_scan.py')
def check(name,fn):
 try: fn()
 except Exception as e: CHECKS.append({'probe':name,'result':'FAIL','type':type(e).__name__,'category':getattr(e,'category',None)})
 else: CHECKS.append({'probe':name,'result':'PASS'})
def rejects(fn):
 try: fn()
 except (q.QualificationError,FileExistsError): return
 raise AssertionError('expected fixed rejection')
def full_fake(directory):
 source=r.origin(directory/'source');ledger=r.ledger(directory);did=r.prepare(ledger,source)['delivery']['delivery_id'];manifest=directory/'PRIVATE_PATH_MARKER.json';manifest.write_text(json.dumps(r.MANIFEST))
 repo_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip()
 evidence=directory/'qualification';fake=r.Fake()
 with patch.object(q,'_ensure_installed',return_value=None):
  preflight=q.preflight(evidence,ROOT,repo_head,tree,ledger,*source[:3],manifest,did,timeout=5)
  dossier=q._read(evidence/'dossier.json')
  auth={**q._read(evidence/'authorization-template.json'),'decision':q.DECISION,'authorization_reference':'FAKE_ONLY_REVIEWER_AUTHORIZATION'}
  authorization=directory/'authorization.json';authorization.write_text(json.dumps(auth))
  q._authorize(dossier,authorization)
  wrong={**auth,'selection':{**auth['selection'],'revision':True}};other=directory/'wrong.json';other.write_text(json.dumps(wrong));rejects(lambda:q._authorize(dossier,other))
  with patch.object(q.app,'_transport_factory',return_value=fake):
   validated=q.remote(evidence,authorization,'validate')
   sent=q.remote(evidence,authorization,'send')
   assert sent['durable_receipt_verified'] and sent['live_status']=='LIVE_UNVERIFIED'
   assert sent['request_counters']['metadata_request_upper_bound']==3 and sent['request_counters']['send_attempt_upper_bound']==1
   replay=q.replay(evidence,timeout=5);assert replay['request_counters']==sent['request_counters']
   postflight=q.postflight(evidence,timeout=5);assert postflight['originals_unchanged']
   assert fake.calls.count('send')==1
   rejects(lambda:q.remote(evidence,authorization,'send'))
   assert fake.calls.count('send')==1
 for response in (preflight,validated,sent,replay,postflight):
  encoded=json.dumps(response)
  assert all(s not in encoded for s in ('PRIVATE_PATH_MARKER','reviewer_private','bot_id','chat_id','message_text'))
 assert (evidence/'active.json').exists()
def reserve_expiry(directory):
 events=directory/'expired';events.mkdir();fake=r.Fake();clock=[100.0]
 with patch('card_market_tracker.watchlist_delivery.budget.time.monotonic',side_effect=lambda:clock[0]):
  budget=r.Budget(15,30);transport=q.AccountedTransport(fake,events,'send',[],budget);append=q._append
  def expire(*args): append(*args);clock[0]=115.0
  with patch.object(q,'_append',side_effect=expire):
   try: transport.send(11,22,'synthetic reviewer text',timeout=14)
   except r.DeliveryError as error: assert error.category=='deadline_exceeded'
   else: raise AssertionError('expired dispatch')
  assert fake.calls==[]
  assert q._counters(q._events(events))['send_attempt_upper_bound']==1
  fresh=q.AccountedTransport(fake,events,'send',[],r.Budget(15,30));rejects(lambda:fresh.send(11,22,'synthetic reviewer text',timeout=14));assert fake.calls==[]
def metadata_cap(directory):
 events=directory/'metadata';events.mkdir();fake=r.Fake()
 transport=q.AccountedTransport(fake,events,'validate',[],r.Budget(15,30))
 for _ in range(4):transport.validate_destination(11,22,timeout=14)
 assert q._counters(q._events(events))['metadata_request_upper_bound']==8
 second=q.AccountedTransport(fake,events,'validate',[],r.Budget(15,30));rejects(lambda:second.validate_bot(11,timeout=14));assert fake.calls.count('destination')==4 and 'bot' not in fake.calls
 rejects(lambda:second.send(11,22,'synthetic reviewer text',timeout=14))
def crash_marker(directory):
 events=directory/'crash';events.mkdir()
 try:
  with q._locked(events):raise RuntimeError('fake crash')
 except RuntimeError:pass
 assert (events/'active.json').exists()
 rejects(lambda:q._locked(events).__enter__())
def scanner_oracle():
 for path,values in scan._PUBLIC_DIGESTS.items():
  for value in values:
   candidate={'type':'Hex High Entropy String','hashed_secret':hashlib.sha1(value.encode()).hexdigest()}
   assert scan._reviewed_public_candidate(path,candidate)
   assert not scan._reviewed_public_candidate('unreviewed/'+path,candidate)
   assert not scan._reviewed_public_candidate(path,{**candidate,'type':'Secret Keyword'})
   assert not scan._reviewed_public_candidate(path,{**candidate,'hashed_secret':hashlib.sha1((value+'0').encode()).hexdigest()})
 assert hashlib.sha256(b'CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\0'+b'{"identity_version":1,"provider":"telegram","signal_id":"wsig1_'+b'0'*64+b'"}').hexdigest()==scan._P8D_ORACLE_A
 assert hashlib.sha256((ROOT/'docs/phases/P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md').read_bytes()).hexdigest()==scan._P8D_CONTRACT
with tempfile.TemporaryDirectory(dir=REPORT,prefix='extra-') as t:
 d=Path(t)
 check('qualification_full_genuine_fake_validate_send_replay_postflight_privacy',lambda:full_fake(d))
 check('durable_send_reservation_before_dispatch_expiry_blocks_method',lambda:reserve_expiry(d))
 check('metadata8_send1_limits_persist_across_wrapper_instances',lambda:metadata_cap(d))
 check('crashed_active_marker_blocks_next_operation',lambda:crash_marker(d))
 check('scanner_path_type_value_exactness_and_literal_content_oracles',scanner_oracle)
print(json.dumps({'head':'a8cfe3f4e9e2bc50558f3a9aee13a1fbd9bf6abd','tree':'820ddbdfc278ada9b2d713a1c0b834f5d59e5dbd','scope':'fake-only independent qualification/scanner checks; installed precondition explicitly bypassed for fake harness','checks':CHECKS},sort_keys=True))
raise SystemExit(int(any(row['result']!='PASS' for row in CHECKS)))
