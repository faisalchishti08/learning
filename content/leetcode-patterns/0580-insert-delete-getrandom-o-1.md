---
card: leetcode-patterns
gi: 580
slug: insert-delete-getrandom-o-1
title: Insert Delete GetRandom O(1)
---

## 1. What it is

Design a `RandomizedSet` class supporting `insert(val)` (add `val` if not already present, return whether it was added), `remove(val)` (remove `val` if present, return whether it was removed), and `getRandom()` (return a uniformly random element among those currently stored). All three methods must run in O(1) average time. Example: `insert(1)` → `true`, `remove(2)` → `false` (not present), `insert(2)` → `true`, `getRandom()` → `1` or `2`, each with probability `1/2`.

## 2. Why & when

The tricky requirement is `getRandom()` in O(1) with a **uniform** distribution — a `HashSet` alone gives O(1) insert/remove/contains, but has no O(1) way to pick a uniformly random element (you cannot index into a hash set's internal buckets fairly or efficiently). An array gives O(1) random access by index (`java.util.Random.nextInt(size)`), but a naive `remove` on an array is O(n) because removing a middle element requires shifting everything after it. Combining a `HashMap` (value → index) with an `ArrayList` solves both requirements at once.

## 3. Core concept

**Key idea:** store all values in an `ArrayList`, and mirror the value-to-position mapping in a `HashMap<value, index>`. Getting a random element becomes "pick a random valid array index," which is O(1). Removing becomes "swap the target with the last element, then remove the last element" — never a middle removal — which keeps removal O(1) too.

**Steps:**
1. `insert(val)`: if `map.containsKey(val)`, return `false`. Otherwise, append `val` to the array, record `map.put(val, array.size() - 1)`, return `true`.
2. `remove(val)`: if `!map.containsKey(val)`, return `false`. Otherwise, look up `val`'s index. Take the array's **last** element, move it into `val`'s old slot, update the map entry for that moved element to its new index, then remove the array's last slot and delete `val` from the map. Return `true`.
3. `getRandom()`: return `array.get(random.nextInt(array.size()))`.

**Why "swap with the last element" is the key trick:** removing from the middle of an `ArrayList` normally shifts every later element, costing O(n). Swapping the target with the last element first means the only removal ever performed is "remove the last element," which is O(1) — the array's order changes, but nothing in the problem requires preserving order.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Removing a middle element by swapping it with the last element, then popping the last slot">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#8b949e" font-size="11">before remove(val=20):</text>
    <rect x="20" y="30" width="60" height="35" fill="#161b22" stroke="#30363d"/><text x="50" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">10</text>
    <rect x="90" y="30" width="60" height="35" fill="#161b22" stroke="#f0883e"/><text x="120" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">20</text>
    <rect x="160" y="30" width="60" height="35" fill="#161b22" stroke="#30363d"/><text x="190" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">30</text>
    <rect x="230" y="30" width="60" height="35" fill="#161b22" stroke="#79c0ff"/><text x="260" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">40 (last)</text>
    <line x1="260" y1="70" x2="120" y2="70" stroke="#79c0ff" marker-end="url(#a7)"/>
    <defs><marker id="a7" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
    <text x="20" y="110" fill="#8b949e" font-size="11">after: swap 40 into 20's slot, then drop the last slot</text>
    <rect x="20" y="120" width="60" height="35" fill="#161b22" stroke="#30363d"/><text x="50" y="142" fill="#e6edf3" text-anchor="middle" font-size="11">10</text>
    <rect x="90" y="120" width="60" height="35" fill="#161b22" stroke="#3fb950"/><text x="120" y="142" fill="#e6edf3" text-anchor="middle" font-size="11">40</text>
    <rect x="160" y="120" width="60" height="35" fill="#161b22" stroke="#30363d"/><text x="190" y="142" fill="#e6edf3" text-anchor="middle" font-size="11">30</text>
  </g>
</svg>

Only the last slot is ever removed — the target's old slot is filled by the last element first, so no shifting of the elements in between is needed.

## 5. Runnable example

**Level 1 — Brute force.** Use only an `ArrayList`: `insert` scans for duplicates (O(n)), `remove` finds the index and shifts everything after it (O(n)), `getRandom` is O(1). Two of three methods fail the O(1) requirement.

**KEY INSIGHT:** pairing a `HashMap` (value → index, giving O(1) duplicate checks and O(1) index lookup) with an `ArrayList` (giving O(1) random access) — plus the swap-with-last trick for removal — makes all three methods O(1).

**Level 2 — Optimal.** `HashMap<Integer, Integer>` plus `ArrayList<Integer>`, with swap-to-last-then-pop removal.

**Level 3 — Hardened.** Correctly updates the map entry for the *moved* element during removal (not just the removed one), and correctly handles removing the last element itself (no swap needed, just pop).

```java
// RandomizedSet.java
import java.util.*;

public class RandomizedSet {

    private final Map<Integer, Integer> valueToIndex = new HashMap<>();
    private final List<Integer> values = new ArrayList<>();
    private final Random random = new Random();

    public boolean insert(int val) {
        if (valueToIndex.containsKey(val)) return false;
        valueToIndex.put(val, values.size());
        values.add(val);
        return true;
    }

    public boolean remove(int val) {
        if (!valueToIndex.containsKey(val)) return false;
        int indexToRemove = valueToIndex.get(val);
        int lastValue = values.get(values.size() - 1);

        values.set(indexToRemove, lastValue);
        valueToIndex.put(lastValue, indexToRemove);

        values.remove(values.size() - 1);
        valueToIndex.remove(val);
        return true;
    }

    public int getRandom() {
        return values.get(random.nextInt(values.size()));
    }

    public static void main(String[] args) {
        RandomizedSet set = new RandomizedSet();
        System.out.println(set.insert(1)); // true
        System.out.println(set.remove(2)); // false, not present
        System.out.println(set.insert(2)); // true
        int r = set.getRandom();
        System.out.println("random is 1 or 2: " + (r == 1 || r == 2)); // true
        System.out.println(set.remove(1)); // true
        System.out.println(set.insert(2)); // false, already present
        System.out.println(set.getRandom()); // 2 (only element left)
    }
}
```

**How to run:** save as `RandomizedSet.java`, then run `java RandomizedSet.java`.

## 6. Walkthrough

Trace `insert(10)`, `insert(20)`, `insert(30)`, `remove(20)`:

| call | values | valueToIndex |
|---|---|---|
| insert(10) | [10] | {10:0} |
| insert(20) | [10,20] | {10:0, 20:1} |
| insert(30) | [10,20,30] | {10:0, 20:1, 30:2} |
| remove(20) | indexToRemove=1, lastValue=30; set values[1]=30, map[30]=1; pop last -> [10,30] | {10:0, 30:1} |

After `remove(20)`, `30` has moved into index `1` (where `20` used to be), and the map reflects that — `getRandom()` afterward can only return `10` or `30`, each still selected uniformly among the two remaining elements.

## 7. Gotchas & takeaways

> Gotcha: after swapping the last element into the removed slot, forgetting to update `valueToIndex` for the *moved* element (only removing the target's own entry) leaves the map pointing at a stale index for that moved value — its next `remove` call would then target the wrong array slot.

- Signal: "O(1) random access to a dynamic collection" plus "O(1) insert/remove" is the HashMap-plus-ArrayList-with-swap-removal signal.
- Removing from an array in O(1) is only possible if you may reorder elements — swap-with-last is the standard trick when order does not matter.
- Related problems: Insert Delete GetRandom O(1) - Duplicates allowed (the harder variant, needing a set of indices per value instead of a single index).
