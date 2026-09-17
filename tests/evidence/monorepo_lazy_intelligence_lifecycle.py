#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
PI = ROOT / "scripts" / "project_intelligence.py"

def run(args, env): return subprocess.run(args, env=env, capture_output=True, text=True)
def req(c,m):
    if not c: raise AssertionError(m)
def y(p): return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
def main():
  with tempfile.TemporaryDirectory() as tmp:
    b=Path(tmp); p=b/'repo'; p.mkdir(); (p/'.ai').mkdir(); (p/'AGENTS.md').write_text('# Rules\n',encoding='utf-8'); (p/'apps/api').mkdir(parents=True); (p/'apps/web').mkdir(parents=True); (p/'shared').mkdir()
    subprocess.run(['git','init','-q'],cwd=p,check=True); subprocess.run(['git','config','user.email','x@example.invalid'],cwd=p,check=True); subprocess.run(['git','config','user.name','AIPS'],cwd=p,check=True); subprocess.run(['git','add','.'],cwd=p,check=True); subprocess.run(['git','commit','-qm','init'],cwd=p,check=True)
    env=dict(os.environ); env['HOME']=str(b/'home'); env['XDG_CONFIG_HOME']=str(b/'config'); (b/'home').mkdir()
    r=run([sys.executable,str(PI),'bootstrap','--project',str(p),'--format','json'],env); req(r.returncode==0,r.stderr)
    store=p/'.ai/intelligence'; intel=y(store/'PROJECT_INTELLIGENCE.yaml'); intel['state']['readiness']='READY'; intel['architecture']={'summary':'Monorepo system summary','confidence':'high','source':'topics/architecture.md'}
    topics=intel.setdefault('topics',{})
    for key,topic,comp in [('architecture','architecture','system'),('api-modules','modules','api'),('web-modules','modules','web'),('shared-conventions','conventions','shared')]:
      f=store/'topics'/f'{key}.md'; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(f'# {key}\nEvidence-grounded fixture topic.\n',encoding='utf-8'); topics[key]={'path':f'topics/{key}.md','topic':topic,'component':comp,'type':'FACT','evidence':['AGENTS.md']}
    (store/'PROJECT_INTELLIGENCE.yaml').write_text(yaml.safe_dump(intel,sort_keys=False),encoding='utf-8')
    graph={'version':1,'nodes':{'api':{'component':'api','type':'app'},'web':{'component':'web','type':'app'},'shared':{'component':'shared','type':'library'}},'edges':[{'source':'api','target':'shared','type':'uses'},{'source':'web','target':'shared','type':'uses'}]}
    (store/'IMPACT_GRAPH.yaml').write_text(yaml.safe_dump(graph,sort_keys=False),encoding='utf-8')
    r=run([sys.executable,str(PI),'context','--project',str(p),'--runtime','codex','--prompt','modify api module conventions','--component','api','--format','json'],env); req(r.returncode==0,r.stderr); d=json.loads(r.stdout); m=d['context']['monorepo']; keys=m['selected_topic_keys']; req('api-modules' in keys,'target component missing'); req('shared-conventions' in keys,'shared topic missing'); req('web-modules' not in keys,'unrelated web topic loaded'); ids={n['id'] for n in m['shared_relationships']['nodes']}; req(ids=={'api','shared'},f'unexpected nodes {ids}'); req('web' in m['shared_relationships']['excluded_components'],'web exclusion not explicit')
  print('monorepo_lazy_intelligence_lifecycle evidence: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
