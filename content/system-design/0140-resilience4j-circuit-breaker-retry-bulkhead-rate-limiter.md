---
card: system-design
gi: 140
slug: resilience4j-circuit-breaker-retry-bulkhead-rate-limiter
title: Resilience4j (circuit breaker, retry, bulkhead, rate limiter)
---

## 1. What it is

**Resilience4j** is a Java library that provides ready-made, well-tested implementations of the resilience patterns already covered in this section: [circuit breaker](0136-circuit-breaker.md), [retry](0135-retries-with-exponential-backoff-jitter.md), [bulkhead](0137-bulkhead-isolation.md), and rate limiter, plus a time limiter for timeouts. In a Spring Boot application, you apply these with a single annotation on a method, or by wrapping a call programmatically — instead of hand-writing the state machines and counters these patterns require.

## 2. Why & when

The circuit breaker's closed/open/half-open state machine, the retry loop's exponential backoff and jitter math, and a bulkhead's pool management are all non-trivial to implement correctly from scratch, and easy to get subtly wrong (as the earlier examples' manual state tracking hinted at). Resilience4j provides these as configurable, tested building blocks. Use it in any Spring Boot service making calls to external dependencies that need protecting — it is the standard, idiomatic way to apply these patterns in the Spring ecosystem, and combines naturally with the resilience concepts already covered.

## 3. Core concept

- **`@CircuitBreaker(name = "...")`:** wraps a method with circuit-breaker logic; configure the failure-rate threshold, sliding window size, and wait duration in open state via `application.yml` properties.
- **`@Retry(name = "...")`:** wraps a method with retry logic, including exponential backoff, configured declaratively rather than hand-coded.
- **`@Bulkhead(name = "...")`:** limits concurrent calls to a method to a configured maximum, implementing the isolation pattern directly.
- **`@RateLimiter(name = "...")`:** limits how many calls to a method are permitted per time window, protecting a dependency (or protecting yourself) from being overwhelmed.
- **Combining annotations:** these annotations can be stacked on one method (e.g. `@CircuitBreaker` + `@Retry` + a fallback method), and Resilience4j applies them in a defined order — typically the circuit breaker wraps the retry, so retries do not happen at all once the breaker is open.
- **Fallback methods:** each annotation supports a `fallbackMethod` attribute naming a method with a matching signature (plus a `Throwable` parameter) to call when the protected call ultimately fails — directly implementing the [fallback](0138-fallbacks-graceful-degradation.md) pattern.

## 4. Diagram

```
  @CircuitBreaker(name="recommendations", fallbackMethod="getDefaultRecommendations")
  @Retry(name="recommendations")
  public List<String> getRecommendations(String userId) {
      return recommendationsClient.fetch(userId);  // the real, protected call
  }

  public List<String> getDefaultRecommendations(String userId, Throwable t) {
      return List.of("Popular Item X", "Popular Item Y");  // the fallback
  }

  Call flow:
  caller -> @CircuitBreaker check (closed? proceed) -> @Retry wraps the real call
         -> real call fails -> retry per policy -> still fails / breaker opens
         -> Resilience4j automatically invokes getDefaultRecommendations(...)
```
*Caption: annotations declare the resilience policy; Resilience4j handles the actual state machine, retry loop, and fallback dispatch underneath.*

## 5. Runnable example

**Level 1 — Basic.** Model `@Retry`-style behavior: a method wrapped with automatic retry on failure.

**Level 2 — Model `@CircuitBreaker`-style behavior.** Combine with retry, so the breaker can stop retries once it trips.

**Level 3 — Fallback dispatch.** When the protected call still fails, automatically invoke the configured fallback method.

```java
// Resilience4jDemo.java
import java.util.*;
import java.util.function.*;

public class Resilience4jDemo {

    // Models what @Retry(name="...") does around a method call.
    static <T> T withRetry(int maxAttempts, Supplier<T> call) {
        RuntimeException lastError = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return call.get();
            } catch (RuntimeException e) {
                lastError = e;
                System.out.println("  [Retry] attempt " + attempt + " failed: " + e.getMessage());
            }
        }
        throw lastError;
    }

    // Models a simple @CircuitBreaker(name="...") - trips after too many consecutive failures.
    static boolean breakerOpen = false;
    static int consecutiveFailures = 0;
    static int breakerThreshold = 3;

    static <T> T withCircuitBreaker(Supplier<T> call, Function<Throwable, T> fallbackMethod) {
        if (breakerOpen) {
            System.out.println("  [CircuitBreaker] OPEN - skipping real call, going straight to fallback");
            return fallbackMethod.apply(new RuntimeException("circuit open"));
        }
        try {
            T result = call.get();
            consecutiveFailures = 0;
            return result;
        } catch (RuntimeException e) {
            consecutiveFailures++;
            if (consecutiveFailures >= breakerThreshold) {
                breakerOpen = true;
                System.out.println("  [CircuitBreaker] threshold reached - breaker now OPEN");
            }
            return fallbackMethod.apply(e); // this call's own failure still gets the fallback
        }
    }

    static List<String> getDefaultRecommendations(Throwable t) {
        return List.of("Popular Item X", "Popular Item Y");
    }

    static int callCount = 0;
    static List<String> getRecommendations(String userId) {
        callCount++;
        throw new RuntimeException("recommendations service down (call #" + callCount + ")");
    }

    public static void main(String[] args) {
        // Level 1 & 2: @Retry wrapped inside @CircuitBreaker - each user request retries, then falls back.
        for (int i = 1; i <= 4; i++) {
            System.out.println("--- request " + i + " for user-" + i + " ---");
            List<String> result = withCircuitBreaker(
                () -> withRetry(2, () -> getRecommendations("user-" + 1)), // retry twice per request
                Resilience4jDemo::getDefaultRecommendations // Level 3: fallback method
            );
            System.out.println("final result: " + result);
        }
    }
}
```

**How to run:** save as `Resilience4jDemo.java`, then run `java Resilience4jDemo.java`. (A real Spring Boot app would annotate the method directly: `@CircuitBreaker(name = "recommendations", fallbackMethod = "getDefaultRecommendations") @Retry(name = "recommendations") public List<String> getRecommendations(String userId) { ... }`, with policy details configured under `resilience4j.circuitbreaker` / `resilience4j.retry` in `application.yml`, using the `spring-boot-starter-aop` and `resilience4j-spring-boot3` dependencies.)

## 6. Walkthrough

1. `withRetry` models `@Retry`: it calls the supplied `call` up to `maxAttempts` times, catching and logging each failure, and re-throwing only after all attempts are exhausted.
2. `withCircuitBreaker` models `@CircuitBreaker`: while `breakerOpen` is `false`, it invokes `call` (which internally runs the retry logic), and on failure increments `consecutiveFailures`, tripping `breakerOpen = true` once `breakerThreshold` is reached.
3. Requests 1 through 3 each run `withRetry(2, ...)` inside `withCircuitBreaker`; since `getRecommendations` always throws, each request logs 2 failed retry attempts, then the circuit breaker's own failure count increments, and the fallback `getDefaultRecommendations` is invoked, returning the static list.
4. By request 3, `consecutiveFailures` reaches `breakerThreshold` (3), so `breakerOpen` flips to `true` before that request's fallback even runs.
5. Request 4 hits the `if (breakerOpen)` branch at the very top of `withCircuitBreaker` and skips straight to the fallback — critically, `withRetry` (and therefore `getRecommendations`) is never even called for this request, confirming that Resilience4j's real behavior (a tripped breaker skipping the wrapped retry entirely) is captured correctly: the breaker stops the retries from happening at all, rather than letting them run and fail every time.

## 7. Gotchas & takeaways

> Gotcha: stacking `@CircuitBreaker` and `@Retry` on the same method without understanding their applied order can accidentally let retries happen *after* the breaker has already opened, defeating the breaker's whole purpose of failing fast — Resilience4j's documented default order wraps retry inside the circuit breaker (as modeled here), so verify your specific annotation order matches the intended behavior, especially when combining more than two of these patterns.

- Resilience4j provides tested, configurable implementations of circuit breaker, retry, bulkhead, and rate limiter, avoiding the need to hand-implement these state machines.
- Spring Boot applies these declaratively via annotations (`@CircuitBreaker`, `@Retry`, `@Bulkhead`, `@RateLimiter`), each configurable through `application.yml` properties.
- A `fallbackMethod` on these annotations directly implements the fallback pattern, automatically invoked when the protected call ultimately fails.
- Related concepts: [Circuit breaker](0136-circuit-breaker.md), [Retries with exponential backoff & jitter](0135-retries-with-exponential-backoff-jitter.md), and [Bulkhead isolation](0137-bulkhead-isolation.md) (the patterns this library implements), [Spring Cloud CircuitBreaker abstraction](0141-spring-cloud-circuitbreaker-abstraction.md) (a broker-agnostic layer that can sit on top of Resilience4j).
