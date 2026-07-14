---
card: microservices
gi: 481
slug: mesh-level-resiliency-retries-timeouts-circuit-breaking
title: "Mesh-level resiliency (retries, timeouts, circuit breaking)"
---

## 1. What it is

**Mesh-level resiliency** means retries, timeouts, and circuit breaking are configured and enforced entirely inside the [sidecar proxies](0479-sidecar-proxy-envoy.md) of a service mesh, rather than written into each application's own code. An operator declares policy (retry up to 3 times, timeout after 2 seconds, open the circuit after 5 consecutive failures) once, centrally, and every proxy in the mesh applies it uniformly to the traffic it handles — regardless of what language or framework the calling and called services happen to be written in.

## 2. Why & when

You push resiliency into the mesh specifically when you want it applied consistently across a polyglot fleet without duplicating the logic in every service:

- **Application-level resiliency libraries only cover applications written in that library's language.** A Java service can use [Resilience4j](0484-service-mesh-vs-library-based-resiliency-resilience4j.md); a Python or Go service calling the same downstream dependency needs its own separate implementation — a mesh applies the identical policy regardless of the caller's language.
- **Centralized policy means centralized, auditable configuration.** "What's our retry policy for calls to `payment-service`?" has one authoritative answer, configured once, rather than potentially many different, drifted answers scattered across every calling service's own code.
- **Changing a resiliency policy shouldn't require redeploying every calling application.** Updating a timeout or retry count at the mesh level takes effect the moment the [control plane](0478-data-plane-vs-control-plane.md) pushes the new configuration — no application code change, no rebuild, no redeploy needed.
- **You use this as the default resiliency layer once a mesh is adopted** — application-level resiliency libraries still have a role for concerns that need application-specific knowledge (like a business-logic-aware fallback value), but the baseline network resiliency belongs at the mesh layer.

## 3. Core concept

Think of a building-wide fire suppression system versus every individual office having its own separate fire extinguisher policy: the building-wide system applies the same detection and response standard everywhere, configured and maintained centrally, regardless of what each individual office does or doesn't have set up on its own. Mesh-level resiliency is that building-wide system for network failures.

Concretely:

1. **Retries**: a proxy configured to retry a failed call automatically re-attempts it (up to a configured maximum), typically only for specific conditions (a 503 response, a connection failure) rather than blindly retrying every kind of failure.
2. **Timeouts**: a proxy configured with a per-call timeout aborts a request that's taking too long, returning an error to the caller rather than waiting indefinitely — protecting the caller from a slow or hung downstream dependency.
3. **Circuit breaking**: a proxy tracking a destination's recent failure rate can "open the circuit" — stop sending it new requests entirely for a cooldown period — once failures cross a threshold, protecting both the struggling destination (giving it room to recover) and the caller (failing fast instead of piling up slow, doomed requests).
4. **All three are configured declaratively, per-route**, meaning different destinations or even different paths to the same destination can have different resiliency policies, tuned to their specific characteristics.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A proxy applies retries on failure, a timeout bound on duration, and opens a circuit breaker after sustained failures, all configured centrally" >
  <rect x="20" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">retry</text>
  <text x="110" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">up to 3x on failure</text>

  <rect x="240" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">timeout</text>
  <text x="330" y="58" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">abort after 2s</text>

  <rect x="460" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">circuit breaker</text>
  <text x="550" y="58" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">open after 5 fails</text>

  <text x="330" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">all three configured once, centrally, and enforced by every proxy uniformly, regardless of caller language</text>
</svg>

Three distinct resiliency mechanisms, each configured centrally and enforced entirely inside the proxy layer.

## 5. Runnable example

Scenario: a proxy applying all three mesh-level resiliency mechanisms to calls toward a downstream dependency. We start with basic retry-on-failure, extend it to a bounded timeout, then handle the hard case: a circuit breaker opening after sustained failures and rejecting calls immediately, without even attempting them, until a cooldown passes.

### Level 1 — Basic

```java
// File: MeshRetryBasic.java -- models the proxy RETRYING a failed call
// automatically, entirely OUTSIDE the calling application's own code.
public class MeshRetryBasic {
    static int attemptCount = 0;

    static String realDownstreamCall() {
        attemptCount++;
        if (attemptCount < 2) {
            throw new RuntimeException("transient failure");
        }
        return "success";
    }

    static String proxyCallWithRetry(int maxRetries) {
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                String result = realDownstreamCall();
                System.out.println("[proxy] succeeded on attempt " + attempt);
                return result;
            } catch (RuntimeException e) {
                System.out.println("[proxy] attempt " + attempt + " failed, retrying (configured policy: retry up to " + maxRetries + ")");
            }
        }
        throw new RuntimeException("retries exhausted");
    }

    public static void main(String[] args) {
        System.out.println("[app] making a normal call -- unaware of any retry policy");
        String result = proxyCallWithRetry(3);
        System.out.println("[app] received: " + result);
    }
}
```

How to run: `java MeshRetryBasic.java`

`proxyCallWithRetry` retries `realDownstreamCall` internally, up to `maxRetries` times — the application's own code (represented by `main`) calls it exactly once and never sees the intermediate failure, exactly like a real Envoy proxy configured with a retry policy absorbing transient failures before the calling application ever notices anything went wrong.

### Level 2 — Intermediate

```java
// File: MeshTimeoutBasic.java -- the SAME retrying proxy, now EXTENDED
// with a TIMEOUT bound -- a call that takes too long is aborted, rather
// than the caller waiting indefinitely for a slow downstream dependency.
public class MeshTimeoutBasic {
    static String slowDownstreamCall(long simulatedDurationMs) throws InterruptedException {
        Thread.sleep(simulatedDurationMs);
        return "success after " + simulatedDurationMs + "ms";
    }

    static String proxyCallWithTimeout(long timeoutMs, long callDurationMs) {
        long start = System.currentTimeMillis();
        try {
            if (callDurationMs > timeoutMs) {
                // Simulates the proxy aborting once the timeout is exceeded,
                // rather than actually waiting the full slow duration.
                Thread.sleep(timeoutMs);
                throw new RuntimeException("call exceeded configured timeout of " + timeoutMs + "ms -- ABORTED");
            }
            return slowDownstreamCall(callDurationMs);
        } catch (InterruptedException e) {
            throw new RuntimeException("interrupted", e);
        } finally {
            System.out.println("[proxy] call bounded at " + (System.currentTimeMillis() - start) + "ms elapsed");
        }
    }

    public static void main(String[] args) {
        System.out.println("--- case 1: fast call, well within timeout ---");
        System.out.println("[app] received: " + proxyCallWithTimeout(500, 50));

        System.out.println();
        System.out.println("--- case 2: slow call, exceeds timeout ---");
        try {
            proxyCallWithTimeout(200, 5000);
        } catch (RuntimeException e) {
            System.out.println("[app] received error: " + e.getMessage());
        }
    }
}
```

How to run: `java MeshTimeoutBasic.java`

`proxyCallWithTimeout` compares the simulated call duration against the configured `timeoutMs` before deciding whether to let it run to completion or abort it early — case 1's 50ms call is well under its 500ms timeout and completes normally, while case 2's 5000ms call would take far longer than its 200ms timeout, so the proxy aborts after only `timeoutMs` has elapsed rather than the caller ever waiting the full 5 seconds.

### Level 3 — Advanced

```java
// File: MeshCircuitBreaker.java -- the SAME resiliency proxy, now
// handling the PRODUCTION-FLAVORED hard case: a CIRCUIT BREAKER opening
// after SUSTAINED failures. Once open, the proxy REJECTS calls
// IMMEDIATELY, without even attempting them -- protecting a struggling
// downstream from a pile of doomed requests, and failing the caller fast
// instead of slow. After a cooldown, the breaker allows a trial call
// through to test recovery.
public class MeshCircuitBreaker {
    enum CircuitState { CLOSED, OPEN, HALF_OPEN }

    static CircuitState state = CircuitState.CLOSED;
    static int consecutiveFailures = 0;
    static final int FAILURE_THRESHOLD = 3;
    static boolean downstreamHealthy = false; // starts broken

    static String realDownstreamCall() {
        if (!downstreamHealthy) {
            throw new RuntimeException("downstream is down");
        }
        return "success";
    }

    static String proxyCallWithCircuitBreaker() {
        if (state == CircuitState.OPEN) {
            System.out.println("[proxy] circuit OPEN -- REJECTING immediately, not even attempting the call");
            throw new RuntimeException("circuit breaker open, failing fast");
        }
        try {
            String result = realDownstreamCall();
            consecutiveFailures = 0;
            if (state == CircuitState.HALF_OPEN) {
                state = CircuitState.CLOSED;
                System.out.println("[proxy] trial call succeeded -- circuit CLOSED, resuming normal traffic");
            } else {
                System.out.println("[proxy] call succeeded");
            }
            return result;
        } catch (RuntimeException e) {
            consecutiveFailures++;
            System.out.println("[proxy] call failed (" + consecutiveFailures + "/" + FAILURE_THRESHOLD + " consecutive failures)");
            if (consecutiveFailures >= FAILURE_THRESHOLD) {
                state = CircuitState.OPEN;
                System.out.println("[proxy] threshold reached -- circuit OPENED, further calls rejected immediately");
            }
            throw e;
        }
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            System.out.println("--- call " + i + " ---");
            try {
                proxyCallWithCircuitBreaker();
            } catch (RuntimeException e) {
                System.out.println("[app] received error: " + e.getMessage());
            }
        }

        System.out.println();
        System.out.println("[recovery] downstream comes back healthy, cooldown elapses -- breaker allows a trial call");
        downstreamHealthy = true;
        state = CircuitState.HALF_OPEN;
        try {
            System.out.println("[app] received: " + proxyCallWithCircuitBreaker());
        } catch (RuntimeException e) {
            System.out.println("[app] received error: " + e.getMessage());
        }
    }
}
```

How to run: `java MeshCircuitBreaker.java`

`consecutiveFailures` accumulates across calls while `downstreamHealthy` is `false`, and once it reaches `FAILURE_THRESHOLD`, `state` flips to `OPEN` — every subsequent call to `proxyCallWithCircuitBreaker` then hits the `if (state == CircuitState.OPEN)` check first and returns immediately with a rejection, never even calling `realDownstreamCall`. Only after the simulated recovery sets `downstreamHealthy = true` and manually transitions `state` to `HALF_OPEN` does a trial call get attempted again — succeeding this time, and closing the circuit back to normal operation.

## 6. Walkthrough

Trace `MeshCircuitBreaker.main` in order. **First**, calls 1 through 3 each hit `proxyCallWithCircuitBreaker` while `state` is still `CLOSED`. Each one calls `realDownstreamCall`, which throws since `downstreamHealthy` is `false` — each catch increments `consecutiveFailures`, reaching `1`, `2`, then `3` across the three calls, and on the third, `consecutiveFailures >= FAILURE_THRESHOLD` becomes `true`, flipping `state` to `OPEN`.

**Next**, call 4 hits `proxyCallWithCircuitBreaker` again, but this time the very first check, `if (state == CircuitState.OPEN)`, is `true` — it prints the rejection message and throws immediately, without `realDownstreamCall` ever being invoked at all for this call.

**Then**, call 5 behaves identically to call 4 — the circuit is still `OPEN`, so it's rejected instantly, with `consecutiveFailures` no longer even being touched, since the whole `try` block is skipped entirely once the circuit is open.

**After that**, the simulated recovery sets `downstreamHealthy = true` and manually sets `state = CircuitState.HALF_OPEN` — representing a real circuit breaker's cooldown timer expiring and allowing exactly one trial call through to test whether the downstream has actually recovered.

**Finally**, the trial call runs `proxyCallWithCircuitBreaker` once more: `state` is `HALF_OPEN`, not `OPEN`, so the rejection branch is skipped and `realDownstreamCall` actually executes — since `downstreamHealthy` is now `true`, it succeeds, `consecutiveFailures` resets to `0`, and because `state` was `HALF_OPEN`, the success branch specifically transitions it back to `CLOSED`, printing confirmation that normal traffic has resumed.

```
--- call 1 ---
[proxy] call failed (1/3 consecutive failures)
[app] received error: downstream is down
--- call 2 ---
[proxy] call failed (2/3 consecutive failures)
[app] received error: downstream is down
--- call 3 ---
[proxy] call failed (3/3 consecutive failures)
[proxy] threshold reached -- circuit OPENED, further calls rejected immediately
[app] received error: downstream is down
--- call 4 ---
[proxy] circuit OPEN -- REJECTING immediately, not even attempting the call
[app] received error: circuit breaker open, failing fast
--- call 5 ---
[proxy] circuit OPEN -- REJECTING immediately, not even attempting the call
[app] received error: circuit breaker open, failing fast

[recovery] downstream comes back healthy, cooldown elapses -- breaker allows a trial call
[proxy] trial call succeeded -- circuit CLOSED, resuming normal traffic
[app] received: success
```

## 7. Gotchas & takeaways

> Retrying every kind of failure indiscriminately — including failures caused by the *caller's own* malformed request, not a transient downstream issue — wastes resources retrying something that will never succeed. Configure retries to trigger only on genuinely retryable conditions (timeouts, connection failures, specific 5xx codes), never on 4xx client errors.
- Retries, timeouts, and circuit breaking are complementary, not redundant — timeouts bound how long any single attempt can take, retries handle transient failures, and circuit breaking protects against sustained failures that retrying alone would just keep hammering.
- Circuit breaking's fail-fast behavior protects two parties at once: the struggling downstream (no pile of doomed requests adding to its load) and the caller (an instant, clear failure instead of a long wait for something that was going to fail anyway).
- Mesh-level resiliency doesn't eliminate the need for application-level thinking entirely — a circuit breaker rejecting a call still needs the calling application to have a sensible response to that rejection (a cached fallback, a graceful error to the end user).
- Compare this against [library-based resiliency](0484-service-mesh-vs-library-based-resiliency-resilience4j.md) for your specific system — the mesh approach shines in polyglot environments with many services sharing policy; a single-language system might reasonably prefer the tighter integration a language-specific library offers.
