---
card: java
gi: 808
slug: sortedmap-navigablemap
title: SortedMap / NavigableMap
---

## 1. What it is

`SortedMap<K, V>` is a [`Map`](0807-map.md) that keeps its **keys** in ascending sorted order — by natural ordering or an explicit `Comparator`. `NavigableMap<K, V>` (Java 6) extends it with the same family of proximity queries [`NavigableSet`](0804-sortedset-navigableset.md) offers, but returning whole entries or keys: `floorKey`/`floorEntry` (greatest key ≤ target), `ceilingKey`/`ceilingEntry` (smallest key ≥ target), `lowerKey`/`lowerEntry` (strictly less), `higherKey`/`higherEntry` (strictly greater), plus range views `headMap`, `tailMap`, `subMap`, and `descendingMap()`. `TreeMap` is the standard implementation, backed by a red-black tree, giving O(log n) for `put`, `get`, `remove`, and every navigation method.

## 2. Why & when

A `HashMap` answers "what's the value for this exact key?" in O(1), but can't answer "what's the event scheduled closest to (but not after) this timestamp?" without scanning every key. `SortedMap`/`NavigableMap` exist for exactly this shape of problem — anything keyed by a value with a natural order (timestamps, scores, prices) where queries need "nearest," "before," "after," or "within this range" rather than only "exact match." Reach for `TreeMap` when the keys are continuously queried by range or proximity; stick with `HashMap` when only exact-key lookups matter, since `TreeMap`'s O(log n) is strictly slower than `HashMap`'s O(1) average for that simpler case.

## 3. Core concept

```java
NavigableMap<Long, String> schedule = new TreeMap<>();
schedule.put(1000L, "standup");
schedule.put(3000L, "lunch");
schedule.put(5000L, "retro");

schedule.floorEntry(4000L);   // 3000=lunch — latest event at or before time 4000
schedule.ceilingEntry(4000L); // 5000=retro — earliest event at or after time 4000
schedule.firstKey();          // 1000
schedule.lastKey();           // 5000

schedule.subMap(1000L, 5000L); // {1000=standup, 3000=lunch} — [1000, 5000)
```

Just like `NavigableSet`, `floor`/`ceiling` are inclusive of an exact match; `lower`/`higher` are always strict.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A NavigableMap's floorEntry and ceilingEntry find the nearest scheduled events on either side of a query timestamp">
  <line x1="40" y1="100" x2="600" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <g font-family="sans-serif">
    <circle cx="100" cy="100" r="6" fill="#6db33f"/>
    <text x="100" y="130" fill="#e6edf3" font-size="10" text-anchor="middle">1000</text>
    <text x="100" y="145" fill="#8b949e" font-size="9" text-anchor="middle">standup</text>

    <circle cx="300" cy="100" r="6" fill="#6db33f"/>
    <text x="300" y="130" fill="#e6edf3" font-size="10" text-anchor="middle">3000</text>
    <text x="300" y="145" fill="#8b949e" font-size="9" text-anchor="middle">lunch</text>

    <circle cx="540" cy="100" r="6" fill="#6db33f"/>
    <text x="540" y="130" fill="#e6edf3" font-size="10" text-anchor="middle">5000</text>
    <text x="540" y="145" fill="#8b949e" font-size="9" text-anchor="middle">retro</text>
  </g>

  <circle cx="420" cy="100" r="5" fill="#79c0ff" stroke="#e6edf3"/>
  <text x="420" y="60" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">query: 4000</text>
  <line x1="420" y1="70" x2="420" y2="94" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3"/>

  <line x1="300" y1="115" x2="420" y2="115" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a808)"/>
  <text x="360" y="112" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">floorEntry=lunch</text>

  <line x1="540" y1="165" x2="420" y2="165" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a808o)"/>
  <line x1="420" y1="165" x2="420" y2="106" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="2"/>
  <text x="480" y="180" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">ceilingEntry=retro</text>

  <defs>
    <marker id="a808" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a808o" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M6,0 L0,3 L6,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

*`floorEntry(4000)` finds the latest event at or before the query time; `ceilingEntry(4000)` finds the earliest at or after it.*

## 5. Runnable example

Scenario: a daily meeting schedule keyed by epoch-millisecond timestamps, growing from basic sorted storage to nearest-event lookups to a full time-window range query with a reversed view.

### Level 1 — Basic

```java
import java.util.*;

public class ScheduleBasic {
    public static void main(String[] args) {
        NavigableMap<Long, String> schedule = new TreeMap<>();
        schedule.put(3000L, "lunch");
        schedule.put(1000L, "standup");
        schedule.put(5000L, "retro");

        System.out.println("schedule in time order: " + schedule);
        System.out.println("first event: " + schedule.firstEntry());
        System.out.println("last event: " + schedule.lastEntry());
    }
}
```

**How to run:** `java ScheduleBasic.java` (JDK 17+).

Expected output:
```
schedule in time order: {1000=standup, 3000=lunch, 5000=retro}
first event: 1000=standup
last event: 5000=retro
```

Even though entries were inserted out of chronological order (`3000`, then `1000`, then `5000`), `TreeMap` always stores and iterates them by ascending key — `standup` (1000) prints first regardless of insertion order.

### Level 2 — Intermediate

```java
import java.util.*;

public class ScheduleNearest {
    public static void main(String[] args) {
        NavigableMap<Long, String> schedule = new TreeMap<>(Map.of(
            1000L, "standup", 3000L, "lunch", 5000L, "retro"
        ));

        long queryTime = 4000L;
        Map.Entry<Long, String> lastBefore = schedule.floorEntry(queryTime);
        Map.Entry<Long, String> nextAfter = schedule.ceilingEntry(queryTime);

        System.out.println("at time " + queryTime + ":");
        System.out.println("  most recent event: " + lastBefore);
        System.out.println("  next upcoming event: " + nextAfter);

        // A query time that exactly matches a key:
        System.out.println("floorEntry(3000) [exact match]: " + schedule.floorEntry(3000L));
        System.out.println("lowerEntry(3000) [strictly before]: " + schedule.lowerEntry(3000L));
    }
}
```

**How to run:** `java ScheduleNearest.java`.

Expected output:
```
at time 4000:
  most recent event: 3000=lunch
  next upcoming event: 5000=retro
floorEntry(3000) [exact match]: 3000=lunch
lowerEntry(3000) [strictly before]: 1000=standup
```

The real-world concern added: answering "what's happening right now (or most recently)" and "what's coming up next" for an arbitrary query time that doesn't land exactly on a scheduled event — `floorEntry`/`ceilingEntry` handle that directly. The exact-match case (`floorEntry(3000)`) confirms `floor` is inclusive, returning the entry at `3000` itself, while `lowerEntry(3000)` demonstrates the strict variant skipping past it to `1000`.

### Level 3 — Advanced

```java
import java.util.*;

public class ScheduleWindow {
    public static void main(String[] args) {
        NavigableMap<Long, String> schedule = new TreeMap<>(Map.of(
            1000L, "standup", 2500L, "1:1 with manager", 3000L, "lunch",
            4500L, "design review", 5000L, "retro", 6000L, "wrap-up"
        ));

        // Time-window query: everything between 2000 and 5000, inclusive on both ends.
        NavigableMap<Long, String> workingHoursWindow = schedule.subMap(2000L, true, 5000L, true);
        System.out.println("events in [2000, 5000]: " + workingHoursWindow);

        // Reverse-chronological view for an "upcoming events, latest first" display, no copy needed.
        NavigableMap<Long, String> reverseView = schedule.descendingMap();
        System.out.println("reverse chronological: " + reverseView);

        // headMap/tailMap for "everything before/after a cutoff".
        System.out.println("morning events (before 3000): " + schedule.headMap(3000L));
        System.out.println("afternoon events (3000 onward): " + schedule.tailMap(3000L));
    }
}
```

**How to run:** `java ScheduleWindow.java`.

Expected output:
```
events in [2000, 5000]: {2500=1:1 with manager, 3000=lunch, 4500=design review, 5000=retro}
reverse chronological: {6000=wrap-up, 5000=retro, 4500=design review, 3000=lunch, 2500=1:1 with manager, 1000=standup}
events before 3000: {1000=standup, 2500=1:1 with manager}
afternoon events (3000 onward): {3000=lunch, 4500=design review, 5000=retro, 6000=wrap-up}
```

This adds the production-flavored hard case: a genuine **time-window** query using the five-argument `subMap(from, fromInclusive, to, toInclusive)` overload, a **reversed view** via `descendingMap()` (a live view, not a rebuilt copy — O(1) to obtain), and the simpler one-sided `headMap`/`tailMap` cutoff queries. All four operate directly on the tree structure in O(log n) to find the boundary, then return a view over the qualifying range rather than copying matching entries into a new map.

## 6. Walkthrough

Tracing `ScheduleWindow.main`:

1. `schedule` is built from an unordered `Map.of(...)` literal but stored in a `TreeMap`, so it immediately reorders into ascending key order internally: `1000, 2500, 3000, 4500, 5000, 6000`.
2. `schedule.subMap(2000L, true, 5000L, true)` walks the tree to find the boundary at or after `2000` (landing on `2500`) and the boundary at or before `5000` (landing on `5000` itself, included because the fourth argument is `true`), returning a view spanning exactly that range — four entries.
3. `schedule.descendingMap()` returns a `NavigableMap` view that iterates the same underlying entries in the opposite order — no new tree is built; it's a reinterpretation of traversal direction over the existing structure, so printing it shows `6000` first and `1000` last.
4. `schedule.headMap(3000L)` returns every entry with a key **strictly less than** `3000` (the default two-argument form is exclusive of the boundary) — `1000` and `2500`, but not `3000` itself.
5. `schedule.tailMap(3000L)` returns every entry with a key **greater than or equal to** `3000` (the default form is inclusive of the boundary) — `3000` through `6000`.
6. Each of these four views is printed directly; none of them mutate `schedule` or copy its entries — they're all backed by the same underlying red-black tree, computed in O(log n) to locate their starting/ending boundary.

## 7. Gotchas & takeaways

> **Gotcha:** the two-argument `headMap(to)`/`tailMap(from)` overloads have **asymmetric inclusivity by default** — `headMap(to)` excludes `to`, while `tailMap(from)` includes `from`. This mirrors how half-open ranges are conventionally expressed (`[from, to)`), but it's easy to assume both are inclusive or both exclusive; use the explicit three-argument overloads (`headMap(to, inclusive)`, `tailMap(from, inclusive)`) when the boundary behavior needs to be unambiguous at the call site.

- `SortedMap`/`NavigableMap` keep keys in continuous ascending (or comparator-defined) order; `TreeMap` is the standard implementation, backed by a red-black tree with O(log n) operations.
- `floorEntry`/`ceilingEntry` are inclusive nearest-match queries; `lowerEntry`/`higherEntry` are strict.
- `subMap`, `headMap`, and `tailMap` return **live views** over a contiguous key range — no copying, O(log n) to establish the boundary.
- `descendingMap()` gives a reversed view in O(1), sharing the same underlying tree as the original.
- Reach for `TreeMap` when range or nearest-key queries matter; stick with [`HashMap`](0807-map.md) for pure exact-key lookups, since it's faster for that simpler case.
