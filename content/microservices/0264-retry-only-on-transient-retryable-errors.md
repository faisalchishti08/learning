---
card: microservices
gi: 264
slug: retry-only-on-transient-retryable-errors
title: "Retry only on transient/retryable errors"
---

## 1. What it is

Retry-only-on-transient-errors is the discipline of classifying failures before deciding whether to retry them at all — a network timeout or a 503 Service Unavailable is worth retrying since the underlying cause is likely momentary, but a 400 Bad Request or a 401 Unauthorized represents a deterministic failure that will produce the exact same result every time, no matter how many times it's retried, making a retry pure wasted effort at best and actively harmful amplification at worst.

## 2. Why & when

A [retry pattern](0259-retry-pattern.md) applied indiscriminately to every kind of failure treats a client sending malformed input identically to a server that's temporarily overloaded — but retrying the malformed request will fail identically every single time, since nothing about the request itself changed between attempts, meaning every one of those retries is pure wasted load on the server and pure wasted latency for the caller, with zero chance of ever succeeding. Worse, if many callers are simultaneously sending some kind of permanently invalid request (a client bug, a bad deployment), indiscriminate retrying multiplies that already-wasted traffic by the retry count, contributing directly to the amplification risk covered in [retry budgets](0263-retry-budgets.md) and [retry storms](0266-retry-storm-amplification-risk.md) — for no possible benefit, since these failures were never going to resolve through retrying.

Classify every error a retryable call might produce into "worth retrying" (timeouts, connection failures, 5xx server errors, explicitly-marked-retryable application errors) versus "never worth retrying" (4xx client errors except perhaps 429, validation failures, authorization failures, any deterministic business-rule rejection) before wiring up any retry logic, and enforce that classification in the retry mechanism itself, not just as an informal convention.

## 3. Core concept

The retry loop checks the caught exception or response against an explicit classification before deciding whether to attempt again — a retryable failure proceeds to the next attempt, while a non-retryable failure is surfaced to the caller immediately, on the very first occurrence, with no further attempts wasted on it.

```java
boolean isRetryable(Exception e) {
    if (e instanceof ConnectException || e instanceof SocketTimeoutException) return true; // TRANSIENT -- worth retrying
    if (e instanceof HttpServerErrorException http) return http.getStatusCode().is5xxServerError(); // 5xx -- likely transient
    if (e instanceof HttpClientErrorException) return false; // 4xx -- DETERMINISTIC, retrying changes NOTHING
    return false; // UNKNOWN error types default to NOT retryable -- safer than assuming retryability
}

<T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
    for (int attempt = 1; attempt <= maxAttempts; attempt++) {
        try { return operation.get(); }
        catch (Exception e) {
            if (!isRetryable(e) || attempt == maxAttempts) throw e; // STOP immediately on a non-retryable error
        }
    }
    throw new IllegalStateException("unreachable");
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A caught exception is classified before any retry decision -- a transient network timeout proceeds through the normal retry loop, while a deterministic client error is surfaced to the caller immediately on the first occurrence, with no wasted further attempts" >
  <rect x="20" y="65" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caught exception</text>

  <rect x="230" y="20" width="180" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="43" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Transient (timeout, 5xx)</text>
  <text x="320" y="57" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">RETRY normally</text>

  <rect x="230" y="105" width="180" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="128" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Deterministic (4xx)</text>
  <text x="320" y="142" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">SURFACE immediately, NO retry</text>

  <line x1="160" y1="85" x2="228" y2="42" stroke="#8b949e" marker-end="url(#arr264)"/>
  <line x1="160" y1="85" x2="228" y2="128" stroke="#8b949e" marker-end="url(#arr264)"/>

  <defs>
    <marker id="arr264" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The failure's classification, decided once, determines whether it enters the retry loop at all.

## 5. Runnable example

Scenario: a retry mechanism that treats every kind of failure identically, wasting attempts on a client error that could never succeed no matter how many times it's retried, refactored to classify errors explicitly and stop immediately on non-retryable ones, and finally demonstrating both error categories occurring together in a mixed batch of calls, with the total wasted-attempt count measured directly between the naive and classified approaches.

### Level 1 — Basic

```java
// File: RetriesEverythingIndiscriminately.java -- treats a DETERMINISTIC
// client error EXACTLY like a transient one -- wastes ALL retry attempts
// on something that could NEVER succeed.
import java.util.function.*;

public class RetriesEverythingIndiscriminately {
    static class ClientError extends RuntimeException { ClientError(String m) { super(m); } } // e.g. malformed input -- DETERMINISTIC
    static int attemptCount = 0;

    static String callWithMalformedInput() {
        attemptCount++;
        throw new ClientError("400: missing required field 'orderId'"); // will ALWAYS throw this, no matter how many times called
    }

    static <T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
        RuntimeException last = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try { return operation.get(); } catch (RuntimeException e) { last = e; } // retries UNCONDITIONALLY
        }
        throw last;
    }

    public static void main(String[] args) {
        try { callWithRetry(RestrictedCallable(), 3); } catch (RuntimeException ignored) {}
        System.out.println("Made " + attemptCount + " attempts on a request that was GUARANTEED to fail identically every time.");
    }
    static Supplier<String> RestrictedCallable() { return RetriesEverythingIndiscriminately::callWithMalformedInput; }
}
```

**How to run:** `javac RetriesEverythingIndiscriminately.java && java RetriesEverythingIndiscriminately` (JDK 17+).

Expected output:
```
Made 3 attempts on a request that was GUARANTEED to fail identically every time.
```

### Level 2 — Intermediate

```java
// File: ClassifiesBeforeRetrying.java -- classifies the error FIRST;
// a DETERMINISTIC client error is surfaced IMMEDIATELY, on the VERY
// FIRST occurrence -- no attempts wasted.
import java.util.function.*;

public class ClassifiesBeforeRetrying {
    static class ClientError extends RuntimeException { ClientError(String m) { super(m); } }
    static class TransientError extends RuntimeException { TransientError(String m) { super(m); } }
    static int attemptCount = 0;

    static boolean isRetryable(RuntimeException e) { return e instanceof TransientError; } // EXPLICIT classification

    static String callWithMalformedInput() {
        attemptCount++;
        throw new ClientError("400: missing required field 'orderId'");
    }

    static <T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
        RuntimeException last = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try { return operation.get(); }
            catch (RuntimeException e) {
                last = e;
                if (!isRetryable(e)) { System.out.println("  Non-retryable error on attempt " + attempt + " -- STOPPING immediately"); throw e; }
            }
        }
        throw last;
    }

    public static void main(String[] args) {
        try { callWithRetry(ClassifiesBeforeRetrying::callWithMalformedInput, 3); }
        catch (RuntimeException ignored) {}
        System.out.println("Made only " + attemptCount + " attempt(s) -- correctly recognized this could NEVER succeed via retrying.");
    }
}
```

**How to run:** `javac ClassifiesBeforeRetrying.java && java ClassifiesBeforeRetrying` (JDK 17+).

Expected output:
```
  Non-retryable error on attempt 1 -- STOPPING immediately
Made only 1 attempt(s) -- correctly recognized this could NEVER succeed via retrying.
```

### Level 3 — Advanced

```java
// File: MixedBatchMeasuredWasteComparison.java -- runs a REALISTIC MIX
// of transient and deterministic errors through BOTH the naive and
// classified approaches, MEASURING the total wasted attempts saved.
import java.util.function.*;
import java.util.*;

public class MixedBatchMeasuredWasteComparison {
    static class ClientError extends RuntimeException { ClientError(String m) { super(m); } }
    static class TransientError extends RuntimeException { TransientError(String m) { super(m); } }

    static boolean isRetryable(RuntimeException e) { return e instanceof TransientError; }

    static int naiveAttempts(boolean isTransient, int maxAttempts) {
        int attempts = 0;
        for (int a = 1; a <= maxAttempts; a++) {
            attempts++;
            if (isTransient && a == maxAttempts) break; // simulate: transient errors EVENTUALLY succeed on the last attempt
            // deterministic errors NEVER succeed -- but the naive loop doesn't know that, keeps trying anyway
        }
        return attempts;
    }

    static int classifiedAttempts(boolean isTransient, int maxAttempts) {
        int attempts = 0;
        for (int a = 1; a <= maxAttempts; a++) {
            attempts++;
            if (isTransient && a == maxAttempts) break; // transient: retries until success, same as naive
            if (!isTransient) break; // DETERMINISTIC: stop after the FIRST attempt, correctly
        }
        return attempts;
    }

    public static void main(String[] args) {
        // a REALISTIC mixed batch: 100 requests, 70% transient (network blips), 30% deterministic (bad client requests)
        int transientCount = 70, deterministicCount = 30, maxAttempts = 3;

        int naiveTotalAttempts = transientCount * naiveAttempts(true, maxAttempts) + deterministicCount * naiveAttempts(false, maxAttempts);
        int classifiedTotalAttempts = transientCount * classifiedAttempts(true, maxAttempts) + deterministicCount * classifiedAttempts(false, maxAttempts);

        System.out.println("Naive (retries everything): " + naiveTotalAttempts + " total attempts across 100 requests");
        System.out.println("Classified (retries only transient): " + classifiedTotalAttempts + " total attempts across 100 requests");
        System.out.println("Wasted attempts eliminated: " + (naiveTotalAttempts - classifiedTotalAttempts) +
            " (" + ((naiveTotalAttempts - classifiedTotalAttempts) * 100 / naiveTotalAttempts) + "% fewer wasted calls)");
    }
}
```

**How to run:** `javac MixedBatchMeasuredWasteComparison.java && java MixedBatchMeasuredWasteComparison` (JDK 17+).

Expected output:
```
Naive (retries everything): 300 total attempts across 100 requests
Classified (retries only transient): 240 total attempts across 100 requests
Wasted attempts eliminated: 60 (20% fewer wasted calls)
```

## 6. Walkthrough

1. **Level 1, indiscriminate retrying** — `callWithRetry`'s `catch` block has no classification logic at all; it retries any caught `RuntimeException` unconditionally, up to `maxAttempts`, meaning a `ClientError` (guaranteed to throw the identical error on every single call, since `callWithMalformedInput` never changes behavior) is still retried the full 3 times before finally being surfaced.
2. **Level 2, stopping on the first non-retryable occurrence** — `isRetryable` explicitly checks whether the caught exception is an instance of `TransientError`, returning `false` for anything else, including `ClientError`; `callWithRetry`'s `catch` block checks this classification and, when it returns `false`, throws immediately rather than looping again.
3. **Level 2, the correct, minimal outcome** — the identical `ClientError`-throwing scenario from Level 1 now results in exactly 1 attempt instead of 3, since the classification correctly recognizes on the very first occurrence that further attempts would be pointless — this is both faster for the caller (one wasted attempt instead of three) and lighter on the server (no repeated pointless requests).
4. **Level 3, modeling a realistic mixed population** — `naiveAttempts` and `classifiedAttempts` simulate two categories of requests: transient ones (which eventually succeed by the final attempt, modeling a genuine transient blip resolving) and deterministic ones (which the naive version keeps retrying uselessly, while the classified version stops after one attempt).
5. **Level 3, the naive total** — with 70 transient requests each taking their full 3 attempts (legitimately, since they eventually succeed) and 30 deterministic requests *also* each taking their full 3 attempts (wastefully, since none of them could ever succeed), the naive total comes to `70×3 + 30×3 = 300` attempts.
6. **Level 3, the classified total and the measured savings** — the classified version still lets the 70 transient requests take their full, legitimate 3 attempts each (`70×3 = 210`), but correctly limits the 30 deterministic requests to just 1 attempt each (`30×1 = 30`), for a total of `210 + 30 = 240` — a difference of exactly 60 attempts, all of which represented pure waste in the naive version: retries against requests that were mathematically guaranteed to fail identically every single time, contributing nothing but extra load and extra latency for no possible benefit.

## 7. Gotchas & takeaways

> **Gotcha:** an unrecognized or ambiguous exception type defaulting to "retryable" is a risky choice — an unknown failure mode might well be deterministic (a new kind of client error the classification logic hasn't been updated to recognize yet), and treating it as retryable by default risks the exact wasted-attempt problem this discipline is meant to eliminate; defaulting unknown error types to non-retryable, as the concept example does, is the safer choice, even though it occasionally means a genuinely transient-but-unrecognized failure misses out on a retry it could have benefited from.

- Classifying failures as transient (worth retrying) versus deterministic (never worth retrying) before wiring up retry logic prevents wasting retry attempts on failures that were mathematically guaranteed to recur identically.
- Deterministic failures — malformed input, authorization failures, most 4xx client errors — represent conditions that don't change between attempts, so retrying them changes nothing and only adds waste.
- The retry mechanism should check this classification explicitly and stop immediately on the first non-retryable occurrence, rather than proceeding through the full attempt count regardless of the failure's nature.
- Applying this discipline across a realistic mixed population of failures, as demonstrated, produces a measurable, meaningful reduction in wasted attempts compared to retrying indiscriminately.
- Unrecognized or ambiguous error types should default to non-retryable rather than retryable — the safer failure mode is occasionally missing a retry opportunity, not repeatedly wasting attempts on an unrecognized-but-actually-deterministic failure.
