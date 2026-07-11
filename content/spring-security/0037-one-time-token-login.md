---
card: spring-security
gi: 37
slug: one-time-token-login
title: "One-Time Token login"
---

## 1. What it is

One-Time Token (OTT) login, added in Spring Security 6.4, is a passwordless authentication mechanism where a user requests a login by providing only an identifier (typically their email or username), the application generates a single-use token and delivers it out-of-band (an emailed magic link, most commonly), and submitting that token — usually just by clicking the link — authenticates the user, with the token immediately invalidated after that one use. `OneTimeTokenGenerationFilter` and `OneTimeTokenAuthenticationFilter` implement the two halves (issuing, then consuming), configured via `http.oneTimeTokenLogin(...)`.

```java
http.oneTimeTokenLogin(ott -> ott
        .tokenGenerationSuccessHandler((request, response, token) ->
                emailService.sendMagicLink(token.getUsername(), "/login/ott?token=" + token.getTokenValue()))
        .defaultSubmitPageUrl("/login/ott"));
```

## 2. Why & when

Passwords carry real, well-known costs — they must be remembered, they get reused across sites (amplifying the blast radius of any one breach), and they must be hashed and stored securely by every application that uses them. A "magic link" login sidesteps all of this: nothing durable is stored beyond a short-lived, single-use token, there's no password to leak or reuse, and the user experience (click a link in an email) is often simpler than remembering and typing a password. It trades this simplicity for a dependency on the delivery channel's own security (the user's email account effectively becomes the actual credential) and for token lifetime/replay considerations that a well-implemented password never needs to worry about in the same way.

Reach for one-time-token login when:

- Building a lightweight application where email delivery is already a reliable, trusted channel, and the added friction of password creation/management would meaningfully hurt onboarding or return-visit conversion.
- Offering a passwordless *option* alongside traditional login, letting users choose the convenience trade-off for themselves.
- Understanding the underlying security assumption clearly: since anyone with access to the user's email inbox can complete the login, this mechanism is only as strong as the security of that email account — appropriate to weigh against the specific application's risk profile.

## 3. Core concept

```
 STEP 1 -- request a token:
   user submits their email/username (no password) to a "request login" endpoint
   OneTimeTokenGenerationFilter (or an explicit call to OneTimeTokenService.generate())
     generates a random, single-use token, associates it with the username, sets a short expiry
     delivers it OUT-OF-BAND (an emailed link containing the token)

 STEP 2 -- consume the token:
   user clicks the link: GET /login/ott?token=<random-value>
   OneTimeTokenAuthenticationFilter:
     looks up the token, checks it hasn't expired AND hasn't already been consumed
     IF valid: authenticate as the associated user, THEN immediately invalidate/consume the token
     IF invalid/expired/already used: reject
```

The token is deliberately single-use and short-lived — its entire security model depends on both properties holding.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A user requests a login by submitting only their email a random single use short lived token is generated and delivered as a magic link out of band clicking the link submits the token which if still valid and unused authenticates the user and is then immediately invalidated">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">user submits email</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(no password)</text>

  <rect x="220" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="305" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">generate single-use</text>
  <text x="305" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">token, email magic link</text>

  <rect x="440" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="85" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">click link -&gt; authenticated</text>
  <text x="530" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">token immediately consumed</text>

  <defs><marker id="a37" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="88" x2="220" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a37)"/>
  <line x1="390" y1="88" x2="440" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a37)"/>
</svg>

Delivery out-of-band (email) is what stands in for the password — whoever controls that channel controls the login.

## 5. Runnable example

The scenario: model token generation, delivery, and single-use consumption, then add expiry, then add replay protection proving a used token can never authenticate again even if intercepted after the fact.

### Level 1 — Basic

Generate a token, "deliver" it, and consume it once.

```java
import java.util.*;

public class OneTimeTokenLevel1 {
    record Token(String value, String username) {}
    static Map<String, Token> issuedTokens = new HashMap<>(); // tokenValue -> Token

    static String generateAndDeliver(String username) {
        String tokenValue = UUID.randomUUID().toString();
        issuedTokens.put(tokenValue, new Token(tokenValue, username));
        return "emailed magic link: /login/ott?token=" + tokenValue; // the "out-of-band delivery"
    }

    static String consumeToken(String tokenValue) {
        Token token = issuedTokens.remove(tokenValue); // REMOVED immediately -- single use
        if (token == null) return "401 Unauthorized: invalid or already-used token";
        return "200 OK, authenticated as " + token.username();
    }

    public static void main(String[] args) {
        String delivery = generateAndDeliver("alice@example.com");
        System.out.println(delivery);

        String tokenValue = delivery.substring(delivery.indexOf("token=") + 6);
        System.out.println("clicking the link: " + consumeToken(tokenValue));
        System.out.println("clicking the SAME link again: " + consumeToken(tokenValue));
    }
}
```

How to run: `java OneTimeTokenLevel1.java`

`consumeToken` calls `issuedTokens.remove` (not `.get`), so the very first successful consumption deletes the entry entirely — a second attempt to use the identical token value finds nothing left to remove and correctly returns `401 Unauthorized`.

### Level 2 — Intermediate

Add expiry, so a token that's valid in structure but too old is still rejected.

```java
import java.util.*;

public class OneTimeTokenLevel2 {
    record Token(String value, String username, long issuedAtEpochSeconds) {}
    static Map<String, Token> issuedTokens = new HashMap<>();
    static final long TOKEN_VALIDITY_SECONDS = 300; // 5 minutes

    static String generateAndDeliver(String username, long nowEpochSeconds) {
        String tokenValue = UUID.randomUUID().toString();
        issuedTokens.put(tokenValue, new Token(tokenValue, username, nowEpochSeconds));
        return tokenValue;
    }

    static String consumeToken(String tokenValue, long nowEpochSeconds) {
        Token token = issuedTokens.get(tokenValue); // peek first, don't remove yet
        if (token == null) return "401 Unauthorized: invalid or already-used token";
        if (nowEpochSeconds - token.issuedAtEpochSeconds() > TOKEN_VALIDITY_SECONDS) {
            issuedTokens.remove(tokenValue); // expired tokens are ALSO consumed/discarded, never left reusable
            return "401 Unauthorized: token expired";
        }
        issuedTokens.remove(tokenValue); // valid AND used -- consume now
        return "200 OK, authenticated as " + token.username();
    }

    public static void main(String[] args) {
        long issuedAt = 1_000_000_000L;
        String tokenValue = generateAndDeliver("alice@example.com", issuedAt);

        System.out.println("used 2 minutes later: " + consumeToken(tokenValue, issuedAt + 120));

        String tokenValue2 = generateAndDeliver("bob@example.com", issuedAt);
        System.out.println("used 10 minutes later: " + consumeToken(tokenValue2, issuedAt + 600));
    }
}
```

How to run: `java OneTimeTokenLevel2.java`

alice's token, used within the 5-minute window, authenticates successfully; bob's token, used 10 minutes after issuance (past `TOKEN_VALIDITY_SECONDS`), is rejected as expired — both branches remove the token from `issuedTokens` regardless of outcome, so an expired token is just as unusable on a second attempt as a legitimately consumed one.

### Level 3 — Advanced

Add explicit replay-detection logging: prove that even an attacker who intercepts an *already-used* token (say, by viewing the email after the legitimate user already clicked it) gains nothing, and log the attempted reuse for visibility.

```java
import java.util.*;

public class OneTimeTokenLevel3 {
    record Token(String value, String username, long issuedAtEpochSeconds) {}
    static Map<String, Token> issuedTokens = new HashMap<>();
    static Set<String> everIssuedTokenValues = new HashSet<>(); // remembers ALL values ever issued, even after consumption
    static List<String> securityLog = new ArrayList<>();
    static final long TOKEN_VALIDITY_SECONDS = 300;

    static String generateAndDeliver(String username, long nowEpochSeconds) {
        String tokenValue = UUID.randomUUID().toString();
        issuedTokens.put(tokenValue, new Token(tokenValue, username, nowEpochSeconds));
        everIssuedTokenValues.add(tokenValue);
        return tokenValue;
    }

    static String consumeToken(String tokenValue, long nowEpochSeconds) {
        Token token = issuedTokens.get(tokenValue);
        if (token == null) {
            if (everIssuedTokenValues.contains(tokenValue)) {
                securityLog.add("REPLAY ATTEMPT: token " + tokenValue.substring(0, 8) + "... was already consumed");
                return "401 Unauthorized: token already used (replay attempt logged)";
            }
            return "401 Unauthorized: token never existed";
        }
        if (nowEpochSeconds - token.issuedAtEpochSeconds() > TOKEN_VALIDITY_SECONDS) {
            issuedTokens.remove(tokenValue);
            return "401 Unauthorized: token expired";
        }
        issuedTokens.remove(tokenValue);
        return "200 OK, authenticated as " + token.username();
    }

    public static void main(String[] args) {
        long issuedAt = 1_000_000_000L;
        String tokenValue = generateAndDeliver("alice@example.com", issuedAt);

        System.out.println("legitimate user clicks the link: " + consumeToken(tokenValue, issuedAt + 30));
        System.out.println("attacker later replays the SAME (now-used) link: " + consumeToken(tokenValue, issuedAt + 60));
        System.out.println("security log: " + securityLog);
    }
}
```

How to run: `java OneTimeTokenLevel3.java`

The legitimate first use succeeds and removes the token from `issuedTokens`; the attacker's later replay of the *same* token value finds it missing from `issuedTokens` but present in `everIssuedTokenValues` (which is never cleared), so `consumeToken` specifically identifies this as a replay attempt (rather than a token that simply never existed) and records it in `securityLog` — actionable information a real application could use to alert the affected user that their magic link was intercepted.

## 6. Walkthrough

Trace the two `consumeToken` calls in Level 3's `main`.

1. `consumeToken(tokenValue, issuedAt + 30)` runs first — `issuedTokens.get(tokenValue)` finds the `Token` created by `generateAndDeliver`, since it hasn't been consumed yet; `issuedAt + 30 - issuedAt = 30`, well under `TOKEN_VALIDITY_SECONDS (300)`, so the expiry check passes; `issuedTokens.remove(tokenValue)` deletes the entry, and the method returns `"200 OK, authenticated as alice@example.com"`.
2. `consumeToken(tokenValue, issuedAt + 60)` runs next, using the *identical* `tokenValue` — `issuedTokens.get(tokenValue)` now returns `null`, since step 1 removed it; the code checks `everIssuedTokenValues.contains(tokenValue)`, which is `true` (this set is never cleared, unlike `issuedTokens`), so it appends a `"REPLAY ATTEMPT: ..."` entry to `securityLog` and returns the `401` message specifically calling out the replay.
3. The distinction between `issuedTokens` (mutable, tokens removed on use/expiry) and `everIssuedTokenValues` (append-only, remembers every value ever issued) is what makes this replay-specific logging possible — without the second set, step 2 would only be able to say "invalid token," with no way to distinguish "never existed" from "already used and now being replayed," a meaningfully different security signal.
4. The final `println` shows `securityLog` containing exactly one entry, confirming the replay was detected and recorded, giving a real application the hook it needs to notify the user (`"someone tried to reuse your login link — was it you?"`) or flag the account for review.

```
consumeToken(tokenValue, +30s)  -> found in issuedTokens, within validity -> CONSUMED -> 200 OK
consumeToken(tokenValue, +60s)  -> NOT in issuedTokens, BUT in everIssuedTokenValues -> REPLAY logged -> 401
```

## 7. Gotchas & takeaways

> **Gotcha:** one-time-token login is only as secure as the delivery channel (email) itself — if an attacker has access to the user's inbox (a compromised email account, a shared/public device left logged into webmail), they can complete the login without ever needing a password at all, which is a materially different threat model from traditional password-based authentication.

- One-time-token login trades password-management overhead for a dependency on the security of the out-of-band delivery channel — appropriate when that channel (typically email) is already trusted and reliable for the application's risk profile.
- Tokens must be both single-use (consumed/deleted immediately on successful authentication) and short-lived (expiring quickly) — either property alone is insufficient; together they minimize the window and reuse potential of an intercepted token.
- Distinguishing "token never existed" from "token was already used" (via a separate, non-expiring record of ever-issued values) enables meaningful replay-attempt detection and user notification, beyond a generic rejection.
- Consider offering one-time-token login as an *additional* option alongside traditional authentication rather than a full replacement, letting users and the application's risk tolerance determine which mechanism fits a given context.
