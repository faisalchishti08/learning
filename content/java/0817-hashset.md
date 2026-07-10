---
card: java
gi: 817
slug: hashset
title: HashSet
---

## 1. What it is

`HashSet` is the standard general-purpose [`Set`](0803-set.md) implementation. Internally, it's backed by a `HashMap` — every element added to the `HashSet` is actually stored as a **key** in that hidden `HashMap`, mapped to a constant dummy value. This means `HashSet`'s performance characteristics, and its uniqueness rule, are entirely inherited from `HashMap`'s: membership checks (`contains`) and insertion (`add`) both rely on the element's `hashCode()` to locate a bucket in O(1) average time, and then `equals()` to confirm (or rule out) an actual match within that bucket.

## 2. Why & when

Any time uniqueness needs to be enforced with the fastest possible average-case lookup — not sorted order, not insertion order, just "is this here or not" — `HashSet` is the default choice, precisely because it's a thin wrapper reusing `HashMap`'s proven O(1) average performance. The catch is that this performance guarantee is only as good as the elements' `hashCode()`/`equals()` implementations: for built-in types like `String` and boxed numbers, these are already correct and well-distributed. For a custom class, `HashSet` will silently misbehave — allowing duplicates that should have been rejected, or failing to find an element that's clearly present — unless `equals()` and `hashCode()` are both overridden, consistently, on that class.

## 3. Core concept

```java
class Point {
    final int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
    // No equals()/hashCode() override yet -- uses Object's defaults (identity-based).
}

Set<Point> visited = new HashSet<>();
visited.add(new Point(1, 2));
boolean stillNew = visited.add(new Point(1, 2)); // a DIFFERENT object, same x/y values
System.out.println(stillNew); // true -- treated as a NEW element, not a duplicate!
```

Without overriding `equals()`/`hashCode()`, `Point` falls back to `Object`'s identity-based defaults — two separately-constructed `Point(1, 2)` objects are considered *different* elements, even though their field values are identical, because `HashSet` (via its internal `HashMap`) only ever sees each object's default hash code and reference-equality check.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HashSet membership relies on hashCode to find a bucket and equals to confirm a match within that bucket">
  <text x="320" y="25" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">add(new Point(1,2)) — internal HashMap operation</text>

  <rect x="40" y="45" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1. hashCode() -&gt; bucket #</text>

  <line x1="220" y1="65" x2="270" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#a817)"/>
  <defs><marker id="a817" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="280" y="45" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2. locate that bucket</text>

  <line x1="460" y1="65" x2="510" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#a817)"/>

  <rect x="520" y="45" width="100" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="570" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3. equals()?</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Without a correct hashCode()/equals() pair on a custom class, step 1 and step 3</text>
  <text x="320" y="158" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">both fall back to Object's identity-based defaults, breaking value-based deduplication.</text>
</svg>

*`hashCode()` finds the bucket in O(1); `equals()` confirms the match inside it — both must be correctly overridden for value-based deduplication.*

## 5. Runnable example

Scenario: tracking visited grid coordinates for a pathfinding algorithm, growing from the broken default-identity behavior to the fix, to demonstrating how a poor-quality `hashCode()` still works correctly but degrades performance.

### Level 1 — Basic

```java
import java.util.*;

public class VisitedGridBroken {
    static class Point {
        final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        // Deliberately no equals()/hashCode() override -- uses Object's identity-based defaults.
    }

    public static void main(String[] args) {
        Set<Point> visited = new HashSet<>();
        visited.add(new Point(1, 2));
        visited.add(new Point(1, 2)); // same coordinates, DIFFERENT object

        System.out.println("visited set size: " + visited.size()); // expect 1 if dedup worked -- but it won't
    }
}
```

**How to run:** `java VisitedGridBroken.java` (JDK 17+).

Expected output:
```
visited set size: 2
```

Both `Point(1, 2)` objects are separately constructed, so without an `equals()`/`hashCode()` override, `HashSet` treats them as two distinct elements — the "visited" tracking is silently broken, and a pathfinding algorithm using this set would revisit the same coordinate over and over.

### Level 2 — Intermediate

```java
import java.util.*;

public class VisitedGridFixed {
    static class Point {
        final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;
            if (!(other instanceof Point p)) return false;
            return x == p.x && y == p.y;
        }

        @Override
        public int hashCode() {
            return Objects.hash(x, y);
        }
    }

    public static void main(String[] args) {
        Set<Point> visited = new HashSet<>();
        visited.add(new Point(1, 2));
        boolean stillNew = visited.add(new Point(1, 2)); // same coordinates, different object

        System.out.println("visited set size: " + visited.size());
        System.out.println("adding the same coordinates again reported new: " + stillNew);
        System.out.println("contains(3,4) before visiting: " + visited.contains(new Point(3, 4)));
    }
}
```

**How to run:** `java VisitedGridFixed.java`.

Expected output:
```
visited set size: 1
adding the same coordinates again reported new: false
contains(3,4) before visiting: false
```

The real-world concern added: overriding `equals()` (value-based comparison of `x`/`y`) and `hashCode()` (`Objects.hash(x, y)`, consistent with that `equals()` definition) together. Now `HashSet` correctly recognizes a second `Point(1, 2)` as a duplicate, regardless of it being a different object reference — exactly the behavior a "visited coordinates" set needs.

### Level 3 — Advanced

```java
import java.util.*;

public class VisitedGridHashQuality {
    static class BadHashPoint {
        final int x, y;
        BadHashPoint(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;
            if (!(other instanceof BadHashPoint p)) return false;
            return x == p.x && y == p.y;
        }

        @Override
        public int hashCode() {
            return 42; // deliberately terrible: every instance lands in the SAME bucket
        }
    }

    public static void main(String[] args) {
        Set<BadHashPoint> visited = new HashSet<>();
        int gridSize = 50;
        long start = System.nanoTime();
        for (int x = 0; x < gridSize; x++) {
            for (int y = 0; y < gridSize; y++) {
                visited.add(new BadHashPoint(x, y));
            }
        }
        boolean found = visited.contains(new BadHashPoint(49, 49)); // worst case: last bucket entry
        long elapsedNanos = System.nanoTime() - start;

        System.out.println("visited set size: " + visited.size() + " (correctness is fine -- equals() still works)");
        System.out.println("found (49,49): " + found);
        System.out.println("elapsed: " + (elapsedNanos / 1_000_000) + " ms");
        System.out.println("-> every element sharing one hash bucket makes lookups degrade toward O(n) instead of O(1)");
    }
}
```

**How to run:** `java VisitedGridHashQuality.java`. The exact millisecond count varies by machine, but it will be visibly, measurably slower than the equivalent workload with `Objects.hash(x, y)` from Level 2 — because every one of the 2,500 points collides into the same bucket.

Expected output shape:
```
visited set size: 2500 (correctness is fine -- equals() still works)
found (49,49): true
elapsed: ~15 ms
-> every element sharing one hash bucket makes lookups degrade toward O(n) instead of O(1)
```

This adds the production-flavored hard case: a `hashCode()` that's **consistent with `equals()`** (so correctness is never violated — `add`/`contains` still work correctly) but is a **poor-quality** hash that returns the same constant for every instance. This doesn't break correctness at all, but it destroys performance: every single element lands in the same bucket, turning `HashSet`'s O(1) average-case lookup into an O(n) linear scan within that one overloaded bucket — a subtle, purely-performance bug that's easy to miss in code review since all tests still pass.

## 6. Walkthrough

Tracing `VisitedGridHashQuality.main`:

1. The nested loop constructs 2,500 `BadHashPoint` objects (a 50×50 grid) and adds each to `visited`.
2. Every `add()` call internally computes `hashCode()` to pick a bucket — but since `hashCode()` always returns `42`, every single one of the 2,500 elements is routed to the **same** bucket, turning that one bucket into an effectively 2,500-element linked chain instead of the roughly-one-element buckets a well-distributed hash would produce.
3. `equals()` is still correctly implemented (comparing `x`/`y` by value), so no incorrect duplicates are ever inserted — `visited.size()` correctly reports `2500`, confirming correctness held up fine.
4. `visited.contains(new BadHashPoint(49, 49))` computes `hashCode()` (`42` again), lands in that same overloaded bucket, and then has to call `equals()` against potentially all 2,500 entries in that bucket one by one until it finds a match — an O(n) linear scan, not the O(1) average lookup `HashSet` is supposed to provide.
5. The measured elapsed time reflects this: noticeably slower than the equivalent lookup would be with a well-distributed hash (like `Objects.hash(x, y)` from Level 2), even though every individual `equals()` call itself is cheap — the sheer number of them, all funneled into one bucket, is what costs time.

## 7. Gotchas & takeaways

> **Gotcha:** `hashCode()` and `equals()` must always be overridden **together** and kept mutually consistent — objects that are `equals()` to each other **must** return the same `hashCode()` (though the reverse isn't required: unequal objects *can* share a hash code, as the bad-hash example shows). Overriding only one of the pair, or overriding them inconsistently, breaks `HashSet`/`HashMap` in ways that are easy to miss until duplicates or missing entries show up in production.

- `HashSet` is backed internally by a `HashMap`, storing each element as a key with a dummy value — its performance and correctness both come directly from `HashMap`'s hashing mechanism.
- Membership relies on `hashCode()` to find a bucket in O(1) average time, then `equals()` to confirm a match within that bucket.
- Custom classes without a correct `equals()`/`hashCode()` override fall back to `Object`'s identity-based defaults, silently breaking value-based deduplication.
- A poorly-distributed (but still `equals()`-consistent) `hashCode()` doesn't cause incorrect results — it causes a severe, easy-to-miss performance regression, degrading lookups from O(1) average toward O(n).
- `HashSet` gives no ordering guarantee whatsoever — reach for [`LinkedHashSet`](0818-linkedhashset.md) or [`TreeSet`](0819-treeset.md) when iteration order matters.
