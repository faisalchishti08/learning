# -*- coding: utf-8 -*-
"""Zero-dependency Markdown subset -> HTML, for tutorial pages (build-time only)."""
import re
import html

_BLOCK_HTML = re.compile(r"^<(svg|div|table|figure|pre|details|section|aside)\b", re.I)
NL = chr(10)


def _inline(text):
    codes = []

    def stash(m):
        codes.append(html.escape(m.group(1)))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])_([^_]+)_(?![\w*])", r"<em>\1</em>", text)

    def unstash(m):
        return "<code>%s</code>" % codes[int(m.group(1))]

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def convert(src):
    lines = src.split(NL)
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()

        # fenced code
        if s.startswith("```"):
            lang = s[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            cls = ' class="lang-%s"' % lang if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, html.escape(NL.join(buf))))
            continue

        # raw block html (svg etc.)
        m = _BLOCK_HTML.match(s)
        if m:
            close = "</%s>" % m.group(1)
            buf = [line]
            if close.lower() not in line.lower():
                i += 1
                while i < n and close.lower() not in lines[i].lower():
                    buf.append(lines[i])
                    i += 1
                if i < n:
                    buf.append(lines[i])
            i += 1
            out.append(NL.join(buf))
            continue

        if not s:
            i += 1
            continue

        # heading
        hm = re.match(r"(#{1,6})\s+(.*)", s)
        if hm:
            lvl = len(hm.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, _inline(hm.group(2)), lvl))
            i += 1
            continue

        # table (header + separator row)
        if "|" in line and i + 1 < n and "-" in lines[i + 1] and \
           re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            header = _cells(lines[i])
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            thead = "".join("<th>%s</th>" % _inline(c) for c in header)
            body = ""
            for r in rows:
                body += "<tr>" + "".join("<td>%s</td>" % _inline(c) for c in r) + "</tr>"
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (thead, body))
            continue

        # blockquote
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % _inline(" ".join(buf)))
            continue

        # unordered list
        if re.match(r"^[-*]\s+", s):
            buf = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                buf.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % _inline(x) for x in buf) + "</ul>")
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", s):
            buf = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                buf.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % _inline(x) for x in buf) + "</ol>")
            continue

        # paragraph
        buf = []
        while i < n:
            t = lines[i].strip()
            if not t or t.startswith("```") or _BLOCK_HTML.match(t) or \
               re.match(r"(#{1,6})\s|^[-*]\s|^\d+\.\s|^>", t):
                break
            buf.append(t)
            i += 1
        out.append("<p>%s</p>" % _inline(" ".join(buf)))

    return NL.join(out)
