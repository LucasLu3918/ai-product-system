#!/usr/bin/env python3
"""Serve the AIPS read-only Parallel Run Dashboard on loopback."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_projection import build_projection


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIPS Parallel Run Dashboard</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#111b2e;--muted:#93a4bd;--text:#e7eef9;--line:#263651;--accent:#7dd3fc;--good:#86efac;--warn:#fde68a;--bad:#fca5a5}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1500px;margin:auto;padding:28px 24px}.top{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:22px}h1{margin:0;font-size:26px}h2{font-size:15px;margin:0 0 12px}.sub{color:var(--muted);margin-top:5px}.mode{border:1px solid var(--accent);color:var(--accent);border-radius:999px;padding:5px 10px;font-size:11px;letter-spacing:.08em}.summary{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}.pill{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 13px}.pill b{font-size:18px;margin-right:6px}.board{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;align-items:start}.column{background:rgba(17,27,46,.72);border:1px solid var(--line);border-radius:12px;padding:12px;min-height:160px}.column h2{color:var(--accent);text-transform:uppercase;letter-spacing:.08em}.card{background:#17243b;border:1px solid #304363;border-radius:10px;padding:12px;margin:10px 0}.card h3{margin:0 0 6px;font-size:15px}.meta{color:var(--muted);font-size:12px}.row{display:flex;justify-content:space-between;gap:8px;margin:5px 0}.badge{border-radius:5px;padding:2px 6px;font-size:11px}.CURRENT{color:var(--good);border:1px solid #28633f}.STALE,.UNKNOWN{color:var(--warn);border:1px solid #806b25}.WORKSPACE_MISSING{color:var(--bad);border:1px solid #803737}.events{border-top:1px solid var(--line);margin-top:10px;padding-top:8px}.event{font-size:11px;color:var(--muted);margin:3px 0}.empty{color:var(--muted);font-style:italic}.foot{color:var(--muted);font-size:11px;margin-top:18px}@media(max-width:640px){main{padding:18px 12px}.top{align-items:start;flex-direction:column}}
</style></head><body><main><div class="top"><div><h1>AIPS Parallel Run Dashboard</h1><div class="sub" id="repo">Loading repository…</div></div><div class="mode">READ_ONLY</div></div><div class="summary" id="summary"></div><div class="board" id="board"></div><div class="foot" id="foot"></div></main>
<script>
const esc=v=>String(v??'UNKNOWN');
const groups=['ACTIVE','VALIDATION','WAITING','BLOCKED','COMPLETE'];
function card(run){const w=run.workspace||{},x=run.execution||{},g=run.gate||{};const events=(run.events||[]).slice(-5).reverse().map(e=>`<div class="event">${esc(e.timestamp)} · ${esc(e.event)} · ${esc(e.status)}</div>`).join('');return `<article class="card"><div class="row"><h3>${esc(run.run_id)}</h3><span class="badge ${esc(w.health)}">${esc(w.health)}</span></div><div class="meta">${esc(run.protocol)} · ${esc(run.current_step)}</div><div class="row"><span>Task</span><span>${esc(x.task_id)}</span></div><div class="row"><span>Runtime</span><span>${esc(x.runtime)}</span></div><div class="row"><span>Gate</span><span>${esc(g.id)} (${esc(g.status)})</span></div><div class="meta">Last activity: ${esc(run.last_activity)}</div>${events?`<div class="events">${events}</div>`:''}</article>`}
function refresh(){fetch('/api/v1/runs',{cache:'no-store'}).then(r=>r.json()).then(data=>{document.getElementById('repo').textContent=`Repository: ${esc(data.repository?.name)} · ${esc(data.repository?.repository_id)}`;const runs=data.runs||[];const counts=Object.fromEntries(groups.map(g=>[g,0]));runs.forEach(r=>{const c=String(r.display_column||'UNKNOWN');const key=c.startsWith('WAITING')?'WAITING':c;counts[key]=(counts[key]||0)+1});document.getElementById('summary').innerHTML=groups.map(g=>`<div class="pill"><b>${counts[g]||0}</b>${g}</div>`).join('');const board=document.getElementById('board');board.innerHTML=groups.map(g=>{const items=runs.filter(r=>{const c=String(r.display_column||'UNKNOWN');return g==='WAITING'?c.startsWith('WAITING'):c===g});return `<section class="column"><h2>${g}</h2>${items.length?items.map(card).join(''):'<div class="empty">No runs</div>'}</section>`}).join('');document.getElementById('foot').textContent=`Snapshot ${esc(data.snapshot_fingerprint)} · refreshed ${new Date().toLocaleTimeString()}`}).catch(e=>{document.getElementById('foot').textContent='Dashboard unavailable: '+e})}refresh();setInterval(refresh,3000);
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    project: Path

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, "text/html; charset=utf-8", HTML.encode("utf-8"))
            return
        if path == "/healthz":
            self._send(200, "application/json", b'{"status":"READY","mode":"READ_ONLY"}')
            return
        if path == "/api/v1/runs":
            body = json.dumps(build_projection(self.project), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
            return
        self._send(404, "application/json", b'{"error":"not_found"}')

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=os.getcwd())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    if args.host != "127.0.0.1":
        parser.error("dashboard only supports --host 127.0.0.1")
    project = Path(args.project).expanduser().resolve()
    handler = type("DashboardHandler", (Handler,), {"project": project})
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{server.server_port}"
    print(json.dumps({"url": url, "mode": "READ_ONLY", "project": str(project)}), flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
