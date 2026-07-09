---
card: java
gi: 543
slug: duration
title: Duration
---

## 1. What it is

`Duration` represents an amount of time measured in seconds and nanoseconds — "3 hours," "500 milliseconds," "90 minutes" — as opposed to `Period` (a separate `java.time` type not covered here), which measures time in calendar terms like years, months, and days. `Duration` is the right tool for machine-precision, exact time spans: timeouts, elapsed processing time, delays — anything where "exactly how many seconds" matters more than "how many calendar days."

## 2. Why & when

You reach for `Duration` whenever you're measuring or specifying an exact time span rather than a calendar-based one — a request timeout of 30 seconds, a cache expiring after 5 minutes, the elapsed time between two `Instant`s (see [[instant]]) or two `LocalDateTime`s (see [[localdatetime]]). It pairs naturally with `Instant.plus(duration)`/`minus(duration)` for computing a new point in time, and with `Duration.between(start, end)` for measuring elapsed time between two existing points. Unlike `Period`, which is calendar-aware (a "month" can be 28-31 days depending on which month), `Duration` is always a fixed, unambiguous number of seconds — exactly what's needed for precise timing logic.

## 3. Core concept

```java
import java.time.*;

Duration thirtySeconds = Duration.ofSeconds(30);
Duration fiveMinutes = Duration.ofMinutes(5);
Duration combined = thirtySeconds.plus(fiveMinutes); // PT5M30S -- 5 minutes 30 seconds

Instant now = Instant.now();
Instant later = now.plus(fiveMinutes); // add a Duration to an Instant

Duration elapsed = Duration.between(now, later); // PT5M -- measure elapsed time between two points

long totalSeconds = elapsed.toSeconds(); // 300
long totalMillis = elapsed.toMillis();   // 300000
```

`Duration` is built with `of*` factory methods (`ofSeconds`, `ofMinutes`, `ofHours`, ...), combined with `plus`/`minus`, applied to a point-in-time value with `Instant.plus(duration)`, and measured between two points with `Duration.between(...)`.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Duration measures an exact span of time in seconds and nanoseconds, independent of calendar concepts">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="180" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Instant t1</text>
  <line x1="210" y1="37" x2="330" y2="37" stroke="#6db33f" stroke-width="2" marker-end="url(#arrowDU)"/>
  <text x="270" y="27" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Duration.between</text>
  <rect x="340" y="20" width="180" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="430" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Instant t2</text>
  <text x="20" y="85" fill="#8b949e" font-size="10" font-family="sans-serif">The gap between t1 and t2, measured in exact seconds/nanoseconds -- a Duration.</text>
  <defs><marker id="arrowDU" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

`Duration.between(t1, t2)` measures the exact elapsed time between two points, independent of any calendar concept like months or years.

## 5. Runnable example

Scenario: implementing a request timeout and retry-delay system for a network client — evolved from basic duration construction and arithmetic, through measuring real elapsed time between operations, to a version implementing exponential backoff with a capped maximum delay.

### Level 1 — Basic

```java
import java.time.*;

public class DurationBasic {
    public static void main(String[] args) {
        Duration timeout = Duration.ofSeconds(30);
        Duration retryDelay = Duration.ofMillis(500);

        System.out.println("Timeout: " + timeout);
        System.out.println("Retry delay: " + retryDelay);
        System.out.println("Timeout in millis: " + timeout.toMillis());
    }
}
```

**How to run:** `java DurationBasic.java`

Expected output:
```
Timeout: PT30S
Retry delay: PT0.5S
Timeout in millis: 30000
```

`Duration.ofSeconds(30)` and `Duration.ofMillis(500)` construct exact time spans. `Duration`'s `toString()` uses the ISO-8601 duration format (`PT30S` means "period of time, 30 seconds"; `PT0.5S` means "0.5 seconds"). `.toMillis()` converts the duration into a plain millisecond count for use with APIs that expect a raw number.

### Level 2 — Intermediate

```java
import java.time.*;

public class DurationMeasured {
    static void simulateWork() {
        try {
            Thread.sleep(150); // simulate some work taking roughly 150ms
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        Instant start = Instant.now();
        simulateWork();
        Instant end = Instant.now();

        Duration elapsed = Duration.between(start, end);

        System.out.println("Work took at least 150ms: " + (elapsed.toMillis() >= 150));
        System.out.println("Elapsed duration is positive: " + (!elapsed.isNegative() && !elapsed.isZero()));
    }
}
```

**How to run:** `java DurationMeasured.java`

Expected output:
```
Work took at least 150ms: true
Elapsed duration is positive: true
```

The real-world concern this adds: measuring **actual** elapsed wall-clock time around a real operation, rather than just constructing a duration from a literal. `Duration.between(start, end)` computes the genuine elapsed time between two `Instant`s captured before and after `simulateWork()`. Since exact millisecond timing varies run to run (system scheduling isn't perfectly precise), the checks here verify *properties* of the result (`>= 150ms`, positive) rather than asserting an exact millisecond count, which would be unreliable to hardcode.

### Level 3 — Advanced

```java
import java.time.*;
import java.util.*;

public class DurationExponentialBackoff {
    static final Duration BASE_DELAY = Duration.ofSeconds(1);
    static final Duration MAX_DELAY = Duration.ofSeconds(30);

    static Duration backoffDelay(int attemptNumber) {
        // Exponential: base * 2^attempt, capped at MAX_DELAY.
        Duration exponential = BASE_DELAY.multipliedBy((long) Math.pow(2, attemptNumber));
        return exponential.compareTo(MAX_DELAY) > 0 ? MAX_DELAY : exponential;
    }

    public static void main(String[] args) {
        for (int attempt = 0; attempt < 7; attempt++) {
            Duration delay = backoffDelay(attempt);
            System.out.println("Attempt " + attempt + ": wait " + delay.getSeconds() + "s");
        }
    }
}
```

**How to run:** `java DurationExponentialBackoff.java`

Expected output:
```
Attempt 0: wait 1s
Attempt 1: wait 2s
Attempt 2: wait 4s
Attempt 3: wait 8s
Attempt 4: wait 16s
Attempt 5: wait 30s
Attempt 6: wait 30s
```

This implements a real production pattern — exponential backoff with a cap — entirely using `Duration` arithmetic. `BASE_DELAY.multipliedBy(2^attempt)` doubles the delay each attempt (`1s, 2s, 4s, 8s, 16s, 32s, ...`), and `.compareTo(MAX_DELAY)` checks whether the computed delay would exceed the `30`-second cap, substituting `MAX_DELAY` whenever it would — attempts `5` and `6` would naturally compute to `32s` and `64s`, but both are correctly clamped down to the `30`-second maximum.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. The `for` loop iterates `attempt` from `0` to `6`.

For `attempt = 0`: `backoffDelay(0)` computes `exponential = BASE_DELAY.multipliedBy((long) Math.pow(2, 0))`. `Math.pow(2, 0)` is `1.0`, cast to `long` gives `1`. `BASE_DELAY.multipliedBy(1)` is `Duration.ofSeconds(1)` unchanged. `exponential.compareTo(MAX_DELAY)`: comparing `1` second to `30` seconds, `1 < 30`, so `compareTo` returns a negative number, which is not `> 0` — the exponential value is returned as-is, `1` second. Printed as `"Attempt 0: wait 1s"`.

For `attempt = 1`: `Math.pow(2, 1) = 2.0`, cast to `2`. `BASE_DELAY.multipliedBy(2)` is `2` seconds. `2 < 30`, not exceeding the cap, returned as-is: `"Attempt 1: wait 2s"`.

This continues doubling: `attempt=2` gives `4` seconds, `attempt=3` gives `8` seconds, `attempt=4` gives `16` seconds — each still under the `30`-second cap.

For `attempt = 5`: `Math.pow(2, 5) = 32.0`, cast to `32`. `BASE_DELAY.multipliedBy(32)` is `32` seconds. `exponential.compareTo(MAX_DELAY)`: comparing `32` seconds to `30` seconds, `32 > 30`, so `compareTo` returns a positive number, which *is* `> 0` — the ternary now returns `MAX_DELAY` instead of `exponential`. Printed as `"Attempt 5: wait 30s"`, not the naturally-computed `32s`.

For `attempt = 6`: `Math.pow(2, 6) = 64.0`, cast to `64`. `BASE_DELAY.multipliedBy(64)` is `64` seconds, far exceeding `30`. The cap applies again: `"Attempt 6: wait 30s"`.

```
attempt 0: 1 * 2^0 = 1s   -> 1 < 30  -> 1s
attempt 1: 1 * 2^1 = 2s   -> 2 < 30  -> 2s
attempt 2: 1 * 2^2 = 4s   -> 4 < 30  -> 4s
attempt 3: 1 * 2^3 = 8s   -> 8 < 30  -> 8s
attempt 4: 1 * 2^4 = 16s  -> 16 < 30 -> 16s
attempt 5: 1 * 2^5 = 32s  -> 32 > 30 -> CAPPED to 30s
attempt 6: 1 * 2^6 = 64s  -> 64 > 30 -> CAPPED to 30s
```

The full sequence printed is `1s, 2s, 4s, 8s, 16s, 30s, 30s` — a classic exponential backoff curve that grows quickly at first, then flattens out at the configured maximum, entirely computed through `Duration`'s arithmetic and comparison methods (`multipliedBy`, `compareTo`) rather than manual second-counting.

## 7. Gotchas & takeaways

> `Duration` and `Period` are easy to confuse but serve different purposes: `Duration` is a fixed number of seconds (exact, unambiguous), while `Period` is calendar-based (a "month" varies in actual length depending on which month it is). Using `Duration.ofDays(30)` to mean "one month" is subtly wrong for calendar purposes — it's always exactly `30 * 24` hours, not "the same calendar date next month," which could be `28`, `29`, `30`, or `31` days later. For calendar-based spans, `Period` is the correct type; `Duration` is for machine-precision time spans.

- `Duration` represents an exact time span in seconds and nanoseconds — timeouts, delays, elapsed processing time — as opposed to calendar-based spans (`Period`).
- `Duration.between(start, end)` measures the exact elapsed time between two point-in-time values (`Instant`, `LocalDateTime`, or other temporal types).
- `Duration` supports arithmetic (`plus`, `minus`, `multipliedBy`, `dividedBy`) and comparison (`compareTo`, `isNegative`, `isZero`), making it composable for patterns like exponential backoff.
- `Duration.toString()` uses ISO-8601 duration format (`PT30S`, `PT1H30M`) — useful for serialization, though `.toSeconds()`/`.toMillis()`/`.getSeconds()` are typically more convenient for arithmetic or logging.
- Never use `Duration.ofDays(...)` to mean "calendar months" or "calendar years" — a `Duration` is always a fixed count of exact time, not a calendar-aware span; use `Period` when calendar semantics genuinely matter.
