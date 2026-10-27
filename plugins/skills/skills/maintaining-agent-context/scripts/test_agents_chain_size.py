"""Tests for agents_chain_size.py; run standalone with `python test_agents_chain_size.py`."""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agents_chain_size as acs  # noqa: E402


def write(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = acs.main(argv)
    return code, out.getvalue()


class ChainSizeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Keep the machine's real Codex configs out of every test.
        self.home_tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.home_tmp.name)
        self.saved = (os.environ.get("CODEX_HOME"), acs.SYSTEM_CONFIG, acs.MANAGED_CONFIG)
        os.environ["CODEX_HOME"] = str(self.home)
        acs.SYSTEM_CONFIG = self.home / "etc" / "config.toml"
        acs.MANAGED_CONFIG = self.home / "etc" / "managed_config.toml"

    def tearDown(self):
        codex_home, acs.SYSTEM_CONFIG, acs.MANAGED_CONFIG = self.saved
        if codex_home is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = codex_home
        self.home_tmp.cleanup()
        self.tmp.cleanup()

    def sizes(self, **kwargs):
        return {rel: total for rel, total, _ in acs.chains(self.root, **kwargs)}

    def test_chain_sums_root_and_nested_files(self):
        write(self.root / "AGENTS.md", 100)
        write(self.root / "a" / "AGENTS.md", 30)
        write(self.root / "a" / "b" / "c" / "AGENTS.md", 7)
        self.assertEqual(self.sizes(), {".": 100, "a": 130, "a/b/c": 137})

    def test_override_masks_sibling(self):
        write(self.root / "AGENTS.md", 100)
        write(self.root / "AGENTS.override.md", 10)
        self.assertEqual(self.sizes(), {".": 10})

    def test_fallback_used_only_without_primary(self):
        write(self.root / "TEAM.md", 40)
        write(self.root / "a" / "AGENTS.md", 5)
        write(self.root / "a" / "TEAM.md", 900)
        self.assertEqual(self.sizes(), {"a": 5})
        self.assertEqual(self.sizes(fallbacks=["TEAM.md"]), {".": 40, "a": 45})

    def test_empty_file_and_skipped_dirs_ignored(self):
        write(self.root / "AGENTS.md", 0)
        write(self.root / "node_modules" / "pkg" / "AGENTS.md", 50)
        write(self.root / ".git" / "AGENTS.md", 50)
        self.assertEqual(self.sizes(), {})

    def test_exclude_prunes_subtree(self):
        write(self.root / "AGENTS.md", 10)
        write(self.root / "docs" / "evals" / "x" / "fixtures" / "AGENTS.md", 50)
        self.assertEqual(self.sizes(excludes=["docs/evals"]), {".": 10})
        self.assertEqual(self.sizes(excludes=["docs/*/x"]), {".": 10})

    def test_symlinked_directory_not_followed(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        write(Path(outside.name) / "AGENTS.md", 50)
        (self.root / "link").symlink_to(outside.name, target_is_directory=True)
        write(self.root / "AGENTS.md", 10)
        self.assertEqual(self.sizes(), {".": 10})

    def test_exit_code_reflects_budget(self):
        write(self.root / "AGENTS.md", 60)
        write(self.root / "a" / "AGENTS.md", 50)
        code, out = run([str(self.root), "--budget", "100"])
        self.assertEqual(code, 1)
        self.assertIn("OVER", out)
        self.assertIn("1 over", out)
        code, _ = run([str(self.root), "--budget", "110"])
        self.assertEqual(code, 0)

    def test_default_budget_is_codex_default(self):
        write(self.root / "AGENTS.md", 32768)
        self.assertEqual(run([str(self.root)])[0], 0)
        write(self.root / "AGENTS.md", 32769)
        self.assertEqual(run([str(self.root)])[0], 1)

    def test_invalid_input(self):
        self.assertEqual(run([str(self.root / "missing")])[0], 2)
        self.assertEqual(run([str(self.root), "--budget", "0"])[0], 2)

    def config(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def trust_root(self, level="trusted"):
        self.config(self.home / "config.toml",
                    'project_doc_max_bytes = 200\n[projects."%s"]\ntrust_level = "%s"\n'
                    % (self.root.resolve(), level))

    def test_user_config_sets_limit(self):
        write(self.root / "AGENTS.md", 150)
        self.config(self.home / "config.toml", "project_doc_max_bytes = 200\n")
        code, out = run([str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("limit 200 B (%s)" % (self.home / "config.toml"), out)

    def test_layers_override_in_codex_order(self):
        write(self.root / "AGENTS.md", 250)
        self.config(acs.SYSTEM_CONFIG, "project_doc_max_bytes = 100\n")
        self.config(self.home / "config.toml", "project_doc_max_bytes = 200\n")
        self.assertIn("limit 200 B", run([str(self.root)])[1])
        self.config(self.home / "work.config.toml", "project_doc_max_bytes = 300\n")
        code, out = run([str(self.root), "--profile", "work"])
        self.assertEqual(code, 0)
        self.assertIn("limit 300 B", out)
        self.config(acs.MANAGED_CONFIG, "project_doc_max_bytes = 50\n")
        self.assertIn("limit 50 B", run([str(self.root), "--profile", "work"])[1])

    def test_project_config_applies_only_when_trusted(self):
        write(self.root / "AGENTS.md", 250)
        self.config(self.root / ".codex" / "config.toml", "project_doc_max_bytes = 300\n")
        self.trust_root("untrusted")
        code, out = run([str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("not trusted", out)
        self.trust_root()
        code, out = run([str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("limit 300 B", out)

    def test_local_config_is_ignored(self):
        write(self.root / "AGENTS.md", 250)
        self.trust_root()
        self.config(self.root / ".codex" / "config.local.toml", "project_doc_max_bytes = 300\n")
        code, out = run([str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("config.local.toml is not read", out)

    def test_fallbacks_come_from_config_and_are_replaced(self):
        write(self.root / "a" / "NOTES.md", 10)
        write(self.root / "b" / "GUIDE.md", 10)
        self.config(acs.SYSTEM_CONFIG, 'project_doc_fallback_filenames = ["NOTES.md"]\n')
        self.config(self.home / "config.toml", 'project_doc_fallback_filenames = [" GUIDE.md ", ""]\n')
        out = run([str(self.root)])[1]
        self.assertIn("b/GUIDE.md", out)
        self.assertNotIn("NOTES.md", out)

    def test_explicit_budget_wins(self):
        write(self.root / "AGENTS.md", 150)
        self.config(self.home / "config.toml", "project_doc_max_bytes = 100\n")
        code, out = run([str(self.root), "--budget", "200"])
        self.assertEqual(code, 0)
        self.assertIn("limit 200 B (--budget)", out)

    def test_broken_config_names_file_without_values(self):
        write(self.root / "AGENTS.md", 10)
        self.config(self.home / "config.toml", 'token = "s3cret"\n[features]\n[features]\n')
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = acs.main([str(self.root)])
        self.assertEqual(code, 2)
        self.assertIn("config.toml", err.getvalue())
        self.assertNotIn("s3cret", out.getvalue() + err.getvalue())

    # 20261024-2348: a notes folder the root imports with @ is not a Codex chain.

    def test_imported_notes_folder_is_not_a_codex_chain(self):
        (self.root / "AGENTS.md").write_text("# Root\n\nNotes: @docs/notes/AGENTS.md\n")
        write(self.root / "docs" / "notes" / "AGENTS.md", 500)
        code, out = run([str(self.root), "--budget", "200"])
        self.assertEqual(code, 0, out)
        self.assertNotIn("OVER", out)
        self.assertIn("import (Claude Code): +500 B  docs/notes", out)
        self.assertIn("1 chain(s), 0 over", out)

    def test_session_learnings_folder_is_outside_the_budget_without_import(self):
        write(self.root / "AGENTS.md", 10)
        write(self.root / "docs" / "session-learnings" / "AGENTS.md", 500)
        code, out = run([str(self.root), "--budget", "200"])
        self.assertEqual(code, 0, out)
        self.assertIn("notes (session-learnings): +500 B  docs/session-learnings", out)

    def test_import_in_claude_md_counts(self):
        write(self.root / "AGENTS.md", 10)
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n@docs/notes/AGENTS.md\n")
        write(self.root / "docs" / "notes" / "AGENTS.md", 500)
        code, out = run([str(self.root), "--budget", "200"])
        self.assertEqual(code, 0, out)
        self.assertIn("import (Claude Code): +500 B  docs/notes", out)

    def test_quoted_or_punctuated_import_is_still_a_chain(self):
        # Claude Code expands neither, so the folder loads only as a nested Codex file.
        (self.root / "AGENTS.md").write_text(
            "See `@docs/a/AGENTS.md` and @docs/b/AGENTS.md;\n")
        write(self.root / "docs" / "a" / "AGENTS.md", 500)
        write(self.root / "docs" / "b" / "AGENTS.md", 500)
        code, out = run([str(self.root), "--budget", "200"])
        self.assertEqual(code, 1, out)
        self.assertNotIn("import (Claude Code)", out)
        self.assertIn("3 chain(s), 2 over", out)

    def test_folder_without_import_stays_a_chain(self):
        write(self.root / "AGENTS.md", 10)
        write(self.root / "docs" / "notes" / "AGENTS.md", 500)
        code, out = run([str(self.root), "--budget", "200"])
        self.assertEqual(code, 1, out)
        self.assertIn("OVER", out)

    def test_reads_only(self):
        write(self.root / "AGENTS.md", 10)
        before = sorted(p.as_posix() for p in self.root.rglob("*"))
        run([str(self.root)])
        self.assertEqual(sorted(p.as_posix() for p in self.root.rglob("*")), before)


if __name__ == "__main__":
    unittest.main()
