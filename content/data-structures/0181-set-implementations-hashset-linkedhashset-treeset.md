---
card: data-structures
gi: 181
slug: set-implementations-hashset-linkedhashset-treeset
title: Set implementations (HashSet, LinkedHashSet, TreeSet)
---

## 1. What it is

`HashSet`, `LinkedHashSet`, and `TreeSet` are the three main `Set` implementations in `java.util`. All three forbid duplicates, matching the `Set` contract, but they differ in what order (if any) they iterate elements in, and in what backs their duplicate-checking.

## 2. Why & when

Pick based on whether you need ordering and what kind. `HashSet` gives the fastest average operations but no ordering guarantee at all. `LinkedHashSet` costs slightly more but preserves insertion order, useful when you want fast lookup and predictable iteration (like deduplicating a list while keeping the first-seen order). `TreeSet` keeps elements sorted at all times, at a higher per-operation cost, useful when you need range queries (`floor`, `ceiling`, `headSet`) or always-sorted iteration.

## 3. Core concept

**What backs each one.** `HashSet` is backed by a `HashMap` internally (each element is stored as a key, with a shared dummy value) — see [hash functions](0085-hash-functions-desirable-properties.md) for the mechanics. `LinkedHashSet` extends `HashSet` but threads a doubly linked list through the entries to preserve insertion order. `TreeSet` is backed by a `TreeMap`, which is backed by a red-black tree — see [TreeMap/TreeSet](0113-treemap-treeset-red-black-backed.md).

**Ordering and complexity guarantees.** `HashSet`: no ordering guarantee; `add`/`contains`/`remove` are `O(1)` average. `LinkedHashSet`: insertion order preserved; same `O(1)` average operations, with a small constant-factor overhead for maintaining the linked list. `TreeSet`: always sorted (natural order or a supplied `Comparator`); `add`/`contains`/`remove` are `O(log n)`.

**Why `TreeSet` costs more but gives more.** Every insert into a `TreeSet` must find its sorted position in a red-black tree, costing `O(log n)` instead of `HashSet`'s `O(1)` average. In exchange, `TreeSet` supports operations no hash-based set can: `first()`, `last()`, `floor(x)`, `ceiling(x)`, and sorted iteration — because the elements are never actually stored in a way that has an "order" for `HashSet` or `LinkedHashSet` to expose beyond insertion sequence.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HashSet with no order, LinkedHashSet preserving insertion order, and TreeSet keeping elements sorted, for the same inserted values">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">insert order: 5, 1, 3</text>

    <text x="10" y="60">HashSet iteration (unordered, bucket-dependent):</text>
    <rect x="280" y="45" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="295" y="61" text-anchor="middle">1</text>
    <rect x="315" y="45" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="330" y="61" text-anchor="middle">3</text>
    <rect x="350" y="45" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="365" y="61" text-anchor="middle">5</text>

    <text x="10" y="100">LinkedHashSet iteration (insertion order):</text>
    <rect x="280" y="85" width="30" height="24" fill="#161b22" stroke="#79c0ff"/><text x="295" y="101" text-anchor="middle">5</text>
    <rect x="315" y="85" width="30" height="24" fill="#161b22" stroke="#79c0ff"/><text x="330" y="101" text-anchor="middle">1</text>
    <rect x="350" y="85" width="30" height="24" fill="#161b22" stroke="#79c0ff"/><text x="365" y="101" text-anchor="middle">3</text>

    <text x="10" y="140">TreeSet iteration (always sorted):</text>
    <rect x="280" y="125" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="295" y="141" text-anchor="middle">1</text>
    <rect x="315" y="125" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="330" y="141" text-anchor="middle">3</text>
    <rect x="350" y="125" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="365" y="141" text-anchor="middle">5</text>
  </g>
</svg>

Same three elements, three different iteration orders — chosen by which guarantee you need.

## 5. Runnable example

```java
// SetImplementations.java
import java.util.*;

public class SetImplementations {

    // Basic: the same insertions into all three Set types, showing the different iteration orders.
    static void basicLevel() {
        Set<Integer> hashSet = new HashSet<>();
        Set<Integer> linkedHashSet = new LinkedHashSet<>();
        Set<Integer> treeSet = new TreeSet<>();

        for (int value : new int[]{5, 1, 3}) {
            hashSet.add(value);
            linkedHashSet.add(value);
            treeSet.add(value);
        }

        System.out.println("basic: HashSet -> " + hashSet);
        System.out.println("basic: LinkedHashSet (insertion order) -> " + linkedHashSet);
        System.out.println("basic: TreeSet (sorted order) -> " + treeSet);
    }

    // Intermediate: deduplicate a list while preserving first-seen order, using LinkedHashSet.
    static List<String> deduplicatePreservingOrder(List<String> items) {
        return new ArrayList<>(new LinkedHashSet<>(items));
    }

    static void intermediateLevel() {
        List<String> input = List.of("banana", "apple", "banana", "cherry", "apple");
        System.out.println("intermediate: deduplicated, order preserved -> " + deduplicatePreservingOrder(input));
    }

    // Advanced: TreeSet's range operations, unavailable on HashSet or LinkedHashSet.
    static void advancedLevel() {
        TreeSet<Integer> scores = new TreeSet<>(List.of(55, 62, 71, 84, 90, 95));

        System.out.println("advanced: first() -> " + scores.first());
        System.out.println("advanced: last() -> " + scores.last());
        System.out.println("advanced: floor(80) -> " + scores.floor(80));    // largest <= 80
        System.out.println("advanced: ceiling(80) -> " + scores.ceiling(80)); // smallest >= 80
        System.out.println("advanced: headSet(80) -> " + scores.headSet(80)); // all elements < 80
        System.out.println("advanced: tailSet(80) -> " + scores.tailSet(80)); // all elements >= 80
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java SetImplementations.java`

## 6. Walkthrough

Insert `5, 1, 3` into all three sets in that order. `HashSet` places each value into a bucket determined by its hash code; the iteration order (`[1, 3, 5]` in this case) is an artifact of bucket layout, not insertion order, and should never be relied upon. `LinkedHashSet` places values the same way for lookup, but also threads them into a linked list in the order they were inserted, so iteration always yields `[5, 1, 3]` — matching insertion exactly. `TreeSet` inserts each value into a red-black tree keyed by natural ordering, so iteration always yields `[1, 3, 5]` — sorted, regardless of insertion order.

For deduplication: `deduplicatePreservingOrder` wraps the input list in a `LinkedHashSet`, which drops the second `"banana"` and second `"apple"` (duplicates), while keeping the surviving elements in their original first-seen order: `[banana, apple, cherry]`. Using a plain `HashSet` here would still deduplicate correctly but could reorder the result unpredictably.

For `TreeSet`'s range operations: `floor(80)` finds the largest stored value `<= 80`, which is `71`. `ceiling(80)` finds the smallest stored value `>= 80`, which is `84`. `headSet(80)` returns a live view of all elements strictly less than `80`. These operations have no equivalent on `HashSet` or `LinkedHashSet`, because those structures have no notion of "less than" between arbitrary elements beyond equality.

**Complexity.** `HashSet`: `add`/`contains`/`remove` `O(1)` average. `LinkedHashSet`: same, plus `O(1)` extra for linked-list maintenance. `TreeSet`: `add`/`contains`/`remove` `O(log n)`; range and navigation operations (`floor`, `ceiling`, `headSet`) also `O(log n)`.

## 7. Gotchas & takeaways

> `TreeSet` requires elements to be mutually comparable — either they implement `Comparable`, or you supply a `Comparator` at construction. Adding an element that cannot be compared to existing elements throws a `ClassCastException` at runtime, not a compile-time error.

- Never rely on `HashSet`'s iteration order for correctness — it can change between JVM versions, between runs, or even after a resize, since it depends on internal bucket layout.
- `LinkedHashSet` costs a small, constant amount more than `HashSet` per operation, for the benefit of predictable iteration order — a good default when you want deduplication with the "first occurrence wins" behavior.
- Reach for `TreeSet` specifically when you need sorted iteration or range queries (`floor`, `ceiling`, `subSet`) — for everything else, `HashSet` or `LinkedHashSet` is faster.
