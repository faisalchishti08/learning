---
card: microservices
gi: 260
slug: max-retry-attempts
title: "Max retry attempts"
---

## 1. What it is

Max retry attempts is the configured hard limit on how many times a [retry pattern](0259-retry-pattern.md) implementation will attempt an operation before giving up and surfacing the final failure to the caller — the safeguard that keeps a retry mechanism from becoming an unbounded loop against a genuinely persistent failure.

## 2. Why & when

Retries help precisely because most transient failures resolve within a handful of attempts — but that framing implicitly assumes a limit exists at all. Without a maximum, a retry loop facing a genuinely broken dependency (not a transient blip, an actual sustained outage) would keep attempting indefinitely, each failed attempt still consuming a thread, a connection, and time, and the caller waiting on that loop would never receive any response at all — arguably worse than a single, prompt failure, since at least a prompt failure lets the caller move on (report an error, try a fallback) rather than hanging forever. The maximum turns "keep trying until this works" into "try a reasonable, bounded number of times, then admit this isn't working right now and let the caller decide what to do next."

Set the maximum based on how quickly a genuinely transient failure for a specific dependency typically resolves, balanced against how costly it is for the caller to wait through all the attempts before finally giving up — a small number (2-5) is typical for synchronous, latency-sensitive calls, while a background or asynchronous job might reasonably tolerate more attempts since nothing is blocking on it in real time.

## 3. Core concept

The retry loop is bounded by the maximum attempt count as its termination condition — once that many attempts have all failed, the loop exits and the caller receives the last recorded failure, rather than the loop continuing to run.

```java
<T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
    RuntimeException lastException = null;
    for (int attempt = 1; attempt <= maxAttempts; attempt++) { // the LOOP is bounded, by design
        try {
            return operation.get();
        } catch (RuntimeException e) {
            lastException = e;
        }
    }
    throw lastException; // reached ONLY after ALL maxAttempts have failed -- the loop DEFINITELY terminates
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without a maximum, a retry loop against a persistent failure continues indefinitely, consuming resources without ever resolving; with a maximum, the same persistent failure is attempted a bounded number of times and then surfaced clearly to the caller" >
  <rect x="20" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">NO maximum</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">retries FOREVER against persistent failure</text>
  <text x="155" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">caller waits INDEFINITELY</text>

  <rect x="350" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">WITH maximum</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">bounded number of attempts</text>
  <text x="485" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">CLEAR failure surfaced promptly</text>
</svg>

The maximum is what turns an open-ended risk into a bounded, predictable one.

## 5. Runnable example

Scenario: an unbounded retry mechanism whose loop is capped only by a safety break after an unreasonable number of iterations (illustrating the risk), refactored to an explicit, sensible maximum that gives up cleanly and promptly, and finally demonstrating measuring and comparing the total time spent under different maximum values against the identical persistent failure, making the direct cost trade-off of the maximum's value concrete.

### Level 1 — Basic

```java
// File: EffectivelyUnboundedRetry.java -- NO real maximum; a safety cap
// exists ONLY to prevent this DEMO from hanging forever -- illustrating
// how MANY wasted attempts an unbounded retry would make against a
// GENUINELY persistent failure.
public class EffectivelyUnboundedRetry {
    static int attemptCount = 0;

    static String callPermanentlyBrokenDependency() {
        attemptCount++;
        throw new RuntimeException("still down");
    }

    public static void main(String[] args) {
        int SAFETY_CAP_FOR_THIS_DEMO_ONLY = 1000; // a REAL unbounded retry has NOTHING like this
        try {
            for (int i = 0; i < SAFETY_CAP_FOR_THIS_DEMO_ONLY; i++) {
                try { callPermanentlyBrokenDependency(); break; }
                catch (RuntimeException ignored) { /* keep going... and going... */ }
            }
        } finally {
            System.out.println("Made " + attemptCount + " attempts against a PERMANENTLY broken dependency before this demo's artificial safety cap stopped it.");
            System.out.println("A REAL unbounded retry has NO such cap -- it would continue truly indefinitely.");
        }
    }
}
```

**How to run:** `javac EffectivelyUnboundedRetry.java && java EffectivelyUnboundedRetry` (JDK 17+).

Expected output:
```
Made 1000 attempts against a PERMANENTLY broken dependency before this demo's artificial safety cap stopped it.
A REAL unbounded retry has NO such cap -- it would continue truly indefinitely.
```

### Level 2 — Intermediate

```java
// File: SensibleMaximum.java -- a DELIBERATE, small maximum -- gives up
// CLEANLY and PROMPTLY after a reasonable number of genuine attempts.
import java.util.function.*;

public class SensibleMaximum {
    static int attemptCount = 0;

    static String callPermanentlyBrokenDependency() {
        attemptCount++;
        throw new RuntimeException("still down (attempt " + attemptCount + ")");
    }

    static <T> T callWithRetry(Supplier<T> operation, int maxAttempts) {
        RuntimeException lastException = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try { return operation.get(); }
            catch (RuntimeException e) { lastException = e; }
        }
        throw lastException; // BOUNDED -- always terminates after maxAttempts
    }

    public static void main(String[] args) {
        try {
            callWithRetry(SensibleMaximum::callPermanentlyBrokenDependency, 3); // a SENSIBLE, small maximum
        } catch (RuntimeException e) {
            System.out.println("Gave up after exactly " + attemptCount + " attempts (the configured maximum): " + e.getMessage());
            System.out.println("The caller received a CLEAR, PROMPT failure instead of waiting indefinitely.");
        }
    }
}
```

**How to run:** `javac SensibleMaximum.java && java SensibleMaximum` (JDK 17+).

Expected output:
```
Gave up after exactly 3 attempts (the configured maximum): still down (attempt 3)
The caller received a CLEAR, PROMPT failure instead of waiting indefinitely.
```

### Level 3 — Advanced

```java
// File: MeasuredTradeoffAcrossMaximums.java -- measures the TOTAL time
// spent (simulated per-attempt cost) across DIFFERENT maximum values,
// making the DIRECT cost trade-off concrete and comparable.
import java.util.function.*;

public class MeasuredTradeoffAcrossMaximums {
    static final long SIMULATED_PER_ATTEMPT_COST_MILLIS = 200; // e.g. a connection timeout per failed attempt

    static <T> T callWithRetry(Supplier<T> operation, int maxAttempts, int[] attemptsUsed) throws InterruptedException {
        RuntimeException lastException = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            Thread.sleep(SIMULATED_PER_ATTEMPT_COST_MILLIS); // simulate the COST of each attempt
            attemptsUsed[0] = attempt;
            try { return operation.get(); }
            catch (RuntimeException e) { lastException = e; }
        }
        throw lastException;
    }

    static void measureMaximum(int maxAttempts) throws InterruptedException {
        int[] attemptsUsed = {0};
        long start = System.currentTimeMillis();
        try {
            callWithRetry(() -> { throw new RuntimeException("still down"); }, maxAttempts, attemptsUsed);
        } catch (RuntimeException ignored) {
            long elapsed = System.currentTimeMillis() - start;
            System.out.println("maxAttempts=" + maxAttempts + ": used " + attemptsUsed[0] + " attempts, took " + elapsed + "ms before caller was notified");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int max : new int[]{1, 3, 5, 10}) {
            measureMaximum(max);
        }
        System.out.println("\nA HIGHER maximum gives MORE chances for a genuinely transient failure to resolve,");
        System.out.println("but ALSO makes the caller wait LONGER before a persistent failure is finally surfaced.");
    }
}
```

**How to run:** `javac MeasuredTradeoffAcrossMaximums.java && java MeasuredTradeoffAcrossMaximums` (JDK 17+).

Expected output (timing approximate):
```
maxAttempts=1: used 1 attempts, took 200ms before caller was notified
maxAttempts=3: used 3 attempts, took 600ms before caller was notified
maxAttempts=5: used 5 attempts, took 1000ms before caller was notified
maxAttempts=10: used 10 attempts, took 2000ms before caller was notified

A HIGHER maximum gives MORE chances for a genuinely transient failure to resolve,
but ALSO makes the caller wait LONGER before a persistent failure is finally surfaced.
```

## 6. Walkthrough

1. **Level 1, illustrating unboundedness's real cost** — the loop has no genuine termination condition tied to a reasonable retry count; only an artificial `SAFETY_CAP_FOR_THIS_DEMO_ONLY` (1000) prevents this example from actually hanging, and even that artificially capped run still wastes 1000 attempts against a dependency that was never going to succeed — a real unbounded retry has nothing playing this safety-cap role at all.
2. **Level 2, a genuine, deliberate limit** — `callWithRetry`'s `for` loop condition (`attempt <= maxAttempts`) is the *actual* termination mechanism, not a workaround; calling it with `maxAttempts = 3` against the permanently broken dependency results in exactly 3 attempts, confirmed by `attemptCount`, before the loop exits and the final exception is thrown.
3. **Level 2, the caller's improved experience** — instead of hanging indefinitely (Level 1's implied risk) or receiving a value like 1000 wasted attempts, the caller here receives a clear, final failure after just 3 genuine attempts — prompt enough to let the caller move on (retry later, alert someone, show an error) rather than being left waiting.
4. **Level 3, quantifying the trade-off directly** — `measureMaximum` runs the identical persistently-failing operation with different `maxAttempts` values (1, 3, 5, 10), each attempt costing a simulated fixed 200ms, and measures the total elapsed time before the caller is finally notified of failure.
5. **Level 3, the linear cost relationship observed** — the printed results show total time scaling directly with `maxAttempts` (roughly 200ms × the maximum), making explicit that every additional retry attempt configured adds a proportional amount of worst-case latency the caller experiences before a persistent failure is finally surfaced.
6. **Level 3, the trade-off this quantification supports** — a higher maximum genuinely does give more opportunities for a truly transient failure to resolve within the retry window, but this measured data shows exactly what that additional resilience costs in the worst case (a truly persistent failure): the caller waits proportionally longer before being told the operation ultimately failed — this concrete, measured trade-off is exactly what should inform the choice of `maxAttempts` for a specific call path, balancing transient-failure recovery against worst-case latency tolerance.

## 7. Gotchas & takeaways

> **Gotcha:** the maximum attempt count interacts directly with [backoff delays](0261-fixed-vs-exponential-backoff.md) between attempts — a high maximum combined with exponential backoff can produce a surprisingly long total worst-case wait time (each successive delay growing), even though the attempt count alone looks modest; always calculate the actual worst-case total wait time (sum of all delays plus per-attempt costs) when choosing a maximum, not just the attempt count in isolation.

- Max retry attempts is the hard limit on how many times a retry mechanism will attempt an operation before giving up and surfacing the final failure to the caller.
- Without this limit, a retry loop facing a genuinely persistent failure (not a transient blip) would continue indefinitely, consuming resources and leaving the caller waiting with no resolution.
- The maximum should be set based on how quickly a specific dependency's transient failures typically resolve, weighed against how much worst-case latency the caller can reasonably tolerate before giving up.
- There's a direct, measurable, roughly linear trade-off between a higher maximum (more chances for a transient failure to resolve) and worst-case latency (longer total wait before a persistent failure is finally surfaced).
- The maximum's real-world impact must be considered together with backoff delays between attempts — the two combine to determine the actual worst-case total wait time, not the attempt count in isolation.
