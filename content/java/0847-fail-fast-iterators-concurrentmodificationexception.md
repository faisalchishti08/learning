---
card: java
gi: 847
slug: fail-fast-iterators-concurrentmodificationexception
title: Fail-fast iterators & ConcurrentModificationException
---

## 1. What it is

Most standard collection iterators (`ArrayList`, `HashMap`, `HashSet`, and the rest — everything **except** the explicitly concurrent collections like [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md) or [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)) are **fail-fast**: each collection tracks an internal `modCount` field, incremented on every structural modification (add/remove, but not a mere `set`/replace). Every iterator captures the collection's `modCount` at creation time, and every `next()` call re-checks that the collection's current `modCount` still matches what it captured — if a structural modification happened outside the iterator's own `remove()` method, the counts diverge, and `next()` throws `ConcurrentModificationException` immediately, rather than continuing to operate on data whose internal layout may have shifted underneath it.

## 2. Why & when

Continuing to iterate a collection whose structure changed mid-traversal (elements shifted, resized, or rehashed) risks skipping elements, revisiting elements, or in more severe cases, corrupting the iteration entirely — silent incorrectness that could go completely unnoticed. Fail-fast behavior trades that silent risk for a loud, immediate, unambiguous signal: `ConcurrentModificationException` the moment an unexpected structural change is detected, making bugs (a `remove()` call made directly on the collection instead of through the iterator, or accidental concurrent modification from another thread) visible during development and testing rather than manifesting as subtle data corruption in production. It's important to understand this is explicitly a **best-effort** mechanism, not a hard guarantee — the JDK documentation itself states fail-fast behavior "should be used only to detect bugs," never relied upon for program correctness, because there are specific situations where a genuine concurrent modification occurs but `ConcurrentModificationException` is *not* thrown.

## 3. Core concept

```java
List<String> items = new ArrayList<>(List.of("a", "b", "c"));

for (String item : items) {
    if (item.equals("b")) {
        items.remove(item); // modifies the list DIRECTLY, bypassing the iterator's own bookkeeping
    }
}
// throws ConcurrentModificationException on the loop's NEXT next() call after the remove --
// the for-each loop's hidden iterator detects modCount changed unexpectedly.
```

The exception is thrown by the iterator's `next()` (or sometimes `hasNext()`, depending on the specific case), not by the `remove()` call itself — the `remove()` succeeds and the modification actually happens; it's the *following* iteration step that discovers the mismatch and reports it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An iterator captures the collection's modCount at creation; each next call compares it against the collection's current modCount, throwing ConcurrentModificationException on a mismatch">
  <rect x="40" y="30" width="200" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="57" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">iterator created</text>
  <text x="140" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">captures modCount = 3</text>

  <line x1="140" y1="75" x2="140" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a847)"/>

  <rect x="40" y="110" width="200" height="45" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="140" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">list.remove(x) directly</text>
  <text x="140" y="100" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">collection's modCount -&gt; 4</text>

  <rect x="380" y="70" width="220" height="45" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="490" y="97" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">next() checks: 4 != 3 -&gt; throw CME</text>

  <line x1="240" y1="132" x2="375" y2="95" stroke="#f85149" stroke-width="1.5" marker-end="url(#a847r)"/>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The mismatch is detected on the NEXT call to next(), not at the moment of the actual modification</text>

  <defs>
    <marker id="a847" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a847r" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

*The iterator's captured `modCount` is compared against the collection's current one on every `next()` call — a mismatch throws immediately.*

## 5. Runnable example

Scenario: exploring the exact boundaries of fail-fast detection, growing from the standard detected case, through a documented edge case where detection surprisingly does NOT fire, to a genuine cross-thread scenario proving the mechanism is best-effort, not a hard guarantee.

### Level 1 — Basic

```java
import java.util.*;

public class StandardDetectionCase {
    public static void main(String[] args) {
        List<String> items = new ArrayList<>(List.of("a", "b", "c", "d"));

        try {
            for (String item : items) {
                if (item.equals("b")) {
                    items.remove(item); // direct removal, bypassing the iterator
                }
            }
        } catch (ConcurrentModificationException e) {
            System.out.println("caught: " + e.getClass().getSimpleName() + " (the standard, expected case)");
        }

        System.out.println("list after the failed attempt: " + items);
    }
}
```

**How to run:** `java StandardDetectionCase.java` (JDK 17+).

Expected output:
```
caught: ConcurrentModificationException (the standard, expected case)
list after the failed attempt: [a, c, d]
```

This is the standard, reliably-detected case: removing `"b"` directly (not through the iterator) is caught on the very next `next()` call the for-each loop makes, exactly as fail-fast detection is designed to work.

### Level 2 — Intermediate

```java
import java.util.*;

public class SecondToLastElementQuirk {
    public static void main(String[] args) {
        // A DOCUMENTED quirk: removing the SECOND-TO-LAST element can fail to throw CME at all,
        // because hasNext() returns false (correctly, by coincidence) BEFORE the modCount check
        // inside next() would have caught the problem -- the loop simply ends early, silently.
        List<String> items = new ArrayList<>(List.of("a", "b", "c"));

        for (String item : items) {
            System.out.println("visiting: " + item);
            if (item.equals("b")) { // "b" is the SECOND-TO-LAST element in a 3-element list
                items.remove(item); // removes "b" -- list becomes ["a", "c"], size drops from 3 to 2
            }
        }
        // NOTICE: "c" is silently never visited, and NO exception was thrown at all!

        System.out.println("final list: " + items);
        System.out.println("-> 'c' was silently skipped, and no ConcurrentModificationException occurred");
        System.out.println("-> this is a DOCUMENTED best-effort limitation, not a bug in your code");
    }
}
```

**How to run:** `java SecondToLastElementQuirk.java`.

Expected output:
```
visiting: a
visiting: b
final list: [a, c]
-> 'c' was silently skipped, and no ConcurrentModificationException occurred
-> this is a DOCUMENTED best-effort limitation, not a bug in your code
```

The real-world concern added: a well-known, documented `ArrayList` iterator quirk. After removing `"b"` (the second-to-last of three elements), the list's size drops to 2. The for-each loop's next check is `hasNext()`, which compares the iterator's internal cursor position against the list's (now-smaller) size — and by coincidence, that check correctly (from `hasNext`'s narrow perspective) reports `false`, ending the loop *before* the `modCount` mismatch would ever have been checked inside a `next()` call. The result: `"c"` is silently never visited, and no exception warns that anything unusual happened at all — proof that fail-fast detection is a best-effort heuristic, not a guarantee that covers every case.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class CrossThreadModification {
    public static void main(String[] args) throws InterruptedException {
        List<Integer> sharedList = Collections.synchronizedList(new ArrayList<>());
        for (int i = 0; i < 1000; i++) sharedList.add(i);

        ExecutorService pool = Executors.newFixedThreadPool(2);
        int[] outcome = {0}; // 0 = not yet determined, 1 = CME thrown, 2 = completed without CME

        Future<?> iterationTask = pool.submit(() -> {
            try {
                int count = 0;
                for (Integer value : sharedList) { // fail-fast iteration, no external synchronized block (deliberately, to show the risk)
                    count++;
                }
                outcome[0] = 2;
                System.out.println("iteration completed without exception, count: " + count);
            } catch (ConcurrentModificationException e) {
                outcome[0] = 1;
                System.out.println("caught ConcurrentModificationException from cross-thread modification");
            }
        });

        pool.submit(() -> {
            for (int i = 0; i < 50; i++) {
                sharedList.add(9999); // concurrent structural modification from ANOTHER thread
            }
        });

        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        iterationTask.get();

        System.out.println("-> CME is POSSIBLE here but NOT GUARANTEED -- outcome depends on precise thread timing");
        System.out.println("-> this is exactly why the JDK docs say: never rely on CME for correctness, only for bug-detection");
    }
}
```

**How to run:** `java CrossThreadModification.java`. This is genuinely non-deterministic — depending on exact thread scheduling, this may print either outcome, and could even occasionally complete without any exception despite the concurrent modification actually happening, or throw some other unusual exception, since the JDK explicitly does not guarantee well-defined behavior once fail-fast is violated from another thread.

Expected output shape (either outcome is a "correct" demonstration of the point):
```
caught ConcurrentModificationException from cross-thread modification
-> CME is POSSIBLE here but NOT GUARANTEED -- outcome depends on precise thread timing
-> this is exactly why the JDK docs say: never rely on CME for correctness, only for bug-detection
```

This adds the production-flavored hard case: a genuine cross-thread structural modification during iteration, with no external synchronization protecting the loop (a violation of the exact discipline required by [`Collections.synchronizedList`](0844-collections-synchronized-wrappers.md)'s own documentation). `ConcurrentModificationException` is a *likely*, but explicitly not *guaranteed*, outcome here — the JDK documentation states fail-fast behavior "cannot be guaranteed" in the presence of unsynchronized concurrent modification, precisely because the underlying `modCount` check itself isn't atomic with respect to other threads, and could theoretically miss a modification, or the collection's internal state could be observed in a genuinely inconsistent, undefined way.

## 6. Walkthrough

Tracing `SecondToLastElementQuirk.main`, the quirk that best illustrates fail-fast's best-effort nature:

1. `items` starts as `["a", "b", "c"]`, a 3-element `ArrayList`. The for-each loop's hidden iterator begins with `cursor = 0`.
2. First iteration: `hasNext()` checks `cursor (0) != size (3)` — true, so `next()` returns `"a"` and advances `cursor` to 1. The `modCount` check inside `next()` passes (nothing has been modified yet). `"a"` is printed.
3. Second iteration: `hasNext()` checks `cursor (1) != size (3)` — true, `next()` returns `"b"` and advances `cursor` to 2, `modCount` check passes. `"b"` is printed, and because `item.equals("b")`, `items.remove("b")` is called directly — this removes the element at index 1, shifting `"c"` down to index 1, shrinking `size` from 3 to 2, and incrementing the list's internal `modCount`.
4. Third iteration: `hasNext()` is checked next — it compares `cursor (2) != size (2)`. Since the list's `remove` call just shrank `size` to 2, and `cursor` is also 2, this comparison is `false` — `hasNext()` reports the iteration is complete, and the for-each loop exits normally, **without ever calling `next()` again**.
5. Because the `modCount` mismatch is only ever checked *inside* `next()` (not inside `hasNext()`), and `hasNext()` returned `false` before `next()` was ever called a third time, the mismatch is never actually checked at all — no exception fires, and `"c"` (which shifted into index 1 but was never visited, since the loop believed it had reached the end) is silently skipped entirely.

## 7. Gotchas & takeaways

> **Gotcha:** fail-fast detection is explicitly a **best-effort** mechanism, documented by the JDK as such — it is not guaranteed to detect every concurrent or unsynchronized structural modification, as the second-to-last-element removal case demonstrates concretely. Never write code whose *correctness* depends on `ConcurrentModificationException` being thrown; only ever treat it as a helpful bug-detection signal on a best-effort basis.

- Fail-fast iterators track a `modCount` captured at creation, checked against the collection's current `modCount` on every `next()` call — a mismatch throws `ConcurrentModificationException` immediately.
- The only safe way to remove elements mid-iteration is through the iterator's own `remove()` method (see [Iterator](0809-iterator.md)), which updates `modCount` consistently with the iterator's own bookkeeping.
- The JDK explicitly documents this as best-effort: specific edge cases (like removing the second-to-last element of a list) can silently skip detection entirely, due to `hasNext()`'s check happening before `next()`'s `modCount` comparison ever runs.
- Cross-thread structural modification during unsynchronized iteration may or may not throw `ConcurrentModificationException` — the outcome is genuinely non-deterministic and must never be relied upon for program correctness.
- For collections genuinely modified concurrently from multiple threads, use fail-safe or weakly-consistent alternatives instead — [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)'s snapshot iterators or [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md)'s weakly consistent iterators are designed specifically to avoid this class of problem entirely, rather than merely detecting it inconsistently.
