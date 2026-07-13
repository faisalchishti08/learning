---
card: microservices
gi: 271
slug: max-concurrent-calls
title: "Max concurrent calls"
---

## 1. What it is

Max concurrent calls is the specific configuration value that sets a [bulkhead](0267-bulkhead-pattern.md)'s capacity — the exact maximum number of simultaneous, in-flight calls to a protected dependency that will be permitted at once, whether implemented via a [thread-pool](0268-thread-pool-bulkhead.md) or [semaphore](0269-semaphore-bulkhead.md) bulkhead — and choosing this number correctly is what determines whether a bulkhead actually protects a dependency without needlessly throttling legitimate traffic.

## 2. Why & when

A bulkhead's protective value comes entirely from this one number: set it too high, and the bulkhead provides little real protection, since the dependency can still be overwhelmed by a large-but-still-under-the-limit burst of concurrent traffic — the resource is technically bounded, but not tightly enough to matter. Set it too low, and the bulkhead becomes an artificial bottleneck that throttles perfectly legitimate traffic even when the protected dependency is completely healthy and could easily have handled more concurrent load — turning a protective mechanism into a self-inflicted availability problem. The right value is neither an arbitrary round number nor a value copied from a different dependency's configuration; it should reflect the protected dependency's actual, known capacity to handle concurrent load without degrading.

Set max concurrent calls based on load testing or observed production data about how much genuine concurrent load a specific dependency can sustain before its own performance degrades — informed by that dependency's actual behavior, not guessed at or set to match some other unrelated dependency's configuration.

## 3. Core concept

The max concurrent calls value directly determines the size of the bulkhead's underlying capacity mechanism (a thread pool's size, or a semaphore's permit count); every call attempting to exceed this ceiling is rejected or queued according to the bulkhead's configured overflow behavior, regardless of how the value itself was chosen — an under- or over-provisioned value produces observably different, measurable behavior under load.

```java
BulkheadConfig config = BulkheadConfig.custom()
    .maxConcurrentCalls(20) // the CORE tunable -- everything else about the bulkhead's behavior flows from THIS
    .maxWaitDuration(Duration.ofMillis(0)) // reject immediately if at capacity (vs. wait briefly)
    .build();
Bulkhead bulkhead = Bulkhead.of("inventory-service", config);

// EVERY protected call checks against this SAME limit:
// calls 1-20: proceed normally
// call 21+ (while 20 are still in flight): REJECTED, per maxWaitDuration's configured behavior
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Setting max concurrent calls too low throttles healthy traffic unnecessarily; setting it too high provides little real protection against overwhelming the dependency; the correct value sits between these extremes, informed by the dependency's actual measured capacity" >
  <rect x="20" y="20" width="180" height="55" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="42" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Too LOW</text>
  <text x="110" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">throttles HEALTHY traffic</text>

  <rect x="230" y="20" width="180" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">WELL-TUNED</text>
  <text x="320" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">matches ACTUAL capacity</text>

  <rect x="440" y="20" width="180" height="55" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="530" y="42" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Too HIGH</text>
  <text x="530" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">little REAL protection</text>
</svg>

The right value sits between two failure modes, requiring real data about the dependency's actual capacity to find.

## 5. Runnable example

Scenario: a bulkhead sized too small for a dependency's genuine capacity, unnecessarily rejecting legitimate traffic the dependency could easily have handled, refactored to a correctly sized bulkhead informed by the dependency's measured actual capacity, and finally demonstrating a bulkhead sized too large, showing it fails to actually prevent the dependency from being overwhelmed during a genuine overload scenario.

### Level 1 — Basic

```java
// File: BulkheadTooSmall.java -- sized WAY below the dependency's REAL
// capacity -- unnecessarily REJECTS legitimate traffic.
import java.util.concurrent.*;

public class BulkheadTooSmall {
    static final int DEPENDENCY_ACTUAL_CAPACITY = 50; // the dependency CAN genuinely handle 50 concurrent calls fine
    static Semaphore bulkhead = new Semaphore(5); // but the bulkhead is set MUCH too low

    static boolean tryCall() { return bulkhead.tryAcquire(); }

    public static void main(String[] args) {
        int legitimateConcurrentTraffic = 20; // WELL within the dependency's actual 50-call capacity
        int accepted = 0, rejected = 0;
        for (int i = 0; i < legitimateConcurrentTraffic; i++) {
            if (tryCall()) accepted++; else rejected++;
        }
        System.out.println("Dependency's REAL capacity: " + DEPENDENCY_ACTUAL_CAPACITY + " concurrent calls");
        System.out.println("Legitimate traffic: " + legitimateConcurrentTraffic + " concurrent calls (well within capacity)");
        System.out.println("Accepted: " + accepted + ", REJECTED: " + rejected + " -- UNNECESSARILY throttled, since the dependency could have handled all of it.");
    }
}
```

**How to run:** `javac BulkheadTooSmall.java && java BulkheadTooSmall` (JDK 17+).

Expected output:
```
Dependency's REAL capacity: 50 concurrent calls
Legitimate traffic: 20 concurrent calls (well within capacity)
Accepted: 5, REJECTED: 15 -- UNNECESSARILY throttled, since the dependency could have handled all of it.
```

### Level 2 — Intermediate

```java
// File: BulkheadCorrectlySized.java -- sized based on the dependency's
// ACTUAL measured capacity (with a reasonable safety margin) -- the SAME
// legitimate traffic is now ACCEPTED normally.
import java.util.concurrent.*;

public class BulkheadCorrectlySized {
    static final int DEPENDENCY_ACTUAL_CAPACITY = 50; // the SAME real capacity as Level 1
    static Semaphore bulkhead = new Semaphore(40); // sized with a REASONABLE margin below the real 50-call limit

    static boolean tryCall() { return bulkhead.tryAcquire(); }

    public static void main(String[] args) {
        int legitimateConcurrentTraffic = 20; // the SAME legitimate load as Level 1
        int accepted = 0, rejected = 0;
        for (int i = 0; i < legitimateConcurrentTraffic; i++) {
            if (tryCall()) accepted++; else rejected++;
        }
        System.out.println("Accepted: " + accepted + ", rejected: " + rejected + " -- ALL legitimate traffic sailed through normally.");
    }
}
```

**How to run:** `javac BulkheadCorrectlySized.java && java BulkheadCorrectlySized` (JDK 17+).

Expected output:
```
Accepted: 20, rejected: 0 -- ALL legitimate traffic sailed through normally.
```

### Level 3 — Advanced

```java
// File: BulkheadTooLargeFailsToProtect.java -- sized WELL ABOVE the
// dependency's REAL capacity -- FAILS to actually prevent the
// dependency from being OVERWHELMED during a genuine surge.
public class BulkheadTooLargeFailsToProtect {
    static final int DEPENDENCY_ACTUAL_CAPACITY = 50; // the dependency genuinely DEGRADES beyond 50 concurrent calls
    static final int BULKHEAD_LIMIT = 200; // set FAR too high -- provides essentially NO real protection

    static boolean isDependencyOverwhelmed(int currentConcurrentCalls) {
        return currentConcurrentCalls > DEPENDENCY_ACTUAL_CAPACITY; // the dependency's OWN real breaking point
    }

    public static void main(String[] args) {
        int surgeTraffic = 150; // a REAL traffic surge -- exceeds the dependency's actual capacity, but is STILL under the bulkhead's 200 limit
        int callsThatWouldBeAdmitted = Math.min(surgeTraffic, BULKHEAD_LIMIT); // the BULKHEAD admits all of it -- 150 < 200

        System.out.println("Traffic surge: " + surgeTraffic + " concurrent calls");
        System.out.println("Bulkhead limit: " + BULKHEAD_LIMIT + " -- admits " + callsThatWouldBeAdmitted + " calls (under its OWN limit)");
        System.out.println("Dependency's real capacity: " + DEPENDENCY_ACTUAL_CAPACITY);
        System.out.println("Result: dependency is " + (isDependencyOverwhelmed(callsThatWouldBeAdmitted) ? "OVERWHELMED -- the bulkhead FAILED to protect it, since its limit was set far above the dependency's actual breaking point" : "fine"));
    }
}
```

**How to run:** `javac BulkheadTooLargeFailsToProtect.java && java BulkheadTooLargeFailsToProtect` (JDK 17+).

Expected output:
```
Traffic surge: 150 concurrent calls
Bulkhead limit: 200 -- admits 150 calls (under its OWN limit)
Dependency's real capacity: 50
Result: dependency is OVERWHELMED -- the bulkhead FAILED to protect it, since its limit was set far above the dependency's actual breaking point
```

## 6. Walkthrough

1. **Level 1, an artificially low ceiling** — `bulkhead`, a `Semaphore` with only 5 permits, is checked against 20 legitimate concurrent calls; because the dependency's actual capacity is 50 (far above both the bulkhead's limit and the actual traffic), 15 of the 20 calls are unnecessarily rejected purely due to the bulkhead's own overly conservative configuration, not because the dependency itself was ever at risk.
2. **Level 2, a value informed by real capacity** — `bulkhead` is now sized to 40, chosen deliberately as a reasonable margin below the dependency's known real capacity of 50 (leaving headroom, rather than setting it to exactly 50); the identical 20-call legitimate traffic now sails through completely, since 20 is well within this correctly-calibrated 40-call limit.
3. **Level 2, the correct outcome** — all 20 calls are accepted with zero rejections, demonstrating that a bulkhead sized appropriately to the dependency's actual capacity provides its intended protection (still capping concurrency well below the dependency's breaking point) without needlessly throttling traffic that the dependency could genuinely have handled.
4. **Level 3, a bulkhead sized far too generously** — `BULKHEAD_LIMIT` is set to 200, dramatically higher than the dependency's actual, measured breaking point of 50 concurrent calls; `isDependencyOverwhelmed` models the dependency's own real degradation threshold, independent of whatever the bulkhead happens to be configured to.
5. **Level 3, a surge that slips through unprotected** — `surgeTraffic` of 150 concurrent calls is well below the bulkhead's overly generous 200-call limit, so the bulkhead admits the entire surge without rejecting anything (`callsThatWouldBeAdmitted = 150`) — but 150 is three times the dependency's actual capacity of 50.
6. **Level 3, the protection failure made concrete** — `isDependencyOverwhelmed(150)` correctly reports `true`, since 150 exceeds the dependency's real 50-call breaking point, despite the bulkhead having done nothing to prevent this outcome — the bulkhead technically functioned exactly as configured (it never exceeded its own 200-call ceiling), but because that ceiling was set without regard to the dependency's actual, real capacity, the bulkhead provided essentially no meaningful protection against the exact scenario it exists to prevent, which is precisely why choosing this value correctly, informed by real measurement rather than an arbitrary or overly generous guess, is what determines whether a bulkhead actually does its job.

## 7. Gotchas & takeaways

> **Gotcha:** a dependency's "actual capacity" isn't a fixed, permanent number — it can change as the dependency's own infrastructure scales up or down, or as its own internal bottlenecks shift; a max concurrent calls value that was correctly calibrated against last quarter's dependency capacity can become stale (either too conservative or too permissive) as that dependency evolves, making periodic re-validation against current, real measurements important, not a one-time calibration exercise.

- Max concurrent calls is the specific value that sets a bulkhead's capacity, and its correctness — not just its existence — determines whether the bulkhead actually protects a dependency without needlessly throttling healthy traffic.
- A value set too low throttles legitimate traffic the protected dependency could easily have handled, turning a protective mechanism into a self-inflicted availability problem.
- A value set too high fails to actually prevent the dependency from being overwhelmed during a genuine traffic surge, since the bulkhead's own ceiling sits above the dependency's real breaking point.
- The correct value should be informed by load testing or observed production data about the dependency's genuine capacity to handle concurrent load, with a reasonable safety margin — not an arbitrary round number or a value copied from an unrelated configuration.
- A dependency's actual capacity can shift over time as its own infrastructure or bottlenecks change, so the configured value needs periodic re-validation against current data, not a one-time calibration left unchanged indefinitely.
