"""Exercise the actual CI frontmatter step against isolated catalog fixtures."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/ci.yml'


def ci_step():
    text = WORKFLOW.read_text(encoding='utf-8')
    start = text.index('      - name: Validate SKILL.md frontmatter\n')
    start = text.index('        run: |\n', start) + len('        run: |\n')
    end = text.find('\n      - ', start)
    if end == -1:
        end = len(text)
    step = textwrap.dedent(text[start:end])
    return step.replace("python - <<'EOF'", f"{shlex.quote(sys.executable)} - <<'EOF'", 1)


class FrontmatterStepTests(unittest.TestCase):
    def run_fixture(self, groups, skills, extra_files=()):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'skills.sh.json').write_text(json.dumps({'groupings': groups}))
            for name, content in skills.items():
                path = root / 'skills' / name / 'SKILL.md'
                path.parent.mkdir(parents=True)
                path.write_text(content)
            extras = extra_files.items() if isinstance(extra_files, dict) else ((name, 'extra') for name in extra_files)
            for name, content in extras:
                path = root / 'skills' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            return subprocess.run(['bash', '-e', '-c', ci_step()], cwd=root,
                                  text=True, capture_output=True)

    def test_renamed_notice_passes_with_minimal_frontmatter(self):
        result = self.run_fixture([{'title': 'Renamed skills', 'skills': ['old']}],
                                  {'old': '---\nname: old\ndescription: Renamed notice\n---\nNotice.\n'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_renamed_notice_rejects_forbidden_frontmatter(self):
        for field in ('license: MIT', '"license": MIT', 'metadata:\n  version: "1.2.3"',
                      'metadata: {version: "1.2.3"}', '"metadata": {"version": "1.2.3"}'):
            with self.subTest(field=field):
                content = f'---\nname: old\ndescription: Notice\n{field}\n---\nNotice.\n'
                result = self.run_fixture([{'title': 'Renamed skills', 'skills': ['old']}],
                                          {'old': content})
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('renamed notice must not declare', result.stdout)

    def test_renamed_notice_rejects_extra_files(self):
        for extra in ('old/LICENSE', 'old/CHANGELOG.md', 'old/scripts/run.py', 'old/notes.txt'):
            with self.subTest(extra=extra):
                result = self.run_fixture([{'title': 'Renamed skills', 'skills': ['old']}],
                                          {'old': '---\nname: old\ndescription: Notice\n---\nNotice.\n'},
                                          (extra,))
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('renamed notice must contain only', result.stdout)

    def test_ordinary_skill_with_required_fields_passes(self):
        result = self.run_fixture([{'title': 'Skills', 'skills': ['new']}],
                                  {'new': '---\nname: new\ndescription: Fixture\nmetadata:\n  version: "1.2.3"\nlicense: MIT\n---\nContent.\n'},
                                  {'new/LICENSE': 'MIT', 'new/CHANGELOG.md': '## [1.2.3] - 2026-11-05\n'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ordinary_skill_without_required_fields_fails(self):
        result = self.run_fixture([{'title': 'Skills', 'skills': ['old']}],
                                  {'old': '---\nname: old\ndescription: Fixture\n---\nContent.\n'})
        self.assertNotEqual(result.returncode, 0)
        for required in ('metadata.version', "'license'", 'missing LICENSE', 'missing CHANGELOG.md'):
            self.assertIn(required, result.stdout)

    def test_other_group_does_not_grant_exemption(self):
        result = self.run_fixture([{'title': 'Renamed skill', 'skills': ['old']}],
                                  {'old': '---\nname: old\ndescription: Fixture\n---\nNotice.\n'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('metadata.version', result.stdout)

    def test_renamed_notice_still_validates_argument_hint(self):
        result = self.run_fixture([{'title': 'Renamed skills', 'skills': ['old']}],
                                  {'old': '---\nname: old\ndescription: Fixture\nargument-hint: "[bad"\n---\nNotice.\n'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('argument-hint', result.stdout)

    def test_renamed_notice_still_requires_name_and_description(self):
        result = self.run_fixture([{'title': 'Renamed skills', 'skills': ['old']}],
                                  {'old': '---\nname: wrong\n---\nNotice.\n'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("!= directory", result.stdout)
        self.assertIn("missing 'description'", result.stdout)


if __name__ == '__main__':
    unittest.main()
