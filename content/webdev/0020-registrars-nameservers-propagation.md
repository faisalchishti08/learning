---
card: webdev
gi: 20
slug: registrars-nameservers-propagation
title: Registrars, nameservers & propagation
---

## 1. What it is

Three distinct entities control where a domain name points:

- A **registry** is the organisation that operates a TLD (e.g. Verisign runs `.com`). It stores the canonical NS records for every domain under that TLD.
- A **registrar** is an ICANN-accredited company (e.g. Namecheap, GoDaddy, Google Domains) that sells domain registrations to the public. It communicates changes to the registry on your behalf.
- A **nameserver** (NS) is the DNS server that holds and serves your zone's actual records (A, MX, TXT, etc.). You configure which nameservers are authoritative for your domain by telling your registrar.

**Propagation** is the delay between making a DNS change and seeing it everywhere on the internet — caused by TTL-based caching at recursive resolvers worldwide.

## 2. Why & when

Understanding this chain matters when:
- You buy a domain and need to point it at a hosting provider or CDN.
- You move DNS management from one provider to another (e.g. from registrar's built-in DNS to Cloudflare).
- A client says "I updated my DNS but it's not working" — you need to know whether the registrar updated the registry, whether the TTL has expired, and which layer is stale.
- You migrate to a new server and need to know how long the transition will take.

## 3. Core concept

Think of the chain like franchising. The **franchisor** (registry) sets the rules and keeps a master list of all franchise owners and which local offices they use. A **franchise broker** (registrar) sells franchise licences (domain registrations) and files paperwork with the franchisor. Each **local office** (nameserver) holds the actual operating information (opening hours, phone numbers — your DNS records). When details change, the local office updates first; the broader world learns gradually as caches expire.

The authority chain for `example.com`:

```
Root (.) → .com registry (Verisign) → example.com registrar (e.g. Namecheap)
        → example.com nameservers (e.g. ns1.cloudflare.com) → DNS records
```

When you register a domain, you tell your registrar which nameservers are authoritative. The registrar writes those NS records into the TLD registry's database (a **glue record** situation if the nameserver's own hostname is under the domain). Until you do this, the domain resolves to the registrar's parking page (or nothing).

**Propagation** explained:

1. You change an A record on your nameserver — instantaneous on the authoritative server.
2. Resolvers that have cached the old record continue returning it for up to the old TTL.
3. Once each resolver's cached copy expires, it re-queries the authoritative server and gets the new record.
4. "Propagation complete" means all significant resolvers worldwide have expired their cache and fetched the new value — typically 0–48 hours depending on the TTL in place before the change.

There is no global DNS push. "Propagation" is just waiting for distributed caches to expire.

## 4. Diagram

<svg viewBox="0 0 640 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Chain from registrar to registry to nameserver to resolver, showing the delegation of DNS authority">
  <defs>
    <marker id="rpa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- You / registrar -->
  <rect x="10" y="120" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="144" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">You</text>
  <text x="75" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">at Registrar UI</text>
  <text x="75" y="174" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(Namecheap etc.)</text>

  <!-- Registrar → Registry -->
  <line x1="142" y1="150" x2="178" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rpa)"/>
  <text x="160" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">EPP</text>

  <!-- Registry -->
  <rect x="180" y="120" width="130" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="245" y="144" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Registry</text>
  <text x="245" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Verisign (.com)</text>
  <text x="245" y="174" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">stores NS records</text>

  <!-- Registry → Nameserver -->
  <line x1="312" y1="150" x2="348" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rpa)"/>
  <text x="330" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">delegates</text>

  <!-- Nameserver -->
  <rect x="350" y="120" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="415" y="140" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Authoritative</text>
  <text x="415" y="156" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Nameserver</text>
  <text x="415" y="174" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ns1.cloudflare.com</text>

  <!-- Nameserver → Resolvers -->
  <line x1="482" y1="150" x2="518" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rpa)"/>
  <text x="500" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">answers</text>

  <!-- Resolvers -->
  <rect x="520" y="120" width="110" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="575" y="144" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Resolvers</text>
  <text x="575" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1.1.1.1 / 8.8.8.8</text>
  <text x="575" y="174" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">cache by TTL</text>

  <!-- Propagation timeline -->
  <text x="320" y="226" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Propagation timeline after a change</text>

  <rect x="10"  y="240" width="620" height="16" rx="4" fill="#0d1117"/>
  <!-- Sections of propagation -->
  <rect x="10"  y="240" width="60"  height="16" rx="2" fill="#6db33f" opacity="0.9"/>
  <rect x="72"  y="240" width="180" height="16" rx="2" fill="#6db33f" opacity="0.4"/>
  <rect x="254" y="240" width="376" height="16" rx="2" fill="#6db33f" opacity="0.15"/>

  <text x="40"  y="272" fill="#6db33f"  font-size="10" text-anchor="middle" font-family="sans-serif">instant</text>
  <text x="162" y="272" fill="#e6edf3"  font-size="10" text-anchor="middle" font-family="sans-serif">nearby resolvers (~mins)</text>
  <text x="442" y="272" fill="#8b949e"  font-size="10" text-anchor="middle" font-family="sans-serif">distant/slow resolvers (hours – 48h)</text>

  <text x="10"  y="296" fill="#8b949e" font-size="10" font-family="sans-serif">t=0 (you save change)</text>
  <text x="580" y="296" fill="#8b949e" font-size="10" text-anchor="end" font-family="sans-serif">t = old TTL (fully propagated)</text>
</svg>

The authority chain runs left to right; propagation delay is entirely a caching (TTL) phenomenon — there is no active push.

## 5. Runnable example

```bash
# Trace the registrar → registry → nameserver chain for a domain
# No installs — whois and dig are built into macOS/Linux

DOMAIN="example.com"

# 1. See who the registrar is and when registration expires
whois $DOMAIN | grep -E "Registrar:|Registry Expiry|Name Server"

# 2. Check what NS records the TLD registry returns (what the registrar filed)
dig $DOMAIN NS +short

# 3. Compare: what a specific nameserver says it holds (the authoritative source)
AUTH=$(dig $DOMAIN NS +short | head -1)
echo "Authoritative server: $AUTH"
dig @$AUTH $DOMAIN A +short

# 4. Check if your local resolver agrees (cached value):
dig $DOMAIN A +short
# If different from step 3, propagation is still in progress.
```

**How to run:** paste into a macOS or Linux terminal. `whois` is pre-installed on macOS; on Ubuntu: `apt install whois`.

Expected snippet:
```
Registrar: RESERVED-Internet Assigned Numbers Authority
Name Server: A.IANA-SERVERS.NET
Name Server: B.IANA-SERVERS.NET
```

## 6. Walkthrough

- `whois $DOMAIN` — queries the WHOIS protocol for the domain's registration metadata. The `Registrar` line shows who you'd log in to in order to change NS records. `Registry Expiry Date` is when the registration lapses if not renewed. `Name Server` lines show what the **registry** currently has on file.
- `dig $DOMAIN NS +short` — asks your recursive resolver for the NS records of the domain. These should match the `Name Server` lines from WHOIS. If they differ, there may be a registry propagation lag (rare — usually near-instant via EPP).
- `AUTH=$(...)` — captures the first nameserver hostname. `dig @$AUTH $DOMAIN A` bypasses your resolver and queries the authoritative server directly — this always shows the current truth, with no caching layer.
- Comparing step 3 vs. step 4 outputs is the definitive propagation check: if the authoritative server returns `1.2.3.4` but your resolver still returns the old IP, the resolver's cache hasn't expired yet. Wait for the old record's TTL to pass.

## 7. Gotchas & takeaways

> **Changing NS records at your registrar takes longer to propagate than changing A/MX records at your nameserver.** NS records are cached at the TLD level with long TTLs (often 172 800 seconds = 48 hours). Moving from one DNS provider to another (changing NS) can take up to 48 hours; changing an A record within the same provider is limited only by your record's own TTL.

> **You can have your domain at registrar A and your DNS at provider B.** Registrar stores ownership and NS delegation; nameserver provider (Cloudflare, Route 53, etc.) stores the actual DNS records. These are independent. Many people keep their domain at Namecheap but point NS to Cloudflare for better performance and DDoS protection.

- Glue records are needed when your nameserver is under its own domain (e.g. `ns1.yourdomain.com`). The registry stores an A record for the NS hostname alongside the NS record itself, breaking the circular dependency.
- ICANN's 60-day transfer lock prevents a domain from being transferred to another registrar for 60 days after registration or a registrar change — an anti-hijacking measure.
- `whois` output format varies by TLD; `rdap` (the modern replacement) returns structured JSON: `curl https://rdap.org/domain/example.com`.
- Renewing a domain before expiry is critical — expired domains enter a grace period then redemption period (expensive to recover) before being released for general registration.
