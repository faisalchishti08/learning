---
card: microservices
gi: 280
slug: timeout-pattern-timelimiter
title: "Timeout pattern (TimeLimiter)"
---

## 1. What it is

The timeout pattern bounds how long a caller will wait for a remote call to complete before giving up and treating it as a failure, instead of waiting indefinitely. Resilience4j's `TimeLimiter` is a dedicated module implementing this for asynchronous calls: it wraps a `CompletableFuture` (or similar) and cancels/fails it with a `TimeoutException` if it hasn't completed within a configured duration, regardless of whether the underlying call is still silently running.

## 2. Why & when

Without a timeout, a caller waiting on a slow or hung downstream dependency ties up its own resources (a thread, a connection, memory for the pending request) for as long as that dependency takes — which, for a truly hung dependency, can be forever. Under load, many such indefinitely-waiting calls exhaust the caller's own thread pool or connection pool, so the caller itself becomes unresponsive even though the actual bug is entirely in the downstream dependency. This is a classic way partial failure in a distributed system cascades into total failure of an otherwise-healthy caller.

A timeout converts "waiting forever" into "waiting a bounded, known amount of time, then failing predictably." That predictable failure can then be handled — retried, sent to a fallback, or surfaced as an error — using the other resilience patterns like [retry](0259-retry-pattern.md), [circuit breaker](0250-circuit-breaker-pattern.md), or [fallback methods](0282-fallback-methods-default-responses.md). Use a timeout on every outbound network call in a distributed system without exception; the only question is what duration is appropriate for that specific call.

## 3. Core concept

A `TimeLimiter` races the actual call against a timer: whichever finishes first determines the outcome. If the call finishes first, its result (success or failure) is returned normally. If the timer fires first, the caller receives a `TimeoutException` and, ideally, the underlying call is cancelled so it stops consuming resources.

```java
import io.github.resilience4j.timelimiter.TimeLimiter;
import io.github.resilience4j.timelimiter.TimeLimiterConfig;
import java.time.Duration;
import java.util.concurrent.*;

TimeLimiterConfig config = TimeLimiterConfig.custom()
    .timeoutDuration(Duration.ofSeconds(2)) // MAXIMUM wait before giving up
    .cancelRunningFuture(true)               // attempt to CANCEL the underlying work on timeout
    .build();
TimeLimiter timeLimiter = TimeLimiter.of(config);

ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
Callable<CompletionStage<String>> supplier = () -> callDownstreamAsync(); // returns a CompletableFuture
Callable<String> decorated = TimeLimiter.decorateFutureSupplier(timeLimiter, supplier);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timer and the actual downstream call race against each other; if the call completes first its result is returned, but if the timer fires first the caller receives a timeout exception and the underlying call is cancelled rather than left running">
  <rect x="30" y="30" width="180" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">downstream call (unknown duration)</text>

  <rect x="30" y="100" width="180" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="124" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">timer (fixed 2s)</text>

  <text x="260" y="55" fill="#8b949e" font-size="8" font-family="sans-serif">race</text>
  <line x1="212" y1="50" x2="320" y2="80" stroke="#8b949e" marker-end="url(#arr280)"/>
  <line x1="212" y1="120" x2="320" y2="90" stroke="#8b949e" marker-end="url(#arr280)"/>

  <rect x="330" y="70" width="160" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="410" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">whichever finishes FIRST wins</text>

  <text x="410" y="140" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">call wins &#8594; real result | timer wins &#8594; TimeoutException + cancel</text>
</svg>

The call and the timer race; the timer winning produces a bounded, predictable TimeoutException instead of an unbounded wait.

## 5. Runnable example

Scenario: a plain synchronous call with no timeout that can block indefinitely, extended with `Future.get(timeout)` to bound the wait, and finally using Resilience4j's `TimeLimiter` with cancellation and combined with a fallback, matching production usage.

### Level 1 — Basic

```java
// File: NoTimeoutBlocksForever.java -- calling a slow/hung dependency
// with NO timeout ties up the caller's thread for as long as it takes.
import java.util.concurrent.*;

public class NoTimeoutBlocksForever {
    static String slowDownstreamCall() throws InterruptedException {
        Thread.sleep(5000); // simulates a hung/slow dependency
        return "result";
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        System.out.println("Calling downstream with NO timeout...");
        String result = slowDownstreamCall(); // blocks for the FULL 5 seconds, no matter what
        System.out.println("Got result: " + result + " after " + (System.currentTimeMillis() - start) + "ms");
    }
}
```

How to run: `java NoTimeoutBlocksForever.java`

The caller invokes `slowDownstreamCall()` directly and simply waits — the call takes 5 seconds and the caller's thread is blocked for the entire duration, no matter how long that turns out to be. If the downstream dependency were actually hung indefinitely rather than just slow, this call would never return, and the calling thread would be lost forever.

### Level 2 — Intermediate

```java
// File: FutureWithTimeout.java -- run the same slow call on a separate
// thread via a Future, and bound the wait using Future.get(timeout),
// giving up with a TimeoutException instead of blocking indefinitely.
import java.util.concurrent.*;

public class FutureWithTimeout {
    static String slowDownstreamCall() throws InterruptedException {
        Thread.sleep(5000);
        return "result";
    }

    public static void main(String[] args) throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<String> future = executor.submit(FutureWithTimeout::slowDownstreamCall);

        long start = System.currentTimeMillis();
        try {
            String result = future.get(2, TimeUnit.SECONDS); // BOUNDED wait, 2s max
            System.out.println("Got result: " + result);
        } catch (TimeoutException e) {
            System.out.println("TIMED OUT after " + (System.currentTimeMillis() - start)
                    + "ms -- gave up waiting instead of blocking for the full 5s");
            future.cancel(true); // attempt to interrupt the still-running call
        } finally {
            executor.shutdownNow();
        }
    }
}
```

How to run: `java FutureWithTimeout.java`

The same 5-second slow call now runs on a background thread via `ExecutorService.submit`, returning a `Future`. The main thread calls `future.get(2, TimeUnit.SECONDS)`, which bounds the wait to 2 seconds. Because the call takes 5 seconds, `get` throws a `TimeoutException` after 2 seconds — the caller gives up on a fixed, predictable schedule instead of waiting the full 5, and calls `future.cancel(true)` to attempt to interrupt the still-running background task.

### Level 3 — Advanced

```java
// File: TimeLimiterWithFallback.java -- Resilience4j's TimeLimiter over
// an async call, decorated with automatic cancellation on timeout and
// combined with a fallback so the caller gets a usable degraded result
// instead of a raw exception. (Needs resilience4j-timelimiter on the classpath.)
import io.github.resilience4j.timelimiter.TimeLimiter;
import io.github.resilience4j.timelimiter.TimeLimiterConfig;
import java.time.Duration;
import java.util.concurrent.*;

public class TimeLimiterWithFallback {
    static CompletableFuture<String> slowDownstreamCallAsync(ScheduledExecutorService scheduler) {
        CompletableFuture<String> future = new CompletableFuture<>();
        scheduler.schedule(() -> future.complete("real result"), 5, TimeUnit.SECONDS); // simulates a slow dependency
        return future;
    }

    static String withFallback(Callable<String> decorated) {
        try {
            return decorated.call();
        } catch (TimeoutException e) {
            return "DEGRADED: showing cached/default data because downstream timed out";
        } catch (Exception e) {
            return "DEGRADED: unexpected error, falling back";
        }
    }

    public static void main(String[] args) throws Exception {
        TimeLimiterConfig config = TimeLimiterConfig.custom()
                .timeoutDuration(Duration.ofSeconds(2))
                .cancelRunningFuture(true)
                .build();
        TimeLimiter timeLimiter = TimeLimiter.of(config);
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

        Callable<CompletionStage<String>> supplier = () -> slowDownstreamCallAsync(scheduler);
        Callable<String> decorated = TimeLimiter.decorateFutureSupplier(timeLimiter, supplier);

        long start = System.currentTimeMillis();
        String result = withFallback(decorated);
        System.out.println("Result: " + result + " (after " + (System.currentTimeMillis() - start) + "ms)");
        scheduler.shutdown();
    }
}
```

How to run: `java -cp .:resilience4j-timelimiter-2.2.0.jar:resilience4j-core-2.2.0.jar TimeLimiterWithFallback.java` (with the Resilience4j TimeLimiter jars on the classpath; in a Spring Boot project this is normally pulled in via `spring-cloud-starter-circuitbreaker-resilience4j` and configured declaratively).

The downstream call is scheduled to complete after 5 seconds, but the `TimeLimiter` is configured with a 2-second `timeoutDuration` and `cancelRunningFuture(true)`. Calling `decorated.call()` starts the async call and races it against the 2-second timer; since the call takes longer, the `TimeLimiter` throws a `TimeoutException` at the 2-second mark and, because `cancelRunningFuture` is enabled, attempts to cancel the underlying `CompletableFuture` so the "wasted" work is abandoned rather than silently completing later and being ignored. The `withFallback` wrapper catches that `TimeoutException` and returns a degraded-but-usable result instead of propagating a raw exception to the end user — this is the production pattern: timeout bounds the wait, and a fallback turns the resulting failure into a graceful degradation.

## 6. Walkthrough

Trace `TimeLimiterWithFallback.main` in order. **First**, a `TimeLimiterConfig` is built with a 2-second timeout and cancellation enabled, and a `TimeLimiter` is constructed from it.

**Next**, `supplier` is defined as a `Callable` that, when invoked, calls `slowDownstreamCallAsync(scheduler)` — this schedules a task to complete the future 5 seconds later and returns the (not-yet-complete) `CompletableFuture` immediately. `TimeLimiter.decorateFutureSupplier` wraps this into `decorated`, a synchronous `Callable<String>` that internally manages the race between the future and the timer.

**`withFallback(decorated)` is called**, which calls `decorated.call()` inside a try block. This is where the race actually happens: internally, the `TimeLimiter` invokes `supplier.call()` to kick off the async call (starting the 5-second scheduled completion), then waits up to 2 seconds for that future to complete.

**At the 2-second mark**, the future still has not completed (it needs 5 seconds total), so the `TimeLimiter` throws a `TimeoutException` from `decorated.call()`. Because `cancelRunningFuture(true)` was set, it also calls `cancel()` on the underlying future — if the downstream call supported real cancellation (e.g., an HTTP client that aborts the socket), this would stop the wasted work; here it just marks the future as cancelled so its eventual completion 3 seconds later is a no-op.

**Back in `withFallback`**, the `catch (TimeoutException e)` block catches this and returns the degraded string `"DEGRADED: showing cached/default data..."` instead of letting the exception propagate further up.

**Finally**, `main` prints the result and the elapsed time, which comes out around 2000ms — bounded by the configured timeout, not the call's actual 5-second duration.

```
supplier.call() starts async work (needs 5s)
        |
        |<---- race ---->|
        |                |
   [future completes]  [2s timer fires FIRST]
        |                |
     (never reached    TimeoutException -> cancel() -> withFallback() -> "DEGRADED: ..." returned to caller
      in this run)
```

Conceptually, this is a "request/response" even though it's in-process: the "request" is the call to `withFallback(decorated)`, and the "response" — after roughly 2000ms instead of 5000ms — is the string `"DEGRADED: showing cached/default data because downstream timed out"`.

## 7. Gotchas & takeaways

> A timeout without cancellation just stops *waiting* — the underlying call may keep running in the background, consuming resources (a thread, a connection, CPU) that never get freed until it eventually finishes on its own. Always pair a timeout with cancellation of the underlying work wherever the client library supports it.

- Every outbound network call needs a timeout; the timeout should be tuned per call based on the callee's expected latency (a fast cache lookup and a slow batch report generator need very different timeouts).
- `TimeLimiter` in Resilience4j is designed for asynchronous calls (`CompletableFuture`); pair it with `cancelRunningFuture(true)` so timed-out work is actually abandoned, not left running.
- A timeout produces a predictable failure — pair it with a [fallback](0282-fallback-methods-default-responses.md) or [retry](0259-retry-pattern.md) so that predictable failure turns into a good user experience rather than just a faster error.
- Setting a timeout too aggressively causes false-positive failures under normal, brief load spikes; setting it too loosely defeats the purpose — base the value on measured p99 latency of the actual dependency, not a guess.
