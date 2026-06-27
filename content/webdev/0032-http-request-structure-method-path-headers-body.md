---
card: webdev
gi: 32
slug: http-request-structure-method-path-headers-body
title: HTTP request structure (method, path, headers, body)
---

## 1. What it is

Every HTTP request is a text message with a strict structure made of four parts:

1. **Method** — what action the client wants (e.g. `GET`, `POST`).
2. **Path** — which resource on that server (e.g. `/users/42`).
3. **Headers** — metadata key/value pairs: who's asking, what format they accept, authentication tokens, etc.
4. **Body** — optional data sent *with* the request (a JSON payload when creating a user, a file being uploaded).

The server reads these four parts to decide what to do and how to respond.

## 2. Why & when

Before HTTP had a defined structure, every server invented its own wire format. The HTTP spec gave every client/server pair a shared grammar so any browser can talk to any server without custom negotiation. Understanding the structure matters whenever you:

- Debug network failures with browser DevTools or `curl -v`.
- Build an API and choose between putting data in the path vs. headers vs. body.
- Read server logs — they record method, path, and status in a standard layout.
- Work with authentication (the token goes in a header, not the URL).

## 3. Core concept

Think of a request like a formal letter. The **envelope** has the method and path (where it's going, what kind of letter), the **letterhead** is the headers (sender, date, format), and the **page content** is the body (what you actually want to say).

The raw text on the wire looks like this:

```
METHOD /path HTTP/1.1\r\n
Header-Name: value\r\n
Another-Header: value\r\n
\r\n
body goes here (optional)
```

The blank line (`\r\n`) is mandatory — it separates headers from body. The server reads until it finds that blank line, then knows headers are done and the body (if any) starts next.

Key rules:
- `GET` and `HEAD` requests conventionally have **no body**.
- `POST`, `PUT`, `PATCH` typically carry a body.
- Headers are case-insensitive (`content-type` = `Content-Type`).
- The path includes the query string: `/search?q=cats&page=2`.

## 4. Diagram

<svg viewBox="0 0 660 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomy of an HTTP request showing request line, headers, blank line, and body">
  <!-- Request box -->
  <rect x="40" y="20" width="580" height="270" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="14" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace" font-weight="bold">HTTP Request</text>

  <!-- Request line -->
  <rect x="60" y="36" width="540" height="38" rx="6" fill="#223344"/>
  <text x="80" y="58" fill="#6db33f" font-size="13" font-family="monospace">POST /api/users HTTP/1.1</text>
  <text x="560" y="58" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="end">← request line (method + path + version)</text>

  <!-- Headers -->
  <rect x="60" y="82" width="540" height="120" rx="6" fill="#161d27"/>
  <text x="80" y="102" fill="#79c0ff" font-size="12" font-family="monospace">Host: api.example.com</text>
  <text x="80" y="120" fill="#79c0ff" font-size="12" font-family="monospace">Content-Type: application/json</text>
  <text x="80" y="138" fill="#79c0ff" font-size="12" font-family="monospace">Authorization: Bearer eyJhbGc...</text>
  <text x="80" y="156" fill="#79c0ff" font-size="12" font-family="monospace">Content-Length: 27</text>
  <text x="560" y="138" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="end">← headers</text>

  <!-- Blank line -->
  <rect x="60" y="210" width="540" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="4,3"/>
  <text x="330" y="225" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">(blank line — separates headers from body)</text>

  <!-- Body -->
  <rect x="60" y="240" width="540" height="36" rx="6" fill="#223344"/>
  <text x="80" y="262" fill="#e6edf3" font-size="12" font-family="monospace">{"name":"Alice","age":30}</text>
  <text x="560" y="262" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="end">← body (optional)</text>
</svg>

The blank line is the separator; without it the server can't tell where headers end and body begins.

## 5. Runnable example

```js
// save as request-demo.js — needs Node.js, no installs
const http = require("http");

// Start a tiny server that echoes back what it received
const server = http.createServer((req, res) => {
  let body = "";
  req.on("data", (chunk) => (body += chunk));
  req.on("end", () => {
    console.log("=== Server saw ===");
    console.log("Method:", req.method);
    console.log("Path:  ", req.url);
    console.log("Headers:", JSON.stringify(req.headers, null, 2));
    console.log("Body:  ", body);
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Got it!");
  });
});

server.listen(3000, () => {
  // Send a POST with headers and a body
  const options = {
    hostname: "localhost",
    port: 3000,
    path: "/api/users",
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer token123",
      "Content-Length": Buffer.byteLength('{"name":"Alice"}'),
    },
  };

  const req = http.request(options, (res) => {
    res.on("data", () => {});
    res.on("end", () => server.close());
  });

  req.write('{"name":"Alice"}');
  req.end();
});
```

**How to run:** `node request-demo.js` (Node.js built-in `http` — no npm install).

## 6. Walkthrough

- `http.createServer(...)` — server prints each part of the incoming request so you can see the four pieces arrive separately.
- `req.method` — the HTTP verb the client sent (`POST`).
- `req.url` — the path portion, here `/api/users`.
- `req.headers` — an object with all headers lowercased; Node normalises them.
- `body` — assembled from `data` chunks; only non-empty because we called `req.write(...)`.
- `options.headers["Content-Length"]` — we must tell the server how many bytes the body is so it knows when the body ends; `Buffer.byteLength` gives the exact byte count (not character count).
- `req.write(...)` sends the body bytes; `req.end()` signals no more data.

## 7. Gotchas & takeaways

> Never put secrets (tokens, passwords) in the **URL path or query string** — URLs appear in server logs, browser history, and `Referer` headers. Secrets belong in the `Authorization` header sent over HTTPS.

> `Content-Length` must match the actual byte length, not the character count. Emoji and non-ASCII characters can be 2–4 bytes each. Use `Buffer.byteLength(str)` in Node, not `str.length`.

- Four parts: **method**, **path**, **headers**, **body**. The blank line between headers and body is mandatory.
- Headers are key/value metadata; they don't change the resource itself, only describe the request.
- `GET` has no body by convention — query data goes in the URL instead.
- `Host` header is required in HTTP/1.1 so the server knows which virtual host is being addressed.
- Read requests raw in `curl -v` to build intuition for what the browser actually sends.
