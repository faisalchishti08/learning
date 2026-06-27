---
card: webdev
gi: 21
slug: hosts-file-local-overrides
title: Hosts file & local overrides
---

## 1. What it is

The **hosts file** is a plain-text file on your local machine that maps hostnames to IP addresses. It is consulted **before** DNS — if a hostname appears in the hosts file, the OS uses that IP directly and skips the DNS lookup entirely.

Locations:
- **macOS / Linux**: `/etc/hosts`
- **Windows**: `C:\Windows\System32\drivers\etc\hosts`

Each line has an IP address followed by one or more hostnames:
```
127.0.0.1   localhost
::1          localhost
93.184.216.34  example.com
```

## 2. Why & when

Common use cases:

- **Local development**: point `myapp.local` or `api.myapp.com` to `127.0.0.1` so you can test your app at a real-looking domain without buying one or modifying DNS.
- **Testing a deployment**: before pointing real DNS to a new server, add the new IP to hosts to verify the site works on the new server while the rest of the world still hits the old one.
- **Blocking sites**: point `ads.example.com` to `0.0.0.0` or `127.0.0.1` to prevent connections (ad blockers like Pi-hole use a similar technique with a local DNS server).
- **Overriding stale DNS**: when DNS propagation is slow, engineers add a hosts entry to unblock themselves while waiting.

## 3. Core concept

Think of the hosts file as a Post-it note on your phone's phonebook: before you look up a name in the book (DNS), you check the Post-it. If it's there, you use that number; the phonebook is never opened.

The lookup order on most operating systems:

1. **Hosts file** — checked first, wins immediately if the name matches.
2. **DNS cache** (OS stub resolver) — checked next.
3. **DNS query** — sent to the configured recursive resolver.

This order is controlled by `/etc/nsswitch.conf` (Linux) or the macOS Directory Services configuration. The default `hosts: files dns` means "check files first, then DNS."

Syntax rules for `/etc/hosts`:
- One entry per line: `<IP>  <hostname> [alias1 alias2 …]`
- Lines starting with `#` are comments.
- Multiple hostnames for the same IP can be listed on one line or on separate lines.
- Both IPv4 and IPv6 entries are valid.
- Wildcards (`*.example.com`) are **not** supported — each hostname must be listed explicitly.
- Changes take effect immediately (no service restart needed on macOS/Linux).

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DNS lookup order showing hosts file checked before DNS cache and DNS resolver">
  <defs>
    <marker id="ha" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="hb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>

  <!-- App -->
  <rect x="10" y="100" width="110" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="122" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">App / Browser</text>
  <text x="65" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">needs IP for host</text>

  <!-- Hosts file -->
  <rect x="170" y="40" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="235" y="62" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">/etc/hosts</text>
  <text x="235" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">checked first</text>

  <!-- Hit label -->
  <rect x="350" y="40" width="90" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="62" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">HIT</text>
  <text x="395" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">return IP, done</text>

  <!-- DNS Cache -->
  <rect x="170" y="130" width="130" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="235" y="152" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">OS DNS cache</text>
  <text x="235" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">checked second</text>

  <!-- Resolver -->
  <rect x="170" y="218" width="130" height="30" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="235" y="238" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">DNS resolver query</text>

  <!-- Arrows -->
  <line x1="122" y1="112" x2="168" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ha)"/>
  <text x="135" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">1st</text>

  <line x1="302" y1="65" x2="348" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ha)"/>
  <text x="325" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">match</text>

  <line x1="235" y1="92" x2="235" y2="128" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#hb)"/>
  <text x="252" y="114" fill="#8b949e" font-size="9" font-family="sans-serif">miss</text>

  <line x1="235" y1="182" x2="235" y2="216" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#hb)"/>
  <text x="252" y="204" fill="#8b949e" font-size="9" font-family="sans-serif">miss</text>

  <!-- Hosts file content sample -->
  <rect x="470" y="20" width="160" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="550" y="40" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace"># /etc/hosts</text>
  <text x="480" y="58" fill="#e6edf3" font-size="10" font-family="monospace">127.0.0.1  localhost</text>
  <text x="480" y="74" fill="#6db33f" font-size="10" font-family="monospace">127.0.0.1  myapp.local</text>
  <text x="480" y="90" fill="#8b949e" font-size="10" font-family="monospace">0.0.0.0    ads.evil.com</text>
  <text x="480" y="106" fill="#8b949e" font-size="10" font-family="monospace">::1        localhost</text>
</svg>

The hosts file intercepts lookups before DNS; a hit short-circuits the entire DNS resolution chain.

## 5. Runnable example

```bash
# Test hosts file override without permanently editing /etc/hosts
# Uses a temporary approach: resolve before and after adding an entry

# 1. Check current resolution for a made-up domain (should fail)
dig +short myapp.local A
# → (empty — no DNS record exists)

# 2. Add a temporary hosts entry (you'll be prompted for your password)
echo "127.0.0.1  myapp.local" | sudo tee -a /etc/hosts

# 3. Re-check — now resolves via hosts file, no DNS needed
ping -c 1 myapp.local
# → PING myapp.local (127.0.0.1): ...

# 4. Clean up: remove the line we added
sudo sed -i '' '/myapp.local/d' /etc/hosts   # macOS
# sudo sed -i '/myapp.local/d' /etc/hosts    # Linux

# 5. Verify it's gone
ping -c 1 myapp.local 2>&1 | head -1
# → ping: cannot resolve myapp.local: Name or service not known
```

**How to run:** paste into a macOS terminal line by line. Linux users: use the Linux `sed` line (without `''`). Requires `sudo` for writing to `/etc/hosts`.

## 6. Walkthrough

- `dig +short myapp.local A` — before the hosts entry, DNS has no record for `myapp.local`; the output is empty (or `NXDOMAIN`).
- `echo "127.0.0.1  myapp.local" | sudo tee -a /etc/hosts` — `tee -a` appends without overwriting; `sudo` is needed because `/etc/hosts` is owned by root. The change is effective immediately — no daemon to restart.
- `ping -c 1 myapp.local` — after the hosts entry, the OS resolves `myapp.local` to `127.0.0.1` before even touching DNS. The ping response shows `(127.0.0.1)`, confirming the override worked.
- `sudo sed -i '' '/myapp.local/d' /etc/hosts` — on macOS `sed -i` requires an empty string argument `''`; on Linux it's just `-i`. The pattern `/myapp.local/d` deletes any line containing that string.
- After cleanup, `ping` fails again — confirming the hosts file was the only source of the resolution.

## 7. Gotchas & takeaways

> **The hosts file does not support wildcards.** You cannot write `127.0.0.1  *.myapp.local` to match all subdomains. You must add each subdomain explicitly: `127.0.0.1  api.myapp.local`, `127.0.0.1  www.myapp.local`, etc. For wildcard local domains, use a local DNS server like `dnsmasq`.

> **Some browsers bypass the OS resolver.** Chrome has its own DNS-over-HTTPS (DoH) implementation; when it uses DoH, the hosts file is still respected for most lookups, but custom TLDs like `.local` may behave differently. If your hosts entry isn't working in Chrome, check `chrome://settings/security` → "Use secure DNS".

- Editing `/etc/hosts` requires `sudo` — write access is restricted to root to prevent malicious apps from hijacking domain names.
- On macOS, flush the DNS cache after editing if changes don't take effect: `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder`.
- Tools like [Gas Mask](https://github.com/2ndalpha/gasmask) (macOS) and [Hosts File Editor](https://hostsfileeditor.com/) (Windows) provide a GUI for managing multiple hosts profiles.
- Ad-blocking solutions like Pi-hole work by running a local DNS server that returns `0.0.0.0` for known ad domains — a scalable, network-wide version of the hosts file trick.
- In Docker Compose, services resolve each other by service name via Docker's built-in DNS — you don't need hosts file entries for container-to-container communication.
