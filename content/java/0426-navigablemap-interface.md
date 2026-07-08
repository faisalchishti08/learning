---
card: java
gi: 426
slug: navigablemap-interface
title: NavigableMap interface
---

## 1. What it is

`NavigableMap<K,V>`, added in Java 6 and implemented by `TreeMap`, extends `SortedMap` with methods for finding the closest keys **around** a given point: `floorKey(k)` (largest key ≤ `k`), `ceilingKey(k)` (smallest key ≥ `k`), `lowerKey(k)` (largest key strictly < `k`), and `higherKey(k)` (smallest key strictly > `k`) — plus corresponding `xxxEntry` variants returning the whole `Map.Entry`, range-view methods (`headMap`, `tailMap`, `subMap`), and `descendingMap()` for reverse iteration.

## 2. Why & when

A plain `SortedMap` only gives you `firstKey()`/`lastKey()` and iteration in sorted order — useful, but it can't directly answer "what's the closest key to this value?" without manually walking the iterator. `NavigableMap`'s `floor`/`ceiling`/`lower`/`higher` family answers exactly that class of question in one call, backed by `TreeMap`'s red-black tree structure, so these lookups run in logarithmic time rather than requiring a linear scan.

You reach for `NavigableMap` any time your data is naturally keyed by a sortable value and you need "closest match" or "range" queries — a price/quantity lookup table (find the discount tier for this order size), an event timeline (find the most recent event before this timestamp), or (as the runnable example below shows) an auction bid book where you need to find bids near, above, or below a given price.

## 3. Core concept

```java
import java.util.*;

NavigableMap<Double, String> bids = new TreeMap<>();
bids.put(100.0, "Alice");
bids.put(150.0, "Bob");
bids.put(200.0, "Carol");

bids.floorKey(175.0);     // 150.0 -- largest key <= 175.0
bids.ceilingKey(175.0);   // 200.0 -- smallest key >= 175.0
bids.lowerKey(150.0);     // 100.0 -- largest key STRICTLY less than 150.0
bids.higherKey(150.0);    // 200.0 -- smallest key STRICTLY greater than 150.0

bids.firstEntry();        // 100.0 = Alice
bids.lastEntry();         // 200.0 = Carol
```

The distinction between `floor`/`ceiling` (inclusive of an exact match) and `lower`/`higher` (strictly excluding an exact match) is the whole API in a nutshell — pick based on whether an exact hit at `k` itself should count.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Given a target key, floorKey and lowerKey look leftward on the sorted key line, while ceilingKey and higherKey look rightward, differing in whether an exact match at the target counts">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <line x1="40" y1="80" x2="600" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <circle cx="120" cy="80" r="5" fill="#6db33f"/><text x="120" y="65" fill="#6db33f" font-size="10" text-anchor="middle">100</text>
  <circle cx="280" cy="80" r="5" fill="#79c0ff"/><text x="280" y="65" fill="#79c0ff" font-size="10" text-anchor="middle">150 (target)</text>
  <circle cx="440" cy="80" r="5" fill="#e6edf3"/><text x="440" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">200</text>

  <text x="120" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">lower(150)=100</text>
  <text x="280" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">floor/ceiling(150)=150</text>
  <text x="440" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">higher(150)=200</text>
  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">floor/ceiling include an exact match at the target; lower/higher never do.</text>
</svg>

`floor`/`ceiling` include an exact hit at the target key; `lower`/`higher` always look strictly past it.

## 5. Runnable example

Scenario: an auction bid book keyed by bid price — the same book, evolved from basic nearest-key lookups, through range views for reporting bid brackets, to processing bids from highest to lowest using `descendingMap` and `pollFirstEntry`/`pollLastEntry`.

### Level 1 — Basic

```java
import java.util.*;

public class AuctionBidLookup {
    public static void main(String[] args) {
        NavigableMap<Double, String> bids = new TreeMap<>();
        bids.put(100.0, "Alice");
        bids.put(150.0, "Bob");
        bids.put(200.0, "Carol");

        double targetPrice = 175.0;
        System.out.println("Highest bid <= " + targetPrice + ": " + bids.floorEntry(targetPrice));
        System.out.println("Lowest bid >= " + targetPrice + ": " + bids.ceilingEntry(targetPrice));
        System.out.println("Highest bid strictly < 150.0: " + bids.lowerEntry(150.0));
        System.out.println("Lowest bid strictly > 150.0: " + bids.higherEntry(150.0));
    }
}
```

**How to run:** `java AuctionBidLookup.java`

`floorEntry`/`ceilingEntry` find the closest bid at or around a target price in logarithmic time, without manually scanning every bid — exactly the kind of query a plain `SortedMap` can't answer directly.

### Level 2 — Intermediate

```java
import java.util.*;

public class AuctionBidRanges {
    public static void main(String[] args) {
        NavigableMap<Double, String> bids = new TreeMap<>();
        bids.put(100.0, "Alice");
        bids.put(150.0, "Bob");
        bids.put(175.0, "Dave");
        bids.put(200.0, "Carol");

        System.out.println("All bids under 175 (exclusive): " + bids.headMap(175.0, false));
        System.out.println("All bids under 175 (inclusive): " + bids.headMap(175.0, true));
        System.out.println("All bids from 150 up (inclusive): " + bids.tailMap(150.0, true));
        System.out.println("Bids between 100 and 200 (100 inclusive, 200 exclusive): "
            + bids.subMap(100.0, true, 200.0, false));
    }
}
```

**How to run:** `java AuctionBidRanges.java`

`headMap`/`tailMap`/`subMap` return **live views** into the same underlying map (not copies) covering a range, with explicit `boolean` flags controlling whether each boundary is inclusive — precise control that's easy to get wrong if you assume a default without checking, so always be explicit about inclusivity when it matters.

### Level 3 — Advanced

```java
import java.util.*;

public class AuctionBidProcessing {
    public static void main(String[] args) {
        NavigableMap<Double, String> bids = new TreeMap<>();
        bids.put(100.0, "Alice");
        bids.put(150.0, "Bob");
        bids.put(175.0, "Dave");
        bids.put(200.0, "Carol");

        System.out.println("Processing bids from HIGHEST to lowest (winner first):");
        NavigableMap<Double, String> highestFirst = bids.descendingMap();
        for (Map.Entry<Double, String> entry : highestFirst.entrySet()) {
            System.out.println("  $" + entry.getKey() + " - " + entry.getValue());
        }

        System.out.println("\nAwarding the auction (highest bid wins, removed from the book):");
        Map.Entry<Double, String> winner = bids.pollLastEntry(); // removes AND returns the highest entry
        System.out.println("Winner: " + winner.getValue() + " at $" + winner.getKey());

        System.out.println("Remaining bids after award: " + bids);
    }
}
```

**How to run:** `java AuctionBidProcessing.java`

`descendingMap()` gives a reversed **view** of the same map (highest key first) without copying or re-sorting anything, and `pollLastEntry()` atomically removes and returns the single highest-keyed entry — a clean, one-call way to "award the auction to the highest bidder and take them out of contention."

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `bids` holds four entries, keyed by price: 100.0 (Alice), 150.0 (Bob), 175.0 (Dave), 200.0 (Carol) — `TreeMap` keeps these sorted by key internally regardless of insertion order.

`bids.descendingMap()` returns a `NavigableMap` view that iterates in the **reverse** of `bids`'s natural order — internally, this doesn't rebuild or copy any data; it's backed by the same red-black tree, just traversed in the opposite direction. The `for` loop over `highestFirst.entrySet()` therefore visits Carol (200.0) first, then Dave (175.0), then Bob (150.0), then Alice (100.0) — printing each with a `$` prefix.

`bids.pollLastEntry()` is then called on the **original** map (not the descending view). This finds the entry with the **highest** key (200.0, Carol), removes it from `bids`, and returns it as a `Map.Entry` — all as one atomic operation. `winner.getValue()` is `"Carol"`, `winner.getKey()` is `200.0`, so `"Winner: Carol at $200.0"` is printed.

Finally, `System.out.println("Remaining bids after award: " + bids)` prints the map's current state — since `pollLastEntry()` actually removed Carol's entry (not just returned a copy of it), `bids` now contains only the three remaining entries: Alice, Bob, and Dave, still sorted by key.

Expected output:
```
Processing bids from HIGHEST to lowest (winner first):
  $200.0 - Carol
  $175.0 - Dave
  $150.0 - Bob
  $100.0 - Alice

Awarding the auction (highest bid wins, removed from the book):
Winner: Carol at $200.0

Remaining bids after award: {100.0=Alice, 150.0=Bob, 175.0=Dave}
```

## 7. Gotchas & takeaways

> `headMap`, `tailMap`, `subMap`, and `descendingMap` all return **live views**, not independent copies — mutating the original map after obtaining one of these views (or mutating the view itself, where supported) affects both, since they share the same underlying data structure. If you need a frozen snapshot instead, explicitly copy it: `new TreeMap<>(bids.headMap(175.0))`.

- `floorKey`/`floorEntry` and `ceilingKey`/`ceilingEntry` include an exact match at the target key; `lowerKey`/`lowerEntry` and `higherKey`/`higherEntry` always look strictly past it, even if the target itself is a key.
- `headMap`, `tailMap`, and `subMap` accept explicit `boolean` inclusive/exclusive flags on their boundaries — always specify them deliberately rather than relying on a remembered default, since getting a boundary's inclusivity wrong is a common source of off-by-one bugs.
- `descendingMap()` gives a reverse-order view without any copying or re-sorting — a genuinely cheap operation, not something to avoid for performance reasons.
- `pollFirstEntry()`/`pollLastEntry()` atomically remove and return the lowest/highest entry in one call — ideal for "process the next item in priority order and take it out of the pool" patterns, like awarding an auction.
- All of these operations run in logarithmic time on `TreeMap`'s underlying red-black tree, making `NavigableMap` a strong choice whenever "closest match" or "range" queries matter, not just simple key lookups.
