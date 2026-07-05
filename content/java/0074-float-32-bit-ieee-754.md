---
card: java
gi: 74
slug: float-32-bit-ieee-754
title: float (32-bit IEEE-754)
---

## 1. What it is

`float` is Java's single-precision, 32-bit floating-point primitive, defined by the IEEE 754 standard. It represents a vast range of real numbers — approximately ±1.4×10⁻⁴⁵ to ±3.4×10³⁸ — but with only about 6–7 significant decimal digits of precision. The 32 bits are divided into 1 sign bit, 8 exponent bits, and 23 mantissa bits.

```java
float temperature = 98.6f;       // suffix f or F required
float ratio       = 1.0f / 3.0f; // 0.33333334 — limited precision
float huge        = 3.4e38f;     // near max value
float tiny        = 1.4e-45f;    // near min positive value
```

A `float` literal requires the suffix `f` (or `F`); without it the compiler treats the number as a `double` and produces a type error on assignment to `float`. The boxed wrapper class is `Float`.

## 2. Why & when

Use `float` when:
- Memory is constrained and you need to store a large array of approximate values (e.g., 3D coordinates, audio samples).
- You are interfacing with graphics APIs (OpenGL, Vulkan, Android Canvas) that work natively in 32-bit floating point.
- The domain has inherently limited precision (e.g., sensor readings, game physics where single-precision is enough).

Prefer `double` (64-bit) for all general-purpose calculations because it provides roughly twice the significant digits and avoids precision errors that accumulate quickly with `float`. **Never use `float` (or `double`) for money** — use `BigDecimal` instead.

## 3. Core concept

```java
// ---- Precision: only ~7 significant digits ----
float a = 1_000_000.5f;
float b = 1_000_000.4f;
System.out.println(a - b);       // 0.0625 — NOT 0.1 (precision lost)

double da = 1_000_000.5;
double db = 1_000_000.4;
System.out.println(da - db);     // 0.09999847412109375 — still imprecise, but closer

// ---- Special values ----
float inf  = Float.POSITIVE_INFINITY;
float nan  = Float.NaN;

System.out.println(1.0f / 0.0f);             // Infinity
System.out.println(-1.0f / 0.0f);            // -Infinity
System.out.println(0.0f / 0.0f);             // NaN
System.out.println(Float.isNaN(nan));         // true
System.out.println(nan == nan);              // false!  (NaN is never equal to itself)
System.out.println(Float.isInfinite(inf));    // true

// ---- Positive and negative zero ----
System.out.println(0.0f == -0.0f);           // true  (they are equal in ==)
System.out.println(1.0f / 0.0f);             // Infinity
System.out.println(1.0f / -0.0f);            // -Infinity (sign differs!)

// ---- Overflow / underflow ----
float overflow   = Float.MAX_VALUE * 2.0f;   // Infinity
float underflow  = Float.MIN_VALUE / 2.0f;   // 0.0 (flush-to-zero)
System.out.println(overflow);                // Infinity
System.out.println(underflow);              // 0.0

// ---- Widening: float → double (safe), narrowing: double → float (lossy) ----
float   f = 3.14159265358979f;
double  d = f;                              // implicit widening
System.out.printf("float  : %.15f%n", (double) f); // only ~7 sig digits filled
System.out.printf("double : %.15f%n", Math.PI);    // full 15 digits

// ---- Float.compare for ordering (handles NaN and -0.0 correctly) ----
System.out.println(Float.compare(1.0f, 2.0f));    // negative
System.out.println(Float.compare(Float.NaN, 1.0f)); // positive (NaN sorts last)
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="float 32-bit layout: 1 sign bit, 8 exponent bits, 23 mantissa bits, with special values Infinity and NaN">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>

  <!-- Bit layout -->
  <rect x="16" y="18" width="668" height="52" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">32-bit float memory layout</text>

  <!-- sign bit -->
  <rect x="24" y="38" width="32" height="26" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="40" y="53" fill="#0d1117" font-size="8" font-weight="bold" text-anchor="middle" font-family="monospace">S</text>

  <!-- exponent bits -->
  <rect x="60" y="38" width="232" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="176" y="53" fill="#0d1117" font-size="8" font-weight="bold" text-anchor="middle" font-family="monospace">Exponent (8 bits)</text>

  <!-- mantissa bits -->
  <rect x="296" y="38" width="380" height="26" rx="3" fill="#8b949e" opacity="0.5"/>
  <text x="486" y="53" fill="#e6edf3" font-size="8" font-weight="bold" text-anchor="middle" font-family="monospace">Mantissa / Significand (23 bits)</text>

  <!-- labels below -->
  <text x="40"  y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="monospace">bit 31</text>
  <text x="176" y="80" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="monospace">bits 30–23</text>
  <text x="486" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">bits 22–0</text>

  <!-- Properties box -->
  <rect x="16" y="92" width="200" height="82" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="116" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">float range</text>
  <line x1="26" y1="114" x2="206" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="127" fill="#e6edf3" font-size="7.5" font-family="monospace">max:  ≈ 3.4 × 10³⁸</text>
  <text x="26" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">min+: ≈ 1.4 × 10⁻⁴⁵</text>
  <text x="26" y="155" fill="#e6edf3" font-size="7.5" font-family="monospace">~7 significant digits</text>
  <text x="26" y="169" fill="#8b949e" font-size="7" font-family="monospace">default (field): 0.0f</text>

  <!-- Special values box -->
  <rect x="228" y="92" width="220" height="82" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="338" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Special values</text>
  <line x1="238" y1="114" x2="438" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="238" y="127" fill="#e6edf3" font-size="7.5" font-family="monospace">Infinity   1.0f/0.0f</text>
  <text x="238" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">-Infinity  -1.0f/0.0f</text>
  <text x="238" y="155" fill="#e6edf3" font-size="7.5" font-family="monospace">NaN        0.0f/0.0f</text>
  <text x="238" y="169" fill="#8b949e" font-size="7" font-family="monospace">NaN != NaN  always</text>

  <!-- vs double box -->
  <rect x="460" y="92" width="224" height="82" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="572" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">float vs double</text>
  <line x1="470" y1="114" x2="674" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="470" y="127" fill="#e6edf3" font-size="7.5" font-family="monospace">float:  32-bit, 7 digits</text>
  <text x="470" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">double: 64-bit, 15 digits</text>
  <text x="470" y="155" fill="#6db33f" font-size="7.5" font-family="monospace">prefer double general use</text>
  <text x="470" y="169" fill="#8b949e" font-size="7" font-family="monospace">float: arrays/graphics only</text>
</svg>

`float` packs 1 sign bit, 8 exponent bits, and 23 mantissa bits into 32 bits, yielding about 7 significant decimal digits and special values `Infinity` and `NaN`.

## 5. Runnable example

Scenario: a temperature sensor analyser — collects sensor readings, detects anomalies, and produces statistics. The example grows from a simple average calculation to handling invalid (NaN) readings and finally to comparing `float` vs `double` precision for accumulated sums.

### Level 1 — Basic

```java
public class FloatBasic {
    public static void main(String[] args) {
        float[] readings = {36.6f, 37.2f, 38.5f, 36.9f, 37.0f};

        float sum = 0.0f;
        float min = Float.MAX_VALUE;
        float max = -Float.MAX_VALUE;

        for (float r : readings) {
            sum += r;
            if (r < min) min = r;
            if (r > max) max = r;
        }

        float avg = sum / readings.length;

        System.out.printf("Readings : ");
        for (float r : readings) System.out.printf("%.1f ", r);
        System.out.println();
        System.out.printf("Min : %.1f °C%n", min);
        System.out.printf("Max : %.1f °C%n", max);
        System.out.printf("Avg : %.2f °C%n", avg);
        System.out.printf("Sum : %.4f   (float accumulation)%n", sum);
    }
}
```

**How to run:** `java FloatBasic.java`

`Float.MAX_VALUE` is the largest positive finite `float` (≈ 3.4×10³⁸). Initialising `min` to `Float.MAX_VALUE` ensures any real reading will be smaller on the first comparison. `%.2f` in `printf` formats the float to two decimal places, which is sufficient for temperature precision. Note that the `sum` printed with `%.4f` may not be exactly the mathematical sum of the five values — this is the nature of floating-point accumulation.

### Level 2 — Intermediate

Same sensor system: extend to handle missing/error readings encoded as `Float.NaN`, skip them in statistics, and flag them as anomalies.

```java
public class FloatIntermediate {

    static boolean isAnomaly(float current, float previous, float threshold) {
        if (Float.isNaN(current)) return true;
        return Math.abs(current - previous) > threshold;
    }

    public static void main(String[] args) {
        // NaN marks a failed sensor read; Infinity marks a sensor overflow
        float[] readings = {36.6f, 37.2f, Float.NaN, 39.5f, 38.8f, Float.POSITIVE_INFINITY, 37.1f};
        float threshold = 1.5f;   // max acceptable jump between readings

        System.out.println("Sensor readings anomaly report");
        System.out.println("Threshold: " + threshold + " °C per step");
        System.out.println();

        float sum   = 0.0f;
        int   valid = 0;
        float prev  = Float.NaN;

        for (int i = 0; i < readings.length; i++) {
            float r = readings[i];
            boolean anomaly = Float.isNaN(r) || Float.isInfinite(r)
                || (!Float.isNaN(prev) && Math.abs(r - prev) > threshold);

            System.out.printf("  [%d] %8s  %s%n",
                i,
                Float.isNaN(r) ? "NaN" : Float.isInfinite(r) ? "Inf" : String.format("%.1f°C", r),
                anomaly ? "⚠ ANOMALY" : "OK");

            if (!Float.isNaN(r) && !Float.isInfinite(r)) {
                sum += r;
                valid++;
            }
            prev = r;
        }

        System.out.println();
        if (valid > 0) {
            System.out.printf("Valid readings : %d%n", valid);
            System.out.printf("Average        : %.2f °C%n", sum / valid);
        } else {
            System.out.println("No valid readings.");
        }
    }
}
```

**How to run:** `java FloatIntermediate.java`

Testing `Float.isNaN(r)` is necessary because `r == Float.NaN` always returns `false` — NaN is never equal to itself by the IEEE 754 standard. Similarly, `Float.isInfinite(r)` correctly detects both `POSITIVE_INFINITY` and `NEGATIVE_INFINITY`. The valid readings accumulator skips NaN and infinite values, preventing them from contaminating the average.

### Level 3 — Advanced

Same sensor system: demonstrate the precision loss from accumulating many `float` values compared with `double`, show the Kahan summation algorithm to compensate, and measure the difference.

```java
public class FloatAdvanced {

    // Kahan compensated summation — reduces floating-point error in long sums
    static float kahanSum(float[] values) {
        float sum  = 0.0f;
        float comp = 0.0f;   // running compensation
        for (float v : values) {
            float y = v - comp;
            float t = sum + y;
            comp = (t - sum) - y;
            sum  = t;
        }
        return sum;
    }

    public static void main(String[] args) {
        // Simulate 10,000 temperature readings all equal to 0.1f
        int N = 10_000;
        float[] readings = new float[N];
        java.util.Arrays.fill(readings, 0.1f);
        double exact = N * 0.1;   // mathematically correct: 1000.0

        // Naive float sum
        float naiveFloat = 0.0f;
        for (float r : readings) naiveFloat += r;

        // Kahan float sum
        float kahanFloat = kahanSum(readings);

        // Naive double sum (for comparison)
        double naiveDouble = 0.0;
        for (float r : readings) naiveDouble += r;   // widened to double each step

        System.out.printf("Expected           : %.6f%n", exact);
        System.out.printf("Naive float sum    : %.6f  error: %.6f%n",
            naiveFloat, Math.abs(naiveFloat - exact));
        System.out.printf("Kahan float sum    : %.6f  error: %.6f%n",
            kahanFloat, Math.abs(kahanFloat - exact));
        System.out.printf("Naive double sum   : %.6f  error: %.6f%n",
            naiveDouble, Math.abs(naiveDouble - exact));

        System.out.println();
        // float[] vs double[] memory footprint
        System.out.printf("float[%,d]  memory: ~%,d bytes%n", N, N * 4);
        System.out.printf("double[%,d] memory: ~%,d bytes%n", N, N * 8);

        // Verify Float.compare handles -0.0 and NaN
        System.out.println();
        float negZero = -0.0f;
        float posZero =  0.0f;
        System.out.println("-0.0f == 0.0f          : " + (negZero == posZero));     // true
        System.out.println("Float.compare(-0f,0f)  : " + Float.compare(negZero, posZero)); // -1
        System.out.println("Float.compare(NaN,1.0f): " + Float.compare(Float.NaN, 1.0f));  // +1
    }
}
```

**How to run:** `java FloatAdvanced.java`

Summing 10,000 values of `0.1f` naively with `float` accumulates rounding error with each step, because `0.1f` cannot be represented exactly in binary floating point. After 10,000 additions the naive float sum may differ from the correct value by several units in the last place. Kahan summation keeps a running compensation term (`comp`) that captures the rounding error on each step and feeds it back on the next, dramatically reducing the accumulated error. Widening each `float` to `double` before addition also reduces error, at the cost of 2× memory. `Float.compare(-0.0f, 0.0f)` returns negative (−0.0 sorts before +0.0) even though `==` considers them equal, which matters for consistent sort ordering.

## 6. Walkthrough

Execution trace through `FloatAdvanced.main`:

**Array setup.** `Arrays.fill(readings, 0.1f)` stores 10,000 copies of the float nearest to 0.1. In IEEE 754 single-precision, the nearest representable value is approximately 0.100000001490116. The true mathematical sum of 10,000 copies should be 1000.0.

**Naive float accumulation.** `naiveFloat += r` widens both operands to float, adds them, and rounds the result back to float. Each addition may introduce a small rounding error. Over 10,000 steps these errors accumulate. The final `naiveFloat` may be off by roughly 0.01–0.05 from 1000.0.

**Kahan summation.** Before each addition the compensation `comp` is subtracted from `v`, giving a corrected value `y = v - comp`. The update `t = sum + y` rounds, but `(t - sum) - y` recovers the rounding error for the next iteration. This keeps the accumulated error at roughly a single-step rounding error regardless of how many values are summed.

**Double accumulation.** Each `float` value is widened to `double` (64-bit) before addition. The double representation of `0.1f` is the same bit pattern with 29 trailing zero mantissa bits, but subsequent arithmetic is in 64-bit space so rounding errors are much smaller per step. The final double sum is typically within machine epsilon of 1000.0.

**`-0.0f` comparison.** IEEE 754 defines `+0.0 == -0.0` as true, so `negZero == posZero` is `true`. However, `Float.compare` uses a total ordering where `-0.0 < +0.0`, returning a negative integer. `NaN` is placed after all finite and infinite values in `Float.compare`'s total ordering, so `Float.compare(NaN, 1.0f)` returns a positive integer even though `NaN > 1.0f` is `false`.

## 7. Gotchas & takeaways

> **`float` literals need the `f` suffix.** Writing `float x = 3.14;` is a compile error — `3.14` is a `double` literal. Use `3.14f`. Without the suffix the compiler reports "possible lossy conversion from double to float."

> **NaN is never equal to itself.** `Float.NaN == Float.NaN` is always `false`. Use `Float.isNaN(x)` to check for NaN — never use `==` against `Float.NaN`.

- `float` is 32-bit single-precision IEEE 754, providing about 6–7 significant decimal digits.
- `float` literals require the `f` (or `F`) suffix; bare decimal literals are `double` by default.
- Division by zero does not throw; it produces `Infinity` (or `-Infinity` or `NaN` for `0.0f/0.0f`).
- `NaN` comparisons always return `false` (even `NaN == NaN`); use `Float.isNaN()`.
- `Float.compare` provides a total ordering consistent with `Comparator`, handling `-0.0` and `NaN` correctly; `==` does not.
- Prefer `double` for general arithmetic. Reserve `float` for memory-sensitive arrays or APIs that require 32-bit floats.
- Never use `float` or `double` for monetary calculations — use `BigDecimal`.
