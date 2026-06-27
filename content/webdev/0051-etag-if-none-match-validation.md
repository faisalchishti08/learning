---
card: webdev
gi: 51
slug: etag-if-none-match-validation
title: ETag & If-None-Match (validation)
---

## 1. What it is

An **ETag** (entity tag) is a fingerprint — typically a hash or version number — that the server assigns to a particular version of a resource. It is sent in the `ETag` response header.

When a client's cached copy expires (or is being validated with `no-cache`), it sends the stored ETag back in the `If-None-Match` request header. The server compares the submitted ETag to the current version:

- **Same ETag → resource unchanged** → server returns `304 Not Modified` with no body. Client uses cached copy.
- **Different ETag → resource changed** → server returns `200 OK` with the new full body.

This is called **conditional request / validation caching**. It optimises for the common case where the resource hasn't changed: no body is transmitted, just a round-trip confirmation.

## 2. Why & when

`max-age` avoids the network entirely for fresh content. But once `max-age` expires, the client doesn't know whether the server's copy is the same or different. Without ETags it would have to re-download the whole body "just in case." With ETags:

- A 100KB JavaScript bundle that hasn't changed → only a 200-byte round trip to confirm `304`.
- A bundle that has changed → full 100KB download with the new content.

ETags are better than `Last-Modified` / `If-Modified-Since` (the older mechanism) because:
- They work for resources where modification time isn't reliable (generated responses, compressed files).
- They can represent byte-level identity, not just timestamp-level.
- They support range request synchronisation.

Set ETags on any server-generated or frequently-updated resource where changes are possible but not guaranteed on every client cycle.

## 3. Core concept

Analogy: a library book with a revision stamp inside the cover. The first time you borrow it the librarian stamps "Edition 7" on your loan receipt. When you bring it back and ask "is the new edition out yet?" the librarian checks: if the stamp still says "Edition 7," they say "same book, you can keep your notes" (304). If the stamp says "Edition 8," they swap the book (200).

The full flow:

```
First request:
Client  GET /bundle.js  →  Server
Server  200 OK + ETag: "a3f92b" + body  →  Client stores body + ETag

Subsequent request (after max-age expires):
Client  GET /bundle.js
        If-None-Match: "a3f92b"  →  Server

If unchanged:
Server  304 Not Modified (no body)  →  Client uses cached body

If changed:
Server  200 OK + ETag: "d7e401" + new body  →  Client replaces cache
```

ETags can be **strong** (byte-for-byte identical) or **weak** (`W/"a3f92b"`, semantically equivalent). Strong ETags are used in range requests; weak ETags are fine for regular caching validation.

## 4. Diagram

<svg viewBox="0 0 680 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ETag validation flow: first request stores ETag, conditional request returns 304 if unchanged or 200 with new body if changed">
  <defs>
    <marker id="a51" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b51" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c51" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#d29922"/></marker>
  </defs>

  <!-- Boxes -->
  <rect x="20" y="20" width="80" height="26" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="60" y="37" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <rect x="580" y="20" width="80" height="26" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="620" y="37" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <!-- Phase 1: first request -->
  <text x="20" y="68" fill="#8b949e" font-size="11" font-family="sans-serif" font-weight="bold">Phase 1 — First request</text>
  <line x1="100" y1="80" x2="578" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a51)"/>
  <text x="340" y="75" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET /bundle.js</text>
  <line x1="580" y1="96" x2="102" y2="96" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b51)"/>
  <text x="340" y="91" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK  ETag: "a3f92b"  ← full body (100KB)</text>
  <!-- cache annotation -->
  <rect x="20" y="108" width="100" height="26" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="70" y="121" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">cache: body</text>
  <text x="70" y="132" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ETag="a3f92b"</text>

  <!-- Phase 2: conditional, unchanged -->
  <text x="20" y="160" fill="#8b949e" font-size="11" font-family="sans-serif" font-weight="bold">Phase 2a — Not changed (304)</text>
  <line x1="100" y1="172" x2="578" y2="172" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a51)"/>
  <text x="340" y="167" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET /bundle.js  If-None-Match: "a3f92b"</text>
  <line x1="580" y1="188" x2="102" y2="188" stroke="#d29922" stroke-width="1.5" marker-end="url(#c51)"/>
  <text x="340" y="183" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">304 Not Modified  (no body — saves 100KB!)</text>

  <!-- Phase 3: conditional, changed -->
  <text x="20" y="218" fill="#8b949e" font-size="11" font-family="sans-serif" font-weight="bold">Phase 2b — Changed (200 + new body)</text>
  <line x1="100" y1="230" x2="578" y2="230" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a51)"/>
  <text x="340" y="225" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET /bundle.js  If-None-Match: "a3f92b"</text>
  <line x1="580" y1="246" x2="102" y2="246" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b51)"/>
  <text x="340" y="241" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK  ETag: "d7e401"  ← new full body</text>
  <text x="340" y="270" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">browser replaces cached body + ETag</text>
</svg>

Conditional requests (Phase 2) send the stored ETag; the server decides 304 (free) or 200+body (paid).

## 5. Runnable example

```js
// save as etag-demo.js  —  node etag-demo.js  (no installs)
const http = require("http");
const crypto = require("crypto");

let resource = "Hello, world! (version 1)";

function etag(content) {
  return '"' + crypto.createHash("md5").update(content).digest("hex").slice(0, 8) + '"';
}

const server = http.createServer((req, res) => {
  const currentEtag = etag(resource);
  const clientEtag  = req.headers["if-none-match"];

  console.log(`Server: request received. Current ETag=${currentEtag}, client sent If-None-Match=${clientEtag}`);

  if (clientEtag === currentEtag) {
    // Resource hasn't changed — no body needed
    res.writeHead(304, { ETag: currentEtag });
    res.end();
    console.log("Server: 304 Not Modified (saved", Buffer.byteLength(resource), "bytes)\n");
  } else {
    res.writeHead(200, {
      "Content-Type": "text/plain",
      ETag: currentEtag,
      "Cache-Control": "no-cache",
    });
    res.end(resource);
    console.log("Server: 200 OK, sent", Buffer.byteLength(resource), "bytes\n");
  }
});

server.listen(3600, () => {
  const agent = new http.Agent({ keepAlive: true });

  function fetch(etag, label, cb) {
    const headers = etag ? { "if-none-match": etag } : {};
    const req = http.get({ hostname: "localhost", port: 3600, path: "/data", headers, agent }, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => {
        const receivedEtag = res.headers["etag"];
        console.log(`Client [${label}]: status=${res.statusCode} etag=${receivedEtag} body="${body}"`);
        cb(receivedEtag);
      });
    });
    req.end();
  }

  // 1) First request — no ETag yet
  fetch(null, "first fetch", (storedEtag) => {
    // 2) Second request — resource unchanged, expect 304
    fetch(storedEtag, "unchanged", (storedEtag2) => {
      // 3) Modify resource, then fetch again — expect 200
      resource = "Hello, world! (version 2)";
      fetch(storedEtag2, "after change", () => {
        agent.destroy();
        server.close();
      });
    });
  });
});
```

**How to run:** `node etag-demo.js` — observe the 304 on the second request and 200 after the resource changes.

## 6. Walkthrough

- `etag(content)` — computes an MD5 hash of the content and wraps it in quotes (ETags must be quoted strings per RFC 7232). Production servers typically use file inode+size+mtime or a content hash.
- `req.headers["if-none-match"]` — browsers send this automatically when they have a stored ETag and the cached copy is stale. We check it on the server manually here.
- `clientEtag === currentEtag` — exact string comparison. Strong ETag matching is byte-exact (including the quotes). Multiple ETags can be sent comma-separated; the server checks if any match.
- `304` response — note we still send the `ETag` header (same value) so the browser knows the cache entry is still valid and can update its freshness timestamp.
- The `agent` with `keepAlive: true` reuses one TCP connection for all three requests — typical browser behaviour.

## 7. Gotchas & takeaways

> A `304` response **must include the same headers** that would be in a `200`: `ETag`, `Cache-Control`, `Vary`. This lets the browser update its cached metadata even though no body arrives.

> Weak ETags (`W/"abc"`) cannot be used with range requests (`Range: bytes=0-999`) — only strong ETags guarantee byte-level identity. If your server compresses dynamically (different `Accept-Encoding` → different bytes but same content), use weak ETags.

> Multiple ETag values in `If-None-Match` are separated by commas: `If-None-Match: "abc", "def"`. The server returns 304 if *any* match (allowing fallback versions).

- ETags and `Last-Modified` often coexist — browsers send both `If-None-Match` and `If-Modified-Since`. The spec says `If-None-Match` takes precedence when both are present.
- Generate ETags from content hashes (MD5/SHA) not timestamps — timestamps have 1-second granularity and may lie in distributed environments.
- Frameworks like Express have `etag` enabled by default for `res.send()` — it sets a weak ETag based on response body length and hash.
- ETag validation is most valuable for frequently-accessed but infrequently-changed resources: fonts, config JSON, large images.
