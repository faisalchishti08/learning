---
card: spring-cloud
gi: 74
slug: retry
title: "Retry"
---

## 1. What it is

Resilience4j's `Retry` module re-attempts a failed call a configurable number of times, with a configurable wait duration (optionally exponential backoff) between attempts, and optional per-exception-type filtering — a more general, standalone version of the retry behavior seen woven into the Gateway `Retry` filter and LoadBalancer's same/next-instance retry earlier in this run, usable to wrap *any* operation, not just HTTP calls.

```properties
resilience4j.retry.instances.billing-service.max-attempts=3
resilience4j.retry.instances.billing-service.wait-duration=200ms
resilience4j.retry.instances.billing-service.enable-exponential-backoff=true
resilience4j.retry.instances.billing-service.exponential-backoff-multiplier=2
resilience4j.retry.instances.billing-service.retry-exceptions=java.io.IOException
resilience4j.retry.instances.billing-service.ignore-exceptions=com.example.InvoiceNotFoundException
```

## 2. Why & when

The earlier Gateway and LoadBalancer retry cards were retry *applied specifically to HTTP calls* in those particular contexts; Resilience4j's `Retry` is the general-purpose building block usable to wrap any operation with transient-failure characteristics — a database call, a message queue publish, a call to a non-Feign, non-`@LoadBalanced` client, or any other operation where "try again after a brief pause" is a reasonable response to a specific kind of failure.

Reach for Resilience4j `Retry` directly when:

- Protecting an operation that isn't already covered by Gateway's `Retry` filter or LoadBalancer's built-in retry — the same "arbitrary code, not just HTTP calls" motivation as the earlier `CircuitBreakerFactory` card.
- Fine-grained exception filtering is needed — `retry-exceptions`/`ignore-exceptions` distinguish genuinely transient failures (network timeouts, connection resets) worth retrying from permanent ones (validation errors, not-found errors) that retrying would never fix.
- Exponential backoff specifically is wanted — spacing retries progressively further apart, reducing the risk that retries themselves pile onto an already-struggling dependency (the same concern raised in the earlier Gateway `Retry` card).

## 3. Core concept

```
 max-attempts: 3, wait-duration: 200ms, exponential-backoff-multiplier: 2

 attempt 1 -> fails (retryable exception) -> wait 200ms
 attempt 2 -> fails (retryable exception) -> wait 400ms (200 * 2)
 attempt 3 -> succeeds, OR fails and max-attempts is exhausted -> propagate the final exception

 retry-exceptions / ignore-exceptions:
   only exceptions matching retry-exceptions (or NOT matching ignore-exceptions) trigger a retry at all
   everything else propagates immediately on the first failure, no retry attempted
```

The exception-type filter decides *whether* to retry at all; the attempt count and backoff decide *how* the retries themselves are paced.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A retryable exception triggers a wait that grows with each attempt via exponential backoff, while a non retryable exception propagates immediately on the first failure without any retry at all">
  <rect x="20" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">retryable exception (e.g. IOException)</text>
  <text x="165" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 1 (fail) -&gt; wait 200ms</text>
  <text x="165" y="76" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 2 (fail) -&gt; wait 400ms -&gt; attempt 3</text>

  <rect x="330" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#e64949" stroke-width="1.5"/>
  <text x="475" y="42" fill="#e64949" font-size="8" text-anchor="middle" font-family="sans-serif">non-retryable exception (e.g. NotFound)</text>
  <text x="475" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 1 (fail) -&gt; propagate IMMEDIATELY</text>
  <text x="475" y="76" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">no further attempts, no waiting at all</text>

  <defs><marker id="a74" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Which exception type occurred entirely decides whether the retry machinery engages at all — a business-logic failure never gets retried just because a retry policy exists.

## 5. Runnable example

The scenario: retry calls to `billing-service` intelligently based on exception type. Start with blind retry-everything (the wrong approach for non-transient failures), then add exception-type filtering, then add exponential backoff timing.

### Level 1 — Basic

Blind retry — every failure gets retried, regardless of whether retrying could ever help.

```java
import java.util.function.Supplier;

public class ResilienceRetryLevel1 {
    static class InvoiceNotFoundException extends RuntimeException {
        InvoiceNotFoundException() { super("invoice not found"); }
    }

    static String callWithBlindRetry(Supplier<String> operation, int maxAttempts) {
        RuntimeException last = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return operation.get();
            } catch (RuntimeException e) {
                System.out.println("attempt " + attempt + " failed: " + e.getMessage() + " -- retrying regardless");
                last = e;
            }
        }
        throw last;
    }

    public static void main(String[] args) {
        Supplier<String> alwaysNotFound = () -> { throw new InvoiceNotFoundException(); };

        try {
            callWithBlindRetry(alwaysNotFound, 3);
        } catch (InvoiceNotFoundException e) {
            System.out.println("gave up after 3 pointless attempts: " + e.getMessage());
        }
    }
}
```

How to run: `java ResilienceRetryLevel1.java`

`InvoiceNotFoundException` means the invoice genuinely doesn't exist — retrying three times against the exact same non-existent resource wastes three round-trips for a result that was never going to change, exactly the failure mode intelligent exception filtering avoids.

### Level 2 — Intermediate

Add exception-type filtering: only retry exceptions that are plausibly transient, propagate everything else immediately.

```java
import java.util.*;
import java.util.function.Supplier;

public class ResilienceRetryLevel2 {
    static class InvoiceNotFoundException extends RuntimeException { InvoiceNotFoundException() { super("invoice not found"); } }
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }

    static Set<Class<? extends RuntimeException>> retryableExceptions = Set.of(TransientNetworkException.class);

    static String callWithFilteredRetry(Supplier<String> operation, int maxAttempts) {
        RuntimeException last = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return operation.get();
            } catch (RuntimeException e) {
                if (!retryableExceptions.contains(e.getClass())) {
                    System.out.println("non-retryable exception (" + e.getClass().getSimpleName() + ") -- propagating immediately");
                    throw e; // don't even count this as a retry attempt -- fail fast
                }
                System.out.println("attempt " + attempt + " failed with retryable exception, retrying");
                last = e;
            }
        }
        throw last;
    }

    public static void main(String[] args) {
        try {
            callWithFilteredRetry(() -> { throw new InvoiceNotFoundException(); }, 3);
        } catch (InvoiceNotFoundException e) {
            System.out.println("failed immediately, no wasted retries: " + e.getMessage());
        }
    }
}
```

How to run: `java ResilienceRetryLevel2.java`

`callWithFilteredRetry` checks `retryableExceptions.contains(e.getClass())` before retrying at all — since `InvoiceNotFoundException` isn't in that set, it propagates on the very first attempt, with no wasted retry attempts against a failure mode retrying could never fix.

### Level 3 — Advanced

Add exponential backoff, and simulate a genuinely transient failure that succeeds on a later attempt, showing the full combination of filtering plus properly-paced retries.

```java
import java.util.*;
import java.util.function.Supplier;

public class ResilienceRetryLevel3 {
    static class InvoiceNotFoundException extends RuntimeException { InvoiceNotFoundException() { super("invoice not found"); } }
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }

    static Set<Class<? extends RuntimeException>> retryableExceptions = Set.of(TransientNetworkException.class);

    static String callWithBackoffRetry(Supplier<String> operation, int maxAttempts,
                                        long baseWaitMs, double multiplier) {
        RuntimeException last = null;
        long wait = baseWaitMs;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return operation.get();
            } catch (RuntimeException e) {
                if (!retryableExceptions.contains(e.getClass())) throw e;
                last = e;
                if (attempt < maxAttempts) {
                    System.out.println("attempt " + attempt + " failed (" + e.getMessage() + "), waiting " + wait + "ms before retry");
                    wait = (long) (wait * multiplier); // exponential backoff -- grows with each retry
                }
            }
        }
        throw last;
    }

    public static void main(String[] args) {
        int[] callCount = {0};
        Supplier<String> flakyThenSucceeds = () -> {
            callCount[0]++;
            if (callCount[0] < 3) throw new TransientNetworkException();
            return "{\"id\":\"42\",\"amount\":199.99}";
        };

        String result = callWithBackoffRetry(flakyThenSucceeds, 5, 100, 2.0);
        System.out.println("final result: " + result);
    }
}
```

How to run: `java ResilienceRetryLevel3.java`

`callWithBackoffRetry` doubles `wait` after each retryable failure (`100ms`, then `200ms`, and so on if needed) — the simulated `flakyThenSucceeds` operation fails its first two calls with the retryable `TransientNetworkException`, and succeeds on the third, so the retry loop absorbs both failures (waiting progressively longer between each) and ultimately returns the successful response, with the caller never seeing either intermediate failure directly.

## 6. Walkthrough

Trace `callWithBackoffRetry`'s execution in Level 3.

1. `attempt=1` runs first — `operation.get()` invokes `flakyThenSucceeds`, incrementing `callCount` to `1`. Since `1 < 3`, it throws `TransientNetworkException`. The `catch` block checks `retryableExceptions.contains(TransientNetworkException.class)`, which is `true`, so it doesn't re-throw. Since `attempt (1) < maxAttempts (5)`, it prints the wait message showing `wait=100`, then doubles `wait` to `200`.
2. `attempt=2` runs — `callCount` becomes `2`, still `< 3`, so another `TransientNetworkException` is thrown. Again retryable, again `attempt (2) < maxAttempts (5)`, so it prints the wait message showing `wait=200` this time, and doubles `wait` again to `400`.
3. `attempt=3` runs — `callCount` becomes `3`, no longer `< 3`, so `flakyThenSucceeds` returns the successful JSON string instead of throwing. `callWithBackoffRetry` returns this value immediately from within the `try` block, without reaching the `catch` at all.
4. The final `println` shows the successful result — from the caller's perspective, this three-attempt, exponentially-backed-off retry sequence happened entirely transparently inside `callWithBackoffRetry`; only the eventual success is visible outside it.

```
attempt 1 -> TransientNetworkException (retryable) -> wait 100ms -> retry
attempt 2 -> TransientNetworkException (retryable) -> wait 200ms -> retry
attempt 3 -> success -> return immediately, no further attempts or waiting needed
```

## 7. Gotchas & takeaways

> **Gotcha:** retries, even well-configured ones, are only appropriate for genuinely idempotent operations — the same double-execution risk raised in the earlier Gateway `Retry` filter card applies identically here, regardless of which layer initiates the retry. A `Retry` wrapping a non-idempotent write operation needs the same careful consideration (idempotency keys, or simply not retrying that specific operation) as any other retry mechanism covered in this run.

- Resilience4j's `Retry` is the general-purpose building block behind the more context-specific retry behaviors covered earlier (Gateway's `Retry` filter, LoadBalancer's same/next-instance retry) — reach for it directly whenever the operation being protected isn't already covered by one of those.
- Exception-type filtering (`retry-exceptions`/`ignore-exceptions`) is what separates a genuinely resilient retry policy from a wasteful one — always distinguish transient failures worth retrying from permanent ones that retrying can never fix.
- Exponential backoff spaces retries progressively further apart, reducing the risk that the retries themselves become additional load on an already-struggling dependency — a flat, fixed wait duration lacks this self-limiting property.
- `Retry` composes naturally with `CircuitBreaker` — a common real configuration retries a handful of times for transient blips, and if failures persist across many separate calls (not just one call's retries), the circuit breaker eventually trips to stop attempting entirely, letting the fallback take over.
