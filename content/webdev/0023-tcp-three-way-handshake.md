---
card: webdev
gi: 23
slug: tcp-three-way-handshake
title: TCP three-way handshake
---

## 1. What it is

Before two programs can exchange data over TCP, they must establish a **connection** using the **three-way handshake** — a sequence of three control messages that synchronise both sides and agree on starting sequence numbers.

The three steps are:
1. **SYN** — client sends a synchronise packet, proposing a sequence number.
2. **SYN-ACK** — server acknowledges the client's SYN and sends its own SYN.
3. **ACK** — client acknowledges the server's SYN. Connection is now open.

After the handshake, data flows. When both sides are done, a four-way **FIN/ACK** exchange tears the connection down.

## 2. Why & when

TCP is a **reliable, ordered, bidirectional** byte stream. Reliability requires both sides to know the starting sequence number of the other's data stream — that's what the handshake negotiates. Without it, neither side knows if packets are arriving in order or being lost.

The handshake is the reason:
- Every new TCP connection costs at least **1 round-trip time (RTT)** before data can flow (SYN → SYN-ACK → ACK + first data).
- HTTPS adds another 1–2 RTTs for TLS negotiation on top.
- HTTP/2 keep-alive and HTTP/3/QUIC exist partly to avoid paying this cost on every request.
- Firewalls and security tools watch for SYN floods (many SYN packets, no ACKs) — a common DoS attack that fills the server's half-open connection table.

## 3. Core concept

Think of the handshake like establishing a phone call:

1. You dial (SYN) — "I want to connect. I'll start numbering my words from 100."
2. The other person picks up and says "Got it! I'll start from 200. Hello?" (SYN-ACK).
3. You say "Hello back!" (ACK). Now you're both talking on the same channel.

The sequence numbers are critical. TCP numbers every byte of data it sends, starting from the random initial sequence number (ISN) chosen in the SYN. This lets the receiver detect gaps, duplicates, and re-order out-of-order segments.

**Detailed exchange:**

```
Client                                   Server

SYN (seq=1000)          ─────────────►
                         ◄─────────────  SYN-ACK (seq=5000, ack=1001)
ACK (ack=5001)          ─────────────►

--- Connection established ---

DATA (seq=1001)         ─────────────►
                         ◄─────────────  ACK (ack=<next byte expected>)

--- Teardown (four-way FIN) ---

FIN (seq=N)             ─────────────►
                         ◄─────────────  ACK (ack=N+1)
                         ◄─────────────  FIN (seq=M)
ACK (ack=M+1)           ─────────────►
```

SYN packets have the SYN flag set; ACK packets have the ACK flag; SYN-ACK has both. TCP packets also carry the sender's current sequence number and (if ACK is set) the next byte number it expects from the other side.

**TIME_WAIT**: after the client sends the final ACK, it stays in `TIME_WAIT` for 2 × MSL (Maximum Segment Lifetime, typically 60–120 s). This prevents delayed packets from a closed connection from being misread by a new connection on the same port.

## 4. Diagram

<svg viewBox="0 0 620 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TCP three-way handshake sequence diagram showing SYN, SYN-ACK, ACK between client and server, then data exchange and FIN teardown">
  <!-- Lifelines -->
  <line x1="120" y1="30" x2="120" y2="300" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="500" y1="30" x2="500" y2="300" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>

  <!-- Headers -->
  <rect x="50"  y="10" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="30" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Client</text>

  <rect x="430" y="10" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="30" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>

  <!-- SYN -->
  <line x1="122" y1="70" x2="498" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#ta)"/>
  <text x="310" y="66" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">SYN  seq=1000</text>

  <!-- SYN-ACK -->
  <line x1="498" y1="120" x2="122" y2="140" stroke="#79c0ff" stroke-width="2" marker-end="url(#tb)"/>
  <text x="310" y="148" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">SYN-ACK  seq=5000, ack=1001</text>

  <!-- ACK -->
  <line x1="122" y1="168" x2="498" y2="188" stroke="#6db33f" stroke-width="2" marker-end="url(#ta)"/>
  <text x="310" y="165" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">ACK  ack=5001</text>

  <!-- Connected label -->
  <rect x="210" y="194" width="200" height="22" rx="4" fill="#6db33f" opacity="0.15"/>
  <text x="310" y="210" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Connection established ✓</text>

  <!-- Data -->
  <line x1="122" y1="230" x2="498" y2="250" stroke="#e6edf3" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#ta)"/>
  <text x="310" y="227" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">DATA  (HTTP request, etc.)</text>

  <!-- FIN label -->
  <text x="310" y="282" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">… then FIN / ACK / FIN / ACK teardown</text>

  <defs>
    <marker id="ta" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="tb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

Three messages cross the network before data flows; each consumes one-way latency. A 50 ms RTT costs 50 ms minimum before the first byte of HTTP request can be sent.

## 5. Runnable example

```js
// save as handshake-observer.js — Node.js, no installs
// Creates a TCP server and a client; logs every step of the connection lifecycle

const net = require("net");

const server = net.createServer((socket) => {
  // Server side: SYN-ACK was sent automatically by the OS TCP stack.
  // This callback fires AFTER the ACK completes (connection is open).
  console.log(`[server] Connection established from ${socket.remoteAddress}:${socket.remotePort}`);
  console.log(`[server] Local sequence tracking: bytes received = ${socket.bytesRead}`);

  socket.on("data", (data) => {
    console.log(`[server] Received data: "${data.toString().trim()}"`);
    socket.write("ACK: got your message\n");
  });

  socket.on("end", () => {
    console.log("[server] Client sent FIN (half-close)");
  });

  socket.on("close", () => {
    console.log("[server] Connection fully closed (4-way FIN complete)");
    server.close();
  });
});

server.listen(5000, "127.0.0.1", () => {
  console.log("[server] Listening — waiting for SYN...");

  const client = net.createConnection({ host: "127.0.0.1", port: 5000 }, () => {
    // Client side: callback fires after ACK sent (handshake complete).
    console.log(`[client] Handshake complete — local port ${client.localPort}`);
    client.write("Hello, server!\n");
  });

  client.on("data", (data) => {
    console.log(`[client] Server replied: "${data.toString().trim()}"`);
    client.end(); // sends FIN
    console.log("[client] FIN sent");
  });
});
```

**How to run:** `node handshake-observer.js` — the OS TCP stack performs the actual three-way handshake transparently; the callbacks fire at the moments shown in the sequence diagram.

Expected output:
```
[server] Listening — waiting for SYN...
[server] Connection established from 127.0.0.1:NNNNN
[server] Local sequence tracking: bytes received = 0
[client] Handshake complete — local port NNNNN
[server] Received data: "Hello, server!"
[client] Server replied: "ACK: got your message"
[client] FIN sent
[server] Client sent FIN (half-close)
[server] Connection fully closed (4-way FIN complete)
```

## 6. Walkthrough

- `net.createServer((socket) => {...})` — the callback fires the moment the three-way handshake completes. You never write SYN or ACK manually — the OS kernel handles all TCP signalling. By the time your code runs, the connection is live.
- `server.listen(5000, "127.0.0.1", ...)` — binds port 5000 and starts listening for SYN packets. The callback fires when the server is ready, not when a client connects.
- `net.createConnection({ host, port }, () => {...})` — client side. The OS sends SYN, waits for SYN-ACK, sends ACK. When ACK is sent, the callback fires: `[client] Handshake complete`. `client.localPort` is the OS-assigned ephemeral source port.
- `client.write("Hello, server!\n")` — sends the first data packet (PSH + ACK flags). The ACK inside this packet piggybacks on top of the data — TCP combines them for efficiency.
- `client.end()` — sends a FIN packet (half-close). The client signals it has no more data to send. The server can still send more; the socket stays half-open until the server also calls `.end()` or `.destroy()`.
- `socket.on("close", ...)` — fires when the full four-way FIN exchange completes and the socket is fully torn down.

## 7. Gotchas & takeaways

> **The three-way handshake takes one full round trip.** Before a single byte of HTTP can be sent, you've already paid: DNS lookup time + one RTT for the handshake. On a 100 ms RTT link, that's 100 ms just to open the connection. HTTP/1.1 keep-alive and HTTP/2 multiplexing exist to amortise this cost.

> **`ECONNREFUSED` means the SYN was rejected** — the server is reachable at the IP level, but nothing is listening on that port (the OS sent back a TCP RST instead of SYN-ACK). `ETIMEDOUT` means the SYN was never answered — the server is unreachable or a firewall silently dropped the packet.

- TCP sequence numbers start at a **random ISN** (Initial Sequence Number), not 0. This prevents old delayed packets from being mistaken for new connection data.
- SYN flood attack: an attacker sends millions of SYN packets without completing the handshake, filling the server's SYN backlog queue. SYN cookies (a Linux kernel feature) mitigate this without state allocation per half-open connection.
- `TIME_WAIT` on the client side after a `close()` is normal and expected — don't try to suppress it by setting `SO_REUSEADDR` without understanding the implications.
- Tools: `tcpdump -n 'tcp[tcpflags] & tcp-syn != 0'` shows all SYN packets in real time; Wireshark shows the full handshake graphically.
