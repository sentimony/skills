#!/usr/bin/env python3
"""Render a saved Markdown, JSON, YAML, TOML, TXT or CSV file to a standalone HTML preview.

Usage: render.py <path-to-file>

Writes a stable path in a private temporary directory, overwriting the previous
render of the same file, and prints its file:// URL. Standard library only.
"""

import codecs
import csv
import html
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import urllib.parse
from datetime import datetime
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11: TOML is shown as text without a syntax check
    tomllib = None

MARKED_URL = "https://cdn.jsdelivr.net/npm/marked@18.1.1/lib/marked.umd.js"
MARKED_SRI = "sha384-rATToyt6602Jnq8c7w8HZwmyOUgPL7mzxX01FBWoV48ns/EgkakGozpES+PnaYOI"
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js"
MERMAID_SRI = "sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp"

# Pinned like marked and mermaid; only json, yaml and toml pages load it.
HIGHLIGHT_URL = "https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11.12.0/highlight.min.js"
HIGHLIGHT_SRI = "sha384-wjfDDhOPPdjtva8vWBhWeVprSpmxisEu5aYT3q1JyACqXpdKpo3PWZTMVq24MBix"
HIGHLIGHTED_FORMATS = ("json", "yaml", "toml")

# Large files are cut at whichever limit comes first; the page says so.
MAX_ROWS = 5000
MAX_BYTES = 2 * 1024 * 1024

FORMATS = {
    ".md": "md",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".txt": "txt",
    ".csv": "csv",
}

# Columns whose longest line is at most this many characters never wrap.
NOWRAP_COLUMN_CHARS = 48

STYLE = """
:root { color-scheme: light dark; --fg: #1f2328; --bg: #ffffff; --muted: #59636e;
  --border: #d1d9e0; --code: #f6f8fa; --accent: #0969da;
  --tok-key: #0550ae; --tok-str: #0a3069; --tok-num: #0550ae; --tok-kw: #cf222e;
  --tok-section: #953800; --tok-comment: #59636e; --danger: #cf222e; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #e6edf3; --bg: #0d1117; --muted: #9198a1; --border: #3d444d;
    --code: #151b23; --accent: #4493f8;
    --tok-key: #79c0ff; --tok-str: #a5d6ff; --tok-num: #79c0ff; --tok-kw: #ff7b72;
    --tok-section: #ffa657; --tok-comment: #9198a1; --danger: #ff7b72; }
}
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
header { border-bottom: 1px solid var(--border); padding: 12px 24px; color: var(--muted);
  font-size: 13px; }
header code { color: var(--fg); }
h1, h2, h3, h4, h5, h6 { scroll-margin-top: 16px; }
#toc { border: 1px solid var(--border); border-radius: 6px; padding: 8px 16px; margin: 0 0 24px;
  font-size: 14px; line-height: 1.5; }
#toc ul { margin: 0; padding-left: 20px; }
#toc > ul { padding-left: 0; list-style: none; }
#toc li { margin: 2px 0; }
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
td code, td a, th { white-space: nowrap; }
.nowrap { white-space: nowrap; }
blockquote { margin: 0; padding: 0 1em; color: var(--muted); border-left: .25em solid var(--border); }
li:has(> input[type=checkbox]) { list-style: none; }
.mermaid { text-align: center; }
footer { border-top: 1px solid var(--border); padding: 12px 24px; color: var(--muted); font-size: 14px; }
footer ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px 20px; }
.index-list { padding-left: 20px; }
.notice { border: 1px solid var(--border); border-left-width: 4px; border-radius: 6px;
  padding: 8px 12px; margin: 0 0 16px; font-size: 14px; }
.notice.error { border-left-color: var(--danger); }
pre.data { counter-reset: line; }
.line { display: block; }
.line::before { counter-increment: line; content: counter(line); display: inline-block; width: 4ch;
  margin-right: 1.5ch; text-align: right; color: var(--muted); user-select: none; }
.hljs-attr, .hljs-attribute, .hljs-name { color: var(--tok-key); }
.hljs-string, .hljs-regexp { color: var(--tok-str); }
.hljs-number, .hljs-literal, .hljs-symbol { color: var(--tok-num); }
.hljs-keyword, .hljs-bullet, .hljs-meta { color: var(--tok-kw); }
.hljs-section, .hljs-title { color: var(--tok-section); font-weight: 600; }
.hljs-comment { color: var(--tok-comment); font-style: italic; }
"""

SCRIPT = r"""
(function () {
  var source = JSON.parse(document.getElementById("source").textContent);
  // The page lives in a temp dir; relative links must point next to the source file.
  var base = JSON.parse(document.getElementById("base").textContent);
  var model = JSON.parse(document.getElementById("model").textContent);
  var siteNav = document.getElementById("site-nav");
  if (siteNav && (model.nav || []).length) {
    var navList = document.createElement("ul");
    model.nav.forEach(function (entry) {
      // Hrefs are relative paths built by render.py; anything with a scheme is dropped.
      if (/^[a-z][a-z0-9+.-]*:/i.test(String(entry.href))) return;
      var item = document.createElement("li");
      var link = document.createElement("a");
      link.setAttribute("href", entry.href);
      link.textContent = entry.label;
      item.appendChild(link);
      navList.appendChild(item);
    });
    siteNav.appendChild(navList);
    siteNav.hidden = false;
  }
  // Previewed neighbors, compared by normalized file URL.
  var previewed = {};
  (model.links || []).forEach(function (uri) {
    try { previewed[new URL(uri).href] = true; } catch (e) { /* skip malformed entry */ }
  });
  function addCopyControls(pre, copyText) {
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
  }
  function showNotice(main, text, kind) {
    var note = document.createElement("div");
    note.className = kind ? "notice " + kind : "notice";
    note.setAttribute("role", kind === "error" ? "alert" : "note");
    note.textContent = text;
    main.appendChild(note);
  }
  // Re-wraps the (possibly highlighted) children of code into one span.line per source line,
  // re-opening highlight spans that cross a line break.
  function splitIntoLines(code, text) {
    var nodes = Array.from(code.childNodes);
    code.textContent = "";
    if (text === "") return;
    var chain = [];
    var target = code;
    var last = null;
    function startLine() {
      last = document.createElement("span");
      last.className = "line";
      code.appendChild(last);
      target = last;
      chain.forEach(function (open) {
        var copy = open.cloneNode(false);
        target.appendChild(copy);
        target = copy;
      });
    }
    function walk(node) {
      if (node.nodeType === 3) {
        node.nodeValue.split("\n").forEach(function (part, i) {
          if (i > 0) startLine();
          if (part) target.appendChild(document.createTextNode(part));
        });
        return;
      }
      var clone = node.cloneNode(false);
      target.appendChild(clone);
      target = clone;
      chain.push(node);
      Array.from(node.childNodes).forEach(walk);
      chain.pop();
      target = target.parentNode;
    }
    startLine();
    nodes.forEach(walk);
    if (/\n$/.test(text)) code.removeChild(last);
  }
  function renderData(data) {
    var main = document.getElementById("content");
    document.getElementById("fallback").hidden = true;
    if (data.error) showNotice(main, "Parse error: " + data.error, "error");
    if (data.notice) showNotice(main, data.notice, "");
    if (data.rows) {
      var table = document.createElement("table");
      var head = document.createElement("thead");
      var body = document.createElement("tbody");
      data.rows.forEach(function (row, index) {
        var tr = document.createElement("tr");
        row.forEach(function (value) {
          var cell = document.createElement(index === 0 ? "th" : "td");
          cell.textContent = value;
          tr.appendChild(cell);
        });
        (index === 0 ? head : body).appendChild(tr);
      });
      table.append(head, body);
      main.appendChild(table);
      markNowrapColumns(main, model.nowrapChars);
      return;
    }
    var text = data.text || "";
    var pre = document.createElement("pre");
    pre.className = "data";
    var code = document.createElement("code");
    // The text enters the DOM as text; highlight.js reads textContent and escapes its output.
    code.textContent = text;
    if (["json", "yaml", "toml"].indexOf(data.fmt) !== -1) {
      code.className = "language-" + data.fmt;
      if (window.hljs) {
        try { hljs.highlightElement(code); } catch (e) { /* keep the plain text */ }
      }
    }
    splitIntoLines(code, text);
    pre.appendChild(code);
    main.appendChild(pre);
    // Highlighting rewrote the DOM, so Copy uses the model text.
    addCopyControls(pre, text);
  }
  if (model.fmt && model.fmt !== "md") {
    renderData(model.data || {});
    return;
  }
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
  function previewHref(original) {
    // A relative link to a Markdown file that has a preview opens the mirrored .html.
    var raw = String(original || "").trim();
    if (!raw || raw.charAt(0) === "#" || /^[\/\\]/.test(raw) || /^[a-z][a-z0-9+.-]*:/i.test(raw)) return null;
    try {
      var bare = new URL(raw, base).href.split("#")[0].split("?")[0];
      if (!previewed[bare]) return null;
    } catch (e) {
      return null;
    }
    var rewritten = raw.replace(/\.md(?=[?#]|$)/i, ".html");
    return rewritten === raw ? null : rewritten;
  }
  var RESERVED_IDS = ["content", "source", "base", "model", "fallback", "toc", "site-nav"];
  function slugify(text) {
    var slug = text.toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, "").trim().replace(/\s+/g, "-");
    return slug || "section";
  }
  function assignHeadingIds(root) {
    var used = {};
    root.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(function (heading) {
      var base = slugify(heading.textContent);
      var slug = base;
      var n = 0;
      while (used[slug] || RESERVED_IDS.indexOf(slug) !== -1) {
        n += 1;
        slug = base + "-" + n;
      }
      used[slug] = true;
      heading.id = slug;
    });
  }
  function buildToc(root, nav) {
    var headings = root.querySelectorAll("h2, h3");
    if (headings.length < 2) return;
    var list = document.createElement("ul");
    var parentItem = null;
    headings.forEach(function (heading) {
      var item = document.createElement("li");
      var link = document.createElement("a");
      link.href = "#" + heading.id;
      link.textContent = heading.textContent;
      item.appendChild(link);
      if (heading.tagName === "H3" && parentItem) {
        var sub = parentItem.querySelector(":scope > ul");
        if (!sub) {
          sub = document.createElement("ul");
          parentItem.appendChild(sub);
        }
        sub.appendChild(item);
        return;
      }
      list.appendChild(item);
      if (heading.tagName === "H2") parentItem = item;
    });
    nav.appendChild(list);
    nav.hidden = false;
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
      html(token) {
        // Bare inline tags without attributes render; any other raw HTML stays text.
        var tag = token.text.trim();
        if (/^<\/?(sup|sub|kbd)>$|^<br\s*\/?>$/i.test(tag)) return tag;
        return escapeHtml(token.text);
      },
      link(token) {
        var mirrored = previewHref(token.href);
        if (mirrored !== null) {
          token.href = mirrored;
          return false;
        }
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
  // A column stays on one line when its longest <br>-separated line is short enough.
  function markNowrapColumns(root, limit) {
    root.querySelectorAll("table").forEach(function (table) {
      var columns = [];
      table.querySelectorAll("tr").forEach(function (row) {
        Array.from(row.children).forEach(function (cell, index) {
          var copy = cell.cloneNode(true);
          copy.querySelectorAll("br").forEach(function (br) { br.replaceWith("\n"); });
          var longest = Math.max.apply(null, copy.textContent.split("\n").map(function (line) {
            return Array.from(line).length;
          }));
          columns[index] = columns[index] || { max: 0, cells: [] };
          columns[index].max = Math.max(columns[index].max, longest);
          columns[index].cells.push(cell);
        });
      });
      columns.forEach(function (column) {
        if (column.max <= limit) column.cells.forEach(function (cell) { cell.classList.add("nowrap"); });
      });
    });
  }
  document.getElementById("content").innerHTML = marked.parse(source);
  document.getElementById("fallback").hidden = true;
  markNowrapColumns(document.getElementById("content"), model.nowrapChars);
  assignHeadingIds(document.getElementById("content"));
  var toc = document.getElementById("toc");
  buildToc(document.getElementById("content"), toc);
  document.getElementById("content").prepend(toc);
  if (location.hash.length > 1) {
    try {
      var target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) target.scrollIntoView();
    } catch (e) { /* malformed hash: stay at the top */ }
  }
  document.querySelectorAll("pre > code").forEach(function (code, index) {
    if (code.classList.contains("language-mermaid")) return;
    var copyText = copySources[index] == null ? code.textContent : copySources[index];
    addCopyControls(code.parentElement, copyText);
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


ROOT_MARKER = ".doc-preview-root"


def preview_root(tmp_root=None):
    root = Path(tmp_root) if tmp_root is not None else Path(tempfile.gettempdir())
    identity = str(os.getuid()) if hasattr(os, "getuid") else "user"
    return root / ("doc-preview-" + identity)


def repo_root(source):
    """Nearest parent holding .git (file or dir, so worktrees work), else the source's folder."""
    resolved = Path(source).resolve()
    for parent in resolved.parents:
        if (parent / ".git").exists():
            return parent
    return resolved.parent


def repo_label(root):
    name = Path(root).name
    return name if name not in ("", ".", "..") else "root"


def html_path(md_path, tmp_root=None, root=None):
    """Return the mirror preview path <preview root>/<repo>/<path from repo root>.html.

    root overrides the detected repo root (a source without .git renders its subfolders under it).
    """
    resolved = Path(md_path).resolve()
    root = Path(root).resolve() if root is not None else repo_root(resolved)
    relative = resolved.relative_to(root)
    # Only .md drops its extension, so x.md and x.json never share a page.
    name = (relative.stem if resolved.suffix.lower() == ".md" else relative.name) + ".html"
    return preview_root(tmp_root) / repo_label(root) / relative.parent / name


def claim_repo_dir(repo_dir, root, preview_root):
    """Make repo_dir belong to root: keep it on a marker match, otherwise clear it first."""
    repo_dir = Path(repo_dir)
    # Guards come first: a symlink or foreign path must never be read as owned or cleared.
    if repo_dir.parent != Path(preview_root):
        raise OSError(f"refusing to use {repo_dir}: not a direct child of the preview root")
    try:
        info = repo_dir.lstat()
    except FileNotFoundError:
        info = None
    if info is not None and (stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)):
        raise OSError(f"refusing to use {repo_dir}: not a plain directory")
    marker = repo_dir / ROOT_MARKER
    wanted = str(Path(root).resolve())
    try:
        if marker.read_text(encoding="utf-8") == wanted:
            return
    except (OSError, UnicodeDecodeError):
        pass
    if info is not None:
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True)
    marker.write_text(wanted, encoding="utf-8")


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    "<style>@media (prefers-color-scheme: dark){svg{stroke:#e6edf3}}</style>"
    '<path d="M10.5 14 L10.5 20" />'
    '<path d="M10.5 17 L12 17" />'
    '<path d="M10.5 5.5 A1.5 1.5 0 0 1 12 4" />'
    '<path d="M10.5 8.5 L10.5 5.5" />'
    '<path d="M12 14 L10.5 14" />'
    '<path d="M12 17 A1.5 1.5 0 0 0 12 14" />'
    '<path d="M12 4 A1.5 1.5 0 0 1 13.5 5.5" />'
    '<path d="M13.5 20 L11.5 17" />'
    '<path d="M13.5 5.5 L13.5 8.5" />'
    '<path d="M13.5 8.5 A1.5 1.5 0 0 1 10.5 8.5" />'
    '<path d="M17.5 14 L17.5 20" />'
    '<path d="M17.5 17 L19.5 17" />'
    '<path d="M17.5 20 L20.5 20" />'
    '<path d="M17.5 5.5 L17.5 8.5" />'
    '<path d="M17.5 8.5 A1.5 1.5 0 0 0 20.5 8.5" />'
    '<path d="M20.5 14 L17.5 14" />'
    '<path d="M20.5 5.5 A1.5 1.5 0 0 0 17.5 5.5" />'
    '<path d="M3.5 10 L4.5 10" />'
    '<path d="M3.5 14 L3.5 20" />'
    '<path d="M3.5 17 L5 17" />'
    '<path d="M3.5 4 L3.5 10" />'
    '<path d="M4.5 10 A2 2 0 0 0 6.5 8" />'
    '<path d="M4.5 4 L3.5 4" />'
    '<path d="M5 14 L3.5 14" />'
    '<path d="M5 17 A1.5 1.5 0 0 0 5 14" />'
    '<path d="M6.5 6 A2 2 0 0 0 4.5 4" />'
    '<path d="M6.5 8 L6.5 6" />'
    "</svg>"
)


def favicon_link():
    href = "data:image/svg+xml," + urllib.parse.quote(FAVICON_SVG, safe="")
    return f'<link rel="icon" type="image/svg+xml" href="{href}">'


def _json_for_script(text):
    data = json.dumps(text)
    return data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_html(md_text, source, generated_at, *, fmt="md", model=None):
    """Return a standalone HTML page that renders md_text (or, for other formats, model["data"])."""
    model = {"links": [], "nav": [], "nowrapChars": NOWRAP_COLUMN_CHARS, "fmt": fmt, **(model or {})}
    if fmt == "md":
        scripts = (
            f'<script src="{MARKED_URL}" integrity="{MARKED_SRI}" crossorigin="anonymous"></script>\n'
            f'<script src="{MERMAID_URL}" integrity="{MERMAID_SRI}" crossorigin="anonymous"></script>\n'
        )
    elif fmt in HIGHLIGHTED_FORMATS:
        scripts = f'<script src="{HIGHLIGHT_URL}" integrity="{HIGHLIGHT_SRI}" crossorigin="anonymous"></script>\n'
    else:
        scripts = ""
    source_text = md_text if fmt == "md" else ""
    title = html.escape(Path(source).name)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{favicon_link()}
<style>{STYLE}</style>
</head>
<body>
<header><code>{html.escape(str(source))}</code> - generated {html.escape(generated_at)}</header>
<nav id="toc" aria-label="Contents" hidden></nav>
<main id="content"></main>
<pre id="fallback">{html.escape(md_text)}</pre>
<footer id="site-nav" aria-label="Site navigation" hidden></footer>
<script type="application/json" id="source">{_json_for_script(source_text)}</script>
<script type="application/json" id="base">{_json_for_script(Path(source).parent.as_uri() + "/")}</script>
<script type="application/json" id="model">{_json_for_script(model)}</script>
{scripts}<script>{SCRIPT}</script>
</body>
</html>
"""


def _size_label(count):
    mib = 1024 * 1024
    return f"{count // mib} MB" if count % mib == 0 else f"{count} bytes"


def _line_count(text):
    return text.count("\n") + (0 if text == "" or text.endswith("\n") else 1)


def _read_limited(source, max_bytes):
    """Return (text, cut): at most max_bytes of the file, BOM removed, a partial last character dropped.

    Reads max_bytes + 1 bytes at most, so a huge file never loads whole. Invalid UTF-8 inside the
    read part raises UnicodeDecodeError.
    """
    with source.open("rb") as handle:
        if handle.read(3) != codecs.BOM_UTF8:
            handle.seek(0)
        raw = handle.read(max_bytes + 1)
    cut = len(raw) > max_bytes
    decoder = codecs.getincrementaldecoder("utf-8")()
    # Not final when cut: an incomplete character at the boundary stays unread instead of failing.
    return decoder.decode(raw[:max_bytes], final=not cut), cut


def _text_data(fmt, text, error, cut, max_bytes):
    data = {"fmt": fmt, "text": text, "error": error, "truncated": cut, "total": None if cut else _line_count(text)}
    if cut:
        data["notice"] = f"Truncated at {_size_label(max_bytes)}"
    return data


def _csv_data(text, cut, max_rows):
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    rows = []
    more = False
    try:
        for row in reader:
            if not row:
                continue
            if len(rows) > max_rows:
                more = True
                break
            rows.append(row)
    except csv.Error as error:
        # A cut inside a quoted field: that record is unfinished and not shown.
        if not (cut and "unexpected end of data" in str(error)):
            raise
    else:
        # A cut after a complete line is fine; otherwise the last record is partial.
        if cut and not more and rows and not text.endswith(("\n", "\r")):
            rows.pop()
    if not rows:
        raise csv.Error("no rows")
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    truncated = cut or more
    data = {"fmt": "csv", "rows": rows, "error": None, "truncated": truncated,
            "total": None if truncated else len(rows) - 1}
    if truncated:
        data["notice"] = f"Showing first {len(rows) - 1} rows"
    return data


def load_data(source, *, max_rows=None, max_bytes=None):
    """Read a supported file into {fmt, text|rows, error, truncated, total[, notice]}.

    Only the shown part is read, so total is None when the file was cut. Parsing failures never
    raise: the file is shown as text with the error. Read and decode errors (OSError,
    UnicodeDecodeError) propagate.
    """
    max_rows = MAX_ROWS if max_rows is None else max_rows
    max_bytes = MAX_BYTES if max_bytes is None else max_bytes
    source = Path(source)
    fmt = FORMATS[source.suffix.lower()]
    text, cut = _read_limited(source, max_bytes)
    if fmt == "csv":
        try:
            return _csv_data(text, cut, max_rows)
        except csv.Error as error:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            return _text_data("txt", text, f"CSV: {error}", cut, max_bytes)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    error = None
    # A cut file is incomplete, so it cannot be checked.
    if fmt == "json" and not cut:
        try:
            json.loads(text)
        except json.JSONDecodeError as problem:
            error = f"line {problem.lineno} column {problem.colno}: {problem.msg}"
    elif fmt == "toml" and tomllib is not None and not cut:
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as problem:
            error = str(problem)
    return _text_data(fmt, text, error, cut, max_bytes)


INLINE_LINK = re.compile(r"\]\(\s*(<[^>\n]*>|[^)\s]*)")
REFERENCE_LINK = re.compile(r"^ {0,3}\[[^\]\n]+\]:[ \t]*(<[^>\n]*>|\S+)", re.MULTILINE)
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def collect_links(text, source, root):
    """Existing .md files inside root that text links to, in first-seen order, without duplicates."""
    source = Path(source).resolve()
    root = Path(root).resolve()
    found = []
    targets = INLINE_LINK.findall(text) + REFERENCE_LINK.findall(text)
    for target in targets:
        target = target.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        if not target or target[0] in "#/\\" or SCHEME.match(target):
            continue
        target = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not target.lower().endswith(".md"):
            continue
        try:
            path = Path(os.path.normpath(source.parent / target))
            usable = not _via_symlink(path, root) and path.is_file()
        except (OSError, ValueError):
            continue
        if usable and path != source and path not in found:
            found.append(path)
    return found


INDEX_NAME = "_index.html"
SKIPPED_DIRS = ("node_modules",)


def _via_symlink(path, root):
    """True when path (taken as written, not resolved) reaches root's tree through a symlink or leaves it."""
    given = Path(os.path.normpath(os.path.abspath(root)))
    root = Path(root).resolve()
    lexical = Path(os.path.normpath(os.path.abspath(path)))
    for base in (root, given):
        try:
            relative = lexical.relative_to(base)
            break
        except ValueError:
            continue
    else:
        return True
    walked = root / relative
    return walked.resolve() != walked


def _inside(path, root):
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except (OSError, ValueError):
        return False


def has_index_md(directory):
    """True when directory holds an _index.md in any letter case (it would collide with the index page)."""
    try:
        return any(entry.name.casefold() == "_index.md" for entry in Path(directory).iterdir())
    except OSError:
        return False


def _nav_dirs(source, root):
    """Folders that get an index page: the source's folder, docs/ when it is a real folder, the root."""
    root = Path(root).resolve()
    dirs = [Path(source).resolve().parent]
    docs = root / "docs"
    if docs.is_dir() and not docs.is_symlink() and _inside(docs, root) and not (docs / ".git").exists():
        dirs.append(docs)
    dirs.append(root)
    unique = []
    for directory in dirs:
        if directory not in unique:
            unique.append(directory)
    return unique


def _readme_sources(source, root):
    """README.md files of the root, the source's folder and docs/ that exist inside root."""
    root = Path(root).resolve()
    source = Path(source).resolve()
    found = []
    for directory in (root, source.parent, root / "docs"):
        readme = directory / "README.md"
        if directory != root and directory != source.parent and (directory / ".git").exists():
            continue
        if readme.is_file() and not _via_symlink(readme, root) and readme != source:
            resolved = readme.resolve()
            if resolved not in found:
                found.append(resolved)
    return found


def index_path(directory, tmp_root=None, root=None):
    """Return the mirror path of a folder's index page: <mirror folder>/_index.html."""
    directory = Path(directory).resolve()
    root = Path(root).resolve() if root is not None else repo_root(directory / "_")
    return preview_root(tmp_root) / repo_label(root) / directory.relative_to(root) / INDEX_NAME


def _rel_href(target, from_dir):
    return urllib.parse.quote(Path(os.path.relpath(target, from_dir)).as_posix())


def entry_href(path, from_dir, tmp_root=None, root=None):
    """Href for a listed .md file: its preview when one exists, else the raw source file.

    Single decision point: render every listed file here instead if the owner prefers it.
    """
    page = html_path(path, tmp_root, root)
    # A symlinked file is listed but never rendered, so it has no preview of its own.
    if root is None:
        # Resolve the folder only: the file itself may be the symlink.
        path = Path(path).parent.resolve() / Path(path).name
        root = repo_root(path)
    if page.exists() and not _via_symlink(path, root):
        try:
            return _rel_href(page, from_dir)
        except ValueError:
            pass
    return Path(path).resolve().as_uri()


def _dir_label(directory, root):
    relative = Path(directory).resolve().relative_to(Path(root).resolve()).as_posix()
    return repo_label(root) + "/" if relative == "." else relative + "/"


def build_nav(source, root, tmp_root=None, *, expected=()):
    """Footer entries [{label, href}] relative to the source's page; missing pages are left out.

    expected lists README sources and folders whose pages are being written by the caller.
    """
    source = Path(source).resolve()
    root = Path(root).resolve()
    expected = {Path(item).resolve() for item in expected}
    from_dir = html_path(source, tmp_root, root).parent
    entries = []
    seen = set()

    def add(label, page, wanted):
        if page in seen or not (page.exists() or wanted):
            return
        try:
            href = _rel_href(page, from_dir)
        except ValueError:
            return
        seen.add(page)
        entries.append({"label": label, "href": href})

    for readme in _readme_sources(source, root):
        add(readme.relative_to(root).as_posix(), html_path(readme, tmp_root, root), readme in expected)
    for directory in _nav_dirs(source, root):
        if has_index_md(directory):
            continue
        add("Index: " + _dir_label(directory, root), index_path(directory, tmp_root, root), directory in expected)
    return entries


def _list_dir(directory, root):
    """Visible subfolders and .md files of directory that stay inside root, sorted by name."""
    folders, files = [], []
    for entry in sorted(directory.iterdir(), key=lambda e: e.name.casefold()):
        name = entry.name
        if name.startswith(".") or name in SKIPPED_DIRS:
            continue
        if entry.is_symlink():
            if entry.is_file() and name.lower().endswith(".md") and _inside(entry, root):
                files.append(entry)
            continue
        if entry.is_dir():
            folders.append(entry)
        elif entry.is_file() and name.lower().endswith(".md"):
            files.append(entry)
    files.sort(key=lambda e: (e.name != "README.md", e.name.casefold()))
    return folders, files


def render_index(directory, root, tmp_root=None):
    """Write the folder index page for directory and return its path (None when _index.md blocks it)."""
    directory = Path(directory).resolve()
    root = Path(root).resolve()
    if not _inside(directory, root):
        raise ValueError(f"{directory} is outside {root}")
    if has_index_md(directory):
        print(f"skipping folder index for {directory}: _index.md would collide with the page name", file=sys.stderr)
        return None
    folders, files = _list_dir(directory, root)
    target = index_path(directory, tmp_root, root)
    page_dir = target.parent
    title = html.escape(_dir_label(directory, root))
    items = []
    for folder in folders:
        child = page_dir / folder.name / INDEX_NAME
        name = html.escape(folder.name)
        if child.exists():
            href = html.escape(_rel_href(child, page_dir), quote=True)
            items.append(f'<li><a href="{href}">{name}/</a></li>')
        else:
            items.append(f"<li>{name}/</li>")
    folder_list = "".join(items)
    file_items = []
    for entry in files:
        href = html.escape(entry_href(entry, page_dir, tmp_root, root), quote=True)
        file_items.append(f'<li><a href="{href}">{html.escape(entry.name)}</a></li>')
    nav_items = []
    for other in _nav_dirs(directory / "_", root)[1:]:
        if other == directory or has_index_md(other):
            continue
        href = html.escape(_rel_href(index_path(other, tmp_root, root), page_dir), quote=True)
        nav_items.append(f'<li><a href="{href}">Index: {html.escape(_dir_label(other, root))}</a></li>')
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    folders_block = f"<h2>Folders</h2><ul class=\"index-list\">{folder_list}</ul>" if folder_list else ""
    files_block = (
        f"<h2>Markdown files</h2><ul class=\"index-list\">{''.join(file_items)}</ul>"
        if file_items else "<p>No Markdown files.</p>"
    )
    footer = f'<footer id="site-nav" aria-label="Site navigation"><ul>{"".join(nav_items)}</ul></footer>' if nav_items else ""
    page = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{favicon_link()}
<style>{STYLE}</style>
</head>
<body>
<header><code>{html.escape(str(directory))}</code> - folder index generated {html.escape(generated_at)}</header>
<main id="content"><h1>{title}</h1>{folders_block}{files_block}</main>
{footer}
</body>
</html>
"""
    _write_atomic(target, page, preview_root(tmp_root) / repo_label(root))
    return target


def _is_fresh(target, source):
    try:
        built = target.stat().st_mtime_ns
        return built >= source.stat().st_mtime_ns and built >= Path(__file__).stat().st_mtime_ns
    except OSError:
        return False


def _ensure_dirs(base, directory):
    """Create directory below base one level at a time, refusing symlinks and non-folders."""
    try:
        relative = Path(directory).relative_to(base)
    except ValueError:
        raise OSError(f"refusing to write {directory}: outside {base}")
    current = Path(base)
    for part in relative.parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            current.mkdir()
            continue
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise OSError(f"refusing to write through {current}: symlink or not a folder")


def _write_atomic(target, page, base):
    """Write page to target; base is the repo's preview folder, never left or crossed by a symlink."""
    temp_name = None
    try:
        _ensure_dirs(base, target.parent)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as handle:
            temp_name = handle.name
            handle.write(page)
        os.replace(temp_name, target)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def _claim_for(source, tmp_root, root=None):
    proot = preview_root(tmp_root)
    proot.parent.mkdir(parents=True, exist_ok=True)
    proot.mkdir(mode=0o700, exist_ok=True)
    info = proot.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise OSError("preview root is not a directory")
    if hasattr(os, "getuid") and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise OSError("preview root must be owned by the current user and private")
    root = Path(root).resolve() if root is not None else repo_root(source)
    claim_repo_dir(proot / repo_label(root), root, proot)
    return root


def _in_nested_repo(path, root):
    """True when a folder between root (exclusive) and path holds its own .git."""
    for parent in Path(path).parents:
        if parent == root:
            return False
        if (parent / ".git").exists():
            return True
    return True


def render_one(source, tmp_root=None, *, skip_if_fresh, follow=False, text=None, expected=(),
               nested=False, nav_expected=(), root=None, data=None):
    """Write the preview of source and return its path.

    follow renders each linked neighbor (depth 1, never their own links); a neighbor that
    cannot be rendered is reported on stderr and left out of the page's link model.
    expected lists sources whose pages are about to exist (the page that triggered this one).
    nested pages (neighbors, README pages) neither render README pages nor write folder indexes;
    nav_expected lists README sources and folders whose pages the top-level call will write.
    """
    source = Path(source).resolve()
    if root is not None:
        # A neighbor handed over by its parent must still lie inside the parent's root.
        source.relative_to(Path(root).resolve())
    target = html_path(source, tmp_root, root)
    if skip_if_fresh and _is_fresh(target, source):
        return target
    fmt = FORMATS.get(source.suffix.lower(), "md")
    if fmt != "md" and data is None:
        data = load_data(source)
    if fmt != "md":
        fmt = data["fmt"]
        text = data.get("text", "")
    elif text is None:
        text = source.read_text(encoding="utf-8")
    root = _claim_for(source, tmp_root, root)
    nav_dirs = _nav_dirs(source, root)
    readmes = _readme_sources(source, root)
    if not nested:
        nav_expected = (*readmes, *nav_dirs)
        for readme in readmes:
            try:
                render_one(readme, tmp_root, skip_if_fresh=True, expected=(source,), nested=True,
                           nav_expected=nav_expected, root=root)
            except (OSError, ValueError, UnicodeDecodeError) as error:
                print(f"skipping README {readme}: {error}", file=sys.stderr)
    links = []
    # Only Markdown carries links to neighbors.
    for neighbor in (collect_links(text, source, root) if fmt == "md" else ()):
        if not _inside(neighbor, root) or _in_nested_repo(neighbor, root):
            continue
        if follow:
            try:
                render_one(neighbor, tmp_root, skip_if_fresh=True, expected=(source,), nested=True,
                           nav_expected=nav_expected, root=root)
            except (OSError, ValueError, UnicodeDecodeError) as error:
                print(f"skipping linked file {neighbor}: {error}", file=sys.stderr)
                continue
        elif neighbor not in expected and not html_path(neighbor, tmp_root, root).exists():
            continue
        links.append(neighbor.as_uri())
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        nav = build_nav(source, root, tmp_root, expected=nav_expected)
    except (OSError, ValueError) as error:
        print(f"skipping navigation for {source}: {error}", file=sys.stderr)
        nav = []
    model = {"links": links, "nav": nav}
    if fmt != "md":
        model["data"] = data
    _write_atomic(target, render_html(text, source, generated_at, fmt=fmt, model=model),
                  preview_root(tmp_root) / repo_label(root))
    if not nested:
        # Deepest first, so a parent index finds its child's index already written.
        for directory in sorted(nav_dirs, key=lambda d: len(d.parts), reverse=True):
            try:
                render_index(directory, root, tmp_root)
            except (OSError, ValueError) as error:
                print(f"skipping folder index for {directory}: {error}", file=sys.stderr)
    return target


def main(argv, *, tmp_root=None):
    if not argv:
        print("usage: render.py <path-to-file>", file=sys.stderr)
        return 2
    md_path = Path(argv[0])
    suffix = md_path.suffix.lower()
    if suffix not in FORMATS:
        print(f"unsupported file type '{suffix}'; supported: {', '.join(sorted(FORMATS))}", file=sys.stderr)
        return 2
    md_text = data = None
    try:
        if FORMATS[suffix] == "md":
            md_text = md_path.read_text(encoding="utf-8")
        else:
            data = load_data(md_path)
    except (OSError, UnicodeDecodeError) as error:
        print(f"cannot read {md_path}: {error}", file=sys.stderr)
        return 1
    try:
        target = render_one(md_path, tmp_root, skip_if_fresh=False, follow=True, text=md_text, data=data)
    except (OSError, ValueError) as error:
        print(f"cannot write preview: {error}", file=sys.stderr)
        return 1
    print(target.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
