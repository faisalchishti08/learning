---
card: webdev
gi: 93
slug: anchor-links-href-target-rel
title: Anchor links (href, target, rel)
---

## 1. What it is

The `<a>` (anchor) element creates hyperlinks. Three attributes drive its behaviour:

- **`href`** — the destination URL or in-page anchor. Where does the link go?
- **`target`** — which browsing context opens the link. Same tab? New tab?
- **`rel`** — the relationship between this page and the destination. Affects SEO, security, and browser behaviour.

```html
<a href="https://example.com" target="_blank" rel="noopener noreferrer">
  Open Example in a new tab
</a>
```

An `<a>` without `href` is an inert anchor — it renders as text with no link behaviour and no default cursor.

## 2. Why & when

Every hyperlink in a web page uses `<a>`. Understanding these three attributes is foundational:

- `href` determines where the user goes — wrong href = broken link.
- `target="_blank"` is common for external links and downloadable resources, but it comes with a security implication that requires `rel="noopener"`.
- `rel` values like `nofollow`, `noopener`, and `noreferrer` affect SEO (telling search engines not to pass "link juice") and security (preventing the opened page from accessing `window.opener`).

## 3. Core concept

**`href` values:**

| Value | Example | Behaviour |
|-------|---------|----------|
| Absolute URL | `https://example.com/page` | External page |
| Relative URL | `../about` | Relative to current page's URL |
| Root-relative | `/about` | Relative to site root |
| In-page anchor | `#section1` | Scrolls to element with that id |
| Empty anchor | `#` | Scrolls to page top |
| `javascript:void(0)` | — | Deprecated; use `<button>` instead |
| `mailto:` | `mailto:you@example.com` | Opens email client |
| `tel:` | `tel:+15551234567` | Initiates a phone call |
| `data:` | Base64 inline | Opens a data URI |

**`target` values:**

| Value | Behaviour |
|-------|----------|
| (absent) | Same tab, same browsing context |
| `_blank` | New tab (or window) |
| `_self` | Same tab (explicit) |
| `_parent` | Parent frame/browsing context |
| `_top` | Top-level frame (breaks out of all frames) |
| `frameName` | Named iframe/window |

**`rel` values (combinable, space-separated):**

| Value | Effect |
|-------|--------|
| `noopener` | New tab cannot access `window.opener` — security protection |
| `noreferrer` | Does not send `Referer` header + implies `noopener` |
| `nofollow` | Tells search engines not to follow this link or pass PageRank |
| `sponsored` | Marks a paid/sponsored link (Google's directive) |
| `ugc` | User-generated content (comments, forum posts) |
| `external` | Indicates link goes to a different site (hint for browsers/AT) |

**`target="_blank"` security:** A page opened in a new tab via `target="_blank"` can access the opener's `window.opener` object and redirect the original tab with `window.opener.location = 'phishing.com'`. This is a **tabnapping** attack. Fix: always add `rel="noopener noreferrer"` to any `target="_blank"` link.

Modern browsers (Chrome 88+, Firefox 79+) now default `rel="noopener"` for `target="_blank"` links automatically, but it's still best practice to write it explicitly.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anchor element with href, target, and rel attributes annotated, showing same-tab vs new-tab destinations and security implications">
  <defs>
    <marker id="arr93g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr93b" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Code box -->
  <rect x="10" y="10" width="620" height="55" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="25" y="38" fill="#e6edf3" font-size="12" font-family="monospace">&lt;a  href="https://example.com"  target="_blank"  rel="noopener noreferrer"&gt;</text>

  <!-- href label -->
  <line x1="75" y1="65" x2="75" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr93g)"/>
  <text x="75" y="110" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">href — where</text>

  <!-- target label -->
  <line x1="290" y1="65" x2="290" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr93b)"/>
  <text x="290" y="110" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">target — where to open</text>

  <!-- rel label -->
  <line x1="470" y1="65" x2="470" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr93g)"/>
  <text x="470" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rel — relationship + security</text>

  <!-- Current page box -->
  <rect x="20" y="130" width="170" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Current tab</text>
  <text x="105" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">page.com</text>
  <text x="105" y="183" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">window.opener = null ✓</text>

  <!-- New tab box -->
  <rect x="440" y="130" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">New tab (target=_blank)</text>
  <text x="530" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">example.com</text>
  <text x="530" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">rel="noopener" → can't access opener</text>

  <!-- Same-tab arrow -->
  <line x1="192" y1="160" x2="248" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr93g)"/>
  <text x="320" y="155" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">target omitted → same tab</text>
  <line x1="392" y1="160" x2="438" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr93g)" stroke-dasharray="4,2"/>

  <!-- _blank arrow (curved effect via two lines) -->
  <line x1="320" y1="180" x2="438" y2="160" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr93b)"/>
  <text x="370" y="200" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">target=_blank → new tab</text>

  <!-- Security note -->
  <rect x="10" y="212" width="620" height="38" rx="4" fill="#2d1117" stroke="#f85149" stroke-width="1"/>
  <text x="320" y="228" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Security: always add rel="noopener noreferrer" to target="_blank" links</text>
  <text x="320" y="244" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Without it, the new tab can redirect your original page (tabnapping attack)</text>
</svg>

`href` = destination; `target` = which context opens it; `rel="noopener noreferrer"` is mandatory security for `target="_blank"`.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Anchor Links</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
    a    { color: #6db33f; }
    .link-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .link-grid a { background: #1c2430; color: #e6edf3; padding: 0.5rem 0.75rem; border-radius: 4px; text-decoration: none; font-size: 0.875rem; }
    .link-grid a:hover { background: #6db33f; }
    #section-a, #section-b { margin: 3rem 0; padding: 2rem; background: #f5f5f5; border-radius: 6px; }
  </style>
</head>
<body>

  <h1 id="top">Anchor Links Demo</h1>

  <h2>Link types</h2>
  <div class="link-grid">
    <!-- Absolute URL, new tab, secure -->
    <a href="https://developer.mozilla.org" target="_blank" rel="noopener noreferrer">
      External link (new tab)
    </a>

    <!-- Root-relative URL, same tab -->
    <a href="/about">Root-relative (same tab)</a>

    <!-- In-page anchor — smooth scroll with CSS -->
    <a href="#section-a">Jump to Section A</a>
    <a href="#section-b">Jump to Section B</a>

    <!-- Back to top -->
    <a href="#top">Back to top</a>

    <!-- mailto -->
    <a href="mailto:hello@example.com?subject=Hello&body=Hi%20there">Email us</a>

    <!-- tel -->
    <a href="tel:+15551234567">Call +1 (555) 123-4567</a>

    <!-- Download -->
    <a href="/report.pdf" download="annual-report-2025.pdf" rel="noopener">
      Download PDF
    </a>
  </div>

  <!-- nofollow example -->
  <p style="margin-top:1rem">
    User review on:
    <a href="https://externalreview.com" rel="nofollow noopener noreferrer" target="_blank">
      externalreview.com
    </a>
    (nofollow = don't pass PageRank)
  </p>

  <section id="section-a">
    <h2>Section A</h2>
    <p>In-page anchor target. Note the URL changes to <code>#section-a</code>.</p>
    <a href="#section-b">Continue to Section B ↓</a>
  </section>

  <section id="section-b">
    <h2>Section B</h2>
    <p>Another in-page anchor. Back to <a href="#top">top</a>.</p>
  </section>

  <script>
    // Programmatically inspect link attributes
    document.querySelectorAll("a[href]").forEach(a => {
      if (a.target === "_blank" && !a.rel.includes("noopener")) {
        console.warn("Insecure _blank link:", a.href);
      }
    });

    // Smooth scroll for in-page anchors (CSS alternative: scroll-behavior: smooth on html)
    document.querySelectorAll('a[href^="#"]').forEach(a => {
      a.addEventListener("click", e => {
        const target = document.querySelector(a.getAttribute("href"));
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: "smooth" });
          history.pushState(null, "", a.href);  // update URL without jump
        }
      });
    });
  </script>
</body>
</html>
```

**How to run:** save as `anchors.html`, open in a browser. Click the in-page anchors to scroll; watch the URL bar update.

## 6. Walkthrough

- `target="_blank" rel="noopener noreferrer"` — the security combination: `noopener` prevents the new tab from accessing `window.opener`; `noreferrer` suppresses the `Referer` header and also implies `noopener`.
- `href="mailto:hello@example.com?subject=Hello&body=Hi%20there"` — `mailto:` URIs support `subject` and `body` query parameters (URL-encoded). The browser opens the default email client.
- `download="annual-report-2025.pdf"` — the `download` attribute tells the browser to download the file instead of navigating to it. The attribute value sets the suggested filename.
- `rel="nofollow"` — tells Google and other search engines: "I don't vouch for this link." Standard for user-submitted URLs.
- The security audit in JS (`a.target === "_blank" && !a.rel.includes("noopener")`) is a simple lint check. Real security audits use tools like axe-core or eslint-plugin-jsx-a11y.
- Smooth scroll: `scrollIntoView({ behavior: "smooth" })` is more controllable than the CSS `scroll-behavior: smooth` on `html` (which affects all scroll events globally). `history.pushState` updates the URL without the default jump-scroll.

## 7. Gotchas & takeaways

> **`target="_blank"` without `rel="noopener"` is a security hole.** The opened page can execute `window.opener.location = 'evil.com'`, redirecting your user's original tab without their knowledge. Always pair them.

> **In-page anchors require the `id` on the target element.** `<a href="#section-a">` only works if there's an element with `id="section-a"` somewhere on the page. Missing or mistyped IDs lead to silent no-ops.

> **`javascript:void(0)` as `href` is an antipattern.** For clickable things that aren't links, use `<button>` — it's keyboard-accessible, screen-reader-announced as "button", and has no URL hack in the href.

- `target="_blank"` + `rel="noopener noreferrer"` — always together, required for security.
- `rel="nofollow"` — for user content, paid links, or links you don't endorse.
- In-page anchors: `href="#id"` links to `id="id"` on the page.
- `mailto:` and `tel:` launch system apps.
- `download` attribute triggers file save instead of navigation.
- Never use `javascript:void(0)` as href; use `<button>` for click-only actions.
