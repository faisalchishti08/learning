---
card: microservices
gi: 359
slug: sli-slo-sla-error-budgets
title: "SLI / SLO / SLA / error budgets"
---

## 1. What it is

An **SLI** (Service Level Indicator) is a specific, measured metric of service behavior — "the percentage of requests completed in under 300ms," often drawn directly from the [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md). An **SLO** (Service Level Objective) is an internal target for that SLI — "99.9% of requests complete in under 300ms, measured over 30 days." An **SLA** (Service Level Agreement) is an external, often contractual, commitment to customers, usually looser than the internal SLO and backed by a consequence (a service credit) if missed. An **error budget** is simply `100% - SLO`, converted into a concrete allowance: at 99.9%, you have a 0.1% error budget, meaning a specific, calculable amount of allowed failure or downtime before you've "spent" it.

## 2. Why & when

Without an explicit SLO, "is the service healthy enough" is a matter of opinion, argued fresh during every incident review. An SLO turns that into an objective, pre-agreed number, and the error budget it implies turns "should we take a risk (a risky deploy, delaying a fix) right now" into a calculation rather than a debate: if you've already spent most of this period's error budget, the answer is no; if you have budget to spare, a calculated risk is reasonable. This is the core practical value of the SLI/SLO/error-budget framework — it converts a vague cultural tension between "ship features" and "keep things stable" into a concrete, shared number both sides can point to.

Define SLIs from your existing golden-signal metrics, set SLOs deliberately looser than 100% (100% reliability is neither achievable nor, past a certain point, worth its cost), and track the resulting error budget continuously. Use the error budget's remaining balance as an actual input to decisions: budget nearly exhausted means prioritize stability work and slow down risky changes; budget largely unspent means there's room to take on calculated risk. Reserve SLAs specifically for external, customer-facing commitments, kept looser than the internal SLO so there's a buffer between "we've noticed we're at risk" (SLO) and "we owe the customer a penalty" (SLA).

## 3. Core concept

The error budget for a given period is `(1 - SLO) × total requests (or total time)`. As failures (or downtime) accumulate against that budget, the remaining balance shrinks; a `burn rate` describes how fast the budget is being consumed relative to the period — a high burn rate means the budget will be exhausted well before the period ends if the current failure rate continues, which is itself a useful, actionable signal distinct from having already exhausted the budget.

```java
double sloTarget = 0.999; // 99.9%
double errorBudgetFraction = 1 - sloTarget; // 0.001 = 0.1%
long totalRequestsThisPeriod = 1_000_000;
long errorBudgetInRequests = (long) (errorBudgetFraction * totalRequestsThisPeriod); // 1000 allowed failures
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bar representing the error budget for the period, partially consumed by actual failures so far; the remaining unconsumed portion is what's left to spend on risk before the budget runs out">
  <rect x="30" y="60" width="580" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <rect x="30" y="60" width="380" height="40" rx="6" fill="#f0883e"/>
  <text x="220" y="85" fill="#1c2430" font-size="10" text-anchor="middle" font-family="sans-serif">CONSUMED (actual failures so far)</text>
  <text x="510" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">REMAINING budget</text>

  <text x="320" y="130" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Remaining budget = room for calculated risk; a high burn rate means it'll run out before the period ends.</text>
</svg>

The error budget shrinks as failures accumulate; the remaining balance is a concrete, shared input to risk decisions.

## 5. Runnable example

Scenario: a service with a defined SLO, first tracked with only a raw error count (no context for whether that's acceptable), then computed properly against an error budget with a clear remaining balance, and finally extended to compute burn rate and flag when the budget is on pace to be exhausted early.

### Level 1 — Basic

```java
// File: RawErrorCountNoContext.java -- just a raw error count, with NO
// reference to any target -- impossible to say if this is fine or a crisis.
import java.util.*;

public class RawErrorCountNoContext {
    public static void main(String[] args) {
        long totalRequests = 1_000_000;
        long failedRequests = 450;

        System.out.println("Failed requests this period: " + failedRequests + " out of " + totalRequests);
        System.out.println("Is this OK?? Impossible to say without a target to compare against.");
    }
}
```

How to run: `java RawErrorCountNoContext.java`

`450` failures out of `1,000,000` requests is just a raw number — without an agreed SLO to compare it against, there's no principled way to say whether this is a normal, acceptable level of failure or a serious problem requiring immediate action.

### Level 2 — Intermediate

```java
// File: ErrorBudgetGivesContext.java -- the SAME raw failure count, now
// compared against a DEFINED SLO's error budget, giving an immediate,
// objective answer.
import java.util.*;

public class ErrorBudgetGivesContext {
    public static void main(String[] args) {
        double sloTarget = 0.999; // 99.9% SLO, agreed in advance
        long totalRequests = 1_000_000;
        long failedRequests = 450;

        long errorBudgetInRequests = (long) ((1 - sloTarget) * totalRequests); // 1000 allowed failures this period
        long remainingBudget = errorBudgetInRequests - failedRequests;
        double percentBudgetConsumed = 100.0 * failedRequests / errorBudgetInRequests;

        System.out.println("SLO: " + (sloTarget * 100) + "%, error budget: " + errorBudgetInRequests + " allowed failures");
        System.out.println("Actual failures so far: " + failedRequests);
        System.out.println("Remaining budget: " + remainingBudget + " failures (" + (100 - percentBudgetConsumed) + "% of budget still unspent)");
        System.out.println("NOW we have an objective answer: " + percentBudgetConsumed + "% of the error budget consumed -- clearly manageable.");
    }
}
```

How to run: `java ErrorBudgetGivesContext.java`

With `sloTarget=0.999`, the error budget for `1,000,000` requests is `1000` allowed failures. Against that, `450` actual failures means `45%` of the budget consumed, with `550` failures (`55%` of the budget) still remaining — a concrete, objective statement of how much room is left, something Level 1's raw count alone could never provide.

### Level 3 — Advanced

```java
// File: BurnRateFlagsEarlyExhaustion.java -- computes the BURN RATE (how
// fast the budget is being consumed relative to elapsed time in the
// period) and flags if the budget is on pace to run out BEFORE the
// period ends, even if the CURRENT percentage consumed still looks fine.
import java.util.*;

public class BurnRateFlagsEarlyExhaustion {
    public static void main(String[] args) {
        double sloTarget = 0.999;
        long totalRequestsExpectedThisPeriod = 1_000_000;
        long errorBudgetInRequests = (long) ((1 - sloTarget) * totalRequestsExpectedThisPeriod); // 1000

        double periodLengthDays = 30;
        double daysElapsed = 5; // we're only 1/6 of the way through the 30-day period
        long failedRequestsSoFar = 400; // but ALREADY 40% of the budget is gone

        double expectedBudgetConsumedByNow = errorBudgetInRequests * (daysElapsed / periodLengthDays); // "normal" pace
        double actualBurnRate = failedRequestsSoFar / expectedBudgetConsumedByNow; // >1.0 means burning FASTER than sustainable

        System.out.println("Day " + daysElapsed + " of " + periodLengthDays + ": " + failedRequestsSoFar
                + "/" + errorBudgetInRequests + " budget consumed (" + (100.0 * failedRequestsSoFar / errorBudgetInRequests) + "%)");
        System.out.println("At a SUSTAINABLE pace, expected consumption by now: ~" + expectedBudgetConsumedByNow + " failures");
        System.out.println("Actual burn rate: " + actualBurnRate + "x sustainable pace");

        if (actualBurnRate > 2.0) {
            System.out.println("BURN RATE ALERT: at this rate, the ENTIRE budget will be exhausted well BEFORE day 30 -- act NOW, even though 40% consumed alone might look 'fine'.");
        }
    }
}
```

How to run: `java BurnRateFlagsEarlyExhaustion.java`

At day 5 of a 30-day period, a sustainable pace would have consumed only `errorBudgetInRequests × (5/30) ≈ 167` failures — but `400` have actually occurred, giving a burn rate of roughly `2.4x` sustainable. Even though "40% of the budget consumed" might not sound alarming in isolation, the burn rate reveals that at the *current pace*, the entire budget will be exhausted well before the 30-day period ends — a distinct, more urgent signal than the raw consumption percentage alone, and specifically the kind of early warning that lets a team react while there's still time, rather than discovering the budget is gone only once it actually hits zero.

## 6. Walkthrough

Trace `BurnRateFlagsEarlyExhaustion.main` in order. **First**, `errorBudgetInRequests` is computed as `(1 - 0.999) × 1,000,000 = 1000` — the total allowed failures for the full 30-day period.

**Next**, `expectedBudgetConsumedByNow` is computed as `1000 × (5 / 30) ≈ 166.67` — this represents what a perfectly even, sustainable failure rate would have consumed by day 5 if the budget were meant to be spent evenly across the whole period.

**Then**, `actualBurnRate` is computed as `failedRequestsSoFar / expectedBudgetConsumedByNow = 400 / 166.67 ≈ 2.4`. A value greater than `1.0` means failures are accumulating faster than a sustainable, evenly-spread pace would predict; `2.4` specifically means burning through the budget about 2.4 times faster than sustainable.

**`main` then prints** the current consumption (`400`/`1000`, or `40%`), the expected consumption at a sustainable pace (`~167`), and the computed burn rate (`~2.4x`).

**Finally**, the `if (actualBurnRate > 2.0)` check evaluates to `true`, so the burn-rate alert prints, explicitly noting that even though `40%` consumed might look tolerable at first glance, the *rate* of consumption predicts the entire budget will be exhausted well before day 30 if nothing changes — prompting action now rather than waiting for the raw consumption percentage to climb further on its own.

```
errorBudget = (1 - 0.999) x 1,000,000 = 1000 allowed failures over 30 days
day 5: expected sustainable consumption ≈ 1000 x (5/30) ≈ 167
day 5: ACTUAL consumption = 400  ->  burn rate = 400/167 ≈ 2.4x sustainable
2.4x > 2.0 threshold -> ALERT: budget will run out early at this pace
```

## 7. Gotchas & takeaways

> Looking only at "percentage of error budget consumed so far" without also considering *how much of the period has elapsed* can hide a dangerously fast burn rate — 40% consumed sounds moderate in isolation, but 40% consumed by day 5 of 30 is a very different, much more urgent situation than 40% consumed by day 25 of 30.

- An SLI is a measured metric, an SLO is the internal target for it, an SLA is the (typically looser) external, contractual commitment, and an error budget is the concrete, calculable allowance implied by `100% - SLO`.
- The error budget turns "should we take a risk right now" into an objective calculation rather than a subjective debate: spend it deliberately on risky changes when there's room, and prioritize stability when it's running low.
- Burn rate (actual consumption relative to a sustainable, evenly-paced consumption for the elapsed time) is a more urgent, earlier-warning signal than raw percentage consumed alone.
- SLIs are typically drawn directly from the [four golden signals](0358-four-golden-signals-latency-traffic-errors-saturation.md) already being tracked, giving a direct, practical link between day-to-day observability data and the higher-level reliability targets a team is accountable for.
