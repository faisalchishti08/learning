---
card: webdev
gi: 47
slug: http-2-multiplexing-header-compression-server-push
title: HTTP/2 (multiplexing, header compression, server push)
---

## 1. What it is

**HTTP/2** (RFC 7540, 2015) is a complete reimplementation of HTTP's wire format that keeps the same semantics (methods, headers, status codes) but changes how bytes travel between client and server. Three headline features:

- **Multiplexing:** many independent requests and responses travel concurrently over a *single* TCP connection on numbered *streams*. No more one-at-a-time queuing or multiple parallel connections.
- **Header compression (HPACK):** headers are compressed using a shared dynamic table and Huffman coding. Sending `Cookie: <large-token>` once; subsequent requests reference the table entry instead of repeating the whole string.
- **Server push:** the server can proactively send resources the client hasn't asked for yet (e.g., send `style.css` at the same time as `index.html`, before the browser parses the `<link>` tag).

HTTP/2 is **binary**, not text. The readable `GET /path HTTP/1.1` format is replaced by binary frames.

## 2. Why & when

HTTP/1.1 has three expensive habits:
1. Requests block each other on one connection (HOL blocking).
2. Each request repeats the same large headers — `User-Agent`, `Cookie`, `Accept-Encoding` are sent verbatim every time.
3. The client can't receive a resource until it discovers it needs it (parse HTML → find `<link>` → request CSS).

HTTP/2 fixes all three. Adoption crossed 50% of web traffic around 2020. All major CDNs and browsers support it. You typically enable it by configuring your web server (Nginx, Caddy, etc.) — Node's `node:http2` module also supports it natively.

Use it when you want better performance without changing application code. HTTP/1.1 optimisations like domain sharding and CSS sprites *hurt* performance on HTTP/2.

## 3. Core concept

Think of HTTP/1.1 as a single-lane highway where each car (request) must wait for the car ahead. HTTP/2 builds a multi-lane highway on the same physical road: each lane is a **stream**, independently numbered (1, 3, 5… odd numbers for client-initiated). All streams share one TCP connection.

**Frames:** data is split into binary frames, each tagged with a stream ID. The server interleaves frames from different streams:

```
[stream 1: HEADERS frame] [stream 3: HEADERS frame] [stream 5: HEADERS frame]
[stream 3: DATA frame]    [stream 1: DATA frame]     [stream 5: DATA frame]
```

**HPACK compression:** client and server each maintain an identical header table. Instead of `User-Agent: Mozilla/5.0 (compatible...)` on every request, the client sends a one-byte index like `62` meaning "use table entry 62." Headers added in one request can be referenced in the next.

**Server push:** the server sends a `PUSH_PROMISE` frame naming a resource it's about to push, then sends the resource data on a new stream. The client can reject pushes it doesn't want with a `RST_STREAM`.

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP/2 multiplexing: multiple streams interleaved on one TCP connection, plus HPACK header table and server push">
  <defs>
    <marker id="a47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#d29922"/></marker>
  </defs>

  <!-- TCP pipe background -->
  <rect x="160" y="20" width="340" height="260" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="5,3"/>
  <text x="330" y="15" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">one TCP connection</text>

  <!-- Client box -->
  <rect x="20" y="110" width="130" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="148" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="85" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HPACK table</text>

  <!-- Server box -->
  <rect x="530" y="110" width="130" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="148" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="595" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HPACK table</text>

  <!-- Streams (requests going right) -->
  <line x1="150" y1="130" x2="528" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#a47)"/>
  <text x="340" y="124" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">stream 1: GET /index.html</text>
  <line x1="150" y1="148" x2="528" y2="148" stroke="#6db33f" stroke-width="2" marker-end="url(#a47)"/>
  <text x="340" y="143" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">stream 3: GET /app.js</text>
  <line x1="150" y1="166" x2="528" y2="166" stroke="#6db33f" stroke-width="2" marker-end="url(#a47)"/>
  <text x="340" y="161" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">stream 5: GET /logo.png</text>

  <!-- Responses (going left) interleaved -->
  <line x1="530" y1="185" x2="152" y2="185" stroke="#79c0ff" stroke-width="2" marker-end="url(#b47)"/>
  <text x="340" y="180" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">stream 3 response (app.js, fast)</text>
  <line x1="530" y1="200" x2="152" y2="200" stroke="#79c0ff" stroke-width="2" marker-end="url(#b47)"/>
  <text x="340" y="195" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">stream 5 response (logo, fast)</text>
  <line x1="530" y1="215" x2="152" y2="215" stroke="#79c0ff" stroke-width="2" marker-end="url(#b47)"/>
  <text x="340" y="210" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">stream 1 response (index, slow)</text>

  <!-- Server push -->
  <line x1="530" y1="240" x2="152" y2="240" stroke="#d29922" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#c47)"/>
  <text x="340" y="235" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">PUSH stream 2: style.css (unsolicited)</text>

  <!-- HPACK annotation -->
  <rect x="20" y="215" width="130" height="50" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="85" y="233" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HPACK: headers compressed</text>
  <text x="85" y="248" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Cookie: (sent once → idx)</text>
  <text x="85" y="263" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">~30-40% savings typical</text>
</svg>

Three streams travel concurrently in both directions; a server push (gold, dashed) delivers `style.css` before the client knew it needed it.

## 5. Runnable example

Node's built-in `node:http2` module lets you run an HTTP/2 server and client locally.

```js
// save as http2-demo.js  —  node http2-demo.js  (no installs; Node 10+)
const http2 = require("node:http2");

// HTTP/2 cleartext (h2c) server — no TLS needed for localhost testing
const server = http2.createServer();

server.on("stream", (stream, headers) => {
  const path = headers[":path"];
  console.log(`Server: stream ${stream.id}  path=${path}`);

  if (path === "/index.html") {
    // Server push style.css before client asks
    stream.pushStream({ ":path": "/style.css" }, (err, pushStream) => {
      if (!err) {
        pushStream.respond({ ":status": 200, "content-type": "text/css" });
        pushStream.end("body { margin: 0 }");
        console.log("Server: pushed /style.css on stream", pushStream.id);
      }
    });
  }

  stream.respond({ ":status": 200, "content-type": "text/plain" });
  stream.end(`Hello from ${path}`);
});

server.listen(3400, () => {
  const client = http2.connect("http://localhost:3400");

  // Request 3 resources concurrently — all on one TCP connection
  const paths = ["/index.html", "/app.js", "/logo.png"];
  let done = 0;

  // Listen for server pushes
  client.on("stream", (pushStream, headers) => {
    let body = "";
    pushStream.on("data", (c) => (body += c));
    pushStream.on("end", () =>
      console.log(`Client: received PUSH ${headers[":path"]}: "${body}"`)
    );
  });

  paths.forEach((p) => {
    const req = client.request({ ":path": p });
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      console.log(`Client: ${p} → "${body}"`);
      if (++done === paths.length) {
        setTimeout(() => { client.close(); server.close(); }, 100);
      }
    });
    req.end();
  });
});
```

**How to run:** `node http2-demo.js` — all requests share one connection; observe the pushed stream arriving.

## 6. Walkthrough

- `http2.createServer()` — creates an h2c (cleartext) HTTP/2 server. Browsers require TLS (`createSecureServer`), but h2c works fine for Node-to-Node demos.
- `server.on("stream", ...)` — fires for each new stream (each request). `headers[":path"]` is the pseudo-header HTTP/2 uses instead of the HTTP/1.1 request line.
- `stream.pushStream({":path": "/style.css"}, ...)` — initiates a server push. The client receives this as a new `stream` event on its session *before* the main response finishes.
- `http2.connect("http://localhost:3400")` — opens one HTTP/2 session (one TCP connection). All three `client.request()` calls share it — no new connections.
- `client.on("stream", ...)` — the push arrives here; the client receives `/style.css` without having requested it.
- `req.end()` in client code — signals "no request body"; required even for GET requests in the http2 API.

## 7. Gotchas & takeaways

> **Server push is largely deprecated.** Chrome removed it in 2022. The `103 Early Hints` response code is the modern replacement for preloading critical resources. Don't build new features that rely on server push.

> **Multiplexing helps most when there are many small resources.** For a single large download (video, large binary) HTTP/2 multiplexing buys nothing over HTTP/1.1.

> HTTP/2 still uses TCP, which means TCP head-of-line blocking remains. On high-packet-loss mobile networks HTTP/2 can be slower than many parallel HTTP/1.1 connections. HTTP/3 fixes this.

- HTTP/2 is binary on the wire — you can't `telnet` or `curl -v` and read it. Use `curl --http2 -v` which decodes frames for you.
- HPACK saves the most on repetitive headers like `Cookie`, `Authorization`, and custom headers sent on every request.
- Domain sharding and CSS sprites hurt HTTP/2 performance — they were HTTP/1.1 workarounds for HOL blocking and parallel connection limits that no longer apply.
- Stream priorities (`PRIORITY` frame) let the client hint which resources are most important, but browser implementations vary.
- Node's `http2` module is built-in — `require("node:http2")`, no npm package needed.
