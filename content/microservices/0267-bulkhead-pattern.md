---
card: microservices
gi: 267
slug: bulkhead-pattern
title: "Bulkhead pattern"
---

## 1. What it is

The bulkhead pattern partitions a service's resources (thread pools, connection pools) into isolated compartments per dependency, named by analogy to a ship's bulkheads — the watertight compartments that let one section flood without sinking the entire vessel — so that one dependency exhausting its allotted resources cannot starve resources needed for calls to a completely different, healthy dependency.

## 2. Why & when

This is the concrete, named pattern implementing what [fault isolation](0242-fault-isolation.md) describes generally: without partitioned resources, a single shared thread pool serving calls to multiple dependencies creates a hidden coupling where one dependency's slowness or failure consumes threads that calls to other, unrelated, perfectly healthy dependencies also needed — exactly the mechanism behind [cascading failures](0243-cascading-failures.md). The bulkhead pattern breaks this coupling structurally, by giving each dependency (or each meaningfully distinct category of work) its own dedicated, bounded resource allocation, so a failure's blast radius is contained to the compartment it originated in.

Apply a bulkhead wherever a service calls more than one dependency through resources that would otherwise be shared — nearly universal for any service with multiple downstream dependencies. This section covers two concrete implementation styles — [thread-pool bulkheads](0268-thread-pool-bulkhead.md) and [semaphore bulkheads](0269-semaphore-bulkhead.md) — each suited to different execution models.

## 3. Core concept

A bulkhead limits the number of concurrent calls to a specific dependency to a fixed maximum, using either a dedicated thread pool (calls execute on separate, isolated threads) or a semaphore (calls execute on the caller's own thread, but concurrency is still capped) — either way, exceeding the limit means new calls are rejected or queued, rather than the dependency's calls competing for resources shared with anything else.

```java
// a BULKHEAD, conceptually -- caps concurrent calls to ONE specific dependency
Bulkhead inventoryBulkhead = Bulkhead.of("inventory-service",
    BulkheadConfig.custom().maxConcurrentCalls(10).build()); // ISOLATED capacity, dedicated to THIS dependency

String result = inventoryBulkhead.executeSupplier(() -> inventoryService.checkStock(productId));
// if inventory-service is SLOW and its 10 slots FILL UP, ONLY inventory-service calls are affected --
// a call to payment-service, using its OWN separate bulkhead, is COMPLETELY unaffected
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two dependencies, inventory service and payment service, each have their own isolated bulkhead with dedicated capacity; inventory service's bulkhead being fully exhausted has no effect on payment service's separate, unaffected bulkhead" >
  <rect x="20" y="20" width="270" height="130" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="155" y="40" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Inventory bulkhead (EXHAUSTED)</text>
  <rect x="40" y="55" width="40" height="30" fill="#8b949e"/><rect x="90" y="55" width="40" height="30" fill="#8b949e"/>
  <rect x="140" y="55" width="40" height="30" fill="#8b949e"/><rect x="190" y="55" width="40" height="30" fill="#8b949e"/>
  <rect x="240" y="55" width="40" height="30" fill="#8b949e"/>
  <text x="155" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">all slots FULL -- new calls REJECTED</text>

  <rect x="350" y="20" width="270" height="130" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="40" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Payment bulkhead (UNAFFECTED)</text>
  <rect x="370" y="55" width="40" height="30" fill="#1c2430" stroke="#6db33f"/><rect x="420" y="55" width="40" height="30" fill="#1c2430" stroke="#6db33f"/>
  <rect x="470" y="55" width="40" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="485" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">plenty of SEPARATE capacity, working normally</text>
</svg>

Isolated compartments mean one dependency's exhaustion is structurally contained, never spilling into another's.

## 5. Runnable example

Scenario: two dependencies sharing one thread pool where one dependency's slowness starves the other, refactored to give each dependency its own dedicated bulkhead pool eliminating that coupling, and finally demonstrating rejecting a call once a bulkhead's capacity is fully exhausted rather than blocking indefinitely, showing the bulkhead's own bounded-capacity behavior under sustained overload.

### Level 1 — Basic

```java
// File: SharedResourceCoupling.java -- ONE shared thread pool for BOTH
// dependencies -- inventory's slowness STARVES payment.
import java.util.concurrent.*;

public class SharedResourceCoupling {
    static ExecutorService sharedPool = Executors.newFixedThreadPool(2);

    static String callSlowInventory() throws InterruptedException { Thread.sleep(300); return "inventory OK"; }
    static String callFastPayment() { return "payment OK"; }

    public static void main(String[] args) throws Exception {
        Future<String> slow1 = sharedPool.submit(SharedResourceCoupling::callSlowInventory);
        Future<String> slow2 = sharedPool.submit(SharedResourceCoupling::callSlowInventory); // BOTH threads occupied

        long start = System.currentTimeMillis();
        Future<String> fast = sharedPool.submit(() -> callFastPayment());
        String result = fast.get();
        System.out.println("Payment call: " + result + ", took " + (System.currentTimeMillis() - start) + "ms -- STARVED by inventory.");
        sharedPool.shutdown();
    }
}
```

**How to run:** `javac SharedResourceCoupling.java && java SharedResourceCoupling` (JDK 17+).

### Level 2 — Intermediate

```java
// File: IsolatedBulkheads.java -- SEPARATE, dedicated bulkhead pools --
// inventory's slowness NO LONGER affects payment AT ALL.
import java.util.concurrent.*;

public class IsolatedBulkheads {
    static ExecutorService inventoryBulkhead = Executors.newFixedThreadPool(2); // inventory's OWN bulkhead
    static ExecutorService paymentBulkhead = Executors.newFixedThreadPool(2);   // payment's OWN, ISOLATED bulkhead

    static String callSlowInventory() throws InterruptedException { Thread.sleep(300); return "inventory OK"; }
    static String callFastPayment() { return "payment OK"; }

    public static void main(String[] args) throws Exception {
        Future<String> slow1 = inventoryBulkhead.submit(IsolatedBulkheads::callSlowInventory);
        Future<String> slow2 = inventoryBulkhead.submit(IsolatedBulkheads::callSlowInventory);

        long start = System.currentTimeMillis();
        Future<String> fast = paymentBulkhead.submit(() -> callFastPayment()); // its OWN bulkhead -- unaffected
        String result = fast.get();
        System.out.println("Payment call: " + result + ", took " + (System.currentTimeMillis() - start) + "ms -- FAST, isolated from inventory.");
        inventoryBulkhead.shutdown(); paymentBulkhead.shutdown();
    }
}
```

**How to run:** `javac IsolatedBulkheads.java && java IsolatedBulkheads` (JDK 17+).

Expected output:
```
Payment call: payment OK, took 1ms -- FAST, isolated from inventory.
```

### Level 3 — Advanced

```java
// File: BulkheadRejectsWhenExhausted.java -- a bulkhead's OWN capacity
// still has a LIMIT -- once EXHAUSTED, further calls are REJECTED
// rather than blocking indefinitely, protecting the CALLER too.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BulkheadRejectsWhenExhausted {
    static final int BULKHEAD_CAPACITY = 3;
    static Semaphore bulkheadSlots = new Semaphore(BULKHEAD_CAPACITY); // caps CONCURRENT calls to THIS dependency

    static String callBulkheadProtected(int callId) throws InterruptedException {
        if (!bulkheadSlots.tryAcquire()) { // NON-blocking check -- if no slot is free, REJECT immediately
            return "call " + callId + ": REJECTED (bulkhead full, " + BULKHEAD_CAPACITY + "/" + BULKHEAD_CAPACITY + " slots occupied)";
        }
        try {
            Thread.sleep(200); // simulates a slow call HOLDING its slot
            return "call " + callId + ": SUCCESS";
        } finally {
            bulkheadSlots.release(); // ALWAYS release, even on failure
        }
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(6);
        // SIX concurrent calls arrive, but the bulkhead only permits 3 AT ONCE
        Future<String>[] futures = new Future[6];
        for (int i = 0; i < 6; i++) {
            final int callId = i + 1;
            futures[i] = pool.submit(() -> callBulkheadProtected(callId));
        }
        for (Future<String> f : futures) System.out.println(f.get());
        pool.shutdown();
    }
}
```

**How to run:** `javac BulkheadRejectsWhenExhausted.java && java BulkheadRejectsWhenExhausted` (JDK 17+).

Expected output (exact ordering of REJECTED vs SUCCESS may vary slightly with thread scheduling, but 3 succeed and 3 are rejected):
```
call 1: SUCCESS
call 2: SUCCESS
call 3: SUCCESS
call 4: REJECTED (bulkhead full, 3/3 slots occupied)
call 5: REJECTED (bulkhead full, 3/3 slots occupied)
call 6: REJECTED (bulkhead full, 3/3 slots occupied)
```

## 6. Walkthrough

1. **Level 1, the coupling problem** — `sharedPool` has only two threads, both occupied by the two `callSlowInventory` submissions for the full 300ms sleep; the `callFastPayment` submission, despite being instantaneous itself, has to wait for a free thread, so its measured elapsed time is dragged down to nearly the same 300ms as the slow calls sharing its pool.
2. **Level 2, separate dedicated pools** — `inventoryBulkhead` and `paymentBulkhead` are entirely independent `ExecutorService` instances; the slow inventory calls occupy only `inventoryBulkhead`'s two threads, leaving `paymentBulkhead`'s threads completely untouched and immediately available.
3. **Level 2, the isolated, fast outcome** — the payment call submitted to its own dedicated bulkhead completes in roughly 1ms, exactly matching its actual processing time with no artificial delay imposed by inventory's unrelated slowness — this is the direct, measurable benefit of resource partitioning.
4. **Level 3, a bulkhead's own bounded capacity** — `bulkheadSlots`, a `Semaphore` initialized with `BULKHEAD_CAPACITY` (3) permits, models a bulkhead's own concurrency limit; `tryAcquire()` attempts to obtain a permit without blocking, returning `false` immediately if none are available rather than waiting.
5. **Level 3, six concurrent calls against three available slots** — all six calls are submitted to a six-thread pool essentially simultaneously; the first three to successfully call `tryAcquire()` obtain one of the three available permits and proceed to their (slow, 200ms) simulated work, while the remaining three find `bulkheadSlots` already fully depleted and are rejected immediately, without ever performing the slow work at all.
6. **Level 3, why rejecting (rather than queuing indefinitely) matters** — if the bulkhead instead queued excess calls indefinitely waiting for a slot to free up, a sustained burst of calls could still accumulate an unbounded backlog of waiting threads or requests, reintroducing a version of the same unbounded-resource-consumption risk the bulkhead was meant to prevent in the first place; rejecting immediately once capacity is exhausted (as `tryAcquire`'s non-blocking behavior does here) gives the caller an immediate, actionable signal — retry later, use a fallback — rather than an indefinite, silent wait, extending the bulkhead's protective philosophy to its own internal capacity limit, not just to isolating one dependency's resources from another's.

## 7. Gotchas & takeaways

> **Gotcha:** sizing a bulkhead too small for a dependency's legitimate peak load creates an artificial bottleneck even when that dependency is completely healthy — a bulkhead trades away the flexibility a shared pool's idle capacity would otherwise provide, so each bulkhead's capacity needs deliberate sizing based on that specific dependency's actual expected concurrency, not a uniform number copied across every dependency regardless of its real traffic pattern.

- The bulkhead pattern partitions resources (thread pools, connection pools) per dependency, so one dependency's exhaustion cannot starve resources needed by a different, healthy dependency — the concrete implementation of the general [fault isolation](0242-fault-isolation.md) principle.
- Isolating resources this way directly addresses a primary mechanism behind [cascading failures](0243-cascading-failures.md): a shared resource pool creating hidden coupling between otherwise-unrelated dependencies.
- A bulkhead itself has a bounded capacity, and calls exceeding that capacity should be rejected promptly rather than queued indefinitely, extending the same protective philosophy to the bulkhead's own limits.
- Two common implementation styles — [thread-pool bulkheads](0268-thread-pool-bulkhead.md) and [semaphore bulkheads](0269-semaphore-bulkhead.md) — suit different execution models, covered next.
- Bulkhead capacity needs deliberate, per-dependency sizing based on real expected concurrency; under-sizing trades away the shared-pool flexibility that used to absorb bursts, creating a bottleneck specific to that dependency even when it's healthy.
