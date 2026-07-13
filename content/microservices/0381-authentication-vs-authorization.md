---
card: microservices
gi: 381
slug: authentication-vs-authorization
title: "Authentication vs authorization"
---

## 1. What it is

**Authentication** answers "who are you?" — it's the process of proving an identity, typically by checking a password, a signed token, or a certificate. **Authorization** answers "what are you allowed to do?" — it's the process of deciding, once identity is known, whether that identity may perform a specific action on a specific resource. They're two distinct steps that always happen in that order: you can't authorize someone whose identity you haven't established, but establishing identity alone tells you nothing about what they're permitted to do next.

## 2. Why & when

Every secured endpoint in a microservices system needs both steps, and conflating them is one of the most common security mistakes teams make. You need to reason about them separately because:

- **They fail differently.** An authentication failure means "I don't know who you are" (typically a `401 Unauthorized` response). An authorization failure means "I know who you are, but you can't do this" (typically a `403 Forbidden` response). Returning the wrong status code, or worse, silently allowing an action because *some* check passed, is a real and common bug class.
- **They're checked at different points.** Authentication usually happens once per request (or once per session/token issuance), often at the edge — see [edge authentication at the gateway](0382-edge-authentication-at-the-gateway.md). Authorization often needs to happen again inside the specific service, because the gateway may know *who* is calling without knowing the fine-grained business rule about *what* that caller may touch (e.g., "can this specific customer view this specific order?").
- **They compose with [zero-trust networking](0380-zero-trust-networking.md) and [defense in depth](0379-defense-in-depth.md).** A system that authenticates well at the edge but never re-checks authorization deeper in the call chain has effectively verified identity once and then trusted it blindly everywhere after — exactly the failure those two topics warn about.

You need this distinction the moment you design any secured operation: first prove identity, then separately decide what that identity may do.

## 3. Core concept

Think of a company office building. Showing your badge to the security guard at the front desk is **authentication** — it proves you are who your badge says you are. Once inside, whether you can enter the finance department, the server room, or just the break room is **authorization** — a separate decision based on your role, made at each door you approach, not just once at the front desk. A valid badge gets you *into the building*; it does not automatically open every door inside it.

Breaking this down further:

1. **Authentication mechanisms** prove identity: a password check, a signed [JWT](0384-json-web-token-jwt-structure-validation.md), a client certificate in [mTLS](0392-mutual-tls-mtls.md), or an [opaque token validated via introspection](0385-opaque-tokens-token-introspection.md). The output of authentication is a *principal* — a known, verified identity (a user, or a service).
2. **Authorization mechanisms** decide permission for that principal: role checks ("is this user an admin?"), scope checks ("does this token include the `orders:read` scope?"), or fine-grained rules ("does this user own this specific order?"). The output of authorization is a yes/no decision for a specific action.
3. **Order matters, always.** Authorization logic that runs before identity is established has nothing meaningful to check permissions *against* — there's no principal yet to evaluate a role or scope for.
4. **Both can happen at multiple layers.** A gateway might authenticate a user and check a coarse-grained scope; a downstream service might re-check a fine-grained, data-specific rule that only it has enough context to enforce. This layering is exactly what [defense in depth](0379-defense-in-depth.md) recommends: don't concentrate every check in one place.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request first passes through authentication, which establishes identity, then through authorization, which checks permission for that identity; failing either step produces a different response code" font-family="sans-serif">
  <rect x="20" y="90" width="120" height="60" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="80" y="124" fill="#e6edf3" font-size="11" text-anchor="middle">Request +
    credential</text>

  <rect x="200" y="70" width="140" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="270" y="95" fill="#79c0ff" font-size="11" text-anchor="middle">Authentication</text>
  <text x="270" y="112" fill="#8b949e" font-size="9" text-anchor="middle">"who are you?"</text>
  <text x="270" y="128" fill="#8b949e" font-size="9" text-anchor="middle">verify token/cert</text>
  <text x="270" y="150" fill="#f85149" font-size="9" text-anchor="middle">fail -&gt; 401</text>

  <rect x="400" y="70" width="140" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="470" y="95" fill="#6db33f" font-size="11" text-anchor="middle">Authorization</text>
  <text x="470" y="112" fill="#8b949e" font-size="9" text-anchor="middle">"what can you do?"</text>
  <text x="470" y="128" fill="#8b949e" font-size="9" text-anchor="middle">check role/scope</text>
  <text x="470" y="150" fill="#f85149" font-size="9" text-anchor="middle">fail -&gt; 403</text>

  <rect x="580" y="90" width="50" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="605" y="124" fill="#6db33f" font-size="10" text-anchor="middle">200</text>

  <line x1="140" y1="120" x2="200" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="340" y1="120" x2="400" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="540" y1="120" x2="580" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>
  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
  <text x="270" y="210" fill="#8b949e" font-size="10" text-anchor="middle">identity established first</text>
  <text x="470" y="210" fill="#8b949e" font-size="10" text-anchor="middle">then permission decided</text>
</svg>

Authentication establishes who is calling; authorization then, separately, decides what that established identity may do — and each step fails with its own distinct response code.

## 5. Runnable example

Scenario: an endpoint that lets a user view an order. We'll build it with no separation at all first, then split authentication from authorization cleanly, then add a fine-grained ownership rule that only the service itself can enforce.

### Level 1 — Basic

```java
// File: NoSeparation.java -- conflates "is there a token at all" with
// "is this allowed" into a single vague check. A common but sloppy pattern.
public class NoSeparation {
    static String viewOrder(String token, String orderId) {
        // ONE check does everything: is there any non-empty token?
        if (token == null || token.isEmpty()) {
            return "DENIED"; // could mean "not authenticated" OR "not authorized" -- unclear which
        }
        return "Order " + orderId + " details returned";
    }

    public static void main(String[] args) {
        System.out.println(viewOrder(null, "order-1"));          // no token at all
        System.out.println(viewOrder("valid-token", "order-1")); // any token -- gets in, no permission check at all
    }
}
```

How to run: `java NoSeparation.java`

`viewOrder` treats "having a token" as sufficient for everything. It never establishes *who* the token belongs to, and never checks *whether* that identity is allowed to view this particular order. Any caller with any non-empty string gets full access — this is the failure mode that authentication/authorization separation exists to prevent.

### Level 2 — Intermediate

```java
// File: SeparatedAuthnAuthz.java -- splits the two concerns cleanly: authentication
// establishes a principal (or fails with 401-style rejection), authorization then
// separately checks that principal's role (or fails with 403-style rejection).
import java.util.*;

public class SeparatedAuthnAuthz {
    static final Map<String, String> VALID_TOKENS = Map.of(
            "token-alice", "alice",
            "token-bob", "bob"
    );
    static final Map<String, String> ROLES = Map.of(
            "alice", "customer",
            "bob", "customer-service-agent"
    );

    // Step 1: AUTHENTICATION -- who is this?
    static String authenticate(String token) {
        return VALID_TOKENS.get(token); // null if the token doesn't map to anyone
    }

    // Step 2: AUTHORIZATION -- is this identity allowed to view ANY order?
    static boolean authorizeViewOrders(String username) {
        String role = ROLES.get(username);
        return "customer".equals(role) || "customer-service-agent".equals(role);
    }

    static String viewOrder(String token, String orderId) {
        String username = authenticate(token);
        if (username == null) {
            return "401: not authenticated -- token did not resolve to any identity";
        }
        if (!authorizeViewOrders(username)) {
            return "403: authenticated as '" + username + "' but not authorized to view orders";
        }
        return "200: order " + orderId + " returned to authenticated, authorized user '" + username + "'";
    }

    public static void main(String[] args) {
        System.out.println(viewOrder("bad-token", "order-1"));  // fails authentication
        System.out.println(viewOrder("token-alice", "order-1")); // authenticates AND authorizes
    }
}
```

How to run: `java SeparatedAuthnAuthz.java`

`authenticate` and `authorizeViewOrders` are now two distinct methods, called in order. A bad token fails at the authentication step and returns a `401`-style result before authorization is ever considered — there's no identity yet to check a role for. A valid token resolves to `"alice"`, whose role (`"customer"`) is then separately checked and permitted, returning `200`. Notice authentication and authorization now produce genuinely different failure messages, which is exactly the distinction Level 1 erased.

### Level 3 — Advanced

```java
// File: FineGrainedAuthorization.java -- adds a coarse-grained role check (can this
// role view orders AT ALL) plus a fine-grained, data-specific ownership check (can
// THIS user view THIS SPECIFIC order) -- the kind of rule only the service itself
// has enough context to enforce, even after the gateway already authenticated the caller.
import java.util.*;

public class FineGrainedAuthorization {
    static final Map<String, String> VALID_TOKENS = Map.of("token-alice", "alice", "token-bob", "bob");
    static final Map<String, String> ROLES = Map.of("alice", "customer", "bob", "customer-service-agent");
    // Which customer owns which order -- only the order service knows this.
    static final Map<String, String> ORDER_OWNER = Map.of("order-1", "alice", "order-2", "carol");

    static String authenticate(String token) {
        return VALID_TOKENS.get(token);
    }

    static boolean hasOrdersRole(String username) {
        String role = ROLES.get(username);
        return "customer".equals(role) || "customer-service-agent".equals(role);
    }

    // Fine-grained rule: customers may ONLY view their own orders; agents may view ANY order.
    static boolean canViewSpecificOrder(String username, String orderId) {
        String role = ROLES.get(username);
        if ("customer-service-agent".equals(role)) return true; // agents: broader authorization
        return username.equals(ORDER_OWNER.get(orderId));       // customers: must own the order
    }

    static String viewOrder(String token, String orderId) {
        String username = authenticate(token);
        if (username == null) return "401: not authenticated";
        if (!hasOrdersRole(username)) return "403: '" + username + "' has no orders-viewing role at all";
        if (!canViewSpecificOrder(username, orderId)) {
            return "403: '" + username + "' is authorized to view orders in general, but NOT order " + orderId;
        }
        return "200: order " + orderId + " returned to '" + username + "'";
    }

    public static void main(String[] args) {
        System.out.println(viewOrder("token-alice", "order-1")); // alice owns order-1 -- allowed
        System.out.println(viewOrder("token-alice", "order-2")); // alice does NOT own order-2 -- denied
        System.out.println(viewOrder("token-bob", "order-2"));   // bob is an agent -- allowed on ANY order
    }
}
```

How to run: `java FineGrainedAuthorization.java`

This adds a second, more specific authorization check on top of the coarse role check. `hasOrdersRole` answers "can this identity view orders as a category at all?" — a check a gateway could plausibly make with just the role claim from a token. `canViewSpecificOrder` answers a question the gateway *cannot* answer, because it requires business data (who owns which order) that only the order service holds. Alice, a customer, is allowed to see her own order but denied on someone else's, even though she passed both authentication and the coarse role check — demonstrating why fine-grained authorization often has to live in the service itself, not just at the edge.

## 6. Walkthrough

Trace `FineGrainedAuthorization.main` in order. **First**, `viewOrder("token-alice", "order-1")` runs. `authenticate("token-alice")` resolves to `"alice"` — authentication succeeds. `hasOrdersRole("alice")` looks up `ROLES.get("alice")` (`"customer"`), which qualifies — coarse authorization succeeds. `canViewSpecificOrder("alice", "order-1")` checks the role again: not an agent, so it falls to `"alice".equals(ORDER_OWNER.get("order-1"))`, and `ORDER_OWNER.get("order-1")` is `"alice"` — true. All checks pass, and `"200: order order-1 returned to 'alice'"` is printed.

**Next**, `viewOrder("token-alice", "order-2")` runs. Authentication and the coarse role check pass identically to before — alice is still a known, role-qualified customer. But `canViewSpecificOrder("alice", "order-2")` now checks `"alice".equals(ORDER_OWNER.get("order-2"))`, and `ORDER_OWNER.get("order-2")` is `"carol"`, not `"alice"` — false. The fine-grained check denies the request with a `403`, even though every earlier check passed.

**Then**, `viewOrder("token-bob", "order-2")` runs. `authenticate` resolves `"bob"`. `hasOrdersRole("bob")` passes (`"customer-service-agent"` qualifies). `canViewSpecificOrder("bob", "order-2")` checks the role first: it *is* `"customer-service-agent"`, so the method returns `true` immediately without even consulting `ORDER_OWNER` — agents bypass the ownership rule by design, because their role grants broader access.

```
alice + order-1 (owns it)      -> 200 returned
alice + order-2 (doesn't own)  -> 403 (fine-grained ownership check fails)
bob   + order-2 (is an agent)  -> 200 returned (role grants broader access)
```

## 7. Gotchas & takeaways

> A very common bug is conflating a `401` and a `403` into one generic "denied" response, as Level 1 does. This isn't just a UX nitpick — it also affects security tooling and client behavior. A `401` tells a client "retry with a fresh credential"; a `403` tells it "this identity will never be allowed, don't bother retrying." Collapsing them into one status can cause clients to retry authorization failures pointlessly, or worse, cause monitoring to miss a spike in *authentication* failures (a possible credential-stuffing attack) because it's buried under routine, expected authorization denials.

- Authentication proves identity; authorization decides permission for that identity — always in that order, never merged into one vague check.
- Coarse-grained authorization (role/scope checks) can often happen at the [gateway](0382-edge-authentication-at-the-gateway.md); fine-grained, data-specific authorization (like ownership) usually has to happen inside the service that holds the relevant data.
- Use distinct response codes: `401` means "I don't know who you are," `403` means "I know who you are, and the answer is no."
- Re-checking authorization inside each service, even after the gateway already authenticated the caller, is a direct application of [defense in depth](0379-defense-in-depth.md) and [zero-trust networking](0380-zero-trust-networking.md).
- Tokens like [JWTs](0384-json-web-token-jwt-structure-validation.md) often carry both identity claims (for authentication) and scope/role claims (for coarse authorization) in the same payload — but that doesn't mean fine-grained checks can be skipped.
