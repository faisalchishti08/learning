---
card: webdev
gi: 24
slug: udp-vs-tcp
title: UDP vs TCP
---

## 1. What it is

**TCP** (Transmission Control Protocol) and **UDP** (User Datagram Protocol) are the two main transport-layer protocols. Both run on top of IP and both use port numbers, but they make fundamentally different trade-offs:

- **TCP** is **reliable, ordered, connection-oriented**. It guarantees every byte arrives, in order, exactly once — or you get an error. Cost: connection overhead, flow control, retransmissions.
- **UDP** is **unreliable, unordered, connectionless**. It fires a packet and forgets. Delivery is not guaranteed, ordering is not guaranteed, and duplicates can happen. Cost: nearly zero overhead.

## 2. Why & when

Neither is universally better. The right choice depends on what "correctness" means for your application.

**Use TCP when:**
- Data must arrive completely and in order (HTTP/HTTPS, database queries, file downloads, email, SSH).
- A missing byte corrupts the result — an HTML page with chunks missing is useless.

**Use UDP when:**
- Timeliness matters more than completeness (real-time audio/video calls, gaming, live telemetry).
- Old data is worthless — a video frame from 200 ms ago is worse than skipping the frame entirely.
- You implement reliability yourself at a higher level (DNS, QUIC, DTLS).

**Real-world uses:**

| Protocol | Transport | Why |
|---------|-----------|-----|
| HTTP/1.1, HTTP/2 | TCP | Documents must be complete |
| HTTP/3 / QUIC | UDP | QUIC rebuilds reliability on UDP, avoids TCP head-of-line blocking |
| DNS | UDP (+ TCP fallback) | Single small query/response — fast, stateless |
| WebRTC (video/audio) | UDP | Real-time; stale frames discarded |
| Online games | UDP | Position updates; old state is useless |
| NTP (time sync) | UDP | Tiny packets; latency matters more than reliability |
| SSH, SFTP | TCP | Must be exact byte-for-byte |

## 3. Core concept

Think of TCP like sending registered mail: every letter is tracked, signed for at delivery, and re-sent if it goes missing. The post office guarantees arrival order.

UDP is like shouting into a crowded room: you say what you have to say, and whoever hears it hears it. No follow-up, no confirmation, no guarantee the message arrives at all — but it's instant.

**Key property differences:**

| Property | TCP | UDP |
|---------|-----|-----|
| Connection setup | 3-way handshake | None |
| Delivery guarantee | Yes (retransmission) | No |
| Ordering | Yes (sequence numbers) | No |
| Duplicate prevention | Yes | No |
| Flow control | Yes (receiver window) | No |
| Congestion control | Yes (AIMD algorithm) | No |
| Header size | 20–60 bytes | 8 bytes |
| Latency | +1 RTT (handshake) | Zero setup |
| Suitable for | Files, web, SSH | Streaming, games, DNS |

**Why UDP for DNS?** A typical DNS query and response are each under 512 bytes — they each fit in a single UDP datagram. The overhead of a TCP handshake would triple the number of packets. If the DNS response is too large (DNSSEC, many records), DNS falls back to TCP automatically.

**Why QUIC (HTTP/3) uses UDP:** TCP head-of-line blocking means one dropped packet stalls all multiplexed HTTP/2 streams on a connection. QUIC implements its own reliable delivery per stream, so a lost packet for stream A doesn't block stream B — impossible with TCP because the OS retransmits before the application sees anything.

## 4. Diagram

<svg viewBox="0 0 640 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side comparison of TCP reliable ordered delivery and UDP fire-and-forget delivery">
  <!-- TCP column -->
  <text x="160" y="24" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">TCP</text>

  <rect x="10" y="34" width="300" height="260" rx="8" fill="#1c2430"/>

  <!-- TCP lifelines -->
  <line x1="80"  y1="50" x2="80"  y2="270" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="250" y1="50" x2="250" y2="270" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="80"  y="48" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Sender</text>
  <text x="250" y="48" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Receiver</text>

  <!-- SYN -->
  <line x1="82" y1="66" x2="248" y2="76" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ua)"/>
  <text x="165" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">SYN</text>
  <!-- SYN-ACK -->
  <line x1="248" y1="88" x2="82" y2="98" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ub)"/>
  <text x="165" y="104" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">SYN-ACK</text>
  <!-- ACK -->
  <line x1="82" y1="112" x2="248" y2="122" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ua)"/>
  <text x="165" y="110" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">ACK</text>

  <!-- Data 1 -->
  <line x1="82" y1="136" x2="248" y2="146" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#ua)"/>
  <text x="165" y="133" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">DATA seq=1</text>
  <line x1="248" y1="158" x2="82" y2="168" stroke="#79c0ff" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#ub)"/>
  <text x="165" y="176" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">ACK seq=2</text>

  <!-- Data 2 — lost, retransmit -->
  <line x1="82" y1="188" x2="190" y2="196" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="135" y="185" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">DATA seq=2 ✗ lost</text>
  <text x="210" y="200" fill="#8b949e" font-size="8" font-family="sans-serif">×</text>
  <!-- Retransmit -->
  <line x1="82" y1="212" x2="248" y2="222" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#ua)"/>
  <text x="165" y="210" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">RETRANSMIT seq=2</text>
  <line x1="248" y1="234" x2="82" y2="244" stroke="#79c0ff" stroke-width="1" stroke-dasharray="2,2" marker-end="url(#ub)"/>
  <text x="165" y="254" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">ACK seq=3</text>

  <!-- UDP column -->
  <text x="480" y="24" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">UDP</text>

  <rect x="330" y="34" width="300" height="260" rx="8" fill="#1c2430"/>

  <!-- UDP lifelines -->
  <line x1="400" y1="50" x2="400" y2="270" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="570" y1="50" x2="570" y2="270" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="400" y="48" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Sender</text>
  <text x="570" y="48" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Receiver</text>

  <!-- No handshake label -->
  <text x="485" y="76" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(no handshake)</text>

  <!-- Datagram 1 -->
  <line x1="402" y1="100" x2="568" y2="110" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#ua)"/>
  <text x="485" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Datagram 1 ✓</text>

  <!-- Datagram 2 — lost, not retransmitted -->
  <line x1="402" y1="140" x2="490" y2="147" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="445" y="137" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Datagram 2 ✗ lost</text>
  <text x="510" y="152" fill="#8b949e" font-size="8" font-family="sans-serif">× (gone)</text>

  <!-- Datagram 3 -->
  <line x1="402" y1="175" x2="568" y2="185" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#ua)"/>
  <text x="485" y="172" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Datagram 3 ✓</text>

  <text x="485" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">No retransmit.</text>
  <text x="485" y="236" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">App decides what to do.</text>

  <defs>
    <marker id="ua" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="ub" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

TCP detects and retransmits lost packet 2; UDP fires and forgets — packet 2 is simply gone, and the app chooses whether to care.

## 5. Runnable example

```js
// save as udp-demo.js — Node.js, no installs
// Sends 5 UDP datagrams from a client to a server; server logs what arrives
// (On a loopback interface all 5 arrive, but the code shows the fire-and-forget pattern)

const dgram = require("dgram");

const server = dgram.createSocket("udp4");

server.on("message", (msg, rinfo) => {
  console.log(`[server] Received: "${msg}" from ${rinfo.address}:${rinfo.port}`);
});

server.on("listening", () => {
  const { address, port } = server.address();
  console.log(`[server] UDP listening on ${address}:${port}`);

  // Client: send 5 datagrams, no connection, no ACK
  const client = dgram.createSocket("udp4");

  for (let i = 1; i <= 5; i++) {
    const message = Buffer.from(`datagram-${i}`);
    client.send(message, 41234, "127.0.0.1", (err) => {
      if (err) console.error(`[client] Send error: ${err.message}`);
      // No guarantee the message arrived — just fire and move on
    });
  }

  // Tear down after 200 ms (no four-way handshake needed)
  setTimeout(() => {
    client.close();
    server.close();
    console.log("[client] All datagrams sent (fire and forget)");
  }, 200);
});

server.bind(41234, "127.0.0.1");
```

**How to run:** `node udp-demo.js` — no npm install; `dgram` is built into Node.

Expected output:
```
[server] UDP listening on 127.0.0.1:41234
[server] Received: "datagram-1" from 127.0.0.1:NNNNN
[server] Received: "datagram-2" from 127.0.0.1:NNNNN
[server] Received: "datagram-3" from 127.0.0.1:NNNNN
[server] Received: "datagram-4" from 127.0.0.1:NNNNN
[server] Received: "datagram-5" from 127.0.0.1:NNNNN
[client] All datagrams sent (fire and forget)
```

## 6. Walkthrough

- `dgram.createSocket("udp4")` — creates a UDP socket. No connection, no handshake, no state. Contrast with `net.createConnection()` for TCP which requires the three-way handshake before any callback fires.
- `server.bind(41234, ...)` — binds to port 41234 and starts listening for incoming UDP datagrams. Unlike TCP, there's no `accept()` step — any datagram arriving on that port triggers `message` immediately.
- `client.send(message, 41234, "127.0.0.1", callback)` — fires a datagram. The callback fires when the datagram is handed to the OS network stack — **not** when it's received. There is no delivery confirmation. The callback's `err` only catches local errors (invalid address, etc.), not delivery failure.
- `for (let i = 1; i <= 5; ...)` — all five sends happen in rapid succession. On loopback they all arrive; on a real network, any could be silently dropped. The code doesn't know which.
- `setTimeout(() => { client.close(); server.close(); }, 200)` — closing a UDP socket is immediate. No FIN exchange, no `TIME_WAIT`, no half-close. This is the UDP equivalent of just hanging up without saying goodbye.

## 7. Gotchas & takeaways

> **"UDP is unreliable" does not mean "UDP is bad"** — it means the protocol is minimal on purpose. Real-time applications like video calls deliberately discard late packets; a retransmitted frame from 500 ms ago would make the call worse, not better. UDP puts the reliability decision in the application's hands.

> **UDP has no flow or congestion control.** A high-rate UDP sender can overwhelm a receiver's buffer and cause packet loss — or, worse, saturate a shared network link and starve TCP connections sharing the path. QUIC (HTTP/3) runs over UDP but implements its own congestion control to be a good network citizen.

- DNS sends queries over UDP to port 53, falling back to TCP only when the response exceeds ~512 bytes.
- WebRTC uses SRTP (Secure Real-time Transport Protocol) over UDP: UDP gives WebRTC the low-latency delivery it needs; SRTP adds encryption.
- QUIC (the transport for HTTP/3) is essentially "TCP-like reliability + TLS 1.3, all implemented over UDP datagrams" — giving browsers control over the transport logic without needing OS-level TCP changes.
- `SO_REUSEPORT` socket option lets multiple processes share a UDP port — useful for scaling DNS servers across CPU cores.
- A UDP socket can `send` without calling `bind` first — the OS auto-assigns an ephemeral source port.
