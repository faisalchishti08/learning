---
card: spring-security
gi: 118
slug: reactive-method-security
title: "Reactive method security"
---

## 1. What it is

Reactive method security extends `@PreAuthorize`/`@PostAuthorize` (card 0062) to methods that return `Mono<T>` or `Flux<T>` — the annotations themselves are unchanged, but the enforcement mechanism underneath must be, since a reactive method's actual work often hasn't happened yet by the time the method call returns; it only happens later, when something subscribes to the returned `Mono`/`Flux`. `@EnableReactiveMethodSecurity` wires up the interceptor that understands this: rather than checking authorization before the method body runs (as `MethodSecurityInterceptor` does for a plain, blocking method), it instruments the returned reactive type itself, performing the authorization check as part of the subscription, reading the current principal via `ReactiveSecurityContextHolder` (card 0116) rather than a `ThreadLocal`-based `SecurityContextHolder`.

```java
@Configuration
@EnableReactiveMethodSecurity
public class MethodSecurityConfig {}

@Service
public class OrderService {

    @PreAuthorize("hasAuthority('SCOPE_read:orders')")
    public Mono<Order> findOrder(String orderId) {
        return orderRepository.findById(orderId); // the CHECK runs before this Mono is actually subscribed to
    }

    @PreAuthorize("hasAuthority('SCOPE_admin')")
    public Flux<Order> findAllOrders() {
        return orderRepository.findAll();
    }
}
```

## 2. Why & when

A blocking `@PreAuthorize`-annotated method's authorization check and its body execution happen in the same synchronous call — check first, then (if authorized) invoke the method, all on one thread, in one uninterrupted sequence. A `Mono`-returning method breaks that assumption: calling `findOrder("123")` doesn't run the query at all, it merely *constructs* a `Mono` describing that query, which only actually executes later when something subscribes to it — potentially on a different thread, potentially after other reactive operators have already been chained on. An authorization check that ran the instant the method was *called* (rather than when the resulting `Mono` is *subscribed to*) would be checking authorization against whatever principal happens to be reachable at construction time, which may not correspond at all to the principal actually driving the eventual subscription — reactive method security exists specifically to defer the check to the correct moment.

Reach for `@EnableReactiveMethodSecurity` when:

- Applying method-level authorization inside a WebFlux application, on service methods returning `Mono`/`Flux` — this is the only variant of method security that composes correctly with those return types.
- An existing Servlet-stack application using `@PreAuthorize` is being ported to WebFlux — the annotations look identical, but silently keeping the Servlet-stack `@EnableMethodSecurity` interceptor active would either fail outright against reactive return types or, worse, check authorization at the wrong moment without any obvious symptom.
- Building custom reactive authorization logic beyond what SpEL expressions naturally express — a custom `ReactiveAuthorizationManager` can be supplied for arbitrarily complex, asynchronous authorization decisions (a check that itself needs to make an async lookup, for instance).

## 3. Core concept

```
Blocking method security (@EnableMethodSecurity):
    caller invokes method()
      -> interceptor checks authorization SYNCHRONOUSLY, on the CALLING thread, using SecurityContextHolder
      -> if authorized: method body runs, returns a value, DONE
      -> if denied: AccessDeniedException thrown IMMEDIATELY, method body never runs

Reactive method security (@EnableReactiveMethodSecurity):
    caller invokes method() -> returns a Mono/Flux DESCRIPTION, nothing has executed yet
      -> the interceptor wraps that Mono/Flux with an authorization check
      -> the check itself happens as part of SUBSCRIBING -- i.e., when something downstream
         actually asks for the value, NOT at the moment method() was called
      -> the check reads the principal via ReactiveSecurityContextHolder (card 0116),
         which correctly resolves regardless of which thread ends up doing the subscribing
      -> if authorized: the ORIGINAL Mono/Flux is subscribed to, proceeds normally
      -> if denied: the Mono/Flux emits an AccessDeniedException as its ERROR signal,
         rather than a synchronous exception thrown at call time

KEY DIFFERENCE: "when does the check happen" moves from "at method CALL time" to
                "at method SUBSCRIBE time" -- because reactive types are lazy descriptions,
                not eagerly-executed computations.
```

This distinction matters because a reactive method can be called, composed with other operators, and passed around *before* anything actually executes — the authorization check must happen at the point where execution genuinely begins, not before.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram contrasting blocking method security where the check runs immediately at call time against reactive method security where calling the method only builds a description and the authorization check runs later at subscription time">
  <rect x="20" y="20" width="290" height="180" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="165" y="42" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Blocking @PreAuthorize</text>
  <rect x="40" y="58" width="250" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="165" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">caller invokes method()</text>
  <line x1="165" y1="88" x2="165" y2="106" stroke="#f0883e" stroke-width="1.4" marker-end="url(#rms118)"/>
  <rect x="40" y="108" width="250" height="30" rx="5" fill="#161b22" stroke="#f0883e" stroke-width="1.2"/>
  <text x="165" y="127" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">check runs IMMEDIATELY</text>
  <line x1="165" y1="138" x2="165" y2="156" stroke="#3fb950" stroke-width="1.4" marker-end="url(#rms118)"/>
  <rect x="40" y="158" width="250" height="30" rx="5" fill="#161b22" stroke="#3fb950" stroke-width="1.2"/>
  <text x="165" y="177" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">method body runs (or throws)</text>

  <rect x="330" y="20" width="290" height="180" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Reactive @PreAuthorize</text>
  <rect x="350" y="58" width="250" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="475" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">caller invokes method()</text>
  <line x1="475" y1="88" x2="475" y2="106" stroke="#8b949e" stroke-width="1.4" marker-end="url(#rms118b)"/>
  <rect x="350" y="108" width="250" height="30" rx="5" fill="#161b22" stroke="#8b949e" stroke-width="1"/>
  <text x="475" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">returns Mono DESCRIPTION only</text>
  <line x1="475" y1="138" x2="475" y2="156" stroke="#3fb950" stroke-width="1.4" marker-end="url(#rms118b)"/>
  <rect x="350" y="158" width="250" height="30" rx="5" fill="#161b22" stroke="#3fb950" stroke-width="1.2"/>
  <text x="475" y="177" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">check runs at SUBSCRIBE time</text>

  <defs>
    <marker id="rms118" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="rms118b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Blocking method security checks at call time; reactive method security defers the check to subscription time, matching the lazy nature of `Mono`/`Flux`.

## 5. Runnable example

The scenario: model both timing behaviors using `CompletableFuture`-based construction versus `Supplier`-based lazy description (standing in for eager blocking calls versus lazy `Mono` construction), showing the check running at the correct moment in each case, then a denied case whose error surfaces as part of the reactive result rather than a synchronous throw.

### Level 1 — Basic

An eager (blocking-style) check versus a lazy (reactive-style) description, showing exactly when each check runs.

```java
import java.util.*;
import java.util.function.*;

public class ReactiveMethodSecurityLevel1 {
    record Order(String id) {}
    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    static Set<String> currentAuthorities = Set.of("SCOPE_read:orders");

    // BLOCKING style: the check runs the INSTANT this method is called
    static Order findOrderBlocking(String orderId) {
        System.out.println("  [blocking] check running NOW, at call time");
        if (!currentAuthorities.contains("SCOPE_read:orders")) throw new AccessDeniedException("denied");
        return new Order(orderId);
    }

    // REACTIVE style: calling this returns a LAZY description; the check runs later, at "subscribe" time
    static Supplier<Order> findOrderReactive(String orderId) {
        System.out.println("  [reactive] method called, but NOTHING has run yet -- just building a description");
        return () -> {
            System.out.println("  [reactive] check running NOW, at 'subscribe' time");
            if (!currentAuthorities.contains("SCOPE_read:orders")) throw new AccessDeniedException("denied");
            return new Order(orderId);
        };
    }

    public static void main(String[] args) {
        System.out.println("--- blocking ---");
        Order blockingResult = findOrderBlocking("order-1");
        System.out.println("result: " + blockingResult);

        System.out.println("--- reactive ---");
        Supplier<Order> lazyOrder = findOrderReactive("order-2"); // NOTHING printed about the check yet
        System.out.println("  (method call returned, but the check has NOT run yet)");
        Order reactiveResult = lazyOrder.get(); // THIS is "subscribing" -- the check runs only now
        System.out.println("result: " + reactiveResult);
    }
}
```

**How to run:** save as `ReactiveMethodSecurityLevel1.java`, run `java ReactiveMethodSecurityLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
--- blocking ---
  [blocking] check running NOW, at call time
result: Order[id=order-1]
--- reactive ---
  [reactive] method called, but NOTHING has run yet -- just building a description
  (method call returned, but the check has NOT run yet)
  [reactive] check running NOW, at 'subscribe' time
result: Order[id=order-2]
```

The `Supplier<Order>` stands in for a `Mono<Order>`: calling `findOrderReactive` returns immediately without running any authorization check at all, and the check only actually executes when `.get()` is called (standing in for `Mono.subscribe()`/a downstream operator triggering execution) — exactly the timing difference `@EnableReactiveMethodSecurity`'s interceptor is built to respect.

### Level 2 — Intermediate

Read the current principal's authorities as part of the (simulated) subscription itself, using an explicitly-carried context rather than a static field — mirroring `ReactiveSecurityContextHolder`'s role from card 0116.

```java
import java.util.*;
import java.util.function.*;

public class ReactiveMethodSecurityLevel2 {
    record Order(String id) {}
    record SecurityContext(String principalName, Set<String> authorities) {}
    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    // mirrors a method annotated @PreAuthorize("hasAuthority('SCOPE_read:orders')") returning Mono<Order>
    static Function<SecurityContext, Order> findOrder(String orderId, String requiredAuthority) {
        // returns a LAZY function -- the "Mono" -- context is supplied later, at subscribe time
        return securityContext -> {
            if (!securityContext.authorities().contains(requiredAuthority)) {
                throw new AccessDeniedException(securityContext.principalName() + " lacks " + requiredAuthority);
            }
            return new Order(orderId);
        };
    }

    public static void main(String[] args) {
        Function<SecurityContext, Order> lazyOrder = findOrder("order-1", "SCOPE_read:orders");

        // "subscribing" happens HERE, with whatever security context is current AT THIS MOMENT
        SecurityContext aliceContext = new SecurityContext("alice", Set.of("SCOPE_read:orders"));
        Order result = lazyOrder.apply(aliceContext);
        System.out.println("alice's subscription result: " + result);

        // the SAME lazy description, "subscribed to" again with a DIFFERENT context
        SecurityContext bobContext = new SecurityContext("bob", Set.of("SCOPE_write:orders")); // no read scope
        try {
            lazyOrder.apply(bobContext);
        } catch (AccessDeniedException e) {
            System.out.println("bob's subscription: DENIED -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ReactiveMethodSecurityLevel2.java`, run `java ReactiveMethodSecurityLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
alice's subscription result: Order[id=order-1]
bob's subscription: DENIED -- bob lacks SCOPE_read:orders
```

What changed: the *same* lazy description (`lazyOrder`) is evaluated twice, against two entirely different security contexts — demonstrating that the authorization check genuinely depends on whatever context is current at the moment of "subscription," not on anything fixed when the method was first called; this mirrors how `ReactiveSecurityContextHolder.getContext()` (card 0116) resolves the *currently* propagating context at the point the reactive chain actually executes, which may be well after — and under a different logical "caller" than — whenever the method reference was first obtained.

### Level 3 — Advanced

Model the denial surfacing as part of the reactive result itself (an error signal), rather than a synchronous exception at call time, and compose a chain of dependent reactive-style operations where an early denial short-circuits later steps — mirroring how a denied `Mono` never triggers its downstream operators.

```java
import java.util.*;
import java.util.function.*;

public class ReactiveMethodSecurityLevel3 {
    record Order(String id, double total) {}
    record SecurityContext(String principalName, Set<String> authorities) {}
    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    // a MINIMAL stand-in for Mono<T> -- either a VALUE or an ERROR, resolved lazily
    static class LazyResult<T> {
        private final Function<SecurityContext, T> computation;
        LazyResult(Function<SecurityContext, T> computation) { this.computation = computation; }

        static <T> LazyResult<T> secured(Function<SecurityContext, T> body, String requiredAuthority) {
            return new LazyResult<>(ctx -> {
                if (!ctx.authorities().contains(requiredAuthority)) {
                    throw new AccessDeniedException(ctx.principalName() + " lacks " + requiredAuthority);
                }
                return body.apply(ctx);
            });
        }

        <R> LazyResult<R> then(Function<T, LazyResult<R>> next) {
            return new LazyResult<>(ctx -> next.apply(this.computation.apply(ctx)).computation.apply(ctx));
        }

        T subscribe(SecurityContext ctx) { return computation.apply(ctx); } // triggers ACTUAL execution
    }

    public static void main(String[] args) {
        // findOrder requires SCOPE_read:orders; applyDiscount (chained after) requires SCOPE_admin
        LazyResult<Order> findOrder = LazyResult.secured(ctx -> new Order("order-1", 100.0), "SCOPE_read:orders");

        LazyResult<Order> findThenDiscount = findOrder.then(order ->
                LazyResult.secured(ctx -> new Order(order.id(), order.total() * 0.9), "SCOPE_admin"));

        // alice: has BOTH required authorities -- the whole chain succeeds
        SecurityContext aliceContext = new SecurityContext("alice", Set.of("SCOPE_read:orders", "SCOPE_admin"));
        Order aliceResult = findThenDiscount.subscribe(aliceContext);
        System.out.println("alice (read+admin): " + aliceResult);

        // bob: has read access but NOT admin -- findOrder succeeds, but the chained discount step is denied
        SecurityContext bobContext = new SecurityContext("bob", Set.of("SCOPE_read:orders"));
        try {
            findThenDiscount.subscribe(bobContext);
        } catch (AccessDeniedException e) {
            System.out.println("bob (read only): chain denied at the SECOND step -- " + e.getMessage());
        }

        // carol: lacks even the FIRST required authority -- never reaches the second check at all
        SecurityContext carolContext = new SecurityContext("carol", Set.of("SCOPE_write:orders"));
        try {
            findThenDiscount.subscribe(carolContext);
        } catch (AccessDeniedException e) {
            System.out.println("carol (no read access): chain denied at the FIRST step -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ReactiveMethodSecurityLevel3.java`, run `java ReactiveMethodSecurityLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice (read+admin): Order[id=order-1, total=90.0]
bob (read only): chain denied at the SECOND step -- bob lacks SCOPE_admin
carol (no read access): chain denied at the FIRST step -- carol lacks SCOPE_read:orders
```

What changed: `LazyResult.then` composes two independently-secured operations into one chain, and the authorization checks only actually run when `.subscribe(ctx)` is called — bob's chain gets past the first `@PreAuthorize`-equivalent check (he has `SCOPE_read:orders`) but fails the second (`SCOPE_admin`), while carol never even reaches the second check because the first one already threw; this mirrors exactly how a real `Mono` chain (`findOrder(id).flatMap(order -> applyDiscount(order))`) short-circuits at whichever `@PreAuthorize`-guarded step first denies access, with every check happening at subscription time, in order, on the actual principal driving that particular subscription.

## 6. Walkthrough

Trace bob's partial-denial case from Level 3, tying it directly to a real `@PreAuthorize`-annotated reactive service chain.

**Step 1 — the equivalent real code:**
```java
@PreAuthorize("hasAuthority('SCOPE_read:orders')")
public Mono<Order> findOrder(String orderId) { return orderRepository.findById(orderId); }

@PreAuthorize("hasAuthority('SCOPE_admin')")
public Mono<Order> applyDiscount(Order order) { return Mono.just(new Order(order.getId(), order.getTotal() * 0.9)); }

public Mono<Order> findOrderWithDiscount(String orderId) {
    return findOrder(orderId).flatMap(this::applyDiscount);
}
```
Calling `findOrderWithDiscount("order-1")` returns a `Mono<Order>` immediately — nothing has executed. This corresponds to constructing `findThenDiscount` in Level 3's code: a description, not a computation that has already run.

**Step 2 — bob's request subscribes to this `Mono`** (in a real application, a WebFlux controller returning it as the response body triggers subscription automatically). This corresponds to `findThenDiscount.subscribe(bobContext)`.

**Step 3 — the first check runs.** `findOrder`'s reactive method security interceptor reads bob's authorities via `ReactiveSecurityContextHolder` (card 0116) — `{"SCOPE_read:orders"}` — checks `hasAuthority('SCOPE_read:orders')`, which passes. The underlying `orderRepository.findById(orderId)` proceeds, corresponding to `LazyResult.secured(ctx -> new Order(...), "SCOPE_read:orders")`'s body executing successfully.

**Step 4 — `flatMap` chains the next step**, corresponding to `LazyResult.then(order -> LazyResult.secured(...))`. This constructs (but does not yet execute) the `applyDiscount` call for the order just retrieved.

**Step 5 — the second check runs**, as part of the same overall subscription continuing to propagate. `applyDiscount`'s interceptor reads bob's authorities again — still `{"SCOPE_read:orders"}`, no `SCOPE_admin` — checks `hasAuthority('SCOPE_admin')`, which fails. `AccessDeniedException` is raised as this step's *error signal*, not a synchronous throw back at the original `findOrderWithDiscount("order-1")` call site (which returned long before this point, only handing back the `Mono` description).

**Step 6 — the error propagates through the reactive chain.** In a real WebFlux application, this typically surfaces as a `403 Forbidden` response, produced by a `ServerAccessDeniedHandler` reacting to the error signal emitted by the `Mono`, mirroring how the Servlet stack's `AccessDeniedException` gets translated into an HTTP response by its own exception-handling machinery.

```
findOrderWithDiscount("order-1") called -> returns Mono description, NOTHING executed yet
        |
        v  (subscription happens later, e.g. when WebFlux serializes the response)
findOrder step:      check hasAuthority('SCOPE_read:orders') for bob -> PASSES -> order fetched
        |
        v
applyDiscount step:  check hasAuthority('SCOPE_admin') for bob       -> FAILS  -> AccessDeniedException (as an error signal)
        |
        v
response: 403 Forbidden
```

## 7. Gotchas & takeaways

> **Gotcha:** enabling `@EnableMethodSecurity` (the blocking-stack annotation) instead of `@EnableReactiveMethodSecurity` inside a WebFlux application either fails to intercept `Mono`/`Flux`-returning methods correctly or, in some misconfigurations, evaluates the SpEL expression against a `SecurityContextHolder` that has nothing meaningful in it (since WebFlux populates `ReactiveSecurityContextHolder`, not the `ThreadLocal`-based one) — always confirm which of the two enabling annotations is active when method security in a WebFlux application appears to be silently not enforcing anything.

- `@PreAuthorize`/`@PostAuthorize` annotations are unchanged between the blocking and reactive stacks — only the enforcement mechanism underneath, enabled via `@EnableReactiveMethodSecurity`, differs.
- The authorization check for a reactive method runs at *subscription* time, not at the moment the method is *called* — because `Mono`/`Flux` are lazy descriptions of work, not already-executed computations.
- A denied check surfaces as an error signal on the returned `Mono`/`Flux`, not a synchronous exception at the original call site, since the call site may have already returned long before the actual check runs.
- Chained reactive operations, each independently secured, are checked in the order they're actually subscribed to — an early step's denial prevents later steps (and their own checks) from ever running at all, exactly mirroring short-circuiting behavior in blocking code, just deferred to a different point in time.
- The principal used for every reactive method security check is resolved via `ReactiveSecurityContextHolder` (card 0116), which correctly reflects whichever logical subscription is currently executing, regardless of physical thread — never a `ThreadLocal`-based lookup, which would not work correctly in this execution model at all.
