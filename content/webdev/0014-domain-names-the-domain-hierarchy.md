---
card: webdev
gi: 14
slug: domain-names-the-domain-hierarchy
title: Domain names & the domain hierarchy
---

## 1. What it is

A **domain name** is a human-readable label — like `www.example.com` — that identifies a location on the internet. Because computers route traffic by IP address, domain names exist purely as a convenience layer for humans: they're translated to IPs by DNS.

Domain names are organised as a strict hierarchy of **labels** separated by dots. Reading right to left, each label is a child of the one to its right. This tree structure is the **domain hierarchy**, and it is globally managed by a standards body (ICANN) through a chain of delegated authorities.

## 2. Why & when

IP addresses change (servers move, cloud scaling). Domain names stay stable and memorable. The hierarchy matters because:

- **Delegation**: any owner of a domain can create unlimited subdomains underneath it, passing authority downward in the tree.
- **Unique global names**: the hierarchy guarantees `example.com` is owned by exactly one entity — no two domains at the same level can share a name.
- **Management**: organisations control their own sub-trees (their zones) independently of everyone else's.

You encounter the hierarchy whenever you register a domain, set up DNS records, configure subdomains, or debug name-resolution failures.

## 3. Core concept

Think of the domain hierarchy like a government address system. The **root** is Earth. Each **country** (TLD) governs names under it. Each **city** (SLD) is a registered entity. Each **street** (subdomain) is that entity's internal organisation.

The components of `www.api.example.co.uk`:

| Label | Name | What it is |
|---|---|---|
| `.` (invisible) | Root | Top of the hierarchy; all names end here |
| `uk` | TLD (Top-Level Domain) | Country code; managed by Nominet |
| `co` | Second-level under ccTLD | Conventionally "commercial" in UK naming |
| `example` | Registered domain (SLD) | The name you pay a registrar to own |
| `api` | Subdomain | Set up by the owner of `example.co.uk` |
| `www` | Subdomain | Conventionally the public website |

A **Fully Qualified Domain Name (FQDN)** ends with the root dot: `www.example.com.` — most tools strip the trailing dot for readability.

TLD categories:

- **gTLDs** (generic): `.com`, `.org`, `.net`, `.io`, `.dev`, `.app` — anyone can register under most.
- **ccTLDs** (country-code): `.uk`, `.de`, `.jp`, `.au` — country-specific rules.
- **New gTLDs**: ICANN opened hundreds of new TLDs after 2013 — `.coffee`, `.bank`, `.lawyer`, etc.
- **Infrastructure**: `.arpa` — used for reverse DNS and protocol infrastructure.

## 4. Diagram

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Domain name hierarchy tree from root down to subdomains">
  <defs>
    <marker id="arrd" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Root -->
  <rect x="270" y="10" width="100" height="36" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="33" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace" font-weight="bold">. (root)</text>

  <!-- TLDs -->
  <rect x="60"  y="90"  width="100" height="36" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="113" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">.com</text>

  <rect x="270" y="90"  width="100" height="36" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="113" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">.org</text>

  <rect x="480" y="90"  width="100" height="36" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="113" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">.uk</text>

  <!-- Lines root → TLDs -->
  <line x1="320" y1="46" x2="110" y2="88" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="320" y1="46" x2="320" y2="88" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="320" y1="46" x2="530" y2="88" stroke="#6db33f" stroke-width="1.5"/>

  <!-- SLDs under .com -->
  <rect x="10"  y="180" width="110" height="36" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="65"  y="203" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">example.com</text>

  <rect x="140" y="180" width="110" height="36" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="195" y="203" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">google.com</text>

  <!-- Lines .com → SLDs -->
  <line x1="110" y1="126" x2="65"  y2="178" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="110" y1="126" x2="195" y2="178" stroke="#79c0ff" stroke-width="1.5"/>

  <!-- Subdomains under example.com -->
  <rect x="10"  y="262" width="80" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="50"  y="281" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">www</text>

  <rect x="100" y="262" width="80" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="281" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">api</text>

  <!-- Lines example.com → subdomains -->
  <line x1="65" y1="216" x2="50"  y2="260" stroke="#8b949e" stroke-width="1"/>
  <line x1="65" y1="216" x2="140" y2="260" stroke="#8b949e" stroke-width="1"/>

  <!-- Labels -->
  <text x="580" y="113" fill="#8b949e" font-size="10" font-family="sans-serif">← TLD</text>
  <text x="580" y="203" fill="#8b949e" font-size="10" font-family="sans-serif">← SLD</text>
  <text x="200" y="281" fill="#8b949e" font-size="10" font-family="sans-serif">← subdomains</text>
</svg>

The tree grows downward; authority flows from root → TLD → SLD → subdomain, with each level delegated to its owner.

## 5. Runnable example

```bash
# No installs needed — uses dig (built into macOS/Linux) or nslookup (Windows)
# Query each level of the hierarchy for api.example.com

# 1. Ask a root nameserver what TLD servers handle .com
dig . NS +short

# 2. Ask one of those for the authoritative nameserver of example.com
dig example.com NS +short

# 3. Ask the authoritative server for the A record of the SLD
dig example.com A +short

# 4. And for a subdomain (here 'www')
dig www.example.com A +short

# Windows alternative (PowerShell):
# Resolve-DnsName example.com -Type NS
# Resolve-DnsName www.example.com -Type A
```

**How to run:** paste each line in a terminal (macOS or Linux); `dig` is pre-installed on both. On Windows use PowerShell's `Resolve-DnsName`.

Expected output for step 3:
```
93.184.216.34
```

## 6. Walkthrough

- `dig . NS +short` — queries the root zone (`.`) for its Name Server records. These are the 13 root server clusters (a.root-servers.net through m.root-servers.net) that know which servers are authoritative for every TLD.
- `dig example.com NS +short` — queries for the NS records of the `example.com` zone. The answer (e.g. `a.iana-servers.net`) is the authoritative nameserver that owns all records under `example.com`.
- `dig example.com A +short` — fetches the IPv4 address record for `example.com` itself (the apex). This is what a browser would ultimately use to open a TCP connection.
- `dig www.example.com A +short` — queries the subdomain. The authoritative server for `example.com` also answers for `www.example.com` because the owner of the parent zone controls all child labels within it.
- `+short` — strips verbose output, showing only the answer records, making the hierarchy easy to trace.

## 7. Gotchas & takeaways

> **Subdomains are free and unlimited** — you own `example.com`, you can create `anything.example.com` without paying the registrar again. You only pay for labels at the SLD level (one level below the TLD you're registering under).

> **`www` is not special** — it's just a subdomain by convention, identical technically to `blog` or `api`. Many sites now serve the apex domain (`example.com`) directly and make `www.example.com` redirect to it.

- Read domain names right to left: `blog.example.com` → root → `.com` → `example` → `blog`.
- The registrar owns `example.com` in the registry; you own it for the duration of your registration.
- FQDN ends with a dot (`example.com.`) — the trailing dot is the root; most UIs hide it.
- ccTLDs sometimes have an extra level before the SLD: `.co.uk`, `.com.au`, `.co.jp`.
- You cannot register a subdomain directly at a registrar — you must own the parent domain first.
