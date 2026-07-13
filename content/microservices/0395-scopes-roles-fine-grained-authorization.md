---
card: microservices
gi: 395
slug: scopes-roles-fine-grained-authorization
title: "Scopes, roles & fine-grained authorization"
---

## 1. What it is

Once a caller's identity is established — through [service-to-service authentication](0391-service-to-service-authentication.md) or a user's OAuth2 token — the next question is *what is this identity allowed to do*. **Scopes**, **roles**, and **fine-grained authorization** are three increasingly precise ways of answering that question. A **scope** is a coarse, token-level grant of permission ("this token can do `orders:write`"). A **role** groups a bundle of permissions under a named identity a user or service is assigned to ("this user is an `ADMIN`"). **Fine-grained authorization** goes further still, evaluating a specific rule against a specific resource instance ("this user may edit *this particular* order, because they own it").

## 2. Why & when

You need to move beyond coarse checks the moment "is this caller authenticated?" stops being a sufficient answer:

- **Scopes** are the natural next step after authentication in an OAuth2 system — they answer "what category of action was this *token* issued to perform?" (see [OAuth2 grant types](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md)), and they travel with the token itself, checked cheaply at the API boundary.
- **Roles** are the natural fit when permissions cluster into stable job-function bundles — an `ADMIN` role bundles many permissions a human administrator needs, so you don't have to grant and check dozens of individual scopes one at a time.
- **Fine-grained (attribute- or relationship-based) authorization** becomes necessary the moment "can do X" depends on *which specific resource* is involved — "can edit orders" isn't the same question as "can edit *this* order," and only the second one prevents user alice from editing user bob's order just because both are `ORDER_EDITOR`s.

Most real systems layer all three: a broad scope gets you past the API gateway, a role determines which categories of endpoint you can reach, and a fine-grained, resource-level check at the point of action confirms you're allowed to touch *this specific* record.

## 3. Core concept

Think of a hospital's access system. A **scope** is like the type of badge you were issued — "clinical staff badge" versus "billing staff badge" — checked once at the building entrance. A **role** is your job title on that badge — "nurse," "attending physician," "billing clerk" — which determines which floors and departments you can enter. **Fine-grained authorization** is the final check at a specific patient's door: even a nurse with full building and floor access can only view *this patient's* chart if they're actually assigned to that patient's care team right now — a check that depends on the specific patient, not just the nurse's badge or job title.

Concretely, three overlapping models cover most systems:

1. **OAuth2 scopes** — attached to the access token itself (e.g., `orders:read`, `orders:write`), checked as a fast, coarse gate before any business logic runs. Scopes describe what the *token* is allowed to request, independent of which specific resources exist.
2. **Role-Based Access Control (RBAC)** — a user or service is assigned one or more roles (`ADMIN`, `EDITOR`, `VIEWER`), and each role maps to a set of permissions. Simple to reason about and administer, but coarse: everyone with a role gets identical access to *every* resource that role covers.
3. **Attribute-/Relationship-Based Access Control (ABAC / ReBAC)** — the authorization decision considers attributes of the *specific* resource and the relationship between the caller and that resource (ownership, team membership, department) — e.g., "allow if `resource.ownerId == caller.userId`," or "allow if caller is a member of `resource.teamId`." This is what closes the gap RBAC alone can't: two users with the identical role can still get different answers for the identical action on different resource instances.

The general pattern is: check the cheapest, coarsest thing first (scope, at the gateway or filter chain), then progressively narrow to the specific resource only when the coarse check passes — avoiding an expensive per-resource lookup for every request that was never going to be allowed anyway.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three layered authorization checks: scope check at the gateway, role check at the service, and fine-grained ownership check at the specific resource, each narrowing the decision further" font-family="sans-serif">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="40" fill="#e6edf3" font-size="10" text-anchor="middle">1. Scope check (token)</text>
  <text x="110" y="55" fill="#8b949e" font-size="9" text-anchor="middle">token has orders:write?</text>

  <rect x="230" y="90" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="110" fill="#e6edf3" font-size="10" text-anchor="middle">2. Role check (service)</text>
  <text x="320" y="125" fill="#8b949e" font-size="9" text-anchor="middle">user has EDITOR role?</text>

  <rect x="440" y="160" width="180" height="60" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="182" fill="#e6edf3" font-size="10" text-anchor="middle">3. Fine-grained check</text>
  <text x="530" y="198" fill="#8b949e" font-size="9" text-anchor="middle">order.ownerId == user.id?</text>
  <text x="530" y="212" fill="#8b949e" font-size="8" text-anchor="middle">(this specific resource)</text>

  <line x1="200" y1="45" x2="230" y2="100" stroke="#8b949e" marker-end="url(#fg)"/>
  <line x1="410" y1="115" x2="440" y2="175" stroke="#8b949e" marker-end="url(#fg)"/>
  <text x="320" y="245" fill="#6db33f" font-size="9" text-anchor="middle">coarse, cheap, first --&gt; specific, expensive, last</text>
  <defs>
    <marker id="fg" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Authorization typically layers from coarse and cheap (does the token carry the right scope) to specific and precise (does this user own this exact resource), each stage narrowing the decision further.

## 5. Runnable example

Scenario: an order-editing endpoint. We layer scope checking, then role checking, then a fine-grained ownership check, so that the same "edit order" request is progressively narrowed from "is this generally allowed" to "is this allowed for this specific order."

### Level 1 — Basic

```java
// File: ScopeOnlyCheck.java -- authorization based SOLELY on the token's scope.
// Any caller with 'orders:write' can edit ANY order, regardless of who they are.
import java.util.*;

public class ScopeOnlyCheck {
    record Token(String userId, Set<String> scopes) {}

    static String editOrder(Token token, String orderId) {
        if (!token.scopes().contains("orders:write")) {
            return "DENIED: token lacks 'orders:write' scope";
        }
        return "ALLOWED: '" + token.userId() + "' edited order '" + orderId + "' -- scope check only";
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", Set.of("orders:write"));
        System.out.println(editOrder(aliceToken, "order-alice-1"));
        // alice's token ALSO lets her edit an order she has nothing to do with.
        System.out.println(editOrder(aliceToken, "order-bob-99"));
    }
}
```

How to run: `java ScopeOnlyCheck.java`

`editOrder` checks only whether the token carries `orders:write`. Both calls succeed identically, including alice editing `order-bob-99` — a scope proves the *token* was issued with a certain permission category, but says nothing about which specific orders alice should actually be allowed to touch.

### Level 2 — Intermediate

```java
// File: ScopeAndRoleCheck.java -- adds an RBAC role check on top of scope.
// Roles narrow WHO can reach the endpoint at all, but a role is still
// resource-agnostic: every EDITOR can edit every order.
import java.util.*;

public class ScopeAndRoleCheck {
    record Token(String userId, Set<String> scopes, Set<String> roles) {}

    static String editOrder(Token token, String orderId) {
        if (!token.scopes().contains("orders:write")) return "DENIED: missing scope";
        if (!token.roles().contains("ORDER_EDITOR")) return "DENIED: missing ORDER_EDITOR role";
        return "ALLOWED: '" + token.userId() + "' edited order '" + orderId + "' -- scope + role, still resource-agnostic";
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", Set.of("orders:write"), Set.of("ORDER_EDITOR"));
        Token guestToken = new Token("mallory", Set.of("orders:write"), Set.of("GUEST"));

        System.out.println(editOrder(aliceToken, "order-alice-1"));
        System.out.println(editOrder(guestToken, "order-alice-1"));   // right scope, wrong role
        // alice has the right SCOPE and the right ROLE -- but this order belongs to someone else entirely.
        System.out.println(editOrder(aliceToken, "order-bob-99"));
    }
}
```

How to run: `java ScopeAndRoleCheck.java`

`editOrder` now requires both `orders:write` scope *and* the `ORDER_EDITOR` role. `guestToken` is correctly rejected — it has the scope but the wrong role. But alice's call against `order-bob-99` still succeeds: her role, `ORDER_EDITOR`, applies uniformly to every order in the system, not just her own. RBAC has narrowed *who* can reach this endpoint, but not *which resources* they can act on once they're there.

### Level 3 — Advanced

```java
// File: FineGrainedOwnershipCheck.java -- adds a resource-level check: even
// with the right scope AND role, the caller must actually OWN (or be granted
// access to) the SPECIFIC order being edited. This is what finally prevents
// alice from editing bob's order.
import java.util.*;

public class FineGrainedOwnershipCheck {
    record Token(String userId, Set<String> scopes, Set<String> roles) {}
    record Order(String orderId, String ownerId, Set<String> sharedWithUserIds) {}

    static final Map<String, Order> ORDERS = Map.of(
            "order-alice-1", new Order("order-alice-1", "alice", Set.of()),
            "order-bob-99", new Order("order-bob-99", "bob", Set.of("carol")) // bob shared this order with carol
    );

    static String editOrder(Token token, String orderId) {
        if (!token.scopes().contains("orders:write")) return "DENIED: missing scope";
        if (!token.roles().contains("ORDER_EDITOR")) return "DENIED: missing ORDER_EDITOR role";

        Order order = ORDERS.get(orderId);
        if (order == null) return "DENIED: order not found";

        boolean isOwner = order.ownerId().equals(token.userId());
        boolean isSharedWith = order.sharedWithUserIds().contains(token.userId());
        if (!isOwner && !isSharedWith) {
            return "DENIED: '" + token.userId() + "' does not own or have access to '" + orderId + "'";
        }
        return "ALLOWED: '" + token.userId() + "' edited '" + orderId + "' (owner=" + isOwner + ", shared=" + isSharedWith + ")";
    }

    public static void main(String[] args) {
        Token aliceToken = new Token("alice", Set.of("orders:write"), Set.of("ORDER_EDITOR"));
        Token carolToken = new Token("carol", Set.of("orders:write"), Set.of("ORDER_EDITOR"));

        System.out.println(editOrder(aliceToken, "order-alice-1"));   // alice owns this order
        System.out.println(editOrder(aliceToken, "order-bob-99"));    // alice does NOT own or share this order -- now correctly denied
        System.out.println(editOrder(carolToken, "order-bob-99"));    // carol was explicitly shared this order by bob
    }
}
```

How to run: `java FineGrainedOwnershipCheck.java`

`Order` now records both an `ownerId` and a `sharedWithUserIds` set, modeling a real per-resource access-control list. `editOrder` performs the scope and role checks exactly as before, then adds a third, resource-specific check: is the caller the order's owner, or has the owner explicitly shared it with them? Alice editing her own order succeeds on ownership. Alice's identical call against `order-bob-99` — which passed both the scope and role checks in Level 2 — is now correctly denied, because neither ownership nor a share applies. Carol, despite never being the owner, is allowed in specifically because bob shared this order with her — a decision that depends entirely on this one resource's data, not on any property of carol's token alone.

## 6. Walkthrough

Trace `FineGrainedOwnershipCheck.main` in order. **First**, `editOrder(aliceToken, "order-alice-1")` runs. The scope check passes (`orders:write` present), the role check passes (`ORDER_EDITOR` present). `ORDERS.get("order-alice-1")` returns an `Order` with `ownerId = "alice"`. `isOwner` evaluates `"alice".equals("alice")`, which is `true`. Since `isOwner` is `true`, the denial branch is skipped, and the method returns an ALLOWED message with `owner=true, shared=false`.

**Next**, `editOrder(aliceToken, "order-bob-99")` runs. Scope and role checks pass identically — alice's token hasn't changed. `ORDERS.get("order-bob-99")` returns an `Order` with `ownerId = "bob"` and `sharedWithUserIds = {"carol"}`. `isOwner` evaluates `"bob".equals("alice")`, which is `false`. `isSharedWith` evaluates `{"carol"}.contains("alice")`, also `false`. Both are false, so the denial branch fires: `"DENIED: 'alice' does not own or have access to 'order-bob-99'"` — the exact gap Level 2 left open, now closed.

**Finally**, `editOrder(carolToken, "order-bob-99")` runs. Scope and role checks pass for carol's token. The same `Order` for `order-bob-99` is fetched. `isOwner` is `"bob".equals("carol")`, `false`. `isSharedWith` is `{"carol"}.contains("carol")`, `true`. Since `isSharedWith` is `true`, the method proceeds to ALLOWED, printing `owner=false, shared=true` — carol's access is legitimate, but for a different reason than ownership.

```
ALLOWED: 'alice' edited 'order-alice-1' (owner=true, shared=false)
DENIED: 'alice' does not own or have access to 'order-bob-99'
ALLOWED: 'carol' edited 'order-bob-99' (owner=false, shared=true)
```

## 7. Gotchas & takeaways

> A very common production bug is stopping at the RBAC layer and assuming "the user has the right role" is equivalent to "the user is allowed to touch this resource." It works fine in testing (where a developer's test user often owns every test resource) and then fails, silently, as a real authorization bypass the first time two different customers' data lives in the same role-protected endpoint — exactly what Level 2 demonstrates with alice and `order-bob-99`.

- Scopes are a coarse, token-level gate — cheap to check, but blind to which specific resources exist.
- Roles (RBAC) group permissions for administrability, but every holder of a role gets identical access to every resource that role covers unless a further check narrows it.
- Fine-grained (ABAC/ReBAC) checks — ownership, sharing, team membership — are what actually prevent one user from acting on another user's data when both share a role.
- Layer these checks from cheapest to most specific: reject on scope or role before ever querying resource-specific data, so most unauthorized requests never reach the expensive check.
- This connects directly to [centralized vs decentralized authorization](0396-centralized-vs-decentralized-authorization.md), which covers *where* these checks should physically live — at the gateway, in each service, or in a dedicated policy engine — and to [OAuth2 roles](0386-oauth2-roles-resource-owner-client-auth-server-resource-serv.md) for how scopes fit into the broader OAuth2 model.
