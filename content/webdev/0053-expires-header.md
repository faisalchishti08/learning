---
card: webdev
gi: 53
slug: expires-header
title: Expires header
---

## 1. What it is

The **`Expires`** header is an HTTP/1.0 response header that sets an absolute date and time after which the cached response is considered stale:

```http
Expires: Thu, 01 Jan 2026 00:00:00 GMT
```

It is the predecessor to `Cache-Control: max-age`. A browser that has a cached response compares the current clock time to the `Expires` value. If now is past the `Expires` date, the cached copy is stale and the browser must revalidate or re-fetch.

A value in the past (or `0`) means "already expired — always revalidate":

```http
Expires: 0
```

## 2. Why & when

`Expires` was introduced in HTTP/1.0 (1996) before `Cache-Control` existed. It remains part of HTTP for backwards compatibility and is still sent by many servers alongside `Cache-Control` headers.

Prefer `Cache-Control: max-age` over `Expires` in new code because:

1. **Clock skew** — `Expires` depends on both client and server clocks being synchronised. If they differ by an hour, caching is off by an hour. `max-age` is relative (seconds from now), immune to clock disagreement.
2. **Predictability** — `max-age=3600` means "one hour from this response" always. An `Expires` date requires recomputing the header on every deploy to avoid accidentally setting a date in the past.
3. **Precedence** — when both `Cache-Control: max-age` and `Expires` are present, `max-age` wins. `Expires` is only consulted when `Cache-Control` is absent entirely.

Still useful to know because: some CDNs, proxies, and old load balancers still inspect `Expires`; some analytics tools report on it; legacy systems you maintain may only speak HTTP/1.0.

## 3. Core concept

Analogy: a "best before" date printed on milk. The factory decides the date at bottling time. Whether the date makes sense depends on the factory and the shop having synchronised calendars. If the shop's clock is an hour ahead, the milk appears expired before it actually is — that's the clock skew problem.

Contrast with `max-age`, which is like saying "good for 7 days from when you buy it" — independent of wall time.

How the browser uses `Expires`:

```
Response received at: 2025-06-01 12:00:00 (browser local clock)
Expires:              2025-06-08 12:00:00 GMT

Freshness lifetime = Expires - response_date = 7 days
If current time < Expires → serve from cache (fresh)
If current time ≥ Expires → revalidate (stale)
```

When `Expires: 0` or a past date is set, the response is immediately stale — every request revalidates. Servers use this to say "never use a cached copy without checking."

Precedence rules (highest to lowest):

```
1. Cache-Control: no-store        → never cache
2. Cache-Control: max-age=N       → use this TTL
3. Expires: <date>                → use this only if no max-age
4. Heuristic caching              → browser guesses based on Last-Modified
```

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Expires header timeline showing fresh window vs stale, and clock skew problem">
  <defs>
    <marker id="a53" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b53" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Timeline bar -->
  <text x="20" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">Expires timeline</text>
  <line x1="20" y1="50" x2="640" y2="50" stroke="#8b949e" stroke-width="2"/>

  <!-- Response received -->
  <line x1="80" y1="40" x2="80" y2="60" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="35" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">response</text>
  <text x="80" y="75" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">received</text>

  <!-- Expires date -->
  <line x1="440" y1="40" x2="440" y2="60" stroke="#d29922" stroke-width="2"/>
  <text x="440" y="35" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">Expires:</text>
  <text x="440" y="75" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">Jan 1 2026</text>

  <!-- Fresh zone -->
  <rect x="80" y="88" width="360" height="28" rx="4" fill="#6db33f" opacity="0.3"/>
  <text x="260" y="106" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">FRESH — serve from cache</text>

  <!-- Stale zone -->
  <rect x="440" y="88" width="200" height="28" rx="4" fill="#d29922" opacity="0.3"/>
  <text x="540" y="106" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">STALE — revalidate</text>

  <!-- Clock skew problem -->
  <text x="20" y="148" fill="#e6edf3" font-size="12" font-family="sans-serif" font-weight="bold">Clock skew problem</text>
  <rect x="20" y="158" width="290" height="60" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="165" y="178" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Server clock: 2025-06-01 12:00 UTC</text>
  <text x="165" y="196" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Client clock: 2025-06-01 13:00 UTC (+1h drift)</text>
  <text x="165" y="214" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Expires: Jun 01 12:30 → already stale for client!</text>

  <!-- max-age comparison -->
  <rect x="340" y="158" width="320" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="178" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Cache-Control: max-age=1800</text>
  <text x="500" y="196" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">→ fresh for 30 min from receipt</text>
  <text x="500" y="214" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">clock skew doesn't matter</text>

  <!-- Precedence note -->
  <text x="20" y="248" fill="#8b949e" font-size="11" font-family="sans-serif">If both present: Cache-Control: max-age wins over Expires</text>
</svg>

`Expires` marks a fixed point in time; content is fresh until that moment, then stale. Clock drift between client and server can make the window unexpectedly short or long. `max-age` avoids this with a relative duration.

## 5. Runnable example

```js
// save as expires-demo.js  —  node expires-demo.js  (no installs)
const http = require("http");

function futureDate(seconds) {
  return new Date(Date.now() + seconds * 1000).toUTCString();
}

const server = http.createServer((req, res) => {
  if (req.url === "/expires-only") {
    // Old-style: absolute date, no Cache-Control
    res.writeHead(200, {
      "Content-Type": "text/plain",
      "Expires": futureDate(3600),          // good for 1 hour
    });
    res.end("Cached with Expires only");

  } else if (req.url === "/both") {
    // Modern: Cache-Control + Expires for old proxies
    res.writeHead(200, {
      "Content-Type": "text/plain",
      "Cache-Control": "public, max-age=3600",
      "Expires": futureDate(3600),          // ignored by modern caches; fallback for HTTP/1.0 proxies
    });
    res.end("Cached with both headers");

  } else if (req.url === "/expired") {
    // Force immediate revalidation
    res.writeHead(200, {
      "Content-Type": "text/plain",
      "Expires": "0",                       // past/zero = already expired
    });
    res.end("Immediately stale");
  }
});

server.listen(3800, () => {
  const paths = ["/expires-only", "/both", "/expired"];
  let done = 0;

  paths.forEach((path) => {
    http.get(`http://localhost:3800${path}`, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => {
        console.log(`${path.padEnd(20)} Expires: ${res.headers["expires"] || "(none)"
          }  Cache-Control: ${res.headers["cache-control"] || "(none)"}`);
        if (++done === paths.length) server.close();
      });
    }).end();
  });
});
```

**How to run:** `node expires-demo.js` — see how `Expires` and `Cache-Control` coexist.

Expected output (dates will be ~1 hour in the future):
```
/expires-only        Expires: Thu, 01 Jun 2025 13:00:00 GMT  Cache-Control: (none)
/both                Expires: Thu, 01 Jun 2025 13:00:00 GMT  Cache-Control: public, max-age=3600
/expired             Expires: 0                              Cache-Control: (none)
```

## 6. Walkthrough

- `futureDate(3600)` — computes an absolute UTC date string 3600 seconds from now. This must be recomputed on every deploy; a hardcoded date quickly becomes a date in the past.
- `/expires-only` — demonstrates HTTP/1.0-style caching. Browsers will cache this until the `Expires` time, but `Cache-Control` takes priority in HTTP/1.1+ caches if present elsewhere.
- `/both` — the recommended approach for maximum compatibility: `Cache-Control: max-age` for modern clients, `Expires` as a fallback for old HTTP/1.0-only proxies and CDN edge nodes.
- `Expires: 0` — RFC 7234 §5.3 says "a value of 0 means the response is already expired." This forces revalidation on every request. Compare to `Cache-Control: no-cache` which is the modern equivalent.

## 7. Gotchas & takeaways

> Never hardcode an `Expires` date far in the future. When that date arrives, every cache in the world starts revalidating simultaneously — and if you want to change the caching policy before the date, you can't. Use `Cache-Control: max-age` with a content-hash filename instead.

> `Expires: 0` is **not** the same as `Expires: <current date>` — `0` is a sentinel value meaning "immediately stale," not a UNIX timestamp. Sending `Expires: Thu, 01 Jan 1970 00:00:00 GMT` (UNIX epoch) has the same effect and is more technically correct.

- `Cache-Control: max-age` always overrides `Expires` in HTTP/1.1+ — send both only for legacy proxy compatibility.
- Clock synchronisation (NTP) matters for `Expires` — unsynchronised servers produce unreliable cache windows.
- `Expires` has second-level granularity; you cannot set it shorter than 1 second.
- Frameworks (Express, Django, Rails) default to `Cache-Control` headers, not `Expires`. You rarely need to set `Expires` in new code.
