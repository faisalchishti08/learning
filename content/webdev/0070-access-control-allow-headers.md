---
card: webdev
gi: 70
slug: access-control-allow-headers
title: Access-Control-Allow-* headers
---

## 1. What it is

The **`Access-Control-Allow-*` family** is the set of HTTP response headers a server uses to grant cross-origin permissions. There are six of them, each controlling a different dimension of what cross-origin JavaScript is permitted to do:

| Header | Direction | Controls |
|--------|-----------|---------|
| `Access-Control-Allow-Origin` | Response | Which origins may read this response |
| `Access-Control-Allow-Methods` | Preflight response | Which HTTP methods are allowed |
| `Access-Control-Allow-Headers` | Preflight response | Which request headers JS may set |
| `Access-Control-Allow-Credentials` | Response | Whether cookies/auth may be sent |
| `Access-Control-Max-Age` | Preflight response | How long to cache the preflight result |
| `Access-Control-Expose-Headers` | Response | Which response headers JS may read |

The server sends these headers; the browser enforces them. Missing even one required header for a given scenario will cause a CORS block.

## 2. Why & when

Without these headers, cross-origin JavaScript can make requests but can't read the responses — the Same-Origin Policy blocks access. Each header exists to unlock a specific capability:

- **Allow-Origin** — the foundational unlock. Without it, nothing else matters.
- **Allow-Methods** — needed for any non-`GET`/`POST`/`HEAD` verb in a preflighted request.
- **Allow-Headers** — needed for any non-safelisted header (e.g. `Authorization`, `Content-Type: application/json`, custom headers).
- **Allow-Credentials** — needed when the frontend sends cookies or uses `credentials: "include"`.
- **Max-Age** — a performance optimisation; without it, every preflighted call pays the extra `OPTIONS` round-trip.
- **Expose-Headers** — needed when JS needs to read response headers beyond the small default safelisted set (`Cache-Control`, `Content-Language`, `Content-Type`, `Expires`, `Last-Modified`, `Pragma`).

## 3. Core concept

Think of a hotel with different access cards. `Allow-Origin` is the front door — only guests from approved rooms get in. `Allow-Methods` and `Allow-Headers` are the floor permissions — a guest can only use the elevator buttons their card allows. `Allow-Credentials` is the minibar key — most guests don't get it. `Expose-Headers` is the hotel's guest ledger — only certain pages are open for reading. `Max-Age` is the front desk stamping your card so you don't have to check in again for 24 hours.

**`Access-Control-Allow-Origin`**

```http
Access-Control-Allow-Origin: https://app.example.com
```
Or open to everyone (only for fully public, unauthenticated resources):
```http
Access-Control-Allow-Origin: *
```
`*` cannot be used when `Allow-Credentials: true`. In that case, echo the specific origin from the request `Origin` header.

**`Access-Control-Allow-Methods`**

```http
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
```
Only matters in preflight responses. Lists all HTTP methods permitted cross-origin. The preflight's `Access-Control-Request-Method` must be in this list.

**`Access-Control-Allow-Headers`**

```http
Access-Control-Allow-Headers: Authorization, Content-Type, X-Request-ID
```
Only in preflight responses. Every header listed in `Access-Control-Request-Headers` must appear here. Comparison is case-insensitive.

**`Access-Control-Allow-Credentials`**

```http
Access-Control-Allow-Credentials: true
```
Must be exactly the string `"true"`. When present, the browser allows cookies and HTTP authentication headers to be included. Requires the origin to be explicitly named (not `*`).

**`Access-Control-Max-Age`**

```http
Access-Control-Max-Age: 86400
```
Seconds to cache the preflight result. Chrome's maximum is 7 200 (2 hours); Firefox allows up to 86 400 (24 hours). Without this header, the browser defaults to 5 seconds.

**`Access-Control-Expose-Headers`**

```http
Access-Control-Expose-Headers: X-Total-Count, X-Request-ID
```
Response header, not preflight. Lists non-standard response headers that JS may access via `response.headers.get(...)`. Without it, custom headers are invisible to JavaScript even if the response reached the browser.

## 4. Diagram

<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Map of Access-Control-Allow-* headers showing which appear on preflight vs real response">
  <defs>
    <marker id="arr70b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="arr70g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Browser -->
  <rect x="10" y="120" width="110" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="65" y="152" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>

  <!-- Server -->
  <rect x="580" y="120" width="110" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="635" y="152" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>

  <!-- Preflight request -->
  <line x1="122" y1="140" x2="578" y2="140" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr70b)" stroke-dasharray="5,3"/>
  <text x="350" y="133" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">OPTIONS  Access-Control-Request-Method / -Headers</text>

  <!-- Preflight response box -->
  <rect x="195" y="22" width="310" height="105" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="42" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">PREFLIGHT RESPONSE HEADERS</text>
  <text x="210" y="60" fill="#6db33f" font-size="9" font-family="monospace">Access-Control-Allow-Origin: https://…</text>
  <text x="210" y="76" fill="#6db33f" font-size="9" font-family="monospace">Access-Control-Allow-Methods: DELETE, PUT</text>
  <text x="210" y="92" fill="#6db33f" font-size="9" font-family="monospace">Access-Control-Allow-Headers: Authorization</text>
  <text x="210" y="108" fill="#6db33f" font-size="9" font-family="monospace">Access-Control-Max-Age: 7200</text>
  <line x1="350" y1="127" x2="350" y2="148" stroke="#6db33f" stroke-width="1" stroke-dasharray="2,2"/>

  <!-- Preflight response arrow -->
  <line x1="578" y1="158" x2="122" y2="158" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr70g)" stroke-dasharray="5,3"/>

  <!-- Real request -->
  <line x1="122" y1="185" x2="578" y2="185" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr70b)"/>
  <text x="350" y="178" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DELETE /api  Authorization: Bearer …</text>

  <!-- Real response -->
  <line x1="578" y1="202" x2="122" y2="202" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr70g)"/>

  <!-- Real response headers box -->
  <rect x="195" y="212" width="310" height="90" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="232" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">REAL RESPONSE HEADERS</text>
  <text x="210" y="250" fill="#6db33f" font-size="9" font-family="monospace">Access-Control-Allow-Origin: https://…</text>
  <text x="210" y="266" fill="#6db33f" font-size="9" font-family="monospace">Access-Control-Allow-Credentials: true</text>
  <text x="210" y="282" fill="#6db33f" font-size="9" font-family="monospace">Access-Control-Expose-Headers: X-Total-Count</text>
  <line x1="350" y1="202" x2="350" y2="212" stroke="#6db33f" stroke-width="1" stroke-dasharray="2,2"/>
</svg>

`Allow-Methods`, `Allow-Headers`, and `Max-Age` belong on the preflight response; `Allow-Credentials` and `Expose-Headers` belong on the real response (and `Allow-Origin` belongs on both).

## 5. Runnable example

```js
// cors-headers.js — Node.js, no installs.
// Demonstrates every Access-Control-Allow-* header in context.
const http = require("http");

const ALLOWED_ORIGINS = new Set(["http://localhost:5500", "https://app.example.com"]);

http.createServer((req, res) => {
  const origin = req.headers.origin || "";
  const allowed = ALLOWED_ORIGINS.has(origin);

  // ── PREFLIGHT ──
  if (req.method === "OPTIONS") {
    if (!allowed) { res.writeHead(403); res.end(); return; }

    res.writeHead(204, {
      // Who can read cross-origin (specific origin required for credentials)
      "Access-Control-Allow-Origin": origin,
      // Which methods are permitted cross-origin
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      // Which request headers JS is allowed to set
      "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-ID",
      // Cache this preflight for 2 hours (Chrome max)
      "Access-Control-Max-Age": "7200",
    });
    res.end();
    return;
  }

  // ── REAL RESPONSE ──
  if (!allowed) { res.writeHead(403); res.end("Forbidden"); return; }

  res.writeHead(200, {
    "Content-Type": "application/json",
    // Required on EVERY CORS response, not just preflight
    "Access-Control-Allow-Origin": origin,
    // Allow cookies / Authorization header to be sent
    "Access-Control-Allow-Credentials": "true",
    // Expose custom response headers to JS (without this, JS can't read them)
    "Access-Control-Expose-Headers": "X-Total-Count, X-Request-ID",
    // Custom headers that will now be readable by JS
    "X-Total-Count": "42",
    "X-Request-ID": "req-abc-123",
  });
  res.end(JSON.stringify({ data: [1, 2, 3] }));

}).listen(8000, () => {
  console.log("Server on http://localhost:8000");
  console.log("From http://localhost:5500 try:");
  console.log(`  fetch("http://localhost:8000/items", {`);
  console.log(`    method: "GET",`);
  console.log(`    credentials: "include",`);
  console.log(`    headers: { Authorization: "Bearer tok" }`);
  console.log(`  }).then(async r => {`);
  console.log(`    console.log(r.headers.get("X-Total-Count")); // "42"`);
  console.log(`    console.log(await r.json());`);
  console.log(`  })`);
});
```

**How to run:** `node cors-headers.js`. Test with curl to inspect the headers:
```bash
# Preflight
curl -si -X OPTIONS http://localhost:8000/items \
  -H "Origin: http://localhost:5500" \
  -H "Access-Control-Request-Method: DELETE" \
  -H "Access-Control-Request-Headers: Authorization"

# Real request
curl -si http://localhost:8000/items \
  -H "Origin: http://localhost:5500"
```

## 6. Walkthrough

- `ALLOWED_ORIGINS` is a `Set` for O(1) lookup. In production, load this from config — hardcoding production origins in source is fine; hardcoding `*` and adding credentials is not.
- `"Access-Control-Allow-Origin": origin` — echoing the specific request origin (not `*`) is required when `Allow-Credentials: true`. Using `*` with credentials causes the browser to block the request even if the origin matches.
- `"Access-Control-Allow-Methods"` — lists all methods the API supports. Including `OPTIONS` is a convention; the browser doesn't actually check for `OPTIONS` in this list, but it avoids confusing some proxies.
- `"Access-Control-Allow-Headers"` — case-insensitive, comma-separated. `X-Request-ID` is a custom header; without listing it here, the browser would block any request that tries to set it.
- `"Access-Control-Max-Age": "7200"` — without this, Chrome defaults to 5 seconds. 7 200 s (2 h) means the browser reuses the cached preflight for two hours per URL.
- `"Access-Control-Allow-Credentials": "true"` — goes on the real response, not just the preflight. If missing, the browser discards the response even though it arrived.
- `"Access-Control-Expose-Headers": "X-Total-Count, X-Request-ID"` — without this, `response.headers.get("X-Total-Count")` returns `null` in JavaScript, even though the header is in the response. This is the most commonly forgotten header in CORS setups.

## 7. Gotchas & takeaways

> **`Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` is invalid.** The browser rejects this combination. If you need cookies or auth, you must echo the specific origin.

> **`Access-Control-Expose-Headers` is forgotten constantly.** If your JS can't read a custom response header, add it to `Expose-Headers`. The browser hides non-safelisted headers by default even after a successful CORS response.

> **All six headers have different placements.** `Allow-Methods`, `Allow-Headers`, and `Max-Age` are only meaningful in preflight responses. `Allow-Credentials` and `Expose-Headers` belong on real responses. `Allow-Origin` goes on both.

- `Allow-Origin` is mandatory on every CORS response; missing it blocks everything.
- `Allow-Credentials: true` requires a specific origin — never `*`.
- `Allow-Methods` and `Allow-Headers` validate the preflight's `Request-*` counterparts.
- `Max-Age` eliminates repeated preflight round-trips; set it to at least a few minutes.
- `Expose-Headers` is the unlock for reading custom response headers from JS.
- Error responses (4xx, 5xx) also need `Allow-Origin` or JS sees only a generic network failure.
