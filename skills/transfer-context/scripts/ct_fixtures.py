"""Git fixtures for context transfer tests."""
from pathlib import Path
import os
import subprocess


def git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME='Test', GIT_AUTHOR_EMAIL='test@example.invalid',
               GIT_COMMITTER_NAME='Test', GIT_COMMITTER_EMAIL='test@example.invalid')
    return subprocess.run(['/usr/bin/git', '-C', str(repo), *args], env=env,
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def make_repo(tmp, remote=None):
    repo = Path(tmp) / 'repo'
    repo.mkdir()
    git(repo, 'init')
    (repo / 'tracked').write_text('original')
    git(repo, 'add', 'tracked')
    git(repo, 'commit', '-m', 'initial')
    (repo / 'tracked').write_text('changed')
    (repo / 'untracked').write_text('new')
    if remote:
        git(repo, 'remote', 'add', 'origin', remote)
    return repo


def make_draft(root, **overrides):
    import json
    meta = {'task': {'objective': 'Complete task', 'status': 'in-progress', 'next_action': 'next step'},
            'verification': {'status': 'unverified', 'evidence': []},
            'continuation': {'recommended_skills': [], 'blockers': [], 'pending_decisions': []},
            'artifacts': []}
    meta.update(overrides)
    sections = ('Resume prompt', 'Objective and acceptance', 'Authority and prohibitions',
                'State', 'Decisions', 'Running now', 'Pending user decisions',
                'Failed approaches', 'Verification', 'Next actions', 'Missing information')
    path = Path(root).parent / 'draft.md'
    path.write_text('---\n' + json.dumps(meta, indent=2) + '\n---\n' +
                    ''.join('\n## ' + section + '\n\nNone.\n' for section in sections))
    return path
