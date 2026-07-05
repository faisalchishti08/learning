---
card: java
gi: 104
slug: subtraction
title: Subtraction -
---

## 1. What it is

The binary `-` operator subtracts its right operand from its left operand. Like `+`, `-`, `*`, and `/`, it applies binary numeric promotion to its operands first: both are promoted to a common type (following `byte`/`short`/`char` → `int` → `long` → `float` → `double`), and the result has that common type. Unlike `+`, `-` has no overload for `String` — subtracting is purely numeric, so `"a" - "b"` does not compile.

```java
int a = 10, b = 3;
System.out.println(a - b);        // 7

byte x = 5, y = 2;
int diff = x - y;                  // byte - byte promotes to int, result type is int, not byte
System.out.println(diff);          // 3

double d = 5.5 - 2;                // int promoted to double: 3.5
System.out.println(d);
```

`-` is also overloaded as a **unary** operator (negation), which is a separate, distinct operator from binary subtraction — covered in its own topic — but it is worth noting here that `5 - -3` (subtraction of a negated value) is valid and equals `8`.

## 2. Why & when

Subtraction shows up anywhere a difference, remaining amount, or delta needs computing:

- Inventory management: `stock - unitsSold` to compute remaining stock.
- Time/date arithmetic: `endTimestamp - startTimestamp` to compute elapsed duration (careful with overflow on `long` epoch millis over huge ranges).
- Geometry and graphics: `x2 - x1` to compute a vector or distance component.
- Financial reconciliation: `expected - actual` to compute a discrepancy.

The same overflow/underflow and precision-loss rules that apply to addition apply to subtraction (see [Integer overflow / underflow behavior](0100-integer-overflow-underflow-behavior.md) and [Loss of precision in conversions](0102-loss-of-precision-in-conversions.md)): `Integer.MIN_VALUE - 1` wraps to `Integer.MAX_VALUE`, and subtracting two nearly equal large `double` values can amplify relative floating-point error (a phenomenon called "catastrophic cancellation").

## 3. Core concept

```java
public class SubtractionDemo {
    public static void main(String[] args) {
        // Basic int subtraction
        int stock = 100, sold = 37;
        System.out.println("Remaining: " + (stock - sold));   // 63

        // byte/short promote to int before subtracting
        byte b1 = 20, b2 = 5;
        int byteDiff = b1 - b2;      // type is int, even though operands are byte
        System.out.println("byte diff (as int): " + byteDiff);

        // Mixed numeric types promote to the widest type present
        long bigNumber = 10_000_000_000L;
        int  smallNumber = 3;
        long result = bigNumber - smallNumber;  // int promoted to long
        System.out.println("long - int: " + result);

        // Underflow wraps silently, just like addition overflow
        int minInt = Integer.MIN_VALUE;
        System.out.println("MIN_VALUE - 1 = " + (minInt - 1));   // wraps to MAX_VALUE

        // Catastrophic cancellation: subtracting nearly equal large doubles loses precision
        double big = 1_000_000.123456;
        double slightlyLess = 1_000_000.123455;
        System.out.println("Difference: " + (big - slightlyLess)); // not exactly 0.000001
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Subtraction promotion diagram: byte minus byte promotes both to int before subtracting, giving an int result even though the inputs were byte. Long minus int promotes the int to long.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Binary numeric promotion applies to - just like + and *</text>

  <rect x="16" y="34" width="320" height="116" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="176" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">byte b1 = 20; byte b2 = 5;</text>
  <text x="30" y="70" fill="#e6edf3" font-size="8" font-family="monospace">b1 (byte) ──┐</text>
  <text x="30" y="86" fill="#e6edf3" font-size="8" font-family="monospace">b2 (byte) ──┤ both promoted to int</text>
  <text x="30" y="102" fill="#79c0ff" font-size="8.5" font-family="monospace">int result = b1 - b2 = 15</text>
  <text x="30" y="122" fill="#6db33f" font-size="7.5" font-family="sans-serif">Result TYPE is int, even</text>
  <text x="30" y="136" fill="#6db33f" font-size="7.5" font-family="sans-serif">though both operands were byte.</text>

  <rect x="352" y="34" width="332" height="116" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="518" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">long big; int small;</text>
  <text x="366" y="70" fill="#e6edf3" font-size="8" font-family="monospace">big (long) ──┐</text>
  <text x="366" y="86" fill="#e6edf3" font-size="8" font-family="monospace">small (int) ──┤ int widened to long</text>
  <text x="366" y="102" fill="#79c0ff" font-size="8.5" font-family="monospace">long result = big - small</text>
  <text x="366" y="122" fill="#6db33f" font-size="7.5" font-family="sans-serif">The wider type present</text>
  <text x="366" y="136" fill="#6db33f" font-size="7.5" font-family="sans-serif">always wins the promotion.</text>
</svg>

Both operands of `-` are promoted to the widest numeric type among them before the subtraction happens.

## 5. Runnable example

Scenario: a warehouse stock tracker that computes remaining inventory after sales, first with simple `int` math, then hardened for underflow (can't sell more than you have) and for computing elapsed time between stock checks.

### Level 1 — Basic

```java
public class SubtractionBasic {
    public static void main(String[] args) {
        int stockMorning = 150;
        int unitsSold = 42;

        int stockEvening = stockMorning - unitsSold;
        System.out.println("Stock this morning: " + stockMorning);
        System.out.println("Units sold: " + unitsSold);
        System.out.println("Stock this evening: " + stockEvening);

        // A second sale that would oversell the remaining stock
        int secondSale = 200;
        int afterSecondSale = stockEvening - secondSale;
        System.out.println("After overselling: " + afterSecondSale);  // negative — nonsensical for stock
    }
}
```

**How to run:** `java SubtractionBasic.java`

`150 - 42 = 108` is a normal, expected subtraction. The second sale of `200` units exceeds the `108` remaining, so `108 - 200 = -92` — a negative stock count that is mathematically correct but business-nonsensical, since a warehouse cannot hold negative units. The program does not catch this; it just prints the impossible number.

### Level 2 — Intermediate

Same tracker, now validating that a sale cannot reduce stock below zero, and computing elapsed time between two stock checks using `long` epoch milliseconds.

```java
public class SubtractionIntermediate {

    static int sell(int currentStock, int quantity) {
        if (quantity > currentStock) {
            throw new IllegalArgumentException(
                "Cannot sell " + quantity + " units; only " + currentStock + " in stock");
        }
        return currentStock - quantity;
    }

    public static void main(String[] args) {
        int stock = 150;
        stock = sell(stock, 42);
        System.out.println("Stock after valid sale: " + stock);

        try {
            stock = sell(stock, 200);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        // Elapsed time between two stock checks, using long epoch millis
        long checkedAt9am  = 1_700_000_000_000L;
        long checkedAt5pm  = checkedAt9am + (8L * 60 * 60 * 1000); // 8 hours later
        long elapsedMillis = checkedAt5pm - checkedAt9am;
        long elapsedHours  = elapsedMillis / (60 * 60 * 1000);
        System.out.println("Elapsed hours between checks: " + elapsedHours);
    }
}
```

**How to run:** `java SubtractionIntermediate.java`

`sell` now validates `quantity > currentStock` *before* subtracting, converting an impossible negative-stock state into a clear, immediate `IllegalArgumentException` rather than a silently wrong number that could propagate through the rest of the system. The elapsed-time calculation uses `long` for millisecond timestamps because `int` would overflow at values around 24.8 days worth of milliseconds — epoch timestamps are always `long` in Java's time APIs for exactly this reason.

### Level 3 — Advanced

Same tracker, now handling stock across multiple warehouses with `Math.subtractExact` to catch any accidental underflow of a `long` accounting total, and demonstrating the catastrophic-cancellation pitfall when subtracting nearly equal `double` measurements (e.g., computing a small weight difference from two large scale readings).

```java
public class SubtractionAdvanced {

    static long totalAcrossWarehouses(long[] stockLevels) {
        long total = 0L;
        for (long level : stockLevels) total = Math.addExact(total, level);
        return total;
    }

    static long safeSubtract(long total, long amount) {
        long result = Math.subtractExact(total, amount);  // throws on underflow instead of wrapping
        if (result < 0) {
            throw new IllegalStateException("Total stock cannot go negative: " + result);
        }
        return result;
    }

    public static void main(String[] args) {
        long[] warehouseStock = { 5000L, 3200L, 1800L };
        long total = totalAcrossWarehouses(warehouseStock);
        System.out.println("Total stock across warehouses: " + total);

        total = safeSubtract(total, 4000L);
        System.out.println("After large sale: " + total);

        try {
            total = safeSubtract(total, 10_000_000L);
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        // Catastrophic cancellation: two nearly-equal large scale readings
        double scaleReadingBefore = 45231.784512;
        double scaleReadingAfter  = 45231.784498;
        double itemWeight = scaleReadingBefore - scaleReadingAfter;
        System.out.println("Computed item weight: " + itemWeight);
        // The true difference is 0.000014, but subtracting two large doubles
        // this close together can expose the accumulated rounding error in each reading.

        // Safer: measure the difference directly with a scale that reports deltas,
        // or round to the precision the hardware actually supports.
        double rounded = Math.round(itemWeight * 1_000_000.0) / 1_000_000.0;
        System.out.println("Rounded to 6 decimal places: " + rounded);
    }
}
```

**How to run:** `java SubtractionAdvanced.java`

`Math.subtractExact` behaves like `-` but throws `ArithmeticException` if the result overflows or underflows the `long` range, giving an explicit signal instead of silent wraparound — `safeSubtract` layers a business-rule check (`result < 0`) on top for the domain-specific "stock can't be negative" invariant, which `Math.subtractExact` alone would not catch since `-6,000,000` is a perfectly valid `long` value. The scale-reading subtraction demonstrates catastrophic cancellation: both readings are large numbers (around 45,231) with only a tiny true difference (0.000014) between them; each reading individually carries some floating-point rounding error in its low-order digits, and subtracting two nearly equal numbers can amplify that relative error dramatically in the result, since most of the significant digits cancel out. Rounding to the precision the hardware actually supports is a pragmatic mitigation, though the fundamentally more robust fix is to avoid computing small differences from large absolute values whenever the underlying instrument can report the delta directly.

## 6. Walkthrough

Trace `safeSubtract(total, 10_000_000L)` where `total = 6000` (after the prior sale):

**`Math.subtractExact(6000L, 10_000_000L)`.** This computes `6000 - 10_000_000 = -9_994_000`. Since `-9,994,000` is well within `long`'s range (`long` can represent values down to roughly `-9.2 * 10^18`), no overflow occurs at the `long`-arithmetic level, and `subtractExact` returns `-9_994_000` normally — it does not throw here, because "underflow" in the overflow-detection sense only means the true mathematical result doesn't fit in 64 bits, which this result does.

**The business-rule check.** `safeSubtract` then checks `result < 0`, which is `true` for `-9,994,000`. It throws `IllegalStateException` with a message embedding the negative result, distinct from the `ArithmeticException` that `Math.subtractExact` would throw for a genuine 64-bit range violation.

**Caught in `main`.** The `catch (IllegalStateException e)` block prints the rejection message. `total` is never actually reassigned to the negative value because the exception is thrown before `safeSubtract` returns.

```
total = 6000
requested amount = 10,000,000
Math.subtractExact(6000, 10000000) = -9,994,000   (fits in long range, no ArithmeticException)
                                          |
                                          v
                              business check: result < 0 ? yes
                                          |
                                          v
                          throw IllegalStateException("... -9994000")
```

**Final output.** The program prints the total after the earlier valid sale, then the caught rejection message for the oversized sale, then moves on to the scale-reading section, printing the raw (possibly imprecise) weight difference followed by the version rounded to six decimal places.

## 7. Gotchas & takeaways

> **`Math.subtractExact` only detects 64-bit range overflow, not domain-specific invalid states.** A perfectly valid negative `long` (like `-9,994,000`) will not trigger it — you still need your own business-rule checks (e.g., `result < 0` for a stock count) layered on top.

> **Subtracting two nearly equal large floating-point numbers can lose most of the result's precision (catastrophic cancellation).** If you only need a small delta, consider whether the source can report the delta directly instead of computing it from two large absolute readings.

- `-` applies binary numeric promotion, exactly like `+`: `byte`/`short`/`char` operands are promoted to `int` before subtracting, and the result matches the widest operand type present.
- Unlike `+`, `-` has no `String` overload — it is always numeric.
- Underflow (going below `MIN_VALUE`) wraps silently for `int`/`long`, just like overflow does for addition; use `Math.subtractExact` for detection.
- Validate business invariants (stock, balances) explicitly after subtracting — the arithmetic itself has no concept of "can't go negative."
