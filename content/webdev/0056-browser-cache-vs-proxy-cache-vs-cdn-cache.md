---
card: webdev
gi: 56
slug: browser-cache-vs-proxy-cache-vs-cdn-cache
title: Browser cache vs proxy cache vs CDN cache
---

## 1. What it is

A **cache** stores a copy of a response so future requests can be served from that copy rather than going all the way back to the origin server. Three distinct layers of caching exist on the path between a user and an origin server:

- **Browser cache** — lives on the user's own device, inside the browser. Private to that one user.
- **Proxy cache** — sits between many users and the internet, typically inside a corporate network or an ISP. Shared across users in that group.
- **CDN cache** — stands for Content Delivery Network. A globally distributed fleet of edge servers (Cloudflare, Fastly, AWS CloudFront, etc.) that caches responses close to users. Shared across all users worldwide who reach the same edge node.

All three follow HTTP's caching rules (`Cache-Control`, `ETag`, `Last-Modified`), but they differ in **location**, **who they serve**, and **who controls them**.

## 2. Why & when

Without caching, every request travels all the way to one origin server. That means:
- Slow responses — latency adds up over long distances.
- High origin load — popular assets hit the same server millions of times.
- High bandwidth cost — the same bytes travel the network repeatedly.

Each cache tier solves a different slice of this:

| Cache | Cuts what? | Controlled by |
|-------|-----------|---------------|
| Browser | Repeat visits by the **same user** | Browser + HTTP headers |
| Proxy | Shared asset fetches inside a **network** | Network admin |
| CDN | Global traffic to the **origin** | Site owner via CDN config |

Use browser caching for personalised or frequently revisited assets. CDN caching for publicly shared static assets (images, JS, CSS). Proxy caching is mostly transparent — you rarely configure it directly.

## 3. Core concept

Think of a popular book. The **origin** is the only printing press. The **CDN** is regional bookstores stocking copies. The **proxy cache** is the shared shelf in your office. Your **browser cache** is the copy on your own desk. The printing press only runs when nobody nearby has a copy yet.

HTTP caching is controlled by the `Cache-Control` response header. Key directives:

- `public` — any intermediate cache (CDN, proxy) may store this.
- `private` — only the browser may store this (e.g. logged-in user's profile page).
- `no-store` — do not cache anywhere.
- `max-age=N` — treat the cached copy as fresh for N seconds.
- `s-maxage=N` — like `max-age` but applies only to shared caches (CDN/proxy), not browsers.

```
Cache-Control: public, max-age=3600, s-maxage=86400
```

This tells the browser to keep the copy for 1 hour, but CDNs can keep it for 24 hours.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three cache tiers between user and origin server">
  <defs>
    <marker id="arr56" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>

  <!-- User/Browser -->
  <rect x="20" y="100" width="120" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="125" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>
  <text x="80" y="143" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">browser cache</text>

  <!-- Proxy -->
  <rect x="190" y="100" width="120" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="250" y="125" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Proxy</text>
  <text x="250" y="143" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">shared (office/ISP)</text>

  <!-- CDN Edge -->
  <rect x="360" y="100" width="120" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="420" y="125" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">CDN Edge</text>
  <text x="420" y="143" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">global shared</text>

  <!-- Origin -->
  <rect x="530" y="100" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="125" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Origin</text>
  <text x="595" y="143" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">server</text>

  <!-- Arrows -->
  <line x1="142" y1="130" x2="188" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr56)"/>
  <line x1="312" y1="130" x2="358" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr56)"/>
  <line x1="482" y1="130" x2="528" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr56)"/>

  <!-- Labels -->
  <text x="80" y="185" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">private</text>
  <text x="250" y="185" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">shared</text>
  <text x="420" y="185" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">shared, global</text>

  <!-- Hit labels -->
  <text x="165" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">cache miss</text>
  <text x="335" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">cache miss</text>
  <text x="505" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">cache miss</text>
</svg>

Request travels left to right, stopping at the first cache that has a fresh copy.

## 5. Runnable example

```js
// server.js — Node.js, no installs. Shows Cache-Control directives in action.
const http = require("http");

http.createServer((req, res) => {
  if (req.url === "/public-asset") {
    // CDN and browser can cache for different durations
    res.setHeader("Cache-Control", "public, max-age=3600, s-maxage=86400");
    res.setHeader("Content-Type", "text/plain");
    res.end("This is a public asset (image/JS/CSS). CDN holds it 24h.");
  } else if (req.url === "/private-data") {
    // Only the browser may cache; no CDN/proxy storage
    res.setHeader("Cache-Control", "private, max-age=300");
    res.setHeader("Content-Type", "text/plain");
    res.end("This is private user data. Only your browser caches it.");
  } else if (req.url === "/no-cache-ever") {
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("Content-Type", "text/plain");
    res.end("This must always be fresh — never cached.");
  } else {
    res.writeHead(404);
    res.end("not found");
  }
}).listen(3000, () => console.log("http://localhost:3000"));
```

**How to run:** `node server.js`, then open `http://localhost:3000/public-asset` in a browser and inspect the Network tab → response headers.

## 6. Walkthrough

- `"public, max-age=3600, s-maxage=86400"` — `public` lets any cache store it; `max-age` tells the browser it's fresh for 1 hour; `s-maxage` overrides that for shared caches (CDN gets 24 hours).
- `"private, max-age=300"` — `private` stops CDNs and proxies from storing the response (it may contain user-specific data). Browser still caches it for 5 minutes.
- `"no-store"` — nothing is stored anywhere. Each request must go to the origin. Use for sensitive data like authentication challenges.
- In the Network tab, hit the endpoint twice. On the second hit you'll see `(from disk cache)` or `304 Not Modified` — that's the browser cache working.

## 7. Gotchas & takeaways

> **`private` doesn't mean encrypted.** It only tells intermediate caches not to store it. The data still travels over the network — use HTTPS to actually protect it in transit.

> **CDN caches can serve stale content for hours if you forget `s-maxage`.** When you deploy a new version, existing CDN copies keep serving the old one until they expire (or you issue a purge).

- Browser cache = private, per-user. Proxy cache = shared, per-network. CDN = shared, global.
- `Cache-Control: public` is required for a CDN to cache the response at all.
- `s-maxage` lets you set CDN TTL independently from browser TTL — useful for long CDN caching with short browser freshness.
- Proxies are largely invisible in modern HTTPS setups (they can't read encrypted traffic), so CDN is the main shared cache you configure.
- Always test caching with hard-refresh disabled — a hard-refresh (`Ctrl+Shift+R`) bypasses the browser cache and inflates your real hit-rate.
