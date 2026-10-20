#!/usr/bin/env python3
from __future__ import annotations
import argparse, fnmatch, json, os, subprocess
from pathlib import Path
from typing import Any
import yaml
ROOT=Path(__file__).resolve().parents[1]; DEFAULT=ROOT/"config/documentation-sync.yaml"; ZERO="0"*40
def pats(v:Any)->list[str]: return [str(x).strip() for x in v or [] if str(x).strip()] if isinstance(v,list) else []
def anymatch(paths,patterns): return any(any(fnmatch.fnmatchcase(p,q) for q in patterns) for p in paths)
def validate_config(doc):
 e=[]
 if doc.get("version")!=1:e.append("version must be 1")
 t=doc.get("technology_guide") or {}
 if t.get("enabled") is not True:e.append("technology_guide.enabled must be true")
 if not t.get("path") or not pats(t.get("triggers")):e.append("technology_guide path/triggers required")
 ids=set()
 for r in doc.get("rules") or []:
  i=str(r.get("id") or "").strip()
  if not i:e.append("rule id required"); continue
  if i in ids:e.append(f"duplicate rule id: {i}")
  ids.add(i)
  if not pats(r.get("triggers")):e.append(f"rule {i} requires triggers")
  if not pats(r.get("human_docs")):e.append(f"rule {i} requires human_docs")
  if not pats(r.get("agent_docs")):e.append(f"rule {i} requires agent_docs")
 return e
def evaluate_changes(files,config):
 e=validate_config(config)
 if e:return e
 # removeprefix, not lstrip: lstrip drops the leading "." of .github/** and disables those triggers.
 changed=sorted({str(x).strip().removeprefix("./") for x in files if str(x).strip()}); s=set(changed); t=config["technology_guide"]
 if anymatch(changed,pats(t.get("triggers"))) and t["path"] not in s:e.append(f"Technology Guide review required: {t['path']} was not updated")
 for r in config.get("rules") or []:
  if not anymatch(changed,pats(r.get("triggers"))):continue
  mh=[x for x in pats(r.get("human_docs")) if x not in s]; ma=[x for x in pats(r.get("agent_docs")) if x not in s]
  if mh:e.append(f"Documentation sync rule {r['id']} requires Human docs: "+", ".join(mh))
  if ma:e.append(f"Documentation sync rule {r['id']} requires Agent docs: "+", ".join(ma))
 return e
def changed_files_from_git(base,head="HEAD",root=ROOT):
 if not base or base==ZERO:return []
 r=subprocess.run(["git","diff","--name-only",f"{base}...{head}"],cwd=root,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr.strip() or "git diff failed")
 return [x.strip() for x in r.stdout.splitlines() if x.strip()]
def evaluate_candidate(base,head,config,root=ROOT):
 """Single diff-based sync entry point; verified pure dependency updates are exempt (Scenario 221)."""
 files=changed_files_from_git(base,head,root)
 if files:
  import sys
  if str(root/"scripts") not in sys.path:sys.path.insert(0,str(root/"scripts"))
  from dependency_impact import pure_dependency_update
  scope=pure_dependency_update(base,head,root)
  if scope["status"]=="PURE_DEPENDENCY_UPDATE" and sorted(set(files))==scope["files"]:return [],scope
 return evaluate_changes(files,config),None
def main():
 p=argparse.ArgumentParser(); p.add_argument("--config",default=str(DEFAULT)); p.add_argument("--base-ref",default=os.environ.get("AIPS_DOCS_DIFF_BASE","")); p.add_argument("--head-ref",default="HEAD"); p.add_argument("--files",nargs="*"); a=p.parse_args(); c=yaml.safe_load(Path(a.config).read_text()) or {}; ce=validate_config(c)
 if ce: print(json.dumps({"valid":False,"errors":ce},indent=2)); return 1
 x=None
 try:
  if a.files is not None or not a.base_ref: f=a.files or []; e=evaluate_changes(f,c)
  else: f=changed_files_from_git(a.base_ref,a.head_ref); e,x=evaluate_candidate(a.base_ref,a.head_ref,c)
 except RuntimeError as r: print(json.dumps({"valid":False,"errors":[str(r)]},indent=2)); return 1
 out={"valid":not e,"changed_files":f,"errors":e}
 if x: out["dependency_update_exemption"]={"status":x["status"],"items":len(x.get("items") or [])}
 print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if not e else 1
if __name__=="__main__": raise SystemExit(main())
