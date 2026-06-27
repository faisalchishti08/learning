---
card: webdev
gi: 33
slug: http-response-structure-status-line-headers-body
title: HTTP response structure (status line, headers, body)
---

## 1. What it is

An HTTP response is the server's answer to a client's request. It has the same three-section shape as a request but with different fields:

1. **Status line** — HTTP version + a numeric status code + a short reason phrase (e.g. `HTTP/1.1 200 OK`).
2. **Headers** — metadata the server attaches: content type, length, caching rules, cookies to set.
3. **Body** — the actual content: HTML, JSON, an image, a file download, or nothing at all.

## 2. Why & when

The status line is the first thing a client checks — before reading a single header or byte of body. A `200` means "here's your data", a `301` means "go look somewhere else", a `404` means "that doesn't exist". Without a machine-readable status code the client would have to guess. Understanding the response structure helps when:

- Reading server logs (`GET /page 200 1234` — method, path, status, bytes).
- Debugging failed API calls (is the body an error message? what does the status code say?).
- Implementing caching (`Cache-Control`, `ETag`, `Last-Modified` all live in response headers).
- Setting cookies from the server (`Set-Cookie` is a response header).

## 3. Core concept

Analogy: the server's response is like a package delivery. The **shipping label** is the status line (this is your package, it's intact). The **packing slip** is the headers (what's inside, how fragile, return address). The **contents** are the body.

Raw response on the wire:

```
HTTP/1.1 200 OK\r\n
Content-Type: application/json\r\n
Content-Length: 27\r\n
\r\n
{"id":42,"name":"Alice"}
```

Rules:
- The blank line after headers is mandatory — same as in requests.
- Status codes are three digits: `1xx` informational, `2xx` success, `3xx` redirect, `4xx` client error, `5xx` server error.
- The reason phrase (`OK`, `Not Found`) is informational only — parsers rely on the number.
- A response can have **no body** (e.g. `204 No Content`, `304 Not Modified`). `Content-Length: 0` or no body at all.

## 4. Diagram

<svg viewBox="0 0 660 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomy of an HTTP response showing status line, headers, blank line, and body">
  <rect x="40" y="20" width="580" height="260" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="14" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace" font-weight="bold">HTTP Response</text>

  <!-- Status line -->
  <rect x="60" y="36" width="540" height="38" rx="6" fill="#223344"/>
  <text x="80" y="58" fill="#6db33f" font-size="13" font-family="monospace">HTTP/1.1 200 OK</text>
  <text x="560" y="58" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="end">← status line (version + code + reason)</text>

  <!-- Headers -->
  <rect x="60" y="82" width="540" height="104" rx="6" fill="#161d27"/>
  <text x="80" y="102" fill="#79c0ff" font-size="12" font-family="monospace">Content-Type: application/json</text>
  <text x="80" y="120" fill="#79c0ff" font-size="12" font-family="monospace">Content-Length: 27</text>
  <text x="80" y="138" fill="#79c0ff" font-size="12" font-family="monospace">Cache-Control: max-age=3600</text>
  <text x="80" y="156" fill="#79c0ff" font-size="12" font-family="monospace">Set-Cookie: session=abc; HttpOnly</text>
  <text x="560" y="130" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="end">← headers</text>

  <!-- Blank line -->
  <rect x="60" y="194" width="540" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="4,3"/>
  <text x="330" y="209" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">(blank line)</text>

  <!-- Body -->
  <rect x="60" y="224" width="540" height="36" rx="6" fill="#223344"/>
  <text x="80" y="246" fill="#e6edf3" font-size="12" font-family="monospace">{"id":42,"name":"Alice"}</text>
  <text x="560" y="246" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="end">← body</text>
</svg>

The status line tells the client immediately whether the request succeeded before it reads anything else.

## 5. Runnable example

```js
// save as response-demo.js — needs Node.js, no installs
const http = require("http");

const server = http.createServer((req, res) => {
  if (req.url === "/data") {
    // 200 with JSON body
    const payload = JSON.stringify({ id: 42, name: "Alice" });
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(payload),
      "Cache-Control": "max-age=3600",
    });
    res.end(payload);
  } else if (req.url === "/gone") {
    // 301 redirect — body is optional but helpful for old browsers
    res.writeHead(301, { Location: "/data" });
    res.end();
  } else {
    // 404 with plain-text body
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found");
  }
});

server.listen(3000, () => {
  // Request /data
  http.get("http://localhost:3000/data", (res) => {
    let body = "";
    res.on("data", (c) => (body += c));
    res.on("end", () => {
      console.log("Status:", res.statusCode);
      console.log("Content-Type:", res.headers["content-type"]);
      console.log("Body:", body);
      server.close();
    });
  });
});
```

**How to run:** `node response-demo.js` — built-in `http`, no npm.

## 6. Walkthrough

- `res.writeHead(200, {...})` — sets the status line (`200`) and all response headers in one call. Must be called before `res.end()`.
- `"Content-Type": "application/json"` — tells the client what format the body is in. Without this, browsers guess (and sometimes guess wrong).
- `"Content-Length": Buffer.byteLength(payload)` — byte count, not character count; lets the client know when the body ends.
- `"Cache-Control": "max-age=3600"` — response header telling the browser it can cache this response for 3600 seconds without re-requesting.
- `res.end(payload)` — sends the body and closes the response. Calling `end` with an argument is equivalent to `write(payload)` + `end()`.
- `301` with `Location: "/data"` — a redirect: client immediately re-requests the new URL. Body is sent but browsers don't display it.
- `res.statusCode` on the client side — the numeric code parsed from the status line.
- `res.headers["content-type"]` — all response headers are accessible as a lowercase-keyed object.

## 7. Gotchas & takeaways

> Calling `res.write()` or `res.end()` **before** `res.writeHead()` locks in a `200` status automatically. If you forget `writeHead` on an error path, the client sees `200` even though you sent an error message in the body.

> `Content-Length` should match the body in bytes. If you set it shorter than the actual body, the client truncates. If longer, the client hangs waiting for bytes that never arrive.

- Three parts: **status line**, **headers**, **body** — blank line between headers and body.
- The status **number** drives client behaviour; the reason phrase is decorative.
- `2xx` = success, `3xx` = redirect, `4xx` = your fault (client), `5xx` = server's fault.
- Response headers are where cookies, caching, content type, and CORS rules live.
- A `204 No Content` response has no body and no `Content-Length` at all.
