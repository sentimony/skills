"""Checkpoint writing and validation tests."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import transfer_context as ct
from ct_fixtures import make_repo, make_draft


class WriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name)
        self.store = Path(self.tmp.name) / 'store'
        self.args = SimpleNamespace(repo=str(self.repo), store=str(self.store), budget=12000,
                                    statusline=False, transcript=None, rollout=None,
                                    prepare=None, refresh=None, rotate=None)
        self.draft = make_draft(self.repo)

    def test_delegated_sessions_through_fake_sibling(self):
        scripts = Path(self.tmp.name) / 'skills/transfer-context/scripts'
        sibling = Path(self.tmp.name) / 'skills/cross-agent/scripts'
        scripts.mkdir(parents=True)
        sibling.mkdir(parents=True)
        module = scripts / 'transfer_context.py'
        shutil.copy(ct.__file__, module)
        fake = sibling / 'cross_agent.py'
        host = Path(self.tmp.name) / 'host.json'
        host.write_text('{}')
        fields = ('session_id', 'task', 'family', 'model', 'effort',
                  'cli_session_id', 'state', 'alive')
        sessions = [dict(zip(fields, ('id1', 'task1', 'claude', 'model1', 'medium',
                                      'cli1', 'running', True))),
                    dict(zip(fields, ('id2', 'task2', 'codex', 'model2', 'high',
                                      'cli2', 'done', False)))]
        fake.write_text('import json, sys\nassert sys.argv[1:] == ' +
                        repr(['--host-context', str(host), '--status']) +
                        '\nprint(' + repr(json.dumps({'sessions': sessions})) + ')\n')
        def invoke(*args):
            return subprocess.run([sys.executable, str(module), *args], capture_output=True,
                                  text=True, check=True)
        facts = json.loads(invoke('facts', '--repo', str(self.repo), '--store', str(self.store),
                                  '--json', '--host-context', str(host)).stdout)
        self.assertEqual(facts['delegated_sessions'], sessions)
        written = json.loads(invoke('write', '--repo', str(self.repo), '--store', str(self.store),
                                    '--json', '--host-context', str(host), str(self.draft)).stdout)
        self.assertEqual(ct.parse_checkpoint(Path(written['path']).read_text())[0]['delegated_sessions'], sessions)
        without = json.loads(invoke('facts', '--repo', str(self.repo), '--store', str(self.store),
                                    '--json').stdout)['delegated_sessions']
        self.assertEqual(without, {'not_captured': 'no --host-context'})
        reasons = []
        for code in ('import sys; sys.exit(1)', "print('invalid json')"):
            fake.write_text(code)
            result = json.loads(invoke('facts', '--repo', str(self.repo), '--store', str(self.store),
                                       '--json', '--host-context', str(host)).stdout)
            reasons.append(result['delegated_sessions']['not_captured'])
        self.assertEqual(len(set(reasons + [without['not_captured']])), 3)
        fake.unlink()
        result = json.loads(invoke('facts', '--repo', str(self.repo), '--store', str(self.store),
                                   '--json', '--host-context', str(host)).stdout)
        self.assertIn('not_captured', result['delegated_sessions'])

    def test_missing_sibling_launcher_records_why_it_is_not_captured(self):
        # Plugin installs have no sibling cross-agent skill: the reason must say so.
        scripts = Path(self.tmp.name) / 'skills/transfer-context/scripts'
        scripts.mkdir(parents=True)
        module = scripts / 'transfer_context.py'
        shutil.copy(ct.__file__, module)
        host = Path(self.tmp.name) / 'host.json'
        host.write_text('{}')
        facts = json.loads(subprocess.run(
            [sys.executable, str(module), 'facts', '--repo', str(self.repo), '--store',
             str(self.store), '--json', '--host-context', str(host)],
            capture_output=True, text=True, check=True).stdout)
        reason = facts['delegated_sessions']['not_captured']
        self.assertIn('cross-agent', reason)
        self.assertIn('not installed', reason)

    def test_delegated_timeout(self):
        with mock.patch.object(ct.subprocess, 'run', side_effect=subprocess.TimeoutExpired('fake', 30)):
            with mock.patch.object(ct.Path, 'is_file', return_value=True):
                self.assertIn('timeout', ct.capture_delegated('host')['not_captured'])

    def test_write_idempotent_and_previous(self):
        first = ct.write_checkpoint(self.draft, self.args)
        self.assertEqual(first, ct.write_checkpoint(self.draft, self.args))
        meta, body = ct.parse_checkpoint(first.read_text())
        self.assertIsNone(meta['previous_transfer_id'])
        self.assertEqual(first.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.store.stat().st_mode & 0o777, 0o700)
        self.assertIn(str(first), body)
        text = self.draft.read_text().replace('next step', 'different step')
        self.draft.write_text(text)
        second = ct.write_checkpoint(self.draft, self.args)
        self.assertEqual(ct.parse_checkpoint(second.read_text())[0]['previous_transfer_id'], first.stem)

    def test_write_refreshes_when_dirty_file_content_changes(self):
        for name in ('tracked', 'untracked'):
            with self.subTest(name=name):
                first = ct.write_checkpoint(self.draft, self.args)
                (self.repo / name).write_text('updated content')
                second = ct.write_checkpoint(self.draft, self.args)
                self.assertNotEqual(first, second)
                meta, _ = ct.parse_checkpoint(second.read_text())
                self.assertEqual(meta['previous_transfer_id'], first.stem)
                self.assertEqual(second, ct.write_checkpoint(self.draft, self.args))

    def test_failure_preserves_latest_and_removes_new_file(self):
        first = ct.write_checkpoint(self.draft, self.args)
        before = {p.name: p.read_bytes() for p in self.store.iterdir()}
        self.draft.write_text(self.draft.read_text().replace('next step', 'different step'))
        real = ct.os.replace
        def replace(src, dst):
            if Path(dst).name.startswith('latest-'):
                raise OSError('simulated failure')
            return real(src, dst)
        with mock.patch.object(ct.os, 'replace', side_effect=replace):
            with self.assertRaises(OSError):
                ct.write_checkpoint(self.draft, self.args)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.store.iterdir()})
        self.assertTrue(first.exists())

    def test_missing_and_secret_rejected(self):
        meta, body = ct.parse_checkpoint(self.draft.read_text())
        meta['artifacts'] = ['missing']
        errors, _ = ct.validate_checkpoint(meta, body, self.repo, 'draft')
        self.assertTrue(any('missing' in e for e in errors))
        errors, _ = ct.validate_checkpoint(meta, body + '\nghp_exampleSecret', self.repo, 'draft')
        self.assertTrue(any('ghp_' in e and 'exampleSecret' not in e for e in errors))


    def test_artifact_object_names_index_and_type(self):
        meta, body = ct.parse_checkpoint(self.draft.read_text())
        meta['artifacts'] = ['ok', {'path': 'x', 'role': 'plan'}]
        errors, _ = ct.validate_checkpoint(meta, body, self.repo, 'draft')
        self.assertIn('artifacts[1]: expected a relative path string, got dict', errors)

    def test_write_reports_resume_commands_and_argument_hint(self):
        command = [sys.executable, ct.__file__]
        args = ['--repo', str(self.repo), '--store', str(self.store)]
        write = subprocess.run(command + ['write', *args, '--json', str(self.draft)], capture_output=True, text=True)
        self.assertEqual(write.returncode, 0, write.stderr)
        data = json.loads(write.stdout)
        transfer_id = Path(data['path']).stem
        self.assertEqual(data['resume_command'], '/transfer-context resume ' + transfer_id)
        self.assertEqual(data['resume_command_codex'], '$transfer-context resume ' + transfer_id)
        root = ct.parse_checkpoint(Path(data['path']).read_text())[0]['project']['root']
        bin_dir = Path(self.tmp.name) / 'bin'
        bin_dir.mkdir()
        for name in ('claude', 'codex'):
            (bin_dir / name).write_text('#!/bin/sh\nprintf "%s" "$1"\n')
            (bin_dir / name).chmod(0o755)
        env = {'PATH': '%s:/usr/bin:/bin' % bin_dir}
        for key, name, argument in (
                ('resume_command_terminal', 'claude', '/transfer-context resume ' + transfer_id),
                ('resume_command_terminal_codex', 'codex', '$transfer-context resume ' + transfer_id)):
            shell = subprocess.run(['sh', '-c', data[key]], capture_output=True, text=True, env=env)
            self.assertEqual(shell.stdout, argument, data[key])
        skill = (Path(ct.__file__).parent.parent / 'SKILL.md').read_text()
        self.assertIn('argument-hint: "[save | resume [<path|id>] | check]"', skill)

    def short_draft(self):
        import re
        text = self.draft.read_text()
        head = text.split('\n## ', 1)[0]
        body = ''.join('\n## %s\n\nSomething.\n' % name for name in
                       ('Objective', 'Decisions', 'Failed approaches', 'Pending user decisions'))
        path = self.draft.with_name('short.md')
        path.write_text(head + '\n' + body)
        return path

    def auto_write(self, body):
        head = self.draft.read_text().split('\n## ', 1)[0]
        path = self.draft.with_name('auto.md')
        path.write_text(head + '\n' + body)
        return subprocess.run([sys.executable, ct.__file__, 'write', '--repo', str(self.repo),
                               '--store', str(self.store), '--auto', '--json', str(path)],
                              capture_output=True, text=True)

    def test_auto_keeps_heading_lines_inside_fenced_blocks(self):
        for fence in ('```', '~~~'):
            with self.subTest(fence=fence):
                body = ''.join('\n## %s\n\nText.\n' % name for name in
                               ('Objective', 'Failed approaches', 'Pending user decisions'))
                body += '\n## Decisions\n\n%ssh\n## Not a section\n%s\nAfter.\n' % (fence, fence)
                result = self.auto_write(body)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                text = Path(json.loads(result.stdout)['path']).read_text()
                decisions = text.split('\n## Decisions\n', 1)[1].split('\n## Pending user decisions', 1)[0]
                self.assertIn('## Not a section', decisions)
                self.assertIn('After.', decisions)
                self.assertEqual(len([l for l in text.splitlines() if l.startswith('## ')]), 12)

    def test_info_string_fence_line_does_not_close_a_fence(self):
        body = ''.join('\n## %s\n\nText.\n' % name for name in
                       ('Objective', 'Failed approaches', 'Pending user decisions'))
        body += '\n## Decisions\n\n```\nfirst\n```python\n## Hidden\nstill code\n```\nAfter.\n'
        result = self.auto_write(body)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = Path(json.loads(result.stdout)['path']).read_text()
        decisions = text.split('\n## Decisions\n', 1)[1].split('\n## Pending user decisions', 1)[0]
        self.assertIn('## Hidden', decisions)
        self.assertIn('After.', decisions)
        self.assertNotIn('\n## Hidden', text.replace(decisions, ''))

    def test_fenced_section_heading_passes_auto_and_validate(self):
        body = ''.join('\n## %s\n\nText.\n' % name for name in
                       ('Decisions', 'Failed approaches', 'Pending user decisions'))
        body = '\n## Objective\n\n```\n## State\nexample\n```\n' + body
        result = self.auto_write(body)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        path = json.loads(result.stdout)['path']
        check = subprocess.run([sys.executable, ct.__file__, 'validate', '--repo', str(self.repo),
                                '--store', str(self.store), path], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertNotIn('out of order', check.stdout + check.stderr)

    def test_auto_rejects_duplicate_section_titles(self):
        base = ''.join('\n## %s\n\nText.\n' % name for name in
                       ('Objective', 'Decisions', 'Failed approaches', 'Pending user decisions'))
        for extra, title in (('\n## Decisions\n\nAgain.\n', 'Decisions'),
                             ('\n## Objective and acceptance\n\nAgain.\n', 'Objective and acceptance')):
            with self.subTest(title=title):
                result = self.auto_write(base + extra)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(title, result.stdout + result.stderr)
                self.assertIn('duplicate', (result.stdout + result.stderr).lower())

    def test_auto_fills_missing_sections_from_the_short_draft(self):
        command = [sys.executable, ct.__file__]
        args = ['--repo', str(self.repo), '--store', str(self.store)]
        short = self.short_draft()
        plain = subprocess.run(command + ['write', *args, '--json', str(short)], capture_output=True, text=True)
        self.assertNotEqual(plain.returncode, 0)
        auto = subprocess.run(command + ['write', *args, '--auto', '--json', str(short)],
                              capture_output=True, text=True)
        self.assertEqual(auto.returncode, 0, auto.stdout + auto.stderr)
        path = json.loads(auto.stdout)['path']
        check = subprocess.run(command + ['validate', *args, path], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        body = Path(path).read_text()
        self.assertEqual(len([line for line in body.splitlines() if line.startswith('## ')]), 11)
        self.assertIn('None recorded.', body)
        self.assertIn('Something.', body)

    def test_secret_artifact_diagnostics_do_not_echo(self):
        secret = 'ghp_EXAMPLEVALUE'
        draft = make_draft(self.repo, artifacts=[secret])
        command = [sys.executable, ct.__file__]
        args = ['--repo', str(self.repo), '--store', str(self.store)]
        write = subprocess.run(command + ['write', *args, str(draft)], capture_output=True, text=True)
        self.assertEqual(write.returncode, 1)
        self.assertNotIn('EXAMPLEVALUE', write.stdout + write.stderr)
        valid = ct.write_checkpoint(make_draft(self.repo), self.args)
        meta, body = ct.parse_checkpoint(valid.read_text())
        meta['artifacts'] = [secret]
        valid.write_text('---\n' + json.dumps(meta) + '\n---\n' + body)
        validate = subprocess.run(command + ['validate', str(valid)], capture_output=True, text=True)
        self.assertEqual(validate.returncode, 1)
        self.assertNotIn('EXAMPLEVALUE', validate.stdout + validate.stderr)

    def test_each_secret_and_ordinary_words(self):
        values = ['ghp_', 'github_pat_', 'glpat-', 'sk-', 'AKIA', 'xoxa-', 'xoxb-',
                  'xoxp-', 'xoxr-', 'xoxs-']
        for prefix in values:
            with self.subTest(prefix=prefix):
                self.assertTrue(ct._secret_errors('line one\n' + prefix + 'EXAMPLE'))
        for value in ('-----BEGIN PRIVATE KEY-----', 'password=example', 'token=example',
                      '"token": "example"'):
            self.assertTrue(ct._secret_errors(value))
        self.assertFalse(ct._secret_errors('task-1 risk-2'))

    def test_validation_and_budget(self):
        meta, body = ct.parse_checkpoint(self.draft.read_text())
        for key in ('task', 'verification', 'continuation', 'artifacts'):
            broken = dict(meta)
            del broken[key]
            self.assertTrue(ct.validate_checkpoint(broken, body, self.repo, 'draft')[0])
        for section in ct.SECTIONS:
            broken = body.replace('## ' + section, '## Removed', 1)
            self.assertTrue(any(section in e for e in ct.validate_checkpoint(meta, broken, self.repo, 'draft')[0]))
        meta['project'] = {}
        self.assertTrue(ct.validate_checkpoint(meta, body, self.repo, 'draft')[0])
        self.args.budget = 1
        path = ct.write_checkpoint(self.draft, self.args)
        saved, saved_body = ct.parse_checkpoint(path.read_text())
        saved['schema_version'] = 2
        self.assertTrue(any('update' in e for e in ct.validate_checkpoint(saved, saved_body, self.repo, 'checkpoint')[0]))
        saved['schema_version'] = 1
        saved['artifacts'] = ['missing']
        errors, warnings = ct.validate_checkpoint(saved, saved_body, self.repo, 'checkpoint')
        self.assertFalse(errors)
        self.assertTrue(warnings)

    def test_first_replace_failure_and_existing_resume_block(self):
        first = ct.write_checkpoint(self.draft, self.args)
        before = {p.name: p.read_bytes() for p in self.store.iterdir()}
        self.draft.write_text(self.draft.read_text().replace('next step', 'other step'))
        with mock.patch.object(ct.os, 'replace', side_effect=OSError('failed')):
            with self.assertRaises(OSError):
                ct.write_checkpoint(self.draft, self.args)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.store.iterdir()})
        meta, body = ct.parse_checkpoint(first.read_text())
        model = {k: meta[k] for k in ('task', 'verification', 'continuation', 'artifacts')}
        model['source'] = {'model': meta['source']['model']}
        self.draft.write_text('---\n' + json.dumps(model) + '\n---\n' + body)
        self.assertEqual(first, ct.write_checkpoint(self.draft, self.args))
        self.assertEqual(body.count(ct.RESUME_MARKER), 2)

    def _write_json(self, text):
        self.draft.write_text(text)
        command = [sys.executable, ct.__file__, 'write', '--repo', str(self.repo),
                   '--store', str(self.store), '--json', str(self.draft)]
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        data = json.loads(run.stdout)
        return data, ct.parse_checkpoint(Path(data['path']).read_text())[1]

    def test_fenced_resume_heading_before_real_section_is_content(self):
        fenced = '\n```\n## Resume prompt\nFAKE\n```\n'
        text = self.draft.read_text().replace('\n## Resume prompt', fenced + '\n## Resume prompt', 1)
        data, body = self._write_json(text)
        self.assertTrue(data['resume_prompt'].startswith('None.\n\n' + ct.RESUME_MARKER))
        self.assertNotIn('FAKE', data['resume_prompt'])
        self.assertIn(fenced, body)
        self.assertEqual(body.count(ct.RESUME_MARKER), 2)
        self.assertLess(body.index('FAKE'), body.index(ct.RESUME_MARKER))
        real = body.index('\n## Resume prompt\n\nNone.')
        self.assertLess(real, body.index(ct.RESUME_MARKER))
        self.assertLess(body.index(ct.RESUME_MARKER), body.index('\n## Objective and acceptance'))

    def test_fenced_heading_inside_resume_section_does_not_end_it(self):
        text = self.draft.read_text().replace(
            '## Resume prompt\n\nNone.\n', '## Resume prompt\n\nGo.\n```\n## X\n```\nDone.\n', 1)
        data, body = self._write_json(text)
        self.assertTrue(data['resume_prompt'].startswith('Go.\n```\n## X\n```\nDone.\n\n' + ct.RESUME_MARKER))
        self.assertLess(body.index('Done.'), body.index(ct.RESUME_MARKER))

    def test_nbsp_after_closing_fence_does_not_close_block(self):
        text = '```\n## Hidden\n```\u00a0\n## Hidden\n```\n## Real\n'
        self.assertEqual([title for title, _, _ in ct._headings(text)], ['Real'])

    def test_symlink_store_is_rejected(self):
        target = Path(self.tmp.name) / 'target'
        target.mkdir()
        self.store.symlink_to(target, target_is_directory=True)
        with self.assertRaises(OSError):
            ct.write_checkpoint(self.draft, self.args)
        self.assertEqual(list(target.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
