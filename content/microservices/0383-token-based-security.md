---
card: microservices
gi: 383
slug: token-based-security
title: "Token-based security"
---

## 1. What it is

**Token-based security** is an approach where, after a caller proves its identity once, it receives a **token** — a piece of data representing "this identity, verified, with these permissions, until this time" — and presents that token on every subsequent request instead of re-proving identity from scratch each time. The server (or any service that receives the token) can check the token itself rather than looking up a session in a shared store, which is what makes tokens a natural fit for microservices, where many independent services need to verify the same caller without all sharing one session database.

## 2. Why & when

Before tokens, the traditional web approach was **server-side sessions**: after login, the server stores session state (who's logged in, what they can do) in memory or a shared store, and gives the client a session ID cookie that's just a lookup key. That works fine for a monolith with one server, but breaks down across microservices for a few reasons:

- **Shared session storage becomes a bottleneck and a single point of failure.** Every service that wants to check "who is this?" would need to query the same central session store, adding a network hop and a dependency every single service now shares.
- **Statelessness scales better.** A well-formed token (especially a signed one like a [JWT](0384-json-web-token-jwt-structure-validation.md)) carries enough information for a service to verify it *without* a network call back to a central store — it just checks a signature and reads embedded claims.
- **Cross-service and cross-domain calls are natural with tokens.** A token can be issued once by a central authority and then verified independently by any service that trusts that authority's signing key, without those services needing to share a database.
- **Tokens carry structured claims**, not just an opaque ID — things like the caller's identity, roles, scopes, and expiry, all inspectable by whichever service receives them (subject, of course, to the token's format — see [opaque tokens](0385-opaque-tokens-token-introspection.md) for the case where claims are *not* directly inspectable).

You reach for token-based security whenever a caller (a browser, a mobile app, or another service) needs to be recognized across multiple, independent requests and potentially multiple independent services — which in a microservices system is essentially every authenticated interaction.

## 3. Core concept

Think of a token like a concert wristband. You show your ticket once at the gate (that's authentication), and in exchange you get a wristband. For the rest of the night, every checkpoint inside the venue — the VIP area, the bar, backstage — just glances at the wristband instead of re-checking your original ticket. The wristband itself carries the information ("general admission," "VIP," "expires at midnight") right there on it, so any checkpoint can decide access on the spot, without radioing back to the front gate every time.

Token-based security has a few recurring pieces:

1. **Issuance** — after successful authentication (often at the [gateway](0382-edge-authentication-at-the-gateway.md) or via an [OAuth2/OIDC](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md) flow), an authorization server or the gateway itself issues a token.
2. **Format** — tokens are broadly either **self-contained** (like a [JWT](0384-json-web-token-jwt-structure-validation.md), where claims are embedded and verifiable via a signature) or **opaque** (a random string that means nothing on its own and must be looked up — see [opaque tokens & token introspection](0385-opaque-tokens-token-introspection.md)). This is a genuine trade-off: self-contained tokens avoid a lookup but can't be instantly revoked; opaque tokens can be revoked instantly but require a lookup on every use.
3. **Transport** — tokens are almost always sent in an `Authorization: Bearer <token>` HTTP header, meaning *whoever holds the token can use it* — which is why transport security (TLS) and short expiry matter so much; a leaked bearer token is as good as a leaked password until it expires or is revoked.
4. **Validation** — the receiving service checks the token is well-formed, unexpired, correctly signed (or, for opaque tokens, still active per an introspection call), and carries sufficient scope for the requested action.
5. **Propagation** — as a request flows from the gateway into and between internal services, the token (or a derived, internal version of it) often needs to travel along, which is the concern covered in [token relay/propagation between services](0389-token-relay-propagation-between-services.md).

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client authenticates once and receives a token, then presents that token as a bearer credential on every subsequent request, and each receiving service validates the token independently" font-family="sans-serif">
  <rect x="20" y="30" width="90" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="65" y="54" fill="#e6edf3" font-size="10" text-anchor="middle">Client</text>

  <rect x="20" y="160" width="90" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="65" y="184" fill="#79c0ff" font-size="9" text-anchor="middle">Auth server</text>

  <line x1="65" y1="70" x2="65" y2="160" stroke="#8b949e" marker-end="url(#a3)"/>
  <text x="20" y="115" fill="#8b949e" font-size="8">1. login</text>
  <line x1="110" y1="180" x2="150" y2="180" stroke="#79c0ff" marker-end="url(#a3)"/>
  <text x="115" y="200" fill="#79c0ff" font-size="8">2. token issued</text>

  <rect x="230" y="90" width="100" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="280" y="110" fill="#e6edf3" font-size="9" text-anchor="middle">Bearer token</text>

  <line x1="65" y1="70" x2="280" y2="90" stroke="#6db33f" stroke-dasharray="3,2"/>

  <rect x="420" y="20" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="42" fill="#e6edf3" font-size="9" text-anchor="middle">Order svc</text>
  <rect x="420" y="80" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="102" fill="#e6edf3" font-size="9" text-anchor="middle">Payment svc</text>
  <rect x="420" y="140" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="162" fill="#e6edf3" font-size="9" text-anchor="middle">Inventory svc</text>

  <line x1="330" y1="105" x2="420" y2="37" stroke="#8b949e" marker-end="url(#a3)"/>
  <line x1="330" y1="105" x2="420" y2="97" stroke="#8b949e" marker-end="url(#a3)"/>
  <line x1="330" y1="105" x2="420" y2="157" stroke="#8b949e" marker-end="url(#a3)"/>
  <text x="380" y="215" fill="#8b949e" font-size="9" text-anchor="middle">3. same token presented, validated independently by each service</text>
  <defs>
    <marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

One token, issued once, is presented on every subsequent call and independently validated by whichever service receives it — no shared session lookup required for self-contained tokens.

## 5. Runnable example

Scenario: a client repeatedly calls services to manage an order. We start with server-side sessions (the pre-token approach, to show its limitation), move to a self-contained bearer token multiple services can validate independently, then add expiry and scope enforcement to make the token production-realistic.

### Level 1 — Basic

```java
// File: ServerSideSession.java -- the PRE-TOKEN approach: a shared, central
// session store that EVERY service would need to query. Shown here as a single
// map to make the shared-dependency limitation obvious.
import java.util.*;

public class ServerSideSession {
    // Simulates a CENTRAL session store every service must reach over the network.
    static final Map<String, String> CENTRAL_SESSION_STORE = new HashMap<>();

    static String login(String username) {
        String sessionId = "session-" + UUID.randomUUID();
        CENTRAL_SESSION_STORE.put(sessionId, username);
        return sessionId;
    }

    // EVERY service, to know who's calling, must query the SAME central store.
    static String orderServiceCheck(String sessionId) {
        String username = CENTRAL_SESSION_STORE.get(sessionId); // network round-trip in reality
        return username == null ? "401: unknown session" : "OrderService recognizes '" + username + "' via central lookup";
    }

    public static void main(String[] args) {
        String sessionId = login("alice");
        System.out.println(orderServiceCheck(sessionId));
        System.out.println("Every service needing identity must query the SAME shared store -- a scaling bottleneck and single point of failure.");
    }
}
```

How to run: `java ServerSideSession.java`

`CENTRAL_SESSION_STORE` stands in for a shared session database that, in a real system, would require a network call from every service on every request. This works, but it means every one of your services now has a hard runtime dependency on that one store being available and fast — exactly the coupling token-based security avoids.

### Level 2 — Intermediate

```java
// File: SelfContainedToken.java -- a self-contained token carries its OWN claims
// (username, issued time) so services can inspect it directly, without a shared store.
import java.util.*;

public class SelfContainedToken {
    // A tiny stand-in for a signed JWT: "claims" bundled with a fake signature.
    static class Token {
        String username;
        long issuedAtMillis;
        String fakeSignature; // in reality, a cryptographic signature over the claims
        Token(String username, long issuedAtMillis, String fakeSignature) {
            this.username = username; this.issuedAtMillis = issuedAtMillis; this.fakeSignature = fakeSignature;
        }
    }

    static Token issueToken(String username) {
        long now = System.currentTimeMillis();
        String signature = "sig(" + username + "," + now + ")"; // stand-in for HMAC/RSA signing
        return new Token(username, now, signature);
    }

    // Any service can verify the token ITSELF -- no shared store, no network lookup.
    static String orderServiceCheck(Token token) {
        String expectedSignature = "sig(" + token.username + "," + token.issuedAtMillis + ")";
        if (!expectedSignature.equals(token.fakeSignature)) {
            return "401: signature invalid, token tampered with";
        }
        return "OrderService independently verified '" + token.username + "' -- NO shared store queried";
    }

    public static void main(String[] args) {
        Token token = issueToken("alice");
        System.out.println(orderServiceCheck(token));
        // Tamper with the username after issuance without updating the signature -- forgery attempt.
        Token forged = new Token("attacker", token.issuedAtMillis, token.fakeSignature);
        System.out.println(orderServiceCheck(forged));
    }
}
```

How to run: `java SelfContainedToken.java`

`orderServiceCheck` recomputes what the signature *should* be from the claims present and compares it to what's attached — a simplified stand-in for verifying a real cryptographic signature. The legitimate token verifies successfully with no external lookup at all. The forged token — claims changed but signature left as-is — fails verification, because the recomputed signature no longer matches. This demonstrates the core property of self-contained tokens: tampering is detectable locally, by any service, without a round-trip to a central authority.

### Level 3 — Advanced

```java
// File: TokenWithExpiryAndScope.java -- production-realistic: tokens carry an
// expiry and a scope, and validation enforces BOTH, independently, on every use --
// modeling the checks a resource server performs on a real bearer token.
import java.util.*;

public class TokenWithExpiryAndScope {
    static class Token {
        String username, scope;
        long issuedAtMillis, expiresAtMillis;
        String fakeSignature;
        Token(String username, String scope, long issuedAtMillis, long expiresAtMillis) {
            this.username = username; this.scope = scope;
            this.issuedAtMillis = issuedAtMillis; this.expiresAtMillis = expiresAtMillis;
            this.fakeSignature = "sig(" + username + "," + scope + "," + issuedAtMillis + "," + expiresAtMillis + ")";
        }
    }

    static Token issueToken(String username, String scope, long ttlMillis) {
        long now = System.currentTimeMillis();
        return new Token(username, scope, now, now + ttlMillis);
    }

    static String verifyAndAuthorize(Token token, String requiredScope) {
        String expectedSignature = "sig(" + token.username + "," + token.scope + "," + token.issuedAtMillis + "," + token.expiresAtMillis + ")";
        if (!expectedSignature.equals(token.fakeSignature)) {
            return "401: signature invalid";
        }
        if (System.currentTimeMillis() > token.expiresAtMillis) {
            return "401: token expired at " + token.expiresAtMillis;
        }
        if (!token.scope.equals(requiredScope)) {
            return "403: token scope '" + token.scope + "' does not grant '" + requiredScope + "'";
        }
        return "200: '" + token.username + "' authorized for '" + requiredScope + "'";
    }

    public static void main(String[] args) throws InterruptedException {
        Token orderToken = issueToken("alice", "orders:write", 60_000);
        Token shortLived = issueToken("alice", "orders:write", 50);

        System.out.println(verifyAndAuthorize(orderToken, "orders:write"));  // fully valid
        System.out.println(verifyAndAuthorize(orderToken, "payments:write")); // valid token, wrong scope

        // Simulate a tampered token: scope upgraded after issuance without a valid signature for the new value.
        Token tampered = new Token("alice", "admin:all", orderToken.issuedAtMillis, orderToken.expiresAtMillis);
        tampered.fakeSignature = orderToken.fakeSignature; // attacker reuses the OLD signature, doesn't recompute it
        System.out.println(verifyAndAuthorize(tampered, "admin:all"));

        Thread.sleep(100);
        System.out.println(verifyAndAuthorize(shortLived, "orders:write")); // now expired
    }
}
```

How to run: `java TokenWithExpiryAndScope.java`

`verifyAndAuthorize` layers three independent checks: signature validity, expiry, and scope — in that order, each capable of rejecting the token on its own. The tampered token is the key hard case: an attacker upgrades the `scope` field to `"admin:all"` but has no way to produce a valid signature for that new value (they don't hold the signing key), so they reuse the old signature — which now mismatches the recomputed expected signature, and the forgery is caught at the very first check, before expiry or scope are even considered.

## 6. Walkthrough

Trace `TokenWithExpiryAndScope.main` in order. **First**, `verifyAndAuthorize(orderToken, "orders:write")` runs. The recomputed signature matches `orderToken.fakeSignature` (nothing was altered), the token hasn't expired (well within its 60-second lifetime), and `token.scope.equals("orders:write")` is true — all three checks pass, returning `"200: 'alice' authorized for 'orders:write'"`.

**Next**, `verifyAndAuthorize(orderToken, "payments:write")` runs with the same untampered token but a different required scope. Signature and expiry checks pass identically, but `"orders:write".equals("payments:write")` is `false` — denied with `403`, showing a fully valid token still can't authorize an action outside its granted scope.

**Then**, the tampered token is built: same username, expiry, and issued time, but `scope` changed to `"admin:all"`, while `fakeSignature` is left as the *original* token's signature (the attacker cannot compute a correct one without the signing key). `verifyAndAuthorize` recomputes `expectedSignature` using the *tampered* fields — which now includes `"admin:all"` — and that recomputed value does not match the stale, reused `fakeSignature`. The check fails at the signature step, `401`, before scope is ever evaluated. This is precisely why self-contained tokens resist tampering: any change to the claims invalidates the signature unless the attacker can forge a new one.

**Finally**, after `Thread.sleep(100)`, `verifyAndAuthorize(shortLived, "orders:write")` runs. Its signature is still valid (nothing was tampered with), but `System.currentTimeMillis()` now exceeds `expiresAtMillis` (100ms elapsed against a 50ms lifetime) — denied with `401` for expiry.

```
orderToken + orders:write    -> 200 authorized
orderToken + payments:write  -> 403 wrong scope
tampered token (admin:all)   -> 401 signature invalid (forgery caught)
shortLived after 100ms       -> 401 expired
```

## 7. Gotchas & takeaways

> A bearer token is exactly what its name says: *whoever bears it, wins*. Unlike a password paired with a username, a leaked bearer token requires no other credential to use — anyone who intercepts it (over an unencrypted connection, from a poorly secured log, from browser storage vulnerable to XSS) can act as the token's owner until it expires or is revoked. This is why bearer tokens should always travel over TLS, have short lifetimes, and never be logged in plaintext.

- Self-contained tokens (like [JWTs](0384-json-web-token-jwt-structure-validation.md)) let any service verify a caller without a shared session store, at the cost of harder instant revocation — see the trade-off discussed in [opaque tokens & token introspection](0385-opaque-tokens-token-introspection.md).
- Always validate signature, expiry, *and* scope on every request — a token that's merely "not expired" doesn't mean it grants the specific permission being requested.
- Short-lived tokens paired with a refresh mechanism limit the damage window of a leaked token, without forcing users to log in constantly.
- Token propagation between internal services is its own design problem — see [token relay/propagation between services](0389-token-relay-propagation-between-services.md) — because forwarding a client's raw token to every downstream service isn't always the right choice.
- Token-based security complements, but doesn't replace, transport encryption: a perfectly valid, unexpired token sent over plaintext HTTP is trivially stolen in transit.
