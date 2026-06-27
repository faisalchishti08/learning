---
card: webdev
gi: 28
slug: content-delivery-networks-cdn
title: Content Delivery Networks (CDN)
---

## 1. What it is

A **Content Delivery Network (CDN)** is a globally distributed network of servers (called **edge servers** or **PoPs — Points of Presence**) that store copies of your content closer to your users. Instead of every request travelling to your single origin server in, say, Virginia, a user in Tokyo gets the content from a CDN server in Tokyo.

CDNs were invented to serve static files fast — images, CSS, JavaScript, videos — but modern CDNs also:

- Terminate TLS at the edge (fewer hops before encryption ends).
- Cache entire HTML pages or API responses.
- Run serverless functions at the edge (Cloudflare Workers, Vercel Edge Functions).
- Absorb DDoS traffic before it reaches your origin.

Major CDNs: Cloudflare, AWS CloudFront, Fastly, Akamai, Azure CDN.

## 2. Why & when

The core problem CDNs solve is **physics**: light through fibre travels at roughly 200,000 km/s, and a round trip across the Atlantic takes ~70–80 ms minimum, no matter how fast your servers are. A Tokyo user hitting a Virginia origin adds ~150 ms of pure latency per request — before any processing.

CDNs collapse that distance. The same Tokyo user hitting a Cloudflare PoP 5 km away adds <5 ms.

Secondary benefits:

- **Origin offload** — the CDN serves cached responses, so your origin handles a fraction of the traffic.
- **DDoS protection** — the CDN's massive bandwidth absorbs volumetric attacks.
- **High availability** — if one PoP fails, requests route to the next nearest.

Use a CDN for any public-facing site or app where performance matters. Skip it for internal tools, auth-gated APIs that can't cache, or private data.

## 3. Core concept

Think of a CDN like a bookstore chain. The publisher (your origin) prints books once. Bookstores (edge servers) in every city stock copies. When someone in Tokyo wants a book, they walk to the local store — not to the publisher in New York. If the local store is out of stock (cache miss), it orders from the publisher (cache fill) and stocks the shelf for the next customer.

The CDN request flow:

1. User's DNS lookup for `assets.example.com` returns the IP of the nearest CDN edge server (via anycast or geo DNS).
2. Request hits the edge server.
3. **Cache hit** → edge returns the cached response instantly, origin never involved.
4. **Cache miss** → edge forwards the request to the origin, caches the response, then returns it.
5. Future requests for the same resource go to the cache until the `Cache-Control` TTL expires.

**Cache invalidation** is the hard part: if you deploy new JavaScript, the CDN might serve the stale version for hours. Solutions:
- **Content-addressed URLs** — embed a hash in the filename (`app.abc123.js`). New deploy = new filename = new cache entry.
- **CDN purge API** — explicitly tell the CDN to evict specific paths on deploy.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CDN request flow: users in Tokyo and London hit nearby edge servers; only cache misses reach the origin in Virginia">
  <defs>
    <marker id="cd" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cm" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <!-- Origin -->
  <rect x="290" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="365" y="42" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Origin Server</text>
  <text x="365" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Virginia, USA</text>
  <!-- Edge Tokyo -->
  <rect x="30" y="130" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="152" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Edge PoP</text>
  <text x="100" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Tokyo</text>
  <!-- Edge London -->
  <rect x="530" y="130" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="600" y="152" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Edge PoP</text>
  <text x="600" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">London</text>
  <!-- cache miss arrows origin<->edge -->
  <line x1="145" y1="140" x2="295" y2="60" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="5,3" marker-end="url(#cm)"/>
  <text x="195" y="90" fill="#8b949e" font-size="9" font-family="sans-serif" transform="rotate(-30,195,90)">cache miss only</text>
  <line x1="530" y1="140" x2="440" y2="60" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="5,3" marker-end="url(#cm)"/>
  <text x="465" y="90" fill="#8b949e" font-size="9" font-family="sans-serif" transform="rotate(30,465,90)">cache miss only</text>
  <!-- User Tokyo -->
  <rect x="30" y="220" width="140" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="100" y="240" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">User (Tokyo)</text>
  <line x1="100" y1="220" x2="100" y2="180" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cd)"/>
  <text x="116" y="202" fill="#6db33f" font-size="9" font-family="sans-serif">&lt;5ms</text>
  <!-- User London -->
  <rect x="530" y="220" width="140" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="600" y="240" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">User (London)</text>
  <line x1="600" y1="220" x2="600" y2="180" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cd)"/>
  <text x="616" y="202" fill="#6db33f" font-size="9" font-family="sans-serif">&lt;5ms</text>
</svg>

Edge PoPs serve cached content locally; only cache misses travel all the way to the origin.

## 5. Runnable example

Use `curl` to see CDN caching in action via HTTP response headers — no installs needed.

```bash
# Fetch a CDN-served asset twice and inspect caching headers
URL="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js"

echo "=== First request ==="
curl -sI "$URL" | grep -iE "cache-control|cf-cache-status|age:|x-cache|content-length"

echo ""
echo "=== Second request (should be a cache hit) ==="
curl -sI "$URL" | grep -iE "cache-control|cf-cache-status|age:|x-cache|content-length"
```

Expected output:
```
=== First request ===
content-length: 87551
cache-control: public, max-age=30672000
cf-cache-status: HIT
age: 1234567

=== Second request (should be a cache hit) ==="
content-length: 87551
cache-control: public, max-age=30672000
cf-cache-status: HIT
age: 1234568
```

**How to run:** paste into any terminal with internet access. `curl` ships with macOS; install via package manager on Linux.

## 6. Walkthrough

- `-sI` — silent mode (`-s`) plus header-only (`-I`). We ask the server to return only HTTP headers, not the body.
- `cache-control: public, max-age=30672000` — the origin told the CDN and browser to cache this file for ~355 days. Because the filename includes the version (`3.7.1`), a new jQuery version gets a different URL.
- `cf-cache-status: HIT` — Cloudflare's proprietary header confirming this request was served from the edge cache, not forwarded to the origin. Other CDNs use similar headers (`X-Cache: HIT`).
- `age: 1234567` — how many seconds ago this cache entry was filled from the origin. A fresh cache entry starts at `age: 0`.
- If you see `cf-cache-status: MISS` on the first request, the PoP nearest to you didn't have the file cached yet; it fetched from origin and cached it. A second request should then show `HIT`.
- `content-length` is consistent across both requests — same file, same bytes.

## 7. Gotchas & takeaways

> **CDNs cache by URL, not by content.** Deploy a new `main.js` to the same path? Users get the stale version until the TTL expires or you purge. Always use content-addressed filenames (e.g. `main.a3f9c2.js`) for versioned assets, or wire your deploy pipeline to purge on push.

> **Private or personalised content must not be CDN-cached by default.** A page showing `Hello, Alice` should never be served to Bob. Set `Cache-Control: private` or `no-store` for authenticated responses unless you're using a CDN that can vary cache by cookie/header intelligently (and you've configured it correctly).

- CDNs terminate TLS at the edge — the first encrypted hop is shorter, which speeds up HTTPS page loads.
- "Cache miss" on first visitor is unavoidable; pre-warming (hitting URLs after deploy) reduces cold-cache misses in production.
- CDN costs are typically egress-based — heavy video traffic is expensive; negotiate bandwidth commitments for large scale.
- Most CDNs also offer WAF (Web Application Firewall) and bot protection at the edge — worth enabling alongside caching.
