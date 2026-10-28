"""Re-export full CI logs and verify integration gates; uses authenticated gh GET only.
Run: python collect_integration_ci.py --state integration-state.json --output OUTPUT
"""
from pathlib import Path
import argparse,subprocess,json,hashlib,re
def main():
 p=argparse.ArgumentParser();p.add_argument("--state",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 s=json.loads(a.state.read_text());repo=s["repo"];rid=s["run_id"];merge=s["merge"]
 def gh(*args):
  p=subprocess.run(["gh",*args],capture_output=True)
  if p.returncode:raise RuntimeError((args,p.returncode,p.stderr.decode()))
  return p.stdout
 def api(path):return json.loads(gh("api",("repos/"+repo+"/"+path).rstrip("/")))
 def save(name,data):
  target=a.output/name
  if target.exists():assert target.read_bytes()==data,("refusing changed overwrite",name)
  else:target.write_bytes(data)
 a.output.mkdir(parents=True,exist_ok=True)
 run=api(f"actions/runs/{rid}");jobs=api(f"actions/runs/{rid}/jobs?per_page=100")["jobs"]
 assert run["head_sha"]==merge and run["event"]=="push" and run["head_branch"]=="main" and run["run_attempt"]==1
 labels={"quality":"quality","compose":"compose","container (linux/amd64)":"container-amd64","container (linux/arm64)":"container-arm64"}
 assert {j["name"] for j in jobs}==set(labels)
 checkout=api("git/commits/"+merge)
 assert checkout["tree"]["sha"]==s["tree"]
 assert [x["sha"] for x in checkout["parents"]]==[s["base"],s["head"]]
 manifest={};summaries=[]
 for job in jobs:
  if job["status"]!="completed":continue
  raw=gh("api","--allow-escape-sequences",f"repos/{repo}/actions/jobs/{job['id']}/logs")
  assert raw,("empty job log",job["name"])
  text=raw.decode("utf-8")
  text,ansi_count=re.subn(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-_])","",text)
  text=re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",lambda m:"\\x"+format(ord(m.group()),"02x"),text)
  assert merge in text,("actual checkout SHA absent",job["name"])
  name="ci-"+labels[job["name"]]
  raw_name=name+".raw.log";name+=".log";sanitized=text.encode("utf-8")
  save(raw_name,raw);save(name,sanitized)
  for filename,data in ((raw_name,raw),(name,sanitized)):
   manifest[filename]={"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"job_id":job["id"],"job":job["name"]}
  manifest[name].update({"raw_sha256":hashlib.sha256(raw).hexdigest(),"removed_terminal_escape_sequences":ansi_count,"no_lines_removed":True})
  mode="installed" if job["name"]=="quality" else "compose" if job["name"]=="compose" else "docker"
  patterns={"catalog":rf"catalog {mode} [^\r\n]+: PASS","persistence":rf"persistence {mode}: PASS","discovery":rf"discovery {mode}: PASS","pinned":rf"pinned {mode} smoke PASS","scoped":rf"scoped {mode} smoke PASS","multi_revision":rf"multi-revision {mode} smoke PASS","discovery_journal":rf"discovery journal {mode} smoke PASS","alert_outbox":rf"alert outbox {mode} smoke PASS","telegram_fake":rf"telegram delivery {mode} smoke PASS","watchlist":r"watchlist smoke PASS;","watchlist_journal":r"watchlist journal smoke PASS;","watchlist_alert_outbox":r"watchlist alert outbox smoke PASS;"}
  job["harness_markers"]={key:bool(re.search(pattern,text)) for key,pattern in patterns.items()}
  job["rw01_rejection_marker"]=bool(re.search(r"watchlist alert outbox smoke PASS;[^\r\n]*RW-01 incompatible originals rejected without mutation",text))
  if job["conclusion"]=="success":
   assert all(job["harness_markers"].values()),("missing harness",job["name"],job["harness_markers"])
   assert job["rw01_rejection_marker"],("missing RW01 marker",job["name"])
  summaries.append({"job":job["name"],"conclusion":job["conclusion"],"markers":sum(job["harness_markers"].values()),"RW01":job["rw01_rejection_marker"]})
 completed=run["status"]=="completed" and all(j["status"]=="completed" for j in jobs)
 status={"run":rid,"merge":merge,"run_status":run["status"],"run_conclusion":run["conclusion"],"jobs":summaries,"all_completed":completed}
 if completed:
  details={"accepted_candidate_head":s["head"],"integration_merge":merge,"source_tree":s["tree"],"run":run,"jobs":jobs,"actual_main_checkout":checkout,"all_source_trees_equal":True,"raw_logs_preserved":True,"readable_logs_preserve_every_line":True}
  save("ci-metadata.json",(json.dumps(details,indent=2,sort_keys=True)+"\n").encode())
  save("ci-log-manifest.json",(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode())
  status["result"]="PASS" if run["conclusion"]=="success" and all(j["conclusion"]=="success" for j in jobs) else "FAIL"
 print(json.dumps(status))
 if completed and status["result"]!="PASS":raise SystemExit(2)
if __name__=="__main__":main()
