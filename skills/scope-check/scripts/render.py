#!/usr/bin/env python3
"""Render a saved Markdown file to a standalone HTML preview.

Usage: render.py <path-to-file.md>

Writes a stable path in a private temporary directory, overwriting the previous
render of the same file, and prints its file:// URL. Standard library only.
"""

import hashlib
import html
import json
import os
import stat
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
.copy-controls { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.copy-controls button { font: inherit; cursor: pointer; padding: 4px 10px; }
.copy-controls button:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.copy-controls [role=status] { color: var(--muted); font-size: 13px; }
table { border-collapse: collapse; display: block; overflow: auto; }
th, td { border: 1px solid var(--border); padding: 6px 13px; }
blockquote { margin: 0; padding: 0 1em; color: var(--muted); border-left: .25em solid var(--border); }
li:has(> input[type=checkbox]) { list-style: none; }
.mermaid { text-align: center; }
"""

SCRIPT = r"""
(function () {
  var source = JSON.parse(document.getElementById("source").textContent);
  // The page lives in a temp dir; relative links must point next to the source file.
  var base = JSON.parse(document.getElementById("base").textContent);
  if (!window.marked) return;
  function escapeHtml(text) {
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function safeUrl(href) {
    if (!href) return null;
    if (href.trim().charAt(0) === "#") return href.trim();
    if (/^[\/\\]/.test(href.trim())) return null;
    try {
      var url = new URL(href, base);
      if (["http:", "https:", "mailto:", "file:"].indexOf(url.protocol) === -1) return null;
      if (url.protocol === "file:" && /^[a-z][a-z0-9+.-]*:/i.test(href.trim())) return null;
      return url.href;
    } catch (e) {
      return null;
    }
  }
  var copySources = [];
  marked.use({
    gfm: true,
    renderer: {
      code(token) {
        var opening = token.raw.match(/^( {0,3})(`{3,}|~{3,})[^\n]*(?:\n|$)/);
        if (!opening) {
          copySources.push(null);
          return false;
        }
        var content = token.raw.slice(opening[0].length);
        var fence = opening[2];
        var closing = new RegExp("^ {0,3}" + fence[0] + "{" + fence.length + ",}[ \t]*(?:\n|$)", "m");
        var end = closing.exec(content);
        if (end) content = content.slice(0, end.index);
        var indentation = opening[1].length;
        if (indentation) {
          content = content.replace(new RegExp("^ {1," + indentation + "}", "gm"), "");
        }
        copySources.push(content);
        return false;
      },
      html(token) { return escapeHtml(token.text); },
      link(token) {
        var href = safeUrl(token.href);
        if (href === null) return this.parser.parseInline(token.tokens);
        token.href = href;
        return false;
      },
      image(token) {
        var href = safeUrl(token.href);
        if (href === null) return escapeHtml(token.text);
        token.href = href;
        return false;
      }
    }
  });
  document.getElementById("content").innerHTML = marked.parse(source);
  document.getElementById("fallback").hidden = true;
  document.querySelectorAll("pre > code").forEach(function (code, index) {
    if (code.classList.contains("language-mermaid")) return;
    var copyText = copySources[index] == null ? code.textContent : copySources[index];
    var pre = code.parentElement;
    var controls = document.createElement("div");
    controls.className = "copy-controls";
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = "Copy";
    var status = document.createElement("span");
    status.setAttribute("role", "status");
    button.addEventListener("click", async function () {
      try {
        await navigator.clipboard.writeText(copyText);
        status.textContent = "Copied";
      } catch (error) {
        status.textContent = "Copy failed. Select the text to copy it manually.";
      }
    });
    controls.append(button, status);
    pre.insertAdjacentElement("afterend", controls);
  });
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


def preview_root(tmp_root=None):
    root = Path(tmp_root) if tmp_root is not None else Path(tempfile.gettempdir())
    identity = str(os.getuid()) if hasattr(os, "getuid") else "user"
    return root / ("doc-preview-" + identity)


def html_path(md_path, tmp_root=None):
    """Return the stable preview path for md_path under tmp_root."""
    md_path = Path(md_path)
    root = preview_root(tmp_root)
    resolved = md_path.resolve()
    repo = resolved.parent.name
    for parent in resolved.parents:
        if (parent / ".git").exists():
            repo = parent.name
            break
    digest = hashlib.sha256(os.fsencode(str(resolved))).hexdigest()[:24]
    return root / repo / resolved.parent.name / (resolved.stem + "-" + digest + ".html")


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
<script type="application/json" id="base">{_json_for_script(Path(source).parent.as_uri() + "/")}</script>
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
    root = preview_root(tmp_root)
    temp_name = None
    try:
        root.parent.mkdir(parents=True, exist_ok=True)
        root.mkdir(mode=0o700, exist_ok=True)
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode):
            raise OSError("preview root is not a directory")
        if hasattr(os, "getuid") and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
            raise OSError("preview root must be owned by the current user and private")
        target.parent.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        page = render_html(md_text, md_path.resolve(), generated_at)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as handle:
            temp_name = handle.name
            handle.write(page)
        os.replace(temp_name, target)
    except OSError as error:
        print(f"cannot write preview: {error}", file=sys.stderr)
        return 1
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    print(target.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
