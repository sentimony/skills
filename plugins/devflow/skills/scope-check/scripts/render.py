#!/usr/bin/env python3
"""Render a saved Markdown spec or plan to a standalone HTML preview.

Usage: render.py <path-to-file.md>

Writes <temp-dir>/scope-check/<repo>/<folder>/<file>.html, overwriting the previous
render of the same file, and prints its file:// URL. Standard library only.
"""

import html
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

MARKED_URL = "https://cdn.jsdelivr.net/npm/marked@18.1.1/lib/marked.umd.js"
MARKED_SRI = "sha384-rATToyt6602Jnq8c7w8HZwmyOUgPL7mzxX01FBWoV48ns/EgkakGozpES+PnaYOI"
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js"
MERMAID_SRI = "sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp"

STYLE = """
:root { color-scheme: light dark; --fg: #1f2328; --bg: #ffffff; --muted: #59636e;
  --border: #d1d9e0; --code: #f6f8fa; --accent: #0969da; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #e6edf3; --bg: #0d1117; --muted: #9198a1; --border: #3d444d;
    --code: #151b23; --accent: #4493f8; }
}
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
header { border-bottom: 1px solid var(--border); padding: 12px 24px; color: var(--muted);
  font-size: 13px; }
header code { color: var(--fg); }
main, #fallback { max-width: 920px; margin: 0 auto; padding: 24px; }
#fallback { white-space: pre-wrap; font: 14px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; }
h1, h2 { border-bottom: 1px solid var(--border); padding-bottom: .3em; }
a { color: var(--accent); }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 85%; }
code { background: var(--code); padding: .2em .4em; border-radius: 6px; }
pre { background: var(--code); padding: 16px; border-radius: 6px; overflow: auto; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; display: block; overflow: auto; }
th, td { border: 1px solid var(--border); padding: 6px 13px; }
blockquote { margin: 0; padding: 0 1em; color: var(--muted); border-left: .25em solid var(--border); }
li:has(> input[type=checkbox]) { list-style: none; }
.mermaid { text-align: center; }
"""

SCRIPT = """
(function () {
  var source = JSON.parse(document.getElementById("source").textContent);
  if (!window.marked) return;
  function escapeHtml(text) {
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function safeUrl(href) {
    if (!href) return null;
    try {
      var url = new URL(href, document.baseURI);
      if (["http:", "https:", "mailto:", "file:"].indexOf(url.protocol) === -1) return null;
      if (url.protocol === "file:" && /^[a-z][a-z0-9+.-]*:/i.test(href.trim())) return null;
      return href;
    } catch (e) {
      return null;
    }
  }
  marked.use({
    gfm: true,
    renderer: {
      html(token) { return escapeHtml(token.text); },
      link(token) {
        if (safeUrl(token.href) === null) return this.parser.parseInline(token.tokens);
        return false;
      },
      image(token) {
        if (safeUrl(token.href) === null) return escapeHtml(token.text);
        return false;
      }
    }
  });
  document.getElementById("content").innerHTML = marked.parse(source);
  document.getElementById("fallback").hidden = true;
  if (!window.mermaid) return;
  var blocks = document.querySelectorAll("code.language-mermaid");
  blocks.forEach(function (code) {
    var div = document.createElement("div");
    div.className = "mermaid";
    div.textContent = code.textContent;
    code.parentElement.replaceWith(div);
  });
  var dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: dark ? "dark" : "default" });
  mermaid.run();
})();
"""


def html_path(md_path, tmp_root=None):
    """Return the stable preview path for md_path under tmp_root."""
    md_path = Path(md_path)
    root = Path(tmp_root) if tmp_root is not None else Path(tempfile.gettempdir())
    resolved = md_path.resolve()
    repo = resolved.parent.name
    for parent in resolved.parents:
        if (parent / ".git").exists():
            repo = parent.name
            break
    return root / "scope-check" / repo / resolved.parent.name / (resolved.stem + ".html")


def _json_for_script(text):
    data = json.dumps(text)
    return data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_html(md_text, source, generated_at):
    """Return a standalone HTML page that renders md_text in the browser."""
    title = html.escape(Path(source).name)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{STYLE}</style>
</head>
<body>
<header><code>{html.escape(str(source))}</code> - generated {html.escape(generated_at)}</header>
<main id="content"></main>
<pre id="fallback">{html.escape(md_text)}</pre>
<script type="application/json" id="source">{_json_for_script(md_text)}</script>
<script src="{MARKED_URL}" integrity="{MARKED_SRI}" crossorigin="anonymous"></script>
<script src="{MERMAID_URL}" integrity="{MERMAID_SRI}" crossorigin="anonymous"></script>
<script>{SCRIPT}</script>
</body>
</html>
"""


def main(argv, *, tmp_root=None):
    if not argv:
        print("usage: render.py <path-to-file.md>", file=sys.stderr)
        return 2
    md_path = Path(argv[0])
    try:
        md_text = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"cannot read {md_path}: {error}", file=sys.stderr)
        return 1
    target = html_path(md_path, tmp_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    target.write_text(render_html(md_text, md_path.resolve(), generated_at), encoding="utf-8")
    print(target.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
