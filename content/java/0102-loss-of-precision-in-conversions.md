---
card: java
gi: 102
slug: loss-of-precision-in-conversions
title: Loss of precision in conversions
---

## 1. What it is

Precision loss happens when a conversion between numeric types cannot represent the original value exactly, even when no narrowing cast is involved. The two main sources are: converting a large integer type (`long`) to a floating-point type (`float`/`double`) that has fewer significant bits than the integer's magnitude requires, and converting between `float` and `double`, where `float` simply cannot store as many significant digits as `double`. Unlike narrowing casts between integer types, this loss is subtle — the value's *type range* looks fine, but its *exact numeric value* silently changes.

```java
long exact   = 9_007_199_254_740_993L;  // one more than 2^53
double asDouble = exact;                 // implicit widening — but double only has 52 mantissa bits
System.out.println(asDouble == exact);   // false! precision was lost in the widening
```

This is surprising because `long → double` is a *widening* conversion (no cast required), yet it can still lose information — widening guarantees no loss of magnitude/range, not no loss of precision.

## 2. Why & when

Precision loss matters whenever exact integer values must survive a trip through floating-point arithmetic:

- Financial calculations where cents must never drift due to floating-point representation (use `BigDecimal` or integer cents instead of `double`).
- Large IDs or timestamps (nanosecond epoch values, snowflake IDs) that exceed `2^53` and get widened to `double` for JSON serialization or display.
- Scientific computation choosing between `float` (less memory, faster, less precise) and `double` (more memory, more precise) for large datasets.
- Any repeated accumulation in a loop, where tiny rounding errors compound over many iterations.

You need to be careful when:
- Comparing floating-point values for exact equality — usually the wrong operation; use a tolerance (epsilon) comparison instead.
- Serializing large `long` IDs into a format that treats them as floating-point numbers (a common bug when integrating with JavaScript, which uses `double` for all numbers).

## 3. Core concept

```java
public class PrecisionDemo {
    public static void main(String[] args) {
        // double has 52 explicit mantissa bits -> exact integers only up to 2^53
        long safeMax = 9_007_199_254_740_992L;   // 2^53, exactly representable
        long unsafe  = safeMax + 1;               // 2^53 + 1, NOT exactly representable

        System.out.println("safeMax as double  == safeMax? " + ((double) safeMax == safeMax));
        System.out.println("unsafe as double   == unsafe?  " + ((double) unsafe == unsafe));
        System.out.println("unsafe as double value: " + (double) unsafe); // rounds to 2^53

        // float has only 23 mantissa bits -> loses precision far sooner
        int intVal = 16_777_217;      // 2^24 + 1
        float asFloat = intVal;        // widening int -> float, but float can't hold 24-bit integers exactly
        System.out.println("intVal as float == intVal? " + (asFloat == intVal));

        // Repeated addition accumulates rounding error
        double sum = 0.0;
        for (int i = 0; i < 10; i++) sum += 0.1;
        System.out.println("0.1 added 10 times: " + sum); // not exactly 1.0
        System.out.println("Equals 1.0?         " + (sum == 1.0));
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Precision loss diagram: long has 64 bits fully usable for integers, double has only 52 mantissa bits so exact integers stop at 2 to the power 53, float has only 23 mantissa bits so exact integers stop at 2 to the power 24.">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Mantissa bits limit which integers a floating type can represent exactly</text>

  <text x="20" y="52" fill="#e6edf3" font-size="9" font-family="monospace">long</text>
  <rect x="20" y="58" width="660" height="18" fill="#1c2430" stroke="#8b949e"/>
  <rect x="20" y="58" width="660" height="18" fill="#6db33f" opacity="0.5"/>
  <text x="350" y="71" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">64-bit integer — exact up to 2^63-1</text>

  <text x="20" y="98" fill="#e6edf3" font-size="9" font-family="monospace">double</text>
  <rect x="20" y="104" width="660" height="18" fill="#1c2430" stroke="#8b949e"/>
  <rect x="20" y="104" width="290" height="18" fill="#79c0ff" opacity="0.5"/>
  <text x="165" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">52-bit mantissa — exact only up to 2^53</text>
  <text x="500" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">beyond here: rounds to nearest representable value</text>

  <text x="20" y="144" fill="#e6edf3" font-size="9" font-family="monospace">float</text>
  <rect x="20" y="150" width="660" height="18" fill="#1c2430" stroke="#8b949e"/>
  <rect x="20" y="150" width="130" height="18" fill="#79c0ff" opacity="0.8"/>
  <text x="85" y="163" fill="#0d1117" font-size="8" text-anchor="middle" font-family="monospace">23-bit mantissa — exact up to 2^24</text>
</svg>

The wider the mantissa, the larger the range of integers a floating-point type can represent exactly before it starts rounding.

## 5. Runnable example

Scenario: an order-processing system that tracks order IDs and total price, first storing IDs as `double` (a common mistake when interoperating with JSON), then hardening it to preserve exact values.

### Level 1 — Basic

```java
public class PrecisionBasic {
    public static void main(String[] args) {
        // Order IDs generated by a snowflake-style ID scheme (large, sequential longs)
        long orderId = 9_007_199_254_740_993L;   // 2^53 + 1

        // Common mistake: converting to double for a "generic numeric" API
        double idAsDouble = orderId;
        long recovered = (long) idAsDouble;

        System.out.println("Original ID:  " + orderId);
        System.out.println("As double:    " + idAsDouble);
        System.out.println("Recovered ID: " + recovered);
        System.out.println("Match?        " + (orderId == recovered));
    }
}
```

**How to run:** `java PrecisionBasic.java`

`orderId` is one more than `2^53`, the largest integer `double` can represent exactly. Widening it to `double` rounds to the nearest representable value — in this case, down to `2^53` itself — losing the `+1`. Casting back to `long` recovers the rounded value, not the original, so `orderId == recovered` is `false`. This is exactly the bug that occurs when large database IDs are serialized through a JSON library or JavaScript client that represents all numbers as `double`.

### Level 2 — Intermediate

Same order system, now keeping IDs as `long` throughout and only converting to `double` for a legitimate floating-point purpose (an average order value), while detecting when a `long` sum has exceeded safe `double` precision.

```java
public class PrecisionIntermediate {

    static boolean fitsExactlyInDouble(long value) {
        // double's mantissa holds 52 explicit bits + 1 implicit = 53 bits of exact integer range
        return Math.abs(value) <= (1L << 53);
    }

    public static void main(String[] args) {
        long[] orderIds = { 1001L, 1002L, 1003L };
        long[] totalsCents = { 250_00L, 999_99L, 1_500_00L };

        // IDs stay as long — never converted to double, no precision risk
        for (long id : orderIds) {
            System.out.println("Order #" + id);
        }

        // Totals: sum as long (exact), only convert to double for a display average
        long sumCents = 0L;
        for (long t : totalsCents) sumCents += t;

        if (!fitsExactlyInDouble(sumCents)) {
            System.out.println("Warning: sum exceeds double's exact integer range");
        }

        double averageCents = (double) sumCents / totalsCents.length; // safe: for display only
        System.out.printf("Average order: $%.2f%n", averageCents / 100.0);
    }
}
```

**How to run:** `java PrecisionIntermediate.java`

Order IDs are never converted to `double` at all — they stay `long` end to end, so no precision loss is possible for identity/lookup purposes. The cents total is also summed as `long` (exact integer arithmetic), and only the final *display* average is converted to `double`, which is an appropriate use since an average is inherently an approximation anyway. `fitsExactlyInDouble` documents the `2^53` boundary explicitly so a future maintainer knows why the check exists, rather than discovering the bug by surprise.

### Level 3 — Advanced

Same order system, now handling money with `BigDecimal` (which avoids floating-point representation error entirely) for a running total that must reconcile exactly with a ledger, and demonstrating why naive `double` accumulation of prices is unsafe for financial code.

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

public class PrecisionAdvanced {

    public static void main(String[] args) {
        // Naive double accumulation of prices — classic financial bug
        double[] pricesDouble = { 0.10, 0.20, 0.30 };
        double totalDouble = 0.0;
        for (double p : pricesDouble) totalDouble += p;
        System.out.println("double total: " + totalDouble);              // 0.6000000000000001
        System.out.println("Equals 0.60?  " + (totalDouble == 0.60));     // false

        // Correct: BigDecimal constructed from String (never from double literals)
        BigDecimal[] pricesExact = {
            new BigDecimal("0.10"),
            new BigDecimal("0.20"),
            new BigDecimal("0.30")
        };
        BigDecimal totalExact = BigDecimal.ZERO;
        for (BigDecimal p : pricesExact) totalExact = totalExact.add(p);
        System.out.println("BigDecimal total: " + totalExact);            // exactly 0.60
        System.out.println("Equals 0.60?      " + (totalExact.compareTo(new BigDecimal("0.60")) == 0));

        // Danger: constructing BigDecimal FROM a double imports its existing imprecision
        BigDecimal fromDoubleBug = new BigDecimal(0.10);
        System.out.println("new BigDecimal(0.10):        " + fromDoubleBug);       // ugly long expansion
        BigDecimal fromDoubleFixed = BigDecimal.valueOf(0.10);
        System.out.println("BigDecimal.valueOf(0.10):    " + fromDoubleFixed);     // clean 0.10

        // Rounding for final display, with explicit rounding mode (never implicit)
        BigDecimal rounded = totalExact.setScale(2, RoundingMode.HALF_UP);
        System.out.println("Rounded total: " + rounded);
    }
}
```

**How to run:** `java PrecisionAdvanced.java`

Summing `0.10 + 0.20 + 0.30` as `double` produces `0.6000000000000001`, not `0.6`, because none of `0.1`, `0.2`, or `0.3` has an exact binary floating-point representation — each carries a tiny rounding error that the sum exposes. `BigDecimal` built from `String` literals stores the decimal digits exactly, so the same sum is exactly `0.60`. Constructing `BigDecimal` directly from a `double` literal (`new BigDecimal(0.10)`) is a well-known trap: it captures the `double`'s *actual* binary value (which is not exactly `0.1`), producing a long, ugly expansion; `BigDecimal.valueOf(double)` avoids this by going through the `double`'s canonical `String` representation first. `setScale` with an explicit `RoundingMode` makes the final rounding decision visible and intentional rather than implicit.

## 6. Walkthrough

Trace the `double` accumulation bug from `main` in the advanced example:

**Adding `0.10 + 0.20`.** Neither `0.10` nor `0.20` has an exact binary representation (much like `1/3` has no exact finite decimal representation). Java's `double` stores the closest representable value to each, and the addition produces the closest representable value to their true sum — which is very close to, but not exactly, `0.30000000000000004`.

**Adding the running total `+ 0.30`.** Adding `0.30` (itself an approximation) to the already-approximate `0.30000000000000004` compounds the rounding, landing on `0.6000000000000001`, one ULP (unit in the last place) away from the mathematically exact `0.6`.

**Comparing `== 0.60`.** Because the accumulated value is not bit-for-bit equal to the literal `0.60` (which is its own closest approximation), the `==` comparison is `false` — this is why floating-point equality comparisons are fragile.

**The `BigDecimal` path.** `new BigDecimal("0.10")` parses the decimal digits `1` and `0` directly into an unscaled integer (`10`) and a scale (`1`), with no binary approximation involved. `add` on two `BigDecimal`s aligns their scales and adds the unscaled integers exactly, so `0.10 + 0.20 + 0.30` produces exactly the `BigDecimal` representing `0.60`.

```
double path:   0.10(approx) + 0.20(approx) = 0.30000000000000004
                                            + 0.30(approx) = 0.6000000000000001
                                            != 0.60 literal

BigDecimal path: "0.10" -> unscaled=10,scale=1
                + "0.20" -> unscaled=20,scale=1  =>  unscaled=30, scale=1
                + "0.30" -> unscaled=30,scale=1  =>  unscaled=60, scale=1  = 6.0 * 10^-1 = 0.60 exactly
```

**Final output.** The program prints the imprecise `double` total, confirms the `==` mismatch, then prints the exact `BigDecimal` total and confirms the match via `compareTo`, and finally shows the `new BigDecimal(double)` trap versus the correct `BigDecimal.valueOf(double)` idiom before rounding for display.

## 7. Gotchas & takeaways

> **`long → double` is a widening conversion, but it is not lossless above `2^53`.** Widening guarantees the value's magnitude fits; it does not guarantee every bit of precision survives. Never round-trip large IDs through `double`.

> **`new BigDecimal(double)` imports the `double`'s hidden imprecision.** Always build `BigDecimal` from a `String` (or use `BigDecimal.valueOf(double)`, which goes through `Double.toString` first) rather than passing a `double` literal directly to the constructor.

- `double` represents integers exactly only up to `2^53`; `float` only up to `2^24`. Beyond that, values silently round to the nearest representable number.
- Never compare `double`/`float` values with `==` after arithmetic — use a tolerance (`Math.abs(a - b) < epsilon`) or, for money, avoid floating-point entirely.
- Use `BigDecimal` (constructed from `String`) for financial or exact-decimal computations; use `long` (e.g., cents) as a simpler alternative when only two decimal places are ever needed.
- Keep IDs, keys, and other values that must remain exact as integer types end-to-end — never convert them to floating-point just because a generic API "accepts a number."
