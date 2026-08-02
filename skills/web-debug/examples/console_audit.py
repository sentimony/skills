import json
import re
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# Example: checkpointed multi-page console audit. Each route keeps its result if
# another route fails, so a long crawl does not discard prior observations.

BASE = 'http://127.0.0.1:5173'  # Confirm the host and port from server startup logs
ROUTES = ['/', '/about', '/settings']  # Replace with your routes
LOGIN = None  # Or e.g. {'path': '/login', 'user': '...', 'password': '...'} for auth-gated apps
# Set this to an element that exists only after hydration; never an SSR-present one.
# While it is None, wait_until_hydrated() does nothing: no hydration is verified anywhere
# in this run, and the 'hydration-error' status below can never be reported.
CLIENT_ONLY_SELECTOR = None
OUTPUT = Path('/tmp/console-audit.json')  # Delete this file to force a fresh crawl

NOISE_TYPES = ('log', 'debug', 'info')  # Dev-server noise; signal is warning/error/pageerror
MAX_LEN = 500  # Truncate verbose framework warnings
MAX_MESSAGES = 200  # Bound each route's checkpoint even when a page emits repeated noise

# Everything the report prints comes from the page or from a checkpoint file, so it is
# untrusted data - and it is printed to a terminal, which acts on some of it. Control
# characters repaint, clear, or recolor the screen and ring the bell; a newline forges a
# report line of its own ("=== /admin: ok, 0 messages ==="); the bidi controls and
# zero-width characters leave the text as written but change how it reads. They are
# escaped rather than dropped, so nothing silently disappears from the evidence.
UNSAFE_TO_PRINT = re.compile(
    '[\x00-\x1f\x7f-\x9f\u061c\u200b-\u200f\u2028\u2029\u202a-\u202e\u2066-\u2069\ufeff]')

# `type(error).__name__` and nothing else. Bounding it here is what lets the report print
# it directly: a checkpoint could otherwise supply 10,000 characters of terminal escapes
# under a status this script treats as its own.
ERROR_CODE = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,63}')


def printable(text):
    """Escape what a terminal would act on, leaving ordinary text (accents included) alone."""
    return UNSAFE_TO_PRINT.sub(lambda match: f'\\u{ord(match.group()):04x}', text)


def wait_until_hydrated(page):
    """App-specific hydration gate. SSR markup exists before handlers are attached.

    Replace with either a client-only selector, or a harmless probe: act on a concrete
    control, assert the observable change, then restore it.
    """
    if CLIENT_ONLY_SELECTOR:
        page.wait_for_selector(CLIENT_ONLY_SELECTOR, timeout=5000)


def settle_dev_server_reload(page):
    """Absorb the cold dev-server reload that wipes freshly typed form values.

    A separate hazard from hydration: Vite dependency re-optimization / HMR reloads the
    component ~500ms after the first load, so a form filled before it lands is reset even
    though handlers were already attached. Prefer the concrete signal described in SKILL.md
    ("Cold dev-server start can reset forms") - a second `framenavigated` or the duplicate
    module fetch - or pre-warm the URL; this fixed pause is the fallback when neither
    signal has been identified during recon.
    """
    page.wait_for_timeout(1500)


def usable_result(value):
    """A resumed route entry is only usable if it has the shape this script itself writes.

    The error_code key must be present whatever the status says: the report below reads
    result['error_code'] directly, and an entry that merely omits the key would be skipped
    by the crawl loop (its status already says 'ok') and only raise KeyError at report time.
    'ok' and 'incomplete' carry it as None: the script leaves it None until an error branch
    overwrites the status away from 'incomplete'. 'hydration-error' and
    'navigation-error' always carry the failing exception's class name, which is why an
    error code has to be a bounded identifier here: the report prints it directly, so a
    checkpoint could otherwise hand it 10,000 characters of terminal escapes under a
    status this script treats as its own.

    Messages and counts are checked against the bounds the writer below actually
    enforces, not merely for being a dict of numbers. add_message() escapes every message
    with printable() and truncates it to MAX_LEN and stops appending at MAX_MESSAGES, and
    counted() only ever emits counts of one or more - so a count of zero, a total past
    MAX_MESSAGES, an over-long key, or a key still carrying a raw escape sequence
    describes a file this script could not have written. Accepting those would let a
    hand-edited or planted checkpoint mark routes 'ok' - skipping them entirely - while
    the report prints attacker-chosen text as if the crawl had observed it.
    """
    if not isinstance(value, dict):
        return False
    status = value.get('status')
    if status not in ('ok', 'incomplete', 'hydration-error', 'navigation-error'):
        return False
    if 'error_code' not in value:
        return False
    error_code = value['error_code']
    if status in ('ok', 'incomplete'):
        if error_code is not None:
            return False
    elif not isinstance(error_code, str) or not ERROR_CODE.fullmatch(error_code):
        return False
    counts = value.get('messages')
    if not isinstance(counts, dict):
        return False
    total = 0
    for message, count in counts.items():
        if not isinstance(message, str) or len(message) > MAX_LEN:
            return False
        if UNSAFE_TO_PRINT.search(message):
            return False
        # isinstance(True, int) is True, and the report sums these.
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            return False
        total += count
    return total <= MAX_MESSAGES


def load_checkpoint():
    """Resume a previous crawl's results, but only when they describe this same crawl.

    A checkpoint from a different BASE or ROUTES list, or one that fails to parse,
    is not a partial version of this run - loading it anyway could silently skip
    routes that were never actually crawled under this configuration. Any mismatch
    or read error starts clean instead, and individual route entries that don't have
    this script's shape are dropped rather than crashing the crawl or the report.

    Entries are also restricted to the routes this run crawls. The header check only
    proves the stored ROUTES list matches; a file can still carry result entries for
    routes outside it, and those would be printed in the report as observations this run
    never made.
    """
    if not OUTPUT.exists():
        return {}
    try:
        checkpoint = json.loads(OUTPUT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    if not isinstance(checkpoint, dict):
        return {}
    if checkpoint.get('base') != BASE or checkpoint.get('routes') != ROUTES:
        return {}
    previous_results = checkpoint.get('results')
    if not isinstance(previous_results, dict):
        return {}
    return {route: value for route, value in previous_results.items()
            if route in ROUTES and usable_result(value)}


results = load_checkpoint()
if results:
    # Resume is silent otherwise: re-running after a fix would reprint the old results
    # verbatim and look like the fix changed nothing.
    finished = sum(1 for route in ROUTES if results.get(route, {}).get('status') == 'ok')
    print(f'Resumed {OUTPUT}: {finished} of {len(ROUTES)} route(s) already finished and '
          f'will be skipped; delete that file to force a fresh crawl.')


def write_checkpoint():
    """Persist bounded route observations before any browser cleanup."""
    checkpoint = {'base': BASE, 'routes': ROUTES, 'results': results}
    temporary = OUTPUT.with_suffix(OUTPUT.suffix + '.tmp')
    temporary.write_text(json.dumps(checkpoint, indent=2, sort_keys=True), encoding='utf-8')
    temporary.replace(OUTPUT)  # Atomic: a kill mid-write cannot truncate OUTPUT


def counted(messages):
    """Deduplicate a route's bounded message list."""
    counts = {}
    for message in messages:
        counts[message] = counts.get(message, 0) + 1
    return counts


with sync_playwright() as p:
    browser = None
    context = None
    try:
        browser = p.chromium.launch(headless=True)
        # One context for the whole audit so a login session carries across routes.
        context = browser.new_context()

        if LOGIN:
            page = context.new_page()
            try:
                page.goto(BASE + LOGIN['path'], wait_until='domcontentloaded')
                # This is the highest-cost site for a false negative: without a session
                # the entire crawl is blocked. Two independent hazards, two steps: a fixed
                # sleep can't prove the form's handlers are attached, so gate on hydration
                # first; hydration in turn says nothing about the cold dev-server reload,
                # which can land after the handlers are attached and wipe what was typed.
                wait_until_hydrated(page)
                settle_dev_server_reload(page)
                page.get_by_label('Email').fill(LOGIN['user'])  # Adjust locators to the app
                page.get_by_label('Password').fill(LOGIN['password'])
                page.get_by_role('button', name='Log in').click()
                # After the redirect the form is gone - don't assert input_value() here.
                page.wait_for_url(lambda url: LOGIN['path'] not in url)
            finally:
                page.close()

        for route in ROUTES:
            if results.get(route, {}).get('status') == 'ok':
                continue  # Already recorded a clean run for this route in a resumed checkpoint

            messages = []
            # 'ok' has to mean "finished", not "started": the finally below persists this
            # entry unconditionally, and a resumed crawl skips whatever says 'ok'.
            result = {'status': 'incomplete', 'messages': {}, 'error_code': None}
            results[route] = result
            page = None
            route_finished = False  # Reset per route: a prior route's success must not leak in

            def add_message(message):
                # Escape before truncating, so the length bound applies to what is
                # printed rather than to text that grows on its way to the terminal.
                if len(messages) < MAX_MESSAGES:
                    messages.append(printable(message)[:MAX_LEN])

            try:
                # A fresh page per route prevents logs from mixing between pages.
                page = context.new_page()
                page.on('console', lambda msg: msg.type not in NOISE_TYPES
                        and add_message(f'[console.{msg.type}] {msg.text}'))
                page.on('pageerror', lambda err: add_message(f'[pageerror] {err}'))
                # requestfailed is a hint, not proof - see "Interpreting Failures" in SKILL.md.
                page.on('requestfailed', lambda req: add_message(
                    f'[requestfailed] {req.url} {req.failure or "unknown"}'))
                page.on('response', lambda res: res.status >= 400
                        and add_message(f'[http {res.status}] {res.url}'))

                page.goto(BASE + route, wait_until='domcontentloaded')
                try:
                    # This proves only that SSR or initial client rendering produced text.
                    page.wait_for_function(
                        'document.body.innerText.trim().length > 0', timeout=5000)
                except PlaywrightTimeoutError:
                    pass  # Text-free canvas/WebGL pages can still produce useful audit evidence.

                try:
                    # Gate: block until the app is interactive. Choose CLIENT_ONLY_SELECTOR
                    # during recon; there is no generic hydration marker.
                    wait_until_hydrated(page)
                except PlaywrightTimeoutError as error:
                    result['status'] = 'hydration-error'
                    result['error_code'] = type(error).__name__
                # Collection window, not a gate: even once hydration is confirmed above,
                # hydration warnings and async errors still arrive after domcontentloaded,
                # so keep this fixed pause purely to collect late console output.
                page.wait_for_timeout(2500)
                # Only a flag here, not the status: teardown below still produces messages
                # for this route, so 'ok' cannot be decided before they are counted.
                route_finished = True
            except Exception as error:
                result['status'] = 'navigation-error'
                result['error_code'] = type(error).__name__
                add_message(f'[navigation-error] {error}')
            finally:
                # Close first: handlers can still fire during teardown, and those
                # events belong to this route's list.
                if page is not None:
                    try:
                        page.close()
                    except PlaywrightError:
                        pass
                # Count first, promote last: Ctrl-C is not an Exception, so an interrupt
                # anywhere above - page.close() is a real IPC round-trip - arrives here
                # with 'incomplete' still set. Ordering matters: the status can never say
                # 'ok' without the messages that back it. 'hydration-error' and
                # 'navigation-error' are not 'incomplete', so they are never promoted.
                result['messages'] = counted(messages)
                if route_finished and result['status'] == 'incomplete':
                    result['status'] = 'ok'
                write_checkpoint()
    finally:
        # A final write preserves the last completed route even if context cleanup fails.
        write_checkpoint()
        if context is not None:
            try:
                context.close()
            finally:
                if browser is not None:
                    browser.close()
        elif browser is not None:
            browser.close()

for route, result in results.items():
    counts = result['messages']
    total = sum(counts.values())
    print(f"\n=== {route}: {result['status']}, {total} messages, {len(counts)} unique ===")
    if result['error_code']:
        print(f"  error: {result['error_code']}")
    for message, count in sorted(counts.items(), key=lambda item: -item[1]):
        prefix = f'{count}x ' if count > 1 else ''
        print(f'  {prefix}{message}')
