---
card: webdev
gi: 46
slug: head-of-line-blocking
title: Head-of-line blocking
---

## 1. What it is

**Head-of-line (HOL) blocking** is when one slow item at the front of a queue forces every item behind it to wait, even though those later items could otherwise be served immediately.

In HTTP there are two distinct layers where HOL blocking occurs:

1. **HTTP/1.1 application-layer HOL**: a slow response at the front of a pipelined sequence blocks faster responses behind it. Each HTTP/1.1 connection can only deliver responses in order.
2. **TCP transport-layer HOL**: even inside HTTP/2's "fixed" multiplexing, a single lost TCP packet freezes *all* streams on that connection until the packet is retransmitted and reordered. This is why HTTP/3/QUIC was invented.

## 2. Why & when

Every web page loads dozens of independent resources. If any of them is slow, naive queuing makes *everything* slow. Understanding HOL blocking explains:

- Why browsers open **6 parallel connections** per origin in HTTP/1.1 (a workaround).
- Why **HTTP/2 multiplexing** looks like magic (it fixes application-layer HOL).
- Why **HTTP/3** still matters even though HTTP/2 looks like it solved the problem (TCP HOL remains).

You will encounter this term in CDN documentation, browser network panels, and performance post-mortems ("the slow font was at the head of the pipeline").

## 3. Core concept

Analogy: a one-lane road at a car wash. Every car must go through in order. A car with a broken windshield wiper that needs extra scrubbing holds up every car behind it — even the ones that only need a quick rinse and are perfectly ready to exit. The narrow lane is the bottleneck.

**HTTP/1.1 HOL (application layer):**

```
Connection pipe  →  [slow.jpg (200ms)] [fast.css (5ms)] [tiny.js (5ms)]

Timeline:
0ms   →  slow.jpg starts
200ms →  slow.jpg finishes
205ms →  fast.css finishes  (had to wait 200ms!)
210ms →  tiny.js finishes
```

**HTTP/2 fixes this** by assigning each request its own *stream* inside one TCP connection. Responses arrive independently. But:

**TCP HOL (transport layer):**

```
TCP packet 7 lost → retransmit needed
All HTTP/2 streams stall until packet 7 arrives
(even if stream 2's data was in packet 8 and arrived fine)
```

TCP's in-order delivery guarantee is the root cause. QUIC (the transport under HTTP/3) has independent streams at the transport level, so a lost packet only stalls the one stream that owns that data.

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Head-of-line blocking: slow request at front stalls faster requests behind it in HTTP/1.1">
  <defs>
    <marker id="a46" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b46" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c46" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- HTTP/1.1 HOL -->
  <text x="20" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">HTTP/1.1 — head-of-line blocking</text>
  <rect x="20" y="32" width="70" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="55" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="200" y="32" width="70" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <!-- 3 pipelined requests -->
  <line x1="90" y1="60" x2="198" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a46)"/>
  <text x="144" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET slow.jpg</text>
  <line x1="90" y1="72" x2="198" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a46)"/>
  <text x="144" y="68" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET fast.css</text>
  <line x1="90" y1="84" x2="198" y2="84" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a46)"/>
  <text x="144" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET tiny.js</text>

  <!-- slow.jpg takes long -->
  <rect x="200" y="92" width="8" height="80" rx="2" fill="#f85149" opacity="0.7"/>
  <text x="215" y="105" fill="#f85149" font-size="10" font-family="sans-serif">slow.jpg processing…</text>
  <!-- blocked indicator -->
  <rect x="20" y="96" width="88" height="76" rx="4" fill="#f85149" opacity="0.12" stroke="#f85149" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="64" y="133" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">BLOCKED</text>
  <text x="64" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">fast.css &amp; tiny.js</text>
  <text x="64" y="162" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">must wait</text>

  <!-- slow response finally -->
  <line x1="200" y1="175" x2="92" y2="175" stroke="#f85149" stroke-width="2" marker-end="url(#c46)"/>
  <text x="148" y="170" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">slow.jpg (200ms later)</text>
  <!-- fast responses now allowed -->
  <line x1="200" y1="190" x2="92" y2="190" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b46)"/>
  <text x="148" y="186" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">fast.css</text>
  <line x1="200" y1="205" x2="92" y2="205" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b46)"/>
  <text x="148" y="201" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">tiny.js</text>

  <!-- HTTP/2 multiplexing comparison -->
  <text x="380" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">HTTP/2 — no app-layer HOL</text>
  <rect x="380" y="32" width="70" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="415" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="570" y="32" width="70" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="605" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>
  <!-- streams -->
  <line x1="450" y1="62" x2="568" y2="62" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a46)"/>
  <text x="508" y="57" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">stream 1: slow.jpg</text>
  <line x1="450" y1="76" x2="568" y2="76" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a46)"/>
  <text x="508" y="71" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">stream 2: fast.css</text>
  <!-- fast responses come back without waiting -->
  <line x1="570" y1="100" x2="452" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b46)"/>
  <text x="510" y="95" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">fast.css (5ms)</text>
  <line x1="570" y1="170" x2="452" y2="170" stroke="#f85149" stroke-width="1.5" marker-end="url(#c46)"/>
  <text x="510" y="165" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">slow.jpg (200ms)</text>
  <text x="510" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">responses arrive independently</text>
</svg>

HTTP/1.1 (left): `fast.css` is stuck behind `slow.jpg` on the single pipe. HTTP/2 (right): each resource travels its own stream and arrives as soon as it's ready.

## 5. Runnable example

This demo simulates HOL blocking by running two HTTP/1.1 requests in series (the blocking scenario) and shows how much time `fast.css` wastes waiting for `slow.jpg`.

```js
// save as hol-demo.js  —  node hol-demo.js  (no installs)
const http = require("http");

const DELAYS = { "/slow.jpg": 200, "/fast.css": 5, "/tiny.js": 5 };

const server = http.createServer((req, res) => {
  const delay = DELAYS[req.url] || 0;
  setTimeout(() => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(`${req.url} done`);
  }, delay);
});

server.listen(3300, () => {
  const start = Date.now();
  const ms = () => (Date.now() - start) + "ms";

  // Serial on one connection — head-of-line blocking in effect
  function serial(paths, idx, done) {
    if (idx >= paths.length) return done();
    const path = paths[idx];
    http.get({ hostname: "localhost", port: 3300, path }, (res) => {
      res.resume();
      res.on("end", () => {
        console.log(`${path} arrived at ${ms()}`);
        serial(paths, idx + 1, done);
      });
    }).end();
  }

  console.log("=== Serial (HOL blocking) ===");
  serial(["/slow.jpg", "/fast.css", "/tiny.js"], 0, () => {
    console.log("\n=== Parallel (workaround: 3 connections) ===");
    const start2 = Date.now();
    const ms2 = () => (Date.now() - start2) + "ms";
    let pending = 3;
    ["/slow.jpg", "/fast.css", "/tiny.js"].forEach((path) => {
      http.get({ hostname: "localhost", port: 3300, path }, (res) => {
        res.resume();
        res.on("end", () => {
          console.log(`${path} arrived at ${ms2()}`);
          if (--pending === 0) server.close();
        });
      }).end();
    });
  });
});
```

**How to run:** `node hol-demo.js` — compare when `fast.css` arrives in each scenario.

Expected output:
```
=== Serial (HOL blocking) ===
/slow.jpg arrived at ~200ms
/fast.css arrived at ~205ms   ← wasted 200ms waiting!
/tiny.js arrived at ~210ms

=== Parallel (workaround: 3 connections) ===
/fast.css arrived at ~6ms     ← no wait
/tiny.js arrived at ~6ms
/slow.jpg arrived at ~201ms
```

## 6. Walkthrough

- `DELAYS` maps paths to artificial processing time. `/slow.jpg` takes 200ms; CSS and JS take 5ms each.
- `serial()` calls requests one-at-a-time and only starts the next after `end` fires. This mimics strict HTTP/1.1 ordering — `fast.css` and `tiny.js` are blocked behind `slow.jpg`.
- The parallel version opens **three separate HTTP connections** simultaneously. This is exactly what browsers do (up to 6 per origin in HTTP/1.1): work around HOL blocking with parallelism at the connection level.
- Notice `fast.css` arrives at ~6ms in parallel vs ~205ms in serial — that 199ms difference is pure HOL blocking overhead.

## 7. Gotchas & takeaways

> HTTP/2 eliminates **application-layer** HOL blocking, but **transport-layer HOL blocking** (inside TCP) still exists. A single lost TCP packet freezes all HTTP/2 streams until it's retransmitted. On high-loss networks HTTP/2 can be slower than 6× parallel HTTP/1.1 connections for this reason.

> Browsers use 6 parallel connections per origin as a HOL workaround. Domain sharding (splitting assets across `cdn1.example.com`, `cdn2.example.com`) exploits this to get 12 connections — but HTTP/2 makes sharding harmful, not helpful.

- HOL blocking exists at two levels: HTTP application layer (fixed by HTTP/2) and TCP transport layer (fixed by HTTP/3/QUIC).
- The browser's 6-connection limit exists precisely because of HTTP/1.1 HOL blocking.
- In browser DevTools (Network tab), look for responses that start late despite the server being fast — that's HOL blocking.
- HTTP/2 multiplexing makes HOL blocking a non-issue for most production traffic, but packet loss on mobile networks can still surface TCP HOL blocking.
