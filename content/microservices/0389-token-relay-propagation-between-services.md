---
card: microservices
gi: 389
slug: token-relay-propagation-between-services
title: "Token relay / propagation between services"
---

## 1. What it is

**Token relay** (also called **token propagation**) is the practice of carrying a caller's identity forward through a chain of internal service-to-service calls, so that when service A calls service B on behalf of an original request, B still knows *who* the original caller was — not just that "service A is calling me." Without it, identity gets lost at the first internal hop: the [gateway](0382-edge-authentication-at-the-gateway.md) authenticates the original user, but every service behind it just sees "some internal caller," with no way to enforce user-specific rules or produce an accurate audit trail.

## 2. Why & when

You need token relay any time a request's journey crosses more than one service and something downstream needs to know the original caller's identity, not just the identity of whichever service happens to be calling it directly:

- **Fine-grained, user-specific authorization downstream.** If service B needs to check "does *this specific user* own this resource" (the kind of check discussed in [authentication vs authorization](0381-authentication-vs-authorization.md)), it needs the *user's* identity, which service A alone can't supply just by being an authenticated service itself.
- **Accurate audit trails.** Logs and audit records across a multi-hop call chain should reflect who ultimately triggered an action, not just an anonymous internal service identity — "service A called service B" tells you far less than "user alice, via service A, triggered an action on service B."
- **Consistent authorization decisions across hops.** If the gateway already checked the user has permission to place an order, and the order service then calls the inventory service, the inventory service may need that same user context to apply its own rules (e.g. per-customer inventory limits).

The alternative — each service call carrying only its *own* service-to-service credential with no trace of the original user — is sometimes the right choice (particularly for purely internal, user-agnostic background work), but it silently loses information the moment any downstream authorization decision actually depends on who the human behind the request was.

## 3. Core concept

Think of a relay race where each runner also carries a small note pinned to their jersey, listing who originally entered the race, even as the baton (and the runner carrying it) changes at every handoff. Without the note, the finish-line judge only knows "the last runner who happened to be holding the baton" — not who the race was actually run on behalf of. Token relay is that note: it travels with the request through every hop, so the final service (and everything in between) can still answer "who is this ultimately for?"

There are a few concrete patterns for how this works in practice:

1. **Direct forwarding** — the gateway forwards the *exact* access token it received from the client to downstream services. Simple, but means every internal service now must be able to validate the *client's* token format and trusts a token whose audience may have been the gateway itself, not necessarily them.
2. **Token exchange** — the gateway (or an intermediate service) exchanges the original token for a new, internally-scoped token via a dedicated token-exchange endpoint (standardized as [RFC 8693](https://www.rfc-editor.org/rfc/rfc8693)), preserving the original user's identity (`sub`) while adjusting the audience and scope to match the downstream service being called. This is the more production-realistic approach for anything beyond a trivial system.
3. **Header-based context propagation** — after the first hop validates the original token, the *verified claims* (username, roles) are forwarded as trusted internal headers or a lightweight internal token for subsequent hops, rather than re-forwarding the original raw token everywhere.
4. **Spring Cloud Gateway's `TokenRelay` filter** is a concrete, common implementation of pattern 1: it automatically forwards the incoming OAuth2 access token to downstream calls made through the gateway, which is convenient but should be understood, not used blindly — see the gotcha below about audience scoping.

Whichever pattern you use, the underlying principle connects directly to [zero-trust networking](0380-zero-trust-networking.md) and [defense in depth](0379-defense-in-depth.md): every hop should still independently validate whatever identity it receives, rather than blindly trusting that "the previous hop already checked."

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without token relay, identity is lost after the first internal hop; with token relay, the original caller's identity travels through every hop, either as the same token or exchanged for internally-scoped equivalents" font-family="sans-serif">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle">No relay: identity lost</text>
  <rect x="20" y="40" width="80" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="60" y="61" fill="#e6edf3" font-size="9" text-anchor="middle">Gateway</text>
  <rect x="150" y="40" width="80" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="190" y="61" fill="#e6edf3" font-size="9" text-anchor="middle">Order svc</text>
  <rect x="150" y="100" width="80" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="190" y="121" fill="#f85149" font-size="9" text-anchor="middle">Inventory svc</text>
  <text x="190" y="150" fill="#f85149" font-size="8" text-anchor="middle">"some internal caller" -- WHO?</text>
  <line x1="100" y1="57" x2="150" y2="57" stroke="#6db33f" marker-end="url(#a8)"/>
  <text x="125" y="47" fill="#6db33f" font-size="7" text-anchor="middle">alice's token</text>
  <line x1="190" y1="74" x2="190" y2="100" stroke="#f85149" stroke-dasharray="3,2" marker-end="url(#a8)"/>
  <text x="235" y="90" fill="#f85149" font-size="7">service id only</text>

  <text x="480" y="20" fill="#e6edf3" font-size="12" text-anchor="middle">With relay: identity travels</text>
  <rect x="400" y="40" width="80" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="440" y="61" fill="#e6edf3" font-size="9" text-anchor="middle">Gateway</text>
  <rect x="510" y="40" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="61" fill="#e6edf3" font-size="9" text-anchor="middle">Order svc</text>
  <rect x="510" y="100" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="121" fill="#e6edf3" font-size="9" text-anchor="middle">Inventory svc</text>
  <text x="555" y="150" fill="#6db33f" font-size="8" text-anchor="middle">"alice, via order-svc" -- known!</text>
  <line x1="480" y1="57" x2="510" y2="57" stroke="#6db33f" marker-end="url(#a8)"/>
  <line x1="555" y1="74" x2="555" y2="100" stroke="#6db33f" marker-end="url(#a8)"/>
  <text x="600" y="90" fill="#6db33f" font-size="7">alice's identity (relayed/exchanged)</text>
  <defs>
    <marker id="a8" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Without relay, downstream services only know which service called them; with relay, the original caller's identity travels through every hop, either directly or as an exchanged, appropriately-scoped token.

## 5. Runnable example

Scenario: a user places an order, which triggers a call chain: gateway to order service to inventory service. We start with identity being lost after the first hop, add direct token forwarding, then add proper token exchange so each hop gets a token correctly scoped for *it*, not a blindly reused one.

### Level 1 — Basic

```java
// File: IdentityLostAfterFirstHop.java -- the gateway authenticates the user, but
// each internal service call only carries a SERVICE identity -- the original user
// is gone after the first hop.
public class IdentityLostAfterFirstHop {
    // Gateway authenticates the user (details omitted -- see edge authentication at the gateway).
    static String gatewayAuthenticatedUser = "alice";

    // OrderService calling InventoryService: only its OWN service identity travels, not alice's.
    static String orderServiceCallsInventory(String callingService) {
        return "InventoryService received a call from '" + callingService + "' -- NO idea which USER this is ultimately for";
    }

    public static void main(String[] args) {
        System.out.println("Gateway authenticated user: " + gatewayAuthenticatedUser);
        System.out.println(orderServiceCallsInventory("order-service"));
        System.out.println("If InventoryService needs a per-USER rule, it has NOTHING to check it against.");
    }
}
```

How to run: `java IdentityLostAfterFirstHop.java`

`orderServiceCallsInventory` only receives `"order-service"` as the caller — the fact that `alice` was the original, authenticated user never makes it past the first internal hop. Any downstream logic that needs to know *which user* triggered the call (a per-customer limit, an audit log entry, an ownership check) has nothing to work with.

### Level 2 — Intermediate

```java
// File: DirectTokenForwarding.java -- the gateway's ORIGINAL token is forwarded
// as-is through every internal hop (like Spring Cloud Gateway's TokenRelay filter),
// preserving identity but reusing the SAME token everywhere, including its original audience.
import java.util.*;

public class DirectTokenForwarding {
    static class Token {
        String sub, aud;
        Token(String sub, String aud) { this.sub = sub; this.aud = aud; }
    }

    static Token gatewayIssuesTokenForUser(String username) {
        return new Token(username, "api-gateway"); // originally scoped for the gateway itself
    }

    // The token is forwarded UNCHANGED to every downstream hop.
    static String orderServiceCallsInventory(Token relayedToken) {
        return "InventoryService received relayed token for '" + relayedToken.sub
                + "' (original audience: '" + relayedToken.aud + "') -- identity IS preserved now";
    }

    public static void main(String[] args) {
        Token userToken = gatewayIssuesTokenForUser("alice");
        System.out.println("Order service forwards the SAME token it received, unchanged:");
        System.out.println(orderServiceCallsInventory(userToken));
        System.out.println("Identity preserved, but InventoryService is validating a token whose audience was 'api-gateway', not itself.");
    }
}
```

How to run: `java DirectTokenForwarding.java`

The original token, including `alice`'s identity, now survives the internal hop into `InventoryService` — a real improvement over Level 1. But notice the token's `aud` claim still says `"api-gateway"`, because that's who it was originally issued for. `InventoryService` is accepting a token that, strictly per the [JWT audience check](0384-json-web-token-jwt-structure-validation.md), wasn't actually minted for it — a real, if often overlooked, looseness in the naive direct-forwarding approach.

### Level 3 — Advanced

```java
// File: TokenExchange.java -- proper TOKEN EXCHANGE (RFC 8693 pattern): each hop
// exchanges the relayed token for a NEW token, correctly scoped (audience + limited
// scope) for the SPECIFIC downstream service being called, while still preserving
// the original user's identity ('sub') through every exchange.
import java.util.*;

public class TokenExchange {
    static class Token {
        String sub, aud, scope;
        Token(String sub, String aud, String scope) { this.sub = sub; this.aud = aud; this.scope = scope; }
        public String toString() { return "Token[sub=" + sub + ", aud=" + aud + ", scope=" + scope + "]"; }
    }

    static final Map<String, String> SERVICE_ALLOWED_SCOPE = Map.of(
            "order-service", "orders:write",
            "inventory-service", "inventory:reserve"
    );

    static Token gatewayIssuesUserToken(String username, String initialScope) {
        return new Token(username, "api-gateway", initialScope);
    }

    // Token exchange endpoint (simulated): given an incoming token and a TARGET audience,
    // issue a NEW token preserving 'sub' but scoped correctly for that target.
    static Token exchangeToken(Token incoming, String targetService) {
        String newScope = SERVICE_ALLOWED_SCOPE.get(targetService);
        if (newScope == null) throw new IllegalArgumentException("no scope policy for " + targetService);
        // sub is PRESERVED across the exchange -- this is what keeps user identity intact end-to-end.
        return new Token(incoming.sub, targetService, newScope);
    }

    static String inventoryServiceHandles(Token token) {
        if (!"inventory-service".equals(token.aud)) {
            return "REJECTED: token audience '" + token.aud + "' is not this service";
        }
        if (!"inventory:reserve".equals(token.scope)) {
            return "REJECTED: token scope '" + token.scope + "' insufficient";
        }
        return "Inventory reserved on behalf of original user '" + token.sub + "' (properly scoped token accepted)";
    }

    public static void main(String[] args) {
        Token originalUserToken = gatewayIssuesUserToken("alice", "orders:write");
        System.out.println("Gateway-issued token: " + originalUserToken);

        // Hop 1 -> 2: order-service exchanges the token for one scoped to inventory-service.
        Token exchangedForInventory = exchangeToken(originalUserToken, "inventory-service");
        System.out.println("Exchanged token for inventory-service: " + exchangedForInventory);
        System.out.println(inventoryServiceHandles(exchangedForInventory));

        // Contrast: what happens if the ORIGINAL, un-exchanged token is sent directly instead?
        System.out.println(inventoryServiceHandles(originalUserToken));
    }
}
```

How to run: `java TokenExchange.java`

`exchangeToken` models a call to a real token-exchange endpoint: given the original token, it issues a *new* token whose `aud` and `scope` are correctly set for the specific downstream service (`inventory-service`), while carrying `sub` (`"alice"`) forward unchanged. `inventoryServiceHandles` then validates both `aud` and `scope` strictly. The properly exchanged token passes both checks and preserves `alice`'s identity end-to-end. The original, un-exchanged token — still bearing `aud = "api-gateway"` — is correctly rejected when presented directly to `inventory-service`, demonstrating exactly the looseness Level 2's direct-forwarding approach glossed over.

## 6. Walkthrough

Trace `TokenExchange.main` in order. **First**, `gatewayIssuesUserToken("alice", "orders:write")` creates `originalUserToken` with `sub = "alice"`, `aud = "api-gateway"`, `scope = "orders:write"` — this represents the token the gateway issued after authenticating alice.

**Next**, `exchangeToken(originalUserToken, "inventory-service")` runs. `SERVICE_ALLOWED_SCOPE.get("inventory-service")` returns `"inventory:reserve"` — the specific scope policy for that service. A brand-new `Token` is constructed: `sub` is copied straight from `incoming.sub` (`"alice"`, preserved exactly), but `aud` is now `"inventory-service"` and `scope` is `"inventory:reserve"` — both freshly set for *this specific downstream hop*, not inherited from the original token.

**Then**, `inventoryServiceHandles(exchangedForInventory)` runs. `token.aud` is `"inventory-service"`, matching exactly — the audience check passes. `token.scope` is `"inventory:reserve"`, matching exactly — the scope check passes. The method returns success, crediting the action to `"alice"` — the original user's identity survived two exchanges (gateway to order-service, order-service to inventory-service) intact.

**Finally**, `inventoryServiceHandles(originalUserToken)` runs — this time passing the *original*, un-exchanged token directly, simulating what Level 2's naive direct-forwarding approach would have done. `token.aud` is still `"api-gateway"`, which does not equal `"inventory-service"` — the audience check fails immediately, and the request is rejected, even though this is the very same token that (in Level 2) was accepted without complaint.

```
gateway-issued token:            sub=alice, aud=api-gateway, scope=orders:write
exchanged for inventory-service: sub=alice, aud=inventory-service, scope=inventory:reserve
  -> inventory reserved on behalf of 'alice' (properly scoped token accepted)
original token sent directly:    sub=alice, aud=api-gateway, scope=orders:write
  -> REJECTED: token audience 'api-gateway' is not this service
```

Sample HTTP shape for a real token-exchange call, per RFC 8693:

```
POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=<original-token>
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=inventory-service
```

## 7. Gotchas & takeaways

> Direct token forwarding (Level 2, and Spring Cloud Gateway's default `TokenRelay` filter) is convenient and often good enough for a simple, shallow call chain, but it silently reuses a token whose audience was never actually the deep downstream service. If that downstream service is strict about audience validation (as it should be, per [JWT validation](0384-json-web-token-jwt-structure-validation.md)), direct forwarding will fail outright; if it's *not* strict about audience — accepting any validly-signed token regardless of `aud` — you've quietly reintroduced the audience-confusion risk that audience checking exists to prevent. Either forward tokens only within a single trust boundary that all agree to accept the same audience, or use real token exchange.

- Without token relay, identity is lost at the first internal hop, and every downstream authorization or audit decision loses access to "who is this ultimately for."
- Direct forwarding is simple but reuses a token whose audience wasn't set for the deep downstream service — fine for shallow chains within one trust boundary, risky beyond that.
- Token exchange ([RFC 8693](https://www.rfc-editor.org/rfc/rfc8693)) issues a fresh, correctly-scoped token per hop while preserving the original user's `sub` — the more correct approach for anything beyond a trivial call chain.
- Every hop should still independently validate whatever token or identity it receives — consistent with [zero-trust networking](0380-zero-trust-networking.md) — rather than assuming a relayed token was already fully checked upstream.
- This closes the loop on the whole security batch: [defense in depth](0379-defense-in-depth.md) and zero trust motivate per-hop verification, [OAuth2/OIDC](0388-openid-connect-oidc.md) define how identity and tokens are issued, and token relay is what keeps that identity intact as a request travels through a real multi-service call chain.
