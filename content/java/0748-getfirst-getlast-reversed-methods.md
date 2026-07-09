---
card: java
gi: 748
slug: getfirst-getlast-reversed-methods
title: getFirst/getLast/reversed methods
---

## 1. What it is

This entry looks specifically at the **default method implementations** that make [SequencedCollection](0746-sequenced-collections-sequencedcollection.md) and [SequencedMap/SequencedSet](0747-sequencedset-sequencedmap.md) work across *existing* JDK types without breaking anything: `getFirst()`, `getLast()`, and `reversed()`, plus their mutating counterparts `addFirst`/`addLast`/`removeFirst`/`removeLast`. Every one of these is defined as a **default method** on the new interfaces, with each implementing class (`ArrayList`, `ArrayDeque`, `LinkedHashSet`, `LinkedHashMap`, `TreeMap`) providing (or inheriting) an efficient concrete implementation appropriate to its own internal structure.

## 2. Why & when

Retrofitting a brand-new interface onto classes that have existed since Java 1.2 (`ArrayList`) or Java 1.4 (`LinkedHashMap`) without breaking binary compatibility is exactly what Java's **default methods** (added in Java 8 for exactly this kind of evolution) are for: `SequencedCollection` can declare `getFirst()` with a default body that works generically (e.g., "call `iterator().next()`"), and any existing class that already has a more efficient way to get its first element (`ArrayList` can index directly; `ArrayDeque` already tracks its head) can override that default with an $O(1)$ implementation instead of falling back to a generic $O(1)$-or-worse default. This is the concrete mechanism by which "millions of lines of code written against `List` since 2004 keep compiling and keep their performance characteristics" and "new code gets a clean `getFirst()`/`getLast()`/`reversed()` vocabulary" can both be true at once — no migration, no deprecation, no breaking change.

## 3. Core concept

```java
import java.util.*;

List<Integer> arrayBacked = new ArrayList<>(List.of(1, 2, 3));
Deque<Integer> dequeBacked = new ArrayDeque<>(List.of(1, 2, 3));

arrayBacked.getFirst();  // O(1): ArrayList indexes directly into its backing array
dequeBacked.getFirst();  // O(1): ArrayDeque already tracks its head pointer

arrayBacked.reversed();  // a reversed *view*, not a copy — O(1) to create
```

Both calls to `getFirst()` use the *same method name* from `SequencedCollection`, but each concrete class supplies its own efficient implementation underneath — the caller doesn't need to know or care which.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SequencedCollection declares default methods that each concrete class can override with an implementation suited to its own internal structure">
  <rect x="230" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SequencedCollection</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">default getFirst(), getLast(), reversed()</text>

  <line x1="280" y1="70" x2="130" y2="105" stroke="#8b949e"/>
  <line x1="380" y1="70" x2="530" y2="105" stroke="#8b949e"/>

  <rect x="30" y="105" width="200" height="46" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="130" y="124" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ArrayList</text>
  <text x="130" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getFirst = get(0), O(1)</text>

  <rect x="430" y="105" width="200" height="46" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="530" y="124" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ArrayDeque</text>
  <text x="530" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getFirst = existing head ptr, O(1)</text>

  <text x="330" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same interface method, different efficient implementation per class</text>
</svg>

*Default methods let one interface vocabulary cover many existing classes without breaking any of them.*

## 5. Runnable example

Scenario: a small benchmark-style program comparing `getFirst`/`getLast`/`reversed` behavior and cost across different concrete collection types.

### Level 1 — Basic

```java
import java.util.*;

public class SequencedBasic {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>(List.of(10, 20, 30));
        System.out.println("first=" + list.getFirst() + " last=" + list.getLast());
        System.out.println("reversed=" + list.reversed());
    }
}
```

**How to run:** `java SequencedBasic.java` (JDK 21+).

This shows the basic vocabulary working on the most common case, `ArrayList`, where `getFirst`/`getLast` are simple index lookups under the hood and `reversed()` gives an immediately usable backwards view.

### Level 2 — Intermediate

```java
import java.util.*;

public class SequencedAcrossTypes {
    static <E> void report(String label, SequencedCollection<E> collection) {
        System.out.println(label + ": first=" + collection.getFirst()
            + " last=" + collection.getLast()
            + " reversed=" + collection.reversed());
    }

    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>(List.of(1, 2, 3));
        Deque<Integer> deque = new ArrayDeque<>(List.of(1, 2, 3));
        LinkedHashSet<Integer> set = new LinkedHashSet<>(List.of(1, 2, 3));

        report("ArrayList", list);
        report("ArrayDeque", deque);
        report("LinkedHashSet", set);
    }
}
```

**How to run:** `java SequencedAcrossTypes.java`.

The real-world concern added: one generic method, `report`, works identically across `ArrayList`, `ArrayDeque`, and `LinkedHashSet` because all three implement `SequencedCollection` — demonstrating that the retrofit genuinely unifies previously unrelated types under one usable interface.

### Level 3 — Advanced

```java
import java.util.*;

public class SequencedPerf {
    static void timeGetFirst(String label, SequencedCollection<Integer> collection, int iterations) {
        long start = System.nanoTime();
        int sum = 0;
        for (int i = 0; i < iterations; i++) {
            sum += collection.getFirst();
        }
        double micros = (System.nanoTime() - start) / 1000.0 / iterations;
        System.out.printf("%-14s getFirst avg: %.3f us/call (sum=%d, ignore)%n", label, micros, sum);
    }

    public static void main(String[] args) {
        final int SIZE = 100_000;
        final int ITERATIONS = 1_000_000;

        List<Integer> arrayList = new ArrayList<>();
        Deque<Integer> arrayDeque = new ArrayDeque<>();
        for (int i = 0; i < SIZE; i++) {
            arrayList.add(i);
            arrayDeque.addLast(i);
        }

        timeGetFirst("ArrayList", arrayList, ITERATIONS);
        timeGetFirst("ArrayDeque", arrayDeque, ITERATIONS);

        // reversed() as a live view: mutate through it and see the source change
        List<Integer> small = new ArrayList<>(List.of(1, 2, 3));
        List<Integer> reversedView = small.reversed();
        reversedView.set(0, 99); // sets the LAST element of `small`
        System.out.println("small after mutating reversed view: " + small);
    }
}
```

**How to run:** `java SequencedPerf.java`.

This adds the production-flavored hard case: measuring that `getFirst()` stays cheap (constant-time, microseconds regardless of collection size) across both `ArrayList` and `ArrayDeque` even at 100,000 elements — confirming the default-method retrofit didn't sacrifice the $O(1)$ performance either type already had — and demonstrating that `reversed()`'s live-view semantics extend to **writes**, not just reads: setting index `0` of the reversed view changes the *last* element of the source list.

## 6. Walkthrough

Tracing the mutation part of `SequencedPerf.main`:

1. `small` is built as `[1, 2, 3]`.
2. `small.reversed()` returns a live view, `reversedView`, whose own index `0` corresponds to `small`'s **last** element (`3`), index `1` corresponds to `small`'s index `1` (`2`), and index `2` corresponds to `small`'s first element (`1`) — the view's index mapping is simply inverted relative to the source.
3. `reversedView.set(0, 99)` writes `99` into the view's position `0`. Because the view is backed directly by `small`, this write is redirected to `small`'s **last position** (index `2`), replacing `3` with `99`.
4. `small` is now `[1, 2, 99]`.

For the timing loop: each `collection.getFirst()` call for `ArrayList` resolves to a direct array index read at position `0` — no traversal — and for `ArrayDeque`, it resolves to reading the deque's already-tracked head slot. Both are genuinely constant-time, so the measured per-call average stays roughly flat regardless of `SIZE`, printing something like:

```
ArrayList      getFirst avg: 0.00X us/call (sum=...)
ArrayDeque     getFirst avg: 0.00X us/call (sum=...)
small after mutating reversed view: [1, 2, 99]
```

(Exact microsecond values vary by machine; the meaningful result is that both are small and roughly equal, not that one is asymptotically worse.)

## 7. Gotchas & takeaways

> **Gotcha:** not every collection can implement `getFirst`/`getLast`/`reversed` efficiently — a plain `HashSet` has no defined order at all, so it doesn't implement `SequencedCollection`. If you need these operations, you must choose an ordered concrete type (`ArrayList`, `LinkedList`, `ArrayDeque`, `LinkedHashSet`) deliberately; the interface won't magically appear on an unordered collection.

- `getFirst`/`getLast`/`reversed` are default methods on `SequencedCollection`, each overridden by concrete classes with an implementation matching their internal structure — so performance stays what it always was for that class.
- This is a textbook use of Java 8's default methods: adding new interface capability to decades-old classes with zero source or binary breakage.
- `reversed()` views support both reads and writes that map back to the corresponding position in the source collection.
- Prefer these named methods over positional access (`get(0)`, `get(size()-1)`) for both readability and because they work uniformly across `List`, `Deque`, and sequenced sets/maps.
- When writing your own collection-like class that has a natural first/last order, consider implementing `SequencedCollection` (or `SequencedMap`) directly so it composes with existing code written against the interface.
