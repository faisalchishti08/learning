---
card: webdev
gi: 17
slug: ttl-dns-caching
title: TTL & DNS caching
---

## 1. What it is

Every DNS resource record carries a **TTL (Time To Live)** — an integer number of seconds that tells caches how long to hold the record before discarding it and fetching a fresh copy. A record with `TTL 3600` can be cached for one hour; after that, the next query must go back to the authoritative server.

TTL is the control knob for the speed/freshness trade-off in DNS. It governs caching at multiple layers: the browser, the OS, and recursive resolvers across the internet.

## 2. Why & when

DNS is a globally distributed system with no push updates. When you change an IP address in your DNS zone, you cannot send a notification to every resolver on earth. Instead, caches expire naturally based on TTL, and each resolver fetches the new value after the old one expires.

This matters in two scenarios:

- **Planned change**: lower the TTL days in advance (e.g. from 86 400 to 300 seconds), make the change, then raise it again once you're confident. The low TTL shrinks the blast radius if you need to roll back.
- **Emergency change**: if a server goes down and you need to point the domain elsewhere, a high TTL means the world is stuck with the old IP for hours.

Balancing TTL: high values reduce resolver load and speed up repeat lookups; low values allow faster propagation but increase query volume to your authoritative servers.

## 3. Core concept

Think of TTL like a sell-by date on a carton of milk at the supermarket. The supermarket (recursive resolver) buys a batch from the dairy (authoritative server) and stamps each carton with an expiry. Shoppers (browsers) take cartons from the shelf and use them until they expire. Once expired, the supermarket orders a fresh batch — but only then, not before.

The caching layers, from closest to furthest:

1. **Browser DNS cache** — Chrome, Firefox, and Safari each cache DNS records internally, often ignoring the OS resolver. Chrome respects TTL but caps entries at 60–300 seconds.
2. **OS stub resolver cache** — `nscd`, `systemd-resolved` (Linux) or the macOS DNS cache hold records for their TTL. `sudo dscacheutil -flushcache` (macOS) or `resolvectl flush-caches` (Linux) clears it.
3. **Router / LAN DNS cache** — most home routers run a small DNS forwarder/cache that serves local devices.
4. **ISP / public recursive resolver** — `1.1.1.1`, `8.8.8.8`, and ISP resolvers cache records for their TTL. These servers serve millions of clients, so a popular domain may be cached continuously.

When a record is cached, the TTL counts down from its original value. A resolver that fetched a `TTL 3600` record 30 minutes ago tells clients the remaining TTL is 1800 — not the original 3600. This "TTL decrement" prevents stale records from living forever in cascaded caches.

## 4. Diagram

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DNS TTL caching layers from browser to authoritative server, showing TTL countdown">
  <defs>
    <marker id="arro" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Authoritative (far right) -->
  <rect x="500" y="120" width="130" height="56" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="565" y="143" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Authoritative</text>
  <text x="565" y="159" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">nameserver</text>
  <text x="565" y="172" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">TTL = 3600 s</text>

  <!-- Recursive resolver -->
  <rect x="340" y="120" width="130" height="56" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="405" y="143" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Recursive</text>
  <text x="405" y="159" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">resolver</text>
  <text x="405" y="172" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">caches 3600 s</text>

  <!-- OS cache -->
  <rect x="180" y="120" width="130" height="56" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="245" y="143" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">OS stub</text>
  <text x="245" y="159" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">resolver</text>
  <text x="245" y="172" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">caches remaining TTL</text>

  <!-- Browser -->
  <rect x="20" y="120" width="130" height="56" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="143" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="85" y="159" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">DNS cache</text>
  <text x="85" y="172" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">internal cache (60-300 s)</text>

  <!-- Arrows (right to left = data flow on cold miss) -->
  <line x1="498" y1="148" x2="472" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arro)"/>
  <line x1="338" y1="148" x2="312" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arro)"/>
  <line x1="178" y1="148" x2="152" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arro)"/>

  <!-- TTL timeline -->
  <rect x="20" y="220" width="610" height="14" rx="4" fill="#0d1117"/>
  <rect x="20" y="220" width="610" height="14" rx="4" fill="#6db33f" opacity="0.25"/>
  <!-- Zones on timeline -->
  <line x1="173" y1="216" x2="173" y2="238" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="326" y1="216" x2="326" y2="238" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="479" y1="216" x2="479" y2="238" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <text x="96"  y="255" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">browser cache</text>
  <text x="249" y="255" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">OS cache</text>
  <text x="402" y="255" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">resolver cache</text>
  <text x="545" y="255" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">authoritative</text>

  <text x="20"  y="280" fill="#8b949e" font-size="10" font-family="sans-serif">Now</text>
  <text x="590" y="280" fill="#8b949e" font-size="10" font-family="sans-serif">TTL expires</text>
</svg>

Each caching layer holds the record until its TTL countdown reaches zero; only then does it re-query the next layer to the right.

## 5. Runnable example

```bash
# Watch TTL decrement in real time with dig
# No installs — built into macOS/Linux

# Run this command twice, ~10 seconds apart
dig example.com A +noall +answer

# First run — fresh from resolver cache:
# example.com.  3600  IN  A  93.184.216.34
# Second run — 10 seconds later:
# example.com.  3590  IN  A  93.184.216.34

# Flush your local OS DNS cache and observe the TTL reset:
# macOS:
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder
# Then query again — TTL will be back to 3600 (fetched fresh):
dig example.com A +noall +answer
```

**How to run:** paste the `dig` commands into a terminal on macOS or Linux. The `sudo` flush command needs your password. On Windows: `ipconfig /flushdns` then `Resolve-DnsName example.com`.

Expected output (two queries 10 seconds apart):
```
example.com.  3600  IN  A  93.184.216.34
example.com.  3590  IN  A  93.184.216.34
```

## 6. Walkthrough

- `dig example.com A +noall +answer` — `+noall` suppresses all output sections, `+answer` re-enables only the answer section. This gives a clean, minimal view showing name, TTL, class, type, and value.
- The second column in each answer line is the **remaining TTL in seconds**. Running the command twice shows the countdown in action: 3600 → 3590 after 10 seconds.
- `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder` — on macOS, `dscacheutil -flushcache` clears the DNS cache entries and `killall -HUP mDNSResponder` restarts the mDNSResponder process (Apple's DNS resolver daemon). After flushing, the next `dig` hits the recursive resolver, which may itself still have a cached copy — explaining why the TTL after flushing isn't always exactly the original value.
- The TTL in the `dig` output is what the **resolver told you**, not what the authoritative record says — it's already been decremented by however long the resolver has been caching it.

## 7. Gotchas & takeaways

> **Lowering TTL before a change is the correct technique.** Set TTL to 300 (5 minutes) at least one full old-TTL period before your planned change. That way, by change time, all resolvers are re-querying every 5 minutes. After the change is stable, raise TTL back to 3600 or 86 400.

> **Flushing your own cache does not fix it for the world.** You can clear your local OS or browser cache instantly, but the ISP's resolver cache will hold the old record until its TTL expires. That's what "DNS propagation" actually is — waiting for distributed resolver caches to expire.

- Minimum TTL in an SOA record sets a floor: resolvers should not cache any record for less than this value, even if the record's own TTL is lower.
- Some browsers (notably Chrome) cap DNS cache at 60 seconds internally, regardless of the record's TTL.
- Negative TTL (NXDOMAIN caching) — the SOA's minimum field also controls how long "this domain does not exist" responses are cached.
- `dig +stats example.com` shows query time; repeated queries show near-0 ms response once cached vs. tens of ms on a cold miss.
- High TTLs (86 400 = 24 hours) make sense for stable records like NS and SOA; low TTLs (60–300) make sense for records that change during deployments.
