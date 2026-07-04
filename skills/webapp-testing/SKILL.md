---
name: webapp-testing
description: Use when the user needs to test, verify, or debug a local web application in a browser — covers frontend functionality checks, UI behavior debugging, capturing screenshots, and reading browser console logs via Playwright.
license: Apache-2.0
compatibility: Requires Python and Playwright
metadata:
  version: "1.1"
---

# Web Application Testing

To test local web applications, write native Python Playwright scripts.

**Helper Scripts Available**:
- `scripts/with_server.py` - Manages server lifecycle (supports multiple servers)

**Always run scripts with `--help` first** to see usage. DO NOT read the source until you try running the script first and find that a customized solution is absolutely necessary. These scripts can be very large and thus pollute your context window. They exist to be called directly as black-box scripts rather than ingested into your context window.

## Decision Tree: Choosing Your Approach

```
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly to identify selectors
    │         ├─ Success → Write Playwright script using selectors
    │         └─ Fails/Incomplete → Treat as dynamic (below)
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Run: python scripts/with_server.py --help
        │        Then use the helper + write simplified Playwright script
        │
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for rendered content (see Waiting Strategy)
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## Example: Using with_server.py

To start a server, run `--help` first, then use the helper:

```bash
python scripts/with_server.py --server "npm run dev" --port 5173 -- python your_automation.py
```

To create an automation script, include only Playwright logic (servers are managed automatically):
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True) # Always launch chromium in headless mode
    page = browser.new_page()
    page.on('console', lambda msg: print(f'[console.{msg.type}] {msg.text}'))
    page.on('pageerror', lambda err: print(f'[pageerror] {err}')) # Uncaught JS exceptions are not console events
    page.goto('http://localhost:5173', wait_until='domcontentloaded') # Server already running and ready
    page.wait_for_function("document.body.innerText.trim().length > 0") # Wait for the SPA to render
    # ... your automation logic
    browser.close()
```

## Waiting Strategy

- **First reconnaissance of an unknown app**: `page.goto(url, wait_until='domcontentloaded')`,
  then `page.wait_for_function("document.body.innerText.trim().length > 0")` — works for
  empty-shell SPAs (React `#root`, Nuxt `#__nuxt`, Vue `#app`).
- **Subsequent actions**: wait on the concrete selectors discovered during reconnaissance
  (`page.wait_for_selector()`, `expect(locator)`).
- **Avoid `networkidle`**: Playwright discourages it, and dev servers with HMR websockets
  (Vite, Nuxt) may never go idle. Use it only as a short-timeout fallback for recon screenshots.

## Best Practices

- Use `sync_playwright()` for synchronous scripts
- Always close the browser when done
- Prefer semantic locators: `page.get_by_role()`, `page.get_by_label()`, `page.get_by_text()`; fall back to CSS selectors or IDs
- Wait for concrete conditions (`page.wait_for_selector()`, `expect(locator)`), not fixed timeouts

## Reference Files

- **examples/** - Examples showing common patterns:
  - `element_discovery.py` - Discovering buttons, links, and inputs on a page
  - `static_html_automation.py` - Using file:// URLs for local HTML
  - `console_logging.py` - Capturing console logs during automation
