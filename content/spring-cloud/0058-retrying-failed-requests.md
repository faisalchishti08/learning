---
card: spring-cloud
gi: 58
slug: retrying-failed-requests
title: "Retrying failed requests"
---

## 1. What it is

Spring Cloud LoadBalancer integrates with Spring Retry to automatically retry a failed call — and critically, it can retry on a *different* instance than the one that just failed, not just re-attempt the same doomed instance, distinguishing "retry the same instance" (`retryOnSameServiceInstance`) from "retry on the next instance the load balancer picks" (`retryOnNextServiceInstance`).

```properties
spring.cloud.loadbalancer.retry.enabled=true
spring.cloud.loadbalancer.retry.retry-on-all-operations=false
spring.cloud.loadbalancer.retry.max-retries-on-same-service-instance=0
spring.cloud.loadbalancer.retry.max-retries-on-next-service-instance=2
```

## 2. Why & when

A failed call to one specific instance often says nothing about whether *other* instances of the same service are healthy — an instance might be individually overloaded, mid-restart, or network-partitioned, while its siblings are perfectly fine. Retrying against a different, freshly-selected instance (rather than hammering the same failed one again) turns many single-instance failures into successes the caller never even notices, without needing the Gateway-level `Retry` filter (covered earlier) to be involved at all — this retry happens at the client-side load-balancing layer, for any code using `@LoadBalanced` clients or Feign.

Configure LoadBalancer retry deliberately when:

- Calls to a downstream service occasionally fail due to an individual instance's transient trouble, and other instances are typically available and healthy — retrying on a different instance meaningfully improves overall success rate.
- The operation being retried is safe to retry — `retry-on-all-operations=false` (the default) means only idempotent-by-convention `GET` requests are retried automatically; retrying a `POST` needs deliberate, explicit configuration given the double-execution risk covered in the earlier Gateway `Retry` card.
- `max-retries-on-same-service-instance` versus `max-retries-on-next-service-instance` need distinct tuning — same-instance retries help with a fleeting timeout; next-instance retries help when the specific instance is genuinely unhealthy.

## 3. Core concept

```
 call fails against instance A
        |
        |-- retryOnSameServiceInstance (up to max-retries-on-same-service-instance)
        |       retry against the SAME instance A -- good for a one-off blip
        |
        |-- retryOnNextServiceInstance (up to max-retries-on-next-service-instance)
                LoadBalancer picks a DIFFERENT instance (B, C, ...) and retries there
                -- good when instance A itself is the problem
```

Same-instance retries assume the failure was transient; next-instance retries assume the specific instance itself might be unhealthy and route around it.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A failed call against one instance is retried first on the same instance for transient blips, then on a different instance selected fresh by the load balancer if the instance itself appears unhealthy">
  <rect x="30" y="20" width="160" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">call fails -&gt; instance A</text>

  <line x1="190" y1="40" x2="240" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a58)"/>

  <rect x="245" y="20" width="180" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="335" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">retry SAME instance A</text>
  <text x="335" y="54" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">up to max-retries-on-same</text>

  <line x1="335" y1="60" x2="335" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a58)"/>
  <text x="380" y="80" fill="#8b949e" font-size="6.5" font-family="sans-serif">still failing</text>

  <rect x="245" y="95" width="180" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="335" y="115" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">retry DIFFERENT instance B</text>
  <text x="335" y="129" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">up to max-retries-on-next</text>

  <defs><marker id="a58" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two retry stages, in order: same instance first (for blips), then a freshly-chosen different instance (for genuinely unhealthy ones).

## 5. Runnable example

The scenario: retry calls to `billing-service` intelligently. Start with no retry (a single failure is fatal), then add same-instance retry for a transient blip, then add next-instance retry when the same instance keeps failing.

### Level 1 — Basic

No retry — a single failure against one instance is final.

```java
import java.util.function.Supplier;

public class LoadBalancerRetryLevel1 {
    record Response(int status) {}

    static Response call(String instance, Supplier<Response> backend) {
        return backend.get(); // one attempt, no retry
    }

    public static void main(String[] args) {
        Supplier<Response> flakyInstance1 = () -> new Response(503); // this instance is having a transient blip

        Response result = call("10.0.2.1:8080", flakyInstance1);
        System.out.println("result: " + result.status()); // 503 -- caller sees the failure directly
    }
}
```

How to run: `java LoadBalancerRetryLevel1.java`

One transient failure against one instance is immediately surfaced to the caller — even though, in reality, the same instance (or a sibling) might well succeed on a second attempt moments later.

### Level 2 — Intermediate

Add same-instance retry: re-attempt against the exact same instance, up to a limit, before giving up.

```java
import java.util.function.Supplier;

public class LoadBalancerRetryLevel2 {
    record Response(int status) {}

    static Response callWithSameInstanceRetry(String instance, Supplier<Response> backend, int maxRetries) {
        Response last = null;
        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            last = backend.get();
            if (last.status() < 500) return last; // success -- stop retrying
            System.out.println("attempt " + attempt + " against " + instance + " -> " + last.status());
        }
        return last; // exhausted same-instance retries, still failing
    }

    public static void main(String[] args) {
        int[] callCount = {0};
        Supplier<Response> instance1 = () -> {
            callCount[0]++;
            return callCount[0] < 2 ? new Response(503) : new Response(200); // fails once, then succeeds
        };

        Response result = callWithSameInstanceRetry("10.0.2.1:8080", instance1, 1);
        System.out.println("final result: " + result.status()); // 200 -- the retry against the SAME instance worked
    }
}
```

How to run: `java LoadBalancerRetryLevel2.java`

`instance1` fails on its first call but succeeds on the second — `callWithSameInstanceRetry` retries against the exact same instance (`maxRetries=1` means one retry after the initial attempt) and catches the transient blip, returning `200` to the caller without ever needing to involve a different instance at all.

### Level 3 — Advanced

Add next-instance retry: when same-instance retries are exhausted and the instance is still failing, have LoadBalancer pick a genuinely different instance and retry there.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

public class LoadBalancerRetryLevel3 {
    record Response(int status) {}

    static List<String> instances = List.of("10.0.2.1:8080", "10.0.2.2:8080", "10.0.2.3:8080");
    static AtomicInteger rrCounter = new AtomicInteger(0);

    static String pickInstance() {
        return instances.get(rrCounter.getAndIncrement() % instances.size());
    }

    static Response callInstance(String instance, Map<String, Supplier<Response>> backends) {
        return backends.get(instance).get();
    }

    static Response callWithFullRetry(Map<String, Supplier<Response>> backends,
                                       int maxRetriesSameInstance, int maxRetriesNextInstance) {
        int nextInstanceAttempts = 0;
        while (true) {
            String instance = pickInstance();
            Response result = null;
            for (int sameAttempt = 0; sameAttempt <= maxRetriesSameInstance; sameAttempt++) {
                result = callInstance(instance, backends);
                System.out.println("try " + instance + " (same-instance attempt " + sameAttempt + ") -> " + result.status());
                if (result.status() < 500) return result; // success anywhere -- done
            }
            nextInstanceAttempts++;
            if (nextInstanceAttempts > maxRetriesNextInstance) return result; // exhausted all retry budget
        }
    }

    public static void main(String[] args) {
        Map<String, Supplier<Response>> backends = new HashMap<>();
        backends.put("10.0.2.1:8080", () -> new Response(503)); // permanently down
        backends.put("10.0.2.2:8080", () -> new Response(503)); // also permanently down
        backends.put("10.0.2.3:8080", () -> new Response(200)); // healthy

        Response result = callWithFullRetry(backends, 0, 2);
        System.out.println("final result: " + result.status());
    }
}
```

How to run: `java LoadBalancerRetryLevel3.java`

`.1` and `.2` are both permanently down, and `.3` is healthy. With `max-retries-on-same-service-instance=0` (no same-instance retry) and `max-retries-on-next-service-instance=2`, the retry loop picks a fresh instance via round-robin on each attempt: `.1` fails, moves to a next-instance retry against `.2`, which also fails, moves to a second next-instance retry against `.3`, which finally succeeds. The caller ultimately gets `200`, never seeing the two intermediate failures directly.

## 6. Walkthrough

Trace `callWithFullRetry`'s execution in Level 3.

1. The outer `while (true)` loop begins its first iteration. `pickInstance()` reads the round-robin counter (`0`), picks `instances.get(0)` = `10.0.2.1:8080`, and increments the counter to `1`.
2. The inner `for` loop runs for `sameAttempt=0` (the only iteration, since `maxRetriesSameInstance=0`). `callInstance` invokes `.1`'s backend, returning `503`. Since `503 >= 500`, the success check fails, and the inner loop ends (no more same-instance attempts configured).
3. Back in the outer loop, `nextInstanceAttempts` increments to `1`. Since `1 > 2` is false, the `while` loop continues to a second iteration rather than giving up.
4. `pickInstance()` now reads counter `1`, picks `instances.get(1)` = `10.0.2.2:8080`, increments to `2`. The inner loop calls `.2`'s backend, also returning `503` — this instance is down too. `nextInstanceAttempts` becomes `2`; still `<= 2`, so the outer loop continues once more.
5. `pickInstance()` reads counter `2`, picks `instances.get(2)` = `10.0.2.3:8080`, increments to `3`. The inner loop calls `.3`'s backend, returning `200` — since `200 < 500`, the success condition is met, and `callWithFullRetry` returns this response immediately, short-circuiting any further retries.
6. The final `println` shows `200` — from the calling code's perspective, this whole two-failure, three-instance retry sequence was completely transparent; only the eventual success (or, had every instance failed, the final failure after exhausting the retry budget) is ever visible outside `callWithFullRetry`.

```
attempt 1: instance .1 -> 503 (same-instance retries exhausted, 0 configured) -> next-instance retry
attempt 2: instance .2 -> 503 (same) -> next-instance retry
attempt 3: instance .3 -> 200 -> SUCCESS, return immediately
```

## 7. Gotchas & takeaways

> **Gotcha:** next-instance retry, by picking a fresh instance via the same round-robin/random algorithm covered earlier, could in principle re-select an instance that already failed earlier in the same retry sequence if that instance is still in the candidate pool — the examples here avoid this by having distinct, deterministic instances, but a real implementation typically excludes already-tried instances from subsequent picks within one logical request's retry sequence to avoid wasting a retry attempt on a known-bad instance.

- `retryOnSameServiceInstance` and `retryOnNextServiceInstance` address two different failure hypotheses — a fleeting blip on an otherwise-healthy instance versus a genuinely unhealthy specific instance — and most real configurations use both together, same-instance retries first (cheap, fast) before falling back to next-instance retries (more expensive, but routes around a truly bad instance).
- Retry is disabled for non-idempotent operations by default (`retry-on-all-operations=false`) — the same double-execution risk covered in the Gateway `Retry` filter card applies identically here; enabling retry for `POST`/`PUT`/`DELETE` requires deliberate consideration of idempotency.
- This retry mechanism operates purely client-side, independent of whether a Gateway `Retry` filter is also configured somewhere upstream — the two can coexist, though stacking too many retry layers across a call chain risks amplifying load on a struggling backend rather than helping it recover.
- Because retries happen transparently inside the `@LoadBalanced` client or Feign call, application code calling a downstream service doesn't need to implement any of its own retry logic — it's entirely a configuration concern.
