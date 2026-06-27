---
card: webdev
gi: 85
slug: header-nav-main-section-article-aside-footer
title: header, nav, main, section, article, aside, footer
---

## 1. What it is

HTML5 introduced seven **sectioning and landmark elements** that describe the major regions of a page. Together they form the semantic skeleton of almost every web page or app:

| Element | Role | ARIA Landmark |
|---------|------|--------------|
| `<header>` | Introductory content for a page or section | `banner` (page-level) |
| `<nav>` | Navigation links | `navigation` |
| `<main>` | The primary, unique content of the page | `main` |
| `<section>` | A thematic grouping of related content | `region` (if titled) |
| `<article>` | Self-contained, independently distributable content | `article` |
| `<aside>` | Tangentially related content | `complementary` |
| `<footer>` | Footer for a page or section | `contentinfo` (page-level) |

Each implies an ARIA landmark role automatically, giving screen reader users keyboard shortcuts to jump between regions without wading through all content linearly.

## 2. Why & when

Before these elements, page regions were anonymous `<div>` blocks identified only by class names or IDs. Screen reader users had no way to skip to the main content or find the navigation without an explicit `role` attribute or skip link.

These elements exist to:
1. **Give structure a voice** — AT announces the landmark, users can jump directly to it.
2. **Create a navigable outline** — headings inside sectioning elements form a hierarchy DevTools and AT can surface.
3. **Enable features** — browser Reader Mode extracts `<article>` content. Search engines boost content in `<article>` and `<main>`.

Use them in every page you build. They cost nothing and make the page meaningfully accessible and machine-readable.

## 3. Core concept

Think of these elements like the **rooms and zones of a building**. `<header>` is the lobby. `<nav>` is the directory board. `<main>` is the main floor. `<article>` is a self-contained exhibit. `<section>` is an area within the exhibit. `<aside>` is a coat room or gift shop — related to the visit, but not the main point. `<footer>` is the exit hall with information signs.

**`<header>`**
- Contains site logo, site title, primary `<nav>`.
- Can also appear inside `<article>` or `<section>` as a section header (not a page header).
- Page-level `<header>` gets ARIA role `banner`; nested ones don't.
- Does not include the `<main>` content.

**`<nav>`**
- Only for major navigation blocks (primary site nav, breadcrumb, pagination).
- Don't wrap every list of links in `<nav>` — only groups of links whose primary purpose is navigation.
- Multiple `<nav>` elements are valid; label them with `aria-label` to distinguish: `<nav aria-label="Primary">`, `<nav aria-label="Breadcrumb">`.

**`<main>`**
- **One per page.** The unique content that differs across pages. Don't include repeated chrome (header, nav, footer) here.
- Screen reader shortcut: `Main` landmark is typically accessible via a single key press.

**`<section>`**
- A thematic grouping that belongs to the current document context.
- Should have a heading (`<h2>`, `<h3>`) that names the section.
- If you can't think of a meaningful heading, use `<div>` instead.

**`<article>`**
- Self-contained: makes sense on its own, can be syndicated or shared.
- Typical uses: blog post, news article, forum post, product card, comment, widget.
- Can be nested — a blog post `<article>` can contain `<article>` elements for comments.

**`<aside>`**
- Content that relates to but is separable from the surrounding content.
- Page-level: sidebar, related links, author bio.
- Inline: pull quote, call-out box within an article.

**`<footer>`**
- Contains copyright, legal links, secondary nav, contact info (`<address>`).
- Can appear inside `<article>` (article footer: tags, share buttons, date) or `<section>`.
- Page-level `<footer>` gets ARIA role `contentinfo`.

## 4. Diagram

<svg viewBox="0 0 560 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Typical page layout showing header at top, nav below, main content with article and aside side by side, section inside main, and footer at bottom">
  <!-- Outer page -->
  <rect x="10" y="10" width="540" height="360" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>

  <!-- header -->
  <rect x="20" y="20" width="520" height="50" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="280" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace" font-weight="bold">&lt;header&gt;</text>
  <text x="280" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">logo · site title · [nav]</text>

  <!-- nav -->
  <rect x="20" y="78" width="520" height="32" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="280" y="99" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">&lt;nav&gt;  Home · About · Contact&lt;/nav&gt;</text>

  <!-- main -->
  <rect x="20" y="118" width="520" height="190" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="50" y="138" fill="#6db33f" font-size="12" font-family="monospace" font-weight="bold">&lt;main&gt;</text>

  <!-- article -->
  <rect x="30" y="145" width="345" height="150" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1.2"/>
  <text x="45" y="163" fill="#6db33f" font-size="10" font-family="monospace">&lt;article&gt;</text>
  <text x="45" y="180" fill="#8b949e" font-size="9" font-family="sans-serif">  &lt;h2&gt;Post Title&lt;/h2&gt;</text>
  <text x="45" y="196" fill="#8b949e" font-size="9" font-family="sans-serif">  &lt;p&gt;...content...&lt;/p&gt;</text>

  <!-- section inside article -->
  <rect x="38" y="205" width="328" height="75" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="50" y="223" fill="#8b949e" font-size="9" font-family="monospace">&lt;section&gt;</text>
  <text x="58" y="239" fill="#8b949e" font-size="9" font-family="sans-serif">&lt;h3&gt;Section heading&lt;/h3&gt;</text>
  <text x="58" y="255" fill="#8b949e" font-size="9" font-family="sans-serif">&lt;p&gt;Thematic block of content&lt;/p&gt;</text>
  <text x="50" y="271" fill="#8b949e" font-size="9" font-family="monospace">&lt;/section&gt;</text>

  <!-- aside -->
  <rect x="383" y="145" width="148" height="150" rx="3" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="390" y="163" fill="#79c0ff" font-size="10" font-family="monospace">&lt;aside&gt;</text>
  <text x="390" y="180" fill="#8b949e" font-size="9" font-family="sans-serif">  Related links</text>
  <text x="390" y="196" fill="#8b949e" font-size="9" font-family="sans-serif">  Author bio</text>
  <text x="390" y="212" fill="#8b949e" font-size="9" font-family="sans-serif">  Ads / callouts</text>
  <text x="390" y="280" fill="#79c0ff" font-size="10" font-family="monospace">&lt;/aside&gt;</text>

  <text x="500" y="300" fill="#6db33f" font-size="12" font-family="monospace">&lt;/main&gt;</text>

  <!-- footer -->
  <rect x="20" y="316" width="520" height="44" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="280" y="335" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">&lt;footer&gt;</text>
  <text x="280" y="352" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">© 2025 · Privacy · Terms · contact info</text>
</svg>

The seven elements together cover the complete semantic skeleton of a typical web page.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Semantic Layout</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: sans-serif; color: #1a1a1a; background: #f5f5f5; }

    header  { background: #1c2430; color: #e6edf3; padding: 1rem 2rem; display: flex; align-items: center; gap: 2rem; }
    header h1 { font-size: 1.25rem; }
    nav a   { color: #6db33f; text-decoration: none; margin-right: 1rem; font-weight: 500; }
    nav a:hover { text-decoration: underline; }

    .layout { max-width: 900px; margin: 1.5rem auto; padding: 0 1rem; display: grid; grid-template-columns: 1fr 260px; gap: 1.5rem; }

    main    { min-width: 0; }
    article { background: white; border-radius: 8px; padding: 1.5rem; }
    section { margin-top: 1.5rem; border-top: 2px solid #6db33f; padding-top: 1rem; }

    aside   { background: white; border-radius: 8px; padding: 1.5rem; align-self: start; }
    aside h3 { color: #6db33f; margin-bottom: 0.5rem; }
    aside ul { padding-left: 1.2rem; }

    footer  { background: #1c2430; color: #8b949e; text-align: center; padding: 1.5rem; margin-top: 2rem; }
    footer a { color: #6db33f; }
    time    { color: #8b949e; font-size: 0.875rem; }
  </style>
</head>
<body>

  <header>
    <h1>My Blog</h1>
    <nav aria-label="Primary">
      <a href="/">Home</a>
      <a href="/archive">Archive</a>
      <a href="/about">About</a>
    </nav>
  </header>

  <div class="layout">
    <main>
      <article>
        <header>  <!-- article-level header, not page-level -->
          <h2>Getting Started with Semantic HTML</h2>
          <p>By Alice · <time datetime="2025-06-01">June 1, 2025</time></p>
        </header>

        <p>Semantic elements transform anonymous divs into meaningful landmarks that browsers, screen readers, and search engines can understand.</p>

        <section aria-labelledby="why-heading">
          <h3 id="why-heading">Why it matters</h3>
          <p>Screen readers can jump directly to the <code>&lt;main&gt;</code> content, skipping repeated navigation. Reader Mode extracts <code>&lt;article&gt;</code> content automatically.</p>
        </section>

        <section aria-labelledby="how-heading">
          <h3 id="how-heading">How to use it</h3>
          <p>Replace <code>&lt;div class="nav"&gt;</code> with <code>&lt;nav&gt;</code>. Replace <code>&lt;div class="main"&gt;</code> with <code>&lt;main&gt;</code>. Each element now carries its own meaning.</p>
        </section>

        <footer>  <!-- article-level footer -->
          <p>Tags: <a href="/tag/html">HTML</a>, <a href="/tag/a11y">Accessibility</a></p>
        </footer>
      </article>
    </main>

    <aside aria-label="Related content">
      <h3>Related Posts</h3>
      <ul>
        <li><a href="#">ARIA Roles Explained</a></li>
        <li><a href="#">CSS for Accessibility</a></li>
        <li><a href="#">HTML5 Form Elements</a></li>
      </ul>
    </aside>
  </div>

  <footer>
    <nav aria-label="Footer">
      <a href="/privacy">Privacy</a> ·
      <a href="/terms">Terms</a> ·
      <a href="/contact">Contact</a>
    </nav>
    <p style="margin-top:0.5rem">&copy; 2025 My Blog</p>
  </footer>

</body>
</html>
```

**How to run:** save as `layout.html`, open in a browser. Use accessibility inspector or VoiceOver/NVDA to hear landmark announcements.

## 6. Walkthrough

- `<header>` at page level — contains the blog name and primary `<nav>`. Gets ARIA role `banner` automatically.
- `<nav aria-label="Primary">` — the `aria-label` distinguishes this from the footer nav. Screen readers announce "Primary navigation landmark" vs "Footer navigation landmark."
- `<main>` — the unique content. Only one per page.
- `<article>` has its own nested `<header>` (article title + byline) and `<footer>` (tags). This is valid — `<header>` and `<footer>` inside a sectioning element are scoped to that section, not the page.
- `<section aria-labelledby="why-heading">` — sections get ARIA role `region` when they have an accessible name. `aria-labelledby="why-heading"` links the section to its `<h3 id="why-heading">` for AT.
- `<aside aria-label="Related content">` — sidebar content. `aria-label` gives AT users context without a visual heading.
- `<footer>` at page level — gets ARIA role `contentinfo`. Contains a second `<nav>` (footer links) and copyright.

## 7. Gotchas & takeaways

> **Only one `<main>` per page.** Two `<main>` elements is invalid HTML. If you need to show/hide sections, put them inside one `<main>` and toggle visibility with CSS/JS.

> **`<section>` without a heading is questionable.** The spec says sections "typically have a heading." A `<section>` with no heading is nearly indistinguishable from a `<div>`. Add a heading or switch to `<div>`.

> **Multiple `<nav>` elements need `aria-label`.** Screen readers list all landmark elements by type. Two `<nav>` elements that both say "navigation" are useless. Label them: "Primary", "Breadcrumb", "Footer", etc.

> **`<header>` and `<footer>` inside `<article>` or `<section>` are not page landmarks.** Only the outermost (direct children of `<body>`) get `banner` / `contentinfo` roles. Nested `<header>` and `<footer>` are generic.

- `<main>` — once per page; primary content; AT can skip to it directly.
- `<article>` — self-contained; syndicatable; nestable (comments inside posts).
- `<section>` — thematic grouping that needs a heading; scoped to parent context.
- `<aside>` — supplementary; sidebar or inline callout.
- `<nav>` — major navigation only; use `aria-label` when multiple `<nav>` elements exist.
- `<header>` / `<footer>` — page-level OR section-level; context determines the ARIA role.
