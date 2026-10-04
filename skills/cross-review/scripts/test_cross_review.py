"""Standalone unit tests for cross_review command adapters and loop guard."""

import hashlib
import io
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cross_review as cr  # noqa: E402

SESSION = "11111111-1111-4111-8111-111111111111"
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cross_review.py")
ARTIFACTS = ("brief.md", "review.md", "session.txt", "run.log")


def expected_claude(model="claude-opus-5-5", effort="medium"):
    # Literal list on purpose: never derive expectations from production constants.
    return [
        "claude", "-p", "--output-format", "json", "--model", model, "--effort", effort,
        "--permission-mode", "default", "--tools", "Read,Grep,Glob",
        "--allowedTools", "Read,Grep,Glob", "--disallowedTools",
        "Write,Edit,NotebookEdit,Bash,Agent,Skill,mcp__*",
        "--strict-mcp-config", "--disable-slash-commands", "--safe-mode",
        "--restricted", "--setting-sources", "",
        "--session-id", SESSION,
    ]


def trust_token(*paths):
    # Hand-written TOML; the test paths contain no quote or backslash.
    return "projects={%s}" % ", ".join('"%s"={trust_level="untrusted"}' % p for p in paths)


def expected_codex(repo, run, model="gpt-6.1-sol", effort="low", trust=None):
    return [
        "codex", "exec", "--json", "-s", "read-only", "-m", model,
        "-c", 'model_reasoning_effort="%s"' % effort,
        "-c", trust or trust_token(Path(repo).resolve()),
        "-C", str(repo), "-o", str(run / "review.md"), "-",
    ]


class GuardTests(unittest.TestCase):
    def test_depth_blocks(self):
        with self.assertRaises(cr.CrossReviewError) as caught:
            cr.ensure_not_nested({"CROSS_REVIEW_DEPTH": "1"})
        self.assertEqual(caught.exception.code, 20)

    def test_empty_depth_also_blocks(self):
        with self.assertRaises(cr.CrossReviewError) as caught:
            cr.ensure_not_nested({"CROSS_REVIEW_DEPTH": ""})
        self.assertEqual(caught.exception.code, 20)

    def test_absent_depth_passes(self):
        self.assertIsNone(cr.ensure_not_nested({"PATH": "/usr/bin"}))

    def test_child_inherits_depth_without_mutating_parent(self):
        parent = {"TASK_SENTINEL": "present"}
        cr.ensure_not_nested(parent)
        child = cr.reviewer_environment(parent)
        self.assertEqual(child["CROSS_REVIEW_DEPTH"], "1")
        self.assertEqual(child["TASK_SENTINEL"], "present")
        self.assertNotIn("CROSS_REVIEW_DEPTH", parent)

    def test_child_environment_keeps_host_markers(self):
        # Task 1 probe showed no host-marker scrub is needed for nested claude -p.
        parent = {"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli", "HOME": "/h"}
        child = cr.reviewer_environment(parent)
        self.assertEqual(child, dict(parent, CROSS_REVIEW_DEPTH="1"))


class ConstantsTests(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(cr.DEFAULTS, {"codex": ("gpt-6.1-sol", "low"),
                                       "claude": ("claude-opus-5-5", "medium")})

    def test_exit_codes(self):
        self.assertEqual(
            (cr.EXIT_OK, cr.EXIT_INVALID_INPUT, cr.EXIT_NESTED, cr.EXIT_MISSING_CLI,
             cr.EXIT_REVIEWER_FAILED, cr.EXIT_EMPTY_RESULT, cr.EXIT_NO_SESSION,
             cr.EXIT_INTERRUPTED),
            (0, 2, 20, 21, 22, 23, 24, 130),
        )

    def test_error_carries_code_and_message(self):
        err = cr.CrossReviewError(23, "empty")
        self.assertEqual((err.code, err.message), (23, "empty"))


class ArgvTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.repo = base / "my repo"
        self.repo.mkdir()
        self.run = base / "run dir"

    def tearDown(self):
        self._tmp.cleanup()

    def build(self, reviewer, model, effort, repo=None):
        repo = repo or self.repo
        return cr.build_run_command(reviewer, repo, self.run, model, effort, SESSION,
                                    untrusted=[str(repo.resolve())])

    def test_claude_run_security_argv(self):
        self.assertEqual(self.build("claude", "claude-opus-5-5", "medium"),
                         expected_claude())

    def test_claude_override_changes_only_model_and_effort(self):
        self.assertEqual(self.build("claude", "claude-sonnet-x", "high"),
                         expected_claude("claude-sonnet-x", "high"))

    def test_codex_run_argv(self):
        self.assertEqual(self.build("codex", "gpt-6.1-sol", "low"),
                         expected_codex(self.repo, self.run))

    def test_codex_override_changes_only_model_and_effort(self):
        self.assertEqual(self.build("codex", "gpt-other", "high"),
                         expected_codex(self.repo, self.run, "gpt-other", "high"))

    def test_paths_with_spaces_stay_single_tokens(self):
        argv = self.build("codex", "gpt-6.1-sol", "low")
        self.assertIn(str(self.repo), argv)
        self.assertIn(str(self.run / "review.md"), argv)

    def test_shell_metacharacters_are_literal(self):
        repo = self.repo.parent / "r; rm -rf $HOME `x` | & >out"
        repo.mkdir()
        argv = self.build("codex", "m;$(id)", "e|x", repo=repo)
        self.assertEqual(argv, expected_codex(repo, self.run, "m;$(id)", "e|x"))
        self.assertTrue(all(isinstance(token, str) for token in argv))

    def test_returns_fresh_list(self):
        first = self.build("claude", "claude-opus-5-5", "medium")
        first.append("--dangerously-skip-permissions")
        self.assertEqual(self.build("claude", "claude-opus-5-5", "medium"),
                         expected_claude())

    def assertInvalid(self, *args, **kwargs):
        with self.assertRaises(cr.CrossReviewError) as caught:
            cr.build_run_command(*args, **kwargs)
        self.assertEqual(caught.exception.code, 2)

    def test_invalid_reviewer(self):
        for reviewer in ("gemini", "", "Codex"):
            self.assertInvalid(reviewer, self.repo, self.run, "m", "e", SESSION)

    def test_empty_model_or_effort(self):
        for reviewer in ("codex", "claude"):
            self.assertInvalid(reviewer, self.repo, self.run, "", "low", SESSION)
            self.assertInvalid(reviewer, self.repo, self.run, "m", "", SESSION)
            self.assertInvalid(reviewer, self.repo, self.run, "  ", "low", SESSION)

    def test_codex_effort_cannot_escape_toml_string(self):
        self.assertInvalid("codex", self.repo, self.run, "m", 'low" x="y', SESSION)

    def test_missing_repo(self):
        missing = self.repo.parent / "absent repo"
        for reviewer in ("codex", "claude"):
            self.assertInvalid(reviewer, missing, self.run, "m", "e", SESSION)

    def test_claude_requires_uuid_session(self):
        self.assertInvalid("claude", self.repo, self.run, "m", "e", "not-a-uuid")

    def test_option_like_model_or_effort(self):
        for reviewer in ("codex", "claude"):
            self.assertInvalid(reviewer, self.repo, self.run,
                               "--dangerously-skip-permissions", "low", SESSION)
            self.assertInvalid(reviewer, self.repo, self.run, "m", "-x", SESSION)

    def test_codex_trust_override_is_exact_literal(self):
        argv = cr.build_run_command("codex", self.repo, self.run, "m", "e", SESSION,
                                    untrusted=["/a b", "/c"])
        i = argv.index("-C")
        self.assertEqual(argv[i - 2:i], [
            "-c", 'projects={"/a b"={trust_level="untrusted"}, '
                  '"/c"={trust_level="untrusted"}}'])

    def test_codex_trust_path_with_quote_is_escaped(self):
        argv = cr.build_run_command("codex", self.repo, self.run, "m", "e", SESSION,
                                    untrusted=['/r "x" \\y'])
        self.assertIn('projects={"/r \\"x\\" \\\\y"={trust_level="untrusted"}}', argv)

    def test_codex_trust_path_with_non_bmp_character_stays_raw(self):
        argv = cr.build_run_command("codex", self.repo, self.run, "m", "e", SESSION,
                                    untrusted=["/r \U0001f600 \u0436"])
        self.assertIn(trust_token("/r \U0001f600 \u0436"), argv)

    def test_codex_trust_path_with_control_character_is_rejected(self):
        for bad in ("/r\nx", "/r\tx", "/r\x7fx", "/r\x00x"):
            with self.subTest(path=bad):
                self.assertInvalid("codex", self.repo, self.run, "m", "e", SESSION,
                                   untrusted=[bad])
                with self.assertRaises(cr.CrossReviewError) as caught:
                    cr.build_resume_command("codex", self.repo, self.run, "m", "e",
                                            SESSION, untrusted=[bad])
                self.assertEqual(caught.exception.code, 2)

    def test_codex_default_computes_trust_paths_for_run_and_resume(self):
        with mock.patch.object(cr, "codex_untrusted_paths",
                               return_value=["/x", "/y"]) as helper:
            run = cr.build_run_command("codex", self.repo, self.run, "m", "e", SESSION)
            resume = cr.build_resume_command("codex", self.repo, self.run, "m", "e",
                                             SESSION)
        self.assertEqual(helper.call_count, 2)
        for argv in (run, resume):
            self.assertIn(trust_token("/x", "/y"), argv)


class SafetyMutantTests(unittest.TestCase):
    """Mutate the production policy constants and prove the literal argv tests notice.

    Each case patches a production constant with one safety token removed and checks
    that the builders' output no longer equals the literal expected argv, which is
    exactly the comparison the argv tests make.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.run = self.repo / "run"

    def tearDown(self):
        self._tmp.cleanup()

    def claude_outputs(self):
        return (cr.build_run_command("claude", self.repo, self.run, "claude-opus-5-5",
                                     "medium", SESSION),
                cr.build_resume_command("claude", self.repo, self.run, "claude-opus-5-5",
                                        "medium", SESSION))

    def codex_outputs(self):
        trust = [str(self.repo.resolve())]
        return (cr.build_run_command("codex", self.repo, self.run, "gpt-6.1-sol", "low",
                                     SESSION, untrusted=trust),
                cr.build_resume_command("codex", self.repo, self.run, "gpt-6.1-sol", "low",
                                        SESSION, untrusted=trust))

    def test_unmutated_policy_matches_literals(self):
        self.assertEqual(self.claude_outputs(),
                         (expected_claude(), expected_claude_resume(SESSION)))
        self.assertEqual(self.codex_outputs(),
                         (expected_codex(self.repo, self.run),
                          expected_codex_resume(self.run, SESSION, repo=self.repo)))

    def test_claude_policy_mutants_break_literal_equality(self):
        policy = list(cr._CLAUDE_POLICY)

        def without(flag, pair):
            i = policy.index(flag)
            return tuple(policy[:i] + policy[i + (2 if pair else 1):])

        deny = policy.index("--disallowedTools") + 1
        weak_deny = list(policy)
        weak_deny[deny] = weak_deny[deny].replace(",mcp__*", "")
        mutants = {
            "--tools": without("--tools", True),
            "--allowedTools": without("--allowedTools", True),
            "--disallowedTools": without("--disallowedTools", True),
            "--permission-mode": without("--permission-mode", True),
            "--strict-mcp-config": without("--strict-mcp-config", False),
            "--disable-slash-commands": without("--disable-slash-commands", False),
            "--safe-mode": without("--safe-mode", False),
            "--restricted": without("--restricted", False),
            "--setting-sources": without("--setting-sources", True),
            "deny pattern": tuple(weak_deny),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name), mock.patch.object(cr, "_CLAUDE_POLICY", mutant):
                run, resume = self.claude_outputs()
                self.assertNotEqual(run, expected_claude())
                self.assertNotEqual(resume, expected_claude_resume(SESSION))

    def test_codex_sandbox_mutants_break_literal_equality(self):
        with mock.patch.object(cr, "_CODEX_RUN_SANDBOX", ()):
            self.assertNotEqual(self.codex_outputs()[0], expected_codex(self.repo, self.run))
        with mock.patch.object(cr, "_CODEX_RESUME_SANDBOX", ()):
            self.assertNotEqual(self.codex_outputs()[1],
                                expected_codex_resume(self.run, SESSION, repo=self.repo))

    def test_codex_trust_mutants_break_literal_equality(self):
        expected = (expected_codex(self.repo, self.run),
                    expected_codex_resume(self.run, SESSION, repo=self.repo))
        trusted = 'projects={%s={trust_level="trusted"}}'
        for name, mutant in {
                "no override": lambda paths: None,
                "trusted": lambda paths: trusted % json.dumps(paths[0])}.items():
            with self.subTest(mutant=name), \
                    mock.patch.object(cr, "_codex_untrusted_override", mutant):
                run, resume = self.codex_outputs()
                self.assertNotEqual(run, expected[0])
                self.assertNotEqual(resume, expected[1])


class SessionParserTests(unittest.TestCase):
    def test_parses_thread_started(self):
        log = json.dumps({"type": "thread.started", "thread_id": PROBE_THREAD}) + "\n"
        self.assertEqual(cr.parse_codex_session(log), PROBE_THREAD)

    def test_text_header_is_not_a_session(self):
        self.assertIsNone(cr.parse_codex_session("session id: %s\n" % PROBE_THREAD))

    def test_absent_returns_none(self):
        self.assertIsNone(cr.parse_codex_session("no metadata here\n"))
        self.assertIsNone(cr.parse_codex_session(""))

    def test_decoys_after_the_first_event_are_ignored(self):
        self.assertEqual(cr.parse_codex_session(PROBE_CODEX_LOG), PROBE_THREAD)

    def test_runner_header_is_skipped(self):
        log = json.dumps({"schema_version": 1, "thread_id": PROBE_THREAD}) + "\n"
        self.assertIsNone(cr.parse_codex_session(log))


# Real shapes captured on 2026-10-04 (codex-cli 0.160.0, Claude Code 2.1.289).
PROBE_THREAD = "01a10896-8bf2-7772-96bf-d48579639203"
PROBE_CODEX_TOKENS = {"input": 48668, "cached_input": 45056, "cache_write": 0,
                      "output": 213, "reasoning": 41}
PROBE_CLAUDE_TOKENS = {"input": 2648, "cached_input": 531, "cache_write": 2115,
                       "output": 4, "reasoning": 0}


def codex_turn(input_tokens, cached, output, reasoning, cache_write=0):
    return json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": input_tokens, "cached_input_tokens": cached,
        "cache_write_input_tokens": cache_write, "output_tokens": output,
        "reasoning_output_tokens": reasoning}})


PROBE_CODEX_LOG = "\n".join([
    json.dumps({"schema_version": 1, "reviewer": "codex"}),
    "Reading prompt from stdin...",
    json.dumps({"type": "thread.started", "thread_id": PROBE_THREAD}),
    json.dumps({"type": "turn.started"}),
    json.dumps({"type": "item.completed", "item": {
        "id": "item_2", "type": "command_execution",
        "command": "/bin/zsh -lc 'cat demo/skills/sample/SKILL.md'",
        "exit_code": 0, "status": "completed"}}),
    json.dumps({"type": "item.completed", "item": {
        "id": "item_3", "type": "agent_message",
        "text": "see /x/skills/decoy/SKILL.md and session 0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5c"}}),
    codex_turn(48668, 45056, 213, 41),
    json.dumps({"type": "thread.started", "thread_id": "0199a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5c"}),
]) + "\n"

PROBE_CLAUDE_OUTPUT = json.dumps({
    "type": "result", "subtype": "success", "is_error": False,
    "result": "Target reviewed: fixture\nCoverage: complete\n",
    "total_cost_usd": 0.0171142,
    "modelUsage": {"claude-opus-5-5": {
        "inputTokens": 2, "outputTokens": 4, "cacheReadInputTokens": 531,
        "cacheCreationInputTokens": 2115, "thinkingTokens": 0, "costUSD": 0.0171142}},
})


class UsageTests(unittest.TestCase):
    def test_prices_are_the_published_table(self):
        self.assertEqual(cr.PRICES_AS_OF, "2026-10-04")
        self.assertEqual(cr.PRICES, {
            "gpt-6.1-sol": (2.00, 0.10, 10.00),
            "gpt-6-sol": (2.00, 0.20, 10.00),
            "gpt-6-astra": (10.00, 1.00, 50.00),
            "gpt-6-luna": (0.10, 0.01, 0.50),
            "gpt-5.3-codex": (1.75, 0.175, 14.00),
        })

    def test_codex_events_give_session_tokens_and_skills(self):
        events = cr.parse_codex_events(PROBE_CODEX_LOG)
        self.assertEqual(events, {"session": PROBE_THREAD, "tokens": PROBE_CODEX_TOKENS,
                                  "skills": ["sample"], "usage_error": None})

    def test_codex_turn_without_core_counts_makes_tokens_unknown(self):
        for usage in ({}, {"input_tokens": 10}, {"input_tokens": "10", "output_tokens": 1}):
            with self.subTest(usage=usage):
                log = "\n".join([codex_turn(100, 40, 10, 5),
                                 json.dumps({"type": "turn.completed", "usage": usage})])
                events = cr.parse_codex_events(log)
                self.assertIsNone(events["tokens"])
                self.assertEqual(events["usage_error"],
                                 "turn.completed with missing or invalid token counts")

    def test_codex_invalid_optional_count_makes_tokens_unknown(self):
        for extra in ({"cached_input_tokens": "45056"}, {"reasoning_output_tokens": -1},
                      {"cache_write_input_tokens": 1.5}):
            with self.subTest(extra=extra):
                usage = dict({"input_tokens": 10, "output_tokens": 1}, **extra)
                events = cr.parse_codex_events(
                    json.dumps({"type": "turn.completed", "usage": usage}))
                self.assertIsNone(events["tokens"])
                self.assertEqual(events["usage_error"],
                                 "turn.completed with missing or invalid token counts")

    def test_codex_absent_or_null_optional_counts_are_zero(self):
        usage = {"input_tokens": 10, "output_tokens": 1, "cached_input_tokens": None}
        self.assertEqual(
            cr.parse_codex_events(json.dumps({"type": "turn.completed", "usage": usage}))["tokens"],
            {"input": 10, "cached_input": 0, "cache_write": 0, "output": 1, "reasoning": 0})

    def test_first_thread_started_wins_even_when_invalid(self):
        log = "\n".join([json.dumps({"type": "thread.started", "thread_id": "not-a-uuid"}),
                         json.dumps({"type": "thread.started", "thread_id": PROBE_THREAD})])
        self.assertIsNone(cr.parse_codex_events(log)["session"])

    def test_codex_turns_are_summed_and_absent_turns_give_none(self):
        log = "\n".join([codex_turn(100, 40, 10, 5), "not json", codex_turn(50, 0, 5, 0, 7)])
        self.assertEqual(cr.parse_codex_events(log)["tokens"],
                         {"input": 150, "cached_input": 40, "cache_write": 7,
                          "output": 15, "reasoning": 5})
        events = cr.parse_codex_events("progress only\n")
        self.assertIsNone(events["tokens"])
        self.assertIsNone(events["usage_error"])

    def test_parse_codex_session_reads_the_event_stream(self):
        self.assertEqual(cr.parse_codex_session(PROBE_CODEX_LOG), PROBE_THREAD)
        self.assertIsNone(cr.parse_codex_session("session id: %s\n" % PROBE_THREAD))

    def test_codex_cost(self):
        # (3612 * 2.00 + 45056 * 0.10 + 213 * 10.00) / 1e6 = 0.0138596
        self.assertEqual(cr.codex_cost("gpt-6.1-sol", PROBE_CODEX_TOKENS), 0.0139)
        self.assertIsNone(cr.codex_cost("gpt-unknown", PROBE_CODEX_TOKENS))

    def test_codex_cost_clamps_cached_above_input(self):
        # Uncached input clamps to 0: (0 * 2.00 + 2000 * 0.10 + 1000 * 10.00) / 1e6 = 0.0102
        tokens = {"input": 1000, "cached_input": 2000, "cache_write": 0,
                  "output": 1000, "reasoning": 0}
        self.assertEqual(cr.codex_cost("gpt-6.1-sol", tokens), 0.0102)

    def test_claude_output_sums_every_model(self):
        raw = json.dumps({"result": "ok", "total_cost_usd": 0.02, "modelUsage": {
            "claude-opus-5-5": {"inputTokens": 2, "outputTokens": 4,
                                "cacheReadInputTokens": 531,
                                "cacheCreationInputTokens": 2115, "thinkingTokens": 0},
            "claude-haiku-4-5-20251001": {"inputTokens": 10, "outputTokens": 3,
                                          "cacheReadInputTokens": 0,
                                          "cacheCreationInputTokens": 0,
                                          "thinkingTokens": 1}}})
        text, usage = cr.parse_claude_output(raw)
        self.assertEqual(text, "ok")
        self.assertEqual(usage["tokens"], {"input": 2658, "cached_input": 531,
                                           "cache_write": 2115, "output": 7,
                                           "reasoning": 1})

    def test_claude_output(self):
        text, usage = cr.parse_claude_output(PROBE_CLAUDE_OUTPUT)
        self.assertEqual(text, "Target reviewed: fixture\nCoverage: complete\n")
        self.assertEqual(usage, {"tokens": PROBE_CLAUDE_TOKENS, "cost_usd": 0.0171})

    def test_claude_output_without_result_or_json(self):
        for raw in ("", "plain text", "[]", json.dumps({"type": "result"}),
                    json.dumps({"result": 5})):
            with self.subTest(raw=raw):
                self.assertEqual(cr.parse_claude_output(raw), (None, None))

    def test_claude_model_usage_without_core_counts_makes_tokens_unknown(self):
        raw = json.dumps({"result": "ok", "total_cost_usd": 0.5,
                          "modelUsage": {"claude-opus-5-5": {"inputTokens": 3}}})
        self.assertEqual(cr.parse_claude_output(raw),
                         ("ok", {"tokens": None, "cost_usd": 0.5}))

    def test_claude_invalid_optional_count_makes_tokens_unknown(self):
        for extra in ({"cacheReadInputTokens": "531"}, {"thinkingTokens": -1}):
            with self.subTest(extra=extra):
                entry = dict({"inputTokens": 2, "outputTokens": 4}, **extra)
                raw = json.dumps({"result": "ok", "total_cost_usd": 0.5,
                                  "modelUsage": {"claude-opus-5-5": entry}})
                self.assertEqual(cr.parse_claude_output(raw),
                                 ("ok", {"tokens": None, "cost_usd": 0.5}))

    def test_claude_non_finite_cost_is_unknown(self):
        for cost in ("NaN", "Infinity"):
            with self.subTest(cost=cost):
                raw = '{"result": "ok", "total_cost_usd": %s}' % cost
                self.assertEqual(cr.parse_claude_output(raw)[1]["cost_usd"], None)

    def test_parsers_survive_deeply_nested_json(self):
        deep = "[" * 100000 + "]" * 100000
        self.assertIsNone(cr.parse_codex_events("{\"a\": %s}\n" % deep)["tokens"])
        self.assertEqual(cr.parse_claude_output('{"result": %s}' % deep), (None, None))

    def test_claude_usage_failure_keeps_the_review_text(self):
        with mock.patch.object(cr, "_claude_usage", side_effect=KeyError("boom")):
            self.assertEqual(cr.parse_claude_output(PROBE_CLAUDE_OUTPUT),
                             ("Target reviewed: fixture\nCoverage: complete\n",
                              {"tokens": None, "cost_usd": None}))

    def test_claude_output_without_model_usage(self):
        text, usage = cr.parse_claude_output(json.dumps({"result": "ok"}))
        self.assertEqual((text, usage), ("ok", {"tokens": None, "cost_usd": None}))

    def test_build_usage_codex(self):
        usage = cr.build_usage("codex", "gpt-6.1-sol", "low", PROBE_CODEX_TOKENS, None,
                               ["sample"])
        self.assertEqual(usage, {
            "schema_version": 1, "reviewer": "codex", "model": "gpt-6.1-sol",
            "effort": "low", "skills": ["sample"],
            "skills_note": "detected from SKILL.md reads",
            "tokens": PROBE_CODEX_TOKENS, "cost_usd": 0.0139, "cost_basis": "price-table",
            "prices_as_of": "2026-10-04", "previous_run": None,
            "session_total": {"tokens": PROBE_CODEX_TOKENS, "cost_usd": 0.0139,
                              "runs": 1, "complete": True}})

    def test_build_usage_claude(self):
        usage = cr.build_usage("claude", "claude-opus-5-5", "medium", PROBE_CLAUDE_TOKENS,
                               0.0171, ["ignored"])
        self.assertEqual(usage["skills"], [])
        self.assertEqual(usage["skills_note"], "disabled by policy")
        self.assertEqual((usage["cost_usd"], usage["cost_basis"], usage["prices_as_of"]),
                         (0.0171, "cli-list", None))

    def test_build_usage_unknown_model_and_missing_tokens(self):
        usage = cr.build_usage("codex", "gpt-unknown", "low", PROBE_CODEX_TOKENS, None, [])
        self.assertEqual((usage["cost_usd"], usage["cost_basis"], usage["prices_as_of"]),
                         (None, "unknown", None))
        self.assertFalse(usage["session_total"]["complete"])
        usage = cr.build_usage("codex", "gpt-6.1-sol", "low", None, None, [])
        self.assertEqual((usage["tokens"], usage["cost_usd"]), (None, None))

    def test_session_total_adds_the_previous_run(self):
        first = cr.build_usage("codex", "gpt-6.1-sol", "low", PROBE_CODEX_TOKENS, None, [])
        second = cr.build_usage("codex", "gpt-6.1-sol", "low", PROBE_CODEX_TOKENS, None, [],
                                previous_run=Path("/tmp/cross-review/prev"), previous=first)
        self.assertEqual(second["previous_run"], "/tmp/cross-review/prev")
        self.assertEqual(second["session_total"], {
            "tokens": {k: 2 * v for k, v in PROBE_CODEX_TOKENS.items()},
            "cost_usd": 0.0278, "runs": 2, "complete": True})

    def test_session_total_without_readable_previous_is_incomplete(self):
        for previous in (None, {"session_total": {"tokens": {}, "runs": 1}}, []):
            with self.subTest(previous=previous):
                usage = cr.build_usage("codex", "gpt-6.1-sol", "low", PROBE_CODEX_TOKENS,
                                       None, [], previous_run=Path("/p"), previous=previous)
                self.assertEqual(usage["session_total"]["runs"], 1)
                self.assertFalse(usage["session_total"]["complete"])

    def test_format_usage_line(self):
        codex = cr.build_usage("codex", "gpt-6.1-sol", "low", PROBE_CODEX_TOKENS, None,
                               ["sample"])
        self.assertEqual(cr.format_usage_line(codex),
                         "usage: codex gpt-6.1-sol effort=low skills=sample "
                         "tokens in=48668 (cached 45056) out=213 (reasoning 41) "
                         "cost~$0.01 (price table 2026-10-04)")
        claude = cr.build_usage("claude", "claude-opus-5-5", "medium", None, None, [])
        self.assertEqual(cr.format_usage_line(claude),
                         "usage: claude claude-opus-5-5 effort=medium "
                         "skills=none (disabled by policy) tokens unknown cost unknown")
        resumed = cr.build_usage("claude", "claude-opus-5-5", "medium", PROBE_CLAUDE_TOKENS,
                                 0.0171, [], previous_run=Path("/p"), previous=None)
        self.assertTrue(cr.format_usage_line(resumed).endswith(
            "cost~$0.02 (claude cli list price) session~$0.02 over 1 runs (incomplete)"))
        line = cr.format_usage_line(resumed)
        self.assertEqual(line, line.encode("ascii").decode("ascii"))
        unicode_model = cr.build_usage("codex", "gpt-\u00fc", "n\u00edzk\u00e9", None, None, [])
        line = cr.format_usage_line(unicode_model)
        self.assertTrue(line.startswith("usage: codex gpt-? effort=n?zk? "), line)
        line.encode("ascii")


# Fake reviewer sources. Each runs as a real child process via sys.executable;
# argv[1] is the expected cwd, argv[2] the -o path (Codex only).
FAKE_CLAUDE = (
    "import json,os,sys; "
    "assert os.environ['CROSS_REVIEW_DEPTH']=='1', 'depth'; "
    "assert os.environ['TASK_SENTINEL']=='present', 'env'; "
    "assert os.path.realpath(os.getcwd())==os.path.realpath(sys.argv[1]), 'cwd'; "
    "assert sys.stdin.read()=='fixture brief', 'stdin'; "
    "sys.stderr.write('claude diagnostics\\n'); "
    "sys.stdout.write(json.dumps({'type': 'result', 'is_error': False, "
    "'result': 'Target reviewed: fixture\\nCoverage: complete\\n', "
    "'total_cost_usd': 0.0171142, 'modelUsage': {'claude-opus-5-5': {"
    "'inputTokens': 2, 'outputTokens': 4, 'cacheReadInputTokens': 531, "
    "'cacheCreationInputTokens': 2115, 'thinkingTokens': 0}}}))"
)

FAKE_CODEX = (
    "import json,os,sys; "
    "assert os.environ['CROSS_REVIEW_DEPTH']=='1', 'depth'; "
    "assert os.path.realpath(os.getcwd())==os.path.realpath(sys.argv[1]), 'cwd'; "
    "assert sys.stdin.read()=='fixture brief', 'stdin'; "
    "sys.stderr.write('progress: thinking\\n'); "
    "print(json.dumps({'type': 'thread.started', 'thread_id': '" + SESSION + "'})); "
    "print(json.dumps({'type': 'item.completed', 'item': {'type': 'command_execution', "
    "'command': 'cat skills/sample/SKILL.md'}})); "
    "print(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 48668, "
    "'cached_input_tokens': 45056, 'cache_write_input_tokens': 0, 'output_tokens': 213, "
    "'reasoning_output_tokens': 41}})); "
    "open(sys.argv[2],'w').write('Target reviewed: fixture\\nCoverage: complete\\n')"
)


def fake_builder(source, argv_extra=None):
    """Replace only the command builder; subprocess stays real."""
    def build(reviewer, repo, run_dir, model, effort, session_id, untrusted=None):
        extra = [str(repo)]
        if reviewer == "codex":
            extra.append(str(Path(run_dir) / "review.md"))
        return [sys.executable, "-c", source] + extra + list(argv_extra or [])
    return build


def tree_snapshot(root):
    snap = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            st = os.lstat(path)
            snap[os.path.relpath(path, root)] = (st.st_mode, st.st_size, st.st_mtime_ns)
    return snap


class RunnerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.tmpdir = base / "tmp root"
        self.tmpdir.mkdir()
        self.repo = base / "target repo"
        self.repo.mkdir()
        (self.repo / "file.txt").write_text("content\n")
        self.brief = base / "brief input.md"
        self.brief.write_text("fixture brief", encoding="utf-8")
        self.env = {k: v for k, v in os.environ.items() if k != "CROSS_REVIEW_DEPTH"}
        self.env["TASK_SENTINEL"] = "present"
        # Isolate from a parent CROSS_REVIEW_DEPTH: restored when the test ends.
        env_patch = mock.patch.dict(os.environ, clear=False)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        os.environ.pop("CROSS_REVIEW_DEPTH", None)
        patches = [
            mock.patch.object(tempfile, "tempdir", str(self.tmpdir)),
            mock.patch.object(cr.shutil, "which", return_value=sys.executable),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self._tmp.cleanup()

    @property
    def root(self):
        return self.tmpdir / "cross-review"

    def run_dirs(self):
        return sorted(self.root.iterdir()) if self.root.exists() else []

    def run_fake(self, reviewer, source, **kwargs):
        with mock.patch.object(cr, "build_run_command", fake_builder(source)):
            return cr.run_review(reviewer, self.repo, self.brief, None, None,
                                 kwargs.get("env", self.env))

    def run_fake_error(self, reviewer, source):
        with self.assertRaises(cr.CrossReviewError) as caught:
            self.run_fake(reviewer, source)
        return caught.exception


class MainTests(RunnerTestCase):
    def call_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cr.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_cli_returns_21_without_spawn(self):
        with mock.patch.object(cr.shutil, "which", return_value=None), \
                mock.patch.object(cr.subprocess, "Popen") as popen, \
                mock.patch.object(cr.subprocess, "run") as run:
            code, _, err = self.call_main(["run", "--reviewer", "codex", "--repo",
                                           str(self.repo), "--brief", str(self.brief)])
        self.assertEqual(code, 21)
        popen.assert_not_called()
        run.assert_not_called()
        self.assertEqual(self.run_dirs(), [])
        self.assertIn("codex", err)

    def test_main_success_prints_absolute_paths(self):
        with mock.patch.dict(os.environ, {"TASK_SENTINEL": "present"}), \
                mock.patch.object(cr, "build_run_command", fake_builder(FAKE_CLAUDE)):
            os.environ.pop("CROSS_REVIEW_DEPTH", None)
            code, out, _ = self.call_main(["run", "--reviewer", "claude", "--repo",
                                           str(self.repo), "--brief", str(self.brief)])
        self.assertEqual(code, 0)
        [run_dir] = self.run_dirs()
        self.assertIn(str(run_dir), out)
        for name in ARTIFACTS:
            self.assertIn(str(run_dir / name), out)
        lines = out.splitlines()
        self.assertTrue(lines[-1].startswith("usage: claude claude-opus-5-5 effort=medium "),
                        lines[-1])
        self.assertIn(str(run_dir / "usage.json"), out)
        for line in lines[:-1]:
            self.assertTrue(os.path.isabs(line.split(": ", 1)[1]), line)

    def test_invalid_input_returns_2(self):
        bad = self.brief.parent / "bad.md"
        bad.write_bytes(b"\xff\xfe broken")
        control = self.brief.parent / "repo\nname"
        control.mkdir()
        cases = [
            ["--reviewer", "codex", "--repo", str(control), "--brief", str(self.brief)],
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", str(bad)],
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", "/nonexistent/b.md"],
            ["--reviewer", "codex", "--repo", "/nonexistent/repo", "--brief", str(self.brief)],
            ["--reviewer", "gemini", "--repo", str(self.repo), "--brief", str(self.brief)],
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", str(self.brief),
             "--model", ""],
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", str(self.brief),
             "--model=--dangerously-bypass-approvals-and-sandbox"],
            ["--reviewer", "claude", "--repo", str(self.repo), "--brief", str(self.brief),
             "--model=--dangerously-skip-permissions"],
            ["--reviewer", "codex", "--repo", str(self.repo), "--brief", str(self.brief),
             "--effort=-x"],
        ]
        for args in cases:
            with self.subTest(args=args), \
                    mock.patch.object(cr.subprocess, "Popen") as popen:
                code, _, _ = self.call_main(["run"] + args)
                self.assertEqual(code, 2)
                popen.assert_not_called()
        self.assertEqual(self.run_dirs(), [])


class GuardSubprocessTests(RunnerTestCase):
    def test_actual_main_with_depth_exits_20_before_cli_and_run_dir(self):
        env = dict(self.env, CROSS_REVIEW_DEPTH="", TMPDIR=str(self.tmpdir),
                   PATH="/nonexistent")
        proc = subprocess.run(
            [sys.executable, SCRIPT, "run", "--reviewer", "codex", "--repo",
             str(self.repo), "--brief", str(self.brief)],
            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 20, proc.stderr)
        self.assertIn("already the cross-reviewer", proc.stderr)
        self.assertFalse(self.root.exists())

    def test_nested_child_run_is_refused(self):
        # The fake reviewer tries to delegate again through the real script.
        nested = (
            "import json,subprocess,sys; "
            "sys.stdin.read(); "
            "r = subprocess.run([sys.executable, %r, 'run', '--reviewer', 'codex', "
            "'--repo', sys.argv[1], '--brief', %r], stdin=subprocess.DEVNULL, "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            "print(json.dumps({'result': 'nested-exit=%%d' %% r.returncode}))"
        ) % (SCRIPT, str(self.brief))
        run_dir = self.run_fake("claude", nested)
        self.assertEqual((run_dir / "review.md").read_text().strip(), "nested-exit=20")
        self.assertEqual(self.run_dirs(), [run_dir])


class RunReviewTests(RunnerTestCase):
    def test_claude_artifacts(self):
        before = tree_snapshot(self.repo)
        run_dir = self.run_fake("claude", FAKE_CLAUDE)
        self.assertEqual(tree_snapshot(self.repo), before)
        self.assertTrue(run_dir.is_absolute())
        self.assertEqual(run_dir.parent, self.root)
        self.assertEqual((run_dir / "brief.md").read_text(), "fixture brief")
        self.assertEqual((run_dir / "review.md").read_text(),
                         "Target reviewed: fixture\nCoverage: complete\n")
        self.assertFalse((run_dir / "claude-output.json").exists())
        usage = json.loads((run_dir / "usage.json").read_text())
        self.assertEqual(usage["tokens"], PROBE_CLAUDE_TOKENS)
        self.assertEqual((usage["cost_usd"], usage["cost_basis"]), (0.0171, "cli-list"))
        self.assertEqual((usage["skills"], usage["skills_note"]), ([], "disabled by policy"))
        session = (run_dir / "session.txt").read_text().strip()
        self.assertRegex(session, cr._UUID_RE.pattern)
        log = (run_dir / "run.log").read_text()
        self.assertIn("claude diagnostics", log)
        self.assertNotIn("Target reviewed", log)

    def test_claude_session_id_is_passed_to_builder(self):
        seen = {}
        inner = fake_builder(FAKE_CLAUDE)

        def spy(reviewer, repo, run_dir, model, effort, session_id, untrusted=None):
            seen["session"] = session_id
            seen["model"], seen["effort"] = model, effort
            return inner(reviewer, repo, run_dir, model, effort, session_id, untrusted)

        with mock.patch.object(cr, "build_run_command", spy):
            run_dir = cr.run_review("claude", self.repo, self.brief, None, None, self.env)
        self.assertEqual((run_dir / "session.txt").read_text().strip(), seen["session"])
        self.assertEqual((seen["model"], seen["effort"]), cr.DEFAULTS["claude"])

    def test_codex_final_answer_comes_from_output_file(self):
        run_dir = self.run_fake("codex", FAKE_CODEX)
        self.assertEqual((run_dir / "review.md").read_text(),
                         "Target reviewed: fixture\nCoverage: complete\n")
        self.assertEqual((run_dir / "session.txt").read_text().strip(), SESSION)
        log = (run_dir / "run.log").read_text()
        self.assertIn("progress: thinking", log)
        self.assertIn('"type": "thread.started"', log)

    def test_codex_without_session_leaves_session_empty(self):
        source = FAKE_CODEX.replace("thread.started", "thread.other")
        run_dir = self.run_fake("codex", source)
        self.assertEqual((run_dir / "session.txt").read_text(), "")
        self.assertIn("session id not found", (run_dir / "run.log").read_text())

    def test_codex_usage_json(self):
        run_dir = self.run_fake("codex", FAKE_CODEX)
        usage = json.loads((run_dir / "usage.json").read_text())
        self.assertEqual(usage, {
            "schema_version": 1, "reviewer": "codex", "model": "gpt-6.1-sol",
            "effort": "low", "skills": ["sample"],
            "skills_note": "detected from SKILL.md reads",
            "tokens": PROBE_CODEX_TOKENS, "cost_usd": 0.0139, "cost_basis": "price-table",
            "prices_as_of": "2026-10-04", "previous_run": None,
            "session_total": {"tokens": PROBE_CODEX_TOKENS, "cost_usd": 0.0139,
                              "runs": 1, "complete": True}})
        self.assertNotIn("fixture brief", (run_dir / "usage.json").read_text())

    def test_usage_failure_keeps_exit_zero_and_is_logged(self):
        with mock.patch.object(cr, "build_usage", side_effect=TypeError("boom")):
            run_dir = self.run_fake("codex", FAKE_CODEX)
        self.assertFalse((run_dir / "usage.json").exists())
        self.assertIn("cross-review: usage not recorded: boom",
                      (run_dir / "run.log").read_text())

    def test_usage_failure_with_failing_log_keeps_exit_zero(self):
        real_log = cr._log

        def log(fd, line):
            if line.startswith("usage"):
                raise OSError("disk full")
            real_log(fd, line)

        with mock.patch.object(cr, "build_usage", side_effect=OverflowError("big")), \
                mock.patch.object(cr, "_log", side_effect=log):
            run_dir = self.run_fake("codex", FAKE_CODEX)
        self.assertEqual((run_dir / "review.md").read_text(),
                         "Target reviewed: fixture\nCoverage: complete\n")

    def test_codex_event_parse_failure_keeps_exit_zero(self):
        with mock.patch.object(cr, "parse_codex_events", side_effect=RuntimeError("boom")):
            run_dir = self.run_fake("codex", FAKE_CODEX)
        self.assertEqual((run_dir / "review.md").read_text(),
                         "Target reviewed: fixture\nCoverage: complete\n")
        self.assertIsNone(json.loads((run_dir / "usage.json").read_text())["tokens"])
        self.assertIn("cross-review: usage incomplete: event parse failed: boom",
                      (run_dir / "run.log").read_text())

    def test_invalid_codex_usage_is_unknown_and_logged(self):
        source = FAKE_CODEX.replace("'input_tokens': 48668, ", "")
        run_dir = self.run_fake("codex", source)
        usage = json.loads((run_dir / "usage.json").read_text())
        self.assertEqual((usage["tokens"], usage["cost_usd"]), (None, None))
        self.assertIn("cross-review: usage incomplete: turn.completed with missing or "
                      "invalid token counts", (run_dir / "run.log").read_text())

    def test_log_header_is_first_json_line(self):
        run_dir = self.run_fake("codex", FAKE_CODEX)
        first, rest = (run_dir / "run.log").read_text().split("\n", 1)
        header = json.loads(first)
        self.assertEqual(header["schema_version"], 1)
        self.assertEqual(header["reviewer"], "codex")
        self.assertEqual(header["mode"], "unspecified")
        self.assertEqual(header["repo"], str(self.repo.resolve()))
        self.assertEqual((header["model"], header["effort"]), cr.DEFAULTS["codex"])
        self.assertTrue(header["cli_version"].startswith("Python"))
        self.assertNotIn("TASK_SENTINEL", first)
        self.assertNotIn("env", header)
        self.assertIn("progress: thinking", rest)

    def test_nonzero_exit_with_partial_result_is_22(self):
        source = "import sys; sys.stdin.read(); print('partial finding'); sys.exit(7)"
        err = self.run_fake_error("claude", source)
        self.assertEqual(err.code, 22)
        self.assertIn("7", err.message)
        self.assertEqual((err.run_dir / "review.md").read_text(), "partial finding\n")

    def test_empty_or_whitespace_result_is_23(self):
        for body in ("", "print('   ')"):
            with self.subTest(body=body):
                err = self.run_fake_error("claude", "import sys; sys.stdin.read()\n" + body)
                self.assertEqual(err.code, 23)
                self.assertTrue((err.run_dir / "run.log").exists())

    def test_codex_missing_output_is_23(self):
        source = "import sys; sys.stdin.read(); print('progress only')"
        err = self.run_fake_error("codex", source)
        self.assertEqual(err.code, 23)

    def test_cli_disappearing_after_which_is_21(self):
        def gone(*args, **kwargs):
            return [str(self.repo.parent / "vanished-cli")]
        with mock.patch.object(cr, "build_run_command", gone):
            with self.assertRaises(cr.CrossReviewError) as caught:
                cr.run_review("codex", self.repo, self.brief, None, None, self.env)
        self.assertEqual(caught.exception.code, 21)

    def test_claude_plain_text_with_exit_zero_is_23_and_kept(self):
        err = self.run_fake_error("claude", "import sys; sys.stdin.read(); print('not json')")
        self.assertEqual(err.code, 23)
        self.assertEqual((err.run_dir / "review.md").read_text(), "not json\n")
        self.assertTrue((err.run_dir / "claude-output.json").exists())
        self.assertEqual(
            stat.S_IMODE(os.lstat(err.run_dir / "claude-output.json").st_mode), 0o600)
        self.assertIn("claude output is not JSON with a result",
                      (err.run_dir / "run.log").read_text())

    def test_claude_blank_result_is_23(self):
        source = ("import json,sys; sys.stdin.read(); "
                  "sys.stdout.write(json.dumps({'result': '   '}))")
        err = self.run_fake_error("claude", source)
        self.assertEqual(err.code, 23)
        self.assertFalse((err.run_dir / "claude-output.json").exists())

    def test_claude_json_result_with_nonzero_exit_is_22(self):
        source = ("import json,sys; sys.stdin.read(); "
                  "sys.stdout.write(json.dumps({'result': 'partial'})); sys.exit(7)")
        err = self.run_fake_error("claude", source)
        self.assertEqual(err.code, 22)
        self.assertEqual((err.run_dir / "review.md").read_text(), "partial")

    def test_unicode_brief(self):
        text = "Огляд плану: перевір усе \u2713 \U0001f600"
        self.brief.write_text(text, encoding="utf-8")
        source = ("import json,sys; data = sys.stdin.buffer.read().decode('utf-8'); "
                  "sys.stdout.write(json.dumps({'result': 'echo:' + data}))")
        run_dir = self.run_fake("claude", source)
        self.assertEqual((run_dir / "brief.md").read_text(encoding="utf-8"), text)
        self.assertEqual((run_dir / "review.md").read_text(encoding="utf-8"), "echo:" + text)

    def test_popen_has_no_shell_or_timeout_and_uses_child_env(self):
        real_popen = subprocess.Popen
        with mock.patch.object(cr.subprocess, "Popen", side_effect=real_popen) as popen:
            self.run_fake("claude", FAKE_CLAUDE)
        # The first Popen is the --version probe; the review spawn is the last one.
        calls = [c for c in popen.call_args_list if c.args[0][-1:] != ["--version"]]
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertIsInstance(args[0] if args else kwargs["args"], list)
        self.assertFalse(kwargs.get("shell", False))
        self.assertNotIn("timeout", kwargs)
        self.assertEqual(kwargs["cwd"], str(self.repo.resolve()))
        self.assertEqual(kwargs["env"]["CROSS_REVIEW_DEPTH"], "1")
        self.assertEqual(kwargs["umask"], 0o077)
        self.assertNotIn("capture_output", kwargs)


class RunDirSafetyTests(RunnerTestCase):
    def permissive(self):
        old = os.umask(0)
        self.addCleanup(os.umask, old)

    def test_modes_and_owner_under_permissive_umask(self):
        self.permissive()
        run_dir = self.run_fake("codex", FAKE_CODEX)
        for path, mode in [(self.root, 0o700), (run_dir, 0o700)] + \
                [(run_dir / n, 0o600) for n in ARTIFACTS + ("usage.json",)]:
            with self.subTest(path=path.name):
                st = os.lstat(path)
                self.assertEqual(stat.S_IMODE(st.st_mode), mode)
                self.assertEqual(st.st_uid, os.getuid())

    def test_codex_output_replaced_with_loose_mode_is_tightened(self):
        self.permissive()
        source = FAKE_CODEX.replace(
            "open(sys.argv[2],'w').write(",
            "os.unlink(sys.argv[2]); os.umask(0); "
            "os.close(os.open(sys.argv[2], os.O_WRONLY|os.O_CREAT, 0o666)); "
            "open(sys.argv[2],'w').write(")
        run_dir = self.run_fake("codex", source)
        self.assertEqual(stat.S_IMODE(os.lstat(run_dir / "review.md").st_mode), 0o600)

    def test_replaced_artifact_is_logged_and_fails(self):
        source = FAKE_CODEX.replace(
            "open(sys.argv[2],'w').write(",
            "os.unlink(sys.argv[2]); os.symlink('/dev/null', sys.argv[2]); (lambda *a: None)(")
        err = self.run_fake_error("codex", source)
        self.assertEqual(err.code, cr.EXIT_REVIEWER_FAILED)
        log = (err.run_dir / "run.log").read_text()
        self.assertIn("cross-review: exit status 0\n", log)
        self.assertIn("cross-review: unsafe artifact after run: ", log)

    def test_new_root_gets_0700_even_under_strict_umask(self):
        old = os.umask(0o277)
        self.addCleanup(os.umask, old)
        run_dir = self.run_fake("claude", FAKE_CLAUDE)
        self.assertEqual(stat.S_IMODE(os.lstat(self.root).st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(os.lstat(run_dir).st_mode), 0o700)

    def test_existing_loose_root_is_not_repaired(self):
        self.root.mkdir()
        os.chmod(self.root, 0o750)
        self.assertEqual(self.run_fake_error("claude", FAKE_CLAUDE).code, 2)
        self.assertEqual(stat.S_IMODE(os.lstat(self.root).st_mode), 0o750)

    def test_symlinked_root_is_rejected(self):
        target = self.tmpdir / "elsewhere"
        target.mkdir(mode=0o700)
        self.root.symlink_to(target)
        err = self.run_fake_error("claude", FAKE_CLAUDE)
        self.assertEqual(err.code, 2)
        self.assertEqual(list(target.iterdir()), [])

    def test_group_accessible_root_is_rejected(self):
        self.root.mkdir()
        os.chmod(self.root, 0o755)
        err = self.run_fake_error("claude", FAKE_CLAUDE)
        self.assertEqual(err.code, 2)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_same_second_runs_do_not_collide(self):
        with mock.patch.object(cr, "_timestamp", return_value="20261003-120000"):
            first = self.run_fake("claude", FAKE_CLAUDE)
            first_review = (first / "review.md").read_text()
            second = self.run_fake("claude", FAKE_CLAUDE)
            third = self.run_fake("claude", FAKE_CLAUDE)
        self.assertEqual(first.name, "20261003-120000")
        self.assertEqual(second.name, "20261003-120000-1")
        self.assertEqual(third.name, "20261003-120000-2")
        self.assertEqual((first / "review.md").read_text(), first_review)


class InterruptTests(RunnerTestCase):
    def interrupt(self, sig):
        pid_file = self.tmpdir / "child.pid"
        wrapper = (
            "import sys, tempfile; "
            "sys.path.insert(0, %r); import cross_review as cr; "
            "tempfile.tempdir = %r; "
            "src = \"import os,sys,time; sys.stdin.read(); open(%r,'w').write(str(os.getpid())); "
            "sys.stdout.write('partial'); sys.stdout.flush(); "
            "sys.stderr.write('ready\\\\n'); sys.stderr.flush(); time.sleep(60)\"; "
            "cr.shutil.which = lambda name: sys.executable; "
            "cr.build_run_command = lambda *a, **k: [sys.executable, '-c', src]; "
            "sys.exit(cr.main(['run', '--reviewer', 'claude', '--repo', %r, "
            "'--brief', %r]))"
        ) % (os.path.dirname(SCRIPT), str(self.tmpdir), str(pid_file), str(self.repo),
             str(self.brief))
        proc = subprocess.Popen([sys.executable, "-c", wrapper], env=self.env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 20
        log = None
        while time.time() < deadline:
            logs = list(self.root.glob("*/run.log")) if self.root.exists() else []
            if logs and "ready" in logs[0].read_text():
                log = logs[0]
                break
            time.sleep(0.05)
        self.assertIsNotNone(log, "fake reviewer never became ready")
        child = int(pid_file.read_text())
        proc.send_signal(sig)
        out, err = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 130, err)
        self.assertNotIn("Traceback", err)
        self.assertIn(str(log.parent), out)
        self.assertEqual((log.parent / "review.md").read_text(), "partial")
        self.assertIn("interrupted", log.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(child, 0)

    def test_sigint_keeps_partial_artifacts_and_stops_reviewer(self):
        self.interrupt(signal.SIGINT)

    def test_sigterm_keeps_partial_artifacts_and_stops_reviewer(self):
        self.interrupt(signal.SIGTERM)


NEW_SESSION = "22222222-2222-4222-8222-222222222222"

# A fake `codex`/`claude` executable placed on PATH. It records argv, cwd, stdin
# and depth, then answers like the real CLI: Codex writes the -o file and prints
# JSONL events on stdout, Claude prints the --output-format json result on stdout.
FAKE_CLI = r"""
import json, os, sys, uuid
name = os.path.basename(sys.argv[0])
data = sys.stdin.read()
record = {"argv": sys.argv[1:], "cwd": os.getcwd(), "stdin": data,
          "depth": os.environ.get("CROSS_REVIEW_DEPTH")}
path = os.path.join(os.environ["FAKE_RECORD"], "%s-%s.json" % (name, uuid.uuid4()))
with open(path, "w") as fh:
    json.dump(record, fh)
answer = "Target reviewed: fixture\nFollow-up handled\n"
if name == "codex":
    sys.stdout.write("progress line\n")
    new = os.environ.get("FAKE_NEW_SESSION", "")
    if new:
        sys.stdout.write(json.dumps({"type": "thread.started", "thread_id": new}) + "\n")
    sys.stdout.write(json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": 1000, "cached_input_tokens": 400, "cache_write_input_tokens": 0,
        "output_tokens": 100, "reasoning_output_tokens": 20}}) + "\n")
    out = sys.argv[sys.argv.index("-o") + 1]
    with open(out, "w") as fh:
        fh.write(answer)
else:
    sys.stdout.write(json.dumps({"type": "result", "result": answer,
                                 "total_cost_usd": 0.01, "modelUsage": {
                                     "claude-opus-5-5": {"inputTokens": 10,
                                                         "outputTokens": 5}}}))
"""


def expected_claude_resume(session, model="claude-opus-5-5", effort="medium"):
    # Literal duplicate of the Task 2 policy with --resume instead of --session-id.
    return [
        "claude", "-p", "--output-format", "json", "--model", model, "--effort", effort,
        "--permission-mode", "default", "--tools", "Read,Grep,Glob",
        "--allowedTools", "Read,Grep,Glob", "--disallowedTools",
        "Write,Edit,NotebookEdit,Bash,Agent,Skill,mcp__*",
        "--strict-mcp-config", "--disable-slash-commands", "--safe-mode",
        "--restricted", "--setting-sources", "",
        "--resume", session,
    ]


def expected_codex_resume(run, session, model="gpt-6.1-sol", effort="low", repo=None):
    return [
        "codex", "exec", "resume", "--json", "-m", model,
        "-c", 'model_reasoning_effort="%s"' % effort,
        "-c", 'sandbox_mode="read-only"',
        "-c", trust_token(Path(repo).resolve()),
        "-o", str(run / "review.md"), session, "-",
    ]


def dir_digest(path):
    out = {}
    for child in sorted(Path(path).iterdir()):
        st = os.lstat(child)
        out[child.name] = (stat.S_IMODE(st.st_mode),
                           hashlib.sha256(child.read_bytes()).hexdigest())
    return out


def git(*args):
    subprocess.run(["git"] + list(args), check=True, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


HAS_GIT = shutil.which("git") is not None


def make_main_repo(path):
    path.mkdir()
    git("-C", str(path), "init", "-q")
    git("-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t",
        "commit", "-q", "--allow-empty", "-m", "x")
    return path


def make_bare_worktree(base, main):
    """Clone main as base/'bare store.git' and add the worktree base/'bare wt'."""
    bare, worktree = base / "bare store.git", base / "bare wt"
    git("clone", "-q", "--bare", str(main), str(bare))
    git("-C", str(bare), "worktree", "add", "-q", "--detach", str(worktree))
    return bare, worktree


@unittest.skipUnless(HAS_GIT, "git is not installed")
class UntrustedPathTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.main = make_main_repo(self.base / "main repo")

    def no_git(self):
        return mock.patch.object(cr, "_git_line", return_value=None)

    def linked(self, name="linked wt"):
        worktree = self.base / name
        git("-C", str(self.main), "worktree", "add", "-q", "--detach", str(worktree))
        return worktree

    def test_bare_worktree_adds_common_dir_and_its_parent(self):
        bare, worktree = make_bare_worktree(self.base, self.main)
        expected = [str(worktree), str(self.base), str(bare)]
        self.assertEqual(cr.codex_untrusted_paths(worktree), expected)
        with self.no_git():
            self.assertEqual(cr.codex_untrusted_paths(worktree), expected)

    def test_separate_git_dir_adds_common_dir_parent(self):
        store = self.base / "store" / "sep.git"
        store.parent.mkdir()
        repo = self.base / "sep repo"
        git("init", "-q", "--separate-git-dir", str(store), str(repo))
        expected = [str(repo), str(store.parent), str(store)]
        self.assertEqual(cr.codex_untrusted_paths(repo), expected)
        with self.no_git():
            self.assertEqual(cr.codex_untrusted_paths(repo), expected)

    def test_fallback_without_git_finds_main_root(self):
        worktree = self.linked()
        sub = self.main / "sub"
        sub.mkdir()
        with self.no_git():
            self.assertEqual(cr.codex_untrusted_paths(worktree),
                             [str(worktree), str(self.main)])
            self.assertEqual(cr.codex_untrusted_paths(sub), [str(sub), str(self.main)])

    def test_git_redirect_variables_are_ignored(self):
        other = make_main_repo(self.base / "other repo")
        worktree = self.linked()
        redirect = {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other),
                    "GIT_COMMON_DIR": str(other / ".git"),
                    "GIT_CEILING_DIRECTORIES": str(self.base),
                    "GIT_INDEX_FILE": str(other / ".git" / "index")}
        with mock.patch.dict(os.environ, redirect):
            self.assertEqual(cr.codex_untrusted_paths(worktree),
                             [str(worktree), str(self.main)])

    def test_unreadable_git_layout_fails_closed(self):
        broken = self.base / "broken"
        broken.mkdir()
        (broken / ".git").write_text("not a gitdir pointer\n")
        with self.no_git(), self.assertRaises(cr.CrossReviewError) as caught:
            cr.codex_untrusted_paths(broken)
        self.assertEqual(caught.exception.code, 2)

    def test_on_disk_spelling_is_added(self):
        cased = self.base / "CaseDir"
        cased.mkdir()
        lower = self.base / "casedir"
        if not lower.exists() or not hasattr(cr.fcntl, "F_GETPATH"):
            self.skipTest("needs a case-insensitive file system with F_GETPATH")
        self.assertEqual(cr.codex_untrusted_paths(lower), [str(lower), str(cased)])

    def tearDown(self):
        self._tmp.cleanup()

    def test_plain_repo(self):
        self.assertEqual(cr.codex_untrusted_paths(self.main), [str(self.main)])

    def test_subdirectory_adds_toplevel(self):
        sub = self.main / "sub dir"
        sub.mkdir()
        self.assertEqual(cr.codex_untrusted_paths(sub), [str(sub), str(self.main)])

    def test_linked_worktree_adds_main_root(self):
        worktree = self.base / "linked wt"
        git("-C", str(self.main), "worktree", "add", "-q", "--detach", str(worktree))
        self.assertEqual(cr.codex_untrusted_paths(worktree),
                         [str(worktree), str(self.main)])
        argv = cr.build_run_command("codex", worktree, self.base / "run", "m", "e", SESSION)
        self.assertIn(trust_token(worktree, self.main), argv)

    def test_non_git_directory(self):
        plain = self.base / "plain"
        plain.mkdir()
        with mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.base)}):
            self.assertEqual(cr.codex_untrusted_paths(plain), [str(plain)])

    def test_old_git_without_path_format_still_finds_main_root(self):
        worktree = self.base / "old wt"
        git("-C", str(self.main), "worktree", "add", "-q", "--detach", str(worktree))
        real_run = subprocess.run

        def old_git(argv, *args, **kwargs):
            if "--path-format=absolute" in argv:
                return subprocess.CompletedProcess(argv, 129, b"", b"")
            return real_run(argv, *args, **kwargs)

        with mock.patch.object(cr.subprocess, "run", side_effect=old_git):
            self.assertEqual(cr.codex_untrusted_paths(worktree),
                             [str(worktree), str(self.main)])
            self.assertEqual(cr.codex_untrusted_paths(self.main), [str(self.main)])

    def test_missing_git_falls_back_to_repo(self):
        with mock.patch.object(cr.subprocess, "run", side_effect=FileNotFoundError("git")):
            self.assertEqual(cr.codex_untrusted_paths(self.main), [str(self.main)])


class ResumeArgvTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo dir"
        self.repo.mkdir()
        self.run = Path(self._tmp.name) / "new run"

    def tearDown(self):
        self._tmp.cleanup()

    def test_claude_resume_argv(self):
        self.assertEqual(
            cr.build_resume_command("claude", self.repo, self.run, "claude-opus-5-5",
                                    "medium", SESSION),
            expected_claude_resume(SESSION))

    def test_codex_resume_argv(self):
        argv = cr.build_resume_command("codex", self.repo, self.run, "gpt-6.1-sol",
                                       "low", SESSION, untrusted=[str(self.repo.resolve())])
        self.assertEqual(argv, expected_codex_resume(self.run, SESSION, repo=self.repo))
        for banned in ("-s", "-C", "--last", "--session-id"):
            self.assertNotIn(banned, argv)

    def test_overrides_change_only_model_and_effort(self):
        self.assertEqual(
            cr.build_resume_command("claude", self.repo, self.run, "m2", "high", SESSION),
            expected_claude_resume(SESSION, "m2", "high"))
        self.assertEqual(
            cr.build_resume_command("codex", self.repo, self.run, "m3", "xhigh", SESSION,
                                    untrusted=[str(self.repo.resolve())]),
            expected_codex_resume(self.run, SESSION, "m3", "xhigh", repo=self.repo))

    def test_invalid_session_or_reviewer(self):
        for reviewer, session, code in [("claude", "nope", 24), ("codex", "", 24),
                                        ("gemini", SESSION, 2)]:
            with self.subTest(reviewer=reviewer, session=session):
                with self.assertRaises(cr.CrossReviewError) as caught:
                    cr.build_resume_command(reviewer, self.repo, self.run, "m", "e", session)
                self.assertEqual(caught.exception.code, code)


class ResumeTests(RunnerTestCase):
    def setUp(self):
        super().setUp()
        base = Path(self._tmp.name)
        self.bin = base / "fake bin"
        self.bin.mkdir()
        for name in ("codex", "claude"):
            path = self.bin / name
            path.write_text("#!%s\n%s" % (sys.executable, FAKE_CLI))
            path.chmod(0o755)
        self.record = base / "record"
        self.record.mkdir()
        self.env["PATH"] = "%s%s%s" % (self.bin, os.pathsep, self.env.get("PATH", ""))
        self.env["FAKE_RECORD"] = str(self.record)
        self.env["FAKE_NEW_SESSION"] = SESSION
        self.elsewhere = base / "elsewhere"
        self.elsewhere.mkdir()

    def records(self):
        out = []
        for path in sorted(self.record.iterdir(), key=lambda p: p.stat().st_mtime_ns):
            out.append(json.loads(path.read_text()))
        return out

    def original(self, reviewer):
        """Create an authentic original run through the real builder and fake CLI."""
        run_dir = cr.run_review(reviewer, self.repo, self.brief, None, None, self.env)
        for path in self.record.iterdir():
            path.unlink()
        return run_dir

    def resume(self, run_dir, prompt="Re-check the second finding.", env=None):
        cwd = os.getcwd()
        os.chdir(self.elsewhere)
        try:
            return cr.resume_review(run_dir, prompt, env or self.env)
        finally:
            os.chdir(cwd)

    def test_resume_session_total_adds_the_original(self):
        original = self.original("codex")
        new_dir = self.resume(original)
        usage = json.loads((new_dir / "usage.json").read_text())
        self.assertEqual(usage["previous_run"], str(original))
        # Each fake codex turn: (600 * 2.00 + 400 * 0.10 + 100 * 10.00) / 1e6 = 0.00224
        self.assertEqual(usage["cost_usd"], 0.0022)
        self.assertEqual(usage["session_total"], {
            "tokens": {"input": 2000, "cached_input": 800, "cache_write": 0,
                       "output": 200, "reasoning": 40},
            "cost_usd": 0.0044, "runs": 2, "complete": True})

    def test_resume_without_previous_usage_is_incomplete(self):
        original = self.original("codex")
        (original / "usage.json").unlink()
        new_dir = self.resume(original)
        total = json.loads((new_dir / "usage.json").read_text())["session_total"]
        self.assertEqual((total["runs"], total["complete"]), (1, False))

    def resume_error(self, run_dir, **kwargs):
        with mock.patch.object(cr.subprocess, "Popen") as popen:
            with self.assertRaises(cr.CrossReviewError) as caught:
                self.resume(run_dir, **kwargs)
        popen.assert_not_called()
        return caught.exception

    def test_codex_resume_round_trip(self):
        original = self.original("codex")
        before = dir_digest(original)
        self.env["FAKE_NEW_SESSION"] = NEW_SESSION
        new_dir = self.resume(original)
        self.assertEqual(dir_digest(original), before)
        self.assertNotEqual(new_dir, original)
        self.assertEqual(new_dir.parent, original.parent)
        [rec] = self.records()
        self.assertEqual(rec["argv"],
                         expected_codex_resume(new_dir, SESSION, repo=self.repo)[1:])
        self.assertEqual(os.path.realpath(rec["cwd"]), os.path.realpath(self.repo))
        self.assertEqual(rec["depth"], "1")
        self.assertIn("Re-check the second finding.", rec["stdin"])
        self.assertIn("read-only", rec["stdin"])
        self.assertNotIn("fixture brief", rec["stdin"])
        self.assertEqual((new_dir / "brief.md").read_text(), rec["stdin"])
        self.assertEqual((new_dir / "review.md").read_text(),
                         "Target reviewed: fixture\nFollow-up handled\n")
        self.assertEqual((new_dir / "session.txt").read_text().strip(), NEW_SESSION)
        header = json.loads((new_dir / "run.log").read_text().split("\n", 1)[0])
        self.assertEqual(header["reviewer"], "codex")
        self.assertEqual(header["repo"], str(self.repo.resolve()))
        self.assertEqual(header["resumed_from"], str(original))
        for name in ARTIFACTS:
            self.assertEqual(stat.S_IMODE(os.lstat(new_dir / name).st_mode), 0o600)

    def layout_round_trip(self, repo, trust):
        run_dir = cr.run_review("codex", repo, self.brief, None, None, self.env)
        [rec] = self.records()
        self.assertEqual(rec["argv"], expected_codex(repo, run_dir, trust=trust)[1:])
        new_dir = self.resume(run_dir)
        rec = self.records()[-1]
        expected = expected_codex_resume(new_dir, SESSION, repo=repo)[1:]
        expected[expected.index(trust_token(repo))] = trust
        self.assertEqual(rec["argv"], expected)

    @unittest.skipUnless(HAS_GIT, "git is not installed")
    def test_linked_worktree_run_and_resume_mark_main_root_untrusted(self):
        base = Path(self._tmp.name).resolve()
        main = make_main_repo(base / "main repo")
        worktree = base / "linked wt"
        git("-C", str(main), "worktree", "add", "-q", "--detach", str(worktree))
        self.layout_round_trip(worktree, trust_token(worktree, main))

    @unittest.skipUnless(HAS_GIT, "git is not installed")
    def test_bare_worktree_run_and_resume_mark_common_dir_untrusted(self):
        base = Path(self._tmp.name).resolve()
        bare, worktree = make_bare_worktree(base, make_main_repo(base / "main repo"))
        self.layout_round_trip(worktree, trust_token(worktree, base, bare))

    def test_path_set_failure_is_2_before_run_dir(self):
        with mock.patch.object(cr, "codex_untrusted_paths",
                               side_effect=cr.CrossReviewError(2, "layout")), \
                mock.patch.object(cr.subprocess, "Popen") as popen:
            with self.assertRaises(cr.CrossReviewError) as caught:
                cr.run_review("codex", self.repo, self.brief, None, None, self.env)
        self.assertEqual(caught.exception.code, 2)
        self.assertIsNone(caught.exception.run_dir)
        popen.assert_not_called()
        self.assertEqual(self.run_dirs(), [])

    def test_codex_run_through_real_builder_forces_repo_untrusted(self):
        run_dir = cr.run_review("codex", self.repo, self.brief, None, None, self.env)
        [rec] = self.records()
        self.assertEqual(rec["argv"], expected_codex(self.repo.resolve(), run_dir)[1:])

    def test_codex_resume_without_new_id_keeps_original(self):
        original = self.original("codex")
        self.env["FAKE_NEW_SESSION"] = ""
        new_dir = self.resume(original)
        self.assertEqual((new_dir / "session.txt").read_text().strip(), SESSION)

    def test_claude_resume_round_trip(self):
        original = self.original("claude")
        session = (original / "session.txt").read_text().strip()
        before = dir_digest(original)
        new_dir = self.resume(original)
        self.assertEqual(dir_digest(original), before)
        [rec] = self.records()
        self.assertEqual(rec["argv"], expected_claude_resume(session)[1:])
        self.assertNotIn("--session-id", rec["argv"])
        self.assertEqual(os.path.realpath(rec["cwd"]), os.path.realpath(self.repo))
        self.assertEqual((new_dir / "session.txt").read_text().strip(), session)

    def test_chained_resume_uses_new_run_metadata(self):
        original = self.original("codex")
        self.env["FAKE_NEW_SESSION"] = NEW_SESSION
        second = self.resume(original)
        third = self.resume(second, prompt="One more question.")
        self.assertEqual(len({original, second, third}), 3)
        rec = self.records()[-1]
        self.assertIn(NEW_SESSION, rec["argv"])

    def test_resume_keeps_model_and_effort_from_header(self):
        run_dir = cr.run_review("codex", self.repo, self.brief, "gpt-x", "high", self.env)
        new_dir = self.resume(run_dir)
        rec = self.records()[-1]
        self.assertEqual(rec["argv"], expected_codex_resume(new_dir, SESSION, "gpt-x",
                                                            "high", repo=self.repo)[1:])

    def test_depth_wins_before_metadata(self):
        env = dict(self.env, CROSS_REVIEW_DEPTH="")
        err = self.resume_error(self.tmpdir / "does-not-exist", env=env)
        self.assertEqual(err.code, 20)

    def test_actual_main_resume_with_depth_exits_20(self):
        env = dict(self.env, CROSS_REVIEW_DEPTH="1", TMPDIR=str(self.tmpdir))
        proc = subprocess.run([sys.executable, SCRIPT, "resume", "--run-dir",
                               "/nonexistent", "--prompt", "x"], env=env,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 20, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def corrupt(self, mutate):
        original = self.original("codex")
        mutate(original)
        return self.resume_error(original)

    def test_bad_session_is_24_without_spawn(self):
        cases = {
            "missing": lambda d: (d / "session.txt").unlink(),
            "empty": lambda d: (d / "session.txt").write_text(""),
            "invalid": lambda d: (d / "session.txt").write_text("not-a-uuid\n"),
            "symlink": lambda d: ((d / "session.txt").unlink(),
                                  (d / "session.txt").symlink_to(self.brief)),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.assertEqual(self.corrupt(mutate).code, 24)

    def test_bad_header_is_24_without_spawn(self):
        def rewrite_header(transform):
            def mutate(d):
                log = d / "run.log"
                first, rest = log.read_text().split("\n", 1)
                log.write_text(transform(first) + "\n" + rest)
            return mutate

        def with_field(key, value):
            def transform(first):
                data = json.loads(first)
                if value is KeyError:
                    del data[key]
                else:
                    data[key] = value
                return json.dumps(data)
            return transform

        cases = {
            "not json": rewrite_header(lambda first: "progress line"),
            "array": rewrite_header(lambda first: "[1, 2]"),
            "unknown schema": rewrite_header(with_field("schema_version", 99)),
            "no schema": rewrite_header(with_field("schema_version", KeyError)),
            "bad reviewer": rewrite_header(with_field("reviewer", "gemini")),
            "relative repo": rewrite_header(with_field("repo", "relative/path")),
            "missing repo": rewrite_header(with_field("repo", "/nonexistent/repo")),
            "empty model": rewrite_header(with_field("model", "")),
            "effort type": rewrite_header(with_field("effort", 3)),
            "option-like model": rewrite_header(with_field("model", "--dangerously-skip-permissions")),
            "option-like effort": rewrite_header(with_field("effort", "-x")),
            "no log": lambda d: (d / "run.log").unlink(),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.assertEqual(self.corrupt(mutate).code, 24)

    def test_unsafe_or_missing_run_dir_is_24(self):
        original = self.original("codex")
        link = self.tmpdir / "linked run"
        link.symlink_to(original)
        loose = self.original("codex")
        os.chmod(loose, 0o755)
        for run_dir in (self.tmpdir / "absent", link, self.brief, loose):
            with self.subTest(run_dir=run_dir.name):
                self.assertEqual(self.resume_error(run_dir).code, 24)

    def test_empty_prompt_is_2(self):
        original = self.original("codex")
        for prompt in ("", "   \n"):
            with self.subTest(prompt=prompt):
                self.assertEqual(self.resume_error(original, prompt=prompt).code, 2)

    def test_main_resume_prints_new_run(self):
        original = self.original("codex")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, self.env, clear=True), \
                redirect_stdout(out), redirect_stderr(err):
            code = cr.main(["resume", "--run-dir", str(original), "--prompt", "again"])
        self.assertEqual(code, 0, err.getvalue())
        new_dir = [d for d in self.run_dirs() if d != original][0]
        self.assertIn("run_dir: %s" % new_dir, out.getvalue())


class UnexpectedOSErrorTests(RunnerTestCase):
    def call_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cr.main(argv)
        return code, out.getvalue(), err.getvalue()

    def run_args(self):
        return ["run", "--reviewer", "claude", "--repo", str(self.repo),
                "--brief", str(self.brief)]

    def test_root_creation_failure_is_2(self):
        disk_full = OSError(28, "No space left on device")
        with mock.patch.object(cr.os, "mkdir", side_effect=disk_full), \
                mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CROSS_REVIEW_DEPTH", None)
            code, _, err = self.call_main(self.run_args())
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)
        self.assertIn("No space left", err)

    def test_artifact_write_failure_is_22(self):
        real_write = os.write

        def failing(fd, data):
            if data.startswith(b"fixture"):
                raise OSError(5, "Input/output error")
            return real_write(fd, data)

        os.environ.pop("CROSS_REVIEW_DEPTH", None)
        with mock.patch.object(cr.os, "write", side_effect=failing), \
                mock.patch.object(cr, "build_run_command", fake_builder(FAKE_CLAUDE)):
            code, out, err = self.call_main(self.run_args())
        self.assertEqual(code, 22)
        self.assertNotIn("Traceback", err)
        self.assertIn("run_dir:", out)

    def test_spawn_os_error_is_22(self):
        os.environ.pop("CROSS_REVIEW_DEPTH", None)
        real_popen = subprocess.Popen

        def popen(argv, *args, **kwargs):
            if argv[-1:] == ["--version"]:
                return real_popen(argv, *args, **kwargs)
            raise OSError(11, "Resource temporarily unavailable")

        with mock.patch.object(cr.subprocess, "Popen", side_effect=popen), \
                mock.patch.object(cr, "build_run_command", fake_builder(FAKE_CLAUDE)):
            code, out, err = self.call_main(self.run_args())
        self.assertEqual(code, 22)
        self.assertNotIn("Traceback", err)
        run_dir = Path(out.splitlines()[0].split(": ", 1)[1])
        self.assertIn("Resource temporarily unavailable", (run_dir / "run.log").read_text())


if __name__ == "__main__":
    unittest.main()
