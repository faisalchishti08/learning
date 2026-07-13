---
card: microservices
gi: 421
slug: chaos-resiliency-testing
title: "Chaos / resiliency testing"
---

## 1. What it is

**Chaos testing** (also called chaos engineering) is the practice of deliberately injecting failure into a running system — killing an instance, adding network latency, dropping a connection, saturating CPU — to verify that the resiliency mechanisms you've built (timeouts, retries, circuit breakers, bulkheads, fallbacks) actually work under real failure conditions, instead of trusting that they work because the code looks right. It's the experimental counterpart to writing resiliency patterns: you don't just implement a [circuit breaker](0248-circuit-breaker-pattern.md) and assume it does its job — you actually make a dependency fail and watch whether the circuit breaker opens the way it's supposed to.

## 2. Why & when

You reach for chaos testing once a system has enough resiliency mechanisms in place that it's worth asking, honestly: do they actually work, together, under real conditions? This matters because resiliency code is exactly the kind of code that's hardest to verify with ordinary tests:

- **The failure paths are the least-exercised paths in production.** A service might run for months with every dependency healthy, meaning its timeout logic, retry logic, and fallback logic never actually execute for real — the first time they run "for real" might be during an actual incident, which is the worst possible time to discover a bug in your safety net.
- **Resiliency mechanisms interact, and the interactions are where bugs hide.** A retry that fires *inside* a circuit breaker's open state, or a timeout that's longer than an upstream caller's own timeout (causing wasted work on both ends), or a bulkhead sized too small for a legitimate traffic spike — these problems only show up when the mechanisms are exercised together, under realistic failure, not when each is unit tested in isolation.
- **Distributed systems fail in combinations, not one at a time.** A real incident is rarely "one service is down" — it's more often "one service is slow, which fills up a thread pool in a caller, which makes the caller slow, which cascades." Chaos testing that only ever kills one thing at a time misses this whole class of cascading failure.
- **It builds real confidence, replacing hope with evidence.** "We have a circuit breaker configured" is a claim; "we killed the dependency and watched the circuit breaker open within 3 seconds and the fallback serve stale data correctly" is evidence.

You start small and controlled — a single experiment in a non-production environment, or a tightly scoped experiment in production with an immediate abort mechanism — and only expand scope (more failure types, more of production, less advance warning) as confidence in both the system and the team's ability to respond grows.

## 3. Core concept

Picture a fire drill. You don't wait for a real fire to find out whether the emergency exits are unlocked, whether the alarm is loud enough, or whether people actually know where to go — you deliberately, safely simulate the emergency in advance, observe what actually happens, and fix whatever the drill reveals before a real fire makes the same gap matter. Chaos testing is a fire drill for distributed-system failure: you don't wait for a real outage to discover a circuit breaker was misconfigured — you cause a small, controlled, contained "fire" and watch whether your safety systems respond correctly.

A disciplined chaos experiment has four steps:

1. **Define a steady state** — a measurable signal that the system is healthy: request success rate, p99 latency, throughput. Without this, you have no way to tell whether your injected failure actually caused a problem.
2. **Form a hypothesis** — a specific, falsifiable claim: "if `PaymentService` becomes unavailable, `OrderService`'s circuit breaker will open within 5 seconds and checkout requests will get a fast, graceful fallback response instead of timing out slowly."
3. **Inject the failure, scoped and reversible** — kill an instance, inject latency, drop a percentage of packets, exhaust a resource — always with a clear way to stop the experiment immediately if things go worse than expected.
4. **Observe and compare against the hypothesis** — did the steady-state signal hold? Did the resiliency mechanism behave as claimed? If not, that's a real gap, found deliberately, on your own schedule, instead of during a real incident.

Common failure types to inject, roughly from safest/most contained to riskiest:

- **Latency injection** — make a dependency slower, testing timeout configuration.
- **Error injection** — make a dependency return errors, testing retry and fallback logic.
- **Instance termination** — kill a process or container, testing load-balancer health checks and failover.
- **Resource exhaustion** — saturate CPU, memory, or a connection pool, testing bulkhead isolation.
- **Network partition** — cut connectivity between specific services, testing how the system behaves when parts of it can't reach each other at all.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chaos experiment measures a steady-state health signal, injects a scoped failure into one dependency, and checks whether the resiliency mechanism -- such as a circuit breaker -- responds as hypothesized, keeping the overall system healthy despite the injected failure" font-family="sans-serif">
  <rect x="30" y="90" width="120" height="60" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="115" fill="#e6edf3" font-size="10" text-anchor="middle">OrderService</text>
  <text x="90" y="132" fill="#8b949e" font-size="9" text-anchor="middle">circuit breaker</text>

  <line x1="150" y1="120" x2="230" y2="120" stroke="#f85149" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="190" y="108" fill="#f85149" font-size="9" text-anchor="middle">injected failure</text>

  <rect x="230" y="90" width="130" height="60" rx="10" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="295" y="115" fill="#f85149" font-size="10" text-anchor="middle">PaymentService</text>
  <text x="295" y="132" fill="#8b949e" font-size="9" text-anchor="middle">chaos: killed / slow</text>

  <rect x="420" y="60" width="190" height="120" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="515" y="82" fill="#e6edf3" font-size="10" text-anchor="middle">Observation</text>
  <text x="515" y="102" fill="#79c0ff" font-size="9" text-anchor="middle">did circuit breaker open?</text>
  <text x="515" y="118" fill="#79c0ff" font-size="9" text-anchor="middle">did fallback serve gracefully?</text>
  <text x="515" y="134" fill="#79c0ff" font-size="9" text-anchor="middle">did steady-state metric hold?</text>
  <text x="515" y="155" fill="#6db33f" font-size="9" text-anchor="middle">evidence, not assumption</text>

  <line x1="90" y1="150" x2="90" y2="200" stroke="#8b949e" stroke-dasharray="2,3"/>
  <text x="90" y="215" fill="#8b949e" font-size="9" text-anchor="middle">steady-state metric watched throughout</text>
</svg>

A chaos experiment injects a scoped, reversible failure into one dependency while watching whether the resiliency mechanism responds as hypothesized and the overall system stays healthy.

## 5. Runnable example

Scenario: `OrderService` calls `PaymentService` through a simple circuit breaker. We run a chaos experiment in three stages: first establishing a steady-state baseline, then injecting a failure and observing the circuit breaker's response, then a harder case — injecting *partial* degradation (intermittent failures) that a naive breaker configuration handles poorly, revealing a real gap.

### Level 1 — Basic

```java
// File: ChaosSteadyStateBaseline.java -- establish a STEADY-STATE baseline
// BEFORE injecting any failure, so later stages have something concrete to
// compare against -- the essential first step of a real chaos experiment.
public class ChaosSteadyStateBaseline {
    static boolean paymentServiceHealthy = true; // the chaos "knob" we'll flip in later stages

    static boolean callPaymentService() {
        return paymentServiceHealthy;
    }

    public static void main(String[] args) {
        int successCount = 0;
        int totalCalls = 50;
        for (int i = 0; i < totalCalls; i++) {
            if (callPaymentService()) successCount++;
        }
        double successRate = (double) successCount / totalCalls;
        System.out.println("Steady-state baseline: " + successCount + "/" + totalCalls
                + " succeeded (" + (successRate * 100) + "% success rate)");
        System.out.println("This is the healthy baseline we'll compare later chaos experiments against.");
    }
}
```

How to run: `java ChaosSteadyStateBaseline.java`

Before injecting any chaos, we measure the steady state: with `paymentServiceHealthy = true`, every call succeeds, giving a 100% baseline success rate. Without recording this number first, there'd be no way to say with confidence, later, "the injected failure caused a measurable degradation" versus "the system was already unreliable and we didn't notice."

### Level 2 — Intermediate

```java
// File: ChaosInjectTotalFailure.java -- the SAME setup, now with a
// CIRCUIT BREAKER protecting the call, and a chaos experiment that kills
// PaymentService entirely -- verifying the hypothesis: "the breaker opens
// and stops making real calls, instead of letting every request time out."
public class ChaosInjectTotalFailure {
    static boolean paymentServiceHealthy = true;

    static boolean callPaymentServiceRaw() {
        if (!paymentServiceHealthy) throw new RuntimeException("PaymentService unreachable (chaos injected)");
        return true;
    }

    // A simple circuit breaker: opens after 5 consecutive failures, stops
    // calling the real dependency while open, and fails fast instead.
    static class SimpleCircuitBreaker {
        private int consecutiveFailures = 0;
        private boolean open = false;
        private static final int FAILURE_THRESHOLD = 5;

        boolean call() {
            if (open) {
                return false; // fails fast, WITHOUT calling the real (broken) dependency
            }
            try {
                boolean result = callPaymentServiceRaw();
                consecutiveFailures = 0;
                return result;
            } catch (RuntimeException e) {
                consecutiveFailures++;
                if (consecutiveFailures >= FAILURE_THRESHOLD) {
                    open = true;
                    System.out.println("  [CircuitBreaker] OPENED after " + consecutiveFailures + " consecutive failures");
                }
                return false;
            }
        }
        boolean isOpen() { return open; }
    }

    public static void main(String[] args) {
        SimpleCircuitBreaker breaker = new SimpleCircuitBreaker();

        System.out.println("--- Injecting chaos: PaymentService goes down ---");
        paymentServiceHealthy = false;

        int realCallAttempts = 0;
        for (int i = 1; i <= 10; i++) {
            boolean wasOpenBefore = breaker.isOpen();
            boolean result = breaker.call();
            if (!wasOpenBefore) realCallAttempts++; // only counts calls that actually reached the "real" dependency
            System.out.println("call " + i + ": result=" + result + " breakerOpen=" + breaker.isOpen());
        }
        System.out.println("Real calls that actually reached the failing dependency: " + realCallAttempts + " out of 10");
        System.out.println("Hypothesis check: breaker opened and stopped hammering the dead dependency: " + breaker.isOpen());
    }
}
```

How to run: `java ChaosInjectTotalFailure.java`

`paymentServiceHealthy = false` is the chaos injection: a deliberate, scoped failure. `SimpleCircuitBreaker.call` wraps `callPaymentServiceRaw`, tracking consecutive failures and flipping `open = true` once the threshold is hit — after which further calls fail fast, without hitting the (already known-dead) real dependency again. `realCallAttempts` tracks how many of the 10 calls actually reached the failing dependency versus how many were short-circuited by the now-open breaker, making the hypothesis ("the breaker stops hammering a dead dependency") directly measurable rather than just assumed.

### Level 3 — Advanced

```java
// File: ChaosInjectPartialDegradation.java -- a HARDER, more realistic
// chaos experiment: PaymentService doesn't die completely, it becomes
// INTERMITTENTLY flaky (fails 40% of the time) -- exposing a real gap: a
// consecutive-failure-based breaker can flap open and closed under partial
// degradation instead of settling into a stable, protective state.
import java.util.*;

public class ChaosInjectPartialDegradation {
    static final Random random = new Random(42); // fixed seed for reproducible chaos
    static double failureRate = 0.0;

    static boolean callPaymentServiceRaw() {
        if (random.nextDouble() < failureRate) throw new RuntimeException("PaymentService intermittent failure (chaos injected)");
        return true;
    }

    static class SimpleCircuitBreaker {
        private int consecutiveFailures = 0;
        private boolean open = false;
        private static final int FAILURE_THRESHOLD = 5;

        boolean call() {
            if (open) return false;
            try {
                boolean result = callPaymentServiceRaw();
                consecutiveFailures = 0; // ANY success resets the counter to zero
                return result;
            } catch (RuntimeException e) {
                consecutiveFailures++;
                if (consecutiveFailures >= FAILURE_THRESHOLD) open = true;
                return false;
            }
        }
        boolean isOpen() { return open; }
    }

    public static void main(String[] args) {
        SimpleCircuitBreaker breaker = new SimpleCircuitBreaker();

        System.out.println("--- Injecting chaos: PaymentService becomes 40% flaky (not fully down) ---");
        failureRate = 0.40;

        int failedCalls = 0;
        int totalCalls = 100;
        for (int i = 1; i <= totalCalls; i++) {
            boolean result = breaker.call();
            if (!result) failedCalls++;
        }

        double effectiveFailureRate = (double) failedCalls / totalCalls;
        System.out.println("Total calls: " + totalCalls + ", failed (from caller's perspective): " + failedCalls
                + " (" + (effectiveFailureRate * 100) + "%)");
        System.out.println("Breaker ended in OPEN state: " + breaker.isOpen());
        System.out.println("GAP FOUND: a consecutive-failure counter that resets on ANY success rarely reaches "
                + "the threshold under intermittent (not total) failure, so the breaker may never open, "
                + "and " + (effectiveFailureRate * 100) + "% of real calls keep hitting the degraded dependency "
                + "instead of failing fast -- this is exactly the kind of gap chaos testing exists to surface.");
    }
}
```

How to run: `java ChaosInjectPartialDegradation.java`

This is the payoff of chaos testing beyond the obvious "kill it entirely" case: with `failureRate = 0.40`, the dependency fails a meaningful chunk of the time but also succeeds often enough that `consecutiveFailures` keeps getting reset to zero by an intervening success before it ever reaches `FAILURE_THRESHOLD` (5). The result is a circuit breaker that, under this specific and realistic failure pattern, may *never open* — meaning roughly 40% of real calls keep reaching a genuinely degraded dependency indefinitely, with no fast-fail protection kicking in. A team that only ever tested "kill the dependency completely" would never have found this — the total-outage case is exactly the one a simple consecutive-failure breaker handles well; it's the partial, intermittent degradation (arguably the more common real-world failure mode) that exposes the gap.

## 6. Walkthrough

Trace `ChaosInjectPartialDegradation.main`. **First**, `failureRate` is set to `0.40`, injecting the chaos condition: any given call to `callPaymentServiceRaw` now has a 40% chance of throwing. **Next**, the loop runs `breaker.call()` 100 times. Consider a representative stretch of calls: suppose calls 1-3 succeed (`consecutiveFailures` stays at 0 after each), call 4 fails (`consecutiveFailures` becomes 1), call 5 succeeds (`consecutiveFailures` resets to 0 in the `try` block before the exception path is even reached), call 6 fails (`consecutiveFailures` becomes 1 again), and so on — because `consecutiveFailures = 0` runs on *every* success, a string of failures needs to happen with no intervening success to ever reach 5 in a row, and at a 40% failure rate that specific run of bad luck is statistically uncommon across many calls, though not impossible.

**Then**, the loop finishes all 100 calls, having tallied `failedCalls` (calls where `breaker.call()` returned `false`, whether from a real failure or a short-circuited open breaker) and leaving `breaker.isOpen()` in whatever state the last threshold check produced. With the fixed random seed (`new Random(42)`), this run is fully reproducible, but the underlying finding holds broadly: the *effective* failure rate the caller experiences (`failedCalls / totalCalls`) tracks close to the injected 40%, largely undamped by the breaker, because the breaker's consecutive-failure design isn't well matched to *intermittent* failure — it's designed to catch a dependency that's *sustained-down*, not one that's *statistically degraded*.

**Finally**, `main` prints the effective failure rate and the breaker's final state, followed by an explicit statement of the gap this experiment revealed: a consecutive-failure-count breaker configuration is often the wrong tool for a partially degraded dependency, and a real system would need a different strategy — such as tracking a rolling failure-rate window over a fixed number of recent calls (which is exactly how production-grade circuit breaker libraries like Resilience4j are typically configured, rather than a bare consecutive-failure counter) to catch this failure mode.

```
--- Injecting chaos: PaymentService becomes 40% flaky (not fully down) ---
Total calls: 100, failed (from caller's perspective): 41 (41.0%)
Breaker ended in OPEN state: false
GAP FOUND: a consecutive-failure counter that resets on ANY success rarely reaches the threshold under
intermittent (not total) failure, so the breaker may never open, and 41.0% of real calls keep hitting the
degraded dependency instead of failing fast -- this is exactly the kind of gap chaos testing exists to surface.
```

## 7. Gotchas & takeaways

> Running chaos experiments only against total outages ("kill the service and see what happens") gives false confidence, because total outages are often the *easiest* failure mode to protect against — a health check and a load balancer catch most of it. The harder, more common real-world failures — a dependency that's slow but not dead, or flaky but not fully down — are exactly what Level 3 above demonstrates a naive breaker configuration can miss entirely. Vary the failure type and severity, not just whether something is fully up or fully down.

- Always establish a measurable steady-state baseline before injecting failure, or you have no way to tell whether an observed problem was caused by your experiment or was already there.
- Start chaos experiments small, scoped, and reversible — a single dependency, a short duration, an immediate abort switch — before expanding scope or moving experiments closer to production.
- Chaos testing verifies resiliency patterns like [circuit breakers](0248-circuit-breaker-pattern.md), [retries](0259-retry-pattern.md), [bulkheads](0267-bulkhead-pattern.md), and [timeouts](0280-timeout-pattern-timelimiter.md) actually behave as configured under real failure — it's the experimental verification layer sitting on top of resiliency code that would otherwise only be trusted by inspection.
- Partial, intermittent degradation is often harder to defend against than total outage, and is arguably more common in real production incidents — make sure your chaos experiments cover it, not just the "kill it" case.
- Chaos testing complements, and comes after, the earlier layers of the [test pyramid](0411-test-pyramid-for-microservices.md) — it's specifically about verifying behavior under real, injected failure conditions that unit and integration tests don't naturally exercise.
