---
card: webdev
gi: 57
slug: cache-busting-content-hashing
title: Cache busting & content hashing
---

## 1. What it is

**Cache busting** is the technique of forcing browsers and CDNs to fetch a new version of a file instead of using a stale cached copy.

The most reliable form of cache busting is **content hashing**: include a fingerprint of the file's contents in its URL. When the file changes, the hash changes, the URL changes, and caches treat it as a brand-new resource — fetching it fresh automatically.

Example:
```
/assets/app.a3f9b7c2.js   ← hash changes every time the file changes
```

A matching HTML file references that hashed URL, so browsers always load the right version. Meanwhile you can set a very long `Cache-Control: max-age` (even a year) on the asset, because the URL itself is the cache key.

## 2. Why & when

Without cache busting you face a dilemma:
- Short `max-age` → good freshness, but users re-download assets on every visit even if nothing changed.
- Long `max-age` → fast repeat visits, but after a deploy users may run old JS with a new backend.

Content hashing escapes the dilemma entirely:

| Situation | Old approach | Content hashing |
|-----------|-------------|-----------------|
| File unchanged | Must re-validate anyway | Served from cache — URL is the same |
| File changed | Need short TTL to catch update | New URL → automatic fresh fetch |
| Deploy rollout | Risk of mixed old/new versions | Each version has its own URL |

Use content hashing for any long-lived static asset: JavaScript bundles, CSS files, fonts, images. Modern bundlers (Webpack, Vite, Parcel, esbuild) do this automatically.

## 3. Core concept

Analogy: imagine every edition of a newspaper had a unique ISBN. Libraries keep a copy as long as it's useful. When a new edition comes out, it has a different ISBN — the library knows to fetch a new copy. Old ISBNs stay on the shelf for anyone who still needs them.

Three steps in practice:

1. **Hash the file.** The build tool reads the file, computes a hash (MD5 or SHA256 of the content), and injects it into the filename: `app.js` → `app.a3f9b7c2.js`.
2. **Reference the hashed URL in HTML.** The HTML file itself is served with `Cache-Control: no-cache` (or `no-store`) so the browser always re-validates it. This way HTML always reflects the latest asset filenames.
3. **Set a long TTL on hashed assets.** Because the URL encodes the version, `Cache-Control: public, max-age=31536000, immutable` is safe — "immutable" tells the browser it never needs to even re-validate.

```
HTML:   Cache-Control: no-cache           → always fresh, small file
Assets: Cache-Control: public, max-age=31536000, immutable  → cache forever
```

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Content hashing flow: build tool produces hashed filename, HTML references it, browser caches indefinitely">
  <defs>
    <marker id="arr57" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Build step -->
  <rect x="20" y="80" width="160" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="108" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Build Tool</text>
  <text x="100" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">app.js → hash →</text>
  <text x="100" y="142" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">app.a3f9b7c2.js</text>

  <!-- Server -->
  <rect x="250" y="60" width="160" height="120" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="88" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>
  <text x="330" y="108" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">index.html</text>
  <text x="330" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Cache-Control: no-cache</text>
  <text x="330" y="144" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">app.a3f9b7c2.js</text>
  <text x="330" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">max-age=31536000</text>

  <!-- Browser -->
  <rect x="490" y="80" width="160" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="108" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>
  <text x="570" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">fetches hashed URL</text>
  <text x="570" y="142" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">caches for 1 year</text>

  <!-- Arrows -->
  <line x1="182" y1="120" x2="248" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr57)"/>
  <line x1="412" y1="120" x2="488" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr57)"/>
</svg>

HTML fetches fresh every time; hashed asset URL is immutable — cached forever or until the hash changes.

## 5. Runnable example

```html
<!-- index.html — open in any browser, no server needed -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Cache busting demo</title>
</head>
<body>
<h2>Cache busting demo</h2>
<pre id="out"></pre>
<button onclick="bust()">Simulate content hash</button>

<script>
// Simulate what a build tool does: hash file content → new URL
async function hashContent(text) {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.slice(0, 4).map(b => b.toString(16).padStart(2, "0")).join("");
}

async function bust() {
  const content_v1 = 'console.log("app v1");';
  const content_v2 = 'console.log("app v2 — new feature added");';

  const hash1 = await hashContent(content_v1);
  const hash2 = await hashContent(content_v2);

  document.getElementById("out").textContent =
    `v1 content → app.${hash1}.js\nv2 content → app.${hash2}.js\n` +
    `\nDifferent content = different hash = different URL.\n` +
    `Browsers fetch the new URL fresh; old URL stays cached.\n`;
}
</script>
</body>
</html>
```

**How to run:** save as `index.html`, open in a browser (double-click or `file://` URL). Click the button to see hashes generated from content.

## 6. Walkthrough

- `crypto.subtle.digest("SHA-256", data)` uses the browser's built-in Web Crypto API to hash the content — same idea build tools use, just shown in-browser for clarity.
- `hashArray.slice(0, 4)` takes only the first 4 bytes (8 hex chars) of the 32-byte SHA-256. Build tools often use 8–10 chars — enough uniqueness without huge filenames.
- Changing even one character in `content_v2` produces a completely different hash. That's the content-addressable property: identical content → identical URL; any change → new URL.
- The generated filenames `app.XXXX.js` illustrate exactly what Webpack/Vite output — the browser has no prior cache entry for the new filename and must fetch it.

## 7. Gotchas & takeaways

> **Don't use query strings for cache busting** (`app.js?v=2`). Some proxies and CDNs ignore query strings when caching, so the old file can still be served. Filename hashing is reliable; query strings are not.

> **HTML must be served without long caching.** If you cache `index.html` for a year and deploy a new asset hash, users load the old HTML, which references the old (possibly deleted) asset URL — broken page.

- Content hash → URL is the cache key → browsers auto-evict old versions without purging.
- Set `Cache-Control: public, max-age=31536000, immutable` on hashed assets — safe because the URL can never serve stale content.
- Set `Cache-Control: no-cache` on `index.html` — forces re-validation on every visit, which is cheap because it's tiny.
- Modern bundlers (Vite, Webpack, Parcel) enable content hashing with one config option (`output.filename: "[name].[contenthash].js"`).
- Old hashed files remain on the CDN/server for users mid-session — no 404s during a deploy rollout.
