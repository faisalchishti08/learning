---
card: java
gi: 682
slug: eddsa-signatures
title: EdDSA signatures
---

## 1. What it is

**Java 15** added built-in support for the **Edwards-Curve Digital Signature Algorithm (EdDSA)**, specifically the **Ed25519** and **Ed448** curve variants, as a standard part of the JDK's cryptography APIs (JEP 339). EdDSA is a modern digital-signature scheme built on twisted Edwards curves, standardized in RFC 8032, chosen by the JDK because of its strong security properties, resistance to several classes of implementation mistakes that have historically plagued other signature schemes (like reused nonces breaking ECDSA), and consistently fast performance. Before Java 15, using EdDSA in a Java application meant pulling in a third-party cryptography library (like Bouncy Castle); afterward, it's accessible through the same standard `java.security.Signature` and `KeyPairGenerator` APIs already used for RSA or ECDSA.

## 2. Why & when

Digital signatures let you prove a message came from the holder of a specific private key and wasn't altered in transit — used for signed JWTs, code signing, TLS certificate chains, and API request authentication. EdDSA was added to the JDK because it addresses real weaknesses of older schemes: traditional ECDSA signatures require a fresh, truly random nonce for every signature, and a single reused or predictable nonce catastrophically leaks the private key — a mistake that has caused real-world key compromises. EdDSA's signature generation is **deterministic** (no external randomness needed at signing time), eliminating that entire failure mode, while also generally being faster to verify. Reach for `Ed25519` (128-bit security level, the common default) or `Ed448` (224-bit security level, for higher-assurance needs) whenever you're implementing new signature-based authentication or integrity checks in Java 15+ and don't have a specific reason to require RSA or classic ECDSA (e.g. interoperability with an external system that only supports those).

## 3. Core concept

```java
import java.security.*;

// Generate an Ed25519 key pair
KeyPairGenerator kpg = KeyPairGenerator.getInstance("Ed25519");
KeyPair keyPair = kpg.generateKeyPair();

// Sign a message
Signature signer = Signature.getInstance("Ed25519");
signer.initSign(keyPair.getPrivate());
signer.update("hello world".getBytes());
byte[] signature = signer.sign();

// Verify it
Signature verifier = Signature.getInstance("Ed25519");
verifier.initVerify(keyPair.getPublic());
verifier.update("hello world".getBytes());
boolean valid = verifier.verify(signature); // true
```

The algorithm name `"Ed25519"` (or `"Ed448"`) is passed to the exact same standard `KeyPairGenerator` and `Signature` classes already used for every other Java signature algorithm — no new API surface to learn.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Signer uses a private key to produce a signature over a message; verifier uses the corresponding public key to check the signature against the message">
  <rect x="20" y="30" width="180" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Signer</text>
  <text x="110" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">private key + message</text>
  <text x="110" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Signature.sign()</text>
  <text x="110" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">deterministic — no</text>
  <text x="110" y="145" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">random nonce needed</text>

  <line x1="200" y1="100" x2="330" y2="100" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="265" y="90" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">signature bytes</text>

  <rect x="340" y="30" width="200" height="160" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="52" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Verifier</text>
  <text x="440" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">public key + message + signature</text>
  <text x="440" y="105" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Signature.verify()</text>
  <text x="440" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">true only if signature</text>
  <text x="440" y="150" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">matches this exact message</text>

  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Only the private key's holder can produce a valid signature; anyone with the public key can verify it, and any tampering with the message invalidates the check.

## 5. Runnable example

Scenario: signing and verifying a message — starting with the simplest sign/verify round trip, then showing tamper detection when the message or signature is altered, then a small "signed message envelope" that bundles message + signature + public key together for later independent verification.

### Level 1 — Basic

```java
// File: EdDsaBasic.java
import java.security.*;

public class EdDsaBasic {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("Ed25519");
        KeyPair keyPair = kpg.generateKeyPair();

        byte[] message = "hello world".getBytes();

        Signature signer = Signature.getInstance("Ed25519");
        signer.initSign(keyPair.getPrivate());
        signer.update(message);
        byte[] signature = signer.sign();

        Signature verifier = Signature.getInstance("Ed25519");
        verifier.initVerify(keyPair.getPublic());
        verifier.update(message);
        boolean valid = verifier.verify(signature);

        System.out.println("Signature length: " + signature.length + " bytes");
        System.out.println("Valid? " + valid);
    }
}
```

**How to run:** `java EdDsaBasic.java`

Expected output:
```
Signature length: 64 bytes
Valid? true
```

### Level 2 — Intermediate

```java
// File: EdDsaTamperCheck.java
import java.security.*;
import java.util.Arrays;

public class EdDsaTamperCheck {
    static boolean verify(PublicKey pub, byte[] message, byte[] signature) throws Exception {
        Signature verifier = Signature.getInstance("Ed25519");
        verifier.initVerify(pub);
        verifier.update(message);
        return verifier.verify(signature);
    }

    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("Ed25519");
        KeyPair keyPair = kpg.generateKeyPair();

        byte[] original = "transfer $100 to Alice".getBytes();

        Signature signer = Signature.getInstance("Ed25519");
        signer.initSign(keyPair.getPrivate());
        signer.update(original);
        byte[] signature = signer.sign();

        System.out.println("Original message valid: " + verify(keyPair.getPublic(), original, signature));

        byte[] tampered = "transfer $900 to Alice".getBytes();
        System.out.println("Tampered message valid: " + verify(keyPair.getPublic(), tampered, signature));

        byte[] tamperedSig = Arrays.copyOf(signature, signature.length);
        tamperedSig[0] ^= 0x01; // flip one bit of the signature itself
        System.out.println("Tampered signature valid: " + verify(keyPair.getPublic(), original, tamperedSig));
    }
}
```

**How to run:** `java EdDsaTamperCheck.java`

Expected output:
```
Original message valid: true
Tampered message valid: false
Tampered signature valid: false
```

This shows the signature is tightly bound to the exact message bytes: changing even the dollar amount in the message, or flipping a single bit of the signature itself, causes verification to fail — the entire point of a signature scheme.

### Level 3 — Advanced

```java
// File: SignedEnvelope.java
import java.security.*;
import java.util.Base64;

public class SignedEnvelope {
    record Envelope(String message, String signatureBase64, String publicKeyBase64) {}

    static Envelope createEnvelope(String message, KeyPair keyPair) throws Exception {
        Signature signer = Signature.getInstance("Ed25519");
        signer.initSign(keyPair.getPrivate());
        signer.update(message.getBytes());
        byte[] sig = signer.sign();

        return new Envelope(
                message,
                Base64.getEncoder().encodeToString(sig),
                Base64.getEncoder().encodeToString(keyPair.getPublic().getEncoded())
        );
    }

    static boolean verifyEnvelope(Envelope env) throws Exception {
        byte[] pubBytes = Base64.getDecoder().decode(env.publicKeyBase64());
        PublicKey pub = KeyFactory.getInstance("Ed25519")
                .generatePublic(new java.security.spec.X509EncodedKeySpec(pubBytes));

        byte[] sig = Base64.getDecoder().decode(env.signatureBase64());

        Signature verifier = Signature.getInstance("Ed25519");
        verifier.initVerify(pub);
        verifier.update(env.message().getBytes());
        return verifier.verify(sig);
    }

    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("Ed25519");
        KeyPair keyPair = kpg.generateKeyPair();

        Envelope envelope = createEnvelope("order #4821 confirmed", keyPair);
        System.out.println("Envelope message: " + envelope.message());
        System.out.println("Signature (base64): " + envelope.signatureBase64().substring(0, 20) + "...");

        boolean valid = verifyEnvelope(envelope);
        System.out.println("Envelope verifies independently: " + valid);

        Envelope forged = new Envelope("order #9999 confirmed", envelope.signatureBase64(), envelope.publicKeyBase64());
        System.out.println("Forged envelope verifies: " + verifyEnvelope(forged));
    }
}
```

**How to run:** `java SignedEnvelope.java`

Expected output (the base64 signature prefix will vary per run since key generation is random):
```
Envelope message: order #4821 confirmed
Signature (base64): 3q2+7wABAgMEBQYHCA...
Envelope verifies independently: true
Forged envelope verifies: false
```

Level 3 packages the message, its Base64-encoded signature, and the Base64-encoded **public key** into one self-contained `Envelope` record — the shape a real system would serialize to JSON and hand to a completely separate verifying process, which reconstructs the `PublicKey` object via `KeyFactory` and `X509EncodedKeySpec` before verifying, without ever needing access to the private key.

## 6. Walkthrough

1. `KeyPairGenerator.getInstance("Ed25519")` asks the JDK's registered security providers for an implementation of key-pair generation for the Ed25519 curve; `.generateKeyPair()` produces a fresh, random `KeyPair` holding a `PrivateKey` and its corresponding `PublicKey`.
2. `createEnvelope` first converts the plaintext `message` string to bytes, then obtains a `Signature.getInstance("Ed25519")` instance and calls `initSign(keyPair.getPrivate())` — this configures the `Signature` object to sign using this specific private key.
3. `signer.update(message.getBytes())` feeds the message bytes into the signature algorithm's internal state (this two-step update-then-sign API lets you feed a message incrementally, e.g. from a stream, before finalizing).
4. `signer.sign()` produces the raw signature bytes — for Ed25519 this is always exactly **64 bytes**, regardless of the message length, since EdDSA's signature size is fixed by the curve, not by the input.
5. Both the signature and the public key (via `keyPair.getPublic().getEncoded()`, which serializes it in the standard X.509 `SubjectPublicKeyInfo` format) are Base64-encoded and bundled into the `Envelope` record alongside the original plaintext message — this `Envelope` is the complete, portable unit a receiver needs.
6. `verifyEnvelope` reverses the encoding: `Base64.getDecoder().decode(...)` recovers the raw public-key bytes, and `KeyFactory.getInstance("Ed25519").generatePublic(new X509EncodedKeySpec(pubBytes))` reconstructs a usable `PublicKey` object from those bytes — this is exactly what an independent verifying process, which never had access to the original `KeyPair` object, would need to do after receiving the envelope over the network or from storage.
7. A fresh `Signature.getInstance("Ed25519")` is initialized for verification via `initVerify(pub)`, fed the same message bytes via `update(...)`, and `verifier.verify(sig)` performs the actual cryptographic check: it recomputes what the signature *should* be for this exact message under this exact public key, and compares.
8. For the legitimate `envelope`, verification returns `true` — the message, signature, and public key are all mutually consistent.
9. For the `forged` envelope — same signature and public key, but a **different message** substituted in — `verifyEnvelope` returns `false`, because the signature was computed over `"order #4821 confirmed"`, not `"order #9999 confirmed"`; EdDSA's signature is a cryptographic function of the exact message bytes, so any substitution is detected.

```
createEnvelope(message, keyPair)
      │
      ▼
sign(message, privateKey) ──► 64-byte signature
      │
      ▼
Envelope{message, signature, publicKey} ──(serialize/transmit)──► verifyEnvelope(envelope)
                                                                        │
                                                          reconstruct PublicKey from bytes
                                                                        │
                                                          verify(message, signature, publicKey)
                                                                        │
                                                              true (unchanged) / false (tampered)
```

## 7. Gotchas & takeaways

> EdDSA signing is **deterministic** — signing the same message with the same private key twice produces the *same* signature both times (unlike ECDSA, which requires fresh randomness per signature and produces a different signature each time). This is a security feature, not a bug: it eliminates the nonce-reuse vulnerability class entirely, but don't mistake identical repeated signatures for a sign of weakness — it's expected behavior.

- `"Ed25519"` and `"Ed448"` are the two standard algorithm names; Ed25519 (128-bit security) is the common default, Ed448 (224-bit security) trades some performance for a higher security margin.
- An Ed25519 signature is always exactly 64 bytes and an Ed25519 public key is always exactly 32 bytes (raw), making them noticeably more compact than equivalent-strength RSA keys/signatures.
- Use `getEncoded()` / `X509EncodedKeySpec` (public keys) and `PKCS8EncodedKeySpec` (private keys) to serialize and reconstruct keys across process or network boundaries — never hand-roll a custom encoding.
- Before Java 15, EdDSA required a third-party library like Bouncy Castle; existing code that added such a dependency purely for EdDSA support can migrate to the standard `java.security` APIs on Java 15+.
- As with any signature scheme, EdDSA proves the message came from the private key's holder and wasn't altered — it says nothing about confidentiality; combine with encryption if the message content itself must also be kept secret.
