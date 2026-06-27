---
card: webdev
gi: 43
slug: connection-management-keep-alive
title: Connection management (keep-alive)
---

## 1. What it is

**Connection management** in HTTP describes how TCP connections are opened, reused, and closed between client and server. The key feature is **keep-alive** (persistent connections), where a single TCP connection is reused for multiple HTTP requests instead of opening a new one for every request.

- **HTTP/1.0**: one TCP connection per request, closed immediately after the response.
- **HTTP/1.1**: connections are **persistent by default** — the same TCP connection stays open for multiple requests (keep-alive).
- **HTTP/2**: multiplexing — many requests travel over one TCP connection simultaneously.

## 2. Why & when

Opening a TCP connection is expensive. It requires a **3-way handshake** (3 round-trips) before the first byte of HTTP is sent, and HTTPS adds a TLS handshake on top (1–2 more round-trips). A typical web page loads 20–100 resources (scripts, stylesheets, images). Without keep-alive, every resource costs a full handshake. Keep-alive lets the browser pay that cost once and amortise it across many requests.

This matters when:

- Profiling site load times — understanding why waterfalls show requests queued instead of parallel.
- Configuring reverse proxies (Nginx, HAProxy) — keep-alive settings between proxy and upstream services affect throughput under load.
- Building HTTP clients — reusing connections avoids per-request overhead and rate limits on connection creation.
- Debugging `Connection: close` appearing when it shouldn't.

## 3. Core concept

Analogy: calling a taxi company. **HTTP/1.0** is calling a new taxi for every errand. **HTTP/1.1 keep-alive** is having one taxi wait outside while you run multiple errands. **HTTP/2** is a minivan that runs all errands simultaneously.

**How keep-alive works in HTTP/1.1:**

1. Client sends request with `Connection: keep-alive` (or omits the header, since it's the default).
2. Server responds and keeps the TCP socket open instead of closing it.
3. Client sends another request on the same socket — no new handshake.
4. Either side can close with `Connection: close`.
5. Servers set a **timeout** (`Keep-Alive: timeout=5, max=100`) — idle connections close after 5 s or 100 requests.

**HTTP/1.1 pipelining** (rarely used): sending multiple requests before the first response arrives, but responses must come back in order (head-of-line blocking). Mostly replaced by HTTP/2.

**HTTP/2 multiplexing**: truly parallel streams over one connection, no head-of-line blocking at the HTTP layer.

Key headers:

```
Connection: keep-alive     # request or response — "keep this socket open"
Connection: close          # tear down after this response
Keep-Alive: timeout=5, max=100  # server's keep-alive policy
```

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of HTTP/1.0 one connection per request versus HTTP/1.1 keep-alive reusing one connection for multiple requests">
  <rect width="680" height="300" fill="#0d1117"/>

  <!-- HTTP/1.0 column -->
  <text x="160" y="24" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTTP/1.0 (no keep-alive)</text>

  <!-- Connection 1 -->
  <rect x="20" y="36" width="280" height="62" rx="5" fill="#2d1a1a" stroke="#f85149" stroke-width="1"/>
  <text x="30" y="53" fill="#8b949e" font-size="10" font-family="sans-serif">TCP handshake</text>
  <text x="30" y="68" fill="#e6edf3" font-size="10" font-family="monospace">GET /index.html → 200</text>
  <text x="30" y="83" fill="#f85149" font-size="10" font-family="sans-serif">Connection closed</text>

  <!-- Connection 2 -->
  <rect x="20" y="106" width="280" height="62" rx="5" fill="#2d1a1a" stroke="#f85149" stroke-width="1"/>
  <text x="30" y="123" fill="#8b949e" font-size="10" font-family="sans-serif">TCP handshake (again)</text>
  <text x="30" y="138" fill="#e6edf3" font-size="10" font-family="monospace">GET /style.css  → 200</text>
  <text x="30" y="153" fill="#f85149" font-size="10" font-family="sans-serif">Connection closed</text>

  <!-- Connection 3 -->
  <rect x="20" y="176" width="280" height="62" rx="5" fill="#2d1a1a" stroke="#f85149" stroke-width="1"/>
  <text x="30" y="193" fill="#8b949e" font-size="10" font-family="sans-serif">TCP handshake (again)</text>
  <text x="30" y="208" fill="#e6edf3" font-size="10" font-family="monospace">GET /app.js     → 200</text>
  <text x="30" y="223" fill="#f85149" font-size="10" font-family="sans-serif">Connection closed</text>

  <text x="160" y="258" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">3 handshakes for 3 resources</text>

  <!-- HTTP/1.1 column -->
  <text x="510" y="24" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTTP/1.1 (keep-alive)</text>

  <!-- Single connection -->
  <rect x="370" y="36" width="290" height="202" rx="5" fill="#162420" stroke="#6db33f" stroke-width="1.5"/>
  <text x="390" y="56" fill="#8b949e" font-size="10" font-family="sans-serif">TCP handshake  (once)</text>
  <line x1="370" y1="66" x2="660" y2="66" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="4,3"/>
  <text x="390" y="86" fill="#e6edf3" font-size="10" font-family="monospace">GET /index.html → 200</text>
  <text x="390" y="116" fill="#e6edf3" font-size="10" font-family="monospace">GET /style.css  → 200</text>
  <text x="390" y="146" fill="#e6edf3" font-size="10" font-family="monospace">GET /app.js     → 200</text>
  <line x1="370" y1="160" x2="660" y2="160" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="4,3"/>
  <text x="390" y="180" fill="#8b949e" font-size="10" font-family="sans-serif">… more requests …</text>
  <text x="390" y="220" fill="#6db33f" font-size="10" font-family="sans-serif">Connection: close  (when done)</text>

  <text x="510" y="258" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">1 handshake for 3+ resources</text>
</svg>

Keep-alive pays the TCP handshake cost once; HTTP/1.0 pays it per request.

## 5. Runnable example

```js
// save as keep-alive.js — needs Node.js, no installs
const http = require("http");

// Track how many distinct socket connections are made
let socketCount = 0;

const server = http.createServer((req, res) => {
  res.setHeader("Content-Type", "text/plain");
  // Keep-alive is the default in HTTP/1.1 — but we can set the policy explicitly
  res.setHeader("Keep-Alive", "timeout=5, max=100");
  res.end("Response for " + req.url);
});

server.on("connection", () => {
  socketCount++;
  console.log(`[server] new TCP connection opened (total: ${socketCount})`);
});

server.listen(3000, () => {
  // --- Test 1: Keep-alive (default) — agent reuses connections ---
  console.log("\n=== Test 1: keep-alive (default http.Agent) ===");
  const keepAliveAgent = new http.Agent({ keepAlive: true, maxSockets: 1 });
  const socketsBefore = socketCount;

  const requests = ["/a", "/b", "/c"].map(
    (path) =>
      new Promise((resolve) => {
        http.get({ hostname: "localhost", port: 3000, path, agent: keepAliveAgent }, (res) => {
          res.resume(); // drain response so socket can be reused
          res.on("end", resolve);
        });
      })
  );

  Promise.all(requests).then(() => {
    console.log(`Connections used for 3 requests (keep-alive): ${socketCount - socketsBefore}`);
    keepAliveAgent.destroy();

    // --- Test 2: No keep-alive — new connection per request ---
    console.log("\n=== Test 2: no keep-alive (agent: false) ===");
    const socketsBefore2 = socketCount;

    const requests2 = ["/x", "/y", "/z"].map(
      (path) =>
        new Promise((resolve) => {
          http.get({ hostname: "localhost", port: 3000, path, agent: false }, (res) => {
            res.resume();
            res.on("end", resolve);
          });
        })
    );

    Promise.all(requests2).then(() => {
      console.log(`Connections used for 3 requests (no keep-alive): ${socketCount - socketsBefore2}`);
      server.close();
    });
  });
});
```

**How to run:** `node keep-alive.js` — built-in `http`, no npm.

## 6. Walkthrough

- `server.on("connection", ...)` — fires once per new TCP socket; `socketCount` lets us count actual connections regardless of HTTP activity.
- `new http.Agent({ keepAlive: true, maxSockets: 1 })` — Node's HTTP agent manages a pool of reusable sockets. `keepAlive: true` tells it not to close sockets after a request. `maxSockets: 1` forces sequential reuse (one socket max) so the count is clear.
- `res.resume()` — drains the response body; if the body isn't consumed, the socket can't be reused because Node doesn't know the response is done.
- Test 1: 3 requests, ~1 new connection — the agent reused the same socket.
- `agent: false` — disables the shared agent; each `http.get` opens its own socket.
- Test 2: 3 requests, 3 new connections — one TCP handshake per request, HTTP/1.0 style.
- `keepAliveAgent.destroy()` — releases all pooled sockets; important in scripts or tests to allow clean exit.

## 7. Gotchas & takeaways

> Not consuming the response body (`res.resume()` or reading all `data` events) **prevents socket reuse**. If you make an HTTP request and ignore the body, the socket stays open and idle until timeout — you'll run out of sockets under load. Always fully consume responses.

> Keep-alive between a reverse proxy and your app server is often misconfigured. If Nginx upstream doesn't use keep-alive, every request pays a new TCP handshake to your Node/Go/Python process — this becomes the bottleneck under load, not your app code.

- HTTP/1.1 connections are **persistent by default** — no `Connection: keep-alive` needed; opt out with `Connection: close`.
- One TCP handshake amortised across many requests = faster page loads, less server load.
- Always drain response bodies; undrained responses block socket reuse.
- Use `http.Agent` with `keepAlive: true` in Node HTTP clients to get connection pooling.
- HTTP/2 goes further: one connection, many simultaneous streams, no head-of-line blocking.
