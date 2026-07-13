---
card: microservices
gi: 242
slug: fault-isolation
title: "Fault isolation"
---

## 1. What it is

Fault isolation is the practice of structuring a system so that a failure in one part — one dependency, one resource pool, one tenant's workload — cannot consume resources needed by unrelated parts, containing the failure's blast radius to just the component that actually failed rather than letting it spread and degrade the whole system.

## 2. Why & when

Without isolation, a shared resource (a single thread pool, a single connection pool) used by calls to many different dependencies creates a hidden coupling between them: if one dependency becomes slow, every thread waiting on calls to that slow dependency accumulates in the shared pool, and once the pool is exhausted, calls to *completely unrelated, perfectly healthy* dependencies can no longer get a thread to run on either — one failing dependency has taken down access to every other dependency, purely through shared resource contention, not any direct interaction between them. This is a primary mechanism behind [cascading failures](0243-cascading-failures.md). Fault isolation, most commonly implemented via the [bulkhead pattern](0242-fault-isolation.md) (dedicating separate resource pools per dependency), prevents this by ensuring one dependency's resource exhaustion can only ever exhaust *its own* dedicated pool.

Apply fault isolation wherever multiple, independent dependencies (or tenants, or workload types) share an underlying resource pool that could be exhausted by one of them misbehaving — nearly always true for any service calling more than one downstream dependency through a shared thread or connection pool.

## 3. Core concept

Isolation is achieved by partitioning a shared resource into separate, dedicated pools per dependency (or tenant), so exhausting one partition has no effect on the resources available to any other partition — the isolation boundary is what determines the blast radius of any single failure.

```java
// WITHOUT isolation -- ONE shared pool serves calls to BOTH dependencies
ExecutorService sharedPool = Executors.newFixedThreadPool(20);
sharedPool.submit(() -> callSlowInventoryService()); // if THIS hangs repeatedly, it can consume ALL 20 threads
sharedPool.submit(() -> callFastPaymentService());    // starved of threads, even though PAYMENT itself is healthy

// WITH isolation -- SEPARATE, dedicated pools; one CANNOT starve the other
ExecutorService inventoryPool = Executors.newFixedThreadPool(10); // inventory's OWN dedicated pool
ExecutorService paymentPool = Executors.newFixedThreadPool(10);   // payment's OWN dedicated pool, UNAFFECTED by inventory's issues
inventoryPool.submit(() -> callSlowInventoryService()); // can exhaust inventoryPool, but NEVER paymentPool
paymentPool.submit(() -> callFastPaymentService());     // stays healthy regardless of inventory's state
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without isolation, a shared thread pool serving calls to both a slow inventory service and a fast payment service can be exhausted entirely by the slow dependency, starving the healthy one; with isolation, each dependency has its own dedicated pool, so the slow dependency's exhaustion cannot affect the healthy one" >
  <rect x="20" y="15" width="280" height="70" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="35" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">WITHOUT isolation</text>
  <text x="160" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ONE shared pool, both dependencies</text>
  <text x="160" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">slow dependency starves the fast one</text>

  <rect x="340" y="15" width="280" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="35" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">WITH isolation</text>
  <text x="480" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">separate dedicated pools</text>
  <text x="480" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">one exhausting cannot affect the other</text>

  <rect x="60" y="120" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="144" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">inventory pool</text>
  <rect x="450" y="120" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="495" y="144" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">payment pool</text>
</svg>

Dedicated, isolated pools ensure one dependency's failure can only exhaust its own allocation, never a healthy dependency's.

## 5. Runnable example

Scenario: a service calling two dependencies through one shared, small thread pool, where a slow dependency's hanging calls exhaust the pool and starve the healthy dependency, refactored to use isolated, per-dependency pools that keep the healthy dependency responsive regardless of the slow one's state, and finally demonstrating measuring and reporting per-pool exhaustion so a real degradation can be observed and attributed to the correct failing dependency.

### Level 1 — Basic

```java
// File: SharedPoolStarvation.java -- ONE shared pool serves BOTH
// dependencies; the SLOW one exhausts it, starving the FAST, healthy one.
import java.util.concurrent.*;

public class SharedPoolStarvation {
    static ExecutorService sharedPool = Executors.newFixedThreadPool(2); // SMALL, SHARED pool

    static String callSlowInventoryService() throws InterruptedException {
        Thread.sleep(500); // simulates a HANGING dependency
        return "inventory OK";
    }
    static String callFastPaymentService() { return "payment OK"; }

    public static void main(String[] args) throws Exception {
        // TWO slow inventory calls occupy BOTH threads in the shared pool
        Future<String> slow1 = sharedPool.submit(() -> callSlowInventoryService());
        Future<String> slow2 = sharedPool.submit(() -> callSlowInventoryService());

        long start = System.currentTimeMillis();
        Future<String> fastCall = sharedPool.submit(() -> callFastPaymentService()); // must WAIT for a free thread
        String result = fastCall.get();
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("Payment call result: " + result + ", but took " + elapsed + "ms -- STARVED waiting for a thread, despite being fast itself.");
        sharedPool.shutdown();
    }
}
```

**How to run:** `javac SharedPoolStarvation.java && java SharedPoolStarvation` (JDK 17+).

### Level 2 — Intermediate

```java
// File: IsolatedDedicatedPools.java -- SEPARATE pools per dependency;
// the slow dependency CANNOT starve the fast, healthy one anymore.
import java.util.concurrent.*;

public class IsolatedDedicatedPools {
    static ExecutorService inventoryPool = Executors.newFixedThreadPool(2); // inventory's OWN pool
    static ExecutorService paymentPool = Executors.newFixedThreadPool(2);   // payment's OWN, ISOLATED pool

    static String callSlowInventoryService() throws InterruptedException {
        Thread.sleep(500);
        return "inventory OK";
    }
    static String callFastPaymentService() { return "payment OK"; }

    public static void main(String[] args) throws Exception {
        Future<String> slow1 = inventoryPool.submit(() -> callSlowInventoryService());
        Future<String> slow2 = inventoryPool.submit(() -> callSlowInventoryService()); // BOTH inventory threads occupied

        long start = System.currentTimeMillis();
        Future<String> fastCall = paymentPool.submit(() -> callFastPaymentService()); // uses its OWN pool -- unaffected
        String result = fastCall.get();
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("Payment call result: " + result + ", took " + elapsed + "ms -- FAST, since it never competed for inventory's threads.");
        inventoryPool.shutdown(); paymentPool.shutdown();
    }
}
```

**How to run:** `javac IsolatedDedicatedPools.java && java IsolatedDedicatedPools` (JDK 17+).

Expected output (timing-dependent, but the qualitative gap is stable):
```
Payment call result: payment OK, took 1ms -- FAST, since it never competed for inventory's threads.
```

### Level 3 — Advanced

```java
// File: MonitoredPoolExhaustion.java -- tracks and reports PER-POOL
// exhaustion, so a real degradation is OBSERVABLE and correctly
// attributed to the ACTUAL failing dependency, not misdiagnosed as
// a system-wide issue.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class MonitoredPoolExhaustion {
    static class MonitoredPool {
        String name;
        ThreadPoolExecutor executor;
        AtomicInteger rejectedCount = new AtomicInteger(0);

        MonitoredPool(String name, int size) {
            this.name = name;
            this.executor = new ThreadPoolExecutor(size, size, 0L, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(1), // a SMALL queue -- exhaustion happens quickly, for a fast demo
                (r, exec) -> rejectedCount.incrementAndGet()); // REJECTED tasks are COUNTED, not silently dropped
        }

        void reportHealth() {
            System.out.println("  [" + name + " pool] active=" + executor.getActiveCount() + ", rejected=" + rejectedCount.get());
        }
    }

    public static void main(String[] args) throws Exception {
        MonitoredPool inventoryPool = new MonitoredPool("inventory", 1); // deliberately TINY, to trigger exhaustion
        MonitoredPool paymentPool = new MonitoredPool("payment", 2);

        // FLOOD the inventory pool with slow tasks -- more than it can handle
        for (int i = 0; i < 5; i++) {
            try { inventoryPool.executor.submit(() -> { try { Thread.sleep(200); } catch (InterruptedException ignored) {} }); }
            catch (RejectedExecutionException ignored) {}
        }

        // payment pool receives NORMAL load -- well within its capacity
        paymentPool.executor.submit(() -> {});
        paymentPool.executor.submit(() -> {});

        Thread.sleep(50); // let submissions settle
        System.out.println("Health report:");
        inventoryPool.reportHealth(); // shows REJECTIONS -- inventory is CLEARLY the failing dependency
        paymentPool.reportHealth();   // shows ZERO rejections -- payment is CLEARLY healthy

        inventoryPool.executor.shutdown(); paymentPool.executor.shutdown();
    }
}
```

**How to run:** `javac MonitoredPoolExhaustion.java && java MonitoredPoolExhaustion` (JDK 17+).

Expected output (exact active/rejected counts may vary slightly with timing, but inventory shows rejections and payment shows none):
```
Health report:
  [inventory pool] active=1, rejected=3
  [payment pool] active=0, rejected=0
```

## 6. Walkthrough

1. **Level 1, the shared bottleneck** — `sharedPool` has only two threads, and the two `callSlowInventoryService` submissions occupy both of them for the full 500ms sleep; the subsequent `callFastPaymentService` submission has no free thread to run on until one of the slow tasks finishes, so its `Future.get()` blocks for nearly the same 500ms as the slow calls, even though `callFastPaymentService` itself does no waiting at all.
2. **Level 2, dedicated pools breaking the coupling** — `inventoryPool` and `paymentPool` are two entirely separate `ExecutorService` instances; the slow calls submitted to `inventoryPool` have no way to consume threads from `paymentPool`, because `ThreadPoolExecutor`s don't share their thread allocations with each other.
3. **Level 2, the isolated outcome** — `paymentPool.submit(...)` finds a free thread immediately (since `inventoryPool`'s exhaustion is entirely contained within `inventoryPool` itself), so the payment call completes in roughly 1ms rather than being dragged down to inventory's 500ms — the exact scenario fault isolation is designed to prevent.
4. **Level 3, tracking rejections explicitly** — `MonitoredPool` wraps a `ThreadPoolExecutor` configured with a small bounded queue and a custom rejection handler that increments `rejectedCount` rather than throwing or silently discarding excess work, giving each pool an observable signal for "this pool is currently overwhelmed."
5. **Level 3, flooding one pool intentionally** — five slow tasks are submitted to the deliberately tiny `inventoryPool` (capacity for one running task plus one queued), so several of them are rejected and counted, simulating a genuinely overwhelmed dependency; `paymentPool`, receiving only two ordinary tasks well within its own capacity, records zero rejections.
6. **Level 3, the health report pinpointing the actual problem** — `reportHealth()` prints each pool's active count and rejection count independently; the resulting report clearly shows `inventory`'s pool under distress (non-zero `rejected`) while `payment`'s pool reports completely healthy (`rejected=0`) — this per-pool visibility is exactly what fault isolation, combined with monitoring each isolated pool separately, provides: a clear, immediate attribution of *which* dependency is actually failing, rather than an ambiguous, system-wide "something's slow" signal that isolation alone (without monitoring) wouldn't fully resolve.

## 7. Gotchas & takeaways

> **Gotcha:** isolating pools per dependency means each pool needs its own sizing decision, and under-sizing an isolated pool can create artificial bottlenecks even when the dependency itself is healthy — a shared pool at least allowed idle capacity from one dependency's calls to absorb a burst from another; isolation trades that flexibility for containment, which is usually the right trade for resilience, but pool sizes need deliberate capacity planning per dependency, not a single one-size-fits-all number copied across every pool.

- Fault isolation partitions shared resources (thread pools, connection pools) per dependency, so one dependency's resource exhaustion cannot starve access to a different, healthy dependency.
- Without isolation, a shared resource pool creates a hidden coupling between unrelated dependencies, where one slow or hanging dependency can degrade access to everything else sharing that pool — a common mechanism behind [cascading failures](0243-cascading-failures.md).
- Isolation should be paired with per-pool monitoring (tracking rejections, active counts) so a degradation can be observed and correctly attributed to the specific failing dependency, not just contained silently.
- This is the underlying principle the [bulkhead pattern](0242-fault-isolation.md), covered by name as its own topic, implements concretely.
- Isolated pools each need their own deliberate capacity planning; under-sizing one can create a bottleneck specific to that dependency even when it's otherwise healthy, trading away the flexibility a shared pool's idle capacity used to provide.
