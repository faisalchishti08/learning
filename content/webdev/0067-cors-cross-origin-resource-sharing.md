---
card: webdev
gi: 67
slug: cors-cross-origin-resource-sharing
title: CORS (Cross-Origin Resource Sharing)
---

## 1. What it is

**CORS (Cross-Origin Resource Sharing)** is the standard mechanism that lets a server explicitly allow cross-origin reads that the Same-Origin Policy (SOP) would otherwise block. It works through HTTP headers — the server opts specific origins, methods, and headers in.

The critical header:
```
Access-Control-Allow-Origin: https://app.example.com
```

Or to allow any origin (public APIs):
```
Access-Control-Allow-Origin: *
```

When the browser sees this header on a response, it allows JavaScript to read it even though the page's origin is different from the server's origin. Without this header, the browser silently blocks the JS from accessing the response body.

## 2. Why & when

You encounter CORS whenever a web page's JavaScript makes a request to a different origin. Common scenarios:

- A SPA at `app.example.com` calls an API at `api.example.com`.
- A frontend at `localhost:3000` calls a backend at `localhost:8000`.
- Any web app calling a public third-party API.

CORS errors show up as `"Failed to fetch"` in JavaScript and a "CORS policy" error in DevTools. The fix is always server-side — the server must send the right headers. You cannot fix a CORS error from the client side alone.

## 3. Core concept

Analogy: CORS is like a **bouncer who checks the guest list**. Your page (the guest) arrives at the server's door and says where they came from. The bouncer (browser) checks if the server's `Access-Control-Allow-Origin` list includes your origin. If yes, you're in. If no, you're blocked — even if the server already served your request.

Two types of CORS requests:

**Simple requests** — fired directly (no preflight) if they use only safe methods (`GET`, `POST`, `HEAD`) with safe headers and content types (`text/plain`, `application/x-www-form-urlencoded`, `multipart/form-data`). The browser sends the request and checks the `Access-Control-Allow-Origin` header on the response.

**Preflighted requests** — triggered when the request uses a non-simple method (`PUT`, `DELETE`, `PATCH`), a custom header (`Authorization`, `Content-Type: application/json`), or other non-simple features. The browser first sends an HTTP `OPTIONS` request (the preflight) asking the server: "Can I do this?" The server answers with what it allows:

```
OPTIONS /api/data HTTP/1.1
Origin: https://app.example.com
Access-Control-Request-Method: DELETE
Access-Control-Request-Headers: Authorization

200 OK
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, DELETE
Access-Control-Allow-Headers: Authorization
Access-Control-Max-Age: 86400
```

Only if the preflight succeeds does the browser send the actual `DELETE` request.

Key CORS response headers:

| Header | Meaning |
|--------|---------|
| `Access-Control-Allow-Origin` | Which origins may read this |
| `Access-Control-Allow-Methods` | Which HTTP methods are allowed |
| `Access-Control-Allow-Headers` | Which request headers are allowed |
| `Access-Control-Allow-Credentials` | Whether cookies may be sent |
| `Access-Control-Max-Age` | How long to cache the preflight result |
| `Access-Control-Expose-Headers` | Which response headers JS may read |

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CORS preflight flow: browser sends OPTIONS, server responds with Allow headers, then actual request proceeds">
  <defs>
    <marker id="arr67a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="arr67b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Browser -->
  <rect x="20" y="95" width="130" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="120" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>
  <text x="85" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">app.example.com</text>
  <text x="85" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JS: fetch DELETE</text>
  <text x="85" y="167" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ Authorization</text>

  <!-- Server -->
  <rect x="530" y="95" width="130" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="120" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>
  <text x="595" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">api.example.com</text>

  <!-- Step 1: Preflight OPTIONS -->
  <line x1="152" y1="125" x2="528" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr67a)"/>
  <text x="340" y="95" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">1. OPTIONS /api  Origin: app.example.com</text>

  <!-- Step 2: Preflight response -->
  <line x1="528" y1="145" x2="152" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr67b)"/>
  <text x="340" y="168" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2. 200 Allow-Origin: app.example.com, Methods: DELETE</text>

  <!-- Step 3: Actual request -->
  <line x1="152" y1="185" x2="528" y2="205" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr67a)"/>
  <text x="340" y="215" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">3. DELETE /api  Authorization: Bearer ...</text>

  <!-- Step 4: Actual response -->
  <line x1="528" y1="225" x2="152" y2="245" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr67b)"/>
  <text x="340" y="258" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">4. 200 OK  Allow-Origin: app.example.com ← JS can read</text>
</svg>

Preflight (OPTIONS) confirms the server's permission; only then does the real request fire.

## 5. Runnable example

```js
// server.js — Node.js, no installs. Shows a properly CORS-enabled API server.
const http = require("http");

const ALLOWED_ORIGIN = "http://localhost:5500"; // adjust to your frontend origin

function setCORSHeaders(req, res) {
  const origin = req.headers.origin;

  // In production, check origin against a whitelist instead of allowing all
  if (origin === ALLOWED_ORIGIN || ALLOWED_ORIGIN === "*") {
    res.setHeader("Access-Control-Allow-Origin", origin);
  }
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  res.setHeader("Access-Control-Allow-Credentials", "true");
  res.setHeader("Access-Control-Max-Age", "86400"); // cache preflight 24h
}

http.createServer((req, res) => {
  setCORSHeaders(req, res);

  // Handle preflight
  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === "/api/data" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ message: "CORS works!", origin: req.headers.origin }));
  } else {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("not found");
  }
}).listen(8000, () => {
  console.log("API at http://localhost:8000");
  console.log("Open a page at " + ALLOWED_ORIGIN + " and fetch /api/data");
});
```

**How to run:** `node server.js`. Open any HTML file served from `http://localhost:5500` (e.g. with VS Code Live Server) and run `fetch("http://localhost:8000/api/data").then(r=>r.json()).then(console.log)` in the browser console.

## 6. Walkthrough

- `setCORSHeaders` runs on every request, including preflight. It checks the `Origin` header and echoes it back in `Access-Control-Allow-Origin` (reflecting the specific origin is required when `Allow-Credentials: true` — `*` doesn't work with credentials).
- `Access-Control-Allow-Methods` tells the browser which HTTP verbs are permitted cross-origin. Without this, only `GET`/`POST`/`HEAD` would be allowed.
- `Access-Control-Allow-Headers` lists which request headers JS is allowed to set cross-origin. `Content-Type` and `Authorization` are both "non-simple" headers that require explicit allowance.
- The `OPTIONS` method check handles the preflight. The server returns `204 No Content` — no body needed, just the headers. `Max-Age=86400` means the browser caches this result for 24 hours and skips preflight on subsequent requests.
- The actual `GET /api/data` then proceeds. The browser reads the `Access-Control-Allow-Origin` on the response and, since it matches, allows `r.json()` to succeed.

## 7. Gotchas & takeaways

> **CORS is enforced by the browser, not the server.** `curl` or Postman ignores CORS entirely — they're not browsers. If an API "has a CORS error," the server is returning the right data; the browser just won't hand it to your JavaScript. The fix is always adding the right headers server-side.

> **`Access-Control-Allow-Origin: *` cannot be combined with `Access-Control-Allow-Credentials: true`.** When cookies or authorization headers are sent (`credentials: "include"` in fetch), the server must echo back the specific origin, not `*`. Browsers reject the wildcard in credentialed requests.

> **Every CORS response needs the headers — not just the 200 OK.** Error responses (400, 401, 500) also need `Access-Control-Allow-Origin`, or the browser blocks them and JS sees only a generic network error.

- CORS fix is always server-side — add `Access-Control-Allow-Origin` (and other headers as needed) to the response.
- Preflights are automatic for non-simple requests — implement `OPTIONS` handling or use framework middleware.
- Express: `app.use(require("cors")())` — the `cors` package handles all headers and OPTIONS automatically.
- Spring Boot: `@CrossOrigin(origins = "...")` on a controller or a global `CorsConfigurationSource` bean.
- Overly permissive CORS (`*` + credentials, or reflecting any origin without a whitelist) is a security vulnerability — an attacker's page can then read authenticated API responses.
