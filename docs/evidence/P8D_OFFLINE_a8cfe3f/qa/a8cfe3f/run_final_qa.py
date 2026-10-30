"""Exact final QA orchestration; mutations limited to this ignored report directory."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,sqlite3
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
HEAD='a8cfe3f4e9e2bc50558f3a9aee13a1fbd9bf6abd'
TREE='820ddbdfc278ada9b2d713a1c0b834f5d59e5dbd'
def git(*args):
    result=subprocess.run(['git','-C',str(ROOT),*args],capture_output=True,check=True)
    return result.stdout.decode('utf-8').strip()
def hashes():
    listed=subprocess.run(['git','-C',str(ROOT),'ls-files','-z'],capture_output=True,check=True).stdout.decode('utf-8').split('\0')
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in listed if name}
def snapshot():
    return {'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),
            'status':git('status','--porcelain=v1','--untracked-files=all'),'tracked_hashes':hashes()}
def save(name,value):
    (OUT/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')
before=snapshot()
save('before.json',before)
assert (before['head'],before['tree'],before['status'])==(HEAD,TREE,'')
checks={
'frozen_design_paths':git('diff','--name-only','50fcb55a0b0e467bcb9d94561412a0f3c6ebc8f9','HEAD','--','docs/adr/0015-manual-watchlist-telegram-delivery.md','docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_V1.md','docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md'),
'prior_module_paths':git('diff','--name-only','9dda9fba0aa9646a67596657d4ae9a7088903808','HEAD','--','src/card_market_tracker/watchlist','src/card_market_tracker/watchlist_journal','src/card_market_tracker/watchlist_alerts','src/card_market_tracker/telegram_delivery')}
save('preservation.json',checks)
assert not any(checks.values())
executions=[]
for label,args in [('committed',['scripts/p8d_qa_probe.py','--mode','all']),('extra',['.p8d-evidence/final/qa/a8cfe3f/extra_probe.py'])]:
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-B',*args]
    started=time.perf_counter()
    run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=180,check=False)
    duration=time.perf_counter()-started
    (OUT/(label+'.stdout.json')).write_text(run.stdout,encoding='utf-8')
    (OUT/(label+'.stderr.txt')).write_text(run.stderr,encoding='utf-8')
    entry={'label':label,'command':command,'exit_code':run.returncode,'runtime_seconds':round(duration,3)}
    try:
        parsed=json.loads(run.stdout)
        entry['groups']=len(parsed['results'])
        entry['pass_groups']=sum(row['status']=='PASS' for row in parsed['results'])
        entry['all_groups_pass']=all(row['status']=='PASS' for row in parsed['results'])
    except Exception:
        entry['all_groups_pass']=False
    executions.append(entry)
    save('executions.json',executions)
    print(json.dumps(entry,sort_keys=True),flush=True)
after=snapshot()
save('after.json',after)
summary={'candidate':HEAD,'tree':TREE,'before_after_identical':before==after,
         'clean_before':before['status']=='','clean_after':after['status']=='',
         'tracked_file_count':len(before['tracked_hashes']),'tracked_hashes_unchanged':before['tracked_hashes']==after['tracked_hashes'],
         'python':sys.version,'sqlite':sqlite3.sqlite_version,'executions':executions,
         'extra_probe_sha256':hashlib.sha256((OUT/'extra_probe.py').read_bytes()).hexdigest(),
         'live':'NOT_AUTHORIZED_NOT_RUN'}
save('summary.json',summary)
print(json.dumps(summary,sort_keys=True))
assert before==after
assert all(item['exit_code']==0 and item['all_groups_pass'] for item in executions)
