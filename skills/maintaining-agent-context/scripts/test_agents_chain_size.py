"""Tests for agents_chain_size.py; run standalone with `python test_agents_chain_size.py`."""

import contextlib
import io
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

    def tearDown(self):
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

    def test_reads_only(self):
        write(self.root / "AGENTS.md", 10)
        before = sorted(p.as_posix() for p in self.root.rglob("*"))
        run([str(self.root)])
        self.assertEqual(sorted(p.as_posix() for p in self.root.rglob("*")), before)


if __name__ == "__main__":
    unittest.main()
