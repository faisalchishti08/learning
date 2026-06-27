---
card: webdev
gi: 68
slug: simple-vs-preflighted-requests
title: Simple vs preflighted requests
---

## 1. What it is

When a browser makes a cross-origin fetch, it places the request into one of two categories:

- **Simple request** — sent directly; no negotiation needed first.
- **Preflighted request** — the browser sends a probe request (`OPTIONS`) first, waits for permission, then sends the real request.

The distinction is entirely automatic. You don't write code to choose; the browser decides based on what the request looks like. Understanding the rules tells you when to expect an extra round-trip and why your server needs to handle `OPTIONS`.

## 2. Why & when

The split exists to protect legacy servers. Before CORS existed, servers never expected cross-origin requests with custom methods or headers — they assumed any `DELETE /resource` or `Content-Type: application/json` POST came from the same origin. Silently sending those requests cross-origin would have broken or exploited those servers.

Simple requests use the same methods and headers that HTML forms and `<img>` tags always could send cross-origin, so there's no new risk — no preflight needed. Preflighted requests can do things forms never could, so the browser asks the server first: "Are you CORS-aware? Do you consent to this?"

In practice: any modern API call using `application/json`, `Authorization`, or verbs like `PUT`/`DELETE`/`PATCH` will be preflighted. Most REST API usage is preflighted.

## 3. Core concept

Think of it like a job applicant sending a résumé vs. showing up unannounced. Simple requests are the résumé — sending them costs nothing and surprises nobody. Preflighted requests are showing up in person: the company (server) must first confirm they're ready to receive you (`OPTIONS` → `200 Allow-*`), then you arrive for the interview (actual request).

**Simple request rules** — ALL must be true:

| Condition | Allowed values |
|-----------|---------------|
| Method | `GET`, `POST`, or `HEAD` |
| Content-Type (if present) | `text/plain`, `application/x-www-form-urlencoded`, `multipart/form-data` |
| Headers | Only CORS-safelisted headers (e.g. `Accept`, `Content-Language`) |
| No `ReadableStream` in request | — |
| No event listeners on `XMLHttpRequestUpload` | — |

If any condition is violated, the browser preflights.

**Preflight trigger examples:**
- `fetch("/api", { method: "DELETE" })` → DELETE is not in the safe list.
- `fetch("/api", { headers: { Authorization: "Bearer …" } })` → `Authorization` is not safelisted.
- `fetch("/api", { headers: { "Content-Type": "application/json" }, method: "POST" })` → `application/json` is not safelisted.

The preflight is an `OPTIONS` request to the same URL carrying two special headers:
- `Access-Control-Request-Method: DELETE` — what method does the real request want?
- `Access-Control-Request-Headers: Authorization` — what non-simple headers does it want?

The server answers with `Access-Control-Allow-*` headers. If the server approves, the real request fires. If not, the browser blocks it without ever sending it.

## 4. Diagram

<svg viewBox="0 0 700 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side comparison: simple request goes direct, preflighted request sends OPTIONS first then the real request">
  <defs>
    <marker id="arr68g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr68b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Left panel: Simple -->
  <rect x="10" y="10" width="320" height="280" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="38" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Simple Request</text>
  <text x="170" y="56" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET / POST(form) / HEAD · safelisted headers</text>

  <rect x="30" y="70" width="100" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="80" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>

  <rect x="210" y="70" width="100" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="260" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <line x1="132" y1="85" x2="208" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr68g)"/>
  <text x="170" y="78" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">1. GET /data  Origin: …</text>

  <line x1="208" y1="100" x2="132" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr68b)"/>
  <text x="170" y="116" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">2. 200 OK  Allow-Origin: …</text>

  <text x="170" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">✓ JS reads response</text>
  <text x="170" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1 round-trip total</text>

  <!-- Right panel: Preflighted -->
  <rect x="360" y="10" width="320" height="280" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="38" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Preflighted Request</text>
  <text x="520" y="56" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DELETE / PUT / custom headers / application/json</text>

  <rect x="380" y="70" width="100" height="40" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="430" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>

  <rect x="560" y="70" width="100" height="40" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="610" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <line x1="482" y1="82" x2="558" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr68b)" stroke-dasharray="4,2"/>
  <text x="520" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. OPTIONS /api  ACR-Method: DELETE</text>

  <line x1="558" y1="97" x2="482" y2="97" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr68g)" stroke-dasharray="4,2"/>
  <text x="520" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2. 204  Allow-Methods: DELETE ✓</text>

  <line x1="482" y1="145" x2="558" y2="145" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr68g)"/>
  <text x="520" y="138" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">3. DELETE /api  Authorization: …</text>

  <line x1="558" y1="160" x2="482" y2="160" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr68b)"/>
  <text x="520" y="175" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">4. 200 OK  Allow-Origin: …</text>

  <text x="520" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">✓ JS reads response</text>
  <text x="520" y="228" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">2 round-trips total</text>
</svg>

Simple requests skip the OPTIONS probe; preflighted requests pay an extra round-trip for server permission.

## 5. Runnable example

```js
// demo.js — Node.js, no installs. Logs whether each fetch would be simple or preflighted.
// Run in Node to see the classification logic; uses http module to make real requests.

const http = require("http");

// Minimal CORS-aware server
const server = http.createServer((req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    console.log("  → Server received PREFLIGHT OPTIONS");
    res.writeHead(204); res.end(); return;
  }

  console.log(`  → Server received: ${req.method} ${req.url}`);
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ ok: true }));
});

server.listen(3000, async () => {
  // Helper: classify a request before sending
  function classify(method, headers = {}) {
    const safeMethods = ["GET", "POST", "HEAD"];
    const safeCT = ["text/plain", "application/x-www-form-urlencoded", "multipart/form-data"];
    const safeHeaders = ["accept", "accept-language", "content-language", "content-type"];

    if (!safeMethods.includes(method)) return "PREFLIGHTED (non-safe method)";
    const ct = (headers["content-type"] || "").split(";")[0].trim();
    if (ct && !safeCT.includes(ct)) return "PREFLIGHTED (non-safe Content-Type)";
    const nonSafe = Object.keys(headers).filter(h => !safeHeaders.includes(h.toLowerCase()));
    if (nonSafe.length) return `PREFLIGHTED (non-safe header: ${nonSafe[0]})`;
    return "SIMPLE";
  }

  const cases = [
    { method: "GET",    headers: {},                                  label: "GET, no custom headers" },
    { method: "POST",   headers: { "content-type": "text/plain" },   label: "POST text/plain" },
    { method: "POST",   headers: { "content-type": "application/json" }, label: "POST JSON" },
    { method: "DELETE", headers: {},                                  label: "DELETE" },
    { method: "GET",    headers: { "authorization": "Bearer abc" },  label: "GET + Authorization" },
  ];

  for (const c of cases) {
    const type = classify(c.method, c.headers);
    console.log(`\n[${c.label}] → ${type}`);
  }

  server.close();
});
```

**How to run:** `node demo.js`

Expected output:
```
[GET, no custom headers] → SIMPLE
[POST text/plain] → SIMPLE
[POST JSON] → PREFLIGHTED (non-safe Content-Type)
[DELETE] → PREFLIGHTED (non-safe method)
[GET + Authorization] → PREFLIGHTED (non-safe header: authorization)
```

## 6. Walkthrough

- `classify(method, headers)` encodes the browser's decision tree. It checks method first, then `Content-Type`, then any other headers. If anything falls outside the safelist, it returns `PREFLIGHTED` with a reason.
- `safeMethods` — only GET, POST, and HEAD bypass preflight. DELETE, PUT, PATCH always trigger it.
- `safeCT` — the safe content types are exactly the three that HTML forms have always been able to send. `application/json` is not in the list, which is why every modern REST `POST` is preflighted.
- `safeHeaders` — the CORS safelisted request headers are a small set. Adding `Authorization`, `X-Custom-Header`, or any non-standard name triggers preflight.
- The server logs `PREFLIGHT OPTIONS` when the OPTIONS probe arrives, then `POST /api` when the real request fires — you'd see two log lines for preflighted requests in a real browser.
- `Access-Control-Max-Age` (not shown here) caches the preflight result in the browser for N seconds, avoiding repeated round-trips for the same endpoint.

## 7. Gotchas & takeaways

> **Adding a single non-safe header converts a simple request to a preflighted one.** A `GET` with just `{ Authorization: "Bearer token" }` now costs two round-trips instead of one. This surprises developers who assume GETs are always "simple."

> **`Content-Type: application/json` always preflights, even on POST.** Almost all modern REST calls — "just a plain POST with JSON" — are preflighted. Plan your server to handle `OPTIONS` on every CORS-enabled endpoint.

- Three safe methods: `GET`, `POST`, `HEAD`. Everything else preflights.
- Three safe content types: `text/plain`, `application/x-www-form-urlencoded`, `multipart/form-data`. `application/json` is not safe.
- Any non-safelisted request header (including `Authorization`) triggers preflight.
- Preflighted ≠ blocked — it just means an extra `OPTIONS` exchange before the real request.
- Use `Access-Control-Max-Age` to cache preflight responses and reduce extra round-trips.
- `curl` and Postman send the real request without preflighting — they're not browsers.
