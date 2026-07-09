---
card: java
gi: 667
slug: records-preview
title: Records (preview)
---

## 1. What it is

**Records**, introduced as a **preview feature** (JEP 359) in **Java 14**, are a compact way to declare a class whose entire purpose is to hold immutable data. Writing `record Point(int x, int y) {}` generates, automatically, everything you'd otherwise hand-write for a data carrier: private final fields for `x` and `y`, a canonical constructor that assigns them, public accessor methods (named `x()` and `y()`, not `getX()`/`getY()`), and correct `equals()`, `hashCode()`, and `toString()` implementations based on all the components. Records are implicitly `final` (can't be subclassed) and their fields are implicitly `final` (truly immutable once constructed) — the whole feature is designed around the idea that a record's identity *is* its data: two records with equal component values are `equals()`, full stop.

## 2. Why & when

Before records, a simple immutable data class like `Point` required 15-30 lines of boilerplate: a constructor, getters, `equals()`, `hashCode()`, `toString()` — all mechanically derivable from the field list, yet all requiring you to write (or generate via your IDE) and then maintain by hand whenever a field was added or removed. This boilerplate obscured intent (is this really "just data," or does it have real behavior?) and was a common source of subtle bugs (an `equals()` that forgot a field, a `hashCode()` inconsistent with `equals()`). Records make the "this class is purely a transparent carrier for these values" intent explicit and let the compiler generate the mechanical parts correctly, every time. Reach for a record whenever you're modeling a plain data aggregate — a coordinate pair, a range, a DTO returned from a method, a key in a map — and reach for a regular `class` when you need mutable state, inheritance, or when the "data" is really an implementation detail behind meaningful behavior.

## 3. Core concept

```java
// Before records: significant boilerplate for one simple idea
final class PointOld {
    private final int x, y;
    PointOld(int x, int y) { this.x = x; this.y = y; }
    int x() { return x; }
    int y() { return y; }
    @Override public boolean equals(Object o) {
        if (!(o instanceof PointOld)) return false;
        PointOld p = (PointOld) o;
        return x == p.x && y == p.y;
    }
    @Override public int hashCode() { return Objects.hash(x, y); }
    @Override public String toString() { return "PointOld[x=" + x + ", y=" + y + "]"; }
}

// With records (Java 14 preview): one line does all of the above
record Point(int x, int y) {}
```

`Point` gets `x()`, `y()`, a constructor `Point(int x, int y)`, `equals()`, `hashCode()`, and `toString()` — all generated from the single component list `(int x, int y)`.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A one-line record declaration expands into a constructor, accessors, equals, hashCode, and toString">
  <rect x="10" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="100" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">record Point(int x, int y) {}</text>

  <line x1="190" y1="95" x2="240" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#rc1)"/>
  <text x="215" y="85" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">compiler generates</text>

  <rect x="250" y="10" width="360" height="170" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="270" y="35" fill="#e6edf3" font-size="10" font-family="monospace">private final int x, y;</text>
  <text x="270" y="55" fill="#e6edf3" font-size="10" font-family="monospace">Point(int x, int y) { ... }</text>
  <text x="270" y="75" fill="#e6edf3" font-size="10" font-family="monospace">int x() { return x; }</text>
  <text x="270" y="95" fill="#e6edf3" font-size="10" font-family="monospace">int y() { return y; }</text>
  <text x="270" y="115" fill="#e6edf3" font-size="10" font-family="monospace">boolean equals(Object o) { ... }</text>
  <text x="270" y="135" fill="#e6edf3" font-size="10" font-family="monospace">int hashCode() { ... }</text>
  <text x="270" y="155" fill="#e6edf3" font-size="10" font-family="monospace">String toString() { ... }</text>

  <defs><marker id="rc1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

One declaration, all the mechanical parts generated consistently and correctly from the component list.

## 5. Runnable example

Scenario: modeling a 2D point used as a map key and compared for equality — first the manual pre-record version to see the boilerplate, then the equivalent record, then extending the record with a compact canonical constructor for validation and an additional derived method, showing records can still carry behavior beyond pure data.

### Level 1 — Basic

```java
// File: PointManual.java
import java.util.Objects;
import java.util.HashSet;
import java.util.Set;

public class PointManual {
    static final class Point {
        private final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        int x() { return x; }
        int y() { return y; }
        @Override public boolean equals(Object o) {
            if (!(o instanceof Point)) return false;
            Point p = (Point) o;
            return x == p.x && y == p.y;
        }
        @Override public int hashCode() { return Objects.hash(x, y); }
        @Override public String toString() { return "Point[x=" + x + ", y=" + y + "]"; }
    }

    public static void main(String[] args) {
        Point a = new Point(1, 2);
        Point b = new Point(1, 2);
        System.out.println(a);
        System.out.println("a.equals(b): " + a.equals(b));

        Set<Point> points = new HashSet<>();
        points.add(a);
        points.add(b);
        System.out.println("Set size (should dedupe): " + points.size());
    }
}
```

**How to run:** `java PointManual.java`

Expected output:
```
Point[x=1, y=2]
a.equals(b): true
Set size (should dedupe): 1
```

### Level 2 — Intermediate

```java
// File: PointRecord.java
import java.util.HashSet;
import java.util.Set;

public class PointRecord {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        Point a = new Point(1, 2);
        Point b = new Point(1, 2);
        System.out.println(a);
        System.out.println("a.equals(b): " + a.equals(b));

        Set<Point> points = new HashSet<>();
        points.add(a);
        points.add(b);
        System.out.println("Set size (should dedupe): " + points.size());

        System.out.println("a.x() = " + a.x() + ", a.y() = " + a.y());
    }
}
```

**How to run:** requires the preview flag since records are a Java 14 preview feature:
```
javac --release 14 --enable-preview PointRecord.java
java --enable-preview PointRecord
```
(On modern JDKs 16+, records are permanent and no preview flag is needed.)

Expected output is functionally identical to Level 1's:
```
Point[x=1, y=2]
a.equals(b): true
Set size (should dedupe): 1
a.x() = 1, a.y() = 2
```

One line — `record Point(int x, int y) {}` — replaced the entire manual `Point` class from Level 1, with identical `equals()`/`hashCode()`/`toString()` behavior generated automatically.

### Level 3 — Advanced

```java
// File: PointValidated.java
public class PointValidated {
    record Point(int x, int y) {
        // Compact canonical constructor: validates before the implicit field assignment.
        Point {
            if (x < -1000 || x > 1000 || y < -1000 || y > 1000) {
                throw new IllegalArgumentException("Point out of bounds: (" + x + ", " + y + ")");
            }
        }

        // Records can still declare additional methods beyond the generated ones.
        double distanceFromOrigin() {
            return Math.sqrt((double) x * x + (double) y * y);
        }

        static Point origin() {
            return new Point(0, 0);
        }
    }

    public static void main(String[] args) {
        Point p1 = new Point(3, 4);
        System.out.println(p1 + " distance from origin: " + p1.distanceFromOrigin());

        Point origin = Point.origin();
        System.out.println(origin + " distance from origin: " + origin.distanceFromOrigin());

        try {
            new Point(5000, 0);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac --release 14 --enable-preview PointValidated.java && java --enable-preview PointValidated`

Expected output:
```
Point[x=3, y=4] distance from origin: 5.0
Point[x=0, y=0] distance from origin: 0.0
Rejected: Point out of bounds: (5000, 0)
```

Level 3 shows a record can have a **compact canonical constructor** (`Point { ... }`, no parameter list repeated) that runs validation logic *before* the implicit field assignments happen, plus additional instance and static methods (`distanceFromOrigin()`, `origin()`) — proving records aren't limited to pure data-with-no-behavior, they're just data-centric by default with generated boilerplate you can supplement.

## 6. Walkthrough

1. `main` calls `new Point(3, 4)`. Because `Point` declares a **compact canonical constructor** (`Point { ... }` with no explicit parameter list or field assignments), the compiler inserts this validation code to run *first*, before the implicit `this.x = x; this.y = y;` assignments that a compact constructor always performs afterward.
2. Inside the compact constructor, `x < -1000 || x > 1000 || y < -1000 || y > 1000` checks `3 < -1000` (false), `3 > 1000` (false), `4 < -1000` (false), `4 > 1000` (false) — the whole condition is `false`, so no exception is thrown, and the compiler-generated field assignments proceed, setting the record's `x` field to `3` and `y` field to `4`.
3. `p1 + " distance from origin: " + p1.distanceFromOrigin()` first implicitly calls `p1.toString()` (the compiler-generated one, producing `"Point[x=3, y=4]"`), then calls `distanceFromOrigin()`, a hand-written instance method that computes `Math.sqrt(3*3 + 4*4)` = `Math.sqrt(25)` = `5.0` — this method reads the record's `x` and `y` fields directly, since methods declared inside a record body have the same access to its private final fields as any instance method would.
4. `System.out.println` prints the concatenated string, `"Point[x=3, y=4] distance from origin: 5.0"`.
5. `Point.origin()` is called next — a `static` factory method declared inside the record, unrelated to the record's generated instance methods, simply returning `new Point(0, 0)`. This goes through the same compact constructor validation (`0` is within bounds), producing an origin point whose `distanceFromOrigin()` naturally computes to `0.0`.
6. Finally, `new Point(5000, 0)` is attempted inside a `try` block. This time, in the compact constructor, `x > 1000` evaluates `5000 > 1000` as `true`, so the whole condition is `true`, and `throw new IllegalArgumentException(...)` executes — critically, **before** any field assignment happens, so no partially-constructed or invalid `Point` object is ever created or returned. The `catch` block in `main` catches this and prints the rejection message.

```
new Point(3, 4) ──► compact constructor validates (3,4 in bounds) ──► implicit x=3, y=4 assigned ──► Point ready
new Point(5000, 0) ──► compact constructor validates (5000 out of bounds) ──► throws ──► no Point ever created
```

## 7. Gotchas & takeaways

> This is a **preview feature** in Java 14 — it requires `--enable-preview` on both `javac` and `java`. The finalized version (Java 16) is largely the same, but preview-era code should be re-verified against the final specification rather than assumed identical; some record-related capabilities (like records implementing interfaces, or being used in pattern matching) arrived incrementally across later JDK releases even after records themselves became permanent.

- A record's accessors are named after the component (`x()`, not `getX()`) — this is a deliberate departure from JavaBeans getter naming, reinforcing that records are a distinct concept, not just "beans with less typing."
- Records are implicitly `final` — you cannot extend a record with another class, and a record cannot extend any class other than the implicit `Record` superclass (though it can implement interfaces).
- `equals()`/`hashCode()` are generated from **all** components — you can't select a subset without dropping to a full explicit implementation, which record syntax still permits if truly needed.
- A compact canonical constructor (`Point { ... }`, no parameter list) is the idiomatic place for validation or normalization logic — it runs before field assignment, letting you reject invalid states at construction time.
- Records can still declare additional instance methods, static methods, and static fields — the generated pieces (constructor, accessors, `equals`/`hashCode`/`toString`) are a baseline you can build on, not a restriction to pure data with zero behavior.
