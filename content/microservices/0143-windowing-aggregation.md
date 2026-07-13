---
card: microservices
gi: 143
slug: windowing-aggregation
title: "Windowing & aggregation"
---

## 1. What it is

Windowing is dividing an unbounded [stream](0138-stream-processing-concepts.md) into finite, bounded chunks — typically by time (every 60 seconds) or by count (every 100 events) — so that an aggregation (a sum, average, count, max) can be computed over a meaningful, finite slice of the stream instead of needing to answer the unanswerable "the average of all events, forever."

## 2. Why & when

An aggregation like "average order value" is meaningless without a boundary: averaged over all time since the system launched, a single early spike or an old, now-irrelevant trend permanently distorts the number, and the value effectively never changes no matter what happens today. Windowing gives the aggregation a meaningful, bounded scope — "average order value in the last 5 minutes" is an actual, useful, continuously-updating answer to a real question, in a way "average order value ever" is not.

Apply windowing to any streaming aggregation where the answer needs to reflect *recent* or *periodic* behavior rather than an all-time running total — real-time dashboards, rate-limiting, anomaly detection, periodic reporting. Skip it only for genuinely unbounded, all-time aggregates where that lack of a boundary is the actual intent (a lifetime total order count, for instance).

## 3. Core concept

Events are bucketed into windows based on their timestamp (or arrival order, for count-based windows), and each window maintains its own independent aggregate; once a window's time boundary (or count) is reached, its final aggregate is emitted and a fresh window begins.

```java
long windowSizeMillis = 60_000; // 1-minute tumbling windows
Map<Long, Double> sumByWindow = new HashMap<>();

void onEvent(Sale sale) {
    long windowStart = (sale.timestampMillis() / windowSizeMillis) * windowSizeMillis; // which window does this belong to?
    sumByWindow.merge(windowStart, sale.amount(), Double::sum); // accumulate WITHIN that window only
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stream of events is divided into three consecutive, non-overlapping 60-second windows; each window independently accumulates its own aggregate total, and older windows do not affect newer ones" >
  <rect x="20" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="75" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Window [0s-60s)</text>
  <text x="110" y="92" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">sum = 145.00</text>

  <rect x="230" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="75" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Window [60s-120s)</text>
  <text x="320" y="92" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">sum = 80.00</text>

  <rect x="440" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="75" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Window [120s-180s)</text>
  <text x="530" y="92" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">sum = 30.00 (still filling)</text>

  <text x="320" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">each window's total is independent -- earlier windows never affect later ones</text>
</svg>

Each tumbling window accumulates and finalizes its own aggregate, unaffected by any other window.

## 5. Runnable example

Scenario: a sales-aggregation stream that starts as an unbounded, ever-growing running total (showing why it becomes meaningless), adds fixed-size tumbling windows so each period gets its own independent total, and finally adds a sliding window to compute a smoother, overlapping "last N seconds" view — a common refinement over non-overlapping tumbling windows.

### Level 1 — Basic

```java
// File: UnboundedRunningTotal.java -- a single, ever-growing total: increasingly
// meaningless as more history accumulates underneath it.
import java.util.*;

public class UnboundedRunningTotal {
    record Sale(double amount, long timestampMillis) {}

    public static void main(String[] args) {
        List<Sale> sales = List.of(
            new Sale(1000.00, 0),      // an early, unusually large spike
            new Sale(10.00, 100_000),
            new Sale(12.00, 200_000),
            new Sale(15.00, 300_000));

        double runningTotal = 0;
        for (Sale s : sales) {
            runningTotal += s.amount();
            System.out.println("At t=" + s.timestampMillis() + ": all-time running total = " + runningTotal);
        }
        System.out.println("The early 1000.00 spike PERMANENTLY dominates this number -- it tells you almost nothing about RECENT activity.");
    }
}
```

**How to run:** `javac UnboundedRunningTotal.java && java UnboundedRunningTotal` (JDK 17+).

Every printed total is dominated by the very first, unusually large sale — there is no way to answer "how are sales doing *right now*" from an all-time running total once enough history has accumulated.

### Level 2 — Intermediate

```java
// File: TumblingWindows.java -- fixed, non-overlapping windows; each gets its OWN
// independent total, so a spike in one window doesn't distort any other.
import java.util.*;

public class TumblingWindows {
    record Sale(double amount, long timestampMillis) {}

    public static void main(String[] args) {
        List<Sale> sales = List.of(
            new Sale(1000.00, 0), new Sale(10.00, 100_000), new Sale(12.00, 200_000), new Sale(15.00, 300_000));
        long windowSizeMillis = 150_000; // 150-second tumbling windows

        Map<Long, Double> sumByWindow = new TreeMap<>();
        for (Sale s : sales) {
            long windowStart = (s.timestampMillis() / windowSizeMillis) * windowSizeMillis;
            sumByWindow.merge(windowStart, s.amount(), Double::sum);
        }

        for (var entry : sumByWindow.entrySet()) {
            System.out.println("Window starting at t=" + entry.getKey() + ": total = " + entry.getValue());
        }
        System.out.println("The 1000.00 spike is CONTAINED to its own window -- later windows are completely unaffected.");
    }
}
```

**How to run:** `javac TumblingWindows.java && java TumblingWindows` (JDK 17+).

Expected output:
```
Window starting at t=0: total = 1000.0
Window starting at t=150000: total = 22.0
Window starting at t=300000: total = 15.0
```

Unlike Level 1, the second and third windows show their own, meaningfully small totals — completely unaffected by the first window's outlier, because each window's aggregate is scoped and independent.

### Level 3 — Advanced

```java
// File: SlidingWindowSmoothing.java -- a sliding window recomputes a "last N
// seconds" aggregate at each new event, giving a smoother, continuously-updated
// view than tumbling windows' abrupt period boundaries.
import java.util.*;

public class SlidingWindowSmoothing {
    record Sale(double amount, long timestampMillis) {}

    public static void main(String[] args) {
        List<Sale> sales = List.of(
            new Sale(10.00, 0), new Sale(15.00, 30_000), new Sale(20.00, 60_000),
            new Sale(12.00, 90_000), new Sale(18.00, 120_000));
        long windowSizeMillis = 90_000; // "last 90 seconds", recomputed at EVERY new event

        List<Sale> seenSoFar = new ArrayList<>();
        for (Sale current : sales) {
            seenSoFar.add(current);
            double windowSum = 0;
            for (Sale s : seenSoFar) {
                if (current.timestampMillis() - s.timestampMillis() <= windowSizeMillis) { // WITHIN the last 90s of `current`
                    windowSum += s.amount();
                }
            }
            System.out.println("At t=" + current.timestampMillis() + ": sliding sum (last 90s) = " + windowSum);
        }
        System.out.println("Each value reflects a SMOOTHLY moving 90-second lookback -- no abrupt reset at a fixed boundary, unlike tumbling windows.");
    }
}
```

**How to run:** `javac SlidingWindowSmoothing.java && java SlidingWindowSmoothing` (JDK 17+).

Expected output:
```
At t=0: sliding sum (last 90s) = 10.0
At t=30000: sliding sum (last 90s) = 25.0
At t=60000: sliding sum (last 90s) = 45.0
At t=90000: sliding sum (last 90s) = 57.0
At t=120000: sliding sum (last 90s) = 65.0
```

## 6. Walkthrough

1. **Level 1** — `runningTotal += s.amount()` accumulates every sale ever seen with no reset point; the printed totals after the first sale are all inflated by the initial 1000.00 outlier forever, no matter how much later, unrelated activity occurs.
2. **Level 2, computing which window an event belongs to** — `(s.timestampMillis() / windowSizeMillis) * windowSizeMillis` performs integer division to find the start of the 150-second bucket a given timestamp falls into, then multiplies back up, a standard technique for mapping a timestamp to its containing fixed-size window.
3. **Level 2, independent accumulation per window** — `sumByWindow.merge(windowStart, s.amount(), Double::sum)` adds each sale's amount only to the entry for its own computed `windowStart`, meaning sales in different windows never contribute to the same running total.
4. **Level 2, the outlier's blast radius contained** — the printed per-window totals show `1000.0` isolated entirely to the `t=0` window, while the `t=150000` and `t=300000` windows show much smaller, more representative totals — directly solving Level 1's problem by giving the aggregate an explicit boundary.
5. **Level 3, the sliding lookback check** — for each `current` sale, the inner loop checks every previously-seen sale `s` and includes it in `windowSum` only if `current.timestampMillis() - s.timestampMillis() <= windowSizeMillis` — meaning the window boundary moves forward with every single new event, rather than being fixed at period starts like `t=0`, `t=150000`, etc.
6. **Level 3, tracing the smooth progression** — at `t=90000`, the check `current.timestampMillis() - s.timestampMillis() <= windowSizeMillis` includes the sale at `t=0` too, since `90000 - 0 = 90000`, which is exactly at the `<= 90000` boundary — so the window sum at that point is `10+15+20+12=57`. At `t=120000`, the same check now *excludes* the sale at `t=0`, since `120000 - 0 = 120000` exceeds `90000`, dropping out of the lookback window for the first time; the sum becomes `15+20+12+18=65`, reflecting that the oldest sale has finally aged out.
7. **Level 3, the inclusive boundary matters** — because the comparison uses `<=` rather than `<`, an event exactly `windowSizeMillis` old is still included; this is a real, consequential choice (inclusive vs. exclusive boundary) that differs between frameworks, and getting it backward silently shifts every window's membership by one edge case.
8. **Level 3, why sliding smooths the picture** — because the window recomputes at every single event rather than only at fixed period boundaries, the sequence of printed sums changes gradually as old sales age out and new ones enter, rather than resetting abruptly to a small number the instant a new tumbling window begins — useful specifically when abrupt period-boundary resets would misrepresent genuinely continuous, ongoing activity.

## 7. Gotchas & takeaways

> **Gotcha:** windowing by event timestamp (as opposed to arrival/processing time) requires deciding how to handle events that arrive late — an event timestamped for a window that has already closed and emitted its final aggregate either gets dropped, triggers a correction to an already-published result, or requires a deliberate grace period before a window is considered truly final; this is a real design decision, not an edge case to ignore.

- Windowing bounds an otherwise-unbounded stream aggregation to a meaningful, finite slice, avoiding the "meaningless because it includes everything, forever" problem of unbounded running totals.
- Tumbling windows are fixed-size, non-overlapping periods; each window's aggregate is independent of every other window's, containing the effect of any single anomalous period.
- Sliding windows recompute a "last N seconds/events" aggregate continuously as new events arrive, producing a smoother, more continuously-updated view than tumbling windows' abrupt period resets.
- The right window type and size depend on what question the aggregate needs to answer: periodic reporting favors tumbling windows aligned to real periods; smooth, continuously-updated views favor sliding windows.
- Late-arriving events relative to an already-closed window are a genuine design decision every windowed system needs to make explicitly, not an edge case that resolves itself.
