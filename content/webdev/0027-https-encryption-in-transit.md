---
card: webdev
gi: 27
slug: https-encryption-in-transit
title: HTTPS & encryption in transit
---

## 1. What it is

**HTTPS** (HyperText Transfer Protocol Secure) is HTTP running inside a TLS tunnel. The HTTP part — request methods, status codes, headers, body — is identical to plain HTTP. The TLS layer wraps it so that:

- All bytes are **encrypted** before leaving the sender's network stack.
- Any tampering in transit causes the receiver to discard the packet.
- The server's identity is confirmed via its certificate.

**Encryption in transit** is the broader concept: data is protected while moving across a network, but it is decrypted at the destination. The database on the other side might store the data unencrypted — that's a separate concern (encryption at rest). HTTPS only guarantees the trip, not what happens at either end.

The URL scheme tells you which is in use: `http://` → plaintext, `https://` → encrypted. Port 80 is conventional for HTTP, port 443 for HTTPS.

## 2. Why & when

Without encryption in transit any network node on the path — routers, ISPs, coffee-shop Wi-Fi, VPN endpoints, CDN edge nodes — can read and silently modify the content. Classic attacks made possible by plain HTTP:

- **Eavesdropping** — reading passwords, session tokens, personal data.
- **Injection** — ISPs used to inject ads; malware inserts crypto miners.
- **Session hijacking** — stealing a cookie seen in plain text to impersonate a user.

HTTPS is now the baseline, not a premium feature. Browsers mark HTTP pages "Not Secure," Google ranks HTTPS sites higher, and HTTP/2 (and HTTP/3) require TLS by spec. Use HTTPS everywhere, including internal services and dev tunnels.

## 3. Core concept

Think of it as a tamper-evident armoured van transporting cash. The destination (bank) knows what the van should contain, and a broken seal proves tampering. The important subtlety: **the van driver (network) can't read the cash** — they just carry the locked box. But once the box is unlocked at the bank (server), the money (data) is in plain view.

The encryption in transit lifecycle:

1. **Client encrypts** the HTTP request using the session key agreed during the TLS handshake.
2. **Ciphertext travels** across the internet — routers only see an opaque stream.
3. **Server decrypts** using the same session key and sees the plain HTTP request.
4. **Server encrypts** the response.
5. **Client decrypts** and renders the page.

The session key is **symmetric** (AES-GCM or ChaCha20-Poly1305) — same key on both sides. It was established without being transmitted, via asymmetric key exchange during the handshake.

Key property: **forward secrecy**. Modern TLS uses ephemeral keys (ECDHE) for each session. Even if the server's private key is compromised later, past sessions cannot be decrypted because the session keys were never stored.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTPS encryption in transit — data encrypted between browser and server, plaintext at each end">
  <defs>
    <marker id="ha" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Browser box -->
  <rect x="20" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="107" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="85" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">sees plaintext</text>
  <!-- Encrypted tunnel -->
  <rect x="175" y="90" width="320" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="335" y="114" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">🔒 Encrypted ciphertext (TLS tunnel)</text>
  <!-- Server box -->
  <rect x="520" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="590" y="107" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="590" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">sees plaintext</text>
  <!-- request arrow -->
  <line x1="150" y1="102" x2="175" y2="102" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="495" y1="102" x2="520" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ha)"/>
  <text x="335" y="74" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">HTTPS request: GET /account</text>
  <!-- ISP eavesdropper -->
  <rect x="280" y="155" width="110" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="335" y="170" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">ISP / router</text>
  <text x="335" y="184" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">sees only ciphertext</text>
  <line x1="335" y1="130" x2="335" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
</svg>

Network intermediaries carry the ciphertext but cannot read or modify it; only the two endpoints hold the session key.

## 5. Runnable example

This Node.js script shows how an HTTPS request looks from the outside (opaque) and from the inside (readable). No installs needed — Node's built-in `https` module is used.

```js
// save as https_demo.js — needs Node.js
const https = require("https");

// Make an HTTPS GET request to a public API
const options = {
  hostname: "httpbin.org",
  path: "/get",
  method: "GET",
  // Node verifies the server cert by default; set rejectUnauthorized: false
  // only for self-signed certs in test environments — NEVER in production
};

const req = https.request(options, (res) => {
  console.log(`Status: ${res.statusCode}`);
  console.log(`TLS cipher: ${res.socket.getCipher().name}`);
  console.log(`TLS version: ${res.socket.getCipher().version}`);

  let body = "";
  res.on("data", (chunk) => (body += chunk));
  res.on("end", () => {
    const parsed = JSON.parse(body);
    console.log(`Server saw our IP as: ${parsed.origin}`);
  });
});

req.on("error", (e) => console.error("Request failed:", e.message));
req.end();
```

**How to run:** save as `https_demo.js`, then run `node https_demo.js`. Requires internet access.

Expected output:
```
Status: 200
TLS cipher: TLS_AES_128_GCM_SHA256
TLS version: TLSv1.3
Server saw our IP as: 203.0.113.42
```

## 6. Walkthrough

- `https.request(options, ...)` — Node opens a TCP connection, performs the TLS handshake automatically, then sends the HTTP GET request inside the encrypted tunnel.
- `res.socket.getCipher()` — after the handshake, the socket object exposes which cipher suite was negotiated. This confirms encryption is active and shows what algorithm is in use.
- `TLS_AES_128_GCM_SHA256` is the cipher: AES-128 (symmetric encryption) in GCM mode (provides both encryption and integrity) with SHA-256 (hash function).
- The response body from `httpbin.org/get` echoes back what the server received — including our public IP address. The server could read the request because TLS decrypted it at the server end.
- `res.on("data", ...)` / `res.on("end", ...)` — HTTP response body arrives in chunks; accumulate and parse JSON when complete.
- Note: the data we printed from the body was plaintext on both ends. What was encrypted was the wire bytes between the two sockets.

## 7. Gotchas & takeaways

> **HTTPS encrypts the path and body, but not the hostname.** The `Host` header and SNI (Server Name Indication) field in the TLS ClientHello are visible to network observers. So an ISP knows you visited `bank.com` but not which page or what data you submitted. (ESNI / ECH, newer TLS extensions, can hide even the hostname.)

> **"Encryption in transit" ≠ "private."** The server decrypts everything. A rogue server, a misconfigured CDN, or server-side logging can expose your data after it arrives. HTTPS only protects the network hop.

- `rejectUnauthorized: false` in Node disables cert verification — never use it in production, it defeats HTTPS authentication entirely.
- Mixed content (an HTTPS page loading `http://` resources) triggers browser warnings and blocks the insecure resource in modern browsers.
- HTTP Strict Transport Security (HSTS) header tells browsers to always use HTTPS for your domain — prevents downgrade attacks even if a user types `http://`.
- Let's Encrypt + Certbot automates certificate issuance and renewal; there's no reason to buy a DV certificate anymore.
