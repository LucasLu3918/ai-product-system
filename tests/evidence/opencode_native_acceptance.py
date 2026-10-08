"""Optional credential-free native OpenCode V2 acceptance; never a baseline dependency."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, ClassVar

ROOT = Path(__file__).resolve().parents[2]


class MockModelHandler(BaseHTTPRequestHandler):
    requests: ClassVar[list[dict[str, Any]]] = []

    def log_message(self, *_args):
        return

    def do_GET(self):
        body = json.dumps({"object": "list", "data": [{"id": "fixture", "object": "model"}]}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
        type(self).requests.append(payload)
        messages = payload.get('messages', [])
        user_prompt = '\n'.join(str(item.get('content', '')) for item in messages if isinstance(item, dict) and item.get('role') == 'user')
        previous_tool = any(item.get('role') == 'tool' or item.get('tool_call_id') for item in messages if isinstance(item, dict))
        body = None
        wants_asset = any(word in user_prompt.casefold() for word in ('建立', '創作', '修改', 'create', 'modify'))
        if payload.get('tools') and not previous_tool and wants_asset:
            modifying = '修改' in user_prompt or 'modify' in user_prompt.casefold()
            preferred = 'edit' if modifying else 'write'
            tool = next((item for item in payload['tools'] if item.get('function', {}).get('name') == preferred), None)
            if tool is None:
                tool = next((item for item in payload['tools'] if item.get('function', {}).get('name') in {'write', 'edit'}), None)
            if tool:
                name = tool['function']['name']
                schema = tool['function'].get('parameters', {})
                props = schema.get('properties', {})
                path_key = next((key for key in ('filePath', 'path', 'file_path') if key in props), 'filePath')
                target = 'existing.svg' if modifying else 'role.svg'
                if name == 'edit':
                    old_key = next((key for key in ('oldString', 'old_string') if key in props), 'oldString')
                    new_key = next((key for key in ('newString', 'new_string') if key in props), 'newString')
                    arguments = {path_key: target, old_key: 'keep', new_key: 'changed'}
                else:
                    content_key = next((key for key in ('content', 'text') if key in props), 'content')
                    arguments = {path_key: target, content_key: '<svg xmlns="http://www.w3.org/2000/svg"><title>AIPS mock</title></svg>'}
                body = {"id": "chatcmpl-aips-fixture", "object": "chat.completion", "created": 1, "model": "fixture", "choices": [{"index": 0, "message": {"role": "assistant", "content": None, "tool_calls": [{"id": "call-aips-write", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}]}, "finish_reason": "tool_calls"}]}
        if body is None:
            body = {"id": "chatcmpl-aips-fixture", "object": "chat.completion", "created": 1, "model": "fixture", "choices": [{"index": 0, "message": {"role": "assistant", "content": "Mock response."}, "finish_reason": "stop"}]}
        if payload.get('stream'):
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Cache-Control', 'no-cache'); self.send_header('Connection', 'keep-alive'); self.end_headers()
            message = body['choices'][0]['message']
            chunks = [{"id": body['id'], "object": "chat.completion.chunk", "created": body['created'], "model": body['model'], "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]}]
            if message.get('tool_calls'):
                for index, call in enumerate(message['tool_calls']):
                    function = call.get('function', {})
                    chunks.append({"id": body['id'], "object": "chat.completion.chunk", "created": body['created'], "model": body['model'], "choices": [{"index": 0, "delta": {"tool_calls": [{"index": index, "id": call.get('id'), "type": "function", "function": {"name": function.get('name'), "arguments": function.get('arguments', '')}}]}, "finish_reason": None}]})
            elif message.get('content'):
                chunks.append({"id": body['id'], "object": "chat.completion.chunk", "created": body['created'], "model": body['model'], "choices": [{"index": 0, "delta": {"content": message['content']}, "finish_reason": None}]})
            chunks.append({"id": body['id'], "object": "chat.completion.chunk", "created": body['created'], "model": body['model'], "choices": [{"index": 0, "delta": {}, "finish_reason": body['choices'][0]['finish_reason']}]})
            for chunk in chunks:
                self.wfile.write(b'data: ' + json.dumps(chunk).encode() + b'\n\n')
                self.wfile.flush()
            self.wfile.write(b'data: [DONE]\n\n'); self.wfile.flush()
            return
        encoded = json.dumps(body).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(encoded))); self.end_headers(); self.wfile.write(encoded)


def plugin_diagnostics(base: Path, server_log) -> list[str]:
    contents = []
    sources = []
    try:
        server_log.seek(0)
        contents.append(server_log.read().decode(errors='replace'))
        sources.append('server-output')
    except (OSError, AttributeError):
        pass
    for path in base.rglob('*.log'):
        if not path.is_file() or path.stat().st_size > 1024 * 1024:
            continue
        try:
            contents.append(path.read_text(errors='replace'))
            sources.append(path.name)
        except OSError:
            continue
    selected = []
    for source, text in zip(sources, contents):
        for line in text.splitlines():
            lower = line.casefold()
            if (
                'failed to load plugin' in lower
                or ('aips-opencode' in lower and any(word in lower for word in ('error', 'failed', 'exception')))
                or ('hook' in lower and any(word in lower for word in ('error', 'failed', 'exception')))
                or 'aips trace could not be recorded' in lower
            ):
                line = re.sub(r'(?i)(password|token|authorization|api[_ -]?key)(["\'=: ]+)[^\s,}]+', r'\1\2[redacted]', line)
                line = line.replace('What is 2 + 2?', '[prompt]')[:500]
                selected.append(f'{source}: {line}')
    if not selected:
        selected = [f'available_log={path.name}' for path in base.rglob('*') if path.is_file() and ('log' in path.name.casefold() or 'error' in path.name.casefold())][:20]
    return selected[-30:]


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
        assert (config / 'plugins/aips-opencode.ts').is_file(), 'verified V2 install did not project the native plugin'
        payload = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/mcp_server.py'), 'config', '--client', 'opencode'], env=env, cwd=base, text=True))
        mock = ThreadingHTTPServer(('127.0.0.1', 0), MockModelHandler)
        model_thread = threading.Thread(target=mock.serve_forever, daemon=True); model_thread.start()
        model_port = mock.server_address[1]
        payload['config']['model'] = 'aips-mock/fixture'
        payload['config']['providers'] = {'aips-mock': {'name': 'AIPS Loopback Mock', 'package': '@opencode/ai/providers/openai-compatible', 'settings': {'baseURL': f'http://127.0.0.1:{model_port}/v1'}, 'models': {'fixture': {'name': 'AIPS Mock Model', 'capabilities': {'tools': True, 'input': ['text'], 'output': ['text']}, 'limit': {'context': 8192, 'output': 512}}}}}
        payload['config']['permission'] = {'write': 'allow', 'edit': 'allow', 'patch': 'allow'}
        (config / 'opencode.json').write_text(json.dumps(payload['config']))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        workspace = base / 'workspace'; workspace.mkdir()
        with tempfile.TemporaryFile() as log:
            server = subprocess.Popen([binary, '--log-level', 'debug', '--print-logs', 'serve', '--hostname', '127.0.0.1', '--port', str(port)], env=dict(env, PWD=str(workspace), AIPS_CLI=str(ROOT / 'bin/aips'), AIPS_GUARD_PYTHON=sys.executable), cwd=workspace, stdout=log, stderr=log)
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
                    try:
                        with urllib.request.urlopen(req, timeout=30) as response:
                            response_body = response.read()
                            return json.loads(response_body) if response_body else None
                    except urllib.error.HTTPError as exc:
                        try:
                            diagnostic = json.loads(exc.read())
                            error = diagnostic.get('error', diagnostic)
                            code = error.get('name', error.get('code', 'unknown')) if isinstance(error, dict) else 'unknown'
                            message = error.get('message', '') if isinstance(error, dict) else ''
                            message = re.sub(r'(?i)(password|token|authorization|api[_ -]?key)(["\'=: ]+)[^\s,}]+', r'\1\2[redacted]', str(message))[:240]
                        except (ValueError, OSError):
                            code, message = 'unparseable_error', ''
                        raise RuntimeError(f'OpenCode API rejected {path.rsplit("/", 1)[-1]} with HTTP {exc.code}; error_code={code}; message={message}') from None

                spec = request('/openapi.json')
                ops = {v.get('operationId'): (method, path) for path, methods in spec['paths'].items() for method, v in methods.items() if isinstance(v, dict)}
                plugin_setup = 'UNVERIFIED'
                plugin_state = 'UNKNOWN'
                if 'plugin.list' in ops:
                    deadline = time.monotonic() + 30
                    aips_entry = None
                    plugin_result = {}
                    while time.monotonic() < deadline:
                        plugin_result = request(ops['plugin.list'][1])
                        plugin_items = plugin_result.get('data', []) if isinstance(plugin_result, dict) else []
                        aips_entry = next((item for item in plugin_items if isinstance(item, dict) and 'aips-opencode' in json.dumps(item)), None)
                        if aips_entry:
                            break
                        time.sleep(.5)
                    if aips_entry:
                        plugin_state = str(aips_entry.get('status', aips_entry.get('state', 'UNKNOWN')))
                        status_value = aips_entry.get('status', aips_entry.get('state'))
                        failed = status_value == 'failed' or (isinstance(status_value, dict) and status_value.get('status') == 'failed')
                        if failed:
                            raise RuntimeError(f'OpenCode discovered but failed to load the AIPS Plugin; error_ref={aips_entry.get("ref", "unknown")}; diagnostics={plugin_diagnostics(base, log)}')
                        plugin_setup = 'VERIFIED'
                    else:
                        diagnostics = []
                        for log_path in (base / 'state').rglob('*.log'):
                            contents = log_path.read_text(errors='replace')
                            contents = re.sub(r'(?i)(password|token|authorization|api[_ -]?key)([\"\'=: ]+)[^\s,}]+', r'\1\2[redacted]', contents)
                            diagnostics.extend(line[:400] for line in contents.splitlines()
                                               if 'plugin' in line.casefold() or 'aips' in line.casefold())
                        raise RuntimeError('OpenCode plugin registry did not report aips-opencode; response_keys='
                                           + repr(sorted(plugin_result.keys())) + '; diagnostics=' + repr(diagnostics[:8]))
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
                session = request(ops['session.create'][1], {'location': {'directory': str(workspace)}})['data']['id']
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
                prompt_op = ops.get('session.prompt')
                if not prompt_op:
                    raise RuntimeError('OpenCode API does not expose session.prompt; model and permission execution remain unverified')
                cli_config = base / 'cli-config'
                (cli_config / 'plugins').mkdir(parents=True, exist_ok=True)
                (cli_config / 'plugins/aips-opencode.ts').write_text((config / 'plugins/aips-opencode.ts').read_text())
                cli_settings = dict(payload['config'])
                cli_settings.pop('mcp', None)
                (cli_config / 'opencode.json').write_text(json.dumps(cli_settings))
                prompt_result = request(prompt_op[1].replace('{sessionID}', session), {'model': {'providerID': 'aips-mock', 'modelID': 'fixture'}, 'text': 'What is 2 + 2?'})
                deadline = time.monotonic() + 15
                while not MockModelHandler.requests and time.monotonic() < deadline:
                    time.sleep(.1)
                if not MockModelHandler.requests:
                    info = prompt_result.get('data', {}).get('info', {}) if isinstance(prompt_result, dict) else {}
                    trace_path = base / 'state/aips/opencode/events.jsonl'
                    trace_exists = trace_path.is_file()
                    raise RuntimeError(f'loopback mock model received no OpenCode request; prompt_outcome={info.get("outcome", "unknown")}; prompt_error={bool(info.get("error"))}; aips_trace={trace_exists}')
                messages = MockModelHandler.requests[-1].get('messages', [])
                request_text = json.dumps(MockModelHandler.requests[-1], ensure_ascii=False)
                model_execution_path = 'serve_api'
                if 'AIPS Turn Context' not in request_text:
                    # The public REST prompt route can bypass runtime session hooks.
                    # Exercise the user's native agent loop through the V2 CLI as well.
                    MockModelHandler.requests.clear()
                    cli = None
                    try:
                        cli = subprocess.run(
                            [binary, '--log-level', 'debug', '--print-logs', 'run', '--standalone', '--model', 'aips-mock/fixture', '--format', 'json', 'What is 2 + 2?'],
                            env=dict(env, PWD=str(workspace), OPENCODE_CONFIG_DIR=str(cli_config), XDG_DATA_HOME=str(base / 'cli-data'), XDG_CACHE_HOME=str(base / 'cli-cache'), AIPS_CLI=str(ROOT / 'bin/aips'), AIPS_GUARD_PYTHON=sys.executable),
                            cwd=workspace, capture_output=True, text=True, timeout=90,
                            check=False,
                        )
                    except subprocess.TimeoutExpired as timeout_error:
                        trace_path = base / 'state/aips/opencode/events.jsonl'
                        trace_events = []
                        if trace_path.is_file():
                            trace_data = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/opencode_trace.py'), '--file', str(trace_path)], env=env, text=True))
                            trace_events = [{key: item.get(key) for key in ('event', 'status', 'reason_code', 'duration_ms', 'context_command_ms', 'workflow_count', 'context_bytes')} for item in trace_data.get('events', [])]
                        raw_logs = timeout_error.stderr or b''
                        if isinstance(raw_logs, bytes):
                            raw_logs = raw_logs.decode(errors='replace')
                        filtered_logs = []
                        for line in raw_logs.splitlines():
                            lower = line.casefold()
                            if any(word in lower for word in ('hook', 'context', 'error', 'failed', 'session')):
                                line = line.replace('What is 2 + 2?', '[prompt]')
                                line = re.sub(r'(?i)(password|token|authorization|api[_ -]?key)(["\'=: ]+)[^\s,}]+', r'\1\2[redacted]', line)
                                filtered_logs.append(line[:400])
                        raise RuntimeError(f'native OpenCode CLI timed out; mock_requests={len(MockModelHandler.requests)}; trace_events={trace_events}; diagnostics={filtered_logs[-12:]}') from None
                    if cli and cli.returncode == 0 and MockModelHandler.requests:
                        cli_request = next((item for item in MockModelHandler.requests if 'AIPS Turn Context' in json.dumps(item, ensure_ascii=False)), None)
                        if cli_request is None:
                            cli_request = next((item for item in MockModelHandler.requests if 'What is 2 + 2?' in json.dumps(item, ensure_ascii=False)), MockModelHandler.requests[-1])
                        if 'AIPS Turn Context' in json.dumps(cli_request, ensure_ascii=False):
                            request_text = json.dumps(cli_request, ensure_ascii=False)
                            messages = cli_request.get('messages', [])
                            model_execution_path = 'native_cli'
                if 'AIPS Turn Context' not in request_text:
                    roles = [item.get('role', 'unknown') for item in messages if isinstance(item, dict)]
                    field_shapes = {str(key): type(value).__name__ for key, value in MockModelHandler.requests[-1].items() if key in {'messages', 'system', 'instructions', 'prompt'}}
                    trace_path = base / 'state/aips/opencode/events.jsonl'
                    trace_events = []
                    if trace_path.is_file():
                        trace_data = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/opencode_trace.py'), '--file', str(trace_path)], env=env, text=True))
                        trace_events = [{key: item.get(key) for key in ('event', 'status', 'decision', 'reason_code', 'duration_ms', 'context_command_ms', 'context_bytes')} for item in trace_data.get('events', [])]
                    cli_error_lines = []
                    if cli and cli.stderr:
                        for line in cli.stderr.splitlines():
                            lower = line.casefold()
                            if any(word in lower for word in ('hook', 'context', 'error', 'failed')):
                                line = line.replace('What is 2 + 2?', '[prompt]')
                                cli_error_lines.append(line[:300])
                    raise RuntimeError(f'AIPS Context was not observed in a native model request; execution_path=serve_api_then_cli; cli_exit={cli.returncode if cli else "not_run"}; message_roles={roles}; prompt_field_shapes={field_shapes}; plugin_state={plugin_state}; trace_events={trace_events}; cli_diagnostics={cli_error_lines[-10:]}; diagnostics={plugin_diagnostics(base, log)}')
                model_delivery = 'VERIFIED'

                def cli_prompt(text):
                    result = subprocess.run(
                        [binary, '--log-level', 'error', 'run', '--standalone', '--model', 'aips-mock/fixture', '--auto', '--format', 'json', text],
                        env=dict(env, PWD=str(workspace), OPENCODE_CONFIG_DIR=str(cli_config), XDG_DATA_HOME=str(base / 'cli-data'), XDG_CACHE_HOME=str(base / 'cli-cache'), AIPS_CLI=str(ROOT / 'bin/aips'), AIPS_GUARD_PYTHON=sys.executable),
                        cwd=workspace, capture_output=True, text=True, timeout=60,
                        check=False,
                    )
                    if result.returncode != 0:
                        error = re.sub(r'(?i)(password|token|authorization|api[_ -]?key)(["\'=: ]+)[^\s,}]+', r'\1\2[redacted]', result.stderr)[:300]
                        raise RuntimeError(f'native CLI agent loop failed; exit={result.returncode}; stderr={error}')

                def prompt(text):
                    created = request(ops['session.create'][1], {'location': {'directory': str(workspace)}})['data']['id']
                    request(prompt_op[1].replace('{sessionID}', created), {'model': {'providerID': 'aips-mock', 'modelID': 'fixture'}, 'text': text})
                    return created

                if model_execution_path == 'native_cli':
                    cli_prompt('請建立一個角色 SVG')
                else:
                    prompt('請建立一個角色 SVG')
                asset = workspace / 'role.svg'
                if not asset.is_file():
                    tool_calls = []
                    for item in MockModelHandler.requests:
                        for message in item.get('messages', []):
                            if isinstance(message, dict) and isinstance(message.get('tool_calls'), list):
                                tool_calls.extend(call.get('function', {}).get('name', 'unknown') for call in message['tool_calls'] if isinstance(call, dict))
                    trace_path = base / 'state/aips/opencode/events.jsonl'
                    trace_events = []
                    if trace_path.is_file():
                        trace_data = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/opencode_trace.py'), '--file', str(trace_path)], env=env, text=True))
                        trace_events = [{key: item.get(key) for key in ('event', 'status', 'decision', 'reason_code', 'domain', 'intent', 'readiness', 'project_mode', 'project', 'action', 'session_root_source')} for item in trace_data.get('events', [])]
                    expected_project_hash = hashlib.sha256(str(workspace.resolve()).encode()).hexdigest()[:16]
                    main_project_hash = hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:16]
                    raise RuntimeError(f'OpenCode did not execute the native write tool; tool_names={tool_calls[-8:]}; mock_requests={len(MockModelHandler.requests)}; expected_workspace_hash={expected_project_hash}; main_project_hash={main_project_hash}; trace_events={trace_events}')
                expected_project_hash = hashlib.sha256(str(workspace.resolve()).encode()).hexdigest()[:16]
                traces = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/opencode_trace.py'), '--file', str(base / 'state/aips/opencode/events.jsonl')], env=env, text=True))
                session_events = [item for item in traces.get('events', []) if item.get('event') in {'context', 'permission'} and item.get('project')]
                if not session_events or any(item.get('project') != expected_project_hash for item in session_events):
                    raise RuntimeError('native Context or permission trace did not bind to the isolated session workspace')
                if not any(item.get('event') == 'permission' and item.get('decision') == 'ALLOW' and item.get('session_root_source') == 'location_directory' for item in session_events):
                    raise RuntimeError('native Allow evidence did not include the active Session location source')
                (workspace / 'existing.svg').write_text('<svg>keep</svg>')
                if model_execution_path == 'native_cli':
                    cli_prompt('請修改既有角色 existing.svg')
                else:
                    prompt('請修改既有角色 existing.svg')
                if (workspace / 'existing.svg').read_text() != '<svg>keep</svg>':
                    raise RuntimeError('AIPS permission hook did not deny modification with partial EPHEMERAL Intelligence')
                traces = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/opencode_trace.py'), '--file', str(base / 'state/aips/opencode/events.jsonl')], env=env, text=True))
                decisions = {event.get('decision') for event in traces.get('events', []) if event.get('event') == 'permission'}
                if not {'ALLOW', 'DENY'} <= decisions:
                    raise RuntimeError('native permission Allow/Deny decisions were not both observed in AIPS trace')
                print(json.dumps({'version': version, 'skills': len(expected), 'commands': 3, 'skill_load': 'VERIFIED', 'mcp': 'CONNECTED', 'plugin_setup': plugin_setup, 'runtime': 'DISCOVERY_VERIFIED', 'model_execution': model_delivery, 'model_execution_path': model_execution_path, 'context_delivery': 'VERIFIED', 'permission_hook_execution': 'VERIFIED', 'permission_decisions': ['ALLOW', 'DENY'], 'pre_tool_guard': 'VERIFIED'}))
                print(json.dumps({'global_instructions': 'OFFICIAL_CONTRACT', 'instruction_model_delivery': 'UNVERIFIED'}))
            finally:
                server.terminate()
                server.wait(timeout=15)
                mock.shutdown(); mock.server_close(); model_thread.join(timeout=5)


if __name__ == '__main__':
    main()
