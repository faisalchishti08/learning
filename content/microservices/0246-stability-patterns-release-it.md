---
card: microservices
gi: 246
slug: stability-patterns-release-it
title: "Stability patterns (Release It!)"
---

## 1. What it is

Stability patterns are a named catalog of resilience techniques popularized by Michael Nygard's book *Release It!* — circuit breakers, bulkheads, timeouts, steady state, fail fast, among others — that together form a shared vocabulary and toolkit for building systems that survive production failure conditions, many of which have since become standard, built-in features of frameworks like Resilience4j and Spring Cloud.

## 2. Why & when

Before this vocabulary became widely shared, teams facing the same recurring production failure modes — a slow dependency dragging down a caller, a resource leak accumulating over days until a restart, one tenant's runaway load starving everyone else — often reinvented ad-hoc, one-off fixes for each incident without recognizing they were solving the same small set of underlying problems repeatedly. *Release It!* named and catalogued these recurring problems and their solutions, giving the industry a shared vocabulary: calling something "a bulkhead" or "a circuit breaker" now communicates a specific, well-understood technique instantly, rather than requiring a fresh explanation each time. This section of the course covers several of these patterns individually and in depth — this topic serves as the map connecting them to their common origin and to each other.

Reach for this shared vocabulary when designing or discussing resilience — naming a problem as "we need a bulkhead here" or "this needs a circuit breaker" communicates a specific, well-understood solution shape immediately to anyone familiar with the pattern catalog, rather than requiring the underlying mechanism to be re-explained from scratch every time.

## 3. Core concept

Each stability pattern addresses a specific, recurring failure mode by name, and most of them work by limiting or containing something — the *rate* of calls (circuit breaker), the *shared resources* one dependency can consume ([bulkhead](0242-fault-isolation.md)), the *time* a call is allowed to take (timeout), or the *accumulation* of resource use over a running process's lifetime (steady state) — turning an open-ended failure risk into a bounded, contained one.

```java
// a QUICK map of several Release It! patterns to their core mechanism:

// TIMEOUT -- bound the TIME a call is allowed to take
future.get(2, TimeUnit.SECONDS); // never wait indefinitely

// CIRCUIT BREAKER -- bound the RATE of calls to a failing dependency
CircuitBreaker breaker = CircuitBreaker.ofDefaults("dependency");
breaker.executeSupplier(() -> callDependency());

// BULKHEAD -- bound the SHARED RESOURCES one dependency can consume
Bulkhead bulkhead = Bulkhead.of("dependency", BulkheadConfig.custom().maxConcurrentCalls(10).build());

// FAIL FAST -- bound how LONG a doomed request is allowed to proceed before being rejected
if (!isValidRequest(request)) throw new BadRequestException(); // reject immediately, don't waste downstream resources on it
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four Release It! stability patterns each bound a different dimension of risk -- timeout bounds time, circuit breaker bounds call rate to a failing dependency, bulkhead bounds shared resource consumption, and fail fast bounds how long a doomed request proceeds before rejection" >
  <rect x="20" y="20" width="140" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Timeout</text>
  <text x="90" y="58" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">bounds TIME</text>

  <rect x="175" y="20" width="140" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="245" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Circuit breaker</text>
  <text x="245" y="58" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">bounds CALL RATE</text>

  <rect x="330" y="20" width="140" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="400" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Bulkhead</text>
  <text x="400" y="58" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">bounds RESOURCE SHARE</text>

  <rect x="485" y="20" width="135" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="552" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Fail fast</text>
  <text x="552" y="58" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">bounds WASTED WORK</text>

  <rect x="150" y="115" width="340" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="140" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Shared goal: turn open-ended risk into a bounded one</text>

  <line x1="90" y1="78" x2="270" y2="113" stroke="#8b949e" marker-end="url(#arr246)"/>
  <line x1="245" y1="78" x2="300" y2="113" stroke="#8b949e" marker-end="url(#arr246)"/>
  <line x1="400" y1="78" x2="350" y2="113" stroke="#8b949e" marker-end="url(#arr246)"/>
  <line x1="552" y1="78" x2="380" y2="113" stroke="#8b949e" marker-end="url(#arr246)"/>

  <defs>
    <marker id="arr246" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each named pattern bounds a different dimension of risk, but all share the same underlying goal.

## 5. Runnable example

Scenario: a dependency-calling client built with none of these patterns applied (unbounded time, unbounded calls, unbounded shared resource use, and wasted work on doomed requests), refactored to layer in timeout and fail-fast bounding, and finally combining circuit breaker and bulkhead protection together — demonstrating how these named patterns compose into one coherent defense rather than being isolated, unrelated techniques.

### Level 1 — Basic

```java
// File: NoStabilityPatterns.java -- NOTHING is bounded: calls can hang
// indefinitely, and a clearly INVALID request is still sent downstream,
// wasting work that could have been rejected immediately.
import java.util.concurrent.*;

public class NoStabilityPatterns {
    static ExecutorService pool = Executors.newFixedThreadPool(2);

    static String callDependency(String request) throws InterruptedException {
        Thread.sleep(1000); // simulates a hang -- NOTHING bounds how long this call can take
        return "processed: " + request;
    }

    public static void main(String[] args) throws Exception {
        String invalidRequest = null; // an OBVIOUSLY invalid request

        // NO fail-fast check -- this doomed request proceeds to the downstream call anyway
        Future<String> future = pool.submit(() -> callDependency(invalidRequest)); // wastes a full 1000ms on something that will fail regardless
        try {
            String result = future.get(); // NO timeout -- would wait FOREVER if the call truly hung
            System.out.println(result);
        } catch (Exception e) {
            System.out.println("Failed after wasting time: " + e.getClass().getSimpleName());
        }
        pool.shutdown();
    }
}
```

**How to run:** `javac NoStabilityPatterns.java && java NoStabilityPatterns` (JDK 17+).

### Level 2 — Intermediate

```java
// File: TimeoutAndFailFast.java -- adds TWO patterns: FAIL FAST (reject
// obviously doomed requests immediately) and TIMEOUT (bound how long
// a call is allowed to take).
import java.util.concurrent.*;

public class TimeoutAndFailFast {
    static ExecutorService pool = Executors.newFixedThreadPool(2);

    static String callDependency(String request) throws InterruptedException {
        Thread.sleep(1000);
        return "processed: " + request;
    }

    static String handleRequest(String request) throws Exception {
        if (request == null) { // FAIL FAST -- reject immediately, don't waste downstream resources
            throw new IllegalArgumentException("invalid request rejected immediately, no downstream call made");
        }
        Future<String> future = pool.submit(() -> callDependency(request));
        return future.get(500, TimeUnit.MILLISECONDS); // TIMEOUT -- bound how long we wait
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        try {
            handleRequest(null); // now rejected INSTANTLY -- fail fast
        } catch (IllegalArgumentException e) {
            long elapsed = System.currentTimeMillis() - start;
            System.out.println("Rejected in " + elapsed + "ms: " + e.getMessage());
        }
        pool.shutdown();
    }
}
```

**How to run:** `javac TimeoutAndFailFast.java && java TimeoutAndFailFast` (JDK 17+).

Expected output:
```
Rejected in 0ms: invalid request rejected immediately, no downstream call made
```

### Level 3 — Advanced

```java
// File: CircuitBreakerPlusBulkheadComposed.java -- CIRCUIT BREAKER and
// BULKHEAD composed TOGETHER, showing how Release It! patterns are
// MEANT to be layered, each protecting against a DIFFERENT dimension
// of risk simultaneously.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class CircuitBreakerPlusBulkheadComposed {
    static ExecutorService dedicatedBulkheadPool = Executors.newFixedThreadPool(3); // BULKHEAD -- isolated resource pool
    static AtomicBoolean breakerOpen = new AtomicBoolean(false); // CIRCUIT BREAKER -- bounds call rate to a failing dependency
    static AtomicInteger consecutiveFailures = new AtomicInteger(0);

    static String callFailingDependency() { throw new RuntimeException("dependency is down"); }

    static String protectedCall(String requestId) {
        if (breakerOpen.get()) return "FALLBACK (breaker open) for " + requestId; // CIRCUIT BREAKER short-circuits

        try {
            Future<String> future = dedicatedBulkheadPool.submit(CircuitBreakerPlusBulkheadComposed::callFailingDependency); // BULKHEAD-isolated call
            return future.get(200, TimeUnit.MILLISECONDS); // TIMEOUT, bounding this call too
        } catch (Exception e) {
            if (consecutiveFailures.incrementAndGet() >= 3) {
                breakerOpen.set(true);
                System.out.println("  [circuit breaker] tripped after 3 consecutive failures");
            }
            return "FALLBACK (call failed) for " + requestId;
        }
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            String result = protectedCall("req-" + i);
            System.out.println(result);
        }
        System.out.println("\nThe BULKHEAD's dedicated pool (dedicatedBulkheadPool) remained ISOLATED throughout --");
        System.out.println("no other part of a real application sharing threads with THIS pool would have been affected,");
        System.out.println("even while this dependency failed repeatedly and eventually tripped its breaker.");
        dedicatedBulkheadPool.shutdown();
    }
}
```

**How to run:** `javac CircuitBreakerPlusBulkheadComposed.java && java CircuitBreakerPlusBulkheadComposed` (JDK 17+).

Expected output:
```
FALLBACK (call failed) for req-1
FALLBACK (call failed) for req-2
  [circuit breaker] tripped after 3 consecutive failures
FALLBACK (call failed) for req-3
FALLBACK (breaker open) for req-4
FALLBACK (breaker open) for req-5

The BULKHEAD's dedicated pool (dedicatedBulkheadPool) remained ISOLATED throughout --
no other part of a real application sharing threads with THIS pool would have been affected,
even while this dependency failed repeatedly and eventually tripped its breaker.
```

## 6. Walkthrough

1. **Level 1, everything unbounded** — `callDependency` sleeps for a full second with nothing limiting that duration, and `handleRequest` (implicit here as the inline call in `main`) proceeds to submit even an obviously invalid `null` request to that slow call, wasting the full second on work that could never have succeeded regardless of how long it was given.
2. **Level 2, fail fast rejecting doomed work immediately** — `handleRequest` checks `request == null` *before* submitting anything to `pool`, throwing immediately; the measured elapsed time in `main` confirms this rejection happens in effectively zero milliseconds, in stark contrast to Level 1's full-second wait for a request that was always going to fail.
3. **Level 2, timeout bounding the remaining risk** — even for a *valid* request that did reach `pool.submit`, `future.get(500, TimeUnit.MILLISECONDS)` ensures the caller never waits longer than 500ms for a response, regardless of how long the actual downstream call might hang — bounding a different dimension of risk (time) than fail-fast bounds (wasted work on doomed requests).
4. **Level 3, combining a bulkhead with a circuit breaker** — `dedicatedBulkheadPool` is a separate, fixed-size pool used exclusively for calls to this one dependency (the bulkhead pattern, as detailed in [fault isolation](0242-fault-isolation.md)), while `breakerOpen`/`consecutiveFailures` implement circuit-breaker-style call-rate bounding on top of it — the two patterns operate on entirely different dimensions (resource isolation versus call suppression) and compose without conflicting.
5. **Level 3, the breaker tripping mid-sequence** — the first two calls to `protectedCall` both fail (since `callFailingDependency` always throws) and increment `consecutiveFailures`; the third failure crosses the threshold of 3, printing the trip message and setting `breakerOpen` to `true` — from that point forward, calls four and five short-circuit immediately via the `breakerOpen` check, never touching `dedicatedBulkheadPool` at all.
6. **Level 3, why layering these patterns matters** — throughout this entire sequence (repeated failures, a tripped breaker, several fallback responses), `dedicatedBulkheadPool` never grows unbounded or leaks threads into any other part of a hypothetical larger application, because the bulkhead's isolation is structural (a separate `ExecutorService`) and entirely independent of whatever the circuit breaker's failure-counting logic is doing — this is the concrete demonstration of why *Release It!*'s catalog of patterns is meant to be combined: each pattern addresses a distinct risk dimension, and using several together (as real production resilience configurations typically do) provides layered protection no single pattern alone would.

## 7. Gotchas & takeaways

> **Gotcha:** knowing the names of these patterns is not the same as correctly tuning their parameters (timeout durations, failure thresholds, pool sizes) for a specific real dependency's actual behavior — applying a pattern with poorly chosen thresholds (a timeout too short for a legitimately slow-but-healthy dependency, a bulkhead sized too small for genuine peak load) can cause more harm than having no protection at all; the pattern names give a shared vocabulary and proven shape, but the specific numbers still require deliberate, dependency-specific tuning.

- *Release It!* catalogued a set of recurring production failure modes and named the techniques that address them — circuit breaker, bulkhead, timeout, fail fast, steady state, among others — giving the industry a shared vocabulary for resilience design.
- Most of these patterns work by bounding some specific dimension of risk: time (timeout), call rate to a failing dependency (circuit breaker), shared resource consumption (bulkhead), or wasted work on doomed requests (fail fast).
- The patterns are designed to be composed together, each addressing a different risk dimension simultaneously, rather than used as alternatives to one another.
- Many of these patterns are now built directly into frameworks like Resilience4j and Spring Cloud, making them accessible as configuration rather than requiring custom implementation.
- Knowing a pattern's name and shape doesn't substitute for correctly tuning its specific parameters to a given dependency's actual, real-world behavior — misconfigured thresholds can cause harm even while nominally "using the right pattern."
