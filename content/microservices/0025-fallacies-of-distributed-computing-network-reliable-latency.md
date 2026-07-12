---
card: microservices
gi: 25
slug: fallacies-of-distributed-computing-network-reliable-latency
title: "Fallacies of distributed computing (network reliable, latency zero, etc.)"
---

## 1. What it is

The **fallacies of distributed computing** are a list of assumptions, first collected by engineers at Sun Microsystems in the 1990s, that programmers commonly and wrongly believe about networks when writing distributed systems. The most cited ones include: the network is reliable, latency is zero, bandwidth is infinite, the network is secure, topology doesn't change, there is one administrator, transport cost is zero, and the network is homogeneous. Every one of these is false in practice, and code written as though any of them were true tends to fail — often only under real production load, long after it "worked fine" in development.

## 2. Why & when

These fallacies matter specifically because they're *comfortable* assumptions — a monolith's in-process calls genuinely never fail due to network issues, never have meaningful latency, and never run out of bandwidth, so a developer moving from monolith to microservices work can carry those habits over without realizing they no longer hold. Code that implicitly assumes "the network is reliable" (no retry logic, no timeout) or "latency is zero" (calling ten downstream services sequentially in a tight loop as if each call were instant) will function correctly in a local demo and then degrade or fail unpredictably once deployed across real machines with real network conditions.

Use this list as a design review checklist specifically for any code that makes a network call: for each fallacy, ask "does my code accidentally assume this is true?" The two most consequential in everyday microservices work are "the network is reliable" (missing retry/circuit-breaker logic) and "latency is zero" (missing timeouts, or an accidental N+1 pattern of sequential remote calls).

## 3. Core concept

Two fallacies, demonstrated concretely:

- **"The network is reliable"** — code with no handling for a call simply failing outright (connection refused, dropped mid-flight) will crash or hang in ways an equivalent in-process call structurally cannot.
- **"Latency is zero"** — code that calls N downstream services sequentially, each with real (even if small) latency, accumulates total latency proportional to N; the same logic run in-process would be effectively instantaneous regardless of N.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An in-process call has zero latency and cannot fail on its own; a network call has real, non-zero latency and can fail independently of the calling code">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">In-process call</text>
  <rect x="30" y="35" width="240" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="62" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">~0ms, cannot fail independently</text>

  <text x="480" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Network call</text>
  <rect x="360" y="35" width="240" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="480" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">real latency, every time</text>
  <text x="480" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">can fail independently of caller</text>
</svg>

Code that assumes a network call behaves like the left box will misbehave the moment reality looks like the right box.

## 5. Runnable example

Scenario: fetching data from three downstream services, first written as if network calls were instant and reliable, then measured to expose the latency-zero fallacy, then hardened against the reliability fallacy with real failure handling.

### Level 1 — Basic

```java
// File: AssumesZeroLatencyAndReliability.java -- code written as if
// the network were instant and never failed
public class AssumesZeroLatencyAndReliability {
    static String callService(String name) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {} // simulates REAL network latency
        return name + "-data";
    }

    public static void main(String[] args) {
        // sequential calls, no timeout, no retry -- written as if latency were zero and failures impossible
        String userData = callService("UserService");
        String orderData = callService("OrderService");
        String inventoryData = callService("InventoryService");
        System.out.println("combined: " + userData + ", " + orderData + ", " + inventoryData);
    }
}
```

**How to run:** `javac AssumesZeroLatencyAndReliability.java && java AssumesZeroLatencyAndReliability` (JDK 17+).

Expected output:
```
combined: UserService-data, OrderService-data, InventoryService-data
```

The output looks fine, but nothing here measures or accounts for the fact that each `callService` invocation takes real time (simulated here as 50ms) and could, in a real system, simply fail. This code silently assumes both the latency-zero and reliable-network fallacies.

### Level 2 — Intermediate

```java
// File: MeasureLatencyFallacy.java -- make the "latency is zero" fallacy
// VISIBLE by actually measuring total time for sequential vs concurrent calls.
import java.util.concurrent.*;

public class MeasureLatencyFallacy {
    static String callService(String name) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return name + "-data";
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        String userData = callService("UserService");
        String orderData = callService("OrderService");
        String inventoryData = callService("InventoryService");
        long sequentialMs = System.currentTimeMillis() - start;
        System.out.println("sequential calls took: " + sequentialMs + "ms (assumes latency doesn't add up -- it does)");

        // now issue the SAME three calls CONCURRENTLY, acknowledging real latency exists
        start = System.currentTimeMillis();
        ExecutorService pool = Executors.newFixedThreadPool(3);
        Future<String> f1 = pool.submit(() -> callService("UserService"));
        Future<String> f2 = pool.submit(() -> callService("OrderService"));
        Future<String> f3 = pool.submit(() -> callService("InventoryService"));
        String u = f1.get(), o = f2.get(), i = f3.get();
        long concurrentMs = System.currentTimeMillis() - start;
        pool.shutdown();
        System.out.println("concurrent calls took: " + concurrentMs + "ms (latency overlapped instead of stacking)");
    }
}
```

**How to run:** `javac MeasureLatencyFallacy.java && java MeasureLatencyFallacy` (JDK 17+).

Expected output (timings approximate):
```
sequential calls took: 150ms (assumes latency doesn't add up -- it does)
concurrent calls took: 50ms (latency overlapped instead of stacking)
```

Calling three services sequentially takes roughly 3x one call's latency (`150ms`), because each `Thread.sleep(50)` genuinely blocks before the next call starts — a monolith's in-process calls would show none of this accumulation. Issuing the same three calls concurrently overlaps their latency, bringing total time down to roughly one call's worth (`50ms`) — proof the latency-zero fallacy has a real, measurable, and fixable cost.

### Level 3 — Advanced

```java
// File: HandleUnreliableNetwork.java -- stop assuming "the network is
// reliable"; add explicit timeout and failure handling for a call that
// can genuinely fail independently of the calling code.
import java.util.concurrent.*;

public class HandleUnreliableNetwork {
    static String callService(String name, boolean simulateFailure) throws Exception {
        if (simulateFailure) {
            Thread.sleep(200); // simulates a call that hangs before eventually failing
            throw new RuntimeException(name + " connection reset");
        }
        Thread.sleep(50);
        return name + "-data";
    }

    static String callWithTimeoutAndFallback(String name, boolean simulateFailure, long timeoutMs, String fallback) {
        ExecutorService pool = Executors.newSingleThreadExecutor();
        try {
            Future<String> future = pool.submit(() -> callService(name, simulateFailure));
            return future.get(timeoutMs, TimeUnit.MILLISECONDS); // bounded wait -- NOT an infinite, "network is reliable" wait
        } catch (TimeoutException e) {
            System.out.println("  " + name + " timed out after " + timeoutMs + "ms -- falling back");
            return fallback;
        } catch (Exception e) {
            System.out.println("  " + name + " failed: " + e.getCause() + " -- falling back");
            return fallback;
        } finally {
            pool.shutdownNow();
        }
    }

    public static void main(String[] args) {
        String userData = callWithTimeoutAndFallback("UserService", false, 100, "default-user");
        String orderData = callWithTimeoutAndFallback("OrderService", true, 100, "default-order"); // simulates a REAL failure
        System.out.println("combined: " + userData + ", " + orderData);
    }
}
```

**How to run:** `javac HandleUnreliableNetwork.java && java HandleUnreliableNetwork` (JDK 17+).

Expected output:
```
  OrderService timed out after 100ms -- falling back
combined: UserService-data, default-order
```

The production-flavored point: `callWithTimeoutAndFallback` bounds every call with an explicit timeout (`100ms`), refusing to assume the network is reliable or that a call will always eventually return. `OrderService`'s simulated failure is caught and degraded to a `fallback` value instead of crashing or hanging the whole program — exactly the kind of explicit handling that "the network is reliable" and "latency is zero" implicitly assume away.

## 6. Walkthrough

1. `callWithTimeoutAndFallback("UserService", false, 100, "default-user")` submits `callService("UserService", false)` to a single-thread executor, then calls `future.get(100, MILLISECONDS)`. Since `simulateFailure` is `false`, the call sleeps `50ms` and returns normally, well within the `100ms` bound — `userData` becomes `"UserService-data"`.
2. `callWithTimeoutAndFallback("OrderService", true, 100, "default-order")` submits `callService("OrderService", true)`, which is designed to sleep `200ms` before throwing — longer than the `100ms` timeout.
3. `future.get(100, MILLISECONDS)` therefore throws `TimeoutException` before `callService` ever gets to its own `throw` statement — the caller gives up waiting rather than blocking indefinitely, which is precisely what "the network is reliable" (and, implicitly, "a call always eventually completes") would wrongly assume is unnecessary.
4. The `catch (TimeoutException e)` block prints the timeout message and returns `"default-order"` as `orderData` — a deliberate fallback value, not a crash.
5. `pool.shutdownNow()` runs in the `finally` block, attempting to interrupt the still-running background task, since letting it linger indefinitely after the caller has already moved on would itself be a resource leak.
6. The final print shows `combined: UserService-data, default-order` — the overall program completed successfully and predictably despite one of its two dependencies genuinely failing, because the code was written without assuming either fallacy.

```
UserService call:  succeeds within timeout -> "UserService-data"
OrderService call: exceeds timeout (100ms) -> TimeoutException caught -> "default-order" (fallback)
        |
combined result: uses the real value where available, a safe fallback where not
```

## 7. Gotchas & takeaways

> **Gotcha:** fixing "the network is reliable" with retries alone, without also addressing "latency is zero," can make things worse — retrying a call that's slow (not truly failed) simply multiplies the total latency the caller experiences, stacking delay on top of delay. Timeouts, retries, and fallbacks need to be reasoned about together, not bolted on independently.

- The fallacies of distributed computing are comfortable but false assumptions about networks — reliable, zero-latency, infinite bandwidth, secure, unchanging topology, and more — that code written for a monolith never needs to violate, but network-calling code violates constantly in production.
- "The network is reliable" and "latency is zero" are the two most consequential fallacies in everyday microservices code: missing failure handling, and missing timeouts or accidental sequential-call latency stacking.
- Measuring the real cost of these assumptions (as `MeasureLatencyFallacy` does) turns a vague worry into a concrete number worth fixing — sequential calls that should be concurrent are a common, fixable source of unnecessary latency.
- Every call across a network boundary should have an explicit, bounded timeout and explicit handling for the call failing outright — code that doesn't is implicitly assuming fallacies that will eventually be proven false in production.
