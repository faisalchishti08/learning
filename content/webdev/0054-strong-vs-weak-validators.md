---
card: webdev
gi: 54
slug: strong-vs-weak-validators
title: Strong vs weak validators
---

## 1. What it is

A **validator** is a piece of data the server attaches to a response so that a client (or cache) can later check whether its copy is still fresh. HTTP has two kinds of validator:

**Strong validators** guarantee byte-for-byte identity. Two resources with the same strong validator are *exactly* the same — every byte matches. Strong ETags and file content hashes are strong validators. They are required for range requests (`Range: bytes=0-999`) because a cache must be sure the byte range it has is from exactly the same version.

**Weak validators** guarantee only semantic equivalence. Two versions with the same weak validator are considered *functionally the same* even if their bytes differ (e.g., a gzip-compressed vs brotli-compressed copy of the same HTML). Weak ETags are prefixed with `W/`:

```http
ETag: "a3f92b"    ← strong validator
ETag: W/"a3f92b"  ← weak validator
```

`Last-Modified` is always treated as a weak validator because it has only 1-second precision — two different versions can share the same modification timestamp.

## 2. Why & when

The strong/weak distinction matters when a server **transforms** a response. For example:

- A transparent proxy that gzip-compresses a response on the fly changes the bytes but not the content.
- A CDN that transcodes a JPEG to WebP changes bytes but delivers the same image.
- A server that adds debugging comments to a JSON response changes bytes but not the data.

A strong ETag on the original cannot be forwarded by the proxy after transformation — the bytes changed, so the ETag would lie. The proxy has two choices: strip the ETag, or convert it to a weak ETag (`W/"..."`).

**Weak ETags are fine for cache validation** (determining whether to send a `304`) but **cannot be used for range requests**. The HTTP spec is strict on this: range requests must use strong ETags because they depend on exact byte positions.

## 3. Core concept

Analogy: comparing two printouts of the same document. **Strong validation** is a byte-exact comparison — same font, same margins, same PDF checksum. **Weak validation** is "same words, same meaning" — you'd say they're the same document even if one is Arial and the other is Times New Roman, or one is A4 and one is letter-sized.

Rules for combining validators:

| Scenario | Strong ETag | Weak ETag | Last-Modified |
|---|---|---|---|
| Cache validation (304 check) | ✓ | ✓ | ✓ (weak) |
| Range requests | ✓ | ✗ | ✗ |
| `If-Match` (write protection) | ✓ | ✗ | ✗ |
| `If-None-Match` | ✓ | ✓ | — |

Comparison rules (RFC 7232):
- **Strong comparison**: two ETags match only if *both are strong* and the opaque values are identical.
- **Weak comparison**: two ETags match if their opaque values are identical regardless of strength prefix.

```
Strong compare "abc" vs "abc"   → match
Strong compare "abc" vs W/"abc" → no match (one is weak)
Weak compare   "abc" vs W/"abc" → match
Weak compare  W/"abc" vs W/"def"→ no match (different value)
```

## 4. Diagram

<svg viewBox="0 0 680 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Strong vs weak validators: strong ETags allow range requests and exact byte matching; weak ETags only allow semantic equality checks">
  <defs>
    <marker id="a54" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b54" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="c54" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Strong ETag column -->
  <rect x="20" y="10" width="290" height="34" rx="6" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="33" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Strong ETag: "a3f92b"</text>

  <rect x="30" y="56" width="270" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="73" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">✓ Cache validation (If-None-Match)</text>
  <rect x="30" y="84" width="270" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="101" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">✓ Range requests (If-Range)</text>
  <rect x="30" y="112" width="270" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="129" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">✓ Optimistic locking (If-Match)</text>
  <rect x="30" y="140" width="270" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="157" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Byte-exact identity guaranteed</text>

  <!-- Weak ETag column -->
  <rect x="360" y="10" width="290" height="34" rx="6" fill="#79c0ff" opacity="0.15" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="505" y="33" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Weak ETag: W/"a3f92b"</text>

  <rect x="370" y="56" width="270" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="505" y="73" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">✓ Cache validation (If-None-Match)</text>
  <rect x="370" y="84" width="270" height="24" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="1"/>
  <text x="505" y="101" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">✗ Range requests — forbidden</text>
  <rect x="370" y="112" width="270" height="24" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="1"/>
  <text x="505" y="129" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">✗ Optimistic locking — forbidden</text>
  <rect x="370" y="140" width="270" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="505" y="157" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Semantic equivalence only</text>

  <!-- Comparison examples -->
  <text x="20" y="192" fill="#e6edf3" font-size="12" font-family="sans-serif" font-weight="bold">Comparison results:</text>
  <rect x="20" y="202" width="630" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="335" y="217" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Strong: "abc" vs "abc" → match   |   "abc" vs W/"abc" → no match</text>
  <rect x="20" y="228" width="630" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="335" y="243" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Weak:   "abc" vs W/"abc" → match  |   W/"abc" vs W/"def" → no match</text>
  <text x="20" y="272" fill="#8b949e" font-size="11" font-family="sans-serif">Last-Modified: always treated as weak (1-second granularity = possible false equality)</text>
</svg>

Strong validators (left) unlock all conditional request features; weak validators (right) work for cache invalidation but not for byte-sensitive operations like range requests.

## 5. Runnable example

```js
// save as validators-demo.js  —  node validators-demo.js  (no installs)
const http   = require("http");
const crypto = require("crypto");

// Two versions that are semantically equivalent but bytes differ (e.g. different whitespace)
const contentV1 = '{"name":"Alice","age":30}';
const contentV2 = '{ "name": "Alice", "age": 30 }'; // same data, different formatting

function strongEtag(s) {
  return '"' + crypto.createHash("sha256").update(s).digest("hex").slice(0, 8) + '"';
}
function weakEtag(s) {
  // Semantic hash: parse JSON, re-serialise canonically
  const parsed = JSON.stringify(JSON.parse(s));
  return 'W/"' + crypto.createHash("sha256").update(parsed).digest("hex").slice(0, 8) + '"';
}

console.log("Content V1:", contentV1);
console.log("Content V2:", contentV2);
console.log();
console.log("Strong ETag V1:", strongEtag(contentV1));
console.log("Strong ETag V2:", strongEtag(contentV2), "← different! bytes differ");
console.log();
console.log("Weak ETag V1:", weakEtag(contentV1));
console.log("Weak ETag V2:", weakEtag(contentV2), "← same! same JSON data");
console.log();

// Demonstrate comparison rules
function strongCompare(a, b) {
  if (a.startsWith('W/') || b.startsWith('W/')) return false;
  return a === b;
}
function weakCompare(a, b) {
  return a.replace(/^W\//, '') === b.replace(/^W\//, '');
}

const pairs = [
  ['"abc"', '"abc"'],
  ['"abc"', 'W/"abc"'],
  ['W/"abc"', 'W/"abc"'],
  ['W/"abc"', 'W/"def"'],
];

console.log("Comparison table:");
pairs.forEach(([a, b]) => {
  console.log(
    `  ${a.padEnd(12)} vs ${b.padEnd(12)}  strong=${strongCompare(a,b) ? "match" : "no   "}  weak=${weakCompare(a,b) ? "match" : "no   "}`
  );
});

// Show that Last-Modified is effectively weak
const server = http.createServer((req, res) => {
  const etag = req.url === "/strong" ? strongEtag(contentV1) : weakEtag(contentV1);
  res.writeHead(200, {
    "Content-Type": "application/json",
    "ETag": etag,
    "Last-Modified": new Date().toUTCString(), // always weak
  });
  res.end(contentV1);
});

server.listen(3900, () => {
  ["strong", "weak"].forEach((type) => {
    http.get(`http://localhost:3900/${type}`, (res) => {
      const etag = res.headers["etag"];
      const lm   = res.headers["last-modified"];
      console.log(`\n/${type} endpoint:`);
      console.log(`  ETag: ${etag}`);
      console.log(`  Last-Modified: ${lm} (always weak — 1s precision)`);
      res.resume();
      res.on("end", () => {
        if (type === "weak") server.close();
      });
    }).end();
  });
});
```

**How to run:** `node validators-demo.js`

## 6. Walkthrough

- `strongEtag(s)` hashes the raw bytes — the resulting ETag changes even if only whitespace differs.
- `weakEtag(s)` parses and re-serialises JSON to get a canonical form, then hashes it. V1 and V2 produce the same weak ETag because they represent the same data.
- `strongCompare(a, b)`: RFC 7232 strong comparison — both ETags must lack the `W/` prefix and must be identical. Any weak ETag immediately returns false.
- `weakCompare(a, b)`: strips the `W/` prefix before comparing. Treats `"abc"` and `W/"abc"` as a match.
- The comparison table shows all four pairings, matching the RFC examples exactly.
- The server demonstrates both: `/strong` returns a strong ETag (no `W/`), `/weak` returns a weak ETag. Both endpoints also send `Last-Modified`, which is inherently weak regardless of the label.

## 7. Gotchas & takeaways

> If your server compresses responses (gzip, br) on the fly, the bytes change between requests with different `Accept-Encoding`. Nginx automatically converts strong ETags to weak ETags when it compresses — check your ETag header if debugging range-request failures after adding compression.

> **Range requests require strong ETags.** If a download manager requests `Range: bytes=0-999` with `If-Range: "abc"` and the server has a weak ETag, the server must ignore the `If-Range` and return the full file. This can silently break resumable downloads.

- Strong ETag + content-hash filename = best-practice for versioned static assets.
- Weak ETags are appropriate for: compressed variants of the same content, semantically identical representations, any case where byte identity isn't meaningful.
- `Last-Modified` is always "weak" by the HTTP spec — even an exact-second match doesn't guarantee byte equality.
- Express's default ETags are weak (`W/"..."`) — fine for cache validation, but not for range requests or `If-Match` write protection.
