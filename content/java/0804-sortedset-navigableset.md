---
card: java
gi: 804
slug: sortedset-navigableset
title: SortedSet / NavigableSet
---

## 1. What it is

`SortedSet<T>` is a [`Set`](0803-set.md) that keeps its elements in **ascending sorted order** at all times — by natural ordering (`Comparable`) or by an explicit `Comparator` supplied at construction. `NavigableSet<T>` (added in Java 6) extends `SortedSet` with proximity-search methods — `floor(e)` (greatest element ≤ e), `ceiling(e)` (smallest element ≥ e), `lower(e)` (strictly less than e), `higher(e)` (strictly greater than e) — plus range views `headSet`, `tailSet`, `subSet`, and a `descendingSet()`/`descendingIterator()` for reverse traversal. `TreeSet` is the standard implementation of both, backed by a red-black tree, giving O(log n) for insertion, removal, and every navigation method above.

## 2. Why & when

A `HashSet` answers "is this element present?" in O(1) but can't answer "what's the closest score to 87?" or "give me everyone ranked in the top 3" without a full O(n) scan and manual sort. `SortedSet`/`NavigableSet` exist for exactly that class of question — anything involving order, ranking, ranges, or nearest-neighbor lookups. Reach for `TreeSet` when the data must stay continuously sorted (a leaderboard that's queried between every insertion) rather than sorted once and left alone (which a `List` plus a single `Collections.sort()` call would handle more cheaply). The cost is that every `add`/`remove`/`contains` becomes O(log n) instead of `HashSet`'s O(1) average — a fair trade whenever range and nearest-neighbor queries are a core part of the workload.

## 3. Core concept

```java
NavigableSet<Integer> scores = new TreeSet<>(Set.of(72, 85, 91, 60, 78));
// sorted order: 60, 72, 78, 85, 91

scores.floor(80);    // 78 — greatest value <= 80
scores.ceiling(80);  // 85 — smallest value >= 80
scores.higher(85);   // 91 — strictly greater than 85
scores.lower(85);    // 78 — strictly less than 85

scores.headSet(80);        // [60, 72, 78]        — everything < 80
scores.tailSet(80);        // [85, 91]             — everything >= 80
scores.subSet(72, 91);     // [72, 78, 85]         — [72, 91)
```

`floor`/`ceiling`/`lower`/`higher` are the four "nearest neighbor" queries, each O(log n) via the tree's structure — no linear scan required even on a large set.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A NavigableSet's floor and ceiling queries locate the nearest values on either side of a target that isn't itself in the set">
  <line x1="40" y1="100" x2="600" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <g font-family="sans-serif">
    <circle cx="80" cy="100" r="6" fill="#6db33f"/><text x="80" y="130" fill="#e6edf3" font-size="11" text-anchor="middle">60</text>
    <circle cx="200" cy="100" r="6" fill="#6db33f"/><text x="200" y="130" fill="#e6edf3" font-size="11" text-anchor="middle">72</text>
    <circle cx="280" cy="100" r="6" fill="#6db33f"/><text x="280" y="130" fill="#e6edf3" font-size="11" text-anchor="middle">78</text>
    <circle cx="440" cy="100" r="6" fill="#6db33f"/><text x="440" y="130" fill="#e6edf3" font-size="11" text-anchor="middle">85</text>
    <circle cx="560" cy="100" r="6" fill="#6db33f"/><text x="560" y="130" fill="#e6edf3" font-size="11" text-anchor="middle">91</text>
  </g>
  <circle cx="360" cy="100" r="5" fill="#79c0ff" stroke="#e6edf3"/>
  <text x="360" y="60" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">target: 80 (not in set)</text>
  <line x1="360" y1="70" x2="360" y2="94" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3"/>

  <line x1="280" y1="115" x2="360" y2="115" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a804)"/>
  <text x="320" y="112" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">floor(80)=78</text>

  <line x1="440" y1="150" x2="360" y2="150" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a804o)"/>
  <line x1="360" y1="150" x2="360" y2="106" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="2"/>
  <text x="400" y="165" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">ceiling(80)=85</text>

  <defs>
    <marker id="a804" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a804o" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M6,0 L0,3 L6,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

*`floor(80)` finds the nearest value at or below the target; `ceiling(80)` finds the nearest at or above it — both in O(log n).*

## 5. Runnable example

Scenario: a game leaderboard stored as a `TreeSet<Integer>`, growing from basic sorted iteration to nearest-rank lookups to full range queries with a custom descending order.

### Level 1 — Basic

```java
import java.util.*;

public class LeaderboardBasic {
    public static void main(String[] args) {
        NavigableSet<Integer> scores = new TreeSet<>();
        scores.add(72);
        scores.add(91);
        scores.add(60);
        scores.add(85);
        scores.add(78);

        System.out.println("sorted scores: " + scores);
        System.out.println("lowest: " + scores.first());
        System.out.println("highest: " + scores.last());
    }
}
```

**How to run:** `java LeaderboardBasic.java` (JDK 17+).

Expected output:
```
sorted scores: [60, 72, 78, 85, 91]
lowest: 60
highest: 91
```

Unlike `HashSet`, iterating a `TreeSet` always yields ascending order — no explicit sort call needed, because the tree maintains order continuously as elements are added.

### Level 2 — Intermediate

```java
import java.util.*;

public class LeaderboardNearest {
    public static void main(String[] args) {
        NavigableSet<Integer> scores = new TreeSet<>(Set.of(60, 72, 78, 85, 91));

        int target = 80;
        Integer nearestBelow = scores.floor(target);
        Integer nearestAtOrAbove = scores.ceiling(target);
        Integer strictlyAbove = scores.higher(85);
        Integer strictlyBelow = scores.lower(85);

        System.out.println("floor(80): " + nearestBelow);
        System.out.println("ceiling(80): " + nearestAtOrAbove);
        System.out.println("higher(85): " + strictlyAbove);
        System.out.println("lower(85): " + strictlyBelow);

        // A score exactly present behaves differently for floor/ceiling vs lower/higher:
        System.out.println("floor(85) [85 IS present]: " + scores.floor(85));   // 85 itself
        System.out.println("lower(85) [strictly less]: " + scores.lower(85));  // 78
    }
}
```

**How to run:** `java LeaderboardNearest.java`.

Expected output:
```
floor(80): 78
ceiling(80): 85
higher(85): 91
lower(85): 78
floor(85) [85 IS present]: 85
lower(85) [strictly less]: 78
```

The real-world concern added: distinguishing the **inclusive** pair (`floor`/`ceiling`, which can return the target itself if present) from the **exclusive** pair (`lower`/`higher`, which never do) — a distinction that matters whenever the logic needs "the next distinct score" versus "the nearest score, ties allowed."

### Level 3 — Advanced

```java
import java.util.*;

public class LeaderboardRanges {
    public static void main(String[] args) {
        // Custom Comparator: highest score first, matching how a leaderboard is displayed.
        NavigableSet<Integer> ranked = new TreeSet<>(Comparator.reverseOrder());
        ranked.addAll(Set.of(60, 72, 78, 85, 91, 68, 95));

        System.out.println("full leaderboard (highest first): " + ranked);

        // Top 3 — headSet on a reverse-ordered set gives the highest scores.
        List<Integer> top3 = new ArrayList<>();
        Iterator<Integer> it = ranked.iterator();
        while (it.hasNext() && top3.size() < 3) {
            top3.add(it.next());
        }
        System.out.println("top 3: " + top3);

        // Range query: scores strictly between 68 and 91 — subSet honors the comparator's order.
        NavigableSet<Integer> midRange = ranked.subSet(91, false, 68, false);
        System.out.println("scores between 68 and 91 (exclusive both ends): " + midRange);

        // descendingSet() flips the view without rebuilding the tree.
        NavigableSet<Integer> ascending = ranked.descendingSet();
        System.out.println("ascending view via descendingSet(): " + ascending);
    }
}
```

**How to run:** `java LeaderboardRanges.java`.

Expected output:
```
full leaderboard (highest first): [95, 91, 85, 78, 72, 68, 60]
top 3: [95, 91, 85]
scores between 68 and 91 (exclusive both ends): [85, 78, 72]
ascending view via descendingSet(): [60, 68, 72, 78, 85, 91, 95]
```

This adds the production-flavored hard case: a **custom `Comparator`** (`Comparator.reverseOrder()`) reversing the set's natural order to match how a leaderboard is normally displayed, plus the three-argument `subSet(from, fromInclusive, to, toInclusive)` overload, which respects whatever order the set was built with — here it correctly returns scores between 68 and 91 even though the set itself iterates highest-to-lowest. `descendingSet()` returns a live, reordered **view** in O(1), not a copy — cheap to obtain whenever a temporarily reversed perspective is needed.

## 6. Walkthrough

Tracing `LeaderboardRanges.main`:

1. `ranked` is constructed with `Comparator.reverseOrder()`, so every insertion via `addAll` is placed according to descending numeric order rather than the natural ascending order `TreeSet` would use by default.
2. Printing `ranked` confirms the order: `95` (highest) first, `60` (lowest) last.
3. The `top3` loop walks `ranked.iterator()` — because the set's internal order is already "highest first," simply taking the first three elements yielded by the iterator gives the top three scores with no separate sort or comparison logic needed.
4. `ranked.subSet(91, false, 68, false)` asks for the range **between** 91 and 68 — since the set's comparator treats "greater" scores as coming first, "from 91 down to 68" is the correct direction to express this range, and both boundary flags are `false` so 91 and 68 themselves are excluded, leaving `85, 78, 72`.
5. `ranked.descendingSet()` returns a `NavigableSet` view that iterates in the *opposite* order to `ranked` — since `ranked` is already descending, this view is ascending, printed as `[60, 68, ..., 95]`. This view shares the same underlying tree nodes as `ranked`; it's a reinterpretation of traversal direction, not a rebuilt copy, so it costs O(1) to create regardless of set size.

## 7. Gotchas & takeaways

> **Gotcha:** `floor`/`ceiling` are **inclusive** of the target value if it's present in the set; `lower`/`higher` are always **strict** and never return the target itself. Mixing these up is an easy off-by-one bug — `scores.floor(85)` returns `85` itself when `85` is in the set, but `scores.lower(85)` returns the next value down (`78`).

- `SortedSet`/`NavigableSet` maintain continuous ascending (or comparator-defined) order; `TreeSet` is the standard implementation, backed by a red-black tree with O(log n) operations.
- `floor`/`ceiling` are inclusive nearest-match queries; `lower`/`higher` are strict (exclusive) nearest-match queries.
- `headSet`, `tailSet`, and `subSet` return **live views** over a contiguous range, all honoring whatever comparator the set was constructed with.
- `descendingSet()`/`descendingIterator()` give a reversed traversal in O(1) without copying the underlying structure.
- Reach for `TreeSet` only when range/nearest-neighbor queries are a core need — for "sort once, read many times" workloads a plain `List` plus `Collections.sort` is usually cheaper.
