"""Optional Claude Code hook entry points."""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from argparse import Namespace

import transfer_context as ct


def session_start(payload, args, store):
    project = ct.collect_facts(args.repo)['project']
    transfer_id = ct.read_latest(store, project['worktree'])
    if not transfer_id:
        return
    path = store / (transfer_id + '.md')
    meta, _ = ct.parse_checkpoint(path.read_text(encoding='utf-8'))
    created = datetime.datetime.fromisoformat(meta['created_at'].replace('Z', '+00:00'))
    age = max(0, int((datetime.datetime.now(datetime.timezone.utc) - created).total_seconds()))
    project = meta['project']
    print('Transfer-context checkpoint: {}\nage: {} seconds\nbranch: {}\nHEAD: {}\n'
          'Run /transfer-context resume to check the current state.'.format(
              path, age, project['branch'], project['head']))


def user_prompt_submit(payload, args, store):
    session_id = payload['session_id']
    transcript = payload['transcript_path']
    if not isinstance(session_id, str) or not session_id or not isinstance(transcript, str) or not transcript:
        return
    args.transcript = transcript
    level = ct.measure_usage(args, {}, store)['level']
    if level not in ('prepare', 'refresh', 'rotate'):
        return
    level = 'prepare' if level == 'refresh' else level
    reminders = store / 'reminders'
    if reminders.is_symlink():
        return
    reminders.mkdir(mode=0o700, exist_ok=True)
    reminders.chmod(0o700)
    marker = reminders / (hashlib.sha256(session_id.encode('utf-8')).hexdigest()[:16] + '-' + level)
    try:
        fd = os.open(str(marker), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    os.close(fd)
    message = 'Transfer-context level: {}. Use /transfer-context to save a checkpoint.'.format(level)
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit',
                                              'additionalContext': message}}))


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in ('session-start', 'user-prompt-submit'):
            return
        payload = json.load(sys.stdin)
        cwd = payload['cwd']
        if not isinstance(cwd, str) or not cwd:
            return
        args = Namespace(repo=cwd, store=None, transcript=None, rollout=None,
                               statusline=False, prepare=None, refresh=None, rotate=None)
        store = ct.resolve_store(args)
        if sys.argv[1] == 'session-start':
            session_start(payload, args, store)
        else:
            user_prompt_submit(payload, args, store)
    except Exception:
        pass


if __name__ == '__main__':
    main()
