"""Checkpoint listing and retention tests."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import transfer_context as ct
from ct_fixtures import make_draft, make_repo


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name)
        self.other = Path(self.tmp.name) / 'other'
        self.other.mkdir()
        self.store = Path(self.tmp.name) / 'store'
        self.args = SimpleNamespace(repo=str(self.repo), store=str(self.store), budget=12000,
                                    statusline=False, transcript=None, rollout=None,
                                    prepare=None, refresh=None, rotate=None)
        self.draft = make_draft(self.repo)

    def checkpoints(self):
        paths = []
        for repo, count in ((self.repo, 3), (self.other, 2)):
            self.args.repo = str(repo)
            for i in range(count):
                self.draft.write_text(self.draft.read_text().replace('"next_action": "next step"',
                                      '"next_action": "step %s"' % len(paths)))
                with patch.object(ct.os, "urandom", return_value=len(paths).to_bytes(4, "big")):
                    path = ct.write_checkpoint(self.draft, self.args)
                paths.append(path)
                self.draft.write_text(self.draft.read_text().replace('"next_action": "step %s"' % (len(paths)-1),
                                      '"next_action": "next step"'))
        self.args.repo = str(self.repo)
        return paths

    def cli(self, *args):
        return subprocess.run([sys.executable, ct.__file__, *args, '--repo', str(self.repo),
                               '--store', str(self.store), '--json'], capture_output=True, text=True)

    def test_listing_and_prune(self):
        paths = self.checkpoints()
        entries = ct.list_checkpoints(self.store)
        self.assertEqual(len(entries), 5)
        self.assertEqual(sum(not e['unlinked'] for e in entries), 2)
        self.assertTrue(all(e['validation'] == 'ok' for e in entries))
        self.assertTrue(all({'id', 'created_at', 'worktree', 'branch', 'head'} <= set(e) for e in entries))
        for argv in (('prune',), ('prune', '--keep', '0')):
            self.assertEqual(self.cli(*argv).returncode, 2)
            self.assertEqual(len(list(self.store.glob('*.md'))), 5)
        self.assertEqual(self.cli('prune', '--keep', '1').returncode, 0)
        self.assertTrue(paths[2].exists())
        self.assertTrue(all(p.exists() for p in paths[3:]))
        self.assertEqual(len(list(self.store.glob('*.md'))), 3)
        (self.store / 'latest-dangling').write_text('20200101T000000Z-12345678')
        self.assertEqual(self.cli('prune', '--keep', '1', '--all').returncode, 0)
        self.assertTrue(paths[4].exists())
        self.assertEqual(len(list(self.store.glob('*.md'))), 2)
        result = self.cli('list')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(json.loads(result.stdout)['checkpoints']), 2)

    def test_invalid_checkpoint_and_protected_old_pointer(self):
        paths = self.checkpoints()
        (self.store / 'latest-extra').write_text(paths[0].stem)
        paths[1].write_text('broken')
        entries = ct.list_checkpoints(self.store)
        self.assertNotEqual(next(e for e in entries if e['id'] == paths[1].stem)['validation'], 'ok')
        self.assertNotIn(paths[0], ct.prune(self.store, 1, True, str(self.repo)))
        self.assertTrue(paths[0].exists())


if __name__ == '__main__':
    unittest.main()
