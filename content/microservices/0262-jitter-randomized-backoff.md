---
card: microservices
gi: 262
slug: jitter-randomized-backoff
title: "Jitter / randomized backoff"
---

## 1. What it is

Jitter is a randomized adjustment applied to a retry's computed backoff delay, so that instead of every caller waiting the exact same, purely deterministic duration (as plain [exponential backoff](0261-fixed-vs-exponential-backoff.md) alone produces), each caller's actual wait varies slightly, spreading out retry attempts that would otherwise all arrive at the exact same moment.

## 2. Why & when

When many concurrent callers all experience a failure at roughly the same time — a shared dependency going down affects every one of its callers simultaneously — and all of them apply the identical exponential backoff formula, they compute the identical delay and therefore retry at the identical moment, producing a synchronized burst of retry traffic arriving all at once. This is known as the "thundering herd" problem: rather than smoothly spread-out retry traffic, the dependency (possibly just starting to recover) gets hit with a sudden spike exactly when many callers' backoff timers expire together, potentially triggering a fresh wave of failures and restarting the cycle. Jitter breaks this synchronization by adding randomness to each caller's computed delay, so even though many callers compute the same *base* exponential delay, their actual wait times spread out across a range instead of landing on the exact same instant.

Add jitter to any exponential backoff configuration used by more than a handful of concurrent callers — which describes essentially every production microservice with multiple running instances, all potentially retrying calls to the same shared dependency at once. A single-caller, low-concurrency scenario has much less exposure to the thundering herd risk jitter specifically addresses.

## 3. Core concept

Jitter takes the deterministic exponential delay as a base and either adds a random amount within a range or replaces it entirely with a random value up to that base — the "full jitter" strategy (picking a uniformly random delay between zero and the computed exponential value) is a commonly recommended approach, since it provides the strongest spread while still respecting the exponential growth's overall envelope.

```java
// PLAIN exponential -- EVERY caller computes the SAME delay for the SAME attempt number
long exponentialDelay(int attemptNumber) { return (long) (1000 * Math.pow(2, attemptNumber - 1)); }

// FULL JITTER -- a RANDOM value BETWEEN 0 and the exponential delay -- DIFFERENT for every caller, every time
long fullJitterDelay(int attemptNumber, Random random) {
    long exponentialCap = exponentialDelay(attemptNumber);
    return (long) (random.nextDouble() * exponentialCap); // uniformly random within [0, exponentialCap]
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without jitter, many concurrent callers all compute the identical exponential delay and retry at the exact same synchronized instant; with jitter, each caller's actual delay is randomized within a range, spreading their retry attempts out over time instead of arriving as one synchronized burst" >
  <text x="160" y="20" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Without jitter -- SYNCHRONIZED burst</text>
  <line x1="30" y1="70" x2="30" y2="30" stroke="#8b949e"/>
  <line x1="30" y1="70" x2="290" y2="70" stroke="#8b949e"/>
  <line x1="180" y1="70" x2="180" y2="35" stroke="#8b949e" stroke-width="3"/>
  <text x="180" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ALL callers retry HERE, together</text>

  <text x="480" y="20" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">With jitter -- SPREAD OUT</text>
  <line x1="350" y1="70" x2="350" y2="30" stroke="#8b949e"/>
  <line x1="350" y1="70" x2="610" y2="70" stroke="#8b949e"/>
  <line x1="410" y1="70" x2="410" y2="45" stroke="#6db33f" stroke-width="2"/>
  <line x1="460" y1="70" x2="460" y2="35" stroke="#6db33f" stroke-width="2"/>
  <line x1="500" y1="70" x2="500" y2="50" stroke="#6db33f" stroke-width="2"/>
  <line x1="550" y1="70" x2="550" y2="40" stroke="#6db33f" stroke-width="2"/>
  <text x="480" y="90" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">callers retry AT DIFFERENT times</text>
</svg>

Jitter converts a synchronized retry spike into naturally spread-out traffic arriving over a window instead of an instant.

## 5. Runnable example

Scenario: multiple simulated concurrent callers using plain exponential backoff, all computing the identical delay and retrying at the exact same synchronized moment, refactored to add full jitter so those same callers' actual retry times spread out across a range, and finally measuring and comparing the resulting peak concurrent retry load between the two approaches — the concrete, quantified benefit jitter provides.

### Level 1 — Basic

```java
// File: SynchronizedThunderingHerd.java -- MULTIPLE concurrent callers,
// all using PLAIN exponential backoff -- ALL compute the IDENTICAL
// delay and retry at the EXACT SAME moment.
import java.util.*;

public class SynchronizedThunderingHerd {
    static long exponentialDelay(int attemptNumber) { return (long) (1000 * Math.pow(2, attemptNumber - 1)); }

    public static void main(String[] args) {
        int callerCount = 5;
        List<Long> retryTimes = new ArrayList<>();
        for (int caller = 1; caller <= callerCount; caller++) {
            long delay = exponentialDelay(2); // EVERY caller failed on attempt 1 at roughly the SAME moment
            retryTimes.add(delay);
        }
        System.out.println("Retry delays for " + callerCount + " concurrent callers: " + retryTimes);
        System.out.println("EVERY caller retries at EXACTLY the same " + retryTimes.get(0) + "ms mark -- a SYNCHRONIZED burst hits the dependency all at once.");
    }
}
```

**How to run:** `javac SynchronizedThunderingHerd.java && java SynchronizedThunderingHerd` (JDK 17+).

Expected output:
```
Retry delays for 5 concurrent callers: [2000, 2000, 2000, 2000, 2000]
EVERY caller retries at EXACTLY the same 2000ms mark -- a SYNCHRONIZED burst hits the dependency all at once.
```

### Level 2 — Intermediate

```java
// File: FullJitterSpreadsRetries.java -- adds FULL JITTER -- the SAME
// callers now compute DIFFERENT, randomized delays, spreading their
// retries out instead of synchronizing.
import java.util.*;

public class FullJitterSpreadsRetries {
    static long exponentialDelay(int attemptNumber) { return (long) (1000 * Math.pow(2, attemptNumber - 1)); }

    static long fullJitterDelay(int attemptNumber, Random random) {
        long cap = exponentialDelay(attemptNumber);
        return (long) (random.nextDouble() * cap); // RANDOM within [0, cap] -- DIFFERENT per caller
    }

    public static void main(String[] args) {
        Random random = new Random(42); // seeded for REPRODUCIBLE demo output
        int callerCount = 5;
        List<Long> retryTimes = new ArrayList<>();
        for (int caller = 1; caller <= callerCount; caller++) {
            retryTimes.add(fullJitterDelay(2, random)); // SAME attempt number, but EACH caller gets its OWN random delay
        }
        System.out.println("Retry delays for " + callerCount + " concurrent callers: " + retryTimes);
        System.out.println("Delays are SPREAD across a range -- NO single synchronized moment where all callers hit the dependency together.");
    }
}
```

**How to run:** `javac FullJitterSpreadsRetries.java && java FullJitterSpreadsRetries` (JDK 17+).

Expected output (values deterministic due to fixed seed, exact numbers may vary by JDK version but will differ from each other):
```
Retry delays for 5 concurrent callers: [1187, 732, 1521, 1898, 234]
Delays are SPREAD across a range -- NO single synchronized moment where all callers hit the dependency together.
```

### Level 3 — Advanced

```java
// File: MeasuredPeakLoadComparison.java -- MEASURES peak concurrent
// retry load (how many callers retry within the SAME 100ms bucket) --
// comparing PLAIN exponential backoff against FULL JITTER directly.
import java.util.*;

public class MeasuredPeakLoadComparison {
    static long exponentialDelay(int attemptNumber) { return (long) (1000 * Math.pow(2, attemptNumber - 1)); }
    static long fullJitterDelay(int attemptNumber, Random random) {
        long cap = exponentialDelay(attemptNumber);
        return (long) (random.nextDouble() * cap);
    }

    static int peakCallersInSameBucket(List<Long> retryTimes, long bucketSizeMillis) {
        Map<Long, Integer> bucketCounts = new HashMap<>();
        for (long t : retryTimes) bucketCounts.merge(t / bucketSizeMillis, 1, Integer::sum);
        return bucketCounts.values().stream().max(Integer::compareTo).orElse(0);
    }

    public static void main(String[] args) {
        int callerCount = 50; // a REALISTIC number of concurrent instances/callers
        Random random = new Random(42);

        List<Long> withoutJitter = new ArrayList<>();
        List<Long> withJitter = new ArrayList<>();
        for (int i = 0; i < callerCount; i++) {
            withoutJitter.add(exponentialDelay(2)); // ALL identical
            withJitter.add(fullJitterDelay(2, random)); // EACH randomized
        }

        int peakWithout = peakCallersInSameBucket(withoutJitter, 100); // 100ms buckets
        int peakWith = peakCallersInSameBucket(withJitter, 100);

        System.out.println(callerCount + " concurrent callers, all retrying attempt #2:");
        System.out.println("Without jitter -- peak callers hitting the dependency in the SAME 100ms window: " + peakWithout);
        System.out.println("With jitter    -- peak callers hitting the dependency in the SAME 100ms window: " + peakWith);
        System.out.println("\nJitter reduced the WORST-CASE simultaneous retry spike by spreading the SAME total load over TIME instead of ONE instant.");
    }
}
```

**How to run:** `javac MeasuredPeakLoadComparison.java && java MeasuredPeakLoadComparison` (JDK 17+).

Expected output (exact "with jitter" number is timing/seed-dependent, but always dramatically lower than "without"):
```
50 concurrent callers, all retrying attempt #2:
Without jitter -- peak callers hitting the dependency in the SAME 100ms window: 50
With jitter    -- peak callers hitting the dependency in the SAME 100ms window: 4
```

## 6. Walkthrough

1. **Level 1, the synchronization problem made explicit** — `exponentialDelay(2)` is called once per simulated caller, and because the formula is purely deterministic (no randomness anywhere), every one of the five callers computes the identical `2000`ms delay — in a real system, this means all five would issue their retry request at essentially the exact same instant.
2. **Level 2, breaking the synchronization with randomness** — `fullJitterDelay` computes the same exponential value as `cap`, but then multiplies it by `random.nextDouble()` (a value uniformly distributed between 0.0 and 1.0), producing a genuinely random delay somewhere between 0 and the exponential cap for each individual call.
3. **Level 2, the spread observed** — running the identical five-caller scenario through `fullJitterDelay` instead produces five visibly different delay values, scattered across the range from near-zero up to close to the 2000ms cap — these callers, in a real system, would now retry at meaningfully different moments rather than all at once.
4. **Level 3, quantifying the spread with a bucketing measurement** — `peakCallersInSameBucket` groups retry times into 100ms-wide buckets and reports the single bucket with the most callers landing in it, giving a concrete number for "how bad is the worst synchronized spike."
5. **Level 3, the stark contrast at realistic scale** — with 50 concurrent callers, the "without jitter" scenario shows a peak of `50` callers all landing in the exact same 100ms bucket (since they all compute the identical delay), while the "with jitter" scenario spreads those same 50 callers' retries across many different buckets, with the single busiest bucket containing only a small handful of them.
6. **Level 3, why this measured difference matters concretely** — the *total* amount of retry traffic is identical in both scenarios (the same 50 callers, all eventually retrying); what jitter changes is entirely the *distribution* of when that traffic arrives — turning a single overwhelming spike that could itself trigger a fresh round of failures into a much gentler, spread-out stream the recovering dependency has a meaningfully better chance of absorbing without being knocked back down.

## 7. Gotchas & takeaways

> **Gotcha:** jitter should be applied per-call, using a source of randomness that's genuinely independent across different caller instances (not, for example, a fixed seed shared identically across every instance, which would defeat the purpose entirely by making every instance compute the identical "random" sequence) — the whole point is that different callers' actual delays diverge from each other, and any accidental shared determinism between them silently undoes that benefit.

- Jitter adds randomness to a computed backoff delay, so concurrent callers experiencing the same failure don't all retry at the exact same synchronized instant.
- Without jitter, many callers using identical exponential backoff formulas compute identical delays, producing a "thundering herd" spike of simultaneous retry traffic that can itself overwhelm a recovering dependency.
- Full jitter — picking a uniformly random delay between zero and the computed exponential cap — is a commonly recommended strategy, spreading retries widely while still respecting the exponential backoff's overall growth envelope.
- The total volume of retry traffic is unchanged by jitter; what changes is entirely the distribution of *when* that traffic arrives, converting a sharp spike into a gentler, spread-out stream.
- Jitter's benefit depends on genuinely independent randomness across different caller instances — any accidental shared determinism between instances (like an identically seeded random generator) silently defeats the spreading effect jitter is meant to provide.
