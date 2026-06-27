---
card: webdev
gi: 72
slug: cors-vs-corb-vs-corp
title: CORS vs CORB vs CORP
---

## 1. What it is

Three browser security mechanisms share the "cross-origin" prefix but solve different problems:

| Name | Stands for | Protects | Controlled by |
|------|-----------|---------|--------------|
| **CORS** | Cross-Origin Resource Sharing | JavaScript reading cross-origin responses | Server (opt-in headers) |
| **CORB** | Cross-Origin Read Blocking | Browser parsing cross-origin HTML/JSON injected via `<img>`, `<script>` tags | Browser (automatic, heuristic) |
| **CORP** | Cross-Origin Resource Policy | A resource being embedded anywhere cross-origin (including `<img>`, `<script>`, iframes) | Server (opt-in header) |

CORS is the most widely known and developer-facing. CORB and CORP emerged from the **Spectre** CPU vulnerability class (2018) — they exist to prevent cross-origin data from being loaded into a process at all, where Spectre-style timing attacks could extract it bit by bit.

## 2. Why & when

The Same-Origin Policy (SOP) prevents JavaScript from reading cross-origin responses, but it doesn't prevent the browser from **loading** cross-origin resources into process memory — `<img src="https://bank.com/account.json">` still fetches the JSON (and the CPU caches it) even though JS can't read it. Spectre showed that a malicious page could infer the bytes via timing side-channels.

- **CORB** is a browser-level heuristic defence: if a resource's MIME type looks like data (HTML, JSON, XML) but was loaded via an element that expects media (an `<img>`, `<video>`, `<script>` tag), CORB strips the response body before it ever reaches the renderer process. No server change needed.
- **CORP** gives servers explicit control: a single header declares who is allowed to embed the resource at all, strengthening CORB's heuristic with a firm policy. Needed because CORB's heuristic has gaps (e.g. resources without a declared MIME type).

You encounter these when:
- Debugging why an `<img>` or `<script>` load fails with a "CORB" message in the console (CORB).
- Hardening a CDN or API so that your resources can only be embedded by your own origins (CORP).
- Combining CORP with `Cross-Origin-Opener-Policy` (COOP) and `Cross-Origin-Embedder-Policy` (COEP) to unlock `SharedArrayBuffer` and high-resolution timers (requires both).

## 3. Core concept

Think of three security guards at a library:

- **CORS guard** stands at the checkout desk. When JS tries to read a book from another library (cross-origin fetch), the guard checks whether the other library (server) said it's okay. No permission → the book is handed back with the cover glued shut (response received but JS can't read it).
- **CORB guard** stands at the shelving robots. When a reader (tag like `<img>`) orders a book labelled "NOVEL" but the shelf delivers what looks like a "CONFIDENTIAL DATABASE DUMP," CORB intercepts it and replaces the contents with an empty page before it even reaches the reader's desk. Happens automatically.
- **CORP guard** is a note in the book itself ("this book may only be taken out by patrons from Branch A"). Any reader from any other branch is turned away at the door, before they even open the book.

**CORS** — controlled by `Access-Control-Allow-*` response headers. Governs whether JS code can read a response. Does not prevent the resource from being fetched into memory.

**CORB** — automatic browser behaviour, no headers needed. Applies to "opaque" cross-origin loads (images, scripts, audio, video). If the server returns HTML/JSON/XML with a correct MIME type, CORB blocks the body from reaching the renderer, replacing it with an empty response. You may see `Cross-Origin Read Blocking (CORB) blocked cross-origin response` in DevTools.

**CORP** — controlled by one response header:
```http
Cross-Origin-Resource-Policy: same-origin
Cross-Origin-Resource-Policy: same-site
Cross-Origin-Resource-Policy: cross-origin
```
- `same-origin` — only pages from the exact same origin may embed this resource.
- `same-site` — pages from the same registrable domain (any subdomain) may embed it.
- `cross-origin` — any page may embed it (equivalent to no policy, but explicit).

Without a CORP header, CORB's heuristic is the only defence. With CORP: `same-origin` or `same-site`, even CORB's gaps are covered — any cross-origin embed is blocked.

## 4. Diagram

<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three-layer diagram showing CORS, CORB, and CORP each blocking at different points in the cross-origin flow">
  <defs>
    <marker id="arr72r" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="arr72g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr72b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Columns -->
  <text x="80" y="28" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">JS / Tag</text>
  <text x="270" y="28" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser layers</text>
  <text x="590" y="28" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>

  <!-- Server box -->
  <rect x="520" y="40" width="150" height="240" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="68" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Resource</text>
  <text x="595" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CORP header ← controls</text>
  <text x="595" y="99" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">who can embed at all</text>
  <line x1="520" y1="110" x2="670" y2="110" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="2,2"/>
  <text x="595" y="128" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">API response</text>
  <text x="595" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CORS headers ← controls</text>
  <text x="595" y="159" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JS read access</text>

  <!-- CORP guard -->
  <rect x="380" y="50" width="110" height="50" rx="5" fill="#0d1117" stroke="#f85149" stroke-width="1.2"/>
  <text x="435" y="72" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">CORP guard</text>
  <text x="435" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">blocks embed by policy</text>
  <line x1="518" y1="75" x2="492" y2="75" stroke="#f85149" stroke-width="1.5" marker-end="url(#arr72r)"/>

  <!-- CORB guard -->
  <rect x="380" y="140" width="110" height="50" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="435" y="162" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">CORB guard</text>
  <text x="435" y="178" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">empties body if MIME mismatch</text>
  <line x1="518" y1="165" x2="492" y2="165" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr72b)"/>

  <!-- CORS guard -->
  <rect x="200" y="220" width="110" height="50" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.2"/>
  <text x="255" y="242" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">CORS guard</text>
  <text x="255" y="258" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">blocks JS read access</text>
  <line x1="378" y1="165" x2="312" y2="245" stroke="#8b949e" stroke-width="1" stroke-dasharray="2,2"/>

  <!-- JS box -->
  <rect x="10" y="220" width="110" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="65" y="242" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JS / Browser</text>
  <text x="65" y="258" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">tag / fetch()</text>
  <line x1="122" y1="245" x2="198" y2="245" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr72g)"/>
</svg>

CORP fires first (at the server's instruction), CORB fires in-flight (browser heuristic), CORS fires last (controls JS read access after the response arrives).

## 5. Runnable example

```js
// cors-corp-demo.js — Node.js, no installs.
// Shows three resources: one with CORP same-origin, one CORS-enabled, one bare.
const http = require("http");

http.createServer((req, res) => {
  if (req.url === "/image-private") {
    // CORP: only same-origin pages can load this image
    res.writeHead(200, {
      "Content-Type": "image/png",
      "Cross-Origin-Resource-Policy": "same-origin",
    });
    // 1x1 transparent PNG bytes
    res.end(Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "base64"));
    return;
  }

  if (req.url === "/image-public") {
    // CORP: any origin may embed this
    res.writeHead(200, {
      "Content-Type": "image/png",
      "Cross-Origin-Resource-Policy": "cross-origin",
    });
    res.end(Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "base64"));
    return;
  }

  if (req.url === "/api/data") {
    // CORS: JS fetch from cross-origin allowed; CORB irrelevant (correct MIME + CORS headers)
    const origin = req.headers.origin || "";
    if (req.method === "OPTIONS") {
      res.writeHead(204, {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET",
        "Cross-Origin-Resource-Policy": "cross-origin",
      });
      res.end(); return;
    }
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": origin || "*",
      // Without CORP header here, CORB will block if loaded as <script src=...>
      "Cross-Origin-Resource-Policy": "cross-origin",
    });
    res.end(JSON.stringify({ message: "CORS + CORP demo", url: req.url }));
    return;
  }

  if (req.url === "/api/no-cors-headers") {
    // Returns JSON with no CORS headers and no CORP header.
    // fetch() from cross-origin: CORS blocks JS read.
    // <img src=...>: CORB strips body (JSON != image MIME type).
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ secret: "you should not read this cross-origin" }));
    return;
  }

  res.writeHead(404); res.end("Not found");
}).listen(8000, () => {
  console.log("Server on http://localhost:8000");
  console.log("CORP same-origin: /image-private  (cross-origin embed blocked)");
  console.log("CORP cross-origin: /image-public  (anyone may embed)");
  console.log("CORS + CORP: /api/data  (JS can read cross-origin)");
  console.log("No headers: /api/no-cors-headers  (CORS+CORB both block)");
});
```

**How to run:** `node cors-corp-demo.js`. Use browser DevTools Network tab to inspect response headers. From a different origin (e.g. a page at `http://localhost:5500`):
```js
// This works (CORS headers present):
await fetch("http://localhost:8000/api/data").then(r => r.json())

// This throws (no CORS headers):
await fetch("http://localhost:8000/api/no-cors-headers").then(r => r.json())
```

## 6. Walkthrough

- `/image-private` — `Cross-Origin-Resource-Policy: same-origin` means any cross-origin `<img src="...">` or `fetch(..., {mode:"no-cors"})` will be blocked before the response body is consumed. Even `<img>` tags — not just JS.
- `/image-public` — `cross-origin` explicitly allows any origin to embed. Same as no CORP header, but explicit and future-proof.
- `/api/data` — has both CORS and CORP. CORS lets JS `fetch()` read it; CORP: `cross-origin` ensures CORB won't strip the body (CORB is less aggressive when CORP explicitly permits cross-origin access).
- `/api/no-cors-headers` — returns `Content-Type: application/json`. If a page does `<img src="http://localhost:8000/api/no-cors-headers">`, CORB detects the MIME type mismatch (JSON != image) and replaces the body with an empty response. If JS does `fetch(...)` from a different origin, CORS blocks JS from reading it. The data never fully loads into renderer memory in either case.

## 7. Gotchas & takeaways

> **CORB is heuristic and MIME-type dependent.** A JSON resource served as `Content-Type: text/plain` or with no content-type may not be CORB-blocked. Always set correct MIME types and add a CORP header for sensitive resources.

> **CORP blocks `<img>` and `<script>` tags, not just `fetch`.** Unlike CORS (which only governs JS-initiated fetches), CORP applies to all cross-origin loads — tags, CSS `url()`, worker imports, iframes. Set `CORP: same-origin` on private API images and internal resources.

> **Enabling `SharedArrayBuffer` requires CORP on all resources.** To use `Cross-Origin-Embedder-Policy: require-corp` (needed for `SharedArrayBuffer`), every subresource on the page must carry a CORP header. Forgetting one resource blocks the whole feature.

- CORS = "can JS read this response?" — server opt-in via `Access-Control-Allow-*`.
- CORB = "should this data enter renderer memory at all?" — automatic browser heuristic based on MIME type.
- CORP = "who may embed this resource at all?" — server opt-in via `Cross-Origin-Resource-Policy`.
- For sensitive resources (user data, private images): set `CORP: same-origin` as a defence-in-depth measure.
- For public CDN assets: set `CORP: cross-origin` to cooperate with pages using strict COEP.
- CORB and CORP both address Spectre-class CPU attacks; CORS addresses application-level data access.
