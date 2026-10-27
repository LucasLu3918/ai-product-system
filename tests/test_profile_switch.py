from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import aips_profile as ap
import protected_paths as pp
import publication_diagnostics
import turn_context_hook as hook

PROFILE_SCRIPT = ROOT / 'scripts' / 'aips_profile.py'
TEST_SWITCH = ap.Switch(False, '測試用開關', 'test-only switch')


class ProfileTestCase(unittest.TestCase):
    """Every test uses a temporary profile path; the real ~/.config/aips is never touched."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(os.path.realpath(self._tmp.name))
        self.path = self.base / 'config' / 'aips' / 'profile.yaml'
        patcher = patch.object(ap, 'profile_settings_path', return_value=self.path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, text: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text, encoding='utf-8')

    def with_test_switch(self):
        return patch.dict(ap.SWITCHES, {'test_relax': TEST_SWITCH})


class DefaultsAndLoadingTests(ProfileTestCase):
    def test_missing_file_is_strict_defaults(self):
        state = ap.load_profile(self.path)
        self.assertEqual(state.status, 'DEFAULT')
        self.assertIsNone(state.diagnostic)
        self.assertEqual(ap.non_default_fields(state), [])
        self.assertEqual(ap.turn_context_line(state), 'aips_profile=strict')
        self.assertEqual(ap.diagnostic_fields(state), {'name': 'strict', 'status': 'DEFAULT',
                                                       'non_default_fields': [], 'reason_code': None})

    def test_every_switch_defaults_off(self):
        # Mechanism rule: a relaxation must be off by default; PR10 enables none.
        with self.with_test_switch():
            self.assertFalse(any(switch.default for switch in ap.SWITCHES.values()))
            self.assertFalse(ap.load_profile(self.path).values['test_relax'])

    def test_missing_file_keeps_turn_context_and_diagnostics_strict(self):
        data = {'project': {'root': '/p'}, 'intelligence': {}, 'requirements': {}, 'context': {},
                'fail_policy': {'mode': 'soft'}, 'task': {'mutation_likely': False}}
        rendered = hook.compact_context(data)
        self.assertIn('aips_profile=strict', rendered.splitlines())
        self.assertNotIn('aips_profile_non_default', rendered)
        self.assertNotIn('aips_profile_status', rendered)

    def test_valid_file_reports_source_and_non_default_names(self):
        self.write('version: 1\nsettings:\n  test_relax: true\n')
        with self.with_test_switch():
            state = ap.load_profile(self.path)
            self.assertEqual(state.status, 'LOADED')
            self.assertTrue(state.values['test_relax'])
            self.assertEqual(state.sources['test_relax'], 'file')
            self.assertEqual(ap.non_default_fields(state), ['test_relax'])
            self.assertEqual(ap.turn_context_line(state), 'aips_profile=strict aips_profile_non_default=test_relax')
            self.assertEqual(ap.diagnostic_fields(state)['non_default_fields'], ['test_relax'])
            payload = ap.show_payload(state)
            self.assertEqual(payload['switches']['test_relax'], {'value': True, 'default': False, 'source': 'file'})

    def test_file_with_empty_settings_is_loaded_with_defaults(self):
        self.write('version: 1\n')
        state = ap.load_profile(self.path)
        self.assertEqual(state.status, 'LOADED')
        self.assertEqual(ap.non_default_fields(state), [])

    def test_malformed_yaml_fails_closed_to_defaults(self):
        self.write('version: [\n')
        state = ap.load_profile(self.path)
        self.assertEqual(state.status, 'INVALID')
        self.assertEqual(state.diagnostic['reason_code'], 'PROFILE_FILE_MALFORMED')
        self.assertEqual(state.diagnostic['fields'], [])
        self.assertEqual(ap.turn_context_line(state), 'aips_profile=strict aips_profile_status=INVALID reason=PROFILE_FILE_MALFORMED')

    def test_malformed_file_never_enables_a_relaxation(self):
        self.write('version: 1\nsettings:\n  test_relax: true\n  broken: [\n')
        with self.with_test_switch():
            state = ap.load_profile(self.path)
            self.assertEqual(state.status, 'INVALID')
            self.assertFalse(state.values['test_relax'])
            self.assertEqual(ap.non_default_fields(state), [])

    def test_unknown_setting_key_rejects_whole_file(self):
        self.write('version: 1\nsettings:\n  test_relax: true\n  not_a_switch: true\n')
        with self.with_test_switch():
            state = ap.load_profile(self.path)
        self.assertEqual(state.status, 'INVALID')
        self.assertEqual(state.diagnostic['reason_code'], 'PROFILE_UNKNOWN_KEY')
        self.assertEqual(state.diagnostic['fields'], ['not_a_switch'])
        self.assertFalse(state.values.get('test_relax', False))

    def test_unknown_top_level_key_is_reported(self):
        self.write('version: 1\nsettings: {}\nextra: 1\n')
        state = ap.load_profile(self.path)
        self.assertEqual(state.diagnostic['reason_code'], 'PROFILE_UNKNOWN_KEY')
        self.assertEqual(state.diagnostic['fields'], ['extra'])

    def test_unexpected_key_names_are_bounded_and_placeholdered(self):
        keys = ''.join(f'  "Bad Key {index}": true\n' for index in range(12))
        self.write('version: 1\nsettings:\n' + keys)
        state = ap.load_profile(self.path)
        self.assertEqual(state.diagnostic['reason_code'], 'PROFILE_UNKNOWN_KEY')
        self.assertEqual(state.diagnostic['fields'], ['<invalid-key>'])
        self.assertLessEqual(len(state.diagnostic['fields']), ap.MAX_REPORTED_FIELDS)

    def test_wrong_value_type_is_rejected(self):
        for value in ('"yes"', '1', 'null', '[true]'):
            with self.subTest(value=value), self.with_test_switch():
                self.write(f'version: 1\nsettings:\n  test_relax: {value}\n')
                state = ap.load_profile(self.path)
                self.assertEqual(state.diagnostic['reason_code'], 'PROFILE_VALUE_TYPE_INVALID')
                self.assertFalse(state.values['test_relax'])

    def test_wrong_schema_version_and_shape_are_malformed(self):
        for text in ('version: 2\nsettings: {}\n', 'version: true\nsettings: {}\n', 'settings: {}\n',
                     'version: 1\nsettings: [1]\n', '- 1\n- 2\n', 'just text\n'):
            with self.subTest(text=text):
                self.write(text)
                self.assertEqual(ap.load_profile(self.path).diagnostic['reason_code'], 'PROFILE_FILE_MALFORMED')

    def test_symlink_and_directory_are_unsafe(self):
        target = self.base / 'elsewhere.yaml'
        target.write_text('version: 1\nsettings: {}\n', encoding='utf-8')
        self.path.parent.mkdir(parents=True)
        self.path.symlink_to(target)
        self.assertEqual(ap.load_profile(self.path).diagnostic['reason_code'], 'PROFILE_FILE_UNSAFE')
        self.path.unlink()
        self.path.mkdir()
        self.assertEqual(ap.load_profile(self.path).diagnostic['reason_code'], 'PROFILE_FILE_UNSAFE')

    def test_oversized_file_is_rejected(self):
        self.write('version: 1\n# ' + 'x' * (ap.MAX_FILE_BYTES + 1) + '\n')
        self.assertEqual(ap.load_profile(self.path).diagnostic['reason_code'], 'PROFILE_FILE_TOO_LARGE')

    def test_unexpected_loader_failure_falls_back_to_defaults(self):
        with patch.object(ap, '_load', side_effect=RuntimeError('boom')):
            state = ap.load_profile(self.path)
        self.assertEqual(state.status, 'INVALID')
        self.assertEqual(state.diagnostic['reason_code'], 'PROFILE_UNAVAILABLE')

    def test_show_text_and_json_are_stable(self):
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(ap.main(['show', '--format', 'json']), 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(list(payload), sorted(payload))
        self.assertEqual(payload['profile_file'], '~/.config/aips/profile.yaml')
        self.assertEqual(payload['switches'], {})
        self.assertNotIn(str(self.base), out.getvalue())
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            ap.main(['show'])
        self.assertIn('switches: none in this version', out.getvalue())


class SetConfirmationTests(ProfileTestCase):
    def confirm(self, typed: str):
        summary = io.StringIO()
        prompts: list[str] = []

        def read_line(prompt: str) -> str:
            prompts.append(prompt)
            return typed

        return summary, prompts, read_line

    def test_set_refuses_without_interactive_terminal_and_writes_nothing(self):
        with self.with_test_switch(), self.assertRaises(ap.ProfileError) as ctx:
            ap.set_switch('test_relax', 'true', interactive=False, read_line=lambda prompt: 'SET test_relax true')
        self.assertEqual(ctx.exception.reason_code, 'PROFILE_SET_REQUIRES_TTY')
        self.assertFalse(self.path.exists())

    def test_non_tty_cli_refuses_with_stable_reason_code(self):
        env = {key: value for key, value in os.environ.items() if key not in {'XDG_CONFIG_HOME'}}
        env['HOME'] = str(self.base / 'home')
        env['XDG_CONFIG_HOME'] = str(self.base / 'xdg')
        proc = subprocess.run([sys.executable, str(PROFILE_SCRIPT), 'set', 'test_relax', 'true'], input='SET test_relax true\n',
                              capture_output=True, text=True, env=env, timeout=60, check=False)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload['reason_code'], 'PROFILE_SET_REQUIRES_TTY')
        self.assertEqual(payload['status'], 'BLOCKED')
        self.assertFalse((self.base / 'xdg' / 'aips' / 'profile.yaml').exists())

    def test_cli_has_no_flag_that_skips_confirmation(self):
        parser = ap.build_parser()
        for flag in ('--yes', '--force', '--no-confirm'):
            with self.subTest(flag=flag), self.assertRaises(SystemExit):
                parser.parse_args(['set', 'test_relax', 'true', flag])

    def test_cli_set_is_refused_when_stdin_is_not_tty_even_with_patched_confirmation(self):
        with self.with_test_switch(), patch.object(ap, '_is_tty', return_value=False), \
                patch.object(ap, '_read_confirmation', return_value='SET test_relax true\n'), \
                patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(ap.main(['set', 'test_relax', 'true']), 1)
        self.assertEqual(json.loads(out.getvalue())['reason_code'], 'PROFILE_SET_REQUIRES_TTY')
        self.assertFalse(self.path.exists())

    def test_unknown_key_is_refused_without_writing(self):
        with self.assertRaises(ap.ProfileError) as ctx:
            ap.set_switch('not_allowed', 'true', interactive=True, read_line=lambda p: 'SET not_allowed true', path=self.path)
        self.assertEqual(ctx.exception.reason_code, 'PROFILE_KEY_NOT_ALLOWED')
        self.assertNotIn('not_allowed', str(ctx.exception))
        self.assertFalse(self.path.exists())

    def test_empty_allow_list_refuses_every_key(self):
        self.assertEqual(ap.SWITCHES, {})
        with self.assertRaises(ap.ProfileError) as ctx:
            ap.set_switch('test_relax', 'true', interactive=True, read_line=lambda p: '', path=self.path)
        self.assertEqual(ctx.exception.reason_code, 'PROFILE_KEY_NOT_ALLOWED')

    def test_value_must_be_true_or_false(self):
        with self.with_test_switch():
            for value in ('yes', 'True', '1', ''):
                with self.subTest(value=value), self.assertRaises(ap.ProfileError) as ctx:
                    ap.set_switch('test_relax', value, interactive=True, read_line=lambda p: '', path=self.path)
                self.assertEqual(ctx.exception.reason_code, 'PROFILE_VALUE_INVALID')
        self.assertFalse(self.path.exists())

    def test_unchanged_value_is_refused_without_prompt(self):
        summary, prompts, read_line = self.confirm('SET test_relax false')
        with self.with_test_switch(), self.assertRaises(ap.ProfileError) as ctx:
            ap.set_switch('test_relax', 'false', interactive=True, read_line=read_line, summary_stream=summary, path=self.path)
        self.assertEqual(ctx.exception.reason_code, 'PROFILE_VALUE_UNCHANGED')
        self.assertEqual(prompts, [])
        self.assertFalse(self.path.exists())

    def test_wrong_confirmation_phrase_declines_without_writing(self):
        for typed in ('', 'yes', 'SET test_relax false', 'set test_relax true', 'SET test_relax true extra'):
            with self.subTest(typed=typed), self.with_test_switch():
                summary, _prompts, read_line = self.confirm(typed)
                with self.assertRaises(ap.ProfileError) as ctx:
                    ap.set_switch('test_relax', 'true', interactive=True, read_line=read_line, summary_stream=summary, path=self.path)
                self.assertEqual(ctx.exception.reason_code, 'PROFILE_SET_DECLINED')
                self.assertFalse(self.path.exists())

    def test_confirmed_set_writes_private_file_and_prints_summary(self):
        summary, prompts, read_line = self.confirm('SET test_relax true')
        with self.with_test_switch():
            result = ap.set_switch('test_relax', 'true', interactive=True, read_line=read_line, summary_stream=summary, path=self.path)
            self.assertEqual(result['status'], 'UPDATED')
            self.assertEqual((result['old'], result['new']), (False, True))
            self.assertEqual(result['non_default_fields'], ['test_relax'])
            state = ap.load_profile(self.path)
            self.assertEqual(state.status, 'LOADED')
            self.assertTrue(state.values['test_relax'])
        self.assertIn('SET test_relax true', prompts[0])
        text = summary.getvalue()
        self.assertIn('old: false', text)
        self.assertIn('new: true', text)
        self.assertIn('test-only switch', text)
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)
        self.assertEqual(os.stat(self.path.parent).st_mode & 0o777, 0o700)
        self.assertNotIn(str(self.base), json.dumps(result))

    def test_set_preserves_other_file_settings_and_back_to_default(self):
        with patch.dict(ap.SWITCHES, {'test_relax': TEST_SWITCH, 'other_relax': ap.Switch(False, 'o', 'other')}):
            self.write('version: 1\nsettings:\n  other_relax: true\n')
            summary, _, read_line = self.confirm('SET test_relax true')
            ap.set_switch('test_relax', 'true', interactive=True, read_line=read_line, summary_stream=summary, path=self.path)
            self.assertEqual(ap.load_profile(self.path).sources['other_relax'], 'file')
            summary, _, read_line = self.confirm('SET test_relax false')
            ap.set_switch('test_relax', 'false', interactive=True, read_line=read_line, summary_stream=summary, path=self.path)
            state = ap.load_profile(self.path)
            self.assertTrue(state.values['other_relax'])
            self.assertFalse(state.values['test_relax'])
            self.assertEqual(ap.non_default_fields(state), ['other_relax'])

    def test_set_never_overwrites_an_invalid_file(self):
        self.write('version: 1\nsettings:\n  test_relax: "yes"\n')
        original = self.path.read_text(encoding='utf-8')
        summary, _, read_line = self.confirm('SET test_relax true')
        with self.with_test_switch(), self.assertRaises(ap.ProfileError) as ctx:
            ap.set_switch('test_relax', 'true', interactive=True, read_line=read_line, summary_stream=summary, path=self.path)
        self.assertEqual(ctx.exception.reason_code, 'PROFILE_FILE_INVALID')
        self.assertEqual(self.path.read_text(encoding='utf-8'), original)

    def test_failed_replace_leaves_previous_file_and_no_temporary_file(self):
        self.write('version: 1\nsettings: {}\n')
        original = self.path.read_text(encoding='utf-8')
        summary, _, read_line = self.confirm('SET test_relax true')
        with self.with_test_switch(), patch.object(ap.os, 'replace', side_effect=OSError('disk full')), \
                self.assertRaises(OSError):
            ap.set_switch('test_relax', 'true', interactive=True, read_line=read_line, summary_stream=summary, path=self.path)
        self.assertEqual(self.path.read_text(encoding='utf-8'), original)
        leftovers = [name for name in os.listdir(self.path.parent) if name.startswith('.aips-profile-')]
        self.assertEqual(leftovers, [])

    def test_main_confirmed_path_writes_only_the_patched_profile(self):
        with self.with_test_switch(), patch.object(ap, '_is_tty', return_value=True), \
                patch.object(ap, '_read_confirmation', return_value='SET test_relax true\n'), \
                patch('sys.stdout', new_callable=io.StringIO) as out, patch('sys.stderr', new_callable=io.StringIO):
            self.assertEqual(ap.main(['set', 'test_relax', 'true']), 0)
        self.assertEqual(json.loads(out.getvalue())['status'], 'UPDATED')
        with self.with_test_switch():
            self.assertTrue(ap.load_profile(self.path).values['test_relax'])


class AgentWriteGuardTests(unittest.TestCase):
    """PR3 guard coverage for the profile file, the profile directory and `aips profile set`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(os.path.realpath(self._tmp.name))
        self.project = self.base / 'project'
        self.project.mkdir()
        self.config = self.base / 'home' / '.config' / 'aips'
        env_patch = patch.dict(os.environ, {'HOME': str(self.base / 'home')})
        env_patch.start()
        self.addCleanup(env_patch.stop)
        for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'AIPS_INSTALL_DIR'):
            os.environ.pop(key, None)

    def test_profile_set_and_profile_file_writes_are_protected(self):
        self.assertTrue(pp.bash_command_writes_protected('aips profile set test_relax true', self.project))
        self.assertTrue(pp.bash_command_writes_protected('/usr/local/bin/aips profile set test_relax true', self.project))
        self.assertTrue(pp.bash_command_writes_protected('echo ok && aips profile set k true', self.project))
        self.assertTrue(pp.bash_command_writes_protected(f'echo "version: 1" > {self.config}/profile.yaml', self.project))
        self.assertTrue(pp.bash_command_writes_protected(f'mv /tmp/x {self.config}/profile.yaml', self.project))
        self.assertTrue(pp.file_tool_write_is_protected('Edit', {'file_path': str(self.config / 'profile.yaml')}, self.project))
        self.assertTrue(pp.file_tool_write_is_protected('Write', {'file_path': str(self.config / 'profiles' / 'x.yaml')}, self.project))

    def test_profile_reads_and_unrelated_commands_are_not_blocked(self):
        self.assertFalse(pp.bash_command_writes_protected('aips profile show', self.project))
        self.assertFalse(pp.bash_command_writes_protected('aips profile show --format json', self.project))
        self.assertFalse(pp.bash_command_writes_protected('aips creative profile draft --model-id m', self.project))
        self.assertFalse(pp.bash_command_writes_protected('cat ' + str(self.config / 'profile.yaml'), self.project))


class PublicationAndTurnContextFieldTests(ProfileTestCase):
    def test_publication_doctor_exposes_names_and_status_only(self):
        self.write('version: 1\nsettings:\n  test_relax: "secret-value"\n')
        with self.with_test_switch():
            fields = publication_diagnostics._profile_fields()
        self.assertEqual(fields['name'], 'strict')
        self.assertEqual(fields['status'], 'INVALID')
        self.assertEqual(fields['reason_code'], 'PROFILE_VALUE_TYPE_INVALID')
        self.assertNotIn('secret-value', json.dumps(fields))

    def test_publication_doctor_result_carries_profile_block(self):
        plain = self.base / 'not-a-repository'
        plain.mkdir()
        result = publication_diagnostics.doctor(plain)
        self.assertEqual(result['profile']['name'], 'strict')
        self.assertIn(result['profile']['status'], {'DEFAULT', 'INVALID', 'LOADED', 'UNAVAILABLE'})
        self.assertNotIn(str(self.base), json.dumps(result['profile']))

    def test_turn_context_line_failure_is_visible_and_strict(self):
        with patch.object(hook, 'turn_context_line', None):
            self.assertEqual(hook.profile_line(), 'aips_profile=strict aips_profile_status=UNAVAILABLE')
        with patch.object(hook, 'turn_context_line', side_effect=RuntimeError('x')):
            self.assertEqual(hook.profile_line(), 'aips_profile=strict aips_profile_status=UNAVAILABLE')


if __name__ == '__main__':
    unittest.main()
