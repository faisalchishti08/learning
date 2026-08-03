---
card: data-structures
gi: 200
slug: common-pitfalls-anti-patterns
title: Common pitfalls & anti-patterns
---

## 1. What it is

This closing page collects the recurring mistakes seen across every structure on this card into one checklist: the wrong-structure choices, the accidental complexity-class traps, and the subtle correctness bugs that come up again and again in real code and interviews.

## 2. Why & when

Many bugs in data-structure code are not new — they are the same handful of anti-patterns recurring in different disguises. Recognizing the *pattern* of the mistake, not just the specific instance, is what lets you catch it in code you have never seen before, including your own.

## 3. Core concept

**The decision criteria for this page: which anti-pattern applies to the code in front of you?** Each entry below names a symptom, its cause, and the fix, so you can match a real piece of code against this list directly.

**`LinkedList.get(i)` in a loop — accidental O(n^2).** Calling `get(i)` for increasing `i` re-walks the list from an end every time, turning an intended `O(n)` traversal into `O(n^2)`. Fix: use a for-each loop or an explicit iterator, covered in [array vs linked structure memory tradeoffs](0197-array-vs-linked-structure-memory-tradeoffs.md).

**Mutating a `HashMap` key after insertion.** If a key object's fields (used in its `hashCode()`) change after it is inserted, the entry becomes unreachable — future lookups compute a different bucket than where the entry actually lives. Fix: use immutable keys, or never mutate fields that participate in `hashCode()`/`equals()`. See [equals/hashCode contract](0014-equals-hashcode-contract.md).

**Modifying a collection directly during iteration.** Calling `list.remove(x)` (not `iterator.remove()`) inside a for-each loop throws `ConcurrentModificationException`. Fix: use `iterator.remove()`, or collect items to remove into a separate list and remove them after the loop. See [fail-fast vs fail-safe iterators](0187-fail-fast-vs-fail-safe-iterators.md).

**Assuming `HashMap`/`HashSet` iteration order is meaningful or stable.** It depends on internal bucket layout, which can change across JVM versions, across runs, or after a resize. Fix: use `LinkedHashMap`/`LinkedHashSet` if insertion order matters, or `TreeMap`/`TreeSet` if sorted order matters.

**Reaching for a segment tree or balanced tree "just in case" when a simpler structure suffices.** Defaulting to the most powerful structure available costs real code complexity and constant-factor overhead for no benefit if the workload never needs that power. Fix: identify the dominant access pattern first — see [choosing a structure by access pattern](0195-choosing-a-structure-by-access-pattern.md) — and pick the simplest structure that satisfies it.

**Using `PriorityQueue`'s iteration order (or `toString()`) as if it were sorted.** Only the root is guaranteed to be the extreme value; sibling and cousin elements have no guaranteed relative order. Fix: only repeated `poll()` calls yield sorted output. See [heap vs balanced tree](0198-when-to-use-a-heap-vs-a-balanced-tree.md).

**Forgetting that `Arrays.asList` is a fixed-size, live view over an array, not an independent, fully mutable list.** Calling `.add()` on it throws; mutating the original array silently changes the list. Fix: wrap in `new ArrayList<>(Arrays.asList(...))` for full mutability, or use `List.of(...)` for true immutability. See [Arrays.asList & List.of](0189-arrays-aslist-list-of-factory-methods.md).

**Treating `Collections.unmodifiableList` as a defensive copy.** It blocks mutation *through the wrapper*, but the original mutable collection can still change the data from elsewhere. Fix: use `List.copyOf(...)` when a true, disconnected snapshot is required. See [immutable/unmodifiable collections](0188-immutable-unmodifiable-collections.md).

**Choosing a Fenwick tree for a min/max range query.** A Fenwick tree's `rangeQuery` trick relies on an invertible operation (subtraction undoing addition); min/max has no such inverse. Fix: use a segment tree for min/max. See [Fenwick vs segment tree tradeoffs](0177-fenwick-vs-segment-tree-tradeoffs.md).

**Forgetting union by rank/size, or path compression, in a union-find implementation.** Without both, a pathological sequence of unions can degrade `find` to `O(n)`. Fix: always implement both together for the near-constant amortized guarantee. See [union by rank/size](0164-union-by-rank-size.md) and [path compression](0165-path-compression.md).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A checklist-style flow: symptom observed in code, matched against a known anti-pattern, leading to the documented fix">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="20" y="10" width="180" height="40" fill="#161b22" stroke="#f44336"/>
    <text x="110" y="30" text-anchor="middle" font-size="9">symptom: slow/wrong code,</text>
    <text x="110" y="44" text-anchor="middle" font-size="9">or a thrown exception</text>

    <rect x="240" y="10" width="180" height="40" fill="#161b22" stroke="#f0883e"/>
    <text x="330" y="30" text-anchor="middle" font-size="9">match against known</text>
    <text x="330" y="44" text-anchor="middle" font-size="9">anti-pattern list</text>

    <rect x="460" y="10" width="160" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="540" y="30" text-anchor="middle" font-size="9">apply the documented,</text>
    <text x="540" y="44" text-anchor="middle" font-size="9">tested fix</text>

    <line x1="200" y1="30" x2="240" y2="30" stroke="#8b949e" marker-end="url(#arrow)"/>
    <line x1="420" y1="30" x2="460" y2="30" stroke="#8b949e" marker-end="url(#arrow)"/>

    <text x="10" y="90" font-size="9" fill="#8b949e">example row: "ConcurrentModificationException" -&gt; "mutated during iteration" -&gt; "use iterator.remove()"</text>
    <text x="10" y="110" font-size="9" fill="#8b949e">example row: "loop feels O(n) but runs slow" -&gt; "LinkedList.get(i) in a loop" -&gt; "use an iterator instead"</text>
  </g>
</svg>

Most data-structure bugs are recognizable patterns, not novel problems — match the symptom, apply the known fix.

## 5. Runnable example

```java
// CommonPitfalls.java
import java.util.*;

public class CommonPitfalls {

    // Basic: the LinkedList.get(i) O(n^2) trap, and its fix.
    static void basicLevel() {
        List<Integer> linkedList = new LinkedList<>();
        for (int i = 0; i < 1000; i++) linkedList.add(i);

        long sumViaGet = 0;
        long start1 = System.nanoTime();
        for (int i = 0; i < linkedList.size(); i++) sumViaGet += linkedList.get(i); // anti-pattern: O(n^2)
        long slowTime = System.nanoTime() - start1;

        long sumViaIterator = 0;
        long start2 = System.nanoTime();
        for (int value : linkedList) sumViaIterator += value; // fix: O(n)
        long fastTime = System.nanoTime() - start2;

        System.out.printf("basic: get(i) loop -> %.2f ms, iterator loop -> %.2f ms%n",
            slowTime / 1_000_000.0, fastTime / 1_000_000.0);
    }

    // Intermediate: ConcurrentModificationException anti-pattern, and the iterator.remove() fix.
    static void intermediateLevel() {
        List<Integer> numbers = new ArrayList<>(List.of(1, 2, 3, 4, 5, 6));
        try {
            for (int n : numbers) {
                if (n % 2 == 0) numbers.remove(Integer.valueOf(n)); // anti-pattern
            }
        } catch (ConcurrentModificationException e) {
            System.out.println("intermediate: anti-pattern threw -> " + e.getClass().getSimpleName());
        }

        List<Integer> numbersFixed = new ArrayList<>(List.of(1, 2, 3, 4, 5, 6));
        Iterator<Integer> it = numbersFixed.iterator();
        while (it.hasNext()) {
            if (it.next() % 2 == 0) it.remove(); // fix
        }
        System.out.println("intermediate: fixed version result -> " + numbersFixed);
    }

    // Advanced: mutating a HashMap key after insertion -- the entry becomes unreachable.
    static class MutableKey {
        int id;
        MutableKey(int id) { this.id = id; }
        @Override public int hashCode() { return Integer.hashCode(id); }
        @Override public boolean equals(Object o) { return o instanceof MutableKey k && k.id == this.id; }
    }

    static void advancedLevel() {
        Map<MutableKey, String> map = new HashMap<>();
        MutableKey key = new MutableKey(1);
        map.put(key, "original value");

        System.out.println("advanced: lookup before mutation -> " + map.get(new MutableKey(1)));

        key.id = 2; // anti-pattern: mutating a field used in hashCode() after insertion

        System.out.println("advanced: lookup with old id (1) after mutation -> " + map.get(new MutableKey(1)));
        System.out.println("advanced: lookup with new id (2) after mutation -> " + map.get(new MutableKey(2)));
        System.out.println("advanced: the entry is now unreachable by EITHER key -- silently lost");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java CommonPitfalls.java`

## 6. Walkthrough

The `get(i)` loop over a `LinkedList` re-walks from an end on every call, making the loop `O(n^2)` overall; the iterator-based loop instead holds a direct node reference and advances it `O(1)` per step, making the total cost `O(n)`. Both loops compute the identical sum, but the timing difference (widening as list size grows) makes the hidden complexity-class trap visible.

The direct-removal loop over `ArrayList` throws `ConcurrentModificationException` the moment the list's internal `modCount` diverges from what the implicit for-each iterator captured. Switching to an explicit `Iterator` and calling `it.remove()` keeps both in sync, producing the correctly filtered list `[1, 3, 5]` with no exception.

For the mutable-key case: `map.put(key, "original value")` places the entry in whichever bucket `key.hashCode()` (based on `id = 1`) computes. Looking it up immediately with an equivalent key (`new MutableKey(1)`) succeeds, since nothing has changed yet. But after `key.id = 2` mutates the *same object already living inside the map*, the map's internal bucket structure is now stale relative to this key's new hash code — looking up `new MutableKey(1)` fails (the object's `hashCode()` now returns a different value, computed from `id=2`, so it is not even found in the bucket where it was originally placed based on `id=1`), and looking up `new MutableKey(2)` *also* fails, because the map never moved the entry to the bucket that `id=2` would compute — the entry is orphaned, unreachable by any lookup, a silent, hard-to-diagnose bug.

**Complexity.** This page has no single complexity of its own — it aggregates the fixes and their complexity implications from every referenced page above.

## 7. Gotchas & takeaways

> Every pitfall on this page has one thing in common: it silently "works" in a small test case, and only breaks or slows down at a scale, timing, or mutation pattern that a quick manual test rarely exercises — this is exactly why these are the mistakes that make it to production.

- When reviewing data-structure code (your own or someone else's), run it mentally against this checklist first — most bugs in this space are one of these recurring patterns, not something genuinely novel.
- This page closes the [Complexity Cheat-Sheet & Selection](0194-time-space-complexity-table-across-structures.md) section, and with it, the full data-structures card — from arrays and linked lists through advanced trees, probabilistic structures, and the Java Collections Framework.
- When in doubt about which structure to use for a new problem, start from [choosing a structure by access pattern](0195-choosing-a-structure-by-access-pattern.md) and work outward from there.
