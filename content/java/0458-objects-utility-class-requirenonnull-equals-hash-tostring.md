---
card: java
gi: 458
slug: objects-utility-class-requirenonnull-equals-hash-tostring
title: Objects utility class (requireNonNull, equals, hash, toString)
---

## 1. What it is

`java.util.Objects`, added in Java 7, is a small final utility class of static, `null`-safe helper methods for the operations every class ends up needing: checking a value isn't `null` (`requireNonNull`), comparing two possibly-`null` references for equality (`equals`), combining several fields into one hash code (`hash`), and producing a safe string representation of a possibly-`null` object (`toString`). None of it is new capability — every one of these could be hand-written with an `if` check — but centralizing them removes a large source of repetitive, easy-to-get-wrong boilerplate from `equals`, `hashCode`, and constructor validation.

## 2. Why & when

Before `Objects`, validating a constructor argument meant writing `if (name == null) throw new NullPointerException("name must not be null");` by hand, every time, in every constructor and setter — tedious and easy to forget in one spot while remembering it in another. Overriding `equals` correctly required careful `null` checks on both sides of every field comparison (`a == null ? b == null : a.equals(b)`), and overriding `hashCode` meant hand-rolling a combination formula, historically something like `31 * result + (field == null ? 0 : field.hashCode())` repeated per field. `Objects` turns each of those patterns into a one-line call: `Objects.requireNonNull(name, "name")`, `Objects.equals(a, b)`, `Objects.hash(field1, field2, field3)`.

You reach for `Objects` constantly, in two main situations: **fail-fast constructor/parameter validation** (`requireNonNull` at the top of a constructor or public method, so a `null` is rejected immediately with a clear message rather than causing a confusing `NullPointerException` three calls later, deep inside unrelated code), and **implementing `equals`/`hashCode`/`toString`** by hand on any class that does not use a `record` (which auto-generates all three) or a code-generation tool like Lombok. Modern IDEs generate `equals`/`hashCode` overrides using exactly these `Objects` methods by default.

## 3. Core concept

```java
import java.util.Objects;

// Fail-fast validation -- throws NullPointerException with a clear message if null
String name = Objects.requireNonNull(rawName, "name must not be null");

// Null-safe equality: does NOT throw if either side is null
boolean same = Objects.equals(a, b); // true if both null, or a.equals(b)

// Combine several fields into one hash code -- null-safe per field
int hashCode = Objects.hash(field1, field2, field3);

// Null-safe toString: "null" instead of throwing NullPointerException
String text = Objects.toString(maybeNullObject, "<none>"); // fallback if null
```

Each method exists to replace one specific hand-written `null`-check pattern with a single, well-tested call.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Objects methods replace hand-written null-check patterns for validation, equality, hashing and string conversion">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#8b949e" font-size="11" font-family="sans-serif">Hand-written pattern</text>
  <text x="340" y="28" fill="#8b949e" font-size="11" font-family="sans-serif">Objects equivalent</text>

  <text x="20" y="55" fill="#e6edf3" font-size="10" font-family="monospace">if (x == null) throw new NPE(...)</text>
  <text x="340" y="55" fill="#6db33f" font-size="10" font-family="monospace">Objects.requireNonNull(x, msg)</text>

  <text x="20" y="85" fill="#e6edf3" font-size="10" font-family="monospace">a==null ? b==null : a.equals(b)</text>
  <text x="340" y="85" fill="#6db33f" font-size="10" font-family="monospace">Objects.equals(a, b)</text>

  <text x="20" y="115" fill="#e6edf3" font-size="10" font-family="monospace">31*result + (f==null?0:f.hashCode())</text>
  <text x="340" y="115" fill="#6db33f" font-size="10" font-family="monospace">Objects.hash(f1, f2, f3)</text>

  <text x="20" y="145" fill="#e6edf3" font-size="10" font-family="monospace">x == null ? "null" : x.toString()</text>
  <text x="340" y="145" fill="#6db33f" font-size="10" font-family="monospace">Objects.toString(x)</text>
</svg>

Every `Objects` method collapses one recurring `null`-check idiom into a single, safe call.

## 5. Runnable example

Scenario: a small `Point` value class — evolved from a constructor that rejects `null` inputs, through a hand-implemented `equals`/`hashCode` built from `Objects`, to a `Point` used correctly and safely inside a `HashSet`, proving the `equals`/`hashCode` contract holds.

### Level 1 — Basic

```java
import java.util.Objects;

public class ObjectsBasic {
    static class Point {
        final String label;
        Point(String label) {
            this.label = Objects.requireNonNull(label, "label must not be null");
        }
    }

    public static void main(String[] args) {
        Point origin = new Point("origin");
        System.out.println("Created point labeled: " + origin.label);

        try {
            new Point(null);
        } catch (NullPointerException e) {
            System.out.println("Rejected null label: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ObjectsBasic.java`

Expected output:
```
Created point labeled: origin
Rejected null label: label must not be null
```

`Objects.requireNonNull(label, "label must not be null")` either returns `label` unchanged (if non-null, so the field assignment proceeds normally) or throws `NullPointerException` immediately, with the given message — failing fast at the constructor boundary instead of letting a `null` slip in and cause a confusing failure later.

### Level 2 — Intermediate

```java
import java.util.Objects;

public class ObjectsEquality {
    static class Point {
        final int x, y;
        final String label; // may be null -- an unlabeled point is allowed

        Point(int x, int y, String label) {
            this.x = x;
            this.y = y;
            this.label = label; // no requireNonNull here -- null IS a valid label
        }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;
            if (!(other instanceof Point)) return false;
            Point that = (Point) other;
            return this.x == that.x
                    && this.y == that.y
                    && Objects.equals(this.label, that.label); // null-safe: handles either label being null
        }

        @Override
        public int hashCode() {
            return Objects.hash(x, y, label); // null-safe per field, combines all three
        }

        @Override
        public String toString() {
            return "Point(" + x + ", " + y + ", " + Objects.toString(label, "<unlabeled>") + ")";
        }
    }

    public static void main(String[] args) {
        Point a = new Point(1, 2, null);
        Point b = new Point(1, 2, null);
        Point c = new Point(1, 2, "home");

        System.out.println("a.equals(b): " + a.equals(b));       // both have null label
        System.out.println("a.equals(c): " + a.equals(c));       // different label
        System.out.println("a.hashCode() == b.hashCode(): " + (a.hashCode() == b.hashCode()));
        System.out.println(a + " / " + c);
    }
}
```

**How to run:** `java ObjectsEquality.java`

Expected output:
```
a.equals(b): true
a.equals(c): false
a.hashCode() == b.hashCode(): true
Point(1, 2, <unlabeled>) / Point(1, 2, home)
```

The real-world concern added here: `label` is allowed to be `null` (an unlabeled point is valid), so `equals` cannot safely call `this.label.equals(that.label)` directly — that would throw if `this.label` is `null`. `Objects.equals` handles that case for free: it returns `true` if both arguments are `null`, `false` if only one is, and otherwise delegates to `.equals()`. `Objects.hash` does the equivalent null-safe work for hashing every field in one call.

### Level 3 — Advanced

```java
import java.util.*;

public class ObjectsInSet {
    static class Point {
        final int x, y;
        final String label;

        Point(int x, int y, String label) {
            this.x = x;
            this.y = y;
            this.label = label;
        }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;
            if (!(other instanceof Point)) return false;
            Point that = (Point) other;
            return this.x == that.x && this.y == that.y && Objects.equals(this.label, that.label);
        }

        @Override
        public int hashCode() {
            return Objects.hash(x, y, label);
        }

        @Override
        public String toString() {
            return "Point(" + x + "," + y + "," + Objects.toString(label, "-") + ")";
        }
    }

    public static void main(String[] args) {
        Set<Point> visited = new HashSet<>();

        Point p1 = new Point(0, 0, null);
        Point p2 = new Point(0, 0, null);   // equal to p1 -- same x, y, and null label
        Point p3 = new Point(1, 1, "flag"); // distinct point

        visited.add(p1);
        visited.add(p2); // duplicate of p1 by equals/hashCode -- HashSet must NOT store it twice
        visited.add(p3);

        System.out.println("Distinct points visited: " + visited.size());
        System.out.println("Set contains a point equal to p1: " + visited.contains(new Point(0, 0, null)));
        System.out.println(visited.contains(p3));
    }
}
```

**How to run:** `java ObjectsInSet.java`

Expected output:
```
Distinct points visited: 2
Set contains a point equal to p1: true
true
```

This is where the `equals`/`hashCode` contract actually matters in production code: `HashSet` relies on `hashCode()` to pick a bucket and `equals()` to detect duplicates within that bucket. Because `Point.hashCode()` and `Point.equals()` are both built from the exact same fields via `Objects.hash` and `Objects.equals`, two `Point` instances with identical `x`, `y`, and `label` are guaranteed to land in the same bucket **and** compare equal — so `p2` is correctly rejected as a duplicate of `p1`, and a freshly constructed `Point(0, 0, null)` is found in the set even though it is not the same object as `p1`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `HashSet<Point> visited` is created empty.

`visited.add(p1)` inserts `Point(0,0,null)`. Internally, `HashSet` calls `p1.hashCode()`, which runs `Objects.hash(x, y, label)` — combining `0`, `0`, and `null` (Java's `Objects.hash` treats a `null` element as contributing `0` to the combination, the same null-safe behavior `Objects.equals` provides for a single value) into one `int`. That hash picks a bucket, and since the set is empty, `p1` is stored directly.

`visited.add(p2)` inserts `Point(0,0,null)` again, a **different object** with identical field values. `p2.hashCode()` computes the exact same combination as `p1.hashCode()` (same `x`, `y`, `label` values in, same result out), so `HashSet` looks in the same bucket it used for `p1`. Finding an existing entry there, it calls `p1.equals(p2)` to check for a true duplicate: `x` matches, `y` matches, and `Objects.equals(this.label, that.label)` compares `null` to `null` and returns `true` without dereferencing either — so `equals` returns `true` overall, and `HashSet` discards `p2` as a duplicate rather than adding a second entry.

`visited.add(p3)` inserts `Point(1,1,"flag")`. Its hash differs from `p1`'s (different `x`, `y`, and `label`), so it lands in a different bucket and is stored as a new entry — bringing the set's size to 2, not 3.

```
add(p1)  --> bucket(hash 0,0,null)      --> empty  --> stored
add(p2)  --> bucket(hash 0,0,null)      --> p1 there, equals()==true --> discarded (duplicate)
add(p3)  --> bucket(hash 1,1,"flag")    --> empty  --> stored
```

`visited.contains(new Point(0, 0, null))` builds a brand-new `Point` that was never added to the set, computes its hash the same way, finds `p1` in that bucket, confirms equality, and returns `true` — proving that `equals`/`hashCode` built consistently from `Objects.equals`/`Objects.hash` let `HashSet` recognize value-equal objects it has never seen as the same object it already stored.

## 7. Gotchas & takeaways

> `equals()` and `hashCode()` must always be overridden **together**, using the exact same set of fields in both. If two objects are `equals()`-equal but have different `hashCode()` values, `HashSet`/`HashMap` will fail to recognize them as duplicates — they can end up in different buckets and never get compared with `equals()` at all. `Objects.hash(...)` and `Objects.equals(...)` built from the same field list, as in the example above, is the easiest way to guarantee this stays in sync.

- `Objects.requireNonNull(value, message)` is the standard, one-line way to fail fast on a `null` argument — put it at the top of constructors and public methods, not buried deep where the resulting `NullPointerException` would be confusing.
- `Objects.equals(a, b)` never throws on `null` — use it instead of `a.equals(b)` whenever `a` (or `b`) might legitimately be `null`.
- `Objects.hash(fields...)` combines any number of fields into one hash code, handling `null` fields safely — this is what most IDE-generated `hashCode()` overrides produce.
- `Objects.toString(value, fallback)` avoids a `NullPointerException` from calling `.toString()` on a `null` reference, substituting the fallback string instead.
- On classes where every field participates in identity (immutable value types), consider a `record` instead — it generates `equals`, `hashCode`, and `toString` (all built the same way `Objects` methods would) automatically, with no boilerplate at all.
