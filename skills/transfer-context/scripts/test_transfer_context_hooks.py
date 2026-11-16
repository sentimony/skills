"""Claude hook behavior through its command-line interface."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import transfer_context as ct
from ct_fixtures import make_repo, make_draft

HOOK = Path(__file__).with_name('transfer_context_hooks.py')


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(self.tmp.name)
        self.store = Path(self.tmp.name) / 'store'
        self.env = dict(os.environ, CONTEXT_TRANSFER_DIR=str(self.store))
        self.args = SimpleNamespace(repo=str(self.repo), store=str(self.store), budget=12000,
                                    statusline=False, transcript=None, rollout=None,
                                    prepare=None, refresh=None, rotate=None)

    def invoke(self, command, payload):
        result = subprocess.run([sys.executable, '-B', str(HOOK), command], input=json.dumps(payload),
                                text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        return result.stdout

    def test_session_start_only_prints_metadata(self):
        payload = {'cwd': str(self.repo), 'source': 'startup'}
        self.assertEqual(self.invoke('session-start', payload), '')
        draft = make_draft(self.repo)
        draft.write_text(draft.read_text().replace('None.', 'SECRET BODY CONTENT'))
        path = ct.write_checkpoint(draft, self.args)
        meta, _ = ct.parse_checkpoint(path.read_text())
        output = self.invoke('session-start', payload)
        for value in (str(path), meta['project']['branch'], meta['project']['head'],
                      '/transfer-context resume', 'age'):
            self.assertIn(value, output)
        self.assertNotIn('SECRET BODY CONTENT', output)

    def test_reminders_once_per_session_and_level(self):
        transcript = Path(self.tmp.name) / 'transcript.jsonl'
        payload = {'cwd': str(self.repo), 'session_id': 'session-a', 'transcript_path': str(transcript)}
        def usage(tokens):
            transcript.write_text(json.dumps({'type': 'assistant', 'message': {'usage': {'input_tokens': tokens}}}) + '\n')
        def context(output):
            return json.loads(output)['hookSpecificOutput']['additionalContext']
        usage(110000)
        self.assertIn('prepare', context(self.invoke('user-prompt-submit', payload)))
        self.assertEqual(self.invoke('user-prompt-submit', payload), '')
        usage(130000)
        self.assertEqual(self.invoke('user-prompt-submit', payload), '')
        usage(160000)
        self.assertIn('rotate', context(self.invoke('user-prompt-submit', payload)))
        self.assertEqual(self.invoke('user-prompt-submit', payload), '')
        payload['session_id'] = 'session-b'
        self.assertIn('rotate', context(self.invoke('user-prompt-submit', payload)))

    def test_bad_input_is_silent(self):
        self.assertEqual(self.invoke('user-prompt-submit', {}), '')
        result = subprocess.run([sys.executable, '-B', str(HOOK), 'session-start'], input='{',
                                text=True, capture_output=True, env=self.env)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))


if __name__ == '__main__':
    unittest.main()
