---
card: java
gi: 757
slug: key-encapsulation-mechanism-api
title: Key Encapsulation Mechanism API
---

## 1. What it is

**Java 21** (JEP 452) adds `javax.crypto.KEM`, a standard API for **Key Encapsulation Mechanisms** — a cryptographic pattern used to securely establish a shared secret key between two parties using public-key cryptography, without directly encrypting the key material with a traditional public-key encryption scheme. A KEM has two operations: **encapsulate** (given a recipient's public key, produce both a shared secret and a small "encapsulation" ciphertext to send them) and **decapsulate** (given the encapsulation and the matching private key, recover the same shared secret). This API is deliberately algorithm-agnostic: it ships with support for classical mechanisms like RSA-based KEMs today, and — because it's a stable, general interface — it's the vehicle through which the JDK can add post-quantum KEM algorithms (like ML-KEM, standardized by NIST) in future releases without applications needing to change how they call into the API.

## 2. Why & when

Traditional public-key encryption (encrypt a message directly with RSA, say) works, but it's inefficient for large payloads and, more importantly, doesn't map cleanly onto newer cryptographic algorithms designed for post-quantum security — many of the leading post-quantum key-establishment algorithms are natively *key encapsulation mechanisms*, not general-purpose public-key encryption schemes, because their underlying math (lattice-based problems, for the NIST-selected ML-KEM) is naturally suited to "generate and securely transmit a random shared secret" rather than "encrypt an arbitrary message." Before this API, Java had no standard, algorithm-agnostic way to express that operation — any post-quantum KEM support would have needed a bespoke, non-standard API, or would have had to awkwardly bend the encapsulation operation into `Cipher`'s encrypt/decrypt shape, which doesn't naturally fit. Adding `KEM` as its own standard interface now means the *pattern* is available in the JDK ahead of any specific post-quantum algorithm shipping — so application code, TLS implementations, and libraries can be written against a stable API shape today, and gain new algorithms as the JDK adds them later, exactly the same way `Cipher` and `Signature` let new algorithms plug in without changing calling code.

## 3. Core concept

```java
import javax.crypto.KEM;
import java.security.*;

KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
kpg.initialize(2048);
KeyPair recipientKeyPair = kpg.generateKeyPair();

KEM kem = KEM.getInstance("RSA-KEM");

// Sender side: derive a shared secret and an encapsulation to send
KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientKeyPair.getPublic());
KEM.Encapsulated encapsulated = encapsulator.encapsulate();
byte[] sharedSecretSender = encapsulated.key().getEncoded();
byte[] encapsulation = encapsulated.encapsulation();

// Recipient side: recover the same shared secret from the encapsulation
KEM.Decapsulator decapsulator = kem.newDecapsulator(recipientKeyPair.getPrivate());
byte[] sharedSecretRecipient = decapsulator.decapsulate(encapsulation).getEncoded();

// sharedSecretSender and sharedSecretRecipient are now identical
```

The sender never needs the recipient's private key, and the recipient never needs anything from the sender except the small `encapsulation` byte array — yet both end up holding the identical shared secret.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sender encapsulates a shared secret using the recipient's public key, producing a shared secret plus a small encapsulation to transmit; the recipient decapsulates using their private key to recover the same shared secret">
  <rect x="20" y="20" width="260" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Sender: encapsulator.encapsulate()</text>
  <text x="150" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">using recipient's PUBLIC key</text>

  <rect x="360" y="20" width="260" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Recipient: decapsulator.decapsulate(enc)</text>
  <text x="490" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">using recipient's PRIVATE key</text>

  <line x1="280" y1="50" x2="350" y2="50" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow757)"/>
  <defs><marker id="arrow757" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
  <text x="315" y="35" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">encapsulation</text>

  <rect x="180" y="120" width="280" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">identical shared secret on both sides</text>

  <text x="320" y="200" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same algorithm-agnostic API shape works for classical and future post-quantum KEMs</text>
</svg>

*Only the small encapsulation crosses the wire — the shared secret itself never does.*

## 5. Runnable example

Scenario: establishing a shared secret to key a symmetric cipher for a message, growing from a bare KEM exchange into a full hybrid encryption flow.

### Level 1 — Basic

```java
import javax.crypto.KEM;
import java.security.*;

public class KemBasic {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        KeyPair recipientKeyPair = kpg.generateKeyPair();

        KEM kem = KEM.getInstance("RSA-KEM");

        KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientKeyPair.getPublic());
        KEM.Encapsulated encapsulated = encapsulator.encapsulate();

        KEM.Decapsulator decapsulator = kem.newDecapsulator(recipientKeyPair.getPrivate());
        SecretKey recovered = decapsulator.decapsulate(encapsulated.encapsulation());

        boolean match = java.util.Arrays.equals(
            encapsulated.key().getEncoded(), recovered.getEncoded());
        System.out.println("shared secrets match: " + match);
    }
}
```

**How to run:** `java KemBasic.java` (JDK 21+).

This runs the minimal encapsulate/decapsulate round trip in a single program and confirms both sides derive the identical shared secret — establishing the core mechanism works before using the secret for anything.

### Level 2 — Intermediate

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.*;

public class KemHybridEncrypt {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        KeyPair recipientKeyPair = kpg.generateKeyPair();

        KEM kem = KEM.getInstance("RSA-KEM");

        // Sender: derive a shared secret, use it to key AES, encrypt the real message
        KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientKeyPair.getPublic());
        KEM.Encapsulated encapsulated = encapsulator.encapsulate();
        SecretKeySpec aesKey = new SecretKeySpec(encapsulated.key().getEncoded(), 0, 16, "AES");

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, aesKey);
        byte[] ciphertext = cipher.doFinal("meet at dawn".getBytes());
        byte[] iv = cipher.getIV();

        // Recipient: recover the same shared secret, derive the same AES key, decrypt
        KEM.Decapsulator decapsulator = kem.newDecapsulator(recipientKeyPair.getPrivate());
        SecretKey recoveredSecret = decapsulator.decapsulate(encapsulated.encapsulation());
        SecretKeySpec recoveredAesKey = new SecretKeySpec(recoveredSecret.getEncoded(), 0, 16, "AES");

        Cipher decipher = Cipher.getInstance("AES/GCM/NoPadding");
        decipher.init(Cipher.DECRYPT_MODE, recoveredAesKey, new GCMParameterSpec(128, iv));
        byte[] plaintext = decipher.doFinal(ciphertext);

        System.out.println("decrypted message: " + new String(plaintext));
    }
}
```

**How to run:** `java KemHybridEncrypt.java`.

The real-world concern added: the shared secret from the KEM is now actually **used** — truncated to an AES-128 key and used to encrypt a real message with AES-GCM (an authenticated cipher) — the classic "hybrid encryption" pattern: use slow public-key crypto only to establish a key, then use fast symmetric crypto for the actual data, which is exactly the use case KEMs are designed for.

### Level 3 — Advanced

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.*;
import java.util.*;

public class KemAdvanced {
    record SecureEnvelope(byte[] encapsulation, byte[] iv, byte[] ciphertext) {}

    static SecureEnvelope encryptFor(PublicKey recipientPublicKey, String message) throws Exception {
        KEM kem = KEM.getInstance("RSA-KEM");
        KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientPublicKey);
        KEM.Encapsulated encapsulated = encapsulator.encapsulate();

        SecretKeySpec aesKey = new SecretKeySpec(encapsulated.key().getEncoded(), 0, 16, "AES");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, aesKey);
        byte[] ciphertext = cipher.doFinal(message.getBytes());

        return new SecureEnvelope(encapsulated.encapsulation(), cipher.getIV(), ciphertext);
    }

    static String decryptWith(PrivateKey recipientPrivateKey, SecureEnvelope envelope) throws Exception {
        KEM kem = KEM.getInstance("RSA-KEM");
        KEM.Decapsulator decapsulator = kem.newDecapsulator(recipientPrivateKey);
        SecretKey recoveredSecret = decapsulator.decapsulate(envelope.encapsulation());

        SecretKeySpec aesKey = new SecretKeySpec(recoveredSecret.getEncoded(), 0, 16, "AES");
        Cipher decipher = Cipher.getInstance("AES/GCM/NoPadding");
        decipher.init(Cipher.DECRYPT_MODE, aesKey, new GCMParameterSpec(128, envelope.iv()));
        return new String(decipher.doFinal(envelope.ciphertext()));
    }

    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        KeyPair recipient = kpg.generateKeyPair();
        KeyPair wrongRecipient = kpg.generateKeyPair(); // a different, unrelated key pair

        SecureEnvelope envelope = encryptFor(recipient.getPublic(), "meet at dawn");
        System.out.println("decrypted with correct key: " + decryptWith(recipient.getPrivate(), envelope));

        try {
            decryptWith(wrongRecipient.getPrivate(), envelope);
        } catch (Exception e) {
            System.out.println("decrypting with wrong key fails as expected: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java KemAdvanced.java`.

This adds the production-flavored hard case: packaging the encapsulation, IV, and ciphertext into a single `SecureEnvelope` record suitable for transmission or storage, plus an explicit negative test — attempting to decrypt with an **unrelated** private key — verifying the scheme fails loudly (an `AEADBadTagException` from AES-GCM's authentication check, since the derived AES key is wrong) rather than silently producing garbage plaintext.

## 6. Walkthrough

Tracing `KemAdvanced.main`:

1. `main` generates two independent RSA key pairs: `recipient` (the intended recipient) and `wrongRecipient` (standing in for an attacker or a misconfigured key, unrelated to `recipient`).
2. `encryptFor(recipient.getPublic(), "meet at dawn")` runs the sender side: a fresh `KEM` instance encapsulates against `recipient`'s **public** key, producing a shared secret and an `encapsulation` byte array; the shared secret is truncated to 16 bytes and used as an AES-128-GCM key to encrypt the message, producing `ciphertext` and an `iv`. All three pieces are bundled into a `SecureEnvelope`.
3. `decryptWith(recipient.getPrivate(), envelope)` runs the correct recipient side: decapsulating `envelope.encapsulation()` with `recipient`'s matching **private** key recovers the identical shared secret the sender derived, which produces the identical AES key, which correctly decrypts `envelope.ciphertext()` using the stored `iv` — printing the original message.
4. `decryptWith(wrongRecipient.getPrivate(), envelope)` attempts the same decapsulation, but with `wrongRecipient`'s private key — which has no mathematical relationship to `recipient`'s public key that was used to create the encapsulation. Decapsulation either produces a different (wrong) shared secret or fails outright, depending on the algorithm; either way, the derived AES key doesn't match the one used to encrypt, so AES-GCM's built-in authentication tag check fails and `doFinal` throws — caught here as a generic `Exception` and reported.

Expected output:
```
decrypted with correct key: meet at dawn
decrypting with wrong key fails as expected: AEADBadTagException
```

## 7. Gotchas & takeaways

> **Gotcha:** a KEM's shared secret is derived key material, not a general-purpose password or arbitrary-length key — always run it through a proper key-derivation step (as simple as truncating to the needed length for a demo, but ideally via HKDF or similar for production use) rather than using the raw encapsulated bytes directly as if they were a pre-vetted symmetric key of exactly the right size and structure for your target cipher.

- `KEM` is algorithm-agnostic: `KEM.getInstance("RSA-KEM")` today, with future JDK releases expected to add post-quantum algorithms (like ML-KEM) under the same API shape.
- The core hybrid-encryption pattern: use a KEM (asymmetric, slower) only to establish a symmetric key, then use that key with a fast symmetric cipher (AES-GCM) for the actual data — never encrypt bulk data directly with asymmetric crypto.
- Only the `encapsulation` byte array needs to cross the wire or be stored — the shared secret itself is derived independently by each side and never transmitted.
- AES-GCM's authentication tag causes decryption to fail loudly when the wrong key is used, rather than silently producing corrupted plaintext — always prefer authenticated cipher modes over unauthenticated ones for exactly this reason.
- Watch for future JDK releases adding standardized post-quantum KEM algorithm names to `KEM.getInstance(...)` — code written against this API today should need little to no change to adopt them later.
