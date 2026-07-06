---
card: java
gi: 353
slug: bounded-type-parameters-t-extends-number
title: Bounded type parameters (T extends Number)
---

## 1. What it is

A bounded type parameter restricts what types can be used for `T`, via `<T extends UpperBound>` — despite the keyword `extends`, this same syntax is used whether the bound is a class or an interface, and it means "T must be UpperBound or a subtype of it." `<T extends Number>` lets a generic method or class call `Number`'s methods (like `doubleValue()`) directly on a value of type `T`, something an unbounded `<T>` would never allow, since an unbounded `T` is only known to be *some* type, with no guaranteed methods beyond those on `Object`.

```java
public class BoundedDemo {
    static <T extends Number> double doubleValue(T value) {
        return value.doubleValue(); // only possible because T is guaranteed to be a Number
    }

    public static void main(String[] args) {
        System.out.println(doubleValue(42));
        System.out.println(doubleValue(3.14));
        // doubleValue("not a number"); // would NOT compile -- String is not a Number
    }
}
```

`<T extends Number>` guarantees, at compile time, that whatever type is used for `T` provides `Number`'s methods — calling `doubleValue("not a number")` fails to compile immediately, since `String` doesn't extend `Number`, rather than failing at runtime.

## 2. Why & when

An unbounded type parameter `<T>` can only be treated as `Object` inside the method or class body — no methods beyond `Object`'s (`toString()`, `equals()`, `hashCode()`) can be called on a value of type `T`. Bounding it to a specific class or interface unlocks that type's methods, letting generic code do real, type-specific work while still working across every type that satisfies the bound.

- **Requiring specific behavior from a generic type** — `<T extends Comparable<T>>` for anything that needs to compare values, `<T extends Number>` for anything that needs numeric operations, `<T extends AutoCloseable>` for anything that needs to be closed.
- **Constraining a generic class or method to a meaningful family of types** — a generic numeric utility class only makes sense for actual numbers, not arbitrary objects; bounding `T` enforces that at the type level rather than relying on a runtime check.
- **Enabling method calls the compiler would otherwise reject** — without a bound, calling any method beyond `Object`'s on a value of type `T` is a compile error; a bound is what makes calling `.doubleValue()`, `.compareTo()`, or similar domain-specific methods possible.

A bound restricts what types are *allowed* for `T` — it does not change how the generic code itself behaves at runtime (type erasure still applies), and only one class (or none) may appear as a bound, though any number of interfaces can be added alongside it (a related topic: multiple bounds).

## 3. Core concept

```java
import java.util.List;

public class BoundedCore {
    static <T extends Number> double sum(List<T> values) {
        double total = 0;
        for (T value : values) total += value.doubleValue(); // relies on the bound
        return total;
    }

    static <T extends Comparable<T>> T max(List<T> values) {
        T best = values.get(0);
        for (T value : values) if (value.compareTo(best) > 0) best = value; // relies on the bound
        return best;
    }

    public static void main(String[] args) {
        System.out.println("Sum: " + sum(List.of(1, 2, 3)));
        System.out.println("Max: " + max(List.of("banana", "apple", "cherry")));
    }
}
```

**How to run:** `java BoundedCore.java`

`sum` requires `T extends Number` to call `doubleValue()`; `max` requires `T extends Comparable<T>` to call `compareTo()` — each bound unlocks exactly the specific method the generic algorithm actually needs, nothing more.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an unbounded type parameter only allows Object's methods; a bounded type parameter unlocks the bound's own methods, at the cost of restricting which types may be used">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="250" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="145" y="55" fill="#8b949e" font-size="10" text-anchor="middle">&lt;T&gt; -- only Object's methods available</text>

  <rect x="20" y="85" width="250" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="145" y="110" fill="#6db33f" font-size="10" text-anchor="middle">&lt;T extends Number&gt; -- Number's methods too</text>

  <text x="300" y="55" fill="#8b949e" font-size="9">accepts ANY type</text>
  <text x="300" y="110" fill="#8b949e" font-size="9">accepts only Number and its subtypes</text>
</svg>

## 5. Runnable example

Scenario: a small statistics helper for numeric data, evolved from one restricted to a single numeric type, into a bounded generic version usable across all `Number` subtypes, into a production-style version that also requires `Comparable` for a combined bound, correctly finding both sum and range.

### Level 1 — Basic

```java
import java.util.List;

public class StatsBasic {
    static double sum(List<Integer> values) { // hardcoded to Integer only
        double total = 0;
        for (int value : values) total += value;
        return total;
    }

    public static void main(String[] args) {
        System.out.println("Sum: " + sum(List.of(1, 2, 3)));
        // sum(List.of(1.5, 2.5)); // would NOT compile -- this method only accepts List<Integer>
    }
}
```

**How to run:** `java StatsBasic.java`

This works, but it's locked to `Integer` specifically — summing a `List<Double>` or `List<Long>` would require an entirely separate, duplicated method, even though the summing logic itself is identical regardless of which specific numeric type is used.

### Level 2 — Intermediate

```java
import java.util.List;

public class StatsIntermediate {
    static <T extends Number> double sum(List<T> values) { // bounded generic -- works for any Number subtype
        double total = 0;
        for (T value : values) total += value.doubleValue();
        return total;
    }

    public static void main(String[] args) {
        System.out.println("Sum of ints: " + sum(List.of(1, 2, 3)));
        System.out.println("Sum of doubles: " + sum(List.of(1.5, 2.5)));
        System.out.println("Sum of longs: " + sum(List.of(100L, 200L)));
    }
}
```

**How to run:** `java StatsIntermediate.java`

One bounded generic method now handles `Integer`, `Double`, `Long`, or any other `Number` subtype, since `<T extends Number>` guarantees `doubleValue()` is always available regardless of which specific numeric type `T` turns out to be at each call.

### Level 3 — Advanced

```java
import java.util.List;

public class StatsAdvanced {
    static <T extends Number> double sum(List<T> values) {
        double total = 0;
        for (T value : values) total += value.doubleValue();
        return total;
    }

    // Multiple bounds: T must be BOTH a Number and Comparable to itself.
    static <T extends Number & Comparable<T>> T range(List<T> values) {
        T min = values.get(0), max = values.get(0);
        for (T value : values) {
            if (value.compareTo(min) < 0) min = value;
            if (value.compareTo(max) > 0) max = value;
        }
        return max; // (returning max here; range magnitude would need subtraction, type-specific)
    }

    public static void main(String[] args) {
        List<Integer> scores = List.of(72, 95, 61, 88, 100);
        System.out.println("Sum: " + sum(scores));
        System.out.println("Max via range(): " + range(scores));
    }
}
```

**How to run:** `java StatsAdvanced.java`

`range` requires `T extends Number & Comparable<T>` — both bounds are necessary because it uses `compareTo` (from `Comparable`) to track the running min/max, while still being restricted to actual numeric types by the `Number` bound, demonstrating that multiple bounds let a single type parameter require several distinct capabilities at once.

## 6. Walkthrough

Execution starts in `main`, which builds `scores = List.of(72, 95, 61, 88, 100)` and calls `sum(scores)` first.

Inside `sum`, the compiler infers `T = Integer` (satisfying `T extends Number`). The loop accumulates: `total` goes `0 -> 72.0 -> 167.0 -> 228.0 -> 316.0 -> 416.0` as each element's `doubleValue()` is added in turn. The method returns `416.0`, printed as `Sum: 416.0`.

`main` then calls `range(scores)`. The compiler infers `T = Integer` here too, checking it satisfies *both* bounds: `Integer extends Number` (true) and `Integer` implements `Comparable<Integer>` (true) — both conditions must hold for this call to compile at all.

Inside `range`, `min` and `max` both start as `values.get(0)`, which is `72`. The loop processes each element: for `72` itself, `72.compareTo(72) < 0` is false (skip min update) and `72.compareTo(72) > 0` is false (skip max update). For `95`: `95.compareTo(72) < 0` is false; `95.compareTo(72) > 0` is true, so `max` becomes `95`. For `61`: `61.compareTo(72) < 0` is true, so `min` becomes `61`; the max check (`61.compareTo(95) > 0`) is false. For `88`: neither comparison changes `min` (61) or `max` (95). For `100`: `100.compareTo(61) < 0` is false; `100.compareTo(95) > 0` is true, so `max` becomes `100`.

After the loop, `range` returns `max`, which is `100`. Back in `main`, this is printed as `Max via range(): 100`.

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sum accumulates every element's doubleValue via the Number bound; range tracks running min and max using compareTo via the Comparable bound, both bounds required simultaneously">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">sum([72,95,61,88,100]): T=Integer satisfies Number -&gt; accumulate doubleValue() -&gt; total=416.0</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">range([72,95,61,88,100]): T=Integer satisfies BOTH Number and Comparable&lt;Integer&gt;</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">  track min/max via compareTo() through the list -&gt; min ends at 61, max ends at 100</text>
  <text x="20" y="105" fill="#8b949e" font-size="10">range() returns max (100) -- both bounds were needed to write this method at all.</text>
</svg>

## 7. Gotchas & takeaways

> Only one class may appear in a bound (a type parameter can extend at most one concrete class), but any number of interfaces can be added alongside it using `&` — `T extends Number & Comparable<T>` is valid, but `T extends Number & Integer` would not be, since `Integer` is a class, not an interface, and you can't bound by two classes at once.

- An unbounded type parameter `<T>` only allows calling `Object`'s methods on a value of type `T` — bounding it (`<T extends SomeType>`) unlocks `SomeType`'s own methods.
- A bound restricts which types are *allowed* to be used for `T`, checked entirely at compile time — it doesn't change runtime behavior beyond what the bound's own methods do.
- Common bounds include `<T extends Number>` (for numeric operations), `<T extends Comparable<T>>` (for ordering/comparison), and combinations of interfaces via `&` for methods requiring multiple capabilities at once.
- Choose the narrowest bound that satisfies what the generic code actually needs — an overly broad bound (or none at all) unnecessarily limits the code to only `Object`'s methods; an overly narrow one unnecessarily restricts which types can be used.
- Bounded wildcards (`? extends Number`) are a related but distinct concept from bounded type parameters (`<T extends Number>`) — the former appears at usage sites for variance, the latter at declaration sites for the type parameter itself.
