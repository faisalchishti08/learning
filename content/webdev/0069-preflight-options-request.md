---
card: webdev
gi: 69
slug: preflight-options-request
title: Preflight OPTIONS request
---

## 1. What it is

A **preflight request** is an automatic `HTTP OPTIONS` request that the browser sends before a cross-origin request that would be preflighted. It asks the server: "I'm about to send a `DELETE` with an `Authorization` header from origin `https://app.example.com` — are you okay with that?"

The server's `Access-Control-Allow-*` response headers are the answer. If the server says yes, the browser sends the real request. If the server says nothing useful (or returns an error), the browser blocks the real request and reports a CORS error to JavaScript — even though the real request was never sent.

The preflight is entirely invisible to your JavaScript code. You cannot intercept or cancel it; the browser handles it automatically.

## 2. Why & when

The preflight exists for **backward compatibility with naive servers**. A server written before CORS existed never expected cross-origin `DELETE` or `PUT` requests, and might perform destructive actions on receipt. The preflight lets the browser confirm the server is CORS-aware before firing the potentially side-effecting real request.

`OPTIONS` was chosen because it is the HTTP method defined for "describe what this endpoint can do" — no side effects, just metadata. A server that wasn't designed for cross-origin requests will typically return `405 Method Not Allowed` or ignore the `OPTIONS` method entirely, signalling to the browser: don't proceed.

You care about preflights when:
- Writing the server code for an API that accepts cross-origin calls.
- Debugging CORS errors — the preflight failing is the most common root cause.
- Optimising performance — each preflighted endpoint costs an extra round-trip per browser session (until the `Access-Control-Max-Age` cache kicks in).

## 3. Core concept

Think of the preflight as a **customs declaration form at the airport**. Before you can carry unusual items cross-border, you must file a form listing what you're bringing. The officer (browser) checks whether the destination country (server) permits those items (`Access-Control-Allow-*`). Only after clearance do you actually cross the border (real request fires).

**Preflight request anatomy:**

```
OPTIONS /api/users/42 HTTP/1.1
Host: api.example.com
Origin: https://app.example.com
Access-Control-Request-Method: DELETE
Access-Control-Request-Headers: Authorization, Content-Type
```

The two `Access-Control-Request-*` headers describe the real request the browser intends to send.

**Expected preflight response:**

```
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400
```

Key details:
- Status can be `200` or `204` — the browser ignores the body entirely; only headers matter.
- `Access-Control-Allow-Origin` must match the request's `Origin` (or be `*` for non-credentialed requests).
- `Access-Control-Allow-Methods` must include the method from `Access-Control-Request-Method`.
- `Access-Control-Allow-Headers` must include every header listed in `Access-Control-Request-Headers`.
- `Access-Control-Max-Age` tells the browser how many seconds to cache this preflight result — until it expires, no second `OPTIONS` is sent for the same method/headers combo at the same URL.

If any required header is missing or the origin is not allowed, the browser raises a CORS error and cancels the real request.

## 4. Diagram

<svg viewBox="0 0 680 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Preflight OPTIONS flow with request and response headers annotated">
  <defs>
    <marker id="arr69b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="arr69g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr69r" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Browser box -->
  <rect x="10" y="120" width="130" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="146" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>
  <text x="75" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JS: fetch DELETE</text>

  <!-- Server box -->
  <rect x="540" y="120" width="130" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="605" y="146" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>
  <text x="605" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">api.example.com</text>

  <!-- Preflight arrow -->
  <line x1="142" y1="140" x2="538" y2="140" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr69b)" stroke-dasharray="5,3"/>

  <!-- Preflight request label box -->
  <rect x="175" y="50" width="330" height="80" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="340" y="70" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">OPTIONS /api/users/42</text>
  <text x="340" y="86" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Origin: https://app.example.com</text>
  <text x="340" y="100" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Access-Control-Request-Method: DELETE</text>
  <text x="340" y="114" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Access-Control-Request-Headers: Authorization</text>
  <line x1="340" y1="132" x2="340" y2="138" stroke="#79c0ff" stroke-width="1" stroke-dasharray="2,2"/>

  <!-- Preflight response arrow -->
  <line x1="538" y1="170" x2="142" y2="170" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr69g)" stroke-dasharray="5,3"/>

  <!-- Preflight response label box -->
  <rect x="175" y="180" width="330" height="95" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="340" y="200" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">HTTP/1.1 204 No Content</text>
  <text x="340" y="216" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Access-Control-Allow-Origin: https://app.example.com</text>
  <text x="340" y="230" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Access-Control-Allow-Methods: DELETE, GET, POST</text>
  <text x="340" y="244" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Access-Control-Allow-Headers: Authorization</text>
  <text x="340" y="258" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">Access-Control-Max-Age: 86400</text>
  <line x1="340" y1="170" x2="340" y2="178" stroke="#6db33f" stroke-width="1" stroke-dasharray="2,2"/>

  <!-- Real request arrow -->
  <line x1="142" y1="188" x2="538" y2="188" stroke="#6db33f" stroke-width="2" marker-end="url(#arr69g)"/>
  <text x="340" y="310" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">→ Real DELETE fires (browser approved)</text>
  <line x1="340" y1="280" x2="340" y2="305" stroke="#6db33f" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="142" y1="275" x2="538" y2="275" stroke="#6db33f" stroke-width="2" marker-end="url(#arr69g)"/>
</svg>

The dashed arrows are the preflight handshake; the solid arrows are the real request that follows only after approval.

## 5. Runnable example

```js
// options-server.js — Node.js, no installs.
// Shows a server correctly handling OPTIONS preflight, then the real DELETE.
const http = require("http");

const CORS_ORIGIN = "https://app.example.com";

http.createServer((req, res) => {
  const origin = req.headers.origin || "";

  if (req.method === "OPTIONS") {
    // ---- PREFLIGHT HANDLER ----
    const requestedMethod = req.headers["access-control-request-method"];
    const requestedHeaders = req.headers["access-control-request-headers"];

    console.log(`Preflight: method=${requestedMethod}  headers=${requestedHeaders}`);

    if (origin !== CORS_ORIGIN) {
      // Origin not allowed — respond with no CORS headers; browser blocks the real request
      res.writeHead(403);
      res.end("Forbidden");
      return;
    }

    res.writeHead(204, {
      "Access-Control-Allow-Origin": CORS_ORIGIN,
      "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Authorization, Content-Type",
      "Access-Control-Max-Age": "86400",  // cache for 24 hours
    });
    res.end();
    return;
  }

  // ---- ACTUAL REQUEST HANDLER ----
  console.log(`Real request: ${req.method} ${req.url}`);
  res.writeHead(200, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": CORS_ORIGIN,  // required on the real response too
  });
  res.end(JSON.stringify({ deleted: true }));

}).listen(8000, () => {
  console.log("Server on http://localhost:8000");
  console.log("Run in browser console (from https://app.example.com):");
  console.log('  fetch("http://localhost:8000/api/item/1", {');
  console.log('    method: "DELETE",');
  console.log('    headers: { Authorization: "Bearer token" }');
  console.log('  })');
});
```

**How to run:** `node options-server.js`. Simulate the preflight manually with curl:
```bash
curl -i -X OPTIONS http://localhost:8000/api/item/1 \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: DELETE" \
  -H "Access-Control-Request-Headers: Authorization"
```

## 6. Walkthrough

- `req.method === "OPTIONS"` — the preflight always arrives as `OPTIONS`. This branch handles only the negotiation; no data is read or written.
- `access-control-request-method` and `access-control-request-headers` — Node lowercases all header names. These describe what the real request wants. The server uses them to decide what to allow.
- `origin !== CORS_ORIGIN` — if the origin isn't on the allowlist, the server returns `403` with no CORS headers. The browser sees no `Access-Control-Allow-Origin` and blocks the real request.
- `res.writeHead(204, { ... })` — `204 No Content` is conventional for preflight responses. The body is ignored. Only the headers matter.
- `Access-Control-Max-Age: 86400` — browsers cache this preflight result for up to 86 400 seconds (24 hours). During that window, the same origin+method+headers combo at the same URL skips the `OPTIONS` round-trip entirely. Chrome caps at 7 200 s (2 hours); Firefox allows up to 86 400 s.
- The real `DELETE` handler still needs `Access-Control-Allow-Origin` on its own response. The preflight approval doesn't carry over to the actual response headers.

## 7. Gotchas & takeaways

> **The browser caches preflight results per URL.** If you change `Access-Control-Max-Age` or add a new method, browsers may still use the old cached preflight for up to the old max-age. Hard-refreshing (Ctrl+Shift+R / Cmd+Shift+R) bypasses the cache.

> **The actual response also needs `Access-Control-Allow-Origin`.** Passing the preflight is not enough — if the real `200 OK` is missing the header, the browser still blocks JavaScript from reading the body.

> **Server frameworks have OPTIONS quirks.** Express routers don't match `OPTIONS` unless you explicitly define a route or use the `cors` middleware. Forgetting this means preflights hit a `404`, which looks like a CORS error.

- Every preflighted endpoint must handle `OPTIONS` and return CORS headers.
- `204 No Content` is the correct status for a preflight response — keep the body empty.
- `Access-Control-Max-Age` reduces preflight overhead; missing it means a round-trip on every fetch.
- Both the preflight response and the real response need `Access-Control-Allow-Origin`.
- Preflight failures look like CORS errors in DevTools — check the OPTIONS request first when debugging.
- `curl` ignores preflights — simulate them explicitly with `-X OPTIONS` and the `Access-Control-Request-*` headers.
