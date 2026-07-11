---
card: spring-security
gi: 40
slug: delegatingpasswordencoder-id-format
title: "DelegatingPasswordEncoder & {id} format"
---

## 1. What it is

`DelegatingPasswordEncoder` stores an algorithm identifier as a curly-brace-wrapped prefix directly on the encoded password string — `{bcrypt}$2a$10$...`, `{argon2}$argon2id$...`, `{noop}plaintext` — and, on `matches`, reads that prefix to pick the correct underlying `PasswordEncoder` for verification, while always encoding *new* passwords with one configured default algorithm. `PasswordEncoderFactories.createDelegatingPasswordEncoder()` is the standard factory producing Spring Boot's actual default `PasswordEncoder` bean.

```java
@Bean
public PasswordEncoder passwordEncoder() {
    return PasswordEncoderFactories.createDelegatingPasswordEncoder(); // Spring Boot's ACTUAL default
}

// what a stored password actually looks like:
// {bcrypt}$2a$10$dXJ2YW5jZS5jb20uYnJhemlsL29mZmljZS5wYXJhbWV0ZXJz.k1Y1
//  ^^^^^^^ this prefix is read by matches() to select BCryptPasswordEncoder for verification
```

## 2. Why & when

An application's password-hashing choice is never truly permanent — a newly recommended algorithm emerges, a compliance requirement changes, or an acquired legacy system's user table needs importing wholesale — but a hard cutover ("delete every stored hash, force every user to reset their password") is disruptive and often unacceptable. `DelegatingPasswordEncoder` solves this by making the *stored data itself* self-describing: because each stored hash carries its own algorithm identifier, verification always uses the correct algorithm no matter when that particular user's hash was created, while new registrations and password changes always use whatever the *current* default is — letting an algorithm migration happen gradually, one successful login at a time, with zero forced resets.

Reach for `DelegatingPasswordEncoder` when:

- Building or maintaining essentially any Spring Security application — it is Spring Boot's actual default `PasswordEncoder` today, precisely because it accommodates future algorithm changes without requiring foresight at initial setup.
- Migrating from one hashing algorithm to another — existing stored hashes (each still correctly prefixed with their original algorithm) continue verifying correctly, while the encoder's configured default for *new* encodes is simply switched to the new algorithm.
- Importing a legacy user table that used a different or even no real hashing scheme — a legacy `{noop}` or `{MD5}` prefix (registered against a corresponding, deliberately weak `PasswordEncoder`) lets those old hashes keep working temporarily, ideally combined with the upgrade-on-login mechanism from the next card to phase them out.

## 3. Core concept

```
 DelegatingPasswordEncoder holds a MAP: {"bcrypt" -> BCryptPasswordEncoder, "argon2" -> Argon2PasswordEncoder, ...}
                            plus ONE configured "idForEncode" (e.g. "bcrypt")

 encode(rawPassword):
   ALWAYS uses the encoder registered under idForEncode
   result = "{" + idForEncode + "}" + thatEncoder.encode(rawPassword)

 matches(rawPassword, storedPassword):
   id = extract text between "{" and "}" at the START of storedPassword
   delegate = map.get(id)                      -- the encoder THIS specific hash was created with
   remainingHash = storedPassword AFTER the "{id}" prefix
   return delegate.matches(rawPassword, remainingHash)
```

Every stored hash is unambiguous about which algorithm produced it — `matches` never has to guess.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three stored password hashes each carry their own algorithm identifier prefix bcrypt argon2 or noop DelegatingPasswordEncoder reads the prefix on each verification attempt and dispatches to the matching underlying encoder while all new encodes always use one single configured default algorithm">
  <rect x="15" y="15" width="220" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="125" y="36" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">{bcrypt}$2a$10$...</text>

  <rect x="15" y="60" width="220" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="125" y="81" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">{argon2}$argon2id$...</text>

  <rect x="15" y="105" width="220" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="125" y="126" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">{noop}legacy-plaintext</text>

  <rect x="290" y="55" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="75" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">DelegatingPasswordEncoder</text>
  <text x="380" y="88" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">reads {id}, dispatches</text>

  <rect x="510" y="10" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="565" y="31" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">BCryptEncoder</text>

  <rect x="510" y="55" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="565" y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">Argon2Encoder</text>

  <rect x="510" y="100" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="565" y="121" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">NoOpEncoder</text>

  <defs><marker id="a40" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="235" y1="32" x2="290" y2="65" stroke="#8b949e" stroke-width="1" marker-end="url(#a40)"/>
  <line x1="235" y1="77" x2="290" y2="77" stroke="#8b949e" stroke-width="1" marker-end="url(#a40)"/>
  <line x1="235" y1="122" x2="290" y2="90" stroke="#8b949e" stroke-width="1" marker-end="url(#a40)"/>
  <line x1="470" y1="65" x2="510" y2="27" stroke="#8b949e" stroke-width="1" marker-end="url(#a40)"/>
  <line x1="470" y1="78" x2="510" y2="72" stroke="#8b949e" stroke-width="1" marker-end="url(#a40)"/>
  <line x1="470" y1="90" x2="510" y2="117" stroke="#8b949e" stroke-width="1" marker-end="url(#a40)"/>
</svg>

Three differently-hashed passwords, all correctly verified by the same single `DelegatingPasswordEncoder` instance.

## 5. Runnable example

The scenario: implement a working `DelegatingPasswordEncoder` model with two real underlying algorithms (PBKDF2 and a plain SHA-256 "legacy" stand-in), then add a third algorithm and confirm all three coexist correctly, then simulate an algorithm migration by switching the default and confirming both old and newly-encoded passwords keep verifying correctly.

### Level 1 — Basic

A minimal delegating encoder supporting two algorithms, dispatching correctly on `matches` based on the stored prefix.

```java
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.*;

public class DelegatingEncoderLevel1 {
    interface PasswordEncoder {
        String encode(String raw);
        boolean matches(String raw, String encodedWithoutPrefix);
    }

    static class Pbkdf2Encoder implements PasswordEncoder {
        public String encode(String raw) {
            try {
                byte[] salt = new byte[16];
                new SecureRandom().nextBytes(salt);
                SecretKeyFactory f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
                byte[] hash = f.generateSecret(new PBEKeySpec(raw.toCharArray(), salt, 100_000, 256)).getEncoded();
                return Base64.getEncoder().encodeToString(salt) + ":" + Base64.getEncoder().encodeToString(hash);
            } catch (Exception e) { throw new RuntimeException(e); }
        }
        public boolean matches(String raw, String stored) {
            try {
                String[] parts = stored.split(":");
                byte[] salt = Base64.getDecoder().decode(parts[0]);
                byte[] storedHash = Base64.getDecoder().decode(parts[1]);
                SecretKeyFactory f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
                byte[] computed = f.generateSecret(new PBEKeySpec(raw.toCharArray(), salt, 100_000, 256)).getEncoded();
                return Arrays.equals(storedHash, computed);
            } catch (Exception e) { throw new RuntimeException(e); }
        }
    }

    static class LegacySha256Encoder implements PasswordEncoder { // stands in for an imported legacy scheme
        public String encode(String raw) {
            try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw.getBytes())); }
            catch (Exception e) { throw new RuntimeException(e); }
        }
        public boolean matches(String raw, String stored) { return encode(raw).equals(stored); }
    }

    static class DelegatingPasswordEncoder implements PasswordEncoder {
        Map<String, PasswordEncoder> encoders = Map.of("pbkdf2", new Pbkdf2Encoder(), "legacysha256", new LegacySha256Encoder());
        String idForEncode = "pbkdf2"; // the CURRENT default for new encodes

        public String encode(String raw) { return "{" + idForEncode + "}" + encoders.get(idForEncode).encode(raw); }

        public boolean matches(String raw, String stored) {
            int closeBrace = stored.indexOf('}');
            String id = stored.substring(1, closeBrace);
            String rest = stored.substring(closeBrace + 1);
            return encoders.get(id).matches(raw, rest);
        }
    }

    public static void main(String[] args) {
        DelegatingPasswordEncoder delegating = new DelegatingPasswordEncoder();

        String newHash = delegating.encode("hunter2");
        System.out.println("new hash: " + newHash);
        System.out.println("matches: " + delegating.matches("hunter2", newHash));

        String legacyImportedHash = "{legacysha256}" + new LegacySha256Encoder().encode("hunter2");
        System.out.println("legacy hash: " + legacyImportedHash);
        System.out.println("legacy matches: " + delegating.matches("hunter2", legacyImportedHash));
    }
}
```

How to run: `java DelegatingEncoderLevel1.java`

`encode` always uses `idForEncode` ("pbkdf2"), producing a `{pbkdf2}`-prefixed hash; `matches` correctly verifies both that freshly-created hash *and* a separately-constructed `{legacysha256}`-prefixed hash, dispatching to the right underlying encoder purely by reading each stored value's own prefix.

### Level 2 — Intermediate

Add a third algorithm and confirm all three coexist and verify correctly side by side, simultaneously.

```java
import java.security.MessageDigest;
import java.util.*;

public class DelegatingEncoderLevel2 {
    interface PasswordEncoder { String encode(String raw); boolean matches(String raw, String stored); }

    static class Sha256Encoder implements PasswordEncoder { // simplified stand-in encoders for brevity
        String prefixTag;
        Sha256Encoder(String tag) { this.prefixTag = tag; }
        public String encode(String raw) {
            try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest((prefixTag + raw).getBytes())); }
            catch (Exception e) { throw new RuntimeException(e); }
        }
        public boolean matches(String raw, String stored) { return encode(raw).equals(stored); }
    }

    static class DelegatingPasswordEncoder implements PasswordEncoder {
        Map<String, PasswordEncoder> encoders = Map.of(
                "algoA", new Sha256Encoder("saltA-"),
                "algoB", new Sha256Encoder("saltB-"),
                "algoC", new Sha256Encoder("saltC-")
        );
        String idForEncode = "algoC"; // CURRENT default

        public String encode(String raw) { return "{" + idForEncode + "}" + encoders.get(idForEncode).encode(raw); }
        public boolean matches(String raw, String stored) {
            int closeBrace = stored.indexOf('}');
            String id = stored.substring(1, closeBrace);
            return encoders.get(id).matches(raw, stored.substring(closeBrace + 1));
        }
    }

    public static void main(String[] args) {
        DelegatingPasswordEncoder delegating = new DelegatingPasswordEncoder();

        // three users, hashed under THREE DIFFERENT algorithms at three different points in the app's history
        Map<String, String> userStore = new LinkedHashMap<>();
        userStore.put("alice", "{algoA}" + new Sha256Encoder("saltA-").encode("hunter2"));
        userStore.put("bob", "{algoB}" + new Sha256Encoder("saltB-").encode("hunter2"));
        userStore.put("carol", delegating.encode("hunter2")); // encoded via the CURRENT default, algoC

        for (var entry : userStore.entrySet()) {
            System.out.println(entry.getKey() + " (" + entry.getValue().substring(0, entry.getValue().indexOf('}') + 1)
                    + "): matches 'hunter2'? " + delegating.matches("hunter2", entry.getValue()));
        }
    }
}
```

How to run: `java DelegatingEncoderLevel2.java`

All three users' passwords verify correctly, despite having been encoded with three genuinely different algorithms at three different times — `delegating.matches` never needs to know in advance which algorithm any particular user's stored hash uses, since the prefix on each one answers that question at verification time.

### Level 3 — Advanced

Simulate a real algorithm migration: switch the delegating encoder's default from an older algorithm to a newer one mid-lifetime, and confirm both pre-migration and post-migration hashes continue to verify correctly without any batch re-hashing.

```java
import java.security.MessageDigest;
import java.util.*;

public class DelegatingEncoderLevel3 {
    interface PasswordEncoder { String encode(String raw); boolean matches(String raw, String stored); }

    static class TaggedEncoder implements PasswordEncoder {
        String tag;
        TaggedEncoder(String tag) { this.tag = tag; }
        public String encode(String raw) {
            try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest((tag + raw).getBytes())); }
            catch (Exception e) { throw new RuntimeException(e); }
        }
        public boolean matches(String raw, String stored) { return encode(raw).equals(stored); }
    }

    static class DelegatingPasswordEncoder implements PasswordEncoder {
        Map<String, PasswordEncoder> encoders = new HashMap<>(Map.of(
                "oldAlgo", new TaggedEncoder("old-"),
                "newAlgo", new TaggedEncoder("new-")
        ));
        String idForEncode; // MUTABLE -- this is what gets switched during a migration

        DelegatingPasswordEncoder(String initialDefault) { this.idForEncode = initialDefault; }

        public String encode(String raw) { return "{" + idForEncode + "}" + encoders.get(idForEncode).encode(raw); }
        public boolean matches(String raw, String stored) {
            int closeBrace = stored.indexOf('}');
            return encoders.get(stored.substring(1, closeBrace)).matches(raw, stored.substring(closeBrace + 1));
        }
    }

    public static void main(String[] args) {
        DelegatingPasswordEncoder delegating = new DelegatingPasswordEncoder("oldAlgo");

        // BEFORE migration: users registering now get hashed with "oldAlgo"
        String preMigrationHash = delegating.encode("hunter2");
        System.out.println("pre-migration hash: " + preMigrationHash);

        // MIGRATION: the application's configuration is updated to a new default
        delegating.idForEncode = "newAlgo";
        System.out.println("--- migration: default switched to newAlgo ---");

        // AFTER migration: NEW registrations get the new algorithm
        String postMigrationHash = delegating.encode("hunter2");
        System.out.println("post-migration hash: " + postMigrationHash);

        // BOTH old and new hashes must STILL verify correctly -- no forced reset for existing users
        System.out.println("pre-migration hash still matches? " + delegating.matches("hunter2", preMigrationHash));
        System.out.println("post-migration hash matches? " + delegating.matches("hunter2", postMigrationHash));
    }
}
```

How to run: `java DelegatingEncoderLevel3.java`

Switching `idForEncode` from `"oldAlgo"` to `"newAlgo"` mid-run changes what algorithm *new* encodes use, but both the hash created before the switch and the one created after continue to verify correctly — `preMigrationHash` still carries its own `{oldAlgo}` prefix, so `matches` still correctly routes it to `oldAlgo`'s encoder regardless of what the *current* default has since become.

## 6. Walkthrough

Trace `delegating.matches("hunter2", preMigrationHash)` from Level 3, called *after* the migration switch.

1. `preMigrationHash` was created earlier in the run, while `idForEncode` was still `"oldAlgo"` — its value looks like `"{oldAlgo}<sha256 hex digest>"`.
2. `matches` first computes `closeBrace = stored.indexOf('}')`, locating the position of the closing brace in `preMigrationHash`.
3. `stored.substring(1, closeBrace)` extracts everything between the opening and closing braces, which is exactly `"oldAlgo"` — critically, this extraction reads the prefix *embedded in the stored value itself*, completely independent of whatever `delegating.idForEncode`'s *current* value happens to be (which is now `"newAlgo"`, after the migration switch).
4. `encoders.get("oldAlgo")` retrieves the `TaggedEncoder` instance configured with `tag = "old-"` — this lookup succeeds because `encoders` (the full map of *all* supported algorithms) still contains an entry for `"oldAlgo"`, even though it's no longer the default used for *new* encodes.
5. `.matches("hunter2", stored.substring(closeBrace + 1))` calls the old encoder's own `matches`, which recomputes `SHA-256("old-" + "hunter2")` and compares it against the stored hash portion — since this is exactly how `preMigrationHash` was originally produced, the comparison succeeds and the overall call returns `true`, confirming that switching the default going forward never invalidates hashes created under the previous default.

```
BEFORE migration:  idForEncode = "oldAlgo"  -> encode("hunter2") -> "{oldAlgo}<hash using old- tag>"
--- idForEncode switched to "newAlgo" ---
AFTER migration:   idForEncode = "newAlgo"  -> encode("hunter2") -> "{newAlgo}<hash using new- tag>"

matches(preMigrationHash)  -> reads "{oldAlgo}" prefix -> uses OLD encoder regardless of current default -> TRUE
matches(postMigrationHash) -> reads "{newAlgo}" prefix -> uses NEW encoder                                -> TRUE
```

## 7. Gotchas & takeaways

> **Gotcha:** the `encoders` map must retain an entry for *every* algorithm identifier ever actually used to produce a stored hash, for as long as any such hash might still need verification — removing an old algorithm's entry from the map (say, during cleanup) while any user's stored password still carries that prefix breaks their ability to ever log in again, since `matches` would find no delegate registered for that identifier.

- `DelegatingPasswordEncoder` makes each stored password hash self-describing via a `{id}` prefix, letting a single encoder instance correctly verify passwords hashed under multiple different algorithms simultaneously.
- New encodes always use one currently configured default algorithm; switching that default (during a migration) never invalidates hashes produced under a previous default, as long as that algorithm's encoder remains registered in the map.
- This is Spring Boot's actual default `PasswordEncoder` bean, chosen specifically for this future-proofing property — most applications benefit from it without any custom configuration at all.
- Never remove a registered algorithm's entry while any stored password might still carry that identifier's prefix — doing so permanently breaks verification for any user whose password hasn't yet been upgraded, a concern the next card's upgrade-on-login mechanism directly addresses.
