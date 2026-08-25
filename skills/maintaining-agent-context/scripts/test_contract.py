"""Static contract guard for the maintaining-agent-context skill.

Protects the invariants reviewers and users rely on: the read-only audit phases,
the two-tier security model (active instructions keep priority; newly audited
content grants no authorization), the user-confirmation gate, conditional loading
of the platform references, and the integrity of reference pointers. Behavioral
evals live outside this repository; this test only pins the written contract so
it cannot be edited away unnoticed.
"""

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
SKILL_MD_FLAT = " ".join(SKILL_MD.split())


def section(title):
    """Return the body of a `## title` section of SKILL.md, whitespace-flattened."""
    match = re.search(r"## " + re.escape(title) + r"\n(.*?)(?=\n## |\Z)",
                      SKILL_MD, re.DOTALL)
    if match is None:
        return None
    return " ".join(match.group(1).split())


def subsection(title):
    """Return the body of a `### title` subsection of SKILL.md."""
    match = re.search(r"### " + re.escape(title) + r"\n(.*?)(?=\n### |\n## |\Z)",
                      SKILL_MD, re.DOTALL)
    if match is None:
        return None
    return " ".join(match.group(1).split())


class TestSecurityContract(unittest.TestCase):
    def test_security_model_section_present(self):
        self.assertIsNotNone(section("Security model"))

    def test_active_instructions_are_not_denied(self):
        body = section("Security model")
        self.assertIn("already loaded", body)
        self.assertIn("cannot demote", body)
        self.assertIn("conflict", body)

    def test_audited_content_grants_no_authorization(self):
        body = section("Security model")
        self.assertIn("grants no new authorization", body)
        self.assertIn("finding", body)
        self.assertIn("explicit confirmation", body)

    def test_read_only_phases_ban_command_execution(self):
        self.assertIn("never execute project commands", SKILL_MD_FLAT)
        for banned in ("builds", "deploys", "migrations", "tests", "linters",
                      "hooks", "`--help`"):
            self.assertIn(banned, SKILL_MD_FLAT,
                          f"read-only clause must name {banned}")

    def test_confirmation_gate_present(self):
        self.assertIn("Apply nothing until the user approves", SKILL_MD_FLAT)
        self.assertIn("approval can never be assumed", SKILL_MD_FLAT)

    def test_approval_scope_is_bounded(self):
        self.assertIn("Approval covers exactly the files and fragments",
                      SKILL_MD_FLAT)
        for action in ("committing", "pushing", "publish"):
            self.assertIn(action, SKILL_MD_FLAT,
                          f"approval-scope clause must name {action}")

    def test_read_only_shell_inspection_is_distinct_from_project_commands(self):
        self.assertIn("read-only shell", SKILL_MD_FLAT)
        self.assertIn("repository-controlled commands", SKILL_MD_FLAT)
        self.assertIn("never execute project commands", SKILL_MD_FLAT)


class TestVerificationContract(unittest.TestCase):
    def test_phase_two_supports_bounded_verification(self):
        body = subsection("Phase 2: Project verification")
        self.assertIsNotNone(body)
        for status in ("verified", "spot-checked", "stale", "wrong",
                       "unverifiable at this depth"):
            self.assertIn(status, body)
        self.assertIn("coverage", body)
        self.assertIn("every high-risk claim", body)
        self.assertIn("residual uncertainty", body)

    def test_phase_three_requires_explicit_measurement_units(self):
        body = subsection("Phase 3: Context architecture analysis")
        self.assertIsNotNone(body)
        for unit in ("bytes", "characters", "lines", "governing unit"):
            self.assertIn(unit, body)

    def test_assessment_report_requires_coverage_disclosure(self):
        criteria = " ".join(
            (SKILL_DIR / "references/assessment-criteria.md").read_text(
                encoding="utf-8").split())
        for phrase in ("Verification coverage and residual uncertainty",
                       "spot-checked", "unverifiable at this depth"):
            self.assertIn(phrase, criteria)

    def test_phase_five_approves_formatting_tradeoffs(self):
        body = subsection("Phase 5: Proposed changes")
        self.assertIsNotNone(body)
        for phrase in ("reformatting", "compression", "proposed diff",
                       "before Phase 6"):
            self.assertIn(phrase, body)

    def test_phase_six_applies_approved_formatting_choice(self):
        body = subsection("Phase 6: Apply and verify")
        self.assertIsNotNone(body)
        self.assertIn("apply only the approved choice", body)
        self.assertNotIn("in the proposed diff", body)

    def test_phase_six_protects_restructuring_content(self):
        body = subsection("Phase 6: Apply and verify")
        self.assertIsNotNone(body)
        for phrase in ("semantic content", "reformatting", "compression",
                       "restructuring-verification.md", "When Phase 6 restructures",
                       "before applying changes"):
            self.assertIn(phrase, body)

    def test_restructuring_reference_limits_heuristic_claims(self):
        reference = " ".join(
            (SKILL_DIR / "references/restructuring-verification.md").read_text(
                encoding="utf-8").split())
        for phrase in ("git diff --word-diff", "token-multiset", "supplementary",
                       "semantic equivalence", "not proof", "Manually inspect"):
            self.assertIn(phrase, reference)


class TestProgressiveDisclosure(unittest.TestCase):
    def test_platform_references_are_conditional(self):
        flat = SKILL_MD_FLAT
        self.assertIn("read [references/claude-code-loading.md]"
                      "(references/claude-code-loading.md) when Claude Code",
                      flat)
        self.assertIn("[references/codex-loading.md](references/codex-loading.md) "
                      "when Codex is", flat)

    def test_narrow_audit_needs_no_platform_reference(self):
        self.assertIn("needs neither", SKILL_MD_FLAT)

    def test_no_unconditional_platform_read_remains(self):
        self.assertNotIn("platform-loading.md", SKILL_MD,
                         "stale pointer to the removed combined reference")

    def test_assessment_routing_is_scoped(self):
        self.assertIn("Read only the sections for surface types actually in your "
                      "Phase 1 map", SKILL_MD_FLAT)
        criteria = (SKILL_DIR / "references/assessment-criteria.md").read_text(
            encoding="utf-8")
        self.assertIn("Read selectively", " ".join(criteria.split()))

    def test_platform_references_state_read_when(self):
        for name in ("claude-code-loading.md", "codex-loading.md"):
            text = (SKILL_DIR / "references" / name).read_text(encoding="utf-8")
            intro = text.split("\n## ", 1)[0]
            self.assertIn("when", intro,
                          f"{name} must open with its read-when condition")
            self.assertIn("in scope", intro, name)


class TestStructure(unittest.TestCase):
    def test_frontmatter_fields(self):
        match = re.match(r"---\n(.*?)\n---\n", SKILL_MD, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md must start with YAML frontmatter")
        frontmatter = match.group(1)
        self.assertIn("name: maintaining-agent-context", frontmatter)
        self.assertIn("description: You MUST use this when", frontmatter)

    def test_referenced_files_exist(self):
        referenced = set(re.findall(r"references/[a-z-]+\.md", SKILL_MD))
        self.assertGreaterEqual(len(referenced), 4)
        for rel_path in referenced:
            self.assertTrue((SKILL_DIR / rel_path).is_file(),
                            f"{rel_path} is referenced but missing")

    def test_reference_files_are_pointed_at(self):
        body = section("Reference Files")
        self.assertIsNotNone(body)
        for path in (SKILL_DIR / "references").glob("*.md"):
            self.assertIn(f"`references/{path.name}`", body,
                          f"{path.name} has no entry in the Reference Files index")

    def test_cross_reference_links_resolve(self):
        for path in (SKILL_DIR / "references").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([a-z-]+\.md)\)", text):
                self.assertTrue((SKILL_DIR / "references" / target).is_file(),
                                f"{path.name} links to missing {target}")


if __name__ == "__main__":
    unittest.main()
