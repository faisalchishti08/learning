---
card: java
gi: 234
slug: equals-hashcode-contract
title: equals/hashCode contract
---

## 1. What it is

The equals/hashCode contract is a small set of rules, documented directly on `Object`, that any override of `equals()` and `hashCode()` (the previous two topics) must obey for hash-based collections and general object comparisons to work correctly. The core rules are: `equals` must be reflexive (`x.equals(x)` is always `true`), symmetric (`x.equals(y)` equals `y.equals(x)`), transitive (if `x.equals(y)` and `y.equals(z)`, then `x.equals(z)`), consistent (repeated calls return the same result, given no changes), and `x.equals(null)` is always `false` — and critically, if `x.equals(y)` is `true`, then `x.hashCode()` must equal `y.hashCode()`.

```java
import java.util.Objects;

class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (!(obj instanceof Point)) return false;
        Point other = (Point) obj;
        return this.x == other.x && this.y == other.y;
    }

    @Override
    public int hashCode() { return Objects.hash(x, y); }
}
```

This `Point` satisfies the contract: `equals` compares content symmetrically and consistently, returns `false` for `null` safely via `instanceof`, and `hashCode` is derived from the exact same fields `equals` compares — meeting every rule the contract requires simultaneously.

## 2. Why & when

The contract exists because `equals` and `hashCode` are not independent methods you can implement however you like — collections, frameworks, and other code throughout the JDK assume the contract holds and will misbehave, sometimes silently, if it doesn't.

- **Symmetry failures break comparisons in surprising directions** — if `a.equals(b)` is `true` but `b.equals(a)` is `false` (a classic bug when comparing a subclass against a superclass, discussed further in the gotchas), code that happens to call `equals` in one order works while the same logical comparison in the other order fails.
- **Transitivity failures cause inconsistent grouping** — if `a` equals `b`, and `b` equals `c`, but `a` does not equal `c`, then whether two objects are considered "the same" depends on which third object happens to be compared, which corrupts sorting, deduplication, and set membership in ways that are hard to trace back to the root cause.
- **The `equals`/`hashCode` link is what `HashMap` and `HashSet` are built on** — as the previous topic showed concretely, violating "equal objects must have equal hash codes" causes lookups to silently fail to find entries that are logically present.

You need to actively think about this contract any time you write a custom `equals`/`hashCode` pair, especially in class hierarchies (where a subclass adds fields) or with mutable objects (where fields used in `equals`/`hashCode` can change after the object is already stored in a hash-based collection).

## 3. Core concept

```java
class Money {
    long cents;
    Money(long cents) { this.cents = cents; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false; // getClass(), not instanceof
        return this.cents == ((Money) obj).cents;
    }

    @Override
    public int hashCode() { return Long.hashCode(cents); }
}
```

Using `getClass() != obj.getClass()` instead of `!(obj instanceof Money)` is a deliberate choice that matters specifically for transitivity in class hierarchies: it ensures a `Money` and any future subclass of `Money` (say, `DiscountedMoney`) are never accidentally considered equal to plain `Money` objects in an asymmetric way, keeping the whole hierarchy's `equals` behaviour transitive and symmetric.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The five contract rules: reflexive, symmetric, transitive, consistent, and null returns false, plus the link that equal objects must share a hash code">
  <rect x="8" y="8" width="584" height="184" rx="8" fill="#0d1117"/>

  <rect x="20" y="20" width="170" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">reflexive: x.equals(x)</text>

  <rect x="205" y="20" width="170" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">symmetric: x~y == y~x</text>

  <rect x="390" y="20" width="190" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">transitive: x~y &amp; y~z -&gt; x~z</text>

  <rect x="20" y="65" width="170" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="85" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">consistent: stable results</text>

  <rect x="205" y="65" width="170" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="85" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">x.equals(null) == false</text>

  <rect x="140" y="115" width="320" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="137" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">x.equals(y) true -&gt; x.hashCode()==y.hashCode()</text>

  <text x="300" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">All five equals rules plus the hashCode link must hold together for collections to behave correctly.</text>
</svg>

The contract is five rules for `equals` plus one crucial link tying `equals` to `hashCode`.

## 5. Runnable example

Scenario: a `Point2D`/`Point3D` class pair that starts by naively violating symmetry and transitivity via subclassing, then is fixed step by step to satisfy the full contract.

### Level 1 — Basic

```java
public class ContractBasic {
    static class Point2D {
        int x, y;
        Point2D(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object obj) {
            if (!(obj instanceof Point2D)) return false; // instanceof: also true for Point3D subclass!
            Point2D p = (Point2D) obj;
            return this.x == p.x && this.y == p.y;
        }
    }

    static class Point3D extends Point2D {
        int z;
        Point3D(int x, int y, int z) { super(x, y); this.z = z; }

        @Override
        public boolean equals(Object obj) {
            if (!(obj instanceof Point3D)) return false;
            Point3D p = (Point3D) obj;
            return this.x == p.x && this.y == p.y && this.z == p.z;
        }
    }

    public static void main(String[] args) {
        Point2D twoD = new Point2D(1, 2);
        Point3D threeD = new Point3D(1, 2, 9);

        System.out.println(twoD.equals(threeD));   // true! Point2D.equals only checks x,y — ignores z
        System.out.println(threeD.equals(twoD));   // false — Point3D.equals requires instanceof Point3D
    }
}
```

**How to run:** `java ContractBasic.java`

`twoD.equals(threeD)` is `true` (it only ever checks `x`/`y`, and `threeD` is-a `Point2D` too, so `instanceof Point2D` passes), but `threeD.equals(twoD)` is `false` (`twoD` is not a `Point3D`) — this is a direct symmetry violation: `x.equals(y) != y.equals(x)`.

### Level 2 — Intermediate

Same classes, now fixed to use `getClass()` instead of `instanceof`, restoring symmetry — at the cost of `Point2D` and `Point3D` never being considered equal to each other at all, which is the standard, contract-safe tradeoff.

```java
import java.util.Objects;

public class ContractIntermediate {
    static class Point2D {
        int x, y;
        Point2D(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null || getClass() != obj.getClass()) return false; // exact class match required
            Point2D p = (Point2D) obj;
            return this.x == p.x && this.y == p.y;
        }

        @Override
        public int hashCode() { return Objects.hash(x, y); }
    }

    static class Point3D extends Point2D {
        int z;
        Point3D(int x, int y, int z) { super(x, y); this.z = z; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null || getClass() != obj.getClass()) return false;
            Point3D p = (Point3D) obj;
            return this.x == p.x && this.y == p.y && this.z == p.z;
        }

        @Override
        public int hashCode() { return Objects.hash(x, y, z); }
    }

    public static void main(String[] args) {
        Point2D twoD = new Point2D(1, 2);
        Point3D threeD = new Point3D(1, 2, 9);

        System.out.println(twoD.equals(threeD)); // false now — different classes
        System.out.println(threeD.equals(twoD)); // false — symmetric with the line above
    }
}
```

**How to run:** `java ContractIntermediate.java`

`getClass() != obj.getClass()` requires the exact runtime class to match (`Point2D.class` is never equal to `Point3D.class`), so both directions of the comparison now consistently return `false` — symmetry is restored, at the cost of accepting that a `Point2D` and a `Point3D` are simply never equal, even when one's `x`/`y` matches the other's.

### Level 3 — Advanced

Same fixed classes, now demonstrating consistency and the hashCode link together inside a `HashSet`, plus a check that reflexivity and the `null` rule both hold as the contract requires.

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public class ContractAdvanced {
    static class Point2D {
        final int x, y; // final: fields cannot change after construction, guaranteeing consistency
        Point2D(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null || getClass() != obj.getClass()) return false;
            Point2D p = (Point2D) obj;
            return this.x == p.x && this.y == p.y;
        }

        @Override
        public int hashCode() { return Objects.hash(x, y); }
    }

    public static void main(String[] args) {
        Point2D p1 = new Point2D(1, 2);

        System.out.println(p1.equals(p1));       // true — reflexive
        System.out.println(p1.equals(null));      // false — required by contract, no exception

        Set<Point2D> seen = new HashSet<>();
        seen.add(new Point2D(1, 2));
        seen.add(new Point2D(1, 2)); // logically equal, different instance
        seen.add(new Point2D(3, 4));
        System.out.println(seen.size()); // 2, not 3 — the duplicate is correctly rejected

        // consistency: repeated calls with unchanged fields always agree
        Point2D p2 = new Point2D(1, 2);
        System.out.println(p1.equals(p2) == p1.equals(p2)); // true, trivially, but demonstrates stability
    }
}
```

**How to run:** `java ContractAdvanced.java`

Making `x` and `y` `final` guarantees consistency by construction: since the fields can never change after the object is created, `equals` and `hashCode` can never produce a different answer for the same pair of objects across repeated calls — a `HashSet` can safely rely on an object's hash code staying the same for as long as it remains stored.

## 6. Walkthrough

Trace the `HashSet` operations in `ContractAdvanced.main`.

**`seen.add(new Point2D(1, 2))` (first time).** A new `Point2D` is created with `x=1, y=2`. `HashSet.add` computes its `hashCode()`, which is `Objects.hash(1, 2)` — call this `H`. No existing entry occupies that bucket, so the object is inserted. `seen` now has one element.

**`seen.add(new Point2D(1, 2))` (second time).** A *different* `Point2D` object is created, also with `x=1, y=2`. `HashSet.add` computes its `hashCode()` — since `hashCode` is derived only from `x` and `y`, this is again exactly `H` (the same value as before). The set looks in the bucket for `H`, finds the previously stored `Point2D(1,2)`, and calls `equals()` to confirm: `getClass()` matches (`Point2D.class == Point2D.class`), `x==x` and `y==y` both `true`, so `equals` returns `true`. The set recognizes this as a duplicate and does **not** add it. `seen` still has one element.

**`seen.add(new Point2D(3, 4))`.** `hashCode()` is `Objects.hash(3, 4)`, some different value from `H` (almost certainly, given different input fields). This lands in a different bucket with no existing matching entry, so it is inserted as a new element. `seen` now has two elements.

**`seen.size()`.** Returns `2` — the two logically distinct points (`(1,2)` and `(3,4)`), with the duplicate `(1,2)` correctly collapsed into one entry.

```
add(Point2D(1,2)) #1 -> hashCode=H -> bucket H empty -> inserted        (size=1)
add(Point2D(1,2)) #2 -> hashCode=H -> bucket H has entry -> equals()=true -> rejected as duplicate (size=1)
add(Point2D(3,4))     -> hashCode=H2 (different) -> bucket H2 empty -> inserted (size=2)
```

**Final output.** `true` (reflexive), `false` (null-safe), `2` (deduplication via the contract working correctly), `true` (consistency demonstration) — four lines confirming every rule of the contract holds for this `Point2D` implementation.

## 7. Gotchas & takeaways

> **Using `instanceof` in `equals` inside a class hierarchy risks breaking symmetry**, exactly as `ContractBasic` demonstrated: a subclass instance can satisfy a superclass's `instanceof` check (making the superclass's `equals` return `true`) while the reverse comparison, using the subclass's stricter `equals`, returns `false`. Using `getClass() != obj.getClass()` instead avoids this at the cost of superclass and subclass instances never being equal to each other — the standard, safe tradeoff (favor composition over inheritance for value classes when this matters, an idea explored more in later design topics).

> **Mutable fields used in `equals`/`hashCode` can silently break a `HashSet`/`HashMap` if changed after insertion** — if an object's hash code changes while it is stored in a hash-based collection, the collection may search the wrong (now-stale) bucket and fail to find or remove the very entry it is holding, effectively "losing" it. Preferring `final` fields for anything included in `equals`/`hashCode`, as this topic's Level 3 does, sidesteps the problem entirely.

- The contract requires `equals` to be reflexive, symmetric, transitive, consistent, and to return `false` (never throw) for `null`.
- The crucial link: if `x.equals(y)` is `true`, then `x.hashCode()` must equal `y.hashCode()` — violating this breaks `HashMap`/`HashSet` lookups.
- Prefer `getClass() != obj.getClass()` over `instanceof` inside `equals` when working within a class hierarchy, to avoid symmetry violations between superclass and subclass instances.
- Fields used by `equals`/`hashCode` should ideally be `final`, so an object's hash code and equality behaviour never change after it has been stored in a hash-based collection.
