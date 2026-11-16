"""Resume selection, identity and drift tests."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import transfer_context as ct
from ct_fixtures import git, make_draft, make_repo


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name, 'git@github.com:O/R.git')
        self.store = Path(self.tmp.name) / 'store'
        self.args = SimpleNamespace(repo=str(self.repo), store=str(self.store), budget=12000,
                                    statusline=False, transcript=None, rollout=None,
                                    prepare=None, refresh=None, rotate=None)
        self.draft = make_draft(self.repo)

    def check(self, target=None):
        return ct.resume_check(target, self.args)

    def test_fresh_end_to_end_and_head(self):
        self.draft.write_text(self.draft.read_text().replace('## Verification\n\nNone.',
                              '## Verification\n\nTests passed.').replace(
                              '## Next actions\n\nNone.', '## Next actions\n\nFinish implementation.'))
        path = ct.write_checkpoint(self.draft, self.args)
        self.assertEqual(self.check()['verdict'], 'fresh')
        self.assertEqual(self.check(path.stem)['path'], str(path))
        self.assertIn('## Verification\n\nTests passed.', path.read_text())
        self.assertIn('## Next actions\n\nFinish implementation.', path.read_text())
        git(self.repo, 'add', 'tracked')
        git(self.repo, 'commit', '-m', 'progress')
        result = self.check(str(path))
        self.assertEqual(result['verdict'], 'drifted')
        self.assertIn('head', [d['kind'] for d in result['drift']])

    def linked(self, name='linked'):
        tree = Path(self.tmp.name) / name
        git(self.repo, 'worktree', 'add', '-b', name, str(tree))
        return tree

    def args_for(self, repo):
        return SimpleNamespace(**dict(vars(self.args), repo=str(repo)))

    def write_in(self, tree):
        draft = make_draft(tree)
        return ct.write_checkpoint(draft, self.args_for(tree))

    def test_resume_from_the_main_checkout_compares_with_the_checkpoint_worktree(self):
        tree = self.linked()
        path = self.write_in(tree)
        result = ct.resume_check(str(path), self.args_for(self.repo))
        self.assertEqual(Path(result['resumed_from_other_worktree']).resolve(), tree.resolve())
        self.assertEqual(result['drift'], [])
        self.assertEqual(result['verdict'], 'fresh')

    def test_real_drift_in_the_checkpoint_worktree_is_still_reported(self):
        tree = self.linked()
        path = self.write_in(tree)
        git(tree, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid',
            'commit', '--allow-empty', '-m', 'progress')
        result = ct.resume_check(str(path), self.args_for(self.repo))
        kinds = [d['kind'] for d in result['drift']]
        self.assertIn('head', kinds)
        self.assertEqual(result['verdict'], 'drifted')
        self.assertIsNotNone(result['resumed_from_other_worktree'])

    def test_removed_worktree_is_a_single_drift_record(self):
        tree = self.linked()
        path = self.write_in(tree)
        git(self.repo, 'worktree', 'remove', '--force', str(tree))
        result = ct.resume_check(str(path), self.args_for(self.repo))
        self.assertEqual([d['kind'] for d in result['drift']], ['worktree-removed'])
        self.assertEqual(Path(result['drift'][0]['detail']['saved']).resolve(), tree.resolve())
        self.assertEqual(result['missing'], [])
        self.assertIn('artifacts', result['unverified'])
        self.assertEqual(result['verdict'], 'drifted')

    def test_saved_path_that_became_a_directory_inside_another_worktree_is_removed(self):
        nested = self.repo / 'nested-wt'
        git(self.repo, 'worktree', 'add', '-b', 'nested', str(nested))
        path = self.write_in(nested)
        git(self.repo, 'worktree', 'remove', '--force', str(nested))
        nested.mkdir()
        result = ct.resume_check(str(path), self.args_for(self.repo))
        self.assertEqual([d['kind'] for d in result['drift']], ['worktree-removed'])
        self.assertEqual(result['verdict'], 'drifted')

    def test_same_worktree_has_no_other_worktree_field(self):
        path = ct.write_checkpoint(self.draft, self.args)
        result = ct.resume_check(str(path), self.args)
        self.assertIsNone(result['resumed_from_other_worktree'])
        none = ct.resume_check(None, SimpleNamespace(**dict(vars(self.args), store=str(Path(self.tmp.name) / 'empty'))))
        self.assertIsNone(none['resumed_from_other_worktree'])

    def test_origin_ref_drift_without_head_change(self):
        head = git(self.repo, 'rev-parse', 'HEAD').strip()
        git(self.repo, 'update-ref', 'refs/remotes/origin/main', head)
        git(self.repo, 'symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        path = ct.write_checkpoint(self.draft, self.args)
        git(self.repo, 'commit', '--allow-empty', '-m', 'another')
        newer = git(self.repo, 'rev-parse', 'HEAD').strip()
        git(self.repo, 'reset', '--soft', head)
        git(self.repo, 'update-ref', 'refs/remotes/origin/main', newer)
        result = self.check(str(path))
        self.assertIn('origin-ref', [item['kind'] for item in result['drift']])
        self.assertNotEqual(path, ct.write_checkpoint(self.draft, self.args))

    def test_captured_refs_becoming_unavailable_are_drift(self):
        head = git(self.repo, 'rev-parse', 'HEAD').strip()
        git(self.repo, 'update-ref', 'refs/heads/default-test', head)
        git(self.repo, 'update-ref', 'refs/remotes/origin/default-test', head)
        git(self.repo, 'symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/default-test')
        path = ct.write_checkpoint(self.draft, self.args)
        git(self.repo, 'update-ref', '-d', 'refs/heads/default-test')
        git(self.repo, 'update-ref', '-d', 'refs/remotes/origin/default-test')
        result = self.check(str(path))
        for kind in ('default-branch-ref', 'origin-ref'):
            entry = next((d for d in result['drift'] if d['kind'] == kind), None)
            self.assertIsNotNone(entry, kind)
            self.assertIsNone(entry['detail']['current'])
            self.assertTrue(entry['detail']['saved'])
        self.assertEqual(result['verdict'], 'drifted')
        self.assertIn('default_branch_head', result['unverified'])
        self.assertIn('origin_ref_head', result['unverified'])

    def test_linked_worktrees_unverified_legacy_and_deduplication(self):
        first = ct.write_checkpoint(self.draft, self.args)
        self.assertIn('default_branch', self.check()['unverified'])
        tree = Path(self.tmp.name) / 'detached tree'
        git(self.repo, 'worktree', 'add', '--detach', str(tree))
        facts = ct.collect_facts(self.repo)['project']
        detached = next(item for item in facts['worktrees'] if Path(item['path']).resolve() == tree.resolve())
        self.assertIsNone(detached['branch'])
        self.assertIn('worktrees', [d['kind'] for d in self.check()['drift']])
        second = ct.write_checkpoint(self.draft, self.args)
        self.assertNotEqual(first, second)
        self.assertEqual(second, ct.write_checkpoint(self.draft, self.args))
        meta, body = ct.parse_checkpoint(first.read_text())
        for key in ('worktrees', 'default_branch', 'default_branch_head', 'origin_ref_head'):
            del meta['project'][key]
        first.write_text('---\n' + json.dumps(meta) + '\n---\n' + body)
        result = self.check(str(first))
        self.assertEqual(set(result['unverified']), {'worktrees', 'default_branch',
                         'default_branch_head', 'origin_ref_head'})
        self.assertNotEqual(result['verdict'], 'invalid')

    def test_branch_dirty_content_deleted_and_rename(self):
        ct.write_checkpoint(self.draft, self.args)
        git(self.repo, 'checkout', '-b', 'other')
        self.assertIn('branch', [d['kind'] for d in self.check()['drift']])
        (self.repo / 'tracked').write_text('different')
        self.assertIn('content', [d['kind'] for d in self.check()['drift']])
        (self.repo / 'untracked').unlink()
        result = self.check()
        self.assertIn('dirty-set', [d['kind'] for d in result['drift']])
        self.assertIn('untracked', [d['detail'] for d in result['drift'] if d['kind'] == 'content'])
        git(self.repo, 'add', '-A')
        git(self.repo, 'mv', 'tracked', 'renamed')
        details = [d['detail'] for d in self.check()['drift'] if d['kind'] == 'content']
        self.assertIn('renamed', details)
        self.assertIn('tracked', details)

    def test_missing_and_identity(self):
        artifact = self.repo / 'artifact'
        artifact.write_text('data')
        self.draft = make_draft(self.repo, artifacts=['artifact'])
        path = ct.write_checkpoint(self.draft, self.args)
        artifact.unlink()
        self.assertEqual(self.check()['missing'], ['artifact'])
        other = Path(self.tmp.name) / 'other'
        other.mkdir()
        git(other, 'init')
        self.args.repo = str(other)
        self.assertEqual(self.check(str(path))['verdict'], 'blocked')
        git(other, 'remote', 'add', 'origin', 'https://github.com/O/R')
        self.assertNotEqual(self.check(str(path))['verdict'], 'blocked')

    def test_malformed_checkpoint_types_return_invalid(self):
        path = ct.write_checkpoint(self.draft, self.args)
        original, body = ct.parse_checkpoint(path.read_text())
        cases = [('project', key, value) for key, value in (
            ('root', 1), ('worktree', []), ('git_common_dir', []),
            ('repository', []), ('branch', 1), ('head', []), ('dirty', None),
            ('dirty', [1]), ('untracked', [1]), ('dirty_digests', []),
            ('dirty_digests', {'file': 1}), ('worktrees', [{}]),
            ('default_branch', []), ('default_branch_head', 3), ('origin_ref_head', {}))]
        cases += [('context', key, value) for key, value in (
            ('occupied_tokens', []), ('window_tokens', {}), ('percent', 'bad'),
            ('basis', []), ('threshold_mode', []))]
        for group, key, value in cases:
            with self.subTest(group=group, key=key, value=value):
                meta = json.loads(json.dumps(original))
                target = meta['project'] if group == 'project' else meta['source']['context']
                target[key] = value
                path.write_text('---\n' + json.dumps(meta) + '\n---\n' + body)
                result = subprocess.run([sys.executable, ct.__file__, 'resume-check', '--json',
                                         '--repo', str(self.repo), '--store', str(self.store), str(path)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(json.loads(result.stdout)['verdict'], 'invalid')

    def test_nul_in_project_paths_is_invalid(self):
        path = ct.write_checkpoint(self.draft, self.args)
        original, body = ct.parse_checkpoint(path.read_text())
        for key in ('root', 'worktree', 'git_common_dir'):
            with self.subTest(key=key):
                meta = json.loads(json.dumps(original))
                meta['project'][key] = 'bad\x00path'
                path.write_text('---\n' + json.dumps(meta) + '\n---\n' + body)
                for command in ('validate', 'resume-check'):
                    result = subprocess.run([sys.executable, ct.__file__, command, '--json',
                                             '--repo', str(self.repo), '--store', str(self.store), str(path)],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    output = json.loads(result.stdout)
                    if command == 'validate':
                        self.assertIn('invalid project.' + key, output['errors'])
                    else:
                        self.assertEqual(output['verdict'], 'invalid')

    def test_selection_invalid_and_exit_codes(self):
        self.assertEqual(self.check()['verdict'], 'none')
        path = ct.write_checkpoint(self.draft, self.args)
        (self.store / ('latest-' + ct.slug(self.repo))).unlink()
        self.assertEqual(self.check()['verdict'], 'choose')
        self.assertIn(str(path), self.check()['candidates'])
        path.write_text('invalid')
        self.assertEqual(self.check(str(path))['verdict'], 'invalid')
        for target in ([], [str(path)]):
            result = subprocess.run([sys.executable, ct.__file__, 'resume-check', '--json',
                                     '--repo', str(self.repo), '--store', str(self.store), *target],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(json.loads(result.stdout)['verdict'], ('choose', 'invalid'))


if __name__ == '__main__':
    unittest.main()
