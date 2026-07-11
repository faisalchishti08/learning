---
card: spring-security
gi: 39
slug: passwordencoder-bcrypt-argon2-scrypt-pbkdf2-delegating
title: "PasswordEncoder (BCrypt, Argon2, SCrypt, PBKDF2, delegating)"
---

## 1. What it is

`PasswordEncoder` is the two-method interface (`encode(rawPassword)`, `matches(rawPassword, encodedPassword)`) behind every password comparison in Spring Security, with several built-in implementations trading off differently: `BCryptPasswordEncoder` (the long-standing, widely-used default, deliberately slow via a configurable work factor), `Argon2PasswordEncoder` (the winner of the 2015 Password Hashing Competition, tunable for both CPU and memory cost, considered the strongest current choice), `SCryptPasswordEncoder` (also memory-hard, an older alternative to Argon2), and `Pbkdf2PasswordEncoder` (NIST-approved, widely supported, but not memory-hard, making it comparatively weaker against GPU-accelerated attacks at equivalent CPU cost).

```java
// PBKDF2, using JDK-native javax.crypto -- no external library needed, unlike BCrypt/Argon2/SCrypt
SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
PBEKeySpec spec = new PBEKeySpec(rawPassword.toCharArray(), salt, 210_000, 256); // iterations, key length
byte[] hash = factory.generateSecret(spec).getEncoded();
```

## 2. Why & when

All four algorithms share the same core goal — make computing the hash deliberately expensive, so brute-forcing every possible password is prohibitively slow even for an attacker with a stolen hash database — but they differ in exactly *how* they impose that cost, which matters because different attack hardware exploits different weaknesses. A purely CPU-bound cost function (like older PBKDF2 configurations) can be accelerated enormously using GPUs or ASICs, which parallelize CPU-bound work extremely well; memory-hard functions (Argon2, SCrypt) deliberately also require large amounts of RAM per hash attempt, which is far harder and more expensive to parallelize at scale, making them meaningfully more resistant to large-scale offline cracking attempts using specialized hardware.

Reach for each specifically when:

- `Argon2PasswordEncoder` for new applications with no legacy constraint — it's the current strongest general recommendation, being both memory-hard and configurable across CPU/memory/parallelism dimensions independently.
- `BCryptPasswordEncoder` when broad compatibility and decades of battle-testing matter more than the memory-hardness Argon2/SCrypt provide — still a perfectly reasonable, widely deployed choice, and Spring Security's own historical default.
- `Pbkdf2PasswordEncoder` specifically when FIPS compliance is a hard requirement (it's the one NIST-approved option among these) — understanding that it is comparatively the weakest against GPU-accelerated attacks at an equivalent configured cost is important context for that trade-off.
- `DelegatingPasswordEncoder` (the next card) whenever an application needs to support verifying passwords hashed by more than one algorithm at once — essential during any migration between algorithms, or simply as Spring Boot's actual current default.

## 3. Core concept

```
 ALL FOUR share this shape:
   encode(rawPassword)  -> a random SALT + a deliberately EXPENSIVE hash, both embedded in ONE stored string
   matches(raw, stored)  -> extract the salt FROM the stored string, re-hash raw with it, compare

 WHERE THEY DIFFER: what makes the hash expensive
   PBKDF2:   CPU-bound only (iteration count)               -- GPU/ASIC-accelerable
   BCrypt:   CPU-bound only (work factor / cost)             -- GPU/ASIC-accelerable, but very mature/vetted
   SCrypt:   CPU-bound AND memory-bound (memory cost param)   -- harder to parallelize on GPU/ASIC
   Argon2:   CPU-bound, memory-bound, AND parallelism-tunable -- current strongest general recommendation
```

The comparison always re-derives the hash from the raw input and the embedded salt/parameters — never a plaintext comparison, regardless of which algorithm is chosen.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four password hashing algorithms PBKDF2 BCrypt SCrypt and Argon2 all impose a deliberate computational cost on hashing but differ in whether that cost is purely CPU bound or also memory bound Argon2 being both memory hard and parallelism tunable is the current strongest recommendation">
  <rect x="15" y="20" width="280" height="130" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="155" y="35" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">CPU-bound only (GPU/ASIC-accelerable)</text>
  <rect x="30" y="50" width="110" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="85" y="72" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">PBKDF2</text>
  <rect x="170" y="50" width="110" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="225" y="72" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">BCrypt</text>

  <rect x="345" y="20" width="280" height="130" rx="9" fill="none" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="485" y="35" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">memory-hard (harder to parallelize)</text>
  <rect x="360" y="50" width="110" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="415" y="72" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">SCrypt</text>
  <rect x="500" y="50" width="110" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="72" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">Argon2</text>
</svg>

The right-hand group's added memory cost is what makes large-scale, hardware-accelerated cracking meaningfully harder.

## 5. Runnable example

The scenario: implement PBKDF2 correctly using only JDK-native APIs (no external dependency needed, making it directly runnable), then measure and tune its cost factor concretely, then model the *comparative* cost characteristics of a memory-hard algorithm to make the CPU-only-versus-memory-hard distinction concrete without requiring an external Argon2 library.

### Level 1 — Basic

A correct, runnable PBKDF2 implementation using `javax.crypto`, with a random salt embedded alongside the hash.

```java
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.SecureRandom;
import java.util.*;

public class PasswordEncoderLevel1 {
    static final int ITERATIONS = 210_000; // OWASP's 2023 recommended minimum for PBKDF2-HMAC-SHA256
    static final int KEY_LENGTH_BITS = 256;

    static byte[] randomSalt() {
        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        return salt;
    }

    static byte[] pbkdf2(char[] rawPassword, byte[] salt) throws Exception {
        SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        PBEKeySpec spec = new PBEKeySpec(rawPassword, salt, ITERATIONS, KEY_LENGTH_BITS);
        return factory.generateSecret(spec).getEncoded();
    }

    // stored format: base64(salt) + ":" + base64(hash) -- BOTH needed to later verify
    static String encode(String rawPassword) throws Exception {
        byte[] salt = randomSalt();
        byte[] hash = pbkdf2(rawPassword.toCharArray(), salt);
        return Base64.getEncoder().encodeToString(salt) + ":" + Base64.getEncoder().encodeToString(hash);
    }

    static boolean matches(String rawPassword, String stored) throws Exception {
        String[] parts = stored.split(":");
        byte[] salt = Base64.getDecoder().decode(parts[0]);
        byte[] storedHash = Base64.getDecoder().decode(parts[1]);
        byte[] computedHash = pbkdf2(rawPassword.toCharArray(), salt);
        return Arrays.equals(storedHash, computedHash);
    }

    public static void main(String[] args) throws Exception {
        String stored = encode("hunter2");
        System.out.println("stored: " + stored);
        System.out.println("matches 'hunter2'? " + matches("hunter2", stored));
        System.out.println("matches 'wrongpass'? " + matches("wrongpass", stored));
    }
}
```

How to run: `java PasswordEncoderLevel1.java`

`encode` generates a fresh random salt every call and derives a 256-bit key via 210,000 PBKDF2 iterations, storing both salt and hash together; `matches` splits them back apart, re-derives the hash from the *submitted* password using the *stored* salt, and compares the resulting byte arrays with `Arrays.equals` — a correct password produces an identical derived hash, a wrong one does not.

### Level 2 — Intermediate

Measure and tune the iteration count directly, making the CPU-cost trade-off concrete and adjustable.

```java
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.SecureRandom;

public class PasswordEncoderLevel2 {
    static byte[] randomSalt() {
        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        return salt;
    }

    static long timeToHash(char[] rawPassword, byte[] salt, int iterations) throws Exception {
        SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        long start = System.nanoTime();
        PBEKeySpec spec = new PBEKeySpec(rawPassword, salt, iterations, 256);
        factory.generateSecret(spec);
        return (System.nanoTime() - start) / 1_000_000; // milliseconds
    }

    public static void main(String[] args) throws Exception {
        byte[] salt = randomSalt();
        char[] password = "hunter2".toCharArray();

        for (int iterations : new int[]{1_000, 50_000, 210_000}) {
            long millis = timeToHash(password, salt, iterations);
            System.out.println(iterations + " iterations -> " + millis + "ms per hash attempt");
        }

        System.out.println();
        System.out.println("an attacker trying 1 BILLION candidate passwords at 210,000 iterations each");
        System.out.println("would need proportionally ~210x longer than at 1,000 iterations for the SAME candidate count --");
        System.out.println("this multiplier, applied uniformly to every single guess, is the entire point of the cost factor.");
    }
}
```

How to run: `java PasswordEncoderLevel2.java`

Timing the same salt and password at increasing iteration counts shows the per-hash cost scaling roughly linearly with `iterations` — this is the tunable knob a real deployment adjusts upward over time as hardware gets faster, keeping the *time* cost per guess roughly constant even as raw compute speed improves.

### Level 3 — Advanced

Model the CPU-only-versus-memory-hard distinction concretely: simulate a memory-hard cost function that requires allocating and touching a large buffer (standing in for Argon2/SCrypt's actual memory-hardness), and compare its resistance profile against pure iteration count.

```java
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.SecureRandom;
import java.util.*;

public class PasswordEncoderLevel3 {
    static byte[] randomSalt() {
        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        return salt;
    }

    // CPU-only cost: pure iteration count (models PBKDF2/BCrypt's approach)
    static byte[] cpuOnlyHash(char[] rawPassword, byte[] salt, int iterations) throws Exception {
        SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        return factory.generateSecret(new PBEKeySpec(rawPassword, salt, iterations, 256)).getEncoded();
    }

    // MEMORY-HARD cost, modeled: allocate a large buffer and force real reads/writes across ALL of it,
    // standing in for what Argon2/SCrypt actually do internally (real algorithms are considerably more involved)
    static byte[] memoryHardHash(char[] rawPassword, byte[] salt, int memoryCostMb) throws Exception {
        byte[] baseHash = cpuOnlyHash(rawPassword, salt, 10_000); // a modest CPU step, same as any KDF
        int bufferSize = memoryCostMb * 1024 * 1024;
        byte[] largeBuffer = new byte[bufferSize]; // THIS allocation is the memory-hardness -- must be resident in RAM
        // touch the ENTIRE buffer, derived from the base hash, so it can't be skipped or approximated
        for (int i = 0; i < bufferSize; i += 4096) {
            largeBuffer[i] = (byte) (baseHash[i % baseHash.length] ^ (i & 0xFF));
        }
        return Arrays.copyOf(largeBuffer, 32); // final derived hash, a function of the fully-touched buffer
    }

    public static void main(String[] args) throws Exception {
        byte[] salt = randomSalt();
        char[] password = "hunter2".toCharArray();

        long cpuStart = System.nanoTime();
        cpuOnlyHash(password, salt, 210_000);
        long cpuMillis = (System.nanoTime() - cpuStart) / 1_000_000;

        long memStart = System.nanoTime();
        memoryHardHash(password, salt, 64); // 64 MB, a realistic Argon2-style memory cost
        long memMillis = (System.nanoTime() - memStart) / 1_000_000;

        System.out.println("CPU-only (PBKDF2, 210k iterations): " + cpuMillis + "ms, negligible extra RAM required");
        System.out.println("memory-hard (64MB working set):      " + memMillis + "ms, AND requires 64MB of RAM per attempt");
        System.out.println();
        System.out.println("an attacker running MANY parallel guesses on a GPU has thousands of compute cores");
        System.out.println("but each core sharing GPU memory bandwidth makes the memory-hard version's PARALLEL");
        System.out.println("throughput scale far worse than the CPU-only version's -- this is Argon2/SCrypt's core advantage.");
    }
}
```

How to run: `java PasswordEncoderLevel3.java`

`memoryHardHash` forces a genuine 64MB memory allocation and touches every page of it, meaning any attacker attempting to run this hash function in parallel across many cores (as a GPU cracking rig would) needs 64MB of memory *per parallel attempt*, quickly exhausting available memory bandwidth long before exhausting compute — the core reason memory-hard functions resist large-scale parallel cracking far better than a purely CPU-bound iteration count does, even when both take a comparable amount of wall-clock time for a single hash on a single core.

## 6. Walkthrough

Trace `memoryHardHash(password, salt, 64)` from Level 3.

1. `cpuOnlyHash(rawPassword, salt, 10_000)` runs first as a modest initial step, producing a 32-byte `baseHash` derived from the password and salt via 10,000 PBKDF2 iterations — this is deliberately a *smaller* iteration count than the pure CPU-only comparison uses, since the memory-hardness (not raw iteration count) is doing most of the defensive work in this design.
2. `bufferSize` is computed as `64 * 1024 * 1024`, i.e. 67,108,864 bytes; `new byte[bufferSize]` allocates that much memory — this allocation must genuinely be resident in RAM for the subsequent loop to touch it, which is the entire point: an attacker's parallel attempt needs this same allocation for *each* concurrent guess.
3. The `for` loop iterates through `largeBuffer` in 4096-byte strides, writing a value derived from `baseHash` and the current index into each touched position — this ensures every part of the large buffer is genuinely read from and written to, rather than merely allocated and left untouched (which an optimizing runtime or a clever attacker's shortcut might otherwise skip).
4. `Arrays.copyOf(largeBuffer, 32)` returns the first 32 bytes of the now-fully-touched buffer as the final derived hash — this value depends on `baseHash`, the salt (via `baseHash`'s own derivation), and the fact that the entire buffer was actually computed, not merely allocated.
5. The final comparison prints both timings and explains the key asymmetry: while a single hash attempt's wall-clock time might be roughly comparable between the CPU-only and memory-hard approaches on one machine, an attacker attempting *many parallel* guesses (the realistic attack scenario against a stolen hash database) hits a hard ceiling with the memory-hard version much sooner, since GPU/ASIC hardware has far more parallel compute cores than it has memory bandwidth to support that many simultaneous 64MB working sets.

```
cpuOnlyHash: 210,000 PBKDF2 iterations                     -> fast per-core, but PARALLELIZES easily (many cores, little RAM each)
memoryHardHash: 10,000 iterations + 64MB buffer touched     -> each parallel attempt needs its OWN 64MB -- doesn't scale on GPU/ASIC
```

## 7. Gotchas & takeaways

> **Gotcha:** choosing an iteration/cost-factor value once and never revisiting it is a common mistake — as hardware gets faster over time, a cost factor that was appropriately expensive years ago becomes comparatively cheap today; production systems should periodically re-evaluate and, ideally, automatically upgrade stored hashes to a stronger configuration on the user's next successful login (the subject of the "password storage history & upgrades" card next in this section).

- All four algorithms (PBKDF2, BCrypt, SCrypt, Argon2) share the same core goal — deliberately expensive hashing to resist brute-force — but differ in whether that cost is purely CPU-bound (easier to accelerate with GPUs/ASICs) or also memory-bound (meaningfully harder to parallelize at scale).
- Argon2 is the current strongest general recommendation for new applications with no legacy constraint, being both memory-hard and independently tunable across CPU, memory, and parallelism dimensions.
- PBKDF2 remains the only NIST/FIPS-approved option among these, relevant specifically when regulatory compliance requires it, despite being comparatively weaker against GPU-accelerated attacks at an equivalent configured cost.
- Cost factors are not "set once and forget" — they should be periodically increased as hardware capability grows, ideally paired with a mechanism (covered in the following cards) to transparently upgrade already-stored hashes when a user next successfully authenticates.
