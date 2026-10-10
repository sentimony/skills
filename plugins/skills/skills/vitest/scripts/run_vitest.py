#!/usr/bin/env python3
"""
Run Vitest through the package manager detected from lockfiles or package.json.

Usage:
    python <skill>/scripts/run_vitest.py --root .
    python <skill>/scripts/run_vitest.py --root . -- tests/example.test.ts
    python <skill>/scripts/run_vitest.py --root . --coverage -- tests/example.test.ts
    python <skill>/scripts/run_vitest.py --root . --test-name "formats currency"

Arguments after "--" are passed directly to Vitest.
"""

import argparse
import collections
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

from node_environment import build_environment, current_node_version, resolve_program


LOCKFILES = [
    ("pnpm-lock.yaml", "pnpm"),
    ("yarn.lock", "yarn"),
    ("bun.lockb", "bun"),
    ("bun.lock", "bun"),
    ("package-lock.json", "npm"),
    ("npm-shrinkwrap.json", "npm"),
]


# Upper bound on every line the runner renders from repository-chosen text. Such text has
# no length of its own - a package.json decides it - so an unbounded render lets the
# repository decide how much of a reader's context it occupies. A real invocation is an
# absolute binary path plus Vitest flags, and a real version range is a handful of
# characters, so this leaves several times the headroom either needs while still being a
# bound. It applies to the rendered value, not to the whole printed line: the fixed label
# in front of it and the truncation marker after it are the runner's own text.
RENDER_LIMIT = 1024


def apply_render_limit(text, limit=RENDER_LIMIT):
    """Cut a rendered value to the limit and state in the line that the cut happened.

    An applied cap is announced with the full length rather than left silent, so a cut
    line can never be mistaken for a whole one.
    """
    if len(text) <= limit:
        return text
    return f"{text[:limit]} ... [truncated, {len(text)} characters total]"


# The characters a declared Node version or version range is written with. Digits and the
# letters used by x/X wildcards and prerelease or build tags, the separators, the
# comparator and union operators, and the spaces between comparators - that is the whole
# set. It is a character set and not a grammar: it admits every ASCII letter and the
# space, so composition from it does not make a string a well-formed range. What it does
# exclude is every control character, every line separator and every invisible formatting
# codepoint, which is what makes a declaration inert to echo; and a declaration written
# outside the set carries no diagnostic value worth rendering.
DECLARED_VERSION_CHARACTERS = re.compile(r"[0-9A-Za-z.+ *,|<>=^~-]*")


def render_declared_version(value, limit=RENDER_LIMIT):
    """Render a version a repository declared, for a preflight blocker or warning.

    These lines echo package.json and version-file text back to the reader, so the text
    is repository data. The exact-version hints are gated by a fullmatch on a version, but
    engines.node is gated by parse_version, which is an unanchored search: a declaration
    of ">=99.0.0 " followed by an escape sequence, injection prose and three thousand
    characters of padding satisfies that gate and used to be interpolated in full. A
    declaration is therefore printed only when it is composed entirely of version-range
    characters and stays within the render limit; otherwise the line states its length
    instead of showing it, which keeps the warning itself (and so which projects get
    warned) exactly as it was. Those two conditions are the whole of what is enforced:
    the character set admits ASCII letters and spaces, so a rendered declaration is not
    promised to be a well-formed range, only to be bounded and free of the control
    characters and invisible codepoints that could repaint a terminal or misrepresent
    what was declared.
    """
    text = str(value)
    if len(text) > limit or not DECLARED_VERSION_CHARACTERS.fullmatch(text):
        return f"[unrenderable declaration, {len(text)} characters]"
    return text


def parse_version(value):
    if not value:
        return None
    match = re.search(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(value))
    if not match:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def is_exact_version(value):
    return bool(re.fullmatch(r"\s*v?\d+\.\d+\.\d+\s*", str(value or "")))


def matches_version_prefix(current, expected):
    return current[: len(expected)] == expected


def read_optional_text(path):
    """Read a version file, or return None when it is not readable as text.

    A version file is repository data, so "the bytes are not UTF-8" is a state it can be
    in, and one a lockless editor or a truncated checkout produces without anybody
    meaning to. It reads the same as a missing file here, which is the state the preflight
    below already handles.
    """
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def read_package_json(root):
    """Read package.json as a mapping, or return an empty one.

    Valid JSON is not a valid manifest, and package.json is repository data: the bytes
    need not be UTF-8 at all, the top level can be a list or a bare number, `scripts` can
    be a list, and a script body can be anything JSON allows. Nothing here is a way to run
    code - the runner would fail closed on a traceback - but a traceback is a worse
    diagnostic than the fallback the runner already has for a project it cannot read. Not
    readable, not decodable and not the documented shape are one answer, established at
    the boundary the way the inspector's read_json already does it, rather than three
    outcomes assumed at each use.
    """
    path = root / "package.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def scripts_mapping(package_json):
    """The package's scripts as a mapping, whatever the file actually held."""
    scripts = package_json.get("scripts") if isinstance(package_json, dict) else None
    return scripts if isinstance(scripts, dict) else {}


def mentions_vitest(body):
    """True when a script body is text that names Vitest.

    Every candidate check below asks whether a body contains `vitest`, which is a
    TypeError against a number and a wrong answer against a list. A body that is not
    text is not a body this runner can read, so it is not a candidate.
    """
    return isinstance(body, str) and "vitest" in body


def package_manager_field(package_json):
    value = package_json.get("packageManager") if package_json else None
    if not isinstance(value, str):
        return None
    manager = value.split("@", 1)[0]
    return manager if manager in {"npm", "pnpm", "yarn", "bun"} else None


def detect_package_manager(root, package_json=None):
    lockfile_managers = []
    for filename, manager in LOCKFILES:
        if (root / filename).exists() and manager not in lockfile_managers:
            lockfile_managers.append(manager)
    if len(lockfile_managers) == 1:
        return lockfile_managers[0]

    declared_manager = package_manager_field(package_json)
    if declared_manager:
        return declared_manager
    if lockfile_managers:
        return lockfile_managers[0]
    return "npm"


# Environment keys the runner accepts in front of the Vitest invocation. This is an
# allowlist, not a denylist, because the key space is unbounded: PATH decides which
# binary the shell resolves, the package-manager config namespaces (npm_config_*,
# NPM_CONFIG_*, BUN_CONFIG_*) redirect what a launcher fetches and executes, and the
# shell-startup and dynamic-loader hooks (ENV, BASH_ENV, LD_*, DYLD_*) make a process
# run code of their own before the program's entry point. Enumerating those is
# enumerating the redirections somebody happened to think of; enumerating the safe
# keys is a closed set. Every key below configures a run without changing which
# program runs: NODE_ENV, CI, DEBUG, FORCE_COLOR and NO_COLOR select behavior and
# output, TZ pins the timezone date tests depend on, and VITE_*/VITEST_* are the
# project's own configuration namespaces. Matching is case sensitive: environment
# names are case sensitive in the shell, each key above has exactly one canonical
# spelling, and under an allowlist an unrecognized case variant simply fails to match
# and is rejected, which is the safe direction.
SAFE_ENV_KEY = (
    r"(?:NODE_ENV|CI|TZ|DEBUG|FORCE_COLOR|NO_COLOR"
    r"|VITE_[A-Z0-9_]*|VITEST(?:_[A-Z0-9_]*)?)"
)

# The value class shared by the keys above. It is shell-inert on purpose: it excludes
# whitespace, quotes, parentheses, braces, brackets, glob characters and every character
# that could start a command, a substitution or a redirection. Equals signs are allowed
# inside a value so option-shaped settings still count.
SAFE_ENV_VALUE = r"[A-Za-z0-9_.:/@,+=-]*"

# NODE_OPTIONS is the one key whose value is constrained, because it is the one key
# that can make Node run other code. An auto-selected script is now spawned by this
# helper as environment plus argv, so NODE_OPTIONS applies to the process we launch and
# its preloads run before anything else, including when Vitest fails immediately. The
# general value class above would admit --require=./payload.cjs, --import=./payload.mjs,
# --experimental-loader=./payload.mjs and --inspect (which opens a debugger port), so
# only the memory-sizing options are accepted: their argument is an integer count of
# megabytes, so they cannot load code, open a port, or change module resolution. Both
# the hyphen and the underscore spelling are accepted because V8 treats them as the same
# flag, and a value is a single token because the value class excludes whitespace.
NODE_OPTIONS_VALUE = r"--max[-_](?:old|semi)[-_]space[-_]size=[0-9]+"

SAFE_ENV_ASSIGNMENT = (
    rf"(?:NODE_OPTIONS={NODE_OPTIONS_VALUE}|{SAFE_ENV_KEY}={SAFE_ENV_VALUE})"
)

# The invisible codepoints the runner refuses to carry into a line it renders. Defined
# once and used by both the argument class below and the test corpus, because a set
# spelled out separately in each place is a set that drifts: U+061C was in the CI grep's
# ancestor list and in neither of the other two for exactly that reason.
#
# It is the whole of the Unicode Bidi_Control property - U+061C ARABIC LETTER MARK,
# U+200E and U+200F, U+202A-U+202E, U+2066-U+2069 - plus the zero-width characters and
# the byte order mark (U+200B-U+200D, U+FEFF), which are not bidi controls but hide
# themselves the same way. Written as a range over U+200B-U+200F rather than as separate
# pieces because the two families are adjacent there. Ranges, not a list, so it stays
# free of literal invisibles in this file.
INVISIBLE_CODEPOINT_CLASS = "\u061c\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff"

DIRECT_SCRIPT_PATTERN = re.compile(
    # Optional environment prefix: one or more KEY=value pairs, with or without
    # cross-env. Both spellings share the same key rule; cross-env stays outside the
    # captured group because the parser applies the assignments itself instead of
    # running that program.
    r"(?:(?:cross-env[ \t]+)?"
    rf"(?P<env>(?:{SAFE_ENV_ASSIGNMENT}[ \t]+)+))?"
    # Optional launcher. Only launchers that run the binary named by their next
    # argument are accepted. Bare npm/pnpm/yarn/bun are rejected because they run a
    # package.json script of that name when one exists, so a script named "vitest"
    # shadows the binary. npm exec is rejected because npm keeps parsing its own
    # --package/-p flags after the positional, which redirects what it fetches and
    # runs. For the same reason the only npx flag allowed is --no-install: flags such
    # as -c or -p change what npx actually executes. Note that an accepted launcher is
    # not a guarantee that the locally installed Vitest runs: bare npx (npm exec) and
    # bunx install a missing binary from whatever registry the resolved config chain
    # selects, and that chain includes the repository's own .npmrc/bunfig.toml. Only
    # npx --no-install refuses to fetch; the pattern accepts both spellings.
    r"(?P<launcher>npx[ \t]+(?:--no-install[ \t]+)?|pnpm[ \t]+exec[ \t]+|bunx[ \t]+)?"
    # Vitest plus its arguments. Three families are excluded. First the shell operators,
    # which chain a command (semicolon, ampersand, pipe), redirect streams, or
    # substitute output (backtick, dollar sign). Second every control character and the
    # Unicode line separators, because these arguments are the one piece of accepted
    # body text the runner renders as a command: an escape sequence there would repaint
    # or clear the reader's terminal, a BEL would ring it, and a NUL cannot even be
    # handed to a child process. Horizontal tab is kept, since it is a legal separator
    # inside a script body, and so is the space. The ranges are C0 without tab
    # (\x00-\x08 and \x0a-\x1f, which also covers the newline and carriage return that
    # chain commands in sh), then DEL and C1 (\x7f-\x9f, which includes NEL at U+0085),
    # then the two Unicode line separators U+2028 and U+2029.
    #
    # Third the invisible formatting codepoints, spelled once in
    # INVISIBLE_CODEPOINT_CLASS above. These carry no control sequence, so they are
    # harmless to a terminal, but they break the property the render exists for. A
    # right-to-left override leaves argv exactly as written and reverses how the rendered
    # path is displayed, so the reader approves one path while the child receives another;
    # a zero-width character makes two different paths render identically. That is the
    # lossy-join failure by a different mechanism. Only the bidi *control* codepoints are
    # in that class, never letters, so an RTL --testNamePattern written in Arabic or
    # Hebrew still matches.
    r"vitest(?:[ \t]+(?P<args>[^&;|<>`$\x00-\x08\x0a-\x1f\x7f-\x9f\u2028\u2029"
    rf"{INVISIBLE_CODEPOINT_CLASS}]*))?"
)

ParsedScript = collections.namedtuple("ParsedScript", ("env", "launcher", "args"))


def parse_direct_vitest_script(body):
    """Return a ParsedScript for a direct script body, or None when it is not direct.

    A script body is direct when it only invokes Vitest. Package scripts are untrusted
    repository data: auto-selecting one means running whatever else it chains. Anything
    with shell chaining, redirection, substitution, a second binary, a launcher that
    runs something other than the binary named by its next argument, or an environment
    key outside the recognized safe set is not auto-run. Being direct is not the same as
    being pinned to the installed Vitest: when node_modules/.bin/vitest is missing, a
    bare `npx`/`bunx` launcher fetches the package from the registry the resolved
    .npmrc/bunfig.toml chain selects, so a direct script can still run a Vitest the
    repository chose. `npx --no-install` is the spelling that rules this out.

    Every separator in the pattern is explicit horizontal whitespace, and the match
    is a fullmatch over the stripped body, so a newline can never enter the command
    line: in sh a bare newline separates commands exactly like a semicolon.

    The pattern already describes the whole accepted shape, so the same match yields
    the pieces the runner executes: the environment assignments as a mapping, the
    launcher tokens as written, and the script's own Vitest arguments as argv. A
    `cross-env` prefix is dropped rather than executed: applying the assignments to
    the child process is exactly what that program does. Environment values contain no
    whitespace by construction, so splitting the prefix on whitespace is exact;
    arguments go through shlex so a quoted argument survives as one token, and a body
    whose quoting does not resolve is treated as not direct.
    """
    match = DIRECT_SCRIPT_PATTERN.fullmatch(str(body or "").strip())
    if not match:
        return None

    env = {}
    for assignment in (match.group("env") or "").split():
        key, _, value = assignment.partition("=")
        env[key] = value

    try:
        args = shlex.split(match.group("args") or "")
    except ValueError:
        return None

    return ParsedScript(env=env, launcher=(match.group("launcher") or "").split(), args=args)


def is_direct_vitest_script(body):
    """True when the body is a direct Vitest invocation the runner may auto-select."""
    return parse_direct_vitest_script(body) is not None


def find_script(package_json, requested, watch=False):
    """Return (script_name, skipped_indirect).

    skipped_indirect is True only when auto-selection found no direct script but
    did skip at least one indirect candidate, so the caller can explain the fallback.
    """
    scripts = scripts_mapping(package_json)
    if requested:
        if requested not in scripts:
            raise SystemExit(f"Script not found in package.json: {requested}")
        return requested, False

    skipped_indirect = False

    if watch:
        watch_names = ("test:watch", "vitest:watch", "watch:test", "watch")
        for name in watch_names:
            value = scripts.get(name)
            if mentions_vitest(value):
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False
        for name, value in scripts.items():
            if mentions_vitest(value) and "watch" in value:
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False
        for name, value in scripts.items():
            if mentions_vitest(value) and "run" not in value:
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False
    else:
        for name in ("test:unit", "test:vitest", "vitest", "test"):
            if mentions_vitest(scripts.get(name)):
                if not is_direct_vitest_script(scripts[name]):
                    skipped_indirect = True
                    continue
                return name, False
        for name, value in scripts.items():
            if mentions_vitest(value):
                if not is_direct_vitest_script(value):
                    skipped_indirect = True
                    continue
                return name, False

    return None, skipped_indirect


def check_node_version(root, package_json):
    current = current_node_version(root)
    current_version = parse_version(current)
    blockers = []
    warnings = []

    engines = package_json.get("engines", {}) if package_json else {}
    volta = package_json.get("volta", {}) if package_json else {}
    exact_hints = {
        ".nvmrc": read_optional_text(root / ".nvmrc"),
        ".node-version": read_optional_text(root / ".node-version"),
        "package.json volta.node": volta.get("node") if isinstance(volta, dict) else None,
    }

    if not current:
        if any(exact_hints.values()) or (isinstance(engines, dict) and engines.get("node")):
            blockers.append("Project declares a Node version, but `node -v` is not available.")
        return blockers, warnings

    for source, expected in exact_hints.items():
        expected_version = parse_version(expected)
        if is_exact_version(expected) and current_version and expected_version and current_version != expected_version:
            blockers.append(
                f"Project expects Node {render_declared_version(expected)} from {source}, "
                f"but current Node is {current}."
            )

    engines_node = engines.get("node") if isinstance(engines, dict) else None
    engine_version = parse_version(engines_node)
    if current_version and engine_version and isinstance(engines_node, str):
        stripped = engines_node.strip()
        # The declaration is rendered, not interpolated: the gate above is parse_version,
        # an unanchored search, so everything after the version-looking substring is
        # arbitrary repository text that this line would otherwise print in full.
        declared = render_declared_version(engines_node)
        # Match the inspector's strict-boundary semantics: >= accepts equality,
        # > does not.
        if stripped.startswith(">=") and current_version < engine_version:
            warnings.append(
                f"package.json engines.node is {declared}, but current Node is {current}."
            )
        elif (
            stripped.startswith(">")
            and not stripped.startswith(">=")
            and current_version <= engine_version
        ):
            warnings.append(
                f"package.json engines.node is {declared}, but current Node is {current}."
            )
        elif re.fullmatch(r"\s*v?\d+(?:\.\d+){0,2}\s*", engines_node) and not matches_version_prefix(current_version, engine_version):
            warnings.append(
                f"package.json engines.node is {declared}, but current Node is {current}."
            )

    return blockers, warnings


def resolve_local_vitest(root):
    local_vitest = root / "node_modules" / ".bin" / "vitest"
    if not local_vitest.exists():
        raise SystemExit(
            "No suitable Vitest command found. Add a package.json script that runs Vitest "
            "or install Vitest locally so node_modules/.bin/vitest exists."
        )
    return str(local_vitest)


def build_command(root, manager, explicit_script, parsed_script, vitest_args, watch=False):
    """Return (command, environment overrides) for the run.

    Only an explicit --script goes through the package manager. That is the user naming
    a script, and it is the only path where the pre<script>/post<script> lifecycle npm
    and yarn run automatically is acceptable. An auto-selected script must never take
    it: the predicate validates the named script's body and nothing else, so a
    package.json could pair an accepted "test" with a "pretest" that runs anything at
    all and bypass the whole check through an adjacent key.

    An auto-selected script therefore runs as the parsed environment plus argv, spawned
    directly with no shell and no package manager in between.
    """
    if explicit_script:
        if manager == "npm":
            return ["npm", "run", explicit_script, "--", *vitest_args], {}
        if manager == "yarn":
            return ["yarn", explicit_script, *vitest_args], {}
        if manager == "pnpm":
            return ["pnpm", explicit_script, *vitest_args], {}
        if manager == "bun":
            return ["bun", "run", explicit_script, *vitest_args], {}

    if parsed_script is not None:
        if parsed_script.launcher:
            # The launcher stays exactly as the script wrote it. Substituting the local
            # binary would change which Vitest runs, and the .npmrc/bunfig.toml caveat
            # documented above applies to it unchanged.
            command = [*parsed_script.launcher, "vitest"]
        else:
            # A bare `vitest` token in a package script only resolves through the PATH
            # the package manager injects, and this path no longer has one.
            command = [resolve_local_vitest(root)]
        # The script's own arguments come first so this helper's arguments can still
        # override them, the way an appended argument does for Vitest.
        return [*command, *parsed_script.args, *vitest_args], dict(parsed_script.env)

    return [resolve_local_vitest(root), "watch" if watch else "run", *vitest_args], {}


def render_command(command, limit=RENDER_LIMIT):
    """Render argv as a single line that is accurate and length-bounded.

    Quoting is per element, so the line shows the same word split the child actually
    receives. A plain join does not: `--testNamePattern "formats currency"` in a script
    body reaches Vitest as three arguments but joins back into four tokens, which reads
    as a different command and does not survive a copy-paste. An accepted script also
    contributes its own arguments here, and those are repository-controlled text, so the
    result is capped as well.
    """
    return apply_render_limit(" ".join(shlex.quote(part) for part in command), limit)


def render_script_environment(keys, limit=RENDER_LIMIT):
    """Render the key names of an accepted script's environment prefix.

    Key names only; a value from the script body is never rendered. A key name is not
    fixed text either: VITE_* and VITEST_* are open-ended namespaces, so a repository
    chooses both the names and their length. The key rule bounds each name to uppercase
    letters, digits and underscores, so the line carries no control characters, no
    invisible formatting codepoints and nothing that could chain or redirect anything,
    but readable prose spelled in that alphabet is still prose, so the line takes the same
    length bound as the command line one line above it.
    """
    return apply_render_limit(", ".join(sorted(keys)), limit)


def main():
    parser = argparse.ArgumentParser(description="Run Vitest with package-manager detection")
    parser.add_argument("--root", default=".", help="Project root (default: current directory)")
    parser.add_argument("--manager", choices=["npm", "pnpm", "yarn", "bun"], help="Override package manager")
    parser.add_argument("--script", help="Package.json script to run instead of auto-detecting")
    parser.add_argument("--coverage", action="store_true", help="Add --coverage")
    parser.add_argument("--watch", action="store_true", help="Use watch mode")
    parser.add_argument("--test-name", help="Filter tests by name pattern")
    parser.add_argument("--skip-node-check", action="store_true", help="Skip project Node version preflight")
    parser.add_argument("--dry-run", action="store_true", help="Print command without running it")
    parser.add_argument("vitest_args", nargs=argparse.REMAINDER, help="Arguments after -- are passed to Vitest")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Root is not a directory: {root}")

    vitest_args = list(args.vitest_args)
    if vitest_args and vitest_args[0] == "--":
        vitest_args = vitest_args[1:]
    if args.coverage:
        vitest_args.insert(0, "--coverage")
    if args.test_name:
        vitest_args = ["--testNamePattern", args.test_name, *vitest_args]

    package_json = read_package_json(root)
    if not args.skip_node_check:
        blockers, warnings = check_node_version(root, package_json)
        for warning in warnings:
            print(f"Warning: {warning}")
        if blockers:
            for blocker in blockers:
                print(blocker)
            print("Switch to the project Node version before running Vitest, for example with nvm/fnm/Volta/mise/asdf.")
            print("Use --skip-node-check to bypass this check.")
            sys.exit(1)

    manager = args.manager or detect_package_manager(root, package_json)
    script_name, skipped_indirect = find_script(package_json, args.script, watch=args.watch)
    scripts = scripts_mapping(package_json)
    parsed_script = None
    if args.script:
        requested_body = scripts.get(args.script)
        if not is_direct_vitest_script(requested_body):
            print(
                "Warning: SCRIPT_NOT_DIRECT (explicit --script runs a package script "
                "that does more than invoke Vitest)"
            )
    elif script_name:
        # find_script only returns a body the parser accepted, so this always parses;
        # if it ever did not, the run falls back to the local binary rather than to the
        # package manager.
        parsed_script = parse_direct_vitest_script(scripts.get(script_name))
    command, script_env = build_command(
        root, manager, args.script, parsed_script, vitest_args, watch=args.watch
    )
    # The environment is built before the command is rendered, because resolving the
    # program is part of deciding what the command is: the Command: line has to name the
    # file that will actually be executed, not a name a PATH lookup will decide later.
    environment = build_environment(root, script_env)
    command = resolve_program(command, environment.get("PATH"), root)
    # Printed only after build_command confirmed the local binary exists, so the note
    # never promises a fallback that is about to fail.
    if skipped_indirect:
        print(
            "Note: SCRIPT_NOT_DIRECT; using node_modules/.bin/vitest. "
            "Pass --script <name> to run the package script instead."
        )

    print(f"Root: {root}")
    print(f"Command: {render_command(command)}")
    if script_env:
        print(f"Script environment: {render_script_environment(script_env)}")
    if args.dry_run:
        return

    # The parsed assignments are applied as process environment, never through a shell.
    result = subprocess.run(command, cwd=root, env=environment)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
