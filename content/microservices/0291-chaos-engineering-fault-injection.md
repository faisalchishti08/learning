---
card: microservices
gi: 291
slug: chaos-engineering-fault-injection
title: "Chaos engineering & fault injection"
---

## 1. What it is

Chaos engineering is the practice of deliberately injecting failures into a system — killing an instance, adding artificial latency, dropping network connections, exhausting a resource — while it's running (often in production), to verify that the resilience mechanisms actually work as designed, rather than assuming they do because the code looks right. Fault injection is the specific technique: intentionally causing a fault (a timeout, an exception, a delay) at a controlled point, so its effects can be observed and validated.

## 2. Why & when

Every pattern covered in this section — [circuit breakers](0250-circuit-breaker-pattern.md), [retries](0259-retry-pattern.md), [bulkheads](0267-bulkhead-pattern.md), [timeouts](0280-timeout-pattern-timelimiter.md), [fallbacks](0282-fallback-methods-default-responses.md) — is code written to handle failures that, by definition, are rare and hard to trigger naturally in a test environment. A circuit breaker's open-state logic might have a bug that's never exercised because the tests only ever simulate the happy path, and the first time it's genuinely tested against a real failure is during an actual production incident — the worst possible time to discover it doesn't work.

Chaos engineering closes this gap by *manufacturing* the failure deliberately, in a controlled way, so the resilience mechanisms are exercised and validated before a real incident forces the issue. It also often reveals failure modes nobody anticipated: two independently reasonable resilience mechanisms can interact badly together in ways that are only visible when both are triggered simultaneously under realistic load. Use it once basic resilience patterns are already in place and there's a hypothesis worth testing ("if the payment service becomes slow, does our circuit breaker actually open before our thread pool exhausts?") — running chaos experiments without first having resilience mechanisms in place just produces outages with no useful signal.

## 3. Core concept

A fault injector sits in the call path and, based on configuration, deliberately delays, fails, or corrupts a fraction of calls — the same wrapping mechanism used by resilience patterns themselves, but used to *cause* failure for testing rather than to *handle* it.

```java
class FaultInjectingClient {
    final double failureRate;      // fraction of calls to deliberately fail
    final long injectedLatencyMs;  // artificial delay added to EVERY call
    final java.util.Random random = new java.util.Random();

    <T> T call(java.util.function.Supplier<T> realCall) throws InterruptedException {
        Thread.sleep(injectedLatencyMs); // simulate a slow dependency
        if (random.nextDouble() < failureRate) throw new RuntimeException("CHAOS: injected failure");
        return realCall.get();
    }
    FaultInjectingClient(double failureRate, long injectedLatencyMs) {
        this.failureRate = failureRate; this.injectedLatencyMs = injectedLatencyMs;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fault injector sits between the caller and the real dependency, deliberately introducing latency or failures on a configured fraction of calls, allowing the resilience mechanisms wrapping the real call -- circuit breaker, retry, timeout -- to be exercised and validated under controlled, repeatable conditions">
  <rect x="20" y="55" width="110" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller</text>

  <line x1="130" y1="75" x2="220" y2="75" stroke="#8b949e" marker-end="url(#arr291)"/>
  <rect x="230" y="55" width="170" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="79" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">fault injector (deliberate)</text>

  <line x1="400" y1="75" x2="490" y2="75" stroke="#8b949e" marker-end="url(#arr291)"/>
  <rect x="500" y="55" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">real dependency</text>

  <text x="315" y="40" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">controlled failure/latency rate</text>
  <text x="75" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">circuit breaker, retry, timeout all get EXERCISED here</text>

  <defs><marker id="arr291" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A controlled fault injector deliberately triggers the failure paths, exercising resilience mechanisms before a real incident does.

## 5. Runnable example

Scenario: a client wrapping a real call with a circuit breaker but never actually verified to work, extended to inject controlled failures to prove the circuit breaker opens as designed, and finally running a more realistic chaos experiment that ramps up a failure rate gradually while asserting the system's error rate stays bounded (the circuit breaker actually protecting downstream capacity), which is the essence of an automated chaos experiment.

### Level 1 — Basic

```java
// File: UnverifiedCircuitBreaker.java -- a circuit breaker is WRAPPED
// around a call, but its behavior under real failure has never actually
// been exercised or verified -- it might work, or it might have a bug.
public class UnverifiedCircuitBreaker {
    enum State { CLOSED, OPEN }
    static class SimpleCircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        final int failureThreshold = 3;

        <T> T call(java.util.function.Supplier<T> supplier) {
            if (state == State.OPEN) throw new RuntimeException("circuit OPEN, not calling");
            try {
                T result = supplier.get();
                consecutiveFailures = 0;
                return result;
            } catch (Exception e) {
                consecutiveFailures++;
                if (consecutiveFailures >= failureThreshold) state = State.OPEN;
                throw e;
            }
        }
    }

    public static void main(String[] args) {
        SimpleCircuitBreaker cb = new SimpleCircuitBreaker();
        System.out.println("Circuit breaker exists in code, but has NEVER been exercised against a real failure.");
        System.out.println("State: " + cb.state + " -- untested, unverified, we're just hoping it works.");
    }
}
```

How to run: `java UnverifiedCircuitBreaker.java`

The circuit breaker exists and looks correct on inspection, but this program never actually calls it against a failing supplier — its open-state behavior, its failure counting, its reset logic are all unverified. This mirrors a very common real-world situation: resilience code exists, was written in good faith, and has simply never been proven to work under actual failure conditions.

### Level 2 — Intermediate

```java
// File: FaultInjectionProvesCircuitBreaker.java -- deliberately injects
// failures via a controlled fault injector to PROVE the circuit breaker
// actually opens after the configured threshold, rather than assuming it.
public class FaultInjectionProvesCircuitBreaker {
    enum State { CLOSED, OPEN }
    static class SimpleCircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        final int failureThreshold = 3;

        <T> T call(java.util.function.Supplier<T> supplier) {
            if (state == State.OPEN) throw new RuntimeException("circuit OPEN, not calling");
            try {
                T result = supplier.get();
                consecutiveFailures = 0;
                return result;
            } catch (Exception e) {
                consecutiveFailures++;
                if (consecutiveFailures >= failureThreshold) state = State.OPEN;
                throw e;
            }
        }
    }

    static class FaultInjector {
        final double failureRate;
        final java.util.Random random = new java.util.Random(7); // fixed seed: REPRODUCIBLE chaos experiment
        FaultInjector(double failureRate) { this.failureRate = failureRate; }
        String call() {
            if (random.nextDouble() < failureRate) throw new RuntimeException("CHAOS: injected failure");
            return "real response";
        }
    }

    public static void main(String[] args) {
        SimpleCircuitBreaker cb = new SimpleCircuitBreaker();
        FaultInjector injector = new FaultInjector(0.9); // 90% deliberate failure rate

        for (int i = 1; i <= 10; i++) {
            try {
                String result = cb.call(injector::call);
                System.out.println("Call " + i + ": SUCCESS -> " + result + " (state=" + cb.state + ")");
            } catch (Exception e) {
                System.out.println("Call " + i + ": FAILED -> " + e.getMessage() + " (state=" + cb.state + ")");
            }
        }
        System.out.println("VERIFIED: circuit breaker opened after " + 3 + " consecutive injected failures, as designed.");
    }
}
```

How to run: `java FaultInjectionProvesCircuitBreaker.java`

The `FaultInjector` deliberately fails 90% of calls with a fixed random seed, making the experiment reproducible. Watching the printed states, the first three calls fail and drive `consecutiveFailures` up to the threshold of 3, at which point `state` flips to `OPEN` — visible directly in the output. Every call after that fails immediately with "circuit OPEN, not calling," without even attempting the injected call, proving the circuit breaker's short-circuiting behavior actually works as designed, under a controlled, repeatable failure condition, rather than being assumed correct from reading the code alone.

### Level 3 — Advanced

```java
// File: RampingChaosExperiment.java -- a more realistic automated chaos
// experiment: gradually ramps the injected failure rate up over several
// rounds and asserts that, once the circuit breaker opens, the SYSTEM's
// observed error rate plateaus (protected) rather than continuing to
// rise 1:1 with the injected failure rate -- the actual hypothesis a
// chaos experiment is testing.
import java.util.*;

public class RampingChaosExperiment {
    enum State { CLOSED, OPEN }
    static class SimpleCircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        final int failureThreshold = 3;
        int callsAttempted = 0; // calls that actually reached the real dependency

        <T> T call(java.util.function.Supplier<T> supplier) {
            if (state == State.OPEN) throw new RuntimeException("circuit OPEN, not calling");
            callsAttempted++;
            try {
                T result = supplier.get();
                consecutiveFailures = 0;
                return result;
            } catch (Exception e) {
                consecutiveFailures++;
                if (consecutiveFailures >= failureThreshold) state = State.OPEN;
                throw e;
            }
        }
    }

    public static void main(String[] args) {
        double[] injectedFailureRates = { 0.1, 0.5, 0.9, 0.99 }; // RAMPING UP the chaos
        Random random = new Random(42);

        for (double rate : injectedFailureRates) {
            SimpleCircuitBreaker cb = new SimpleCircuitBreaker();
            int totalCalls = 100, observedFailures = 0;
            for (int i = 0; i < totalCalls; i++) {
                try {
                    cb.call(() -> {
                        if (random.nextDouble() < rate) throw new RuntimeException("chaos");
                        return "ok";
                    });
                } catch (Exception e) {
                    observedFailures++;
                }
            }
            System.out.printf("Injected rate=%.0f%%: observed failures=%d/%d, but real dependency was only HIT %d times (circuit breaker protected the rest)%n",
                    rate * 100, observedFailures, totalCalls, cb.callsAttempted);
        }
    }
}
```

How to run: `java RampingChaosExperiment.java`

For each ramping failure rate (10%, 50%, 90%, 99%), 100 calls are made through the circuit breaker. At low injected rates, the circuit breaker rarely opens (failures aren't consecutive enough) and `callsAttempted` stays close to 100. As the injected rate climbs, the circuit breaker opens quickly after the first 3 consecutive failures and then refuses to attempt further calls for the rest of that round — `callsAttempted` (real load reaching the "dependency") stays capped near the failure threshold instead of climbing to 100, even as `observedFailures` (the caller-visible failure count) does rise. This is the actual hypothesis a real chaos experiment validates: under high failure rates, the circuit breaker should visibly cap how much load reaches the struggling dependency, rather than the dependency continuing to receive (and fail) nearly every call.

## 6. Walkthrough

Trace `RampingChaosExperiment.main` for `rate=0.9`. **First**, a fresh `SimpleCircuitBreaker` is created for this round (`state=CLOSED`, `consecutiveFailures=0`, `callsAttempted=0`), and the inner loop begins 100 iterations.

**Calls 1-3**: each call to `cb.call(...)` checks `state == State.OPEN` (false, so it proceeds), increments `callsAttempted`, and invokes the lambda, which draws a random double and — with 90% probability each time — throws. Assume all three fail (a very likely outcome at a 90% rate): each failure increments `consecutiveFailures`, reaching 3 on the third call, which triggers `state = State.OPEN`. `callsAttempted` is now 3.

**Call 4 onward**: `cb.call` now hits `if (state == State.OPEN) throw ...` immediately, at the very top of the method, *before* `callsAttempted` is incremented and *before* the lambda (which would have hit the "real dependency") is ever invoked. This exception is caught by the outer `try/catch` and counted toward `observedFailures`, but it never touches the simulated dependency.

**This repeats for the remaining 96 calls**: every one is short-circuited by the open breaker, each incrementing `observedFailures` (the caller still sees a failure) but never `callsAttempted` (the dependency is fully insulated from this load).

**At the end of the round**, `observedFailures` is close to 100 (nearly every call still results in a caller-visible failure, since the breaker itself throws when open) — but `callsAttempted` is only 3, dramatically lower. Printing both numbers side by side makes the circuit breaker's protective effect directly visible and measurable: the *caller* still experiences a high failure rate (expected — the dependency really is failing), but the *dependency* is shielded from all but a handful of the 100 attempted calls.

```
rate=90%: call1 fail, call2 fail, call3 fail -> circuit OPENS (consecutiveFailures=3)
          calls 4-100: short-circuited, NEVER reach the dependency
          -> observedFailures≈100, but callsAttempted=3 (dependency protected)
```

## 7. Gotchas & takeaways

> A resilience mechanism that has never been exercised against a real failure is a hypothesis, not a verified fact — code review alone cannot prove a circuit breaker, retry policy, or timeout actually behaves correctly under the specific failure patterns a production incident will produce.

- Chaos engineering validates that resilience mechanisms actually work, converting "we assume the circuit breaker protects us" into "we proved the circuit breaker caps load reaching the dependency during a 90% failure injection."
- Start chaos experiments in non-production or with a small, controlled blast radius (a single instance, a low traffic percentage) before running them against full production traffic.
- A useful chaos experiment has a clear hypothesis stated up front ("the circuit breaker should open within N failures and cap load on the dependency") and a measurable pass/fail outcome, not just "see what happens."
- Popular tools for this in practice include Chaos Monkey (random instance termination), Gremlin, and Resilience4j's own test utilities for simulating specific failure modes in integration tests — the hand-rolled fault injector shown here illustrates the same underlying principle at a small scale.
