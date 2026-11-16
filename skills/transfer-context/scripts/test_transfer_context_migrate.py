"""Migration of legacy checkpoint stores into the default store."""
import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import transfer_context as ct
from ct_fixtures import make_draft, make_repo


class MigrateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.realpath(self.tmp.name)
        self.home = self.root + '/home'
        self.repo = make_repo(self.root)
        self.legacy = self.repo / '.git/context-transfer'
        self.legacy.mkdir()
        self.env = {'HOME': self.home, 'PATH': os.environ.get('PATH', '')}

    def write_legacy(self):
        """Write one valid checkpoint into the legacy store and return its path."""
        args = argparse.Namespace(repo=str(self.repo), store=str(self.legacy), budget=12000,
                                  statusline=False, transcript=None, rollout=None,
                                  prepare=None, refresh=None, rotate=None)
        with mock.patch.dict(os.environ, self.env, clear=True):
            return ct.write_checkpoint(make_draft(self.repo), args)

    def cli(self, *argv):
        return subprocess.run([sys.executable, ct.__file__, *argv, '--repo', str(self.repo), '--json'],
                              capture_output=True, text=True, env=self.env)

    def default_store(self):
        with mock.patch.dict(os.environ, self.env, clear=True):
            return ct._state_store(self.repo)

    def test_dry_run_reports_without_writing(self):
        path = self.write_legacy()
        done = self.cli('migrate', '--dry-run')
        self.assertEqual(done.returncode, 0, done.stderr)
        report = json.loads(done.stdout)
        self.assertTrue(report['dry_run'])
        self.assertEqual(report['copied'], [path.stem])
        self.assertFalse(self.default_store().exists())

    def test_migrate_copies_checkpoints_and_pointers_with_private_modes(self):
        path = self.write_legacy()
        pointers = sorted(p.name for p in self.legacy.glob('latest-*'))
        self.assertEqual(len(pointers), 1)
        done = self.cli('migrate')
        self.assertEqual(done.returncode, 0, done.stderr)
        report = json.loads(done.stdout)
        self.assertEqual((report['dry_run'], report['copied'], report['pointers']), (False, [path.stem], pointers))
        target = self.default_store()
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o700)
        for name in [path.name] + pointers:
            self.assertEqual((target / name).read_bytes(), (self.legacy / name).read_bytes())
            self.assertEqual(stat.S_IMODE((target / name).stat().st_mode), 0o600)
        self.assertTrue(path.exists(), 'the legacy store is left for an explicit prune')
        with mock.patch.dict(os.environ, self.env, clear=True):
            self.assertEqual(ct.resolve_store(argparse.Namespace(repo=str(self.repo), store=None)), target)
            report = ct.store_report(target, argparse.Namespace(repo=str(self.repo), store=None))
        self.assertEqual(report, 'default')

    def test_second_run_is_a_no_op_and_a_different_target_file_is_a_conflict(self):
        path = self.write_legacy()
        self.assertEqual(self.cli('migrate').returncode, 0)
        again = json.loads(self.cli('migrate').stdout)
        self.assertEqual((again['copied'], again['skipped']), ([], []))
        target = self.default_store() / path.name
        target.write_text('different')
        conflict = self.cli('migrate')
        self.assertEqual(conflict.returncode, 1)
        self.assertEqual(json.loads(conflict.stdout)['skipped'], [{'id': path.stem, 'reason': 'target differs', 'path': str(self.legacy / path.name)}])
        self.assertEqual(target.read_text(), 'different')

    def test_invalid_and_symlinked_checkpoints_are_skipped(self):
        good = self.write_legacy()
        (self.legacy / '20260101T000000Z-aaaaaaaa.md').write_text('broken')
        (self.legacy / '20260101T000000Z-bbbbbbbb.md').symlink_to(good)
        report = json.loads(self.cli('migrate').stdout)
        self.assertEqual(report['copied'], [good.stem])
        self.assertEqual(report['skipped'], [{'id': '20260101T000000Z-aaaaaaaa', 'reason': 'invalid checkpoint',
                                     'path': str(self.legacy / '20260101T000000Z-aaaaaaaa.md')}])
        self.assertEqual(sorted(p.name for p in self.default_store().glob('*.md')), [good.name])

    def test_docs_legacy_store_is_a_source_and_custom_store_is_refused(self):
        docs = self.repo / 'docs/context-transfer'
        docs.mkdir(parents=True)
        path = self.write_legacy()
        (docs / path.name).write_bytes(path.read_bytes())
        report = json.loads(self.cli('migrate', '--dry-run').stdout)
        self.assertEqual(report['copied'], [path.stem])
        self.assertEqual(sorted(report['sources']), sorted([str(self.legacy), str(docs)]))
        custom = subprocess.run([sys.executable, ct.__file__, 'migrate', '--repo', str(self.repo),
                                 '--store', self.root + '/custom', '--json'],
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(custom.returncode, 1)
        self.assertIn('default store', custom.stdout)

    def test_store_line_warns_about_skipped_legacy_checkpoints(self):
        self.write_legacy()
        (self.legacy / '20260101T000000Z-aaaaaaaa.md').write_text('broken')
        self.assertEqual(self.cli('migrate').returncode, 1)
        args = argparse.Namespace(repo=str(self.repo), store=None)
        with mock.patch.dict(os.environ, self.env, clear=True):
            report = ct.store_report(ct.resolve_store(args), args)
        self.assertTrue(report.startswith('default;'), report)
        self.assertIn('1 legacy checkpoint', report)
        self.assertIn('migrate --dry-run', report)
        skipped = json.loads(self.cli('migrate').stdout)['skipped']
        self.assertEqual(skipped[0]['path'], str(self.legacy / '20260101T000000Z-aaaaaaaa.md'))

    def test_store_line_names_the_migrate_command(self):
        self.write_legacy()
        args = argparse.Namespace(repo=str(self.repo), store=None)
        with mock.patch.dict(os.environ, self.env, clear=True):
            report = ct.store_report(ct.resolve_store(args), args)
        self.assertTrue(report.startswith('legacy (%s)' % self.legacy), report)
        self.assertIn('migrate --dry-run', report)


if __name__ == '__main__':
    unittest.main()
