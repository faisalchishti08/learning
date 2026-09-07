---
card: system-design
gi: 134
slug: timeouts
title: Timeouts
---

## 1. What it is

A **timeout** is a maximum time a caller will wait for a response before giving up and treating the call as failed, instead of waiting indefinitely. Without a timeout, a single slow or hung dependency can hold a caller's thread (and any resource it holds, like a database connection) open forever, one caller at a time, until the caller itself runs out of resources.

## 2. Why & when

Networks and remote services can hang for far longer than any reasonable request should take — a dropped packet with no retransmit, a downstream service stuck in an infinite loop, a database lock held forever. Without a timeout, a caller waiting on such a call is stuck waiting forever too, and if this happens repeatedly (many callers all waiting on the same hung dependency), it can exhaust the caller's own thread pool or connection pool, turning one slow dependency into a total outage of the calling service. Set a timeout on every network call and every operation that could plausibly hang — this is one of the single most important reliability practices in any distributed system.

## 3. Core concept

- **Every remote call needs a timeout:** HTTP calls, database queries, message broker operations — anything that crosses a process or network boundary can hang, and needs an explicit maximum wait time.
- **Choosing a timeout value:** too short, and normal, slightly-slower-than-usual calls get needlessly cut off (a false failure); too long, and a genuinely hung call still ties up resources for a long time before giving up. A common approach is to set the timeout based on the dependency's own observed [tail latency](0126-tail-latency-percentiles-p50-p95-p99.md) (e.g. a bit above its p99), not just a guess.
- **Timeout triggers a clear failure, not a hang:** once the timeout fires, the caller gets a definite failure response immediately, freeing its thread and any held resources — this failure can then be handled by a [retry](0135-retries-with-exponential-backoff-jitter.md), a [fallback](0138-fallbacks-graceful-degradation.md), or surfaced to the end user.
- **Nested timeouts must be consistent:** if service A calls B, which calls C, A's overall timeout should be at least as long as B's timeout plus B's own processing time — otherwise A can give up and return an error to its caller while B is still legitimately waiting on C, wasting the work B and C are still doing.
- **Connection timeout vs read timeout:** a connection timeout bounds how long to wait to *establish* a connection; a read (or response) timeout bounds how long to wait for actual *data* once connected — both need to be set, since a hang can happen at either stage.

## 4. Diagram

```
WITHOUT A TIMEOUT:                    WITH A TIMEOUT:

  Caller -> call to Service B          Caller -> call to Service B
            (B is hung, never          set timeout = 2000ms
             responds)                          |
  Caller's thread WAITS...                      v
  ...WAITS...                          2000ms elapses, B still hasn't
  ...WAITS FOREVER                     responded -> timeout FIRES
  (thread never freed,                          |
   resource exhaustion                 Caller's thread is FREED IMMEDIATELY,
   under repeated calls)               gets a clear failure to handle
                                       (retry, fallback, or error to its own caller)
```
*Caption: without a timeout, a hung dependency holds a caller's resources indefinitely; a timeout guarantees the caller gets a definite answer, and its resources back, within a bounded time.*

## 5. Runnable example

**Level 1 — Basic.** Call a slow, simulated dependency with no timeout, and observe the caller blocked for its full duration.

**Level 2 — Add a timeout.** The same slow call now returns a bounded, definite failure instead of an unbounded wait.

**Level 3 — Nested timeout consistency.** Show why an outer timeout shorter than an inner timeout wastes the inner call's work.

```java
// Timeouts.java
import java.util.concurrent.*;

public class Timeouts {

    static String slowDependencyCall() throws InterruptedException {
        Thread.sleep(5000); // simulates a hung or very slow downstream dependency
        return "response from slow dependency";
    }

    public static void main(String[] args) throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();

        // Level 1 & 2: call the slow dependency WITH a timeout, instead of waiting unboundedly.
        Future<String> future = executor.submit(Timeouts::slowDependencyCall);
        long start = System.currentTimeMillis();
        try {
            String result = future.get(2000, TimeUnit.MILLISECONDS); // 2-second timeout
            System.out.println("got result: " + result);
        } catch (TimeoutException e) {
            long elapsed = System.currentTimeMillis() - start;
            System.out.println("call timed out after " + elapsed + "ms (bounded, NOT the full 5000ms) - caller is now free to react");
            future.cancel(true); // stop waiting on the underlying call
        }

        // Level 3: nested timeout inconsistency - outer timeout shorter than inner call's own timeout.
        int serviceBOwnTimeoutMs = 3000; // B's own configured timeout for calling C
        int serviceAOverallTimeoutMs = 1000; // A gives up on the WHOLE chain after only 1000ms

        System.out.println("--- nested call chain: A -> B -> C ---");
        System.out.println("service B's own timeout when calling C: " + serviceBOwnTimeoutMs + "ms");
        System.out.println("service A's overall timeout for the whole call to B: " + serviceAOverallTimeoutMs + "ms");
        if (serviceAOverallTimeoutMs < serviceBOwnTimeoutMs) {
            System.out.println("MISCONFIGURED: A gives up at " + serviceAOverallTimeoutMs
                + "ms while B may still be legitimately waiting on C for up to " + serviceBOwnTimeoutMs + "ms");
            System.out.println("-> B (and C) continue doing work for a request A has already abandoned - wasted resources");
        }

        executor.shutdownNow();
    }
}
```

**How to run:** save as `Timeouts.java`, then run `java Timeouts.java`.

## 6. Walkthrough

1. `slowDependencyCall` sleeps for `5000ms`, modeling a dependency that takes far longer than a reasonable request should.
2. `future.get(2000, TimeUnit.MILLISECONDS)` bounds how long the caller will wait for that result; because the actual call takes 5 seconds but the timeout is only 2, a `TimeoutException` is thrown well before the underlying call ever finishes.
3. The caught exception's handler prints the actual elapsed time (about 2000ms, not 5000ms), demonstrating that the caller was freed at the timeout boundary, not at the point the slow call would have eventually finished.
4. `future.cancel(true)` then signals the underlying task to stop, so the caller's resources are not tied up any longer than necessary waiting for a result it has already given up on.
5. Level 3 lays out a concrete nested-timeout mismatch: service A's `1000ms` overall timeout is shorter than service B's own `3000ms` timeout for its call to C. The code detects `serviceAOverallTimeoutMs < serviceBOwnTimeoutMs` and prints the consequence directly: A abandons the request and reports failure to its own caller, while B and C may still be doing real work on a request nobody is waiting for anymore — a common, wasteful misconfiguration in real multi-service call chains.

## 7. Gotchas & takeaways

> Gotcha: setting a timeout without also handling the resulting failure (via a retry, a fallback, or a clear error surfaced to the user) just converts "hangs forever" into "fails frequently" — a timeout alone is only half the fix. Pair every timeout with an explicit plan for what to do when it fires.

- Every network call or operation that can hang needs an explicit timeout, or a single slow dependency can exhaust a caller's resources by holding them indefinitely.
- Timeout values should be chosen based on the dependency's real observed latency (ideally its tail latency), balancing false failures on the slow end against wasted waiting on the hung end.
- Nested calls need consistent timeout budgets — an outer timeout shorter than an inner call's own timeout wastes the inner call's work on a request the outer caller has already abandoned.
- Related concepts: [Retries with exponential backoff & jitter](0135-retries-with-exponential-backoff-jitter.md) (the typical response to a timeout firing), [Circuit breaker](0136-circuit-breaker.md) (stops calling a dependency altogether once its timeouts become frequent), [Tail latency & percentiles (p50/p95/p99)](0126-tail-latency-percentiles-p50-p95-p99.md) (informs a sensible timeout value).
