---
card: microservices
gi: 404
slug: method-security-preauthorize-postauthorize
title: "Method security (@PreAuthorize, @PostAuthorize)"
---

## 1. What it is

**Method security** is Spring Security's mechanism for enforcing authorization rules at the level of an individual Java method, rather than only at the URL level via `authorizeHttpRequests` in a [`SecurityFilterChain`](0400-spring-security-core-filters-authentication-authorization.md). Enabled with `@EnableMethodSecurity`, it uses annotations — most commonly `@PreAuthorize` and `@PostAuthorize` — evaluated via Spring AOP just before or after a method actually runs, letting authorization rules reference the method's own arguments and return value, not just the HTTP request that triggered it.

## 2. Why & when

You reach for method security whenever URL-pattern authorization alone can't express the rule you actually need:

- **Ownership checks require data the URL doesn't carry.** `GET /orders/{id}` being authenticated tells you nothing about whether *this specific caller* owns *this specific order* — that requires looking at the loaded entity, which only the method body (or its return value) has access to.
- **Service-layer methods are called from more than one entry point.** A `OrderService.cancel(orderId)` method might be invoked from a REST controller, a scheduled job, or an internal message listener — putting the authorization rule on the method itself, rather than duplicating it in every caller, guarantees it's enforced everywhere.
- **Defense in depth.** Even if a controller-level check is correct today, a future refactor that adds a new call path bypasses it entirely unless the rule also lives closer to the data — method security is a second layer, consistent with [defense in depth](0379-defense-in-depth.md).
- **Fine-grained scope and role logic** built on the same `Authentication`/authorities model covered in [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md), but expressed as a Spring Expression Language (SpEL) condition evaluated right next to the method it protects.

You need this the moment "is this request authenticated with the right role" (URL-level) stops being precise enough and the real question becomes "does *this* caller have the right to act on *this specific piece of data*."

## 3. Core concept

Think of URL-level authorization as a building's front-desk security guard, checking a badge before letting anyone onto a floor — coarse-grained, fast, and blind to what happens once you're inside. Method security is like a second guard stationed at each individual office door on that floor, who additionally checks "is this specific visitor allowed into *this specific* office" — a decision that depends on details (whose office it is) the front desk never had.

The essential pieces:

1. **`@EnableMethodSecurity`** — turns on annotation-driven method security via Spring AOP proxies; without it, `@PreAuthorize`/`@PostAuthorize` annotations are silently ignored.

```java
@Configuration
@EnableMethodSecurity  // enables @PreAuthorize, @PostAuthorize, @PreFilter, @PostFilter
public class MethodSecurityConfig { }
```

2. **`@PreAuthorize`** — a SpEL expression evaluated *before* the method runs; if it evaluates to `false`, the method body never executes and an `AccessDeniedException` is thrown instead.

```java
@PreAuthorize("hasAuthority('SCOPE_orders:write')")
public Order cancel(String orderId) { ... }

@PreAuthorize("#orderId == authentication.name or hasRole('ADMIN')")
public Order getOrder(String orderId) { ... }
```

3. **`@PostAuthorize`** — a SpEL expression evaluated *after* the method returns, with access to the return value via `returnObject`; if it evaluates to `false`, the return value is discarded and an `AccessDeniedException` is thrown instead — useful exactly when the authorization decision depends on data only the method itself can produce (e.g., loading an entity to check its owner field).

```java
@PostAuthorize("returnObject.ownerId == authentication.name")
public Order getOrder(String orderId) { ... } // must load the order to know its owner
```

4. **`@PreFilter` / `@PostFilter`** — related annotations that filter a collection argument or return value down to only the elements the caller is authorized to see, rather than rejecting the whole call outright.

The key structural difference: `@PreAuthorize` can reject a call cheaply, before any work happens, using only the method's *arguments*; `@PostAuthorize` necessarily lets the method's work happen first (it needs the *result* to decide), so it's more expensive and — critically — must never be used to guard a method with side effects that shouldn't happen for an unauthorized caller.

## 4. Diagram

<svg viewBox="0 0 660 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PreAuthorize evaluates before the method body runs and can reject the call before any work happens; PostAuthorize lets the method body run first and then evaluates the result, rejecting only after the work is already done" font-family="sans-serif">
  <text x="165" y="24" fill="#e6edf3" font-size="12" text-anchor="middle">@PreAuthorize</text>
  <rect x="30" y="40" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="65" fill="#e6edf3" font-size="9" text-anchor="middle">check SpEL</text>
  <rect x="200" y="40" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="255" y="65" fill="#e6edf3" font-size="9" text-anchor="middle">method body</text>
  <line x1="140" y1="60" x2="200" y2="60" stroke="#6db33f" marker-end="url(#ms)"/>
  <rect x="30" y="100" width="110" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="85" y="121" fill="#f85149" font-size="9" text-anchor="middle">AccessDenied</text>
  <line x1="85" y1="80" x2="85" y2="100" stroke="#f85149" stroke-dasharray="3,2" marker-end="url(#ms)"/>
  <text x="165" y="155" fill="#8b949e" font-size="9" text-anchor="middle">work never happens if denied</text>

  <text x="500" y="24" fill="#e6edf3" font-size="12" text-anchor="middle">@PostAuthorize</text>
  <rect x="370" y="40" width="110" height="40" rx="6" fill="#79c0ff"/>
  <text x="425" y="65" fill="#0d1117" font-size="9" text-anchor="middle">method body</text>
  <rect x="540" y="40" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="595" y="65" fill="#e6edf3" font-size="9" text-anchor="middle">check returnObject</text>
  <line x1="480" y1="60" x2="540" y2="60" stroke="#79c0ff" marker-end="url(#ms)"/>
  <rect x="540" y="100" width="110" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="595" y="121" fill="#f0883e" font-size="9" text-anchor="middle">discard + deny</text>
  <line x1="595" y1="80" x2="595" y2="100" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#ms)"/>
  <text x="500" y="155" fill="#f0883e" font-size="9" text-anchor="middle">work ALREADY happened before denial</text>

  <defs>
    <marker id="ms" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

@PreAuthorize can reject cheaply before work happens; @PostAuthorize must let the work happen first, which matters most when that work has side effects.

## 5. Runnable example

Scenario: an `OrderService` where callers can only act on orders they own, unless they're an admin. We simulate `@PreAuthorize`-style argument-based checks first, then `@PostAuthorize`-style return-value checks that require loading data first, then combine both to show why picking the wrong one for a mutating method is a real production hazard.

### Level 1 — Basic

```java
// File: PreAuthorizeStyleCheck.java -- simulates @PreAuthorize: the check
// runs BEFORE any work, using only the caller's identity and the method's
// OWN ARGUMENTS (no data loading needed yet).
import java.util.*;

public class PreAuthorizeStyleCheck {
    record Authentication(String name, Set<String> authorities) {}

    // Mirrors: @PreAuthorize("#orderId.startsWith(authentication.name) or hasRole('ADMIN')")
    static boolean preAuthorizeCheck(Authentication auth, String orderId) {
        boolean ownsOrderByConvention = orderId.startsWith(auth.name() + "-");
        boolean isAdmin = auth.authorities().contains("ROLE_ADMIN");
        return ownsOrderByConvention || isAdmin;
    }

    static String cancelOrder(Authentication auth, String orderId) {
        if (!preAuthorizeCheck(auth, orderId)) {
            throw new SecurityException("Access Denied -- caller cannot cancel " + orderId);
        }
        System.out.println("[OrderService] " + orderId + " cancelled by " + auth.name());
        return "cancelled";
    }

    public static void main(String[] args) {
        Authentication alice = new Authentication("alice", Set.of());
        Authentication admin = new Authentication("root", Set.of("ROLE_ADMIN"));

        cancelOrder(alice, "alice-order-1");   // owns it by naming convention -- allowed
        try {
            cancelOrder(alice, "bob-order-2"); // doesn't own it, not admin -- denied BEFORE any work
        } catch (SecurityException e) {
            System.out.println("Rejected as expected: " + e.getMessage());
        }
        cancelOrder(admin, "bob-order-2");     // admin override -- allowed
    }
}
```

How to run: `java PreAuthorizeStyleCheck.java`

`preAuthorizeCheck` is evaluated with only `auth` and `orderId` — the raw method arguments — exactly what a real `@PreAuthorize("#orderId.startsWith(authentication.name) or hasRole('ADMIN')")` expression has available to it before Spring AOP lets the method body run. `cancelOrder` throws before printing anything when denied — the "cancel" action's side effect (the print statement, standing in for a database write) never executes for a rejected call, which is the whole point of a *pre*-check.

### Level 2 — Intermediate

```java
// File: PostAuthorizeStyleCheck.java -- simulates @PostAuthorize: the check
// runs AFTER the method body executes, because the authorization decision
// depends on data (the loaded order's owner) that only exists once the
// "database" has actually been queried.
import java.util.*;

public class PostAuthorizeStyleCheck {
    record Authentication(String name, Set<String> authorities) {}
    record Order(String id, String ownerId, String status) {}

    static final Map<String, Order> ORDERS = Map.of(
            "order-1", new Order("order-1", "alice", "PENDING"),
            "order-2", new Order("order-2", "bob", "PENDING")
    );

    // Mirrors: @PostAuthorize("returnObject.ownerId == authentication.name or hasRole('ADMIN')")
    static boolean postAuthorizeCheck(Authentication auth, Order loaded) {
        return loaded.ownerId().equals(auth.name()) || auth.authorities().contains("ROLE_ADMIN");
    }

    static Order getOrder(Authentication auth, String orderId) {
        Order order = ORDERS.get(orderId); // the WORK -- a read, already happened by the time we check
        System.out.println("[OrderService] loaded " + orderId + " (owner=" + order.ownerId() + ") to evaluate authorization");
        if (!postAuthorizeCheck(auth, order)) {
            throw new SecurityException("Access Denied -- " + auth.name() + " does not own " + orderId);
        }
        return order;
    }

    public static void main(String[] args) {
        Authentication alice = new Authentication("alice", Set.of());
        System.out.println("Result: " + getOrder(alice, "order-1")); // owns it -- returned
        try {
            getOrder(alice, "order-2"); // does NOT own it -- denied, but only AFTER the load already happened
        } catch (SecurityException e) {
            System.out.println("Rejected as expected: " + e.getMessage());
        }
    }
}
```

How to run: `java PostAuthorizeStyleCheck.java`

`getOrder` performs the "work" — loading `order` from `ORDERS` — *before* `postAuthorizeCheck` runs, because there's no other way to know the order's `ownerId` in advance. This mirrors `@PostAuthorize("returnObject.ownerId == authentication.name")` exactly: Spring Security lets the method execute fully, inspects the return value, and only then decides whether to let the caller actually see it. Notice the `System.out.println` inside `getOrder` runs even for Alice's rejected call to `order-2` — the read happened regardless of the outcome, which is fine for a read-only method but would be a serious problem for a method with real side effects.

### Level 3 — Advanced

```java
// File: MixingPreAndPostIncorrectly.java -- demonstrates the PRODUCTION
// HAZARD of using @PostAuthorize-style logic on a MUTATING method: the
// side effect (a state change) happens BEFORE the authorization check, so
// an unauthorized caller can trigger real state mutation even though the
// final result is correctly withheld from them. Then shows the FIX: move
// the check to @PreAuthorize-style, evaluated on ARGUMENTS before any mutation.
import java.util.*;

public class MixingPreAndPostIncorrectly {
    record Authentication(String name, Set<String> authorities) {}
    static class Order {
        final String id; final String ownerId; String status;
        Order(String id, String ownerId, String status) { this.id = id; this.ownerId = ownerId; this.status = status; }
    }

    static final Map<String, Order> ORDERS = new HashMap<>(Map.of(
            "order-1", new Order("order-1", "alice", "PENDING")
    ));

    static boolean ownsOrPostAuthCheck(Authentication auth, Order order) {
        return order.ownerId().equals(auth.name()) || auth.authorities().contains("ROLE_ADMIN");
    }

    // WRONG: mutates first, checks authorization on the result afterward.
    static Order cancelOrder_WRONG_postAuthStyle(Authentication auth, String orderId) {
        Order order = ORDERS.get(orderId);
        order.status = "CANCELLED"; // <-- the mutation ALREADY happened, unconditionally
        System.out.println("[WRONG] mutated " + orderId + " to CANCELLED before checking who's asking");
        if (!ownsOrPostAuthCheck(auth, order)) {
            throw new SecurityException("Access Denied -- but the cancellation ALREADY took effect!");
        }
        return order;
    }

    // RIGHT: check authorization on ARGUMENTS before touching any state -- true @PreAuthorize semantics.
    static boolean canCancel(Authentication auth, String orderId) {
        Order order = ORDERS.get(orderId);
        return order != null && ownsOrPostAuthCheck(auth, order);
    }

    static Order cancelOrder_RIGHT_preAuthStyle(Authentication auth, String orderId) {
        if (!canCancel(auth, orderId)) {
            throw new SecurityException("Access Denied -- rejected BEFORE any mutation");
        }
        Order order = ORDERS.get(orderId);
        order.status = "CANCELLED";
        System.out.println("[RIGHT] mutated " + orderId + " to CANCELLED only after authorization passed");
        return order;
    }

    public static void main(String[] args) {
        Authentication mallory = new Authentication("mallory", Set.of()); // does NOT own order-1

        try {
            cancelOrder_WRONG_postAuthStyle(mallory, "order-1");
        } catch (SecurityException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
        System.out.println("order-1 status after WRONG attempt: " + ORDERS.get("order-1").status
                + " -- mutation leaked despite the rejection!");

        ORDERS.put("order-2", new Order("order-2", "alice", "PENDING"));
        try {
            cancelOrder_RIGHT_preAuthStyle(mallory, "order-2");
        } catch (SecurityException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
        System.out.println("order-2 status after RIGHT attempt: " + ORDERS.get("order-2").status
                + " -- correctly untouched");
    }
}
```

How to run: `java MixingPreAndPostIncorrectly.java`

`cancelOrder_WRONG_postAuthStyle` mutates `order.status` unconditionally, then checks authorization — mirroring the mistake of putting `@PostAuthorize` (or, worse, no method-level annotation at all and only a URL-level check) on a mutating method that needed a pre-check instead. `cancelOrder_RIGHT_preAuthStyle` calls `canCancel`, which loads the order *read-only* to inspect its owner but performs no mutation, and only proceeds to mutate `order.status` after that check passes — exactly matching real `@PreAuthorize` semantics, where the SpEL expression can reference a service-layer lookup but the annotated method body itself doesn't run until authorization clears.

## 6. Walkthrough

Trace `MixingPreAndPostIncorrectly.main`. **First**, `cancelOrder_WRONG_postAuthStyle(mallory, "order-1")` runs. `ORDERS.get("order-1")` returns the existing order owned by `"alice"`. The very next line unconditionally sets `order.status = "CANCELLED"` — this is the bug: the mutation has already happened, in-place, on the shared `Order` object stored in `ORDERS`. The print statement confirms the mutation. Only *then* does `ownsOrPostAuthCheck(mallory, order)` run: `order.ownerId()` is `"alice"`, which doesn't equal `mallory`'s name, and `mallory` has no `ROLE_ADMIN` authority, so the check returns `false`, and a `SecurityException` is thrown.

**Next**, back in `main`, the `catch` block prints the rejection message — but the exception was thrown *after* the mutation, not instead of it. `main` then reads `ORDERS.get("order-1").status` directly and prints `"CANCELLED"` — proving the state change leaked through despite the caller being denied. This is the concrete production hazard: from the caller's point of view they were told "access denied," but the order was cancelled anyway.

**Then**, `main` sets up a fresh `"order-2"` owned by `"alice"` and calls `cancelOrder_RIGHT_preAuthStyle(mallory, "order-2")`. This time `canCancel` runs *first*: it loads `order-2` read-only, and `ownsOrPostAuthCheck` again returns `false` for mallory. `canCancel` returns `false`, so `cancelOrder_RIGHT_preAuthStyle` throws immediately, *before* ever reaching the `order.status = "CANCELLED"` line.

**Finally**, `main` reads `ORDERS.get("order-2").status` and prints `"PENDING"` — unchanged, confirming the pre-check-style method correctly prevented any mutation from happening for an unauthorized caller.

```
[WRONG] mutated order-1 to CANCELLED before checking who's asking
Rejected: Access Denied -- but the cancellation ALREADY took effect!
order-1 status after WRONG attempt: CANCELLED -- mutation leaked despite the rejection!
Rejected: Access Denied -- rejected BEFORE any mutation
order-2 status after RIGHT attempt: PENDING -- correctly untouched
```

## 7. Gotchas & takeaways

> `@PostAuthorize` is safe for read-only methods, where "the work" is just a database read with no side effects — but using it (or any post-hoc check) to guard a *mutating* method is a real, well-documented anti-pattern: the mutation happens unconditionally before the check ever runs, so a denied caller can still trigger the state change even though they never see the result. Always use `@PreAuthorize` (checked on arguments, before the method body runs) for anything that writes.

- `@PreAuthorize` evaluates on the method's *arguments*, before the body runs, and can cheaply reject a call with zero side effects — the right choice for any mutating method.
- `@PostAuthorize` evaluates on the method's *return value*, after the body has already fully executed — only safe for read-only methods where "the work" has no observable side effect worth protecting.
- `@EnableMethodSecurity` must be present or these annotations are silently ignored — always verify method security is actually active in integration tests, not just assumed from the annotation's presence.
- Method security and URL-level `authorizeHttpRequests` (from [Spring Security core](0400-spring-security-core-filters-authentication-authorization.md)) are complementary layers, not substitutes — URL-level rules are coarse and fast; method-level rules are fine-grained and can reference actual data.
- Because method security relies on Spring AOP proxies, calling an `@PreAuthorize`-annotated method from *within the same class* (a self-invocation) bypasses the proxy entirely and skips the check — a well-known Spring AOP limitation worth testing for explicitly.
