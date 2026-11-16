"""Context usage sources and threshold behavior."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import transfer_context as ct


class UsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {'HOME': str(self.root), 'PATH': os.environ.get('PATH', '')}

    def run_cli(self, *args, data=None):
        return subprocess.run([sys.executable, ct.__file__, 'usage', '--repo', str(self.root),
                               '--store', str(self.root / 'store'), '--json', *args],
                              input=json.dumps(data) if data is not None else None,
                              text=True, capture_output=True, env=self.env)

    def test_statusline(self):
        window = {'context_window_size': 200000, 'used_percentage': 63,
                  'current_usage': {'input_tokens': 1000, 'cache_creation_input_tokens': 25000,
                                    'cache_read_input_tokens': 100000}, 'total_input_tokens': 9999999}
        result = self.run_cli('--statusline', data={'context_window': window})
        self.assertEqual(result.returncode, 0, result.stderr)
        usage = json.loads(result.stdout)
        self.assertEqual((usage['level'], usage['occupied_tokens'], usage['basis']),
                         ('refresh', 126000, 'statusline'))
        del window['current_usage']
        self.assertEqual(json.loads(self.run_cli('--statusline', data={'context_window': window}).stdout)['occupied_tokens'], 126000)
        window['used_percentage'] = None
        self.assertEqual(json.loads(self.run_cli('--statusline', data={'context_window': window}).stdout)['level'], 'unknown')

    def test_transcript_and_rollout(self):
        transcript = self.root / 'transcript'
        main = {'type': 'assistant', 'message': {'usage': {'input_tokens': 100000, 'cache_creation_input_tokens': 25000, 'cache_read_input_tokens': 0}}}
        side = {'type': 'assistant', 'isSidechain': True, 'message': {'usage': {'input_tokens': 999999}}}
        transcript.write_text(json.dumps(main) + '\n' + json.dumps(side) + '\n{')
        usage = json.loads(self.run_cli('--transcript', str(transcript)).stdout)
        self.assertEqual((usage['level'], usage['occupied_tokens'], usage['window_tokens'], usage['threshold_mode'], usage['basis']),
                         ('refresh', 125000, None, 'tokens', 'transcript-estimate'))
        rollout = self.root / 'rollout'
        rollout.write_text(json.dumps({'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {'last_token_usage': {'input_tokens': 100}, 'total_token_usage': {'input_tokens': 9999999}, 'model_context_window': 200000}}}) + '\n')
        usage = json.loads(self.run_cli('--rollout', str(rollout)).stdout)
        self.assertEqual((usage['level'], usage['occupied_tokens'], usage['basis']), ('ok', 100, 'codex-rollout'))
        self.assertEqual(json.loads(self.run_cli().stdout)['level'], 'unknown')

    def test_thresholds_and_config(self):
        store = self.root / 'store'
        store.mkdir()
        (store / 'config.json').write_text(json.dumps({'prepare': '30%', 'window_tokens': 200000}))
        source = {'context_window': {'used_percentage': 30, 'context_window_size': 200000}}
        self.assertEqual(json.loads(self.run_cli('--statusline', data=source).stdout)['level'], 'prepare')
        self.assertEqual(json.loads(self.run_cli('--statusline', '--prepare', '40%', data=source).stdout)['level'], 'ok')
        self.assertEqual(self.run_cli('--statusline', '--prepare', '70%', '--refresh', '60%', data=source).returncode, 2)

    def test_tokens_decide_and_percent_is_informational(self):
        # A known 1M window does not move the default token thresholds.
        source = {'context_window': {'used_percentage': 12, 'context_window_size': 1000000,
                                     'current_usage': {'input_tokens': 120000}}}
        usage = json.loads(self.run_cli('--statusline', data=source).stdout)
        self.assertEqual((usage['level'], usage['threshold_mode'], usage['percent']), ('prepare', 'tokens', 12.0))
        # Without a window the level is still decided and percent is null.
        transcript = self.root / 'transcript'
        transcript.write_text(json.dumps({'type': 'assistant', 'message': {'usage': {'input_tokens': 160000}}}) + '\n')
        usage = json.loads(self.run_cli('--transcript', str(transcript)).stdout)
        self.assertEqual((usage['level'], usage['threshold_mode'], usage['percent']), ('rotate', 'tokens', None))
        # Integer flags are tokens; a percent flag stays accepted: converted to tokens when
        # the window is known, replaced by the default token level when it is not.
        usage = json.loads(self.run_cli('--transcript', str(transcript), '--rotate', '170000').stdout)
        self.assertEqual(usage['level'], 'refresh')
        usage = json.loads(self.run_cli('--transcript', str(transcript), '--rotate', '90%').stdout)
        self.assertEqual((usage['level'], usage['threshold_mode']), ('rotate', 'tokens'))
        self.assertEqual(self.run_cli('--statusline', '--prepare', '15%', data=source).returncode, 2)
        usage = json.loads(self.run_cli('--statusline', '--prepare', '5%', data=source).stdout)
        self.assertEqual(usage['level'], 'prepare')

    def test_facts_uses_same_measurement(self):
        result = subprocess.run([sys.executable, ct.__file__, 'facts', '--repo', str(self.root), '--json', '--statusline'],
                                input=json.dumps({'context_window': {'used_percentage': 63, 'context_window_size': 200000}}),
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(json.loads(result.stdout)['context']['level'], 'refresh')


if __name__ == '__main__':
    unittest.main()
