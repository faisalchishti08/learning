---
card: data-structures
gi: 114
slug: navigablemap-navigableset-operations
title: NavigableMap / NavigableSet operations
---

## 1. What it is

`NavigableMap` and `NavigableSet` are interfaces that `TreeMap` and `TreeSet` implement, adding **range and neighbor queries** on top of plain sorted iteration: finding the closest key above or below a given value, or extracting a sub-range of the collection as a live view.

## 2. Why & when

A plain `Map` only supports exact-key lookup. `NavigableMap` answers questions a sorted structure is uniquely suited for — "what is the smallest key at least X?", "give me every entry between X and Y" — in `O(log n)`, without scanning the whole collection. Use these methods whenever you need range-based logic: finding the next available timeslot, the closest price tier, or all events within a date window.

## 3. Core concept

**What backs it.** Since `TreeMap` and `TreeSet` are backed by a [red-black tree](0111-red-black-trees.md), any "closest key" query is really a bounded walk down from the root, comparing against the target — the same `O(log n)` path a normal search takes, just stopping at the nearest match instead of an exact one.

**The neighbor methods.** `NavigableMap` provides four core lookups, each with a `NavigableSet` equivalent:

- `floorKey(k)` — the largest key `<= k` (or `null` if none exists).
- `ceilingKey(k)` — the smallest key `>= k`.
- `lowerKey(k)` — the largest key strictly `< k`.
- `higherKey(k)` — the smallest key strictly `> k`.

**Range views.** `headMap(k)`, `tailMap(k)`, and `subMap(from, to)` return a **live view** — a window onto the same underlying tree, not a copy. Changes to the original map appear in the view, and (for most operations) changes to the view write back to the original map.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sorted set of keys 10, 20, 30, 40 with floorKey and ceilingKey of 25 highlighted as the nearest neighbors on each side">
  <g font-family="sans-serif" font-size="11">
    <line x1="60" y1="70" x2="580" y2="70" stroke="#8b949e"/>
    <circle cx="140" cy="70" r="6" fill="#161b22" stroke="#8b949e"/><text x="140" y="55" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <circle cx="260" cy="70" r="6" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="260" y="55" fill="#79c0ff" text-anchor="middle" font-size="9">20</text>
    <circle cx="380" cy="70" r="6" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="380" y="55" fill="#f0883e" text-anchor="middle" font-size="9">30</text>
    <circle cx="500" cy="70" r="6" fill="#161b22" stroke="#8b949e"/><text x="500" y="55" fill="#e6edf3" text-anchor="middle" font-size="9">40</text>
    <line x1="320" y1="30" x2="320" y2="110" stroke="#e6edf3" stroke-dasharray="3,3"/>
    <text x="320" y="20" fill="#e6edf3" text-anchor="middle" font-size="9">target = 25</text>
    <text x="260" y="100" fill="#79c0ff" text-anchor="middle" font-size="9">floorKey(25) = 20</text>
    <text x="380" y="100" fill="#f0883e" text-anchor="middle" font-size="9">ceilingKey(25) = 30</text>
    <text x="320" y="145" fill="#8b949e" text-anchor="middle" font-size="9">headMap(30) = {10,20}   tailMap(30) = {30,40}</text>
  </g>
</svg>

For target `25` (not present in the set), `floorKey` finds the nearest key at or below it (`20`); `ceilingKey` finds the nearest at or above it (`30`) — both in `O(log n)`.

## 5. Runnable example

```java
// NavigableMapDemo.java
import java.util.NavigableMap;
import java.util.NavigableSet;
import java.util.TreeMap;
import java.util.TreeSet;

public class NavigableMapDemo {

    // Basic: the four neighbor-lookup methods on a NavigableMap.
    static void basicLevel() {
        NavigableMap<Integer, String> priceTiers = new TreeMap<>();
        priceTiers.put(10, "bronze");
        priceTiers.put(20, "silver");
        priceTiers.put(30, "gold");
        priceTiers.put(40, "platinum");

        System.out.println("basic: floorKey(25)   -> " + priceTiers.floorKey(25));   // largest key <= 25
        System.out.println("basic: ceilingKey(25) -> " + priceTiers.ceilingKey(25)); // smallest key >= 25
        System.out.println("basic: lowerKey(20)   -> " + priceTiers.lowerKey(20));   // largest key < 20
        System.out.println("basic: higherKey(20)  -> " + priceTiers.higherKey(20));  // smallest key > 20
    }

    // Intermediate: range views (headMap/tailMap/subMap) are LIVE windows onto the same map.
    static void intermediateLevel() {
        NavigableMap<Integer, String> priceTiers = new TreeMap<>();
        priceTiers.put(10, "bronze");
        priceTiers.put(20, "silver");
        priceTiers.put(30, "gold");
        priceTiers.put(40, "platinum");

        NavigableMap<Integer, String> upToGold = priceTiers.headMap(30, true); // inclusive of 30
        System.out.println("intermediate: headMap(30, inclusive) -> " + upToGold);

        priceTiers.put(25, "silver-plus"); // mutate the ORIGINAL map after taking the view
        System.out.println("intermediate: after adding 25 to original, view now -> " + upToGold);
    }

    // Advanced: a realistic task -- find the next available timeslot at or after a requested time, using a NavigableSet.
    static void advancedLevel() {
        NavigableSet<Integer> bookedSlots = new TreeSet<>(); // times as minutes-since-midnight
        bookedSlots.add(540);  // 9:00
        bookedSlots.add(600);  // 10:00
        bookedSlots.add(660);  // 11:00

        int requested = 615; // 10:15
        Integer nextFree = findNextFreeSlot(bookedSlots, requested, 60);
        System.out.println("advanced: requested 10:15, next free 60-min slot starts at minute -> " + nextFree);
    }

    static Integer findNextFreeSlot(NavigableSet<Integer> booked, int requestedMinute, int slotLength) {
        int candidate = requestedMinute;
        while (booked.contains(candidate)) {
            Integer next = booked.higher(candidate); // smallest booked time strictly after candidate
            candidate = (next == null) ? candidate + slotLength : next;
        }
        return candidate;
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `NavigableMapDemo.java`, then run `java NavigableMapDemo.java`.

## 6. Walkthrough

1. `basicLevel()` builds a map of keys `10, 20, 30, 40`. `floorKey(25)` walks the tree comparing against `25`, and returns `20` — the largest key not exceeding it. `ceilingKey(25)` returns `30` the same way, from the other side. `lowerKey(20)` and `higherKey(20)` behave the same, but exclude `20` itself even though it is present, since both are strict (`<` / `>`), unlike `floor`/`ceiling`.
2. `intermediateLevel()` takes `headMap(30, true)`, a live view containing every key up to and including `30`. After the view is created, `25` is added directly to the original `priceTiers` map. Printing the view again shows `25` now included — proving the view reflects the tree's current state, not a frozen snapshot taken at view-creation time.
3. `advancedLevel()` models finding the next free 60-minute slot at or after `10:15` (minute `615`), given bookings at `9:00, 10:00, 11:00`. `615` is not booked, so `findNextFreeSlot` returns it immediately — the loop's `contains` check fails on the very first iteration, meaning `10:15` itself is already free.

## 7. Gotchas & takeaways

> Gotcha: `headMap`/`tailMap`/`subMap` return **live views**, not copies — mutating the original map after taking a view changes what the view shows, and in most cases mutating the view itself writes back to the original map too. Treating a range view as an independent snapshot is a common source of subtle bugs.

- `floorKey`/`ceilingKey` are inclusive of an exact match; `lowerKey`/`higherKey` are always strict, even if the given key exists in the map.
- All neighbor and range operations cost `O(log n)`, since they reuse the same red-black tree walk as an exact-key lookup.
- Range views (`headMap`, `tailMap`, `subMap`) are windows onto the same tree, not copies — changes propagate both ways in most cases.
- Related concepts: [TreeMap & TreeSet (red-black backed)](0113-treemap-treeset-red-black-backed.md), [Red-black trees](0111-red-black-trees.md).
