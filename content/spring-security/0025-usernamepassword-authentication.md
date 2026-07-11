---
card: spring-security
gi: 25
slug: username-password-authentication
title: "Username/password authentication"
---

## 1. What it is

Username/password authentication is the foundational credential model Spring Security is built around: a client supplies a username and a plaintext password (over some channel — a form submission, a Basic header), the application looks up the stored user by username via a `UserDetailsService`, and a `PasswordEncoder` compares the supplied password against the stored (hashed, never plaintext) password. `UsernamePasswordAuthenticationToken` is the concrete `Authentication` implementation carrying this credential pair, both before verification (principal = raw username, credentials = raw password) and after (principal = the loaded `UserDetails`, credentials typically erased).

```java
// before authentication: an unverified token, holding the raw submitted credentials
Authentication unverified = new UsernamePasswordAuthenticationToken(rawUsername, rawPassword);

// UserDetailsService loads the stored user; PasswordEncoder verifies the password
UserDetails stored = userDetailsService.loadUserByUsername(rawUsername);
if (passwordEncoder.matches(rawPassword, stored.getPassword())) {
    Authentication verified = new UsernamePasswordAuthenticationToken(stored, null, stored.getAuthorities());
}
```

## 2. Why & when

Nearly every other authentication mechanism in Spring Security is, at its core, a variation or extension of this same load-then-verify pattern — form login and HTTP Basic both ultimately produce a `UsernamePasswordAuthenticationToken` and hand it to the same `DaoAuthenticationProvider`; understanding this base case first is what makes every later, more specialized mechanism (OAuth2, remember-me, pre-authentication) legible as "the same shape, different credential source." The password is *never* compared as plaintext against plaintext — `PasswordEncoder.matches` recomputes a hash from the supplied raw password and compares hashes, since storing (or even briefly holding) a plaintext password anywhere durable is a serious security liability.

Reach for understanding username/password authentication specifically when:

- Building or debugging any login mechanism, since nearly every other one builds directly on this pattern — a custom `AuthenticationProvider` for a different credential type still typically follows the identical load-then-verify shape.
- Choosing or configuring a `PasswordEncoder` — `BCryptPasswordEncoder` is the standard modern default, deliberately slow (computationally expensive) to resist brute-force attacks, and every stored password should use it (or an equivalent) rather than a fast general-purpose hash like plain SHA-256.
- Understanding why credentials are erased from the `Authentication` object after successful authentication (`eraseCredentials`) — holding a raw password in memory for longer than necessary widens the window in which a memory-inspection attack could recover it.

## 3. Core concept

```
 UsernamePasswordAuthenticationToken, BEFORE verification:
   principal   = "alice"        (raw username)
   credentials = "hunter2"      (raw password)
   authenticated = false

 DaoAuthenticationProvider.authenticate(unverified):
   1. UserDetails stored = userDetailsService.loadUserByUsername("alice")
        stored.getPassword() = "$2a$10$N9qo8uLOickgx2ZMRZoMy..."  (BCrypt hash, NEVER plaintext)
   2. passwordEncoder.matches("hunter2", stored.getPassword())
        -- re-hashes "hunter2" WITH THE SAME SALT embedded in the stored hash, compares results
   3. IF matches: return a NEW, verified UsernamePasswordAuthenticationToken
        principal = stored (the UserDetails, not the raw string anymore)
        credentials = null  (ERASED)
        authorities = stored.getAuthorities()
        authenticated = true
```

The stored password is never decrypted or compared in plaintext — only ever re-hashed and compared as a hash.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A raw username and password are wrapped in an unverified UsernamePasswordAuthenticationToken DaoAuthenticationProvider loads the stored user via UserDetailsService and verifies the password by re hashing it with PasswordEncoder and comparing against the stored hash producing a verified token with credentials erased">
  <rect x="10" y="65" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="85" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">raw username +</text>
  <text x="80" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">raw password</text>

  <rect x="200" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="290" y="44" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">UserDetailsService.loadUser</text>

  <rect x="200" y="112" width="180" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="290" y="136" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">PasswordEncoder.matches</text>

  <rect x="450" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="85" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">verified token</text>
  <text x="535" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">credentials ERASED</text>

  <defs><marker id="a25" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="150" y1="83" x2="200" y2="42" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a25)"/>
  <line x1="150" y1="93" x2="200" y2="132" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a25)"/>
  <line x1="380" y1="42" x2="450" y2="80" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a25)"/>
  <line x1="380" y1="132" x2="450" y2="95" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a25)"/>
</svg>

Two independent lookups converge into one verified (or rejected) result — neither step alone determines the outcome.

## 5. Runnable example

The scenario: build a minimal username/password verification pipeline with a hash-based encoder, then add salting to defend against precomputed-hash attacks, then add credential erasure and account-lockout tracking, a realistic production concern.

### Level 1 — Basic

A minimal encoder and a load-then-verify check, using Java's built-in hashing as a stand-in for BCrypt.

```java
import java.security.MessageDigest;
import java.util.*;

public class UsernamePasswordAuthLevel1 {
    static String hash(String raw) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(raw.getBytes());
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    record StoredUser(String username, String hashedPassword) {}

    public static void main(String[] args) {
        Map<String, StoredUser> userStore = new HashMap<>();
        userStore.put("alice", new StoredUser("alice", hash("hunter2")));

        String submittedUsername = "alice";
        String submittedPassword = "hunter2";

        StoredUser stored = userStore.get(submittedUsername);
        boolean matches = stored != null && hash(submittedPassword).equals(stored.hashedPassword());
        System.out.println("authenticated? " + matches);

        System.out.println("wrong password: " + (hash("wrongpass").equals(stored.hashedPassword())));
    }
}
```

How to run: `java UsernamePasswordAuthLevel1.java`

`hash` is called on the submitted password fresh each time and compared against the *stored* hash — the raw password `"hunter2"` is never stored anywhere, only its hash, and a wrong guess produces a different hash that correctly fails the comparison.

### Level 2 — Intermediate

Add per-user salting, defending against precomputed rainbow-table attacks — real `PasswordEncoder` implementations like `BCryptPasswordEncoder` do this automatically, embedding the salt in the stored hash string itself.

```java
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.*;

public class UsernamePasswordAuthLevel2 {
    static String hashWithSalt(String raw, String salt) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest((salt + raw).getBytes());
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    static String randomSalt() {
        byte[] bytes = new byte[8];
        new SecureRandom().nextBytes(bytes);
        return HexFormat.of().formatHex(bytes);
    }

    record StoredUser(String username, String salt, String saltedHash) {}

    static StoredUser register(String username, String rawPassword) {
        String salt = randomSalt();
        return new StoredUser(username, salt, hashWithSalt(rawPassword, salt));
    }

    static boolean verify(StoredUser stored, String submittedPassword) {
        return hashWithSalt(submittedPassword, stored.salt()).equals(stored.saltedHash());
    }

    public static void main(String[] args) {
        Map<String, StoredUser> userStore = new HashMap<>();
        userStore.put("alice", register("alice", "hunter2"));
        userStore.put("bob", register("bob", "hunter2")); // SAME password as alice

        System.out.println("alice's salt: " + userStore.get("alice").salt());
        System.out.println("bob's salt:   " + userStore.get("bob").salt());
        System.out.println("same stored hash despite same password? "
                + userStore.get("alice").saltedHash().equals(userStore.get("bob").saltedHash()));

        System.out.println("alice verifies with 'hunter2'? " + verify(userStore.get("alice"), "hunter2"));
    }
}
```

How to run: `java UsernamePasswordAuthLevel2.java`

Even though alice and bob chose the identical password `"hunter2"`, their `saltedHash` values differ, since each has an independently random `salt` mixed in before hashing — this is exactly why an attacker who steals the user store cannot use a single precomputed table of common-password hashes to crack every account at once.

### Level 3 — Advanced

Add credential erasure after successful authentication and account-lockout tracking after repeated failures — two real production concerns layered onto the same core verification logic.

```java
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.*;

public class UsernamePasswordAuthLevel3 {
    static String hashWithSalt(String raw, String salt) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest((salt + raw).getBytes());
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }
    static String randomSalt() {
        byte[] bytes = new byte[8];
        new SecureRandom().nextBytes(bytes);
        return HexFormat.of().formatHex(bytes);
    }

    static class UnverifiedToken {
        String principal; String credentials; // mutable ONLY so credentials can be erased after use
        UnverifiedToken(String principal, String credentials) { this.principal = principal; this.credentials = credentials; }
        void eraseCredentials() { this.credentials = null; }
    }

    record StoredUser(String username, String salt, String saltedHash) {}

    static class AccountLockTracker {
        Map<String, Integer> failedAttempts = new HashMap<>();
        static final int MAX_ATTEMPTS = 3;

        boolean isLocked(String username) { return failedAttempts.getOrDefault(username, 0) >= MAX_ATTEMPTS; }
        void recordFailure(String username) { failedAttempts.merge(username, 1, Integer::sum); }
        void recordSuccess(String username) { failedAttempts.remove(username); }
    }

    static String authenticate(UnverifiedToken token, Map<String, StoredUser> userStore, AccountLockTracker lockTracker) {
        if (lockTracker.isLocked(token.principal)) {
            return "423 Locked: too many failed attempts for " + token.principal;
        }
        StoredUser stored = userStore.get(token.principal);
        boolean matches = stored != null && hashWithSalt(token.credentials, stored.salt()).equals(stored.saltedHash());
        if (!matches) {
            lockTracker.recordFailure(token.principal);
            return "401 Unauthorized (attempt " + lockTracker.failedAttempts.getOrDefault(token.principal, 0)
                    + "/" + AccountLockTracker.MAX_ATTEMPTS + ")";
        }
        lockTracker.recordSuccess(token.principal);
        token.eraseCredentials(); // credentials wiped IMMEDIATELY after successful verification
        return "200 OK, authenticated as " + token.principal + " (credentials now null: " + (token.credentials == null) + ")";
    }

    public static void main(String[] args) {
        String salt = randomSalt();
        Map<String, StoredUser> userStore = Map.of("alice", new StoredUser("alice", salt, hashWithSalt("hunter2", salt)));
        AccountLockTracker lockTracker = new AccountLockTracker();

        for (int i = 0; i < 3; i++) {
            System.out.println(authenticate(new UnverifiedToken("alice", "wrongpass"), userStore, lockTracker));
        }
        System.out.println(authenticate(new UnverifiedToken("alice", "hunter2"), userStore, lockTracker));
    }
}
```

How to run: `java UsernamePasswordAuthLevel3.java`

Three consecutive wrong-password attempts each call `lockTracker.recordFailure`, and once the count reaches `MAX_ATTEMPTS` (3), even the fourth attempt — using the *correct* password `"hunter2"` — is rejected immediately by the `isLocked` check before the password is ever compared, and `token.eraseCredentials()` is only ever reached on the success path, which this run never gets to.

## 6. Walkthrough

Trace the full sequence of four `authenticate` calls in Level 3's `main`.

1. Call 1: `isLocked("alice")` checks `failedAttempts.getOrDefault("alice", 0) >= 3`, which is `0 >= 3`, `false`, so it proceeds; `hashWithSalt("wrongpass", salt)` does not equal the stored hash, so `matches` is `false`; `recordFailure` bumps `failedAttempts["alice"]` to `1`, and the method returns `"401 Unauthorized (attempt 1/3)"`.
2. Call 2: identical to call 1, except `failedAttempts["alice"]` is now `2` after `recordFailure`, so the message reads `"attempt 2/3"`.
3. Call 3: identical again, `failedAttempts["alice"]` becomes `3`, message reads `"attempt 3/3"`.
4. Call 4 (the correct-password attempt): `isLocked("alice")` now checks `3 >= 3`, which is `true`, so the method returns `"423 Locked: too many failed attempts for alice"` *immediately* — critically, `hashWithSalt` is never even called for this attempt, meaning the correct password is never actually checked once the account is locked.
5. Had the account not been locked, this fourth call's `hashWithSalt("hunter2", salt)` would have matched the stored hash, `recordSuccess` would have cleared `failedAttempts["alice"]` entirely, `token.eraseCredentials()` would have set `token.credentials` to `null`, and the method would have returned a `200 OK` message confirming the erasure.

```
attempt 1 (wrong): isLocked=false -> hash check FAILS -> failedAttempts["alice"]=1 -> 401
attempt 2 (wrong): isLocked=false -> hash check FAILS -> failedAttempts["alice"]=2 -> 401
attempt 3 (wrong): isLocked=false -> hash check FAILS -> failedAttempts["alice"]=3 -> 401
attempt 4 (RIGHT): isLocked=true  -> 423 Locked (password never even checked this time)
```

## 7. Gotchas & takeaways

> **Gotcha:** comparing a submitted password's hash against a stored hash using a plain `String.equals` (as this example does, for clarity) is subtly vulnerable to a timing attack in a genuinely adversarial context, since `equals` typically short-circuits on the first differing character — real `PasswordEncoder` implementations use a constant-time comparison internally specifically to avoid leaking information through response-time differences. Never hand-roll password comparison in production code; always use a vetted `PasswordEncoder`.

- Passwords are always compared as hashes, never as plaintext — a `PasswordEncoder` re-hashes the freshly submitted password and compares the result against the stored hash, never decrypting anything.
- Per-user salting (embedded directly in the stored hash by modern encoders like `BCryptPasswordEncoder`) defends against precomputed rainbow-table attacks, ensuring identical passwords never produce identical stored hashes across different accounts.
- Credentials should be erased from the `Authentication` object immediately after successful verification, minimizing how long a raw password lingers in memory.
- Account lockout after repeated failed attempts is a standard production hardening measure, but it must be checked *before* any password comparison runs, so a locked account's correct password is never evaluated at all while locked out.
