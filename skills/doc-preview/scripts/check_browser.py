"""Optional Playwright browser regression: python3 scripts/check_browser.py.

Requires Playwright, Chromium, and access to the pinned CDN assets. The ordinary
stdlib-only CI suite does not invoke this check.
"""

import tempfile
from pathlib import Path

# Request cases 1-11 ("Оформлення, яке прев'ю має показувати як GitHub") -> PASS line:
#  1 sup with version link              -> PASS inline tag allowlist
#  2 <br> in a table cell               -> PASS table cell structure
#  3 link to another md -> its preview  -> PASS md links
#  4 code with <br>/<sup> in a cell     -> PASS table cell structure
#  5 wave headings nested in the TOC    -> PASS toc and anchors
#  6 code/link/th never wrap            -> PASS table nowrap names
#  7 "(done)" heading + summary table   -> PASS done heading and summary table
#  8 short columns stay on one line     -> PASS table short columns nowrap
#  9 unorganised plugin, full number    -> PASS table unorg plugin and full request number
# 10 sup link in a table cell           -> PASS table sup link
# 11 escaped pipe inside code           -> PASS table escaped pipe in code
# Further lines cover favicon, footer navigation, formats and the URL policy.

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
        source.write_text('`skills` <sup>[v0.0.104](https://example.com/)</sup> <SUP>up</SUP> <sub>low</sub> <kbd>K</kbd> a<br>b <sup class="x">attr</sup> <img src=x onerror="window.pwned=1"> <script>window.pwned=1</script>', encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('#content sup').count() == 2
        assert page.locator('#content sup a').get_attribute('href') == 'https://example.com/'
        assert page.locator('#content sub').count() == 1
        assert page.locator('#content kbd').count() == 1
        assert page.locator('#content br').count() == 1
        assert page.locator('#content img, #content script, #content [class]').count() == 0
        assert '<sup class="x">' in page.locator('#content').inner_text()
        assert page.evaluate('window.pwned') is None
        print('PASS inline tag allowlist')
        source.write_text(
            '# Top\n\n## Waves\n\n### Wave 1b\n\n<details>\n<summary>Details <b>x</b></summary>\n\n'
            '| A | B |\n| --- | --- |\n| one | two |\n\n### Inner heading\n\n</details>\n\n'
            '<details open>\n<summary>Open</summary>\n\ntext\n\n</details>\n\n'
            '<details onclick="window.pwned=1">\n<summary><img src=x onerror="window.pwned=1"></summary>\n\nbody\n\n</details>\n',
            encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('#content details').count() == 2, page.locator('#content details').count()
        assert page.locator('#content details > summary').count() == 2
        assert page.locator('#content details table').count() == 1
        assert page.locator('#content details').first.evaluate('n => n.open') is False
        assert page.locator('#content details').nth(1).evaluate('n => n.open') is True
        assert page.locator('#content details table').is_hidden()
        assert page.locator('#content details').first.locator('summary b').count() == 0
        assert page.locator('summary').first.inner_text() == 'Details <b>x</b>'
        assert page.locator('summary').first.evaluate('n => getComputedStyle(n).cursor') == 'pointer'
        page.locator('#content details > summary').first.click()
        assert page.locator('#content details table').is_visible()
        assert page.locator('#content details table td').first.inner_text() == 'one'
        assert '<details onclick' in page.locator('#content').inner_text()
        assert page.locator('#content img').count() == 0
        assert page.evaluate('window.pwned') is None
        page.locator('#content details > summary').first.click()
        assert page.locator('#content details table').is_hidden()
        page.locator('#toc a', has_text='Inner heading').click()
        assert page.locator('#content details').first.evaluate('n => n.open') is True
        assert page.locator('#inner-heading').is_visible()
        page.locator('#content details > summary').first.click()
        page.evaluate('location.hash = ""')
        page.evaluate('location.hash = "#inner-heading"')
        assert page.locator('#content details').first.evaluate('n => n.open') is True
        print('PASS details accordion')
        icon_requests = []
        page.on('request', lambda request: icon_requests.append(request.url) if 'favicon' in request.url else None)
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('link[rel=icon]').get_attribute('href').startswith('data:image/svg+xml,')
        assert icon_requests == [], icon_requests
        print('PASS favicon')
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
        source.write_text('# Triage\n\n## План хвиль\n\n### Хвиля 1a (done)\n\n| Request | Plugin & skills | Description |\n| --- | --- | --- |\n| [20261022-0252](x.md) | `skills`<sup>[v0.0.103](https://github.com/sentimony/skills/tree/v0.0.103)</sup> | text |\n\n### Хвиля 1b\n\n## План хвиль\n\n## Content\n', encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('#toc').is_visible()
        assert page.locator('#content > #toc').count() == 1
        assert page.locator('#toc > ul > li').count() == 3
        assert page.locator('#toc > ul > li').first.locator('ul > li').count() == 2
        assert page.locator('#toc > ul > li > a').nth(1).get_attribute('href') == '#план-хвиль-1'
        assert page.locator('#content h2').nth(1).get_attribute('id') == 'план-хвиль-1'
        assert page.locator('#content h2').nth(2).get_attribute('id') == 'content-1'
        assert page.evaluate('document.getElementById("content").tagName') == 'MAIN'
        item = page.locator('#toc li li a').first
        assert item.inner_text() == 'Хвиля 1a (done)'
        item.click()
        assert page.evaluate('decodeURIComponent(location.hash)') == '#хвиля-1a-done'
        source.write_text('# Heading\n\n[anchor](#heading)\n', encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('#content a').get_attribute('href') == '#heading'
        assert page.locator('#heading').evaluate('node => node.tagName') == 'H1'
        assert not page.locator('#toc').is_visible()
        print('PASS toc and anchors')
        case7 = root / 'case-7'
        case7.mkdir()
        done = case7 / 'summary.md'
        done.write_text('## План хвиль\n\n### Хвиля 1a (done)\n\n| Request | Plugin & skills |\n| --- | --- |\n'
                        '| [20261022-0252](x.md) | `skills`<sup>v0.0.103</sup> |\n\n### Хвиля 1b\n', encoding='utf-8')
        assert render.main([str(done)], tmp_root=root) == 0
        page.goto(render.html_path(done, root).as_uri(), wait_until='networkidle')
        assert page.locator('#content h3').first.inner_text() == 'Хвиля 1a (done)'
        assert page.locator('#toc li li a').first.inner_text() == 'Хвиля 1a (done)'
        assert page.locator('#content table').count() == 1
        assert page.locator('#content th').count() == 2 and page.locator('#content td').count() == 2
        assert page.locator('#content table caption, #content table tfoot').count() == 0
        print('PASS done heading and summary table')
        repo = root / 'repo'
        (repo / '.git').mkdir(parents=True)
        (repo / 'docs' / 'requests').mkdir(parents=True)
        (repo / 'docs' / 'reviews').mkdir(parents=True)
        (repo / 'docs' / 'requests' / 'r.md').write_text('# R\n\n[back](../reviews/triage.md)\n', encoding='utf-8')
        (repo / 'docs' / 'requests' / 'заявка a.md').write_text('# Z\n', encoding='utf-8')
        (root / 'outside.md').write_text('# Outside\n', encoding='utf-8')
        triage = repo / 'docs' / 'reviews' / 'triage.md'
        triage.write_text('[req](../requests/r.md) [missing](../requests/none.md) [ext](../requests/r.md#top) '
                          '[ru](../requests/заявка%20a.md) [out](../../../outside.md) [web](https://example.com/r.md)\n', encoding='utf-8')
        assert render.main([str(triage)], tmp_root=root) == 0
        page.goto(render.html_path(triage, root).as_uri(), wait_until='networkidle')
        hrefs = page.locator('#content a').evaluate_all('links => links.map(a => a.getAttribute("href"))')
        assert hrefs[0] == '../requests/r.html', hrefs
        assert hrefs[1] == (repo / 'docs' / 'requests' / 'none.md').resolve().as_uri(), hrefs
        assert hrefs[2] == '../requests/r.html#top', hrefs
        assert hrefs[3].endswith('.html') and '../requests/' in hrefs[3], hrefs
        assert hrefs[4] == (root / 'outside.md').resolve().as_uri(), hrefs
        assert hrefs[5] == 'https://example.com/r.md', hrefs
        page.locator('#content a').first.click()
        page.wait_for_load_state('networkidle')
        assert page.url.endswith('/docs/requests/r.html'), page.url
        assert page.locator('#content h1').inner_text() == 'R'
        page.locator('#content a').first.click()
        page.wait_for_load_state('networkidle')
        assert page.url.endswith('/docs/reviews/triage.html'), page.url
        print('PASS md links')
        (repo / 'README.md').write_text('# Repo readme\n', encoding='utf-8')
        (repo / 'docs' / 'README.md').write_text('# Docs readme\n', encoding='utf-8')
        (repo / 'docs' / 'reviews' / 'a <b> & "c".md').write_text('# Odd\n', encoding='utf-8')
        assert render.main([str(triage)], tmp_root=root) == 0
        mirror = render.preview_root(root) / 'repo'
        page.goto(render.html_path(triage, root).as_uri(), wait_until='networkidle')
        assert page.url.startswith(mirror.as_uri()), page.url
        labels = page.locator('#site-nav a').evaluate_all('links => links.map(a => a.textContent)')
        assert labels == ['README.md', 'docs/README.md', 'Index: docs/reviews/', 'Index: docs/', 'Index: repo/'], labels
        assert page.locator('#site-nav').is_visible()
        page.get_by_role('link', name='Index: docs/', exact=True).click()
        page.wait_for_load_state('networkidle')
        assert page.url == (mirror / 'docs' / '_index.html').as_uri(), page.url
        assert page.locator('h1').inner_text() == 'docs/'
        assert page.get_by_role('link', name='reviews/').count() == 1
        assert page.get_by_role('link', name='Index: repo/').count() == 1
        page.get_by_role('link', name='reviews/').click()
        page.wait_for_load_state('networkidle')
        assert page.url == (mirror / 'docs' / 'reviews' / '_index.html').as_uri(), page.url
        assert page.get_by_role('link', name='a <b> & "c".md').count() == 1
        assert page.locator('main b').count() == 0
        page.get_by_role('link', name='triage.md').click()
        page.wait_for_load_state('networkidle')
        assert page.url == render.html_path(triage, root).as_uri(), page.url
        assert page.locator('#content a').count() == 6
        print('PASS footer navigation')
        page.set_viewport_size({'width': 700, 'height': 900})
        long_text = 'Опис із довгим текстом, який має переноситися за словами, а не обрізатися, навіть у вузькому вікні, бо колонка довга. '
        table = ('| Request | Plugin & skills | Description |\n| --- | --- | --- |\n'
                 '| [20261022-0252](https://example.com/a) | `cross-agent`<sup>[0.0.7](https://github.com/sentimony/cross-agent/tree/v0.0.7/skills/cross-agent)</sup>'
                 '<br>↳ `cross-agent`<sup>0.0.6</sup><br>↳ `parallel-agents`<sup>0.0.5</sup> | ' + long_text + '`--mode read-only\\|no-network` лишається у клітинці |\n')
        source.write_text(table, encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('#content tr').count() == 2
        assert page.locator('#content table').count() == 1
        assert page.locator('#content td').count() == 3 and page.locator('#content th').count() == 3
        cell = page.locator('#content td').nth(1)
        assert cell.locator('code').count() == 3 and cell.locator('br').count() == 2
        assert cell.locator('sup').count() == 3 and cell.locator('table, td').count() == 0
        print('PASS table cell structure')
        for selector in ('td code', 'td a', 'th'):
            assert page.locator('#content ' + selector).first.evaluate('n => getComputedStyle(n).whiteSpace') == 'nowrap', selector
        print('PASS table nowrap names')
        classes = page.locator('#content td').evaluate_all('cells => cells.map(c => c.classList.contains("nowrap"))')
        assert classes == [True, True, False], classes
        head = page.locator('#content th').evaluate_all('cells => cells.map(c => c.classList.contains("nowrap"))')
        assert head == [True, True, False], head
        assert page.locator('#content td').first.evaluate('n => getComputedStyle(n).whiteSpace') == 'nowrap'
        assert page.locator('#content td').nth(2).evaluate('n => getComputedStyle(n).whiteSpace') != 'nowrap'
        assert page.locator('#content td a').first.evaluate('n => n.getClientRects().length') == 1
        # Each <br>-separated line of the plugin cell sits on one visual row: its boxes share a vertical band.
        rows = cell.evaluate("""n => { var tops = [], cur = [];
          Array.from(n.childNodes).forEach(function (c) {
            if (c.nodeName === "BR") { tops.push(cur); cur = []; return; }
            var r = document.createRange(); r.selectNodeContents(c);
            Array.from(r.getClientRects()).forEach(function (q) { cur.push([q.top, q.bottom]); });
          }); tops.push(cur); return tops; }""")
        assert len(rows) == 3, rows
        for tops in rows:
            assert tops and max(t[0] for t in tops) < min(t[1] for t in tops), rows
        print('PASS table short columns nowrap')
        assert page.locator('#content td').nth(1).locator('code').nth(1).inner_text() == 'cross-agent'
        print('PASS table unorg plugin and full request number')
        link = cell.locator('sup > a')
        assert link.get_attribute('href') == 'https://github.com/sentimony/cross-agent/tree/v0.0.7/skills/cross-agent'
        assert link.inner_text() == '0.0.7'
        print('PASS table sup link')
        desc = page.locator('#content td').nth(2)
        assert desc.locator('code').inner_text() == '--mode read-only|no-network'
        assert page.locator('#content tr').nth(1).locator('td').count() == 3
        source.write_text(table.replace('\\|', '|'), encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        # GFM drops cells beyond the header width, so the bare pipe cuts the description short.
        cut = page.locator('#content tr').nth(1).locator('td')
        assert cut.count() == 3, cut.count()
        assert 'no-network' not in cut.nth(2).inner_text(), cut.nth(2).inner_text()
        print('PASS table escaped pipe in code')
        cols = 6
        source.write_text('|' + ' Колонка |' * cols + '\n|' + ' --- |' * cols + '\n|' + ' значення-комірки |' * cols + '\n', encoding='utf-8')
        assert render.main([str(source)], tmp_root=root) == 0
        page.goto(render.html_path(source, root).as_uri(), wait_until='networkidle')
        assert page.locator('#content table').evaluate('n => getComputedStyle(n).overflowX') == 'auto'
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        print('PASS wide table scroll')
        formats = root / 'formats'
        formats.mkdir()

        def open_data(name, text):
            path = formats / name
            path.write_text(text, encoding='utf-8')
            assert render.main([str(path)], tmp_root=root) == 0
            page.goto(render.html_path(path, root).as_uri(), wait_until='networkidle')
            return path

        def copied_text():
            page.evaluate('''window.copied = null;
              Object.defineProperty(navigator, "clipboard", {configurable: true,
                value: {writeText: async text => { window.copied = text; }}});''')
            page.get_by_role('button', name='Copy').click(timeout=15000)
            return page.evaluate('window.copied')

        def check_json_page(expected, text):
            lines = text.rstrip('\n').split('\n')
            assert page.locator('pre code .line').count() == len(lines), page.locator('pre code .line').count()
            assert page.locator('pre code .line').first.inner_text() == lines[0]
            assert page.locator('pre code .line').first.evaluate(
                "n => getComputedStyle(n, '::before').content").startswith('counter('), 'numbers come from CSS'
            # Line numbers live in CSS, never in the text a reader selects.
            assert page.locator('pre code').evaluate('n => n.textContent') == ''.join(lines)
            assert copied_text() == expected

        json_text = '{\n  "name": "demo",\n  "items": [1, true, null]\n}\n'
        open_data('a.json', json_text)
        check_json_page(json_text, json_text)
        assert page.locator('pre code .tk-key').count() == 2
        assert page.locator('pre code .tk-num').count() == 1
        assert page.locator('pre code .tk-kw').count() == 2
        assert page.locator('pre code .tk-str').first.inner_text() == '"demo"'
        assert page.locator('#toc').is_hidden()
        assert page.title() == 'a.json'
        open_data('multi.toml', 'a = """\nfirst\nsecond\n"""\nb = 2\n')
        assert page.locator('pre code .line').count() == 5
        assert [page.locator('pre code .line').nth(i).inner_text() for i in (1, 2)] == ['first', 'second']
        assert page.locator('pre code .tk-str').count() >= 1
        open_data('c.yaml', '# note\nkey: value\nlist:\n  - one\n')
        assert page.locator('pre code .line').count() == 4
        print('PASS formats')
        open_data('bad.json', '{"a": }')
        assert page.locator('.notice').is_visible()
        assert 'line 1 column 7' in page.locator('.notice').inner_text()
        assert page.locator('pre code .line').count() == 1
        print('PASS invalid json shows error')
        open_data('t.csv', 'name,note\n<b>x</b>,"a,b"\nsecond,\n')
        assert page.locator('#content table thead th').count() == 2
        assert page.locator('#content table tr').count() == 3
        assert page.locator('#content td').first.inner_text() == '<b>x</b>'
        assert page.locator('#content b').count() == 0
        assert page.locator('#content td').nth(1).inner_text() == 'a,b'
        print('PASS csv table')
        original_rows = render.MAX_ROWS
        render.MAX_ROWS = 2
        try:
            open_data('big.csv', 'h\n1\n2\n3\n')
        finally:
            render.MAX_ROWS = original_rows
        assert page.locator('#content table tr').count() == 3
        assert page.locator('.notice').inner_text() == 'Showing first 2 rows'
        print('PASS csv truncation notice')
        open_data('plain.txt', 'just <i>text</i>\nline two\n')
        assert page.locator('pre code .line').count() == 2
        assert page.locator('pre code [class^=tk-]').count() == 0
        assert page.locator('#content i').count() == 0
        assert copied_text() == 'just <i>text</i>\nline two\n'
        assert page.locator('script[src]').count() == 0
        print('PASS txt without highlighting')
        requested = []
        page.on('request', lambda request: requested.append(request.url))
        open_data('offline.json', json_text)
        assert [url for url in requested if not url.startswith('file:')] == [], requested
        assert page.locator('script[src]').count() == 0
        assert page.locator('pre code .tk-key').count() == 2
        check_json_page(json_text, json_text)
        print('PASS json highlighted without any request')
        hostile = '{"x": "</script><img src=x onerror=window.pwned=1>"}\n'
        open_data('hostile.json', hostile)
        assert page.evaluate('window.pwned') is None
        assert page.locator('#content img, pre code img').count() == 0
        assert '</script><img src=x onerror=window.pwned=1>' in page.locator('pre code').inner_text()
        assert copied_text() == hostile
        open_data('hostile.csv', 'a\n<img src=x onerror=window.pwned=1>\n')
        assert page.evaluate('window.pwned') is None
        assert page.locator('#content img').count() == 0
        print('PASS hostile data stays text')
        browser.close()


if __name__ == '__main__':
    main()
