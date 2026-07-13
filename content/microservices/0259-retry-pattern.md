---
card: microservices
gi: 259
slug: retry-pattern
title: "Retry pattern"
---

## 1. What it is

The retry pattern is the practice of automatically re-attempting a failed operation, rather than immediately surfacing the failure to the caller, on the reasoning that many failures in a distributed system — a momentary network blip, a brief resource contention spike — are transient and will succeed on a second attempt made moments later, even though the first attempt genuinely failed.

## 2. Why & when

In a distributed system where [partial failure](0239-why-distributed-systems-fail-partial-failure.md) is the norm, a meaningful fraction of failures are self-resolving within a very short window — a load balancer briefly routing to an instance mid-restart, a database connection pool momentarily exhausted before a connection frees up, a packet lost to ordinary network jitter. Surfacing every one of these transient blips directly to the end user or upstream caller, rather than quietly retrying and very likely succeeding on the next attempt, produces a needlessly fragile user experience for problems that would have resolved themselves within milliseconds. The retry pattern automates this "try again" instinct, but — as the rest of this section's topics on [max attempts](0260-max-retry-attempts.md), [backoff](0261-fixed-vs-exponential-backoff.md), [jitter](0262-jitter-randomized-backoff.md), and [retryable-error classification](0264-retry-only-on-transient-retryable-errors.md) cover — doing it correctly requires several deliberate safeguards, or the "fix" for transient failures can make a real, sustained failure meaningfully worse.

Apply retries to operations where transient failure is plausible and where the operation is safe to attempt more than once — the safety consideration (idempotency) is critical, and is exactly what [why distributed systems fail](0239-why-distributed-systems-fail-partial-failure.md) covers regarding timeout ambiguity. Never retry blindly without considering whether the operation is safe to repeat, and never retry indefinitely without a limit — both mistakes turn a resilience mechanism into an amplifier of the very problem it was meant to solve.

## 3. Core concept

A retry wraps a call in a loop that catches a failure, waits (typically with increasing delay between attempts), and tries again, up to some limit — the calling code experiences either an eventual success or a final failure after all attempts are exhausted, rather than the raw first-attempt outcome alone.

```java
<T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
    RuntimeException lastException = null;
    for (int attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return operation.get(); // SUCCESS on any attempt returns immediately
        } catch (RuntimeException e) {
            lastException = e;
            System.out.println("Attempt " + attempt + " failed: " + e.getMessage());
            // (a real implementation adds a WAIT here between attempts -- see backoff topics)
        }
    }
    throw lastException; // ALL attempts exhausted -- surface the LAST failure to the caller
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A call fails on its first attempt, is retried and fails again on the second attempt, then succeeds on the third attempt -- the caller only ever sees the final, successful result, unaware that two earlier attempts failed" >
  <rect x="20" y="55" width="130" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="85" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Attempt 1: FAIL</text>

  <rect x="200" y="55" width="130" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="265" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Attempt 2: FAIL</text>

  <rect x="380" y="55" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="445" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Attempt 3: SUCCESS</text>

  <line x1="150" y1="75" x2="198" y2="75" stroke="#8b949e" marker-end="url(#arr259)"/>
  <line x1="330" y1="75" x2="378" y2="75" stroke="#8b949e" marker-end="url(#arr259)"/>

  <text x="560" y="75" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">Caller sees: SUCCESS</text>
  <line x1="510" y1="75" x2="558" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr259g)"/>

  <defs>
    <marker id="arr259" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr259g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The caller experiences only the eventual outcome, unaware of transient failures the retry loop absorbed along the way.

## 5. Runnable example

Scenario: a call that fails outright on its first attempt with no retry at all (surfacing a transient blip directly), refactored to retry automatically and succeed transparently once the transient condition resolves, and finally demonstrating an operation that never succeeds within the attempt limit, correctly exhausting all attempts and surfacing the final failure rather than retrying forever.

### Level 1 — Basic

```java
// File: NoRetryAtAll.java -- a SINGLE attempt; a TRANSIENT failure
// (that would have succeeded moments later) is surfaced IMMEDIATELY.
public class NoRetryAtAll {
    static int callCount = 0;

    // simulates a TRANSIENT failure: fails on the first call, would SUCCEED on a second
    static String callDependency() {
        callCount++;
        if (callCount == 1) throw new RuntimeException("transient network blip");
        return "success";
    }

    public static void main(String[] args) {
        try {
            String result = callDependency();
            System.out.println("Result: " + result);
        } catch (RuntimeException e) {
            System.out.println("FAILED immediately: " + e.getMessage() + " -- even though a SECOND attempt would have succeeded!");
        }
    }
}
```

**How to run:** `javac NoRetryAtAll.java && java NoRetryAtAll` (JDK 17+).

Expected output:
```
FAILED immediately: transient network blip -- even though a SECOND attempt would have succeeded!
```

### Level 2 — Intermediate

```java
// File: AutomaticRetry.java -- retries AUTOMATICALLY on failure; the
// SAME transient blip is now transparently absorbed.
import java.util.function.*;

public class AutomaticRetry {
    static int callCount = 0;

    static String callDependency() {
        callCount++;
        if (callCount == 1) throw new RuntimeException("transient network blip");
        return "success";
    }

    static <T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
        RuntimeException lastException = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return operation.get(); // SUCCESS returns immediately, whichever attempt it happens on
            } catch (RuntimeException e) {
                lastException = e;
                System.out.println("  Attempt " + attempt + " failed: " + e.getMessage() + " -- retrying");
            }
        }
        throw lastException;
    }

    public static void main(String[] args) {
        String result = callWithRetry(AutomaticRetry::callDependency, 3);
        System.out.println("Final result: " + result + " -- the CALLER never even saw the first attempt's failure directly.");
    }
}
```

**How to run:** `javac AutomaticRetry.java && java AutomaticRetry` (JDK 17+).

Expected output:
```
  Attempt 1 failed: transient network blip -- retrying
Final result: success -- the CALLER never even saw the first attempt's failure directly.
```

### Level 3 — Advanced

```java
// File: ExhaustsAllAttemptsOnPersistentFailure.java -- a GENUINELY
// persistent failure (not transient) correctly exhausts ALL attempts
// and surfaces the FINAL failure -- retries do NOT mean infinite retries.
import java.util.function.*;

public class ExhaustsAllAttemptsOnPersistentFailure {
    static int callCount = 0;

    // simulates a GENUINE, ongoing outage -- NEVER succeeds, no matter how many times it's called
    static String callPermanentlyBrokenDependency() {
        callCount++;
        throw new RuntimeException("dependency is down (attempt " + callCount + ")");
    }

    static <T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
        RuntimeException lastException = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return operation.get();
            } catch (RuntimeException e) {
                lastException = e;
                System.out.println("  Attempt " + attempt + "/" + maxAttempts + " failed: " + e.getMessage());
            }
        }
        throw lastException; // ALL attempts exhausted -- correctly STOPS here, does NOT retry forever
    }

    public static void main(String[] args) {
        try {
            callWithRetry(ExhaustsAllAttemptsOnPersistentFailure::callPermanentlyBrokenDependency, 3);
        } catch (RuntimeException e) {
            System.out.println("Final failure surfaced to caller after " + callCount + " total attempts: " + e.getMessage());
            System.out.println("The retry mechanism correctly STOPPED at the configured limit, rather than retrying indefinitely.");
        }
    }
}
```

**How to run:** `javac ExhaustsAllAttemptsOnPersistentFailure.java && java ExhaustsAllAttemptsOnPersistentFailure` (JDK 17+).

Expected output:
```
  Attempt 1/3 failed: dependency is down (attempt 1)
  Attempt 2/3 failed: dependency is down (attempt 2)
  Attempt 3/3 failed: dependency is down (attempt 3)
Final failure surfaced to caller after 3 total attempts: dependency is down (attempt 3)
The retry mechanism correctly STOPPED at the configured limit, rather than retrying indefinitely.
```

## 6. Walkthrough

1. **Level 1, the unnecessarily fragile baseline** — `callDependency` is designed (for this example) to fail only on its very first invocation and succeed on any subsequent one, modeling a genuinely transient blip; `main` calls it exactly once, so the transient failure is surfaced directly to the caller even though the underlying condition would have resolved on its own within moments.
2. **Level 2, absorbing the transient failure automatically** — `callWithRetry` wraps the identical `callDependency` call in a loop; the first attempt fails exactly as in Level 1, but instead of surfacing that failure, the loop catches it, logs it, and proceeds to a second attempt — which succeeds, since `callCount` is now `2`.
3. **Level 2, the caller's experience** — `main`'s call to `callWithRetry` returns `"success"` directly, with no exception ever reaching it; the caller experiences a clean, successful call despite the underlying transient failure that occurred on the first real attempt — exactly the value proposition the retry pattern provides.
4. **Level 3, a failure that isn't actually transient** — `callPermanentlyBrokenDependency` throws on *every* invocation, unconditionally, modeling a genuine, ongoing outage rather than a momentary blip; retrying this operation any number of times within a short window will never produce a different outcome.
5. **Level 3, the retry loop still bounded** — `callWithRetry`'s loop runs for exactly `maxAttempts` (3) iterations regardless of whether the underlying failure is transient or persistent; after the third failed attempt, the loop exits normally (not via some special "give up" branch) and the final `throw lastException` line executes, surfacing the last failure to the caller.
6. **Level 3, why this bounded behavior matters** — if `callWithRetry` retried without any limit, a genuinely broken dependency would cause this call to loop forever (or for an extremely long time), consuming resources and blocking the caller indefinitely on an operation that was never going to succeed — the printed final message confirms the mechanism correctly recognized the limit had been reached and surfaced a clear failure instead, which is the necessary complement to Level 2's success story: retries help exactly where the underlying problem genuinely is transient, and correctly give up, with a clear signal, where it isn't.

## 7. Gotchas & takeaways

> **Gotcha:** retrying a non-idempotent operation (like a payment charge with no [idempotency key](0239-why-distributed-systems-fail-partial-failure.md)) after a timeout can cause the operation to be performed twice, since a timeout provides no certainty about whether the original attempt actually completed — the retry pattern is only safe to apply broadly to operations that are genuinely safe to repeat; for anything else, retries need to be paired with idempotency guarantees, not applied blindly to every failed call.

- The retry pattern automatically re-attempts a failed operation, on the reasoning that many distributed-system failures are transient and likely to succeed on a subsequent attempt.
- It works by wrapping a call in a bounded loop that catches failures, waits between attempts, and tries again — the caller sees either an eventual success or a final failure after all attempts are exhausted.
- Retries genuinely help absorb transient failures (brief network blips, momentary resource contention) transparently, without the caller ever needing to know a failure occurred at all.
- Retries must always be bounded by a maximum attempt count, covered next — an unbounded retry loop against a genuinely persistent failure would consume resources and block the caller indefinitely.
- Retrying is only safe for operations that can be repeated without harmful side effects; applying it blindly to non-idempotent operations risks performing the operation more than once, as covered in the timeout-ambiguity discussion under [why distributed systems fail](0239-why-distributed-systems-fail-partial-failure.md).
