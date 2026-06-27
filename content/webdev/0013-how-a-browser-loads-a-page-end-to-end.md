---
card: webdev
gi: 13
slug: how-a-browser-loads-a-page-end-to-end
title: How a browser loads a page end-to-end
---

## 1. What it is

When you type a URL and hit Enter, you don't "go" to a website — your browser initiates a precisely ordered chain of operations that ends with rendered pixels on your screen. This sequence is called the **browser navigation pipeline**, and it involves DNS resolution, TCP/TLS handshaking, HTTP request/response cycles, HTML parsing, sub-resource fetching, and layout/paint.

The entire round trip from keystroke to first paint typically takes **50–500 ms** on a fast connection. Understanding each step tells you where to look when something is slow or broken.

## 2. Why & when

Every web developer needs a mental model of this pipeline because:

- **Performance debugging**: is the site slow because of DNS, a slow server, large JavaScript, or layout thrashing? Each has a different fix.
- **Security**: knowing that TLS negotiates before any HTTP headers are sent explains why HSTS and certificate pinning work.
- **Debugging network errors**: `ERR_NAME_NOT_RESOLVED` = DNS failure; `ERR_CONNECTION_REFUSED` = no server on that port; `ERR_CERT_AUTHORITY_INVALID` = TLS failure. The step tells you the layer.

This sequence fires **every** time you navigate to a new URL. Subsequent navigations may skip parts (DNS cache hit, HTTP/2 connection reuse), but a cold first load runs all of it.

## 3. Core concept

Think of ordering a pizza by post. You first look up the pizzeria's address in the phone book (DNS), drive to the building and knock (TCP connect), show ID because the door is locked (TLS), slide your written order through the slot (HTTP request), wait while the kitchen cooks (server processing), and receive a box of ingredients with assembly instructions (HTML + assets).

The steps in order:

1. **Parse the URL** — browser breaks `https://example.com/path?q=1` into scheme, host, path, and query string.
2. **Check caches** — browser HTTP cache, service workers, and prefetch cache are checked before any network call.
3. **DNS resolution** — `example.com` is converted to an IP address (e.g. `93.184.216.34`).
4. **TCP connection** — a three-way handshake (SYN / SYN-ACK / ACK) opens a reliable byte stream to port 443.
5. **TLS handshake** — client and server agree on cipher suite, the server presents its certificate, and a shared session key is derived. Only then can encrypted data flow.
6. **HTTP request** — browser sends `GET /path HTTP/1.1` plus headers (Host, Accept, cookies, etc.).
7. **Server response** — server returns a status code, response headers, and body (usually HTML).
8. **HTML parse + DOM construction** — the browser streams the HTML and builds the DOM tree node by node. Blocking `<script>` tags pause parsing.
9. **Sub-resource fetching** — as the parser discovers `<link>`, `<img>`, `<script>` tags it dispatches new requests (each potentially repeating steps 3–7, often reusing the open TCP/TLS connection via HTTP keep-alive or HTTP/2 multiplexing).
10. **CSSOM construction** — CSS is parsed into a style tree.
11. **Render tree + layout** — DOM + CSSOM merge into a render tree; the browser calculates each element's size and position.
12. **Paint & composite** — pixels are drawn to screen layers which the GPU composites into what you see.

## 4. Diagram

<svg viewBox="0 0 680 360" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Browser page-load pipeline from URL entry to rendered pixels">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Step boxes -->
  <rect x="10"  y="20"  width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75"  y="39"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1. Parse URL</text>
  <text x="75"  y="55"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">&amp; check caches</text>

  <rect x="170" y="20"  width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="39"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2. DNS lookup</text>
  <text x="235" y="55"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">hostname → IP</text>

  <rect x="330" y="20"  width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="39"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">3. TCP connect</text>
  <text x="395" y="55"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SYN / SYN-ACK / ACK</text>

  <rect x="490" y="20"  width="130" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="39"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">4. TLS handshake</text>
  <text x="555" y="55"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">cert + session key</text>

  <rect x="10"  y="120" width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75"  y="139" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">5. HTTP request</text>
  <text x="75"  y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET /path + headers</text>

  <rect x="170" y="120" width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="139" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">6. Server response</text>
  <text x="235" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK + HTML body</text>

  <rect x="330" y="120" width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="139" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">7. Parse HTML</text>
  <text x="395" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">build DOM tree</text>

  <rect x="490" y="120" width="130" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="139" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">8. Fetch sub-resources</text>
  <text x="555" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">CSS, JS, images…</text>

  <rect x="170" y="220" width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="239" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">9. Build CSSOM</text>
  <text x="235" y="255" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">parse stylesheets</text>

  <rect x="330" y="220" width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="239" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">10. Render tree</text>
  <text x="395" y="255" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DOM + CSSOM merge</text>

  <rect x="490" y="220" width="130" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="239" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">11. Layout + Paint</text>
  <text x="555" y="255" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">pixels on screen</text>

  <!-- Arrows row 1 -->
  <line x1="142" y1="42" x2="168" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="302" y1="42" x2="328" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="462" y1="42" x2="488" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Down from step 4 to step 5 area (right-to-left row) -->
  <line x1="555" y1="64" x2="555" y2="100" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="555" y1="100" x2="75" y2="100" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="75"  y1="100" x2="75" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Arrows row 2 -->
  <line x1="142" y1="142" x2="168" y2="142" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="302" y1="142" x2="328" y2="142" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="462" y1="142" x2="488" y2="142" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Down to row 3 -->
  <line x1="555" y1="164" x2="555" y2="200" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="555" y1="200" x2="235" y2="200" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="235" y1="200" x2="235" y2="218" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Arrows row 3 -->
  <line x1="302" y1="242" x2="328" y2="242" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="462" y1="242" x2="488" y2="242" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Label -->
  <text x="340" y="320" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Blue border = HTTPS-only steps (skipped for plain HTTP)</text>
</svg>

A cold page load runs all 11 steps in sequence; warm loads skip cached DNS, reuse open connections, and hit the HTTP cache.

## 5. Runnable example

This Node.js script simulates steps 5–7 (request, response, HTML) and measures how long each part takes, mirroring what a real browser measures.

```js
// save as load-timer.js  —  requires Node.js, no npm install
const https = require("https");

const url = "https://example.com/";
const t0 = Date.now();

const req = https.get(url, (res) => {
  const afterHeaders = Date.now();
  console.log(`Status:          ${res.statusCode}`);
  console.log(`Time to headers: ${afterHeaders - t0} ms`);

  let bytes = 0;
  res.on("data", (chunk) => { bytes += chunk.length; });
  res.on("end", () => {
    const done = Date.now();
    console.log(`Body size:       ${bytes} bytes`);
    console.log(`Total load time: ${done - t0} ms`);
  });
});

req.on("error", (e) => console.error("Request failed:", e.message));
```

**How to run:** `node load-timer.js` — Node handles DNS, TCP, and TLS automatically; you measure HTTP response time.

Expected output (approximate — real numbers vary by location):
```
Status:          200
Time to headers: 120 ms
Body size:       1256 bytes
Total load time: 135 ms
```

## 6. Walkthrough

- `const https = require("https")` — Node's built-in HTTPS module; handles DNS → TCP → TLS for you, just like a browser.
- `const t0 = Date.now()` — timestamp before any network work begins, equivalent to the browser's `navigationStart`.
- `https.get(url, (res) => {...})` — fires the GET request. Node performs DNS lookup and TCP+TLS handshake before this callback fires. `res` is the streaming response object.
- `afterHeaders - t0` — measures time from navigation start to receiving the response status and headers; this is roughly the browser's `responseStart` metric (TTFB — time to first byte).
- `res.on("data", ...)` — accumulates body chunks as they arrive over the network. The browser does this too, building the DOM incrementally as HTML chunks stream in.
- `res.on("end", ...)` — fires when the body is fully received; analogous to the browser's `DOMContentLoaded` or `load` event depending on what the HTML contains.
- `done - t0` — total wall-clock time for DNS + TCP + TLS + server processing + body transfer, the real network cost the browser pays before it can even start parsing.

## 7. Gotchas & takeaways

> DNS lookup is cached — but only for the TTL the DNS record specifies. If DNS is slow on the first visit and then fast on the next, that's why: the cache is cold/warm, not your internet connection changing.

> TLS adds latency even before a single byte of content is exchanged. Modern TLS 1.3 reduced the handshake from 2 round trips to 1, and TLS session resumption can drop it to 0 — but plain HTTP still beats cold HTTPS on raw first-byte time. Use HTTPS anyway; the security is worth it.

- The order is fixed: DNS → TCP → TLS → HTTP → parse → sub-resources → render. You can't skip steps, only speed them up.
- Render-blocking resources (synchronous `<script>` in `<head>`) pause HTML parsing at step 7 until the JS is downloaded and executed.
- `DOMContentLoaded` fires after the HTML is parsed; `load` fires after all sub-resources (images, iframes) finish downloading.
- Chrome DevTools → Network tab shows every step as a waterfall; the coloured segments map directly to DNS / connect / TLS / TTFB / download.
- HTTP/2 multiplexes many sub-resources over a single TCP connection; HTTP/3 moves to QUIC (UDP-based) to eliminate TCP head-of-line blocking.
