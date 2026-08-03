---
card: data-structures
gi: 196
slug: ordered-vs-unordered-structure-tradeoffs
title: Ordered vs unordered structure tradeoffs
---

## 1. What it is

"Ordered" structures (`TreeMap`, `TreeSet`, sorted arrays) keep elements in a defined order at all times, and pay a cost for it. "Unordered" structures (`HashMap`, `HashSet`) make no such promise, and are faster precisely because they never have to maintain one. This page compares the two families directly, so paying for ordering is a deliberate choice, not an accident.

## 2. Why & when

Every ordering guarantee costs something — extra comparisons on insert, a taller tree to search, or a sort step before you can use the data. If your workload never actually needs sorted output or range queries, that cost buys nothing. If it does need them, the cost is not optional — no unordered structure can answer "what is the smallest key greater than X?" without a full scan.

## 3. Core concept

**The decision criteria.**
- **Do you ever iterate the data and need it in sorted order?** If yes, an ordered structure saves you from sorting every time you iterate.
- **Do you ever ask "nearest," "range," "first," or "last"?** Only an ordered structure answers these in less than `O(n)`.
- **Is raw lookup/insert/delete speed the only thing that matters?** If ordering is never used, an unordered structure is strictly faster for the same operations.

**The cost breakdown, concretely.** `HashMap`/`HashSet`: `O(1)` average for `get`/`put`/`contains`/`remove`, because a hash function jumps directly to (approximately) the right bucket — no comparisons against other keys needed to place a new one. `TreeMap`/`TreeSet`: `O(log n)` for the same operations, because every insert must walk down a tree, comparing against existing keys at each level, to find the correct sorted position — see [TreeMap/TreeSet](0113-treemap-treeset-red-black-backed.md).

**What ordering buys you that no unordered structure can.** Sorted iteration with zero extra work (`O(n)` to traverse, already in order). `firstKey()`/`lastKey()` in `O(log n)`. `floorKey(x)`/`ceilingKey(x)` — nearest key below/above `x` — in `O(log n)`. `headMap(x)`/`tailMap(x)`/`subMap(x, y)` — range views — in `O(log n)` to construct, backed live by the original tree, no copying.

**Why "sort it once at the end" sometimes beats an ordered structure throughout.** If you insert a large batch of data once, then only need sorted order for a single final pass (never insert again after that), it can be cheaper to use an unordered `HashMap` during the insert-heavy phase (`O(1)` per insert) and sort once at the end (`O(n log n)` total) than to pay `O(log n)` per insert throughout with a `TreeMap`. The right choice depends on whether ordering is needed continuously or only at specific checkpoints.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing HashMap's O(1) unordered operations against TreeMap's O(log n) ordered operations that add range and nearest-neighbor capability">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">HashMap: O(1) avg, no order</text>
    <rect x="20" y="30" width="200" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="50" text-anchor="middle" font-size="9">get/put/contains -- O(1)</text>
    <text x="20" y="80" font-size="9" fill="#f44336">floorKey / range query: NOT POSSIBLE without full scan</text>

    <text x="10" y="130">TreeMap: O(log n), sorted always</text>
    <rect x="20" y="140" width="200" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="120" y="160" text-anchor="middle" font-size="9">get/put/contains -- O(log n)</text>
    <text x="20" y="190" font-size="9" fill="#3fb950">floorKey / range query: O(log n), built in</text>
  </g>
</svg>

The gap is not just speed — it is capability that only an ordered structure has at all.

## 5. Runnable example

```java
// OrderedVsUnordered.java
import java.util.*;

public class OrderedVsUnordered {

    // Basic: HashMap can't answer "nearest key" at all -- you'd have to scan every entry.
    static Integer nearestKeyViaScan(Map<Integer, String> map, int target) {
        Integer best = null;
        for (int key : map.keySet()) {
            if (key <= target && (best == null || key > best)) best = key;
        }
        return best;
    }

    static void basicLevel() {
        Map<Integer, String> hashMap = new HashMap<>();
        hashMap.put(10, "a"); hashMap.put(25, "b"); hashMap.put(40, "c");

        // No built-in method for this -- must scan all entries, O(n).
        System.out.println("basic: nearest key <= 30 via HashMap scan -> " + nearestKeyViaScan(hashMap, 30));
    }

    // Intermediate: TreeMap answers the same question in O(log n), built in.
    static void intermediateLevel() {
        TreeMap<Integer, String> treeMap = new TreeMap<>();
        treeMap.put(10, "a"); treeMap.put(25, "b"); treeMap.put(40, "c");

        System.out.println("intermediate: nearest key <= 30 via TreeMap.floorKey -> " + treeMap.floorKey(30));
    }

    // Advanced: measure the real cost difference for pure insert/lookup, when ordering is never actually used.
    static void advancedLevel() {
        int n = 200_000;

        long startHash = System.nanoTime();
        Map<Integer, Integer> hashMap = new HashMap<>();
        for (int i = 0; i < n; i++) hashMap.put(i, i);
        long hashTime = System.nanoTime() - startHash;

        long startTree = System.nanoTime();
        Map<Integer, Integer> treeMap = new TreeMap<>();
        for (int i = 0; i < n; i++) treeMap.put(i, i);
        long treeTime = System.nanoTime() - startTree;

        System.out.printf("advanced: HashMap %d inserts -> %.1f ms%n", n, hashTime / 1_000_000.0);
        System.out.printf("advanced: TreeMap %d inserts -> %.1f ms%n", n, treeTime / 1_000_000.0);
        System.out.println("advanced: if ordering is never queried, this TreeMap cost was pure waste");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java OrderedVsUnordered.java`

## 6. Walkthrough

`nearestKeyViaScan` on a `HashMap` with keys `{10, 25, 40}` must check every single entry to find the largest key `<= 30` — there is no shortcut, because a `HashMap`'s bucket layout has no relationship to numeric key order. For 3 entries this is trivial, but for a million entries, this becomes a full `O(n)` scan every single time the question is asked.

`treeMap.floorKey(30)` on the same logical data answers the identical question directly: the red-black tree backing `TreeMap` walks from the root, comparing against `30` at each step, converging on `25` (the largest key `<= 30`) in `O(log n)` — for a million entries, roughly 20 comparisons instead of a million.

The `advancedLevel` benchmark inserts `200,000` sequential integers into both a `HashMap` and a `TreeMap`, with no ordering ever queried afterward. `HashMap`'s inserts should measurably outpace `TreeMap`'s, since every `TreeMap.put` does `O(log n)` comparison work that `HashMap.put` skips entirely — work that, in this scenario, buys nothing, since the program never asks for sorted order, a range, or a nearest key.

**Complexity.** `HashMap`/`HashSet`: `O(1)` average per operation, no ordering support. `TreeMap`/`TreeSet`: `O(log n)` per operation, full ordering support (`firstKey`, `lastKey`, `floorKey`, `ceilingKey`, `headMap`, `tailMap`, `subMap`, all `O(log n)`).

## 7. Gotchas & takeaways

> Choosing `TreeMap` "just in case ordering is useful later" pays the `O(log n)` cost on every single operation from day one, whether or not that ordering is ever actually used — prefer `HashMap` until a concrete, present need for sorted access or range queries appears.

- If ordering is only needed occasionally (a report generated once a day, say), consider a `HashMap` for the hot path plus a one-time sort (`O(n log n)`) when the ordered view is actually needed — often cheaper overall than paying `O(log n)` per operation continuously.
- `LinkedHashSet`/`LinkedHashMap` occupy a middle ground: `O(1)` average operations like a hash-based structure, plus **insertion-order** iteration (not sorted order) — a real option when you want predictable iteration without paying the `TreeMap` comparison cost.
- The next page, [array vs linked structure memory tradeoffs](0197-array-vs-linked-structure-memory-tradeoffs.md), covers a separate axis of comparison — memory layout — that applies independently of the ordered/unordered choice discussed here.
