---
card: data-structures
gi: 14
slug: equals-hashcode-contract
title: equals() & hashCode() contract
---

## 1. What it is

`equals()` and `hashCode()` are two methods every Java object inherits from `Object`. `equals()` decides whether two objects are *logically* the same (not just the same reference), and `hashCode()` returns an `int` "bucket number" used by hash-based collections like `HashMap` and `HashSet`. Java's **contract** is a rule linking them: if `a.equals(b)` is `true`, then `a.hashCode()` must equal `b.hashCode()`. Break that rule, and hash-based collections silently misbehave.

## 2. Why & when

You override both methods whenever a class needs value-based equality — for example, a `Point(x, y)` where two different `Point` instances with the same coordinates should be treated as equal. This matters most the moment such objects go into a `HashSet`, are used as `HashMap` keys, or are compared with `.equals()` in application logic. Skipping `hashCode()` while overriding only `equals()` (or vice versa) is a classic bug: the object "looks" equal in tests that use `.equals()` directly, but disappears from `HashSet`/`HashMap` lookups.

## 3. Core concept

**The contract has three required properties for `equals()`:** reflexive (`a.equals(a)` is always `true`), symmetric (`a.equals(b)` implies `b.equals(a)`), and transitive (`a.equals(b)` and `b.equals(c)` implies `a.equals(c)`). It must also be consistent (repeated calls with unchanged objects return the same result) and `a.equals(null)` must always be `false`.

**The hashCode rule: equal objects MUST have equal hash codes.** If `a.equals(b)` is `true`, `a.hashCode() == b.hashCode()` must also be `true`. The reverse is not required — two unequal objects are allowed to share a hash code (a **collision**); hash-based collections are built to handle that.

**Why breaking the rule corrupts `HashMap`/`HashSet`:** a `HashMap` uses `hashCode()` to pick which bucket to search, then `equals()` to find the exact match inside that bucket. If two equal objects report different hash codes, the map looks in the wrong bucket and the "existing" key is never found — `map.get(key)` returns `null` even though an equal key was `put()` earlier, and duplicate-looking entries pile up in a `HashSet`.

**Default identity behavior, and when to override it.** `Object`'s default `equals()` checks reference identity (`this == other`) and default `hashCode()` derives from the object's identity (often its memory address, JVM-dependent). Immutable value classes should override both together, using the same set of fields in each, so the contract holds automatically.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A HashMap using hashCode to pick a bucket, then equals to find the exact key within that bucket">
  <g font-family="sans-serif" font-size="12">
    <text x="90" y="20" fill="#8b949e" text-anchor="middle">key.hashCode()</text>
    <rect x="30" y="30" width="120" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="90" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">Point(1,2)</text>
    <text x="90" y="75" fill="#8b949e" text-anchor="middle" font-size="10">hash -&gt; bucket 3</text>
    <line x1="150" y1="45" x2="260" y2="45" stroke="#79c0ff" marker-end="url(#a2)"/>
    <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#79c0ff"/></marker></defs>
    <text x="450" y="20" fill="#8b949e" text-anchor="middle">buckets (array of linked entries)</text>
    <rect x="270" y="30" width="360" height="140" fill="none" stroke="#f0883e"/>
    <text x="290" y="50" fill="#8b949e" font-size="10">bucket 0</text>
    <text x="290" y="70" fill="#8b949e" font-size="10">bucket 1</text>
    <text x="290" y="90" fill="#8b949e" font-size="10">bucket 2</text>
    <rect x="360" y="98" width="220" height="26" fill="#0d1117" stroke="#3fb950"/>
    <text x="470" y="116" fill="#e6edf3" text-anchor="middle" font-size="10">bucket 3: [Point(1,2), Point(9,9)]</text>
    <text x="290" y="150" fill="#8b949e" font-size="10">bucket 4</text>
    <text x="350" y="190" fill="#79c0ff" text-anchor="middle">hashCode() finds the bucket fast; equals() then scans that bucket for the real match</text>
  </g>
</svg>

`hashCode()` narrows the search to one bucket in constant time. `equals()` then confirms the exact match by scanning only that bucket's entries.

## 5. Runnable example

The artifact below shows a correct `equals()`/`hashCode()` override, and then a broken class that violates the contract to demonstrate the failure directly.

```java
// EqualsHashCodeContract.java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public class EqualsHashCodeContract {

    // Basic: a correct value-based equals/hashCode pair, using the same fields in both.
    static final class Point {
        final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;              // reflexive shortcut
            if (!(other instanceof Point)) return false;  // type check, false for null too
            Point p = (Point) other;
            return this.x == p.x && this.y == p.y;
        }

        @Override
        public int hashCode() {
            return Objects.hash(x, y); // derived from the SAME fields used in equals
        }

        @Override
        public String toString() { return "Point(" + x + "," + y + ")"; }
    }

    // Intermediate: a class that overrides equals() but "forgets" hashCode() -- breaks the contract.
    static final class BrokenPoint {
        final int x, y;
        BrokenPoint(int x, int y) { this.x = x; this.y = y; }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;
            if (!(other instanceof BrokenPoint)) return false;
            BrokenPoint p = (BrokenPoint) other;
            return this.x == p.x && this.y == p.y;
        }
        // hashCode() NOT overridden: falls back to Object's identity-based hash.
    }

    static void basicLevel() {
        Point a = new Point(1, 2);
        Point b = new Point(1, 2);
        System.out.println("basic: a.equals(b) -> " + a.equals(b)); // true
        System.out.println("basic: a.hashCode() == b.hashCode() -> " + (a.hashCode() == b.hashCode())); // true

        Set<Point> points = new HashSet<>();
        points.add(a);
        System.out.println("basic: set.contains(b) -> " + points.contains(b)); // true: found correctly
    }

    static void intermediateLevel() {
        BrokenPoint a = new BrokenPoint(1, 2);
        BrokenPoint b = new BrokenPoint(1, 2);
        System.out.println("intermediate: a.equals(b) -> " + a.equals(b)); // true: fields match
        System.out.println("intermediate: hashCodes equal? -> " + (a.hashCode() == b.hashCode())); // false: identity-based

        Set<BrokenPoint> broken = new HashSet<>();
        broken.add(a);
        // Contract violated: equal objects landed in different buckets, so lookup fails.
        System.out.println("intermediate: set.contains(b) -> " + broken.contains(b)); // false, even though a.equals(b) is true
    }

    // Advanced: applying the contract to a realistic composite key (order matters, so fields are ordered fields not a Set).
    static final class OrderKey {
        final String customerId;
        final int orderNumber;
        OrderKey(String customerId, int orderNumber) {
            this.customerId = customerId;
            this.orderNumber = orderNumber;
        }
        @Override
        public boolean equals(Object other) {
            if (this == other) return true;
            if (!(other instanceof OrderKey)) return false;
            OrderKey k = (OrderKey) other;
            return orderNumber == k.orderNumber && Objects.equals(customerId, k.customerId);
        }
        @Override
        public int hashCode() { return Objects.hash(customerId, orderNumber); }
    }

    static void advancedLevel() {
        java.util.Map<OrderKey, String> orders = new java.util.HashMap<>();
        orders.put(new OrderKey("cust-42", 7), "Laptop");
        String found = orders.get(new OrderKey("cust-42", 7)); // a DIFFERENT instance, same field values
        System.out.println("advanced: lookup with a new equal-by-value key -> " + found); // "Laptop"
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `EqualsHashCodeContract.java`, then run `java EqualsHashCodeContract.java`.

## 6. Walkthrough

1. `basicLevel()` builds two separate `Point` instances with the same `x`/`y`. `equals()` compares fields, so `a.equals(b)` is `true`, and `hashCode()` is derived from those same fields, so the hash codes match too — the contract holds.
2. Adding `a` to a `HashSet<Point>` then checking `contains(b)` succeeds: the set computes `b.hashCode()`, finds the same bucket `a` landed in, then confirms with `equals()` — a correct round trip.
3. `intermediateLevel()` uses `BrokenPoint`, which overrides `equals()` but leaves the inherited identity-based `hashCode()` untouched. `a.equals(b)` is still `true` by value, but `a.hashCode()` and `b.hashCode()` differ because they come from object identity, not fields.
4. Adding `a` to a `HashSet<BrokenPoint>` and checking `contains(b)` returns `false`: the set hashes `b` into a *different* bucket than the one holding `a`, so it never even reaches the `equals()` check — the contract violation causes a silent lookup failure.
5. `advancedLevel()` shows the contract paying off in a realistic case: a `HashMap<OrderKey, String>` correctly finds a value using a brand-new `OrderKey` instance, purely because that instance is equal-by-value and hashes to the same bucket as the original key.

## 7. Gotchas & takeaways

> Gotcha: overriding `equals()` without overriding `hashCode()` (or vice versa) compiles fine and passes any test that only calls `.equals()` directly — the bug only appears once the object is used as a `HashMap` key or placed in a `HashSet`, where lookups silently fail. Always override both together, from the same fields.

- Equal objects (`equals()` returns `true`) must produce equal `hashCode()` values — hash-based collections rely on this to find entries.
- Unequal objects are allowed to share a hash code (a collision); collections handle that case correctly on their own.
- Use `Objects.hash(field1, field2, ...)` and an `instanceof` + field comparison in `equals()`, built from the exact same set of fields, so the contract holds by construction.
- Related concepts: [Primitives vs references](0010-primitives-vs-references.md) (why `==` and `.equals()` differ for objects) — see also the upcoming hashing/collision material in the Java Collections Framework section.
