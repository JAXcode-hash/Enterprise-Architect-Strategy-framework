"""A small, dependency-free Markdown subset renderer.

Handles exactly what this framework emits: headings, tables, lists, fenced
code, blockquotes, paragraphs, and inline bold / italic / code / links. Not a
general Markdown implementation and does not try to be one.
"""

from __future__ import annotations

import html
import re

_INLINE = (
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)"), r"<em>\1</em>"),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), r'<a href="\2">\1</a>'),
)


def _inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = out.replace("\\|", "|")
    for pattern, repl in _INLINE:
        out = pattern.sub(repl, out)
    return out


def _row_cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    parts, buf, escaped = [], "", False
    for ch in body:
        if escaped:
            buf += ch
            escaped = False
        elif ch == "\\":
            buf += ch
            escaped = True
        elif ch == "|":
            parts.append(buf.strip())
            buf = ""
        else:
            buf += ch
    parts.append(buf.strip())
    return parts


def _is_divider(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|", line.strip()))


def render(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    list_open: str | None = None

    def close_list():
        nonlocal list_open
        if list_open:
            out.append(f"</{list_open}>")
            list_open = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            close_list()
            lang = stripped[3:].strip()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre{cls}><code>{html.escape(chr(10).join(block))}</code></pre>")
            continue

        if not stripped:
            close_list()
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and _is_divider(lines[i + 1]):
            close_list()
            head = _row_cells(stripped)
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(_row_cells(lines[i]))
                i += 1
            out.append('<div class="tw"><table><thead><tr>'
                       + "".join(f"<th>{_inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>")
            for row in body:
                row += [""] * (len(head) - len(row))
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row[:len(head)])
                           + "</tr>")
            out.append("</tbody></table></div>")
            continue

        if stripped.startswith(">"):
            close_list()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote>{_inline(' '.join(quote))}</blockquote>")
            continue

        if re.match(r"^---+$", stripped):
            close_list()
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m:
            if list_open != "ul":
                close_list()
                out.append("<ul>")
                list_open = "ul"
            out.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue

        m = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if m:
            if list_open != "ol":
                close_list()
                out.append("<ol>")
                list_open = "ol"
            out.append(f"<li>{_inline(m.group(1))}</li>")
            i += 1
            continue

        close_list()
        para = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|\||>|```|[-*]\s|\d+[.)]\s|---+$)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(para))}</p>")

    close_list()
    return "\n".join(out)
