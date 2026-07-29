---
card: leetcode-patterns
gi: 590
slug: design-a-number-container-system
title: Design a Number Container System
---

## 1. What it is

Design a `NumberContainers` class mapping indices to numbers, where **multiple indices can hold the same number**. `change(index, number)` sets (or overwrites) the number at `index`. `find(number)` returns the **smallest index** currently holding `number`, or `-1` if no index currently holds it. Example: `change(2,10)`, `change(1,10)`, `find(10)` → `1` (the smallest index holding `10`); `change(1,20)`, `find(10)` → `2` (index `1` no longer holds `10`).

## 2. Why & when

`find(number)` needs "the smallest index currently holding this number," which changes as indices are reassigned — some previously-smallest index might later be overwritten with a different number, so the answer must always reflect *current* state, not just "smallest index that was ever assigned this number." A `TreeSet` per number, keeping its assigned indices sorted, answers "smallest current index" in O(log n) via `first()`, and a second map tracks each index's current number so `change` can correctly remove it from its *old* number's set before adding it to the new one.

## 3. Core concept

**Key idea:** maintain two maps. `indexToNumber: HashMap<index, number>` records what number each index currently holds (needed to know what to remove when an index is reassigned). `numberToIndices: HashMap<number, TreeSet<index>>` records, for each number, the sorted set of indices currently holding it — a `TreeSet` keeps insertion, removal, and "smallest element" all at O(log n).

**Steps:**
1. `change(index, number)`: if `index` already holds some `oldNumber` (look it up in `indexToNumber`), remove `index` from `numberToIndices[oldNumber]` (and, if that set becomes empty, you may leave it empty or remove the map entry — either is correct, since `find` on an empty/missing set both mean "not found"). Add `index` to `numberToIndices[number]`. Update `indexToNumber[index] = number`.
2. `find(number)`: look up `numberToIndices.get(number)`; if it exists and is non-empty, return its `first()` (the smallest index); otherwise return `-1`.

**Why the `TreeSet` per number, not a single global structure:** each number's set of holding-indices is entirely independent of every other number's — `find(10)` should never be slowed down by how many indices hold `20`. Splitting by number into separate `TreeSet`s keeps each one small and each `find` call fast, scoped only to the relevant number.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two maps: index to its current number, and number to a sorted TreeSet of indices holding it">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">indexToNumber</text>
    <rect x="30" y="30" width="240" height="30" fill="#161b22" stroke="#3fb950"/><text x="150" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">1 -&gt; 10, 2 -&gt; 10, 5 -&gt; 20</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">numberToIndices</text>
    <rect x="410" y="30" width="240" height="30" fill="#161b22" stroke="#f0883e"/><text x="530" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">10 -&gt; TreeSet{1,2}</text>
    <rect x="410" y="65" width="240" height="30" fill="#161b22" stroke="#f0883e"/><text x="530" y="85" fill="#e6edf3" text-anchor="middle" font-size="11">20 -&gt; TreeSet{5}</text>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">find(10) = numberToIndices[10].first() = 1, O(log n)</text>
  </g>
</svg>

`indexToNumber` tells `change` what to remove; `numberToIndices`'s per-number `TreeSet` tells `find` the smallest current index directly, with no scanning.

## 5. Runnable example

**Level 1 — Brute force.** Store all `(index, number)` pairs in a `HashMap<index, number>` only; on each `find(number)`, scan every entry, filtering for a matching number and tracking the minimum index. O(total indices ever set) per `find` call.

**KEY INSIGHT:** pre-group indices by the number they hold, in a sorted structure, so "smallest index holding this number" is a direct O(log n) lookup (`TreeSet.first()`) instead of a full scan — the cost of maintaining that grouping is paid incrementally on each `change`, not all at once on each `find`.

**Level 2 — Optimal.** `HashMap<Integer, Integer>` (index to number) plus `HashMap<Integer, TreeSet<Integer>>` (number to sorted indices), O(log n) per call.

**Level 3 — Hardened.** Correctly removes an index from its *old* number's set before adding it to the new number's set on `change` (so a reassigned index does not "leak" into two numbers' sets at once), and correctly returns `-1` when a number's set is empty or absent.

```java
// NumberContainers.java
import java.util.*;

public class NumberContainers {

    private final Map<Integer, Integer> indexToNumber = new HashMap<>();
    private final Map<Integer, TreeSet<Integer>> numberToIndices = new HashMap<>();

    public void change(int index, int number) {
        if (indexToNumber.containsKey(index)) {
            int oldNumber = indexToNumber.get(index);
            TreeSet<Integer> oldSet = numberToIndices.get(oldNumber);
            oldSet.remove(index);
        }
        indexToNumber.put(index, number);
        numberToIndices.computeIfAbsent(number, k -> new TreeSet<>()).add(index);
    }

    public int find(int number) {
        TreeSet<Integer> set = numberToIndices.get(number);
        if (set == null || set.isEmpty()) return -1;
        return set.first();
    }

    public static void main(String[] args) {
        NumberContainers nc = new NumberContainers();
        System.out.println(nc.find(10)); // -1, none yet
        nc.change(2, 10);
        nc.change(1, 10);
        System.out.println(nc.find(10)); // 1, smallest index holding 10
        nc.change(1, 20);
        System.out.println(nc.find(10)); // 2, index 1 no longer holds 10
        System.out.println(nc.find(20)); // 1
    }
}
```

**How to run:** save as `NumberContainers.java`, then run `java NumberContainers.java`.

## 6. Walkthrough

Trace `change(2,10)`, `change(1,10)`, `find(10)`, `change(1,20)`, `find(10)`:

| call | indexToNumber | numberToIndices | return |
|---|---|---|---|
| change(2,10) | {2:10} | {10:{2}} | — |
| change(1,10) | {2:10, 1:10} | {10:{1,2}} | — |
| find(10) | (unchanged) | (unchanged) | 1 |
| change(1,20) | old number for index 1 was 10 -> remove 1 from {10}'s set; {2:10, 1:20} | {10:{2}, 20:{1}} | — |
| find(10) | (unchanged) | (unchanged) | 2 |

`change(1,20)` correctly removes index `1` from `10`'s set before adding it to `20`'s set — without that removal, `find(10)` would have incorrectly still returned `1`.

## 7. Gotchas & takeaways

> Gotcha: skipping the removal of `index` from its old number's `TreeSet` before reassigning it (only updating `indexToNumber` and inserting into the new number's set) leaves a stale index in the old set — a later `find(oldNumber)` could return an index that no longer actually holds that number.

- Signal: "track the smallest/first key-holder for a value that can be reassigned" is the two-map (reverse-lookup-plus-sorted-set) signal.
- `TreeSet.first()` gives the smallest element in O(log n); plain `HashSet` has no ordering, so it cannot answer "smallest" without a full scan.
- Related problems: Design a Food Rating System (a very similar "reverse index into a sorted structure, updated on change" pattern, but tracking maximum rating instead of minimum index).
