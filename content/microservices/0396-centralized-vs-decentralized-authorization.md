---
card: microservices
gi: 396
slug: centralized-vs-decentralized-authorization
title: "Centralized vs decentralized authorization"
---

## 1. What it is

Once you've decided *what* authorization rules apply — [scopes, roles, and fine-grained checks](0395-scopes-roles-fine-grained-authorization.md) — you still need to decide *where* those rules are evaluated. **Centralized authorization** puts the decision in one shared place (a gateway, a dedicated policy service) that every request passes through. **Decentralized authorization** pushes the decision into each individual service, which evaluates its own rules locally against its own request. Most real systems land somewhere in between, and understanding the trade-off is what lets you choose deliberately instead of by accident.

## 2. Why & when

This decision shapes how consistently rules are enforced, how fast decisions are made, and how hard the system is to change:

- **Centralized authorization** (e.g., checking permissions at the [API gateway](0382-edge-authentication-at-the-gateway.md), or via a dedicated Policy Decision Point like Open Policy Agent) gives you one place to see, audit, and update every rule — valuable when consistency and auditability matter more than raw latency, and especially valuable for coarse checks that don't need per-resource data.
- **Decentralized authorization** (each service enforces its own rules, often using data only it has, like resource ownership) is necessary the moment a decision depends on data a central point doesn't have easy access to — recall from [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md) that an ownership check needs the *order's* actual owner field, which lives inside the order service, not at the gateway.
- **A network call to a remote policy engine on every request** adds latency and a new failure mode (what happens if the policy service is down?) that a local, in-process check avoids — this pushes systems toward decentralizing at least the fine-grained layer even when they centralize the coarse layer.
- **Consistency risk** is the classic argument for centralizing: if every service implements its own version of "does this role allow this action," they inevitably drift — one service might forget a check entirely, or implement it slightly differently than its neighbor.

In practice, the choice usually isn't all-or-nothing: most systems centralize the coarse, cheap checks (authentication, scope, coarse role gates) at the edge, and decentralize the fine-grained, resource-specific checks into each service, matching the layered pattern from [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md).

## 3. Core concept

Think of airport security versus a company's individual office badge readers. Airport security (centralized) is one checkpoint everyone passes through once: it checks ID and boarding pass uniformly, using rules that don't depend on which specific gate you're headed to. Once past it, you still need your individual badge to get into each secure office (decentralized) — a check only that office can meaningfully make, because only that office knows who's actually authorized to be inside *it specifically*, today, for *this* meeting.

Three architectural patterns show up in practice:

1. **Gateway-enforced authorization.** The [API gateway](0382-edge-authentication-at-the-gateway.md) validates the token and checks coarse rules (scope, broad role) before a request is even routed to a backend service. Fast, consistent, but limited to whatever data the gateway itself has — typically just the token's claims.
2. **Policy Decision Point (PDP) / Policy Enforcement Point (PEP) pattern.** Each service (the PEP) sends the details of an authorization question to a centralized policy engine (the PDP — e.g., Open Policy Agent, evaluating rules written in Rego) and enforces whatever answer comes back. This centralizes the *rules* while keeping enforcement distributed, and lets you update policy in one place without redeploying every service.
3. **Fully decentralized, in-service checks.** Each service implements its own authorization logic in code, directly against its own data — the fine-grained ownership check from [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md) is a natural example, since only the order service can cheaply check "does this order belong to this user."

The trade-off in one sentence: centralizing buys consistency and a single audit point at the cost of coupling every service to a shared decision point (and its latency and availability); decentralizing buys speed and access to local data at the cost of rules that can silently diverge between services unless deliberately kept in sync.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Centralized: gateway checks scope once for every service. Decentralized: each service independently checks its own fine-grained rules against local data. Hybrid: gateway does the coarse check, each service does its own fine-grained check." font-family="sans-serif">
  <text x="150" y="20" fill="#e6edf3" font-size="11" text-anchor="middle">Centralized</text>
  <rect x="60" y="35" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="57" fill="#e6edf3" font-size="9" text-anchor="middle">Gateway: scope + role check</text>
  <rect x="20" y="100" width="70" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="55" y="120" fill="#e6edf3" font-size="8" text-anchor="middle">Order</text>
  <rect x="110" y="100" width="70" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="145" y="120" fill="#e6edf3" font-size="8" text-anchor="middle">Payment</text>
  <rect x="200" y="100" width="70" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="235" y="120" fill="#e6edf3" font-size="8" text-anchor="middle">Shipping</text>
  <text x="150" y="150" fill="#8b949e" font-size="8" text-anchor="middle">no fine-grained check -- trusts gateway</text>

  <text x="480" y="20" fill="#e6edf3" font-size="11" text-anchor="middle">Decentralized / hybrid</text>
  <rect x="400" y="35" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="57" fill="#e6edf3" font-size="9" text-anchor="middle">Gateway: coarse scope check</text>
  <rect x="400" y="100" width="80" height="50" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="440" y="120" fill="#e6edf3" font-size="8" text-anchor="middle">Order svc</text>
  <text x="440" y="135" fill="#8b949e" font-size="7" text-anchor="middle">+ own ownership check</text>
  <rect x="500" y="100" width="80" height="50" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="540" y="120" fill="#e6edf3" font-size="8" text-anchor="middle">Payment svc</text>
  <text x="540" y="135" fill="#8b949e" font-size="7" text-anchor="middle">+ own ownership check</text>
  <text x="490" y="175" fill="#f0883e" font-size="8" text-anchor="middle">each service adds its own fine-grained rule</text>
</svg>

A purely centralized model trusts the gateway's decision everywhere downstream; a hybrid model centralizes the coarse check but leaves each service responsible for checks that need its own local data.

## 5. Runnable example

Scenario: the same order-editing decision from [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md), now examined from the perspective of *where* the check runs. We simulate a fully centralized gateway check, then a policy-engine-backed hybrid, then a fully decentralized in-service check with a local policy cache for resilience.

### Level 1 — Basic

```java
// File: FullyCentralizedGateway.java -- the gateway makes the ENTIRE authorization
// decision using only the token's claims, and every downstream service blindly
// trusts whatever the gateway already decided.
import java.util.*;

public class FullyCentralizedGateway {
    record Token(String userId, Set<String> scopes, Set<String> roles) {}

    // The gateway's decision, based ONLY on the token -- it has no idea which order is involved.
    static boolean gatewayAllows(Token token) {
        return token.scopes().contains("orders:write") && token.roles().contains("ORDER_EDITOR");
    }

    // Downstream service does NOTHING further -- it trusts the gateway completely.
    static String orderServiceHandles(Token token, String orderId, boolean gatewayApproved) {
        if (!gatewayApproved) return "DENIED at gateway";
        return "ALLOWED (trusting gateway): '" + token.userId() + "' edited '" + orderId + "'";
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", Set.of("orders:write"), Set.of("ORDER_EDITOR"));
        boolean approved = gatewayAllows(aliceToken);
        // The gateway approved this because alice's TOKEN looks fine -- it never checked WHICH order.
        System.out.println(orderServiceHandles(aliceToken, "order-bob-99", approved));
    }
}
```

How to run: `java FullyCentralizedGateway.java`

`gatewayAllows` only ever sees the token — it has no access to order data, so it cannot possibly know that `order-bob-99` doesn't belong to alice. `orderServiceHandles` compounds the problem by trusting `gatewayApproved` unconditionally and performing no check of its own. The result: alice edits an order she doesn't own, because the one place capable of catching that (the order service, which holds the ownership data) never looked.

### Level 2 — Intermediate

```java
// File: PolicyEnginePDP.java -- a centralized POLICY ENGINE (PDP) is consulted
// for the decision, but the SERVICE (PEP) supplies resource-specific context
// (like the order's owner) as part of the request -- centralizing the RULES
// while keeping the resource DATA where it actually lives.
import java.util.*;

public class PolicyEnginePDP {
    record Token(String userId, Set<String> scopes, Set<String> roles) {}
    record PolicyRequest(String userId, Set<String> scopes, Set<String> roles, String action, String resourceOwnerId) {}

    // Simulated policy engine (e.g. Open Policy Agent) -- centralizes the RULE,
    // but is fed resource-specific facts by whichever service is asking.
    static boolean policyEngineDecides(PolicyRequest req) {
        boolean scopeOk = req.scopes().contains("orders:write");
        boolean roleOk = req.roles().contains("ORDER_EDITOR");
        boolean ownsResource = req.userId().equals(req.resourceOwnerId());
        return scopeOk && roleOk && ownsResource;
    }

    static final Map<String, String> ORDER_OWNERS = Map.of("order-alice-1", "alice", "order-bob-99", "bob");

    static String orderServiceHandles(Token token, String orderId) {
        String owner = ORDER_OWNERS.get(orderId);
        PolicyRequest req = new PolicyRequest(token.userId(), token.scopes(), token.roles(), "edit", owner);
        boolean allowed = policyEngineDecides(req);
        return allowed
                ? "ALLOWED: '" + token.userId() + "' edited '" + orderId + "' (policy engine approved, owner=" + owner + ")"
                : "DENIED: policy engine rejected '" + token.userId() + "' editing '" + orderId + "' (owner=" + owner + ")";
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", Set.of("orders:write"), Set.of("ORDER_EDITOR"));
        System.out.println(orderServiceHandles(aliceToken, "order-alice-1"));
        System.out.println(orderServiceHandles(aliceToken, "order-bob-99")); // correctly denied now
    }
}
```

How to run: `java PolicyEnginePDP.java`

`orderServiceHandles` still asks a centralized decision point (`policyEngineDecides`), but this time it first looks up `ORDER_OWNERS.get(orderId)` — data only the order service has — and passes it *into* the policy request. `policyEngineDecides` centralizes the rule ("scope AND role AND ownership") in one auditable place, but the resource-specific fact (`resourceOwnerId`) travels with the request rather than living inside the policy engine itself. This closes the Level 1 gap: alice editing bob's order is now correctly denied, because the policy engine was actually given the ownership fact needed to catch it.

### Level 3 — Advanced

```java
// File: DecentralizedWithFallbackPolicy.java -- the order-service now enforces
// its OWN fine-grained rule locally (fully decentralized for this specific
// check), while still respecting a centrally-DEFINED role policy that it
// caches locally -- so a remote policy engine outage doesn't take down
// authorization entirely (graceful degradation).
import java.util.*;

public class DecentralizedWithFallbackPolicy {
    record Token(String userId, Set<String> scopes, Set<String> roles) {}
    record Order(String orderId, String ownerId) {}

    static final Map<String, Order> ORDERS = Map.of(
            "order-alice-1", new Order("order-alice-1", "alice"),
            "order-bob-99", new Order("order-bob-99", "bob"));

    // A LOCAL cache of the centrally-defined role policy -- refreshed periodically
    // from the central policy service, but usable even if that service is unreachable.
    static final Set<String> CACHED_ROLES_ALLOWED_TO_EDIT = Set.of("ORDER_EDITOR", "ADMIN");

    static boolean remotePolicyEngineReachable = false; // simulate an outage

    static String orderServiceHandles(Token token, String orderId) {
        if (!token.scopes().contains("orders:write")) return "DENIED: missing scope";

        boolean roleOk;
        String source;
        if (remotePolicyEngineReachable) {
            roleOk = callRemotePolicyEngine(token); // would be the authoritative source, normally
            source = "remote policy engine";
        } else {
            // Fall back to the local cache instead of failing open OR failing every request.
            roleOk = token.roles().stream().anyMatch(CACHED_ROLES_ALLOWED_TO_EDIT::contains);
            source = "LOCAL CACHE (remote policy engine unreachable)";
        }
        if (!roleOk) return "DENIED: role check failed via " + source;

        // Ownership is ALWAYS checked locally -- only this service has the order data.
        Order order = ORDERS.get(orderId);
        if (order == null || !order.ownerId().equals(token.userId())) {
            return "DENIED: '" + token.userId() + "' does not own '" + orderId + "' (checked locally, via " + source + " for role)";
        }
        return "ALLOWED: '" + token.userId() + "' edited '" + orderId + "' (role via " + source + ", ownership checked locally)";
    }

    static boolean callRemotePolicyEngine(Token token) {
        throw new IllegalStateException("should not be called when remotePolicyEngineReachable is false");
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", Set.of("orders:write"), Set.of("ORDER_EDITOR"));
        System.out.println(orderServiceHandles(aliceToken, "order-alice-1"));
        System.out.println(orderServiceHandles(aliceToken, "order-bob-99"));
    }
}
```

How to run: `java DecentralizedWithFallbackPolicy.java`

`orderServiceHandles` first checks scope locally (cheap, always available from the token). It then attempts the role decision via the "remote policy engine," but since `remotePolicyEngineReachable` is `false`, it falls back to `CACHED_ROLES_ALLOWED_TO_EDIT` — a locally cached snapshot of the centrally-defined policy, kept fresh by periodic sync in a real system. This means an outage of the central policy engine degrades to "decisions based on the last known-good policy" rather than either failing every request (unavailable) or, worse, failing open and allowing everything. The ownership check, by contrast, is *never* delegated to any remote system — it's inherently local, because only the order service holds `ORDERS`.

## 6. Walkthrough

Trace `DecentralizedWithFallbackPolicy.main` for `orderServiceHandles(aliceToken, "order-bob-99")`. **First**, `token.scopes().contains("orders:write")` is checked against `aliceToken` — `true`, so this passes.

**Next**, since `remotePolicyEngineReachable` is `false`, the code takes the fallback branch: `roleOk = token.roles().stream().anyMatch(CACHED_ROLES_ALLOWED_TO_EDIT::contains)`. `aliceToken.roles()` is `{"ORDER_EDITOR"}`, and `CACHED_ROLES_ALLOWED_TO_EDIT` contains `"ORDER_EDITOR"` — so `roleOk` is `true`, decided entirely from the local cache, with `source` set to the fallback message.

**Then**, since `roleOk` is `true`, execution reaches the ownership check. `ORDERS.get("order-bob-99")` returns `Order("order-bob-99", "bob")`. `order.ownerId().equals(token.userId())` evaluates `"bob".equals("alice")`, which is `false` — so the condition `order == null || !order.ownerId().equals(...)` is `true`, and the method returns a DENIED message naming both the caller and the fact this was checked locally.

**Finally**, note what *didn't* happen: even though the central policy engine was unreachable, alice was still correctly blocked from editing bob's order, because that specific check never depended on the remote system in the first place. Compare this to `orderServiceHandles(aliceToken, "order-alice-1")`, which passes the same scope and (cached) role checks, then finds `order.ownerId().equals("alice")` is `true` and returns ALLOWED.

```
ALLOWED: 'alice' edited 'order-alice-1' (role via LOCAL CACHE (remote policy engine unreachable), ownership checked locally)
DENIED: 'alice' does not own 'order-bob-99' (checked locally, via LOCAL CACHE (remote policy engine unreachable) for role)
```

## 7. Gotchas & takeaways

> A dangerous failure mode for centralized authorization is "fail open" — if the central policy service becomes unreachable and services are coded to allow requests through rather than block them (often to avoid an outage), a policy-engine outage silently becomes a total authorization bypass. Level 3's local-cache fallback is one defensible middle ground: it degrades to "the last known-good policy" instead of either extreme, but it still requires deliberately deciding, in advance, what a stale cache is allowed to authorize.

- Centralized authorization (gateway checks, a policy engine) buys consistency and a single audit point, at the cost of coupling every request to a shared decision point's availability and latency.
- Decentralized, in-service checks are necessary whenever a decision depends on data only that service has — resource ownership being the clearest example.
- The PDP/PEP pattern (a central policy engine, fed resource-specific facts by each service) is a common middle ground: it centralizes *rules* while keeping resource *data* where it lives.
- Plan explicitly for what happens when a centralized decision point is unreachable — fail closed, fail to a cached policy, or accept a real availability trade-off; don't let it default to fail-open by accident.
- This decision sits directly on top of [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md): that topic defines *what* gets checked, this one decides *where* each check physically runs.
