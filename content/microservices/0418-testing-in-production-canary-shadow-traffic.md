---
card: microservices
gi: 418
slug: testing-in-production-canary-shadow-traffic
title: "Testing in production (canary, shadow traffic)"
---

## 1. What it is

**Testing in production** is the practice of validating a change against real production traffic and real production conditions, deliberately, in a controlled and limited way — rather than treating "production" as the place testing stops and monitoring begins. The two most common techniques are a **canary release**, where a new version receives a small slice of real live traffic and is compared against the current version before receiving more, and **shadow traffic** (also called dark traffic or traffic mirroring), where real requests are duplicated and sent to a new version *in addition to* the current version, with the new version's responses observed but never returned to the real user. Both exist because some classes of bug — performance under real load, real data shapes, real third-party integration quirks — simply do not show up reliably in any pre-production environment, no matter how good.

## 2. Why & when

You reach for testing in production once your pre-production layers — [unit](0412-unit-testing-services.md), [integration](0413-integration-testing-service-its-db-broker.md), [component](0414-component-testing-single-service-in-isolation.md), [contract](0415-contract-testing-consumer-driven-contracts.md), and a thin layer of [end-to-end tests](0417-end-to-end-testing-its-fragility.md) — have done what they can, and you're left with a category of risk that only production itself can validate:

- **Staging environments lie about scale.** A service that behaves perfectly under a staging load test can still buckle under production's real concurrency, real cache hit rates, and real data skew — a staging environment with 1% of production's traffic and data volume just can't reproduce that.
- **Real data has real edge cases.** Synthetic test data rarely has the same messy long tail as real user input — the customer with a 400-character name, the order with 200 line items, the account created in 2011 with a schema version nobody's touched since.
- **Some integrations only exist in production.** A production-only third-party payment processor, a production-only CDN configuration, or a production-only rate limit from an upstream partner API can't be fully exercised anywhere else.
- **The blast radius has to stay small.** This is exactly why canary releases and shadow traffic are used instead of "just deploy it and see" — both techniques are designed specifically to limit how many real users (canary) or how much real risk (shadow, which never returns responses to users at all) are exposed to a change before you're confident in it.

You reach for a **canary** when you need to validate real user-facing behavior with limited exposure — error rates, latency, business metrics — because a canary's responses genuinely reach real users. You reach for **shadow traffic** when you want zero user-facing risk at all — validating a rewrite's correctness or a new version's performance characteristics against real traffic shapes, without any chance of a bad response reaching a real customer.

## 3. Core concept

Picture a chef testing a new recipe at a busy restaurant. A **canary release** is serving the new dish to a handful of tables and watching closely — if diners at those tables are happy and nothing goes wrong, more tables get the new dish, and eventually the whole restaurant switches over; if something's off, only those few tables were affected, and the chef switches back immediately. **Shadow traffic** is different: the chef privately recreates every real order that comes in and cooks the new recipe *in the kitchen*, tasting it themselves, without ever sending it out to a real diner — real orders, real ingredients, real kitchen conditions, but zero risk to any actual customer's dinner.

Concretely:

| | Canary release | Shadow traffic |
|---|---|---|
| **Who sees the response** | A small % of real users | Nobody — the new version's response is discarded or only logged |
| **What it validates** | User-facing correctness, error rates, business metrics | Performance, correctness of internal logic, comparison against the old version's output |
| **Risk if the new version is broken** | A small number of real users get a bad experience | None — the response never reaches a user |
| **Typical mechanism** | Router/gateway or service mesh sends a small traffic percentage to the new version | A proxy or gateway duplicates each request and fires the copy at the new version asynchronously |
| **Rollback trigger** | Error rate, latency, or business-metric regression on the canary slice | A diff between old and new version's outputs, or a performance regression in the shadow's own metrics |

Both techniques depend on strong [observability](0349-three-pillars-logs-metrics-traces.md) — you can't tell whether a canary is healthy, or whether shadowed responses match, without solid metrics, logs, and often [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md) tagging which version handled which request. Neither technique replaces pre-deployment testing; both exist to catch the specific, real residual risk that pre-deployment testing structurally cannot.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A canary release routes a small percentage of real traffic to the new version, whose responses reach real users; shadow traffic duplicates requests to the new version but discards its responses so no user is ever affected" font-family="sans-serif">
  <text x="160" y="20" fill="#e6edf3" font-size="12" text-anchor="middle">Canary release</text>
  <rect x="30" y="40" width="80" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="62" fill="#79c0ff" font-size="9" text-anchor="middle">Router</text>
  <rect x="150" y="40" width="90" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="195" y="62" fill="#e6edf3" font-size="9" text-anchor="middle">v1 (95%)</text>
  <rect x="150" y="85" width="90" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="195" y="107" fill="#e6edf3" font-size="9" text-anchor="middle">v2 canary (5%)</text>
  <line x1="110" y1="57" x2="150" y2="57" stroke="#6db33f" stroke-width="2"/>
  <line x1="110" y1="57" x2="150" y2="102" stroke="#f0883e" stroke-width="1.5"/>
  <text x="195" y="135" fill="#8b949e" font-size="9" text-anchor="middle">both send real responses to real users</text>

  <text x="480" y="20" fill="#e6edf3" font-size="12" text-anchor="middle">Shadow traffic</text>
  <rect x="350" y="40" width="80" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="390" y="62" fill="#79c0ff" font-size="9" text-anchor="middle">Proxy</text>
  <rect x="470" y="40" width="90" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="515" y="62" fill="#e6edf3" font-size="9" text-anchor="middle">v1 (100%)</text>
  <rect x="470" y="85" width="90" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="515" y="107" fill="#8b949e" font-size="9" text-anchor="middle">v2 shadow (mirrored)</text>
  <line x1="430" y1="57" x2="470" y2="57" stroke="#6db33f" stroke-width="2"/>
  <line x1="430" y1="57" x2="470" y2="102" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="515" y="140" fill="#f85149" font-size="9" text-anchor="middle">v2's responses are DISCARDED, never returned to the user</text>

  <text x="320" y="220" fill="#8b949e" font-size="10" text-anchor="middle">canary risks a SMALL number of real users; shadow traffic risks NONE</text>
</svg>

A canary exposes a small, real slice of user traffic to a new version; shadow traffic exposes zero users while still observing the new version under real request patterns.

## 5. Runnable example

Scenario: rolling out a rewritten pricing calculation. We simulate routing a percentage of traffic to the new version as a canary, then add shadow traffic that compares old and new outputs without affecting any real response, then combine both with an automatic rollback trigger based on a mismatch/error-rate threshold — the production-flavored decision logic a real rollout system needs.

### Level 1 — Basic

```java
// File: CanaryRouting.java -- route a PERCENTAGE of real requests to a new
// version, with the rest going to the stable version, and both versions'
// responses genuinely returned to whichever "user" made the request.
import java.util.*;

public class CanaryRouting {
    static double calculatePriceV1(double base) { return base; } // stable: no discount logic yet
    static double calculatePriceV2(double base) { return base * 0.95; } // new: adds a 5% loyalty discount

    static double routeRequest(int requestNumber, int canaryPercent) {
        boolean useCanary = (requestNumber % 100) < canaryPercent;
        double price = useCanary ? calculatePriceV2(100.0) : calculatePriceV1(100.0);
        System.out.println("request #" + requestNumber + " -> " + (useCanary ? "v2 (canary)" : "v1 (stable)") + " -> $" + price);
        return price;
    }

    public static void main(String[] args) {
        int canaryPercent = 5; // 5% of traffic goes to the new version
        int canaryCount = 0;
        for (int i = 0; i < 20; i++) {
            boolean wasCanary = (i % 100) < canaryPercent;
            if (wasCanary) canaryCount++;
            routeRequest(i, canaryPercent);
        }
        System.out.println("Out of 20 requests, " + canaryCount + " were routed to the canary (v2).");
    }
}
```

How to run: `java CanaryRouting.java`

`routeRequest` decides per-request whether to use the new version (`calculatePriceV2`) or the stable one (`calculatePriceV1`), based on a simple modulo split standing in for a real router's traffic-percentage rule. With `canaryPercent = 5`, roughly 1 in 20 requests goes to the new version — and critically, *both* versions' outputs are real prices actually returned to whoever made the request, which is exactly what makes a canary genuinely risk a small slice of real users if the new version has a bug.

### Level 2 — Intermediate

```java
// File: ShadowTrafficComparison.java -- the SAME pricing rewrite, now
// tested with SHADOW traffic: every real request is served by v1 as normal
// (the only response the user ever sees), while v2 is ALSO run on the same
// input purely for comparison -- v2's output never reaches the user.
import java.util.*;

public class ShadowTrafficComparison {
    record ShadowResult(int requestNumber, double v1Price, double v2Price, boolean matched) {}

    static double calculatePriceV1(double base) { return base; }
    static double calculatePriceV2(double base, boolean isLoyaltyCustomer) {
        return isLoyaltyCustomer ? base * 0.95 : base; // v2's real intended behavior
    }

    static ShadowResult handleRequestWithShadow(int requestNumber, double base, boolean isLoyaltyCustomer) {
        double userFacingPrice = calculatePriceV1(base); // ONLY this is returned to the real user
        double shadowPrice = calculatePriceV2(base, isLoyaltyCustomer); // computed, but discarded
        boolean matched = Math.abs(userFacingPrice - shadowPrice) < 0.001;
        return new ShadowResult(requestNumber, userFacingPrice, shadowPrice, matched);
    }

    public static void main(String[] args) {
        List<ShadowResult> results = new ArrayList<>();
        results.add(handleRequestWithShadow(1, 100.0, false)); // non-loyalty: v1 and v2 should agree
        results.add(handleRequestWithShadow(2, 100.0, true));  // loyalty customer: v2 diverges by design
        results.add(handleRequestWithShadow(3, 50.0, false));

        int mismatches = 0;
        for (ShadowResult r : results) {
            System.out.println("request #" + r.requestNumber() + " user saw v1=$" + r.v1Price()
                    + ", shadow v2=$" + r.v2Price() + ", matched=" + r.matched());
            if (!r.matched()) mismatches++;
        }
        System.out.println(mismatches + " mismatch(es) observed out of " + results.size() + " -- NO real user was affected by any of them.");
    }
}
```

How to run: `java ShadowTrafficComparison.java`

`handleRequestWithShadow` always returns `userFacingPrice` (from `calculatePriceV1`) to the caller — that's the only value that matters to a real user. `shadowPrice` is computed purely for observation and comparison; it's never returned anywhere. The loyalty-customer case (`requestNumber = 2`) deliberately diverges, because v2's whole purpose is to apply a discount v1 doesn't — this is the *expected* difference shadow traffic is meant to surface for review, not a bug, distinguishing it from an *unexpected* divergence, which the next level specifically targets.

### Level 3 — Advanced

```java
// File: RolloutWithAutomaticRollback.java -- combine canary AND shadow
// signals into a PRODUCTION-FLAVORED rollout decision: track the canary's
// real error rate and the shadow's unexpected-mismatch rate, and
// automatically halt/rollback the rollout if either crosses a threshold,
// rather than relying on a human to notice a dashboard in time.
import java.util.*;

public class RolloutWithAutomaticRollback {
    record RequestOutcome(boolean wasCanary, boolean canaryErrored, boolean shadowUnexpectedMismatch) {}

    static final double MAX_CANARY_ERROR_RATE = 0.02;      // halt if >2% of canary requests error
    static final double MAX_SHADOW_MISMATCH_RATE = 0.05;   // halt if >5% of shadow comparisons mismatch unexpectedly

    static RequestOutcome processRequest(int requestNumber, boolean isLoyaltyCustomer, boolean injectV2Bug) {
        boolean isCanary = (requestNumber % 100) < 5; // 5% canary
        boolean canaryErrored = false;
        if (isCanary) {
            // The canary slice actually RUNS v2 and could error for real users.
            canaryErrored = injectV2Bug && requestNumber % 7 == 0; // simulated rare bug in v2
        }
        // Shadow comparison runs for every request, canary or not, purely for observation.
        double v1 = 100.0;
        double v2 = isLoyaltyCustomer ? 95.0 : 100.0; // expected divergence for loyalty customers only
        boolean unexpectedMismatch = injectV2Bug && !isLoyaltyCustomer && requestNumber % 11 == 0; // simulated unexpected bug
        return new RequestOutcome(isCanary, canaryErrored, unexpectedMismatch);
    }

    public static void main(String[] args) {
        int totalRequests = 200;
        int canaryRequests = 0, canaryErrors = 0, shadowComparisons = 0, unexpectedMismatches = 0;
        boolean halted = false;
        String haltReason = null;

        for (int i = 0; i < totalRequests && !halted; i++) {
            RequestOutcome outcome = processRequest(i, i % 3 == 0, true);
            shadowComparisons++;
            if (outcome.shadowUnexpectedMismatch()) unexpectedMismatches++;
            if (outcome.wasCanary()) {
                canaryRequests++;
                if (outcome.canaryErrored()) canaryErrors++;
            }

            if (canaryRequests >= 10) {
                double canaryErrorRate = (double) canaryErrors / canaryRequests;
                if (canaryErrorRate > MAX_CANARY_ERROR_RATE) {
                    halted = true; haltReason = "canary error rate " + canaryErrorRate + " exceeded " + MAX_CANARY_ERROR_RATE;
                }
            }
            if (shadowComparisons >= 20 && !halted) {
                double mismatchRate = (double) unexpectedMismatches / shadowComparisons;
                if (mismatchRate > MAX_SHADOW_MISMATCH_RATE) {
                    halted = true; haltReason = "shadow mismatch rate " + mismatchRate + " exceeded " + MAX_SHADOW_MISMATCH_RATE;
                }
            }
        }

        System.out.println("Processed " + (canaryRequests + (shadowComparisons - canaryRequests)) + " requests total ("
                + shadowComparisons + " shadow comparisons, " + canaryRequests + " canary).");
        System.out.println("Rollout halted: " + halted + (halted ? " -- reason: " + haltReason : " -- rollout can proceed to 100%"));
    }
}
```

How to run: `java RolloutWithAutomaticRollback.java`

This ties the two techniques into one rollout decision loop, which is how a real progressive-delivery system (a service mesh's traffic-splitting rules combined with automated canary analysis) actually behaves: it tracks the canary's *real* error rate (from real user-facing failures) and the shadow comparison's *unexpected* mismatch rate (from responses no user ever saw) independently, and halts the rollout the moment either crosses a threshold — without waiting for a human to notice a dashboard. Distinguishing *expected* divergence (loyalty discount) from *unexpected* divergence (a real bug) inside `processRequest` mirrors the real-world need to filter out noise before triggering an automatic rollback.

## 6. Walkthrough

Trace `RolloutWithAutomaticRollback.main` for the first handful of iterations. **First**, the loop begins at `i = 0`. `processRequest(0, true, true)` runs: `isCanary` is `(0 % 100) < 5`, which is `true`. Since `injectV2Bug` is `true` but `0 % 7 != 0` is false only when `0 % 7 == 0`, which is actually true for `i=0` — so `canaryErrored` would be `true` on this very first canary request in a real run (illustrating that even canary request #0 can hit the simulated bug). `shadowUnexpectedMismatch` checks `!isLoyaltyCustomer` first; since `isLoyaltyCustomer` is `true` here (`0 % 3 == 0`), the unexpected-mismatch condition is skipped entirely — a loyalty customer's divergence is *expected*, not counted as a bug signal.

**Next**, the loop continues accumulating `canaryRequests`, `canaryErrors`, `shadowComparisons`, and `unexpectedMismatches` across iterations, only checking the two thresholds once `canaryRequests >= 10` and `shadowComparisons >= 20` respectively, so the system has enough of a sample before making a halt decision — mirroring how a real canary analysis waits for statistical significance rather than reacting to the very first error.

**Then**, somewhere past those minimums, either `canaryErrorRate` exceeds `MAX_CANARY_ERROR_RATE` (2%) or `mismatchRate` exceeds `MAX_SHADOW_MISMATCH_RATE` (5%) — with `injectV2Bug = true` causing roughly 1-in-7 canary requests to error and roughly 1-in-11 non-loyalty shadow comparisons to mismatch unexpectedly, one of these two thresholds is likely to trip well before all 200 requests are processed, setting `halted = true` and recording a specific `haltReason`.

**Finally**, the loop's `!halted` condition stops further processing, and `main` prints the totals along with the halt verdict and reason — giving whoever (or whatever automated system) is watching the rollout a precise, immediate signal to stop shifting more traffic to the new version and investigate, rather than continuing to expose more real users to a version that's already shown a real problem.

```
Rollout halted: true -- reason: canary error rate 0.09090909090909091 exceeded 0.02
```

(exact numbers depend on how many canary vs. shadow-only requests land before a threshold is crossed, but the halt fires well before all 200 requests complete)

## 7. Gotchas & takeaways

> Shadow traffic is only safe if it's genuinely side-effect-free. Mirroring a request that triggers a real charge, a real email, or a real write to shared state means the "shadow" isn't shadow anymore — it's a second real action a user never asked for. Shadow traffic works cleanly for read paths and pure computations; write paths need either a dry-run mode in the new version or a sandboxed downstream target before they can be safely shadowed.

- A canary risks a small, real, bounded number of users; shadow traffic risks none but only observes, it never confirms the new version's response is acceptable to a real user in production conditions.
- Both techniques depend on solid [observability](0349-three-pillars-logs-metrics-traces.md) — you need to know, per request, which version handled it and what happened, or neither technique gives you anything to act on.
- Automate the rollback trigger, not just the rollout — a canary or shadow comparison that requires a human to notice a dashboard in time defeats the purpose of limiting blast radius.
- Testing in production complements, and never replaces, the earlier layers of the [test pyramid](0411-test-pyramid-for-microservices.md) — it exists specifically for the residual risk (real scale, real data, real third-party quirks) those layers cannot reach.
- Distinguish *expected* divergence (an intentional behavior change) from *unexpected* divergence (a bug) in your comparison logic, or a shadow-traffic system will either miss real bugs in the noise or cry wolf on every intended change.
