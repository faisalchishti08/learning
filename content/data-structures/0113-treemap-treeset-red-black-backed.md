---
card: data-structures
gi: 113
slug: treemap-treeset-red-black-backed
title: 'TreeMap & TreeSet (red-black backed)'
---

## 1. What it is

`java.util.TreeMap` and `java.util.TreeSet` are Java's sorted collection types. Internally, both are backed by a [red-black tree](0111-red-black-trees.md) — `TreeSet` is actually implemented as a thin wrapper around a `TreeMap`, storing each element as a key mapped to a shared dummy value.

## 2. Why & when

Choose `TreeMap` or `TreeSet` whenever you need keys or elements kept in sorted order at all times, with efficient range queries (everything below a value, everything between two values). A `HashMap` gives faster average-case operations but no ordering guarantee at all; a `TreeMap` trades a little speed (`O(log n)` instead of `O(1)`) for guaranteed order and range operations.

## 3. Core concept

**What backs it.** Every entry is a node in a red-black tree, ordered either by the keys' natural ordering (via `Comparable`) or by an explicit `Comparator` supplied at construction time. The red-black balancing rules guarantee the tree's height stays `O(log n)`, so lookup, insert, and delete are all `O(log n)` in the worst case — not just on average.

**Ordering and complexity guarantees.** Iterating a `TreeMap` or `TreeSet` always visits entries in ascending key order (an in-order traversal of the underlying tree) — this is a documented guarantee, unlike `HashMap`'s unspecified iteration order. `containsKey`, `get`, `put`, and `remove` all cost `O(log n)`.

**When to choose it.** Pick `TreeMap`/`TreeSet` over `HashMap`/`HashSet` when you need sorted iteration, or range operations like "the smallest key greater than X" — covered in [NavigableMap / NavigableSet operations](0114-navigablemap-navigableset-operations.md). Pick the hash-based versions when you only need fast lookup and do not care about order.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A TreeMap holding keys 10, 20, 30 as a red black tree, with an in order traversal yielding sorted iteration order">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">TreeMap&lt;Integer,String&gt; -- backed by a red-black tree</text>
    <circle cx="300" cy="40" r="18" fill="#161b22" stroke="#8b949e" stroke-width="2"/><text x="300" y="44" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <circle cx="220" cy="100" r="16" fill="#3d1418" stroke="#f85149" stroke-width="2"/><text x="220" y="104" fill="#e6edf3" text-anchor="middle" font-size="8">10</text>
    <circle cx="380" cy="100" r="16" fill="#3d1418" stroke="#f85149" stroke-width="2"/><text x="380" y="104" fill="#e6edf3" text-anchor="middle" font-size="8">30</text>
    <line x1="286" y1="52" x2="234" y2="88" stroke="#8b949e"/>
    <line x1="314" y1="52" x2="366" y2="88" stroke="#8b949e"/>
    <rect x="180" y="150" width="280" height="30" fill="#0d1117" stroke="#79c0ff"/>
    <text x="320" y="170" fill="#e6edf3" text-anchor="middle" font-size="10">iteration order: 10 -&gt; 20 -&gt; 30 (always sorted)</text>
  </g>
</svg>

The tree stores keys `10, 20, 30` in red-black form; iterating the `TreeMap` always walks the tree in-order, yielding sorted keys regardless of insertion order.

## 5. Runnable example

```java
// TreeMapTreeSetDemo.java
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.Comparator;

public class TreeMapTreeSetDemo {

    // Basic: common methods and the guaranteed sorted iteration order.
    static void basicLevel() {
        Map<Integer, String> scores = new TreeMap<>();
        scores.put(30, "Charlie");
        scores.put(10, "Alice");
        scores.put(20, "Bob");

        System.out.println("basic: TreeMap keys, inserted 30,10,20 -> iterates as " + scores.keySet());
        System.out.println("basic: get(20) -> " + scores.get(20));

        Set<String> names = new TreeSet<>();
        names.add("mango");
        names.add("apple");
        names.add("banana");
        System.out.println("basic: TreeSet, inserted mango,apple,banana -> iterates as " + names);
    }

    // Intermediate: a custom Comparator for reverse order, plus TreeMap's own entrySet iteration.
    static void intermediateLevel() {
        Map<Integer, String> reverseScores = new TreeMap<>(Comparator.reverseOrder());
        reverseScores.put(10, "Alice");
        reverseScores.put(30, "Charlie");
        reverseScores.put(20, "Bob");

        System.out.print("intermediate: reverse-ordered TreeMap entries -> ");
        for (Map.Entry<Integer, String> entry : reverseScores.entrySet()) {
            System.out.print(entry.getKey() + "=" + entry.getValue() + " ");
        }
        System.out.println();
    }

    // Advanced: a realistic task -- rank students by score using a TreeMap<Integer, List<String>> for ties.
    static void advancedLevel() {
        Map<Integer, java.util.List<String>> byScore = new TreeMap<>(Comparator.reverseOrder());
        record(byScore, 85, "Dan");
        record(byScore, 92, "Eve");
        record(byScore, 85, "Frank"); // ties with Dan at 85

        System.out.println("advanced: leaderboard, highest score first ->");
        for (Map.Entry<Integer, java.util.List<String>> entry : byScore.entrySet()) {
            System.out.println("  score " + entry.getKey() + ": " + entry.getValue());
        }
    }

    static void record(Map<Integer, java.util.List<String>> byScore, int score, String name) {
        byScore.computeIfAbsent(score, key -> new java.util.ArrayList<>()).add(name);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TreeMapTreeSetDemo.java`, then run `java TreeMapTreeSetDemo.java`.

## 6. Walkthrough

1. `basicLevel()` inserts keys `30, 10, 20` into a `TreeMap`, in that exact order. Iterating `keySet()` prints `[10, 20, 30]` — sorted order, ignoring insertion order entirely, because the underlying red-black tree keeps keys ordered by comparison, not by arrival. The `TreeSet` behaves the same way for strings, using natural (alphabetical) ordering.
2. `intermediateLevel()` passes `Comparator.reverseOrder()` to the `TreeMap` constructor. Every internal comparison the red-black tree performs now uses that comparator instead of natural ordering, so `entrySet()` iterates `30, 20, 10` — descending, without changing any other code.
3. `advancedLevel()` builds a leaderboard keyed by score, descending, where each score maps to a list of names (to handle ties). `record` uses `computeIfAbsent` to create the list on first use, then appends the name. Iterating the map naturally yields the leaderboard from highest to lowest score, with `85` correctly grouping both `Dan` and `Frank`.

## 7. Gotchas & takeaways

> Gotcha: a `TreeMap`/`TreeSet` throws a `ClassCastException` at runtime if you insert keys with no natural ordering and no `Comparator` supplied — unlike a `HashMap`, which only needs `hashCode()`/`equals()`. Always supply a `Comparator` for types that are not `Comparable`.

- `TreeMap` and `TreeSet` are backed by a red-black tree, guaranteeing `O(log n)` for `get`, `put`, `remove`, and `contains` — always, not just on average.
- Iteration always follows sorted order (ascending by default, or by the supplied `Comparator`) — a documented guarantee, unlike `HashMap`'s unspecified order.
- `TreeSet` is implemented internally as a `TreeMap` whose values are all a shared dummy object.
- Related concepts: [Red-black trees](0111-red-black-trees.md), [NavigableMap / NavigableSet operations](0114-navigablemap-navigableset-operations.md), [HashSet & LinkedHashMap ordering](0092-hashset-linkedhashmap-ordering.md).
