---
card: webdev
gi: 39
slug: content-negotiation-accept-accept-language-accept-encoding
title: Content negotiation (Accept, Accept-Language, Accept-Encoding)
---

## 1. What it is

**Content negotiation** is the mechanism where the client tells the server what formats, languages, and encodings it can handle, and the server picks the best match. Three request headers carry the client's preferences:

- **`Accept`** — preferred media types (JSON, HTML, images…).
- **`Accept-Language`** — preferred human languages (`en-US`, `fr`, `zh-CN`).
- **`Accept-Encoding`** — compression methods the client can decompress (`gzip`, `br`, `deflate`).

The server responds with the chosen format identified via response headers (`Content-Type`, `Content-Language`, `Content-Encoding`).

## 2. Why & when

Without content negotiation, a server would need separate endpoints for every format: `/data.json`, `/data.xml`, `/data.html`. Instead, one URL (`/data`) serves everyone, responding in the format each client requests. This matters when:

- A browser wants HTML but an API client wants JSON — same URL, different responses.
- Users prefer different languages — one endpoint serves `en`, `fr`, or `ja` based on `Accept-Language`.
- Serving compressed responses — gzip reduces bandwidth by 60–80%; the server only compresses if the client announces support via `Accept-Encoding`.
- Debugging "why did I get HTML when I wanted JSON?" — the `Accept` header is almost always the answer.

## 3. Core concept

Think of a waiter with a multilingual menu. You say "I'd like this in Spanish please, and I can't read Italian" — that's content negotiation. The waiter brings the Spanish menu if available, falls back to English if not.

**Quality values (q-factors):** clients can attach a priority to each preference with `;q=0.x` (default 1.0 = highest). The server picks the highest-quality match it can serve.

```
Accept: text/html, application/json;q=0.9, */*;q=0.1
```
This says: "Prefer HTML, then JSON, then anything else, in that order."

**`Accept` negotiation flow:**
1. Client lists supported types with optional q-values.
2. Server compares against types it can produce.
3. Server picks the best match and sets `Content-Type` on the response.
4. If no match is possible, server returns `406 Not Acceptable`.

**`Accept-Language`:** same pattern, different dimension.
```
Accept-Language: en-US, en;q=0.9, fr;q=0.5
```
Server sends `Content-Language: en-US` (or whichever it chose).

**`Accept-Encoding`:** compression. Most HTTP/1.1+ clients send:
```
Accept-Encoding: gzip, deflate, br
```
Server compresses with one of these, sends `Content-Encoding: gzip` in the response. The client auto-decompresses.

## 4. Diagram

<svg viewBox="0 0 680 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Content negotiation flow: client sends Accept headers, server picks best match, responds with chosen format">
  <!-- Client -->
  <rect x="20" y="60" width="180" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="82" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Client</text>
  <text x="30"  y="106" fill="#e6edf3" font-size="10" font-family="monospace">Accept: text/html</text>
  <text x="30"  y="122" fill="#e6edf3" font-size="10" font-family="monospace">  application/json;q=0.9</text>
  <text x="30"  y="142" fill="#e6edf3" font-size="10" font-family="monospace">Accept-Language: fr,en;q=0.8</text>
  <text x="30"  y="162" fill="#e6edf3" font-size="10" font-family="monospace">Accept-Encoding: gzip, br</text>

  <!-- Arrow right -->
  <line x1="204" y1="140" x2="310" y2="140" stroke="#6db33f" stroke-width="2" marker-end="url(#arrowg)"/>
  <text x="257" y="132" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">request</text>

  <!-- Server negotiation box -->
  <rect x="314" y="80" width="170" height="120" rx="8" fill="#161d27" stroke="#8b949e" stroke-width="1.2"/>
  <text x="399" y="100" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Server picks best match</text>
  <text x="399" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Can serve: JSON, XML</text>
  <text x="399" y="136" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Can serve: fr, en</text>
  <text x="399" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Can compress: gzip</text>
  <text x="399" y="174" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">→ sends JSON + fr + gzip</text>

  <!-- Arrow right from server negotiation -->
  <line x1="488" y1="140" x2="590" y2="140" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrowb)"/>
  <text x="539" y="132" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">response</text>

  <!-- Response headers box -->
  <rect x="594" y="80" width="66" height="120" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="627" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Content-Type:</text>
  <text x="627" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">app/json</text>
  <text x="627" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Content-Lang:</text>
  <text x="627" y="146" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">fr</text>
  <text x="627" y="164" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Content-Enc:</text>
  <text x="627" y="178" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">gzip</text>

  <!-- 406 note -->
  <rect x="314" y="220" width="170" height="36" rx="6" fill="#2d1a1a" stroke="#f85149" stroke-width="1"/>
  <text x="399" y="237" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">No match found?</text>
  <text x="399" y="251" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">→ 406 Not Acceptable</text>

  <defs>
    <marker id="arrowg" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrowb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Client sends preferences; server picks best match and echoes the chosen format in response headers.

## 5. Runnable example

```js
// save as content-negotiation.js — needs Node.js, no installs
const http = require("http");
const zlib = require("zlib");

const data = {
  json: '{"message":"Hello","lang":"fr"}',
  html: "<html><body><p>Bonjour</p></body></html>",
};

const server = http.createServer((req, res) => {
  const accept         = req.headers["accept"]          || "*/*";
  const acceptLang     = req.headers["accept-language"] || "en";
  const acceptEncoding = req.headers["accept-encoding"] || "";

  // Pick content type
  let contentType, body;
  if (accept.includes("application/json")) {
    contentType = "application/json";
    body = data.json;
  } else if (accept.includes("text/html")) {
    contentType = "text/html";
    body = data.html;
  } else {
    res.writeHead(406);
    return res.end("406: cannot serve " + accept);
  }

  // Pick language
  const lang = acceptLang.split(",")[0].split(";")[0].trim(); // "fr" from "fr, en;q=0.9"

  // Compress if client supports gzip
  const headers = {
    "Content-Type":     contentType,
    "Content-Language": lang,
    "Vary":             "Accept, Accept-Language, Accept-Encoding",
  };

  if (acceptEncoding.includes("gzip")) {
    const compressed = zlib.gzipSync(Buffer.from(body));
    headers["Content-Encoding"] = "gzip";
    headers["Content-Length"]   = compressed.length;
    res.writeHead(200, headers);
    return res.end(compressed);
  }

  headers["Content-Length"] = Buffer.byteLength(body);
  res.writeHead(200, headers);
  res.end(body);
});

server.listen(3000, () => {
  const request = (headers, label) =>
    new Promise((resolve) => {
      const opts = { hostname: "localhost", port: 3000, path: "/", headers };
      http.get(opts, (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () => {
          const raw = Buffer.concat(chunks);
          const body = res.headers["content-encoding"] === "gzip"
            ? zlib.gunzipSync(raw).toString()
            : raw.toString();
          console.log(`[${label}] ${res.statusCode} | ${res.headers["content-type"]} | enc:${res.headers["content-encoding"] || "none"}`);
          console.log("  body:", body);
          resolve();
        });
      });
    });

  (async () => {
    await request({ accept: "application/json", "accept-language": "fr", "accept-encoding": "gzip" }, "JSON+gzip");
    await request({ accept: "text/html", "accept-language": "en-US" }, "HTML");
    await request({ accept: "image/png" }, "PNG (no match)");
    server.close();
  })();
});
```

**How to run:** `node content-negotiation.js` — built-in `http` and `zlib`, no npm.

## 6. Walkthrough

- `accept.includes("application/json")` — real servers use a proper parser; this is simplified for clarity.
- `lang = acceptLang.split(",")[0].split(";")[0].trim()` — extracts the primary language tag; `"fr, en;q=0.9"` → `"fr"`.
- `zlib.gzipSync(Buffer.from(body))` — compresses the body when the client supports gzip. The compressed buffer replaces the string.
- `headers["Content-Encoding"] = "gzip"` — response header telling the client to decompress before rendering.
- `"Vary": "Accept, Accept-Language, Accept-Encoding"` — critical header telling caches that responses vary by these request headers; without it, a cache might serve a compressed gzip body to a client that didn't ask for gzip.
- `406` response — when no format can be matched, `406 Not Acceptable` is the correct status code.
- On the client side: `zlib.gunzipSync(raw)` — decompresses the gzip body to recover the original string.

## 7. Gotchas & takeaways

> Always send the **`Vary`** header listing the negotiation headers you used to build the response. If you compress for gzip clients but don't include `Vary: Accept-Encoding`, a CDN may cache the gzip response and serve it to a client that didn't ask for compression — breaking the client.

> `Accept: */*` is a wildcard meaning "anything". `fetch()` in browsers sends `Accept: */*` by default. Always check what your client actually sends in DevTools before assuming content negotiation is working.

- Three negotiation headers: `Accept` (format), `Accept-Language` (language), `Accept-Encoding` (compression).
- Server picks the best match and echoes its choice in `Content-Type`, `Content-Language`, `Content-Encoding`.
- No match possible → `406 Not Acceptable`.
- `Vary` header is required when caching negotiated responses — list all headers you negotiated on.
- Q-values (`;q=0.9`) express priority; lower q = lower preference; default is 1.0.
