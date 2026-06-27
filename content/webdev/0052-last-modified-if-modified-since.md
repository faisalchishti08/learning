---
card: webdev
gi: 52
slug: last-modified-if-modified-since
title: Last-Modified & If-Modified-Since
---

## 1. What it is

**Last-Modified** is a response header that tells the client when the resource was last changed, expressed as an HTTP-date:

```http
Last-Modified: Tue, 10 Jun 2025 14:23:00 GMT
```

**If-Modified-Since** is the corresponding *request* header. When a client has a cached copy with a `Last-Modified` date, it sends that date back on subsequent requests:

```http
If-Modified-Since: Tue, 10 Jun 2025 14:23:00 GMT
```

The server compares the date to the resource's current modification time:

- **Not modified since that date** → `304 Not Modified` (no body).
- **Modified since that date** → `200 OK` with the new body and updated `Last-Modified`.

This is the older sibling of ETag/`If-None-Match` — timestamp-based rather than content-hash-based.

## 2. Why & when

`Last-Modified` / `If-Modified-Since` was the original HTTP caching mechanism (HTTP/1.0) and it still works well for:

- **Static files served from disk** — the file system provides modification timestamps for free.
- **Resources where the last-write time reliably represents change** — uploaded images, documents, log exports.
- **Bandwidth-sensitive scenarios** — a `304` avoids retransmitting potentially large bodies.

It's less reliable than ETags for:
- Dynamically generated content (modification time may not track logical change).
- Files that are rewritten with the same content (mtime changes, content doesn't).
- Sub-second changes (HTTP dates have 1-second precision).
- Distributed systems where different nodes may report different mtimes.

In practice, well-configured servers send *both* `Last-Modified` and `ETag`, and browsers send *both* `If-Modified-Since` and `If-None-Match`. If both are present, `If-None-Match` takes precedence (RFC 7232).

## 3. Core concept

Analogy: a newspaper subscription. The deliverer checks: "Has today's paper been printed after the last one you received?" If no new edition since your last copy, you get nothing and keep what you have (304). If there's a new edition, you get the whole paper (200).

The date-comparison logic the server runs:

```
resourceMtime = file system modification time
clientDate   = If-Modified-Since header value

if (resourceMtime <= clientDate):
    return 304 Not Modified
else:
    return 200 OK + new body + Last-Modified: <resourceMtime>
```

Important nuance: the comparison is `≤`, not `<`. If the resource was modified *at exactly the same second* as the client's cached version, the server still returns 304 — the assumption is same-second means same version.

```
Timeline:
Jun 10 14:23:00 → server generates resource → Last-Modified: Jun 10 14:23:00
Client stores this date.

Jun 12 09:00:00 → client's cache expires → sends If-Modified-Since: Jun 10 14:23:00

Case A: resource still from Jun 10 → 304 (mtime 14:23:00 ≤ client date 14:23:00)
Case B: resource updated Jun 11   → 200 (mtime > client date)
```

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Last-Modified and If-Modified-Since flow: first response includes Last-Modified date; subsequent conditional request returns 304 if not changed or 200 with new date if changed">
  <defs>
    <marker id="a52" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b52" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c52" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#d29922"/></marker>
  </defs>

  <!-- Entities -->
  <rect x="20" y="14" width="90" height="24" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="30" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <rect x="570" y="14" width="90" height="24" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="615" y="30" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <!-- Timeline line -->
  <line x1="65" y1="38" x2="65" y2="275" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="615" y1="38" x2="615" y2="275" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <!-- Step 1: initial request -->
  <text x="20" y="60" fill="#8b949e" font-size="10" font-family="sans-serif">t=0 Initial</text>
  <line x1="110" y1="66" x2="568" y2="66" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a52)"/>
  <text x="340" y="61" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET /report.pdf</text>

  <!-- Step 2: 200 + Last-Modified -->
  <line x1="570" y1="82" x2="112" y2="82" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b52)"/>
  <text x="340" y="77" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK  Last-Modified: Tue, 10 Jun 2025 14:23:00 GMT  ← body</text>

  <!-- cache stored -->
  <rect x="20" y="94" width="100" height="30" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="70" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cached body</text>
  <text x="70" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mtime: 14:23:00</text>

  <!-- Time passes -->
  <text x="240" y="145" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">— max-age expires, client revalidates —</text>

  <!-- Step 3: conditional request -->
  <text x="20" y="168" fill="#8b949e" font-size="10" font-family="sans-serif">Case A: unchanged</text>
  <line x1="110" y1="175" x2="568" y2="175" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a52)"/>
  <text x="340" y="170" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET /report.pdf  If-Modified-Since: Tue, 10 Jun 2025 14:23:00 GMT</text>
  <line x1="570" y1="190" x2="112" y2="190" stroke="#d29922" stroke-width="1.5" marker-end="url(#c52)"/>
  <text x="340" y="185" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">304 Not Modified  (no body)</text>

  <!-- Case B: changed -->
  <text x="20" y="218" fill="#8b949e" font-size="10" font-family="sans-serif">Case B: changed</text>
  <line x1="110" y1="225" x2="568" y2="225" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a52)"/>
  <text x="340" y="220" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET /report.pdf  If-Modified-Since: Tue, 10 Jun 2025 14:23:00 GMT</text>
  <line x1="570" y1="242" x2="112" y2="242" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b52)"/>
  <text x="340" y="237" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK  Last-Modified: Thu, 12 Jun 2025 08:01:00 GMT  ← new body</text>
</svg>

On revalidation the client echoes the stored `Last-Modified` date; the server compares it to the file's current mtime and answers 304 or 200.

## 5. Runnable example

```js
// save as last-modified-demo.js  —  node last-modified-demo.js  (no installs)
const http = require("http");
const fs   = require("fs");
const path = require("path");

// Create a temp file we can modify
const FILE = path.join(process.cwd(), "_demo_resource.txt");
fs.writeFileSync(FILE, "Version 1 content");

function httpDate(d) {
  return new Date(d).toUTCString();
}

const server = http.createServer((req, res) => {
  const stat = fs.statSync(FILE);
  const mtime = stat.mtimeMs;
  const lastModified = httpDate(mtime);

  const ifModifiedSince = req.headers["if-modified-since"];

  if (ifModifiedSince) {
    const clientDate = new Date(ifModifiedSince).getTime();
    if (mtime <= clientDate + 1000) { // +1000ms tolerance for 1-second granularity
      res.writeHead(304, { "Last-Modified": lastModified });
      console.log(`Server: 304 Not Modified (mtime=${lastModified})`);
      return res.end();
    }
  }

  const body = fs.readFileSync(FILE);
  res.writeHead(200, {
    "Content-Type": "text/plain",
    "Last-Modified": lastModified,
    "Cache-Control": "max-age=10",
  });
  res.end(body);
  console.log(`Server: 200 OK, body="${body}", Last-Modified=${lastModified}`);
});

server.listen(3700, () => {
  function fetch(ims, label, cb) {
    const headers = ims ? { "if-modified-since": ims } : {};
    http.get({ hostname: "localhost", port: 3700, path: "/file", headers }, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => {
        const lm = res.headers["last-modified"];
        console.log(`Client [${label}]: ${res.statusCode} body="${body}" Last-Modified=${lm}\n`);
        cb(lm);
      });
    }).end();
  }

  // 1) First request
  fetch(null, "initial", (lm) => {
    // 2) Same date — expect 304
    fetch(lm, "unchanged", (lm2) => {
      // 3) Modify the file, then request again
      setTimeout(() => {
        fs.writeFileSync(FILE, "Version 2 content");
        fetch(lm2, "after modification", () => {
          fs.unlinkSync(FILE);
          server.close();
        });
      }, 1100); // wait >1 second so mtime definitely differs
    });
  });
});
```

**How to run:** `node last-modified-demo.js` — the 1-second wait ensures the file mtime is detectably newer.

## 6. Walkthrough

- `fs.statSync(FILE).mtimeMs` — Node gives modification time in milliseconds; we convert to an HTTP-date string with `toUTCString()`.
- `if-modified-since` header is parsed back to a timestamp with `new Date(ifModifiedSince).getTime()`.
- The `+1000ms` tolerance handles the 1-second granularity of HTTP dates: a file modified at `14:23:00.500` has mtime 500ms later than the `14:23:00` date the client stores. Without a tolerance, the comparison `500ms <= 0ms` would wrongly trigger a 200.
- `setTimeout(..., 1100)` — we wait >1 second before modifying the file to guarantee the mtime is strictly greater than the stored HTTP-date, triggering a `200`.
- On real servers (Nginx, Apache, S3) this comparison is done automatically. Node's `http` module does not do it — you implement it in middleware (e.g., `express.static` does this for you).

## 7. Gotchas & takeaways

> **1-second granularity** is the biggest weakness. Two writes within the same second produce the same `Last-Modified` value — the second change is invisible to the cache. ETags with content hashes catch this case.

> In clustered deployments, different servers may have different file timestamps for the same content (e.g., deployed at slightly different times). This causes inconsistent 304 vs 200 responses. ETags based on content hashes are consistent across all nodes.

> `Last-Modified` is usually ignored for `POST`, `PUT`, `DELETE` — it only matters for `GET` and `HEAD` responses.

- `express.static` automatically sends `Last-Modified` and handles `If-Modified-Since` — you get caching for free when serving static files.
- When both `Last-Modified` and `ETag` are present, `ETag` / `If-None-Match` takes precedence per RFC 7232.
- HTTP-date format is always GMT: `Tue, 10 Jun 2025 14:23:00 GMT`. Never use local time.
- A `304` response must still include `Cache-Control`, `Expires`, `Vary`, `ETag`, and `Last-Modified` headers to update the browser's stored metadata.
