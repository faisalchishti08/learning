---
card: webdev
gi: 65
slug: cache-storage-api
title: Cache Storage API
---

## 1. What it is

The **Cache Storage API** is a browser API that lets JavaScript (usually a Service Worker) store and retrieve `Request`/`Response` pairs — full HTTP responses, including headers and body. Unlike `localStorage` (strings only) or IndexedDB (arbitrary objects), Cache Storage speaks natively in HTTP terms.

```js
// Store a response
const cache = await caches.open("my-cache-v1");
await cache.put("/api/data", new Response(JSON.stringify({ hello: "world" })));

// Retrieve it
const response = await cache.match("/api/data");
const data = await response.json();
```

It's the foundation of Progressive Web Apps (PWAs) and offline-first experiences.

## 2. Why & when

The browser's HTTP cache (controlled by `Cache-Control` headers) stores responses automatically but gives the developer no programmatic control over what to store or when to serve from cache vs the network.

Cache Storage changes that: your JavaScript code decides exactly:
- **What to cache** — specific URLs, API responses, assets.
- **When to cache** — on install, on first fetch, on user action.
- **What to serve** — cache-first, network-first, or stale-while-revalidate strategies.
- **When to evict** — your code clears old caches explicitly.

Use Cache Storage when building:
- Offline-capable pages (PWAs).
- Apps that need to work on flaky connections.
- Apps where performance is critical and you want fine-grained control over asset caching.

It's almost always used together with a **Service Worker**, which intercepts network requests and decides whether to respond from Cache Storage or the real network.

## 3. Core concept

Analogy: Cache Storage is a **programmable vending machine**. The ordinary HTTP cache is automatic vending — it decides what to stock based on `Cache-Control` headers. Cache Storage hands you the keys: you decide what goes in, what comes out, and what gets thrown away.

Key methods on a `Cache` object:

| Method | What it does |
|--------|-------------|
| `cache.put(request, response)` | Store a response for a request |
| `cache.add(url)` | Fetch the URL and store the response |
| `cache.addAll([urls])` | Fetch and store multiple URLs at once |
| `cache.match(request)` | Retrieve cached response (or `undefined`) |
| `cache.delete(request)` | Remove one entry |
| `cache.keys()` | List all cached requests |

`caches` (plural) is the global object that manages named caches:
```js
caches.open("v1")       // open or create a named cache
caches.has("v1")        // check if named cache exists
caches.delete("v1")     // delete entire named cache
caches.keys()           // list all named caches
```

Common caching strategy — **cache-first with network fallback**:
```js
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(cached =>
      cached || fetch(event.request)
    )
  );
});
```

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service Worker intercepts fetch, checks Cache Storage, falls back to network">
  <defs>
    <marker id="arr65a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr65b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="arr65c" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>

  <!-- Page -->
  <rect x="20" y="85" width="100" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Page</text>

  <!-- Service Worker -->
  <rect x="185" y="70" width="130" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="250" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Service</text>
  <text x="250" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Worker</text>
  <text x="250" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">intercepts fetch</text>

  <!-- Cache Storage -->
  <rect x="390" y="35" width="130" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="455" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Cache</text>
  <text x="455" y="76" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Storage</text>
  <text x="455" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">HIT → serve direct</text>

  <!-- Network -->
  <rect x="390" y="130" width="130" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="455" y="160" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Network</text>
  <text x="455" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">MISS → fetch</text>

  <!-- Arrows -->
  <line x1="122" y1="110" x2="183" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr65a)"/>
  <text x="153" y="103" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">fetch</text>

  <line x1="317" y1="95" x2="388" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr65b)"/>
  <text x="350" y="75" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">check cache</text>

  <line x1="317" y1="115" x2="388" y2="155" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr65c)"/>
  <text x="350" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fallback</text>
</svg>

Service Worker intercepts every fetch, checks Cache Storage first, falls back to the network on a miss.

## 5. Runnable example

```html
<!-- cache-storage-demo.html — open in Chrome/Firefox (needs service worker support) -->
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Cache Storage demo</title></head>
<body>
<h2>Cache Storage API demo</h2>
<p>Open DevTools → Application → Cache Storage to inspect entries.</p>
<button onclick="fillCache()">Fill cache</button>
<button onclick="readCache()">Read from cache</button>
<button onclick="clearCache()">Clear cache</button>
<pre id="out" style="background:#1c2430;color:#e6edf3;padding:1em;margin-top:1em"></pre>

<script>
const CACHE = "demo-v1";
function log(m) { document.getElementById("out").textContent += m + "\n"; }
function clearLog() { document.getElementById("out").textContent = ""; }

async function fillCache() {
  clearLog();
  // Cache Storage doesn't need a service worker to write from page JS
  const cache = await caches.open(CACHE);
  // Store a synthetic response (no real network request)
  await cache.put("/api/hello",
    new Response(JSON.stringify({ message: "Hello from cache!" }), {
      headers: { "Content-Type": "application/json" }
    })
  );
  // Fetch and cache a real public resource
  await cache.add("https://httpbin.org/get");
  const keys = await cache.keys();
  log("Cached " + keys.length + " entries:");
  keys.forEach(r => log("  " + r.url));
}

async function readCache() {
  clearLog();
  const cache = await caches.open(CACHE);
  const resp = await cache.match("/api/hello");
  if (resp) {
    const data = await resp.json();
    log("Cache hit /api/hello: " + JSON.stringify(data));
  } else {
    log("Cache miss — fill first.");
  }
}

async function clearCache() {
  clearLog();
  await caches.delete(CACHE);
  log("Cache '" + CACHE + "' deleted.");
}
</script>
</body>
</html>
```

**How to run:** save as `cache-storage-demo.html`, open in a browser (Chrome/Firefox). Click "Fill cache" — it stores a synthetic response and fetches a real URL. Inspect in DevTools → Application → Cache Storage.

## 6. Walkthrough

- `caches.open(CACHE)` opens (or creates) a named cache bucket called `"demo-v1"`. Named caches let you version your cache: swap `"demo-v1"` for `"demo-v2"` during an app update and delete the old one.
- `cache.put("/api/hello", new Response(...))` stores a hand-crafted response for the key `/api/hello`. No network request is made — useful for synthetic offline responses.
- `cache.add("https://httpbin.org/get")` issues a real `fetch`, then stores the response. It's shorthand for `fetch(url).then(r => cache.put(url, r))`.
- `cache.keys()` returns an array of `Request` objects representing everything stored. `r.url` gives the URL string.
- `caches.delete(CACHE)` wipes the entire named cache — typical during a PWA update when old caches should be evicted.
- In DevTools → Application → Cache Storage, you can see every stored entry and inspect the response headers and body.

## 7. Gotchas & takeaways

> **Cache Storage is origin-scoped**, not tab-scoped. All Service Workers on the same origin share the same cache storage — naming caches (`"v1"`, `"v2"`) and deleting old versions during Service Worker `activate` is critical to avoid serving stale assets forever.

> **`cache.put` stores responses by their URL as the key.** If you put the same URL twice, the second call overwrites the first. Beware of accidentally caching error responses (404, 500) — always check `response.ok` before caching.

- Cache Storage is ideal for static assets (JS, CSS, images) and offline fallback pages — pair with Service Worker for full offline capability.
- Browsers enforce storage quotas (shared with IndexedDB). Use `navigator.storage.estimate()` to check remaining quota.
- Cache Storage is not a substitute for the HTTP cache — both can exist simultaneously; Cache Storage gives programmatic control, HTTP cache is automatic.
- Versioning strategy: install new cache (`"v2"`), serve from it, then in `activate` delete `"v1"` so old clients on the old Service Worker still have their cache.
- Test with DevTools → Application → Service Workers → "Offline" checkbox to simulate offline mode.
