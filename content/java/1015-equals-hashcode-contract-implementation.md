---
card: java
gi: 1015
slug: equals-hashcode-contract-implementation
title: equals/hashCode contract & implementation
---

## 1. What it is

Every Java object inherits `equals(Object)` and `hashCode()` from `Object`, which by default compare **identity** (are these the exact same object in memory?) rather than **value** (do these two objects represent the same logical data?). Overriding both together lets two distinct objects — different instances, same data — be treated as equal. The two methods form a **contract**: if `a.equals(b)` is `true`, then `a.hashCode()` **must** equal `b.hashCode()`. Breaking that contract doesn't cause a compile error; it causes silent, confusing bugs in anything backed by a hash table, like `HashMap` or `HashSet`.

## 2. Why & when

Collections like `HashMap` and `HashSet` use `hashCode()` to decide which internal "bucket" an object belongs in, and only then use `equals()` to check for an exact match within that bucket. If two equal objects report different hash codes, a `HashSet` can end up storing "duplicate" entries that are `.equals()` to each other but land in different buckets — and a `HashMap.get()` can fail to find a value that was, by every reasonable definition, already put in. This is exactly why the contract must hold, and why it's dangerous to override one method without the other.

Override `equals`/`hashCode` when a class represents a **value** — two `Point(3, 4)` instances should be considered equal regardless of which object reference you're holding — and you plan to compare instances for equality or store them in hash-based collections. Skip it for classes that are inherently about **identity** (a `Connection`, a `Thread`) where two instances are never meant to be considered "the same" just because their fields happen to match.

## 3. Core concept

```
class Point {
    private final int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;              // same reference -> trivially equal
        if (!(obj instanceof Point other)) return false; // different type -> never equal
        return this.x == other.x && this.y == other.y;   // compare the actual fields
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(x, y); // MUST be consistent with equals's fields
    }
}

Point a = new Point(3, 4);
Point b = new Point(3, 4); // a different object, same data
System.out.println(a.equals(b));       // true -- value equality
System.out.println(a.hashCode() == b.hashCode()); // MUST also be true, or the contract breaks
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two distinct Point objects with the same x and y fields being equal to each other and reporting identical hash codes, placing them in the same HashMap bucket">
  <rect x="30" y="30" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">a = Point(3,4)</text>

  <rect x="30" y="110" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">b = Point(3,4)</text>

  <rect x="280" y="65" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="87" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">equals: true</text>
  <text x="350" y="105" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">hashCode: same</text>

  <line x1="160" y1="55" x2="280" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="160" y1="135" x2="280" y2="105" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two different object references with identical field values must both `.equals()` each other and report the same `.hashCode()`.

## 5. Runnable example

Scenario: using a custom `Point` class as a `HashSet` element and `HashMap` key, evolving from the broken default identity-based behavior into a correct, contract-honoring implementation.

### Level 1 — Basic

```java
// File: EqualsHashCodeBasic.java
import java.util.HashSet;
import java.util.Set;

class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
    // No equals/hashCode override -- uses Object's default IDENTITY comparison.
}

public class EqualsHashCodeBasic {
    public static void main(String[] args) {
        Point a = new Point(3, 4);
        Point b = new Point(3, 4); // logically the same point, different object

        System.out.println("a.equals(b): " + a.equals(b));

        Set<Point> points = new HashSet<>();
        points.add(a);
        points.add(b);
        System.out.println("set size: " + points.size());
    }
}
```

**How to run:** save as `EqualsHashCodeBasic.java`, then `javac EqualsHashCodeBasic.java && java EqualsHashCodeBasic` (JDK 17+).

Expected output:
```
a.equals(b): false
set size: 2
```

`a` and `b` represent the exact same logical point `(3, 4)`, but the default `equals` only considers them equal if they're the *same object* — so the `HashSet` (which should logically hold one unique point) ends up storing two "duplicate" entries.

### Level 2 — Intermediate

```java
// File: EqualsHashCodeIntermediate.java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (!(obj instanceof Point other)) return false;
        return this.x == other.x && this.y == other.y;
    }

    @Override
    public int hashCode() {
        return Objects.hash(x, y);
    }
}

public class EqualsHashCodeIntermediate {
    public static void main(String[] args) {
        Point a = new Point(3, 4);
        Point b = new Point(3, 4);

        System.out.println("a.equals(b): " + a.equals(b));
        System.out.println("hashCodes match: " + (a.hashCode() == b.hashCode()));

        Set<Point> points = new HashSet<>();
        points.add(a);
        points.add(b);
        System.out.println("set size: " + points.size());
    }
}
```

**How to run:** save as `EqualsHashCodeIntermediate.java`, then `javac EqualsHashCodeIntermediate.java && java EqualsHashCodeIntermediate` (JDK 17+).

Expected output:
```
a.equals(b): true
hashCodes match: true
set size: 1
```

The real-world concern added: `equals` and `hashCode` are overridden together, consistently based on the same fields (`x` and `y`). The `HashSet` now correctly recognizes `a` and `b` as the same logical point, storing only one entry.

### Level 3 — Advanced

```java
// File: EqualsHashCodeAdvanced.java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

// Deliberately broken: hashCode based on DIFFERENT fields than equals.
// This is exactly the kind of subtle contract violation that compiles fine
// and only fails at runtime, inside a hash-based collection.
class BrokenPoint {
    int x, y;
    String label; // NOT used in equals, but IS used in hashCode -- contract violation

    BrokenPoint(int x, int y, String label) { this.x = x; this.y = y; this.label = label; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (!(obj instanceof BrokenPoint other)) return false;
        return this.x == other.x && this.y == other.y; // only x, y
    }

    @Override
    public int hashCode() {
        return Objects.hash(label); // only label -- inconsistent with equals!
    }
}

class Point {
    final int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
    @Override public boolean equals(Object obj) {
        if (this == obj) return true;
        if (!(obj instanceof Point other)) return false;
        return this.x == other.x && this.y == other.y;
    }
    @Override public int hashCode() { return Objects.hash(x, y); }
}

public class EqualsHashCodeAdvanced {
    public static void main(String[] args) {
        BrokenPoint a = new BrokenPoint(3, 4, "start");
        BrokenPoint b = new BrokenPoint(3, 4, "finish"); // equals(a) is true, but hashCode differs!

        System.out.println("broken: a.equals(b) = " + a.equals(b));
        System.out.println("broken: hashCodes match = " + (a.hashCode() == b.hashCode()));

        Map<Point, String> visited = new HashMap<>();
        visited.put(new Point(3, 4), "first visit");
        String lookup = visited.get(new Point(3, 4)); // a DIFFERENT object, same coordinates
        System.out.println("correct lookup result: " + lookup);
    }
}
```

**How to run:** save as `EqualsHashCodeAdvanced.java`, then `javac EqualsHashCodeAdvanced.java && java EqualsHashCodeAdvanced` (JDK 17+).

Expected output:
```
broken: a.equals(b) = true
broken: hashCodes match = false
correct lookup result: first visit
```

The production-flavored hard case: `BrokenPoint` violates the contract — `a.equals(b)` is `true` (both have `x=3, y=4`), but `a.hashCode() != b.hashCode()` because `hashCode` used a different field (`label`) than `equals` did. This exact bug means `a` and `b` could end up in different `HashSet` buckets despite being "equal," silently breaking lookups and duplicate detection — the correctly-implemented `Point`, by contrast, retrieves the right value via `HashMap.get` even from a completely different object instance.

## 6. Walkthrough

Tracing `visited.get(new Point(3, 4))` in `EqualsHashCodeAdvanced.main`:

1. `visited.put(new Point(3, 4), "first visit")` stores an entry: `HashMap` calls `.hashCode()` on the key object to determine which internal bucket to place it in, then stores the key-value pair there.
2. `visited.get(new Point(3, 4))` constructs a **brand-new** `Point` object — a different reference from the one used in `put`, but with the same `x = 3, y = 4` fields.
3. `HashMap.get` first calls `.hashCode()` on this new key. Because `Point.hashCode()` is `Objects.hash(x, y)`, and both `Point` instances have identical `x` and `y` values, this new key's hash code is **identical** to the one computed during `put` — so `HashMap` looks in the exact same bucket.
4. Within that bucket, `HashMap` calls `.equals()` to confirm an exact match: `new Point(3,4).equals(the stored Point(3,4))` evaluates `this.x == other.x && this.y == other.y`, which is `3 == 3 && 4 == 4`, `true`.
5. Since both the hash code matched (found the right bucket) and `equals` matched (confirmed the right entry within that bucket), `HashMap.get` successfully returns `"first visit"` — even though the key object passed to `get` is a completely different instance from the one passed to `put`.
6. This only works because `hashCode` and `equals` are based on the *same* fields. If `Point` had the same bug as `BrokenPoint` — `hashCode` based on a field `equals` ignores, or vice versa — step 3 could compute a different hash code for the lookup, sending `HashMap.get` to search the wrong bucket entirely, silently returning `null` even though a "matching" entry does exist elsewhere in the map.

## 7. Gotchas & takeaways

> **Gotcha:** the contract is one-directional in an important sense — equal objects **must** have equal hash codes, but unequal objects are *allowed* to accidentally share a hash code (that's just a hash collision, which `equals` resolves correctly within the bucket). The dangerous violation is the other way: `equals` says two objects match, but `hashCode` disagrees.

- The equals/hashCode contract: if `a.equals(b)` is `true`, then `a.hashCode() == b.hashCode()` **must** also be true — violating this breaks `HashMap`, `HashSet`, and any hash-based collection in ways that don't show up as compile errors.
- Always override both methods together, based on the exact same set of fields — never override one without the other, and never include a field in one but not the other.
- `Objects.hash(field1, field2, ...)` and `Objects.equals(a, b)` (null-safe) are the standard, idiomatic building blocks for writing both methods by hand.
- Records generate a correct, consistent `equals`/`hashCode` pair automatically based on every component — see [record components & canonical constructor](0954-record-components-canonical-constructor.md) for how that generation works.
- Mutable fields used in `equals`/`hashCode` are risky: if an object's field changes after it's already been placed in a `HashSet`, its hash code can change too, and the set may never find it again to remove or check it — this is a strong argument for keeping fields used in equality immutable.
- Don't override `equals`/`hashCode` for identity-based classes (like a `Connection` or a `Thread`) where two instances should never be considered interchangeable just because some fields match.
