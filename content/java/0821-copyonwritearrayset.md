---
card: java
gi: 821
slug: copyonwritearrayset
title: CopyOnWriteArraySet
---

## 1. What it is

`CopyOnWriteArraySet<E>` is a thread-safe [`Set`](0803-set.md) implementation built directly on top of [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md) — internally, it *is* a `CopyOnWriteArrayList` with uniqueness enforced by a linear `contains()`/`equals()` scan before every `add()`. It inherits the same copy-on-write strategy: every mutation copies the entire backing array, applies the change, and atomically swaps the reference, while reads and iteration proceed lock-free against a stable snapshot. Because uniqueness checking is a linear scan rather than a hash lookup, `add()` and `contains()` are O(n), not the O(1) average `HashSet` provides.

## 2. Why & when

`CopyOnWriteArraySet` exists for the same niche as `CopyOnWriteArrayList`, but for use cases needing *uniqueness* rather than just an ordered sequence — a read-heavy, write-light set of unique registered listeners or subscribers, iterated constantly by notification logic and modified only rarely (a listener subscribing or unsubscribing). Its O(n) `add`/`contains` cost is a real trade-off, only sensible when the set stays small (a handful to a few dozen elements — typical for listener registries) and reads vastly outnumber writes. For a set that's either large or frequently mutated, [`ConcurrentSkipListSet`](0822-concurrentskiplistset.md) (if sorted order is also wanted) or `Collections.newSetFromMap(new ConcurrentHashMap<>())` (for large, frequently-written, thread-safe sets) are far better choices.

## 3. Core concept

```java
Set<String> subscribers = new CopyOnWriteArraySet<>();
subscribers.add("alice@example.com");
subscribers.add("bob@example.com");
boolean addedAgain = subscribers.add("alice@example.com"); // duplicate -- linear scan finds it, rejected

System.out.println(addedAgain);        // false
System.out.println(subscribers.size()); // 2

Iterator<String> notifying = subscribers.iterator(); // snapshot, exactly like CopyOnWriteArrayList
subscribers.add("carol@example.com");                  // invisible to the iterator above
```

Every `add()` call internally scans the current backing array for an existing match before deciding whether to perform the copy-and-append — this is the O(n) cost that trades against `HashSet`'s O(1) average, in exchange for lock-free, exception-free concurrent iteration.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CopyOnWriteArraySet checks for duplicates with a linear scan before copying the array and appending, unlike HashSet's O(1) hash-based check">
  <rect x="40" y="30" width="230" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HashSet.add(x)</text>
  <text x="155" y="72" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">O(1) average — hash bucket lookup</text>

  <rect x="350" y="30" width="250" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">CopyOnWriteArraySet.add(x)</text>
  <text x="475" y="72" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">O(n) scan + O(n) copy-on-write</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Worth it specifically when reads/iteration dominate and the set stays small</text>
</svg>

*`add()` pays both a linear duplicate scan and a full array copy — a real cost, justified only when reads dominate and the set stays small.*

## 5. Runnable example

Scenario: a small notification-subscriber registry, growing from basic thread-safe unique subscription to proving snapshot iteration behaves identically to `CopyOnWriteArrayList`'s, to a direct benchmark showing exactly why this structure is unsuitable at larger scale.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.*;

public class SubscribersBasic {
    public static void main(String[] args) {
        Set<String> subscribers = new CopyOnWriteArraySet<>();
        subscribers.add("alice@example.com");
        subscribers.add("bob@example.com");
        boolean addedAgain = subscribers.add("alice@example.com"); // duplicate

        System.out.println("subscribers: " + subscribers);
        System.out.println("re-adding alice reported new: " + addedAgain);
    }
}
```

**How to run:** `java SubscribersBasic.java` (JDK 17+).

Expected output:
```
subscribers: [alice@example.com, bob@example.com]
re-adding alice reported new: false
```

Functionally identical to any other `Set` from the caller's perspective — the copy-on-write and linear-scan mechanics underneath are invisible except in performance and concurrency behavior.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class SubscribersSnapshotNotification {
    public static void main(String[] args) {
        Set<String> subscribers = new CopyOnWriteArraySet<>();
        subscribers.add("alice@example.com");
        subscribers.add("bob@example.com");

        Iterator<String> notifying = subscribers.iterator(); // snapshot taken now

        // A new subscriber signs up WHILE notification is conceptually "in progress".
        subscribers.add("carol@example.com");
        subscribers.remove("bob@example.com"); // an existing one unsubscribes too

        System.out.println("notifying based on the OLD snapshot:");
        while (notifying.hasNext()) {
            System.out.println("  -> " + notifying.next());
        }

        System.out.println("current subscriber set (reflects the concurrent changes): " + subscribers);
    }
}
```

**How to run:** `java SubscribersSnapshotNotification.java`.

Expected output:
```
notifying based on the OLD snapshot:
  -> alice@example.com
  -> bob@example.com
current subscriber set (reflects the concurrent changes): [alice@example.com, carol@example.com]
```

The real-world concern added: proving the exact same snapshot-iteration guarantee [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md) provides applies here too — no `ConcurrentModificationException`, and the in-progress notification loop sees a fixed, consistent point-in-time view regardless of subscriptions or unsubscriptions happening concurrently.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class SubscribersScaleComparison {
    public static void main(String[] args) {
        int elementCount = 5_000;
        int operations = 20_000;

        Set<Integer> cowSet = new CopyOnWriteArraySet<>();
        Set<Integer> hashSet = Collections.synchronizedSet(new HashSet<>());

        for (int i = 0; i < elementCount; i++) {
            cowSet.add(i);
            hashSet.add(i);
        }

        long cowTime = timeContainsChecks(cowSet, elementCount, operations);
        long hashSetTime = timeContainsChecks(hashSet, elementCount, operations);

        System.out.println(operations + " contains() checks against a set of " + elementCount + " elements:");
        System.out.println("  CopyOnWriteArraySet:            " + cowTime + " ms");
        System.out.println("  synchronized HashSet:           " + hashSetTime + " ms");
        System.out.println("-> CopyOnWriteArraySet's linear scan does not scale the way HashSet's hashing does");
    }

    static long timeContainsChecks(Set<Integer> set, int elementCount, int checks) {
        Random random = new Random(3);
        long start = System.currentTimeMillis();
        for (int i = 0; i < checks; i++) {
            set.contains(random.nextInt(elementCount));
        }
        return System.currentTimeMillis() - start;
    }
}
```

**How to run:** `java SubscribersScaleComparison.java`. Exact timings vary by machine; the relative gap (`CopyOnWriteArraySet` far slower at this scale) is the reproducible, consistent result.

Expected output shape:
```
20000 contains() checks against a set of 5000 elements:
  CopyOnWriteArraySet:            ~900 ms
  synchronized HashSet:           ~2 ms
-> CopyOnWriteArraySet's linear scan does not scale the way HashSet's hashing does
```

This adds the production-flavored hard case: a direct benchmark demonstrating exactly where `CopyOnWriteArraySet` stops being a reasonable choice. At 5,000 elements, each `contains()` call performs a genuine linear scan (O(n)) through the current backing array — compared against a `synchronized HashSet`'s O(1) average hash lookup, the gap is enormous and grows worse as `elementCount` increases. This is precisely why the type is recommended only for small (listener-registry-sized) sets, never as a general-purpose thread-safe `Set`.

## 6. Walkthrough

Tracing `SubscribersScaleComparison.main`:

1. Both `cowSet` and `hashSet` are populated with the same 5,000 integers, `0` through `4999`.
2. `timeContainsChecks` runs 20,000 random `contains(index)` calls against whichever set is passed in, timing the total elapsed duration.
3. For `hashSet` (a synchronized `HashSet`), each `contains()` call computes the integer's hash code, jumps directly to the corresponding bucket, and checks for a match — O(1) average, so 20,000 calls complete almost instantly regardless of the 5,000-element size.
4. For `cowSet` (`CopyOnWriteArraySet`), each `contains()` call walks the entire backing array from the start, comparing each element via `equals()` until a match is found or the array is exhausted — O(n) per call, meaning 20,000 calls each potentially scanning up to 5,000 elements adds up to roughly 100 million element comparisons in the worst case.
5. The measured elapsed times reflect this directly: the synchronized `HashSet` finishes in a couple of milliseconds, while `CopyOnWriteArraySet` takes hundreds of times longer for the identical logical operation — a stark, reproducible demonstration of why this structure's use case is deliberately narrow.

## 7. Gotchas & takeaways

> **Gotcha:** `CopyOnWriteArraySet`'s `add()`/`contains()`/`remove()` are all O(n), not O(1) — it is fundamentally *not* a drop-in thread-safe replacement for `HashSet` at scale. Reaching for it out of habit (rather than a deliberate read-heavy/write-light/small-size assessment) is a common performance mistake once a "small listener list" quietly grows into a genuinely large set.

- `CopyOnWriteArraySet` is built on [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md), adding a linear-scan duplicate check before every `add()`.
- Reads and iteration are lock-free and see a stable, snapshot-consistent view — exactly like `CopyOnWriteArrayList`, and for the same underlying reason.
- `add`/`contains`/`remove` are all O(n), making this structure appropriate only for **small** sets under **read-heavy, write-light** access patterns — the canonical use case is a listener/subscriber registry.
- For larger or write-heavy thread-safe sets, prefer `Collections.newSetFromMap(new ConcurrentHashMap<>())` or [`ConcurrentSkipListSet`](0822-concurrentskiplistset.md) instead.
- Choosing this type is a deliberate trade-off, not a safe default — verify the expected set size and read/write ratio before reaching for it.
