---
card: java
gi: 233
slug: hashcode
title: hashCode()
---

## 1. What it is

`hashCode()` is another method inherited from `Object` that returns an `int` "hash" summarizing an object — a number that hash-based collections (`HashMap`, `HashSet`, `HashTable`) use to quickly bucket and locate objects, instead of scanning every element one by one. `Object`'s default implementation typically derives this number from the object's memory address, meaning two distinct objects almost always get different default hash codes, even if their content is identical.

```java
class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
}

public class HashCodeDemo {
    public static void main(String[] args) {
        Point a = new Point(1, 2);
        Point b = new Point(1, 2);
        System.out.println(a.hashCode()); // some number, e.g. 366712642
        System.out.println(b.hashCode()); // a DIFFERENT number, even though content matches
    }
}
```

Without an override, `a.hashCode()` and `b.hashCode()` are almost certainly different, even though `a` and `b` hold identical `x`/`y` values — this becomes a real problem the moment `Point` is also expected to work correctly as a `HashSet` element or `HashMap` key, which is exactly what the next topic (the equals/hashCode contract) addresses.

## 2. Why & when

`hashCode()` exists purely to make hash-based collections fast, and it must be overridden any time `equals()` is overridden, for reasons the next topic explains in depth.

- **Bucketing performance** — a `HashMap` uses an object's `hashCode()` to decide which internal "bucket" to search, turning what would otherwise be a slow linear scan through every entry into a near-constant-time lookup.
- **Consistency with equals** — if two objects are `equal` (via an overridden `equals`) but have different hash codes, hash-based collections can fail to find an entry that is genuinely present, since they will look in the wrong bucket entirely.
- **Deterministic bucket placement** — a class's `hashCode()` should be derived from the same fields used in `equals()`, so that equal objects always land in the same bucket and unequal objects are very likely to land in different ones (reducing collisions and keeping lookups fast).

Override `hashCode()` any time you override `equals()` for a class, and derive it from exactly the same fields `equals()` compares — `java.util.Objects.hash(field1, field2, ...)` is the standard, convenient way to do this correctly without hand-rolling the arithmetic.

## 3. Core concept

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
    public int hashCode() {
        return Objects.hash(x, y); // derived from the SAME fields equals() compares
    }
}
```

`Objects.hash(x, y)` combines `x` and `y` into a single `int`, deterministically — calling it twice with the same `x` and `y` always produces the same number, which is exactly the property `HashMap` and `HashSet` depend on to reliably find objects they previously stored.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="hashCode determines which bucket an object goes into inside a hash map, equal objects must land in the same bucket for lookups to work correctly">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Point(1, 2).hashCode()</text>

  <line x1="110" y1="55" x2="110" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="250" y="70" width="100" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Bucket #7</text>

  <rect x="410" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">another Point(1, 2)</text>
  <line x1="490" y1="55" x2="300" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both equal Points must produce the same hashCode, so they land in the</text>
  <text x="300" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SAME bucket — otherwise a HashMap/HashSet lookup can silently fail to find them.</text>
</svg>

Two objects considered equal by `equals()` must land in the same hash bucket, which is only guaranteed if `hashCode()` is derived consistently from the same fields.

## 5. Runnable example

Scenario: an `Employee` class used as a `HashMap` key for looking up salaries, evolved from a plain override into a working lookup, then hardened to show exactly what breaks when `hashCode` is missing or inconsistent.

### Level 1 — Basic

```java
import java.util.Objects;

public class HashCodeBasic {
    static class Employee {
        String id;
        Employee(String id) { this.id = id; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof Employee)) return false;
            return this.id.equals(((Employee) obj).id);
        }

        @Override
        public int hashCode() {
            return Objects.hash(id); // consistent with equals: derived from id
        }
    }

    public static void main(String[] args) {
        Employee a = new Employee("E100");
        Employee b = new Employee("E100");
        System.out.println(a.hashCode() == b.hashCode()); // true — same id, same hash
    }
}
```

**How to run:** `java HashCodeBasic.java`

`a` and `b` are distinct objects but share the same `id`, and since `hashCode()` is derived from `id`, they produce identical hash codes — a prerequisite for `a` and `b` to work interchangeably as `HashMap` keys.

### Level 2 — Intermediate

Same `Employee`, now actually used as a `HashMap` key to look up a salary, demonstrating why matching `hashCode` and `equals` together make the lookup succeed.

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

public class HashCodeIntermediate {
    static class Employee {
        String id;
        Employee(String id) { this.id = id; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof Employee)) return false;
            return this.id.equals(((Employee) obj).id);
        }

        @Override
        public int hashCode() { return Objects.hash(id); }
    }

    public static void main(String[] args) {
        Map<Employee, Double> salaries = new HashMap<>();
        salaries.put(new Employee("E100"), 75000.0); // stored with one Employee instance

        Employee lookupKey = new Employee("E100"); // a DIFFERENT instance, same id
        System.out.println(salaries.get(lookupKey)); // 75000.0 — found despite being a different object
    }
}
```

**How to run:** `java HashCodeIntermediate.java`

`salaries.get(lookupKey)` first computes `lookupKey.hashCode()` to find the right bucket, then uses `equals()` to confirm the match within that bucket — since both `hashCode` and `equals` are derived from `id`, the lookup succeeds even though `lookupKey` is a completely different object from the one originally stored.

### Level 3 — Advanced

Same scenario, now contrasted with a broken version that overrides `equals` but forgets `hashCode` — demonstrating concretely how this breaks `HashMap` lookups silently, then the correct fix.

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

public class HashCodeAdvanced {
    // BROKEN: overrides equals but NOT hashCode
    static class BrokenEmployee {
        String id;
        BrokenEmployee(String id) { this.id = id; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof BrokenEmployee)) return false;
            return this.id.equals(((BrokenEmployee) obj).id);
        }
        // hashCode() NOT overridden -> falls back to Object's identity-based default
    }

    // FIXED: overrides both, consistently
    static class FixedEmployee {
        String id;
        FixedEmployee(String id) { this.id = id; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof FixedEmployee)) return false;
            return this.id.equals(((FixedEmployee) obj).id);
        }

        @Override
        public int hashCode() { return Objects.hash(id); }
    }

    public static void main(String[] args) {
        Map<BrokenEmployee, Double> brokenMap = new HashMap<>();
        brokenMap.put(new BrokenEmployee("E100"), 75000.0);
        System.out.println("Broken lookup: " + brokenMap.get(new BrokenEmployee("E100"))); // null! wrong bucket

        Map<FixedEmployee, Double> fixedMap = new HashMap<>();
        fixedMap.put(new FixedEmployee("E100"), 75000.0);
        System.out.println("Fixed lookup: " + fixedMap.get(new FixedEmployee("E100"))); // 75000.0, found correctly
    }
}
```

**How to run:** `java HashCodeAdvanced.java`

`BrokenEmployee` overrides `equals` (so two instances with the same `id` are logically equal) but inherits `Object`'s identity-based `hashCode`, so the stored instance and the lookup instance almost certainly hash into *different* buckets — the `HashMap` never even checks `equals` against the right entry, because it never looks in the bucket containing it, so `get` returns `null` despite a logically matching entry existing in the map.

## 6. Walkthrough

Trace both `get` calls in `HashCodeAdvanced.main`.

**`brokenMap.put(new BrokenEmployee("E100"), 75000.0)`.** The `HashMap` calls `hashCode()` on the new `BrokenEmployee` — since it is not overridden, this resolves to `Object`'s default, based on the object's identity (roughly, its memory address). Say this yields some bucket, call it bucket `B1`. The entry is stored there.

**`brokenMap.get(new BrokenEmployee("E100"))`.** A brand new `BrokenEmployee` object is created for the lookup. `HashMap` calls `hashCode()` on *this* new object — since it is a different object, `Object`'s identity-based default almost certainly returns a different number, landing in a different bucket, say `B2`. The `HashMap` searches only bucket `B2`; it never finds the entry stored in `B1`, and never even gets to call `equals()` to check for a logical match. The result is `null`.

**`fixedMap.put(new FixedEmployee("E100"), 75000.0)`.** `hashCode()` is called on the new `FixedEmployee`, computed as `Objects.hash("E100")` — call this value `H`. The entry is stored in the bucket corresponding to `H`.

**`fixedMap.get(new FixedEmployee("E100"))`.** A new `FixedEmployee` is created for the lookup, with the same `id`, `"E100"`. `hashCode()` computes `Objects.hash("E100")` again — the *same* deterministic value `H`, since it depends only on `id`. The `HashMap` searches the correct bucket, finds the stored entry, calls `equals()` to confirm the match (`"E100".equals("E100")` is `true`), and returns `75000.0`.

```
BrokenEmployee: put uses hashCode() = identity-based(instance1) -> bucket B1
                get uses hashCode() = identity-based(instance2) -> bucket B2 (different!)
                -> bucket never matches -> equals() never even checked -> null

FixedEmployee:  put uses hashCode() = Objects.hash("E100") = H -> bucket for H
                get uses hashCode() = Objects.hash("E100") = H (same) -> same bucket
                -> equals() checked -> true -> 75000.0
```

**Final output.** `"Broken lookup: null"` followed by `"Fixed lookup: 75000.0"` — a direct demonstration that overriding `equals` without also overriding `hashCode` consistently breaks hash-based collection lookups, even though the objects are logically equal by the `equals` definition alone.

## 7. Gotchas & takeaways

> **Overriding `equals` without also overriding `hashCode` is one of the most common real-world Java bugs** — it compiles fine and often even seems to work in quick manual tests, but silently breaks `HashMap`/`HashSet` lookups, because equal objects can land in different buckets and the collection never even attempts the `equals` comparison that would have found them.

> **`hashCode()` must be derived from the same fields `equals()` uses for comparison** — if `equals` ignores a field (say, a cache or a timestamp) but `hashCode` includes it, two equal objects can still produce different hash codes, reintroducing the exact same bug in a subtler form.

- `hashCode()` exists to let hash-based collections (`HashMap`, `HashSet`) bucket objects for fast lookup, rather than comparing against every stored element.
- Any time you override `equals()`, you must also override `hashCode()`, using the same fields, or hash-based collections will behave incorrectly.
- `java.util.Objects.hash(field1, field2, ...)` is the standard, safe way to combine multiple fields into one consistent hash code.
- Equal objects (per `equals()`) must always produce equal hash codes; unequal objects are allowed to share a hash code (a "collision"), just less efficiently.
