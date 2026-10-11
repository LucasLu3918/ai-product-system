"""Bounded repair regression evidence; fixtures never claim real vision quality."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import creative_execution as c
import creative_repair as repair
from creative_errors import Blocked
from creative_request_policy import admit_prompt
from turn_intent import classify_task


def blocked(fn, reason):
    try:
        fn()
    except Blocked as exc:
        assert exc.reason_code == reason, (exc.reason_code, reason)
    else:
        raise AssertionError(f'Expected {reason}')


def fixture(root):
    prepared = c.prepare(root, 'characters', 'wizard', 'Wizard', 'Wizard identity', 'anime fantasy', 'Wizard portrait', ['round glasses', 'lightning scar on forehead skin'])
    (root / 'model').mkdir()
    binary = root / 'mflux-generate'
    buffer = io.BytesIO()
    Image.new('RGB', (64, 64), 'white').save(buffer, format='PNG')
    binary.write_text('#!/usr/bin/env python3\nimport pathlib,sys\np=pathlib.Path(sys.argv[sys.argv.index("--output")+1]); p.write_bytes(bytes.fromhex(' + repr(buffer.getvalue().hex()) + '))\n')
    binary.chmod(0o755)
    return c.configure(root, prepared['bundle'], {'provider': 'mflux_local', 'runtime': 'mflux-generate', 'runtime_version': 'fixture', 'model': {'id': 'dev', 'revision': 'fixture', 'local_path': str(root / 'model'), 'license': 'fixture', 'license_source': 'local fixture'}, 'mflux_executable': str(binary), 'width': 64, 'height': 64, 'steps': 1, 'timeout_seconds': 10, 'max_retries': 0})['bundle']


def vision(assessments):
    states = iter(assessments)
    def request(url, *, data=None, **kwargs):
        if url.endswith('/api/tags'):
            return json.dumps({'models': [{'name': 'vision-fixture'}]}).encode()
        body = json.loads(data)
        assert len(body['messages'][0]['images']) == 5
        assert kwargs['timeout'] <= 120
        criteria = json.loads(body['messages'][0]['content'].split('Criteria: ')[-1])
        assessment = next(states)
        checks = [{'id': item['id'], 'assessment': assessment if item['kind'] == 'required' else 'MATCH', 'evidence': 'Visible forehead placement', 'suggestion': 'Keep scar on skin'} for item in criteria]
        return json.dumps({'message': {'content': json.dumps({'observations': [{'check': 'identity', 'assessment': 'POSSIBLE_ISSUE' if assessment == 'DEFECT' else 'MATCH', 'evidence': 'Forehead detail', 'suggestion': 'Inspect skin'}], 'checks': checks})}}).encode()
    return request


def main():
    for prompt in ('請按疤痕在額頭皮膚、不在頭髮上，重出一張哈利', '請在 characters/harry-potter-v1 下，以日式奇幻動漫風重出一張哈利波特，閃電疤痕在額頭皮膚中央、不在頭髮上，圓眼鏡葛萊分多長袍，精緻有質感'):
        assert classify_task(prompt)['domain'] == 'creative'
        grant = admit_prompt(prompt)
        assert grant['grants']['execute']['allowed'] and grant['grants']['repair']['allowed'] and grant['max_outputs'] == 1
        assert not grant['grants']['quality-loop']['allowed']
    for prompt in ('分析重出一張角色圖片為什麼失敗', '不要重出一張角色圖片', '只規劃角色重畫', '請解釋重出一張哈利的方式', '請不要重新生成圖片', 'Please explain how to repair and generate an image'):
        assert not admit_prompt(prompt)['grants']['execute']['allowed'], prompt
        assert not admit_prompt(prompt)['grants']['repair']['allowed'], prompt
    assert admit_prompt('請生成一張角色圖片')['grants']['quality-check']['allowed']
    assert not admit_prompt('建立角色資料夾')['grants']['quality-check']['allowed']
    feedback_grant = admit_prompt('哈利波特的閃電是刀疤跟髮型沒關係，不可以在頭髮上呈現')
    assert feedback_grant['grants']['feedback']['allowed'] and not feedback_grant['grants']['execute']['allowed']
    auto = admit_prompt('請生成一張角色圖片，產圖後檢查並自動修正')
    assert auto['grants']['quality-loop']['allowed'] and auto['max_repairs'] == 2
    for prompt in ('請生成圖片，但不要自動修復', 'Generate an image, but do not automatically repair it'):
        assert not admit_prompt(prompt)['grants']['quality-loop']['allowed']
    assert admit_prompt('請生成一張角色圖片，自動修正最多一次')['max_repairs'] == 1
    assert admit_prompt('請生成兩張角色圖片，自動修正')['max_repair_total'] == 4
    assert admit_prompt('請生成兩張角色圖片，自動修正，總共最多一次')['max_repair_total'] == 1
    criteria = repair.checklist({'character': {'identity_features': ['scar on forehead']}, 'style': {'intent': 'anime'}})
    blocked(lambda: repair.validate_checks([], criteria), 'visual_review_response_invalid')
    blocked(lambda: repair.validate_checks([{'id': 'required-1', 'assessment': 'MATCH', 'evidence': '', 'suggestion': 'ok'}] * 2, criteria), 'visual_review_response_invalid')
    with tempfile.TemporaryDirectory(prefix='creative-repair-') as temp:
        base = Path(temp)
        with patch.dict(os.environ, {'XDG_STATE_HOME': str(base / 'state'), 'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH']}):
            root = base / 'revision'; root.mkdir()
            bundle = fixture(root)
            generated = c.execute(root, bundle)
            manifest = generated['manifest']; original = (root / manifest).read_bytes()
            before = {row['path']: (root / row['path']).read_bytes() for row in json.loads(original)['profiles']}
            record = repair.feedback(root, manifest, ['Scar is on hair'])
            assert record['generation_executed'] is False and (root / manifest).read_bytes() == original
            settings = {'defects': ['Scar is on hair'], 'critical_features': ['scar on exposed forehead skin'], 'forbidden_misplacements': ['lightning mark on hair'], 'prefer_edit': False}
            with ThreadPoolExecutor(max_workers=2) as pool:
                revisions = list(pool.map(lambda _: repair.revision(root, manifest, settings), range(2)))
            assert revisions[0]['bundle'] != revisions[1]['bundle']
            for row in revisions:
                new_profile = root / Path(row['bundle']).parent.parent / 'CHARACTER_PROFILE.yaml'
                assert 'lightning mark on hair' in yaml.safe_load(new_profile.read_text())['acceptance_criteria']['forbidden_misplacements']
            assert all((root / path).read_bytes() == content for path, content in before.items())
            if os.name != 'nt':
                lock = root / Path(bundle).parent.parent / '.aips-creative-repair.lock'
                with lock.open('a') as holder:
                    c.fcntl.flock(holder.fileno(), c.fcntl.LOCK_EX)
                    token = repair.execution_deadline.set(time.monotonic() + 0.05)
                    try:
                        blocked(lambda: repair.revision(root, manifest, settings), 'time_budget_exhausted')
                    finally:
                        repair.execution_deadline.reset(token)
                        c.fcntl.flock(holder.fileno(), c.fcntl.LOCK_UN)

            after = c.execute(root, revisions[0]['bundle'])
            comparison = repair.compare(root, manifest, after['manifest'])
            assert comparison['user_acceptance'] == 'NOT_RECORDED'
            assert comparison['before']['image']['sha256'] == json.loads(original)['output']['sha256']
            with patch.object(c, 'local_request', vision(['DEFECT'])):
                reviewed = c.review_assist(root, after['manifest'], 'vision-fixture', detailed=True)
            report = json.loads((root / reviewed['report']).read_text())
            assert report['machine_decision'] == 'DEFECTS_FOUND' and report['authority'] == 'NONE'
            assert json.loads((root / after['manifest']).read_text())['review']['status'] == 'PENDING'
            (root / manifest).write_bytes(original.replace(b'"COMPLETE"', b'"CHANGED"'))
            blocked(lambda: repair.compare(root, manifest, after['manifest']), 'creative_comparison_lineage_mismatch')
            (root / manifest).write_bytes(original)
            for name, states, expected_count, reason in [('repaired', ['DEFECT', 'MATCH'], 2, 'awaiting_human_review'), ('uncertain', ['UNCERTAIN'], 1, 'uncertain_machine_review'), ('repeated', ['DEFECT'] * 2, 2, 'repeated_defect_requires_strategy'), ('exhausted', ['DEFECT'], 1, 'repair_budget_exhausted')]:
                project = base / name; project.mkdir(); source = fixture(project)
                with patch.object(c, 'local_request', vision(states)):
                    result = repair.quality_loop(project, source, 'vision-fixture', 0 if name == 'exhausted' else 2, 30)
                assert result['generation_attempts'] == expected_count, result
                assert result['reason_code'] == reason, result
                assert result['accepted_count'] == 0
                assert all(json.loads((project / row['manifest']).read_text())['review']['status'] == 'PENDING' for row in result['attempts'])
                blocked(lambda project=project, source=source: repair.quality_loop(project, source, 'vision-fixture', 2, 30), 'creative_request_already_used')
            project = base / 'missing-review'; project.mkdir(); source = fixture(project)
            with patch.object(c, 'local_request', lambda *a, **kw: b'{"models":[]}'):
                blocked(lambda: repair.quality_loop(project, source, 'missing', 2, 30), 'visual_review_model_not_installed')
            assert not list(project.rglob('creative-execution-manifest.json'))
            project = base / 'time'; project.mkdir(); source = fixture(project)
            with patch.object(c, 'local_request', vision([])):
                result = repair.quality_loop(project, source, 'vision-fixture', 2, 1)
            assert result['generation_attempts'] == 0 and result['reason_code'] == 'time_budget_exhausted'
    print('Creative repair lifecycle PASS: original prompts, negative intent, criterion coverage, versioned feedback/revisions, concurrent preparation, bound comparison, finite repair/uncertainty/time stops, and no false Human acceptance')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
