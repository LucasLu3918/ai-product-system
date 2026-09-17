#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]; PI=ROOT/'scripts/project_intelligence.py'
def run(args,env): return subprocess.run(args,env=env,capture_output=True,text=True)
def req(c,m):
    if not c: raise AssertionError(m)
def y(p): return yaml.safe_load(p.read_text(encoding='utf-8')) or {}
def main():
  with tempfile.TemporaryDirectory() as tmp:
    b=Path(tmp); p=b/'repo'; p.mkdir(); (p/'.ai').mkdir(); agents=p/'AGENTS.md'; agents.write_text('# Project Rules\n',encoding='utf-8'); (p/'main.py').write_text('print("ok")\n',encoding='utf-8')
    subprocess.run(['git','init','-q'],cwd=p,check=True); subprocess.run(['git','config','user.email','x@example.invalid'],cwd=p,check=True); subprocess.run(['git','config','user.name','AIPS'],cwd=p,check=True); subprocess.run(['git','add','.'],cwd=p,check=True); subprocess.run(['git','commit','-qm','init'],cwd=p,check=True)
    env=dict(os.environ); env['HOME']=str(b/'home'); env['XDG_CONFIG_HOME']=str(b/'config'); (b/'home').mkdir()
    r=run([sys.executable,str(PI),'bootstrap','--project',str(p),'--format','json'],env); req(r.returncode==0,r.stderr); store=p/'.ai/intelligence'; ip=store/'PROJECT_INTELLIGENCE.yaml'; intel=y(ip); intel['derived_invariants']=[{'id':'inv-logging','statement':'All service entry points must use structured logging.','type':'OBSERVED_CONVENTION','confidence':'high','evidence':['main.py'],'confirmed_count':3}]; ip.write_text(yaml.safe_dump(intel,sort_keys=False),encoding='utf-8')
    before_agents=agents.read_text(encoding='utf-8'); before_intel=ip.read_text(encoding='utf-8')
    denied=run([sys.executable,str(PI),'promote-invariant','--project',str(p),'--invariant-id','inv-logging','--target','AGENTS.md','--format','json'],env); req(denied.returncode!=0,'promotion without approval must fail'); req(agents.read_text(encoding='utf-8')==before_agents,'unapproved promotion mutated source'); req(ip.read_text(encoding='utf-8')==before_intel,'unapproved promotion mutated intelligence')
    ok=run([sys.executable,str(PI),'promote-invariant','--project',str(p),'--invariant-id','inv-logging','--target','AGENTS.md','--approved','--format','json'],env); req(ok.returncode==0,f'{ok.stdout} {ok.stderr}'); d=json.loads(ok.stdout); req(d['status']=='PROMOTED','promotion status wrong'); txt=agents.read_text(encoding='utf-8'); req('AIPS:promoted:inv-logging' in txt,'managed marker missing'); req('structured logging' in txt,'authoritative statement missing')
    registry=y(store/'SOURCE_REGISTRY.yaml'); src=next(s for s in registry['sources'] if s['path']=='AGENTS.md'); req(src['content_duplicated'] is False,'registry must remain pointer-over-copy'); after=y(ip); item=next(i for i in after['derived_invariants'] if i['id']=='inv-logging'); req(item['status']=='PROMOTED','candidate not marked promoted'); req('statement' not in item and 'text' not in item and 'value' not in item,'derived duplicate content retained'); req(item['authoritative_source']=='AGENTS.md','authoritative pointer missing')
    again=run([sys.executable,str(PI),'promote-invariant','--project',str(p),'--invariant-id','inv-logging','--target','AGENTS.md','--approved','--format','json'],env); req(again.returncode==0,again.stderr); req(json.loads(again.stdout)['status']=='ALREADY_PROMOTED','promotion must be idempotent'); req(agents.read_text(encoding='utf-8').count('AIPS:promoted:inv-logging')==1,'promotion duplicated marker')
  print('project_intelligence_promotion_lifecycle evidence: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
