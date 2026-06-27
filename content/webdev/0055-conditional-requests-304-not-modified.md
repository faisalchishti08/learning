---
card: webdev
gi: 55
slug: conditional-requests-304-not-modified
title: Conditional requests & 304 Not Modified
---

## 1. What it is

A **conditional request** is an HTTP request that includes a *precondition header*. The server evaluates the precondition against the current state of the resource and either fulfils the request normally or responds with a short status code that avoids sending the full body.

The most common conditional request for caching is the **GET + validator** pattern:

| Request header | Server response header checked |
|---|---|
| `If-None-Match: "abc"` | `ETag` |
| `If-Modified-Since: <date>` | `Last-Modified` |

When the precondition succeeds (resource unchanged): **`304 Not Modified`** — no body, just headers.
When the precondition fails (resource changed): **`200 OK`** — full body.

There are also precondition headers used for write safety:

| Header | Use |
|---|---|
| `If-Match: "abc"` | Only apply PUT/DELETE if ETag matches (optimistic locking) |
| `If-Unmodified-Since: <date>` | Only write if not changed since this date |
| `If-Range: "abc"` | Resume a range download only if the resource hasn't changed |

## 2. Why & when

A `304` response has no body. For a 500KB image, a `304` is ~200 bytes vs 500,000 bytes — a 2500× reduction in data transferred. The client still pays one round-trip (to confirm the resource is the same), but nothing more.

Use cases:

- **Browser cache validation** — the most common case. After `max-age` expires, the browser sends `If-None-Match` / `If-Modified-Since` to avoid downloading unchanged assets.
- **CDN-to-origin checks** — a CDN edge node validates its cached copy against origin before serving.
- **Resumable downloads** — `Range: bytes=1000-` with `If-Range: <etag>` resumes a partial download only if the file hasn't changed.
- **Optimistic concurrency on APIs** — `If-Match` on a PUT prevents a lost-update race condition (two users editing the same record simultaneously).

## 3. Core concept

Analogy: a valet checking a coat. "I have coat ticket #7319. Is the coat in the wardrobe still the same one?" If yes → "yes, still here" (304, no coat). If no → "we have a new coat, here it is" (200, full coat). Either way the valet checked — but only the second case requires moving the coat.

The full `304` flow:

```
1. Client sends:
   GET /style.css HTTP/1.1
   If-None-Match: "a3f92b"
   If-Modified-Since: Mon, 09 Jun 2025 10:00:00 GMT

2. Server evaluates:
   - currentEtag == "a3f92b" ?  → yes (or Last-Modified not changed)
   → 304 Not Modified

3. Server sends:
   HTTP/1.1 304 Not Modified
   ETag: "a3f92b"
   Cache-Control: max-age=3600
   (no body at all)

4. Browser uses cached body + updates freshness metadata.
```

Key rule: the `304` response **must include** any headers that would appear in the equivalent `200` and affect how the cache stores the response: `ETag`, `Cache-Control`, `Vary`, `Expires`. This lets the browser update its cached metadata without a body.

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Conditional request flow: browser sends If-None-Match, server returns 304 if unchanged (no body) or 200 if changed (full body)">
  <defs>
    <marker id="a55" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b55" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c55" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#d29922"/></marker>
    <marker id="d55" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Entities -->
  <rect x="20" y="10" width="80" height="24" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="60" y="26" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <rect x="300" y="10" width="80" height="24" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="26" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Cache</text>
  <rect x="580" y="10" width="80" height="24" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="620" y="26" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Origin</text>

  <!-- Step 1: conditional request from browser to cache/origin -->
  <text x="20" y="56" fill="#8b949e" font-size="10" font-family="sans-serif" font-weight="bold">1. Conditional request</text>
  <line x1="100" y1="64" x2="298" y2="64" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a55)"/>
  <text x="200" y="59" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">GET /style.css</text>
  <line x1="380" y1="64" x2="578" y2="64" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a55)"/>
  <text x="478" y="59" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">If-None-Match: "a3f92b"</text>

  <!-- Step 2: server check -->
  <text x="20" y="92" fill="#8b949e" font-size="10" font-family="sans-serif" font-weight="bold">2. Server evaluates</text>
  <rect x="540" y="97" width="120" height="34" rx="5" fill="#1c2430" stroke="#d29922" stroke-width="1"/>
  <text x="600" y="112" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">currentEtag == "a3f92b"?</text>
  <text x="600" y="126" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">YES → 304 / NO → 200</text>

  <!-- Branch: 304 -->
  <text x="20" y="158" fill="#d29922" font-size="10" font-family="sans-serif" font-weight="bold">3a. Unchanged → 304 (no body, cheap!)</text>
  <line x1="580" y1="168" x2="382" y2="168" stroke="#d29922" stroke-width="2" marker-end="url(#c55)"/>
  <text x="480" y="163" fill="#d29922" font-size="9" text-anchor="middle" font-family="sans-serif">304 Not Modified (headers only)</text>
  <line x1="300" y1="168" x2="102" y2="168" stroke="#d29922" stroke-width="2" marker-end="url(#c55)"/>
  <text x="200" y="163" fill="#d29922" font-size="9" text-anchor="middle" font-family="sans-serif">304 — browser uses cached body</text>
  <!-- size annotation -->
  <rect x="540" y="176" width="120" height="18" rx="3" fill="#0d1117" stroke="#d29922" stroke-width="1"/>
  <text x="600" y="188" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">~200 bytes sent</text>

  <!-- Branch: 200 -->
  <text x="20" y="222" fill="#79c0ff" font-size="10" font-family="sans-serif" font-weight="bold">3b. Changed → 200 (new body)</text>
  <line x1="580" y1="232" x2="382" y2="232" stroke="#79c0ff" stroke-width="2" marker-end="url(#b55)"/>
  <text x="480" y="227" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">200 OK + ETag: "d7e401" + body</text>
  <line x1="300" y1="232" x2="102" y2="232" stroke="#79c0ff" stroke-width="2" marker-end="url(#b55)"/>
  <text x="200" y="227" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">200 — browser replaces cached copy</text>
  <!-- size annotation -->
  <rect x="540" y="240" width="120" height="18" rx="3" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="600" y="252" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">full body (e.g. 50KB)</text>

  <text x="20" y="292" fill="#8b949e" font-size="11" font-family="sans-serif">304 headers must include: ETag, Cache-Control, Vary — browser updates cache metadata</text>
</svg>

The `304` path (gold) sends only ~200 bytes; the `200` path (blue) sends the full body. Both require one round-trip.

## 5. Runnable example

```js
// save as conditional-requests.js  —  node conditional-requests.js  (no installs)
const http   = require("http");
const crypto = require("crypto");

let resource = { body: "stylesheet v1 { color: red }", version: 1 };

function etag(r) {
  return '"' + crypto.createHash("sha1").update(r.body).digest("hex").slice(0, 8) + '"';
}

const server = http.createServer((req, res) => {
  const currentEtag = etag(resource);
  const clientEtag  = req.headers["if-none-match"];
  const ifMs        = req.headers["if-modified-since"];

  // Evaluate precondition (If-None-Match takes priority over If-Modified-Since)
  const etagMatch = clientEtag && clientEtag === currentEtag;
  const dateMatch = !clientEtag && ifMs && new Date(ifMs).getTime() >= resource.mtime;
  const unchanged = etagMatch || dateMatch;

  if (unchanged) {
    // 304 — must still send caching headers
    res.writeHead(304, {
      "ETag": currentEtag,
      "Cache-Control": "no-cache",
      "Last-Modified": new Date(resource.mtime || Date.now()).toUTCString(),
    });
    return res.end();
  }

  resource.mtime = Date.now();
  res.writeHead(200, {
    "Content-Type": "text/css",
    "ETag": currentEtag,
    "Cache-Control": "no-cache",
    "Last-Modified": new Date(resource.mtime).toUTCString(),
  });
  res.end(resource.body);
});

server.listen(4000, () => {
  function request(headers, label, cb) {
    const req = http.request({ hostname: "localhost", port: 4000, path: "/style.css",
                               method: "GET", headers }, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => {
        const et = res.headers["etag"];
        console.log(`[${label.padEnd(18)}] status=${res.statusCode}  ETag=${et}  body="${body}"`);
        cb(res.headers);
      });
    });
    req.end();
  }

  // 1) First request — no validators
  request({}, "1. initial", (h) => {
    const storedEtag = h["etag"];
    const storedLm   = h["last-modified"];

    // 2) Conditional with ETag — should 304
    request({ "if-none-match": storedEtag }, "2. if-none-match", (h2) => {

      // 3) Conditional with Last-Modified — should 304
      request({ "if-modified-since": storedLm }, "3. if-modified-since", () => {

        // 4) Modify resource, then conditional — should 200
        resource.body = "stylesheet v2 { color: blue }";
        request({ "if-none-match": storedEtag }, "4. after change", () => {

          // 5) Both headers — If-None-Match wins
          request({ "if-none-match": '"wrongetag"', "if-modified-since": storedLm },
            "5. both (etag wins)", () => server.close());
        });
      });
    });
  });
});
```

**How to run:** `node conditional-requests.js`

Expected output:
```
[1. initial          ] status=200  ETag="xxxxxxxx"  body="stylesheet v1 { color: red }"
[2. if-none-match    ] status=304  ETag="xxxxxxxx"  body=""
[3. if-modified-since] status=304  ETag="xxxxxxxx"  body=""
[4. after change     ] status=200  ETag="yyyyyyyy"  body="stylesheet v2 { color: blue }"
[5. both (etag wins) ] status=200  ETag="yyyyyyyy"  body="stylesheet v2 { color: blue }"
```

## 6. Walkthrough

- `etag(r)` — SHA-1 of the body bytes, first 8 chars. A real server would compute this from the file content or version ID.
- `etagMatch` — compares client's `If-None-Match` to current ETag. Note: real servers must handle comma-separated lists (`"abc", "def"`) and wildcard `*`.
- `dateMatch` — falls back to `Last-Modified` only when no `If-None-Match` is present (`!clientEtag`). RFC 7232 §6 requires this ordering.
- `304` response includes `ETag` and `Cache-Control` — even though there's no body, the browser uses these headers to update its cached metadata (new `max-age` countdown, updated ETag).
- Request 5 shows `If-None-Match: "wrongetag"` failing (ETag changed) even though `If-Modified-Since` would pass — `If-None-Match` always takes precedence.

## 7. Gotchas & takeaways

> A `304` response with **no `ETag` header** tells the browser the cached copy is still valid, but the browser may not update its ETag or Cache-Control metadata. Always include `ETag` in your `304` to keep the cache in sync.

> `If-None-Match: *` is a special wildcard: the condition fails (→ sends body) if *any* current representation exists. Used in creation flows: "give me the resource only if there isn't one yet."

> Browsers automatically send `If-None-Match` and `If-Modified-Since` when they have stored validators and the resource is stale. You don't add this yourself in `fetch()` — but you can force a full request with `cache: "reload"` or `cache: "no-store"` in the Fetch API.

- `304` is about **network bandwidth** savings, not latency savings — one round-trip is still required.
- `If-Match` / `If-Unmodified-Since` are for write operations: prevent overwriting a resource someone else changed (optimistic locking). Returns `412 Precondition Failed` when the condition doesn't hold.
- CDNs reuse conditional request logic to validate their edge caches against origin servers, transparently to clients.
- In browser DevTools, a `304` appears as a very small "from cache" entry in the Network tab — the response has no body column.
