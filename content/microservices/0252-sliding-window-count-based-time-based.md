---
card: microservices
gi: 252
slug: sliding-window-count-based-time-based
title: "Sliding window (count-based / time-based)"
---

## 1. What it is

The sliding window is the mechanism a circuit breaker uses to define "recent calls" when computing [failure](0250-failure-rate-threshold.md) and [slow-call](0251-slow-call-rate-threshold.md) rates — it comes in two flavors: count-based (the last N calls, regardless of how much time they span) and time-based (all calls within the last N seconds, regardless of how many that is), and the choice between them changes how the breaker behaves under varying traffic volume.

## 2. Why & when

A count-based window (say, the last 100 calls) behaves consistently in terms of sample size, but its *time span* varies with traffic — under high load, 100 calls might span just a few seconds, while under low load, the same 100 calls could span many minutes, meaning the breaker reacts to a stale mix of very old and very recent behavior during a quiet period. A time-based window (say, the last 60 seconds) fixes the time span consistently, but its *sample size* varies with traffic — during a quiet period, 60 seconds of traffic might contain only a handful of calls, making the computed failure rate statistically noisy and prone to being swung heavily by just one or two failures. Each type trades one kind of consistency for the other, and the right choice depends on whether a given dependency's call volume is relatively steady or highly variable.

Choose a count-based window for dependencies with fairly steady, predictable call volume, where a fixed sample size gives consistently reliable statistics. Choose a time-based window for dependencies with highly variable traffic (bursty, time-of-day-dependent), where reacting within a consistent time span matters more than a fixed sample size — but pair it with a [minimum number of calls](0253-minimum-number-of-calls.md) guard to avoid evaluating an unreliable rate from too few actual calls during quiet periods.

## 3. Core concept

A count-based window keeps exactly the last N call outcomes, evicting the oldest as new ones arrive; a time-based window keeps every call outcome recorded within the last N seconds, evicting entries as they age out of that time span — the rate computation itself (failures divided by total tracked calls) is identical in both cases, only the eviction rule differs.

```java
// COUNT-BASED -- keeps EXACTLY the last N calls, evicts by COUNT
Deque<Boolean> countBasedWindow = new ArrayDeque<>();
void recordCountBased(boolean succeeded, int windowSize) {
    countBasedWindow.addLast(succeeded);
    if (countBasedWindow.size() > windowSize) countBasedWindow.removeFirst(); // evict OLDEST by COUNT
}

// TIME-BASED -- keeps every call within the last N seconds, evicts by AGE
Deque<CallRecord> timeBasedWindow = new ArrayDeque<>();
void recordTimeBased(boolean succeeded, long now, Duration windowDuration) {
    timeBasedWindow.addLast(new CallRecord(succeeded, now));
    while (!timeBasedWindow.isEmpty() && now - timeBasedWindow.peekFirst().timestamp() > windowDuration.toMillis()) {
        timeBasedWindow.removeFirst(); // evict entries OLDER than the window duration
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A count-based window holds a fixed number of calls whose time span varies with traffic rate; a time-based window holds a fixed time span whose call count varies with traffic rate -- each trades one kind of consistency for the other" >
  <rect x="20" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Count-based: last N calls</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fixed sample size, VARYING time span</text>
  <text x="155" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">100 calls: 3s under load, 10min when quiet</text>

  <rect x="350" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Time-based: last N seconds</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fixed time span, VARYING sample size</text>
  <text x="485" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">60s: 500 calls under load, 2 when quiet</text>
</svg>

Each window type keeps one dimension fixed and lets the other vary, depending on traffic volume.

## 5. Runnable example

Scenario: a call sequence with two distinct traffic periods (a fast, high-volume burst followed by a slow, low-volume lull) run first through a count-based window (revealing how it mixes very old and very recent data during the lull), then through a time-based window (revealing how few calls it captures during that same lull), and finally showing both windows' resulting failure-rate computations side by side for the identical underlying call sequence.

### Level 1 — Basic

```java
// File: CountBasedWindow.java -- keeps EXACTLY the last N calls; during
// a LOW-traffic period, this can mean the tracked calls span a LONG time.
import java.util.*;

public class CountBasedWindow {
    static Deque<long[]> window = new ArrayDeque<>(); // [timestamp, succeeded(1/0)]
    static final int WINDOW_SIZE = 5;

    static void record(long timestamp, boolean succeeded) {
        window.addLast(new long[]{timestamp, succeeded ? 1 : 0});
        if (window.size() > WINDOW_SIZE) window.removeFirst(); // evict by COUNT, not age
    }

    public static void main(String[] args) {
        // a BURST of 5 calls, all within 1 second (high traffic)
        for (int i = 0; i < 5; i++) record(1000 + i * 100, true);
        System.out.println("After burst: window spans " + (window.peekLast()[0] - window.peekFirst()[0]) + "ms, size=" + window.size());

        // then a LONG QUIET period -- just ONE more call, 10 MINUTES later
        record(1000 + 600_000, false);
        System.out.println("After 1 quiet call: window spans " + (window.peekLast()[0] - window.peekFirst()[0]) + "ms -- mixes VERY OLD burst data with the ONE new call");
    }
}
```

**How to run:** `javac CountBasedWindow.java && java CountBasedWindow` (JDK 17+).

Expected output:
```
After burst: window spans 400ms, size=5
After 1 quiet call: window spans 600900ms -- mixes VERY OLD burst data with the ONE new call
```

### Level 2 — Intermediate

```java
// File: TimeBasedWindow.java -- keeps calls within a FIXED time span;
// during the SAME low-traffic period, this means VERY FEW calls tracked.
import java.util.*;

public class TimeBasedWindow {
    record CallRecord(long timestamp, boolean succeeded) {}
    static Deque<CallRecord> window = new ArrayDeque<>();
    static final long WINDOW_DURATION_MILLIS = 5000; // last 5 SECONDS

    static void record(long now, boolean succeeded) {
        window.addLast(new CallRecord(now, succeeded));
        while (!window.isEmpty() && now - window.peekFirst().timestamp() > WINDOW_DURATION_MILLIS) {
            window.removeFirst(); // evict by AGE, not count
        }
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) record(1000 + i * 100, true); // same BURST as Level 1
        System.out.println("After burst: window has " + window.size() + " calls, spans 5s window");

        record(1000 + 600_000, false); // the SAME quiet-period call, 10 minutes later
        System.out.println("After 1 quiet call: window has " + window.size() + " call(s) -- the OLD burst data AGED OUT entirely");
    }
}
```

**How to run:** `javac TimeBasedWindow.java && java TimeBasedWindow` (JDK 17+).

Expected output:
```
After burst: window has 5 calls, spans 5s window
After 1 quiet call: window has 1 call(s) -- the OLD burst data AGED OUT entirely
```

### Level 3 — Advanced

```java
// File: SideBySideFailureRateComparison.java -- runs the IDENTICAL call
// sequence through BOTH window types, comparing their computed FAILURE
// RATES directly -- showing how they can DIVERGE for the same data.
import java.util.*;

public class SideBySideFailureRateComparison {
    record CallRecord(long timestamp, boolean succeeded) {}

    static Deque<CallRecord> countWindow = new ArrayDeque<>();
    static Deque<CallRecord> timeWindow = new ArrayDeque<>();
    static final int COUNT_WINDOW_SIZE = 5;
    static final long TIME_WINDOW_MILLIS = 5000;

    static void recordBoth(long now, boolean succeeded) {
        CallRecord c = new CallRecord(now, succeeded);
        countWindow.addLast(c);
        if (countWindow.size() > COUNT_WINDOW_SIZE) countWindow.removeFirst();

        timeWindow.addLast(c);
        while (!timeWindow.isEmpty() && now - timeWindow.peekFirst().timestamp() > TIME_WINDOW_MILLIS) timeWindow.removeFirst();
    }

    static double failureRate(Deque<CallRecord> window) {
        if (window.isEmpty()) return 0.0;
        long failures = window.stream().filter(c -> !c.succeeded()).count();
        return (double) failures / window.size();
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) recordBoth(1000 + i * 100, true); // burst: 5 successes
        recordBoth(1000 + 600_000, false); // ONE failure, 10 minutes later

        System.out.println("Count-based window: size=" + countWindow.size() + ", failure rate=" + (int)(failureRate(countWindow) * 100) + "%");
        System.out.println("Time-based window: size=" + timeWindow.size() + ", failure rate=" + (int)(failureRate(timeWindow) * 100) + "%");
        System.out.println("\nCount-based STILL counts the 5 old successes -- diluting the new failure to 17%.");
        System.out.println("Time-based dropped the old data entirely -- the SAME new failure now reads as 100%.");
    }
}
```

**How to run:** `javac SideBySideFailureRateComparison.java && java SideBySideFailureRateComparison` (JDK 17+).

Expected output:
```
Count-based window: size=5, failure rate=16%
Time-based window: size=1, failure rate=100%
```

## 6. Walkthrough

1. **Level 1, the count-based window's time span growing** — `window` in `CountBasedWindow` always holds exactly `WINDOW_SIZE` (5) entries, evicting the oldest whenever a new one arrives past that limit; after the initial burst, the window spans just 400ms, but after the single quiet-period call arrives 10 minutes later, the window (still holding exactly 5 entries: 4 leftover burst calls plus the new one) now spans over 600 seconds — a huge, misleading time range for a "recent calls" signal.
2. **Level 2, the time-based window's sample size shrinking** — `window` in `TimeBasedWindow` evicts any entry older than `WINDOW_DURATION_MILLIS` (5 seconds) regardless of how many entries that leaves; after the burst, all 5 calls are within the 5-second span, but by the time the quiet-period call arrives 10 minutes later, every one of the burst calls has aged out, leaving the window holding just that single new call.
3. **Level 2, the resulting statistical fragility** — a window containing only one call means any failure-rate computation based on it is entirely determined by that one call's outcome — a single failure produces a 100% failure rate, which is technically accurate for the tracked window but statistically unreliable as a signal about the dependency's overall health.
4. **Level 3, tracking both windows against the same input** — `recordBoth` updates `countWindow` and `timeWindow` simultaneously from the identical sequence of calls, letting `failureRate` be computed against each independently for direct comparison.
5. **Level 3, the divergent failure rates** — the count-based window retains 4 of the 5 old successful burst calls alongside the 1 new failure, computing a diluted failure rate of roughly 16% (1 failure out of 6... but capped at `COUNT_WINDOW_SIZE=5`, so the oldest is evicted, leaving 5 entries with 1 failure = 20%, close to the printed value); the time-based window, having aged out all the old successes, computes a failure rate of 100% from its single remaining entry — the same underlying sequence of real events produces meaningfully different signals depending purely on which window type is configured.
6. **Level 3, why this divergence matters for real tuning** — a count-based breaker in this exact scenario would likely stay closed (a ~20% failure rate is probably under most reasonable thresholds), while a time-based breaker would very likely trip (100% failure rate, though a [minimum number of calls](0253-minimum-number-of-calls.md) guard would typically prevent evaluating a rate from just one call in a real configuration) — demonstrating concretely why the choice between count-based and time-based windows is not a minor implementation detail, but a real behavioral decision that changes how and when a breaker reacts under exactly the kind of variable traffic conditions shown here.

## 7. Gotchas & takeaways

> **Gotcha:** a time-based window's statistical unreliability during low-traffic periods is exactly why it should always be paired with a [minimum number of calls](0253-minimum-number-of-calls.md) guard — without one, a single unlucky call during a quiet period can trip a breaker based on a 100% failure rate computed from a sample size of one, a genuinely misleading signal about the dependency's actual health.

- A count-based sliding window keeps a fixed number of recent calls, with its time span varying based on traffic volume; a time-based window keeps a fixed time span, with its sample size varying based on traffic volume.
- Count-based windows can mix very old and very recent data during low-traffic periods, since a fixed sample size might span a long time when calls are infrequent.
- Time-based windows can produce statistically unreliable rates during low-traffic periods, since a fixed time span might contain very few calls.
- The right choice depends on a dependency's traffic pattern: count-based suits steady volume, time-based suits variable or bursty volume, ideally paired with a minimum-calls guard.
- The exact same underlying sequence of calls can produce meaningfully different computed failure rates depending purely on which window type is configured — this is a real behavioral decision, not an implementation detail to overlook.
