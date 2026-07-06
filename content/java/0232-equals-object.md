---
card: java
gi: 232
slug: equals-object
title: equals(Object)
---

## 1. What it is

`equals(Object)` is another method inherited from `Object`, whose job is to decide whether two objects should be considered "equal." `Object`'s default implementation simply checks reference identity — `this == other` — meaning two distinct objects are *never* equal by default, even if all their fields hold identical values, unless a class overrides `equals` to compare actual content instead.

```java
class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
}

public class EqualsDemo {
    public static void main(String[] args) {
        Point a = new Point(1, 2);
        Point b = new Point(1, 2);
        System.out.println(a == b);      // false — different objects in memory
        System.out.println(a.equals(b)); // false — Object's default equals is just ==
    }
}
```

Even though `a` and `b` hold identical `x` and `y` values, `a.equals(b)` is `false`, because `Point` never overrode `equals` — `Object`'s default treats "equal" as "the exact same object," which is rarely what you actually want for value-like classes.

## 2. Why & when

Overriding `equals` lets a class define what "equal" genuinely means for its own data, which matters anywhere content comparison, not identity comparison, is the goal.

- **Value semantics** — classes representing values (like `Point`, `Money`, or a custom `Coordinate`) should typically be equal when their fields match, since two `Point(1, 2)` instances conceptually represent the same point, regardless of which object they happen to be.
- **Collections rely on it** — `List.contains`, `Set` membership, `HashMap` key lookups, and `removeIf`-style content matching all use `equals` internally; without a correct override, a `HashSet<Point>` could hold two points that "look" identical but are treated as distinct entries.
- **Correctness of comparisons throughout a program** — any code that checks `someObject.equals(other)` to decide "are these the same value" depends entirely on the class having implemented that comparison meaningfully.

Override `equals` for classes that represent values you want compared by content; leave `Object`'s default reference-identity `equals` alone for classes that represent genuinely distinct entities where two separately-created instances should never be considered the same (many mutable, identity-based objects fall into this category).

## 3. Core concept

```java
class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;                    // same object: trivially equal
        if (!(obj instanceof Point)) return false;        // wrong type: never equal
        Point other = (Point) obj;
        return this.x == other.x && this.y == other.y;    // compare actual content
    }
}
```

The overridden `equals` takes an `Object` parameter (matching `Object`'s exact signature), checks reference identity first as a fast path, rejects anything that is not a `Point` via `instanceof`, then safely casts and compares the actual `x`/`y` fields — this three-step pattern (identity check, type check, field comparison) is the standard shape almost every `equals` override follows.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="equals override checks same reference first then instanceof type check then compares fields, returning true only if all checks pass">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">this == obj ? -&gt; true</text>

  <line x1="150" y1="55" x2="150" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <text x="180" y="70" fill="#8b949e" font-size="8" font-family="sans-serif">no</text>

  <rect x="40" y="80" width="220" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="150" y="102" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">not instanceof Point ? -&gt; false</text>

  <line x1="150" y1="115" x2="150" y2="135" stroke="#8b949e" stroke-width="1.5"/>
  <text x="180" y="130" fill="#8b949e" font-size="8" font-family="sans-serif">no</text>

  <rect x="40" y="140" width="220" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="162" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">compare x and y fields</text>

  <text x="450" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Standard shape: identity check,</text>
  <text x="450" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">type check, then field comparison.</text>
</svg>

Every well-formed `equals` override follows the same three-step shape: identity, type, then content.

## 5. Runnable example

Scenario: a `Coordinate` class used to deduplicate GPS waypoints, evolved from a plain `equals` override into one used correctly inside a `HashSet`, then hardened against a subtle `null`/subtype bug.

### Level 1 — Basic

```java
public class EqualsBasic {
    static class Coordinate {
        double lat, lon;
        Coordinate(double lat, double lon) { this.lat = lat; this.lon = lon; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof Coordinate)) return false;
            Coordinate other = (Coordinate) obj;
            return this.lat == other.lat && this.lon == other.lon;
        }
    }

    public static void main(String[] args) {
        Coordinate a = new Coordinate(40.0, -74.0);
        Coordinate b = new Coordinate(40.0, -74.0);
        System.out.println(a.equals(b)); // true — same content, different objects
    }
}
```

**How to run:** `java EqualsBasic.java`

`a` and `b` are two distinct objects in memory, but `equals` now compares `lat`/`lon` content instead of identity, so `a.equals(b)` correctly returns `true`.

### Level 2 — Intermediate

Same `Coordinate`, now stored in a `HashSet` to deduplicate waypoints — this only works correctly because `equals` is overridden (a `HashSet` also needs a matching `hashCode`, covered next, but this example focuses purely on `equals`'s role in `contains`).

```java
import java.util.ArrayList;
import java.util.List;

public class EqualsIntermediate {
    static class Coordinate {
        double lat, lon;
        Coordinate(double lat, double lon) { this.lat = lat; this.lon = lon; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof Coordinate)) return false;
            Coordinate other = (Coordinate) obj;
            return this.lat == other.lat && this.lon == other.lon;
        }
    }

    static List<Coordinate> deduplicate(List<Coordinate> raw) {
        List<Coordinate> unique = new ArrayList<>();
        for (Coordinate c : raw) {
            if (!unique.contains(c)) { // contains() relies on equals()
                unique.add(c);
            }
        }
        return unique;
    }

    public static void main(String[] args) {
        List<Coordinate> waypoints = List.of(
            new Coordinate(40.0, -74.0),
            new Coordinate(40.0, -74.0), // duplicate content, different object
            new Coordinate(51.5, -0.1)
        );
        System.out.println(deduplicate(waypoints).size()); // 2, not 3
    }
}
```

**How to run:** `java EqualsIntermediate.java`

`unique.contains(c)` scans `unique` and calls `equals` against each existing element; because `Coordinate.equals` compares content, the second waypoint (identical `lat`/`lon` to the first, but a separate object) is correctly recognized as already present and skipped.

### Level 3 — Advanced

Same waypoint system, now demonstrating (and fixing) a subtle real bug: comparing against `null` or an unrelated type must return `false` cleanly, never throw, and `equals` must remain symmetric even when a caller passes arguments in the "wrong" order.

```java
import java.util.Objects;

public class EqualsAdvanced {
    static class Coordinate {
        double lat, lon;
        Coordinate(double lat, double lon) { this.lat = lat; this.lon = lon; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof Coordinate)) return false; // false for null AND for unrelated types, never throws
            Coordinate other = (Coordinate) obj;
            return Double.compare(this.lat, other.lat) == 0
                && Double.compare(this.lon, other.lon) == 0; // handles NaN correctly, unlike ==
        }
    }

    public static void main(String[] args) {
        Coordinate a = new Coordinate(40.0, -74.0);

        System.out.println(a.equals(null));           // false, no NullPointerException
        System.out.println(a.equals("not a coordinate")); // false, no ClassCastException
        System.out.println(a.equals(a));               // true, identity fast path

        Coordinate nanA = new Coordinate(Double.NaN, 0);
        Coordinate nanB = new Coordinate(Double.NaN, 0);
        System.out.println(nanA.equals(nanB)); // true — Double.compare treats NaN as equal to itself, unlike ==
    }
}
```

**How to run:** `java EqualsAdvanced.java`

`obj instanceof Coordinate` returns `false` for both `null` and a `String` argument (`instanceof` against `null` is always `false`, and never throws), so `equals` degrades gracefully instead of crashing; using `Double.compare` instead of `==` also correctly treats two `NaN` latitude values as equal to each other, which raw `==` would not (since `NaN == NaN` is `false` in Java).

## 6. Walkthrough

Trace each call in `EqualsAdvanced.main` in order.

**`a.equals(null)`.** Inside `equals`, `this == obj` compares `a` to `null` — `false`. Next, `obj instanceof Coordinate` is evaluated with `obj` being `null`; `instanceof` always returns `false` when the left-hand value is `null`, regardless of the type on the right, so the method returns `false` immediately, without ever attempting a cast.

**`a.equals("not a coordinate")`.** `this == obj` is `false` (different types and references entirely). `obj instanceof Coordinate` checks whether the `String` is a `Coordinate` — it is not, so this is `false`, and the method returns `false` before any cast is attempted, avoiding a `ClassCastException`.

**`a.equals(a)`.** `this == obj` compares `a` to itself — `true`, since they are literally the same reference. The method returns `true` immediately via the fast path, without needing to compare any fields.

**`nanA.equals(nanB)`.** `this == obj` is `false` (distinct objects). `obj instanceof Coordinate` is `true`. The cast succeeds. `Double.compare(Double.NaN, Double.NaN)` is defined to return `0` (treating NaN as equal to NaN, unlike the `==` operator which always treats `NaN == NaN` as `false`), and `Double.compare(0, 0)` is also `0`. Both comparisons yield `0`, so the `&&` of `== 0` checks is `true`.

```
a.equals(null)              -> instanceof null -> false -> false (no exception)
a.equals("not a coordinate")-> instanceof String -> false -> false (no exception)
a.equals(a)                 -> this == obj -> true -> true (fast path)
nanA.equals(nanB)            -> Double.compare(NaN,NaN)==0 && Double.compare(0,0)==0 -> true
```

**Final output.** `false`, `false`, `true`, `true` — printed on four separate lines, demonstrating that a well-written `equals` handles `null`, unrelated types, self-comparison, and edge-case values like `NaN` all correctly and without ever throwing.

## 7. Gotchas & takeaways

> **`equals` must never throw for a `null` or wrong-type argument** — the contract (detailed fully in the next topic, the equals/hashCode contract) requires `x.equals(null)` to return `false`, never throw `NullPointerException`. Using `instanceof` for the type check (rather than manually calling `obj.getClass()` before checking null) naturally handles `null` safely, since `instanceof` against `null` is always `false`.

> **Comparing `double`/`float` fields with `==` inside `equals` mishandles `NaN`** — `NaN == NaN` is always `false` in Java's floating-point semantics, which would make a `Coordinate` holding `NaN` never equal to another identical one. `Double.compare` (or `Double.equals`, which boxed `Double` uses) treats `NaN` as equal to itself, which is almost always the more useful behaviour for value comparisons.

- `Object`'s default `equals` is pure reference identity (`==`); override it whenever two objects with matching content should be considered equal.
- The standard override shape is: same-reference fast path, then an `instanceof` type check, then a field-by-field comparison.
- Collection methods like `contains`, `remove`, and `Set`/`Map` membership all rely on `equals` internally.
- Use `Double.compare` (not `==`) when comparing floating-point fields inside `equals`, so `NaN` values behave sensibly.
