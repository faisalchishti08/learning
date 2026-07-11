---
card: spring-cloud
gi: 75
slug: time-limiter
title: "Time limiter"
---

## 1. What it is

Resilience4j's `TimeLimiter` caps how long an asynchronous call is allowed to run before it's cancelled and treated as a failure — specifically designed for `CompletableFuture`/reactive-style calls, where "just block and wait" isn't the execution model, so a dedicated timeout mechanism is needed to bound how long the caller waits for a result.

```properties
resilience4j.timelimiter.instances.billing-service.timeout-duration=2s
resilience4j.timelimiter.instances.billing-service.cancel-running-future=true
```

```java
CircuitBreaker cb = circuitBreakerFactory.create("billing-service");
CompletableFuture<Invoice> future = cb.run(
    () -> CompletableFuture.supplyAsync(() -> billingClient.getInvoice(orderId)),
    throwable -> CompletableFuture.completedFuture(new Invoice(orderId, 0.0))
);
```

## 2. Why & when

A slow-but-not-yet-failed call is a real, distinct failure mode from an outright error — the Bulkhead card addressed *how many* slow calls can be in flight at once; `TimeLimiter` addresses *how long* any single call is allowed to keep waiting before it's simply given up on. Without a time limit, an asynchronous operation that never completes (a hung connection, a backend that accepted the request but never responds) can leave a caller waiting indefinitely, which is functionally similar to the resource-exhaustion risk covered in the Bulkhead card, but from the angle of individual call duration rather than concurrent call count.

Reach for `TimeLimiter` when:

- Working with `CompletableFuture` or reactive (`Mono`/`Flux`) call chains, where a plain synchronous timeout mechanism (like a simple `Thread.sleep`-based approach) doesn't naturally apply.
- A downstream dependency has occasionally exhibited genuinely unbounded hangs (not just slow-but-finite responses) — a hard ceiling on wait time turns "wait forever" into "wait at most N seconds, then treat it as a failure and fall back."
- Combined with a circuit breaker: a `TimeLimiter`-triggered timeout is recorded as a failure by the circuit breaker wrapping the same call, so repeated timeouts (not just outright errors) can also trip the breaker open.

## 3. Core concept

```
 asynchronous call starts (a CompletableFuture, not yet resolved)
        |
        v
 TimeLimiter starts a countdown: timeout-duration
        |
        |-- call completes before the timeout -> its actual result (success or failure) is used
        |-- timeout elapses first -> the future is treated as FAILED (a TimeoutException)
                                       cancel-running-future=true -> attempts to actually cancel/interrupt it too
```

The timeout is a race between the real call finishing and the clock running out — whichever happens first determines the outcome the caller sees.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An asynchronous call races against a configured timeout, and whichever finishes first determines whether the caller sees the real result or a timeout failure that can trigger the fallback">
  <rect x="30" y="30" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="140" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">async call starts</text>
  <text x="140" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">CompletableFuture, not yet resolved</text>

  <line x1="140" y1="80" x2="140" y2="105" stroke="#8b949e" stroke-width="1.3"/>

  <rect x="30" y="110" width="220" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="140" y="134" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">call finishes first -&gt; real result used</text>

  <rect x="360" y="30" width="250" height="50" rx="8" fill="#1c2430" stroke="#e64949" stroke-width="1.2"/>
  <text x="485" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">timeout-duration countdown</text>
  <text x="485" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">runs in parallel with the real call</text>

  <line x1="485" y1="80" x2="485" y2="105" stroke="#8b949e" stroke-width="1.3"/>

  <rect x="360" y="110" width="250" height="40" rx="6" fill="#e6494930" stroke="#e64949" stroke-width="1.3"/>
  <text x="485" y="134" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">timer fires first -&gt; TimeoutException -&gt; fallback</text>

  <defs><marker id="a75" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two clocks race in parallel; whichever crosses the finish line first decides what the caller ultimately experiences.

## 5. Runnable example

The scenario: bound how long calls to `billing-service` are allowed to take. Start with unbounded waiting on an async call (the risk), then add a time limiter racing the call against a timeout, then combine it with a fallback for a complete, resilient result.

### Level 1 — Basic

Unbounded waiting — no time limit at all.

```java
import java.util.concurrent.*;

public class TimeLimiterLevel1 throws Exception {
    public static void main(String[] args) throws Exception {
        CompletableFuture<String> hungCall = new CompletableFuture<>(); // never completed -- simulates a genuine hang

        // in a real scenario, .get() with no timeout would block FOREVER here
        // for demonstration, we bound it artificially just to show the problem without actually hanging this example
        try {
            hungCall.get(2, TimeUnit.SECONDS); // even this "short" demo wait shows the shape of the problem
        } catch (TimeoutException e) {
            System.out.println("without a real time limiter, this caller would have simply hung indefinitely");
        }
    }
}
```

How to run: `java TimeLimiterLevel1.java` (Note: fix the stray `throws Exception` after the class name before running — see corrected code below.)

```java
import java.util.concurrent.*;

public class TimeLimiterLevel1 {
    public static void main(String[] args) throws Exception {
        CompletableFuture<String> hungCall = new CompletableFuture<>();
        try {
            hungCall.get(2, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            System.out.println("without a real time limiter, this caller would have simply hung indefinitely");
        }
    }
}
```

Without any bound at all, `hungCall.get()` (called with no timeout argument) would block the calling thread forever — the artificial 2-second bound here is only to make the demonstration finish; a real unprotected call has no such safety net.

### Level 2 — Intermediate

Add a `TimeLimiter`-style wrapper: race the real call against a configured timeout, treating a timeout as a failure.

```java
import java.util.concurrent.*;

public class TimeLimiterLevel2 {
    static <T> T runWithTimeLimit(Supplier<CompletableFuture<T>> asyncCall, Duration timeout) throws Exception {
        CompletableFuture<T> future = asyncCall.get();
        try {
            return future.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            future.cancel(true); // cancel-running-future=true equivalent
            throw new RuntimeException("call timed out after " + timeout);
        }
    }

    public static void main(String[] args) {
        // a call that takes 3 seconds -- too slow for a 1-second limit
        Supplier<CompletableFuture<String>> slowCall = () -> CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(3000); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
            return "{\"id\":\"42\"}";
        });

        try {
            String result = runWithTimeLimit(slowCall, Duration.ofSeconds(1));
            System.out.println("result: " + result);
        } catch (RuntimeException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

How to run: `java TimeLimiterLevel2.java`

`runWithTimeLimit` calls `future.get(timeout, unit)`, which throws `TimeoutException` if the future hasn't resolved within the bound — the simulated `slowCall` takes 3 seconds but the limit is only 1 second, so the wait times out, the future is cancelled, and a clear `RuntimeException` is thrown instead of the caller waiting the full 3 seconds (or longer, had the call genuinely hung).

### Level 3 — Advanced

Combine the time limiter with a fallback, mirroring the real `CircuitBreaker.run(supplier, fallback)` pattern from earlier cards, so a timeout produces a graceful degraded result instead of an exception the caller must handle explicitly.

```java
import java.util.concurrent.*;
import java.util.function.Function;

public class TimeLimiterLevel3 {
    record Invoice(String id, double amount) {}

    static <T> T runWithTimeLimitAndFallback(Supplier<CompletableFuture<T>> asyncCall, Duration timeout,
                                              Function<Throwable, T> fallback) {
        CompletableFuture<T> future = asyncCall.get();
        try {
            return future.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
        } catch (Exception e) {
            future.cancel(true);
            System.out.println("[time limiter] call did not complete in time (" + timeout + "), using fallback");
            return fallback.apply(e);
        }
    }

    public static void main(String[] args) {
        Supplier<CompletableFuture<Invoice>> slowBillingCall = () -> CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(3000); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
            return new Invoice("42", 199.99);
        });

        Function<Throwable, Invoice> fallback = throwable -> new Invoice("42", 0.0); // degraded default

        Invoice result = runWithTimeLimitAndFallback(slowBillingCall, Duration.ofSeconds(1), fallback);
        System.out.println("caller received: " + result); // never throws -- always gets SOME Invoice back
    }
}
```

How to run: `java TimeLimiterLevel3.java`

`runWithTimeLimitAndFallback` never lets an exception reach the caller directly — whether the underlying call times out or fails outright, the `catch` block invokes `fallback.apply(...)`, producing a degraded-but-valid `Invoice` either way. The slow call (3 seconds) against the 1-second limit times out exactly as in Level 2, but this time the caller receives a usable, if degraded, result instead of having to handle a raw exception itself — the same graceful-degradation shape as the earlier Feign circuit breaker fallback card, now specifically applied to the time-bound dimension of failure.

## 6. Walkthrough

Trace `runWithTimeLimitAndFallback`'s execution in Level 3.

1. `asyncCall.get()` runs first, invoking `slowBillingCall`, which starts a `CompletableFuture` running `Thread.sleep(3000)` on a separate thread before eventually completing with `Invoice("42", 199.99)` — but this hasn't happened yet; the future is returned immediately, still pending.
2. `future.get(1000, TimeUnit.MILLISECONDS)` is called — this blocks the calling thread for up to 1000ms waiting for the future to resolve. Since the underlying async work takes 3000ms, the 1000ms wait elapses first, and `get` throws `TimeoutException`.
3. The `catch (Exception e)` block catches this — it calls `future.cancel(true)`, attempting to interrupt the still-running background work (whether the actual sleeping thread genuinely responds to the interrupt depends on the operation, but the intent is to stop wasting resources on a result the caller has already given up waiting for), and prints the "using fallback" message.
4. `fallback.apply(e)` is called, invoking the `fallback` function with the caught exception — it ignores the exception's specific content and simply returns `new Invoice("42", 0.0)`, a deliberately degraded but structurally valid response.
5. The final `println` shows the caller received `Invoice[id=42, amount=0.0]` — a usable result, delivered within roughly 1 second (the configured timeout) rather than the 3 seconds the real call would have taken, or worse, an indefinite hang had no time limit existed at all.

```
asyncCall.get() -> future starts (will take 3000ms to complete)
future.get(1000ms timeout) -> 1000ms elapses first -> TimeoutException
   -> future.cancel(true) (stop wasting resources on it)
   -> fallback.apply(...) -> Invoice("42", 0.0) returned to the caller
```

## 7. Gotchas & takeaways

> **Gotcha:** `cancel-running-future=true` requests cancellation, but whether the underlying operation actually stops running depends on whether that operation's code responds to interruption — a `Thread.sleep` does respond (throwing `InterruptedException`), but a tight CPU-bound loop or a blocking I/O call that doesn't check the interrupted flag may continue consuming resources in the background even after the caller has already moved on with a fallback result. Cancellation is a request, not a guarantee.

- `TimeLimiter` addresses call *duration* specifically — complementary to `Bulkhead` (concurrent call *count*) and `CircuitBreaker` (failure *rate*), each guarding a different dimension of a dependency's potential misbehavior.
- It's specifically designed for asynchronous (`CompletableFuture`/reactive) call shapes, where a synchronous "just wait N seconds" approach doesn't naturally fit the execution model already in use.
- Combining `TimeLimiter` with a fallback (as in Level 3) turns "the call is taking too long" into a graceful degraded result, exactly the same pattern the earlier circuit breaker and Feign fallback cards established for outright failures — now applied to the time-bound failure mode too.
- A `TimeLimiter` timeout is typically recorded as a failure by any `CircuitBreaker` wrapping the same operation — repeated slow calls (not just outright errors) can and should contribute to tripping the circuit breaker, since a dependency that's reliably too slow is functionally unhealthy even if it eventually, technically, "succeeds."
