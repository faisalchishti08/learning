---
card: microservices
gi: 390
slug: token-exchange
title: "Token exchange"
---

## 1. What it is

**Token exchange** is a standardized OAuth2 grant ([RFC 8693](https://www.rfc-editor.org/rfc/rfc8693)) that lets a service trade one security token for a *different* token — one scoped, audienced, or even actor-annotated differently — without going back to the end user to log in again. [Token relay](0389-token-relay-propagation-between-services.md) introduced the idea informally: this topic is the actual protocol behind the "exchange" pattern, including the parts that matter most in production — how it represents *delegation* (a service acting *on behalf of* a user) versus *impersonation* (a service acting *as* a user), and how it lets a downstream service receive a token narrowly scoped to exactly what it needs.

## 2. Why & when

You reach for token exchange whenever a single incoming token isn't the *right shape* for every hop it needs to travel through:

- **Audience narrowing.** A token issued for the gateway shouldn't necessarily be accepted, unmodified, by a deep internal service — see the audience-confusion gotcha in [token relay](0389-token-relay-propagation-between-services.md). Token exchange mints a new token whose `aud` claim is exactly the next hop.
- **Scope down-scoping.** The gateway's token might carry broad scopes (`orders:read orders:write payments:read`), but the specific downstream call only needs `orders:write`. Exchanging for a narrower token limits the blast radius if that token ever leaks.
- **Delegation with a paper trail.** When service A calls service B *because* user alice asked it to, RFC 8693 lets the new token carry both alice's identity (`sub`) *and* an `act` (actor) claim recording that service A performed the exchange — "acting for alice." This is different from just impersonating alice with no record of who initiated the call.
- **Crossing trust domains.** A token minted by one authorization server sometimes needs to be exchanged for a token trusted by a different authorization server — e.g., a partner's token exchanged for an internal one after a federation handshake.

You don't need full token exchange for a small system where every service already trusts the same tokens with the same audience — direct forwarding is fine there. It becomes necessary once you have narrowly-scoped downstream services, multiple trust boundaries, or a compliance requirement to record delegation chains.

## 3. Core concept

Think of a passport-controlled diplomatic reception with multiple rooms, each requiring a *different* pass. You arrive with a valid entry passport (the original token). At the front desk, instead of using that same passport to walk into every room, you exchange it at each doorway for a room-specific badge — the badge still says whose passport it was issued against, but it's stamped only for that room, and expires when you leave. If you lose a badge, only that one room is exposed — not the whole reception.

RFC 8693 formalizes this exchange as an OAuth2 grant:

```
grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=<token being exchanged>
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=<target service>
&scope=<optionally narrower scope>
&actor_token=<optional: the calling service's own token>
&actor_token_type=urn:ietf:params:oauth:token-type:access_token
```

Two claims matter most in the response token:

1. **`sub`** — stays the original subject (e.g., `alice`). This is what keeps identity intact across the exchange, exactly as in [token relay](0389-token-relay-propagation-between-services.md).
2. **`act`** — an optional nested claim identifying who is *acting on behalf of* `sub`. When service `order-service` exchanges alice's token to call `inventory-service`, the new token can carry `act: {"sub": "order-service"}`, recording explicitly "order-service, acting for alice" — a delegation chain, not silent impersonation.

An authorization server exposes this as a `/token` endpoint (the same endpoint used for other [OAuth2 grant types](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md)), and only trusted internal clients are normally allowed to call it — an attacker who can freely mint exchanged tokens defeats the whole point.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service presents alice's broad token to the authorization server's token-exchange endpoint and receives back a narrower token scoped to inventory-service, with an actor claim recording the delegation" font-family="sans-serif">
  <rect x="20" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="40" fill="#e6edf3" font-size="10" text-anchor="middle">Token: sub=alice</text>
  <text x="95" y="55" fill="#8b949e" font-size="9" text-anchor="middle">aud=gateway, scope=broad</text>

  <rect x="230" y="90" width="180" height="70" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="112" fill="#e6edf3" font-size="11" text-anchor="middle">Authorization Server</text>
  <text x="320" y="128" fill="#8b949e" font-size="9" text-anchor="middle">POST /token</text>
  <text x="320" y="143" fill="#8b949e" font-size="9" text-anchor="middle">grant_type=token-exchange</text>

  <rect x="470" y="20" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="545" y="40" fill="#e6edf3" font-size="10" text-anchor="middle">New token: sub=alice</text>
  <text x="545" y="55" fill="#e6edf3" font-size="9" text-anchor="middle">act.sub=order-service</text>
  <text x="545" y="70" fill="#8b949e" font-size="9" text-anchor="middle">aud=inventory-service</text>

  <rect x="230" y="200" width="180" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="225" fill="#e6edf3" font-size="10" text-anchor="middle">order-service (caller)</text>

  <line x1="170" y1="45" x2="230" y2="110" stroke="#79c0ff" marker-end="url(#tx1)"/>
  <text x="180" y="80" fill="#79c0ff" font-size="8">present as subject_token</text>
  <line x1="320" y1="200" x2="320" y2="160" stroke="#f0883e" marker-end="url(#tx1)"/>
  <text x="345" y="180" fill="#f0883e" font-size="8">calls exchange</text>
  <line x1="410" y1="115" x2="470" y2="55" stroke="#6db33f" marker-end="url(#tx1)"/>
  <text x="440" y="90" fill="#6db33f" font-size="8">exchanged token</text>
  <defs>
    <marker id="tx1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

order-service presents alice's broad token as the subject_token and its own credentials as the actor; the authorization server returns a narrower token that preserves alice's identity while recording who is acting on her behalf.

## 5. Runnable example

Scenario: an order-approval flow. order-service needs to call a downstream approval-service, but only for the specific action alice requested, and with a record that order-service — not alice directly — made the call. We build up from a naive re-use of the original token to a full RFC 8693-style exchange with delegation tracking.

### Level 1 — Basic

```java
// File: NaiveTokenReuse.java -- order-service simply re-uses alice's ORIGINAL,
// broadly-scoped token when calling approval-service. No exchange, no narrowing,
// no record of WHICH internal service actually made the call.
public class NaiveTokenReuse {
    record Token(String sub, String aud, String scope) {}

    static Token gatewayToken(String user) {
        return new Token(user, "gateway", "orders:read orders:write payments:read approvals:write");
    }

    static String approvalServiceHandles(Token token) {
        return "ApprovalService approved action for '" + token.sub()
                + "' using a token scoped for '" + token.aud() + "' with scopes [" + token.scope() + "]";
    }

    public static void main(String[] args) {
        Token aliceToken = gatewayToken("alice");
        System.out.println(approvalServiceHandles(aliceToken));
        System.out.println("Problem: this same broad token would ALSO work against payments and orders endpoints.");
    }
}
```

How to run: `java NaiveTokenReuse.java`

`approvalServiceHandles` accepts alice's original token as-is. It works, but the token still carries `payments:read` and `orders:write` scopes it doesn't need for approvals — if this token leaked from approval-service's logs, it would grant far more than approvals access. There's also no record that `order-service`, specifically, is the one that triggered the call.

### Level 2 — Intermediate

```java
// File: BasicTokenExchange.java -- order-service now calls a simulated
// token-exchange endpoint before calling approval-service, receiving a
// NARROWER token scoped ONLY to what approval-service needs.
import java.util.*;

public class BasicTokenExchange {
    record Token(String sub, String aud, String scope) {}

    static final Map<String, String> TARGET_SCOPE = Map.of(
            "approval-service", "approvals:write"
    );

    // Simulated POST /token with grant_type=token-exchange.
    static Token exchange(Token subjectToken, String targetAudience) {
        String narrowScope = TARGET_SCOPE.get(targetAudience);
        if (narrowScope == null) throw new IllegalArgumentException("no exchange policy for " + targetAudience);
        return new Token(subjectToken.sub(), targetAudience, narrowScope);
    }

    static String approvalServiceHandles(Token token) {
        if (!"approval-service".equals(token.aud())) return "REJECTED: wrong audience";
        if (!token.scope().equals("approvals:write")) return "REJECTED: unexpected scope " + token.scope();
        return "ApprovalService approved action for '" + token.sub() + "' with narrowly-scoped token";
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", "gateway", "orders:read orders:write payments:read approvals:write");
        Token exchanged = exchange(aliceToken, "approval-service");
        System.out.println("Exchanged token: aud=" + exchanged.aud() + ", scope=" + exchanged.scope());
        System.out.println(approvalServiceHandles(exchanged));
    }
}
```

How to run: `java BasicTokenExchange.java`

`exchange` looks up the exact scope approval-service is allowed to receive and mints a brand-new token carrying only that scope, still crediting `alice` as the subject. `approvalServiceHandles` now strictly checks both audience and scope, and the exchanged token satisfies both — but note the exchanged token still doesn't record *which* internal service performed the exchange; if `order-service`'s credentials were ever stolen, we'd have no way to distinguish its exchanges from any other trusted caller's.

### Level 3 — Advanced

```java
// File: DelegatedTokenExchange.java -- full RFC 8693-style exchange: the
// exchanged token carries BOTH the original subject ('sub') AND an actor
// claim ('act') recording exactly which internal service performed the
// exchange -- true delegation, not silent impersonation. Also rejects
// exchange requests from services with no exchange policy (least privilege).
import java.util.*;

public class DelegatedTokenExchange {
    record Actor(String sub) {}
    record Token(String sub, String aud, String scope, Actor act) {
        boolean hasDelegation() { return act != null; }
    }

    // Policy: which callers may exchange for which targets, and with what scope.
    record ExchangePolicy(String callerService, String targetAudience, String allowedScope) {}

    static final List<ExchangePolicy> POLICIES = List.of(
            new ExchangePolicy("order-service", "approval-service", "approvals:write"),
            new ExchangePolicy("order-service", "inventory-service", "inventory:reserve")
            // notice: no policy for "recommendation-service" -> approval-service
    );

    static Token exchange(Token subjectToken, String callerService, String targetAudience) {
        ExchangePolicy policy = POLICIES.stream()
                .filter(p -> p.callerService().equals(callerService) && p.targetAudience().equals(targetAudience))
                .findFirst()
                .orElseThrow(() -> new SecurityException(
                        "no exchange policy allows '" + callerService + "' to obtain a token for '" + targetAudience + "'"));
        // sub is preserved; act records who actually performed the exchange.
        return new Token(subjectToken.sub(), targetAudience, policy.allowedScope(), new Actor(callerService));
    }

    static String approvalServiceHandles(Token token) {
        if (!"approval-service".equals(token.aud())) return "REJECTED: wrong audience";
        if (!token.hasDelegation()) return "REJECTED: no actor claim -- cannot audit who initiated this";
        return "ApprovalService approved action for '" + token.sub()
                + "', delegated via '" + token.act().sub() + "' (fully auditable)";
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", "gateway", "orders:read orders:write payments:read approvals:write", null);

        // Legitimate: order-service exchanges alice's token for an approval-service-scoped token.
        Token exchanged = exchange(aliceToken, "order-service", "approval-service");
        System.out.println("Exchanged: sub=" + exchanged.sub() + ", aud=" + exchanged.aud()
                + ", scope=" + exchanged.scope() + ", act.sub=" + exchanged.act().sub());
        System.out.println(approvalServiceHandles(exchanged));

        // Attack attempt: a compromised, unrelated service tries to exchange for the SAME target.
        try {
            exchange(aliceToken, "recommendation-service", "approval-service");
        } catch (SecurityException e) {
            System.out.println("Blocked: " + e.getMessage());
        }
    }
}
```

How to run: `java DelegatedTokenExchange.java`

`POLICIES` acts as a stand-in for the authorization server's exchange rules: only `order-service` is permitted to exchange alice's token for `approval-service` or `inventory-service` audiences, and each exchange has its own allowed scope. `exchange` looks up the caller against these policies *before* minting anything — a caller with no matching policy gets a `SecurityException`, exactly the outcome for the attack attempt from `recommendation-service`. The successful exchange builds a token with `act.sub = "order-service"`, giving `approvalServiceHandles` (and any audit log reading this token) a complete, verifiable delegation chain: alice asked, order-service acted on her behalf, approval-service granted it.

## 6. Walkthrough

Trace `DelegatedTokenExchange.main` in order. **First**, `aliceToken` is constructed directly (standing in for a token the gateway already issued after authenticating alice), with broad scopes and `act = null`.

**Next**, `exchange(aliceToken, "order-service", "approval-service")` runs. The `POLICIES` list is searched for an entry where `callerService` equals `"order-service"` and `targetAudience` equals `"approval-service"` — the first `ExchangePolicy` matches, giving `allowedScope = "approvals:write"`. A new `Token` is built: `sub` copied unchanged as `"alice"`, `aud` set to `"approval-service"`, `scope` set to the policy's narrow value, and `act` set to `new Actor("order-service")`.

**Then**, `approvalServiceHandles(exchanged)` runs. `token.aud()` equals `"approval-service"` — audience check passes. `token.hasDelegation()` is `true` because `act` is non-null — the auditability check passes. The method returns a success string naming both `alice` (the subject) and `order-service` (the actor).

**Finally**, the attack attempt calls `exchange(aliceToken, "recommendation-service", "approval-service")`. The stream filter finds no `ExchangePolicy` where `callerService` equals `"recommendation-service"`, so `findFirst()` returns empty and `orElseThrow` fires a `SecurityException` — caught and printed, demonstrating the exchange endpoint itself enforces which services may act as delegates for which targets.

```
Exchanged: sub=alice, aud=approval-service, scope=approvals:write, act.sub=order-service
ApprovalService approved action for 'alice', delegated via 'order-service' (fully auditable)
Blocked: no exchange policy allows 'recommendation-service' to obtain a token for 'approval-service'
```

Sample HTTP request/response for the real exchange call:

```
POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <order-service-client-credentials>

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=<alice's original access token>
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=approval-service
&scope=approvals:write

HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "<new token>",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
  "token_type": "Bearer",
  "expires_in": 300
}
```

Decoded, the new token's payload carries `"sub": "alice"`, `"aud": "approval-service"`, `"scope": "approvals:write"`, and `"act": {"sub": "order-service"}`.

## 7. Gotchas & takeaways

> It's tempting to let *any* authenticated internal service call the token-exchange endpoint for *any* target audience — that turns token exchange into a universal privilege-escalation tool instead of a narrowing one. Always pair token exchange with an explicit policy of which callers may exchange for which audiences and scopes, exactly like `POLICIES` in Level 3; without it, a compromised low-value service could mint itself a perfectly valid, narrowly-scoped token for a high-value target simply by asking.

- Token exchange (RFC 8693) preserves the original subject (`sub`) while minting a new token with the correct audience and, ideally, a narrower scope for each downstream hop.
- The `act` (actor) claim distinguishes *delegation* ("order-service, acting for alice") from silent impersonation, and gives audit logs a real chain of custody.
- Down-scoping on exchange limits the blast radius of a leaked downstream token — it can only do what that one hop needed, not everything the original token could do.
- Only trusted, explicitly-authorized services should be able to call the exchange endpoint at all — treat it as sensitive infrastructure, not a generic utility.
- This builds directly on [token relay / propagation](0389-token-relay-propagation-between-services.md) and feeds into [service-to-service authentication](0391-service-to-service-authentication.md), which covers how the *caller itself* (not just the token) proves its identity when requesting an exchange.
