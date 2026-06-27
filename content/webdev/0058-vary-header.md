---
card: webdev
gi: 58
slug: vary-header
title: Vary header
---

## 1. What it is

The **`Vary` response header** tells caches which request headers can change the response content. It answers: "what information did the server look at before deciding what to send back?"

```
Vary: Accept-Encoding
Vary: Accept-Language, Accept-Encoding
```

When a cache stores a response with `Vary: Accept-Encoding`, it stores it separately for each `Accept-Encoding` value a client might send. A gzip-compressed response and an uncompressed response for the same URL are two different cache entries.

Without `Vary`, a cache would hand the same gzip-encoded bytes to a client that can't decode gzip — breaking the response.

## 2. Why & when

Servers often serve different content from the same URL depending on request context:

- **Content negotiation** — gzip vs no compression (`Accept-Encoding`), English vs French (`Accept-Language`), JSON vs HTML (`Accept`).
- **Device type** — responsive images served based on a `Viewport-Width` hint.
- **Authentication state** — some (not recommended) setups vary by `Cookie` or `Authorization`.

Without `Vary`, a shared cache (CDN/proxy) could:
1. Receive request from a gzip-capable client. Store gzip response.
2. Receive request from a gzip-incapable client. Return gzip bytes from cache. **Client breaks.**

`Vary` tells the cache: "these headers must match to use this cached copy."

## 3. Core concept

Analogy: a vending machine that remembers your language preference. If you press "Coke" in English it shows "Enjoy your Coke." If someone in French does the same, it shows "Profitez de votre Coca." The machine caches both phrases under the key `{button: Coke, language: en}` and `{button: Coke, language: fr}` — the cache key includes the language dimension.

HTTP caches work the same way. The cache key is normally just the URL. `Vary` adds more dimensions:

```
Cache key WITHOUT Vary:   GET /page
Cache key WITH Vary: Accept-Encoding:   GET /page + Accept-Encoding value
```

Practical effect:

| Request | Cached key | Stored separately? |
|---------|-----------|-------------------|
| `GET /data` + `Accept-Encoding: gzip` | `/data` + gzip | entry A |
| `GET /data` + `Accept-Encoding: identity` | `/data` + identity | entry B |

`Vary: *` means every single request is unique — effectively disables caching. Avoid unless you really need it.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Vary header causes CDN to store separate cache entries per Accept-Encoding value">
  <defs>
    <marker id="arr58" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr58b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Client A -->
  <rect x="20" y="60" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="81" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client A</text>
  <text x="85" y="97" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Accept-Encoding: gzip</text>

  <!-- Client B -->
  <rect x="20" y="140" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="161" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client B</text>
  <text x="85" y="177" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Accept-Encoding: identity</text>

  <!-- CDN Cache -->
  <rect x="250" y="50" width="180" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="75" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">CDN Cache</text>
  <rect x="265" y="85" width="150" height="35" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="340" y="103" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">/data + gzip → bytes A</text>
  <rect x="265" y="130" width="150" height="35" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="340" y="148" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">/data + identity → bytes B</text>
  <text x="340" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Vary: Accept-Encoding</text>

  <!-- Arrows -->
  <line x1="152" y1="85" x2="248" y2="103" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr58)"/>
  <line x1="152" y1="165" x2="248" y2="148" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr58b)"/>
</svg>

Same URL, two separate cache entries — one per unique `Accept-Encoding` value seen.

## 5. Runnable example

```js
// server.js — Node.js, no installs.
const http = require("http");
const zlib = require("zlib");

http.createServer((req, res) => {
  const body = "Hello! This response may be gzip-compressed.";
  const acceptEncoding = req.headers["accept-encoding"] || "";

  // Tell the cache: different Accept-Encoding = different cached response
  res.setHeader("Vary", "Accept-Encoding");
  res.setHeader("Cache-Control", "public, max-age=60");

  if (acceptEncoding.includes("gzip")) {
    res.setHeader("Content-Encoding", "gzip");
    res.setHeader("Content-Type", "text/plain");
    zlib.gzip(body, (err, compressed) => {
      res.writeHead(200);
      res.end(compressed);
      console.log("Served: gzip (" + compressed.length + " bytes)");
    });
  } else {
    res.setHeader("Content-Type", "text/plain");
    res.writeHead(200);
    res.end(body);
    console.log("Served: plain text (" + body.length + " bytes)");
  }
}).listen(3000, () => {
  const http2 = require("http");

  // Simulate gzip-capable client
  http2.get({ port: 3000, headers: { "accept-encoding": "gzip" } }, (r) => {
    console.log("Client A encoding:", r.headers["content-encoding"]);
    r.resume();
  });

  // Simulate plain client
  http2.get({ port: 3000 }, (r) => {
    let b = "";
    r.on("data", d => b += d);
    r.on("end", () => {
      console.log("Client B body:", b);
      process.exit(0);
    });
  });
});
```

**How to run:** `node server.js`. Watch two different responses from the same URL.

## 6. Walkthrough

- `res.setHeader("Vary", "Accept-Encoding")` is the crucial line — it tells any cache that the response depends on the `Accept-Encoding` request header.
- The server then actually checks `req.headers["accept-encoding"]` and branches: gzip compressed bytes for capable clients, plain text otherwise.
- `Content-Encoding: gzip` tells the client how to decode the body. Without this, a gzip-unaware client would see garbled bytes.
- Without `Vary`, a CDN receiving the gzip response first would serve those compressed bytes to the next client regardless of that client's capabilities — corrupting the response.
- `Cache-Control: public, max-age=60` allows CDN caching. The `Vary` ensures separate storage per encoding.

## 7. Gotchas & takeaways

> **`Vary: Cookie` or `Vary: Authorization` effectively destroys CDN cache hit rates.** Every user has a unique cookie, so the CDN can never reuse a stored response. If you vary by auth state, serve public and private content from different URLs instead.

> **`Vary: *` disables caching entirely for shared caches.** Only use it as a last resort — it tells every proxy/CDN that no two requests are equivalent.

- `Vary` adds dimensions to the cache key — each unique combination of varied header values gets its own stored response.
- Most production servers emit `Vary: Accept-Encoding` automatically (Nginx, Express compression middleware) — verify with DevTools.
- `Vary: Accept-Language` is useful but doubles (or more) your CDN storage per URL.
- Browsers also respect `Vary` for their own local cache, not just CDNs.
- Check for unnecessary `Vary` values; each one multiplies cache storage and reduces hit rates.
