---
card: webdev
gi: 45
slug: http-1-1-persistent-connections-pipelining
title: HTTP/1.1 persistent connections & pipelining
---

## 1. What it is

HTTP/1.1 introduced two performance features that let clients squeeze more work out of a single TCP connection:

**Persistent connections** (also called keep-alive): after the server sends a response, the TCP connection *stays open*. The client can send the next request immediately without a new TCP handshake. This is the **default** in HTTP/1.1 — you have to explicitly opt out with `Connection: close`.

**Pipelining**: instead of waiting for response 1 before sending request 2, the client fires several requests in a row down the same connection *without waiting*. The server processes them and sends responses *in the same order*. This further reduces idle time.

Both features target the same enemy: **latency wasted on connection setup**. A TCP handshake costs at minimum one round-trip (client→server→client); a TLS handshake adds one or two more. On a page with 50 assets that penalty adds up fast.

## 2. Why & when

Before HTTP/1.1, every request opened a brand-new TCP connection. Browsers worked around this with **parallel connections** — opening 6–8 sockets to the same host simultaneously. That worked but wastes server file descriptors and amplifies congestion.

Persistent connections remove the need for as many parallel sockets. Pipelining takes the next step: instead of the classic stop-and-wait rhythm:

```
send req1 → wait → recv res1 → send req2 → wait → recv res2 ...
```

Pipelining makes it:

```
send req1, req2, req3 → recv res1, res2, res3
```

In practice, **pipelining is disabled in most browsers** because many proxies and servers don't implement the response-ordering requirement correctly — they silently reorder or drop responses. HTTP/2 multiplexing (the next topic) solves the same problem properly.

## 3. Core concept

Analogy: imagine ordering at a coffee bar. Without persistent connections you walk in, order, get your coffee, leave, and come back in through the queue for each additional item. With persistent connections you stay at the counter. With pipelining you shout "latte, then croissant, then sparkling water" all at once; the barista still makes them in order and slides them to you one by one.

The key constraint: **responses must be returned in the same order as requests**. The server can't mix them up. This serial ordering is what causes the head-of-line blocking problem (covered in the next tutorial).

```
Client                  Server
  |-- GET /style.css -->  |
  |-- GET /app.js   -->   |   (pipelined, no wait)
  |-- GET /logo.png -->   |
  |                       | [processes in order]
  |<-- 200 style.css ---  |
  |<-- 200 app.js ------  |
  |<-- 200 logo.png ----  |
```

**Connection management headers:**

| Header | Meaning |
|---|---|
| `Connection: keep-alive` | HTTP/1.0 opt-in (1.1 default) |
| `Connection: close` | close after this response |
| `Keep-Alive: timeout=5, max=100` | optional idle timeout & request limit |

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of serial requests versus pipelined requests on a persistent connection">
  <defs>
    <marker id="a45" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b45" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Serial (left) -->
  <text x="20" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">Serial (no pipeline)</text>
  <rect x="20" y="30" width="60" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="50" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="180" y="30" width="60" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <!-- req1 -->
  <line x1="80" y1="62" x2="178" y2="62" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>
  <text x="128" y="57" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">req 1</text>
  <!-- res1 -->
  <line x1="180" y1="80" x2="82" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b45)"/>
  <text x="130" y="95" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">res 1</text>
  <!-- req2 -->
  <line x1="80" y1="110" x2="178" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>
  <text x="128" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">req 2 (waited)</text>
  <!-- res2 -->
  <line x1="180" y1="128" x2="82" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b45)"/>
  <text x="130" y="143" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">res 2</text>
  <!-- req3 -->
  <line x1="80" y1="158" x2="178" y2="158" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>
  <text x="128" y="153" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">req 3 (waited)</text>
  <!-- res3 -->
  <line x1="180" y1="176" x2="82" y2="176" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b45)"/>
  <text x="130" y="191" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">res 3</text>
  <!-- idle annotation -->
  <rect x="82" y="82" width="96" height="26" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="130" y="99" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">idle (waiting)</text>

  <!-- Pipelined (right) -->
  <text x="380" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">Pipelined</text>
  <rect x="380" y="30" width="60" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="410" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="560" y="30" width="60" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="590" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <!-- 3 requests back-to-back -->
  <line x1="440" y1="58" x2="558" y2="58" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>
  <text x="498" y="53" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">req 1</text>
  <line x1="440" y1="72" x2="558" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>
  <text x="498" y="68" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">req 2</text>
  <line x1="440" y1="86" x2="558" y2="86" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>
  <text x="498" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">req 3</text>

  <!-- responses in order -->
  <line x1="560" y1="110" x2="442" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b45)"/>
  <text x="500" y="106" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">res 1</text>
  <line x1="560" y1="126" x2="442" y2="126" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b45)"/>
  <text x="500" y="122" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">res 2</text>
  <line x1="560" y1="142" x2="442" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b45)"/>
  <text x="500" y="138" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">res 3</text>
  <text x="490" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no idle gaps between requests</text>
</svg>

Pipelining (right) fires all three requests before any response arrives, eliminating the idle gaps that serial requests (left) waste on waiting.

## 5. Runnable example

This Node.js demo creates a server and two clients: one serial, one that sends pipelined requests over a raw TCP socket.

```js
// save as pipeline.js  —  node pipeline.js  (no installs)
const http = require("http");
const net  = require("net");

const server = http.createServer((req, res) => {
  const delay = req.url === "/slow" ? 80 : 0;
  setTimeout(() => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(`Response for ${req.url}`);
  }, delay);
});

server.listen(3200, () => {
  console.log("--- Persistent connection (serial) ---");
  makeSerialRequests(() => {
    console.log("\n--- Pipelined requests (raw TCP) ---");
    makePipelinedRequests(() => server.close());
  });
});

function makeSerialRequests(done) {
  const options = { hostname: "localhost", port: 3200, path: "/first", method: "GET",
                    headers: { Connection: "keep-alive" } };
  const t0 = Date.now();
  const req1 = http.request(options, (res1) => {
    res1.resume();
    res1.on("end", () => {
      console.log(`req /first done at ${Date.now() - t0}ms`);
      // second request on same connection
      const req2 = http.request({ ...options, path: "/second" }, (res2) => {
        res2.resume();
        res2.on("end", () => {
          console.log(`req /second done at ${Date.now() - t0}ms`);
          done();
        });
      });
      req2.end();
    });
  });
  req1.end();
}

function makePipelinedRequests(done) {
  const t0 = Date.now();
  const socket = net.connect(3200, "localhost", () => {
    // Fire two requests without waiting for responses
    socket.write("GET /slow HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n");
    socket.write("GET /fast HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n");
    console.log(`Both requests sent at ${Date.now() - t0}ms`);
  });

  let buf = "", count = 0;
  socket.on("data", (chunk) => {
    buf += chunk.toString();
    const parts = buf.split("\r\n\r\n");
    while (parts.length > 1) {
      count++;
      const body = parts[1].split("\r\n")[0];
      console.log(`response ${count} body: "${body}" at ${Date.now() - t0}ms`);
      buf = parts.slice(2).join("\r\n\r\n");
      parts.splice(0, 2);
    }
  });
  socket.on("end", done);
}
```

**How to run:** `node pipeline.js` — compare the timing of serial vs pipelined requests.

## 6. Walkthrough

- `makeSerialRequests`: uses Node's `http.request` with `Connection: keep-alive`. After `res1` ends, a second `http.request` reuses the underlying socket transparently — the library manages the pool. This is persistent connections in action.
- `makePipelinedRequests`: drops to `net.connect` to write raw HTTP text, sending both requests before waiting for any response. This is pipelining: the server receives `/slow` and `/fast` in one TCP read.
- `delay` in the server handler: `/slow` takes 80ms while `/fast` is instant. Despite `/fast` finishing first, the pipelined responses still arrive *in request order* (`/slow` first, `/fast` second) because the server must not reorder them.
- The `parts.split("\r\n\r\n")` parsing splits headers from body. A robust parser would check `Content-Length` instead; this works here because both bodies are short and arrive in separate segments.

## 7. Gotchas & takeaways

> Pipelining requires responses **in the same order as requests**. If your slow request is first (e.g. `/slow` before `/fast`), the fast response is stuck waiting behind the slow one. This is **head-of-line blocking** — the next tutorial goes deep on it.

> Most browsers **never enable pipelining** because buggy proxy servers silently drop or reorder pipelined responses. HTTP/2 solves this properly with multiplexing; don't try to use HTTP/1.1 pipelining in production.

- HTTP/1.1 persistent connections are on by default — you opt *out* with `Connection: close`.
- Node's `http` module manages connection pooling automatically; you usually don't write the raw socket code shown above.
- The `Keep-Alive: timeout=N` header hints at how long to keep an idle socket alive — servers close idle connections to free resources.
- Each HTTP/1.1 connection still only carries one response at a time in practice; HTTP/2 is the real solution to concurrency.
