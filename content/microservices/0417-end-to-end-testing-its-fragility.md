---
card: microservices
gi: 417
slug: end-to-end-testing-its-fragility
title: "End-to-end testing & its fragility"
---

## 1. What it is

An **end-to-end (E2E) test** exercises a real user journey across a full, running system — multiple real services, a real database, a real broker, sometimes a real browser driving a real UI — checking that the pieces genuinely work together, not just in isolation. It sits at the very tip of the [test pyramid](0411-test-pyramid-for-microservices.md): the broadest possible scope, and deliberately the smallest number of tests, because that breadth comes at a steep cost in speed, infrastructure, and — the focus of this topic — **fragility**: end-to-end tests fail for reasons that have nothing to do with the code they're supposed to be testing far more often than any other layer.

## 2. Why & when

You write a small number of end-to-end tests to answer a question no lower layer can answer on its own: does the *whole system*, wired together for real, actually deliver the user-facing outcome it's supposed to? A perfect unit-test suite, a perfect integration-test suite, and a perfect set of passing contract tests can still add up to a broken checkout flow if, say, a network policy blocks one service from reaching another in the deployed environment, or a shared piece of configuration is wrong in a way no single service's tests would catch.

- **It's the only layer that proves real deployment topology works.** Service discovery, network policies, load balancer configuration, TLS between services — these only get exercised when real services actually run and actually talk to each other.
- **It validates the user's actual experience**, end to end, which matters most for the handful of flows where a real business consequence hinges on the whole chain working: checkout, signup, payment.
- **It should be small, not absent.** The [test pyramid](0411-test-pyramid-for-microservices.md)'s message isn't "skip end-to-end tests" — it's "have very few of them, covering only your most critical journeys," because everything they catch that lower layers miss is real and worth catching; the mistake is relying on them for *coverage* rather than for a final, thin confirmation.
- **You reach for them last, not first**, when adding test coverage for a new feature — write the unit, integration, component, and contract tests first, and add an end-to-end test only if there's a critical cross-service journey none of those layers can verify.

## 3. Core concept

Picture testing a relay race. A unit test checks each runner's individual sprint form in isolation. A component test checks that one runner, on a real track, runs their leg correctly when handed a baton under controlled conditions. An end-to-end test is running the *entire* relay for real, all four runners, all three handoffs, on race day — which is the only way to know the whole team actually wins, but is also the one test that can fail because of a gust of wind, a runner who tripped on an untied shoelace, or a delayed start, none of which say anything about whether any individual runner is actually fast.

That last point is the core of **fragility**: an end-to-end test has many more moving parts than any other layer, and each one is an independent chance for the test to fail for a reason unrelated to a real bug:

1. **Environmental flakiness** — a shared test environment that's slow, has stale data, or has another test's leftover state interfering.
2. **Timing and race conditions** — a UI test that clicks a button before an asynchronous call finishes, or a check that runs before an eventually-consistent read has caught up.
3. **Network flakiness** — a real HTTP call between real services in a real (if test) network can simply time out under load, unrelated to any actual defect.
4. **Test interdependence** — tests that share setup state can pass or fail based on execution order, making failures hard to reproduce locally.
5. **Long feedback loops** — when an end-to-end suite takes 30+ minutes, engineers stop trusting (and start ignoring) its failures, which defeats the entire purpose of having tests.

The mitigation strategy that experienced teams converge on is not "add more end-to-end tests to compensate for lower-layer gaps" — that makes fragility worse — but the opposite: keep the end-to-end layer thin, covering only the handful of journeys where a cross-service failure would be a genuine business emergency, and push everything else down into faster, more deterministic layers, including [contract tests](0415-contract-testing-consumer-driven-contracts.md) for cross-service compatibility specifically.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An end-to-end test runs a request through several real services, a real database, and a real broker; any one of these real dependencies failing for an unrelated reason makes the whole test fail, which is the source of its fragility">
  <rect x="30" y="90" width="90" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="75" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Gateway</text>
  <rect x="150" y="90" width="90" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="195" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Svc</text>
  <rect x="270" y="90" width="90" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="315" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Payment Svc</text>
  <rect x="390" y="90" width="90" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="435" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Inventory Svc</text>
  <rect x="510" y="90" width="100" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="560" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">real DB +</text>
  <text x="560" y="128" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">real broker</text>

  <line x1="120" y1="115" x2="150" y2="115" stroke="#79c0ff" stroke-width="2"/>
  <line x1="240" y1="115" x2="270" y2="115" stroke="#79c0ff" stroke-width="2"/>
  <line x1="360" y1="115" x2="390" y2="115" stroke="#79c0ff" stroke-width="2"/>
  <line x1="480" y1="115" x2="510" y2="115" stroke="#79c0ff" stroke-width="2"/>

  <text x="320" y="60" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">5 real hops -- ANY one flaking fails the whole test</text>
  <text x="320" y="180" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">a timeout, stale row, or slow network at ANY hop = a failing test, whether or not there's a real bug</text>
</svg>

Every additional real hop an end-to-end test crosses is another independent chance to fail for a reason unrelated to an actual defect.

## 5. Runnable example

Scenario: a checkout journey spanning three services (Order, Payment, Inventory). We simulate the happy path first, then introduce a realistic source of end-to-end flakiness (a transient timeout on one hop that isn't a real bug), then build a retry-and-diagnose strategy that distinguishes "the code is broken" from "the environment glitched" — the practical response to E2E fragility.

### Level 1 — Basic

```java
// File: CheckoutEndToEndHappyPath.java -- a simulated end-to-end journey:
// three "real" services called in sequence, each doing real work, exactly
// like an E2E test driving a real deployed system.
public class CheckoutEndToEndHappyPath {
    static boolean orderServiceValidate(String orderId) {
        System.out.println("[OrderService] validating " + orderId);
        return true;
    }
    static boolean paymentServiceCharge(String orderId) {
        System.out.println("[PaymentService] charging for " + orderId);
        return true;
    }
    static boolean inventoryServiceReserve(String orderId) {
        System.out.println("[InventoryService] reserving stock for " + orderId);
        return true;
    }

    static boolean runCheckoutJourney(String orderId) {
        return orderServiceValidate(orderId) && paymentServiceCharge(orderId) && inventoryServiceReserve(orderId);
    }

    public static void main(String[] args) {
        boolean succeeded = runCheckoutJourney("order-1");
        System.out.println("End-to-end checkout journey succeeded: " + succeeded);
    }
}
```

How to run: `java CheckoutEndToEndHappyPath.java`

`runCheckoutJourney` chains three real service calls in sequence, exactly the shape of a real E2E test driving a live checkout flow across three deployed services. On a good day, with every service healthy and every network hop fast, this is straightforward. The next level introduces what happens on a *typical* day, where one hop is momentarily slow for reasons unrelated to any bug.

### Level 2 — Intermediate

```java
// File: CheckoutEndToEndFlaky.java -- the SAME journey, now with a
// SIMULATED transient failure on one hop (standing in for a real network
// blip or a momentarily slow dependency) -- demonstrating how a single
// flaky hop fails the ENTIRE end-to-end test, even though nothing about
// the actual business logic is wrong.
import java.util.concurrent.atomic.AtomicInteger;

public class CheckoutEndToEndFlaky {
    // Simulates a real dependency that is occasionally slow/unavailable for
    // reasons that have nothing to do with a code defect (e.g. a cold start,
    // a GC pause, a transient network blip).
    static final AtomicInteger paymentCallCount = new AtomicInteger(0);

    static boolean orderServiceValidate(String orderId) {
        System.out.println("[OrderService] validating " + orderId);
        return true;
    }
    static boolean paymentServiceCharge(String orderId) {
        int attempt = paymentCallCount.incrementAndGet();
        if (attempt == 1) {
            System.out.println("[PaymentService] TRANSIENT FAILURE on attempt " + attempt + " (simulated network blip, not a real bug)");
            return false;
        }
        System.out.println("[PaymentService] charging for " + orderId + " (attempt " + attempt + ")");
        return true;
    }
    static boolean inventoryServiceReserve(String orderId) {
        System.out.println("[InventoryService] reserving stock for " + orderId);
        return true;
    }

    static boolean runCheckoutJourneyNoRetry(String orderId) {
        return orderServiceValidate(orderId) && paymentServiceCharge(orderId) && inventoryServiceReserve(orderId);
    }

    public static void main(String[] args) {
        boolean succeeded = runCheckoutJourneyNoRetry("order-1");
        System.out.println("End-to-end checkout journey succeeded: " + succeeded
                + " -- FAILED, but not because of a real defect in any service's logic.");
    }
}
```

How to run: `java CheckoutEndToEndFlaky.java`

`paymentServiceCharge` fails on its first invocation, simulating exactly the kind of transient issue that's common in real distributed systems — a cold JVM, a brief network blip, a load balancer still warming up — and has nothing to do with whether the payment logic is correct. Because `runCheckoutJourneyNoRetry` short-circuits on the first `false`, the entire journey is reported as failed, `inventoryServiceReserve` never even runs, and — critically — a human reading only "checkout E2E test failed" has no way to tell, from that signal alone, whether this is a real regression or an environmental blip. This is fragility in its purest form: one transient hop failure produces the same red build as a genuine bug.

### Level 3 — Advanced

```java
// File: CheckoutEndToEndRetryAndDiagnose.java -- the SAME journey, now with
// a PRODUCTION-FLAVORED mitigation: bounded retries for genuinely transient
// hops, PLUS a clear distinction in the failure report between "still
// failing after retries" (investigate as a real bug) and "succeeded after
// a retry" (log it as environmental flakiness, don't page anyone).
import java.util.concurrent.atomic.AtomicInteger;

public class CheckoutEndToEndRetryAndDiagnose {
    record HopResult(String hopName, boolean succeeded, int attemptsUsed) {}
    record JourneyReport(boolean overallSucceeded, java.util.List<HopResult> hops) {}

    static final AtomicInteger paymentCallCount = new AtomicInteger(0);

    static HopResult callWithRetry(String hopName, int maxAttempts, java.util.function.IntPredicate attemptSucceeds) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            if (attemptSucceeds.test(attempt)) {
                return new HopResult(hopName, true, attempt);
            }
            System.out.println("[" + hopName + "] attempt " + attempt + " failed, retrying...");
        }
        return new HopResult(hopName, false, maxAttempts);
    }

    static JourneyReport runCheckoutJourneyWithRetries(String orderId) {
        java.util.List<HopResult> hops = new java.util.ArrayList<>();

        HopResult order = callWithRetry("OrderService", 3, attempt -> true); // always succeeds
        hops.add(order);
        if (!order.succeeded()) return new JourneyReport(false, hops);

        HopResult payment = callWithRetry("PaymentService", 3, attempt -> {
            int callNum = paymentCallCount.incrementAndGet();
            return callNum > 1; // fails once, then succeeds -- a TRANSIENT issue
        });
        hops.add(payment);
        if (!payment.succeeded()) return new JourneyReport(false, hops);

        HopResult inventory = callWithRetry("InventoryService", 3, attempt -> true); // always succeeds
        hops.add(inventory);

        return new JourneyReport(inventory.succeeded(), hops);
    }

    public static void main(String[] args) {
        JourneyReport report = runCheckoutJourneyWithRetries("order-1");
        System.out.println("Overall succeeded: " + report.overallSucceeded());
        for (HopResult hop : report.hops()) {
            String verdict = hop.attemptsUsed() == 1 ? "clean" : "needed " + (hop.attemptsUsed() - 1) + " retr(y/ies) -- likely environmental, not a code bug";
            System.out.println("  " + hop.hopName() + ": succeeded=" + hop.succeeded() + " (" + verdict + ")");
        }
    }
}
```

How to run: `java CheckoutEndToEndRetryAndDiagnose.java`

`callWithRetry` gives each hop a small, bounded number of attempts before declaring it truly failed — this doesn't hide real bugs (a hop that fails on every attempt still fails the journey), but it stops a single transient blip from failing the whole test outright. Just as important is the diagnostic report: each `HopResult` records `attemptsUsed`, so the final output distinguishes a hop that succeeded cleanly from one that needed a retry — the latter is a signal worth tracking (if `PaymentService` needs a retry on every third E2E run, that's worth investigating as infrastructure flakiness) without it triggering an urgent "the checkout flow is broken" alarm on its own. This mirrors how mature E2E suites are actually run in production: bounded retries at the test-runner level, combined with flakiness dashboards that separate "genuinely broken" from "environmentally flaky," rather than treating every red run identically.

## 6. Walkthrough

Trace `CheckoutEndToEndRetryAndDiagnose.main` in order. **First**, `runCheckoutJourneyWithRetries("order-1")` calls `callWithRetry("OrderService", 3, attempt -> true)`. Since the predicate always returns `true`, attempt 1 succeeds immediately, producing `HopResult("OrderService", true, 1)`. `order.succeeded()` is `true`, so the journey continues.

**Next**, `callWithRetry("PaymentService", 3, ...)` runs. Attempt 1: `paymentCallCount.incrementAndGet()` returns `1`; the predicate `callNum > 1` evaluates to `false`, so attempt 1 fails, and `"[PaymentService] attempt 1 failed, retrying..."` prints. Attempt 2: `paymentCallCount.incrementAndGet()` returns `2`; `2 > 1` is `true`, so attempt 2 succeeds. `callWithRetry` returns `HopResult("PaymentService", true, 2)` — note `attemptsUsed` is `2`, recording that a retry was needed.

**Then**, `callWithRetry("InventoryService", 3, attempt -> true)` runs, succeeding cleanly on attempt 1, producing `HopResult("InventoryService", true, 1)`.

**Finally**, `report.overallSucceeded()` is `true` because the last hop (`inventory`) succeeded, and the loop over `report.hops()` prints each hop's verdict: `OrderService` and `InventoryService` show `attemptsUsed == 1`, labeled "clean," while `PaymentService` shows `attemptsUsed == 2`, labeled as having needed a retry and flagged as likely environmental rather than a code defect — giving whoever reads this report exactly the information needed to decide whether to investigate a bug or just note a flaky dependency.

```
[PaymentService] attempt 1 failed, retrying...
Overall succeeded: true
  OrderService: succeeded=true (clean)
  PaymentService: succeeded=true (needed 1 retr(y/ies) -- likely environmental, not a code bug)
  InventoryService: succeeded=true (clean)
```

## 7. Gotchas & takeaways

> The most common institutional response to a flaky E2E suite is to add a blanket retry around the *entire* test (rerun the whole failing test up to 3 times) rather than around individual hops. That hides real, intermittent bugs just as effectively as it hides environmental flakiness — a genuine race condition that fails 1 time in 4 will "pass" a blanket retry just as often as a truly transient network blip, and the team loses the ability to tell them apart. Retry (and log) at the level of the specific flaky dependency, not the whole test.

- Keep the end-to-end layer thin — a handful of tests covering your most critical, highest-business-risk journeys — per the [test pyramid](0411-test-pyramid-for-microservices.md); it is the most expensive and least deterministic layer you have.
- Most of what E2E fragility "catches" that looks like a bug is actually environmental noise; distinguish "failed after retries" from "needed a retry but ultimately passed" instead of treating every red run as equally urgent.
- Push cross-service compatibility checks down into [contract testing](0415-contract-testing-consumer-driven-contracts.md) wherever possible — it catches the same class of bug an E2E test would, far faster and far more reliably.
- A slow, unreliable E2E suite that engineers routinely ignore or re-run until it's green is worse than no E2E suite at all — it burns time without providing the confidence it's supposed to.
- When an E2E test does fail for a real reason, the fault could be in any of several services — pair it with good [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md) and [correlation IDs](0351-correlation-ids-request-ids.md) so a failure can actually be localized quickly instead of triggering a slow manual investigation across every service in the journey.
