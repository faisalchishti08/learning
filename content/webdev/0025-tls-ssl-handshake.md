---
card: webdev
gi: 25
slug: tls-ssl-handshake
title: TLS/SSL handshake
---

## 1. What it is

The **TLS handshake** is the brief negotiation that happens before any HTTPS data flows. TLS (Transport Layer Security) is the current protocol; SSL (Secure Sockets Layer) is its older predecessor that was replaced, but the name "SSL" stuck in everyday speech. When your browser connects to `https://example.com`, the two sides spend a fraction of a second agreeing on:

1. **Which cipher suite to use** — the algorithms for key exchange, encryption, and integrity checking.
2. **The server's identity** — the server presents a certificate proving it really is `example.com`.
3. **A shared secret** — without ever sending the secret across the wire, both sides independently arrive at the same encryption keys.

After that short negotiation, all data travels encrypted. The handshake happens once per connection; subsequent requests on the same connection reuse the established session.

## 2. Why & when

Without TLS, HTTP is plain text. Anyone between you and the server — an ISP, a café Wi-Fi router, a rogue access point — can read every byte or silently alter it. TLS solves three problems at once:

- **Confidentiality** — data is encrypted; eavesdroppers see noise.
- **Integrity** — a tampered packet is detected and discarded.
- **Authentication** — you know you're talking to the real server, not an impostor.

The handshake is triggered whenever a client opens a new TLS connection: first visit to an HTTPS site, an API call from a mobile app, a service-to-service request inside a data centre. Modern TLS 1.3 reduced the handshake to **one round trip** (older TLS 1.2 needed two), so the cost is minimal.

## 3. Core concept

Think of it like establishing a private conversation with a stranger in a crowded room using a lock-and-key trick:

1. **ClientHello** — the client announces the TLS version and cipher suites it supports, plus a random nonce.
2. **ServerHello + Certificate** — the server picks a cipher suite, sends its own nonce, and presents its certificate (its identity card, signed by a trusted authority).
3. **Key exchange** — using **asymmetric cryptography** (e.g. ECDH), both sides contribute a public value. Each side can compute the same shared secret without the secret itself ever leaving either machine.
4. **Finished messages** — both sides send a "Finished" message encrypted with the new keys. If the other side can decrypt it, the keys are correct and the identity is confirmed.
5. **Application data flows** — from here, all data uses fast **symmetric encryption** (e.g. AES-GCM) derived from the shared secret.

The asymmetric step (expensive) bootstraps the symmetric step (fast). Only the handshake pays the asymmetric cost; bulk data pays only the cheap symmetric cost.

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TLS 1.3 handshake sequence between client and server">
  <!-- panels -->
  <rect x="30" y="20" width="120" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="45" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="530" y="20" width="120" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="590" y="45" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Server</text>
  <!-- vertical lifelines -->
  <line x1="90" y1="60" x2="90" y2="280" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="590" y1="60" x2="590" y2="280" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <!-- arrows -->
  <defs>
    <marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <!-- ClientHello -->
  <line x1="90" y1="90" x2="580" y2="90" stroke="#6db33f" stroke-width="1.8" marker-end="url(#a)"/>
  <text x="335" y="82" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ClientHello (TLS ver, cipher suites, nonce)</text>
  <!-- ServerHello + Cert -->
  <line x1="590" y1="130" x2="100" y2="130" stroke="#79c0ff" stroke-width="1.8" marker-end="url(#b)"/>
  <text x="335" y="122" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ServerHello + Certificate + key share</text>
  <!-- Finished client -->
  <line x1="90" y1="180" x2="580" y2="180" stroke="#6db33f" stroke-width="1.8" marker-end="url(#a)"/>
  <text x="335" y="172" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Finished (encrypted, proves keys match)</text>
  <!-- Finished server -->
  <line x1="590" y1="220" x2="100" y2="220" stroke="#79c0ff" stroke-width="1.8" marker-end="url(#b)"/>
  <text x="335" y="212" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Finished (encrypted)</text>
  <!-- App data -->
  <line x1="90" y1="260" x2="580" y2="260" stroke="#8b949e" stroke-width="1.8" marker-end="url(#a)"/>
  <text x="335" y="252" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Encrypted application data (HTTP request)</text>
</svg>

TLS 1.3 completes the handshake in **one round trip**; application data can follow immediately after the client's Finished message.

## 5. Runnable example

Use `curl` to see the TLS handshake details — no install needed on macOS/Linux.

```bash
# -v = verbose; shows TLS version, cipher suite, and certificate chain
curl -v --tlsv1.3 https://example.com 2>&1 | head -50
```

Expected output (trimmed):
```
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
* TLSv1.3 (IN),  TLS handshake, Server hello (2):
* TLSv1.3 (IN),  TLS handshake, Certificate (11):
* TLSv1.3 (IN),  TLS handshake, FINISHED (20):
* TLSv1.3 (OUT), TLS handshake, Finished (20):
* SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256
* Server certificate:
*  subject: C=US, ST=California, L=Los Angeles; O=Internet Corporation for Assigned Names…
*  start date: Jan 13 00:00:00 2025 GMT
*  expire date: Feb 12 23:59:59 2026 GMT
*  SSL certificate verify ok.
```

**How to run:** open any terminal and paste the command. `curl` ships with macOS; on Debian/Ubuntu run `sudo apt install curl` first.

## 6. Walkthrough

- `-v` turns on verbose mode; curl prints every TLS message with direction (`OUT`/`IN`) and type.
- `--tlsv1.3` forces the minimum version to TLS 1.3 so we see the modern one-RTT handshake (drop this flag to allow 1.2 fallback if the server needs it).
- `TLS handshake, Client hello` — curl sends the ClientHello with its supported cipher suites.
- `TLS handshake, Server hello` + `Certificate` arrive together — TLS 1.3 combines them into one flight, saving a round trip versus TLS 1.2.
- `TLS handshake, FINISHED (20)` from the server means "my keys are derived, I'm ready."
- `TLS handshake, Finished (20)` from `OUT` (curl) confirms our keys match — handshake complete.
- `SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256` — the negotiated symmetric cipher (AES-128 in GCM mode with SHA-256 for integrity).
- `SSL certificate verify ok` — curl checked the certificate chain against the system's trusted CA store and it passed.

The actual HTTP request travels in the lines after all this — only after the handshake is done.

## 7. Gotchas & takeaways

> **"SSL" is dead but the name lives on.** SSL 2.0, 3.0, and TLS 1.0/1.1 are all deprecated and blocked by modern browsers. When someone says "SSL certificate" they actually mean a TLS certificate. Use TLS 1.2 minimum; prefer 1.3.

> **The handshake authenticates the server, not the user.** The client verifies the server's certificate, but the server doesn't automatically verify the client. Client certificates exist but are rarely used for public web traffic — logins handle user auth separately.

- TLS handshake happens once per TCP connection; HTTP/2 and HTTP/3 keep connections alive so the cost is amortised.
- Asymmetric crypto (e.g. ECDH) is used only during key exchange; bulk data uses symmetric (AES-GCM) which is orders of magnitude faster.
- TLS 1.3 saves one full round trip versus TLS 1.2 — meaningful on high-latency mobile connections.
- Certificate expiry breaks HTTPS hard: browsers show an error page, not degraded functionality. Set renewal reminders or use auto-renew (e.g. Let's Encrypt + Certbot).
