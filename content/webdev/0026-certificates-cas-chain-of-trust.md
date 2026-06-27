---
card: webdev
gi: 26
slug: certificates-cas-chain-of-trust
title: Certificates, CAs & chain of trust
---

## 1. What it is

A **TLS certificate** is a digitally signed document that proves a server owns a domain name. It answers the question: "How do I know I'm really talking to `bank.com` and not an impostor?" The certificate contains:

- The **domain name** it's valid for (e.g. `*.example.com`).
- The server's **public key** (used in the handshake).
- **Who signed it** — a Certificate Authority (CA).
- **Validity dates** — certificates expire (typically after 90 days to 1 year).

A **Certificate Authority (CA)** is an organisation that browsers and operating systems have agreed to trust (e.g. DigiCert, Let's Encrypt, Comodo). When a CA signs a certificate, it's vouching that the domain owner was verified.

The **chain of trust** is the path from the server's certificate up through one or more intermediate CAs to a root CA pre-installed in your browser or OS. Browsers trust root CAs; root CAs trust intermediates; intermediates trust websites.

## 2. Why & when

Without CAs, anyone could create a certificate for `bank.com` — the browser would have no way to distinguish the real one from a fake. The CA system solves this: only someone who can prove control of a domain (by responding to a DNS or HTTP challenge) can get a certificate signed for it.

You encounter this whenever:
- You set up HTTPS for a new domain (you need to obtain a certificate).
- A certificate expires and you forget to renew it (users get browser warnings).
- A CA is compromised (the browser vendors can revoke trust in that CA's entire chain).
- You're debugging a `certificate verify failed` error in code.

## 3. Core concept

Think of it like a notarised passport. Your passport (certificate) says your name is John Smith and contains your photo (public key). The government (CA) stamped and signed it — and border agents (browsers) trust governments. If a stranger hands you a piece of paper saying "I'm John Smith, trust me," you ignore it. If it has an official stamp, you accept it.

The chain works like this:

```
Root CA (self-signed, pre-installed in browser)
  └─ Intermediate CA (signed by Root CA)
       └─ Website certificate (signed by Intermediate CA)
```

Browsers don't talk to CAs in real time for every connection (that would be slow). Instead, they validate the **signature chain** cryptographically: the website cert's signature is valid under the intermediate's public key, and the intermediate's signature is valid under the root's public key. If any link breaks (expired, tampered, wrong domain) the browser rejects the connection.

How CAs verify domain ownership (called **DV — Domain Validation**):
- **HTTP challenge**: the CA asks you to put a specific file at `http://yourdomain.com/.well-known/acme-challenge/<token>`. If it's there, you control the domain.
- **DNS challenge**: the CA asks you to add a TXT record to your domain's DNS. If it's there, you control the DNS, hence the domain.

Higher-assurance certs (OV, EV) also verify company identity, but DV is sufficient for encryption.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Certificate chain of trust from root CA to website certificate">
  <defs>
    <marker id="ca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Root CA -->
  <rect x="220" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="42" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Root CA</text>
  <text x="320" y="60" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">pre-installed in browser/OS</text>
  <!-- arrow down -->
  <line x1="320" y1="70" x2="320" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#ca)"/>
  <text x="335" y="93" fill="#6db33f" font-size="10" font-family="sans-serif">signs</text>
  <!-- Intermediate CA -->
  <rect x="195" y="110" width="250" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Intermediate CA</text>
  <text x="320" y="150" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">e.g. Let's Encrypt R11</text>
  <!-- arrow down -->
  <line x1="320" y1="160" x2="320" y2="200" stroke="#79c0ff" stroke-width="2" marker-end="url(#ca)"/>
  <text x="335" y="183" fill="#79c0ff" font-size="10" font-family="sans-serif">signs</text>
  <!-- Website cert -->
  <rect x="170" y="200" width="300" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="224" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Website Certificate</text>
  <text x="320" y="244" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">domain: example.com | valid: 90 days</text>
  <!-- browser check label -->
  <text x="320" y="270" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">browser verifies chain bottom-up cryptographically</text>
</svg>

Browser starts at the website certificate and verifies each signature up to a root it already trusts.

## 5. Runnable example

Inspect a live certificate chain using `openssl` — available on macOS/Linux by default.

```bash
# Connect to example.com and print the full certificate chain
openssl s_client -connect example.com:443 -showcerts 2>/dev/null \
  | openssl x509 -noout -text \
  | grep -E "Subject:|Issuer:|Not Before:|Not After :"
```

Expected output (values will differ by run date):
```
        Subject: C=US, ST=California, L=Los Angeles, O=Internet Corporation for Assigned Names and Numbers, CN=www.example.org
        Issuer: C=US, O=DigiCert Inc, CN=DigiCert Global G2 TLS RSA SHA256 2020 CA1
        Not Before: Jan 13 00:00:00 2025 GMT
        Not After : Feb 12 23:59:59 2026 GMT
```

**How to run:** paste into any macOS or Linux terminal. On Windows, use WSL or Git Bash.

## 6. Walkthrough

- `openssl s_client -connect example.com:443` opens a TLS connection on port 443 and dumps everything the server sends during the handshake, including the full certificate chain (`-showcerts`).
- `2>/dev/null` suppresses the connection status chatter so only certificate data reaches the next pipe.
- `openssl x509 -noout -text` decodes the raw certificate bytes into human-readable form. `-noout` means "don't print the base64 PEM blob itself."
- `grep -E "Subject:|Issuer:|Not Before:|Not After :"` trims to the four lines we care about.
- **Subject** — who this certificate belongs to (domain and org).
- **Issuer** — which CA signed it (the intermediate CA's name). Run the same command on the intermediate to see its Issuer — that will be the Root CA.
- **Not Before / Not After** — the validity window. A certificate used before or after these dates is rejected.

To see all certs in the chain, drop the second pipe and look for multiple `BEGIN CERTIFICATE` blocks in the raw output.

## 7. Gotchas & takeaways

> **Expired certificates are a complete outage, not degraded service.** Browsers refuse the connection entirely; users can't click through (unlike HTTP errors). Automate renewal — tools like Certbot + Let's Encrypt renew every 60 days so the 90-day cert never expires.

> **Self-signed certificates are fine internally, fatal publicly.** A cert you sign yourself has no CA vouching for it. Dev environments: fine. Public site: browsers show a scary warning and most users leave.

- Root CA keys are kept offline in physical vaults — a compromised root CA would break trust for millions of sites simultaneously.
- Let's Encrypt issues free DV certificates and dominates the market; it automated the CA process so there's no excuse for running HTTP-only.
- `openssl s_client` is your best friend for diagnosing certificate errors: wrong CN, wrong chain order, expired, wrong port.
- Certificate pinning (hardcoding the expected cert in an app) prevents MITM but makes rotation painful — avoid in web apps, use carefully in mobile apps.
