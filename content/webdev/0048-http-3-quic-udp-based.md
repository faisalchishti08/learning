---
card: webdev
gi: 48
slug: http-3-quic-udp-based
title: HTTP/3 & QUIC (UDP-based)
---

## 1. What it is

**HTTP/3** (RFC 9114, 2022) is the third major version of HTTP. Like HTTP/2 it multiplexes many streams over one connection, but the transport layer underneath is completely different:

- HTTP/1.1 and HTTP/2 run over **TCP**.
- HTTP/3 runs over **QUIC** (RFC 9000), which runs over **UDP**.

**QUIC** (originally a Google experiment, now an IETF standard) is a general-purpose transport protocol built in user-space above UDP. It re-implements what TCP provides (reliable delivery, ordering, flow control, congestion control) but adds:

- **Independent stream multiplexing** — a lost packet stalls only the stream that owns it, not all streams.
- **Built-in TLS 1.3** — the encryption handshake is integrated, saving round trips.
- **Connection migration** — changing IP (e.g., switching from Wi-Fi to cellular) doesn't break the connection.
- **0-RTT resumption** — reconnecting to a known server sends data immediately with no handshake round trips.

## 2. Why & when

HTTP/2 solved HTTP/1.1's application-layer HOL blocking, but TCP still has transport-layer HOL blocking: one lost packet freezes all streams until it's retransmitted. On lossy networks (mobile, long-distance, satellite) this throttles performance badly.

Additionally, TCP connection setup plus TLS handshake costs 2–3 round trips (RTT) before the first byte of data arrives. On a 100ms RTT link that's 300ms of dead time before the page starts loading.

QUIC/HTTP/3 targets exactly these pain points. Adoption is substantial: Cloudflare, Google, Facebook, and major CDNs all support it. Browser support is universal. You enable it server-side; clients negotiate automatically via the `Alt-Svc` header or DNS HTTPS records.

## 3. Core concept

Analogy: TCP is like a conveyor belt — items must come off in order; one jammed item stops the belt. QUIC is like separate parallel conveyor belts (one per stream) sharing the same physical channel. A jam on belt 3 doesn't stop belt 1 or belt 5.

The key architectural insight: **QUIC moves multiplexing into the transport layer**. HTTP/2's multiplexing was an HTTP-level abstraction, but the streams still collapsed into a single ordered TCP byte stream underneath. QUIC streams are ordered *within each stream* but independent across streams.

```
TCP (HTTP/1.1 & 2):           QUIC (HTTP/3):
┌────────────────────┐        ┌────────┐ ┌────────┐ ┌────────┐
│ byte stream        │        │stream 1│ │stream 3│ │stream 5│
│ [pkt1][pkt2][×pkt3]│        │[A][B]  │ │[X][×Y]│ │[M][N]  │
│   everything stops │        │ok      │ │stall  │ │ok      │
└────────────────────┘        └────────┘ └────────┘ └────────┘
                              lost pkt only stalls stream 3
```

**TLS 1.3 integration:** QUIC always encrypts — there is no plaintext QUIC. The handshake fuses the QUIC connection setup and the TLS key exchange, achieving a 1-RTT initial connection (vs 2–3 for TCP+TLS).

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP/3 over QUIC over UDP compared to HTTP/2 over TCP; showing independent streams and built-in TLS">
  <defs>
    <marker id="a48" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b48" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c48" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Protocol stack left: HTTP/2 over TCP -->
  <text x="80" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold" text-anchor="middle">HTTP/2 stack</text>
  <rect x="20" y="32" width="120" height="28" rx="4" fill="#6db33f" opacity="0.25" stroke="#6db33f" stroke-width="1"/>
  <text x="80" y="51" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HTTP/2 (framing)</text>
  <rect x="20" y="64" width="120" height="28" rx="4" fill="#79c0ff" opacity="0.2" stroke="#79c0ff" stroke-width="1"/>
  <text x="80" y="83" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">TLS 1.3</text>
  <rect x="20" y="96" width="120" height="28" rx="4" fill="#8b949e" opacity="0.3" stroke="#8b949e" stroke-width="1"/>
  <text x="80" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">TCP</text>
  <rect x="20" y="128" width="120" height="28" rx="4" fill="#8b949e" opacity="0.15" stroke="#8b949e" stroke-width="1"/>
  <text x="80" y="147" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">IP / UDP</text>

  <!-- Protocol stack right: HTTP/3 over QUIC -->
  <text x="400" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold" text-anchor="middle">HTTP/3 stack</text>
  <rect x="340" y="32" width="120" height="28" rx="4" fill="#6db33f" opacity="0.25" stroke="#6db33f" stroke-width="1"/>
  <text x="400" y="51" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HTTP/3 (framing)</text>
  <rect x="340" y="64" width="120" height="60" rx="4" fill="#d29922" opacity="0.2" stroke="#d29922" stroke-width="1.5"/>
  <text x="400" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">QUIC</text>
  <text x="400" y="105" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">(TLS 1.3 built in)</text>
  <rect x="340" y="128" width="120" height="28" rx="4" fill="#8b949e" opacity="0.15" stroke="#8b949e" stroke-width="1"/>
  <text x="400" y="147" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">UDP</text>

  <!-- HOL comparison -->
  <text x="80" y="185" fill="#e6edf3" font-size="12" font-family="sans-serif" font-weight="bold" text-anchor="middle">Lost packet ×</text>
  <rect x="20" y="195" width="40" height="20" rx="3" fill="#6db33f" opacity="0.4"/>
  <rect x="64" y="195" width="40" height="20" rx="3" fill="#f85149" opacity="0.7"/>
  <text x="84" y="209" fill="#fff" font-size="10" text-anchor="middle" font-family="sans-serif">×</text>
  <rect x="108" y="195" width="40" height="20" rx="3" fill="#6db33f" opacity="0.2" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="80" y="232" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">all 3 streams blocked (TCP)</text>

  <text x="400" y="185" fill="#e6edf3" font-size="12" font-family="sans-serif" font-weight="bold" text-anchor="middle">Lost packet ×</text>
  <rect x="340" y="195" width="40" height="20" rx="3" fill="#6db33f" opacity="0.4"/>
  <rect x="384" y="195" width="40" height="20" rx="3" fill="#f85149" opacity="0.7"/>
  <text x="404" y="209" fill="#fff" font-size="10" text-anchor="middle" font-family="sans-serif">×</text>
  <rect x="428" y="195" width="40" height="20" rx="3" fill="#6db33f" opacity="0.4"/>
  <text x="340" y="232" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">only middle stream blocked (QUIC)</text>

  <!-- RTT comparison -->
  <text x="170" y="260" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="middle">TCP+TLS: 2-3 RTT to first byte</text>
  <text x="510" y="260" fill="#6db33f" font-size="11" font-family="sans-serif" text-anchor="middle">QUIC: 1 RTT (0-RTT on resume)</text>
</svg>

QUIC merges TLS into the transport, and its independent streams mean a packet loss only stalls the affected stream, not the whole connection.

## 5. Runnable example

Browsers and servers negotiate HTTP/3 automatically; you can observe it with `curl`. The following shows how to check which protocol a server is using and inspect the difference. Since QUIC requires UDP and TLS, we'll use `curl` with a real HTTPS endpoint.

```bash
# How to run: paste into any terminal with curl installed (macOS/Linux default)

# Check if a server supports HTTP/3 — look for "alt-svc: h3" header
curl -s -I --http2 https://cloudflare.com | grep -i "alt-svc\|http"

# Force HTTP/1.1
echo "=== HTTP/1.1 ==="
curl -s -o /dev/null -w "Protocol: %{http_version}  Time: %{time_total}s\n" \
  --http1.1 https://cloudflare.com

# Force HTTP/2
echo "=== HTTP/2 ==="
curl -s -o /dev/null -w "Protocol: %{http_version}  Time: %{time_total}s\n" \
  --http2 https://cloudflare.com

# HTTP/3 (curl 7.88+ with QUIC support compiled in — Homebrew curl has it)
echo "=== HTTP/3 ==="
curl -s -o /dev/null -w "Protocol: %{http_version}  Time: %{time_total}s\n" \
  --http3-only https://cloudflare.com 2>/dev/null || echo "(HTTP/3 not in this curl build)"

# Inspect QUIC frames in detail (if http3 available)
curl -v --http3-only https://cloudflare.com 2>&1 | head -30
```

**How to run:** paste into a terminal. The first command reveals the `Alt-Svc: h3=":443"` header that browsers use to discover HTTP/3 support.

## 6. Walkthrough

- `curl -I --http2` — sends a HEAD request negotiating HTTP/2; the `Alt-Svc` response header is how the server advertises HTTP/3 support. Browsers store this and use QUIC on the *next* visit.
- `%{http_version}` in curl's write-out format prints `1.1`, `2`, or `3` depending on the negotiated version.
- `--http3-only` — forces QUIC/UDP. This only works if curl was compiled with a QUIC library (ngtcp2, quiche, etc.). macOS's default curl uses LibreSSL which often lacks QUIC; Homebrew's `curl` package includes it.
- The first connection is usually 1-RTT with QUIC; a second connection to the same server typically achieves 0-RTT using stored session tickets.
- `Alt-Svc: h3=":443"; ma=86400` — the `ma` (max-age) tells the client to remember this for 86400 seconds.

## 7. Gotchas & takeaways

> QUIC travels over UDP port 443. Many enterprise firewalls block UDP 443 or rate-limit it. Browsers fall back to HTTP/2 automatically when QUIC is blocked — check your firewall if HTTP/3 isn't being used even though the server supports it.

> QUIC is implemented in **user-space**, not the OS kernel like TCP. This means each QUIC library (Chrome's, Firefox's, Cloudflare's) can iterate independently — but it also means CPU cost is slightly higher than kernel-accelerated TCP.

- HTTP/3 = HTTP/2 semantics + QUIC transport. Switching from HTTP/2 to HTTP/3 is transparent to application code.
- QUIC always encrypts — there is no plaintext QUIC. TLS 1.3 is mandatory and built into the handshake.
- Packet loss only stalls the affected stream in QUIC; TCP's in-order delivery stalls all streams.
- Connection IDs (not IP:port 4-tuples) let QUIC connections survive network changes (Wi-Fi → cellular).
- `Alt-Svc` headers and DNS HTTPS records are how servers advertise HTTP/3 support to clients.
