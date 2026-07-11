---
card: spring-cloud
gi: 68
slug: spring-cloud-circuit-breaker-abstraction
title: "Spring Cloud Circuit Breaker abstraction"
---

## 1. What it is

Spring Cloud Circuit Breaker is a thin, vendor-neutral abstraction (`CircuitBreakerFactory`, `CircuitBreaker`) sitting in front of actual circuit breaker implementations — Resilience4j is the standard choice today (Netflix Hystrix, the historical default, is no longer actively developed) — so application code depends on one consistent API regardless of which underlying library actually does the work.

```java
@Service
class OrdersService {
    private final CircuitBreakerFactory circuitBreakerFactory;

    Invoice getInvoiceWithProtection(String orderId) {
        CircuitBreaker cb = circuitBreakerFactory.create("billing-service");
        return cb.run(
            () -> billingClient.getInvoice(orderId),      // the protected call
            throwable -> new Invoice(orderId, 0.0)          // the fallback
        );
    }
}
```

## 2. Why & when

The earlier cards already used circuit breakers in specific contexts — the Gateway `CircuitBreaker` filter, Feign's circuit breaker fallback integration. This card is the shared abstraction underneath both of those, and the one to reach for directly when protecting *arbitrary* code (not just a Gateway route or a Feign call) — a database call, a call to a non-Feign HTTP client, any operation with a real chance of failing and a sensible fallback.

Reach for the `CircuitBreakerFactory` abstraction directly when:

- Protecting code that isn't already covered by Gateway's `CircuitBreaker` filter or Feign's built-in circuit breaker integration — any arbitrary method call, not necessarily an HTTP call at all.
- You want the option to swap the underlying circuit breaker implementation later without rewriting every call site — depending on the abstraction rather than Resilience4j's own API directly keeps that door open, even though Resilience4j is effectively the only realistic choice today.
- Consistent behavior and configuration style are wanted across every protected call in an application, regardless of whether that call happens to go through Gateway, Feign, or plain application code.

## 3. Core concept

```
 application code
       |
       v
 CircuitBreakerFactory.create("name")   <- vendor-neutral: doesn't know or care which library is underneath
       |
       v
 CircuitBreaker.run(supplier, fallbackFunction)
       |
       |-- CLOSED: runs supplier() -- success returns its result, failure records it and may trip OPEN
       |-- OPEN: skips supplier() entirely, runs fallbackFunction(throwable) immediately
       |-- HALF_OPEN: allows a trial run of supplier()
```

The abstraction's job is to expose exactly this run-with-fallback shape consistently, regardless of which library actually implements the state machine and failure tracking underneath.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code depends only on the vendor neutral CircuitBreakerFactory abstraction, which is backed by a swappable underlying implementation such as Resilience4j">
  <rect x="30" y="30" width="220" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="140" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">application code</text>
  <text x="140" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">cb.run(supplier, fallback)</text>

  <line x1="140" y1="80" x2="140" y2="110" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a68)"/>

  <rect x="30" y="115" width="220" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="137" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">CircuitBreakerFactory</text>
  <text x="140" y="153" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">vendor-neutral abstraction</text>

  <rect x="380" y="115" width="230" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="495" y="137" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Resilience4j (swappable)</text>
  <text x="495" y="153" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">actual state machine + tracking</text>

  <line x1="250" y1="140" x2="378" y2="140" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a68)"/>

  <defs><marker id="a68" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Application code talks only to the abstraction; the concrete circuit breaker implementation is an interchangeable detail behind it.

## 5. Runnable example

The scenario: protect a call to a downstream `orders-service` dependency (not through Gateway or Feign, just direct application code) using the abstraction's shape. Start with an unprotected call, then wrap it in the abstract run-with-fallback pattern, then swap the "implementation" underneath without touching the calling code — demonstrating the abstraction's actual value.

### Level 1 — Basic

Unprotected — a direct call with no circuit breaker at all.

```java
import java.util.function.Supplier;

public class CircuitBreakerAbstractionLevel1 {
    record Invoice(String id, double amount) {}

    static Supplier<Invoice> billingCall = () -> { throw new RuntimeException("billing-service is down"); };

    public static void main(String[] args) {
        try {
            Invoice invoice = billingCall.get();
            System.out.println(invoice);
        } catch (RuntimeException e) {
            System.out.println("caller sees a raw failure: " + e.getMessage());
        }
    }
}
```

How to run: `java CircuitBreakerAbstractionLevel1.java`

No abstraction, no fallback — exactly the baseline the circuit breaker abstraction is meant to improve on, familiar from earlier cards.

### Level 2 — Intermediate

Introduce the abstract `run(supplier, fallback)` shape, independent of any specific underlying implementation.

```java
import java.util.function.Function;
import java.util.function.Supplier;

public class CircuitBreakerAbstractionLevel2 {
    record Invoice(String id, double amount) {}

    // the abstraction: application code only ever calls THIS shape
    interface CircuitBreaker {
        <T> T run(Supplier<T> supplier, Function<Throwable, T> fallback);
    }

    // a minimal, no-real-state-machine implementation -- just try/catch, standing in for "some backing library"
    static class SimpleCircuitBreaker implements CircuitBreaker {
        public <T> T run(Supplier<T> supplier, Function<Throwable, T> fallback) {
            try {
                return supplier.get();
            } catch (Throwable t) {
                return fallback.apply(t);
            }
        }
    }

    static Supplier<Invoice> billingCall = () -> { throw new RuntimeException("billing-service is down"); };

    public static void main(String[] args) {
        CircuitBreaker cb = new SimpleCircuitBreaker();
        Invoice invoice = cb.run(billingCall, throwable -> new Invoice("unknown", 0.0));
        System.out.println("caller received: " + invoice); // never throws, always gets an Invoice
    }
}
```

How to run: `java CircuitBreakerAbstractionLevel2.java`

Calling code now depends only on the `CircuitBreaker` interface's `run` method — it has no idea `SimpleCircuitBreaker` is a bare try/catch with no real failure-rate tracking or state machine underneath. That's precisely the abstraction's point: the calling code's shape is stable, while the implementation behind it can be anything satisfying the same interface.

### Level 3 — Advanced

Swap in a more sophisticated implementation (with real failure tracking, mirroring what Resilience4j actually provides) behind the exact same interface, with zero changes to the calling code — demonstrating the abstraction's real value.

```java
import java.util.*;
import java.util.function.Function;
import java.util.function.Supplier;

public class CircuitBreakerAbstractionLevel3 {
    record Invoice(String id, double amount) {}

    interface CircuitBreaker {
        <T> T run(Supplier<T> supplier, Function<Throwable, T> fallback);
    }

    // a more realistic implementation, with actual state tracking -- this is what a Resilience4j-backed
    // implementation of the SAME interface would provide underneath the Spring Cloud Circuit Breaker abstraction
    static class TrackingCircuitBreaker implements CircuitBreaker {
        enum State { CLOSED, OPEN }
        State state = State.CLOSED;
        Deque<Boolean> window = new ArrayDeque<>();
        int windowSize = 3;

        public <T> T run(Supplier<T> supplier, Function<Throwable, T> fallback) {
            if (state == State.OPEN) {
                System.out.println("[TrackingCircuitBreaker] OPEN -- skipping real call");
                return fallback.apply(new RuntimeException("circuit open"));
            }
            try {
                T result = supplier.get();
                recordOutcome(false);
                return result;
            } catch (Throwable t) {
                recordOutcome(true);
                return fallback.apply(t);
            }
        }

        void recordOutcome(boolean failed) {
            window.addLast(failed);
            if (window.size() > windowSize) window.removeFirst();
            if (window.size() == windowSize && window.stream().allMatch(b -> b)) {
                state = State.OPEN;
                System.out.println("[TrackingCircuitBreaker] all recent calls failed -- OPENING");
            }
        }
    }

    static Supplier<Invoice> billingCall = () -> { throw new RuntimeException("billing-service is down"); };

    // this method is UNCHANGED from Level 2 in shape -- it only depends on the CircuitBreaker interface
    static Invoice protectedCall(CircuitBreaker cb) {
        return cb.run(billingCall, throwable -> new Invoice("unknown", 0.0));
    }

    public static void main(String[] args) {
        CircuitBreaker cb = new TrackingCircuitBreaker(); // swapped implementation, same interface
        for (int i = 0; i < 5; i++) {
            System.out.println("call " + i + " -> " + protectedCall(cb));
        }
    }
}
```

How to run: `java CircuitBreakerAbstractionLevel3.java`

`protectedCall`'s body is identical in shape to Level 2's usage — it calls `cb.run(...)` and nothing more — but `cb` is now a `TrackingCircuitBreaker` with genuine failure-window tracking, and after enough consecutive failures it actually trips `OPEN` and starts skipping the real call entirely, printing a distinct message. This is the abstraction delivering on its promise: the *calling code* (`protectedCall`) never changed at all between Level 2 and Level 3, only the concrete implementation behind the shared `CircuitBreaker` interface did — exactly mirroring how swapping from Resilience4j to a hypothetical alternative implementation of Spring Cloud Circuit Breaker wouldn't require touching any application code depending on the abstraction.

## 6. Walkthrough

Trace the five calls in Level 3.

1. Calls `0` through `2` each invoke `protectedCall(cb)`, which calls `cb.run(billingCall, fallback)`. Since `state` starts `CLOSED`, each call attempts `supplier.get()` (i.e., `billingCall.get()`), which always throws. The `catch` block calls `recordOutcome(true)` and returns `fallback.apply(t)`, producing `Invoice("unknown", 0.0)` each time. After the third failure, `recordOutcome` finds the 3-slot window full and all `true` (all failures), so it flips `state` to `OPEN` and prints the "OPENING" message.
2. Call `3` invokes `protectedCall(cb)` again — this time `run` immediately checks `state == OPEN`, which is now `true`, so it prints the "skipping real call" message and returns `fallback.apply(...)` directly, without ever calling `billingCall.get()` again — the failing backend is spared a fourth doomed attempt.
3. Call `4` behaves identically to call `3` — still `OPEN`, still skips the real call, still returns the fallback `Invoice`.
4. Across all five calls, `protectedCall`'s own source code never changed and never needed to know anything about `TrackingCircuitBreaker`'s internal state machine or failure window — it only ever called the abstract `run` method, exactly the separation of concerns the Spring Cloud Circuit Breaker abstraction is designed to provide between application code and whatever concrete resilience library sits underneath it.

```
call 0: CLOSED -> try real call -> fails -> fallback -> window=[F]
call 1: CLOSED -> try real call -> fails -> fallback -> window=[F,F]
call 2: CLOSED -> try real call -> fails -> fallback -> window=[F,F,F] -> ALL failed -> OPEN
call 3: OPEN -> real call skipped entirely -> fallback
call 4: OPEN -> real call skipped entirely -> fallback

protectedCall()'s own code: IDENTICAL across all 5 calls and across Level 2 vs Level 3
```

## 7. Gotchas & takeaways

> **Gotcha:** the abstraction's genericity means it necessarily exposes only the lowest-common-denominator configuration surface across possible implementations — for Resilience4j-specific tuning (custom `SlidingWindowType`, specific `ignoreExceptions` lists, detailed metrics tags), you still need to configure the Resilience4j-specific customizer (a later card), not the abstract `CircuitBreakerFactory` API alone. The abstraction covers the common case cleanly; deep tuning still requires reaching into the concrete implementation.

- Spring Cloud Circuit Breaker's value is exactly what Level 3 demonstrated directly: calling code depends on a stable interface, while the underlying implementation (its state machine, failure tracking, thresholds) can evolve or be swapped without touching every call site.
- This abstraction is what both the Gateway `CircuitBreaker` filter and Feign's circuit breaker integration are built on top of — understanding it directly explains the shared vocabulary (`run`, fallback function, CLOSED/OPEN/HALF_OPEN) across all three contexts.
- Reach for `CircuitBreakerFactory` directly (rather than relying on Gateway or Feign's built-in integration) whenever protecting code that isn't already an HTTP call routed through either of those — database calls, message queue operations, any operation with a meaningful failure mode and a sensible fallback.
- In practice today, Resilience4j is the only actively-maintained implementation choice — the abstraction's vendor-neutrality is more about isolating application code from implementation details than about realistically swapping vendors, since Hystrix (the historical alternative) is no longer actively developed.
