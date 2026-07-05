---
card: java
gi: 96
slug: implicit-widening-conversions
title: Implicit widening conversions
---

## 1. What it is

A widening conversion happens automatically when a value of a smaller numeric type is used where a larger numeric type is expected, without any explicit cast. The conversion is implicit (no syntax required) because no information is lost — the destination type can represent every value the source type can.

Widening primitive conversions allowed by the JLS (§5.1.2):

```
byte → short → int → long → float → double
char → int → long → float → double
```

Reading the chain left to right: a `byte` widens to `short`, `int`, `long`, `float`, or `double`. A `char` widens to `int`, `long`, `float`, or `double`. Note: `byte` and `short` do **not** widen to `char`; those require explicit casts.

```java
int    i = 42;
long   l = i;        // int → long (widening, implicit, OK)
double d = i;        // int → double (widening, implicit, OK)

byte b  = 10;
short s = b;         // byte → short (widening, OK)

// char c = b;       // byte → char: NOT an implicit widening — needs explicit cast
```

## 2. Why & when

Widening conversions happen silently in three situations:
1. **Assignment** — `long x = someInt;`
2. **Method invocation** — passing an `int` to a method that declares `long`.
3. **Arithmetic promotion** — when operands of mixed types appear in an expression (e.g., `int + long` → both promoted to `long`).

You need to be aware of widening because:
- `int → float` and `long → float`, as well as `long → double`, can **lose precision** (floats have 23 bits of mantissa; not all 32-bit int values are exactly representable). The conversion itself never throws an exception, but the result may surprise you.
- Arithmetic promotion silently promotes `byte`/`short`/`char` operands to `int` in almost all arithmetic expressions, which is why `byte b = b1 + b2;` is a compile error.

## 3. Core concept

```java
public class WideningDemo {

    public static void main(String[] args) {
        // ---- Basic widening on assignment ----
        byte  b = 100;
        short s = b;    // byte → short
        int   i = s;    // short → int
        long  l = i;    // int → long
        float f = l;    // long → float (may lose precision for large longs)
        double d = f;   // float → double

        System.out.printf("byte=%d short=%d int=%d long=%d float=%.1f double=%.1f%n",
            b, s, i, l, f, d);

        // ---- char widens to int ----
        char ch = 'A';    // Unicode code point 65
        int  codePoint = ch;   // char → int: 65
        System.out.println("'A' as int: " + codePoint);

        // ---- Precision loss: int → float ----
        int    big  = 123_456_789;
        float  bigF = big;         // 123456792 — nearest representable float
        System.out.printf("int: %d  float: %.0f  (difference: %d)%n",
            big, bigF, (long) bigF - big);

        // ---- long → double precision loss ----
        long   bigL  = 9_999_999_999_999_999L;
        double bigD  = bigL;       // not exactly representable
        System.out.printf("long: %d  double: %.0f%n", bigL, bigD);

        // ---- Arithmetic promotion ----
        byte x = 10, y = 20;
        // byte result = x + y;   // COMPILE ERROR: + promotes both to int → need cast
        int  result = x + y;      // OK
        System.out.println("byte+byte = int: " + result);

        // ---- Mixed arithmetic ----
        int  seconds = 3600;
        long hours   = seconds / 3600L;  // int / long: seconds promoted to long
        System.out.println("hours: " + hours);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Widening chain: byte and char both widen toward double through int, long, float; arrows show safe widening; int to float and long to double marked as potentially losing precision">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Widening primitive conversion chain — implicit, no cast required</text>

  <!-- type boxes -->
  <!-- byte -->
  <rect x="18" y="38" width="54" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="45" y="56" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">byte</text>
  <text x="45" y="73" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">8 bit</text>

  <!-- char -->
  <rect x="18" y="110" width="54" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="45" y="128" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">char</text>
  <text x="45" y="145" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">16 bit</text>

  <!-- short -->
  <rect x="108" y="38" width="54" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="135" y="56" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">short</text>
  <text x="135" y="73" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">16 bit</text>

  <!-- int -->
  <rect x="210" y="70" width="54" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="237" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">int</text>
  <text x="237" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">32 bit</text>

  <!-- long -->
  <rect x="318" y="70" width="54" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">long</text>
  <text x="345" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">64 bit</text>

  <!-- float -->
  <rect x="428" y="70" width="54" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="455" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">float</text>
  <text x="455" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">32 bit IEEE</text>

  <!-- double -->
  <rect x="538" y="70" width="62" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="569" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">double</text>
  <text x="569" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">64 bit IEEE</text>

  <!-- arrows: byte → short -->
  <line x1="72" y1="52" x2="106" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <!-- short → int -->
  <line x1="162" y1="52" x2="205" y2="77" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <!-- char → int -->
  <line x1="72" y1="124" x2="205" y2="94" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <!-- int → long -->
  <line x1="264" y1="84" x2="316" y2="84" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <!-- long → float (precision warning) -->
  <line x1="372" y1="84" x2="426" y2="84" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4 2" marker-end="url(#arr2)"/>
  <!-- float → double -->
  <line x1="482" y1="84" x2="536" y2="84" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <!-- int → float direct -->
  <path d="M264,72 Q346,44 426,72" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2" marker-end="url(#arr2)"/>

  <defs>
    <marker id="arr"  markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 Z" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 Z" fill="#8b949e"/>
    </marker>
  </defs>

  <!-- legend -->
  <line x1="18" y1="158" x2="40" y2="158" stroke="#6db33f" stroke-width="1.5"/>
  <text x="44" y="162" fill="#6db33f" font-size="7.5" font-family="sans-serif">safe (no precision loss)</text>
  <line x1="180" y1="158" x2="202" y2="158" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4 2"/>
  <text x="206" y="162" fill="#8b949e" font-size="7.5" font-family="sans-serif">may lose precision (int/long → float, long → double)</text>
</svg>

Dashed arrows mark conversions that are still implicit but may silently lose precision for large values.

## 5. Runnable example

Scenario: a sensor data pipeline that collects raw `byte` readings, aggregates them into `int` totals, computes `long` timestamps, and produces `double` averages — widening conversions happen at each stage automatically.

### Level 1 — Basic

```java
public class WideningBasic {
    public static void main(String[] args) {
        // Raw sensor reading stored as byte (0–127 range)
        byte rawReading = 72;    // e.g., temperature in tenths of a degree

        // Stage 1: byte → int (widening, implicit)
        int count   = 10;        // number of readings
        int sumTemp = rawReading * count;  // byte promoted to int in arithmetic
        System.out.printf("Raw: %d  Sum: %d%n", rawReading, sumTemp);

        // Stage 2: int → long (widening, implicit) for large totals
        long totalMilliseconds = sumTemp * 60_000L;   // int * long → long
        System.out.printf("Total ms: %d%n", totalMilliseconds);

        // Stage 3: int → double for average
        double average = sumTemp / (double) count;    // explicit cast to get floating division
        // Without cast: sumTemp / count → integer division
        System.out.printf("Average: %.1f%n", average);

        // char → int widening
        char sensorId = 'A';
        int  numericId = sensorId;   // char → int: 65
        System.out.printf("Sensor '%c' = id %d%n", sensorId, numericId);
    }
}
```

**How to run:** `java WideningBasic.java`

`rawReading * count` promotes `byte rawReading` to `int` automatically before the multiplication — you do not need a cast. `sumTemp * 60_000L` promotes `int sumTemp` to `long` because one operand (`60_000L`) is already `long`. `char sensorId = 'A'` widened to `int numericId` gives the Unicode code point 65 without a cast. The only explicit cast needed here is `(double)` in `sumTemp / (double) count` to force floating-point division — widening for `/` would not happen automatically without it.

### Level 2 — Intermediate

Same pipeline: accumulate readings in a loop, pass mixed types to methods, and demonstrate method invocation widening — where an `int` argument widens to `long` or `double` in the method signature.

```java
public class WideningIntermediate {

    static double computeAverage(long sum, int count) {   // note: sum is long
        return (double) sum / count;   // long / int → both promoted to double? No — cast needed
    }

    static void printStats(String label, double value) {   // accepts any numeric type
        System.out.printf("  %-20s %.4f%n", label, value);
    }

    public static void main(String[] args) {
        byte[] readings = {68, 71, 73, 70, 72, 69, 74, 71, 73, 72};

        // Accumulate: byte → int promotion in every +=
        int sumInt = 0;
        for (byte r : readings) {
            sumInt += r;   // r widens to int before +=
        }

        // int → long widening on method call: sumInt passed as long
        double avg = computeAverage(sumInt, readings.length);

        // int → double widening on method call
        printStats("Average temperature:", avg);
        printStats("Min possible (byte):", Byte.MIN_VALUE);   // byte → double
        printStats("Max possible (byte):", Byte.MAX_VALUE);   // byte → double

        // Arithmetic promotion: short + short → int
        short s1 = 100, s2 = 27;
        // short diff = s1 - s2;   // ERROR: int result of - cannot be assigned to short
        int diff = s1 - s2;        // OK — explicit int
        System.out.printf("  %-20s %d%n", "Difference:", diff);

        // float → double widening
        float  fSum = sumInt;      // int → float (exact for values < 2^24)
        double dSum = fSum;        // float → double
        System.out.printf("  %-20s %.1f%n", "Sum (via float→double):", dSum);
    }
}
```

**How to run:** `java WideningIntermediate.java`

`sumInt` is an `int`. When passed to `computeAverage(long sum, ...)`, the compiler automatically widens it to `long` — no cast required. Similarly, `Byte.MIN_VALUE` (a `byte`) passed to `printStats(String, double)` widens to `double` through the chain `byte → short → int → long → float → double`. The expression `s1 - s2` promotes both `short` operands to `int` (arithmetic promotion rule), so the result is `int` — it cannot be assigned to `short` without an explicit cast, even if the value fits.

### Level 3 — Advanced

Same pipeline: demonstrate precision loss when widening large `int` or `long` to `float`/`double`, show how method overloading resolution interacts with widening, and accumulate sensor data with mixed types in a realistic analytics scenario.

```java
import java.util.*;

public class WideningAdvanced {

    // Overloaded methods — widening selects the best match
    static void process(long value)   { System.out.println("  long: "   + value); }
    static void process(double value) { System.out.println("  double: " + value); }

    public static void main(String[] args) {
        // ---- Precision loss: int → float ----
        int exact = 123_456_789;
        float approx = exact;   // widening: int → float
        System.out.printf("int    : %d%n", exact);
        System.out.printf("float  : %.0f%n", approx);          // 123456792 — rounded!
        System.out.printf("error  : %d%n", (int) approx - exact);

        // ---- Precision loss: long → double ----
        long bigL = 9_007_199_254_740_993L;  // 2^53 + 1 — first integer not exactly in double
        double bigD = bigL;
        System.out.printf("long   : %d%n", bigL);
        System.out.printf("double : %.0f%n", bigD);            // 9007199254740992 — off by 1

        // ---- Overload resolution with widening ----
        int  iv = 100;
        // process(iv) → int widens to long (preferred over double — narrower widening wins)
        process(iv);          // picks long overload

        byte bv = 50;
        // process(bv) → byte widens to long (byte→short→int→long, or byte→short→int→float→double)
        // JLS: widening to long is closer than to double
        process(bv);          // picks long overload

        // ---- Realistic pipeline ----
        List<Byte> sensorData = new ArrayList<>();
        Random rng = new Random(42);
        for (int i = 0; i < 1000; i++) {
            sensorData.add((byte) (rng.nextInt(60) + 40));  // 40–99
        }

        long   sumLong   = 0;
        int    minVal    = Integer.MAX_VALUE;
        int    maxVal    = Integer.MIN_VALUE;
        for (byte r : sensorData) {
            sumLong += r;    // byte → long (widening on +=)
            if (r < minVal) minVal = r;   // byte → int
            if (r > maxVal) maxVal = r;   // byte → int
        }

        double avgDouble = (double) sumLong / sensorData.size();  // long → double
        System.out.printf("Readings : %d%n", sensorData.size());
        System.out.printf("Sum      : %d%n", sumLong);
        System.out.printf("Average  : %.3f%n", avgDouble);
        System.out.printf("Min/Max  : %d / %d%n", minVal, maxVal);
    }
}
```

**How to run:** `java WideningAdvanced.java`

`123_456_789` widened to `float` becomes `123_456_792` — the nearest representable IEEE 754 single-precision value. No exception is thrown; the loss is silent. `9_007_199_254_740_993L` (2^53 + 1) widened to `double` rounds to `9_007_199_254_740_992.0` (2^53) because `double` only has 52 explicit mantissa bits. For overload resolution, when an `int` is passed to `process`, the JLS prefers the widening that requires fewer steps — `int → long` is one step, `int → float → double` is two steps (or even `int → double` counts as one, but the `long` overload matches first in the fixed method-resolution order). In the sensor loop, `sumLong += r` widens `byte r` to `long` silently on every iteration — a common and correct pattern for avoiding `int` overflow when summing many readings.

## 6. Walkthrough

Trace the arithmetic promotion in `WideningIntermediate.main`:

**`sumInt += r` in the loop.** `r` is a `byte` (e.g., 68). The `+=` compound assignment internally performs `sumInt = (int)(sumInt + r)`. The `+` operator promotes both operands to `int`: `int sumInt + int(r)`. The result is `int`. The compound assignment re-narrows to `int` (which is already `int`, so no change). After all 10 iterations, `sumInt = 713`.

**`computeAverage(sumInt, readings.length)`.** The method signature is `computeAverage(long sum, int count)`. The caller passes `sumInt` (an `int`) and `readings.length` (an `int`). The compiler widens `sumInt` → `long` at the call site. Inside `computeAverage`: `(double) sum / count`. The cast makes `sum` → `double`. Then `double / int` — `count` widens to `double`. Result: `713.0 / 10.0 = 71.3`.

**`printStats("Min possible:", Byte.MIN_VALUE)`.** `Byte.MIN_VALUE` is `-128` (a `byte`). The method signature is `printStats(String, double)`. Widening chain: `byte → short → int → long → float → double` — but the compiler applies this in one step (not iteratively). The value `-128.0` is exact in `double`.

```
Widening chain for computeAverage(sumInt, readings.length):
  sumInt (int, 713) → long (713L)       [at call site]
  return (double) sum / count
    → (double) 713L = 713.0             [explicit cast]
    → 713.0 / 10                        [int count]
    → 713.0 / 10.0 = 71.3              [int widens to double for /]
```

## 7. Gotchas & takeaways

> **`int → float` and `long → double` can silently lose precision.** There is no compile-time warning or runtime exception. If you need exact integer arithmetic at large magnitudes (>2^24 for float, >2^53 for double), stay in `long` or use `BigDecimal`.

> **`byte` and `short` operands in arithmetic expressions are always promoted to `int`.** Adding two `byte` values gives an `int`, not a `byte`. To store the result in a `byte` or `short`, you need an explicit narrowing cast — which itself can overflow.

- Implicit widening: `byte → short → int → long → float → double` and `char → int → long → float → double`.
- `byte` and `char` do not widen to each other — that requires an explicit cast.
- `byte`/`short`/`char` operands are promoted to `int` in all arithmetic expressions (JLS §5.6.1).
- Method invocation widens arguments to match the declared parameter type automatically.
- `int/long → float` and `long → double` are safe conversions but can lose magnitude precision for large values.
- Mixed-type arithmetic (e.g., `int + long`) promotes the smaller type to the larger; `int + double` → `double`.
- Use `(double) intVal / divisor` to force floating-point division; `intVal / (double) divisor` works too — just be explicit.
