---
card: system-design
gi: 141
slug: spring-cloud-circuitbreaker-abstraction
title: Spring Cloud CircuitBreaker abstraction
---

## 1. What it is

**Spring Cloud CircuitBreaker** is a thin, unified API for applying a circuit breaker to a call, regardless of which underlying implementation actually provides it — [Resilience4j](0140-resilience4j-circuit-breaker-retry-bulkhead-rate-limiter.md) or Sentinel. Your code calls `circuitBreakerFactory.create("name").run(call, fallback)`, and the specific breaker library doing the real work underneath is determined by which starter dependency is on the classpath — the same "code against an abstraction, plug in an implementation" idea already seen in [Spring Cloud Stream's binder abstraction](0121-spring-cloud-stream-binder-abstraction.md).

## 2. Why & when

Coding directly against Resilience4j's own annotations ties your business logic to that specific library's API. Spring Cloud CircuitBreaker's abstraction lets you write the protected call once, using its generic `run` method, and swap which underlying circuit-breaker implementation actually executes it purely through a dependency and configuration change. Use it when you want your core call-protection logic decoupled from a specific resilience library's API — the same motivation as any binder or adapter abstraction: minimize how much of your code needs to change if the underlying implementation choice changes later.

## 3. Core concept

- **`CircuitBreakerFactory`:** an injectable Spring bean; call `circuitBreakerFactory.create("circuitBreakerName")` to get a `CircuitBreaker` instance configured under that name.
- **`.run(Supplier<T> toRun, Function<Throwable, T> fallback)`:** the generic method that actually executes the protected call, invoking `fallback` automatically if `toRun` fails or the breaker is open — this single method signature is the entire abstraction surface your business code needs to know about.
- **Implementation-specific configuration stays separate:** the *behavior* (failure threshold, wait duration) is still configured through the specific implementation's own configuration mechanism (e.g. Resilience4j's `application.yml` properties), but your calling *code* never references Resilience4j's types directly.
- **Swapping implementations:** changing from the Resilience4j starter to a different starter (e.g. Sentinel) is a dependency and configuration change; the code calling `circuitBreakerFactory.create(...).run(...)` does not change at all.
- **Named circuit breakers:** each call to `create("name")` retrieves (or creates) a distinct, independently-tracked breaker for that name, letting you protect several different dependencies with separate breaker states through the same API.

## 4. Diagram

```
   Your code (implementation-agnostic):

   CircuitBreaker cb = circuitBreakerFactory.create("recommendations");
   List<String> result = cb.run(
       () -> recommendationsClient.fetch(userId),      // the real call
       throwable -> List.of("Popular Item X", "Popular Item Y")  // the fallback
   );

              |
              v
   Spring Cloud CircuitBreaker abstraction layer
              |
       +------+------+
       v             v
  Resilience4j    Sentinel       <- swap this dependency to change
  implementation  implementation    implementation; the code above is UNCHANGED
```
*Caption: the same `run(call, fallback)` call works regardless of which circuit-breaker library is actually wired in underneath.*

## 5. Runnable example

**Level 1 — Basic.** An implementation-agnostic `run(call, fallback)` method, backed by a pluggable breaker implementation.

**Level 2 — Swap the underlying implementation.** The same calling code works identically against two different simulated breaker backends.

**Level 3 — Named, independent breakers.** Two different dependencies get their own independently-tracked breaker state through the same factory API.

```java
// SpringCloudCircuitBreakerDemo.java
import java.util.*;
import java.util.function.*;

public class SpringCloudCircuitBreakerDemo {

    // The abstraction: any implementation just needs to provide this shape.
    interface CircuitBreaker {
        <T> T run(Supplier<T> toRun, Function<Throwable, T> fallback);
    }

    // A Resilience4j-style implementation, hidden behind the abstraction.
    static class Resilience4jStyleBreaker implements CircuitBreaker {
        public <T> T run(Supplier<T> toRun, Function<Throwable, T> fallback) {
            try {
                System.out.println("  [Resilience4j-backed breaker] attempting call");
                return toRun.get();
            } catch (RuntimeException e) {
                System.out.println("  [Resilience4j-backed breaker] call failed, invoking fallback");
                return fallback.apply(e);
            }
        }
    }

    // A Sentinel-style implementation, ALSO hidden behind the same abstraction.
    static class SentinelStyleBreaker implements CircuitBreaker {
        public <T> T run(Supplier<T> toRun, Function<Throwable, T> fallback) {
            try {
                System.out.println("  [Sentinel-backed breaker] attempting call");
                return toRun.get();
            } catch (RuntimeException e) {
                System.out.println("  [Sentinel-backed breaker] call failed, invoking fallback");
                return fallback.apply(e);
            }
        }
    }

    // Models CircuitBreakerFactory - hands out a named breaker, backed by whichever implementation is configured.
    static class CircuitBreakerFactory {
        Map<String, CircuitBreaker> breakersByName = new HashMap<>();
        Supplier<CircuitBreaker> implementationSupplier; // whichever starter is "on the classpath"

        CircuitBreakerFactory(Supplier<CircuitBreaker> implementationSupplier) {
            this.implementationSupplier = implementationSupplier;
        }

        CircuitBreaker create(String name) {
            return breakersByName.computeIfAbsent(name, n -> implementationSupplier.get());
        }
    }

    // Your business logic - written ONCE, referencing only the abstraction, never a specific breaker library.
    static List<String> getRecommendations(CircuitBreakerFactory factory, boolean serviceHealthy) {
        CircuitBreaker cb = factory.create("recommendations");
        return cb.run(
            () -> {
                if (!serviceHealthy) throw new RuntimeException("recommendations service down");
                return List.of("Personalized Item A", "Personalized Item B");
            },
            throwable -> List.of("Popular Item X", "Popular Item Y")
        );
    }

    public static void main(String[] args) {
        // Level 1 & 2: the SAME business logic method, run against two different underlying implementations.
        CircuitBreakerFactory factoryWithResilience4j = new CircuitBreakerFactory(Resilience4jStyleBreaker::new);
        System.out.println("--- configured with Resilience4j-style breaker ---");
        System.out.println("result: " + getRecommendations(factoryWithResilience4j, false));

        CircuitBreakerFactory factoryWithSentinel = new CircuitBreakerFactory(SentinelStyleBreaker::new);
        System.out.println("--- configured with Sentinel-style breaker (dependency swap only) ---");
        System.out.println("result: " + getRecommendations(factoryWithSentinel, false));

        // Level 3: named, independent breakers for two different dependencies via the same factory.
        CircuitBreakerFactory factory = new CircuitBreakerFactory(Resilience4jStyleBreaker::new);
        CircuitBreaker recommendationsBreaker = factory.create("recommendations");
        CircuitBreaker paymentsBreaker = factory.create("payments");
        System.out.println("recommendations breaker and payments breaker are distinct instances: "
            + (recommendationsBreaker != paymentsBreaker));
        System.out.println("calling create(\"recommendations\") again returns the SAME instance: "
            + (factory.create("recommendations") == recommendationsBreaker));
    }
}
```

**How to run:** save as `SpringCloudCircuitBreakerDemo.java`, then run `java SpringCloudCircuitBreakerDemo.java`. (A real Spring Boot app would inject `CircuitBreakerFactory` as a bean, and the actual implementation used would be determined entirely by which starter — `spring-cloud-circuitbreaker-resilience4j` or `-sentinel` — is on the classpath.)

## 6. Walkthrough

1. `getRecommendations` is written once, calling only `factory.create("recommendations")` and `cb.run(...)` — it never references `Resilience4jStyleBreaker` or `SentinelStyleBreaker` directly, modeling genuinely implementation-agnostic business logic.
2. The first call passes `factoryWithResilience4j`, whose `implementationSupplier` produces `Resilience4jStyleBreaker` instances; the printed log line confirms this specific implementation handled the call and its fallback.
3. The second call passes `factoryWithSentinel` instead — the exact same `getRecommendations` method runs unchanged, but the printed log line now shows the Sentinel-style implementation handling the identical call and fallback logic.
4. Both calls produce the identical final result (`[Popular Item X, Popular Item Y]`), confirming the business outcome is unaffected by which implementation was plugged in — only the underlying mechanism handling the call differed.
5. Level 3 demonstrates the factory's named-instance behavior: `factory.create("recommendations")` and `factory.create("payments")` return different objects (tracked independently), while calling `create("recommendations")` a second time returns the exact same instance as before — confirming each named breaker maintains its own independent state, letting one dependency's breaker trip without affecting another's.

## 7. Gotchas & takeaways

> Gotcha: the abstraction covers the common `run(call, fallback)` operation well, but implementation-specific tuning (Resilience4j's sliding window type, Sentinel's specific flow-control rules) still happens through that implementation's own configuration mechanism, not through the abstraction itself — switching implementations can mean re-expressing the same tuning intent in a different configuration format, even though the calling code stays identical.

- Spring Cloud CircuitBreaker provides one generic `run(call, fallback)` API, letting business logic stay decoupled from a specific circuit-breaker library like Resilience4j or Sentinel.
- Swapping the underlying implementation is a dependency and configuration change; the calling code that uses `CircuitBreakerFactory` does not need to change.
- Named breakers, retrieved via `create(name)`, each track their own independent state, letting several distinct dependencies share the same factory API safely.
- Related concepts: [Resilience4j (circuit breaker, retry, bulkhead, rate limiter)](0140-resilience4j-circuit-breaker-retry-bulkhead-rate-limiter.md) (a common underlying implementation this abstraction wraps), [Spring Cloud Stream binder abstraction](0121-spring-cloud-stream-binder-abstraction.md) (the same broker/implementation-agnostic pattern applied to messaging).
