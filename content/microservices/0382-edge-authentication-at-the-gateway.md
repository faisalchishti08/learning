---
card: microservices
gi: 382
slug: edge-authentication-at-the-gateway
title: "Edge authentication at the gateway"
---

## 1. What it is

**Edge authentication at the gateway** means verifying a caller's identity once, at the single entry point where external traffic enters your microservices system — the [API gateway](0382-edge-authentication-at-the-gateway.md) — before any request is allowed to reach the services behind it. Instead of every one of your dozens of services independently implementing "parse the login credential, verify the password, issue a session," that logic lives in exactly one place at the edge, and services behind the gateway can trust that any request reaching them has already cleared that first check.

## 2. Why & when

You want authentication concentrated at the edge whenever you have more than a handful of services, for reasons that compound as the system grows:

- **Duplication avoidance.** Implementing full credential verification (password hashing, MFA, token issuance) in every service is wasteful and error-prone; one team's rushed implementation becomes the weak link, undermining security for the whole system.
- **Consistent policy.** A single gateway enforces one consistent authentication policy — token format, expiry rules, required headers — instead of each service potentially drifting to its own slightly different rules.
- **Reduced exposure of raw credentials.** Only the gateway (and the identity provider it talks to) needs to handle raw passwords or MFA flows; internal services only ever see already-verified, already-issued tokens, shrinking the number of places a raw credential could leak.
- **Simpler client experience.** External clients authenticate once against one well-known endpoint, rather than needing to know how to authenticate against every individual service they might eventually call.

This matters as soon as external clients (browsers, mobile apps, third-party integrations) need to reach *any* service — you want exactly one hardened, well-tested front door, not N loosely-guarded ones. It is not, however, a substitute for internal checks: as [defense in depth](0379-defense-in-depth.md) and [zero-trust networking](0380-zero-trust-networking.md) stress, services behind the gateway should still independently verify what the gateway forwards, in case the gateway is ever bypassed or a request is spoofed internally.

## 3. Core concept

Think of a large office building with one manned lobby and many separate departments upstairs. Visitors show ID and sign in once at the lobby desk — that's edge authentication. The lobby then issues a visible badge for the rest of the visit. Individual departments don't re-run a full ID check at every door, but they *do* glance at the badge before letting someone into a sensitive room — a lighter, second check that assumes the lobby already did the heavy lifting, but doesn't blindly trust a badge that looks tampered with.

Mechanically, edge authentication at the gateway typically works like this:

1. **A client sends credentials** (a username/password, or in modern systems, redirects through an [OAuth2/OIDC](0388-openid-connect-oidc.md) flow) to the gateway or to an identity provider the gateway trusts.
2. **The gateway (or identity provider) verifies those credentials** and, on success, issues a **token** — often a [JWT](0384-json-web-token-jwt-structure-validation.md) or an [opaque token](0385-opaque-tokens-token-introspection.md) — that represents the now-authenticated identity.
3. **The client includes that token on every subsequent request**, typically in an `Authorization: Bearer <token>` header.
4. **The gateway validates the token on every incoming request** — checking its signature, expiry, and issuer — before forwarding the request onward.
5. **The gateway forwards identity information downstream**, often by re-signing a lighter internal token or by passing along verified claims as headers, so that internal services know who the original caller was without each one needing to re-verify a raw credential — this is the beginning of [token relay/propagation](0389-token-relay-propagation-between-services.md).

Crucially, the gateway authenticating a request is not the same as authorizing every downstream action — see [authentication vs authorization](0381-authentication-vs-authorization.md). The gateway typically handles authentication and maybe coarse-grained authorization (e.g., "does this token have any valid scope at all"), while fine-grained, data-specific authorization stays in the owning service.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client authenticates once at the gateway; the gateway validates the token on every request and forwards verified identity to internal services, which do not re-run raw credential checks" font-family="sans-serif">
  <rect x="20" y="90" width="90" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="65" y="119" fill="#e6edf3" font-size="10" text-anchor="middle">Client</text>

  <rect x="200" y="60" width="140" height="110" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="270" y="82" fill="#79c0ff" font-size="11" text-anchor="middle">API Gateway</text>
  <text x="270" y="100" fill="#8b949e" font-size="9" text-anchor="middle">validate token</text>
  <text x="270" y="114" fill="#8b949e" font-size="9" text-anchor="middle">(sig, expiry, issuer)</text>
  <text x="270" y="132" fill="#8b949e" font-size="9" text-anchor="middle">forward verified</text>
  <text x="270" y="146" fill="#8b949e" font-size="9" text-anchor="middle">identity downstream</text>

  <rect x="440" y="30" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="54" fill="#e6edf3" font-size="9" text-anchor="middle">Order svc</text>
  <rect x="440" y="90" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="114" fill="#e6edf3" font-size="9" text-anchor="middle">Payment svc</text>
  <rect x="440" y="150" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="174" fill="#e6edf3" font-size="9" text-anchor="middle">Inventory svc</text>

  <line x1="110" y1="115" x2="200" y2="115" stroke="#8b949e" marker-end="url(#a2)"/>
  <text x="155" y="105" fill="#8b949e" font-size="8" text-anchor="middle">1. credential</text>
  <line x1="340" y1="50" x2="440" y2="50" stroke="#6db33f" marker-end="url(#a2)"/>
  <line x1="340" y1="110" x2="440" y2="110" stroke="#6db33f" marker-end="url(#a2)"/>
  <line x1="340" y1="170" x2="440" y2="170" stroke="#6db33f" marker-end="url(#a2)"/>
  <text x="390" y="200" fill="#6db33f" font-size="9" text-anchor="middle">2. verified identity forwarded to each service</text>
  <defs>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

The gateway is the one place raw credentials are checked; every internal service receives an already-verified identity instead of re-implementing credential verification itself.

## 5. Runnable example

Scenario: a client wants to call an order-placing endpoint. We start with each service checking raw credentials itself (the anti-pattern), move authentication to a single gateway that issues a token, then have the gateway validate that token on every request and forward verified identity downstream.

### Level 1 — Basic

```java
// File: EveryServiceChecksCredentials.java -- the ANTI-PATTERN: each service
// independently re-implements raw credential checking. Duplicated, inconsistent,
// and every service now handles sensitive passwords directly.
import java.util.*;

public class EveryServiceChecksCredentials {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");

    // OrderService re-checks the raw password itself.
    static boolean orderServiceLogin(String username, String password) {
        return password.equals(USER_PASSWORDS.get(username));
    }
    // PaymentService ALSO re-checks the raw password itself, separately.
    static boolean paymentServiceLogin(String username, String password) {
        return password.equals(USER_PASSWORDS.get(username));
    }

    public static void main(String[] args) {
        System.out.println("OrderService login: " + orderServiceLogin("alice", "hunter2"));
        System.out.println("PaymentService login: " + paymentServiceLogin("alice", "hunter2"));
        System.out.println("Two services, two separate places holding and checking the raw password -- duplicated attack surface.");
    }
}
```

How to run: `java EveryServiceChecksCredentials.java`

Both services independently know about and check the raw password. This works, but it means the raw password (or its hash) has to be available to, and correctly checked by, every single service that wants to authenticate a user — doubling (or N-tupling) the number of places a credential-checking bug or leak could occur.

### Level 2 — Intermediate

```java
// File: GatewayIssuesToken.java -- authentication moves to ONE place: the gateway.
// It checks the raw credential once and issues a token; services never see the password.
import java.util.*;

public class GatewayIssuesToken {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");
    static final Map<String, String> ISSUED_TOKENS = new HashMap<>(); // token -> username

    // Only the GATEWAY handles the raw password.
    static String gatewayLogin(String username, String password) {
        if (!password.equals(USER_PASSWORDS.get(username))) {
            return null; // authentication failed
        }
        String token = "token-" + username + "-" + System.nanoTime();
        ISSUED_TOKENS.put(token, username);
        return token;
    }

    // A downstream service NEVER sees a password -- only a token.
    static String orderServiceHandle(String token) {
        String username = ISSUED_TOKENS.get(token);
        if (username == null) return "401: invalid or unknown token";
        return "Order placed on behalf of '" + username + "' -- service never saw a password";
    }

    public static void main(String[] args) {
        String token = gatewayLogin("alice", "hunter2");
        System.out.println("Issued token: " + token);
        System.out.println(orderServiceHandle(token));
        System.out.println(orderServiceHandle("forged-token")); // no raw credential involved, just an invalid token
    }
}
```

How to run: `java GatewayIssuesToken.java`

`gatewayLogin` is the only place `USER_PASSWORDS` is ever consulted. Once it verifies the password, it issues an opaque token and records it — `orderServiceHandle` only ever looks up that token, never a password. This is the core edge-authentication shift: credential verification is centralized, and services trust a token instead of re-implementing password checks.

### Level 3 — Advanced

```java
// File: GatewayValidatesEveryRequest.java -- the gateway now validates the token
// (checking expiry and signature, simulated) on EVERY incoming request before
// forwarding, and forwards VERIFIED identity + scope downstream as headers --
// modeling real gateway behavior including token expiry and scope-based routing.
import java.util.*;

public class GatewayValidatesEveryRequest {
    static class IssuedToken {
        String username, scope;
        long expiresAtMillis;
        IssuedToken(String username, String scope, long expiresAtMillis) {
            this.username = username; this.scope = scope; this.expiresAtMillis = expiresAtMillis;
        }
    }
    static final Map<String, IssuedToken> TOKENS = new HashMap<>();

    static String issueToken(String username, String scope, long ttlMillis) {
        String token = "token-" + username + "-" + System.nanoTime();
        TOKENS.put(token, new IssuedToken(username, scope, System.currentTimeMillis() + ttlMillis));
        return token;
    }

    // Gateway-side validation run on EVERY request, not just at login time.
    static Map<String, String> gatewayValidateAndForward(String token, String requiredScope) {
        IssuedToken t = TOKENS.get(token);
        if (t == null) {
            return Map.of("status", "401", "reason", "token not recognized");
        }
        if (System.currentTimeMillis() > t.expiresAtMillis) {
            return Map.of("status", "401", "reason", "token expired");
        }
        if (!t.scope.equals(requiredScope)) {
            return Map.of("status", "403", "reason", "token scope '" + t.scope + "' insufficient for '" + requiredScope + "'");
        }
        // Forward VERIFIED identity downstream -- the service trusts these headers came from the gateway.
        return Map.of("status", "200", "X-Verified-User", t.username, "X-Verified-Scope", t.scope);
    }

    public static void main(String[] args) throws InterruptedException {
        String shortLivedToken = issueToken("alice", "orders:write", 50); // expires in 50ms
        String properToken = issueToken("alice", "orders:write", 60_000);

        System.out.println(gatewayValidateAndForward(properToken, "orders:write"));   // valid, in scope
        System.out.println(gatewayValidateAndForward(properToken, "payments:write")); // valid token, WRONG scope
        Thread.sleep(100); // let the short-lived token expire
        System.out.println(gatewayValidateAndForward(shortLivedToken, "orders:write")); // now expired
    }
}
```

How to run: `java GatewayValidatesEveryRequest.java`

This version tracks expiry and scope on each issued token and re-validates both on *every* request — not just at the moment of login. `gatewayValidateAndForward` checks token existence, expiry, and scope in order, and only on full success does it produce the verified headers a downstream service would trust (`X-Verified-User`, `X-Verified-Scope`). This models the real behavior of gateways like Spring Cloud Gateway with an OAuth2 resource-server filter: every request is independently validated, tokens have a lifetime, and scope mismatches are rejected with `403` even for an otherwise-valid, unexpired token.

## 6. Walkthrough

Trace `GatewayValidatesEveryRequest.main` in order. **First**, two tokens are issued: `shortLivedToken` for `"alice"` with scope `"orders:write"` and a 50ms lifetime, and `properToken` with the same scope but a 60-second lifetime.

**Next**, `gatewayValidateAndForward(properToken, "orders:write")` runs. The token is found in `TOKENS`, `System.currentTimeMillis()` is well before its expiry, and its scope (`"orders:write"`) matches the required scope exactly — all three checks pass, so the method returns a map with `"status": "200"` plus the forwarded identity headers.

**Then**, `gatewayValidateAndForward(properToken, "payments:write")` runs with the *same* still-valid token, but a different required scope. Token lookup and expiry checks pass identically, but `t.scope.equals("payments:write")` is `false` (the token only carries `"orders:write"`) — so this call is denied with `"status": "403"`, demonstrating that a valid, unexpired token doesn't automatically grant every scope.

**Finally**, after `Thread.sleep(100)` lets 100ms pass, `gatewayValidateAndForward(shortLivedToken, "orders:write")` runs. The token is still found in the map, but `System.currentTimeMillis() > t.expiresAtMillis` is now `true` (100ms elapsed against a 50ms lifetime) — so it fails at the expiry check with `"status": "401"`, before scope is even considered.

```
properToken   + orders:write   -> 200, X-Verified-User=alice, X-Verified-Scope=orders:write
properToken   + payments:write -> 403, token scope insufficient
shortLived... + orders:write   -> 401, token expired (after 100ms sleep)
```

Sample real-world equivalent of the successful case, as an actual HTTP exchange the gateway would forward:

```
GET /orders HTTP/1.1
Authorization: Bearer token-alice-abc123...

--> gateway validates, then forwards internally as:

GET /orders HTTP/1.1
X-Verified-User: alice
X-Verified-Scope: orders:write
```

## 7. Gotchas & takeaways

> Gateway authentication is not a substitute for internal checks. If a service is ever reachable directly — bypassing the gateway, whether by misconfiguration, a leaked internal DNS name, or a misconfigured network policy — and that service blindly trusts an `X-Verified-User` header without confirming it actually came from the gateway (e.g., via a signed internal token or a network policy that only permits the gateway to reach it), an attacker can simply set that header themselves and impersonate anyone. Forwarded identity headers are only trustworthy if the path that sets them cannot be bypassed.

- Centralizing authentication at the gateway means raw credentials are handled in exactly one hardened place, not duplicated across every service.
- The gateway should validate the token (signature, expiry, issuer) on *every* request, not just cache "this client logged in once" indefinitely.
- Gateway authentication typically pairs with coarse-grained authorization (scope checks); fine-grained, data-specific authorization still belongs in the owning service — see [authentication vs authorization](0381-authentication-vs-authorization.md).
- Forwarded identity must itself be trustworthy — either the network guarantees only the gateway can reach internal services, or the forwarded identity is itself a verifiable, signed token, not a plain header anyone could forge.
- This is one layer in [defense in depth](0379-defense-in-depth.md): the gateway is a strong first check, but [zero-trust networking](0380-zero-trust-networking.md) still expects internal services to verify what reaches them.
