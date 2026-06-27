---
card: webdev
gi: 38
slug: request-vs-response-vs-entity-headers
title: Request vs response vs entity headers
---

## 1. What it is

HTTP headers are grouped by where they belong in a conversation:

- **Request headers** — sent only by the client in a request. Describe the client, its capabilities, and what it wants.
- **Response headers** — sent only by the server in a response. Describe the server, the result, and directives for the client.
- **Representation (entity) headers** — describe the *body* itself. Can appear in both requests and responses because both can carry a body.

(Note: HTTP/1.1 spec uses the term *entity headers*; HTTP/2 and later use *representation headers* — same concept, newer name.)

## 2. Why & when

Understanding which type a header belongs to tells you:

- Where to put it. Putting `Authorization` on a response, or `WWW-Authenticate` on a request, makes no sense — clients reject or ignore it.
- What went wrong when a request fails. `406 Not Acceptable` means the server can't satisfy the `Accept` header (a request header). `415 Unsupported Media Type` means the server can't parse the `Content-Type` (an entity header). Two different problems, two different fixes.
- How to implement a server correctly. Response headers like `Cache-Control` and `Set-Cookie` go on the server's reply; request headers like `If-None-Match` go on the browser's re-request.

## 3. Core concept

Think of it like a phone call. **Request headers** are what the caller says before you pick up the phone (caller ID, ringback tone preference). **Response headers** are what you say as you answer ("this is Alice, I'm available until 5 pm"). **Entity headers** describe the message content being passed back and forth during the actual conversation ("the document I'm faxing is 4 pages, encoded in A4 landscape").

**Common request headers:**

| Header | What it says |
|--------|-------------|
| `Host` | Which server hostname the client wants (required in HTTP/1.1) |
| `Accept` | Preferred response format |
| `Accept-Encoding` | Compression the client supports (`gzip`, `br`) |
| `Authorization` | Client's credentials |
| `User-Agent` | What software is making the request |
| `If-None-Match` | Conditional: only respond if resource changed |
| `Cookie` | Sends stored cookies back to the server |

**Common response headers:**

| Header | What it says |
|--------|-------------|
| `Location` | URL to redirect to (3xx) or URL of new resource (201) |
| `WWW-Authenticate` | Auth challenge (401) |
| `Set-Cookie` | Instructs client to store a cookie |
| `Cache-Control` | Caching rules for this response |
| `Access-Control-Allow-Origin` | CORS: who may read this response |
| `Server` | Server software name |

**Common entity/representation headers (both directions):**

| Header | What it says |
|--------|-------------|
| `Content-Type` | Format of the body |
| `Content-Length` | Byte count of the body |
| `Content-Encoding` | Compression applied to the body (`gzip`) |
| `Content-Language` | Human language of the body (`en-US`) |

## 4. Diagram

<svg viewBox="0 0 680 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three columns showing request-only, response-only, and shared entity headers">
  <rect width="680" height="320" fill="#0d1117"/>

  <!-- Client box -->
  <rect x="20"  y="20" width="190" height="270" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Request headers</text>
  <text x="115" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(client → server)</text>
  <text x="35"  y="84" fill="#e6edf3" font-size="11" font-family="monospace">Host</text>
  <text x="35"  y="104" fill="#e6edf3" font-size="11" font-family="monospace">Accept</text>
  <text x="35"  y="124" fill="#e6edf3" font-size="11" font-family="monospace">Accept-Encoding</text>
  <text x="35"  y="144" fill="#e6edf3" font-size="11" font-family="monospace">Authorization</text>
  <text x="35"  y="164" fill="#e6edf3" font-size="11" font-family="monospace">User-Agent</text>
  <text x="35"  y="184" fill="#e6edf3" font-size="11" font-family="monospace">Cookie</text>
  <text x="35"  y="204" fill="#e6edf3" font-size="11" font-family="monospace">If-None-Match</text>
  <text x="35"  y="224" fill="#e6edf3" font-size="11" font-family="monospace">Referer</text>

  <!-- Entity / shared column -->
  <rect x="242" y="20" width="194" height="270" rx="8" fill="#162420" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="339" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Entity headers</text>
  <text x="339" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(both directions)</text>
  <text x="258" y="84" fill="#e6edf3" font-size="11" font-family="monospace">Content-Type</text>
  <text x="258" y="104" fill="#e6edf3" font-size="11" font-family="monospace">Content-Length</text>
  <text x="258" y="124" fill="#e6edf3" font-size="11" font-family="monospace">Content-Encoding</text>
  <text x="258" y="144" fill="#e6edf3" font-size="11" font-family="monospace">Content-Language</text>
  <text x="258" y="164" fill="#e6edf3" font-size="11" font-family="monospace">Content-Range</text>
  <text x="258" y="184" fill="#e6edf3" font-size="11" font-family="monospace">Last-Modified</text>
  <text x="258" y="204" fill="#e6edf3" font-size="11" font-family="monospace">ETag</text>

  <!-- Response headers -->
  <rect x="468" y="20" width="190" height="270" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="563" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Response headers</text>
  <text x="563" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(server → client)</text>
  <text x="484" y="84" fill="#e6edf3" font-size="11" font-family="monospace">Location</text>
  <text x="484" y="104" fill="#e6edf3" font-size="11" font-family="monospace">Set-Cookie</text>
  <text x="484" y="124" fill="#e6edf3" font-size="11" font-family="monospace">Cache-Control</text>
  <text x="484" y="144" fill="#e6edf3" font-size="11" font-family="monospace">WWW-Authenticate</text>
  <text x="484" y="164" fill="#e6edf3" font-size="11" font-family="monospace">Access-Control-*</text>
  <text x="484" y="184" fill="#e6edf3" font-size="11" font-family="monospace">Server</text>
  <text x="484" y="204" fill="#e6edf3" font-size="11" font-family="monospace">Retry-After</text>
</svg>

Entity headers (dashed centre) travel in both directions; the outer two columns are direction-specific.

## 5. Runnable example

```js
// save as header-types.js — needs Node.js, no installs
const http = require("http");

const server = http.createServer((req, res) => {
  // Log request-only and entity headers from the incoming request
  console.log("\n[Request headers]");
  console.log("  Host:           ", req.headers["host"]);
  console.log("  Authorization:  ", req.headers["authorization"] || "(none)");
  console.log("  User-Agent:     ", req.headers["user-agent"]);

  console.log("[Entity headers in request]");
  console.log("  Content-Type:   ", req.headers["content-type"]   || "(none)");
  console.log("  Content-Length: ", req.headers["content-length"] || "(none)");

  const payload = JSON.stringify({ ok: true });

  // Set response-only headers + entity headers on the response
  res.writeHead(200, {
    // Response-only
    "Cache-Control":  "max-age=60",
    "Set-Cookie":     "session=abc123; HttpOnly",
    // Entity — describing the body we're about to send
    "Content-Type":   "application/json",
    "Content-Length": Buffer.byteLength(payload),
  });
  res.end(payload);
});

server.listen(3000, () => {
  const options = {
    hostname: "localhost", port: 3000, path: "/", method: "POST",
    headers: {
      // Request headers
      "Authorization": "Bearer token42",
      "User-Agent":    "HeaderDemo/1.0",
      // Entity headers — body is JSON
      "Content-Type":   "application/json",
      "Content-Length": Buffer.byteLength('{"x":1}'),
    },
  };

  const req = http.request(options, (res) => {
    console.log("\n[Response headers]");
    console.log("  Cache-Control:", res.headers["cache-control"]);
    console.log("  Set-Cookie:   ", res.headers["set-cookie"]);
    console.log("  Content-Type: ", res.headers["content-type"]);
    res.on("data", () => {});
    res.on("end", () => server.close());
  });

  req.write('{"x":1}');
  req.end();
});
```

**How to run:** `node header-types.js` — built-in `http`, no npm.

## 6. Walkthrough

- `req.headers["host"]` — request header; always present in HTTP/1.1.
- `req.headers["authorization"]` — request header; not on response side.
- `req.headers["content-type"]` in the *request* — entity header describing the request body.
- `"Cache-Control"` and `"Set-Cookie"` in `res.writeHead(...)` — response-only headers that instruct the client's caching layer and cookie store.
- `"Content-Type"` and `"Content-Length"` in `res.writeHead(...)` — entity headers describing the response body.
- `Buffer.byteLength(payload)` — byte length, not character length; important for accurate `Content-Length`.
- `res.headers["set-cookie"]` on the client side — response header the client received; it would store this cookie and send it back as `Cookie` on subsequent requests.

## 7. Gotchas & takeaways

> `ETag` and `Last-Modified` are entity headers that travel on responses, but they feed *request* headers (`If-None-Match`, `If-Modified-Since`) on the client's next request. They're a two-turn caching handshake across two different header categories.

> Don't put `Authorization` in a response — it has no meaning there. The server-side counterpart is `WWW-Authenticate`, which tells the client *what* kind of credentials to send. They're distinct headers in distinct categories.

- Request headers = client's metadata about itself and what it wants.
- Response headers = server's metadata about the result and directives for the client.
- Entity (representation) headers = metadata about the message body — valid in both directions.
- `Content-Type`, `Content-Length`, `Content-Encoding` are entity headers; always set them when sending a body.
- `Set-Cookie` is response-only; `Cookie` is request-only — they're a complementary pair.
