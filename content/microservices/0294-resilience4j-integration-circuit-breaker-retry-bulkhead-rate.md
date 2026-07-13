---
card: microservices
gi: 294
slug: resilience4j-integration-circuit-breaker-retry-bulkhead-rate
title: "Resilience4j integration (circuit breaker, retry, bulkhead, rate limiter, time limiter)"
---

## 1. What it is

Resilience4j is a lightweight Java resilience library providing separate, independently usable modules for each resilience pattern covered in this section — `CircuitBreaker`, `Retry`, `Bulkhead`, `RateLimiter`, and `TimeLimiter` — each implemented as a functional decorator that wraps a `Supplier`, `Function`, `Runnable`, or similar functional interface. Unlike its predecessor Hystrix, which bundled everything into one monolithic command object, Resilience4j lets each pattern be added, configured, and composed independently, using only the ones actually needed for a given call.

## 2. Why & when

A single outbound call to a critical dependency often needs more than one resilience pattern simultaneously: a timeout to bound the wait, a circuit breaker to stop calling once the dependency is known unhealthy, a bulkhead to limit how many concurrent calls can be in flight, and a retry to smooth over transient blips — each addressing a different failure mode. Resilience4j's decorator-based design makes composing these straightforward: each module produces a decorated version of the same functional type, so they nest naturally (`Retry.decorateSupplier(retry, CircuitBreaker.decorateSupplier(cb, TimeLimiter... ))`).

Use Resilience4j directly (or via the Spring Cloud Circuit Breaker abstraction for the circuit breaker piece specifically) whenever a Spring Boot application needs any combination of these patterns around calls to external dependencies — it is the standard, actively maintained choice in the current Spring ecosystem, integrated via `spring-boot-starter-aop` plus module-specific starters, or configured programmatically as shown here.

## 3. Core concept

Each module exposes a `decorateSupplier` (or equivalent) static method that wraps a functional interface, returning a new instance of the same type with the resilience behavior applied — composing several is just nesting these calls.

```java
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.retry.Retry;
import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.ratelimiter.RateLimiter;
import java.util.function.Supplier;

Supplier<String> raw = () -> inventoryClient.checkStock(sku);

Supplier<String> decorated = Retry.decorateSupplier(retry,
        CircuitBreaker.decorateSupplier(circuitBreaker,
        Bulkhead.decorateSupplier(bulkhead,
        RateLimiter.decorateSupplier(rateLimiter, raw))));
// each layer wraps the one inside it -- rate limiter innermost, retry outermost
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four independent Resilience4j modules nest around the real call: rate limiter innermost, then bulkhead, then circuit breaker, then retry outermost, each contributing its own protection without needing to know about the others">
  <rect x="20" y="20" width="600" height="150" rx="8" fill="none" stroke="#79c0ff" stroke-width="1"/>
  <text x="320" y="38" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Retry (outer)</text>

  <rect x="45" y="45" width="550" height="115" rx="8" fill="none" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">CircuitBreaker</text>

  <rect x="70" y="65" width="500" height="80" rx="8" fill="none" stroke="#79c0ff" stroke-width="1"/>
  <text x="320" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Bulkhead</text>

  <rect x="95" y="85" width="450" height="50" rx="8" fill="none" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">RateLimiter</text>

  <rect x="230" y="105" width="180" height="25" rx="5" fill="#1c2430" stroke="#e6edf3"/>
  <text x="320" y="122" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">real call (innermost)</text>
</svg>

Each pattern nests independently around the real call; composition is just wrapping one decorator inside another.

## 5. Runnable example

Scenario: a single unprotected call to an inventory service, extended to add a circuit breaker alone, and finally composing circuit breaker, retry, and bulkhead together in the recommended order to show all three protections working simultaneously on the same call.

### Level 1 — Basic

```java
// File: RawUnprotectedCall.java -- calls the inventory client directly,
// with no resilience protection of any kind.
public class RawUnprotectedCall {
    static int callCount = 0;
    static String checkStock(String sku) {
        callCount++;
        throw new RuntimeException("inventory-service unreachable");
    }

    public static void main(String[] args) {
        try {
            System.out.println(checkStock("sku-123"));
        } catch (Exception e) {
            System.out.println("FAILED (no protection at all): " + e.getMessage());
        }
        System.out.println("Calls made: " + callCount);
    }
}
```

How to run: `java RawUnprotectedCall.java`

The call fails immediately with no retry, no circuit breaking, no concurrency limiting — a single failed attempt, a single call made, a raw exception surfaced.

### Level 2 — Intermediate

```java
// File: SingleCircuitBreakerModule.java -- adds JUST the CircuitBreaker
// module from Resilience4j (hand-rolled stand-in shown here; the real
// import is io.github.resilience4j.circuitbreaker.CircuitBreaker), no
// other modules yet.
public class SingleCircuitBreakerModule {
    enum State { CLOSED, OPEN }
    static class CircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        final int threshold = 2;

        <T> T decorateAndCall(java.util.function.Supplier<T> supplier) {
            if (state == State.OPEN) throw new RuntimeException("circuit OPEN");
            try {
                T result = supplier.get();
                consecutiveFailures = 0;
                return result;
            } catch (Exception e) {
                consecutiveFailures++;
                if (consecutiveFailures >= threshold) state = State.OPEN;
                throw e;
            }
        }
    }

    static int callCount = 0;
    static String checkStock(String sku) {
        callCount++;
        throw new RuntimeException("inventory-service unreachable");
    }

    public static void main(String[] args) {
        CircuitBreaker cb = new CircuitBreaker();
        for (int i = 1; i <= 4; i++) {
            try {
                System.out.println("Call " + i + ": " + cb.decorateAndCall(() -> checkStock("sku-123")));
            } catch (Exception e) {
                System.out.println("Call " + i + ": FAILED -- " + e.getMessage() + " (state=" + cb.state + ")");
            }
        }
        System.out.println("Real dependency calls made: " + callCount + " out of 4 attempted");
    }
}
```

How to run: `java SingleCircuitBreakerModule.java`

The circuit breaker alone tracks consecutive failures and opens after 2, so of 4 attempted calls, only the first 2 actually reach `checkStock` (both fail, tripping the breaker), while calls 3 and 4 are short-circuited. This shows a single Resilience4j module used in isolation — the building block that gets composed with others in production.

### Level 3 — Advanced

```java
// File: ComposedResilience4jStack.java -- composes CircuitBreaker,
// Retry, and Bulkhead together (hand-rolled stand-ins mirroring the real
// io.github.resilience4j.* APIs), in the recommended order: Retry
// outermost, CircuitBreaker next, Bulkhead innermost -- limiting
// concurrent calls, retrying transient failures, and stopping entirely
// once the dependency is known unhealthy, all at once.
import java.util.concurrent.Semaphore;

public class ComposedResilience4jStack {
    enum State { CLOSED, OPEN }
    static class CircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        final int threshold = 3;
        <T> T call(java.util.function.Supplier<T> supplier) {
            if (state == State.OPEN) throw new RuntimeException("circuit OPEN");
            try { T r = supplier.get(); consecutiveFailures = 0; return r; }
            catch (Exception e) { consecutiveFailures++; if (consecutiveFailures >= threshold) state = State.OPEN; throw e; }
        }
    }
    static class Bulkhead {
        final Semaphore semaphore;
        Bulkhead(int maxConcurrent) { semaphore = new Semaphore(maxConcurrent); }
        <T> T call(java.util.function.Supplier<T> supplier) {
            if (!semaphore.tryAcquire()) throw new RuntimeException("bulkhead FULL");
            try { return supplier.get(); } finally { semaphore.release(); }
        }
    }
    static <T> T withRetry(java.util.function.Supplier<T> supplier, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try { return supplier.get(); }
            catch (Exception e) { if (attempt == maxAttempts) throw e; }
        }
        throw new IllegalStateException("unreachable");
    }

    static int callCount = 0;
    static String checkStock(String sku) {
        callCount++;
        throw new RuntimeException("inventory-service unreachable");
    }

    public static void main(String[] args) {
        CircuitBreaker circuitBreaker = new CircuitBreaker();
        Bulkhead bulkhead = new Bulkhead(2);

        for (int i = 1; i <= 5; i++) {
            try {
                String result = withRetry(() -> circuitBreaker.call(() -> bulkhead.call(() -> checkStock("sku-123"))), 2);
                System.out.println("Logical call " + i + ": " + result);
            } catch (Exception e) {
                System.out.println("Logical call " + i + ": FAILED -- " + e.getMessage() + " (breaker=" + circuitBreaker.state + ")");
            }
        }
        System.out.println("Total REAL dependency calls made: " + callCount + " (across 5 logical calls x up to 2 retries each = up to 10 possible)");
    }
}
```

How to run: `java ComposedResilience4jStack.java`

Each logical call is wrapped: retry (2 attempts) is outermost, wrapping the circuit breaker, which wraps the bulkhead (max 2 concurrent, though this single-threaded example never actually contends), which wraps the real call. The first logical call's 2 retry attempts both hit the dependency and fail, and the second logical call's first attempt also fails — after 3 total real failures, the circuit breaker opens. From that point, every remaining attempt (across both remaining retries of call 2 and all of calls 3-5) is short-circuited by the open breaker before ever reaching the bulkhead or the dependency. The final call count is far below the theoretical maximum of 10, showing all three modules contributing: retry smooths individual transient failures, the circuit breaker stops the pattern once failures are clearly not transient, and the bulkhead would have capped concurrent in-flight calls had this example used multiple threads.

## 6. Walkthrough

Trace `ComposedResilience4jStack.main`'s first two logical calls. **First**, logical call 1 invokes `withRetry(..., 2)`, which calls the composed lambda at `attempt=1`: `circuitBreaker.call(() -> bulkhead.call(() -> checkStock(...)))`.

**Inside `circuitBreaker.call`**, `state` is `CLOSED`, so it proceeds to call the bulkhead lambda. **Inside `bulkhead.call`**, `semaphore.tryAcquire()` succeeds (nothing else holds a permit), so it calls `checkStock`, which increments `callCount` to 1 and throws. The `finally` in `bulkhead.call` releases the semaphore permit regardless of the exception, then the exception propagates up to `circuitBreaker.call`'s `catch` block, which increments `consecutiveFailures` to 1 (below the threshold of 3) and re-throws.

**Back in `withRetry`**, `attempt=1`'s failure is caught; since `attempt != maxAttempts(2)`, it loops to `attempt=2` and runs the identical composed lambda again. This time `callCount` reaches 2, `consecutiveFailures` reaches 2 (still below 3), and since `attempt == maxAttempts`, the exception is finally re-thrown out of `withRetry` — logical call 1 fails after exhausting its 2 retries, having made 2 real dependency calls.

**Logical call 2** begins the same way: `withRetry` at `attempt=1` calls through the same composed chain. `circuitBreaker.state` is still `CLOSED` (carried over from call 1), so it proceeds; `bulkhead.call` succeeds in acquiring its permit; `checkStock` runs, `callCount` reaches 3, and this failure pushes `consecutiveFailures` to 3 — meeting the threshold, so `circuitBreaker.state` flips to `OPEN` before the exception even finishes propagating out of `circuitBreaker.call`.

**`withRetry`'s `attempt=2`** for logical call 2 now calls the composed lambda again — but this time `circuitBreaker.call`'s very first check, `if (state == State.OPEN)`, is true, so it throws immediately, *never even reaching* `bulkhead.call` or `checkStock`. `callCount` stays at 3. This is the last attempt (`attempt==maxAttempts`), so `withRetry` re-throws, and logical call 2 fails having made only 1 additional real call (3 total so far) instead of 2.

**Logical calls 3, 4, and 5** each follow the same pattern as call 2's second attempt: every single attempt is short-circuited by the still-open breaker, contributing 0 further increments to `callCount`.

```
call 1: attempt1 (real, fail, count=1) -> attempt2 (real, fail, count=2) -> retries exhausted, FAIL
call 2: attempt1 (real, fail, count=3, BREAKER OPENS) -> attempt2 (short-circuited) -> FAIL
call 3,4,5: all attempts short-circuited, count stays at 3
                                    total real dependency calls: 3 (out of a possible 10)
```

## 7. Gotchas & takeaways

> Composing multiple Resilience4j modules without thinking through their interaction order can produce surprising behavior — see [bounded retries + circuit breaker ordering](0292-bounded-retries-circuit-breaker-combination-ordering.md) for why retry-outside-circuit-breaker is the generally recommended order, and note that a bulkhead innermost means it only gates calls that have already passed the circuit breaker's check, which is usually desired (don't waste a bulkhead permit on a call that's about to be short-circuited anyway).

- Resilience4j's per-module design means only the modules actually needed for a given call should be composed — not every call needs all five.
- Each module is independently configurable and independently testable in isolation, which is valuable both for understanding behavior and for the kind of [chaos engineering](0291-chaos-engineering-fault-injection.md) validation covered earlier in this section.
- In a real Spring Boot project, these modules are typically configured via `application.yml` under `resilience4j.circuitbreaker`, `resilience4j.retry`, `resilience4j.bulkhead`, etc. (see [Resilience4j config via application.yml](0296-resilience4j-config-via-application-yml.md)) rather than built up programmatically as shown here for illustration.
- Prefer the annotation-based style (`@CircuitBreaker`, `@Retry`, `@Bulkhead` — see [Resilience4j annotations](0295-resilience4j-annotations-circuitbreaker-retry-bulkhead-ratel.md)) for typical Spring service methods; the programmatic `decorateSupplier` style shown here is most useful for more dynamic composition or non-Spring-managed code.
