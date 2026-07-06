---
card: java
gi: 277
slug: integer-max-value-min-value-constants
title: Integer.MAX_VALUE / MIN_VALUE constants
---

## 1. What it is

`Integer.MAX_VALUE` and `Integer.MIN_VALUE` are `public static final` constants defined on the `Integer` wrapper class, representing the largest and smallest values a 32-bit `int` can hold: `2147483647` and `-2147483648` respectively. Every other numeric wrapper class (`Long`, `Short`, `Byte`, `Double`, `Float`) provides its own equivalent `MAX_VALUE`/`MIN_VALUE` constants, sized appropriately for that type.

```java
public class MaxMinDemo {
    public static void main(String[] args) {
        System.out.println("Integer.MAX_VALUE: " + Integer.MAX_VALUE); // 2147483647
        System.out.println("Integer.MIN_VALUE: " + Integer.MIN_VALUE); // -2147483648

        int nearMax = Integer.MAX_VALUE;
        int overflowed = nearMax + 1; // silently WRAPS AROUND to Integer.MIN_VALUE!
        System.out.println("MAX_VALUE + 1 = " + overflowed);
    }
}
```

`Integer.MAX_VALUE + 1` does not throw an exception or produce a larger number — it silently overflows, wrapping around to `Integer.MIN_VALUE` (`-2147483648`), since `int` arithmetic in Java uses fixed-width, two's-complement representation with no automatic overflow detection; this is exactly the kind of surprising behaviour understanding these constants helps you anticipate and guard against.

## 2. Why & when

Understanding these boundary constants matters for writing correct arithmetic that doesn't silently produce wrong results when values get large, and for validating input against a type's actual representable range.

- **Detecting or preventing overflow before it happens** — comparing a value against `Integer.MAX_VALUE` (or checking whether an operation's result would exceed it) before performing arithmetic that could overflow is a standard defensive technique, especially when accumulating sums or computing counts that could plausibly grow very large.
- **Choosing the right numeric type for the data's actual range** — if a value could legitimately exceed roughly two billion (like a running total of many large numbers, or a timestamp measured in milliseconds since a fixed date, which can exceed `int`'s range surprisingly quickly), `long` (with `Long.MAX_VALUE` roughly 9.2 quintillion) is the appropriate type, not `int`.
- **Validating that parsed or received values fit within the expected type's range** — data coming from external sources (user input, files, network responses) might contain numbers that, while textually valid, exceed what the target primitive type can actually represent; checking against `MAX_VALUE`/`MIN_VALUE` (or catching the exception `parseInt` throws for out-of-range text, covered in the walkthrough) helps catch this before it causes silent corruption.

Use `Integer.MAX_VALUE`/`MIN_VALUE` (and the equivalent constants on other numeric wrapper classes) whenever your code needs to know a type's actual representable boundaries — for validating input ranges, detecting potential overflow before it silently corrupts a calculation, or choosing an appropriately-sized type for data that might grow large.

## 3. Core concept

```java
public class MaxMinCore {
    static boolean wouldOverflow(int a, int b) {
        long sum = (long) a + (long) b; // widen to long FIRST, so the addition itself cannot overflow
        return sum > Integer.MAX_VALUE || sum < Integer.MIN_VALUE;
    }

    public static void main(String[] args) {
        System.out.println(wouldOverflow(2_000_000_000, 2_000_000_000)); // true — would overflow as int
        System.out.println(wouldOverflow(100, 200));                       // false — safely within range
    }
}
```

`wouldOverflow` widens both operands to `long` *before* adding them, since `long` can safely hold any value two `int`s could ever sum to without itself overflowing — this lets the method safely check whether the *would-be* `int` result would exceed `Integer.MAX_VALUE` or fall below `Integer.MIN_VALUE`, without ever actually performing the risky `int` addition that could silently wrap around.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The int type range spans from Integer MIN_VALUE to Integer MAX_VALUE, adding one past MAX_VALUE silently wraps around to MIN_VALUE rather than throwing an exception or growing larger">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <line x1="60" y1="80" x2="540" y2="80" stroke="#8b949e" stroke-width="2"/>
  <text x="60" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">MIN_VALUE</text>
  <text x="60" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-2147483648</text>

  <text x="540" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">MAX_VALUE</text>
  <text x="540" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2147483647</text>

  <path d="M 540 80 Q 570 40 60 80" stroke="#f85149" stroke-width="1.5" fill="none" marker-end="url(#arrow)"/>
  <text x="300" y="35" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">MAX_VALUE + 1 wraps around to MIN_VALUE</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">int arithmetic silently overflows — no exception, no warning, just a wrapped result.</text>
</svg>

`int` values silently wrap around past `MAX_VALUE`, landing back at `MIN_VALUE`, with no exception thrown.

## 5. Runnable example

Scenario: an order-total accumulator vulnerable to silent overflow, evolved from a naive summing loop into one that safely detects and prevents overflow, then hardened with a proper switch to `long` for genuinely large-scale accumulation.

### Level 1 — Basic

```java
public class MaxMinBasic {
    public static void main(String[] args) {
        int a = Integer.MAX_VALUE;
        int b = 1;
        int sum = a + b; // silently overflows!
        System.out.println("Sum: " + sum); // -2147483648, NOT 2147483648
    }
}
```

**How to run:** `java MaxMinBasic.java`

`a + b` silently wraps around to `Integer.MIN_VALUE` instead of throwing any exception or producing the mathematically correct, larger value — this is the core danger `MAX_VALUE`/`MIN_VALUE` awareness helps you anticipate.

### Level 2 — Intermediate

Same accumulation idea, now with an explicit overflow check performed before each addition, using the widen-to-`long` technique to safely detect the problem before it corrupts the running total.

```java
public class MaxMinIntermediate {
    static int safeAdd(int a, int b) {
        long result = (long) a + (long) b;
        if (result > Integer.MAX_VALUE || result < Integer.MIN_VALUE) {
            throw new ArithmeticException("int overflow: " + a + " + " + b + " = " + result);
        }
        return (int) result;
    }

    public static void main(String[] args) {
        System.out.println(safeAdd(100, 200)); // 300, fine

        try {
            safeAdd(Integer.MAX_VALUE, 1);
        } catch (ArithmeticException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java MaxMinIntermediate.java`

`safeAdd` computes the sum using `long` arithmetic first (which cannot overflow for any two `int` inputs, since `long`'s range vastly exceeds `int`'s), then checks whether that mathematically correct result would actually fit back into an `int` — if not, it throws a clear `ArithmeticException` instead of silently returning a wrapped, wrong value.

### Level 3 — Advanced

Same order-total scenario, now demonstrating the more robust, production-appropriate fix: switching the accumulator to `long` entirely, since order totals summed across many transactions could plausibly exceed `int`'s roughly two-billion-unit range in a real, high-volume system — alongside validation that individually parsed values themselves fit within expected bounds.

```java
public class MaxMinAdvanced {
    static long accumulateTotal(int[] amounts) {
        long total = 0; // long: safe even if this sum would exceed int's range
        for (int amount : amounts) {
            total += amount; // safe: long has vastly more headroom than int
        }
        return total;
    }

    static void validateFitsInInt(long value, String context) {
        if (value > Integer.MAX_VALUE || value < Integer.MIN_VALUE) {
            throw new IllegalArgumentException(context + " value " + value + " does not fit in an int");
        }
    }

    public static void main(String[] args) {
        int[] amounts = new int[10];
        java.util.Arrays.fill(amounts, Integer.MAX_VALUE / 2); // large values, summed many times

        long total = accumulateTotal(amounts);
        System.out.println("Total (as long, no overflow): " + total);

        try {
            validateFitsInInt(total, "grand total");
        } catch (IllegalArgumentException e) {
            System.out.println("Validation caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java MaxMinAdvanced.java`

`accumulateTotal` uses a `long` accumulator specifically because summing ten values each close to `Integer.MAX_VALUE / 2` would clearly exceed what a plain `int` accumulator could safely hold; `validateFitsInInt` then explicitly checks whether the final `long` total would actually fit back into an `int`, demonstrating the complete, safe pattern: use a wider type for accumulation, then validate explicitly at the boundary if a narrower type is genuinely required downstream.

## 6. Walkthrough

Trace `main` in `MaxMinAdvanced` step by step.

**`Arrays.fill(amounts, Integer.MAX_VALUE / 2)`.** `Integer.MAX_VALUE / 2` is `2147483647 / 2 = 1073741823` (integer division truncates). Every element of the ten-element `amounts` array is set to this value.

**`accumulateTotal(amounts)`.** `total` (a `long`) starts at `0`. The loop adds `1073741823` ten times: `total = 1073741823 * 10 = 10737418230`. Since `total` is declared as `long`, this addition proceeds safely — `10737418230` fits comfortably within `long`'s vastly larger range (`Long.MAX_VALUE` is over 9.2 quintillion), so no overflow occurs at any point during the accumulation, even though this sum (`10,737,418,230`) already exceeds `Integer.MAX_VALUE` (`2,147,483,647`) by roughly five times.

**`System.out.println("Total (as long, no overflow): " + total)`.** Prints `"Total (as long, no overflow): 10737418230"`.

**`validateFitsInInt(total, "grand total")`.** Checks `total > Integer.MAX_VALUE`: `10737418230 > 2147483647` is `true`, so `IllegalArgumentException("grand total value 10737418230 does not fit in an int")` is thrown immediately.

**The `catch` block.** Catches this exception. Prints `"Validation caught: grand total value 10737418230 does not fit in an int"`.

```
amounts = [1073741823, 1073741823, ..., 1073741823]  (10 elements)

accumulateTotal (long total):
  total = 0
  + 1073741823 (x10) -> total = 10737418230   (safe: long has huge headroom)

validateFitsInInt(10737418230, "grand total"):
  10737418230 > Integer.MAX_VALUE (2147483647)? -> true
  -> throws IllegalArgumentException("grand total value 10737418230 does not fit in an int")
```

**Final output.**
```
Total (as long, no overflow): 10737418230
Validation caught: grand total value 10737418230 does not fit in an int
```
Had `accumulateTotal` used an `int` accumulator instead of `long`, this sum would have silently overflowed and wrapped around to some incorrect, much smaller (or even negative) value with no exception or warning at all — using `long` for the accumulation, and only checking against `Integer.MAX_VALUE`/`MIN_VALUE` at the point where a narrower type is genuinely needed, is exactly the safe, correct pattern this example demonstrates.

## 7. Gotchas & takeaways

> **`int` arithmetic in Java never throws an exception on overflow — it silently wraps around** — this is fundamentally different from some other languages or explicit checked-arithmetic modes; code that assumes "if this were going to overflow, I'd get an error" is simply wrong for ordinary `int`/`long` arithmetic in Java. If overflow safety matters, you must check for it explicitly (as shown here) or use `Math.addExact`, `Math.multiplyExact`, and similar methods (covered in the upcoming `Math` class topic), which *do* throw `ArithmeticException` on overflow.

> **`Integer.MIN_VALUE`'s absolute value cannot be represented as a positive `int`** — `Math.abs(Integer.MIN_VALUE)` actually returns `Integer.MIN_VALUE` itself (a negative number!), rather than its true positive magnitude, because that true magnitude (`2147483648`) is one greater than `Integer.MAX_VALUE` and simply cannot fit in an `int` at all. This is a genuinely surprising, well-documented edge case worth remembering whenever working with `Math.abs` near the boundaries of `int`'s range.

- `Integer.MAX_VALUE` (`2147483647`) and `Integer.MIN_VALUE` (`-2147483648`) mark the exact boundaries of what a 32-bit `int` can represent; every numeric wrapper class provides equivalent constants for its own type.
- `int` arithmetic silently wraps around on overflow, with no exception thrown by default — exceeding `MAX_VALUE` by adding wraps around to a value near `MIN_VALUE`, not a larger positive number.
- Detect potential overflow by widening operands to a larger type (like `long`) before performing arithmetic, then checking whether the result would actually fit in the narrower target type.
- `Math.abs(Integer.MIN_VALUE)` returns `Integer.MIN_VALUE` itself (still negative), since its true positive magnitude cannot be represented within `int`'s range — a well-known, surprising edge case.
