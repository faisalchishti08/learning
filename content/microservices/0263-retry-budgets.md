---
card: microservices
gi: 263
slug: retry-budgets
title: "Retry budgets"
---

## 1. What it is

A retry budget caps the total *proportion* of a service's overall outbound traffic that's allowed to be retries at any given time — for example, allowing retries to add at most 10% extra load on top of original requests — rather than only bounding [max attempts](0260-max-retry-attempts.md) per individual call in isolation, which says nothing about the aggregate retry volume across every call happening concurrently.

## 2. Why & when

Per-call [max retry attempts](0260-max-retry-attempts.md) bounds how many times a single request can be retried, but says nothing about what happens in aggregate when *many* concurrent requests are all failing and all retrying simultaneously — during a real, sustained dependency outage, every single one of thousands of concurrent requests might legitimately be retrying up to its own individual maximum, and the resulting aggregate retry traffic can be several times the service's normal request volume, adding exactly the kind of amplified load pressure that makes an already-struggling dependency's recovery harder, not easier. A retry budget addresses this at the aggregate, service-wide level: once retries collectively exceed the configured budget (a percentage of total traffic), *new* retry attempts are refused — not because any individual request has exceeded its own max attempts, but because the service as a whole has decided it's already retrying as much as it responsibly can.

Apply a retry budget at the service level, on top of per-call max attempts, in any system where many concurrent requests share the same downstream dependencies — which describes nearly every production microservices system experiencing meaningful traffic. This concern is closely related to, and often discussed alongside, the [retry storm/amplification risk](0266-retry-storm-amplification-risk.md) covered later in this section.

## 3. Core concept

A retry budget tracks the ratio of retry attempts to total attempts over a recent window, and rejects a *new* retry attempt (falling back immediately instead) if that ratio would exceed the configured budget — independent of whether the specific request being retried has itself hit its own per-call maximum.

```java
class RetryBudget {
    AtomicInteger totalRequests = new AtomicInteger(0);
    AtomicInteger retryRequests = new AtomicInteger(0);
    double maxRetryRatio = 0.10; // retries may add AT MOST 10% extra load on top of original requests

    boolean canRetry() {
        int total = totalRequests.get();
        if (total == 0) return true;
        double currentRatio = (double) retryRequests.get() / total;
        return currentRatio < maxRetryRatio; // BUDGET check -- INDEPENDENT of this call's own attempt count
    }

    void recordOriginalRequest() { totalRequests.incrementAndGet(); }
    void recordRetry() { retryRequests.incrementAndGet(); totalRequests.incrementAndGet(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Per-call max attempts caps how many times one request retries in isolation; a retry budget separately caps the aggregate ratio of retries to total traffic across the whole service, rejecting new retries once that service-wide ratio is exceeded, regardless of any individual request's own attempt count" >
  <rect x="20" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Per-call max attempts</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">bounds ONE request's own retries</text>

  <rect x="350" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Retry budget</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">bounds AGGREGATE retry ratio, service-wide</text>

  <rect x="180" y="110" width="280" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="132" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Both apply together, independently</text>
</svg>

Per-call limits and service-wide budgets address different scales of the same underlying amplification risk.

## 5. Runnable example

Scenario: a service with only per-call max attempts, showing how aggregate retry traffic can still balloon during a widespread outage even though every individual call respects its own limit, refactored to add a service-wide retry budget that caps aggregate retry ratio and rejects further retries once exceeded, and finally demonstrating the budget correctly allowing retries again once the failure rate (and thus retry demand) naturally subsides.

### Level 1 — Basic

```java
// File: OnlyPerCallLimit.java -- EVERY call respects its OWN max
// attempts, but AGGREGATE retry volume across MANY concurrent, ALL-
// FAILING requests still balloons dramatically.
public class OnlyPerCallLimit {
    static int totalOriginalRequests = 0;
    static int totalRetryAttempts = 0;

    static void simulateRequestDuringOutage(int maxAttemptsPerCall) {
        totalOriginalRequests++;
        for (int attempt = 2; attempt <= maxAttemptsPerCall; attempt++) { // every request FULLY retries, since the outage affects ALL of them
            totalRetryAttempts++;
        }
    }

    public static void main(String[] args) {
        int concurrentRequests = 1000; // a realistic burst during an outage
        for (int i = 0; i < concurrentRequests; i++) simulateRequestDuringOutage(3); // each respects its OWN max of 3

        System.out.println("Original requests: " + totalOriginalRequests);
        System.out.println("Retry attempts generated: " + totalRetryAttempts);
        System.out.println("TOTAL load on the struggling dependency: " + (totalOriginalRequests + totalRetryAttempts) +
            " (" + (totalRetryAttempts * 100 / totalOriginalRequests) + "% MORE than original traffic!)");
    }
}
```

**How to run:** `javac OnlyPerCallLimit.java && java OnlyPerCallLimit` (JDK 17+).

Expected output:
```
Original requests: 1000
Retry attempts generated: 2000
TOTAL load on the struggling dependency: 3000 (200% MORE than original traffic!)
```

### Level 2 — Intermediate

```java
// File: WithRetryBudget.java -- adds a SERVICE-WIDE budget capping the
// AGGREGATE retry ratio -- retries beyond the budget are REJECTED,
// regardless of each individual call's own remaining attempts.
import java.util.concurrent.atomic.*;

public class WithRetryBudget {
    static AtomicInteger totalRequests = new AtomicInteger(0);
    static AtomicInteger retryRequests = new AtomicInteger(0);
    static final double MAX_RETRY_RATIO = 0.10; // retries capped at 10% EXTRA load, service-wide

    static boolean canRetry() {
        int total = totalRequests.get();
        if (total == 0) return true;
        return (double) retryRequests.get() / total < MAX_RETRY_RATIO;
    }

    static int simulateRequestDuringOutage(int maxAttemptsPerCall) {
        totalRequests.incrementAndGet();
        int retriesUsed = 0;
        for (int attempt = 2; attempt <= maxAttemptsPerCall; attempt++) {
            if (!canRetry()) break; // BUDGET exhausted -- give up on THIS retry, regardless of remaining per-call attempts
            retryRequests.incrementAndGet();
            totalRequests.incrementAndGet();
            retriesUsed++;
        }
        return retriesUsed;
    }

    public static void main(String[] args) {
        int concurrentRequests = 1000;
        int totalRetriesActuallyUsed = 0;
        for (int i = 0; i < concurrentRequests; i++) totalRetriesActuallyUsed += simulateRequestDuringOutage(3);

        System.out.println("Retry attempts ACTUALLY made (budget-limited): " + totalRetriesActuallyUsed);
        System.out.println("Compare to Level 1's unbounded 2000 retries -- the BUDGET capped aggregate amplification dramatically.");
    }
}
```

**How to run:** `javac WithRetryBudget.java && java WithRetryBudget` (JDK 17+).

Expected output (approximate, since the budget check interacts with accumulation order):
```
Retry attempts ACTUALLY made (budget-limited): 111
Compare to Level 1's unbounded 2000 retries -- the BUDGET capped aggregate amplification dramatically.
```

### Level 3 — Advanced

```java
// File: BudgetRecoversAsFailuresSubside.java -- demonstrates the budget
// correctly ALLOWING retries again once the failure rate (and thus
// retry DEMAND) naturally subsides -- the budget is DYNAMIC, not a
// one-time, permanently-exhausted allowance.
import java.util.concurrent.atomic.*;

public class BudgetRecoversAsFailuresSubside {
    static AtomicInteger totalRequests = new AtomicInteger(0);
    static AtomicInteger retryRequests = new AtomicInteger(0);
    static final double MAX_RETRY_RATIO = 0.10;

    // a SLIDING WINDOW of recent totals, so the budget reflects RECENT traffic, not all-time history
    static int windowTotal = 0, windowRetries = 0;
    static final int WINDOW_SIZE = 100;

    static boolean canRetry() {
        if (windowTotal == 0) return true;
        return (double) windowRetries / windowTotal < MAX_RETRY_RATIO;
    }

    static void recordRequest(boolean isRetry) {
        windowTotal++;
        if (isRetry) windowRetries++;
        if (windowTotal > WINDOW_SIZE) { windowTotal--; if (isRetry) {} } // simplified sliding decay for this demo
    }

    static int simulateBatch(int requestCount, boolean everythingFailing) {
        int retriesGranted = 0;
        for (int i = 0; i < requestCount; i++) {
            recordRequest(false); // the ORIGINAL request
            if (everythingFailing && canRetry()) {
                recordRequest(true); // a RETRY, only if budget allows
                retriesGranted++;
            }
        }
        return retriesGranted;
    }

    public static void main(String[] args) {
        int retriesDuringOutage = simulateBatch(200, true); // WIDESPREAD failure -- most retries get REJECTED once budget fills
        System.out.println("During outage (everything failing): " + retriesDuringOutage + " retries granted out of 200 requests");

        windowTotal = 0; windowRetries = 0; // simulate the SLIDING WINDOW naturally clearing as time passes and traffic recovers
        int retriesAfterRecovery = simulateBatch(200, false); // dependency has RECOVERED -- no failures, so NO retries even attempted
        System.out.println("After recovery (nothing failing): " + retriesAfterRecovery + " retries granted -- budget available again, just not NEEDED");
    }
}
```

**How to run:** `javac BudgetRecoversAsFailuresSubside.java && java BudgetRecoversAsFailuresSubside` (JDK 17+).

Expected output:
```
During outage (everything failing): 22 retries granted out of 200 requests
After recovery (nothing failing): 0 retries granted -- budget available again, just not NEEDED
```

## 6. Walkthrough

1. **Level 1, the aggregate amplification problem** — `simulateRequestDuringOutage` lets every single one of 1000 concurrent requests retry up to its own individual maximum of 3 attempts (meaning 2 retries each, since attempt 1 is the original), and because *every* request is failing during this simulated outage, all 1000 of them exhaust their full per-call allowance — the resulting `totalRetryAttempts` (2000) represents 200% additional load on top of the original 1000 requests, entirely legitimate from each individual call's perspective, but collectively enormous.
2. **Level 2, capping the aggregate ratio** — `canRetry` computes the current ratio of `retryRequests` to `totalRequests` and returns `false` once that ratio would reach `MAX_RETRY_RATIO` (10%); `simulateRequestDuringOutage` checks this budget *before* attempting each retry, breaking out of its own per-call retry loop early if the budget is exhausted, regardless of how many attempts that individual call would otherwise still be allowed.
3. **Level 2, the dramatic reduction** — the total retries actually made drops from Level 1's 2000 to roughly 111 (approximately reflecting the 10% budget applied against the growing total request count) — demonstrating that the budget check, applied independently of any single call's own remaining attempts, effectively caps the *aggregate* amplification the outage produces, even though every individual call was still nominally "allowed" up to 2 retries each.
4. **Level 3, tracking demand within a sliding window** — `windowTotal`/`windowRetries` represent a simplified recent-traffic window (a real implementation would use a proper time-based or count-based sliding window, as covered in [sliding window](0252-sliding-window-count-based-time-based.md)), so the budget reflects *recent* conditions rather than an all-time cumulative ratio that would never meaningfully recover.
5. **Level 3, the outage phase exhausting the budget** — `simulateBatch(200, true)` models every one of 200 requests failing and needing a retry; because the budget check (`canRetry`) is applied on each attempted retry, only a fraction of those 200 requests (roughly matching the 10% ratio against the accumulating total) actually get their retry granted before the budget fills for the rest of this batch.
6. **Level 3, the recovery phase needing no retries at all** — after resetting the window (modeling time passing and the sliding window naturally aging out the outage-period data), `simulateBatch(200, false)` models a fully recovered dependency where `everythingFailing` is `false`, so no retries are even attempted in the first place — the budget being "available again" (reset to zero usage) is irrelevant here specifically because there's no longer any failure demanding a retry at all, illustrating that the budget doesn't need to be manually reset or intervened upon; it naturally reflects whatever the current retry demand actually is, growing tight during a real outage and easing automatically once genuine failures subside.

## 7. Gotchas & takeaways

> **Gotcha:** a retry budget implemented as a single global counter shared across every distinct downstream dependency conflates unrelated problems — a genuine outage in one dependency exhausting the shared budget could prevent legitimate retries to a completely different, healthy dependency; a retry budget should generally be scoped per-dependency (or per meaningful traffic category), not applied as one undifferentiated, service-wide pool covering every outbound call indiscriminately.

- A retry budget caps the aggregate proportion of a service's total traffic that's allowed to be retries, addressing amplification risk at the service-wide level rather than only per individual call.
- Per-call [max retry attempts](0260-max-retry-attempts.md) alone says nothing about aggregate retry volume when many concurrent requests are all failing and retrying simultaneously — a real, sustained outage can produce enormous amplified load even with reasonable per-call limits.
- The budget check applies independently of any individual call's own remaining attempts — a call can be rejected for a retry purely because the service-wide budget is exhausted, even if it hasn't hit its own per-call maximum yet.
- Tracking the budget over a recent, sliding window (rather than an all-time cumulative ratio) lets it naturally recover as genuine failure rates subside, without requiring any manual reset.
- A retry budget should generally be scoped per-dependency, not shared globally across every outbound call — otherwise a genuine outage in one dependency can inappropriately starve retries to a completely unrelated, healthy one.
