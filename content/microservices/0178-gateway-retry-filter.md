---
card: microservices
gi: 178
slug: gateway-retry-filter
title: "Gateway retry filter"
---

## 1. What it is

Spring Cloud Gateway's retry filter automatically re-attempts a failed request to a backend a configured number of times, optionally with backoff between attempts and limited to specific HTTP status codes or exception types — declarative, configuration-driven retry behavior applied at the routing layer, sparing every individual client and every individual backend from needing to implement retry logic themselves.

## 2. Why & when

A backend failure is often transient — a momentary network blip, a brief instance restart, a fleeting overload — and simply failing the client's request immediately on the first such failure wastes an opportunity to succeed on a near-immediate retry, something a struggling but fundamentally healthy backend would often satisfy just fine a moment later. Implementing retry logic in every client that talks to the gateway duplicates that logic across every consumer; implementing it in every backend service duplicates it across every service. A retry filter at the gateway handles this exactly once, uniformly, for every route configured to use it.

Configure the retry filter for routes to backends where transient failures are plausible and where the underlying operation is safe to retry — critically, only for operations that are genuinely safe to repeat (idempotent reads, or writes protected by [idempotent consumer](0127-idempotent-consumers.md)-style safeguards), since blindly retrying a non-idempotent write (a payment charge, for instance) risks the exact double-processing problem idempotency is meant to prevent.

## 3. Core concept

The retry filter wraps a route's backend call; on a failure matching the configured retryable conditions (specific status codes, specific exceptions), it re-attempts the call, up to a configured maximum number of attempts, optionally with a backoff delay between attempts — only surfacing a failure to the client once the retry budget is exhausted.

```java
.filters(f -> f.retry(config -> config
    .setRetries(3)
    .setStatuses(HttpStatus.BAD_GATEWAY, HttpStatus.SERVICE_UNAVAILABLE) // ONLY retry these -- not 400s, which won't fix themselves
    .setBackoff(Duration.ofMillis(100), Duration.ofSeconds(1), 2, true))) // exponential backoff between attempts
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request fails on its first attempt with a 503; the retry filter automatically retries with backoff, and the second attempt succeeds -- the client only ever sees the final successful response, unaware a retry happened" >
  <rect x="20" y="60" width="100" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>

  <rect x="220" y="20" width="200" height="130" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#8b949e" font-size="8" font-family="sans-serif">Retry filter</text>
  <text x="240" y="65" fill="#e6edf3" font-size="7.5" font-family="sans-serif">attempt 1 -&gt; 503, backoff</text>
  <text x="240" y="90" fill="#e6edf3" font-size="7.5" font-family="sans-serif">attempt 2 -&gt; 200 OK</text>
  <text x="240" y="125" fill="#8b949e" font-size="7" font-family="sans-serif">client only sees the final result</text>

  <rect x="480" y="60" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Backend</text>

  <line x1="120" y1="82" x2="218" y2="82" stroke="#8b949e" marker-end="url(#arr59)"/>
  <line x1="420" y1="82" x2="478" y2="82" stroke="#8b949e" marker-end="url(#arr59)"/>

  <defs>
    <marker id="arr59" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The retry happens entirely inside the gateway; the client experiences only the eventual outcome, never the intermediate failure.

## 5. Runnable example

Scenario: an order lookup route that starts with no retry, failing the client immediately on a single transient error, adds a configurable retry filter with status-code-based eligibility and backoff, and finally demonstrates the critical safety distinction between retrying a safe, idempotent GET versus correctly refusing to blindly retry a non-idempotent POST.

### Level 1 — Basic

```java
// File: NoRetryImmediateFailure.java -- ONE transient failure immediately fails
// the client's request, even though a near-instant retry would likely succeed.
public class NoRetryImmediateFailure {
    static int callCount = 0;
    static String callBackend() {
        callCount++;
        if (callCount == 1) throw new RuntimeException("503 Service Unavailable (transient)"); // fails ONCE, then would succeed
        return "200 OK";
    }

    public static void main(String[] args) {
        try {
            System.out.println(callBackend());
        } catch (RuntimeException e) {
            System.out.println("Client sees: " + e.getMessage());
            System.out.println("A retry would have succeeded (the SECOND call works fine), but nothing retried it.");
        }
    }
}
```

**How to run:** `javac NoRetryImmediateFailure.java && java NoRetryImmediateFailure` (JDK 17+).

### Level 2 — Intermediate

```java
// File: RetryFilterWithBackoffAndStatusFilter.java -- retries ONLY configured
// status codes, with BACKOFF between attempts, transparently to the client.
import java.util.*;

public class RetryFilterWithBackoffAndStatusFilter {
    static class BackendException extends RuntimeException {
        int statusCode;
        BackendException(int statusCode, String message) { super(message); this.statusCode = statusCode; }
    }

    static class RetryFilter {
        int maxRetries;
        Set<Integer> retryableStatuses;
        long backoffMillis;
        RetryFilter(int maxRetries, Set<Integer> retryableStatuses, long backoffMillis) {
            this.maxRetries = maxRetries; this.retryableStatuses = retryableStatuses; this.backoffMillis = backoffMillis;
        }

        String call(java.util.function.Supplier<String> backendCall) throws InterruptedException {
            int attempt = 0;
            while (true) {
                attempt++;
                try {
                    return backendCall.get();
                } catch (BackendException e) {
                    boolean retryable = retryableStatuses.contains(e.statusCode);
                    System.out.println("  attempt " + attempt + " failed with status " + e.statusCode + " (retryable=" + retryable + ")");
                    if (!retryable || attempt > maxRetries) throw e; // give up: not retryable, or budget exhausted
                    Thread.sleep(backoffMillis); // BACKOFF before the next attempt
                }
            }
        }
    }

    static int callCount = 0;
    static String flakyBackendCall() {
        callCount++;
        if (callCount < 3) throw new BackendException(503, "Service Unavailable"); // fails TWICE, succeeds on the 3rd
        return "200 OK, order data";
    }

    public static void main(String[] args) throws InterruptedException {
        RetryFilter retryFilter = new RetryFilter(3, Set.of(503, 502), 50);
        String result = retryFilter.call(RetryFilterWithBackoffAndStatusFilter::flakyBackendCall);
        System.out.println("Client receives: " + result + " (client NEVER saw the two intermediate 503s)");
    }
}
```

**How to run:** `javac RetryFilterWithBackoffAndStatusFilter.java && java RetryFilterWithBackoffAndStatusFilter` (JDK 17+).

Expected output:
```
  attempt 1 failed with status 503 (retryable=true)
  attempt 2 failed with status 503 (retryable=true)
Client receives: 200 OK, order data (client NEVER saw the two intermediate 503s)
```

### Level 3 — Advanced

```java
// File: SafeVsUnsafeRetryDistinction.java -- retrying a SAFE, idempotent GET is
// fine; blindly retrying an UNSAFE, non-idempotent POST risks DOUBLE-PROCESSING.
import java.util.*;

public class SafeVsUnsafeRetryDistinction {
    static class BackendException extends RuntimeException {
        int statusCode;
        BackendException(int statusCode, String message) { super(message); this.statusCode = statusCode; }
    }

    static class RetryFilter {
        int maxRetries; Set<Integer> retryableStatuses; Set<String> retryableMethods;
        RetryFilter(int maxRetries, Set<Integer> retryableStatuses, Set<String> retryableMethods) {
            this.maxRetries = maxRetries; this.retryableStatuses = retryableStatuses; this.retryableMethods = retryableMethods;
        }
        String call(String httpMethod, java.util.function.Supplier<String> backendCall) {
            int attempt = 0;
            while (true) {
                attempt++;
                try {
                    return backendCall.get();
                } catch (BackendException e) {
                    // BOTH conditions matter: retryable STATUS *and* retryable METHOD (idempotent-safe)
                    boolean statusOk = retryableStatuses.contains(e.statusCode);
                    boolean methodOk = retryableMethods.contains(httpMethod);
                    if (!statusOk || !methodOk || attempt > maxRetries) {
                        System.out.println("  " + httpMethod + " attempt " + attempt + ": NOT retrying (statusOk=" + statusOk + ", methodOk=" + methodOk + ")");
                        throw e;
                    }
                    System.out.println("  " + httpMethod + " attempt " + attempt + ": retrying (safe: idempotent method + retryable status)");
                }
            }
        }
    }

    static int chargeAttempts = 0;
    static String chargeCustomerPost() { // NON-idempotent: charging TWICE is a REAL financial bug
        chargeAttempts++;
        System.out.println("    !!! ACTUALLY CHARGING THE CUSTOMER (attempt " + chargeAttempts + ") !!!");
        throw new BackendException(503, "Service Unavailable");
    }

    static int getAttempts = 0;
    static String getOrderStatusGet() { // idempotent: reading twice is harmless
        getAttempts++;
        if (getAttempts < 2) throw new BackendException(503, "Service Unavailable");
        return "200 OK, order status";
    }

    public static void main(String[] args) {
        RetryFilter retryFilter = new RetryFilter(2, Set.of(503), Set.of("GET")); // ONLY GET is in the safe-to-retry set

        System.out.println("=== GET (idempotent, safe to retry) ===");
        String getResult = retryFilter.call("GET", SafeVsUnsafeRetryDistinction::getOrderStatusGet);
        System.out.println("Result: " + getResult);

        System.out.println("\n=== POST (NOT idempotent, must NOT blindly retry) ===");
        try {
            retryFilter.call("POST", SafeVsUnsafeRetryDistinction::chargeCustomerPost);
        } catch (BackendException e) {
            System.out.println("Failed as expected -- POST failure surfaced to caller WITHOUT a blind retry.");
        }
        System.out.println("Customer was charged " + chargeAttempts + " time(s) -- the retry filter correctly refused to risk a SECOND charge.");
    }
}
```

**How to run:** `javac SafeVsUnsafeRetryDistinction.java && java SafeVsUnsafeRetryDistinction` (JDK 17+).

Expected output:
```
=== GET (idempotent, safe to retry) ===
  GET attempt 1: retrying (safe: idempotent method + retryable status)
Result: 200 OK, order status

=== POST (NOT idempotent, must NOT blindly retry) ===
    !!! ACTUALLY CHARGING THE CUSTOMER (attempt 1) !!!
  POST attempt 1: NOT retrying (statusOk=true, methodOk=false)
Failed as expected -- POST failure surfaced to caller WITHOUT a blind retry.
Customer was charged 1 time(s) -- the retry filter correctly refused to risk a SECOND charge.
```

## 6. Walkthrough

1. **Level 1** — `callBackend` throws on its first invocation and would succeed on a second, but nothing in `main` attempts a second call; the client's `catch` block reports the failure directly, having never had the opportunity to benefit from the transient nature of the error.
2. **Level 2, the retry loop with eligibility check** — `RetryFilter.call` wraps `backendCall.get()` in a `while (true)` loop; on catching a `BackendException`, it checks `retryableStatuses.contains(e.statusCode)` before deciding whether to retry, meaning only failures matching the configured status codes trigger another attempt.
3. **Level 2, backoff between attempts** — `Thread.sleep(backoffMillis)` runs between a failed attempt and the next retry, giving the backend a brief window to recover rather than immediately hammering it again.
4. **Level 2, the client's experience** — `flakyBackendCall` fails on its first two invocations and succeeds on the third; `main`'s single call to `retryFilter.call(...)` handles all three attempts internally, and the printed `"Client receives:"` line shows only the final, successful result — the two intermediate 503 failures were entirely absorbed inside the filter.
5. **Level 3, adding a method-safety check** — `RetryFilter.call` now takes an `httpMethod` parameter and checks `retryableMethods.contains(httpMethod)` *in addition to* the status code check; the configured `retryableMethods` set contains only `"GET"`, deliberately excluding `"POST"`.
6. **Level 3, the safe GET retrying normally** — `getOrderStatusGet` fails once and succeeds on its second attempt; because `httpMethod` is `"GET"` (in the safe set) and the status is retryable, the retry proceeds exactly as in Level 2, and the client receives the eventual success transparently.
7. **Level 3, the unsafe POST correctly refusing to retry** — `chargeCustomerPost` throws on its first (and only) invocation; even though its `statusCode` (503) matches `retryableStatuses`, `methodOk` evaluates to `false` because `"POST"` is not in `retryableMethods`, so `call` immediately re-throws the exception rather than attempting a second call — the printed `chargeAttempts` count of exactly `1` confirms the customer's card was charged (or at least attempted) only once, directly demonstrating that the retry filter's method-awareness prevented a potential double-charge that a naive, status-code-only retry policy (like Level 2's) would have risked.

## 7. Gotchas & takeaways

> **Gotcha:** a request can fail with a network-level error (a connection timeout, a dropped connection) *after* the backend has already begun processing it, meaning even a nominally idempotent-looking operation might have partially executed before the failure that triggered a retry — true safety requires the backend operation itself to be genuinely idempotent (see [idempotent consumers](0127-idempotent-consumers.md)), not just relying on the gateway's HTTP-method-based heuristic (GET is "probably safe," POST is "probably not") as a complete guarantee.

- The retry filter automatically re-attempts failed backend calls according to configured status-code and retry-count rules, transparently to the client, sparing individual clients and backends from implementing this logic themselves.
- Backoff between retry attempts gives a struggling backend room to recover rather than immediately re-sending the same load that may have contributed to the original failure.
- Retry eligibility should be restricted to genuinely idempotent operations — retrying a non-idempotent write (like a payment charge) risks the exact double-processing problem idempotency safeguards are meant to prevent.
- Combining status-code-based and HTTP-method-based eligibility checks (retry GETs, refuse to blindly retry POSTs) is a practical, if imperfect, heuristic for distinguishing safe from unsafe retries.
- True retry safety ultimately depends on the backend operation's own idempotency, not just the gateway's HTTP-method heuristic — a network failure can occur after a backend has partially processed even a nominally safe-looking request.
