---
card: spring-security
gi: 50
slug: compromised-password-checking-haveibeenpwned
title: "Compromised password checking (HaveIBeenPwned)"
---

## 1. What it is

`CompromisedPasswordChecker` (added in Spring Security 6.3) is a single-method interface (`check(rawPassword)`) that answers whether a password appears in a known data-breach corpus, with `HaveIBeenPwnedRestApiPasswordChecker` as the built-in implementation querying the HaveIBeenPwned Pwned Passwords API — using a k-anonymity scheme so the *full* password (or its full hash) is never transmitted to the external service, only the first five characters of its SHA-1 hash, with the matching check completed locally against the returned candidate list.

```java
@Bean
public CompromisedPasswordChecker compromisedPasswordChecker() {
    return new HaveIBeenPwnedRestApiPasswordChecker();
}

// used during registration or password-change flows, NOT during every login:
CompromisedPasswordDecision decision = compromisedPasswordChecker.check(rawPassword);
if (decision.isCompromised()) {
    throw new CompromisedPasswordException("This password has appeared in a known data breach");
}
```

## 2. Why & when

A password can be perfectly well-hashed with a strong, slow algorithm and still be a bad password — if it's `"password123"` or a phrase leaked in a previous, unrelated breach, an attacker doesn't need to crack the hash at all; they simply try the same known-bad password directly (a technique called credential stuffing), since a large fraction of real users reuse passwords across sites. `CompromisedPasswordChecker` catches exactly this case at the moment a password is created or changed, checking it against a corpus of hundreds of millions of passwords already known to have appeared in breaches, entirely independent of and complementary to how strongly that password is subsequently hashed for storage.

Reach for compromised password checking when:

- Enforcing password quality requirements at registration or password-change time — pairing a compromised-password check alongside (not instead of) a strong hashing algorithm addresses two entirely different threats: hash-cracking resistance and reused-known-bad-password resistance.
- Understanding the k-anonymity mechanism specifically — it exists so the checking service (a third party, even if trusted) never actually learns the user's real password or its full hash, only a broad hash prefix shared by many possible passwords, from which it returns *candidates* the caller checks locally.
- Never call this check on every single login — it belongs at password-creation/change time (registration, password reset, password change), not as a per-login gate, both for performance reasons and because a password that was fine when set and hasn't been breached since doesn't need re-checking on every authentication.

## 3. Core concept

```
 K-ANONYMITY scheme (what HaveIBeenPwnedRestApiPasswordChecker actually does):

   1. compute sha1(rawPassword)  -- LOCALLY, never leaves the application
   2. send ONLY the first 5 hex characters of that hash to the external API
        e.g. sha1("password123") = "CBFDA..." -> send "CBFDA"
   3. the API returns EVERY known-breached password hash SHARING that same 5-char prefix
        (typically hundreds of candidates -- the prefix alone doesn't identify ONE specific password)
   4. LOCALLY, check whether the FULL hash of the actual password appears anywhere in that returned list
   5. the external service NEVER learns which exact password (among the hundreds sharing the prefix) was checked
```

Only a broad, shared prefix ever leaves the application — the actual password (and even its full hash) never does.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A raw password is hashed locally only the first five hex characters of the hash are sent to the external API which returns hundreds of candidate hashes sharing that prefix the caller then locally checks whether the full hash of the actual password appears in that returned list ensuring the external service never learns the real password">
  <rect x="15" y="65" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">sha1(password)</text>
  <text x="85" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">computed LOCALLY</text>

  <rect x="200" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="275" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">send first 5 chars</text>
  <text x="275" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">to external API</text>

  <rect x="395" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="470" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">API returns HUNDREDS</text>
  <text x="470" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">of candidate hashes</text>

  <rect x="200" y="130" width="345" height="42" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="372" y="156" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">LOCAL check: is the FULL hash in that list?</text>

  <defs><marker id="a50" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="88" x2="200" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a50)"/>
  <line x1="350" y1="88" x2="395" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a50)"/>
  <line x1="470" y1="111" x2="400" y2="130" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a50)"/>
</svg>

The external service only ever sees a broad, shared prefix — never enough to identify the actual password.

## 5. Runnable example

The scenario: implement the k-anonymity scheme end to end using real SHA-1 hashing (JDK-native `MessageDigest`), against a small simulated breach corpus standing in for the real HaveIBeenPwned dataset, then confirm the prefix genuinely corresponds to many candidates (not just one), then wire the check into a registration flow.

### Level 1 — Basic

Compute a real SHA-1 hash, extract its prefix, and check it against a small simulated corpus using the k-anonymity pattern.

```java
import java.security.MessageDigest;
import java.util.*;

public class CompromisedPasswordLevel1 {
    // a TINY simulated breach corpus -- the real HaveIBeenPwned dataset has hundreds of millions of entries
    static Set<String> knownBreachedHashes = Set.of(
            sha1Hex("password123"),
            sha1Hex("qwerty"),
            sha1Hex("letmein123")
    );

    static String sha1Hex(String input) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-1").digest(input.getBytes());
            return HexFormat.of().withUpperCase().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    // models the EXTERNAL API call: given a 5-char PREFIX, return ALL matching full hashes from the corpus
    static List<String> queryApiByPrefix(String fiveCharPrefix) {
        return knownBreachedHashes.stream().filter(h -> h.startsWith(fiveCharPrefix)).toList();
    }

    static boolean isCompromised(String rawPassword) {
        String fullHash = sha1Hex(rawPassword);
        String prefix = fullHash.substring(0, 5); // ONLY this ever "leaves" the application
        List<String> candidates = queryApiByPrefix(prefix); // simulates the API round trip
        return candidates.contains(fullHash); // the FULL comparison happens LOCALLY
    }

    public static void main(String[] args) {
        System.out.println("'password123' compromised? " + isCompromised("password123"));
        System.out.println("'MyUnique$Phrase99!' compromised? " + isCompromised("MyUnique$Phrase99!"));
    }
}
```

How to run: `java CompromisedPasswordLevel1.java`

`isCompromised` computes the full SHA-1 hash locally, extracts only its first five characters as `prefix`, and passes *only that prefix* to `queryApiByPrefix` (standing in for the real network call) — the final `candidates.contains(fullHash)` comparison happens entirely locally, using the full hash the "API" never actually received.

### Level 2 — Intermediate

Confirm the prefix genuinely corresponds to many candidates sharing it, not a single uniquely-identifying value — the actual privacy property k-anonymity provides.

```java
import java.security.MessageDigest;
import java.util.*;

public class CompromisedPasswordLevel2 {
    static String sha1Hex(String input) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-1").digest(input.getBytes());
            return HexFormat.of().withUpperCase().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    public static void main(String[] args) {
        String targetPassword = "hunter2";
        String targetHash = sha1Hex(targetPassword);
        String targetPrefix = targetHash.substring(0, 5);

        System.out.println("checking password: '" + targetPassword + "'");
        System.out.println("full SHA-1 hash: " + targetHash);
        System.out.println("prefix SENT to the API: " + targetPrefix);

        // generate a LARGE pool of OTHER random strings and count how many SHARE this same prefix,
        // demonstrating the prefix alone does NOT uniquely identify targetPassword
        Random random = new Random(42);
        int sharingPrefixCount = 0;
        for (int i = 0; i < 2_000_000; i++) {
            String candidate = "random-string-" + random.nextInt(100_000_000);
            if (sha1Hex(candidate).startsWith(targetPrefix)) sharingPrefixCount++;
        }

        System.out.println("out of 2,000,000 random strings, " + sharingPrefixCount + " share the SAME 5-char prefix");
        System.out.println("(in the REAL API, EVERY one of those matching entries -- often hundreds -- would be returned,");
        System.out.println(" making it impossible for the API to know WHICH SPECIFIC password was actually being checked)");
    }
}
```

How to run: `java CompromisedPasswordLevel2.java`

Because SHA-1 produces a roughly uniform hash distribution, a five-hex-character prefix (20 bits) is shared by roughly 1 in 2^20 (about 1 in a million) random inputs — with 2,000,000 random candidates tested, a meaningful handful will share the exact prefix `targetHash` happens to have, concretely demonstrating that the prefix alone is nowhere near enough information to identify `"hunter2"` specifically among everything else sharing it.

### Level 3 — Advanced

Wire the check into a registration flow, rejecting compromised passwords while accepting strong, unique ones, and add a fallback behavior for when the external check is unavailable — a realistic production resilience concern.

```java
import java.security.MessageDigest;
import java.util.*;

public class CompromisedPasswordLevel3 {
    static Set<String> knownBreachedHashes = Set.of(sha1Hex("password123"), sha1Hex("qwerty"), sha1Hex("welcome1"));

    static String sha1Hex(String input) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-1").digest(input.getBytes());
            return HexFormat.of().withUpperCase().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    static List<String> queryApiByPrefix(String prefix, boolean simulateApiOutage) {
        if (simulateApiOutage) throw new RuntimeException("API unreachable (simulated outage)");
        return knownBreachedHashes.stream().filter(h -> h.startsWith(prefix)).toList();
    }

    static class CompromisedPasswordException extends RuntimeException {
        CompromisedPasswordException(String m) { super(m); }
    }

    static String registerUser(String username, String rawPassword, boolean simulateApiOutage) {
        String fullHash = sha1Hex(rawPassword);
        String prefix = fullHash.substring(0, 5);

        try {
            List<String> candidates = queryApiByPrefix(prefix, simulateApiOutage);
            if (candidates.contains(fullHash)) {
                throw new CompromisedPasswordException("This password has appeared in a known data breach -- please choose another");
            }
        } catch (RuntimeException apiFailure) {
            if (apiFailure instanceof CompromisedPasswordException) throw apiFailure; // re-throw the REAL rejection
            // the API itself is unreachable -- FAIL OPEN (allow registration) rather than blocking all signups entirely,
            // a deliberate availability trade-off, logged for follow-up rather than silently ignored
            System.out.println("  (compromised-password check unavailable, proceeding without it -- logged for review)");
        }

        return "registered " + username;
    }

    public static void main(String[] args) {
        System.out.println(registerUser("alice", "MyUnique$Phrase99!", false));

        try {
            registerUser("bob", "password123", false);
        } catch (CompromisedPasswordException ex) {
            System.out.println("bob: rejected -- " + ex.getMessage());
        }

        System.out.println(registerUser("carol", "password123", true)); // API is DOWN -- fails open, proceeds anyway
    }
}
```

How to run: `java CompromisedPasswordLevel3.java`

alice's unique passphrase registers successfully; bob's `"password123"` is correctly rejected, since it's in the simulated breach corpus; carol's identical `"password123"` — which *should* also be rejected — instead succeeds when `simulateApiOutage` is `true`, since the code deliberately fails open (allows registration to proceed) rather than blocking every signup when the external check itself is unavailable, a real production trade-off worth making deliberately and logging for later review.

## 6. Walkthrough

Trace `registerUser("carol", "password123", true)` from Level 3.

1. `fullHash = sha1Hex("password123")` computes carol's password hash locally, and `prefix = fullHash.substring(0, 5)` extracts its first five characters.
2. Inside the `try` block, `queryApiByPrefix(prefix, true)` is called with `simulateApiOutage = true` — this immediately throws `new RuntimeException("API unreachable (simulated outage)")`, modeling a network failure or the external service being temporarily down.
3. The `catch (RuntimeException apiFailure)` block catches this exception; `apiFailure instanceof CompromisedPasswordException` checks whether this is a genuine "password found in breach" rejection — it is not (it's a plain `RuntimeException` representing the outage), so this check is `false`, and the re-throw branch is skipped.
4. Because the exception was *not* a genuine compromised-password rejection, control falls to the `println` inside the catch block, logging that the check was unavailable and proceeding anyway — this is the deliberate "fail open" behavior.
5. `registerUser` reaches its final `return "registered " + username` line normally, returning `"registered carol"` — despite `"password123"` genuinely being in `knownBreachedHashes` (as proven by bob's earlier, successful rejection when the API *was* available), carol's identical password slips through this time, purely because the check itself couldn't run; this is exactly the trade-off worth deliberately deciding and logging, rather than either blocking all registrations during an outage or silently and invisibly skipping the check.

```
alice: check runs normally -> not found in corpus -> registered
bob:   check runs normally -> "password123" FOUND in corpus -> REJECTED
carol: check FAILS (simulated outage) -> fails OPEN, logged -> registered anyway (same password as bob's rejected one!)
```

## 7. Gotchas & takeaways

> **Gotcha:** treating a compromised-password rejection as equivalent to a generic validation error and silently ignoring any exception from the checker (rather than deliberately distinguishing "the password was found in a breach" from "the check itself failed") risks either accidentally letting a fail-open outage go completely unnoticed, or accidentally blocking every registration during a routine external API blip — both outcomes worth avoiding through the explicit distinction shown in Level 3.

- `CompromisedPasswordChecker` addresses a different threat than strong password hashing: reused, previously-breached passwords are vulnerable to direct credential-stuffing attempts, regardless of how strongly the application itself subsequently hashes them.
- The k-anonymity scheme (sending only a short hash prefix, checking the full hash locally against the returned candidates) ensures the external checking service never learns the actual password or its full hash.
- This check belongs at password-creation or password-change time, not on every login — it answers "is this a bad password to set," not "did you type the right password this time."
- Explicitly deciding (and logging) how to handle the external check itself being unavailable — fail open (allow registration, flag for review) versus fail closed (block registration entirely) — is a deliberate availability/security trade-off that should never be left to accidental exception-handling behavior.
