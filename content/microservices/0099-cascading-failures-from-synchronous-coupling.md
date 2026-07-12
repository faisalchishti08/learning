---
card: microservices
gi: 99
slug: cascading-failures-from-synchronous-coupling
title: "Cascading failures from synchronous coupling"
---

## 1. What it is

A cascading failure is what happens when [failure propagation](0098-failure-propagation-across-synchronous-chains.md) doesn't just travel up a chain but *amplifies* as it goes — a slow or failing downstream service causes its callers to exhaust their own resources (threads, connections) while waiting, which makes *those* callers slow or unresponsive too, which cascades to *their* callers, and so on. Unlike simple failure propagation (one bad response causes another), a cascading failure specifically involves resource exhaustion at each hop, which is what turns a single service's localized problem into a system-wide outage that can outlast the original failure by a wide margin.

## 2. Why & when

The mechanism is specifically about resource exhaustion: a service with a bounded thread pool (see [backpressure](0086-backpressure-in-synchronous-calls.md)) handling requests that call a now-slow downstream dependency will have every one of its threads eventually occupied waiting on that dependency, given enough concurrent traffic — at which point the calling service can no longer accept *any* new requests, not even ones that don't touch the failing dependency at all. Its own callers then experience the calling service as fully down, not just degraded, and the same resource-exhaustion pattern repeats one level up. This is why a single slow (not even fully down — just slow) service deep in a call graph can take down services with no direct relationship to whatever the original problem was.

Understand this mechanism specifically to justify why timeouts, circuit breakers, and bulkheads aren't optional resilience nice-to-haves — they are what prevents one service's resource pool from being consumed entirely by calls to one struggling dependency, which is the specific failure mode that turns a contained problem into a cascading one.

## 3. Core concept

Without a bound on how many resources a call to one dependency can consume, a slow dependency can consume *all* of a caller's resources, starving unrelated requests that share the same resource pool.

```
Service B has a pool of 10 threads, serving requests to BOTH dependency C (now slow) and dependency X (healthy)
    |
    v
As more requests arrive needing C: more of B's 10 threads get stuck waiting on C
    |
    v
Eventually: ALL 10 threads are stuck waiting on C
    |
    v
A NEW request needing only X (which is perfectly healthy) has NO thread available -- B appears TOTALLY DOWN
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service B's shared thread pool becomes entirely consumed by requests waiting on slow dependency C, leaving no threads available for unrelated requests to healthy dependency X, making B appear fully down">
  <rect x="20" y="20" width="240" height="150" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service B: 10-thread pool</text>
  <text x="140" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ALL 10 threads stuck waiting on C</text>
  <rect x="35" y="70" width="210" height="80" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="115" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">[thread][thread][thread]...</text>
  <text x="140" y="130" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">all waiting on slow C</text>

  <rect x="320" y="20" width="130" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="385" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Dependency C</text>
  <text x="385" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(slow)</text>

  <rect x="320" y="120" width="130" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="385" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Dependency X</text>
  <text x="385" y="158" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">(healthy, but unreachable -- no threads left!)</text>

  <line x1="260" y1="60" x2="320" y2="45" stroke="#79c0ff" stroke-width="1.5"/>
  <rect x="480" y="120" width="130" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="545" y="142" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">new request for X:</text>
  <text x="545" y="157" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">BLOCKED, no thread free</text>
</svg>

A shared, unbounded resource pool lets a slow dependency starve requests that have nothing to do with it.

## 5. Runnable example

Scenario: `ServiceB` handling requests to two independent dependencies, `C` (which becomes slow) and `X` (which stays healthy), first with a shared, uncapped-per-dependency thread pool showing how `X`'s requests get starved once `C` degrades, then fixed with a bulkhead — a separate, isolated resource pool per dependency — so a slow `C` can no longer affect calls to `X` at all.

### Level 1 — Basic

```java
// File: SharedPoolStarvation.java -- ONE shared thread pool serves BOTH
// dependency C (slow) and dependency X (healthy) -- C's slowness
// starves X's requests once the pool fills up with C-bound threads.
import java.util.concurrent.*;

public class SharedPoolStarvation {
    static ExecutorService sharedPool = Executors.newFixedThreadPool(3); // ONE pool for everything

    static String callC() throws InterruptedException { Thread.sleep(300); return "C responded"; } // SLOW
    static String callX() throws InterruptedException { Thread.sleep(10); return "X responded"; }  // fast, healthy

    public static void main(String[] args) throws Exception {
        // 3 requests for C fill the ENTIRE shared pool (pool size = 3)
        Future<String> c1 = sharedPool.submit(SharedPoolStarvation::callC);
        Future<String> c2 = sharedPool.submit(SharedPoolStarvation::callC);
        Future<String> c3 = sharedPool.submit(SharedPoolStarvation::callC);

        Thread.sleep(20); // let the 3 C-calls occupy the pool first
        long start = System.currentTimeMillis();
        Future<String> xRequest = sharedPool.submit(SharedPoolStarvation::callX); // NO thread free -- must wait
        String xResult = xRequest.get();
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(xResult + " -- but had to wait ~" + elapsed + "ms (pool was full of C-bound threads)");

        c1.get(); c2.get(); c3.get();
        sharedPool.shutdown();
    }
}
```

**How to run:** `javac SharedPoolStarvation.java && java SharedPoolStarvation` (JDK 17+).

Expected output (elapsed time will vary slightly, always at least 250):
```
X responded -- but had to wait ~276ms (pool was full of C-bound threads)
```

`X` itself only takes 10ms to respond, but the request for it had to wait nearly the full 300ms that `C`'s slow calls were occupying the shared pool — `X`'s health was completely irrelevant to how long its caller had to wait.

### Level 2 — Intermediate

```java
// File: BulkheadIsolation.java -- give C and X SEPARATE, isolated
// thread pools (a "bulkhead") -- C's slowness can no longer touch X's
// requests AT ALL, regardless of how much load C is under.
import java.util.concurrent.*;

public class BulkheadIsolation {
    static ExecutorService cPool = Executors.newFixedThreadPool(3); // ISOLATED pool for C
    static ExecutorService xPool = Executors.newFixedThreadPool(3); // ISOLATED pool for X -- unaffected by C

    static String callC() throws InterruptedException { Thread.sleep(300); return "C responded"; }
    static String callX() throws InterruptedException { Thread.sleep(10); return "X responded"; }

    public static void main(String[] args) throws Exception {
        Future<String> c1 = cPool.submit(BulkheadIsolation::callC);
        Future<String> c2 = cPool.submit(BulkheadIsolation::callC);
        Future<String> c3 = cPool.submit(BulkheadIsolation::callC); // fills C's pool ENTIRELY

        Thread.sleep(20);
        long start = System.currentTimeMillis();
        Future<String> xRequest = xPool.submit(BulkheadIsolation::callX); // X has its OWN pool -- unaffected
        String xResult = xRequest.get();
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(xResult + " -- took only ~" + elapsed + "ms (C's slowness never touched X's pool)");

        c1.get(); c2.get(); c3.get();
        cPool.shutdown(); xPool.shutdown();
    }
}
```

**How to run:** `javac BulkheadIsolation.java && java BulkheadIsolation` (JDK 17+).

Expected output (elapsed time will vary slightly, but always well under 300):
```
X responded -- took only ~11ms (C's slowness never touched X's pool)
```

### Level 3 — Advanced

```java
// File: MeasuringCascadeContainment.java -- run BOTH scenarios back to
// back and print the difference DIRECTLY, making the cascading-failure
// containment measurable rather than just qualitative.
import java.util.concurrent.*;

public class MeasuringCascadeContainment {
    static String callC() throws InterruptedException { Thread.sleep(300); return "C responded"; }
    static String callX() throws InterruptedException { Thread.sleep(10); return "X responded"; }

    static long measureXLatencyWithSharedPool() throws Exception {
        ExecutorService sharedPool = Executors.newFixedThreadPool(3);
        for (int i = 0; i < 3; i++) sharedPool.submit(MeasuringCascadeContainment::callC);
        Thread.sleep(20);
        long start = System.currentTimeMillis();
        sharedPool.submit(MeasuringCascadeContainment::callX).get();
        long elapsed = System.currentTimeMillis() - start;
        sharedPool.shutdown();
        return elapsed;
    }

    static long measureXLatencyWithBulkhead() throws Exception {
        ExecutorService cPool = Executors.newFixedThreadPool(3);
        ExecutorService xPool = Executors.newFixedThreadPool(3);
        for (int i = 0; i < 3; i++) cPool.submit(MeasuringCascadeContainment::callC);
        Thread.sleep(20);
        long start = System.currentTimeMillis();
        xPool.submit(MeasuringCascadeContainment::callX).get();
        long elapsed = System.currentTimeMillis() - start;
        cPool.shutdown(); xPool.shutdown();
        return elapsed;
    }

    public static void main(String[] args) throws Exception {
        long sharedLatency = measureXLatencyWithSharedPool();
        long bulkheadLatency = measureXLatencyWithBulkhead();
        System.out.println("X's latency with a SHARED pool (C is slow): ~" + sharedLatency + "ms");
        System.out.println("X's latency with an ISOLATED bulkhead pool: ~" + bulkheadLatency + "ms");
        System.out.println("Cascade containment improvement: ~" + (sharedLatency - bulkheadLatency) + "ms saved");
    }
}
```

**How to run:** `javac MeasuringCascadeContainment.java && java MeasuringCascadeContainment` (JDK 17+).

Expected output (exact numbers will vary, but shared latency is always dramatically higher than bulkhead latency):
```
X's latency with a SHARED pool (C is slow): ~277ms
X's latency with an ISOLATED bulkhead pool: ~12ms
Cascade containment improvement: ~265ms saved
```

## 6. Walkthrough

1. **Level 1** — `sharedPool`, sized at exactly 3 threads, receives three submissions all calling the slow `callC` (each sleeping 300ms). `main` waits 20ms (letting all three occupy the pool), then submits a call to the fast `callX` — but since all 3 threads in `sharedPool` are already occupied by the `C` calls, the `X` submission has to *wait in the pool's internal queue* until one of the `C` calls finishes and frees a thread. The elapsed time measured around `xRequest.get()` is therefore close to `C`'s full 300ms delay, even though `callX` itself only takes 10ms to actually run once it finally gets a thread.
2. **Level 2 — isolating with a bulkhead** — `cPool` and `xPool` are now entirely separate `ExecutorService` instances, each with their own 3 threads. `main` fills `cPool` completely with the same three slow `C` calls, but submits the `X` call to `xPool` instead — a completely independent pool that `C`'s calls never touch. The elapsed time this time is close to `callX`'s own actual 10ms delay, essentially unaffected by how badly `cPool` is currently backed up.
3. **Level 3 — measuring the difference directly** — `measureXLatencyWithSharedPool` and `measureXLatencyWithBulkhead` package up Level 1's and Level 2's scenarios respectively as reusable methods returning the measured elapsed time. `main` calls both in sequence and prints all three numbers: the shared-pool latency (dominated by `C`'s slowness), the bulkhead latency (reflecting only `X`'s own actual speed), and their difference — making the containment benefit a concrete, measured number rather than just a qualitative claim.
4. **Why the difference is the whole point** — in both scenarios, `dependency C` is equally slow and equally overloaded — nothing about `C`'s actual health changed between Level 1 and Level 2. The *only* difference is whether `X`'s requests share a resource pool with `C`'s requests or have their own isolated pool. This isolates the cascading-failure mechanism to exactly one variable: shared versus isolated resource pools, and shows that variable alone determines whether `C`'s slowness becomes `X`'s problem too.
5. **Connecting this back to a real service** — in a real `ServiceB` handling many different kinds of requests (some needing `C`, some needing `X`, some needing neither), an isolated bulkhead per downstream dependency (or per request type) is what prevents one dependency's outage from exhausting the thread pool that *unrelated* requests also depend on — exactly the mechanism this example measures directly.

## 7. Gotchas & takeaways

> **Gotcha:** bulkheads add real resource overhead — more separate, smaller thread pools instead of one larger shared pool means each pool individually has less headroom to absorb its own bursts of traffic. Size each isolated pool based on that specific dependency's realistic call volume and latency, not just an even split of whatever the shared pool used to have.

- Cascading failure specifically involves resource exhaustion: a slow dependency consumes shared resources (threads, connections) faster than they free up, eventually starving requests that don't even touch the slow dependency.
- A bulkhead — an isolated resource pool per dependency or request type — is the direct fix: it caps how much of a caller's total capacity any single dependency's problems can consume.
- The measured latency difference between a shared pool and an isolated bulkhead, as Level 3 demonstrates, is often dramatic — a slow dependency can inflate unrelated requests' latency by an order of magnitude when pools are shared.
- This mechanism is why [client-side timeouts](0096-client-side-timeouts-connect-read.md) alone aren't sufficient protection — a bounded wait per call still consumes a thread for that bounded duration, and enough concurrent bounded waits can still exhaust a shared pool.
- Combine bulkheads with timeouts and (typically) circuit breakers for full protection: bulkheads limit blast radius across dependencies, timeouts bound how long any one call can occupy a resource, and circuit breakers stop sending traffic to a dependency that's clearly failing.
