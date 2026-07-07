---
card: java
gi: 376
slug: override
title: '@Override'
---

## 1. What it is

`@Override` is a built-in annotation you place directly above a method to declare "this method is meant to override (or implement) a method inherited from a superclass or interface." The compiler checks that claim: if no matching method actually exists in any supertype, compilation fails immediately. It applies to overriding an inherited method, and also to implementing an abstract method from an interface or abstract class — both count as "overriding" for this annotation's purposes.

## 2. Why & when

The single most common source of "override" bugs is an accidental **overload** instead of an override — the new method's name or parameter types don't exactly match the superclass method's, so Java treats it as a brand new, unrelated method rather than a replacement for the old one. This happens easily with the trio of methods every class inherits from `Object`: `equals(Object)`, `hashCode()`, and `toString()`. Writing `equals(MyClass other)` instead of `equals(Object other)` is a classic mistake — it looks right, compiles fine, and creates a second `equals` method that most of Java's standard library (which always calls `equals(Object)`) will never actually use.

Always add `@Override` whenever you intend to override or implement an inherited method. It costs nothing when the override is correct, and it converts an entire category of silent, easy-to-miss bugs into precise, immediate compile errors.

## 3. Core concept

```java
import java.util.Objects;

public class OverrideEqualsDemo {
    static class Point {
        int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object other) { // MUST be Object, not Point, to really override
            if (!(other instanceof Point p)) return false;
            return x == p.x && y == p.y;
        }

        @Override
        public int hashCode() {
            return Objects.hash(x, y);
        }
    }

    public static void main(String[] args) {
        Point a = new Point(1, 2);
        Point b = new Point(1, 2);
        System.out.println(a.equals(b)); // true: real equals(Object) override is used
    }
}
```

**How to run:** `java OverrideEqualsDemo.java`

`equals(Object other)` is annotated `@Override` and correctly matches `Object.equals(Object)`'s exact signature — the compiler confirms this. `a.equals(b)` calls this real override, comparing `x` and `y`, and correctly returns `true`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="equals(Point) is a distinct overload from equals(Object), so @Override on the wrong signature is rejected by the compiler, exposing the mistake immediately">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="55" fill="#6db33f" font-size="10" text-anchor="middle">Object.equals(Object other)</text>

  <rect x="350" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="55" fill="#6db33f" font-size="10" text-anchor="middle">Point.equals(Object other) -- real override</text>
  <line x1="290" y1="50" x2="345" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ok)"/>

  <rect x="350" y="90" width="260" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="480" y="115" fill="#f85149" font-size="10" text-anchor="middle">Point.equals(Point other) -- different overload!</text>

  <text x="20" y="150" fill="#f85149" font-size="10">@Override on equals(Point) is a compile error -- it doesn't match ANY Object method, exposing the mistake.</text>

  <defs><marker id="ok" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

## 5. Runnable example

Scenario: putting `Point` objects into a `HashSet` for deduplication, evolved from a version with the classic `equals(Point)` overload bug, to the same bug caught immediately by adding `@Override`, to a fully correct version that deduplicates as intended.

### Level 1 — Basic

```java
import java.util.HashSet;
import java.util.Set;

public class PointOverloadBug {
    static class Point {
        int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }

        // NO @Override -- and the parameter type is wrong: this is an overload, not an override
        public boolean equals(Point other) {
            return x == other.x && y == other.y;
        }
        // hashCode() not overridden either -- HashSet can't group equal points together
    }

    public static void main(String[] args) {
        Set<Point> points = new HashSet<>();
        points.add(new Point(1, 1));
        points.add(new Point(1, 1)); // "same" point, but HashSet doesn't know that

        System.out.println("Size: " + points.size()); // expected 1, but prints 2
    }
}
```

**How to run:** `java PointOverloadBug.java`

`equals(Point other)` never actually overrides `Object.equals(Object)` — `HashSet` internally calls `equals(Object)` (and `hashCode()`) on its elements, never this unrelated `equals(Point)` overload, so it treats the two `Point(1, 1)` instances as completely distinct objects. `Size: 2` is printed instead of the intended `1` — a silent correctness bug.

### Level 2 — Intermediate

```java
public class PointOverrideCaughtByCompiler {
    static class Point {
        int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }

        @Override // now marked -- the compiler will check this
        public boolean equals(Point other) { // still the WRONG parameter type
            return x == other.x && y == other.y;
        }
    }

    public static void main(String[] args) {
        System.out.println("If this compiled, @Override would have caught the bug above.");
    }
}
```

**How to run:** `javac PointOverrideCaughtByCompiler.java` (deliberately fails to compile)

Simply adding `@Override` above the exact same buggy signature from Level 1 turns the silent correctness bug into an immediate compile error: `method does not override or implement a method from a supertype`, because `equals(Point)` still doesn't match `Object.equals(Object)`. This is the annotation doing its job — catching the mistake before the program can even run.

### Level 3 — Advanced

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public class PointOverrideFixed {
    static class Point {
        int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object other) { // correct signature -- really overrides Object.equals
            if (!(other instanceof Point p)) return false;
            return x == p.x && y == p.y;
        }

        @Override
        public int hashCode() { // must also override this to keep the equals/hashCode contract
            return Objects.hash(x, y);
        }
    }

    public static void main(String[] args) {
        Set<Point> points = new HashSet<>();
        points.add(new Point(1, 1));
        points.add(new Point(1, 1)); // now correctly recognised as equal

        System.out.println("Size: " + points.size()); // correctly 1
    }
}
```

**How to run:** `java PointOverrideFixed.java`

With `equals(Object other)` correctly matching `Object`'s signature (confirmed by `@Override` compiling successfully) and `hashCode()` also overridden to stay consistent with `equals`, `HashSet` now correctly recognises the two `Point(1, 1)` instances as equal — `points.size()` reports `1`, the intended, correct behaviour.

## 6. Walkthrough

Execution starts in `main`. `points.add(new Point(1, 1))` is called first. Internally, `HashSet.add` computes `hashCode()` on the new `Point` to decide which internal bucket to place it in; since `Point.hashCode()` is genuinely overridden here (`Objects.hash(x, y)`), it returns a hash derived from `x=1, y=1`. Finding no existing entry in that bucket, the set stores this `Point` and returns `true` (added).

`points.add(new Point(1, 1))` is called a second time with a *different* `Point` object holding the same `x` and `y` values. `HashSet.add` computes `hashCode()` on this second object: since `Objects.hash(1, 1)` is deterministic, it produces the exact same hash as the first `Point`, landing in the same bucket. `HashSet` then calls `equals(Object)` between the new object and the existing one in that bucket to check for a true duplicate — because `equals` is correctly overridden with the `Object` signature, this call actually reaches `Point`'s comparison logic, which checks `x == p.x && y == p.y`, both true, so `equals` returns `true`. `HashSet` recognises this as a duplicate and does **not** add a second entry.

`points.size()` reflects only the one genuinely-stored `Point`, so `main` prints `Size: 1`.

Contrast with Level 1: there, `hashCode()` was never overridden at all, so `HashSet` used `Object`'s default identity-based hash code — two different object instances get two different default hash codes, almost certainly landing in different buckets, so `equals` (even if it had been correctly overridden) would likely never even be consulted. That's why Level 1 printed `Size: 2`.

Expected output (Level 3): `Size: 1`

## 7. Gotchas & takeaways

> Overriding `equals(Object)` without also overriding `hashCode()` (or vice versa) breaks the fundamental contract that equal objects must have equal hash codes — always override both together, and let `@Override` on each one confirm you've matched `Object`'s exact signatures.

- `@Override` applies to overriding inherited methods and to implementing interface/abstract methods — both are checked identically by the compiler.
- The classic bug it catches: writing `equals(MyClass other)` instead of `equals(Object other)` creates a silent, unrelated overload that `HashSet`, `HashMap`, `List.contains`, and most of the standard library will never actually call.
- Always override `equals(Object)` and `hashCode()` together — breaking their contract (equal objects must hash equally) causes silent, hard-to-diagnose bugs in any hash-based collection.
- `@Override` is purely a compile-time check with zero runtime cost or behaviour — it exists entirely to catch signature mismatches before the program runs.
- Modern IDEs generate correct `equals`/`hashCode`/`toString` overrides (with `@Override` already attached) automatically — preferring generated code over hand-written versions avoids this class of mistake entirely.
