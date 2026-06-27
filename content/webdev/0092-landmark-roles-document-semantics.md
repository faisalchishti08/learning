---
card: webdev
gi: 92
slug: landmark-roles-document-semantics
title: Landmark roles & document semantics
---

## 1. What it is

**ARIA landmark roles** are semantic labels that identify the major regions of a page for assistive technology (AT). Screen readers expose landmarks as a navigation shortcut — users can jump directly to any landmark without reading through all preceding content.

HTML5 semantic elements automatically imply landmark roles. You get landmarks for free just by using the right elements:

| Semantic element | Implicit landmark role | AT label |
|-----------------|----------------------|---------|
| `<header>` (page-level) | `banner` | "banner" |
| `<nav>` | `navigation` | "navigation" |
| `<main>` | `main` | "main" |
| `<aside>` | `complementary` | "complementary" |
| `<footer>` (page-level) | `contentinfo` | "content info" |
| `<section>` with accessible name | `region` | name of section |
| `<form>` with accessible name | `form` | name of form |
| `<search>` | `search` | "search" |

You can also assign roles explicitly with ARIA: `role="banner"`, `role="main"`, etc. — but prefer semantic elements when they exist.

## 2. Why & when

Screen reader users navigate long pages using two main strategies: headings and landmarks. A page with good landmark structure lets a user land at `<main>` in one keystroke, jump to `<nav>`, jump to the search form — without pressing Tab through every interactive element.

Without landmarks, a screen reader user hears everything sequentially from the top. With landmarks, the page is as scannable for them as visual layout is for sighted users.

Use ARIA roles explicitly when:
- You can't use the semantic HTML element (e.g., a legacy `<div>` codebase, a custom component system).
- You need to add a role that has no HTML equivalent (`role="search"` predates `<search>`).
- You have multiple of the same landmark and need `aria-label` to distinguish them.

## 3. Core concept

Think of landmark roles like **floor signs in a shopping mall**. Floor signs show "Food Court", "Parking", "Restrooms" — users scan the signs to navigate, not every store. Landmarks are the page's floor signs. Without them, AT users must walk every aisle.

**Landmark roles reference:**

`banner` — the page header (site logo, title, primary nav). Only one per page; provided by `<header>` at the body level.

`navigation` — a major navigation block. Multiple `<nav>` elements create multiple `navigation` landmarks. Label each with `aria-label` or `aria-labelledby` to distinguish them.

```html
<nav aria-label="Primary">...</nav>
<nav aria-label="Breadcrumb">...</nav>
<nav aria-label="Pagination">...</nav>
```

`main` — the primary content. One per page. The landmark AT users jump to with "go to main content." Also used by "skip to content" links.

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
...
<main id="main-content">...</main>
```

`complementary` — content that complements `main` but makes sense independently (sidebars, related links). Provided by `<aside>`.

`contentinfo` — page footer (copyright, terms, contact). One per page; provided by `<footer>` at the body level.

`region` — a notable section. Only becomes a landmark if it has an accessible name (`aria-labelledby` or `aria-label`). Without a name, `<section>` has no landmark role.

```html
<section aria-labelledby="trending-heading">
  <h2 id="trending-heading">Trending Topics</h2>
  ...
</section>
```

`form` — a form region. `<form>` only gets the landmark role when it has an accessible name.

`search` — the search region. Use `<search>` element (HTML 2023) or `<form role="search">`.

**The skip link pattern** — mandatory for keyboard-only users. The first interactive element on every page should be a skip link that jumps to `<main>`:

```html
<a href="#main" class="skip-link">Skip to content</a>

<style>
.skip-link {
  position: absolute;
  left: -9999px;
}
.skip-link:focus {
  left: 0;
  top: 0;
  z-index: 9999;
  padding: 0.5rem 1rem;
  background: #6db33f;
  color: white;
}
</style>
```

## 4. Diagram

<svg viewBox="0 0 580 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Page layout annotated with landmark role names next to each semantic region">
  <!-- Skip link -->
  <rect x="10" y="10" width="560" height="24" rx="3" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="290" y="26" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">"Skip to main content" link (visible on focus, first element in tab order)</text>

  <!-- banner -->
  <rect x="10" y="42" width="560" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="290" y="62" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">&lt;header&gt;  →  role="banner"</text>
  <text x="290" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Site logo · site title</text>

  <!-- navigation -->
  <rect x="10" y="93" width="560" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="290" y="113" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">&lt;nav aria-label="Primary"&gt;  →  role="navigation"</text>

  <!-- main + aside row -->
  <rect x="10" y="130" width="385" height="140" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="202" y="152" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">&lt;main&gt;  →  role="main"</text>
  <rect x="20" y="160" width="365" height="100" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="202" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">&lt;section aria-labelledby="h"&gt;</text>
  <text x="202" y="202" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→  role="region" (only when named)</text>
  <text x="202" y="246" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">primary content here</text>

  <rect x="402" y="130" width="168" height="140" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="486" y="152" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">&lt;aside&gt;</text>
  <text x="486" y="167" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">role="complementary"</text>
  <text x="486" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">sidebar</text>
  <text x="486" y="215" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">related links</text>

  <!-- footer / contentinfo -->
  <rect x="10" y="278" width="560" height="34" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="290" y="299" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">&lt;footer&gt;  →  role="contentinfo"</text>
  <text x="290" y="306" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">copyright · terms · contact</text>
</svg>

Semantic elements imply ARIA landmark roles automatically — no extra attributes needed except `aria-label` when multiple landmarks of the same type exist.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Landmark Roles Demo</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; }

    .skip-link {
      position: absolute;
      left: -9999px;
      top: 0;
      background: #6db33f;
      color: white;
      padding: 0.5rem 1rem;
      text-decoration: none;
      font-weight: bold;
      z-index: 9999;
    }
    .skip-link:focus { left: 0; }

    header  { background: #1c2430; color: #e6edf3; padding: 1rem 2rem; }
    nav a   { color: #6db33f; margin-right: 1rem; }
    .layout { display: grid; grid-template-columns: 1fr 220px; gap: 1rem; max-width: 900px; margin: 1rem auto; padding: 0 1rem; }
    main    { min-width: 0; }
    aside   { background: #f5f5f5; padding: 1rem; border-radius: 6px; align-self: start; }
    footer  { background: #1c2430; color: #8b949e; padding: 1rem 2rem; margin-top: 1rem; }

    /* role="search" styling */
    [role="search"] { display: flex; gap: 0.5rem; }
    [role="search"] input { padding: 0.3rem 0.6rem; border: 1px solid #ddd; border-radius: 4px; flex: 1; }
  </style>
</head>
<body>

  <!-- 1: skip link (must be first) -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <!-- 2: banner landmark -->
  <header>
    <h1>My Site</h1>
    <!-- 3: navigation landmark with label -->
    <nav aria-label="Primary">
      <a href="/">Home</a>
      <a href="/articles">Articles</a>
      <a href="/about">About</a>
    </nav>
    <!-- 4: search landmark -->
    <form role="search" aria-label="Site search">
      <input type="search" aria-label="Search terms">
      <button type="submit">Search</button>
    </form>
  </header>

  <div class="layout">
    <!-- 5: main landmark -->
    <main id="main-content">
      <!-- 6: named region landmark -->
      <section aria-labelledby="featured-heading">
        <h2 id="featured-heading">Featured Article</h2>
        <article>
          <h3>Getting Started with Landmarks</h3>
          <p>Landmark roles make pages navigable for screen reader users.</p>
        </article>
      </section>
    </main>

    <!-- 7: complementary landmark -->
    <aside aria-label="Related content">
      <h3>Related</h3>
      <ul><li><a href="#">ARIA Deep Dive</a></li></ul>
    </aside>
  </div>

  <!-- 8: contentinfo landmark -->
  <footer>
    <!-- second nav needs a different label -->
    <nav aria-label="Footer">
      <a href="/privacy">Privacy</a> ·
      <a href="/terms">Terms</a>
    </nav>
    <p>&copy; 2025 My Site</p>
  </footer>

  <script>
    // List all ARIA landmark roles on the page
    const landmarkSelectors = [
      "[role='banner'], header:not(article header):not(section header):not(aside header)",
      "[role='navigation'], nav",
      "[role='main'], main",
      "[role='complementary'], aside",
      "[role='contentinfo'], footer:not(article footer):not(section footer):not(aside footer)",
      "[role='search'], search",
      "[role='region'][aria-labelledby], [role='region'][aria-label], section[aria-labelledby], section[aria-label]",
      "[role='form'][aria-label], [role='form'][aria-labelledby]",
    ];
    landmarkSelectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(el => {
        const role = el.getAttribute("role") || el.tagName.toLowerCase();
        const label = el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || "";
        console.log(`${role}${label ? ` (${label})` : ""}:`, el.tagName);
      });
    });
  </script>
</body>
</html>
```

**How to run:** save as `landmarks.html`, open in a browser. Press Tab — the skip link is the first focusable element. With macOS VoiceOver (Cmd+F5), press Caps Lock+U to list all landmarks.

## 6. Walkthrough

- `<a href="#main-content" class="skip-link">` — visually hidden until focused (positioned off-screen with `left: -9999px`). When a keyboard user presses Tab on arrival, this is the first stop. Activating it jumps directly to `<main id="main-content">`.
- `<header>` at page level — gets `banner` role. The same `<header>` inside `<article>` or `<section>` does NOT get a landmark role (the CSS selector `:not(article header)` in the demo illustrates this).
- `<nav aria-label="Primary">` and `<nav aria-label="Footer">` — two `<nav>` elements both produce `navigation` landmarks. The `aria-label` makes them distinguishable: "Primary navigation" vs "Footer navigation."
- `<form role="search">` — `<form>` without a name has no landmark role. `role="search"` adds the search landmark. The newer `<search>` HTML element does this natively.
- `<section aria-labelledby="featured-heading">` — without `aria-labelledby`, `<section>` has no landmark role. The `aria-labelledby` pointing to the `<h2>` gives it the `region` landmark role with the heading text as its name.
- `<aside aria-label="Related content">` — `<aside>` always gets the `complementary` landmark role. The `aria-label` provides a descriptive name for users who navigate by landmarks.

## 7. Gotchas & takeaways

> **Nested `<header>` and `<footer>` don't get landmark roles.** `<header>` inside an `<article>` is not a `banner`; `<footer>` inside a `<section>` is not `contentinfo`. Only the top-level (direct or indirect child of `<body>`) versions get those roles.

> **`<section>` without an accessible name is NOT a landmark.** A nameless `<section>` has no ARIA role. Add `aria-labelledby` pointing to its heading, or `aria-label`, to activate the `region` landmark role.

> **Don't overuse landmarks.** Not every `<div>` needs a role and not every section needs to be a landmark. Too many landmarks are as bad as none — AT users get an overwhelming list. Use landmarks for the major, navigable regions of the page.

- HTML5 semantic elements give landmark roles for free — just use them correctly.
- Skip link = first element in tab order, jumps to `<main>` — required for keyboard accessibility.
- Multiple same-type landmarks need `aria-label` to distinguish them.
- `<section>` only becomes a `region` landmark when it has an accessible name.
- Inspect landmarks in DevTools → Accessibility panel, or use a screen reader's landmark list.
