---
card: webdev
gi: 94
slug: rel-attributes-noopener-noreferrer-nofollow
title: rel attributes (noopener, noreferrer, nofollow)
---

## 1. What it is

The `rel` attribute on `<a>` and `<link>` elements declares the **relationship** between the current document and the linked resource. Multiple values can be combined in a single attribute, space-separated:

```html
<a href="https://example.com" target="_blank" rel="noopener noreferrer external">
  Visit Example
</a>
```

The three most important `rel` values for everyday development:

| Value | Effect |
|-------|--------|
| `noopener` | Prevents the new page from accessing `window.opener` |
| `noreferrer` | Suppresses `Referer` header; also implies `noopener` |
| `nofollow` | Tells search crawlers not to follow this link |

Additional useful values:
- `sponsored` — paid/advertising link (Google's alternative to `nofollow` for ads)
- `ugc` — user-generated content (comments, forum posts)
- `external` — signals the link leaves the current site (hint for browsers and AT)
- `alternate` — alternative representation of the page (RSS feed, print version, translated version)
- `canonical` — on `<link>`, tells search engines the canonical URL for this page

## 2. Why & when

`rel` values serve two distinct audiences:

**Security (noopener, noreferrer):** When you open a link in a new tab (`target="_blank"`), the new page can execute `window.opener.location = 'phishing.com'` to silently redirect your user's original tab. This is the **tabnapping attack**. `rel="noopener"` nullifies `window.opener` in the opened page.

**SEO (nofollow, sponsored, ugc):** Search engine crawlers use hyperlinks to discover pages and assign authority ("PageRank"). When you link to a page, you implicitly pass authority to it. `nofollow` tells the crawler: "don't count this link in your authority calculations." Use it for: paid links (required by Google), user-submitted URLs (forums, comments), or links to unverified sources.

## 3. Core concept

Think of `rel` values like **notes stapled to a link** before it's sent. `noopener` says "carry nothing back from the destination." `noreferrer` says "don't tell the destination where you came from." `nofollow` says "don't follow this link for PageRank purposes, just for navigation."

**`noopener` in detail:**

```html
<!-- Vulnerable: opened tab can read/modify window.opener -->
<a href="https://example.com" target="_blank">Unsafe link</a>

<!-- Safe: opened tab's window.opener is null -->
<a href="https://example.com" target="_blank" rel="noopener">Safe link</a>
```

In the malicious page:
```js
// Without noopener — this works and redirects the original tab:
window.opener.location = 'https://phishing.com';

// With noopener — window.opener is null, this throws:
window.opener.location = 'https://phishing.com'; // TypeError: Cannot set property 'location' of null
```

**`noreferrer` in detail:**

Without `noreferrer`, browsers send the `Referer` HTTP header containing the current page URL when a user clicks a link. The destination site sees: "This visitor came from `https://yoursite.com/secret-page`."

`rel="noreferrer"` suppresses the `Referer` header entirely. The destination sees an unattributed direct visit. It also implies `noopener`.

```
Without noreferrer:
  Referer: https://yoursite.com/internal/reports

With noreferrer:
  (no Referer header sent)
```

**`nofollow` in detail:**

```html
<!-- Standard link — passes PageRank authority -->
<a href="https://trusted-partner.com">Our partner</a>

<!-- nofollow — does NOT pass authority -->
<a href="https://user-review.com" rel="nofollow">External review</a>
<a href="https://paid-sponsor.com" rel="sponsored">Sponsor</a>
<a href="#comment-42" rel="ugc">User comment link</a>
```

Google now treats `nofollow`, `sponsored`, and `ugc` as hints (not commands) — it may still crawl or index linked pages. For programmatic ad links, use `sponsored`; for user content, use `ugc`; for generic "don't follow", use `nofollow`.

**`rel` on `<link>` (different context):**

```html
<head>
  <link rel="stylesheet" href="style.css">
  <link rel="icon" href="favicon.ico">
  <link rel="canonical" href="https://example.com/page">
  <link rel="alternate" type="application/rss+xml" href="/feed.xml" title="RSS">
  <link rel="preload" href="hero.jpg" as="image">
</head>
```

`rel` on `<link>` in `<head>` has a completely different set of values that describe how to use the linked resource, not a navigational relationship.

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three panels showing noopener blocking window.opener access, noreferrer suppressing the Referer header, and nofollow instructing crawlers not to follow">
  <!-- noopener -->
  <rect x="10" y="10" width="190" height="230" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="105" y="32" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">noopener</text>
  <rect x="22" y="45" width="166" height="55" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="105" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">yoursite.com</text>
  <text x="105" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(original tab)</text>
  <rect x="22" y="115" width="166" height="55" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="105" y="134" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">example.com (new tab)</text>
  <text x="105" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">window.opener = null</text>
  <line x1="105" y1="100" x2="105" y2="113" stroke="#f85149" stroke-width="1.5"/>
  <text x="105" y="108" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">✗ blocked</text>
  <text x="105" y="200" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">prevents tabnapping</text>
  <text x="105" y="218" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use with target=_blank</text>

  <!-- noreferrer -->
  <rect x="225" y="10" width="190" height="230" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="32" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">noreferrer</text>
  <text x="245" y="58" fill="#e6edf3" font-size="9" font-family="monospace">Without:</text>
  <text x="245" y="74" fill="#8b949e" font-size="8" font-family="monospace">Referer: https://</text>
  <text x="245" y="87" fill="#8b949e" font-size="8" font-family="monospace">yoursite.com/page</text>
  <line x1="320" y1="100" x2="320" y2="113" stroke="#79c0ff" stroke-width="1"/>
  <text x="245" y="125" fill="#e6edf3" font-size="9" font-family="monospace">With noreferrer:</text>
  <text x="245" y="142" fill="#6db33f" font-size="8" font-family="monospace">(no Referer header)</text>
  <text x="245" y="159" fill="#6db33f" font-size="8" font-family="monospace">dest sees direct visit</text>
  <text x="320" y="200" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">hides source URL</text>
  <text x="320" y="218" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">implies noopener too</text>

  <!-- nofollow -->
  <rect x="440" y="10" width="190" height="230" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="32" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">nofollow</text>
  <text x="455" y="58" fill="#8b949e" font-size="9" font-family="sans-serif">Search crawler visits:</text>
  <text x="455" y="75" fill="#e6edf3" font-size="9" font-family="monospace">yoursite.com</text>
  <line x1="535" y1="88" x2="535" y2="108" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="455" y="110" width="166" height="50" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="535" y="130" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">rel="nofollow"</text>
  <text x="535" y="147" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">crawler: skip this link</text>
  <line x1="535" y1="162" x2="535" y2="180" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="535" y="188" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">no PageRank passed</text>
  <text x="535" y="210" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use: ads, UGC, untrusted</text>
</svg>

`noopener` blocks `window.opener` access; `noreferrer` hides the referring URL; `nofollow` instructs search crawlers not to pass authority.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>rel Attributes</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
    a    { color: #6db33f; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; margin-top: 1rem; }
    th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #ddd; }
    th { background: #1c2430; color: #e6edf3; }
    code { background: #f5f5f5; padding: 0 3px; border-radius: 3px; }
  </style>
</head>
<body>

  <h1>rel Attribute Examples</h1>

  <table>
    <tr><th>Link</th><th>rel value</th><th>Purpose</th></tr>
    <tr>
      <td><a href="https://developer.mozilla.org" target="_blank" rel="noopener noreferrer">MDN Docs</a></td>
      <td><code>noopener noreferrer</code></td>
      <td>External link — safe new tab</td>
    </tr>
    <tr>
      <td><a href="https://example-partner.com" rel="noopener external" target="_blank">Partner site</a></td>
      <td><code>noopener external</code></td>
      <td>Partner — external hint for AT</td>
    </tr>
    <tr>
      <td><a href="https://user-review.com" rel="nofollow ugc noopener noreferrer" target="_blank">User review</a></td>
      <td><code>nofollow ugc</code></td>
      <td>User-submitted — no PageRank</td>
    </tr>
    <tr>
      <td><a href="https://paid-link.com" rel="sponsored noopener noreferrer" target="_blank">Sponsored</a></td>
      <td><code>sponsored</code></td>
      <td>Paid link — required by Google</td>
    </tr>
  </table>

  <h2>window.opener demo</h2>
  <p>
    <button onclick="openUnsafe()">Open WITHOUT noopener (unsafe)</button>
    <button onclick="openSafe()">Open WITH noopener (safe)</button>
  </p>
  <p id="status" style="font-family:monospace;color:#6db33f"></p>

  <script>
    function openUnsafe() {
      // The opened window can access window.opener
      const w = window.open("about:blank", "_blank");
      if (w) {
        w.document.write("<p>I can access opener: " + (w.opener ? "YES ⚠️" : "NO ✓") + "</p>");
        document.getElementById("status").textContent = "opener accessible: " + (w.opener ? "YES ⚠️" : "NO");
      }
    }

    function openSafe() {
      // The opened window cannot access window.opener (noopener)
      const w = window.open("about:blank", "_blank", "noopener");
      // window.open() supports "noopener" as a windowFeature string
      // Note: w itself is null when noopener is set (by design)
      document.getElementById("status").textContent = "window ref: " + (w === null ? "null (noopener applied) ✓" : "accessible");
    }

    // Audit: find any _blank links missing noopener
    document.querySelectorAll("a[target='_blank']").forEach(a => {
      if (!a.relList.contains("noopener") && !a.relList.contains("noreferrer")) {
        console.warn("Missing noopener on:", a.href);
      }
    });
  </script>
</body>
</html>
```

**How to run:** save as `rel.html`, open in a browser. Click both buttons and observe the `status` message.

## 6. Walkthrough

- `rel="noopener noreferrer"` combined — `noreferrer` implies `noopener`, so they're redundant together, but many teams specify both for explicit clarity and for older browsers that only support one.
- `window.open("about:blank", "_blank", "noopener")` — the third parameter to `window.open` accepts feature strings. Passing `"noopener"` here is equivalent to `rel="noopener"` on a link. When `noopener` is specified, the return value of `window.open` is `null` — you can't get a reference to the opened window.
- `a.relList.contains("noopener")` — the `relList` property is a `DOMTokenList` (same as `classList`) of space-separated values from the `rel` attribute. `.contains("noopener")` checks membership without string parsing.
- `rel="sponsored"` — Google requires this for paid/ad links. Using `nofollow` for ads is also acceptable, but `sponsored` is more specific and signals intent clearly.
- `rel="ugc"` — for user-generated content (comments, wiki edits, forum posts). Tells crawlers the site owner didn't write or endorse the link.
- The audit loop: check every `[target="_blank"]` link for missing `noopener` or `noreferrer`. This pattern is used in accessibility/security linters.

## 7. Gotchas & takeaways

> **`noreferrer` implies `noopener` — you only need both for older browser compatibility.** On any browser released after 2020, `noreferrer` alone is enough to null `window.opener`. Writing both is belt-and-suspenders for coverage.

> **Modern Chrome (88+) applies `noopener` to all `target="_blank"` links by default.** But Safari and older browsers don't. Always write `rel="noopener noreferrer"` explicitly — don't depend on browser defaults.

> **`nofollow` is a hint, not a command.** Google treats it as a hint and may still crawl linked pages. It does reliably prevent PageRank passing, but doesn't make the link invisible to crawlers.

- `noopener` = null out `window.opener` in the new tab; required for `target="_blank"`.
- `noreferrer` = suppress `Referer` header + implies `noopener`.
- `nofollow` = no PageRank pass; use for untrusted, user-content, or unendorsed links.
- `sponsored` = paid/ad links; `ugc` = user-generated content links.
- `relList.contains(value)` = check programmatically without string parsing.
- Combine values in one attribute: `rel="noopener noreferrer external nofollow"`.
