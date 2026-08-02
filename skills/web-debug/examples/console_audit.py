import json
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# Example: checkpointed multi-page console audit. Each route keeps its result if
# another route fails, so a long crawl does not discard prior observations.

BASE = 'http://127.0.0.1:5173'  # Confirm the host and port from server startup logs
ROUTES = ['/', '/about', '/settings']  # Replace with your routes
LOGIN = None  # Or e.g. {'path': '/login', 'user': '...', 'password': '...'} for auth-gated apps
CLIENT_ONLY_SELECTOR = None  # An element that exists only after hydration; never an SSR-present one
OUTPUT = Path('/tmp/console-audit.json')

NOISE_TYPES = ('log', 'debug', 'info')  # Dev-server noise; signal is warning/error/pageerror
MAX_LEN = 500  # Truncate verbose framework warnings
MAX_MESSAGES = 200  # Bound each route's checkpoint even when a page emits repeated noise


def wait_until_hydrated(page):
    """App-specific hydration gate. SSR markup exists before handlers are attached.

    Replace with either a client-only selector, or a harmless probe: act on a concrete
    control, assert the observable change, then restore it.
    """
    if CLIENT_ONLY_SELECTOR:
        page.wait_for_selector(CLIENT_ONLY_SELECTOR, timeout=5000)


def load_checkpoint():
    """Resume a previous crawl's results, but only when they describe this same crawl.

    A checkpoint from a different BASE or ROUTES list, or one that fails to parse,
    is not a partial version of this run - loading it anyway could silently skip
    routes that were never actually crawled under this configuration. Any mismatch
    or read error starts clean instead.
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
    return previous_results


results = load_checkpoint()


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
                # the entire crawl is blocked. A fixed sleep can't prove the form's
                # handlers are attached (cold dev-server HMR reload ~500ms after load can
                # also wipe freshly typed values - see SKILL.md) - gate on hydration instead.
                wait_until_hydrated(page)
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
            result = {'status': 'ok', 'messages': {}, 'error_code': None}
            results[route] = result
            page = None

            def add_message(message):
                if len(messages) < MAX_MESSAGES:
                    messages.append(message[:MAX_LEN])

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
                result['messages'] = counted(messages)
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
