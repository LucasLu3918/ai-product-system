"""Optional credential-free native OpenCode V2 acceptance; never a baseline dependency."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    args = parser.parse_args()
    binary = str(Path(args.binary).resolve(strict=True))
    with tempfile.TemporaryDirectory(prefix='aips-opencode-native-') as tmp:
        base = Path(tmp).resolve()
        config = base / 'config/opencode'
        env = dict(os.environ, HOME=str(base), XDG_CONFIG_HOME=str(base / 'config'), XDG_DATA_HOME=str(base / 'data'), XDG_CACHE_HOME=str(base / 'cache'), XDG_STATE_HOME=str(base / 'state'), OPENCODE_CONFIG_DIR=str(config), AIPS_VALIDATION_PYTHON=sys.executable)
        # No inherited provider/auth/service overrides enter this isolated runtime.
        for key in list(env):
            if key.startswith(('OPENCODE_', 'OPENAI_', 'ANTHROPIC_', 'GOOGLE_', 'GEMINI_', 'AWS_', 'AZURE_')) and key != 'OPENCODE_CONFIG_DIR':
                env.pop(key)
        version = subprocess.check_output([binary, '--version'], env=env, text=True).strip()
        if not re.fullmatch(r'(?:opencode\s+)?v?2\.\d+\.\d+', version):
            raise ValueError('native acceptance requires an explicit OpenCode V2 binary')
        for command in [
            [sys.executable, str(ROOT / 'scripts/opencode_skill_projection.py'), 'install'],
            [sys.executable, str(ROOT / 'scripts/portable_commands.py'), 'install', '--host', 'opencode'],
        ]:
            subprocess.run(command, env=env, cwd=base, capture_output=True, check=True)
        payload = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/mcp_server.py'), 'config', '--client', 'opencode'], env=env, cwd=base, text=True))
        (config / 'opencode.json').write_text(json.dumps(payload['config']))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        with tempfile.TemporaryFile() as log:
            server = subprocess.Popen([binary, 'serve', '--hostname', '127.0.0.1', '--port', str(port)], env=env, cwd=base, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 20
                password = ''
                while not password and time.monotonic() < deadline:
                    log.seek(0)
                    match = re.search(r'server password\s+(\S+)', log.read().decode())
                    if match:
                        password = match.group(1)
                    else:
                        time.sleep(.1)
                if not password:
                    raise RuntimeError('private native server readiness failed')
                authorization = 'Basic ' + base64.b64encode(('opencode:' + password).encode()).decode()

                def request(path, body=None):
                    req = urllib.request.Request(f'http://127.0.0.1:{port}' + path, data=None if body is None else json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Authorization': authorization})
                    with urllib.request.urlopen(req, timeout=15) as response:
                        body = response.read()
                        return json.loads(body) if body else None

                spec = request('/openapi.json')
                ops = {v.get('operationId'): (method, path) for path, methods in spec['paths'].items() for method, v in methods.items() if isinstance(v, dict)}
                expected = {p.parent.name for p in config.glob('skills/*/SKILL.md')}
                found = {}
                for op, names in [('skill.list', expected), ('command.list', {'aips-plan', 'aips-impact', 'aips-constitution'})]:
                    deadline = time.monotonic() + 30
                    while True:
                        items = request(ops[op][1]).get('data', [])
                        found = {i.get('id', i.get('name')): i for i in items}
                        if names <= found.keys():
                            break
                        if time.monotonic() >= deadline:
                            raise RuntimeError(f'{op}: native discovery incomplete')
                        time.sleep(.5)
                    if op == 'skill.list':
                        assert all(found[name].get('description') and found[name].get('content') for name in names)
                session = request(ops['session.create'][1], {})['data']['id']
                load_path = ops['experimental.session.skill'][1].replace('{sessionID}', session)
                request(load_path, {'id': 'tdd', 'resume': False})
                message_paths = [path for path, methods in spec['paths'].items() if '{sessionID}' in path and path.endswith('/message') and 'get' in methods]
                assert len(message_paths) == 1, 'native session message operation is ambiguous'
                messages = request(message_paths[0].replace('{sessionID}', session))
                assert 'Test-Driven Development' in json.dumps(messages), 'native Skill body was not loaded'
                deadline = time.monotonic() + 15
                while True:
                    mcp = request(ops['mcp.list'][1]).get('data', [])
                    if any(i.get('name') == 'aips' and i.get('status', {}).get('status') == 'connected' for i in mcp):
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError('native MCP connection incomplete')
                    time.sleep(.5)
                print(json.dumps({'version': version, 'skills': len(expected), 'commands': 3, 'skill_load': 'VERIFIED', 'mcp': 'CONNECTED', 'runtime': 'DISCOVERY_VERIFIED', 'model_execution': 'UNVERIFIED', 'pre_tool_guard': 'UNSUPPORTED'}))
                print(json.dumps({'global_instructions': 'OFFICIAL_CONTRACT', 'instruction_model_delivery': 'UNVERIFIED'}))
            finally:
                server.terminate()
                server.wait(timeout=15)


if __name__ == '__main__':
    main()
