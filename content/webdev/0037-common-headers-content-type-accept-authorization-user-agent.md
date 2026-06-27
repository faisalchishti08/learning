---
card: webdev
gi: 37
slug: common-headers-content-type-accept-authorization-user-agent
title: Common headers (Content-Type, Accept, Authorization, User-Agent)
---

## 1. What it is

HTTP headers are key/value pairs sent in both requests and responses to carry metadata about the message. Four show up constantly:

- **Content-Type** — what format the body is in (request or response).
- **Accept** — what formats the client is willing to receive (request only).
- **Authorization** — credentials proving who's asking (request only).
- **User-Agent** — who sent the request: browser, curl, a mobile app (request only).

Headers are case-insensitive and separated from the body by a blank line.

## 2. Why & when

Without `Content-Type`, the server doesn't know if the body is JSON, form data, or an XML blob — it would have to guess. Without `Accept`, the server sends whatever it feels like. Without `Authorization`, every endpoint is public. Without `User-Agent`, the server can't distinguish a bot from a browser.

These four headers appear in almost every API call, every authenticated endpoint, and every `fetch()` from JavaScript. Understanding them matters when:

- An API returns `415 Unsupported Media Type` (missing or wrong `Content-Type`).
- You get JSON back but expected HTML (or vice versa) — mismatched `Accept`.
- An endpoint returns `401` — `Authorization` header is absent or malformed.
- A scraper gets blocked — server is checking `User-Agent`.

## 3. Core concept

Analogy: mailing a package. **Content-Type** is the label on the box ("fragile glass inside"). **Accept** is the recipient's note on the door ("only accept packages under 5 kg"). **Authorization** is the signature on a delivery requiring ID. **User-Agent** is the delivery company's uniform.

**Content-Type** — the MIME type of the body. In a *request*, it tells the server how to parse what you sent. In a *response*, it tells the client how to interpret what was returned.

```
Content-Type: application/json          # body is JSON
Content-Type: text/html; charset=utf-8  # body is HTML, UTF-8 encoded
Content-Type: multipart/form-data; boundary=----XYZ  # file upload
```

**Accept** — preference list for the response format. The server picks the best match (content negotiation — see tutorial 39).

```
Accept: application/json
Accept: text/html, application/xhtml+xml, */*
```

**Authorization** — credential schemes. The most common:

```
Authorization: Bearer <JWT-or-opaque-token>   # OAuth 2 / JWT
Authorization: Basic dXNlcjpwYXNz             # Base64(user:password) — use over HTTPS only
Authorization: ApiKey abc123                  # common in API keys, not formally specified
```

**User-Agent** — identifies the software making the request.

```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ...
User-Agent: curl/8.4.0
User-Agent: MyApp/2.1 (https://myapp.com)
```

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four common HTTP headers shown with their direction and purpose">
  <rect width="680" height="300" fill="#0d1117"/>

  <!-- Column labels -->
  <text x="90"  y="28" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Header</text>
  <text x="240" y="28" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Direction</text>
  <text x="460" y="28" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Purpose</text>

  <!-- Content-Type -->
  <rect x="20"  y="40" width="140" height="48" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="90"  y="62" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">Content-Type</text>
  <text x="240" y="62" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Req + Resp</text>
  <text x="460" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Format of the body</text>
  <text x="460" y="72" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">application/json, text/html, multipart/form-data</text>

  <!-- Accept -->
  <rect x="20"  y="100" width="140" height="48" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90"  y="122" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Accept</text>
  <text x="240" y="122" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Request only</text>
  <text x="460" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Formats client will accept</text>
  <text x="460" y="132" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Accept: application/json, text/html;q=0.9</text>

  <!-- Authorization -->
  <rect x="20"  y="160" width="140" height="48" rx="5" fill="#1c2430" stroke="#e3b341" stroke-width="1.2"/>
  <text x="90"  y="182" fill="#e3b341" font-size="12" text-anchor="middle" font-family="monospace">Authorization</text>
  <text x="240" y="182" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Request only</text>
  <text x="460" y="175" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Credentials for the request</text>
  <text x="460" y="192" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Bearer &lt;token&gt; | Basic &lt;base64&gt;</text>

  <!-- User-Agent -->
  <rect x="20"  y="220" width="140" height="48" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90"  y="242" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">User-Agent</text>
  <text x="240" y="242" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Request only</text>
  <text x="460" y="235" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Identifies the client software</text>
  <text x="460" y="252" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Mozilla/5.0 ... | curl/8.4.0</text>
</svg>

`Content-Type` travels both directions; the other three are request-only.

## 5. Runnable example

```js
// save as headers-demo.js — needs Node.js, no installs
const http = require("http");

const server = http.createServer((req, res) => {
  const contentType = req.headers["content-type"] || "(none)";
  const accept      = req.headers["accept"]        || "(none)";
  const auth        = req.headers["authorization"] || "(none)";
  const userAgent   = req.headers["user-agent"]    || "(none)";

  console.log("\n--- Incoming request ---");
  console.log("Content-Type: ", contentType);
  console.log("Accept:       ", accept);
  console.log("Authorization:", auth);
  console.log("User-Agent:   ", userAgent);

  // Honour the Accept header — send JSON or plain text
  if (accept.includes("application/json")) {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ message: "Here is your JSON" }));
  } else {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Here is plain text");
  }
});

server.listen(3000, () => {
  // Request 1: JSON client
  const opts1 = {
    hostname: "localhost", port: 3000, path: "/api/data", method: "POST",
    headers: {
      "Content-Type":  "application/json",
      "Accept":        "application/json",
      "Authorization": "Bearer secret-token",
      "User-Agent":    "MyApp/1.0",
    },
  };

  // Request 2: plain-text client
  const opts2 = {
    hostname: "localhost", port: 3000, path: "/api/data", method: "GET",
    headers: {
      "Accept":     "text/plain",
      "User-Agent": "curl/8.4.0",
    },
  };

  const doRequest = (opts, label, done) => {
    const r = http.request(opts, (res) => {
      let b = "";
      res.on("data", (c) => (b += c));
      res.on("end", () => { console.log(`\n[${label}] Response body:`, b); done(); });
    });
    if (opts.method === "POST") r.write('{"key":"val"}');
    r.end();
  };

  doRequest(opts1, "JSON client", () =>
    doRequest(opts2, "Plain client", () => server.close())
  );
});
```

**How to run:** `node headers-demo.js` — built-in `http`, no npm.

## 6. Walkthrough

- `req.headers["content-type"]` — Node lowercases all header names; always access them in lowercase.
- `req.headers["authorization"]` — the raw value including the scheme (`Bearer secret-token`). Parse it by splitting on space: `["Bearer", "secret-token"]`.
- Server checks `accept.includes("application/json")` — simple content negotiation based on the `Accept` header.
- `opts1` sends a `POST` body, so it needs `Content-Type: application/json`; `opts2` is a `GET` with no body so no `Content-Type` needed.
- `User-Agent: "MyApp/1.0"` — custom apps should set a recognisable user agent so server operators can see who's calling.
- The two responses differ only because `Accept` differs — same server endpoint, different output format.

## 7. Gotchas & takeaways

> For `POST`/`PUT`/`PATCH`, **always set `Content-Type`**. Without it the server either rejects the request (`415`) or tries to guess the format — and often guesses wrong. `fetch()` does NOT set `Content-Type` for you when you pass a string body.

> `Authorization: Basic` encodes credentials in Base64, which is **not encryption**. Anyone who intercepts the request can decode it instantly. Only use Basic auth over HTTPS, never over plain HTTP.

- `Content-Type` tells the receiver how to parse the body; it goes on both requests and responses.
- `Accept` is a wish list for the response format; the server picks the best match.
- `Authorization` carries credentials; always send it over HTTPS.
- `User-Agent` identifies the caller; set a meaningful value for custom clients so logs are readable.
- All header names are case-insensitive; Node normalises them to lowercase.
