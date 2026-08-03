---
card: data-structures
gi: 187
slug: fail-fast-vs-fail-safe-iterators
title: Fail-fast vs fail-safe iterators
---

## 1. What it is

A **fail-fast** iterator detects that its underlying collection was structurally modified during iteration (outside the iterator itself) and immediately throws `ConcurrentModificationException`. A **fail-safe** iterator instead iterates over a stable snapshot or a specially designed concurrent structure, tolerating concurrent modification without throwing — though it may not reflect the very latest changes.

## 2. Why & when

Most `java.util` collections (`ArrayList`, `HashMap`, `HashSet`) use fail-fast iterators, because catching an in-progress bug (modifying a collection while iterating it, usually by accident) immediately is far more useful than silently producing corrupted or unpredictable results. The `java.util.concurrent` collections (`CopyOnWriteArrayList`, `ConcurrentHashMap`) use fail-safe iterators instead, because in genuinely concurrent code, some other thread modifying the collection while you iterate is an expected, normal situation — not a bug to catch.

## 3. Core concept

**How fail-fast detection works.** Standard collections like `ArrayList` and `HashMap` maintain an internal `modCount` field, incremented on every structural change (add, remove — not `set`, which does not change structure). When an iterator is created, it captures the current `modCount`. Every `hasNext()`/`next()` call compares the live `modCount` against the captured value; a mismatch throws `ConcurrentModificationException` immediately.

**Why this is "best-effort," not a hard guarantee.** The Java documentation is explicit: fail-fast behavior is not guaranteed in all cases (a modification that happens not to change `modCount` in a detectable way could slip through), so code should never rely on `ConcurrentModificationException` for correctness — only as a debugging aid that surfaces likely bugs early.

**How fail-safe iteration works, by structure.** `CopyOnWriteArrayList`: every mutation creates a brand-new copy of the entire backing array; an iterator created before the mutation keeps its own reference to the **old** array, so it never sees the change and never throws — it simply iterates a frozen snapshot from the moment it was created. `ConcurrentHashMap`: iterators are weakly consistent — they reflect the state of the map at some point during (not necessarily at the start or end of) the iteration, may or may not show concurrent updates, but never throw and never re-traverse an element.

**The tradeoff.** Fail-fast catches bugs early but cannot be used safely across threads without external synchronization. Fail-safe tolerates concurrent modification without crashing, but its snapshot/weakly-consistent view may be stale, and the copy-on-write mechanism specifically has a real memory and CPU cost per mutation.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fail-fast iterator detecting a modCount mismatch and throwing, versus fail-safe iterator working from a separate snapshot unaffected by concurrent changes">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20" fill="#f44336">Fail-fast (ArrayList):</text>
    <rect x="20" y="30" width="200" height="30" fill="#161b22" stroke="#f44336"/>
    <text x="120" y="50" text-anchor="middle" font-size="9">modCount=3 (iterator captured 3)</text>
    <text x="20" y="80" font-size="9" fill="#f44336">list.add(x) elsewhere -&gt; modCount=4</text>
    <text x="20" y="100" font-size="9" fill="#f44336">next() checks 4 != 3 -&gt; throws immediately</text>

    <text x="340" y="20" fill="#3fb950">Fail-safe (CopyOnWriteArrayList):</text>
    <rect x="350" y="30" width="200" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="450" y="50" text-anchor="middle" font-size="9">iterator holds snapshot array</text>
    <text x="350" y="80" font-size="9" fill="#3fb950">list.add(x) elsewhere -&gt; new array created</text>
    <text x="350" y="100" font-size="9" fill="#3fb950">iterator keeps using its OLD snapshot, no throw</text>
  </g>
</svg>

Fail-fast compares a live counter every step; fail-safe iterates a private, unaffected snapshot.

## 5. Runnable example

```java
// FailFastVsFailSafe.java
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;

public class FailFastVsFailSafe {

    // Basic: trigger ConcurrentModificationException on a fail-fast ArrayList iterator.
    static void basicLevel() {
        List<Integer> numbers = new ArrayList<>(List.of(1, 2, 3, 4));
        try {
            for (int n : numbers) {
                if (n == 2) {
                    numbers.remove(Integer.valueOf(2)); // modifying the list directly during for-each
                }
            }
        } catch (ConcurrentModificationException e) {
            System.out.println("basic: caught -> " + e.getClass().getSimpleName());
        }
    }

    // Intermediate: the safe fix -- use Iterator.remove() instead of the collection's own remove().
    static void intermediateLevel() {
        List<Integer> numbers = new ArrayList<>(List.of(1, 2, 3, 4));
        Iterator<Integer> it = numbers.iterator();
        while (it.hasNext()) {
            if (it.next() == 2) {
                it.remove(); // safe: the iterator's own remove keeps modCount in sync
            }
        }
        System.out.println("intermediate: safely removed via Iterator.remove() -> " + numbers);
    }

    // Advanced: CopyOnWriteArrayList never throws, but its iterator sees a frozen snapshot from creation time.
    static void advancedLevel() {
        CopyOnWriteArrayList<Integer> numbers = new CopyOnWriteArrayList<>(List.of(1, 2, 3, 4));
        Iterator<Integer> it = numbers.iterator(); // snapshot taken here: [1,2,3,4]

        numbers.add(5); // mutates the live list; the iterator's snapshot is unaffected

        List<Integer> seenByIterator = new ArrayList<>();
        while (it.hasNext()) seenByIterator.add(it.next());

        System.out.println("advanced: live list after add -> " + numbers);
        System.out.println("advanced: iterator's frozen snapshot (does not include 5) -> " + seenByIterator);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java FailFastVsFailSafe.java`

## 6. Walkthrough

Start with `[1, 2, 3, 4]` in an `ArrayList`. The for-each loop implicitly creates an `Iterator`, which captures `modCount` at creation. When the loop body calls `numbers.remove(Integer.valueOf(2))` directly (not through the iterator), the list's internal `modCount` increments, but the iterator's captured copy does not. On the next `hasNext()`/`next()` call, the iterator compares its stale captured value against the live `modCount`, finds a mismatch, and throws `ConcurrentModificationException` — exactly the "best-effort bug detector" behavior described above.

The fix: use `it.remove()` instead of `numbers.remove(...)`. Because `Iterator.remove()` is implemented as part of the same object doing the traversal, it updates both the list **and** the iterator's internal expected-`modCount` together, keeping them in sync — no exception, and the removal is applied correctly, producing `[1, 3, 4]`.

For `CopyOnWriteArrayList`: calling `.iterator()` captures a reference to the **current backing array** — `[1, 2, 3, 4]`. Calling `numbers.add(5)` afterward does not mutate that array in place; instead, `CopyOnWriteArrayList` allocates a **brand-new** array `[1, 2, 3, 4, 5]` and swaps the list's internal reference to point at it. The already-created iterator still holds its reference to the **old** array, so it iterates `[1, 2, 3, 4]` — never seeing the `5`, and never throwing, because from its perspective nothing about the array it is reading ever changed.

**Complexity.** Fail-fast detection: `O(1)` overhead per `next()` call (one integer comparison). Fail-safe via copy-on-write: each **mutation** costs `O(n)` to copy the entire backing array, but each **read** (including iteration) is lock-free and `O(1)` per step — a deliberate tradeoff favoring cheap, frequent reads over occasional, expensive writes.

## 7. Gotchas & takeaways

> `ConcurrentModificationException` can occur even in **single-threaded** code — it is not exclusively a concurrency bug indicator. Any direct mutation of a collection during its own iteration, even from the same thread, triggers it. The name is about *concurrent* modification of the collection's structure relative to the iterator, not necessarily about multiple threads.

- Never rely on `ConcurrentModificationException` being thrown as a correctness guarantee — the Javadoc explicitly calls this "best-effort," so code should be written to avoid the unsafe pattern in the first place, not to catch the exception as a control-flow mechanism.
- `CopyOnWriteArrayList` is a good fit for read-heavy, write-rare concurrent scenarios (like a list of event listeners) — its `O(n)` write cost makes it a poor fit for write-heavy workloads.
- `ConcurrentHashMap`'s iterators are weakly consistent, not snapshot-based like `CopyOnWriteArrayList` — they may reflect some, all, or none of a concurrent modification made during the iteration, but they are still guaranteed never to throw and never to revisit an already-seen element.
