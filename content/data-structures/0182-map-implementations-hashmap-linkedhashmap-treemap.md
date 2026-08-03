---
card: data-structures
gi: 182
slug: map-implementations-hashmap-linkedhashmap-treemap
title: Map implementations (HashMap, LinkedHashMap, TreeMap)
---

## 1. What it is

`HashMap`, `LinkedHashMap`, and `TreeMap` are the three main `Map` implementations in `java.util`. All three store key-value pairs with unique keys, but they differ in iteration order and lookup mechanism, mirroring the same three-way split seen in [Set implementations](0181-set-implementations-hashset-linkedhashset-treeset.md) — because `HashSet`, `LinkedHashSet`, and `TreeSet` are literally built on top of these three map types internally.

## 2. Why & when

`HashMap` is the default choice for nearly everything: fastest average lookup, no ordering needed. `LinkedHashMap` is the right choice when you want fast lookup **and** predictable iteration order (insertion order by default, or access order for building an [LRU cache](0175-linkedhashmap-access-order-for-lru.md)). `TreeMap` is the right choice when you need keys sorted at all times, or range operations like "find the entry with the largest key less than X."

## 3. Core concept

**What backs each one.** `HashMap`: an array of buckets, each holding entries that hash to the same index, using chaining (a linked list, or a red-black tree for buckets with many collisions, since Java 8) to resolve collisions. `LinkedHashMap`: extends `HashMap`, adding a doubly linked list threading through every entry in insertion (or access) order. `TreeMap`: a red-black tree keyed by the map's keys, giving `O(log n)` operations and always-sorted iteration.

**Ordering and complexity guarantees.** `HashMap`: no ordering guarantee; `get`/`put`/`remove` `O(1)` average. `LinkedHashMap`: insertion order (or access order, if configured) preserved; same `O(1)` average operations. `TreeMap`: keys always sorted; `get`/`put`/`remove` `O(log n)`; additional navigation methods (`firstKey`, `floorKey`, `ceilingEntry`) also `O(log n)`.

**Why null keys/values differ across implementations.** `HashMap` allows one `null` key and any number of `null` values. `LinkedHashMap` inherits the same rule. `TreeMap` does **not** allow a `null` key (unless a custom `Comparator` explicitly handles nulls), because comparing `null` against other keys to determine sorted position has no natural meaning.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HashMap using buckets with no order, LinkedHashMap threading a linked list through entries for order, and TreeMap using a red-black tree for sorted keys">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">HashMap: buckets, order depends on hash</text>
    <rect x="20" y="30" width="50" height="24" fill="#0d1117" stroke="#8b949e"/><text x="45" y="46" text-anchor="middle" font-size="9">bucket0</text>
    <rect x="80" y="30" width="50" height="24" fill="#0d1117" stroke="#8b949e"/><text x="105" y="46" text-anchor="middle" font-size="9">bucket1</text>
    <rect x="140" y="30" width="50" height="24" fill="#0d1117" stroke="#8b949e"/><text x="165" y="46" text-anchor="middle" font-size="9">bucket2</text>

    <text x="10" y="90">LinkedHashMap: buckets + insertion-order chain</text>
    <rect x="20" y="100" width="50" height="24" fill="#161b22" stroke="#79c0ff"/><text x="45" y="116" text-anchor="middle" font-size="9">B</text>
    <rect x="80" y="100" width="50" height="24" fill="#161b22" stroke="#79c0ff"/><text x="105" y="116" text-anchor="middle" font-size="9">A</text>
    <rect x="140" y="100" width="50" height="24" fill="#161b22" stroke="#79c0ff"/><text x="165" y="116" text-anchor="middle" font-size="9">C</text>
    <line x1="70" y1="112" x2="80" y2="112" stroke="#79c0ff"/>
    <line x1="130" y1="112" x2="140" y2="112" stroke="#79c0ff"/>

    <text x="10" y="150">TreeMap: red-black tree, always sorted</text>
    <circle cx="90" cy="175" r="14" fill="#161b22" stroke="#3fb950"/><text x="90" y="179" text-anchor="middle" font-size="9">M</text>
    <circle cx="50" cy="195" r="12" fill="#0d1117" stroke="#8b949e"/><text x="50" y="199" text-anchor="middle" font-size="8">A</text>
    <circle cx="130" cy="195" r="12" fill="#0d1117" stroke="#8b949e"/><text x="130" y="199" text-anchor="middle" font-size="8">Z</text>
  </g>
</svg>

Same three key-value pairs, three different internal structures and iteration guarantees.

## 5. Runnable example

```java
// MapImplementations.java
import java.util.*;

public class MapImplementations {

    // Basic: the same insertions into all three Map types, showing different iteration orders.
    static void basicLevel() {
        Map<String, Integer> hashMap = new HashMap<>();
        Map<String, Integer> linkedHashMap = new LinkedHashMap<>();
        Map<String, Integer> treeMap = new TreeMap<>();

        String[] keys = {"banana", "apple", "cherry"};
        for (int i = 0; i < keys.length; i++) {
            hashMap.put(keys[i], i);
            linkedHashMap.put(keys[i], i);
            treeMap.put(keys[i], i);
        }

        System.out.println("basic: HashMap keys -> " + hashMap.keySet());
        System.out.println("basic: LinkedHashMap keys (insertion order) -> " + linkedHashMap.keySet());
        System.out.println("basic: TreeMap keys (sorted) -> " + treeMap.keySet());
    }

    // Intermediate: word frequency counting, a common HashMap use case with getOrDefault / merge.
    static Map<String, Integer> wordFrequency(String text) {
        Map<String, Integer> freq = new HashMap<>();
        for (String word : text.toLowerCase().split("\\s+")) {
            freq.merge(word, 1, Integer::sum);
        }
        return freq;
    }

    static void intermediateLevel() {
        Map<String, Integer> freq = wordFrequency("the quick brown fox the lazy fox");
        System.out.println("intermediate: word frequencies -> " + freq);
    }

    // Advanced: TreeMap's navigation methods, useful for range-based lookups (e.g. a leaderboard tier system).
    static void advancedLevel() {
        TreeMap<Integer, String> tiers = new TreeMap<>();
        tiers.put(0, "Bronze");
        tiers.put(1000, "Silver");
        tiers.put(2000, "Gold");
        tiers.put(3000, "Platinum");

        int[] playerScores = {1500, 250, 3200, 999};
        for (int score : playerScores) {
            String tier = tiers.floorEntry(score).getValue(); // largest threshold <= score
            System.out.println("advanced: score " + score + " -> tier " + tier);
        }
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java MapImplementations.java`

## 6. Walkthrough

Insert `"banana", "apple", "cherry"` (with values `0, 1, 2`) into all three maps. `HashMap`'s `keySet()` prints in an order determined by each key's hash bucket — not insertion order, and not alphabetical. `LinkedHashMap`'s `keySet()` prints `[banana, apple, cherry]`, exactly matching insertion order, because of its internal linked list. `TreeMap`'s `keySet()` prints `[apple, banana, cherry]`, alphabetically sorted, because every key lives in a red-black tree ordered by natural `String` comparison.

For word frequency counting: `freq.merge(word, 1, Integer::sum)` is the idiomatic `HashMap` pattern for "increment a counter, starting from zero." For each word, if it is not yet a key, `merge` inserts it with value `1`. If it already exists, `merge` calls `Integer::sum` on the existing value and `1`, updating the count. Running this on `"the quick brown fox the lazy fox"` produces `{the=2, fox=2, quick=1, brown=1, lazy=1}` (in whatever order `HashMap` happens to iterate).

For the tier lookup: `tiers.floorEntry(1500)` finds the entry with the largest key `<= 1500`, which is `1000 -> "Silver"` — correctly placing a score of `1500` in the Silver tier. `tiers.floorEntry(250)` finds `0 -> "Bronze"`. This kind of "which bucket does this value fall into?" query is exactly what `TreeMap` is for, and has no equivalent on `HashMap` or `LinkedHashMap`.

**Complexity.** `HashMap`: `get`/`put`/`remove` `O(1)` average. `LinkedHashMap`: same, plus small constant overhead for the linked list. `TreeMap`: `get`/`put`/`remove` `O(log n)`; navigation methods (`floorEntry`, `ceilingEntry`, `firstKey`) also `O(log n)`.

## 7. Gotchas & takeaways

> `HashMap`'s worst-case lookup degrades from `O(1)` to `O(log n)` (not `O(n)`) since Java 8, when a single bucket accumulates enough colliding entries (8 or more) that Java converts that bucket's linked list into a small red-black tree internally — this is an implementation detail, not something you need to manage, but it explains why `HashMap` has better worst-case behavior than older textbooks describe.

- Never use a mutable object as a `HashMap` key if its `hashCode()` can change after insertion — the entry becomes unreachable, silently "lost" in the wrong bucket. See [equals/hashCode contract](0014-equals-hashcode-contract.md).
- Choose `LinkedHashMap` over `HashMap` specifically when iteration order matters to your logic or output — for example, printing results in the order they were computed, or building an LRU cache with access-order mode.
- Choose `TreeMap` specifically when you need sorted keys or range/navigation queries — for everything else, `HashMap` (or `LinkedHashMap` if order matters) is faster.
