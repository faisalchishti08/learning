---
card: webdev
gi: 22
slug: tcp-ip-model-osi-model
title: TCP/IP model & OSI model
---

## 1. What it is

The **TCP/IP model** and the **OSI model** are conceptual frameworks that describe how network communication is divided into layers of responsibility. Each layer handles a specific concern and communicates only with the layers directly above and below it.

- The **OSI model** (Open Systems Interconnection, 1984) has **7 layers** and was designed as a vendor-neutral reference standard.
- The **TCP/IP model** (1970s, formalised in RFC 1122) has **4 layers** and is what the actual internet runs on. It maps roughly to OSI layers but combines several.

Neither model is code — they're organisational vocabularies that help engineers talk about protocols and debug problems at the right level.

## 2. Why & when

These models matter because:

- **Debugging vocabulary**: "this is a layer 3 problem" (routing/IP) vs. "layer 7 problem" (HTTP/application) instantly focuses investigation.
- **Protocol placement**: knowing HTTP is layer 7, TCP is layer 4, and IP is layer 3 explains why you can swap HTTP for gRPC without changing how routers forward packets.
- **Security**: firewalls operate at layer 3/4 (IP/port); WAFs operate at layer 7 (HTTP content). Understanding which layer an attack targets tells you which defence is needed.
- **Job interviews and certifications**: OSI layers are a universal reference. Every network engineer uses them.

## 3. Core concept

Think of the layers as the departments in a postal service. You write a letter (application data), put it in an envelope with a recipient name (session/presentation), the post office adds a routing slip (network/IP), the truck driver loads it on the right vehicle (data link/Ethernet), and the physical road carries it (physical/cable). Each layer adds its own envelope on the way out and strips it on the way in — this is **encapsulation**.

**OSI model (7 layers):**

| Layer | Name | Examples |
|-------|------|---------|
| 7 | Application | HTTP, HTTPS, DNS, SMTP, FTP |
| 6 | Presentation | TLS/SSL, compression, encoding |
| 5 | Session | Session management, NetBIOS |
| 4 | Transport | TCP, UDP |
| 3 | Network | IP (IPv4/IPv6), ICMP, routing |
| 2 | Data Link | Ethernet, Wi-Fi (802.11), ARP, MAC addresses |
| 1 | Physical | Cables, fibre, radio waves, voltage |

**TCP/IP model (4 layers) and rough OSI mapping:**

| TCP/IP Layer | OSI Equivalent | Protocols |
|-------------|---------------|---------|
| Application | 5, 6, 7 | HTTP, DNS, SMTP, SSH |
| Transport | 4 | TCP, UDP |
| Internet | 3 | IP, ICMP |
| Network Access (Link) | 1, 2 | Ethernet, Wi-Fi |

**Encapsulation in practice:** when you send an HTTP request, the data passes down the stack:
- HTTP adds headers (layer 7).
- TCP adds source/dest port + sequence numbers (layer 4).
- IP adds source/dest IP address (layer 3).
- Ethernet adds MAC addresses + frame check (layer 2).
- Converted to bits and transmitted (layer 1).

The receiving end strips headers in reverse order back up to layer 7.

## 4. Diagram

<svg viewBox="0 0 660 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side OSI 7-layer model and TCP/IP 4-layer model with protocol examples">
  <!-- OSI Column -->
  <text x="180" y="24" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">OSI Model</text>

  <!-- L7 -->
  <rect x="30"  y="34"  width="300" height="34" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70"  y="56" fill="#6db33f" font-size="11" font-family="sans-serif" font-weight="bold">7 Application</text>
  <text x="200" y="56" fill="#8b949e" font-size="11" font-family="monospace">HTTP, HTTPS, DNS, SMTP</text>

  <!-- L6 -->
  <rect x="30"  y="70"  width="300" height="34" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="70"  y="92" fill="#6db33f" font-size="11" font-family="sans-serif">6 Presentation</text>
  <text x="200" y="92" fill="#8b949e" font-size="11" font-family="monospace">TLS, JPEG, gzip</text>

  <!-- L5 -->
  <rect x="30"  y="106" width="300" height="34" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="70"  y="128" fill="#6db33f" font-size="11" font-family="sans-serif">5 Session</text>
  <text x="200" y="128" fill="#8b949e" font-size="11" font-family="monospace">NetBIOS, RPC</text>

  <!-- L4 -->
  <rect x="30"  y="142" width="300" height="34" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70"  y="164" fill="#79c0ff" font-size="11" font-family="sans-serif" font-weight="bold">4 Transport</text>
  <text x="200" y="164" fill="#8b949e" font-size="11" font-family="monospace">TCP, UDP, QUIC</text>

  <!-- L3 -->
  <rect x="30"  y="178" width="300" height="34" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70"  y="200" fill="#79c0ff" font-size="11" font-family="sans-serif" font-weight="bold">3 Network</text>
  <text x="200" y="200" fill="#8b949e" font-size="11" font-family="monospace">IP, ICMP, routing</text>

  <!-- L2 -->
  <rect x="30"  y="214" width="300" height="34" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="70"  y="236" fill="#8b949e" font-size="11" font-family="sans-serif">2 Data Link</text>
  <text x="200" y="236" fill="#8b949e" font-size="11" font-family="monospace">Ethernet, Wi-Fi, ARP</text>

  <!-- L1 -->
  <rect x="30"  y="250" width="300" height="34" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="70"  y="272" fill="#8b949e" font-size="11" font-family="sans-serif">1 Physical</text>
  <text x="200" y="272" fill="#8b949e" font-size="11" font-family="monospace">cables, fibre, radio</text>

  <!-- TCP/IP Column -->
  <text x="530" y="24" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">TCP/IP Model</text>

  <!-- Application (maps to 5+6+7) -->
  <rect x="360" y="34" width="270" height="106" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="78" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Application</text>
  <text x="495" y="96" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">HTTP, DNS, SMTP, SSH</text>
  <text x="495" y="114" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">≈ OSI layers 5, 6, 7</text>
  <text x="495" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">TLS lives here</text>

  <!-- Transport -->
  <rect x="360" y="142" width="270" height="34" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="164" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Transport</text>

  <!-- Internet -->
  <rect x="360" y="178" width="270" height="34" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="200" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Internet (IP)</text>

  <!-- Link -->
  <rect x="360" y="214" width="270" height="70" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="248" fill="#8b949e" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Network Access</text>
  <text x="495" y="268" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">≈ OSI layers 1 + 2</text>

  <!-- Bracket connecting OSI 5-7 to TCP/IP Application -->
  <line x1="332" y1="51" x2="358" y2="51" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,2" opacity="0.6"/>
  <line x1="332" y1="137" x2="358" y2="137" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,2" opacity="0.6"/>
</svg>

OSI provides precise vocabulary (L4 = Transport); TCP/IP is what actually runs. Both describe the same physical reality from different altitudes.

## 5. Runnable example

```bash
# Observe all 4 TCP/IP layers in action with a real HTTP request
# Uses: curl (application layer), tcpdump or netstat (transport/network layer)

# Terminal 1: watch layer 3/4 — TCP connections to port 80
# (requires admin on macOS; swap 'lo0' for 'eth0' on Linux)
sudo tcpdump -i any -n 'port 80' &

# Terminal 2 (or same terminal after backgrounding):
# Layer 7 — HTTP request (application layer)
curl -v http://example.com/ 2>&1 | head -30

# Stop tcpdump
kill %1

# Alternative (no root needed): show the TCP state machine
# Open a connection and watch it progress:
node -e "
const net = require('net');
const s = net.createConnection({ host: 'example.com', port: 80 }, () => {
  console.log('Layer 4 (Transport): TCP connection established');
  s.write('GET / HTTP/1.0\r\nHost: example.com\r\n\r\n');
});
s.once('data', d => {
  console.log('Layer 7 (Application): HTTP response received');
  console.log(d.toString().split('\r\n')[0]);
  s.destroy();
});
"
```

**How to run:** the `node` version requires no sudo and shows layers 4 and 7 clearly. The `tcpdump` version shows raw TCP packets but needs admin rights.

Expected output from the Node version:
```
Layer 4 (Transport): TCP connection established
Layer 7 (Application): HTTP response received
HTTP/1.0 200 OK
```

## 6. Walkthrough

- `net.createConnection({ host: 'example.com', port: 80 }, ...)` — Node resolves `example.com` at layer 3 (DNS + IP), opens a TCP connection at layer 4, and fires the callback when the three-way handshake completes. From code's perspective, layers 1–4 are invisible.
- `s.write('GET / HTTP/1.0\r\nHost: example.com\r\n\r\n')` — this is a raw layer 7 (application) HTTP request written directly over the TCP socket. No HTTP library — you're talking to the protocol directly.
- `s.once('data', d => ...)` — receives the server's raw HTTP response bytes. `d.toString().split('\r\n')[0]` extracts just the status line: `HTTP/1.0 200 OK`.
- `tcpdump -n 'port 80'` — captures layer 2 frames containing layer 3 IP packets containing layer 4 TCP segments. Each line in the output shows: timestamp, source IP:port → dest IP:port, TCP flags (S = SYN, . = ACK, P = PUSH/data).
- The combination shows the stack: DNS at L3/L7, TCP handshake at L4, HTTP exchange at L7.

## 7. Gotchas & takeaways

> **"Layer 7 problem" vs "layer 4 problem" is not just jargon.** If you can `telnet example.com 443` (layer 4 connection succeeds) but the HTTPS handshake fails (layer 7), the problem is in TLS/certificates, not routing or firewalls. Knowing which layer fails tells you exactly where to look.

> **TLS doesn't fit neatly into the OSI model.** It's often called "layer 6" in OSI terminology, but in practice it sits between the TCP socket (L4) and the application (L7). The TCP/IP model is more honest: TLS is just part of the application layer stack.

- Routers operate at layer 3; switches operate at layer 2. A "layer 7 load balancer" like Nginx can inspect HTTP content and route by URL path — a layer 3/4 load balancer can only route by IP and port.
- ICMP (ping, traceroute) is layer 3 — it travels inside IP packets. Blocking ICMP in a firewall blocks `ping` but not TCP connections.
- OSI layers 5 and 6 are rarely discussed in modern web work — most session and presentation functionality was absorbed into TLS and application protocols.
- The mnemonic for OSI layers 7→1: **A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing.
