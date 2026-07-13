---
card: microservices
gi: 368
slug: custom-meters-counter-gauge-timer-distributionsummary
title: "Custom meters (Counter, Gauge, Timer, DistributionSummary)"
---

## 1. What it is

Micrometer provides four core meter types for recording custom application metrics: a **Counter** (a value that only ever increases — total orders placed), a **Gauge** (a value that can go up or down, reflecting current state — active connections right now), a **Timer** (records both the count and duration distribution of timed events — how long checkout takes, and how often it happens), and a **DistributionSummary** (records a distribution of non-time values — the size, in bytes, of uploaded files). Choosing the right meter type for what you're actually measuring is what makes the resulting metric meaningful.

## 2. Why & when

Each meter type exists because the four different kinds of things worth measuring — cumulative counts, current levels, timed durations, and non-time distributions — genuinely behave differently and need different underlying representations to be queried meaningfully later. Using a Counter for something that should be a Gauge (or vice versa) produces a metric that looks superficially fine but answers the wrong question when someone tries to query it — a Counter modeling "current active connections" would only ever increase, never reflecting connections closing, making it useless for understanding current load.

Use a Counter for anything that only accumulates and never decreases (total requests, total errors, total orders placed). Use a Gauge for anything reflecting a current, fluctuating level (active connections, queue depth, cache size). Use a Timer specifically for measuring how long an operation takes, since it captures both count and duration distribution together in one meter, giving you rate and latency percentiles from a single instrument. Use a DistributionSummary for any other distribution of values that isn't time-based (payload sizes, batch sizes, item counts per order).

## 3. Core concept

A `Counter` only exposes an `increment()` operation. A `Gauge` is typically registered against a value supplier (a function Micrometer calls to read the current value whenever it's needed, rather than being pushed to directly) so it always reflects live state. A `Timer` wraps a block of code (or is recorded manually with a duration) and internally tracks both a count and a duration histogram. A `DistributionSummary` is recorded with `record(value)` calls and tracks a similar histogram, just for arbitrary numeric values instead of durations.

```java
Counter ordersPlaced = registry.counter("orders.placed");
Gauge.builder("connections.active", pool, Pool::getActiveCount).register(registry);
Timer checkoutTimer = registry.timer("checkout.duration");
DistributionSummary uploadSizes = registry.summary("upload.size.bytes");
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four meter types: Counter only goes up, Gauge fluctuates with current state, Timer records count plus duration distribution, DistributionSummary records a distribution of non-time values">
  <rect x="15" y="20" width="145" height="150" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="87" y="45" fill="#3fb950" font-size="10.5" text-anchor="middle" font-family="sans-serif">Counter</text>
  <text x="87" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">only increases</text>

  <rect x="170" y="20" width="145" height="150" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="242" y="45" fill="#79c0ff" font-size="10.5" text-anchor="middle" font-family="sans-serif">Gauge</text>
  <text x="242" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">current level, up or down</text>

  <rect x="325" y="20" width="145" height="150" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="397" y="45" fill="#f0883e" font-size="10.5" text-anchor="middle" font-family="sans-serif">Timer</text>
  <text x="397" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">count + duration distribution</text>

  <rect x="480" y="20" width="145" height="150" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="552" y="45" fill="#f85149" font-size="10.5" text-anchor="middle" font-family="sans-serif">DistributionSummary</text>
  <text x="552" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">non-time value distribution</text>
</svg>

Each meter type is shaped for a genuinely different kind of measurement — picking the right one is what makes the metric meaningful.

## 5. Runnable example

Scenario: a checkout flow instrumented first with the wrong meter type (a Counter misused for a fluctuating value), then corrected with the appropriate Gauge, Counter, and Timer types applied to their actual matching concerns, and finally extended with a DistributionSummary tracking order sizes.

### Level 1 — Basic

```java
// File: WrongMeterTypeMisused.java -- a Counter is used to track ACTIVE
// connections, a value that should go UP AND DOWN; but Counter only ever
// increases, producing a MEANINGLESS metric for this purpose.
import java.util.*;

public class WrongMeterTypeMisused {
    static int activeConnectionsCounterMisused = 0; // WRONG meter type for this concern

    static void connectionOpened() { activeConnectionsCounterMisused++; }
    static void connectionClosed() { activeConnectionsCounterMisused++; } // WRONG: incrementing on CLOSE too, since Counter can't decrease!

    public static void main(String[] args) {
        connectionOpened(); connectionOpened(); connectionOpened(); // 3 opened
        connectionClosed(); connectionClosed(); // 2 closed -- should mean only 1 STILL active

        System.out.println("'Active connections' counter value: " + activeConnectionsCounterMisused
                + " -- but only 1 connection is ACTUALLY still open! This metric is USELESS for understanding current load.");
    }
}
```

How to run: `java WrongMeterTypeMisused.java`

Because a Counter can only increase, `connectionClosed` is forced to also increment the same counter (there's no way to decrement a true counter meaningfully) — the resulting value (`5`) bears no relationship to the actual number of currently open connections (`1`), making this metric useless for its intended purpose of understanding current load.

### Level 2 — Intermediate

```java
// File: CorrectMeterTypesApplied.java -- uses a GAUGE for the
// fluctuating active-connections concern, a COUNTER for the genuinely
// cumulative total-connections-opened concern, and a TIMER for checkout duration.
import java.util.*;

public class CorrectMeterTypesApplied {
    static int activeConnections = 0; // backing value for the Gauge -- can go up AND down
    static int totalConnectionsOpenedCounter = 0; // genuinely cumulative -- Counter is correct HERE

    static void connectionOpened() { activeConnections++; totalConnectionsOpenedCounter++; }
    static void connectionClosed() { activeConnections--; } // Gauge's backing value CAN decrease -- correct

    record TimerRecording(long durationMs) {}
    static List<TimerRecording> checkoutTimerRecordings = new ArrayList<>();
    static void recordCheckoutDuration(long durationMs) { checkoutTimerRecordings.add(new TimerRecording(durationMs)); }

    public static void main(String[] args) {
        connectionOpened(); connectionOpened(); connectionOpened();
        connectionClosed(); connectionClosed();

        recordCheckoutDuration(120);
        recordCheckoutDuration(95);

        System.out.println("Gauge (active connections RIGHT NOW): " + activeConnections + " -- CORRECT, reflects the true current count.");
        System.out.println("Counter (total connections EVER opened): " + totalConnectionsOpenedCounter + " -- CORRECT, genuinely cumulative.");
        System.out.println("Timer recordings (count=" + checkoutTimerRecordings.size() + "): " + checkoutTimerRecordings);
    }
}
```

How to run: `java CorrectMeterTypesApplied.java`

`activeConnections` is decremented on close, correctly modeling a Gauge's fluctuating current-value behavior — the final value (`1`) accurately reflects that one connection is still open. `totalConnectionsOpenedCounter`, by contrast, only ever increases and correctly reports the true cumulative total (`3`) of connections ever opened — a genuinely appropriate use of a Counter. `checkoutTimerRecordings` captures both the count and the individual durations of timed checkout operations, exactly what a real Timer meter tracks internally.

### Level 3 — Advanced

```java
// File: DistributionSummaryForOrderSizes.java -- adds a
// DistributionSummary tracking the NUMBER OF ITEMS per order (a
// non-time value distribution), computing percentiles from it exactly
// like a Timer would for durations, but for a completely different kind
// of measurement.
import java.util.*;

public class DistributionSummaryForOrderSizes {
    static List<Integer> orderItemCountRecordings = new ArrayList<>(); // backs a DistributionSummary

    static void recordOrderSize(int itemCount) { orderItemCountRecordings.add(itemCount); }

    static double percentile(List<Integer> values, int p) {
        List<Integer> sorted = new ArrayList<>(values);
        Collections.sort(sorted);
        int index = (int) Math.ceil(p / 100.0 * sorted.size()) - 1;
        return sorted.get(Math.max(index, 0));
    }

    public static void main(String[] args) {
        int[] orderSizes = {1, 2, 1, 3, 1, 2, 15, 1, 2, 1}; // mostly small orders, one large bulk order
        for (int size : orderSizes) recordOrderSize(size);

        double mean = orderItemCountRecordings.stream().mapToInt(Integer::intValue).average().orElse(0);
        double p50 = percentile(orderItemCountRecordings, 50);
        double p99 = percentile(orderItemCountRecordings, 99);

        System.out.println("DistributionSummary for order sizes -- count=" + orderItemCountRecordings.size()
                + ", mean=" + mean + ", p50=" + p50 + ", p99=" + p99);
        System.out.println("p99 correctly reveals the RARE bulk order of 15 items, exactly like a Timer's p99 reveals slow request durations.");
    }
}
```

How to run: `java DistributionSummaryForOrderSizes.java`

`orderItemCountRecordings` accumulates the item count for each order, and `percentile` computes distribution statistics from it exactly the way a Timer's duration histogram would — but here applied to a non-time value (item count) rather than milliseconds. The computed `p99` correctly surfaces the outlier bulk order of `15` items, mirroring the same principle from the [RED method](0356-red-method-rate-errors-duration.md)'s duration percentiles: a DistributionSummary reveals the shape and tail of any non-time numeric distribution, not just typical durations.

## 6. Walkthrough

Trace `DistributionSummaryForOrderSizes.main` in order. **First**, the loop calls `recordOrderSize` once for each value in `orderSizes`, appending each to `orderItemCountRecordings` in order — the list ends up holding `[1, 2, 1, 3, 1, 2, 15, 1, 2, 1]`, ten values total.

**Next**, `mean` is computed via `mapToInt(Integer::intValue).average()`, summing all ten values (`1+2+1+3+1+2+15+1+2+1 = 29`) and dividing by `10`, giving `2.9`.

**Then**, `percentile(orderItemCountRecordings, 50)` runs: it copies and sorts the list, producing `[1, 1, 1, 1, 1, 2, 2, 2, 3, 15]`. The index computation is `ceil(0.5 × 10) - 1 = 4`, so `sorted.get(4)` returns `1` — the median order size.

**Then**, `percentile(orderItemCountRecordings, 99)` runs on the same sorted list: the index computation is `ceil(0.99 × 10) - 1 = ceil(9.9) - 1 = 10 - 1 = 9`, so `sorted.get(9)` returns the last (largest) element, `15` — correctly identifying the one bulk order as representative of the top 1% of order sizes.

**Finally**, `main` prints the count, mean, p50, and p99 — the mean (`2.9`) looks unremarkable and only mildly elevated by the outlier, while the p99 (`15`) unambiguously reveals that rare bulk order's exact size, exactly as a Timer's p99 would reveal a rare slow request's exact duration, demonstrating the same distributional insight applied to a completely different kind of measured value.

```
orderSizes: [1,2,1,3,1,2,15,1,2,1]
sorted:     [1,1,1,1,1,2,2,2,3,15]
mean = 29/10 = 2.9        (only mildly affected by the outlier)
p50  = sorted[4] = 1      (typical order size)
p99  = sorted[9] = 15     (correctly reveals the rare bulk order)
```

## 7. Gotchas & takeaways

> Registering a Gauge against a snapshot value taken once, rather than a live value supplier that Micrometer calls fresh each time the metric is read, produces a Gauge that's silently frozen at whatever the value happened to be at registration time — always register Gauges against a function/supplier that reads the *current* live state, not a value captured once upfront.

- Counter (only increases), Gauge (current, fluctuating level), Timer (count + duration distribution), and DistributionSummary (count + non-time value distribution) each model a genuinely different kind of measurement.
- Using the wrong meter type — like a Counter for something that should decrease — produces a metric that looks fine superficially but is meaningless or actively misleading when queried.
- A Timer and a DistributionSummary both give you count plus a percentile distribution; the only real difference is whether the recorded values represent time or something else.
- Choosing the right meter type per measurement is what makes [RED](0356-red-method-rate-errors-duration.md), [USE](0357-use-method-utilization-saturation-errors.md), and custom application metrics actually answer the questions they're meant to answer.
