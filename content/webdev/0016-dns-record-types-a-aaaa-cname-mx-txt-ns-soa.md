---
card: webdev
gi: 16
slug: dns-record-types-a-aaaa-cname-mx-txt-ns-soa
title: DNS record types (A, AAAA, CNAME, MX, TXT, NS, SOA)
---

## 1. What it is

A DNS zone is a collection of **resource records (RRs)** — each one is a typed key-value pair that answers a specific question about a domain. The type tells resolvers *what kind of answer* follows.

The seven record types every web developer needs to know:

| Type | Stands for | Answer |
|------|-----------|--------|
| **A** | Address | IPv4 address for a hostname |
| **AAAA** | Address (IPv6) | IPv6 address for a hostname |
| **CNAME** | Canonical Name | Alias: "this name is really that name" |
| **MX** | Mail Exchanger | Which mail server handles email for this domain |
| **TXT** | Text | Arbitrary text — used for verification & policy |
| **NS** | Name Server | Which servers are authoritative for this zone |
| **SOA** | Start of Authority | Metadata about the zone itself |

## 2. Why & when

Different record types serve different infrastructure goals:

- **A / AAAA** — needed for any hostname that browsers connect to.
- **CNAME** — lets you point a subdomain at a third-party service (CDN, SaaS) without knowing its IP.
- **MX** — required to receive email; wrong MX = email to your domain is rejected.
- **TXT** — SPF, DKIM, DMARC (email anti-spoofing), Google site verification, ACME domain validation for TLS certificates.
- **NS** — defines the authoritative nameservers for a zone; crucial when delegating a subdomain to a different DNS provider.
- **SOA** — automatically maintained by your DNS provider; rarely edited manually, but its serial number drives zone transfers.

Understanding these is essential when configuring hosting, email, CDNs, TLS certificates, and any third-party domain verification.

## 3. Core concept

Think of a DNS zone file like a phone book with specialised sections. The **A** section lists people's home addresses (IPs). The **CNAME** section says "John Smith — see Jon Smyth" (alias). The **MX** section tells the post office where to deliver mail. The **TXT** section has sticky notes (verification codes, policy statements). The **NS** section names the librarians responsible for this edition. The **SOA** section is the book's edition number and publisher contact.

Key rules:
- **CNAME cannot coexist with other records at the same name.** You cannot have `example.com CNAME something.else.com` and also `example.com A 1.2.3.4` — CNAMEs are exclusive.
- **CNAME cannot be used at the zone apex.** `example.com` (the root of the zone) cannot be a CNAME; use `www.example.com` instead. (Some providers offer ALIAS/ANAME records as a workaround.)
- **MX points to a hostname, not an IP.** `10 mail.example.com` — the `10` is priority (lower = preferred); the hostname then needs its own A/AAAA record.
- **SOA has one per zone.** It records the primary nameserver, admin email, zone serial, and refresh/retry/expire/minimum TTL values.

## 4. Diagram

<svg viewBox="0 0 660 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DNS record types shown as labelled rows in a zone file table">
  <!-- Background panel -->
  <rect x="10" y="10" width="640" height="320" rx="10" fill="#1c2430"/>

  <!-- Header -->
  <rect x="10" y="10" width="640" height="36" rx="10" fill="#0d1117"/>
  <text x="30"  y="33" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">Name</text>
  <text x="190" y="33" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">TTL</text>
  <text x="270" y="33" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">Type</text>
  <text x="350" y="33" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">Value</text>

  <!-- Row: A -->
  <text x="30"  y="72" fill="#e6edf3" font-size="12" font-family="monospace">example.com.</text>
  <text x="190" y="72" fill="#8b949e" font-size="12" font-family="monospace">3600</text>
  <text x="270" y="72" fill="#79c0ff" font-size="12" font-family="monospace" font-weight="bold">A</text>
  <text x="350" y="72" fill="#e6edf3" font-size="12" font-family="monospace">93.184.216.34</text>

  <!-- Row: AAAA -->
  <text x="30"  y="102" fill="#e6edf3" font-size="12" font-family="monospace">example.com.</text>
  <text x="190" y="102" fill="#8b949e" font-size="12" font-family="monospace">3600</text>
  <text x="270" y="102" fill="#79c0ff" font-size="12" font-family="monospace" font-weight="bold">AAAA</text>
  <text x="350" y="102" fill="#e6edf3" font-size="12" font-family="monospace">2606:2800:220:1:248:…</text>

  <!-- Row: CNAME -->
  <text x="30"  y="132" fill="#e6edf3" font-size="12" font-family="monospace">www.example.com.</text>
  <text x="190" y="132" fill="#8b949e" font-size="12" font-family="monospace">3600</text>
  <text x="270" y="132" fill="#79c0ff" font-size="12" font-family="monospace" font-weight="bold">CNAME</text>
  <text x="350" y="132" fill="#e6edf3" font-size="12" font-family="monospace">example.com.</text>

  <!-- Row: MX -->
  <text x="30"  y="162" fill="#e6edf3" font-size="12" font-family="monospace">example.com.</text>
  <text x="190" y="162" fill="#8b949e" font-size="12" font-family="monospace">3600</text>
  <text x="270" y="162" fill="#79c0ff" font-size="12" font-family="monospace" font-weight="bold">MX</text>
  <text x="350" y="162" fill="#e6edf3" font-size="12" font-family="monospace">10 mail.example.com.</text>

  <!-- Row: TXT -->
  <text x="30"  y="192" fill="#e6edf3" font-size="12" font-family="monospace">example.com.</text>
  <text x="190" y="192" fill="#8b949e" font-size="12" font-family="monospace">3600</text>
  <text x="270" y="192" fill="#79c0ff" font-size="12" font-family="monospace" font-weight="bold">TXT</text>
  <text x="350" y="192" fill="#e6edf3" font-size="12" font-family="monospace">"v=spf1 include:…"</text>

  <!-- Row: NS -->
  <text x="30"  y="222" fill="#e6edf3" font-size="12" font-family="monospace">example.com.</text>
  <text x="190" y="222" fill="#8b949e" font-size="12" font-family="monospace">86400</text>
  <text x="270" y="222" fill="#79c0ff" font-size="12" font-family="monospace" font-weight="bold">NS</text>
  <text x="350" y="222" fill="#e6edf3" font-size="12" font-family="monospace">a.iana-servers.net.</text>

  <!-- Row: SOA -->
  <text x="30"  y="252" fill="#e6edf3" font-size="12" font-family="monospace">example.com.</text>
  <text x="190" y="252" fill="#8b949e" font-size="12" font-family="monospace">3600</text>
  <text x="270" y="252" fill="#79c0ff" font-size="12" font-family="monospace" font-weight="bold">SOA</text>
  <text x="350" y="252" fill="#e6edf3" font-size="12" font-family="monospace">ns1.example.com. admin…</text>

  <!-- Divider lines -->
  <line x1="20" y1="48" x2="640" y2="48" stroke="#8b949e" stroke-width="0.5" opacity="0.4"/>
  <line x1="20" y1="78" x2="640" y2="78" stroke="#8b949e" stroke-width="0.5" opacity="0.2"/>
  <line x1="20" y1="108" x2="640" y2="108" stroke="#8b949e" stroke-width="0.5" opacity="0.2"/>
  <line x1="20" y1="138" x2="640" y2="138" stroke="#8b949e" stroke-width="0.5" opacity="0.2"/>
  <line x1="20" y1="168" x2="640" y2="168" stroke="#8b949e" stroke-width="0.5" opacity="0.2"/>
  <line x1="20" y1="198" x2="640" y2="198" stroke="#8b949e" stroke-width="0.5" opacity="0.2"/>
  <line x1="20" y1="228" x2="640" y2="228" stroke="#8b949e" stroke-width="0.5" opacity="0.2"/>

  <text x="30" y="300" fill="#8b949e" font-size="11" font-family="sans-serif">Trailing dot (.) = FQDN (fully qualified). TTL in seconds.</text>
</svg>

Each row is one DNS resource record; a zone file contains many such rows, one per name/type combination.

## 5. Runnable example

```bash
# Query all common record types for a real domain
# No installs — dig is built into macOS/Linux

DOMAIN="example.com"

echo "=== A (IPv4) ==="
dig $DOMAIN A +short

echo "=== AAAA (IPv6) ==="
dig $DOMAIN AAAA +short

echo "=== CNAME for www ==="
dig www.$DOMAIN CNAME +short

echo "=== MX (mail) ==="
dig $DOMAIN MX +short

echo "=== TXT (SPF / verification) ==="
dig $DOMAIN TXT +short

echo "=== NS (nameservers) ==="
dig $DOMAIN NS +short

echo "=== SOA (zone metadata) ==="
dig $DOMAIN SOA +short

# Try ANY — returns all records (support is declining, but still works on many servers)
# dig $DOMAIN ANY +short
```

**How to run:** paste into a terminal on macOS or Linux. On Windows use `Resolve-DnsName example.com -Type A` etc. in PowerShell.

Expected output (abbreviated):
```
=== A (IPv4) ===
93.184.216.34
=== MX (mail) ===
0 .
=== NS (nameservers) ===
b.iana-servers.net.
a.iana-servers.net.
```

## 6. Walkthrough

- `dig $DOMAIN A +short` — asks for the IPv4 address record. The `+short` flag strips the query and header lines, leaving just the answer value.
- `dig $DOMAIN AAAA` — IPv6 equivalent. A site dual-stacked (supports both IPv4 and IPv6) has both A and AAAA records for the same name. Browsers try AAAA first when available (Happy Eyeballs algorithm).
- `dig www.$DOMAIN CNAME` — queries the CNAME for `www`. If the output is a hostname (ending in `.`), DNS will follow that chain until it hits an A/AAAA record; the browser sees only the final IP.
- `dig $DOMAIN MX` — returns priority + mail hostname pairs. Multiple MX records let you have primary and backup mail servers; lower priority number = higher preference.
- `dig $DOMAIN TXT` — returns all TXT records. SPF (`v=spf1 …`) lists authorised email senders; DKIM and DMARC have their own TXT records at specific subdomains (`_dmarc.example.com`, `selector._domainkey.example.com`).
- `dig $DOMAIN NS` — lists the authoritative nameservers. These must match what the registrar has on file at the TLD level; a mismatch causes resolution failures.
- `dig $DOMAIN SOA` — shows the primary nameserver, responsible mailbox, serial number (incremented on every zone change), and refresh/retry/expire timings used by secondary nameservers.

## 7. Gotchas & takeaways

> **CNAME at the apex is forbidden by the DNS spec** (RFC 1034). Tools like Cloudflare's CNAME Flattening or Route 53's ALIAS records work around this by resolving the CNAME server-side and returning an A record to clients — but this is a provider extension, not standard DNS.

> **MX must point to a hostname, never an IP.** `MX 10 1.2.3.4` is invalid by RFC 974. Create an A record for the mail server hostname, then point MX at that hostname.

- Multiple A records for the same name = round-robin load balancing (primitive but effective).
- TXT records have a 255-character limit per string; long SPF/DKIM values use multiple strings concatenated.
- `dig +multiline example.com SOA` shows the SOA record in human-readable multiline format.
- A missing or wrong AAAA record causes IPv6 clients to fall back to IPv4 — they still connect, just slower.
- When you move email to Google Workspace or Microsoft 365, their setup wizard tells you exactly which MX and TXT records to add.
