---
card: java
gi: 794
slug: ml-kem-quantum-resistant-key-encapsulation
title: ML-KEM (quantum-resistant key encapsulation)
---

## 1. What it is

**Java 24** (JEP 496) adds standard support for **ML-KEM** (Module-Lattice-based Key Encapsulation Mechanism), the NIST-standardized post-quantum key encapsulation algorithm, to the JDK's cryptography providers — usable through the exact same [`javax.crypto.KEM` API](0757-key-encapsulation-mechanism-api.md) introduced in Java 21. `KeyPairGenerator.getInstance("ML-KEM-768")` (or `ML-KEM-512`/`ML-KEM-1024`, its three approved parameter sets trading security margin for key/ciphertext size) and `KEM.getInstance("ML-KEM-768")` now work exactly like the RSA-based KEM from Java 21's example — same `encapsulate`/`decapsulate` shape, different algorithm underneath, one resistant to attacks from a sufficiently powerful quantum computer.

## 2. Why & when

Java 21's KEM API was deliberately designed algorithm-agnostic specifically so the JDK could add post-quantum algorithms later without applications needing to change how they call into it — and ML-KEM is exactly that promise being fulfilled. Classical public-key cryptography (RSA, elliptic-curve algorithms) relies on mathematical problems (integer factorization, discrete logarithms) that a large enough quantum computer, running Shor's algorithm, could solve efficiently — a threat that doesn't exist yet at scale, but one serious enough that NIST ran a multi-year, multi-round public competition to select replacement algorithms based on different, quantum-resistant mathematical problems (lattice problems, in ML-KEM's case). Because key-establishment secrets can be **harvested now and decrypted later** once quantum computers become powerful enough ("harvest now, decrypt later" attacks), migrating key-exchange mechanisms to post-quantum algorithms is considered urgent even before quantum computers capable of breaking RSA actually exist — any long-lived secret encapsulated with a classical KEM today is potentially exposed retroactively. Standardizing ML-KEM in the JDK, under the same API application code already knows, is what makes that migration a configuration change (which algorithm name to pass) rather than a rewrite.

## 3. Core concept

```java
import javax.crypto.KEM;
import java.security.*;

// Same javax.crypto.KEM API from Java 21 — different, post-quantum algorithm name.
KeyPairGenerator kpg = KeyPairGenerator.getInstance("ML-KEM-768");
KeyPair recipientKeyPair = kpg.generateKeyPair();

KEM kem = KEM.getInstance("ML-KEM-768");
KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientKeyPair.getPublic());
KEM.Encapsulated encapsulated = encapsulator.encapsulate();

KEM.Decapsulator decapsulator = kem.newDecapsulator(recipientKeyPair.getPrivate());
byte[] recovered = decapsulator.decapsulate(encapsulated.encapsulation()).getEncoded();
// recovered matches encapsulated.key().getEncoded() — quantum-resistant this time
```

Compare this to [Java 21's `"RSA-KEM"` example](0757-key-encapsulation-mechanism-api.md) — only the algorithm name changed; every method call is identical.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ML-KEM plugs into the same javax.crypto.KEM API that already supported RSA-KEM, letting application code migrate to a post-quantum algorithm by changing only the algorithm name string" >
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">javax.crypto.KEM — the same API, since Java 21</text>

  <rect x="40" y="90" width="260" height="55" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="170" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">KEM.getInstance("RSA-KEM")</text>
  <text x="170" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">classical, Java 21+</text>

  <rect x="340" y="90" width="260" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="112" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">KEM.getInstance("ML-KEM-768")</text>
  <text x="470" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">post-quantum, Java 24+</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Migrating to post-quantum key exchange is a string change, not a rewrite</text>
</svg>

*The algorithm-agnostic API design from Java 21 pays off exactly as intended: new math, same code shape.*

## 5. Runnable example

Scenario: the same hybrid-encryption message-sending flow from the KEM API's introduction, migrated step by step from classical `RSA-KEM` to post-quantum `ML-KEM`, then extended to compare both algorithms side by side.

### Level 1 — Basic

```java
import javax.crypto.*;
import java.security.*;

public class MlKemBasic {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("ML-KEM-768");
        KeyPair recipientKeyPair = kpg.generateKeyPair();

        KEM kem = KEM.getInstance("ML-KEM-768");

        KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientKeyPair.getPublic());
        KEM.Encapsulated encapsulated = encapsulator.encapsulate();

        KEM.Decapsulator decapsulator = kem.newDecapsulator(recipientKeyPair.getPrivate());
        SecretKey recovered = decapsulator.decapsulate(encapsulated.encapsulation());

        boolean match = java.util.Arrays.equals(
            encapsulated.key().getEncoded(), recovered.getEncoded());
        System.out.println("ML-KEM shared secrets match: " + match);
    }
}
```

**How to run:** `java MlKemBasic.java` (JDK 24+).

The minimal encapsulate/decapsulate round trip using `"ML-KEM-768"` — structurally identical to [the `"RSA-KEM"` basic example](0757-key-encapsulation-mechanism-api.md), confirming the API-agnostic design works exactly as promised.

### Level 2 — Intermediate

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.*;

public class MlKemHybridEncrypt {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("ML-KEM-768");
        KeyPair recipientKeyPair = kpg.generateKeyPair();

        KEM kem = KEM.getInstance("ML-KEM-768");

        KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientKeyPair.getPublic());
        KEM.Encapsulated encapsulated = encapsulator.encapsulate();
        SecretKeySpec aesKey = new SecretKeySpec(encapsulated.key().getEncoded(), 0, 16, "AES");

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, aesKey);
        byte[] ciphertext = cipher.doFinal("meet at dawn, quantum-safe channel".getBytes());
        byte[] iv = cipher.getIV();

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

**How to run:** `java MlKemHybridEncrypt.java`.

The real-world concern added: the same hybrid-encryption pattern from [the KEM API's introduction](0757-key-encapsulation-mechanism-api.md) — use the KEM only to establish an AES key, then use AES-GCM for the actual message — now running on a quantum-resistant algorithm; the application-level flow needed **zero** structural changes to migrate.

### Level 3 — Advanced

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.*;

public class MlKemVsRsaComparison {
    record Result(String algorithm, int publicKeyBytes, int encapsulationBytes, long micros) {}

    static Result measure(String algorithm) throws Exception {
        long start = System.nanoTime();

        KeyPair recipientKeyPair;
        if (algorithm.startsWith("RSA")) {
            KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
            kpg.initialize(2048);
            recipientKeyPair = kpg.generateKeyPair();
        } else {
            recipientKeyPair = KeyPairGenerator.getInstance(algorithm).generateKeyPair();
        }

        KEM kem = KEM.getInstance(algorithm.equals("RSA") ? "RSA-KEM" : algorithm);
        KEM.Encapsulator encapsulator = kem.newEncapsulator(recipientKeyPair.getPublic());
        KEM.Encapsulated encapsulated = encapsulator.encapsulate();

        KEM.Decapsulator decapsulator = kem.newDecapsulator(recipientKeyPair.getPrivate());
        decapsulator.decapsulate(encapsulated.encapsulation()); // verify it works

        long micros = (System.nanoTime() - start) / 1000;
        return new Result(algorithm,
            recipientKeyPair.getPublic().getEncoded().length,
            encapsulated.encapsulation().length,
            micros);
    }

    public static void main(String[] args) throws Exception {
        for (String algorithm : new String[]{"RSA", "ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"}) {
            Result r = measure(algorithm);
            System.out.printf("%-12s public key: %4d bytes, encapsulation: %4d bytes, time: %d us%n",
                r.algorithm(), r.publicKeyBytes(), r.encapsulationBytes(), r.micros());
        }
    }
}
```

**How to run:** `java MlKemVsRsaComparison.java`.

This adds the production-flavored hard case: measuring and comparing **classical RSA-KEM against all three ML-KEM parameter sets** — public key size, encapsulation size, and timing — the concrete trade-off data a real migration decision needs: ML-KEM's three parameter sets (`512`/`768`/`1024`, roughly analogous to AES-128/192/256 security levels) trade key and ciphertext size for security margin, and the numbers this program prints are exactly what informs choosing among them for a given application's bandwidth and security requirements.

## 6. Walkthrough

Tracing `MlKemVsRsaComparison.main`:

1. `main` loops over four algorithm identifiers: `"RSA"` (a marker handled specially to build a 2048-bit RSA key pair, since `"RSA-KEM"` isn't itself a `KeyPairGenerator` algorithm name), and `"ML-KEM-512"`, `"ML-KEM-768"`, `"ML-KEM-1024"`.
2. For each, `measure(algorithm)` times a full round trip: generate a key pair, encapsulate against the public key, decapsulate against the private key (to confirm correctness, discarding the recovered secret since only timing and sizes matter here), and record the public key's encoded byte length and the encapsulation's byte length.
3. For the RSA case, key generation uses the ordinary `"RSA"` `KeyPairGenerator` algorithm at 2048 bits, but the KEM operations themselves use `KEM.getInstance("RSA-KEM")` — mirroring exactly how [the original KEM introduction](0757-key-encapsulation-mechanism-api.md) set it up.
4. For each ML-KEM variant, both key generation and the KEM instance use the **same** algorithm string (e.g., `"ML-KEM-768"`) — unlike RSA, ML-KEM's key-pair-generation algorithm and its KEM algorithm share one name, since ML-KEM was designed from the ground up specifically as a KEM, not adapted from a general-purpose encryption scheme.
5. `main` prints a formatted line per algorithm, showing the concrete size and timing trade-offs side by side.

Expected output shape (exact byte counts and timings vary slightly by JVM warmup and provider implementation, but the *relative* pattern — ML-KEM's much smaller keys and encapsulations compared to RSA-2048, and larger parameter sets producing larger keys — holds):
```
RSA          public key:  294 bytes, encapsulation:  256 bytes, time: 1840 us
ML-KEM-512   public key:  800 bytes, encapsulation:  768 bytes, time:   95 us
ML-KEM-768   public key: 1184 bytes, encapsulation: 1088 bytes, time:  110 us
ML-KEM-1024  public key: 1568 bytes, encapsulation: 1568 bytes, time:  130 us
```

## 7. Gotchas & takeaways

> **Gotcha:** ML-KEM's three parameter sets are **not interchangeable** — a public key generated for `"ML-KEM-768"` cannot be used with a `KEM` instance created via `KEM.getInstance("ML-KEM-512")`, since they're distinct algorithms with different key formats and security levels under the hood, even though their names look like variations of "the same thing." Always use the identical algorithm string for both key generation and KEM instantiation, and keep that string consistent between the encapsulating and decapsulating parties.

- Java 24 (JEP 496) adds standard `ML-KEM-512`/`ML-KEM-768`/`ML-KEM-1024` support to the JDK's cryptography providers, usable through [the same `javax.crypto.KEM` API](0757-key-encapsulation-mechanism-api.md) introduced in Java 21 — this is exactly the future-proofing that API's design promised.
- ML-KEM is NIST's standardized post-quantum key encapsulation algorithm, based on lattice problems believed resistant to attacks from both classical and quantum computers.
- Migrating existing `KEM`-based code from `"RSA-KEM"` to an `ML-KEM` variant is a matter of changing the algorithm name string, not restructuring the encapsulate/decapsulate flow.
- ML-KEM produces meaningfully smaller public keys and encapsulations than RSA-2048, alongside typically faster operation times — post-quantum security here doesn't come with a size or performance penalty relative to classical RSA.
- Migrating key-establishment to post-quantum algorithms is considered urgent even before large-scale quantum computers exist, due to "harvest now, decrypt later" risk against any long-lived secret encapsulated with classical algorithms today.
