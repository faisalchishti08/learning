---
card: webdev
gi: 15
slug: dns-resolution-recursive-authoritative
title: DNS resolution (recursive & authoritative)
---

## 1. What it is

**DNS resolution** is the process of converting a domain name (`example.com`) into an IP address (`93.184.216.34`). It works by asking a chain of servers in the domain hierarchy until one can give a definitive answer.

There are two distinct roles in this chain:

- A **recursive resolver** (also called a recursive nameserver or full-service resolver) does the legwork: it asks other servers on your behalf, caches the results, and returns the final answer to you. Your ISP or a public service like `8.8.8.8` (Google) or `1.1.1.1` (Cloudflare) runs these.
- An **authoritative nameserver** is the source of truth for a specific zone. It holds the actual DNS records and answers with authority — no guessing, no caching, just the records it owns.

## 2. Why & when

Without a structured resolution process, querying the internet would require you to know in advance which server holds every domain — impossible at scale. The recursive/authoritative split solves this:

- **Recursive resolvers** shield clients from complexity. Your browser only ever talks to one resolver; the resolver handles all the sub-queries.
- **Authoritative servers** let each domain owner control their own records independently, with no central authority needing to know every IP in the world.
- **Caching** (covered in the TTL tutorial) makes the system fast: popular names are resolved once and reused thousands of times.

You think about this when debugging `ERR_NAME_NOT_RESOLVED`, when a DNS change you made isn't visible yet, or when choosing a DNS provider for speed and reliability.

## 3. Core concept

Think of resolution like a library research desk. You (the browser) ask the **reference librarian** (recursive resolver) for a book. The librarian doesn't know every book, but knows which **index catalogue** to check first. The index (root nameserver) says "TLD librarians handle `.com` books — ask them." The TLD librarian says "the `example.com` department has your book — go there." The **department** (authoritative nameserver) hands you the book directly.

The full query path for `www.example.com`:

1. **Stub resolver** — a tiny DNS client in your OS. It forwards the query to the configured recursive resolver (usually your router, which forwards to your ISP or a configured server like `1.1.1.1`).
2. **Recursive resolver** — checks its cache first. On a cold miss, it starts climbing the hierarchy:
   - Queries a **root nameserver** (one of 13 clusters): "who handles `.com`?" → gets NS records for `.com` TLD servers.
   - Queries a **TLD nameserver** for `.com`: "who handles `example.com`?" → gets NS records pointing to `example.com`'s authoritative servers (e.g. `a.iana-servers.net`).
   - Queries the **authoritative nameserver** for `example.com`: "what is the A record for `www.example.com`?" → gets `93.184.216.34`.
3. **Returns** the IP to the stub resolver, which gives it to the browser. The recursive resolver also caches the answer for the record's TTL.

The authoritative nameserver says "I am the authority — this answer is definitive." Recursive resolvers mark their answers as "non-authoritative" because they got them second-hand.

## 4. Diagram

<svg viewBox="0 0 660 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DNS resolution query chain from browser through recursive resolver to root, TLD, and authoritative nameservers">
  <defs>
    <marker id="fwd" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="ret" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Browser -->
  <rect x="10" y="130" width="110" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="151" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="65" y="169" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">stub resolver</text>

  <!-- Recursive resolver -->
  <rect x="190" y="130" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="255" y="151" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Recursive</text>
  <text x="255" y="167" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Resolver</text>
  <text x="255" y="183" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1.1.1.1 / 8.8.8.8</text>

  <!-- Root -->
  <rect x="390" y="20" width="120" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="450" y="40" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Root</text>
  <text x="450" y="56" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">nameserver (13)</text>

  <!-- TLD -->
  <rect x="390" y="140" width="120" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="450" y="160" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">TLD</text>
  <text x="450" y="176" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">nameserver (.com)</text>

  <!-- Authoritative -->
  <rect x="390" y="254" width="120" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="450" y="274" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Authoritative</text>
  <text x="450" y="290" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">a.iana-servers.net</text>

  <!-- Browser ↔ resolver (query / answer) -->
  <line x1="122" y1="148" x2="188" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fwd)"/>
  <line x1="188" y1="162" x2="122" y2="162" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ret)"/>
  <text x="155" y="142" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">query</text>
  <text x="155" y="178" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">93.184.216.34</text>

  <!-- Resolver ↔ Root -->
  <line x1="330" y1="148" x2="388" y2="58" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fwd)"/>
  <line x1="386" y1="62" x2="332" y2="155" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ret)"/>
  <text x="368" y="95" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" transform="rotate(-28,368,95)">1. who handles .com?</text>

  <!-- Resolver ↔ TLD -->
  <line x1="322" y1="163" x2="388" y2="163" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fwd)"/>
  <line x1="388" y1="170" x2="322" y2="170" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ret)"/>
  <text x="355" y="158" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">2. who handles example.com?</text>

  <!-- Resolver ↔ Authoritative -->
  <line x1="330" y1="172" x2="388" y2="258" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fwd)"/>
  <line x1="386" y1="262" x2="332" y2="176" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ret)"/>
  <text x="368" y="225" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" transform="rotate(35,368,225)">3. IP for www.example.com?</text>
</svg>

Green arrows = queries (forward); blue arrows = answers (back). All queries go through the recursive resolver so the browser only ever talks to one server.

## 5. Runnable example

```bash
# Trace DNS resolution step-by-step with dig +trace
# No installs — built into macOS and Linux

dig +trace www.example.com

# The output shows every server queried in order:
# 1. Root nameservers (. NS)
# 2. .com TLD nameservers
# 3. example.com authoritative nameserver
# 4. Final A record answer

# Also compare: recursive (non-authoritative) vs authoritative answer:
dig www.example.com A              # non-authoritative (from your recursive resolver cache)
dig @a.iana-servers.net www.example.com A  # authoritative answer directly from the source
```

**How to run:** paste into a terminal (macOS/Linux). `dig` is pre-installed on macOS; on Ubuntu/Debian: `apt install dnsutils`.

Expected snippet from `+trace` (abbreviated):
```
. 518400  IN  NS  a.root-servers.net.
com. 172800 IN  NS  a.gtld-servers.net.
example.com. 86400 IN NS  a.iana-servers.net.
www.example.com. 3600 IN A  93.184.216.34
```

## 6. Walkthrough

- `dig +trace www.example.com` — forces `dig` to simulate the full recursive walk starting from the root. Without `+trace`, `dig` just asks your local resolver which returns a cached (non-authoritative) answer.
- First section (`. NS`) — the root zone's nameservers. These are the starting point of every resolution; `dig` picks one randomly.
- Second section (`com. NS`) — the root server returned NS records for `.com`, pointing to the TLD servers operated by Verisign.
- Third section (`example.com. NS`) — the `.com` TLD server returned the NS records for `example.com`, pointing to IANA's authoritative servers.
- Fourth section (A record) — the authoritative server directly returned the IP. Notice the `flags: qr aa` in the output — `aa` means **Authoritative Answer**, the definitive source.
- `dig @a.iana-servers.net www.example.com A` — bypasses your resolver, querying the authoritative server directly. The `aa` flag confirms it is authoritative. Your resolver's cached copy lacks this flag.

## 7. Gotchas & takeaways

> **Recursive resolvers can lie.** ISPs used to return their own search page IP for NXDOMAIN (non-existent domain) responses. Use `1.1.1.1` or `8.8.8.8` as your resolver for honest answers, or use DNS-over-HTTPS/TLS for privacy.

> **"The DNS change isn't propagating"** is usually misunderstood. DNS records don't actively push to all resolvers — old resolvers just cache the old answer until its TTL expires. Reduce your TTL *before* making a change to speed up the effective update.

- The root nameservers are not a bottleneck — there are 13 clusters with hundreds of anycast instances worldwide.
- The stub resolver in your OS checks `/etc/resolv.conf` (Linux) or network settings to find the recursive resolver address.
- DNSSEC adds cryptographic signatures at each delegation step so resolvers can verify answers weren't tampered with.
- Recursive resolvers share cache across many clients — a popular domain hit by one user benefits thousands.
- `dig +short example.com A` gives just the IP; `dig +trace` gives the full walk.
