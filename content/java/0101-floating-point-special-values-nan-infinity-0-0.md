---
card: java
gi: 101
slug: floating-point-special-values-nan-infinity-0-0
title: Floating-point special values (NaN, Infinity, -0.0)
---

## 1. What it is

Java's `float` and `double` follow IEEE 754, which reserves special bit patterns for values that are not ordinary numbers: `NaN` (Not a Number), `POSITIVE_INFINITY`, `NEGATIVE_INFINITY`, and a signed zero (`0.0` and `-0.0` are distinct bit patterns). These arise naturally from arithmetic — dividing by zero does not throw for floating-point types, and some operations (like `0.0 / 0.0`) have no defined numeric result.

```java
double a = 1.0 / 0.0;    // Infinity  (not an exception)
double b = -1.0 / 0.0;   // -Infinity
double c = 0.0 / 0.0;    // NaN
double d = -0.0;         // negative zero, a distinct bit pattern from 0.0
```

This is unlike integer division, where `1 / 0` throws `ArithmeticException`. Floating-point arithmetic is designed to keep computing and propagate the special value through subsequent operations instead of halting.

## 2. Why & when

These values appear whenever floating-point computations touch their edge cases:

- Statistical or scientific code where a division could legitimately be by zero (e.g., normalizing by a zero-variance sample).
- Parsing untrusted numeric input that could produce overflow to `Infinity`.
- Comparing computed results where a bug silently introduced a `NaN` that then poisons every downstream calculation.
- Physics/graphics code where `-0.0` matters for sign-dependent branching (e.g., direction vectors).

You need to actively handle them when:
- A `NaN` must be detected and rejected rather than silently compared as unequal to everything (including itself).
- Sorting or ordering code, where `NaN` interacts unusually with comparison operators.

## 3. Core concept

```java
public class SpecialValuesDemo {
    public static void main(String[] args) {
        double posInf = 1.0 / 0.0;
        double negInf = -1.0 / 0.0;
        double nan    = 0.0 / 0.0;

        System.out.println("1.0/0.0  = " + posInf);
        System.out.println("-1.0/0.0 = " + negInf);
        System.out.println("0.0/0.0  = " + nan);

        // NaN is never equal to anything, including itself
        System.out.println("nan == nan       -> " + (nan == nan));           // false
        System.out.println("Double.isNaN(nan) -> " + Double.isNaN(nan));      // true

        // -0.0 == 0.0 is true with ==, but Double.compare and equals see them as different
        double posZero = 0.0, negZero = -0.0;
        System.out.println("posZero == negZero        -> " + (posZero == negZero)); // true
        System.out.println("Double.compare(pz, nz)     -> " + Double.compare(posZero, negZero)); // 1
        System.out.println("Double.valueOf(pz).equals(negZero) -> " + Double.valueOf(posZero).equals(negZero)); // false

        // Infinity arithmetic
        System.out.println("Infinity + 1     -> " + (posInf + 1));   // Infinity
        System.out.println("Infinity - Infinity -> " + (posInf - posInf)); // NaN
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Floating point special values: dividing by zero gives Infinity or negative Infinity depending on sign, zero divided by zero gives NaN, and NaN never equals anything including itself.">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Division by zero on floating-point types never throws</text>

  <rect x="16" y="34" width="210" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="121" y="50" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">positive / 0.0</text>
  <text x="24" y="70" fill="#e6edf3" font-size="8" font-family="monospace">1.0 / 0.0</text>
  <text x="24" y="86" fill="#79c0ff" font-size="9" font-family="monospace">= Infinity</text>
  <text x="24" y="106" fill="#8b949e" font-size="7" font-family="sans-serif">Larger than any</text>
  <text x="24" y="118" fill="#8b949e" font-size="7" font-family="sans-serif">finite double.</text>
  <text x="24" y="134" fill="#8b949e" font-size="7" font-family="sans-serif">Infinity + x</text>
  <text x="24" y="146" fill="#8b949e" font-size="7" font-family="sans-serif">stays Infinity.</text>

  <rect x="238" y="34" width="210" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="343" y="50" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">negative / 0.0</text>
  <text x="246" y="70" fill="#e6edf3" font-size="8" font-family="monospace">-1.0 / 0.0</text>
  <text x="246" y="86" fill="#79c0ff" font-size="9" font-family="monospace">= -Infinity</text>
  <text x="246" y="106" fill="#8b949e" font-size="7" font-family="sans-serif">Sign of the dividend</text>
  <text x="246" y="118" fill="#8b949e" font-size="7" font-family="sans-serif">determines the sign</text>
  <text x="246" y="134" fill="#8b949e" font-size="7" font-family="sans-serif">of the resulting</text>
  <text x="246" y="146" fill="#8b949e" font-size="7" font-family="sans-serif">infinity.</text>

  <rect x="460" y="34" width="226" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="573" y="50" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">0.0 / 0.0</text>
  <text x="468" y="70" fill="#e6edf3" font-size="8" font-family="monospace">0.0 / 0.0</text>
  <text x="468" y="86" fill="#79c0ff" font-size="9" font-family="monospace">= NaN</text>
  <text x="468" y="106" fill="#8b949e" font-size="7" font-family="sans-serif">Undefined result.</text>
  <text x="468" y="118" fill="#8b949e" font-size="7" font-family="sans-serif">NaN == NaN is false.</text>
  <text x="468" y="134" fill="#8b949e" font-size="7" font-family="sans-serif">Use Double.isNaN()</text>
  <text x="468" y="146" fill="#8b949e" font-size="7" font-family="sans-serif">to detect it.</text>
</svg>

Floating-point division by zero produces a defined special value instead of throwing, and each special value has its own comparison rules.

## 5. Runnable example

Scenario: a sensor-averaging service that computes rolling averages from a stream of readings, where some readings can be zero (a legitimate value) and the divisor (sample count) could itself become zero.

### Level 1 — Basic

```java
public class SpecialValuesBasic {
    public static void main(String[] args) {
        double[] readings = { 10.0, 20.0, 30.0 };
        double sum = 0.0;
        for (double r : readings) sum += r;
        double average = sum / readings.length;
        System.out.println("Average: " + average);

        // Now an empty batch — division by zero on doubles
        double[] empty = {};
        double emptySum = 0.0;
        double emptyAverage = emptySum / empty.length;  // 0.0 / 0 -> NaN, no exception
        System.out.println("Average of empty batch: " + emptyAverage);
    }
}
```

**How to run:** `java SpecialValuesBasic.java`

The normal batch computes `60.0 / 3 = 20.0` as expected. The empty batch divides `0.0` by `0` (an `int` `0`, promoted to `double` for the division) — this does not throw `ArithmeticException` the way integer division would; it silently produces `NaN` and the program keeps running with a nonsensical average.

### Level 2 — Intermediate

Same averaging service, now detecting `NaN` explicitly before reporting a result, and handling the "all readings are Infinity" case that could arise from a runaway sensor.

```java
public class SpecialValuesIntermediate {

    static double computeAverage(double[] readings) {
        double sum = 0.0;
        for (double r : readings) sum += r;
        return sum / readings.length;
    }

    static String describe(double average) {
        if (Double.isNaN(average)) {
            return "no data (NaN) — batch was empty";
        }
        if (Double.isInfinite(average)) {
            return "sensor overflow (" + average + ") — check hardware";
        }
        return String.format("%.2f", average);
    }

    public static void main(String[] args) {
        double[][] batches = {
            { 10.0, 20.0, 30.0 },
            {},                              // empty -> NaN
            { Double.MAX_VALUE, Double.MAX_VALUE }  // sum overflows -> Infinity
        };

        for (double[] batch : batches) {
            double avg = computeAverage(batch);
            System.out.println("Batch of " + batch.length + ": " + describe(avg));
        }
    }
}
```

**How to run:** `java SpecialValuesIntermediate.java`

`Double.isNaN(average)` is the only reliable way to detect `NaN` — comparing `average == Double.NaN` would always be `false`, even when `average` genuinely is `NaN`, because IEEE 754 defines `NaN` as unequal to everything, including itself. `Double.isInfinite` similarly detects both `POSITIVE_INFINITY` and `NEGATIVE_INFINITY`. Summing two `Double.MAX_VALUE` values overflows the finite range of `double` and produces `Infinity` rather than throwing, which `describe` now reports as a sensor problem instead of a plausible-looking number.

### Level 3 — Advanced

Same service, now guarding against `NaN` propagation through a multi-stage pipeline (raw readings → filtered readings → average → alert threshold check), and correctly distinguishing `0.0` from `-0.0` where sign matters for a direction-sensitive sensor.

```java
public class SpecialValuesAdvanced {

    static double[] filterValid(double[] readings) {
        int count = 0;
        for (double r : readings) if (!Double.isNaN(r)) count++;
        double[] out = new double[count];
        int idx = 0;
        for (double r : readings) if (!Double.isNaN(r)) out[idx++] = r;
        return out;
    }

    static double computeAverage(double[] readings) {
        if (readings.length == 0) return Double.NaN;
        double sum = 0.0;
        for (double r : readings) sum += r;
        return sum / readings.length;
    }

    static boolean exceedsThreshold(double average, double threshold) {
        // NaN compared with any relational operator is always false — must check explicitly first
        if (Double.isNaN(average)) {
            throw new IllegalStateException("Cannot evaluate threshold: average is NaN");
        }
        return average > threshold;
    }

    public static void main(String[] args) {
        // Raw stream includes a corrupted NaN reading (e.g., from a bad sensor packet)
        double[] raw = { 12.5, Double.NaN, 15.0, 13.5 };
        double[] valid = filterValid(raw);
        double average = computeAverage(valid);
        System.out.println("Valid readings: " + valid.length + ", average: " + average);

        try {
            boolean alert = exceedsThreshold(average, 20.0);
            System.out.println("Alert: " + alert);
        } catch (IllegalStateException e) {
            System.out.println("Guarded: " + e.getMessage());
        }

        // Sign-sensitive direction sensor: distinguishing 0.0 from -0.0
        double flow = -0.0;
        String direction = (Double.doubleToRawLongBits(flow) != 0L) ? "reverse (at rest)" : "forward (at rest)";
        System.out.println("Flow " + flow + " -> " + direction);

        // Demonstrate why a naive NaN filter must run before averaging, not after
        double[] allNaN = { Double.NaN, Double.NaN };
        double avgAllNaN = computeAverage(filterValid(allNaN));
        System.out.println("All-NaN batch average: " + avgAllNaN); // NaN again, from empty filtered array
    }
}
```

**How to run:** `java SpecialValuesAdvanced.java`

`filterValid` removes `NaN` entries before they can poison the sum — once a single `NaN` enters an addition chain, every subsequent partial sum becomes `NaN` too, since any arithmetic operation involving `NaN` produces `NaN`. `exceedsThreshold` explicitly checks `Double.isNaN` first, because `average > threshold` would silently evaluate to `false` for a `NaN` average — a dangerous false negative for an alerting system, since it looks like "no alert" instead of "couldn't evaluate." `Double.doubleToRawLongBits` exposes the sign bit to distinguish `-0.0` from `0.0`, which `==` cannot do since IEEE 754 defines `-0.0 == 0.0` as `true`. The final case shows that filtering does not always leave data behind: filtering an all-`NaN` batch yields an empty array, and averaging an empty array reintroduces `NaN` via `0/0`, so the top-level caller still needs to handle that case.

## 6. Walkthrough

Trace the program from `main` for the corrupted raw batch `{ 12.5, NaN, 15.0, 13.5 }`:

**Filtering.** `filterValid` scans twice: first to count non-`NaN` entries (3), then to copy them into a correctly sized array `{12.5, 15.0, 13.5}`. The `NaN` value at index 1 fails `!Double.isNaN(r)` and is skipped both times.

**Averaging.** `computeAverage` sums the 3 filtered values: `12.5 + 15.0 + 13.5 = 41.0`, then divides by `3` giving `13.666...`. No special value is produced because the filtered array has no `NaN` and the divisor is non-zero.

**Threshold check.** `exceedsThreshold(13.67, 20.0)` first checks `Double.isNaN(13.67)`, which is `false`, so it proceeds to `13.67 > 20.0`, which is `false`. `alert` prints as `false` — a normal, uneventful path.

**Sign check.** `flow = -0.0`. `Double.doubleToRawLongBits(-0.0)` returns a `long` with the sign bit set (a nonzero value, specifically `0x8000000000000000`), while `doubleToRawLongBits(0.0)` returns `0L`. Because the raw bits are nonzero, the ternary picks `"reverse (at rest)"` — a distinction that `flow == 0.0` (which is `true` for `-0.0`) could never make.

```
raw:      [12.5, NaN, 15.0, 13.5]
filter -> [12.5, 15.0, 13.5]              (NaN dropped)
sum    -> 41.0
average-> 41.0 / 3 = 13.666...
check  -> isNaN? no -> 13.666 > 20.0? no -> alert = false
```

**All-NaN case.** For `allNaN = {NaN, NaN}`, `filterValid` returns an empty array (length 0). `computeAverage` explicitly checks `readings.length == 0` and returns `Double.NaN` directly — without that guard, `0.0 / 0` would produce `NaN` anyway, but the explicit check documents the intent and avoids relying on the coincidence.

## 7. Gotchas & takeaways

> **`NaN` is never equal to anything, including itself.** `x == Double.NaN` and even `x == x` (when `x` is `NaN`) both evaluate to `false`. Always use `Double.isNaN(x)` to test for it.

> **`0.0 == -0.0` is `true`, but they are different bit patterns.** `Double.compare(0.0, -0.0)` returns a positive number and `Double.valueOf(0.0).equals(-0.0)` is `false`. This matters for sign-sensitive code and for `TreeSet`/`TreeMap`, which use `compareTo`, not `==`.

- Floating-point division by zero never throws — it produces `Infinity`, `-Infinity`, or `NaN` depending on the operands.
- Any arithmetic operation with a `NaN` operand produces `NaN` — it propagates silently through a whole computation chain.
- Detect special values explicitly with `Double.isNaN`, `Double.isInfinite`, and (for sign) `Double.doubleToRawLongBits`.
- Filter or guard against `NaN`/`Infinity` as close to the data source as possible, before they can contaminate downstream sums, comparisons, or thresholds.
