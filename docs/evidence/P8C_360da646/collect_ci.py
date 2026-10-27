"""Collect complete GitHub CI logs and metadata without changing the candidate.
Run: python collect_ci.py --output DIRECTORY
Requires ordinary authenticated gh; creates evidence files only after run completion.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,re
from pathlib import Path
REPO="KastaTM/card-market-tracker"
CANDIDATE="360da646892e46545ca70e8838bc3a2a89e460a3"
TREE="3ce94d6e214de74889475753807122b526085b98"
RUN=40586563511

def gh(*args):
    return subprocess.check_output(["gh",*args])
def api(path):
    return json.loads(gh("api",f"repos/{REPO}/{path}"))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    run=api(f"actions/runs/{RUN}")
    assert run["head_sha"]==CANDIDATE and run["event"]=="pull_request"
    if run["status"]!="completed":
        print(json.dumps({"status":"pending","run":RUN,"head":CANDIDATE}))
        return 0
    jobs=api(f"actions/runs/{RUN}/jobs")["jobs"]
    labels={"quality":"quality","compose":"compose",
        "container (linux/amd64)":"container-amd64",
        "container (linux/arm64)":"container-arm64"}
    assert {j["name"] for j in jobs}==set(labels)
    checkout_sha="c08800bc7a255255a287ddce884ebe7ee749722f"
    checkout=api("git/commits/"+checkout_sha)
    assert checkout["tree"]["sha"]==TREE
    assert [p["sha"] for p in checkout["parents"]]==[
        "228d5c8d0d91edf03ddb86a489c8232eeb7c08bc",CANDIDATE]
    args.output.mkdir(parents=True,exist_ok=True)
    files={}
    def save(name,data):
        target=args.output/name
        if target.exists():
            assert target.read_bytes()==data, ("refusing changed overwrite",name)
        else:
            target.write_bytes(data)
        files[name]={"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
    for job in jobs:
        assert job["status"]=="completed"
        # API permits complete per-job export. Capture, never forward raw controls.
        raw=gh("api","--allow-escape-sequences",
               f"repos/{REPO}/actions/jobs/{job['id']}/logs")
        assert raw, ("empty job log",job["name"])
        text=raw.decode("utf-8")
        text,ansi_count=re.subn(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-_])","",text)
        text=re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
                    lambda match: "\\x"+format(ord(match.group()),"02x"),text)
        assert checkout_sha in text, ("unverified actual checkout",job["name"])
        name="ci-"+labels[job["name"]]+".log"
        save(name,text.encode("utf-8"))
        files[name].update({"raw_sha256":hashlib.sha256(raw).hexdigest(),
                           "removed_terminal_escape_sequences":ansi_count})
        mode="installed" if job["name"]=="quality" else "compose" if job["name"]=="compose" else "docker"
        patterns={
            "catalog":rf"catalog {mode} [^\r\n]+: PASS",
            "persistence":rf"persistence {mode}: PASS",
            "discovery":rf"discovery {mode}: PASS",
            "pinned":rf"pinned {mode} smoke PASS",
            "scoped":rf"scoped {mode} smoke PASS",
            "multi_revision":rf"multi-revision {mode} smoke PASS",
            "discovery_journal":rf"discovery journal {mode} smoke PASS",
            "alert_outbox":rf"alert outbox {mode} smoke PASS",
            "telegram_fake":rf"telegram delivery {mode} smoke PASS",
            "watchlist":r"watchlist smoke PASS;",
            "watchlist_journal":r"watchlist journal smoke PASS;",
            "watchlist_alert_outbox":r"watchlist alert outbox smoke PASS;",
        }
        job["harness_markers"]={key:bool(re.search(pattern,text))
                                for key,pattern in patterns.items()}
        if job["conclusion"]=="success":
            assert all(job["harness_markers"].values()), ("harness marker absent",job["harness_markers"])
    details={"candidate_head":CANDIDATE,"candidate_tree":TREE,
        "run":run,"jobs":jobs,"actual_pr_checkout":checkout,
        "checkout_tree_equals_candidate":True,
        "logs_are_complete_api_job_output_ansi_sanitized":True,
        "github_masks_credentials_before_log_export":True}
    save("ci-metadata.json",(json.dumps(details,indent=2,sort_keys=True)+"\n").encode())
    save("ci-log-manifest.json",(json.dumps(files,indent=2,sort_keys=True)+"\n").encode())
    print(json.dumps({"head":CANDIDATE,"tree":TREE,"run":RUN,
        "conclusion":run["conclusion"],
        "jobs":{j["name"]:j["conclusion"] for j in jobs},"files":files}))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
