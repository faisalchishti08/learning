---
card: java
gi: 100
slug: integer-overflow-underflow-behavior
title: Integer overflow / underflow behavior
---

## 1. What it is

Java's integer types (`byte`, `short`, `int`, `long`) have a fixed number of bits and wrap silently when an arithmetic result exceeds their range — there is no automatic promotion to a bigger type and no exception thrown. Overflow happens when a value goes above `MAX_VALUE`; underflow happens when it goes below `MIN_VALUE`. Both wrap around using two's-complement arithmetic, as if the number line were a circle that connects `MAX_VALUE` back to `MIN_VALUE`.

```java
int max = Integer.MAX_VALUE;   // 2147483647
int over = max + 1;            // -2147483648 (wraps to MIN_VALUE)

int min = Integer.MIN_VALUE;   // -2147483648
int under = min - 1;           // 2147483647 (wraps to MAX_VALUE)
```

This is a deliberate design choice inherited from C: raw arithmetic operators (`+`, `-`, `*`) are fast and never check bounds. Detecting overflow is the programmer's job, using either manual checks or the `Math.*Exact` helper methods.

## 2. Why & when

Overflow bugs show up whenever a running total, counter, or accumulated size can exceed the type's range:

- Summing a large array of `int` values into an `int` accumulator (should often accumulate into a `long` instead).
- Computing `(a + b) / 2` for array midpoints — classic binary-search overflow bug when `a + b` exceeds `Integer.MAX_VALUE`.
- Multiplying dimensions (`width * height * channels`) for buffer sizing.
- Counting events over a long-running process where an `int` counter eventually wraps to negative.

You need to actively guard against overflow when:
- The values are user-controlled or unbounded (file sizes, request counts, timestamps).
- The computation is safety- or money-critical, where a silent wrap could cause a wrong but plausible-looking result.

## 3. Core concept

```java
public class OverflowDemo {
    public static void main(String[] args) {
        // Overflow: MAX_VALUE + 1 wraps to MIN_VALUE
        int a = Integer.MAX_VALUE;
        System.out.println("MAX_VALUE       = " + a);
        System.out.println("MAX_VALUE + 1   = " + (a + 1));

        // Underflow: MIN_VALUE - 1 wraps to MAX_VALUE
        int b = Integer.MIN_VALUE;
        System.out.println("MIN_VALUE       = " + b);
        System.out.println("MIN_VALUE - 1   = " + (b - 1));

        // Multiplication overflow is easy to trigger and easy to miss
        int big1 = 100_000;
        int big2 = 100_000;
        System.out.println("100000 * 100000 = " + (big1 * big2)); // wraps, not 10_000_000_000

        // The classic midpoint bug
        int lo = 1_500_000_000, hi = 2_000_000_000;
        int badMid = (lo + hi) / 2;              // overflows before dividing
        int goodMid = lo + (hi - lo) / 2;         // safe: no intermediate overflow
        System.out.println("bad mid  = " + badMid);
        System.out.println("good mid = " + goodMid);

        // Math.*Exact throws instead of wrapping
        try {
            Math.addExact(Integer.MAX_VALUE, 1);
        } catch (ArithmeticException e) {
            System.out.println("addExact threw: " + e.getMessage());
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Integer wraparound diagram: a circular number line where MAX_VALUE plus 1 wraps to MIN_VALUE, and MIN_VALUE minus 1 wraps to MAX_VALUE.">
  <rect x="8" y="8" width="684" height="194" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">int range wraps like a circle — no exception, no warning</text>

  <circle cx="350" cy="118" r="80" fill="none" stroke="#8b949e" stroke-width="1.5"/>
  <circle cx="350" cy="38" r="4" fill="#6db33f"/>
  <text x="350" y="28" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">0</text>

  <circle cx="430" cy="118" r="4" fill="#79c0ff"/>
  <text x="452" y="122" fill="#79c0ff" font-size="8.5" font-family="monospace">MAX_VALUE (2147483647)</text>

  <circle cx="270" cy="118" r="4" fill="#79c0ff"/>
  <text x="120" y="122" fill="#79c0ff" font-size="8.5" font-family="monospace" text-anchor="end">MIN_VALUE (-2147483648)</text>

  <path d="M 430 118 A 8 8 0 0 1 424 128" fill="none" stroke="#6db33f" stroke-width="2"/>
  <text x="440" y="150" fill="#6db33f" font-size="8" font-family="monospace">+1 wraps here →</text>

  <path d="M 270 118 A 8 8 0 0 0 276 128" fill="none" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="150" fill="#6db33f" font-size="8" font-family="monospace">← -1 wraps here</text>

  <text x="350" y="188" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">MAX_VALUE + 1 == MIN_VALUE   |   MIN_VALUE - 1 == MAX_VALUE</text>
</svg>

Arithmetic on fixed-width integers wraps around the range boundary silently — visualize it as a clock face, not a line with edges.

## 5. Runnable example

Scenario: a ticket-sales counter that tracks total tickets sold and total revenue in cents, first naively with `int`, then hardened against overflow.

### Level 1 — Basic

```java
public class OverflowBasic {
    public static void main(String[] args) {
        int ticketsSold = 0;
        int revenueCents = 0;

        int[] sales = { 500_000_000, 500_000_000, 500_000_000, 500_000_000, 500_000_000 };
        for (int saleCents : sales) {
            revenueCents += saleCents;   // int accumulator — will overflow
            ticketsSold++;
        }

        System.out.println("Tickets sold: " + ticketsSold);
        System.out.println("Revenue (cents): " + revenueCents); // wrong: wrapped negative
    }
}
```

**How to run:** `java OverflowBasic.java`

Five sales of 500,000,000 cents sum to 2,500,000,000 — bigger than `Integer.MAX_VALUE` (2,147,483,647). The `int` accumulator wraps partway through the loop, producing a negative "revenue" that is nonsensical for a real business report, and the program gives no indication anything went wrong.

### Level 2 — Intermediate

Same ticket system, now accumulating into a `long` (which has enough range for realistic revenue) and validating the result is non-negative before reporting.

```java
public class OverflowIntermediate {
    public static void main(String[] args) {
        int ticketsSold = 0;
        long revenueCents = 0L;   // widened accumulator avoids the wrap for this range

        int[] sales = { 500_000_000, 500_000_000, 500_000_000, 500_000_000, 500_000_000 };
        for (int saleCents : sales) {
            revenueCents += saleCents;  // int saleCents promoted to long before adding
            ticketsSold++;
        }

        System.out.println("Tickets sold: " + ticketsSold);
        System.out.println("Revenue (cents): " + revenueCents);
        System.out.printf("Revenue (dollars): $%,.2f%n", revenueCents / 100.0);

        if (revenueCents < 0) {
            throw new IllegalStateException("Revenue went negative — overflow detected");
        }
    }
}
```

**How to run:** `java OverflowIntermediate.java`

Switching the accumulator from `int` to `long` gives 63 bits of usable magnitude instead of 31, comfortably covering realistic revenue totals. Each `int` value is implicitly widened to `long` before the addition, so the running sum never wraps for these inputs. A defensive `if (revenueCents < 0)` check is added anyway — widening only postpones the problem, it does not eliminate it, so a sanity check documents the assumption and would catch a future regression.

### Level 3 — Advanced

Same ticket system, now with an untrusted per-sale amount (could be attacker-controlled or corrupted), using `Math.addExact` and `Math.multiplyExact` so any genuine overflow throws instead of silently producing a wrong total, and a `BigInteger` fallback path for values known to be extreme.

```java
import java.math.BigInteger;

public class OverflowAdvanced {

    static long accumulateSafely(long[] centsPerSale) {
        long total = 0L;
        for (long cents : centsPerSale) {
            total = Math.addExact(total, cents);   // throws ArithmeticException on overflow
        }
        return total;
    }

    public static void main(String[] args) {
        long[] normalSales = { 500_000_000L, 500_000_000L, 500_000_000L };
        long total = accumulateSafely(normalSales);
        System.out.println("Safe total (cents): " + total);

        // Simulate a corrupted/attacker-controlled batch that would overflow even a long accumulator
        long[] extremeSales = { Long.MAX_VALUE - 10, 20 };
        try {
            accumulateSafely(extremeSales);
        } catch (ArithmeticException e) {
            System.out.println("Detected overflow: " + e.getMessage());
            // Fall back to arbitrary-precision arithmetic for this batch
            BigInteger safeTotal = BigInteger.ZERO;
            for (long cents : extremeSales) {
                safeTotal = safeTotal.add(BigInteger.valueOf(cents));
            }
            System.out.println("BigInteger total: " + safeTotal);
        }

        // multiplyExact guards a pixel-buffer-size style calculation
        try {
            int width = 100_000, height = 100_000;
            int pixels = Math.multiplyExact(width, height); // overflows int range
        } catch (ArithmeticException e) {
            System.out.println("Detected multiply overflow: " + e.getMessage());
        }
    }
}
```

**How to run:** `java OverflowAdvanced.java`

`Math.addExact` performs the same addition as `+` but checks the result against the type's range and throws `ArithmeticException` instead of wrapping — this converts a silent data-corruption bug into a loud, catchable failure. The extreme batch deliberately exceeds even `long`'s range, so `accumulateSafely` throws; the `catch` block then recomputes the same batch using `BigInteger`, which has no fixed bit width and never overflows, at the cost of being slower and boxed. `Math.multiplyExact` shows the same pattern for multiplication, which overflows far more easily than addition because the result grows so much faster.

## 6. Walkthrough

Trace `accumulateSafely(extremeSales)` with `extremeSales = { Long.MAX_VALUE - 10, 20 }`:

**First iteration.** `total = 0`, `cents = Long.MAX_VALUE - 10`. `Math.addExact(0, Long.MAX_VALUE - 10)` computes the sum, checks it is within `long` range (it is — `Long.MAX_VALUE - 10` is not the max), and returns `Long.MAX_VALUE - 10`. `total` is updated.

**Second iteration.** `cents = 20`. `Math.addExact(Long.MAX_VALUE - 10, 20)` computes `Long.MAX_VALUE + 10` internally. Because this exceeds `Long.MAX_VALUE`, `addExact` detects the overflow condition (checking the sign bits of the operands versus the result) and throws `ArithmeticException` with a message like "long overflow" before returning any value.

**Caught in `main`.** The `catch (ArithmeticException e)` block runs. It prints the message, then re-processes `extremeSales` using `BigInteger.add`, which represents integers as arbitrary-length digit arrays with no upper bound, so the true sum (`Long.MAX_VALUE + 10`) is computed and printed exactly.

```
total=0                      + (MAX-10)  -> addExact checks range -> OK   -> total = MAX-10
total=MAX-10                 + 20        -> addExact checks range -> FAIL -> throws ArithmeticException
                                                                         |
                                                                         v
                                                        catch block: BigInteger fallback
                                                        BigInteger.ZERO.add(MAX-10).add(20) = exact sum
```

**Final output.** The program prints the safe total for the normal batch, the caught overflow message for the extreme batch, the exact `BigInteger` sum, and the caught multiply-overflow message for the pixel calculation — every potential wraparound in the program is either avoided or explicitly detected.

## 7. Gotchas & takeaways

> **Overflow and underflow never throw by default.** `int`, `long`, `+`, `-`, and `*` wrap silently. If you need detection, you must opt in with `Math.addExact`, `Math.subtractExact`, `Math.multiplyExact`, or `Math.toIntExact`.

> **Widening the accumulator type only raises the ceiling, it does not remove it.** A `long` accumulator overflows too, just at a much larger number — always match the accumulator's range to the true worst-case input, or use `Math.addExact`/`BigInteger` when the worst case is unbounded.

- Overflow wraps `MAX_VALUE` around to `MIN_VALUE` (and vice versa) using two's-complement rules — visualize the range as a circle, not a line.
- Multiplication overflows far more easily than addition because products grow quadratically; check it explicitly with `Math.multiplyExact`.
- The classic `(lo + hi) / 2` midpoint bug is avoided with `lo + (hi - lo) / 2`, which never overflows if `lo` and `hi` are both valid indices.
- For truly unbounded magnitudes (arbitrary-precision needs), use `java.math.BigInteger`, which never overflows but is slower and not a primitive.
