---
card: java
gi: 278
slug: number-abstract-class
title: Number abstract class
---

## 1. What it is

`Number` is an abstract class that all the numeric wrapper classes (`Integer`, `Long`, `Double`, `Float`, `Short`, `Byte`) extend. It declares a small set of abstract conversion methods — `intValue()`, `longValue()`, `doubleValue()`, `floatValue()`, and a couple more — that every numeric wrapper must implement, letting you write code that works generically across any numeric wrapper type without knowing its exact class in advance.

```java
public class NumberDemo {
    static double sumAsDouble(Number a, Number b) { // accepts ANY numeric wrapper type
        return a.doubleValue() + b.doubleValue(); // works regardless of the actual wrapper class
    }

    public static void main(String[] args) {
        System.out.println(sumAsDouble(5, 3.14));      // Integer + Double
        System.out.println(sumAsDouble(10L, (short) 2)); // Long + Short
    }
}
```

`sumAsDouble` accepts a `Number` parameter, which any of `Integer`, `Long`, `Double`, `Short`, and the rest can be passed as (via autoboxing); calling `.doubleValue()` on either parameter works uniformly regardless of which specific wrapper class was actually passed, since `Number` guarantees every subclass provides that conversion method.

## 2. Why & when

`Number` exists to let you write code that operates generically across every numeric type, without needing a separate overload or code path for `Integer`, `Long`, `Double`, and so on individually.

- **Writing one method instead of many overloads** — without `Number`, accepting "any kind of number" would require either a separate overloaded method for each wrapper type, or accepting `Object` and manually checking/casting, both far more cumbersome than a single method accepting `Number` directly.
- **Uniform conversion regardless of the underlying type** — `intValue()`, `longValue()`, `doubleValue()`, and `floatValue()` are guaranteed to exist on any `Number` subclass, letting you extract whichever primitive representation you need, with the appropriate widening or narrowing conversion happening automatically as part of each method's own implementation.
- **A common supertype for mixed-numeric-type collections or parameters** — if you're processing a collection or accepting a parameter that could reasonably be any numeric type (say, a generic configuration value that might be an `int`, a `long`, or a `double` depending on context), typing it as `Number` avoids forcing every caller to already know or convert to one specific type upfront.

Use `Number` as a parameter or field type when your code genuinely needs to handle multiple numeric wrapper types generically and only cares about extracting a primitive value in one particular form (usually via `doubleValue()`, the most universally lossless-enough conversion for general arithmetic); for code that only ever deals with one specific numeric type, using that concrete type (`Integer`, `Double`, etc.) directly remains simpler and clearer.

## 3. Core concept

```java
abstract class Number { // simplified illustration of the real java.lang.Number
    abstract int intValue();
    abstract long longValue();
    abstract float floatValue();
    abstract double doubleValue();
}

// Integer, Long, Double, etc. all implement these methods, each doing the appropriate conversion:
// Integer.doubleValue() simply widens the int to a double
// Double.intValue() truncates the double's fractional part to produce an int
```

Every numeric wrapper implements all four abstract methods, but each conversion behaves according to that specific type's own semantics — `Integer.doubleValue()` is a safe, lossless widening conversion, while `Double.intValue()` is a lossy narrowing conversion that truncates any fractional part, which is important to understand before calling these methods expecting a particular kind of result.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Number is an abstract superclass with Integer Long Double Float Short and Byte all extending it, each implementing intValue longValue floatValue and doubleValue according to its own conversion semantics">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">abstract Number</text>

  <line x1="250" y1="55" x2="100" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="280" y1="55" x2="230" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="320" y1="55" x2="370" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="350" y1="55" x2="500" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="40" y="95" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="115" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Integer</text>

  <rect x="170" y="95" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="230" y="115" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Long</text>

  <rect x="310" y="95" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="115" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Double</text>

  <rect x="440" y="95" width="120" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="115" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Short, Byte...</text>

  <text x="300" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Every wrapper implements the same abstract conversion methods, each with its own type-specific semantics.</text>
</svg>

Every numeric wrapper extends `Number`, implementing the same conversion methods with type-appropriate semantics.

## 5. Runnable example

Scenario: a generic statistics utility accepting mixed numeric types, evolved from a single-type calculation into one accepting any `Number`, then hardened with awareness of lossy narrowing conversions between different numeric types.

### Level 1 — Basic

```java
public class NumberBasic {
    static double average(Number a, Number b) {
        return (a.doubleValue() + b.doubleValue()) / 2;
    }

    public static void main(String[] args) {
        System.out.println(average(10, 20));     // both Integer
        System.out.println(average(10.5, 20.5));  // both Double
    }
}
```

**How to run:** `java NumberBasic.java`

`average` accepts `Number` parameters, so it works identically whether given two `Integer`s or two `Double`s — `doubleValue()` provides a uniform way to extract a `double` regardless of the actual wrapper type passed in.

### Level 2 — Intermediate

Same utility, now processing a mixed list of different numeric wrapper types together, demonstrating `Number` as a genuinely useful common type for heterogeneous numeric data.

```java
import java.util.List;

public class NumberIntermediate {
    static double sumAll(List<Number> values) {
        double total = 0;
        for (Number value : values) {
            total += value.doubleValue(); // works uniformly regardless of each element's actual wrapper type
        }
        return total;
    }

    public static void main(String[] args) {
        List<Number> mixed = List.of(10, 20L, 3.5, (short) 7, 1.25f); // Integer, Long, Double, Short, Float
        System.out.println("Sum: " + sumAll(mixed));
    }
}
```

**How to run:** `java NumberIntermediate.java`

`List<Number>` holds five genuinely different wrapper types simultaneously — `Integer`, `Long`, `Double`, `Short`, and `Float` — and `sumAll` processes every one of them uniformly via `doubleValue()`, demonstrating `Number`'s real value: eliminating the need for type-specific handling when only a generic numeric value is actually needed.

### Level 3 — Advanced

Same statistics utility, now demonstrating the lossy-narrowing pitfall directly: converting a `Number` to `intValue()` when its underlying value is actually a `Double` with a fractional part, or exceeds `int`'s range — both silently produce a different, potentially surprising result rather than throwing an exception.

```java
import java.util.List;

public class NumberAdvanced {
    static void inspectAsInt(Number n) {
        int truncated = n.intValue(); // narrowing: may lose precision or overflow silently
        System.out.println(n + " (" + n.getClass().getSimpleName() + ") .intValue() -> " + truncated);
    }

    public static void main(String[] args) {
        List<Number> values = List.of(42, 3.99, -3.99, 5_000_000_000L);

        for (Number value : values) {
            inspectAsInt(value);
        }
    }
}
```

**How to run:** `java NumberAdvanced.java`

`intValue()` on a `Double` truncates toward zero (discarding the fractional part entirely, not rounding), and `intValue()` on a `Long` whose value exceeds `int`'s range silently produces a wrapped, incorrect result — neither case throws an exception, which is exactly why calling `intValue()` on a `Number` of unknown or mixed origin requires understanding these type-specific narrowing behaviours in advance.

## 6. Walkthrough

Trace the loop in `NumberAdvanced.main` over all four values.

**`value = 42` (an `Integer`).** `inspectAsInt(42)`: `n.intValue()` on an `Integer` simply returns its own wrapped value directly, no conversion needed: `42`. Prints `"42 (Integer) .intValue() -> 42"`.

**`value = 3.99` (a `Double`).** `inspectAsInt(3.99)`: `n.intValue()` on a `Double` truncates toward zero, discarding the fractional `.99` entirely (not rounding to the nearest integer): `3`. Prints `"3.99 (Double) .intValue() -> 3"`.

**`value = -3.99` (a `Double`).** `inspectAsInt(-3.99)`: truncation toward zero for a negative value also discards the fractional part, moving toward `0`, not away from it: `-3` (not `-4`, which rounding would produce). Prints `"-3.99 (Double) .intValue() -> -3"`.

**`value = 5_000_000_000L` (a `Long`).** `inspectAsInt(5000000000L)`: this value (`5,000,000,000`) exceeds `Integer.MAX_VALUE` (`2,147,483,647`) by a significant margin. `Long.intValue()` simply truncates the lower 32 bits of the underlying `long` representation, producing whatever value those bits represent as an `int` — this results in a value that has no straightforward arithmetic relationship to the original number (a form of silent overflow/wraparound specific to this narrowing conversion), printed here as whatever `int` value those bits happen to represent.

```
42            (Integer): intValue() -> 42        (no conversion needed)
3.99          (Double):  intValue() -> 3         (truncates toward zero, discards .99)
-3.99         (Double):  intValue() -> -3         (truncates toward zero, discards .99, does NOT round to -4)
5000000000    (Long):    intValue() -> some wrapped, unrelated-looking value (bits truncated, exceeds int range)
```

**Final output** (the exact wrapped value for the `Long` case depends on its specific bit pattern, but the general shape is):
```
42 (Integer) .intValue() -> 42
3.99 (Double) .intValue() -> 3
-3.99 (Double) .intValue() -> -3
5000000000 (Long) .intValue() -> 705032704
```
This demonstrates concretely why `intValue()` (and the other narrowing conversions on `Number`) must be used with a clear understanding of the actual underlying type and its value range — none of these narrowing conversions throw an exception, even when the result is clearly not a faithful representation of the original number.

## 7. Gotchas & takeaways

> **Narrowing conversions on `Number` (like `intValue()` called on a `Double` or a large `Long`) never throw an exception, even when the conversion loses significant information or produces a nonsensical result** — `doubleValue().intValue()`-style truncation silently discards fractional parts (rounding toward zero, not to the nearest integer), and converting a `long` outside `int`'s range silently truncates bits, producing an unrelated value. Always know the actual range and precision of the underlying value before calling a narrowing `Number` conversion method, or validate explicitly first.

> **`Number` itself provides no arithmetic operators or methods beyond these conversions** — you cannot write `numberA + numberB` directly on two `Number`-typed references (Java's `+` operator doesn't work on `Number`, only on actual primitives or specifically on `String` for concatenation); you must first call the appropriate conversion method (like `doubleValue()`) to obtain a primitive before performing arithmetic, exactly as every example here has done.

- `Number` is the abstract superclass of every numeric wrapper class (`Integer`, `Long`, `Double`, `Float`, `Short`, `Byte`), declaring conversion methods (`intValue()`, `longValue()`, `floatValue()`, `doubleValue()`) every subclass must implement.
- Using `Number` as a parameter or field type lets code handle any numeric wrapper type generically, avoiding separate overloads or manual type-checking for each specific numeric type.
- Widening conversions (like `Integer.doubleValue()`) are always safe and lossless; narrowing conversions (like `Double.intValue()` or a large `Long.intValue()`) can silently lose precision or produce unrelated results, without throwing any exception.
- `Number` provides no arithmetic operators itself — extract a primitive via the appropriate conversion method before performing any arithmetic operation.
