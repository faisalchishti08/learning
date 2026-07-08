---
card: java
gi: 454
slug: threadlocalrandom
title: ThreadLocalRandom
---

## 1. What it is

`ThreadLocalRandom`, added in Java 7, provides a random number generator that's automatically scoped to the **current thread** — obtained via the static method `ThreadLocalRandom.current()`, never `new ThreadLocalRandom()`. Each thread that calls `current()` gets access to its own independent generator state, maintained internally without any object you construct or manage yourself, and without any shared state between threads that would need coordinating.

## 2. Why & when

A single shared `java.util.Random` instance is thread-safe (its methods are internally synchronized against concurrent access via a compare-and-swap loop on one shared seed), but that shared seed becomes a genuine point of **contention** under heavy concurrent use — many threads all fighting over updates to the same seed value, retrying their CAS operation when another thread updates it first. `ThreadLocalRandom` sidesteps this entirely: since each thread has its own generator state, there's no shared seed to contend over at all, and no synchronization overhead — a meaningful throughput improvement for any workload that generates a lot of random numbers concurrently across many threads.

You reach for `ThreadLocalRandom.current()` any time you need random numbers from code that runs concurrently across multiple threads — parallel simulations, load-testing tools that need randomized inputs, or any multi-threaded workload doing per-thread randomized work — essentially, `ThreadLocalRandom` should be your default choice over a single shared `Random` instance whenever multiple threads are involved.

## 3. Core concept

```java
import java.util.concurrent.ThreadLocalRandom;

ThreadLocalRandom random = ThreadLocalRandom.current(); // NOT "new ThreadLocalRandom()"

int diceRoll = random.nextInt(1, 7);       // bound: 1 inclusive, 7 EXCLUSIVE -- so 1 through 6
double probability = random.nextDouble();  // [0.0, 1.0)
double range = random.nextDouble(-1, 1);   // [-1.0, 1.0)
```

Every thread that calls `ThreadLocalRandom.current()` transparently gets its own generator state — you never construct or explicitly manage a separate instance per thread yourself; the "current thread" scoping happens automatically inside the static factory method.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single shared Random instance forces concurrent threads to contend over one shared seed; ThreadLocalRandom gives each thread its own independent generator state, with no shared seed and no contention at all">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#f85149" font-size="11" font-family="sans-serif">Shared java.util.Random: all threads contend over ONE seed</text>
  <rect x="30" y="38" width="580" height="26" rx="4" fill="#1c2430" stroke="#f85149"/><text x="320" y="56" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Thread A, B, C, D all CAS-retry against the same seed value</text>

  <text x="20" y="95" fill="#6db33f" font-size="11" font-family="sans-serif">ThreadLocalRandom: each thread has its OWN generator state</text>
  <rect x="30" y="107" width="130" height="26" fill="#1c2430" stroke="#6db33f"/><text x="95" y="125" fill="#6db33f" font-size="9" text-anchor="middle">A's own state</text>
  <rect x="180" y="107" width="130" height="26" fill="#1c2430" stroke="#6db33f"/><text x="245" y="125" fill="#6db33f" font-size="9" text-anchor="middle">B's own state</text>
  <rect x="330" y="107" width="130" height="26" fill="#1c2430" stroke="#6db33f"/><text x="395" y="125" fill="#6db33f" font-size="9" text-anchor="middle">C's own state</text>
</svg>

No shared seed means no contention — each thread's random generation is entirely independent of every other thread's.

## 5. Runnable example

Scenario: generating random values across concurrent threads — the same generator, evolved from a basic single-thread bounded random value, through verifying correct, contention-free generation across several concurrent threads, to a parallel Monte Carlo simulation estimating π using independent random samples on each thread.

### Level 1 — Basic

```java
import java.util.concurrent.ThreadLocalRandom;

public class TLRBasic {
    public static void main(String[] args) {
        ThreadLocalRandom random = ThreadLocalRandom.current(); // no "new" -- get the CURRENT thread's instance

        int diceRoll = random.nextInt(1, 7); // bound: 1 inclusive, 7 exclusive -- i.e. 1 to 6
        System.out.println("Is a valid roll (1-6): " + (diceRoll >= 1 && diceRoll <= 6));

        double probability = random.nextDouble();
        System.out.println("Is a valid probability (0.0-1.0): " + (probability >= 0.0 && probability < 1.0));
    }
}
```

**How to run:** `java TLRBasic.java`

`ThreadLocalRandom.current()` gets the calling thread's own generator; `nextInt(1, 7)` produces a value in `[1, 7)` — 1 through 6 inclusive, since the upper bound is exclusive. (The actual dice roll value varies each run — `ThreadLocalRandom` is deliberately not seedable for reproducibility, so the printed checks confirm validity rather than an exact value.)

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class TLRConcurrent {
    public static void main(String[] args) throws Exception {
        int threadCount = 4;
        int perThread = 1000;
        ExecutorService pool = Executors.newFixedThreadPool(threadCount);

        // Each thread calls ThreadLocalRandom.current().nextInt() independently, with
        // NO shared lock or shared seed to contend over -- unlike a single shared java.util.Random,
        // whose nextInt() internally retries a compare-and-swap loop under concurrent access.
        List<Future<Integer>> futures = new ArrayList<>();
        for (int t = 0; t < threadCount; t++) {
            futures.add(pool.submit(() -> {
                ThreadLocalRandom random = ThreadLocalRandom.current();
                int validCount = 0;
                for (int i = 0; i < perThread; i++) {
                    int value = random.nextInt(0, 100);
                    if (value >= 0 && value < 100) validCount++;
                }
                return validCount;
            }));
        }

        int totalValid = 0;
        for (Future<Integer> future : futures) {
            totalValid += future.get();
        }

        System.out.println("Expected total generated values: " + (threadCount * perThread));
        System.out.println("Actual valid values across all threads: " + totalValid);
        System.out.println("All concurrent generation succeeded with no shared-state contention: "
            + (totalValid == threadCount * perThread));

        pool.shutdown();
    }
}
```

**How to run:** `java TLRConcurrent.java`

Four threads each generate 1000 random values fully concurrently, with no external synchronization written anywhere in this code — each thread's call to `ThreadLocalRandom.current()` operates entirely independently, with no shared seed to coordinate access to, unlike a single shared `Random` instance would require.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class MonteCarloPi {
    static long countPointsInCircle(long samples) {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        long inside = 0;
        for (long i = 0; i < samples; i++) {
            double x = random.nextDouble(-1, 1);
            double y = random.nextDouble(-1, 1);
            if (x * x + y * y <= 1.0) inside++;
        }
        return inside;
    }

    public static void main(String[] args) throws Exception {
        int threadCount = 4;
        long samplesPerThread = 2_000_000;
        ExecutorService pool = Executors.newFixedThreadPool(threadCount);

        List<Future<Long>> futures = new ArrayList<>();
        for (int t = 0; t < threadCount; t++) {
            futures.add(pool.submit(() -> countPointsInCircle(samplesPerThread)));
        }

        long totalInside = 0;
        for (Future<Long> future : futures) {
            totalInside += future.get();
        }
        pool.shutdown();

        long totalSamples = threadCount * samplesPerThread;
        double piEstimate = 4.0 * totalInside / totalSamples;

        System.out.println("Total samples: " + totalSamples);
        System.out.println("Pi estimate within 0.01 of actual: " + (Math.abs(piEstimate - Math.PI) < 0.01));
    }
}
```

**How to run:** `java MonteCarloPi.java`

Each of 4 threads independently generates 2 million random `(x, y)` points in `[-1, 1) × [-1, 1)` and counts how many fall inside the unit circle — since a circle of radius 1 has area `π`, and its bounding square has area `4`, the ratio of points inside the circle to total points approximates `π / 4`. Because each thread uses its own `ThreadLocalRandom` with zero shared state, all 4 threads generate their 2 million samples fully in parallel with no coordination overhead.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four tasks are submitted to a 4-thread pool, each calling `countPointsInCircle(2_000_000)`.

Inside `countPointsInCircle`, `ThreadLocalRandom.current()` obtains the calling thread's own generator — since each of the 4 threads calls this independently, all 4 proceed with zero contention between them. The loop runs 2 million times per thread: `x` and `y` are each drawn uniformly from `[-1, 1)`, simulating a random point somewhere in a 2×2 square centered at the origin. `x * x + y * y <= 1.0` checks whether that point falls within distance 1 of the origin — inside the unit circle inscribed in that square. `inside` counts how many of the 2 million points per thread satisfy this.

Once all 4 futures complete, `totalInside` sums each thread's count, giving the total number of "inside the circle" points across all 8 million samples (`4 threads × 2,000,000` each). `piEstimate = 4.0 * totalInside / totalSamples` applies the geometric relationship: the fraction of points landing inside the circle approximates the ratio of the circle's area to the square's area (`π / 4`), so multiplying that observed fraction by 4 estimates `π` itself.

`Math.abs(piEstimate - Math.PI) < 0.01` checks that this Monte Carlo estimate landed within `0.01` of the true value of π — with 8 million total samples, this level of accuracy is reliably achieved (Monte Carlo estimation error shrinks with the square root of the sample count, and 8 million samples is more than enough for two-decimal-place accuracy in the vast majority of runs).

Expected output:
```
Total samples: 8000000
Pi estimate within 0.01 of actual: true
```

## 7. Gotchas & takeaways

> `ThreadLocalRandom` is **deliberately not seedable** in any way that guarantees a reproducible sequence — unlike `new Random(seed)`, there's no equivalent way to force `ThreadLocalRandom` to replay the exact same sequence of values across runs. This is an intentional design choice (to avoid a shared, predictable seed being a security or fairness concern in concurrent contexts), but it means `ThreadLocalRandom` is a poor fit for anything requiring deterministic, reproducible randomness — testing scenarios that need repeatable "random" sequences should use a seeded `Random` (or a testing-specific abstraction) instead.

- Always obtain an instance via the static `ThreadLocalRandom.current()` — never construct one with `new`, which isn't how this class is meant to be used at all.
- Each thread that calls `current()` gets its own independent generator state, eliminating the shared-seed contention a single `Random` instance would experience under concurrent access from many threads.
- `ThreadLocalRandom` should be the default choice over a shared `Random` instance for any multi-threaded code generating random values — the API (`nextInt`, `nextDouble`, bounded overloads) is otherwise very similar to `Random`'s.
- It cannot be seeded for reproducible sequences — use a seeded `Random` instead whenever deterministic, repeatable randomness is genuinely required (such as in certain kinds of tests).
- Monte Carlo-style simulations (like the π estimation above) are a natural fit for `ThreadLocalRandom`, since they typically involve many independent random samples that parallelize cleanly across threads with no coordination needed between them.
