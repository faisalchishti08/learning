---
card: microservices
gi: 505
slug: cache-stampede-thundering-herd
title: "Cache stampede / thundering herd"
---

## 1. What it is

A **cache stampede** (or **thundering herd**) happens when a popular cache entry expires and a large burst of concurrent requests for that same key all miss the cache simultaneously — every one of them independently proceeds to hit the underlying data store or expensive computation at once, instead of just one request refreshing the cache while the rest wait for or reuse that result. What should have been one expensive operation becomes N simultaneous expensive operations, often overwhelming the very system the cache was meant to protect.

## 2. Why & when

You need to defend against stampedes specifically for any hot cache key with meaningful concurrent traffic, because the failure mode is a direct, severe amplification of load exactly when a system is already momentarily vulnerable:

- **A popular key means many concurrent requests are likely to arrive within the same short window** — the more popular the cached value, the more requests are waiting on it at any given moment, and the worse a stampede against it will be when it expires.
- **The underlying data store often can't handle N simultaneous requests as easily as it handles 1 request every so often.** A database query that's perfectly fine run once every 60 seconds (the cache's TTL) can be a serious problem run 500 times in the same single second, which is exactly what an unguarded stampede does.
- **This is a self-inflicted amplification, not an external traffic spike** — the load multiplication comes entirely from the cache's own expiry mechanics interacting with concurrent request patterns, meaning it's fully within your control to prevent.
- **You add stampede protection specifically to hot keys where the underlying computation or query is expensive enough that N simultaneous copies would actually cause harm** — for cheap-to-recompute or low-traffic keys, the protection's own complexity may not be worth adding.

## 3. Core concept

Think of a single ticket window at a popular event, where the window closes briefly for a break (the cache entry expiring) — if everyone in line rushes every other ticket window simultaneously the moment the main window closes, all those other windows get overwhelmed at once. A better system: one person is deputized to specifically go refresh the main window's supply while everyone else in line simply waits a moment for it to reopen, rather than everyone scattering to overload every alternative resource simultaneously.

Concretely, the common mitigations:

1. **Locking (single-flight)**: when a cache miss occurs, the first request to notice acquires a lock and proceeds to recompute the value; every other concurrent request for the same key waits on that lock and reuses the result once it's ready, rather than each independently recomputing.
2. **Early/probabilistic expiry**: refresh a cache entry slightly *before* its actual expiry, with some randomized jitter — spreading out refresh timing across many keys so they don't all expire in the same instant, and giving one lucky early request the job of refreshing before the crowd would otherwise stampede at the exact expiry moment.
3. **Stale-while-revalidate**: serve the (slightly) stale cached value to most requests while exactly one request in the background refreshes it — trading a small amount of extra staleness for completely avoiding the stampede's load spike.
4. **Request coalescing**: multiple concurrent requests for the same missing key are deliberately merged into one actual underlying call, with the single result fanned back out to every waiting caller.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without protection, many concurrent requests on a cache miss all hit the origin simultaneously; with single-flight locking, only one request hits the origin while the rest wait and reuse its result">
  <rect x="20" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="165" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">unprotected: STAMPEDE</text>
  <text x="165" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">500 concurrent requests -&gt; 500 origin calls</text>

  <rect x="350" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">single-flight: PROTECTED</text>
  <text x="495" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">500 concurrent requests -&gt; 1 origin call, 499 wait</text>
</svg>

Single-flight locking collapses a stampede of N concurrent recomputations into exactly one.

## 5. Runnable example

Scenario: a cache-miss handler under concurrent load. We start with a basic unprotected version demonstrating the stampede problem directly, extend it to single-flight locking that collapses concurrent misses into one computation, then handle the hard case: ensuring waiting requests correctly receive the result even if the one doing the actual work fails, rather than hanging forever.

### Level 1 — Basic

```java
// File: StampedeUnprotected.java -- models the PROBLEM: MANY concurrent
// threads all missing the cache SIMULTANEOUSLY, each independently
// hitting the expensive origin computation.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class StampedeUnprotected {
    static AtomicInteger originCallCount = new AtomicInteger(0);

    static String expensiveOriginCall() {
        originCallCount.incrementAndGet();
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return "computed-value";
    }

    static String getWithoutProtection(String key) {
        // NO locking, NO coordination -- every caller that misses just computes independently.
        return expensiveOriginCall();
    }

    public static void main(String[] args) throws InterruptedException {
        int concurrentRequests = 20;
        ExecutorService pool = Executors.newFixedThreadPool(concurrentRequests);
        CountDownLatch latch = new CountDownLatch(concurrentRequests);

        for (int i = 0; i < concurrentRequests; i++) {
            pool.submit(() -> {
                getWithoutProtection("popular-key");
                latch.countDown();
            });
        }
        latch.await();
        pool.shutdown();

        System.out.println("[unprotected] " + concurrentRequests + " concurrent requests resulted in "
                + originCallCount.get() + " ACTUAL origin calls -- a full STAMPEDE");
    }
}
```

How to run: `java StampedeUnprotected.java`

`getWithoutProtection` has no coordination between concurrent callers at all — every one of the 20 threads independently calls `expensiveOriginCall`, and `originCallCount` ends up equal to the full concurrency level, demonstrating the stampede in its rawest, unmitigated form.

### Level 2 — Intermediate

```java
// File: SingleFlightBasic.java -- the SAME concurrent load, now
// PROTECTED with single-flight locking: only ONE thread actually performs
// the expensive computation; every OTHER concurrent caller for the SAME
// key waits and reuses that single result.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SingleFlightBasic {
    static AtomicInteger originCallCount = new AtomicInteger(0);
    static ConcurrentHashMap<String, CompletableFuture<String>> inFlightRequests = new ConcurrentHashMap<>();

    static String expensiveOriginCall() {
        originCallCount.incrementAndGet();
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return "computed-value";
    }

    static String getWithSingleFlight(String key) {
        CompletableFuture<String> future = inFlightRequests.computeIfAbsent(key, k ->
            CompletableFuture.supplyAsync(SingleFlightBasic::expensiveOriginCall)
        );
        try {
            return future.get(); // waits for the SHARED computation, whether it started it or not
        } catch (Exception e) {
            throw new RuntimeException(e);
        } finally {
            inFlightRequests.remove(key, future); // clean up once this specific computation is done
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int concurrentRequests = 20;
        ExecutorService pool = Executors.newFixedThreadPool(concurrentRequests);
        CountDownLatch latch = new CountDownLatch(concurrentRequests);

        for (int i = 0; i < concurrentRequests; i++) {
            pool.submit(() -> {
                getWithSingleFlight("popular-key");
                latch.countDown();
            });
        }
        latch.await();
        pool.shutdown();

        System.out.println("[single-flight] " + concurrentRequests + " concurrent requests resulted in "
                + originCallCount.get() + " ACTUAL origin call(s) -- stampede AVOIDED");
    }
}
```

How to run: `java SingleFlightBasic.java`

`inFlightRequests.computeIfAbsent` is the coordination point: only the *first* thread to reach it for a given key actually creates a new `CompletableFuture` running `expensiveOriginCall`; every subsequent concurrent thread for the same key finds the already-present future and simply calls `.get()` on it, blocking until the first thread's computation completes and reusing its exact result — `originCallCount` ends up at `1` regardless of how many concurrent callers there were.

### Level 3 — Advanced

```java
// File: SingleFlightWithFailureHandling.java -- the SAME single-flight
// coordination, now handling the PRODUCTION-FLAVORED hard case: the ONE
// thread actually performing the computation FAILS. Every WAITING thread
// must receive that failure too (not hang forever waiting on a future
// that will never complete successfully), and a SUBSEQUENT request after
// the failure must be allowed to RETRY rather than being permanently
// stuck behind a cached failure.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SingleFlightWithFailureHandling {
    static AtomicInteger originCallAttempts = new AtomicInteger(0);
    static ConcurrentHashMap<String, CompletableFuture<String>> inFlightRequests = new ConcurrentHashMap<>();

    // Fails on the FIRST attempt, succeeds on the SECOND -- simulates a transient origin failure.
    static String flakyOriginCall() {
        int attempt = originCallAttempts.incrementAndGet();
        try { Thread.sleep(30); } catch (InterruptedException ignored) {}
        if (attempt == 1) {
            throw new RuntimeException("origin call failed on attempt " + attempt);
        }
        return "computed-value (attempt " + attempt + ")";
    }

    static String getWithSingleFlight(String key, int callerNum) {
        CompletableFuture<String> future = inFlightRequests.computeIfAbsent(key, k ->
            CompletableFuture.supplyAsync(SingleFlightWithFailureHandling::flakyOriginCall)
        );
        try {
            String result = future.get();
            System.out.println("[caller " + callerNum + "] received: " + result);
            return result;
        } catch (Exception e) {
            System.out.println("[caller " + callerNum + "] received the SAME failure the computing thread hit: " + e.getCause().getMessage());
            return null;
        } finally {
            // CRITICAL: remove the future so a LATER request can retry, rather than being
            // permanently stuck behind a cached failed future forever.
            inFlightRequests.remove(key, future);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // First wave: 5 concurrent callers, all sharing the SAME in-flight (failing) computation.
        ExecutorService pool = Executors.newFixedThreadPool(5);
        CountDownLatch firstWaveLatch = new CountDownLatch(5);
        for (int i = 1; i <= 5; i++) {
            int callerNum = i;
            pool.submit(() -> { getWithSingleFlight("popular-key", callerNum); firstWaveLatch.countDown(); });
        }
        firstWaveLatch.await();
        pool.shutdown();

        System.out.println();
        System.out.println("--- second wave, AFTER the failure: a NEW request must be able to RETRY, not stay stuck ---");
        String retryResult = getWithSingleFlight("popular-key", 6);
        System.out.println("[caller 6, retry] final result: " + retryResult);
    }
}
```

How to run: `java SingleFlightWithFailureHandling.java`

`flakyOriginCall` deliberately throws on its first invocation. All five first-wave callers share the same `CompletableFuture`, so all five receive the identical failure via `future.get()` throwing an `ExecutionException` wrapping that `RuntimeException` — each caller's `catch` block reports the shared failure. The `finally` block's `inFlightRequests.remove(key, future)` runs for every caller, but critically, once the failed future is removed, the sixth caller's later request finds no in-flight entry at all and triggers a *fresh* `computeIfAbsent` call — this time `flakyOriginCall`'s second invocation succeeds, demonstrating that a failure doesn't permanently poison the key for all future requests.

## 6. Walkthrough

Trace `SingleFlightWithFailureHandling.main` in order. **First**, five threads are submitted, each calling `getWithSingleFlight("popular-key", callerNum)`. Whichever thread reaches `computeIfAbsent` first creates the shared `CompletableFuture`, running `flakyOriginCall` asynchronously; the other four find that same future already present and simply attach to it via `.get()`.

**Next**, `flakyOriginCall` runs exactly once for this whole wave (since `computeIfAbsent` guarantees single execution), and since this is `originCallAttempts`' first increment, `attempt == 1`, so it throws `RuntimeException("origin call failed on attempt 1")`.

**Then**, every one of the five waiting `future.get()` calls throws an `ExecutionException` wrapping that same original exception — each caller's own `catch` block runs independently, printing that it received the same shared failure, and each caller's `finally` block calls `inFlightRequests.remove(key, future)`.

**After that**, `remove(key, future)`'s two-argument form only actually removes the mapping if the currently-stored future still equals this specific `future` object — since all five callers are removing the *same* future instance for the same key, this operation is safely idempotent; after the first successful removal, subsequent calls find no matching entry left to remove, which causes no error since `remove` simply returns `false` in that case.

**Finally**, the second wave calls `getWithSingleFlight("popular-key", 6)` fresh. Since `inFlightRequests` no longer contains an entry for `"popular-key"` (it was removed after the failure), `computeIfAbsent` creates a brand-new `CompletableFuture`, running `flakyOriginCall` again — this time `originCallAttempts.incrementAndGet()` returns `2`, so the `if (attempt == 1)` check is `false`, and the call succeeds, returning `"computed-value (attempt 2)"`, which caller 6 receives successfully.

```
[caller 1] received the SAME failure the computing thread hit: origin call failed on attempt 1
[caller 2] received the SAME failure the computing thread hit: origin call failed on attempt 1
[caller 3] received the SAME failure the computing thread hit: origin call failed on attempt 1
[caller 4] received the SAME failure the computing thread hit: origin call failed on attempt 1
[caller 5] received the SAME failure the computing thread hit: origin call failed on attempt 1

--- second wave, AFTER the failure: a NEW request must be able to RETRY, not stay stuck ---
[caller 6] received: computed-value (attempt 2)
[caller 6, retry] final result: computed-value (attempt 2)
```

(Exact ordering of the first five "received" lines can vary, since all five callers complete their `catch` blocks concurrently — but all five always report the identical failure message, and caller 6 always succeeds on its independent retry.)

## 7. Gotchas & takeaways

> A single-flight implementation that forgets to remove the in-flight entry after a *failure* (only removing it after success) permanently poisons that key — every future request would keep attaching to the same, already-failed future forever, turning one transient failure into a permanent outage for that key. The `finally` block's unconditional cleanup, run regardless of success or failure, is what prevents this.
- Single-flight locking is the most precise stampede protection — exactly one origin call regardless of concurrency — but it does mean all waiting requests experience the *same* latency as the slowest path (the actual computation), rather than being served a possibly-stale value immediately.
- Stale-while-revalidate is a common complementary or alternative approach: serve the last known value immediately to every concurrent caller while exactly one background refresh runs, trading a small amount of extra staleness for zero added latency on the waiting requests.
- This pattern matters most for genuinely hot keys with expensive origin computations — the coordination overhead of `computeIfAbsent` and `CompletableFuture` isn't free, so applying it universally to every cache key, including cold ones, is unnecessary complexity for keys that were never going to stampede in the first place.
- Combine this with jittered TTLs on related keys (avoiding many keys expiring at the exact same instant) as a complementary defense — single-flight protects any one key from a stampede, but staggered expiry reduces how often many different keys' stampede-protection logic all fires at once, which matters for overall system load even with per-key protection in place.
