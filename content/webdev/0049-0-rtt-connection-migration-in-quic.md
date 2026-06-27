---
card: webdev
gi: 49
slug: 0-rtt-connection-migration-in-quic
title: 0-RTT & connection migration in QUIC
---

## 1. What it is

QUIC offers two capabilities that go beyond what TCP can do:

**0-RTT (zero round-trip time resumption):** when a client reconnects to a server it has talked to before, it can send application data (an HTTP request) in the very first packet — before any handshake response arrives. The latency for the first byte drops from 1 RTT to 0 RTT.

**Connection migration:** a QUIC connection is identified by a **Connection ID** chosen by each endpoint, not by the IP-address:port 4-tuple that TCP uses. If the client's IP changes (e.g., phone switches from Wi-Fi to cellular mid-session), the QUIC connection keeps working without interruption. The client sends a path validation probe on the new network path, and the server updates which address it sends to.

## 2. Why & when

**0-RTT matters for repeat visitors.** The first ever visit to a server still costs 1 RTT for the QUIC+TLS handshake. But 90%+ of requests are to hosts the client has seen before (CDNs, APIs, first-party servers). 0-RTT turns those repeat connections into zero-latency starts.

**Connection migration matters for mobile users.** A phone moving between Wi-Fi and cellular used to break HTTP/2 connections (TCP sees a new IP, tears down the socket). With QUIC, the same connection continues — important for streaming, in-progress API calls, and download resumption.

You won't configure these explicitly as a developer — they're enabled automatically by QUIC-capable clients and servers. But knowing the limits is important:

- 0-RTT data is **replay-vulnerable**: an attacker who captures a 0-RTT packet can replay it (safe for GET; potentially dangerous for POST/PUT with side effects).
- Connection migration requires the server's load balancer to route by Connection ID, not by IP.

## 3. Core concept

**0-RTT explained with session tickets:**

Think of a hotel key card. The first time you check in, staff verify your ID (1 RTT handshake). On checkout you keep the key card (session ticket). Next visit you swipe the card before the desk agent even looks up — you're already inside (0 RTT). The catch: if someone steals your key card and swipes it first, the front desk can't tell the difference (replay attack).

Technically: after a successful QUIC+TLS 1.3 handshake, the server sends the client a **session ticket** (an encrypted blob of session keys). On the next connection, the client sends this ticket in the first flight and can include HTTP requests in the same datagram. The server decrypts the ticket, verifies it hasn't expired, and processes the requests — all before sending its own handshake response.

**Connection migration explained:**

```
TCP: connection = (src IP, src port, dst IP, dst port)
     IP changes → TCP tears down, reconnects from zero

QUIC: connection = (Connection ID)
     IP changes → client sends PATH_CHALLENGE on new path
                  server responds PATH_RESPONSE
                  connection continues, no data lost
```

The Connection ID is random bytes chosen by each endpoint. Servers may issue multiple Connection IDs to a client so it can rotate them when migrating (helps prevent linkability — a new path gets a new CID).

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="0-RTT resumption: client sends request in first packet using stored session ticket; connection migration: Connection ID stays stable across IP change">
  <defs>
    <marker id="a49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#d29922"/></marker>
  </defs>

  <!-- 0-RTT section -->
  <text x="20" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">0-RTT resumption</text>
  <rect x="20" y="32" width="70" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="55" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="210" y="32" width="70" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="245" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <!-- First visit: 1-RTT -->
  <text x="20" y="75" fill="#8b949e" font-size="10" font-family="sans-serif">First visit (1-RTT):</text>
  <line x1="90" y1="85" x2="208" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a49)"/>
  <text x="148" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ClientHello + QUIC init</text>
  <line x1="210" y1="100" x2="92" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#b49)"/>
  <text x="150" y="114" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ServerHello + session ticket</text>
  <line x1="90" y1="125" x2="208" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a49)"/>
  <text x="148" y="120" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">GET /page (1-RTT)</text>

  <!-- Second visit: 0-RTT -->
  <text x="20" y="155" fill="#e6edf3" font-size="10" font-family="sans-serif">Resume visit (0-RTT):</text>
  <line x1="90" y1="165" x2="208" y2="165" stroke="#d29922" stroke-width="2" marker-end="url(#c49)"/>
  <text x="148" y="160" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">ticket + GET /page (0-RTT data!)</text>
  <line x1="210" y1="180" x2="92" y2="180" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b49)"/>
  <text x="150" y="194" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK (server accepted 0-RTT)</text>

  <!-- Connection migration section -->
  <text x="360" y="22" fill="#e6edf3" font-size="13" font-family="sans-serif" font-weight="bold">Connection migration</text>
  <rect x="360" y="32" width="100" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="410" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Phone</text>
  <rect x="580" y="32" width="80" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="620" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>

  <!-- On Wi-Fi -->
  <text x="360" y="72" fill="#8b949e" font-size="10" font-family="sans-serif">On Wi-Fi (IP: 192.168.1.5):</text>
  <line x1="460" y1="82" x2="578" y2="82" stroke="#6db33f" stroke-width="2" marker-end="url(#a49)"/>
  <text x="518" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">CID=a1b2 streaming</text>
  <line x1="580" y1="96" x2="462" y2="96" stroke="#79c0ff" stroke-width="2" marker-end="url(#b49)"/>

  <!-- Network change -->
  <rect x="360" y="112" width="300" height="18" rx="3" fill="#d29922" opacity="0.15" stroke="#d29922" stroke-width="1"/>
  <text x="510" y="125" fill="#d29922" font-size="10" text-anchor="middle" font-family="sans-serif">📶 switches to cellular (IP: 10.0.0.5)</text>

  <!-- On cellular — same CID -->
  <text x="360" y="150" fill="#8b949e" font-size="10" font-family="sans-serif">On cellular (new IP, same CID):</text>
  <line x1="460" y1="160" x2="578" y2="160" stroke="#6db33f" stroke-width="2" marker-end="url(#a49)"/>
  <text x="518" y="155" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">CID=a1b2 PATH_CHALLENGE</text>
  <line x1="580" y1="174" x2="462" y2="174" stroke="#79c0ff" stroke-width="2" marker-end="url(#b49)"/>
  <text x="518" y="188" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">PATH_RESPONSE → continue</text>
  <line x1="460" y1="200" x2="578" y2="200" stroke="#6db33f" stroke-width="2" marker-end="url(#a49)"/>
  <text x="518" y="216" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">CID=a1b2 streaming continues</text>

  <!-- TCP comparison -->
  <text x="360" y="250" fill="#f85149" font-size="11" font-family="sans-serif">TCP: IP change = connection reset = reload</text>
  <text x="360" y="268" fill="#6db33f" font-size="11" font-family="sans-serif">QUIC: IP change = PATH_CHALLENGE = seamless</text>
</svg>

0-RTT sends the HTTP request in the first packet (no wait); connection migration validates the new path with `PATH_CHALLENGE` and continues the same connection after an IP change.

## 5. Runnable example

We can't run QUIC in plain Node without a library, but we can simulate the conceptual logic: session ticket storage and path validation signalling.

```js
// save as quic-concepts.js  —  node quic-concepts.js  (no installs)

// Simulates what QUIC + TLS 1.3 session tickets do conceptually.
// Real QUIC uses ngtcp2/quiche libraries; this illustrates the state machine.

const crypto = require("crypto");

// --- Session ticket store (server side) ---
const SESSION_KEY = crypto.randomBytes(32);

function issueSessionTicket(clientId) {
  const payload = JSON.stringify({ clientId, issued: Date.now() });
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", SESSION_KEY, iv);
  const enc = Buffer.concat([cipher.update(payload, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return { enc: enc.toString("base64"), iv: iv.toString("base64"), tag: tag.toString("base64") };
}

function verifySessionTicket(ticket) {
  try {
    const decipher = crypto.createDecipheriv(
      "aes-256-gcm",
      SESSION_KEY,
      Buffer.from(ticket.iv, "base64")
    );
    decipher.setAuthTag(Buffer.from(ticket.tag, "base64"));
    const payload = decipher.update(Buffer.from(ticket.enc, "base64")) + decipher.final("utf8");
    const { clientId, issued } = JSON.parse(payload);
    const age = Date.now() - issued;
    if (age > 7 * 24 * 60 * 60 * 1000) throw new Error("ticket expired");
    return { valid: true, clientId, ageMs: age };
  } catch (e) {
    return { valid: false, reason: e.message };
  }
}

// --- Simulate 0-RTT flow ---
console.log("=== First connection (1-RTT) ===");
console.log("Client → Server: ClientHello");
console.log("Server → Client: ServerHello + handshake");
const ticket = issueSessionTicket("phone-abc");
console.log("Server → Client: session ticket issued");
console.log("Client: stores ticket for next visit\n");

console.log("=== Second connection (0-RTT) ===");
console.log("Client → Server: [ticket + GET /page] in first packet — no RTT wait");
const result = verifySessionTicket(ticket);
console.log("Server: ticket verification →", result);
console.log("Server → Client: 200 OK (accepted 0-RTT data)\n");

// --- Simulate connection migration ---
console.log("=== Connection migration ===");
const connectionId = crypto.randomBytes(8).toString("hex");
console.log(`Connection established, CID=${connectionId}, src=192.168.1.5:50000`);
console.log("... streaming 50% done ...\n");
console.log("📶 Network change: Wi-Fi → Cellular (new src IP: 10.0.0.5)");
console.log(`Client → Server: [CID=${connectionId}] PATH_CHALLENGE on 10.0.0.5`);
console.log(`Server → Client: [CID=${connectionId}] PATH_RESPONSE — new path validated`);
console.log(`Streaming continues on 10.0.0.5 with same CID=${connectionId}`);
console.log("TCP would have reset; QUIC continues seamlessly.");
```

**How to run:** `node quic-concepts.js` — observe the 0-RTT ticket flow and migration signalling.

## 6. Walkthrough

- `issueSessionTicket`: encrypts a payload with AES-256-GCM (authenticated encryption). Real QUIC uses TLS 1.3 session tickets with negotiated cipher suites — same idea. The server keeps the key; the client keeps the encrypted blob.
- `verifySessionTicket`: decrypts and authenticates the ticket. The GCM auth tag ensures tampering is detected. Age check prevents very old tickets.
- `0-RTT` simulation prints the timing: after the first connection the client has a ticket. On the second, it sends the ticket *and* the HTTP request together — the server can respond without a handshake round trip.
- `connectionId = crypto.randomBytes(8).toString("hex")` — QUIC Connection IDs are typically 4–20 bytes of random. They don't encode any routing info, so load balancers must use a consistent hashing scheme or store CID→server mappings.
- `PATH_CHALLENGE` / `PATH_RESPONSE`: the real QUIC frame names (RFC 9000 §8.2). After detecting a path change, the client sends a challenge frame with a random 8-byte payload; the server echoes it back to prove the new path is two-way reachable.

## 7. Gotchas & takeaways

> **0-RTT data is replay-vulnerable.** A network attacker who records a 0-RTT packet can replay it later. TLS 1.3 makes idempotent requests (GET, HEAD) safe for 0-RTT; the spec recommends servers reject non-idempotent 0-RTT (POST, PUT) unless they have anti-replay protection in place.

> **Connection migration doesn't work through symmetric NAT.** Many NATs change the external port on every packet, breaking the CID routing assumption. QUIC connection migration works best on networks that preserve the client's external address (most cellular networks, direct IPv6).

- 0-RTT saves exactly 1 RTT on reconnections — meaningful on latency-sensitive mobile connections.
- Connection IDs (CIDs) are what make QUIC connections portable across IP changes.
- Servers should offer multiple CIDs per connection so clients can rotate them on path migration (preventing CID-based tracking).
- Session ticket lifetime matters: shorter = more secure, longer = more 0-RTT hits. TLS 1.3 recommends ≤7 days.
- Real QUIC in production requires a library: ngtcp2, quiche (Cloudflare/Mozilla), MsQuic (Microsoft), or lsquic (LiteSpeed).
