---
card: webdev
gi: 81
slug: html-comments
title: HTML comments
---

## 1. What it is

An **HTML comment** is text inside an HTML file that the browser ignores when rendering. Comments are visible in the source code but produce no visual output, no DOM nodes, and no effect on layout.

```html
<!-- This is an HTML comment -->
<p>This paragraph renders normally.</p>
<!-- Comments can span
     multiple lines -->
```

Comments start with `<!--` and end with `-->`. Everything between those delimiters is ignored by the browser's HTML parser.

## 2. Why & when

Comments serve two main purposes:

1. **Documentation** — explaining non-obvious markup choices, marking the start/end of large template sections, or leaving breadcrumbs for future maintainers.
2. **Temporarily disabling markup** — commenting out HTML during debugging or development without deleting it.

Unlike code comments, HTML comments are shipped to users in the page source. Anyone can view them with "View Source." This makes HTML comments appropriate for structural notes but inappropriate for:
- Internal passwords, tokens, or credentials.
- Internal task notes you don't want users to see.
- Business logic, pricing rules, or internal notes.

In templates (Jinja2, Handlebars, ERB, Blade), server-side comment syntax (`{# ... #}`, `{{!-- ... --}}`) is preferred for notes you don't want in the delivered HTML.

## 3. Core concept

Think of HTML comments like **pencil notes on a blueprint**. They help the architect (developer) understand the drawing, but they don't appear on the final building (rendered page). However, anyone looking at the blueprint can still read them — comments are never private.

**Syntax rules:**

```html
<!-- Single line -->

<!--
  Multi-line
  comment
-->

<p>Text <!-- inline comment --> more text</p>

<!-- Commenting out a block:
<nav>
  <a href="/old-page">Old Link</a>
</nav>
-->
```

**What can't go inside a comment:**

```html
<!-- Nested <!-- comments --> are invalid --> ← the first --> ends the comment
<!-- Comments cannot contain two dashes -- in the middle -->  ← browser-dependent parsing
```

The `--` sequence inside a comment is technically not allowed by the HTML5 spec (it was valid in SGML but causes issues in old parsers). Modern browsers handle it, but it's best to avoid double dashes mid-comment.

**JS and CSS comments are different:**

| Context | Comment syntax |
|---------|---------------|
| HTML | `<!-- ... -->` |
| CSS | `/* ... */` |
| JavaScript | `// single line` or `/* multi-line */` |

You cannot use `//` or `/* */` as HTML comments; they will appear as literal text in the page.

**DOM access:** Comments are nodes in the DOM tree (`Comment` node, `nodeType === 8`). JavaScript can read them:

```js
const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_COMMENT);
while (walker.nextNode()) {
  console.log(walker.currentNode.nodeValue); // prints comment text
}
```

This is occasionally used by frameworks that embed metadata in HTML comments (e.g., server-side rendering hydration hints).

## 4. Diagram

<svg viewBox="0 0 580 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTML source showing comments alongside rendered page where comments are invisible">
  <!-- Source -->
  <rect x="10" y="20" width="265" height="160" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="142" y="42" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTML Source</text>
  <text x="25" y="62" fill="#8b949e" font-size="9" font-family="monospace">&lt;!-- Navigation section --&gt;</text>
  <text x="25" y="80" fill="#e6edf3" font-size="9" font-family="monospace">&lt;nav&gt;</text>
  <text x="35" y="96" fill="#e6edf3" font-size="9" font-family="monospace">&lt;a href="/"&gt;Home&lt;/a&gt;</text>
  <text x="25" y="112" fill="#e6edf3" font-size="9" font-family="monospace">&lt;/nav&gt;</text>
  <text x="25" y="130" fill="#8b949e" font-size="9" font-family="monospace">&lt;!-- NOTE: add search later --&gt;</text>
  <text x="25" y="148" fill="#e6edf3" font-size="9" font-family="monospace">&lt;main&gt;...&lt;/main&gt;</text>
  <text x="25" y="166" fill="#8b949e" font-size="9" font-family="monospace">&lt;!-- end main --&gt;</text>

  <!-- Arrow -->
  <text x="295" y="105" fill="#8b949e" font-size="18" text-anchor="middle" font-family="sans-serif">→</text>
  <text x="295" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">browser renders</text>

  <!-- Rendered -->
  <rect x="315" y="20" width="255" height="160" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="443" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Rendered Page</text>
  <text x="330" y="80" fill="#e6edf3" font-size="11" font-family="sans-serif">Home   (nav link)</text>
  <text x="330" y="110" fill="#e6edf3" font-size="11" font-family="sans-serif">...main content...</text>
  <text x="443" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">comments invisible to user</text>
  <text x="443" y="172" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">but visible in View Source</text>
</svg>

Comments appear in HTML source and the DOM tree but produce no visible output on the rendered page.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HTML Comments</title>
</head>
<body>

  <!-- ── HEADER SECTION ────────────────────────── -->
  <header>
    <h1>My Site</h1>
    <!-- NOTE: add a logo here -->
  </header>

  <!-- Main content: article layout -->
  <main>
    <article>
      <h2>Article Title</h2>
      <p>Visible content.</p>

      <!-- Temporarily disabled until designs are approved:
      <aside class="sidebar">
        <h3>Related</h3>
        <ul><li>Link 1</li></ul>
      </aside>
      -->
    </article>
  </main>
  <!-- ── END MAIN ───────────────────────────────── -->

  <script>
    // Access comment nodes from JavaScript
    function findComments(root) {
      const comments = [];
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
      while (walker.nextNode()) {
        comments.push(walker.currentNode.nodeValue.trim());
      }
      return comments;
    }

    const allComments = findComments(document.body);
    console.log("Found comments:", allComments.length);
    allComments.forEach((c, i) => console.log(`[${i}]`, c.slice(0, 60)));

    // Create a comment node programmatically
    const comment = document.createComment(" Added by JavaScript ");
    document.body.appendChild(comment);
  </script>
</body>
</html>
```

**How to run:** save as `comments.html`, open in a browser, check the console (F12) for the comment text. Right-click → "View Page Source" to see comments in the raw HTML.

## 6. Walkthrough

- `<!-- ── HEADER SECTION ──── -->` — section markers like this are common in template files. They act as visual fences making large HTML files navigable. Seen in WordPress themes, Jinja2 templates, and CMS-driven pages.
- The `<aside>` block is commented out. The browser skips the entire block from `<!--` to `-->`. This is a clean way to disable code during development without losing it.
- `document.createTreeWalker(root, NodeFilter.SHOW_COMMENT)` — the TreeWalker API traverses the DOM. `NodeFilter.SHOW_COMMENT` (value `128`) makes it yield only `Comment` nodes. `nodeValue` holds the text between `<!--` and `-->`.
- `document.createComment(" Added by JavaScript ")` creates a `Comment` node. After `appendChild`, it appears in the DOM (and in DevTools Elements panel) but not on screen.
- The JS `allComments.forEach` output shows all comment text — including the multi-line commented-out `<aside>` block, which appears as a single comment string.

## 7. Gotchas & takeaways

> **HTML comments are public.** Users can view page source and see every comment. Never put credentials, API keys, internal URLs, or business-sensitive notes in HTML comments — they ship to every visitor.

> **Nested `<!--` is invalid.** `<!-- outer <!-- inner --> outer -->` — the parser ends the comment at the first `-->`, leaving ` outer -->` as literal text. Nest quotes or use server-side templates for nested comments.

> **Comments aren't stripped in production by default.** JavaScript bundlers (Webpack, Vite) strip JS comments. HTML comments are left as-is unless you use an HTML minifier. Add minification to your build pipeline to remove them from shipped pages.

- Syntax: `<!-- comment text -->`. Multi-line works fine.
- Invisible to users in the rendered page; fully visible in "View Source."
- Use for structural markers and temporary debugging — never for secrets.
- Avoid `--` inside comments; avoid nesting `<!--` inside comments.
- Comments are real DOM nodes (`nodeType === 8`); JS can read them via TreeWalker.
- Strip comments in production via HTML minification to reduce page size.
