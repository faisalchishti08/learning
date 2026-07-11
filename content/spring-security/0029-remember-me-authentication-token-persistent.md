---
card: spring-security
gi: 29
slug: remember-me-authentication-token-persistent
title: "Remember-me authentication (token & persistent)"
---

## 1. What it is

Remember-me lets a user stay authenticated across browser restarts and session expiry, beyond the lifetime of a normal session, by issuing a long-lived cookie checked by `RememberMeAuthenticationFilter` whenever the normal session-based `SecurityContext` is empty. Spring Security offers two implementations: `TokenBasedRememberMeServices` (a signed, stateless cookie encoding username, expiry, and a hash — nothing stored server-side) and `PersistentTokenBasedRememberMeServices` (a random series/token pair stored server-side in a database, rotated on every use, which can be individually revoked).

```java
http.rememberMe(remember -> remember
        .key("a-consistent-secret-signing-key") // TokenBasedRememberMeServices signs cookies with this
        .tokenValiditySeconds(1209600)); // 14 days
```

## 2. Why & when

A normal session expires relatively quickly (often on browser close, or after a modest inactivity timeout) — reasonable for security, but a poor experience for an application a user expects to stay logged into for weeks, like a social media site or a shopping cart. Remember-me trades some security margin for convenience: on any request where `SecurityContextHolderFilter` finds no session-backed `Authentication`, `RememberMeAuthenticationFilter` checks for a remember-me cookie and, if valid, establishes a (typically lower-trust, `RememberMeAuthenticationToken`-flagged) authentication automatically, without requiring the user to re-enter credentials.

Reach for `TokenBasedRememberMeServices` (the simpler, stateless option) when:

- No server-side storage is wanted for remember-me state, and the reduced ability to revoke an individual remember-me cookie early (short of rotating the shared signing `key`, which invalidates *every* outstanding cookie at once) is an acceptable trade-off.

Reach for `PersistentTokenBasedRememberMeServices` (the database-backed option) when:

- Individual remember-me sessions need to be revocable (a user clicking "sign out everywhere," or an admin revoking a specific compromised device) without invalidating every other user's remember-me cookie.
- The series/token rotation on every use (a new token value is issued and stored after each successful remember-me authentication, while the series identifier stays constant) provides a way to *detect* cookie theft — if a stolen, already-used token is presented again, it signals the series has been compromised, and the whole series can be invalidated.

## 3. Core concept

```
 TokenBasedRememberMeServices (STATELESS):
   cookie = base64( username + ":" + expiryTime + ":" + HMAC(username + ":" + expiryTime + ":" + password + ":" + key) )
   validation: recompute the HMAC using the SAME key, compare -- no database lookup needed at all
   revocation: only by rotating "key" (invalidates EVERY remember-me cookie ever issued, application-wide)

 PersistentTokenBasedRememberMeServices (SERVER-SIDE STORAGE):
   cookie = base64(series : token)
   database row: (series, username, token, lastUsed)
   validation: look up "series" in the database, compare "token" against the STORED token
   on EVERY successful use: issue a NEW random token, UPDATE the stored row (same series, new token)
   if a PRESENTED token does NOT match the stored one for its series -> series COMPROMISED, invalidate it entirely
```

The stateless variant trades revocability for simplicity; the persistent variant trades a small amount of storage for fine-grained, individual revocation and theft detection.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request with no session backed authentication is checked by RememberMeAuthenticationFilter for a remember me cookie the token based variant verifies it via a signed HMAC with no storage while the persistent variant looks up a series in a database and rotates the token on every successful use">
  <rect x="15" y="70" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="90" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">no session-backed</text>
  <text x="90" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Authentication found</text>

  <rect x="215" y="70" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="305" y="90" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">RememberMeAuthentication</text>
  <text x="305" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Filter checks cookie</text>

  <rect x="450" y="20" width="170" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="535" y="40" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">token-based: verify HMAC</text>
  <text x="535" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">no storage lookup</text>

  <rect x="450" y="115" width="170" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="535" y="135" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">persistent: DB lookup</text>
  <text x="535" y="148" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">rotate token on use</text>

  <defs><marker id="a29" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="93" x2="215" y2="93" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a29)"/>
  <line x1="395" y1="83" x2="450" y2="45" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a29)"/>
  <line x1="395" y1="103" x2="450" y2="138" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a29)"/>
</svg>

Two independent ways to answer "is this remember-me cookie still valid," each with a different revocation story.

## 5. Runnable example

The scenario: implement both remember-me strategies against the same "user stays logged in" goal, then demonstrate token rotation and theft detection under the persistent strategy — the concrete advantage stateless cookies cannot offer.

### Level 1 — Basic

`TokenBasedRememberMeServices`-style: a signed, stateless cookie, verified purely by recomputing its signature.

```java
import java.security.MessageDigest;
import java.util.*;

public class RememberMeLevel1 {
    static final String SIGNING_KEY = "a-consistent-secret-signing-key";

    static String hmac(String data) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest((data + SIGNING_KEY).getBytes());
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    record RememberMeCookie(String username, long expiryEpochSeconds, String signature) {}

    static RememberMeCookie issueCookie(String username, long expiryEpochSeconds) {
        String signature = hmac(username + ":" + expiryEpochSeconds);
        return new RememberMeCookie(username, expiryEpochSeconds, signature);
    }

    static boolean isValid(RememberMeCookie cookie, long nowEpochSeconds) {
        if (nowEpochSeconds > cookie.expiryEpochSeconds()) return false; // expired
        String expectedSignature = hmac(cookie.username() + ":" + cookie.expiryEpochSeconds());
        return expectedSignature.equals(cookie.signature()); // NO database lookup at all
    }

    public static void main(String[] args) {
        RememberMeCookie cookie = issueCookie("alice", 1_000_000_000L + 1_209_600L); // now + 14 days
        System.out.println("cookie: " + cookie);
        System.out.println("valid now? " + isValid(cookie, 1_000_000_000L));
        System.out.println("valid after expiry? " + isValid(cookie, 1_000_000_000L + 1_209_600L + 1));

        RememberMeCookie tampered = new RememberMeCookie("alice", cookie.expiryEpochSeconds(), "forged-signature");
        System.out.println("tampered signature valid? " + isValid(tampered, 1_000_000_000L));
    }
}
```

How to run: `java RememberMeLevel1.java`

`isValid` never touches any stored state — it purely recomputes the expected `hmac` from the cookie's own `username`/`expiryEpochSeconds` fields and compares it to the presented `signature`; a tampered cookie with a forged signature fails immediately, since only someone possessing `SIGNING_KEY` can produce a matching hash.

### Level 2 — Intermediate

`PersistentTokenBasedRememberMeServices`-style: a database-backed series/token pair, validated by lookup rather than signature recomputation.

```java
import java.util.*;

public class RememberMeLevel2 {
    record TokenRow(String series, String username, String token) {}
    static Map<String, TokenRow> tokenStore = new HashMap<>(); // keyed by series

    static String randomToken() { return UUID.randomUUID().toString(); }

    record PersistentCookie(String series, String token) {}

    static PersistentCookie issueCookie(String username) {
        String series = randomToken(); // constant for this "device"/browser for as long as it stays valid
        String token = randomToken();
        tokenStore.put(series, new TokenRow(series, username, token));
        return new PersistentCookie(series, token);
    }

    static Optional<PersistentCookie> validateAndRotate(PersistentCookie presented) {
        TokenRow row = tokenStore.get(presented.series());
        if (row == null) return Optional.empty(); // unknown series entirely
        if (!row.token().equals(presented.token())) {
            tokenStore.remove(presented.series()); // token MISMATCH -> treat series as compromised, invalidate it
            return Optional.empty();
        }
        String newToken = randomToken(); // ROTATE: issue a fresh token for the SAME series
        tokenStore.put(row.series(), new TokenRow(row.series(), row.username(), newToken));
        return Optional.of(new PersistentCookie(row.series(), newToken));
    }

    public static void main(String[] args) {
        PersistentCookie cookie = issueCookie("alice");
        System.out.println("issued: " + cookie);

        Optional<PersistentCookie> rotated = validateAndRotate(cookie);
        System.out.println("after first use, rotated to: " + rotated);

        // reusing the OLD (now-stale) token on the same series
        Optional<PersistentCookie> reusedOld = validateAndRotate(cookie);
        System.out.println("reusing OLD token after rotation: " + reusedOld);
    }
}
```

How to run: `java RememberMeLevel2.java`

The first `validateAndRotate` call succeeds and rotates `token` to a new random value while keeping `series` unchanged; a *second* call reusing the original, now-stale `cookie` fails, since `row.token()` no longer matches — because `validateAndRotate` also removes the entry entirely on mismatch, this series can never be used again, precisely the theft-detection behavior a stolen-and-replayed old cookie would trigger.

### Level 3 — Advanced

Combine both strategies behind a shared interface and simulate a realistic theft scenario: an attacker steals an *already-used* (rotated-past) cookie value and attempts to use it, triggering detection and full series invalidation, protecting the legitimate user's *current* cookie from working again either — the correct, conservative response to suspected theft.

```java
import java.util.*;

public class RememberMeLevel3 {
    record TokenRow(String series, String username, String token, boolean invalidated) {}
    static Map<String, TokenRow> tokenStore = new HashMap<>();

    static String randomToken() { return UUID.randomUUID().toString().substring(0, 8); }

    record PersistentCookie(String series, String token) {}

    static PersistentCookie issueCookie(String username) {
        String series = randomToken();
        String token = randomToken();
        tokenStore.put(series, new TokenRow(series, username, token, false));
        return new PersistentCookie(series, token);
    }

    static String validateAndRotate(PersistentCookie presented) {
        TokenRow row = tokenStore.get(presented.series());
        if (row == null || row.invalidated()) return "REJECTED: unknown or already-invalidated series";
        if (!row.token().equals(presented.token())) {
            // token mismatch on a KNOWN series -> strong signal of theft: invalidate the ENTIRE series
            tokenStore.put(row.series(), new TokenRow(row.series(), row.username(), row.token(), true));
            return "REJECTED + SERIES INVALIDATED: stale token presented, possible cookie theft detected";
        }
        String newToken = randomToken();
        tokenStore.put(row.series(), new TokenRow(row.series(), row.username(), newToken, false));
        return "ACCEPTED, rotated to new token " + newToken;
    }

    public static void main(String[] args) {
        PersistentCookie originalCookie = issueCookie("alice");
        System.out.println("issued: " + originalCookie);

        // LEGITIMATE user uses the cookie -- token rotates, browser stores the NEW value automatically
        System.out.println("legitimate use: " + validateAndRotate(originalCookie));

        // ATTACKER stole the cookie value BEFORE rotation and tries it now, AFTER the legitimate rotation already happened
        System.out.println("attacker replays STOLEN pre-rotation cookie: " + validateAndRotate(originalCookie));

        // the LEGITIMATE user's browser (holding the NEW, rotated token) tries again -- but the series is now invalidated too
        PersistentCookie rotatedCookie = new PersistentCookie(originalCookie.series(), "whatever-the-new-token-was");
        System.out.println("even the legitimate (rotated) cookie now: " + validateAndRotate(rotatedCookie));
    }
}
```

How to run: `java RememberMeLevel3.java`

The legitimate first use rotates the token successfully; the attacker's replay of the *stale, pre-rotation* cookie is detected as a token mismatch on a known series and triggers full series invalidation; critically, the legitimate user's own subsequent attempt — even with what *should* be the correct rotated token — is now also rejected, since the entire series was invalidated as a precaution, forcing the legitimate user to log in again with their actual password, which is the conservative, correct trade-off once theft is suspected.

## 6. Walkthrough

Trace the three `validateAndRotate` calls in Level 3's `main`.

1. `validateAndRotate(originalCookie)` (legitimate use) runs first: `tokenStore.get(originalCookie.series())` finds the row created by `issueCookie`, `invalidated` is `false`, and `row.token().equals(presented.token())` is `true` (nothing has changed yet), so the method takes the rotation branch: it generates `newToken`, stores a fresh `TokenRow` for the same `series` with that new token, and returns the "ACCEPTED, rotated" message.
2. `validateAndRotate(originalCookie)` (attacker replay) runs next, presenting the *same* `originalCookie` object again — but the stored row for this `series` now holds the *new*, rotated token from step 1, not the original one. `row.token().equals(presented.token())` is now `false`, since `presented.token()` is still the stale, pre-rotation value. This triggers the mismatch branch: the stored row is overwritten with `invalidated = true`, and the method returns the "REJECTED + SERIES INVALIDATED" message.
3. `validateAndRotate(rotatedCookie)` (legitimate user's next attempt) runs last: `tokenStore.get(rotatedCookie.series())` finds the *same* row, but this time `row.invalidated()` is `true` (set in step 2), so the very first condition, `row == null || row.invalidated()`, is `true`, and the method immediately returns the generic "unknown or already-invalidated series" rejection — without even reaching the token-comparison logic.
4. This sequence demonstrates the full theft-response lifecycle: a single stale-token replay is enough to invalidate the whole series for *everyone*, including its legitimate owner, which is deliberately conservative — the alternative (only rejecting the attacker's specific stale request while leaving the series otherwise active) would leave a plausible ongoing compromise unaddressed.

```
step 1 (legit, first use):    token matches   -> ACCEPTED, token rotated (old token now stale)
step 2 (attacker, stale token): token MISMATCH  -> REJECTED, entire series marked invalidated
step 3 (legit, next attempt):  series already invalidated -> REJECTED immediately, no comparison even needed
```

## 7. Gotchas & takeaways

> **Gotcha:** with `TokenBasedRememberMeServices`, there is no way to revoke a single stolen cookie without also invalidating every other user's remember-me cookie application-wide (since revocation only happens by rotating the shared signing `key`) — an application with real theft-response requirements should choose `PersistentTokenBasedRememberMeServices` specifically for this reason, despite its added storage requirement.

- `TokenBasedRememberMeServices` is stateless and simple (a signed cookie, verified by recomputing its HMAC) but cannot revoke an individual cookie, only invalidate all of them at once by rotating the shared key.
- `PersistentTokenBasedRememberMeServices` stores a rotating series/token pair server-side, enabling both individual revocation and theft *detection* — a stale token replay is a strong, actionable signal that a cookie has likely been stolen.
- Token rotation happening on every successful use is what makes theft detection possible at all — without rotation, a stolen cookie value would remain valid indefinitely, indistinguishable from the legitimate owner's continued use.
- Remember-me authentication typically carries lower trust than a fresh, credential-verified session — sensitive operations (changing a password, viewing payment details) commonly require re-authenticating with real credentials even while a valid remember-me session is active.
