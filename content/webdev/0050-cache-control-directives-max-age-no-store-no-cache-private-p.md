---
card: webdev
gi: 50
slug: cache-control-directives-max-age-no-store-no-cache-private-p
title: Cache-Control directives (max-age, no-store, no-cache, private, public)
---

## 1. What it is

**Cache-Control** is an HTTP header (both request and response) that instructs caches — browsers, CDNs, reverse proxies — how to store, validate, and serve responses. It replaced the older `Expires` header and is the primary mechanism for controlling HTTP caching.

Key directives:

| Directive | Who it applies to | Meaning |
|---|---|---|
| `max-age=N` | any cache | store and use for N seconds without re-checking |
| `no-store` | any cache | never store this response at all |
| `no-cache` | any cache | store it, but always validate with origin before serving |
| `private` | shared caches only | only the end-user's browser may cache this |
| `public` | any cache | shared caches (CDNs) may cache this |
| `s-maxage=N` | shared caches only | overrides `max-age` for CDNs/proxies |
| `must-revalidate` | any cache | after `max-age` expires, must revalidate (don't serve stale) |
| `immutable` | browser | never revalidate during `max-age` (even on reload) |

## 2. Why & when

Caching is one of the biggest performance levers on the web. Without caching, every page load fetches every asset from the origin server. With caching, a CDN 10ms away serves the same file millions of times.

The directives solve different problems:
- `max-age` and `s-maxage` control *how long* caches serve content without checking.
- `no-store` solves privacy: bank statements, medical records, OTP pages.
- `no-cache` solves staleness without sacrificing privacy: always check, but use cached copy if still valid.
- `private` prevents a shared CDN from caching per-user data (dashboards, shopping carts).
- `public` explicitly opts heavy static assets into shared CDN caching.

You set `Cache-Control` on your server for every response type: HTML (short or no-cache), static assets (long max-age + immutable), API responses (varies), authenticated pages (private or no-store).

## 3. Core concept

Analogy: a vending machine. `max-age=3600` means "this sandwich is good for 1 hour — serve it without checking." `no-cache` means "always phone the factory before dispensing, but keep a copy for comparison." `no-store` means "the machine can't keep any copy at all." `private` means "only the personal fridge in room 401 may store this, not the shared vending machine in the lobby."

The typical web cache hierarchy:

```
Browser cache (private) → CDN / Reverse proxy (shared) → Origin server
```

`private`: only browser cache. `public`: both browser and CDN. `no-store`: none. `no-cache`: either, but must validate.

Common patterns:

```http
# Immutable versioned asset (bundle.a3f2b.js)
Cache-Control: public, max-age=31536000, immutable

# HTML index (always check for updates)
Cache-Control: no-cache

# Authenticated API response (per-user, check often)
Cache-Control: private, max-age=60

# Sensitive data
Cache-Control: no-store
```

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cache-Control directives decision flow: where response gets cached and for how long">
  <defs>
    <marker id="a50" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b50" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="c50" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Response starts here -->
  <rect x="280" y="10" width="120" height="28" rx="6" fill="#6db33f" opacity="0.3" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="29" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HTTP Response</text>

  <!-- no-store branch -->
  <line x1="280" y1="24" x2="80" y2="70" stroke="#f85149" stroke-width="1.5" marker-end="url(#b50)"/>
  <text x="155" y="50" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif" transform="rotate(-20,155,50)">no-store</text>
  <rect x="20" y="70" width="120" height="28" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="80" y="89" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Never cached</text>

  <!-- no-cache branch -->
  <line x1="340" y1="38" x2="340" y2="74" stroke="#d29922" stroke-width="1.5" marker-end="url(#a50)"/>
  <text x="355" y="60" fill="#d29922" font-size="10" font-family="sans-serif">no-cache</text>
  <rect x="270" y="74" width="140" height="28" rx="6" fill="#1c2430" stroke="#d29922" stroke-width="1.5"/>
  <text x="340" y="93" fill="#d29922" font-size="11" text-anchor="middle" font-family="sans-serif">Store, always validate</text>

  <!-- public / private branch -->
  <line x1="400" y1="24" x2="580" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#c50)"/>
  <text x="510" y="44" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" transform="rotate(20,510,44)">max-age</text>

  <!-- private -->
  <rect x="480" y="70" width="110" height="28" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="89" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">+ private</text>
  <rect x="480" y="110" width="110" height="28" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="535" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Browser cache only</text>
  <line x1="535" y1="98" x2="535" y2="108" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a50)"/>

  <!-- public -->
  <rect x="600" y="70" width="70" height="28" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="635" y="89" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">+ public</text>
  <rect x="600" y="110" width="70" height="28" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="635" y="129" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">CDN + browser</text>
  <line x1="635" y1="98" x2="635" y2="108" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a50)"/>

  <!-- max-age timeline -->
  <text x="20" y="175" fill="#e6edf3" font-size="12" font-family="sans-serif" font-weight="bold">max-age lifetime:</text>
  <rect x="20" y="185" width="200" height="22" rx="4" fill="#6db33f" opacity="0.35"/>
  <text x="120" y="200" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Fresh — serve from cache</text>
  <rect x="224" y="185" width="80" height="22" rx="4" fill="#d29922" opacity="0.35"/>
  <text x="264" y="200" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Stale / validate</text>
  <line x1="20" y1="214" x2="304" y2="214" stroke="#8b949e" stroke-width="1"/>
  <text x="20" y="228" fill="#8b949e" font-size="10" font-family="sans-serif">t=0</text>
  <text x="200" y="228" fill="#8b949e" font-size="10" font-family="sans-serif">max-age expires</text>

  <!-- immutable annotation -->
  <rect x="20" y="245" width="200" height="22" rx="4" fill="#6db33f" opacity="0.15" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="120" y="260" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">immutable: never revalidate in period</text>

  <!-- must-revalidate annotation -->
  <rect x="224" y="245" width="80" height="22" rx="4" fill="#d29922" opacity="0.15" stroke="#d29922" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="264" y="260" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">must-revalidate</text>
</svg>

`no-store` prevents any caching; `no-cache` caches but always validates; `max-age` with `private`/`public` controls where and how long fresh responses are served.

## 5. Runnable example

```js
// save as cache-control-demo.js  —  node cache-control-demo.js  (no installs)
const http = require("http");

const responses = {
  "/static/app.js":  { body: "console.log('app')", headers: {
    "Cache-Control": "public, max-age=31536000, immutable",
    "Content-Type": "application/javascript",
  }},
  "/api/dashboard":  { body: '{"user":"alice"}', headers: {
    "Cache-Control": "private, max-age=60",
    "Content-Type": "application/json",
  }},
  "/api/session-otp": { body: "739281", headers: {
    "Cache-Control": "no-store",
    "Content-Type": "text/plain",
  }},
  "/index.html":     { body: "<h1>Home</h1>", headers: {
    "Cache-Control": "no-cache",
    "Content-Type": "text/html",
  }},
};

const server = http.createServer((req, res) => {
  const route = responses[req.url];
  if (!route) {
    res.writeHead(404);
    return res.end("Not found");
  }
  res.writeHead(200, route.headers);
  res.end(route.body);
});

server.listen(3500, async () => {
  // Fetch each route and print its Cache-Control
  const paths = Object.keys(responses);
  let done = 0;
  paths.forEach((path) => {
    http.get(`http://localhost:3500${path}`, (res) => {
      const cc = res.headers["cache-control"];
      const ct = res.headers["content-type"];
      console.log(`${path.padEnd(25)} Cache-Control: ${cc}`);
      res.resume();
      res.on("end", () => { if (++done === paths.length) server.close(); });
    });
  });
});
```

**How to run:** `node cache-control-demo.js` — each route demonstrates a different caching strategy.

Expected output:
```
/static/app.js            Cache-Control: public, max-age=31536000, immutable
/api/dashboard            Cache-Control: private, max-age=60
/api/session-otp          Cache-Control: no-store
/index.html               Cache-Control: no-cache
```

## 6. Walkthrough

- `/static/app.js` — versioned asset (the hash is in the filename). `public` allows CDN caching; `max-age=31536000` (1 year) means browsers serve it from disk without any network request; `immutable` tells the browser "even if you hard-refresh, don't revalidate during this window."
- `/api/dashboard` — user-specific data. `private` prevents CDNs from serving one user's dashboard to another; `max-age=60` lets the browser avoid refetching for 60 seconds.
- `/api/session-otp` — one-time-use sensitive data. `no-store` means it never lands in any cache anywhere, never appears in browser history's cache, never gets stored to disk.
- `/index.html` — always-up-to-date. `no-cache` means the browser caches the HTML but must revalidate with the server before serving it. If the server returns `304 Not Modified`, the browser uses its cached copy without re-downloading.

## 7. Gotchas & takeaways

> `no-cache` does NOT mean "don't cache." It means "cache it, but check with the server every time before serving." If you want nothing cached anywhere, use `no-store`.

> Without `Cache-Control`, browsers apply **heuristic caching**: they guess a reasonable TTL based on `Last-Modified` age (typically 10% of the last-modified delta). This is almost never what you want. Always send explicit `Cache-Control`.

> `max-age` in a *request* is different from a *response*: in a request it means "don't give me a cached copy older than N seconds." Servers rarely inspect request `Cache-Control`, but caches do.

- `public, max-age=31536000, immutable` + a content-hash filename = best-practice for versioned static assets.
- `private, no-cache` on authenticated pages balances security and performance — CDN can't serve it, but browser can validate cheaply.
- `s-maxage` overrides `max-age` only for shared caches (CDNs). Use it when you want CDN TTL different from browser TTL.
- `must-revalidate` prevents serving stale content when a cache loses connectivity — without it some caches will serve stale indefinitely.
