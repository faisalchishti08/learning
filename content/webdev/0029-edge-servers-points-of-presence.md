---
card: webdev
gi: 29
slug: edge-servers-points-of-presence
title: Edge servers & points of presence
---

## 1. What it is

A **Point of Presence (PoP)** is a physical location where a CDN or cloud provider has installed servers — a building full of machines in Tokyo, Frankfurt, São Paulo, and hundreds of other cities. Each PoP contains one or more **edge servers**: computers that sit at the "edge" of the network, as close to end users as possible.

"Edge" is a spatial metaphor: if the internet were a wheel, your origin data centre is the hub, and the edge servers are at the rim — scattered near every group of users. An edge server does some or all of the work that the origin would otherwise have to do:

- Serve cached static files (HTML, JS, CSS, images, video).
- Terminate TLS so the encrypted connection ends nearby.
- Run lightweight logic — URL rewrites, auth checks, A/B experiments (via edge functions like Cloudflare Workers or AWS Lambda@Edge).
- Absorb and filter malicious traffic before it reaches origin.

## 2. Why & when

Speed is why. Data must physically travel through cables and routers. A fibre optic signal crosses the Atlantic in ~60 ms one-way; the speed of light in glass is not negotiable. Moving computation and content closer to users cuts that delay.

PoPs matter most when:

- Serving global audiences (different continents = different PoPs).
- Assets are large (video, high-res images) — saved bytes per hop add up.
- TLS handshake latency matters — each additional RTT to origin adds ~100 ms for users far away.
- You need DDoS mitigation — the PoP absorbs traffic before it reaches origin.

For a small internal app used only in one office, a single region is fine; PoPs are overkill.

## 3. Core concept

Imagine a pizza chain. The central kitchen (origin server) makes dough, sauce, and toppings in bulk. But delivery from one kitchen to every city would take hours. So they open local franchise locations (PoPs) stocked from the central kitchen. Customers order from the nearest franchise; only unusual orders (a topping the franchise doesn't stock) go back to the central kitchen.

How CDN routing directs users to the nearest PoP:

1. **Anycast IP** — the CDN advertises the same IP address from every PoP simultaneously. Internet routing (BGP) automatically delivers your packet to the topologically nearest PoP. Cloudflare uses this.
2. **GeoDNS** — the DNS server looks up the requester's IP geolocation and returns a different IP per region. Slower to adapt to network changes, but simpler.

Once at the PoP, the edge server checks its cache:

- **Cache hit** → respond immediately from local storage (microseconds of disk/RAM access).
- **Cache miss** → fetch from origin (hundreds of milliseconds), cache the result, respond.

**Edge functions** push even further: instead of just serving files, the edge server executes code — personalising responses, authenticating tokens, rewriting URLs — without a round trip to origin. The code runs in a lightweight sandbox (V8 isolates or WebAssembly) and starts in milliseconds, not the seconds a cold Lambda might take.

## 4. Diagram

<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Global CDN PoP layout: users routed to nearest edge server, edge fetches from origin only on cache miss">
  <defs>
    <marker id="ea" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="eb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <!-- Origin -->
  <rect x="290" y="10" width="140" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="30" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Origin</text>
  <text x="360" y="48" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">US-East data centre</text>
  <!-- PoPs -->
  <rect x="30" y="130" width="120" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">PoP — Tokyo</text>
  <text x="90" y="166" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">edge server</text>

  <rect x="200" y="130" width="120" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">PoP — London</text>
  <text x="260" y="166" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">edge server</text>

  <rect x="380" y="130" width="130" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="445" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">PoP — São Paulo</text>
  <text x="445" y="166" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">edge server</text>

  <rect x="550" y="130" width="120" height="44" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="610" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">PoP — Sydney</text>
  <text x="610" y="166" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">edge server</text>

  <!-- cache miss lines to origin -->
  <line x1="90" y1="130" x2="310" y2="56" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#eb)"/>
  <line x1="260" y1="130" x2="340" y2="56" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#eb)"/>
  <line x1="445" y1="130" x2="390" y2="56" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#eb)"/>
  <line x1="610" y1="130" x2="430" y2="56" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#eb)"/>

  <!-- Users -->
  <rect x="30" y="230" width="120" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="90" y="250" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">User (Tokyo)</text>
  <line x1="90" y1="230" x2="90" y2="174" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ea)"/>

  <rect x="200" y="230" width="120" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="260" y="250" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">User (London)</text>
  <line x1="260" y1="230" x2="260" y2="174" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ea)"/>

  <rect x="380" y="230" width="130" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="445" y="250" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">User (São Paulo)</text>
  <line x1="445" y1="230" x2="445" y2="174" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ea)"/>

  <rect x="550" y="230" width="120" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="610" y="250" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">User (Sydney)</text>
  <line x1="610" y1="230" x2="610" y2="174" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ea)"/>

  <text x="350" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">dashed = cache miss (fetches from origin)</text>
</svg>

Each user hits the nearest PoP; only cache misses travel to the origin.

## 5. Runnable example

Use `curl` with the `--resolve` flag to force a request to a specific PoP IP and compare response times versus hitting the origin directly.

```bash
# Replace with a real CDN hostname you have access to.
# This example uses Cloudflare's own website as a public CDN target.
HOSTNAME="www.cloudflare.com"

echo "=== Via CDN (nearest PoP) ==="
time curl -so /dev/null -w "HTTP %{http_code}  TTFB: %{time_starttransfer}s  Total: %{time_total}s\n" \
  "https://${HOSTNAME}/"

echo ""
echo "=== CDN PoP identity (Cloudflare-specific headers) ==="
curl -sI "https://${HOSTNAME}/" | grep -iE "cf-ray|server:|cf-cache-status"
```

**How to run:** paste into any macOS or Linux terminal with internet access.

Expected output (latency values vary by location):
```
=== Via CDN (nearest PoP) ===
HTTP 200  TTFB: 0.043s  Total: 0.109s

=== CDN PoP identity (Cloudflare-specific headers) ===
server: cloudflare
cf-ray: 8f1a2b3c4d5e6f78-NRT
cf-cache-status: DYNAMIC
```

## 6. Walkthrough

- `time curl -so /dev/null -w "..."` — `-s` silent, `-o /dev/null` discard body, `-w` print a custom format string showing HTTP status and timing.
- `time_starttransfer` is **TTFB** (Time To First Byte) — how long until the first byte of the response header arrived. This includes DNS, TCP connect, TLS handshake, and server processing. For a cached edge hit it's often under 50 ms.
- `time_total` includes downloading the full body. For our header-only comparison run, the body is minimal.
- `cf-ray` is Cloudflare's request tracing ID. The suffix (`NRT`) is the IATA airport code of the PoP that served the request — `NRT` = Narita, Tokyo. This tells you exactly which PoP handled you.
- `cf-cache-status: DYNAMIC` means the response was not served from cache (it's dynamic HTML); a static asset like a JS file would show `HIT`.
- Compare these numbers with `time curl` against a raw origin in another region — the difference is the PoP's latency savings.

## 7. Gotchas & takeaways

> **Anycast means "nearest" by BGP topology, not geography.** Due to routing policies, the "nearest" PoP in network hops might not be geographically closest. Users in some regions can get routed to a PoP in another country if peering agreements make that path cheaper for the ISP.

> **Edge functions cold-start differently from serverless.** V8-isolate-based edge functions (Cloudflare Workers) start in under 1 ms — no cold starts. Container-based ones (Lambda@Edge) can take hundreds of milliseconds on cold start. Know your platform's model.

- PoP count varies widely: Cloudflare has 300+, a smaller CDN might have 20. More PoPs = closer to more users, but cost more.
- TLS termination at the edge means the CDN decrypts your traffic — choose a CDN you trust, or use end-to-end encryption (mTLS) for sensitive payloads.
- `cf-ray` header (and equivalents on other CDNs) is invaluable for support tickets — it tells exactly which server handled the request.
- Edge functions run stateless per-request; for shared state (rate limiting counters, session data) you need a distributed KV store at the edge (e.g. Cloudflare KV, Durable Objects).
