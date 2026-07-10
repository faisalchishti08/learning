---
card: java
gi: 848
slug: fail-safe-iterators
title: Fail-safe iterators
---

## 1. What it is

Fail-safe iterators are the opposite design choice from [fail-fast iterators](0847-fail-fast-iterators-concurrentmodificationexception.md): instead of detecting and throwing on concurrent structural modification, they're built to tolerate it entirely, by design, never throwing `ConcurrentModificationException` regardless of what happens to the collection during iteration. The JDK's concurrent collections achieve this in two different ways: [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)/[`CopyOnWriteArraySet`](0821-copyonwritearrayset.md) iterators traverse a fixed **snapshot** of the array taken at iterator-creation time, completely insulated from any later modification; [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md)/[`ConcurrentLinkedQueue`](0837-concurrentlinkedqueue-deque.md) iterators are **weakly consistent** — they traverse the live, actively-changing structure without locking, guaranteed to reflect the state of the collection as of iterator creation and to never throw, but not guaranteed to reflect every subsequent modification, or to represent any single consistent instant once concurrent changes occur.

## 2. Why & when

Fail-fast's throw-on-detection behavior is the right choice for single-threaded (or externally-synchronized) code, where an unexpected structural change during iteration almost always indicates a real bug worth surfacing loudly. But for collections genuinely designed for concurrent multi-threaded access — where "some other thread might be adding or removing elements right now" isn't a bug, it's the expected, normal operating condition — throwing an exception every time that happens would make the collection essentially unusable for its intended purpose. Fail-safe iteration exists specifically for that scenario: a consumer thread can safely iterate a concurrently-modified collection to completion, every time, without needing external locking or having to catch and retry on `ConcurrentModificationException`. The tradeoff, in both flavors, is weaker consistency: a snapshot iterator can present stale data (missing very recent additions), and a weakly consistent iterator doesn't guarantee a single coherent instant's view at all — code relying on fail-safe iteration must accept that the data observed during iteration is *approximately* current, not a hard guarantee of exactness.

## 3. Core concept

```java
// Snapshot-style fail-safe: CopyOnWriteArrayList
CopyOnWriteArrayList<String> snapshotStyle = new CopyOnWriteArrayList<>(List.of("a", "b"));
Iterator<String> snapshotIt = snapshotStyle.iterator(); // fixed snapshot, taken NOW
snapshotStyle.add("c"); // invisible to snapshotIt, no matter what -- it's iterating a frozen copy

// Weakly-consistent-style fail-safe: ConcurrentHashMap
ConcurrentHashMap<String, Integer> weaklyConsistentStyle = new ConcurrentHashMap<>(Map.of("x", 1));
Iterator<String> keyIt = weaklyConsistentStyle.keySet().iterator();
weaklyConsistentStyle.put("y", 2); // MAY or MAY NOT be visible to keyIt, depending on internal timing -- not guaranteed either way

// BOTH iterators are guaranteed to never throw ConcurrentModificationException, regardless of the outcome above.
```

The shared guarantee across both flavors is simply "never throws" — the *specifics* of what each one actually observes during concurrent modification differ meaningfully between the two implementations.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Snapshot-style fail-safe iterators freeze a copy at creation time and never see later changes; weakly consistent iterators traverse the live structure and may or may not see later changes, but neither ever throws">
  <rect x="30" y="30" width="270" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="165" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Snapshot (CopyOnWriteArrayList)</text>
  <text x="165" y="75" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">frozen at creation — NEVER sees later changes</text>

  <rect x="340" y="30" width="270" height="65" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="475" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Weakly consistent (ConcurrentHashMap)</text>
  <text x="475" y="75" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">live traversal — MAY see later changes</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both share ONE guarantee: neither ever throws ConcurrentModificationException</text>
</svg>

*Two different fail-safe strategies, one shared guarantee: neither ever throws, regardless of concurrent modification.*

## 5. Runnable example

Scenario: a live metrics dashboard reading from a concurrently-updated data structure, growing from basic fail-safe iteration proving no exception occurs, to directly contrasting snapshot versus weakly-consistent visibility of concurrent changes, to a realistic monitoring loop that correctly treats its own view as approximate rather than exact.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.*;

public class FailSafeBasic {
    public static void main(String[] args) {
        CopyOnWriteArrayList<String> metrics = new CopyOnWriteArrayList<>(List.of("cpu:ok", "memory:ok"));

        Iterator<String> it = metrics.iterator();
        metrics.add("disk:warning"); // concurrent modification, conceptually -- here just sequential for clarity

        System.out.println("iterating (no exception, guaranteed):");
        while (it.hasNext()) {
            System.out.println("  " + it.next());
        }
        System.out.println("current full metrics list: " + metrics);
    }
}
```

**How to run:** `java FailSafeBasic.java` (JDK 17+).

Expected output:
```
iterating (no exception, guaranteed):
  cpu:ok
  memory:ok
current full metrics list: [cpu:ok, memory:ok, disk:warning]
```

No exception occurs, and — because `CopyOnWriteArrayList`'s iterator is snapshot-based — `"disk:warning"` (added after the iterator was created) is never visible to this particular iteration, even though it's clearly present in the list itself afterward.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class SnapshotVsWeaklyConsistent {
    public static void main(String[] args) {
        // Snapshot style: CopyOnWriteArrayList
        CopyOnWriteArrayList<String> snapshotList = new CopyOnWriteArrayList<>(List.of("a", "b"));
        Iterator<String> snapshotIt = snapshotList.iterator();
        snapshotList.add("c");

        List<String> snapshotSeen = new ArrayList<>();
        while (snapshotIt.hasNext()) snapshotSeen.add(snapshotIt.next());
        System.out.println("snapshot iterator saw: " + snapshotSeen + " (never includes 'c', guaranteed)");

        // Weakly consistent style: ConcurrentHashMap
        ConcurrentHashMap<String, Integer> weakMap = new ConcurrentHashMap<>(Map.of("x", 1, "y", 2));
        Iterator<String> weakIt = weakMap.keySet().iterator();
        weakMap.put("z", 3); // may or may not be observed -- not a hard guarantee either way

        List<String> weakSeen = new ArrayList<>();
        while (weakIt.hasNext()) weakSeen.add(weakIt.next());
        System.out.println("weakly consistent iterator saw: " + weakSeen + " ('z' may or may not appear, both are valid)");
    }
}
```

**How to run:** `java SnapshotVsWeaklyConsistent.java`. The snapshot result is deterministic every run; the weakly-consistent result's inclusion (or exclusion) of `"z"` may vary depending on internal implementation details, though on most current JDK versions for this simple sequential case, it's commonly (but not by any documented guarantee) observed.

Expected output shape:
```
snapshot iterator saw: [a, b] (never includes 'c', guaranteed)
weakly consistent iterator saw: [x, y] ('z' may or may not appear, both are valid)
```

(or, equally validly: `weakly consistent iterator saw: [x, y, z] ('z' may or may not appear, both are valid)`)

The real-world concern added: directly contrasting the two fail-safe strategies side by side on the same kind of operation (add an element after obtaining the iterator, then iterate). The snapshot iterator's exclusion of `"c"` is a **hard, documented guarantee** — code can rely on it. The weakly-consistent iterator's handling of `"z"` is explicitly **not** a guarantee either way — code must not depend on whether such an element appears or not, only on the fact that iteration completes safely regardless.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ApproximateMonitoringLoop {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentHashMap<String, Integer> requestCounts = new ConcurrentHashMap<>();
        AtomicBoolean keepGoing = new AtomicBoolean(true);

        ExecutorService pool = Executors.newFixedThreadPool(3);

        // Simulated request handlers, continuously updating counts.
        for (int i = 0; i < 2; i++) {
            final int workerId = i;
            pool.submit(() -> {
                int req = 0;
                while (keepGoing.get()) {
                    requestCounts.merge("worker-" + workerId, 1, Integer::sum);
                    req++;
                    if (req > 10_000) break;
                }
            });
        }

        // A monitoring task iterating the live map while updates are happening concurrently.
        pool.submit(() -> {
            for (int round = 0; round < 3; round++) {
                try { Thread.sleep(20); } catch (InterruptedException ignored) {}
                int totalObserved = 0;
                for (Integer count : requestCounts.values()) { // fail-safe: never throws, even mid-update
                    totalObserved += count;
                }
                System.out.println("monitoring round " + round + ": approximate total so far = " + totalObserved);
            }
        });

        Thread.sleep(200);
        keepGoing.set(false);
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("final actual totals: " + requestCounts);
        System.out.println("-> monitoring rounds saw APPROXIMATE, ever-increasing totals -- never an exception, never a hard-frozen snapshot");
    }
}
```

**How to run:** `java ApproximateMonitoringLoop.java`. Exact numbers vary significantly by machine speed and thread scheduling; the key guarantee being demonstrated is that the monitoring loop never throws, regardless of the continuously-changing map it's reading from.

Expected output shape:
```
monitoring round 0: approximate total so far = 8214
monitoring round 1: approximate total so far = 15872
monitoring round 2: approximate total so far = 20001
final actual totals: {worker-0=10001, worker-1=10001}
```

This adds the production-flavored hard case: a realistic monitoring/metrics-reading loop iterating a `ConcurrentHashMap` that's being continuously, actively updated by two other worker threads at the same time. Each monitoring round's `totalObserved` is a reasonable **approximation** of the true total at roughly that moment — never a hard, frozen, guaranteed-exact snapshot, and never at risk of throwing an exception either, which is exactly the tradeoff fail-safe (specifically weakly-consistent) iteration is designed to provide: safe, approximate, live monitoring without locking or exceptions.

## 6. Walkthrough

Tracing `ApproximateMonitoringLoop.main`:

1. Two worker tasks are submitted, each looping and calling `requestCounts.merge("worker-N", 1, Integer::sum)` repeatedly — each call atomically increments that worker's own counter, up to 10,000 times or until `keepGoing` is flipped to `false`.
2. A third task runs the monitoring loop: three rounds, each sleeping 20ms then iterating `requestCounts.values()` (a live, weakly-consistent view) and summing whatever counts it observes into `totalObserved`.
3. Because the two worker threads are continuously calling `merge` throughout the entire time the monitoring loop is iterating, the monitoring iterator may observe a counter's value partway through its climb, or may observe a newly-added key that didn't exist when iteration started (if a third worker key were ever added, though here both keys exist from very early on) — none of this causes any exception; the iterator simply reports whatever it currently observes as it walks the live structure.
4. Each round's printed `totalObserved` is expected to increase from round to round, roughly tracking the workers' ongoing progress, but is never guaranteed to be perfectly precise at the exact instant it's computed — by the time the sum finishes accumulating, the actual underlying values may have already changed further.
5. After `keepGoing.set(false)` stops both workers and the pool fully shuts down, the final `requestCounts` printed reflects the true, final, settled totals — contrasted against the necessarily approximate, in-flight totals the monitoring rounds observed while updates were still actively happening, demonstrating the practical difference between "a live, safe, approximate read" and "the final, settled, exact state."

## 7. Gotchas & takeaways

> **Gotcha:** "fail-safe" does not mean "always sees the absolute latest data" — it means "never throws an exception, but the exact data observed under concurrent modification is either a fixed stale snapshot (`CopyOnWriteArrayList`-style) or an unspecified partial view (`ConcurrentHashMap`-style weak consistency)." Code that treats a fail-safe iteration's result as a precise, exact, real-time count is making an assumption the iterator's contract explicitly does not support.

- Fail-safe iterators (as opposed to [fail-fast](0847-fail-fast-iterators-concurrentmodificationexception.md) ones) are designed to never throw `ConcurrentModificationException`, by intentional design rather than best-effort detection.
- [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)/[`CopyOnWriteArraySet`](0821-copyonwritearrayset.md) achieve this via a fixed snapshot taken at iterator creation — later modifications are never visible to that iterator, a hard guarantee.
- [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md)/[`ConcurrentLinkedQueue`](0837-concurrentlinkedqueue-deque.md) achieve this via weak consistency — the iterator traverses the live structure without locking, and may or may not reflect concurrent modifications, with no guarantee either way beyond never throwing.
- Fail-safe iteration is the right choice for genuinely concurrent, continuously-modified data — a monitoring dashboard, a live metrics reader — where throwing on every concurrent change would make the collection unusable for its intended purpose.
- Never rely on the exact contents observed during fail-safe iteration for correctness-critical logic — treat the result as approximately current, not precisely exact, unless the specific implementation's documentation states a stronger guarantee.
