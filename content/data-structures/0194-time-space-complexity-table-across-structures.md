---
card: data-structures
gi: 194
slug: time-space-complexity-table-across-structures
title: Time/space complexity table across structures
---

## 1. What it is

This page is a single reference table listing the time complexity of the core operations (access, search, insert, delete) for every major data structure covered on this card, side by side. It exists so you can compare structures at a glance instead of hunting through dozens of individual pages.

## 2. Why & when

Interviews and system design discussions often move fast between structures — "why not just use an array here?", "what if we needed faster deletes?" — and having the comparative numbers memorized (or quickly re-derivable) is what lets you answer without hesitation. This table is the page to return to whenever you need the numbers fast, with links back to the detailed page for any structure whose reasoning you want to re-derive.

## 3. Core concept

**The decision criteria.** For any given structure, four numbers matter most: access by index/key, search for a value, insert, and delete — each in the average and worst case where they differ meaningfully.

**The full comparison table.**

| Structure | Access | Search | Insert | Delete | Space |
|---|---|---|---|---|---|
| [Array (static)](0015-static-fixed-size-arrays.md) | O(1) | O(n) | O(n) | O(n) | O(n) |
| [Dynamic array / ArrayList](0020-array-resizing-amortized-append.md) | O(1) | O(n) | O(1) amortized (end), O(n) (middle) | O(n) | O(n) |
| [Linked list (singly/doubly)](0046-doubly-linked-list.md) | O(n) | O(n) | O(1) (at known node) | O(1) (at known node) | O(n) |
| [Stack](0064-push-pop-peek-o-1.md) | O(n) | O(n) | O(1) (top) | O(1) (top) | O(n) |
| [Queue](0077-enqueue-dequeue-peek.md) | O(n) | O(n) | O(1) (tail) | O(1) (head) | O(n) |
| [HashMap / HashSet](0093-hashcode-equals-for-correct-keys.md) | -- | O(1) avg, O(n) worst | O(1) avg | O(1) avg | O(n) |
| [TreeMap / TreeSet](0113-treemap-treeset-red-black-backed.md) | -- | O(log n) | O(log n) | O(log n) | O(n) |
| [Binary heap](0116-heap-property-array-representation.md) | O(1) (min/max only) | O(n) | O(log n) | O(log n) (root) | O(n) |
| [Trie](0126-prefix-tree-trie-structure.md) | -- | O(key length) | O(key length) | O(key length) | O(alphabet size * n) |
| [Binary search tree (unbalanced)](0098-binary-tree-binary-search-tree-bst.md) | O(n) worst | O(n) worst | O(n) worst | O(n) worst | O(n) |
| [Balanced BST (AVL/red-black)](0110-avl-trees-rotations.md) | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| [Segment tree](0152-segment-tree-range-query-update.md) | -- | O(log n) (range) | O(log n) (point) | O(log n) | O(n) |
| [Fenwick tree](0153-fenwick-tree-binary-indexed-tree-bit.md) | -- | O(log n) (range sum) | O(log n) (point) | O(log n) | O(n) |
| [Disjoint set (optimized)](0166-near-constant-amortized-complexity-inverse-ackermann.md) | -- | O(alpha(n)) | O(alpha(n)) | -- | O(n) |
| [Skip list](0170-skip-list.md) | O(log n) expected | O(log n) expected | O(log n) expected | O(log n) expected | O(n) |

**Why "amortized" and "average" appear so often, and why that matters.** Several entries (`ArrayList` end-insert, `HashMap` operations) are not worst-case guarantees. `ArrayList` end-insert is `O(1)` amortized because of periodic doubling (see [amortized analysis](0004-amortized-analysis-dynamic-array-doubling.md)); any single call could be `O(n)` during a resize. `HashMap` operations are `O(1)` average because a pathological input (all keys colliding into one bucket) can degrade to `O(n)` (or `O(log n)` since Java 8's bucket treeification) in the worst case. Knowing which guarantee you actually have matters when correctness or latency bounds are on the line.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A visual spectrum from O(1) to O(n) showing where each structure's typical search operation falls">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <line x1="40" y1="100" x2="600" y2="100" stroke="#8b949e"/>
    <text x="40" y="120" font-size="9">O(1)</text>
    <text x="300" y="120" font-size="9">O(log n)</text>
    <text x="580" y="120" font-size="9">O(n)</text>

    <circle cx="60" cy="100" r="5" fill="#3fb950"/><text x="60" y="85" text-anchor="middle" font-size="8">HashMap</text>
    <circle cx="300" cy="100" r="5" fill="#79c0ff"/><text x="300" y="85" text-anchor="middle" font-size="8">TreeMap, balanced BST</text>
    <circle cx="300" cy="100" r="5" fill="#79c0ff"/>
    <circle cx="500" cy="100" r="5" fill="#f0883e"/><text x="500" y="85" text-anchor="middle" font-size="8">unbalanced BST (worst case)</text>
    <circle cx="580" cy="100" r="5" fill="#f44336"/><text x="580" y="85" text-anchor="middle" font-size="8">array, linked list</text>
  </g>
</svg>

Hash-based structures cluster at O(1); tree-based structures cluster at O(log n); linear structures sit at O(n).

## 5. Runnable example

```java
// ComplexityComparison.java
import java.util.*;

public class ComplexityComparison {

    // Basic: measure real search time across structures for the same lookup task, at a fixed size.
    static void basicLevel() {
        int n = 50_000;
        List<Integer> arrayList = new ArrayList<>();
        Set<Integer> hashSet = new HashSet<>();
        TreeSet<Integer> treeSet = new TreeSet<>();
        for (int i = 0; i < n; i++) { arrayList.add(i); hashSet.add(i); treeSet.add(i); }

        int target = n - 1; // worst case for a linear scan: the last element

        long t1 = System.nanoTime();
        arrayList.contains(target);
        long arrayTime = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        hashSet.contains(target);
        long hashTime = System.nanoTime() - t2;

        long t3 = System.nanoTime();
        treeSet.contains(target);
        long treeTime = System.nanoTime() - t3;

        System.out.printf("basic: ArrayList.contains -> %d ns%n", arrayTime);
        System.out.printf("basic: HashSet.contains -> %d ns%n", hashTime);
        System.out.printf("basic: TreeSet.contains -> %d ns%n", treeTime);
    }

    // Intermediate: show the gap widening as n scales up, confirming the Big-O predictions.
    static void intermediateLevel() {
        for (int n : new int[]{10_000, 100_000, 1_000_000}) {
            List<Integer> arrayList = new ArrayList<>();
            Set<Integer> hashSet = new HashSet<>();
            for (int i = 0; i < n; i++) { arrayList.add(i); hashSet.add(i); }

            long t1 = System.nanoTime();
            arrayList.contains(n - 1);
            long arrayTime = System.nanoTime() - t1;

            long t2 = System.nanoTime();
            hashSet.contains(n - 1);
            long hashTime = System.nanoTime() - t2;

            System.out.printf("intermediate: n=%d, ArrayList=%d ns, HashSet=%d ns, ratio=%.1fx%n",
                n, arrayTime, hashTime, (double) arrayTime / Math.max(hashTime, 1));
        }
    }

    // Advanced: choosing the right structure for a task based on the operations it actually needs.
    static void advancedLevel() {
        // Task: track unique visitor IDs, and frequently check "have we seen this ID?"
        Set<String> visitorIds = new HashSet<>(); // O(1) contains -- the right choice for pure membership checks

        // Task: maintain a leaderboard needing sorted iteration and range queries.
        TreeMap<Integer, String> leaderboard = new TreeMap<>(); // O(log n), but gives floorKey/ceilingKey for free

        visitorIds.add("visitor-1");
        leaderboard.put(9500, "player-1");

        System.out.println("advanced: HashSet chosen for membership -> contains -> " + visitorIds.contains("visitor-1"));
        System.out.println("advanced: TreeMap chosen for ranking -> floorKey(9000) -> " + leaderboard.floorKey(9000));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ComplexityComparison.java`

## 6. Walkthrough

Run `basicLevel` with `n = 50,000` elements in each structure, searching for the last-inserted value. `ArrayList.contains` must scan up to all `50,000` elements in the worst case (linear search, since a `List` has no ordering shortcut), giving the largest measured time. `HashSet.contains` computes one hash and checks one (or a few, on collision) bucket, giving the smallest measured time. `TreeSet.contains` walks a red-black tree of height `~log2(50000) ≈ 16`, landing between the two.

`intermediateLevel` repeats this at three different sizes (`10,000`, `100,000`, `1,000,000`) and prints the ratio between `ArrayList` and `HashSet` search time. As `n` grows, this ratio should grow too — `ArrayList`'s `O(n)` search cost scales linearly with size, while `HashSet`'s `O(1)` average cost stays roughly flat, so the gap between them widens exactly as the complexity table predicts.

`advancedLevel` shows the table used the way it is meant to be used: matching the operations a task actually needs to the structure that provides them cheaply. Pure membership checking needs only `O(1)` `contains` — `HashSet` is the right choice, and its lack of ordering is irrelevant to the task. A leaderboard needing "who ranks just below this score" needs `TreeMap`'s `floorKey`, an operation `HashMap` cannot provide at any complexity — here, `O(log n)` is worth paying for the capability, not a weakness to avoid.

**Complexity.** This page is a reference, not an algorithm — its "complexity" is simply the aggregate of every structure's own complexity, summarized above. Always re-derive or verify a specific number against the structure's own dedicated page ([segment tree](0152-segment-tree-range-query-update.md), [Fenwick tree](0153-fenwick-tree-binary-indexed-tree-bit.md), etc.) when precision matters, since this table intentionally compresses nuance (average vs. worst case, amortized vs. per-call) into single cells.

## 7. Gotchas & takeaways

> A table cell showing `O(1)` or `O(log n)` can hide an "average case" or "amortized" qualifier that matters enormously for latency-sensitive code — a single `ArrayList.add` call that happens to trigger a resize is `O(n)`, not `O(1)`, even though the amortized cost across many calls is `O(1)`.

- Use this table to narrow down candidates quickly, then verify the specific guarantee (worst-case vs average vs amortized) on the structure's dedicated page before committing to a design decision that depends on it.
- The next few pages turn this raw table into decision guidance: [choosing a structure by access pattern](0195-choosing-a-structure-by-access-pattern.md), [ordered vs unordered tradeoffs](0196-ordered-vs-unordered-structure-tradeoffs.md), and more.
- When two structures have the same Big-O for the operation you care about, the tie-break is usually constant factors and memory overhead — covered in [array vs linked structure memory tradeoffs](0197-array-vs-linked-structure-memory-tradeoffs.md).
