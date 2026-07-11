---
card: spring-cloud
gi: 72
slug: bulkhead
title: "Bulkhead"
---

## 1. What it is

A bulkhead limits how many concurrent calls to a specific dependency are allowed at once — implemented either as a `SemaphoreBulkhead` (a simple concurrent-call counter with a fixed limit) or a `ThreadPoolBulkhead` (a dedicated, isolated thread pool for that dependency's calls) — named after a ship's bulkheads, which physically compartmentalize a hull so that one compartment flooding doesn't sink the whole vessel.

```properties
resilience4j.bulkhead.instances.billing-service.max-concurrent-calls=20

resilience4j.thread-pool-bulkhead.instances.reporting-service.max-thread-pool-size=5
resilience4j.thread-pool-bulkhead.instances.reporting-service.core-thread-pool-size=5
resilience4j.thread-pool-bulkhead.instances.reporting-service.queue-capacity=10
```

## 2. Why & when

A circuit breaker protects against a dependency that's *failing*; a bulkhead protects against a dependency that's *slow* — without a limit on concurrent calls, a slow (but not outright failing) downstream service can let callers pile up indefinitely, each holding a thread (or other resource) waiting for a response, until the *calling* service itself runs out of resources and starts failing too — resource exhaustion cascading from one struggling dependency into an otherwise-healthy caller.

Reach for a bulkhead when:

- A specific dependency's slowness (not outright failure) has historically caused the calling service to run out of threads/connections, taking down calls to *other*, unrelated, perfectly healthy dependencies in the process.
- Multiple downstream dependencies share a caller's limited resource pool (a fixed-size thread pool, a limited connection pool), and one dependency's problems shouldn't be allowed to starve the others of that shared resource.
- `ThreadPoolBulkhead` specifically, when a dependency's calls should be genuinely isolated onto their own dedicated threads — protecting the caller's *main* request-handling threads from ever being occupied by that dependency's slow calls at all.

## 3. Core concept

```
 without a bulkhead:
   caller has, say, 200 total threads shared across ALL downstream calls
   billing-service gets slow -> more and more threads pile up waiting on it
   -> eventually ALL 200 threads are stuck waiting on billing-service
   -> calls to inventory-service, promotions-service, etc. can't even get a thread to run on

 with a bulkhead (max-concurrent-calls=20 for billing-service):
   billing-service gets slow -> AT MOST 20 threads/calls can be stuck waiting on it at once
   -> the other 180 threads remain free for inventory-service, promotions-service, etc.
   -> the 21st+ concurrent call to billing-service is rejected immediately (or queued), not left to pile up
```

A bulkhead caps the blast radius of one dependency's slowness to a bounded slice of the caller's total resources, rather than letting it consume everything.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without a bulkhead a slow billing service call can consume every available thread, starving calls to other services, while a bulkhead caps billing service to a bounded slice, leaving the rest free">
  <rect x="20" y="20" width="290" height="80" rx="10" fill="#1c2430" stroke="#e64949" stroke-width="1.5"/>
  <text x="165" y="42" fill="#e64949" font-size="8" text-anchor="middle" font-family="sans-serif">without bulkhead</text>
  <text x="165" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">slow billing-service call consumes</text>
  <text x="165" y="74" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ALL 200 shared threads eventually</text>
  <text x="165" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">other services starved of threads too</text>

  <rect x="330" y="20" width="290" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">with bulkhead (max=20)</text>
  <text x="475" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-service capped at 20 concurrent</text>
  <text x="475" y="74" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">180 threads remain free for other calls</text>
  <text x="475" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">21st+ call rejected/queued, not left to pile up</text>

  <defs><marker id="a72" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The bulkhead's cap is what stops one slow dependency from monopolizing shared resources that other, unrelated calls also need.

## 5. Runnable example

The scenario: protect a shared thread pool from being monopolized by a slow `billing-service`. Start with unbounded concurrent calls (the resource exhaustion problem), then add a semaphore-style bulkhead capping concurrency, then simulate the actual starvation-prevention effect against a second, unrelated service sharing the same pool.

### Level 1 — Basic

Unbounded concurrent calls — no protection against a slow dependency consuming everything.

```java
import java.util.concurrent.atomic.AtomicInteger;

public class BulkheadLevel1 {
    static AtomicInteger activeBillingCalls = new AtomicInteger(0);
    static int totalSharedThreads = 10; // deliberately small, to make the problem visible quickly

    static boolean callBilling() {
        int current = activeBillingCalls.incrementAndGet(); // no limit at all -- grows without bound
        return current <= totalSharedThreads; // true means "still had a thread available"
    }

    public static void main(String[] args) {
        // simulate 15 slow, concurrent billing-service calls all piling up at once
        int successfullyStarted = 0;
        for (int i = 0; i < 15; i++) {
            if (callBilling()) successfullyStarted++;
        }
        System.out.println("billing calls that found a free thread: " + successfullyStarted + " out of 15");
        System.out.println("threads now stuck on billing-service: " + activeBillingCalls.get()
                + " out of " + totalSharedThreads + " total -- NOTHING left for other services");
    }
}
```

How to run: `java BulkheadLevel1.java`

`activeBillingCalls` grows without any cap — 15 concurrent slow calls against only 10 total shared threads means every single thread ends up stuck waiting on `billing-service`, leaving nothing at all for any other, unrelated downstream call that might need a thread at the same time.

### Level 2 — Intermediate

Add a semaphore-style bulkhead: cap `billing-service`'s concurrent calls at a configured limit, rejecting anything beyond it immediately.

```java
import java.util.concurrent.atomic.AtomicInteger;

public class BulkheadLevel2 {
    static class SemaphoreBulkhead {
        AtomicInteger active = new AtomicInteger(0);
        int maxConcurrentCalls;

        SemaphoreBulkhead(int maxConcurrentCalls) { this.maxConcurrentCalls = maxConcurrentCalls; }

        boolean tryAcquire() {
            int current = active.incrementAndGet();
            if (current > maxConcurrentCalls) {
                active.decrementAndGet(); // give the slot back -- this call is rejected
                return false;
            }
            return true;
        }

        void release() { active.decrementAndGet(); }
    }

    public static void main(String[] args) {
        SemaphoreBulkhead billingBulkhead = new SemaphoreBulkhead(5); // cap at 5, out of a much larger shared pool

        int accepted = 0, rejected = 0;
        for (int i = 0; i < 15; i++) {
            if (billingBulkhead.tryAcquire()) accepted++;
            else rejected++;
        }

        System.out.println("accepted: " + accepted + ", rejected immediately: " + rejected);
        System.out.println("threads consumed by billing-service: " + billingBulkhead.active.get() + " (capped at 5)");
    }
}
```

How to run: `java BulkheadLevel2.java`

`SemaphoreBulkhead.tryAcquire` rejects any call beyond `maxConcurrentCalls`, immediately handing the slot back rather than letting it linger — out of 15 attempted concurrent calls, only 5 are accepted and the other 10 are rejected immediately (in a real system, this typically means the caller gets a `BulkheadFullException` right away, fast enough to try a fallback rather than waiting indefinitely for a thread that was never going to become available).

### Level 3 — Advanced

Simulate the actual starvation-prevention effect: a shared pool serving both `billing-service` (slow) and `inventory-service` (healthy), confirming the bulkhead keeps `inventory-service` calls succeeding even while `billing-service` is being hammered with far more concurrent requests than its cap allows.

```java
import java.util.concurrent.atomic.AtomicInteger;

public class BulkheadLevel3 {
    static class SemaphoreBulkhead {
        AtomicInteger active = new AtomicInteger(0);
        int maxConcurrentCalls;
        SemaphoreBulkhead(int max) { this.maxConcurrentCalls = max; }
        boolean tryAcquire() {
            int current = active.incrementAndGet();
            if (current > maxConcurrentCalls) { active.decrementAndGet(); return false; }
            return true;
        }
        void release() { active.decrementAndGet(); }
    }

    static int totalSharedThreads = 20;
    static AtomicInteger threadsInUse = new AtomicInteger(0);

    static SemaphoreBulkhead billingBulkhead = new SemaphoreBulkhead(5); // billing-service capped at 5
    // inventory-service has NO bulkhead cap of its own -- it just needs a free thread from the shared pool

    static boolean callBilling() {
        if (!billingBulkhead.tryAcquire()) return false; // rejected by the bulkhead before even touching a thread
        boolean gotThread = threadsInUse.incrementAndGet() <= totalSharedThreads;
        return gotThread; // (billingBulkhead.release() would happen when the slow call actually finishes)
    }

    static boolean callInventory() {
        int used = threadsInUse.incrementAndGet();
        boolean gotThread = used <= totalSharedThreads;
        if (!gotThread) threadsInUse.decrementAndGet();
        return gotThread;
    }

    public static void main(String[] args) {
        // 30 concurrent billing-service calls arrive, all slow -- far more than its bulkhead cap of 5
        int billingAccepted = 0;
        for (int i = 0; i < 30; i++) if (callBilling()) billingAccepted++;

        System.out.println("billing-service calls that acquired a thread: " + billingAccepted + " (capped at 5 by its bulkhead)");
        System.out.println("shared threads consumed so far: " + threadsInUse.get() + " out of " + totalSharedThreads);

        // inventory-service, unrelated and healthy, still tries to get a thread from the SAME shared pool
        boolean inventoryCallSucceeded = callInventory();
        System.out.println("inventory-service call still got a thread: " + inventoryCallSucceeded
                + " (because billing-service was capped, plenty of threads remained free)");
    }
}
```

How to run: `java BulkheadLevel3.java`

Even though 30 concurrent calls arrive for `billing-service`, `billingBulkhead.tryAcquire()` rejects all but 5 of them immediately, so only 5 shared threads ever actually get consumed by `billing-service` — leaving 15 of the 20 total shared threads free. When `callInventory()` then requests a thread from that same shared pool, it succeeds easily, because `billing-service`'s slowness was contained to its bulkhead's cap rather than being allowed to consume the entire shared pool, exactly the isolation a bulkhead exists to guarantee.

## 6. Walkthrough

Trace Level 3's execution.

1. The loop calls `callBilling()` 30 times. Each call first invokes `billingBulkhead.tryAcquire()` — for the first 5 calls, `active.incrementAndGet()` returns `1` through `5`, each `<= 5`, so `tryAcquire` returns `true` and the call proceeds to consume a shared thread via `threadsInUse.incrementAndGet()`.
2. Starting with the 6th call, `active.incrementAndGet()` returns `6`, which is `> 5`, so `tryAcquire` immediately decrements `active` back down (giving the slot back) and returns `false` — `callBilling` short-circuits and returns `false` without ever touching `threadsInUse` at all. This repeats for calls 6 through 30, all rejected at the bulkhead before consuming any shared thread.
3. The first `println` confirms exactly 5 of the 30 attempted `billing-service` calls succeeded in acquiring a thread — precisely the bulkhead's configured cap, regardless of how many more were attempted.
4. The second `println` shows `threadsInUse.get()` at `5` — only the 5 bulkhead-accepted calls actually consumed shared threads; the 25 rejected calls left the pool completely untouched.
5. `callInventory()` runs — it has no bulkhead of its own, so it directly calls `threadsInUse.incrementAndGet()`, which returns `6`, comfortably `<= 20`. The call succeeds easily, since 15 of the pool's 20 threads remain free precisely because `billing-service`'s 25 excess concurrent attempts were rejected at the bulkhead rather than being allowed to actually consume threads.

```
30 concurrent billing-service calls arrive
   -> bulkhead (cap=5) accepts only the first 5, rejects the other 25 immediately
   -> shared pool: 5/20 threads consumed by billing-service

inventory-service call arrives (no bulkhead of its own)
   -> shared pool still has 15/20 threads free
   -> succeeds easily, completely unaffected by billing-service's flood of requests
```

## 7. Gotchas & takeaways

> **Gotcha:** `SemaphoreBulkhead` limits *concurrent calls* but the calling thread still runs the call itself (blocking on it, in a blocking client) — it doesn't isolate the *thread* the way `ThreadPoolBulkhead` does. If the calling code's own request-handling threads are what's making these calls, a semaphore bulkhead limits how many can be in flight, but a slow call among the permitted few still occupies one of those actual request-handling threads for its full duration. `ThreadPoolBulkhead` genuinely isolates the calls onto their own dedicated pool, fully protecting the caller's main threads from ever being tied up by that dependency at all — a meaningfully different (and often stronger) isolation guarantee, at the cost of the overhead of managing a separate thread pool.

- A bulkhead protects against a *slow* dependency consuming shared resources, complementing (not replacing) a circuit breaker, which protects against a *failing* one — real production resilience configuration typically uses both together for the same dependency.
- The bulkhead's cap should reflect how much of the caller's total resource budget one dependency is allowed to consume, not the dependency's own expected throughput — it's fundamentally about protecting the *caller's* other work, not optimizing the protected dependency's performance.
- `SemaphoreBulkhead` is lighter-weight and simpler; `ThreadPoolBulkhead` provides stronger isolation (a genuinely separate thread pool) at the cost of additional resource overhead — choose based on how strictly the calling threads themselves need to be protected.
- A rejected bulkhead call should, like a tripped circuit breaker, generally have a sensible fallback — being turned away immediately by a full bulkhead is a fast, cheap failure mode exactly because it avoids the alternative of waiting indefinitely for a resource that was never going to become available in time.
