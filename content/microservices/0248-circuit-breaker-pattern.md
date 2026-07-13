---
card: microservices
gi: 248
slug: circuit-breaker-pattern
title: "Circuit breaker pattern"
---

## 1. What it is

A circuit breaker is a resilience mechanism, named by analogy to an electrical circuit breaker, that monitors calls to a dependency and, once failures cross a defined threshold, "trips" — stopping further calls to that dependency immediately (returning a fallback instead) rather than continuing to call a dependency that's clearly failing, giving the failing dependency room to recover and protecting the caller from wasting resources on calls almost certain to fail anyway.

## 2. Why & when

Without a circuit breaker, a caller facing a genuinely failing dependency keeps calling it on every single incoming request, each call wasting time (waiting for a timeout), threads, and connections on an operation that's very likely to fail again — this is precisely the resource-accumulation mechanism behind [cascading failures](0243-cascading-failures.md). A circuit breaker interrupts this by tracking recent call outcomes and, once the failure rate crosses a threshold, switching to immediately rejecting calls (returning a fallback) instead of attempting them — protecting the caller's own resources and, just as importantly, reducing load on the already-struggling dependency, giving it a better chance to recover instead of being hit with continued traffic while it's down.

Apply a circuit breaker to any call to an external dependency where a sustained failure is plausible and where failing fast with a fallback is preferable to repeatedly attempting (and waiting out) calls very likely to fail. It's especially valuable for dependencies whose failures are slow (timeouts) rather than fast (immediate connection refusal), since slow failures are what accumulate the most resource cost per failed call.

## 3. Core concept

A circuit breaker tracks recent call outcomes in a sliding window and moves through distinct states based on that tracked failure rate — covered by name in [closed/open/half-open states](0249-closed-open-half-open-states.md) — but at its core, it wraps a call with a check: if the dependency has been failing too much recently, skip the call entirely and use a fallback instead.

```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50) // trip once 50% of recent calls have failed
    .slidingWindowSize(10)    // "recent" means the last 10 calls
    .waitDurationInOpenState(Duration.ofSeconds(30)) // stay tripped for 30s before testing recovery
    .build();
CircuitBreaker breaker = CircuitBreaker.of("inventory-service", config);

String result = breaker.executeSupplier(() -> inventoryService.checkStock(productId));
// if the FAILURE RATE is too high, this call is SKIPPED entirely -- an exception is thrown IMMEDIATELY, no call attempted
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calls pass through a circuit breaker that tracks recent outcomes; while the failure rate stays under threshold, calls proceed normally to the dependency, but once the threshold is crossed, the breaker trips and every subsequent call is rejected immediately with a fallback, without reaching the dependency at all" >
  <rect x="20" y="65" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caller</text>

  <rect x="230" y="55" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Circuit breaker</text>
  <text x="320" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">tracks recent outcomes</text>

  <rect x="490" y="20" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Dependency (if OK)</text>

  <rect x="490" y="110" width="130" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="555" y="135" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Fallback (if tripped)</text>

  <line x1="140" y1="85" x2="228" y2="85" stroke="#8b949e" marker-end="url(#arr248)"/>
  <line x1="410" y1="72" x2="488" y2="42" stroke="#8b949e" marker-end="url(#arr248)"/>
  <line x1="410" y1="98" x2="488" y2="128" stroke="#8b949e" marker-end="url(#arr248)"/>

  <defs>
    <marker id="arr248" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The breaker decides, based on recent history, whether a call actually reaches the dependency or is redirected to a fallback instantly.

## 5. Runnable example

Scenario: a dependency-calling client with no protection (repeatedly hitting a failing dependency, wasting time on every call), refactored to add a simple circuit breaker that trips after a failure threshold and immediately rejects further calls, and finally demonstrating the measured time savings across a sustained failure period compared to the unprotected version — the concrete payoff a circuit breaker provides.

### Level 1 — Basic

```java
// File: NoCircuitBreaker.java -- EVERY call attempts the dependency
// directly, even though it's CONSISTENTLY failing -- wasting time on
// every single attempt.
public class NoCircuitBreaker {
    static String callFailingDependency() throws InterruptedException {
        Thread.sleep(200); // simulates the COST of attempting a call that will fail
        throw new RuntimeException("dependency unavailable");
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        int failures = 0;
        for (int i = 1; i <= 6; i++) {
            try { callFailingDependency(); }
            catch (RuntimeException e) { failures++; }
        }
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(failures + " failures out of 6 attempts, took " + elapsed + "ms total -- EVERY call paid the full cost.");
    }
}
```

**How to run:** `javac NoCircuitBreaker.java && java NoCircuitBreaker` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SimpleCircuitBreaker.java -- a MINIMAL circuit breaker: trips
// after a failure threshold, then REJECTS immediately without attempting
// the call at all.
public class SimpleCircuitBreaker {
    static boolean breakerOpen = false;
    static int consecutiveFailures = 0;
    static final int FAILURE_THRESHOLD = 3;

    static String callFailingDependency() throws InterruptedException {
        Thread.sleep(200);
        throw new RuntimeException("dependency unavailable");
    }

    static String protectedCall() throws InterruptedException {
        if (breakerOpen) throw new RuntimeException("circuit open -- rejected immediately, no call attempted"); // FAST rejection

        try {
            return callFailingDependency();
        } catch (RuntimeException e) {
            if (++consecutiveFailures >= FAILURE_THRESHOLD) {
                breakerOpen = true;
                System.out.println("  [breaker] TRIPPED after " + FAILURE_THRESHOLD + " consecutive failures");
            }
            throw e;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        int failures = 0;
        for (int i = 1; i <= 6; i++) {
            try { protectedCall(); }
            catch (RuntimeException e) { failures++; }
        }
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(failures + " failures out of 6 attempts, took " + elapsed + "ms total -- calls 4-6 were REJECTED instantly.");
    }
}
```

**How to run:** `javac SimpleCircuitBreaker.java && java SimpleCircuitBreaker` (JDK 17+).

Expected output (timing approximate):
```
  [breaker] TRIPPED after 3 consecutive failures
6 failures out of 6 attempts, took 600ms total -- calls 4-6 were REJECTED instantly.
```

### Level 3 — Advanced

```java
// File: MeasuredSavingsUnderSustainedFailure.java -- runs BOTH the
// unprotected and the circuit-breaker-protected version over the SAME
// number of attempts, measuring and comparing the ACTUAL time cost.
public class MeasuredSavingsUnderSustainedFailure {
    static String callFailingDependency() throws InterruptedException {
        Thread.sleep(200);
        throw new RuntimeException("dependency unavailable");
    }

    static long runUnprotected(int attempts) throws InterruptedException {
        long start = System.currentTimeMillis();
        for (int i = 0; i < attempts; i++) {
            try { callFailingDependency(); } catch (RuntimeException ignored) {}
        }
        return System.currentTimeMillis() - start;
    }

    static long runProtected(int attempts) throws InterruptedException {
        boolean[] breakerOpen = {false};
        int[] consecutiveFailures = {0};
        int threshold = 3;

        long start = System.currentTimeMillis();
        for (int i = 0; i < attempts; i++) {
            if (breakerOpen[0]) continue; // REJECTED instantly -- no time spent
            try { callFailingDependency(); }
            catch (RuntimeException e) {
                if (++consecutiveFailures[0] >= threshold) breakerOpen[0] = true;
            }
        }
        return System.currentTimeMillis() - start;
    }

    public static void main(String[] args) throws InterruptedException {
        int attempts = 10;
        long unprotectedTime = runUnprotected(attempts);
        long protectedTime = runProtected(attempts);

        System.out.println("Unprotected: " + attempts + " attempts took " + unprotectedTime + "ms");
        System.out.println("Circuit-breaker-protected: " + attempts + " attempts took " + protectedTime + "ms");
        double savingsPercent = 100.0 * (unprotectedTime - protectedTime) / unprotectedTime;
        System.out.printf("Savings: %.0f%% less time spent, for the IDENTICAL number of logical attempts.%n", savingsPercent);
    }
}
```

**How to run:** `javac MeasuredSavingsUnderSustainedFailure.java && java MeasuredSavingsUnderSustainedFailure` (JDK 17+).

Expected output (approximate, timing-dependent):
```
Unprotected: 10 attempts took 2000ms
Circuit-breaker-protected: 10 attempts took 600ms
Savings: 70% less time spent, for the IDENTICAL number of logical attempts.
```

## 6. Walkthrough

1. **Level 1, paying full cost every time** — `callFailingDependency` sleeps 200ms before throwing on *every single call*, and `main`'s loop calls it six times unconditionally, meaning the total elapsed time is close to 6 × 200ms = 1200ms, with every one of those milliseconds spent on a call that had no realistic chance of succeeding, given the dependency's consistent failure.
2. **Level 2, tracking failures toward a threshold** — `protectedCall` increments `consecutiveFailures` on each caught exception, and once that count reaches `FAILURE_THRESHOLD` (3), it sets `breakerOpen` to `true`; from that point forward, the very first check inside `protectedCall` (`if (breakerOpen)`) causes an immediate rejection without ever calling `callFailingDependency` again.
3. **Level 2, the measured effect** — the total elapsed time for six attempts drops from Level 1's roughly 1200ms to roughly 600ms, since only the first three calls actually pay the 200ms cost; the remaining three are rejected essentially instantly, once the breaker has tripped.
4. **Level 3, running both versions for direct comparison** — `runUnprotected` and `runProtected` both attempt the identical number of logical calls (`attempts = 10`) against the identical failing dependency, differing only in whether circuit-breaker logic is applied; this side-by-side structure isolates the circuit breaker's actual contribution rather than relying on separately-run, less comparable measurements.
5. **Level 3, the growing gap as attempts increase** — with 10 attempts instead of Level 2's 6, the unprotected version pays the full 200ms cost all 10 times (2000ms total), while the protected version pays it only for the first 3 (until the breaker trips) and rejects the remaining 7 essentially free — the savings gap widens as more attempts occur while the dependency remains down, which is exactly the scenario (a sustained outage) where a circuit breaker provides the most value.
6. **Level 3, interpreting the computed savings percentage** — the printed savings percentage (roughly 70% in this example) quantifies concretely what "protecting the caller's resources" actually means in practice: not just avoiding a philosophical risk, but measurably reducing the real time and resource cost paid across a sustained dependency outage, precisely because most of the ten attempts never need to reach (or wait on) the failing dependency at all once the breaker has tripped.

## 7. Gotchas & takeaways

> **Gotcha:** a circuit breaker that never re-attempts the dependency once tripped would keep every future call permanently failing via fallback, even long after the dependency has actually recovered — real circuit breakers solve this by periodically allowing a small number of test calls through after a wait period, covered by name in [closed/open/half-open states](0249-closed-open-half-open-states.md); a breaker without this recovery-testing behavior is only half the pattern.

- A circuit breaker tracks recent call outcomes to a dependency and, once a failure threshold is crossed, stops attempting further calls and returns a fallback immediately instead.
- This protects the caller from wasting resources on calls very likely to fail, and reduces load on the already-struggling dependency, giving it room to recover.
- The value is largest for dependencies whose failures are slow (timeouts) rather than instantaneous, since slow failures accumulate the most wasted resource cost per attempt.
- A circuit breaker is most valuable during a *sustained* failure period — the longer a dependency stays down, the more calls the breaker prevents from paying the full failure cost.
- A complete circuit breaker implementation must also periodically re-test the dependency to detect recovery, not just trip and stay tripped forever — this recovery mechanism is what the closed/open/half-open state machine, covered next, formalizes.
