"""Minimal, deterministic Markdown -> HTML. Zero dependencies. Subset suited to
MPSC content: headings, lists, bold/italic/code, links, hr, blockquote,
paragraphs, and raw-HTML block passthrough (lines starting with '<')."""
import re
import html as _html

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_CODE = re.compile(r"`([^`]+?)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline(text):
    # text is already HTML-escaped; apply inline markup
    text = _CODE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _ITAL.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    text = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    return text


def render(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    n = len(lines)
    para = []

    def flush_para():
        if para:
            out.append("<p>" + _inline(_html.escape(" ".join(para))) + "</p>")
            para.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            flush_para(); i += 1; continue

        # raw HTML passthrough (tables etc.)
        if stripped.startswith("<"):
            flush_para(); out.append(stripped); i += 1; continue

        if stripped == "---":
            flush_para(); out.append("<hr>"); i += 1; continue

        m = re.match(r"(#{1,4})\s+(.*)", stripped)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>" + _inline(_html.escape(m.group(2))) + f"</h{lvl}>")
            i += 1; continue

        if stripped.startswith(">"):
            flush_para()
            out.append("<blockquote>" + _inline(_html.escape(stripped[1:].strip())) + "</blockquote>")
            i += 1; continue

        # unordered list
        if re.match(r"[-*]\s+", stripped):
            flush_para(); out.append("<ul>")
            while i < n and re.match(r"[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                out.append("<li>" + _inline(_html.escape(item)) + "</li>")
                i += 1
            out.append("</ul>"); continue

        # ordered list
        if re.match(r"\d+\.\s+", stripped):
            flush_para(); out.append("<ol>")
            while i < n and re.match(r"\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                out.append("<li>" + _inline(_html.escape(item)) + "</li>")
                i += 1
            out.append("</ol>"); continue

        para.append(stripped); i += 1

    flush_para()
    return "\n".join(out)
