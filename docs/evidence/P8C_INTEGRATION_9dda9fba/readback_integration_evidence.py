"""Bytewise public integration-evidence readback (GitHub GET only).
python readback_integration_evidence.py --commit SHA --prefix docs/evidence/P8C_INTEGRATION_9dda9fba --output downloaded --reference local-public --receipt receipt.json
"""
from pathlib import Path,PurePosixPath
from datetime import UTC,datetime
from concurrent.futures import ThreadPoolExecutor
import argparse,subprocess,json,hashlib,base64,re
def main():
 p=argparse.ArgumentParser();p.add_argument("--repo",default="KastaTM/card-market-tracker");p.add_argument("--commit",required=True);p.add_argument("--prefix",required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--reference",type=Path);p.add_argument("--receipt",type=Path,required=True);a=p.parse_args()
 assert re.fullmatch("[0-9a-f]{40}",a.commit)
 assert not PurePosixPath(a.prefix).is_absolute() and ".." not in PurePosixPath(a.prefix).parts
 def api(path):
  q=subprocess.run(["gh","api",("repos/"+a.repo+"/"+path).rstrip("/")],capture_output=True)
  assert q.returncode==0,(path,q.returncode,q.stderr.decode())
  return json.loads(q.stdout)
 commit=api("git/commits/"+a.commit)
 tree=api("git/trees/"+commit["tree"]["sha"]+"?recursive=1")
 assert not tree["truncated"]
 prefix=a.prefix.rstrip("/")+"/"
 blobs={x["path"][len(prefix):]:x for x in tree["tree"] if x["type"]=="blob" and x["path"].startswith(prefix)}
 assert "evidence-manifest.json" in blobs
 for name in blobs:
  assert not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts and "\\" not in name
 def fetch(name):
  metadata=blobs[name];obj=api("git/blobs/"+metadata["sha"]);assert obj["encoding"]=="base64"
  data=base64.b64decode(obj["content"],validate=False)
  blob_hash=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
  assert blob_hash==metadata["sha"]==obj["sha"]
  if a.reference:assert data==(a.reference/name).read_bytes(),("local byte mismatch",name)
  target=a.output/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  return name,data,{"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"git_blob_sha1":blob_hash,"bytewise_equal_reference":bool(a.reference)}
 a.output.mkdir(parents=True,exist_ok=True)
 _,manifest_data,manifest_info=fetch("evidence-manifest.json");manifest=json.loads(manifest_data)
 assert set(blobs)==set(manifest["files"])|{"evidence-manifest.json"}
 records={"evidence-manifest.json":manifest_info}
 with ThreadPoolExecutor(max_workers=4) as pool:
  for name,data,info in pool.map(fetch,sorted(manifest["files"])):
   expected=manifest["files"][name]
   assert len(data)==expected["bytes"] and info["sha256"]==expected["sha256"],("manifest mismatch",name)
   records[name]=info
 state=json.loads((a.output/"integration-state.json").read_text())
 assert state["merge"]==manifest["merge"] and state["tree"]==manifest["source_tree"]
 baseline=api("git/trees/"+state["tree"]+"?recursive=1");assert not baseline["truncated"]
 def outside(entries):return {x["path"]:(x["type"],x["mode"],x["sha"]) for x in entries if x["type"]!="tree" and not x["path"].startswith(prefix)}
 assert outside(tree["tree"])==outside(baseline["tree"]), "Evidence commit changes source outside its evidence prefix"
 proof={"utc":datetime.now(UTC).isoformat(),"result":"PASS","repository":a.repo,"evidence_commit":a.commit,"evidence_tree":commit["tree"]["sha"],"prefix":a.prefix,"merge":state["merge"],"accepted_source_tree":state["tree"],"source_outside_evidence_unchanged":True,"manifest_sha256":manifest_info["sha256"],"artifacts_verified":len(records),"all_manifest_hashes_match":True,"all_downloaded_bytes_equal_local_reference":bool(a.reference),"files":records}
 a.receipt.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
 print(json.dumps({k:v for k,v in proof.items() if k!="files"}))
if __name__=="__main__":main()
