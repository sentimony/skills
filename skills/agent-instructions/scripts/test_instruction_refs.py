"""Tests for instruction_refs.py; run standalone with `python test_instruction_refs.py`."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instruction_refs as ir  # noqa: E402


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = ir.main(argv)
    return code, out.getvalue()


class InstructionRefsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def agents(self, text, where="AGENTS.md"):
        write(self.root / where, text)
        return run([str(self.root)])

    def test_existing_path_is_ok_and_missing_is_broken(self):
        write(self.root / "docs" / "a.md")
        code, out = self.agents("See `docs/a.md` and `docs/missing.md`.\n")
        self.assertEqual(code, 1)
        self.assertIn("broken AGENTS.md:1  `docs/missing.md`", out)
        self.assertNotIn("docs/a.md`  -", out)
        self.assertIn("ok 1", out)

    def test_path_resolves_relative_to_instruction_folder(self):
        write(self.root / "pkg" / "notes.md")
        write(self.root / "pkg" / "AGENTS.md", "Read `notes.md`.\n")
        code, out = run([str(self.root)])
        self.assertEqual(code, 0, out)

    def test_bare_name_found_deeper_is_ok_by_suffix(self):
        write(self.root / "src" / "deep" / "teamModes.ts")
        code, out = self.agents("Edit `teamModes.ts`.\n")
        self.assertEqual(code, 0, out)

    def test_several_suffix_matches_are_ambiguous_not_broken(self):
        write(self.root / "a" / "setup.sh")
        write(self.root / "b" / "setup.sh")
        code, out = self.agents("Run `setup.sh`.\n")
        self.assertEqual(code, 0)
        self.assertIn("ambiguous AGENTS.md:1", out)

    def test_route_is_skipped_not_broken(self):
        code, out = self.agents("Open `/login` and `/exports/issues`.\n")
        self.assertEqual(code, 0)
        self.assertIn("skipped (route) 2", out)

    def test_external_repo_url_home_and_pattern_are_skipped(self):
        code, out = self.agents(
            "`io/exports` `https://x.dev/a.md` `~/.codex/AGENTS.md` "
            "`data/*.json` `docs/<name>.md` `git@host:o/r.git`\n")
        self.assertEqual(code, 0, out)
        for kind in ("external repo", "url", "home", "pattern"):
            self.assertIn("skipped (%s)" % kind, out)

    def test_gitignored_and_generated_dirs_are_skipped(self):
        write(self.root / ".gitignore", ".auth/\n")
        code, out = self.agents("Uses `.auth/state.json` and `coverage/index.html`.\n")
        self.assertEqual(code, 0, out)
        self.assertIn("skipped (gitignored) 1", out)
        self.assertIn("skipped (generated) 1", out)

    def test_package_script_checked_against_nearest_package_json(self):
        write(self.root / "package.json", json.dumps({"scripts": {"build": "x"}}))
        code, out = self.agents("Run `pnpm run build`, then `npm run lint`.\n")
        self.assertEqual(code, 1)
        self.assertIn("no script 'lint'", out)
        self.assertNotIn("'build'", out)

    def test_nested_instruction_uses_nested_package_json(self):
        write(self.root / "package.json", json.dumps({"scripts": {"root": "x"}}))
        write(self.root / "app" / "package.json", json.dumps({"scripts": {"dev": "x"}}))
        write(self.root / "app" / "AGENTS.md", "`yarn run dev` and `yarn run root`\n")
        code, out = run([str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("no script 'root'", out)
        self.assertNotIn("'dev'", out)

    def test_workspace_filter_is_skipped(self):
        code, out = self.agents("`pnpm --filter web run dev`\n")
        self.assertEqual(code, 0, out)
        self.assertIn("skipped (workspace filter) 1", out)

    def test_make_target_checked_against_makefile(self):
        write(self.root / "Makefile", ".PHONY: test\ntest:\n\techo\n")
        code, out = self.agents("`make test` and `make deploy`\n")
        self.assertEqual(code, 1)
        self.assertIn("no target 'deploy'", out)
        self.assertNotIn("'test'", out)

    def test_fenced_command_lines_are_checked_but_fenced_paths_are_not(self):
        write(self.root / "package.json", json.dumps({"scripts": {}}))
        code, out = self.agents("```bash\npnpm run nope\ncat docs/missing.md\n```\n")
        self.assertEqual(code, 1)
        self.assertIn("broken AGENTS.md:2", out)
        self.assertNotIn("missing.md", out)

    def test_exclude_prunes_tree_and_exit_codes(self):
        write(self.root / "fixtures" / "AGENTS.md", "`nope/missing.md`\n")
        self.assertEqual(run([str(self.root)])[0], 1)
        self.assertEqual(run([str(self.root), "--exclude", "fixtures"])[0], 0)
        self.assertEqual(run([str(self.root / "absent")])[0], 2)

    def test_import_line_resolves(self):
        write(self.root / "AGENTS.md", "x\n")
        write(self.root / "CLAUDE.md", "`@AGENTS.md`\n")
        code, out = run([str(self.root)])
        self.assertEqual(code, 0, out)

    def test_reads_only(self):
        write(self.root / "AGENTS.md", "`a/b.md`\n")
        before = sorted(p.as_posix() for p in self.root.rglob("*") if ".git/" not in p.as_posix())
        run([str(self.root)])
        after = sorted(p.as_posix() for p in self.root.rglob("*") if ".git/" not in p.as_posix())
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
