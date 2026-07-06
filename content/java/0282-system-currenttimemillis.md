---
card: java
gi: 282
slug: system-currenttimemillis
title: System.currentTimeMillis()
---

## 1. What it is

`System.currentTimeMillis()` returns the current time as a `long`, representing the number of milliseconds elapsed since midnight, January 1, 1970, UTC — a reference point known as "the epoch." It's the simplest, most fundamental way to get "what time is it right now" or to measure elapsed durations in Java, though modern code often prefers `System.nanoTime()` for measuring elapsed durations specifically (covered in the gotchas) and the `java.time` package for working with calendar dates and human-readable times.

```java
public class CurrentTimeDemo {
    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();

        Thread.sleep(150); // pause for approximately 150 milliseconds

        long end = System.currentTimeMillis();
        System.out.println("Elapsed: " + (end - start) + " ms");
    }
}
```

`System.currentTimeMillis()` is called twice, before and after a deliberate pause, and the difference between the two `long` values gives the approximate elapsed duration in milliseconds — this simple subtraction pattern is the most common use of this method: measuring how long some operation took.

## 2. Why & when

`System.currentTimeMillis()` provides a simple, universally available way to timestamp events and measure elapsed durations, without needing any additional classes or imports.

- **Timestamping events** — recording "when did this happen" as a single `long` value is compact, easily stored, easily compared, and directly convertible to a human-readable date if needed (via `java.util.Date` or, in modern code, `java.time.Instant`).
- **Measuring elapsed wall-clock time** — subtracting an earlier `currentTimeMillis()` reading from a later one gives the approximate real-world duration between two points in a program's execution, useful for basic performance logging or timeout logic.
- **A universal reference point (the epoch) enabling comparison across systems** — because it's always measured from the same fixed reference point (January 1, 1970, UTC), timestamps captured on different machines, in different time zones, or at different times can be meaningfully compared, stored, and transmitted, unlike a `String` representation that might depend on locale or format.

Use `System.currentTimeMillis()` for simple event timestamps and rough elapsed-time measurements where millisecond precision is sufficient; for genuinely precise interval measurement (benchmarking, performance-sensitive timing), prefer `System.nanoTime()` instead, since it's specifically designed for measuring elapsed time accurately and isn't affected by system clock adjustments, unlike `currentTimeMillis()`.

## 3. Core concept

```java
public class CurrentTimeCore {
    static long timestamp(String eventName) {
        long now = System.currentTimeMillis();
        System.out.println(eventName + " occurred at epoch millis: " + now);
        return now;
    }

    public static void main(String[] args) {
        long loginTime = timestamp("Login");
        long logoutTime = timestamp("Logout");
        System.out.println("Session duration: " + (logoutTime - loginTime) + " ms");
    }
}
```

Each call to `System.currentTimeMillis()` captures the current epoch time at that exact moment, and simple subtraction between two captured values gives the elapsed duration between them — this is the fundamental pattern underlying most everyday uses of this method.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="currentTimeMillis measures milliseconds elapsed since the epoch, January 1 1970 UTC, subtracting two readings gives the elapsed duration between two points in time">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <line x1="60" y1="80" x2="540" y2="80" stroke="#8b949e" stroke-width="2"/>
  <text x="60" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">epoch (0 ms)</text>
  <text x="60" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Jan 1, 1970 UTC</text>

  <circle cx="380" cy="80" r="5" fill="#79c0ff"/>
  <text x="380" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">start</text>

  <circle cx="470" cy="80" r="5" fill="#6db33f"/>
  <text x="470" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">end</text>

  <text x="425" y="115" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">end - start = elapsed ms</text>
</svg>

`currentTimeMillis()` measures elapsed milliseconds since the fixed epoch reference point.

## 5. Runnable example

Scenario: a small performance-timing utility, evolved from a single measured operation into repeated measurements collected in a list, then hardened with a comparison against `System.nanoTime()` for higher-precision timing.

### Level 1 — Basic

```java
public class CurrentTimeBasic {
    static void simulateWork() {
        long total = 0;
        for (int i = 0; i < 10_000_000; i++) total += i;
    }

    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        simulateWork();
        long end = System.currentTimeMillis();
        System.out.println("Work took: " + (end - start) + " ms");
    }
}
```

**How to run:** `java CurrentTimeBasic.java`

The elapsed time between `start` and `end` gives an approximate measure of how long `simulateWork()` took to run — the exact number will vary between runs and machines, but the pattern (capture before, capture after, subtract) is always the same.

### Level 2 — Intermediate

Same idea, now timing multiple operations and collecting the durations, demonstrating repeated timestamp-and-subtract measurements used to compare relative performance.

```java
import java.util.ArrayList;
import java.util.List;

public class CurrentTimeIntermediate {
    static void simulateWork(int iterations) {
        long total = 0;
        for (int i = 0; i < iterations; i++) total += i;
    }

    public static void main(String[] args) {
        int[] sizes = { 1_000_000, 5_000_000, 10_000_000 };
        List<Long> durations = new ArrayList<>();

        for (int size : sizes) {
            long start = System.currentTimeMillis();
            simulateWork(size);
            long end = System.currentTimeMillis();
            long duration = end - start;
            durations.add(duration);
            System.out.println(size + " iterations took: " + duration + " ms");
        }

        System.out.println("All durations: " + durations);
    }
}
```

**How to run:** `java CurrentTimeIntermediate.java`

Each loop iteration times a differently-sized workload independently, collecting the results into a `List<Long>` — this pattern generalizes the basic single-measurement idea into a small benchmarking loop, useful for comparing how performance scales with input size.

### Level 3 — Advanced

Same benchmarking idea, now comparing `System.currentTimeMillis()` against `System.nanoTime()` for the same operation, demonstrating the precision difference and why `nanoTime()` is generally preferred for measuring short elapsed durations specifically.

```java
public class CurrentTimeAdvanced {
    static void simulateWork() {
        long total = 0;
        for (int i = 0; i < 1_000_000; i++) total += i;
    }

    public static void main(String[] args) {
        // Using currentTimeMillis -- millisecond precision, coarser
        long millisStart = System.currentTimeMillis();
        simulateWork();
        long millisEnd = System.currentTimeMillis();
        System.out.println("currentTimeMillis elapsed: " + (millisEnd - millisStart) + " ms");

        // Using nanoTime -- nanosecond precision, designed specifically for elapsed-time measurement
        long nanoStart = System.nanoTime();
        simulateWork();
        long nanoEnd = System.nanoTime();
        long elapsedNanos = nanoEnd - nanoStart;
        System.out.println("nanoTime elapsed: " + elapsedNanos + " ns (" + (elapsedNanos / 1_000_000.0) + " ms)");
    }
}
```

**How to run:** `java CurrentTimeAdvanced.java`

`System.nanoTime()` provides far finer-grained precision (nanoseconds rather than milliseconds) and is specifically designed for measuring elapsed time accurately, unaffected by system clock adjustments that could otherwise distort a `currentTimeMillis()`-based measurement — for a workload fast enough that `currentTimeMillis()` might report `0` ms elapsed (too fast to register at millisecond granularity), `nanoTime()` would still show a meaningful, non-zero duration.

## 6. Walkthrough

Trace `main` in `CurrentTimeAdvanced` conceptually (exact timing values vary by machine and run, so the walkthrough focuses on the mechanism, not specific numbers).

**`millisStart = System.currentTimeMillis()`.** Captures the current epoch time in milliseconds, say (hypothetically) `1718000000000`.

**`simulateWork()` runs the first time.** Performs one million additions in a loop — this typically takes well under a millisecond on modern hardware, but the exact duration depends on the machine.

**`millisEnd = System.currentTimeMillis()`.** Captures the epoch time again, say `1718000000001` (one millisecond later) or possibly the exact same value as `millisStart`, if the entire operation completed within the same millisecond tick.

**`millisEnd - millisStart`.** This could be `0` or `1` (or occasionally more, depending on system load), since millisecond-granularity timing can't distinguish durations shorter than one millisecond — a real limitation this comparison is designed to expose.

**`nanoStart = System.nanoTime()`.** Captures a nanosecond-precision timestamp (note: `nanoTime()`'s absolute value has no defined relationship to wall-clock time or the epoch — it's only meaningful for computing *differences* between two calls, never as an absolute timestamp).

**`simulateWork()` runs the second time.** Same operation as before.

**`nanoEnd = System.nanoTime()`.** Captures another nanosecond-precision timestamp.

**`elapsedNanos = nanoEnd - nanoStart`.** This difference, being nanosecond-precise, will show a genuinely meaningful, non-zero duration even for an operation fast enough to appear as `0` ms under `currentTimeMillis()` — say, something like `800000` nanoseconds (0.8 milliseconds).

```
currentTimeMillis(): granularity = 1 millisecond
  millisStart=T, simulateWork(), millisEnd=T or T+1 -> elapsed could show as 0 ms (too coarse to measure precisely)

nanoTime(): granularity = nanoseconds
  nanoStart=N, simulateWork(), nanoEnd=N+~800000 -> elapsedNanos ~800000 ns = ~0.8 ms (meaningful, precise measurement)
```

**Illustrative output** (exact numbers vary by run and machine):
```
currentTimeMillis elapsed: 0 ms
nanoTime elapsed: 823456 ns (0.823456 ms)
```
This demonstrates concretely why `nanoTime()` is the better tool specifically for measuring short elapsed durations: `currentTimeMillis()`'s millisecond granularity can report `0` for operations that clearly did take *some* measurable time, while `nanoTime()` reveals the actual, meaningful duration.

## 7. Gotchas & takeaways

> **`System.nanoTime()`'s absolute return value has no defined meaning relative to wall-clock time or the epoch — it must only ever be used to compute the *difference* between two calls within the same program run**, never treated as an actual timestamp or compared across different JVM instances. `currentTimeMillis()`, by contrast, does represent an actual, meaningful point in wall-clock time (milliseconds since the epoch) and can reasonably be stored, compared across systems, or converted to a human-readable date.

> **`System.currentTimeMillis()` can be affected by system clock adjustments (like NTP synchronization or a user manually changing the system clock), which can make elapsed-time measurements based on it occasionally inaccurate or even negative** — `System.nanoTime()` is specifically designed to avoid this issue for elapsed-time measurement, since it's based on a monotonic clock source unaffected by wall-clock adjustments; prefer it whenever precise interval measurement (not an actual timestamp) is the actual goal.

- `System.currentTimeMillis()` returns milliseconds elapsed since the epoch (January 1, 1970, UTC) as a `long`, providing a simple, universal timestamp or basis for measuring elapsed duration.
- Subtracting an earlier reading from a later one gives the approximate elapsed real-world time between two points in a program's execution.
- For genuinely precise elapsed-time measurement (benchmarking, performance timing), prefer `System.nanoTime()`, which offers nanosecond precision and isn't affected by system clock adjustments.
- `nanoTime()`'s absolute value is meaningless on its own — only differences between two `nanoTime()` calls within the same JVM run are valid to use.
