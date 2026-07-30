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
HYDRATED_SELECTOR = None  # Set an app-specific interactive selector when interactions need hydration
OUTPUT = Path('/tmp/console-audit.json')

NOISE_TYPES = ('log', 'debug', 'info')  # Dev-server noise; signal is warning/error/pageerror
MAX_LEN = 500  # Truncate verbose framework warnings
MAX_MESSAGES = 200  # Bound each route's checkpoint even when a page emits repeated noise

results = {}


def write_checkpoint():
    """Persist bounded route observations before any browser cleanup."""
    OUTPUT.write_text(json.dumps(results, indent=2, sort_keys=True), encoding='utf-8')


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
                # Cold dev-server starts can wipe typed values (HMR reload ~500ms after
                # load) - wait for render to settle before filling; see SKILL.md.
                page.wait_for_timeout(1500)
                page.get_by_label('Email').fill(LOGIN['user'])  # Adjust locators to the app
                page.get_by_label('Password').fill(LOGIN['password'])
                page.get_by_role('button', name='Log in').click()
                # After the redirect the form is gone - don't assert input_value() here.
                page.wait_for_url(lambda url: LOGIN['path'] not in url)
            finally:
                page.close()

        for route in ROUTES:
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

                if HYDRATED_SELECTOR:
                    try:
                        # Choose this selector during recon; there is no generic hydration marker.
                        page.wait_for_selector(HYDRATED_SELECTOR, timeout=5000)
                    except PlaywrightTimeoutError as error:
                        result['status'] = 'hydration-error'
                        result['error_code'] = type(error).__name__
                # Fixed pause is legitimate here: hydration warnings and async errors
                # arrive after domcontentloaded.
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
