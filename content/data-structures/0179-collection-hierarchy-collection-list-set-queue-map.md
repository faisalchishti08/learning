---
card: data-structures
gi: 179
slug: collection-hierarchy-collection-list-set-queue-map
title: Collection hierarchy (Collection/List/Set/Queue/Map)
---

## 1. What it is

The **Java Collections Framework** is a set of interfaces and classes in `java.util` for storing and manipulating groups of objects. At the top sits the `Collection` interface, with three main branches — `List`, `Set`, `Queue` — each adding different rules about order and duplicates. `Map` sits outside this hierarchy, because it stores key-value pairs, not single elements.

## 2. Why & when

Knowing this hierarchy tells you what any given type guarantees, without reading its source. If a method's parameter type is `List<String>`, you know order matters and duplicates are allowed. If it is `Set<String>`, you know duplicates are impossible. Choosing the right interface as a method signature (not the concrete class) is what lets callers swap `ArrayList` for `LinkedList` later without changing any calling code.

## 3. Core concept

**What backs each branch, at the interface level.** `Collection` is the root interface: add, remove, size, iterate — the bare minimum every group of elements supports. `List` extends it, adding index-based access and allowing duplicates, in insertion order. `Set` extends it, forbidding duplicates, with no guaranteed order (though some implementations add one). `Queue` extends it, adding ordering rules for processing elements (first-in-first-out, or priority-based). `Map` is a **separate root**, not a `Collection`, because it maps keys to values rather than holding a flat group of elements — though every `Map` exposes its keys, values, and entries as `Collection` views.

**Ordering and duplicate guarantees, by branch.** `List`: ordered, duplicates allowed. `Set`: no duplicates; ordering depends on the specific implementation (`HashSet` unordered, `LinkedHashSet` insertion order, `TreeSet` sorted order). `Queue`: typically ordered for removal (FIFO for `LinkedList`-as-`Queue`, priority order for `PriorityQueue`). `Deque` (a sub-interface of `Queue`) allows insertion and removal at both ends.

**Why this matters for choosing an implementation.** The interface tells you *what* is guaranteed; the concrete class tells you *how* it is achieved and at what cost. `List` guarantees order and index access; whether you pick `ArrayList` (fast index access, slow middle insert) or `LinkedList` (slow index access, fast insert at known position) depends on your actual usage pattern, covered in [List implementations](0180-list-implementations-arraylist-linkedlist-vector.md).

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Java Collections Framework hierarchy, with Collection at the root branching into List, Set, and Queue, and Map as a separate root">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="250" y="10" width="140" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="320" y="30" text-anchor="middle">Collection</text>

    <rect x="60" y="80" width="100" height="30" fill="#0d1117" stroke="#8b949e"/><text x="110" y="100" text-anchor="middle">List</text>
    <rect x="270" y="80" width="100" height="30" fill="#0d1117" stroke="#8b949e"/><text x="320" y="100" text-anchor="middle">Set</text>
    <rect x="480" y="80" width="100" height="30" fill="#0d1117" stroke="#8b949e"/><text x="530" y="100" text-anchor="middle">Queue</text>

    <line x1="320" y1="40" x2="110" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="40" x2="320" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="40" x2="530" y2="80" stroke="#79c0ff"/>

    <text x="110" y="145" text-anchor="middle" font-size="8">ArrayList</text>
    <text x="110" y="160" text-anchor="middle" font-size="8">LinkedList</text>
    <text x="320" y="145" text-anchor="middle" font-size="8">HashSet</text>
    <text x="320" y="160" text-anchor="middle" font-size="8">TreeSet</text>
    <text x="530" y="145" text-anchor="middle" font-size="8">ArrayDeque</text>
    <text x="530" y="160" text-anchor="middle" font-size="8">PriorityQueue</text>

    <rect x="270" y="190" width="100" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="320" y="210" text-anchor="middle">Map (separate root)</text>
    <text x="320" y="230" text-anchor="middle" font-size="8" fill="#8b949e">HashMap, LinkedHashMap, TreeMap</text>
  </g>
</svg>

`Map` is deliberately outside the `Collection` tree — it stores pairs, not single elements.

## 5. Runnable example

```java
// CollectionHierarchy.java
import java.util.*;

public class CollectionHierarchy {

    // Basic: the same data added to a List, a Set, and a Queue, showing each interface's guarantees.
    static void basicLevel() {
        List<Integer> list = new ArrayList<>(List.of(3, 1, 3, 2));
        Set<Integer> set = new HashSet<>(List.of(3, 1, 3, 2));
        Queue<Integer> queue = new LinkedList<>(List.of(3, 1, 3, 2));

        System.out.println("basic: List keeps order and duplicates -> " + list);
        System.out.println("basic: Set drops duplicates, no guaranteed order -> " + set);
        System.out.println("basic: Queue keeps insertion order for FIFO removal -> " + queue.poll());
    }

    // Intermediate: Map is not a Collection, but exposes Collection views (keySet, values, entrySet).
    static void intermediateLevel() {
        Map<String, Integer> map = new HashMap<>();
        map.put("a", 1);
        map.put("b", 2);

        Set<String> keys = map.keySet();          // Set view
        Collection<Integer> values = map.values(); // Collection view
        Set<Map.Entry<String, Integer>> entries = map.entrySet(); // Set of pairs

        System.out.println("intermediate: keySet() -> " + keys);
        System.out.println("intermediate: values() -> " + values);
        System.out.println("intermediate: entrySet() -> " + entries);
    }

    // Advanced: write a method against the Collection interface, so it works for any branch of the hierarchy.
    static int countGreaterThan(Collection<Integer> items, int threshold) {
        int count = 0;
        for (int item : items) {
            if (item > threshold) count++;
        }
        return count;
    }

    static void advancedLevel() {
        List<Integer> list = List.of(5, 10, 15, 20);
        Set<Integer> set = new TreeSet<>(List.of(5, 10, 15, 20));

        System.out.println("advanced: countGreaterThan(list, 10) -> " + countGreaterThan(list, 10));
        System.out.println("advanced: countGreaterThan(set, 10) -> " + countGreaterThan(set, 10));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java CollectionHierarchy.java`

## 6. Walkthrough

Build a `List`, a `Set`, and a `Queue` from the same input `[3, 1, 3, 2]`. The `List` (`ArrayList`) keeps every element in insertion order, duplicates included: `[3, 1, 3, 2]`. The `Set` (`HashSet`) silently drops the second `3`, since sets forbid duplicates — the printed order is not guaranteed to match insertion order. The `Queue` (`LinkedList` used as a `Queue`) supports `poll()`, which removes and returns the head — the first element inserted, `3`, following first-in-first-out order.

For `Map`, note it is never passed anywhere a `Collection<T>` is expected — `map.keySet()` returns a `Set<String>`, `map.values()` returns a `Collection<Integer>`, and `map.entrySet()` returns a `Set<Map.Entry<String,Integer>>`. These views let you iterate a map's contents using ordinary `Collection` operations, without `Map` itself being one.

Writing `countGreaterThan(Collection<Integer> items, ...)` against the `Collection` interface, not `List` or `Set` specifically, lets the exact same method work for both a `List` and a `Set` argument — the caller's concrete choice does not affect the method's logic, only which guarantees (order, duplicates) the caller relies on.

**Complexity.** The hierarchy itself has no runtime cost — it is purely a type system tool. Actual complexity depends entirely on which concrete implementation you choose within each branch, covered on the following pages.

## 7. Gotchas & takeaways

> `Map` does not extend `Collection`. A common early-Java mistake is trying to pass a `Map` where a `Collection` is expected — the compiler correctly rejects this, and the fix is to pass one of its views (`keySet()`, `values()`, or `entrySet()`) instead.

- Always declare variables and method parameters using the **interface** type (`List<T>`, not `ArrayList<T>`) unless you specifically need a method only the concrete class provides — this keeps your code free to swap implementations later.
- `Queue` is an interface, and `LinkedList` implements both `List` and `Queue` simultaneously — this dual nature is occasionally useful but can also be a source of confusion about which contract a given `LinkedList` reference is being used under.
- The next several pages go implementation by implementation: [List](0180-list-implementations-arraylist-linkedlist-vector.md), [Set](0181-set-implementations-hashset-linkedhashset-treeset.md), [Map](0182-map-implementations-hashmap-linkedhashmap-treemap.md), and [Queue/Deque](0183-queue-deque-implementations.md).
