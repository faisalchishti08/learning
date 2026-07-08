---
card: java
gi: 413
slug: timeunit-enum
title: TimeUnit enum
---

## 1. What it is

`TimeUnit` (in `java.util.concurrent`) is an enum representing units of time — `NANOSECONDS`, `MICROSECONDS`, `MILLISECONDS`, `SECONDS`, `MINUTES`, `HOURS`, `DAYS` — designed to make time-based API calls (`sleep`, `await`, `get` with timeouts) self-documenting and to make converting between units straightforward and mistake-resistant. Instead of a bare `long` parameter that could mean anything, methods like `future.get(5, TimeUnit.SECONDS)` state their unit explicitly right at the call site.

## 2. Why & when

Before `TimeUnit`, time-based parameters were plain `long` values in an implicit unit (usually milliseconds), and it was on you to remember which unit each API expected, and to manually multiply or divide when converting — a classic source of bugs (accidentally sleeping for 5000 seconds instead of 5000 milliseconds because two different APIs assumed different units). `TimeUnit` fixes both problems: the unit is explicit in every call, and `TimeUnit` itself provides conversion methods (`toMillis()`, `toSeconds()`, `convert()`) so you never have to hand-write a multiplication and risk an off-by-a-factor-of-1000 error.

You'll see `TimeUnit` everywhere across `java.util.concurrent`: `ExecutorService.awaitTermination(timeout, unit)`, `Future.get(timeout, unit)`, `Thread.sleep` doesn't take one directly but `TimeUnit.SECONDS.sleep(n)` is a clearer alternative, `ScheduledExecutorService.schedule(task, delay, unit)`, and many more — anywhere a duration needs to be passed explicitly.

## 3. Core concept

```java
import java.util.concurrent.TimeUnit;

TimeUnit.SECONDS.sleep(2);              // clearer than Thread.sleep(2000) -- the unit is explicit

long millis = TimeUnit.SECONDS.toMillis(30);  // 30_000 -- convert seconds to milliseconds
long seconds = TimeUnit.MINUTES.toSeconds(5); // 300 -- convert minutes to seconds

// convert(sourceDuration, sourceUnit): convert 90 seconds into minutes
long minutes = TimeUnit.MINUTES.convert(90, TimeUnit.SECONDS); // 1 (integer division, truncates)
```

`TimeUnit` conversions between smaller and larger units use integer arithmetic, so converting from a smaller unit to a larger one truncates rather than rounds — `TimeUnit.MINUTES.convert(90, TimeUnit.SECONDS)` gives `1`, not `1.5`, because 90 seconds is 1.5 minutes and the result type is a whole `long`.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TimeUnit values ordered from smallest to largest, with conversion methods moving between them">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">TimeUnit, smallest to largest:</text>
  <text x="30" y="55" fill="#79c0ff" font-size="10" font-family="sans-serif">NANOSECONDS -&gt; MICROSECONDS -&gt; MILLISECONDS -&gt; SECONDS -&gt; MINUTES -&gt; HOURS -&gt; DAYS</text>

  <rect x="30" y="75" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SECONDS.toMillis(30)</text>
  <text x="120" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">= 30000 (exact, multiply up)</text>

  <rect x="420" y="75" width="180" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="510" y="97" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">MINUTES.convert(90, SECONDS)</text>
  <text x="510" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">= 1 (truncated, not 1.5)</text>
</svg>

Converting to a smaller unit is always exact; converting to a larger unit truncates any remainder.

## 5. Runnable example

Scenario: a retry mechanism with exponential backoff for a flaky network call — the same retry loop, evolved from hardcoded millisecond sleeps, through explicit `TimeUnit`-based waits, to a version that converts a configured backoff into whatever unit an external timeout API expects.

### Level 1 — Basic

```java
public class RetryHardcodedMillis {
    static boolean attemptCall(int attempt) {
        return attempt == 3; // simulate: succeeds only on the 3rd try
    }

    public static void main(String[] args) throws InterruptedException {
        for (int attempt = 1; attempt <= 5; attempt++) {
            if (attemptCall(attempt)) {
                System.out.println("Succeeded on attempt " + attempt);
                return;
            }
            System.out.println("Attempt " + attempt + " failed, waiting...");
            Thread.sleep(1000); // 1000 what? milliseconds -- but the reader has to know that convention
        }
    }
}
```

**How to run:** `java RetryHardcodedMillis.java`

`Thread.sleep(1000)` works, but a bare number leaves the unit implicit — anyone reading it has to already know `Thread.sleep` takes milliseconds; a similarly-shaped call to a different API might expect seconds instead, and nothing here guards against that confusion.

### Level 2 — Intermediate

```java
import java.util.concurrent.TimeUnit;

public class RetryExplicitTimeUnit {
    static boolean attemptCall(int attempt) {
        return attempt == 3;
    }

    public static void main(String[] args) throws InterruptedException {
        for (int attempt = 1; attempt <= 5; attempt++) {
            if (attemptCall(attempt)) {
                System.out.println("Succeeded on attempt " + attempt);
                return;
            }
            System.out.println("Attempt " + attempt + " failed, waiting 1 second...");
            TimeUnit.SECONDS.sleep(1); // unit is unambiguous right at the call site
        }
    }
}
```

**How to run:** `java RetryExplicitTimeUnit.java`

`TimeUnit.SECONDS.sleep(1)` says exactly what it means with no implicit convention to remember — the unit travels with the value, making the code self-documenting and eliminating an entire category of "which unit did this API expect" bugs.

### Level 3 — Advanced

```java
import java.util.concurrent.TimeUnit;

public class RetryExponentialBackoff {
    static boolean attemptCall(int attempt) {
        return attempt == 4;
    }

    public static void main(String[] args) throws InterruptedException {
        long baseDelay = 1; // configured in SECONDS, the unit most humans think in
        TimeUnit configUnit = TimeUnit.SECONDS;

        for (int attempt = 1; attempt <= 5; attempt++) {
            if (attemptCall(attempt)) {
                System.out.println("Succeeded on attempt " + attempt);
                return;
            }

            long backoffInConfigUnit = baseDelay * (1L << (attempt - 1)); // 1, 2, 4, 8, 16 seconds
            long backoffInMillis = TimeUnit.MILLISECONDS.convert(backoffInConfigUnit, configUnit);

            System.out.println("Attempt " + attempt + " failed, backing off "
                + backoffInConfigUnit + " " + configUnit + " (" + backoffInMillis + " ms)");

            TimeUnit.MILLISECONDS.sleep(backoffInMillis);
        }
    }
}
```

**How to run:** `java RetryExponentialBackoff.java`

The backoff is configured in `SECONDS` (human-friendly), but `TimeUnit.MILLISECONDS.convert(backoffInConfigUnit, configUnit)` cleanly converts it to whatever unit the actual sleep call needs — this pattern (configure in one unit, convert to whatever an API demands) is exactly why `TimeUnit` exists: the conversion logic lives in one place and cannot silently drift out of sync.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `baseDelay = 1` and `configUnit = TimeUnit.SECONDS` represent "the backoff is configured in seconds, doubling each attempt."

**Attempt 1:** `attemptCall(1)` returns `false` (only attempt 4 succeeds). `backoffInConfigUnit = 1 * (1L << 0) = 1` (1 second). `TimeUnit.MILLISECONDS.convert(1, TimeUnit.SECONDS)` converts 1 second into 1000 milliseconds. The message prints `"backing off 1 SECONDS (1000 ms)"`, and `TimeUnit.MILLISECONDS.sleep(1000)` pauses for 1 second.

**Attempt 2:** `backoffInConfigUnit = 1 * (1L << 1) = 2` seconds, converting to 2000ms — the exponential doubling (`1L << (attempt - 1)`, i.e. `2^(attempt-1)`) means the delay sequence is 1, 2, 4, 8, 16 seconds across attempts 1 through 5. The program sleeps 2 seconds.

**Attempt 3:** `backoffInConfigUnit = 4` seconds (4000ms), sleeps 4 seconds.

**Attempt 4:** `attemptCall(4)` returns `true` this time — the loop's `if` branch fires, printing `"Succeeded on attempt 4"`, and `return` exits `main` immediately, without ever computing or sleeping through attempt 4's backoff (since success is checked *before* the backoff logic in each iteration).

Expected output:
```
Attempt 1 failed, backing off 1 SECONDS (1000 ms)
Attempt 2 failed, backing off 2 SECONDS (2000 ms)
Attempt 3 failed, backing off 4 SECONDS (4000 ms)
Succeeded on attempt 4
```

## 7. Gotchas & takeaways

> `TimeUnit.convert()` (and the `toXxx()` shorthand methods) use **integer division when converting to a larger unit**, which **truncates** rather than rounds. `TimeUnit.MINUTES.convert(90, TimeUnit.SECONDS)` returns `1`, not `1.5` or `2` — always convert to the smallest unit you actually need for a calculation if you care about precision, and only convert up to a larger unit for display or logging purposes.

- `TimeUnit` makes duration parameters self-documenting — the unit travels with the value instead of being an implicit, easy-to-misremember convention.
- `TimeUnit.X.sleep(n)` is a clearer, equivalent alternative to `Thread.sleep(millis)` when you want the unit explicit in the code.
- `toMillis()`, `toSeconds()`, `toMinutes()`, etc. convert *from* the unit you called them on *to* that specific target unit.
- `unit.convert(sourceDuration, sourceUnit)` is the general form: convert *from* `sourceUnit` *to* `unit` — read it as "how many of *me* is this amount of *that*."
- `TimeUnit` is used throughout `java.util.concurrent` — `awaitTermination`, `Future.get`, `ScheduledExecutorService.schedule`, `Semaphore.tryAcquire`, and more all take a `(duration, TimeUnit)` pair for exactly this reason.
