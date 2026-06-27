---
card: webdev
gi: 18
slug: ip-addresses-ipv4-vs-ipv6
title: IP addresses (IPv4 vs IPv6)
---

## 1. What it is

An **IP address** (Internet Protocol address) is a numerical label assigned to every device on a network. It serves two functions: **identification** (who you are) and **location** (how to route packets to you). DNS translates domain names into IP addresses; TCP then opens a connection to that address.

There are two versions in active use:

- **IPv4**: 32-bit addresses written as four 8-bit octets in decimal, separated by dots — `93.184.216.34`. ~4.3 billion possible addresses.
- **IPv6**: 128-bit addresses written as eight groups of four hex digits, separated by colons — `2606:2800:220:1:248:1893:25c8:1946`. ~340 undecillion possible addresses.

## 2. Why & when

IPv4 launched in 1981 with roughly 4.3 billion addresses — a number that seemed enormous. By the 2010s the internet had run out. IPv6 was designed in 1998 to solve this; its address space is so large that every grain of sand on Earth could have trillions of IP addresses.

In practice both coexist via **dual-stack**: servers have both an A record (IPv4) and AAAA record (IPv6). Browsers use the Happy Eyeballs algorithm to race both, connecting on whichever responds first. You need to understand the distinction when:

- Configuring server firewall rules (IPv6 rules are separate from IPv4).
- Reading access logs (IPv6 addresses look totally different).
- Debugging connectivity — IPv4 and IPv6 paths can have different MTUs, routing, or filtering.
- Choosing CDN or cloud settings — some require explicit IPv6 enablement.

## 3. Core concept

Think of IPv4 like a four-digit postal code system that ran out of unique codes after the planet's population exploded. IPv6 is the new system with a code long enough to label every atom in a country.

**IPv4 structure:**
```
93   .  184  .  216  .  34
8bit    8bit    8bit    8bit
= 32 bits total
```
Range per octet: 0–255. Written in dotted-decimal notation.

**IPv6 structure:**
```
2606 : 2800 : 0220 : 0001 : 0248 : 1893 : 25c8 : 1946
16bit  16bit  16bit  16bit  16bit  16bit  16bit  16bit
= 128 bits total
```
Written in colon-separated hexadecimal. Leading zeros in a group may be omitted. A run of consecutive all-zero groups is replaced with `::` (only once per address): `2001:db8::1` = `2001:0db8:0000:0000:0000:0000:0000:0001`.

**Special addresses to know:**

| Address | Meaning |
|---------|---------|
| `127.0.0.1` | IPv4 loopback ("this machine") |
| `::1` | IPv6 loopback |
| `0.0.0.0` | "any IPv4 address on this machine" (used in bind/listen calls) |
| `::` | "any IPv6 address" |
| `192.168.x.x`, `10.x.x.x`, `172.16–31.x.x` | Private (RFC 1918) — not routable on public internet |
| `fd00::/8` | Private IPv6 range (unique local addresses) |
| `169.254.x.x` | Link-local IPv4 — auto-assigned when DHCP fails |

**CIDR notation** — IP addresses are grouped into **subnets** using a prefix length: `192.168.1.0/24` means the first 24 bits are the network, leaving 8 bits for hosts (256 addresses: `192.168.1.0` – `192.168.1.255`).

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side comparison of IPv4 32-bit and IPv6 128-bit address structures">
  <!-- IPv4 panel -->
  <rect x="10" y="10" width="300" height="240" rx="10" fill="#1c2430"/>
  <text x="160" y="36" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">IPv4 (32 bits)</text>

  <!-- Octet boxes -->
  <rect x="25"  y="52" width="58" height="38" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="54"  y="77" fill="#e6edf3" font-size="16" text-anchor="middle" font-family="monospace" font-weight="bold">93</text>

  <text x="90"  y="77" fill="#8b949e" font-size="16" text-anchor="middle" font-family="monospace">.</text>

  <rect x="100" y="52" width="58" height="38" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="129" y="77" fill="#e6edf3" font-size="16" text-anchor="middle" font-family="monospace" font-weight="bold">184</text>

  <text x="165" y="77" fill="#8b949e" font-size="16" text-anchor="middle" font-family="monospace">.</text>

  <rect x="175" y="52" width="58" height="38" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="204" y="77" fill="#e6edf3" font-size="16" text-anchor="middle" font-family="monospace" font-weight="bold">216</text>

  <text x="240" y="77" fill="#8b949e" font-size="16" text-anchor="middle" font-family="monospace">.</text>

  <rect x="250" y="52" width="50" height="38" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="275" y="77" fill="#e6edf3" font-size="16" text-anchor="middle" font-family="monospace" font-weight="bold">34</text>

  <text x="25"  y="112" fill="#8b949e" font-size="10" text-anchor="start" font-family="sans-serif">8 bits   8 bits   8 bits   8 bits</text>
  <text x="160" y="135" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">4.3 billion addresses</text>
  <text x="160" y="155" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Range per octet: 0–255</text>
  <text x="160" y="175" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Written in decimal</text>

  <text x="25"  y="210" fill="#79c0ff" font-size="11" font-family="sans-serif">Private: 192.168.x.x</text>
  <text x="25"  y="228" fill="#79c0ff" font-size="11" font-family="sans-serif">Loopback: 127.0.0.1</text>

  <!-- IPv6 panel -->
  <rect x="330" y="10" width="300" height="240" rx="10" fill="#1c2430"/>
  <text x="480" y="36" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">IPv6 (128 bits)</text>

  <!-- Abbreviated address -->
  <text x="480" y="72" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">2606:2800:220:1:</text>
  <text x="480" y="90" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">248:1893:25c8:1946</text>

  <line x1="345" y1="100" x2="625" y2="100" stroke="#6db33f" stroke-width="0.5" opacity="0.5"/>

  <text x="480" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">8 groups × 16 bits (hex)</text>
  <text x="480" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">340 undecillion addresses</text>
  <text x="480" y="160" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Written in hexadecimal</text>
  <text x="480" y="180" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">::1 = loopback (short form)</text>

  <text x="345" y="210" fill="#79c0ff" font-size="11" font-family="sans-serif">Private: fd00::/8</text>
  <text x="345" y="228" fill="#79c0ff" font-size="11" font-family="sans-serif">Loopback: ::1</text>
</svg>

IPv4 is 32-bit decimal; IPv6 is 128-bit hex. Both identify the same concept — a network interface — at different scales.

## 5. Runnable example

```bash
# Explore IP addresses on your own machine — no installs needed

# macOS: show all network interfaces and their IPv4/IPv6 addresses
ifconfig | grep -E "inet |inet6"

# Linux:
ip addr show | grep -E "inet |inet6"

# Windows (PowerShell):
# Get-NetIPAddress | Select-Object InterfaceAlias, AddressFamily, IPAddress

# Query a site's IPv4 and IPv6 addresses:
dig example.com A +short      # IPv4
dig example.com AAAA +short   # IPv6

# Ping via each:
ping -c3 93.184.216.34
ping6 -c3 2606:2800:220:1:248:1893:25c8:1946   # may time out if IPv6 not routed

# Show your public IP (uses external service):
curl -s https://api.ipify.org && echo " (IPv4)"
curl -s https://api6.ipify.org && echo " (IPv6)"
```

**How to run:** paste into a terminal (macOS or Linux). The last two `curl` commands fetch your public IP from ipify.org — useful to confirm whether your ISP provides IPv6.

Expected snippet from `ifconfig`:
```
inet 192.168.1.5 netmask 0xffffff00 broadcast 192.168.1.255
inet6 fe80::1%lo0 prefixlen 64 scopeid 0x1
```

## 6. Walkthrough

- `ifconfig | grep -E "inet |inet6"` — filters network interface output to show only lines with IPv4 (`inet`) and IPv6 (`inet6`) addresses. You'll see loopback (`127.0.0.1`, `::1`) and your LAN address (`192.168.x.x` or `10.x.x.x`).
- `inet6 fe80::…` — `fe80::/10` is the link-local range. Every IPv6 interface auto-assigns itself a link-local address, even without a DHCPv6 server. It's only valid on the local network segment (hence "link-local").
- `dig example.com A / AAAA` — `A` returns an IPv4 address; `AAAA` (four As, for 4× the bits) returns IPv6. If a domain has both, it's dual-stacked.
- `curl -s https://api.ipify.org` — the `api.ipify.org` endpoint returns your public IPv4 over IPv4 transport; `api6.ipify.org` resolves only to an AAAA record, so your client must use IPv6. If the IPv6 request fails, your connection is IPv4-only.
- `192.168.1.5` — a private RFC 1918 address. Traffic from your machine to the internet exits through NAT (Network Address Translation) on your router, which replaces the private source address with its public IP.

## 7. Gotchas & takeaways

> **`0.0.0.0` in a server's bind call does NOT mean "no address"** — it means "listen on all available IPv4 interfaces." Similarly `::` means "all IPv6 interfaces." When a server binds `0.0.0.0:80`, it accepts connections arriving at any of the machine's IPv4 addresses.

> **NAT is not the same as a firewall.** Home routers use NAT (network address translation) to let many devices share one public IPv4 address. IPv6 doesn't need NAT because every device can have a globally unique address — which is why IPv6 connections from inside a firewall can bypass NAT-based restrictions if the firewall rules aren't updated.

- `127.0.0.1` and `localhost` resolve to the loopback interface — traffic never leaves the machine.
- A `/24` subnet has 256 addresses (`0`–`255`); a `/16` has 65 536; a `/8` has 16 777 216.
- IPv6 addresses in URLs must be wrapped in brackets: `http://[::1]:3000/`.
- `ping6` and `curl -6` force IPv6; `ping` and `curl -4` force IPv4 — useful for testing dual-stack setups.
- CGNAT (carrier-grade NAT) — many mobile ISPs put thousands of customers behind a single public IPv4. If you see `100.64.x.x` as your "public" IP, you're behind CGNAT.
