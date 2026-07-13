---
card: microservices
gi: 295
slug: resilience4j-annotations-circuitbreaker-retry-bulkhead-ratel
title: "Resilience4j annotations (@CircuitBreaker, @Retry, @Bulkhead, @RateLimiter, @TimeLimiter)"
---

## 1. What it is

Resilience4j provides annotations — `@CircuitBreaker`, `@Retry`, `@Bulkhead`, `@RateLimiter`, `@TimeLimiter` — that apply the corresponding resilience pattern to a Spring-managed bean method declaratively, via Spring AOP, instead of manually wrapping the call with `decorateSupplier` calls as shown in the [programmatic integration](0294-resilience4j-integration-circuit-breaker-retry-bulkhead-rate.md). Each annotation names a configured instance (matching a name defined in `application.yml`) and optionally a fallback method to invoke on failure, keeping the resilience concern entirely out of the method body itself.

## 2. Why & when

Manually composing decorators inside every method that needs resilience protection is repetitive and mixes cross-cutting concerns (retry, circuit breaking) with the actual business logic of the method. Annotations move that composition to the method signature/metadata level, applied transparently via a Spring AOP proxy — the method body reads as plain business logic, and the resilience behavior is declared, not hand-wired.

Use annotations for the common case: a normal Spring `@Service` method calling an external dependency, where the desired resilience behavior is static and configuration-driven. Prefer the programmatic API from the previous topic when the composition needs to be dynamic (chosen at runtime, built per-request) or when the code isn't a Spring-managed bean and therefore can't benefit from the AOP proxy that annotations depend on.

## 3. Core concept

Multiple annotations stack on the same method; Spring AOP applies them as nested proxies, and each references a named configuration plus, for `@CircuitBreaker`/`@Retry`/etc., an optional fallback method with a matching signature plus a `Throwable` parameter.

```java
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import org.springframework.stereotype.Service;

@Service
class InventoryService {
    private final InventoryClient inventoryClient;
    InventoryService(InventoryClient inventoryClient) { this.inventoryClient = inventoryClient; }

    @Retry(name = "inventory")               // applies FIRST (outer, per convention)
    @CircuitBreaker(name = "inventory", fallbackMethod = "checkStockFallback") // applies SECOND (inner)
    String checkStock(String sku) {
        return inventoryClient.checkStock(sku); // plain business logic, no resilience code here
    }

    // Fallback signature MUST match the original method's params, plus a trailing Throwable.
    String checkStockFallback(String sku, Throwable t) {
        return "UNKNOWN (inventory check failed: " + t.getMessage() + ")";
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Spring AOP proxy sits in front of the actual bean method, intercepting calls to apply the annotated resilience behavior before delegating to the real method body, and routing any failure to the configured fallback method instead of letting the exception propagate to the caller">
  <rect x="20" y="55" width="110" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller</text>

  <line x1="130" y1="75" x2="220" y2="75" stroke="#8b949e" marker-end="url(#arr295)"/>
  <rect x="230" y="40" width="180" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Spring AOP proxy</text>
  <text x="320" y="75" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@Retry + @CircuitBreaker</text>
  <text x="320" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">applied around the call</text>

  <line x1="410" y1="60" x2="490" y2="60" stroke="#8b949e" marker-end="url(#arr295)"/>
  <rect x="500" y="40" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="64" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">real method body</text>

  <line x1="410" y1="90" x2="490" y2="110" stroke="#8b949e" marker-end="url(#arr295)"/>
  <rect x="500" y="95" width="120" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="560" y="117" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">fallback method</text>

  <defs><marker id="arr295" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The AOP proxy intercepts the call, enforces the annotated resilience behavior, and routes failures to the fallback.

## 5. Runnable example

Scenario: a plain service method with no annotations that fails outright, hand-simulated proxy behavior showing what `@Retry` alone would do, and finally simulating the full stacked annotation behavior (`@Retry` + `@CircuitBreaker` + fallback) as Spring AOP would apply it, since annotation processing itself requires a running Spring context that a bare `java File.java` cannot provide.

### Level 1 — Basic

```java
// File: PlainMethodNoAnnotations.java -- a service method with no
// resilience annotations at all; any failure propagates directly.
public class PlainMethodNoAnnotations {
    static class InventoryClient {
        int callCount = 0;
        String checkStock(String sku) {
            callCount++;
            throw new RuntimeException("inventory-service unreachable");
        }
    }

    static class InventoryService {
        final InventoryClient inventoryClient;
        InventoryService(InventoryClient inventoryClient) { this.inventoryClient = inventoryClient; }
        String checkStock(String sku) { return inventoryClient.checkStock(sku); } // NO resilience annotations
    }

    public static void main(String[] args) {
        InventoryService service = new InventoryService(new InventoryClient());
        try {
            System.out.println(service.checkStock("sku-123"));
        } catch (Exception e) {
            System.out.println("FAILED directly: " + e.getMessage());
        }
    }
}
```

How to run: `java PlainMethodNoAnnotations.java`

`checkStock` calls the client directly, and the failure propagates straight to the caller — this is the baseline "no annotations applied" behavior that `@Retry`/`@CircuitBreaker` would sit in front of in a real Spring context.

### Level 2 — Intermediate

```java
// File: SimulatedRetryAnnotationBehavior.java -- simulates EXACTLY what
// Spring AOP does when it sees @Retry(name = "inventory") on a method:
// it wraps the real call in a proxy that retries on failure according to
// the NAMED configuration, without the method body itself containing
// any retry logic.
public class SimulatedRetryAnnotationBehavior {
    static class InventoryClient {
        int callCount = 0;
        String checkStock(String sku) {
            callCount++;
            if (callCount < 3) throw new RuntimeException("transient inventory-service error");
            return "IN_STOCK"; // succeeds on the 3rd attempt
        }
    }

    // This proxy is what Spring AOP generates automatically for a
    // method annotated @Retry(name = "inventory") -- application code
    // never writes this class itself.
    static class RetryAopProxy {
        final int maxAttempts = 3; // from application.yml: resilience4j.retry.instances.inventory.max-attempts
        String checkStockWithRetryApplied(InventoryClient client, String sku) {
            for (int attempt = 1; attempt <= maxAttempts; attempt++) {
                try { return client.checkStock(sku); } // delegates to the REAL (unannotated) method body
                catch (Exception e) { if (attempt == maxAttempts) throw e; }
            }
            throw new IllegalStateException("unreachable");
        }
    }

    public static void main(String[] args) {
        InventoryClient client = new InventoryClient();
        RetryAopProxy proxy = new RetryAopProxy();
        System.out.println("Result: " + proxy.checkStockWithRetryApplied(client, "sku-123"));
        System.out.println("Real dependency calls made: " + client.callCount
                + " (the @Retry-annotated method body itself contains ZERO retry logic -- the proxy adds it)");
    }
}
```

How to run: `java SimulatedRetryAnnotationBehavior.java`

`RetryAopProxy` stands in for what Spring's AOP machinery generates when it processes an `@Retry(name = "inventory")` annotation — application code never writes this class; it's synthesized. The underlying `checkStock` fails transiently for its first two calls and succeeds on the third; the proxy retries transparently, so `checkStockWithRetryApplied` ultimately returns `"IN_STOCK"` even though the real method itself has no retry logic in its body at all — that behavior is entirely contributed by the annotation-driven proxy layer.

### Level 3 — Advanced

```java
// File: SimulatedStackedAnnotations.java -- simulates the FULL stacked
// behavior of @Retry(name="inventory") + @CircuitBreaker(name="inventory",
// fallbackMethod="checkStockFallback") on the same method, exactly as
// Spring AOP would compose them (Retry outer, CircuitBreaker inner, per
// Resilience4j's documented default ordering), including invoking the
// fallback method by reflection-equivalent dispatch once the breaker opens.
public class SimulatedStackedAnnotations {
    enum State { CLOSED, OPEN }

    static class InventoryClient {
        int callCount = 0;
        String checkStock(String sku) {
            callCount++;
            throw new RuntimeException("inventory-service down"); // persistently failing, NOT transient
        }
    }

    // The REAL business-logic bean, as the developer writes it -- annotations
    // would appear here in actual Spring code; this class just holds the
    // plain method and its fallback, since the proxy logic is simulated separately.
    static class InventoryService {
        final InventoryClient inventoryClient;
        InventoryService(InventoryClient inventoryClient) { this.inventoryClient = inventoryClient; }
        String checkStock(String sku) { return inventoryClient.checkStock(sku); }
        String checkStockFallback(String sku, Throwable t) {
            return "UNKNOWN (inventory check failed: " + t.getMessage() + ")";
        }
    }

    // Simulates the composed AOP proxy Spring generates for the stacked annotations.
    static class StackedAopProxy {
        State circuitState = State.CLOSED;
        int consecutiveFailures = 0;
        final int failureThreshold = 2;
        final int maxRetryAttempts = 2;

        String invoke(InventoryService service, String sku) {
            try {
                for (int attempt = 1; attempt <= maxRetryAttempts; attempt++) {
                    try {
                        return callThroughCircuitBreaker(service, sku);
                    } catch (Exception e) {
                        if (attempt == maxRetryAttempts) throw e;
                    }
                }
                throw new IllegalStateException("unreachable");
            } catch (Exception finalFailure) {
                return service.checkStockFallback(sku, finalFailure); // proxy dispatches to the fallback method
            }
        }

        String callThroughCircuitBreaker(InventoryService service, String sku) {
            if (circuitState == State.OPEN) throw new RuntimeException("circuit OPEN");
            try {
                String result = service.checkStock(sku);
                consecutiveFailures = 0;
                return result;
            } catch (Exception e) {
                consecutiveFailures++;
                if (consecutiveFailures >= failureThreshold) circuitState = State.OPEN;
                throw e;
            }
        }
    }

    public static void main(String[] args) {
        InventoryClient client = new InventoryClient();
        InventoryService service = new InventoryService(client);
        StackedAopProxy proxy = new StackedAopProxy();

        for (int i = 1; i <= 3; i++) {
            String result = proxy.invoke(service, "sku-123");
            System.out.println("Logical call " + i + ": " + result);
        }
        System.out.println("Real dependency calls made: " + client.callCount);
    }
}
```

How to run: `java SimulatedStackedAnnotations.java`

This simulates exactly what a Spring bean annotated with both `@Retry(name = "inventory")` and `@CircuitBreaker(name = "inventory", fallbackMethod = "checkStockFallback")` would do at runtime. Logical call 1's 2 retry attempts both fail against the persistently broken dependency, tripping the circuit breaker after the 2nd real failure; the retry loop then exhausts and the outer `catch` dispatches to `checkStockFallback`, returning a graceful degraded string instead of propagating the exception. Logical calls 2 and 3 find the circuit already open, so their retry attempts are short-circuited immediately without any further real dependency calls, and each still resolves gracefully via the same fallback dispatch.

## 6. Walkthrough

Trace `SimulatedStackedAnnotations.main`'s logical call 1 in order — mirroring exactly what Spring AOP does for `@Retry` + `@CircuitBreaker(fallbackMethod=...)` on a real bean method. **First**, `proxy.invoke(service, "sku-123")` is called, entering the outer `try` and the retry `for` loop at `attempt=1`.

**`callThroughCircuitBreaker` runs**: `circuitState` is `CLOSED`, so it calls `service.checkStock(sku)` — the actual, unannotated business-logic method — which delegates to `inventoryClient.checkStock`, incrementing `callCount` to 1 and throwing. This is caught inside `callThroughCircuitBreaker`, `consecutiveFailures` becomes 1 (below the threshold of 2), and the exception is re-thrown.

**Back in `invoke`'s retry loop**, `attempt=1`'s failure is caught; since `attempt != maxRetryAttempts(2)`, it loops to `attempt=2` and calls `callThroughCircuitBreaker` again. This time `callCount` reaches 2, `consecutiveFailures` reaches 2 (meeting the threshold), `circuitState` flips to `OPEN`, and the exception propagates again. Since this was the final retry attempt, it escapes the inner `for` loop's `try/catch` entirely and is caught by `invoke`'s outer `try/catch`.

**The outer `catch (Exception finalFailure)` block** now runs `service.checkStockFallback(sku, finalFailure)` — this is precisely what Spring AOP does when a method annotated with a `fallbackMethod` ultimately fails after all its resilience layers have been exhausted: it looks up the named fallback method (matched by parameter types plus a trailing `Throwable`) and invokes it with the original arguments plus the triggering exception, returning its result to the original caller instead of letting the exception surface.

**Logical call 2** begins fresh at `proxy.invoke`, but `circuitState` is still `OPEN` from call 1 (state persists across the proxy instance, matching a real, singleton-scoped Resilience4j circuit breaker registry entry). `attempt=1` calls `callThroughCircuitBreaker`, which immediately throws `"circuit OPEN"` without ever reaching `service.checkStock` — `callCount` stays at 2. `attempt=2` behaves identically. The retry loop exhausts, and the outer catch again dispatches to `checkStockFallback`, this time with a "circuit OPEN" exception as the cause instead of the original "inventory-service down" — the fallback still returns a usable string either way, since it accepts any `Throwable`.

```
call 1: attempt1(real,fail,count=1) -> attempt2(real,fail,count=2,OPENS) -> retries exhausted -> fallback("...service down")
call 2: attempt1(short-circuited) -> attempt2(short-circuited) -> retries exhausted -> fallback("...circuit OPEN")
call 3: (same as call 2)
                                    total real dependency calls: 2
```

## 7. Gotchas & takeaways

> A fallback method's signature must exactly match the annotated method's parameter types, with an additional trailing parameter assignable from the thrown exception type — a mismatched signature causes Resilience4j to fail to find the fallback at startup (or silently not apply it, depending on version), which is a common source of "the fallback never seems to run" bugs.

- Annotations keep resilience concerns out of business-logic method bodies, applied transparently via a Spring AOP proxy — but this means calling an annotated method from *within the same class* (self-invocation) bypasses the proxy entirely, since Spring AOP only intercepts calls that go through the proxy object from outside.
- Stacking annotations composes them the same way the programmatic API does; the same ordering considerations from [bounded retries + circuit breaker ordering](0292-bounded-retries-circuit-breaker-combination-ordering.md) apply — Resilience4j's Spring integration applies them in a well-documented, consistent order.
- The `name` attribute on each annotation must match a named configuration block in `application.yml` (see [Resilience4j config via application.yml](0296-resilience4j-config-via-application-yml.md)); an unrecognized name falls back to that module's global default configuration.
- Annotation-based usage requires the target method's class to be a genuine Spring-managed bean going through a proxy — plain `new`-instantiated objects outside the Spring context, as necessarily used in this topic's runnable examples, never get the annotation behavior applied automatically, which is exactly why the examples simulate the proxy's behavior by hand.
