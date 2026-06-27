---
card: webdev
gi: 66
slug: same-origin-policy-sop
title: Same-Origin Policy (SOP)
---

## 1. What it is

The **Same-Origin Policy (SOP)** is a browser security rule that prevents JavaScript on one origin from reading data from a different origin. It is the fundamental isolation layer that keeps websites from attacking each other.

Two URLs share the same **origin** only if all three of these match:
1. **Scheme** (protocol): `https` vs `http`
2. **Host** (domain): `example.com` vs `other.com`
3. **Port**: `:443` vs `:8080`

```
https://example.com:443/page.html  ← origin: https://example.com:443

https://example.com/other          → SAME origin (port 443 implied, same scheme+host)
http://example.com/page            → DIFFERENT (scheme differs: http vs https)
https://api.example.com/data       → DIFFERENT (host differs: api subdomain)
https://example.com:8080/page      → DIFFERENT (port differs)
```

## 2. Why & when

Without SOP, a malicious page at `evil.com` could use your logged-in session to read your emails from `gmail.com`, steal your bank balance from `mybank.com`, or read your private messages from any other site — all by making requests with your cookies automatically attached.

SOP prevents this: JavaScript at `evil.com` cannot read the response from `gmail.com` even if the browser successfully fetches it, because the origins differ.

SOP is not something you "use" directly — it's enforced automatically by every browser. But you need to understand it because:
- It determines when `fetch` or `XMLHttpRequest` will fail in your own code.
- It determines when you need CORS (next tutorial).
- It determines what a Service Worker can cache.

## 3. Core concept

Analogy: SOP is like a **building access badge**. You can walk into your own office (same origin). You can look through a window at another building (you can *see* their page), but you can't open their filing cabinets (can't read their data with your credentials).

What SOP restricts:
- **Reading** cross-origin `fetch` / `XHR` responses.
- **Reading** `localStorage`, `sessionStorage`, cookies from a different origin.
- **Accessing** `contentDocument` of a cross-origin `<iframe>`.

What SOP does **not** restrict:
- **Sending** requests — `fetch("https://other.com")` fires; SOP only blocks reading the response.
- **Loading** resources via `<script src>`, `<img src>`, `<link href>` — these are "simple" cross-origin loads, fine by default.
- **Navigating** to a different origin — clicking a link is fine.

This is a crucial distinction: SOP is about **reading**, not sending or loading.

```
// Allowed: fire a request cross-origin (the request reaches the server)
await fetch("https://api.other.com/data");   // sends

// Blocked: reading the response if the server doesn't allow it (CORS)
const data = await response.json();  // throws if SOP blocks the response read
```

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SOP: evil.com JS can send a request to bank.com but cannot read the response; same-origin page can read freely">
  <defs>
    <marker id="arr66a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr66b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- evil.com -->
  <rect x="20" y="60" width="130" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="85" y="82" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">evil.com JS</text>
  <text x="85" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">different origin</text>

  <!-- bank.com server -->
  <rect x="380" y="40" width="140" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="68" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">bank.com</text>
  <text x="450" y="84" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">server responds</text>
  <text x="450" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(response reaches browser)</text>

  <!-- bank.com page -->
  <rect x="20" y="155" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="178" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">bank.com JS</text>
  <text x="85" y="194" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same origin</text>

  <!-- evil.com → bank.com: request allowed, response blocked -->
  <line x1="152" y1="80" x2="378" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr66a)"/>
  <text x="265" y="60" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">request sends OK</text>

  <line x1="378" y1="90" x2="152" y2="90" stroke="#f85149" stroke-width="1.5" marker-end="url(#arr66b)"/>
  <text x="265" y="107" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">response BLOCKED by SOP</text>

  <!-- bank.com page → bank.com server: all fine -->
  <line x1="152" y1="175" x2="378" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr66a)"/>
  <line x1="378" y1="130" x2="152" y2="180" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr66a)"/>
  <text x="265" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">same-origin: request + response both OK</text>
</svg>

SOP blocks reading the cross-origin response in the browser; the server never knows the block happened.

## 5. Runnable example

```html
<!-- sop-demo.html — open in any browser (no server needed for the demo logic) -->
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>SOP demo</title></head>
<body>
<h2>Same-Origin Policy demo</h2>
<p>Open this file at <code>file://</code> — its origin is <code>null</code>.</p>
<button onclick="trySameOrigin()">Fetch same-origin (httpbin)</button>
<button onclick="tryCrossOrigin()">Fetch cross-origin (blocked)</button>
<pre id="out" style="background:#1c2430;color:#e6edf3;padding:1em;margin-top:1em"></pre>

<script>
function log(m) { document.getElementById("out").textContent += m + "\n"; }
function clearLog() { document.getElementById("out").textContent = ""; }

// This page is at file:// — effectively origin "null"
// httpbin.org is a different origin.
// Both requests are cross-origin here; the difference is whether the server
// sends CORS headers (httpbin does for /get).

async function trySameOrigin() {
  clearLog();
  log("Current page origin: " + location.origin);
  log("Attempting fetch to https://httpbin.org/get (sends CORS headers)...");
  try {
    const r = await fetch("https://httpbin.org/get");
    const data = await r.json();
    log("Success! url field: " + data.url);
  } catch (e) {
    log("Failed: " + e.message);
  }
}

async function tryCrossOrigin() {
  clearLog();
  log("Attempting fetch to https://example.com (no CORS headers)...");
  try {
    // example.com does not send Access-Control-Allow-Origin
    const r = await fetch("https://example.com", { mode: "cors" });
    const text = await r.text();
    log("Got: " + text.slice(0, 100));
  } catch (e) {
    log("Blocked by SOP/CORS: " + e.message);
    log("(The browser received the response but won't hand it to JS)");
  }
}
</script>
</body>
</html>
```

**How to run:** save as `sop-demo.html` and open in a browser. Click each button and read the console — the second fetch is blocked despite the server returning a 200.

## 6. Walkthrough

- `location.origin` shows the page's current origin. From `file://`, it's `"null"` — a special opaque origin that's cross-origin to everything.
- The first fetch (`httpbin.org/get`) succeeds because httpbin explicitly opts into cross-origin reads by sending `Access-Control-Allow-Origin: *` — that's CORS, covered next.
- The second fetch (`example.com`) sends a request and gets a response (200 with HTML), but SOP blocks `r.text()` from returning anything — `fetch` throws a network error instead.
- The error message is intentionally vague (`Failed to fetch`) — browsers hide details from cross-origin error reads to prevent leaking information.
- DevTools → Console shows "CORS policy" errors that explain which header was missing.

## 7. Gotchas & takeaways

> **SOP blocks reading, not sending.** The server receives your cross-origin request normally — including your cookies. This is why CSRF attacks are possible even with SOP: a malicious page can send a state-changing request to your bank; SOP just prevents it from reading the bank's response. Use `SameSite` cookies and CSRF tokens to stop this.

> **`<script>`, `<img>`, `<link>`, `<video>` all load cross-origin by default.** SOP only restricts programmatic cross-origin data reads (fetch, XHR). Serving JavaScript to anyone means that JS runs in their origin's context — CDN scripts are trusted by the loading page.

- Origin = scheme + host + port (all three must match).
- SOP is enforced by browsers — servers never see it; the browser blocks the JS from reading the response.
- SOP errors appear in DevTools console as "CORS policy" errors — CORS is the mechanism used to relax SOP.
- Subdomains are different origins: `app.example.com` ≠ `api.example.com`.
- `document.domain` manipulation (old trick to share state between subdomains) is deprecated and blocked in modern browsers.
