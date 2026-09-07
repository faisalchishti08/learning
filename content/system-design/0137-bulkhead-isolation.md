---
card: system-design
gi: 137
slug: bulkhead-isolation
title: Bulkhead isolation
---

## 1. What it is

**Bulkhead isolation** partitions a system's resources (thread pools, connection pools, or entire service instances) so that a failure or slowdown in one part cannot exhaust the resources needed by another, unrelated part. The name comes from a ship's bulkheads: watertight compartments that keep a hull breach in one section from flooding and sinking the entire ship.

## 2. Why & when

Without isolation, one slow or failing dependency can silently take down completely unrelated functionality, simply by consuming a resource everything else also depends on — for example, if all outgoing calls share one thread pool, calls to a slow "recommendations" service can occupy every thread in that pool while they wait, leaving zero threads available for a completely unrelated, healthy "checkout" call. Use bulkheads whenever a single service makes calls to multiple, independent dependencies, so that one dependency's problems stay contained to the functionality that actually depends on it.

## 3. Core concept

- **Shared resource pool (no isolation):** all outgoing calls, regardless of destination, draw from one thread pool or one connection pool — a slowdown in any single dependency can consume the whole pool.
- **Per-dependency isolation:** give each dependency (or each category of functionality) its own dedicated, separately-sized pool. A slow "recommendations" call can exhaust *its own* small pool, but the "checkout" pool remains completely untouched and fully available.
- **Sizing each bulkhead:** size each pool according to that specific dependency's expected load and how much resource exhaustion in that one area is acceptable to tolerate — a critical dependency might get a generous pool; a non-essential one gets a small, tightly-bounded pool.
- **Combines naturally with circuit breakers:** a [circuit breaker](0136-circuit-breaker.md) can be applied per bulkhead, so a struggling dependency's own isolated pool trips its own breaker, independent of any other dependency's health.
- **Isolation can also apply at a coarser level:** entire service instances, or even entire clusters, can be partitioned by customer tier or by feature, so a problem in one partition does not affect another — the same principle applied at a larger scale.

## 4. Diagram

```
NO ISOLATION (shared pool):            BULKHEAD ISOLATION (separate pools):

  Shared thread pool (10 threads)       Recommendations pool (3 threads)
       |         |                            |
  Recommendations  Checkout                Recommendations calls
  calls (SLOW,     calls                   (all 3 threads stuck,
   hang, use 9      (only 1                 but ONLY these 3)
   of 10 threads)   thread left)
                                          Checkout pool (7 threads, SEPARATE)
  -> checkout starves too, even                |
     though checkout itself is healthy    Checkout calls proceed normally,
                                           completely unaffected
```
*Caption: without isolation, one slow dependency can starve resources needed by unrelated, healthy functionality; separate pools contain the damage to just the affected area.*

## 5. Runnable example

**Level 1 — Basic.** A shared thread pool lets a slow dependency's calls starve resources needed by an unrelated, healthy call.

**Level 2 — Bulkhead isolation.** Give each dependency its own pool, so the slow one's exhaustion does not affect the other.

**Level 3 — Sizing bulkheads appropriately.** Show a correctly-sized bulkhead absorbing a burst without affecting other pools.

```java
// BulkheadIsolation.java
import java.util.concurrent.*;
import java.util.*;

public class BulkheadIsolation {

    public static void main(String[] args) throws Exception {
        // Level 1: shared pool - a slow dependency's calls can consume all available threads.
        ExecutorService sharedPool = Executors.newFixedThreadPool(4);
        List<Future<String>> slowCallsShared = new ArrayList<>();
        for (int i = 0; i < 4; i++) { // occupy ALL 4 threads with slow "recommendations" calls
            slowCallsShared.add(sharedPool.submit(() -> { Thread.sleep(2000); return "recommendations result"; }));
        }
        Future<String> checkoutCallShared = sharedPool.submit(() -> "checkout result"); // no thread free for this!
        try {
            String result = checkoutCallShared.get(200, TimeUnit.MILLISECONDS); // short wait to prove it's stuck
            System.out.println("shared pool - checkout result: " + result);
        } catch (TimeoutException e) {
            System.out.println("shared pool - checkout call STUCK waiting: all threads consumed by slow recommendations calls");
        }
        sharedPool.shutdownNow();

        // Level 2: bulkhead isolation - separate pools per dependency.
        ExecutorService recommendationsPool = Executors.newFixedThreadPool(4); // its own dedicated pool
        ExecutorService checkoutPool = Executors.newFixedThreadPool(2);        // separate, isolated pool

        List<Future<String>> slowCallsIsolated = new ArrayList<>();
        for (int i = 0; i < 4; i++) { // saturate recommendationsPool entirely
            slowCallsIsolated.add(recommendationsPool.submit(() -> { Thread.sleep(2000); return "recommendations result"; }));
        }
        Future<String> checkoutCallIsolated = checkoutPool.submit(() -> "checkout result"); // uses a SEPARATE pool
        String isolatedResult = checkoutCallIsolated.get(200, TimeUnit.MILLISECONDS); // succeeds immediately
        System.out.println("isolated pools - checkout result: " + isolatedResult + " (completely unaffected by recommendations being saturated)");

        recommendationsPool.shutdownNow();
        checkoutPool.shutdown();

        // Level 3: correctly-sized bulkhead absorbs a burst within its own pool, without affecting others.
        ExecutorService searchPool = Executors.newFixedThreadPool(3); // sized for expected search burst
        int burstSize = 3;
        List<Future<String>> searchBurst = new ArrayList<>();
        for (int i = 0; i < burstSize; i++) {
            int id = i;
            searchBurst.add(searchPool.submit(() -> "search result " + id));
        }
        for (Future<String> f : searchBurst) System.out.println("search pool handled: " + f.get());
        System.out.println("search pool absorbed the full burst of " + burstSize + " within its own dedicated capacity");
        searchPool.shutdown();
    }
}
```

**How to run:** save as `BulkheadIsolation.java`, then run `java BulkheadIsolation.java`.

## 6. Walkthrough

1. Level 1 submits 4 slow, 2-second tasks to a single `sharedPool` of exactly 4 threads, fully occupying it, then submits an unrelated, fast `checkoutCallShared` task to the same pool.
2. Because all 4 threads are busy sleeping on the slow tasks, `checkoutCallShared.get(200, ...)` times out — the checkout call is stuck in the queue, not because checkout itself is slow, but purely because it shares a resource pool with the struggling recommendations calls.
3. Level 2 repeats the exact same scenario, but with `recommendationsPool` and `checkoutPool` as two entirely separate `ExecutorService` instances. The 4 slow tasks saturate `recommendationsPool` exactly as before.
4. This time, `checkoutCallIsolated` is submitted to `checkoutPool`, a completely different pool with its own threads; `checkoutCallIsolated.get(200, ...)` succeeds immediately, since its pool was never touched by the recommendations slowdown.
5. Level 3 shows a `searchPool` sized generously enough (3 threads) to handle an expected burst of exactly 3 concurrent search requests, all completing successfully within that pool's own dedicated capacity — reinforcing that correct bulkhead sizing, not just the presence of separate pools, is what actually prevents resource exhaustion within a given bulkhead itself.

## 7. Gotchas & takeaways

> Gotcha: bulkheads only isolate the specific resource they partition (e.g. a thread pool); if two "isolated" dependencies still share something else critical — the same underlying database connection pool, the same downstream network link — a failure there can still cross the boundary the thread-pool bulkhead was meant to enforce. Trace every shared resource, not just the most obvious one, when designing isolation boundaries.

- Bulkhead isolation partitions resources (thread pools, connection pools) per dependency, so one dependency's failure or slowness cannot exhaust resources needed by unrelated, healthy functionality.
- Sizing each bulkhead appropriately for its own expected load is what determines whether it actually absorbs bursts and failures without either starving itself or wastefully over-provisioning.
- Bulkheads and circuit breakers combine naturally: each isolated pool can have its own breaker, tripping independently based on that specific dependency's health.
- Related concepts: [Circuit breaker](0136-circuit-breaker.md) (commonly applied per-bulkhead), [Connection reuse & pooling](0128-connection-reuse-pooling.md) (the kind of resource a bulkhead often partitions), [Single points of failure elimination](0133-single-points-of-failure-elimination.md) (the broader review discipline bulkheads support).
