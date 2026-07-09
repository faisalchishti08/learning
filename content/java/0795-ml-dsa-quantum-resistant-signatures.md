---
card: java
gi: 795
slug: ml-dsa-quantum-resistant-signatures
title: ML-DSA (quantum-resistant signatures)
---

## 1. What it is

**Java 24** (JEP 497) adds standard support for **ML-DSA** (Module-Lattice-based Digital Signature Algorithm), NIST's standardized post-quantum digital signature algorithm, through the JDK's existing `java.security.Signature` and `KeyPairGenerator` APIs. `KeyPairGenerator.getInstance("ML-DSA")` (with three approved parameter sets, `ML-DSA-44`, `ML-DSA-65`, `ML-DSA-87`, chosen via `AlgorithmParameterSpec`) and `Signature.getInstance("ML-DSA")` work exactly like signing with `"RSA"` or `"Ed25519"` already did — `sign()`, `verify()`, the same call shape — with a quantum-resistant algorithm underneath, shipping in the same release as [ML-KEM](0794-ml-kem-quantum-resistant-key-encapsulation.md), its key-establishment counterpart.

## 2. Why & when

Digital signatures and key encapsulation solve different problems — "prove this message came from me and wasn't altered" versus "securely agree on a shared secret" — but both rely on the same category of classical hard-math assumptions (factoring, discrete logarithms) that a large enough quantum computer would undermine. Where [ML-KEM](0794-ml-kem-quantum-resistant-key-encapsulation.md) addresses the key-establishment side, ML-DSA addresses the signature side, and NIST standardized both from the same broader post-quantum cryptography competition, based on related lattice-hardness assumptions. Signatures have a somewhat different urgency profile than encapsulated secrets — a signature verified today doesn't need to remain *secret* against a future quantum computer, so "harvest now, forge later" isn't quite the same threat as "harvest now, decrypt later." But long-lived signed artifacts (code-signing certificates, firmware signatures, legal documents with decades-long validity requirements) still need signatures that remain unforgeable for as long as the artifact matters — which, for some of these, extends well into a future where large-scale quantum computers might exist. Shipping ML-DSA through the JDK's existing `Signature` API means that migration, again, is a matter of an algorithm name, not a new API to learn.

## 3. Core concept

```java
import java.security.*;

// Same java.security.Signature/KeyPairGenerator API — new algorithm name.
KeyPairGenerator kpg = KeyPairGenerator.getInstance("ML-DSA");
KeyPair signerKeyPair = kpg.generateKeyPair();

Signature signer = Signature.getInstance("ML-DSA");
signer.initSign(signerKeyPair.getPrivate());
signer.update("contract v3 final".getBytes());
byte[] signature = signer.sign();

Signature verifier = Signature.getInstance("ML-DSA");
verifier.initVerify(signerKeyPair.getPublic());
verifier.update("contract v3 final".getBytes());
boolean valid = verifier.verify(signature); // true — quantum-resistant this time
```

Identical shape to signing with RSA or an elliptic-curve algorithm — only `"ML-DSA"` is new.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ML-DSA plugs into the same java.security.Signature API used for RSA and elliptic curve signatures, providing quantum-resistant signing and verification with an unchanged call shape" >
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">java.security.Signature — sign() / verify(), unchanged since forever</text>

  <rect x="40" y="90" width="260" height="55" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="170" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Signature.getInstance("RSA")</text>
  <text x="170" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">classical</text>

  <rect x="340" y="90" width="260" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="112" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Signature.getInstance("ML-DSA")</text>
  <text x="470" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">post-quantum, Java 24+</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Signing and verifying long-lived documents against a future quantum threat</text>
</svg>

*ML-KEM secures key establishment; ML-DSA secures signatures — the same post-quantum migration story, applied to the other half of asymmetric cryptography.*

## 5. Runnable example

Scenario: signing a document, growing from a basic sign/verify round trip into a tamper-detection check, then into a realistic long-lived-document signing and archival flow.

### Level 1 — Basic

```java
import java.security.*;

public class MlDsaBasic {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("ML-DSA");
        KeyPair signerKeyPair = kpg.generateKeyPair();

        Signature signer = Signature.getInstance("ML-DSA");
        signer.initSign(signerKeyPair.getPrivate());
        signer.update("contract v3 final".getBytes());
        byte[] signature = signer.sign();

        Signature verifier = Signature.getInstance("ML-DSA");
        verifier.initVerify(signerKeyPair.getPublic());
        verifier.update("contract v3 final".getBytes());
        boolean valid = verifier.verify(signature);

        System.out.println("signature valid: " + valid);
    }
}
```

**How to run:** `java MlDsaBasic.java` (JDK 24+).

The minimal sign/verify round trip using `"ML-DSA"` — the exact same three-step shape (`initSign`/`update`/`sign`, then `initVerify`/`update`/`verify`) developers already know from RSA or EC signatures.

### Level 2 — Intermediate

```java
import java.security.*;

public class MlDsaTamperCheck {
    static byte[] sign(PrivateKey key, String message) throws Exception {
        Signature signer = Signature.getInstance("ML-DSA");
        signer.initSign(key);
        signer.update(message.getBytes());
        return signer.sign();
    }

    static boolean verify(PublicKey key, String message, byte[] signature) throws Exception {
        Signature verifier = Signature.getInstance("ML-DSA");
        verifier.initVerify(key);
        verifier.update(message.getBytes());
        return verifier.verify(signature);
    }

    public static void main(String[] args) throws Exception {
        KeyPair keyPair = KeyPairGenerator.getInstance("ML-DSA").generateKeyPair();

        String original = "transfer $100 to account 42";
        byte[] signature = sign(keyPair.getPrivate(), original);

        System.out.println("original message valid: " + verify(keyPair.getPublic(), original, signature));

        String tampered = "transfer $100000 to account 42"; // attacker modifies the amount
        System.out.println("tampered message valid: " + verify(keyPair.getPublic(), tampered, signature));
    }
}
```

**How to run:** `java MlDsaTamperCheck.java`.

The real-world concern added: verifying the **same signature** against both the original and a maliciously altered message — demonstrating that even a small change to the signed content causes verification to correctly fail, the core guarantee any digital signature scheme provides, confirmed here for ML-DSA specifically.

### Level 3 — Advanced

```java
import java.security.*;
import java.util.*;

public class MlDsaArchivalSigning {
    record SignedDocument(String content, byte[] publicKeyBytes, byte[] signature, long signedAtEpochMillis) {}

    static SignedDocument signDocument(KeyPair signerKeyPair, String content) throws Exception {
        Signature signer = Signature.getInstance("ML-DSA");
        signer.initSign(signerKeyPair.getPrivate());
        signer.update(content.getBytes());
        byte[] signature = signer.sign();

        return new SignedDocument(content, signerKeyPair.getPublic().getEncoded(),
            signature, System.currentTimeMillis());
    }

    static boolean verifyDocument(SignedDocument doc) throws Exception {
        KeyFactory kf = KeyFactory.getInstance("ML-DSA");
        PublicKey publicKey = kf.generatePublic(new java.security.spec.X509EncodedKeySpec(doc.publicKeyBytes()));

        Signature verifier = Signature.getInstance("ML-DSA");
        verifier.initVerify(publicKey);
        verifier.update(doc.content().getBytes());
        return verifier.verify(doc.signature());
    }

    public static void main(String[] args) throws Exception {
        KeyPair signerKeyPair = KeyPairGenerator.getInstance("ML-DSA").generateKeyPair();

        SignedDocument doc = signDocument(signerKeyPair,
            "This deed grants perpetual archival rights, effective immediately.");

        System.out.println("document signed at: " + new Date(doc.signedAtEpochMillis()));
        System.out.println("re-verified from encoded public key: " + verifyDocument(doc));

        // Simulate reconstructing the document (e.g., after loading from long-term storage)
        SignedDocument reloaded = new SignedDocument(
            doc.content(), doc.publicKeyBytes(), doc.signature(), doc.signedAtEpochMillis());
        System.out.println("re-verified after simulated storage round trip: " + verifyDocument(reloaded));
    }
}
```

**How to run:** `java MlDsaArchivalSigning.java`.

This adds the production-flavored hard case: packaging a signed document with its **encoded public key** (via `PublicKey.getEncoded()`) into a storable `SignedDocument` record, then reconstructing the `PublicKey` from those raw encoded bytes via `KeyFactory` before verifying — the realistic shape of a long-term archival system, where the verifying party doesn't hold the original `PublicKey` object in memory, only whatever bytes were stored or transmitted alongside the signed content.

## 6. Walkthrough

Tracing `MlDsaArchivalSigning.main`:

1. `main` generates an ML-DSA key pair and calls `signDocument`, which signs the document's content bytes with the private key, producing a `signature` byte array, and bundles the content, the **encoded** public key bytes, the signature, and a timestamp into a `SignedDocument` record.
2. `verifyDocument(doc)` reconstructs a usable `PublicKey` object from `doc.publicKeyBytes()` via `KeyFactory.getInstance("ML-DSA").generatePublic(new X509EncodedKeySpec(...))` — this is the step a real archival or verification system would need, since only raw bytes (not a live `PublicKey` object) typically survive being written to storage or sent over a network.
3. With the reconstructed public key, `verifyDocument` re-hashes the document's content and checks it against the stored signature, returning `true` since nothing about the content or signature has changed.
4. `main` prints the signing timestamp and the first verification result.
5. It then builds `reloaded`, a fresh `SignedDocument` record constructed from the same underlying byte arrays — standing in for "the document as it would look after being read back from long-term storage" — and verifies it independently, confirming the signature remains valid purely from the stored bytes, with no dependency on the original in-memory `KeyPair` object at all.

Expected output shape (the timestamp reflects the actual run time):
```
document signed at: Wed Jul 01 12:00:00 UTC 2026
re-verified from encoded public key: true
re-verified after simulated storage round trip: true
```

## 7. Gotchas & takeaways

> **Gotcha:** `KeyFactory.generatePublic(...)` reconstructs a `PublicKey` from encoded bytes, but it must be given a `KeyFactory` for the **matching algorithm** (`"ML-DSA"` here) — attempting to reconstruct ML-DSA-encoded key bytes with, say, an `"RSA"` `KeyFactory` throws an `InvalidKeySpecException` rather than silently producing a usable-but-wrong key. Always store or transmit the algorithm identifier alongside encoded key material, not just the raw bytes.

- Java 24 (JEP 497) adds standard `ML-DSA` support (parameter sets `ML-DSA-44`/`ML-DSA-65`/`ML-DSA-87`) through the JDK's existing `Signature`/`KeyPairGenerator`/`KeyFactory` APIs — no new API surface to learn.
- ML-DSA is NIST's standardized post-quantum digital signature algorithm, shipping alongside [ML-KEM](0794-ml-kem-quantum-resistant-key-encapsulation.md) from the same post-quantum cryptography standardization effort.
- Migrating existing `Signature`-based signing code to ML-DSA is a matter of changing the algorithm name string, identical to migrating between RSA and elliptic-curve signature algorithms today.
- Long-lived signed artifacts (code signing, firmware, legal documents with decades-long validity) are the primary motivation for adopting post-quantum signatures now, even though the "harvest now, forge later" urgency is lower than for encapsulated secrets.
- When storing or transmitting a `PublicKey`, always keep its algorithm identifier alongside the encoded bytes, so a `KeyFactory` for the correct algorithm can reconstruct it later.
