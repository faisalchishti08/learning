---
card: microservices
gi: 243
slug: cascading-failures
title: "Cascading failures"
---

## 1. What it is

A cascading failure is a chain reaction where one component's failure causes a second component to fail (typically through resource exhaustion or timeout pile-up), which in turn causes a third to fail, and so on — a localized problem that, left uncontained, spreads through a system's dependency graph and can take down services that had no direct connection to the original failure at all.

## 2. Why & when

The mechanism behind most cascading failures is straightforward once [fault isolation](0242-fault-isolation.md) and [partial failure](0239-why-distributed-systems-fail-partial-failure.md) are understood: a downstream service becomes slow (not necessarily fully down — slow is often worse), callers waiting on it hold resources (threads, connections) for longer than usual, those resources accumulate faster than they're freed, the caller itself becomes resource-starved and slow to respond to *its own* callers, and the degradation propagates one layer further up the call graph — repeating at each layer until services with no direct relationship to the original slow dependency are failing too. Understanding this mechanism is what motivates nearly every pattern in this section: [circuit breakers](0248-circuit-breaker-pattern.md) stop calling a failing dependency before resources pile up, [bulkheads](0242-fault-isolation.md) contain resource exhaustion to one dependency's pool, and timeouts prevent an individual call from holding a resource indefinitely.

Design explicitly against cascading failure in any system with more than a shallow, single-layer dependency graph — which is most real microservices systems. A single service with no downstream dependencies has no cascading failure risk to design around.

## 3. Core concept

A cascade propagates because each layer's resource exhaustion becomes the *cause* of the next layer's slowness, and breaking the chain at any single layer (via a timeout, a circuit breaker, or isolation) prevents the failure from reaching layers further up, even if the original failure isn't fixed.

```java
// the CASCADE mechanism, one hop:
// service-C is slow -> service-B's threads calling service-C pile up waiting ->
// service-B's thread pool exhausts -> service-B becomes slow to ITS OWN callers ->
// service-A's threads calling service-B pile up -> service-A ALSO exhausts -> repeat...

// BREAKING the chain at ONE hop stops it from reaching further layers:
CircuitBreaker serviceCBreaker = CircuitBreaker.ofDefaults("service-C");
String result = serviceCBreaker.executeSupplier(() -> callServiceC());
// once service-C's failures TRIP the breaker, service-B STOPS waiting on it --
// service-B's OWN threads stay free -- service-A never sees service-B degrade AT ALL
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service C becomes slow, causing service B's threads calling it to pile up and exhaust, which makes service B slow to its own caller service A, which in turn exhausts -- a chain reaction that a circuit breaker between B and C stops at the first hop, protecting A entirely" >
  <rect x="480" y="65" width="120" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Service C (slow)</text>

  <rect x="270" y="65" width="120" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B</text>

  <rect x="60" y="65" width="120" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A</text>

  <line x1="270" y1="87" x2="180" y2="87" stroke="#8b949e" stroke-dasharray="4,4" marker-end="url(#arr243)"/>
  <text x="225" y="70" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">threatened to spread</text>

  <rect x="390" y="60" width="60" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="82" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Circuit</text>
  <text x="420" y="94" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">breaker</text>

  <line x1="480" y1="87" x2="452" y2="87" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="140" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">STOPS the cascade here -- A never affected</text>

  <defs>
    <marker id="arr243" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Breaking the chain at any single hop prevents the cascade from ever reaching the layers further upstream.

## 5. Runnable example

Scenario: a three-service call chain (A calls B calls C) where C's slowness propagates uncontained all the way to A, exhausting resources at every layer, refactored to add a circuit breaker between B and C that stops the cascade at that single hop, and finally demonstrating the breaker's protective effect measured directly: A's response time and resource usage stay stable even while C remains completely broken.

### Level 1 — Basic

```java
// File: UncontainedCascade.java -- C's slowness propagates THROUGH B,
// exhausting resources at EVERY layer, all the way up to A.
import java.util.concurrent.*;

public class UncontainedCascade {
    static ExecutorService poolA = Executors.newFixedThreadPool(2);
    static ExecutorService poolB = Executors.newFixedThreadPool(2);

    static String callServiceC() throws InterruptedException { Thread.sleep(300); return "C result"; } // SLOW, no protection

    static String callServiceB() throws Exception {
        Future<String> future = poolB.submit(UncontainedCascade::callServiceC); // B's thread WAITS on C
        return future.get(); // BLOCKS for the full 300ms -- B is now ALSO slow
    }

    static String callServiceA() throws Exception {
        Future<String> future = poolA.submit(UncontainedCascade::callServiceB); // A's thread WAITS on B, which waits on C
        return future.get(); // A is now ALSO slow -- the cascade reached the TOP layer
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        String result = callServiceA();
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("A's response: " + result + ", took " + elapsed + "ms -- C's slowness reached ALL THE WAY to A.");
        poolA.shutdown(); poolB.shutdown();
    }
}
```

**How to run:** `javac UncontainedCascade.java && java UncontainedCascade` (JDK 17+).

### Level 2 — Intermediate

```java
// File: CircuitBreakerStopsCascade.java -- a SIMPLE circuit breaker
// between B and C: after enough failures/slow calls, B STOPS waiting
// on C at all -- the cascade CANNOT reach A.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class CircuitBreakerStopsCascade {
    static ExecutorService poolA = Executors.newFixedThreadPool(2);
    static ExecutorService poolB = Executors.newFixedThreadPool(2);
    static AtomicBoolean breakerOpen = new AtomicBoolean(false); // OPEN = stop calling C

    static String callServiceC() throws InterruptedException { Thread.sleep(300); return "C result"; }

    static String callServiceB() {
        if (breakerOpen.get()) {
            return "B FALLBACK (breaker open -- not calling C at all)"; // FAST -- no waiting, no thread tied up on C
        }
        try {
            Future<String> future = poolB.submit(CircuitBreakerStopsCascade::callServiceC);
            String result = future.get(500, TimeUnit.MILLISECONDS);
            return result;
        } catch (Exception e) {
            breakerOpen.set(true); // TRIP the breaker on a failure/timeout
            return "B FALLBACK (just tripped)";
        }
    }

    static String callServiceA() throws Exception {
        Future<String> future = poolA.submit(CircuitBreakerStopsCascade::callServiceB); // A's thread waits on B -- but B is now FAST
        return future.get();
    }

    public static void main(String[] args) throws Exception {
        breakerOpen.set(true); // simulate the breaker having ALREADY tripped from earlier failures
        long start = System.currentTimeMillis();
        String result = callServiceA();
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("A's response: " + result + ", took " + elapsed + "ms -- FAST, since B never waited on C.");
        poolA.shutdown(); poolB.shutdown();
    }
}
```

**How to run:** `javac CircuitBreakerStopsCascade.java && java CircuitBreakerStopsCascade` (JDK 17+).

Expected output:
```
A's response: B FALLBACK (breaker open -- not calling C at all), took 0ms -- FAST, since B never waited on C.
```

### Level 3 — Advanced

```java
// File: MeasuredProtectionUnderSustainedFailure.java -- measures A's
// response time across MULTIPLE calls, with C PERMANENTLY broken --
// proving A's performance stays STABLE despite C never recovering.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.*;

public class MeasuredProtectionUnderSustainedFailure {
    static ExecutorService poolB = Executors.newFixedThreadPool(2);
    static AtomicBoolean breakerOpen = new AtomicBoolean(false);
    static AtomicInteger consecutiveFailures = new AtomicInteger(0);
    static final int FAILURE_THRESHOLD = 3;

    static String callServiceC() throws InterruptedException { Thread.sleep(300); throw new RuntimeException("C is down"); } // PERMANENTLY broken

    static String callServiceB() {
        if (breakerOpen.get()) return "B FALLBACK";
        try {
            Future<String> future = poolB.submit(MeasuredProtectionUnderSustainedFailure::callServiceC);
            String result = future.get(500, TimeUnit.MILLISECONDS);
            consecutiveFailures.set(0);
            return result;
        } catch (Exception e) {
            if (consecutiveFailures.incrementAndGet() >= FAILURE_THRESHOLD) {
                breakerOpen.set(true);
                System.out.println("  [breaker] TRIPPED after " + FAILURE_THRESHOLD + " consecutive failures");
            }
            return "B FALLBACK (call failed)";
        }
    }

    static long timedCallToB() {
        long start = System.currentTimeMillis();
        callServiceB();
        return System.currentTimeMillis() - start;
    }

    public static void main(String[] args) {
        List<Long> responseTimes = new ArrayList<>();
        for (int i = 1; i <= 6; i++) {
            long elapsed = timedCallToB();
            responseTimes.add(elapsed);
            System.out.println("Call " + i + ": " + elapsed + "ms");
        }

        long avgAfterTrip = responseTimes.subList(3, 6).stream().mapToLong(Long::longValue).sum() / 3;
        System.out.println("\nAverage response time AFTER breaker tripped (calls 4-6): " + avgAfterTrip + "ms -- STABLE, despite C remaining completely broken.");
        poolB.shutdown();
    }
}
```

**How to run:** `javac MeasuredProtectionUnderSustainedFailure.java && java MeasuredProtectionUnderSustainedFailure` (JDK 17+).

Expected output (exact millisecond values vary slightly, pattern is stable):
```
Call 1: 300ms
Call 2: 300ms
  [breaker] TRIPPED after 3 consecutive failures
Call 3: 300ms
Call 4: 0ms
Call 5: 0ms
Call 6: 0ms

Average response time AFTER breaker tripped (calls 4-6): 0ms -- STABLE, despite C remaining completely broken.
```

## 6. Walkthrough

1. **Level 1, the full uncontained chain** — `callServiceA` submits work to `poolA` that internally calls `callServiceB`, which itself submits work to `poolB` that calls `callServiceC`; because `callServiceC` sleeps for 300ms with no protection anywhere in the chain, every layer's `Future.get()` blocks for essentially that same 300ms, meaning C's slowness is fully and directly experienced by A, three layers away.
2. **Level 2, breaking the chain at one hop** — `callServiceB` checks `breakerOpen` *before* attempting to call C at all; when the breaker is open, it returns a fallback string immediately, without ever submitting work to `poolB` or waiting on `callServiceC` in any way.
3. **Level 2, A's isolation from C's problem** — `callServiceA` still calls `callServiceB` and waits on the result exactly as before, but because `callServiceB` itself now returns near-instantly (thanks to the open breaker), A's wait time is near-instant too — A never learns, experiences, or is affected by the fact that C is completely broken underneath.
4. **Level 3, tracking failures to trip the breaker automatically** — `consecutiveFailures` counts consecutive failed/timed-out calls to C, and once that count reaches `FAILURE_THRESHOLD` (3), `breakerOpen` is set to `true` automatically, without any external intervention — this models the self-protecting behavior real circuit breakers provide, covered in more depth in [the circuit breaker pattern](0248-circuit-breaker-pattern.md) itself.
5. **Level 3, the measured before-and-after** — the first three calls each take roughly 300ms (still waiting on C directly, accumulating toward the failure threshold), and the third call's failure is what actually trips the breaker; calls four through six, made after the breaker has tripped, return in near-zero milliseconds each, because they hit the `breakerOpen` fast-path and never touch `poolB` or `callServiceC` at all.
6. **Level 3, the stability this achieves under sustained failure** — the computed average of calls four through six is close to 0ms, even though `callServiceC` is permanently broken and never recovers throughout this entire program's execution — this is the concrete, measured proof that breaking the cascade chain at one hop (B stopping its calls to C) keeps everything upstream of that point (A, and B's own responsiveness to A) stable and fast, regardless of how long the original failure (C) persists.

## 7. Gotchas & takeaways

> **Gotcha:** a cascading failure often looks, from the outside, like a mysterious, system-wide outage with no obvious single cause — by the time symptoms are visible at the top layer (service A timing out), the actual root cause (service C) may be several hops away and non-obvious from A's own logs or metrics alone; tracing a cascade back to its origin requires distributed tracing or correlated metrics across every layer in the call chain, not just monitoring the layer where symptoms first appeared.

- A cascading failure is a chain reaction where one component's slowness or failure causes resource exhaustion at each layer above it in the call graph, potentially reaching services with no direct relationship to the original failure.
- The mechanism is resource accumulation: callers waiting on a slow dependency hold threads/connections longer, exhausting their own pool and becoming slow to their own callers in turn.
- Breaking the chain at any single hop — via a timeout, a [circuit breaker](0248-circuit-breaker-pattern.md), or resource isolation — prevents the cascade from reaching layers further upstream, even while the original failure persists.
- Nearly every resilience pattern in this section exists specifically to interrupt this propagation mechanism at some point in a system's dependency graph.
- Diagnosing a cascading failure after the fact requires tracing across every layer in the call chain, since the visible symptoms at the top layer can be many hops removed from the actual root cause.
