---
card: webdev
gi: 84
slug: semantic-vs-non-semantic-elements
title: Semantic vs non-semantic elements
---

## 1. What it is

**Semantic elements** are HTML tags that carry meaning about the content they contain — they tell the browser, search engine, and assistive technology *what the content is*, not just how it should look.

**Non-semantic elements** carry no meaning about their content — they're generic containers used purely for layout or styling.

```html
<!-- Non-semantic: says nothing about what this IS -->
<div class="navigation">
  <div class="nav-link">Home</div>
  <div class="nav-link">About</div>
</div>

<!-- Semantic: the element type itself explains the content -->
<nav>
  <a href="/">Home</a>
  <a href="/about">About</a>
</nav>
```

Both render identically. The difference is in the *meaning* encoded in the markup.

## 2. Why & when

Non-semantic `<div>` and `<span>` were the dominant tools until HTML5 (2014). The web was full of pages that used `<div class="header">`, `<div class="footer">`, `<div class="nav">` — class names conveying meaning that the HTML itself didn't express.

HTML5 introduced semantic elements because:

1. **Accessibility** — screen readers announce elements by type. `<nav>` is announced as "navigation landmark"; `<div class="nav">` is announced as nothing special.
2. **SEO** — search engines give more weight to content inside `<article>`, `<h1>`, `<main>` than to content inside anonymous `<div>` blocks.
3. **Maintainability** — `<header>` is self-documenting; `<div class="hdr">` requires a class-name convention that must be communicated and enforced.
4. **Browser features** — reader modes in Safari and Firefox use semantic elements to extract article content; headings create a navigable outline in DevTools and AT software.

Use semantic elements always. Fall back to `<div>` / `<span>` only when no semantic element fits.

## 3. Core concept

Think of semantic HTML like **labelled rooms in a building**. A door labelled "Kitchen" tells anyone — visitor, fire marshal, building inspector — what's inside without opening it. A door labelled "Room 4" tells you nothing. Both contain the same food and appliances, but the labelled one is navigable without inspection.

**Non-semantic container elements:**

| Element | Purpose |
|---------|---------|
| `<div>` | Generic block container |
| `<span>` | Generic inline container |

These two elements have no default meaning. Use them only when no semantic element fits.

**Semantic elements by category:**

*Document structure:*
- `<header>` — introductory content for a page or section
- `<nav>` — navigation links
- `<main>` — the primary content (one per page)
- `<footer>` — footer for a page or section
- `<aside>` — tangentially related content (sidebars, callouts)

*Content grouping:*
- `<article>` — self-contained, independently distributable content (blog post, news story)
- `<section>` — a thematic grouping of content, typically with a heading

*Text semantics:*
- `<h1>`–`<h6>` — headings (hierarchy, not size)
- `<p>` — paragraph
- `<blockquote>` — extended quotation
- `<figure>` / `<figcaption>` — self-contained content with optional caption
- `<time>` — machine-readable date/time (`<time datetime="2025-01-15">January 15</time>`)
- `<address>` — contact information
- `<strong>` — strong importance (bold by default, but semantic)
- `<em>` — emphasis (italic by default, but semantic)
- `<mark>` — highlighted/relevant text
- `<code>`, `<pre>`, `<kbd>`, `<samp>`, `<var>` — code and technical content

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side page outlines: left uses all divs with class names, right uses semantic elements that express meaning directly">
  <!-- Non-semantic -->
  <rect x="10" y="10" width="295" height="248" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="157" y="32" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Non-semantic (divs)</text>

  <rect x="25" y="44" width="265" height="30" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="157" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">&lt;div class="header"&gt;</text>

  <rect x="25" y="82" width="265" height="25" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="157" y="99" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">&lt;div class="nav"&gt;</text>

  <rect x="25" y="115" width="265" height="60" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="157" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">&lt;div class="main"&gt;</text>
  <text x="157" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">&lt;div class="article"&gt;</text>

  <rect x="25" y="183" width="265" height="25" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="157" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">&lt;div class="sidebar"&gt;</text>

  <rect x="25" y="216" width="265" height="30" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="157" y="236" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">&lt;div class="footer"&gt;</text>
  <text x="157" y="254" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">meaning in class names only</text>

  <!-- Semantic -->
  <rect x="335" y="10" width="295" height="248" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="482" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Semantic (HTML5)</text>

  <rect x="350" y="44" width="265" height="30" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="482" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;header&gt;</text>

  <rect x="350" y="82" width="265" height="25" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="482" y="99" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;nav&gt;</text>

  <rect x="350" y="115" width="265" height="60" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="482" y="138" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;main&gt;</text>
  <text x="482" y="155" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;article&gt;</text>

  <rect x="350" y="183" width="265" height="25" rx="3" fill="#0d1117" stroke="#79c0ff" stroke-width="0.8"/>
  <text x="482" y="200" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">&lt;aside&gt;</text>

  <rect x="350" y="216" width="265" height="30" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="482" y="236" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;footer&gt;</text>
  <text x="482" y="254" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">meaning in element type itself</text>
</svg>

Same visual layout, radically different meaning: class names express intent to developers; semantic elements express intent to browsers, AT, and search engines.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Semantic Elements Demo</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 1rem; }
    header, footer { background: #1c2430; color: #e6edf3; padding: 1rem; border-radius: 6px; }
    nav a { margin-right: 1rem; color: #6db33f; }
    main { display: flex; gap: 1rem; margin: 1rem 0; }
    article { flex: 3; background: #f6f8fa; padding: 1rem; border-radius: 6px; }
    aside { flex: 1; background: #f6f8fa; padding: 1rem; border-radius: 6px; }
    mark { background: #ffeb3b; }
  </style>
</head>
<body>

  <header>
    <h1>My Blog</h1>
    <nav>
      <a href="/">Home</a>
      <a href="/about">About</a>
      <a href="/contact">Contact</a>
    </nav>
  </header>

  <main>
    <article>
      <h2>Why Semantic HTML Matters</h2>
      <p>Published <time datetime="2025-01-15">January 15, 2025</time></p>
      <p>
        Semantic HTML lets us write markup where the <em>element type itself</em>
        explains the content. A <code>&lt;nav&gt;</code> element is
        <strong>unambiguously</strong> navigation. <mark>Screen readers announce
        it as a landmark</mark>, search engines give it weight, and developers
        understand it without reading class names.
      </p>
      <figure>
        <blockquote cite="https://www.w3.org/TR/html52/">
          "Conformance requirements apply to documents, user agents, and authoring tools."
        </blockquote>
        <figcaption>— HTML5 Specification, W3C</figcaption>
      </figure>
    </article>

    <aside>
      <h3>Related</h3>
      <ul>
        <li><a href="#">ARIA Roles</a></li>
        <li><a href="#">Accessibility</a></li>
      </ul>
    </aside>
  </main>

  <footer>
    <address>Contact: <a href="mailto:hello@example.com">hello@example.com</a></address>
    <p>&copy; 2025 My Blog</p>
  </footer>

  <script>
    // Browsers expose semantic elements as document properties/methods
    console.log("Main element:", document.querySelector("main")?.tagName); // MAIN
    console.log("Nav element:", document.querySelector("nav")?.tagName);   // NAV
    console.log("Article:", document.querySelector("article")?.tagName);   // ARTICLE

    // time's datetime attribute is machine-readable
    const t = document.querySelector("time");
    console.log("datetime attribute:", t.getAttribute("datetime")); // "2025-01-15"
    console.log("display text:", t.textContent);                    // "January 15, 2025"
  </script>
</body>
</html>
```

**How to run:** save as `semantic.html`, open in a browser. Try browser reader mode (if available) — it uses semantic elements to extract the article content.

## 6. Walkthrough

- `<header>` contains the site title and `<nav>`. A screen reader announces: "banner landmark" (the ARIA role implied by page-level `<header>`), then "navigation landmark" for `<nav>`.
- `<main>` wraps the primary content. There should be exactly one `<main>` per page. AT users can jump directly to `<main>` via keyboard shortcut.
- `<article>` marks a self-contained piece of content that makes sense outside the page (share it, syndicate it). `<section>` groups related content that needs the page context.
- `<time datetime="2025-01-15">` — the display text is human-readable ("January 15, 2025"); the `datetime` attribute is machine-readable (ISO 8601 date). Search engines and calendar apps can parse the `datetime` attribute.
- `<figure>` + `<figcaption>` — the spec defines `<figure>` as "self-contained content referenced from the main flow." `<figcaption>` is its caption. Both are commonly used for images, code listings, and charts.
- `<mark>` = highlighted/relevant text (yellow by default). `<strong>` = strong importance. `<em>` = emphasis. These are not just bold/italic — they carry semantic weight used by AT.

## 7. Gotchas & takeaways

> **`<section>` ≠ `<div>` with a heading.** `<section>` should have a heading (`<h2>`, `<h3>`) that labels the section. A generic layout division without a heading is a `<div>`, not a `<section>`.

> **`<article>` can be nested.** A blog post (`<article>`) can contain comment `<article>` elements. Each nested `<article>` is independently distributable.

> **Semantic doesn't mean no `<div>` or `<span>`.** These are still needed for styling hooks when no semantic element fits. The rule is: use semantic when available; fall back to `<div>`/`<span>` when not.

- Semantic elements encode meaning in the element type itself, not in class names.
- Key structural elements: `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`, `<footer>`.
- Accessibility benefits: screen readers announce semantic elements as landmarks users can skip to.
- SEO benefit: `<article>`, `<h1>`–`<h6>`, and `<main>` content gets higher search relevance.
- `<time datetime="...">` — machine-readable date, human-readable display text.
- `<div>` and `<span>` are valid but last-resort containers when no semantic element fits.
