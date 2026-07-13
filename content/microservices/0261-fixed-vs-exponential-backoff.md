---
card: microservices
gi: 261
slug: fixed-vs-exponential-backoff
title: "Fixed vs exponential backoff"
---

## 1. What it is

Backoff is the wait time inserted between retry attempts; fixed backoff waits the same duration before every retry, while exponential backoff multiplies the wait duration by a growing factor after each successive failure — the difference determines how quickly retry attempts arrive during a sustained problem, and how much load a struggling dependency receives while it's trying to recover.

## 2. Why & when

Retrying with no delay at all (attempting again immediately after a failure) can actually make a struggling dependency's situation worse — a burst of immediate retries arriving right on top of the original request adds load to a system that's already showing signs of difficulty, precisely when it can least afford it. Fixed backoff introduces a consistent pause between attempts, which helps somewhat, but under a sustained outage affecting many concurrent callers, a fixed delay means every caller retries on the same, predictable cadence, potentially synchronizing into repeated waves of simultaneous load. Exponential backoff addresses both concerns: the delay grows with each successive failure (1s, 2s, 4s, 8s...), giving a struggling dependency progressively more breathing room the longer a problem persists, naturally easing off exactly when a sustained issue is indicated rather than continuing to hammer it at a constant rate.

Use fixed backoff for simple cases where the retry window is short and the dependency's failure is expected to be brief and isolated. Use exponential backoff for anything where a sustained outage is plausible and where reducing load on a struggling dependency over time genuinely matters — which is the more common, more defensible default for production systems calling external dependencies.

## 3. Core concept

Fixed backoff waits `delay` before every retry, regardless of how many attempts have already failed; exponential backoff computes the wait as `baseDelay * multiplier^(attemptNumber - 1)`, so each successive failure produces a longer wait than the one before it, typically capped at some maximum to avoid the delay growing without bound.

```java
// FIXED backoff -- the SAME wait, every single time
long fixedDelay(int attemptNumber) { return 1000; } // always 1 second

// EXPONENTIAL backoff -- GROWS with each successive failure
long exponentialDelay(int attemptNumber, long baseDelayMillis, double multiplier, long maxDelayMillis) {
    long delay = (long) (baseDelayMillis * Math.pow(multiplier, attemptNumber - 1));
    return Math.min(delay, maxDelayMillis); // CAPPED -- doesn't grow forever
}
// attempt 1: 1000ms, attempt 2: 2000ms, attempt 3: 4000ms, attempt 4: 8000ms... (multiplier=2, capped at some max)
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fixed backoff produces the identical delay before every retry attempt, forming a flat line; exponential backoff produces a delay that roughly doubles with each successive attempt, forming a rapidly climbing curve that gives a struggling dependency progressively more relief" >
  <line x1="40" y1="140" x2="40" y2="20" stroke="#8b949e"/>
  <line x1="40" y1="140" x2="600" y2="140" stroke="#8b949e"/>
  <text x="20" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">delay</text>
  <text x="580" y="155" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">attempt #</text>

  <line x1="60" y1="120" x2="580" y2="120" stroke="#8b949e" stroke-width="1.5"/>
  <text x="500" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fixed -- SAME every time</text>

  <path d="M 60 130 L 160 110 L 260 75 L 360 40 L 460 25" stroke="#6db33f" fill="none" stroke-width="2"/>
  <text x="500" y="35" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">exponential -- grows each attempt</text>
</svg>

Exponential backoff's growing delay gives a struggling dependency progressively more relief as failures continue.

## 5. Runnable example

Scenario: a fixed-backoff retry that keeps hammering a struggling dependency at a constant rate regardless of how long the problem persists, refactored to exponential backoff that eases off progressively as failures continue, and finally demonstrating a capped exponential backoff, showing the delay growth being bounded to a reasonable maximum rather than growing without limit for a very long-running failure.

### Level 1 — Basic

```java
// File: FixedBackoff.java -- the SAME delay before EVERY retry,
// regardless of how many attempts have already failed.
public class FixedBackoff {
    static final long FIXED_DELAY_MILLIS = 1000;

    static long delayForAttempt(int attemptNumber) { return FIXED_DELAY_MILLIS; } // ALWAYS the same

    public static void main(String[] args) {
        for (int attempt = 1; attempt <= 5; attempt++) {
            System.out.println("Before attempt " + attempt + ": wait " + delayForAttempt(attempt) + "ms");
        }
        long totalWait = 0;
        for (int attempt = 1; attempt <= 5; attempt++) totalWait += delayForAttempt(attempt);
        System.out.println("Total wait across 5 attempts: " + totalWait + "ms -- the load is EVENLY spread, never easing off.");
    }
}
```

**How to run:** `javac FixedBackoff.java && java FixedBackoff` (JDK 17+).

Expected output:
```
Before attempt 1: wait 1000ms
Before attempt 2: wait 1000ms
Before attempt 3: wait 1000ms
Before attempt 4: wait 1000ms
Before attempt 5: wait 1000ms
Total wait across 5 attempts: 5000ms -- the load is EVENLY spread, never easing off.
```

### Level 2 — Intermediate

```java
// File: ExponentialBackoff.java -- the delay GROWS with each successive
// attempt, easing off load on a STRUGGLING dependency over time.
public class ExponentialBackoff {
    static final long BASE_DELAY_MILLIS = 1000;
    static final double MULTIPLIER = 2.0;

    static long delayForAttempt(int attemptNumber) {
        return (long) (BASE_DELAY_MILLIS * Math.pow(MULTIPLIER, attemptNumber - 1)); // GROWS each time
    }

    public static void main(String[] args) {
        for (int attempt = 1; attempt <= 5; attempt++) {
            System.out.println("Before attempt " + attempt + ": wait " + delayForAttempt(attempt) + "ms");
        }
        long totalWait = 0;
        for (int attempt = 1; attempt <= 5; attempt++) totalWait += delayForAttempt(attempt);
        System.out.println("Total wait across 5 attempts: " + totalWait + "ms -- the LATER attempts arrive MUCH more sparsely, easing pressure.");
    }
}
```

**How to run:** `javac ExponentialBackoff.java && java ExponentialBackoff` (JDK 17+).

Expected output:
```
Before attempt 1: wait 1000ms
Before attempt 2: wait 2000ms
Before attempt 3: wait 4000ms
Before attempt 4: wait 8000ms
Before attempt 5: wait 16000ms
Total wait across 5 attempts: 31000ms -- the LATER attempts arrive MUCH more sparsely, easing pressure.
```

### Level 3 — Advanced

```java
// File: CappedExponentialBackoff.java -- adds a MAXIMUM delay CAP --
// the delay grows exponentially at FIRST, but STOPS growing once it
// hits a sensible ceiling, for a LONG-running failure scenario.
public class CappedExponentialBackoff {
    static final long BASE_DELAY_MILLIS = 1000;
    static final double MULTIPLIER = 2.0;
    static final long MAX_DELAY_MILLIS = 10_000; // a REASONABLE ceiling -- never wait longer than this between attempts

    static long delayForAttempt(int attemptNumber) {
        long uncappedDelay = (long) (BASE_DELAY_MILLIS * Math.pow(MULTIPLIER, attemptNumber - 1));
        return Math.min(uncappedDelay, MAX_DELAY_MILLIS); // CAPPED -- never exceeds MAX_DELAY_MILLIS
    }

    public static void main(String[] args) {
        for (int attempt = 1; attempt <= 8; attempt++) {
            long uncapped = (long) (BASE_DELAY_MILLIS * Math.pow(MULTIPLIER, attempt - 1));
            long capped = delayForAttempt(attempt);
            String note = uncapped > MAX_DELAY_MILLIS ? " (would be " + uncapped + "ms uncapped -- CAPPED at " + MAX_DELAY_MILLIS + "ms)" : "";
            System.out.println("Attempt " + attempt + ": wait " + capped + "ms" + note);
        }
    }
}
```

**How to run:** `javac CappedExponentialBackoff.java && java CappedExponentialBackoff` (JDK 17+).

Expected output:
```
Attempt 1: wait 1000ms
Attempt 2: wait 2000ms
Attempt 3: wait 4000ms
Attempt 4: wait 8000ms
Attempt 5: wait 10000ms (would be 16000ms uncapped -- CAPPED at 10000ms)
Attempt 6: wait 10000ms (would be 32000ms uncapped -- CAPPED at 10000ms)
Attempt 7: wait 10000ms (would be 64000ms uncapped -- CAPPED at 10000ms)
Attempt 8: wait 10000ms (would be 128000ms uncapped -- CAPPED at 10000ms)
```

## 6. Walkthrough

1. **Level 1, the constant cadence** — `delayForAttempt` returns `FIXED_DELAY_MILLIS` (1000) unconditionally, regardless of `attemptNumber`; printing the delay for five successive attempts shows the identical value every time, and the total wait across those five attempts is simply `5 × 1000 = 5000`ms, evenly distributed with no change in pacing as failures continue.
2. **Level 2, the growing delay** — `delayForAttempt` computes `BASE_DELAY_MILLIS * MULTIPLIER^(attemptNumber - 1)`, meaning attempt 1 waits 1000ms (`2^0 = 1`), attempt 2 waits 2000ms (`2^1 = 2`), attempt 3 waits 4000ms (`2^2 = 4`), and so on, doubling with each successive attempt.
3. **Level 2, the practical effect on dependency load** — the total wait across the same five attempts grows to 31000ms, dramatically more than Level 1's 5000ms, but critically, this extra time is concentrated in the *later* attempts (attempt 5 alone waits 16000ms) — meaning a dependency experiencing a sustained problem receives progressively sparser retry traffic the longer the problem persists, exactly the easing-off behavior a struggling system benefits from.
4. **Level 3, the same exponential growth, now bounded** — `delayForAttempt` computes the identical uncapped exponential value as Level 2, but wraps it in `Math.min(uncappedDelay, MAX_DELAY_MILLIS)`, ensuring the returned delay never exceeds 10000ms regardless of how large the exponential formula alone would produce.
5. **Level 3, where the cap starts mattering** — the printed output shows attempts 1 through 4 growing normally (1000, 2000, 4000, 8000ms, all under the 10000ms cap), but attempt 5's uncapped value of 16000ms gets capped down to exactly 10000ms, and every subsequent attempt (6, 7, 8) would grow to values like 32000ms, 64000ms, and 128000ms uncapped, but all are capped at the same 10000ms ceiling.
6. **Level 3, why the cap matters for a long-running failure** — without this cap, a sufficiently long sequence of retry attempts against a very persistent failure would eventually wait absurdly long between attempts (minutes, then hours, as the exponential formula continues compounding) — the cap ensures the backoff strategy still provides *some* regular chance to detect recovery within a reasonable, bounded time frame, rather than the exponential growth eventually making retries so infrequent they're effectively useless for timely recovery detection.

## 7. Gotchas & takeaways

> **Gotcha:** exponential backoff alone, applied identically across many concurrent callers all failing at roughly the same moment (a shared dependency going down for everyone simultaneously), can cause all of them to retry in synchronized waves at the same computed delays — this "thundering herd" problem is exactly what [jitter](0262-jitter-randomized-backoff.md), covered next, is designed to solve by adding randomness to break up this synchronization.

- Fixed backoff waits the identical duration before every retry attempt; exponential backoff grows the wait duration with each successive failure, typically by doubling.
- Exponential backoff eases off load on a struggling dependency progressively as a problem persists, rather than continuing to apply constant pressure at the same rate throughout an outage.
- A maximum delay cap on exponential backoff prevents the growing delay from eventually becoming unreasonably long during a very persistent failure, keeping recovery-detection opportunities reasonably frequent even over an extended outage.
- Fixed backoff is simpler and reasonable for short, isolated retry windows; exponential backoff is the more defensible default for production calls to external dependencies where sustained outages are plausible.
- Exponential backoff alone doesn't prevent many concurrent callers from retrying in synchronized waves at the same computed delays — addressing that specific problem requires adding jitter, covered as the next topic.
