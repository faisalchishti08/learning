---
card: java
gi: 389
slug: autoboxing-pitfalls-npe-identity-caching-128-127
title: 'Autoboxing pitfalls (NPE, == identity, caching -128..127)'
---

## 1. What it is

Autoboxing and unboxing (see [[autoboxing-primitive-wrapper]] and [[auto-unboxing-wrapper-primitive]]) make primitives and wrapper objects look almost interchangeable in source code, but three specific pitfalls come from the ways they genuinely aren't: **unboxing a `null` throws `NullPointerException`**; **comparing boxed values with `==` compares object identity, not numeric value**; and **the JVM caches `Integer` (and other wrapper) objects for small values, roughly -128 to 127**, which makes `==` on small numbers appear to work correctly by accident, only to silently break for larger ones.

## 2. Why & when

These pitfalls exist because `Integer` (and the other wrapper classes) are genuinely reference types with object identity, even though autoboxing makes them look like primitives most of the time. `==` on any reference type always compares identity ("are these the exact same object?"), never value — this is completely consistent with how `==` behaves for every other object type in Java, but it surprises people specifically with boxed numbers because the *literal* code (`Integer a = 100; Integer b = 100; a == b`) reads as if it should obviously compare the numbers.

The caching behaviour makes this worse in a sneaky way: `Integer.valueOf(int)` (which autoboxing calls internally) returns a **cached, shared object** for values from -128 to 127, but allocates a genuinely new object for anything outside that range. So `Integer a = 100; Integer b = 100; a == b` happens to be `true` (both reference the same cached object), lulling developers into believing `==` works for boxed integers — right up until a value like `200` breaks that same code silently, since `200` falls outside the cache and gets two separate objects.

The fix for all of this is the same, simple rule: never use `==` to compare boxed wrapper values for equality — always use `.equals()`, and always guard against `null` before unboxing.

## 3. Core concept

```java
public class BoxingPitfallsDemo {
    public static void main(String[] args) {
        Integer a = 100, b = 100; // both within the cache range (-128..127)
        System.out.println("100 == 100 (cached): " + (a == b)); // true -- same cached object, by luck

        Integer c = 200, d = 200; // both OUTSIDE the cache range
        System.out.println("200 == 200 (not cached): " + (c == d)); // false -- two distinct objects!

        System.out.println("Correct comparison: " + c.equals(d)); // true -- always correct, regardless of caching
    }
}
```

**How to run:** `java BoxingPitfallsDemo.java`

`a == b` is `true` purely because `100` falls within `Integer`'s cached range, so `a` and `b` happen to reference the identical cached object. `c == d` is `false` even though both hold the mathematical value `200`, because `200` is outside the cache, so autoboxing allocates two separate `Integer` objects. `c.equals(d)` is `true` in both cases, since `.equals()` correctly compares the actual numeric values, never identity.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="values within the Integer cache range share one object so == appears to work by luck, while values outside the cache get separate objects so == silently gives the wrong answer">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">Integer a = 100, b = 100;   (within cache -128..127)</text>
  <rect x="240" y="40" width="140" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="310" y="62" fill="#6db33f" font-size="10" text-anchor="middle">one cached Integer(100)</text>
  <line x1="140" y1="65" x2="235" y2="57" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="140" y1="85" x2="235" y2="65" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="20" y="100" fill="#6db33f" font-size="10">a == b -&gt; true (same object, by luck of caching)</text>

  <text x="20" y="130" fill="#e6edf3" font-size="11">Integer c = 200, d = 200;   (outside cache range)</text>
  <rect x="220" y="140" width="120" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="280" y="160" fill="#f85149" font-size="9" text-anchor="middle">new Integer(200)</text>
  <rect x="380" y="140" width="120" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="440" y="160" fill="#f85149" font-size="9" text-anchor="middle">new Integer(200)</text>
  <text x="20" y="185" fill="#f85149" font-size="10">c == d -&gt; false! Two distinct objects with the same value -- always use .equals() instead.</text>
</svg>

## 5. Runnable example

Scenario: a loyalty-points comparison feature, evolved from a version that appears to work correctly in small-scale testing (values happen to be within the cache range), through the exact moment larger real-world values expose the bug, to a properly fixed version using `.equals()` throughout.

### Level 1 — Basic

```java
public class LoyaltyPointsTestingSmallValues {
    static boolean samePoints(Integer a, Integer b) {
        return a == b; // looks reasonable, tests pass... for now
    }

    public static void main(String[] args) {
        System.out.println(samePoints(50, 50));   // true -- within cache, "works"
        System.out.println(samePoints(100, 100)); // true -- within cache, "works"
    }
}
```

**How to run:** `java LoyaltyPointsTestingSmallValues.java`

Both test cases use small values within `Integer`'s cache range, so `a == b` happens to give the mathematically correct answer both times — this creates false confidence that `==` is a valid way to compare these boxed values, when it's actually working by coincidence.

### Level 2 — Intermediate

```java
public class LoyaltyPointsBugExposed {
    static boolean samePoints(Integer a, Integer b) {
        return a == b; // the same "working" code from Level 1
    }

    public static void main(String[] args) {
        System.out.println(samePoints(50, 50));     // still true -- within cache
        System.out.println(samePoints(500, 500));   // FALSE! -- real customers earn more than 127 points
    }
}
```

**How to run:** `java LoyaltyPointsBugExposed.java`

The exact same `samePoints` method that "worked" in Level 1 now silently returns `false` for `samePoints(500, 500)` — two customers who genuinely have the identical point total are incorrectly reported as having different totals, purely because `500` falls outside the `Integer` cache and each argument gets its own separate object.

### Level 3 — Advanced

```java
public class LoyaltyPointsFixed {
    static boolean samePoints(Integer a, Integer b) {
        if (a == null || b == null) { // guard against null BEFORE calling .equals() or unboxing
            return a == b; // both null -> true; exactly one null -> false; safe identity check here is fine
        }
        return a.equals(b); // correct numeric comparison, regardless of caching
    }

    public static void main(String[] args) {
        System.out.println(samePoints(50, 50));    // true -- correct, and no longer by luck
        System.out.println(samePoints(500, 500));  // true now -- bug fixed
        System.out.println(samePoints(500, null)); // false -- handled safely, no NullPointerException
        System.out.println(samePoints(null, null)); // true -- both absent, treated as equal
    }
}
```

**How to run:** `java LoyaltyPointsFixed.java`

`samePoints` now checks for `null` first — if either argument is `null`, `a == b` is used deliberately (safe here, since it's comparing against `null`, not doing a numeric comparison, and Java allows `==` against `null` without triggering unboxing). Once both are confirmed non-`null`, `.equals()` performs a genuine value comparison, correct regardless of whether the values happen to fall inside or outside the cache range.

## 6. Walkthrough

Execution starts in `main`. `samePoints(500, 500)` is called first (tracing the previously-broken case). Both `500` literals are autoboxed into `Integer` objects as they're passed as arguments — since `500` is outside the -128..127 cache range, this produces two genuinely separate `Integer` objects, one for each argument.

Inside `samePoints`, `a == null || b == null` checks: `a` is a real (non-null) `Integer` object, so `a == null` is `false`; same for `b`. The whole condition is `false`, so the guard branch is skipped. `a.equals(b)` runs next: `Integer.equals` compares the actual `int` values wrapped by each object — `500` and `500` — which are equal, so it returns `true`, regardless of the fact that `a` and `b` are two distinct objects. `main` prints `true`.

`samePoints(500, null)` runs next. The second argument, `null`, is passed directly as `Integer b = null` — no autoboxing occurs for a `null` literal, since `null` is already a valid reference of any reference type. Inside `samePoints`, `a == null || b == null` checks: `a == null` is `false`, but `b == null` is `true` — the whole condition is `true` (short-circuited `||`). The guard branch executes: `return a == b`, which is `Integer(500) == null` — this is a safe, ordinary reference comparison against `null` (it does **not** attempt to unbox `a`, since `==` against `null` never triggers unboxing), and it's `false`, since `a` is a real object, not `null`. `main` prints `false`.

`samePoints(null, null)` runs last. Both `a == null` and `b == null` are `true`, so the guard branch runs: `return a == b`, which is `null == null`, `true`. `main` prints `true`.

Expected output:
```
true
true
false
true
```

## 7. Gotchas & takeaways

> `Integer.valueOf(int)` — which is exactly what autoboxing calls internally — caches and reuses objects only for values from -128 to 127 (the exact range is guaranteed by the JVM specification, though implementations may cache a wider range). Code that appears to work correctly with `==` on boxed integers during testing with small values can silently break in production once real values exceed that range — always use `.equals()`, never assume small-scale testing has proven `==` correct.

- Comparing boxed wrapper objects with `==` compares object identity, never numeric value — this is standard, correct `==` behaviour for any reference type, it just surprises people specifically with numbers.
- The JVM caches `Integer` objects (and similarly for `Byte`, `Short`, `Long`, `Character`, `Boolean`) for a small range of common values, making `==` appear to work by coincidence for those values only.
- Always use `.equals()` to compare boxed wrapper values for equality — it is correct in every case, regardless of caching, and costs essentially nothing extra.
- Always check for `null` before letting a boxed reference participate in unboxing (arithmetic, comparisons via `<`/`>`, loop conditions) — unboxing `null` throws `NullPointerException` immediately, see [[auto-unboxing-wrapper-primitive]].
- When guarding against `null` before an equality check, compare against `null` with `==` directly (safe, since it never triggers unboxing) — only call `.equals()` once you've confirmed the reference is genuinely non-null.
