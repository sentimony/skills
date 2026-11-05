"""Optional Playwright browser regression: python3 scripts/check_browser.py.

Requires Playwright, Chromium, and access to the pinned CDN assets. The ordinary
stdlib-only CI suite does not invoke this check.
"""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

import render

CASES = [
    ("plain", '```text\nFirst "quoted" & <tag>\nSecond\n\n```\n', 'First "quoted" & <tag>\nSecond\n\n'),
    ("long fence", '````text\nfirst\n```\nsecond\n````\n', 'first\n```\nsecond\n'),
    ("mixed fences", '````text\n~~~\n```\nlast\n````\n', '~~~\n```\nlast\n'),
    ("tildes", '~~~~text\n```\n~~~\nlast\n~~~~\n', '```\n~~~\nlast\n'),
    ("list", '1. Item\n\n   ```text\n   one\n   two\n\n   ```\n', 'one\ntwo\n\n'),
    ("list in quote", "> 1. Item\n>\n>    ~~~~text\n>    one\n>    ~~~\n>    two\n>    ~~~~\n", "one\n~~~\ntwo\n"),
    ("quote", '> ```text\n> one\n> two\n>\n> ```\n', 'one\ntwo\n\n'),
    ("indent", '  ```text\n  one\n    two\n  ```\n', 'one\n  two\n'),
    ("long closing fence", '```text\none\n``````\n', 'one\n'),
    ("fence-like content", '````text\n``` extra\n~~~\n```` trailing\nend\n````\n', '``` extra\n~~~\n```` trailing\nend\n'),
    ("empty fence", '```text\n```\n', ''),
    ("unclosed", '```text\none\ntwo\n', 'one\ntwo\n'),
]


def main():
    with tempfile.TemporaryDirectory() as directory, sync_playwright() as playwright:
        root = Path(directory)
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        for name, markdown, expected in CASES:
            source = root / 'source.md'
            source.write_text(markdown, encoding='utf-8')
            assert render.main([str(source)], tmp_root=root) == 0
            page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
            page.evaluate('''window.copied = null;
                Object.defineProperty(navigator, "clipboard", {configurable: true,
                  value: {writeText: async text => { window.copied = text; }}});''')
            page.get_by_role('button', name='Copy').click(timeout=15000)
            actual = page.evaluate('window.copied')
            assert actual == expected, f'{name}: expected {expected!r}, got {actual!r}'
            print(f'PASS {name}')
        source.write_text("[network](//example.com/a) [absolute](/etc/passwd) [file](file:///etc/passwd) [relative](local.md) [web](https://example.com/) ![network image](//example.com/a.png) ![absolute image](/a.png) ![file image](file:///a.png)", encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('#content a').count() == 2
        assert page.locator('#content img').count() == 0
        assert page.locator('#content a').first.get_attribute('href') == (root / 'local.md').resolve().as_uri()
        print('PASS URL policy')
        requested = []
        def intercept_image(route):
            requested.append(route.request.url)
            route.fulfill(status=200, content_type='image/png', body=b'')
        page.route('https://example.com/pixel.png', intercept_image)
        source.write_text('![remote](https://example.com/pixel.png)', encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert requested == ['https://example.com/pixel.png']
        page.unroute('https://example.com/pixel.png', intercept_image)
        print('PASS remote image request')
        source.write_text('# Heading\n\n[anchor](<  #heading>)\n\n```text\ncontent\n```\n', encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        target = render.html_path(source, root)
        html = target.read_text(encoding='utf-8')
        marker = '  document.querySelectorAll("pre > code").forEach(function (code, index) {'
        assert html.count(marker) == 1
        target.write_text(html.replace(marker, '  copySources.length = 0;\n' + marker), encoding='utf-8')
        page.goto(target.as_uri(), wait_until='networkidle')
        assert page.locator('#content a').get_attribute('href') == '#heading'
        page.evaluate('''window.copied = null;
          Object.defineProperty(navigator, "clipboard", {configurable: true,
            value: {writeText: async text => { window.copied = text; }}});''')
        page.get_by_role('button', name='Copy').click(timeout=15000)
        assert page.evaluate('window.copied') == page.locator('#content pre code').inner_text()
        print('PASS padded anchor and missing copy source fallback')
        source.write_text('```mermaid\ngraph LR\n A-->B\n```\n\n```text\nafter\n```\n', encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        page.evaluate('''window.copied = null;
          Object.defineProperty(navigator, "clipboard", {configurable: true,
            value: {writeText: async text => { window.copied = text; }}});''')
        page.get_by_role('button', name='Copy').click(timeout=15000)
        assert page.evaluate('window.copied') == 'after\n'
        print('PASS copy after Mermaid')
        page.evaluate('''Object.defineProperty(navigator, "clipboard", {configurable: true,
          value: {writeText: async () => { throw new Error("denied"); }}});''')
        page.get_by_role('button', name='Copy').click()
        assert page.get_by_role('status').inner_text().startswith('Copy failed')
        assert page.locator('pre code').inner_text()
        print('PASS clipboard failure retains text')
        browser.close()


if __name__ == '__main__':
    main()
