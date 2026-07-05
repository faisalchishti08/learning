---
card: java
gi: 97
slug: explicit-narrowing-conversions-casting
title: Explicit narrowing conversions (casting)
---

## 1. What it is

A narrowing conversion moves a value from a larger numeric type to a smaller one, potentially losing information. Java requires an explicit cast `(targetType) value` for every narrowing conversion — the compiler will not do it implicitly. The developer must acknowledge the risk.

Narrowing conversions defined by the JLS (§5.1.3):

```
short, char, byte, int, long, float, double
  ↓ any step left (or from float/double to integer)
```

Common narrowing casts:

```java
double d = 9.99;
int    i = (int) d;      // 9 — fractional part truncated, no rounding
long   l = 1_000_000_000_000L;
int    n = (int) l;      // -727379968 — upper bits discarded, result wraps
int    x = 260;
byte   b = (byte) x;     // 4 — 260 mod 256 = 4
```

The cast never throws an exception — even extreme truncation or wrapping happens silently.

## 2. Why & when

You need a narrowing cast when:
- Dividing screen coordinates stored as `double` or `float` into pixel-sized `int` values.
- Packing a range-checked `int` into a `byte` for a protocol byte stream.
- Converting a computed `long` that you know fits into `int` (e.g., after a `Math.min`).
- Reading raw binary data: `(byte)(stream.read())` to preserve bit patterns.

The risks are:
- **Truncation** — `(int) 9.9` is 9, not 10. Java truncates toward zero.
- **Overflow/wrapping** — `(byte) 260` is 4 because Java keeps only the low-order bits (260 % 256 = 4).
- **Sign change** — `(byte) 200` is -56 because 200 in unsigned binary is `1100 1000`; interpreted as signed two's complement it is -56.

## 3. Core concept

```java
public class NarrowingDemo {

    public static void main(String[] args) {
        // ---- double → int: truncation toward zero ----
        double pi   = 3.14159;
        int    piInt = (int) pi;   // 3 — fraction dropped
        System.out.println("(int) 3.14159 = " + piInt);

        double neg  = -3.9;
        int    negInt = (int) neg;  // -3 — truncated toward zero (not floor)
        System.out.println("(int) -3.9 = " + negInt);

        // ---- long → int: high bits discarded ----
        long bigLong = 3_000_000_000L;     // > Integer.MAX_VALUE (2147483647)
        int  wrapped = (int) bigLong;      // -1294967296 — wrapping
        System.out.println("(int) 3_000_000_000L = " + wrapped);

        // ---- int → byte: low 8 bits only ----
        int  val260 = 260;
        byte b260   = (byte) val260;   // 4 (260 & 0xFF = 4)
        System.out.println("(byte) 260 = " + b260);

        int  val200 = 200;
        byte b200   = (byte) val200;   // -56 (200 in signed byte = -56)
        System.out.println("(byte) 200 = " + b200);

        // ---- int → char: low 16 bits, reinterpreted as Unicode code point ----
        int  codePoint = 65;
        char letter    = (char) codePoint;   // 'A'
        System.out.println("(char) 65 = " + letter);

        // ---- Safe narrowing with range check ----
        long safeL = 42L;
        if (safeL >= Integer.MIN_VALUE && safeL <= Integer.MAX_VALUE) {
            int safeI = (int) safeL;   // guaranteed no wrapping
            System.out.println("Safe: " + safeI);
        }

        // ---- float → int: NaN becomes 0, Infinity becomes MAX_VALUE ----
        System.out.println("(int) NaN      = " + (int) Float.NaN);       // 0
        System.out.println("(int) +Inf     = " + (int) Float.POSITIVE_INFINITY); // 2147483647
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three narrowing cast results: double 9.99 to int gives 9 (truncation); long 3000000000 to int gives negative number (wrapping); int 200 to byte gives negative 56 (sign change). All require explicit cast.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Narrowing cast — explicit (TargetType) required; may silently corrupt value</text>

  <!-- double → int: truncation -->
  <rect x="16" y="32" width="210" height="118" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="121" y="48" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">double → int: truncation</text>
  <text x="24" y="65" fill="#e6edf3" font-size="8" font-family="monospace">double d = 9.99;</text>
  <text x="24" y="80" fill="#e6edf3" font-size="8" font-family="monospace">int i = (int) d;</text>
  <text x="24" y="96" fill="#6db33f" font-size="8" font-family="monospace">i == 9</text>
  <text x="24" y="112" fill="#8b949e" font-size="7" font-family="sans-serif">Fraction discarded.</text>
  <text x="24" y="124" fill="#8b949e" font-size="7" font-family="sans-serif">Truncates toward zero.</text>
  <text x="24" y="136" fill="#8b949e" font-size="7" font-family="sans-serif">-3.9 → -3 (not -4).</text>

  <!-- long → int: wrapping -->
  <rect x="238" y="32" width="210" height="118" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="343" y="48" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">long → int: wrapping</text>
  <text x="246" y="65" fill="#e6edf3" font-size="8" font-family="monospace">long l = 3_000_000_000L;</text>
  <text x="246" y="80" fill="#e6edf3" font-size="8" font-family="monospace">int i = (int) l;</text>
  <text x="246" y="96" fill="#8b949e" font-size="8" font-family="monospace">i == -1294967296</text>
  <text x="246" y="112" fill="#8b949e" font-size="7" font-family="sans-serif">High 32 bits discarded.</text>
  <text x="246" y="124" fill="#8b949e" font-size="7" font-family="sans-serif">Low 32 bits kept and</text>
  <text x="246" y="136" fill="#8b949e" font-size="7" font-family="sans-serif">reinterpreted as signed.</text>

  <!-- int 200 → byte: sign change -->
  <rect x="460" y="32" width="226" height="118" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="573" y="48" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">int → byte: sign change</text>
  <text x="468" y="65" fill="#e6edf3" font-size="8" font-family="monospace">int x = 200; // 0xC8</text>
  <text x="468" y="80" fill="#e6edf3" font-size="8" font-family="monospace">byte b = (byte) x;</text>
  <text x="468" y="96" fill="#8b949e" font-size="8" font-family="monospace">b == -56</text>
  <text x="468" y="112" fill="#8b949e" font-size="7" font-family="sans-serif">Keeps low 8 bits: 0xC8.</text>
  <text x="468" y="124" fill="#8b949e" font-size="7" font-family="sans-serif">Bit 7 = sign bit → negative</text>
  <text x="468" y="136" fill="#8b949e" font-size="7" font-family="sans-serif">200 − 256 = −56.</text>
</svg>

Every narrowing cast risks silent data corruption — truncation, wrapping, or sign reversal — with no runtime exception.

## 5. Runnable example

Scenario: a binary image processor that converts 32-bit ARGB pixel values, extracts channel bytes, scales floating-point color components to `int` pixel values, and packs them back — all operations require narrowing casts.

### Level 1 — Basic

```java
public class NarrowingBasic {
    public static void main(String[] args) {
        // ARGB packed as int: bits 31-24=A, 23-16=R, 15-8=G, 7-0=B
        int argb = 0xFF_C8_3C_14;  // alpha=255, R=200, G=60, B=20

        // Extract channels using narrowing cast — int → byte
        byte alpha = (byte)((argb >> 24) & 0xFF);
        byte red   = (byte)((argb >> 16) & 0xFF);
        byte green = (byte)((argb >>  8) & 0xFF);
        byte blue  = (byte)( argb        & 0xFF);

        // Note: & 0xFF masks to low 8 bits before cast; without it sign extension
        // would be wrong for values > 127 (byte treats them as negative)
        System.out.printf("ARGB: #%08X%n", argb);
        System.out.printf("  A=%d  R=%d  G=%d  B=%d%n",
            alpha & 0xFF, red & 0xFF, green & 0xFF, blue & 0xFF);

        // Scale double (0.0–1.0) to int (0–255) pixel value
        double brightness = 0.753;
        int pixelVal = (int)(brightness * 255);   // 192 — truncation
        System.out.printf("Brightness %.3f → pixel %d%n", brightness, pixelVal);

        // Narrowing long → int after bounds check
        long computedWidth = 1920L;
        int  width = (int) Math.min(computedWidth, Integer.MAX_VALUE);
        System.out.println("Width: " + width);
    }
}
```

**How to run:** `java NarrowingBasic.java`

`(argb >> 16) & 0xFF` shifts `R` to the low byte and masks it to 8 bits, giving an `int` in range 0–255. The cast `(byte)` then converts it to the signed byte type — values 128–255 become negative, but when printed with `& 0xFF` they are correctly displayed as unsigned. `(int)(brightness * 255)` truncates 192.015 to 192. `Math.min(computedWidth, Integer.MAX_VALUE)` returns a `long` — the cast `(int)` is safe here because the `min` guarantees the value fits.

### Level 2 — Intermediate

Same processor: applying a brightness curve to each channel (float arithmetic), then narrowing back to byte, with clamping to prevent overflow.

```java
public class NarrowingIntermediate {

    static byte clampedByte(int value) {
        // Clamp to 0–255, then narrowing cast (safe because we clamped)
        int clamped = Math.max(0, Math.min(255, value));
        return (byte) clamped;   // 0–127 stay positive; 128–255 → signed negative, bit-correct
    }

    static int applyCurve(byte channel, float gamma) {
        // & 0xFF converts signed byte to unsigned int
        int  unsigned  = channel & 0xFF;
        // Apply gamma curve: new = 255 * (unsigned/255)^gamma
        float normalized = unsigned / 255.0f;
        float corrected  = (float) Math.pow(normalized, gamma);
        float scaled     = corrected * 255.0f;
        return (int) scaled;   // float → int: truncation (expected)
    }

    public static void main(String[] args) {
        int[] pixels = {0xFF_80_40_20, 0xFF_FF_00_80, 0xFF_10_F0_C0};
        float gamma = 0.5f;   // brighten: square-root curve

        System.out.printf("%-14s  %-14s%n", "Original", "Gamma-corrected");
        for (int px : pixels) {
            byte r = (byte)((px >> 16) & 0xFF);
            byte g = (byte)((px >>  8) & 0xFF);
            byte b = (byte)( px        & 0xFF);

            int rNew = applyCurve(r, gamma);
            int gNew = applyCurve(g, gamma);
            int bNew = applyCurve(b, gamma);

            byte rB = clampedByte(rNew);
            byte gB = clampedByte(gNew);
            byte bB = clampedByte(bNew);

            int newPx = (0xFF << 24) | ((rB & 0xFF) << 16) | ((gB & 0xFF) << 8) | (bB & 0xFF);
            System.out.printf("#%06X          #%06X%n",
                px & 0xFFFFFF, newPx & 0xFFFFFF);
        }
    }
}
```

**How to run:** `java NarrowingIntermediate.java`

`channel & 0xFF` is the unsigned widening of a signed `byte` — this is the canonical pattern for treating a Java `byte` as unsigned. After the float gamma curve computation, `(int) scaled` truncates the float. `clampedByte` then ensures the value is in 0–255 before the cast `(byte)` — avoiding the sign-change surprise for values 128–255 (they will still be stored as negative bytes, but `& 0xFF` when extracting them restores the unsigned value). This clamped-cast is the safe narrowing idiom.

### Level 3 — Advanced

Same pipeline: a full image transformation that also downsizes a `long` accumulator to `short` for a compact histogram, uses `Math.toIntExact` as a safe alternative to a plain cast, and shows how `float → double → int` round-trips can drift.

```java
import java.util.*;

public class NarrowingAdvanced {

    static byte[] extractChannels(int[] pixels, int channel) {
        // channel: 0=R, 1=G, 2=B
        byte[] out = new byte[pixels.length];
        int shift = (2 - channel) * 8;
        for (int i = 0; i < pixels.length; i++) {
            out[i] = (byte)((pixels[i] >> shift) & 0xFF);   // narrowing: int → byte
        }
        return out;
    }

    static short[] buildHistogram(byte[] channel) {
        long[] counts = new long[256];
        for (byte b : channel) {
            counts[b & 0xFF]++;
        }
        // Normalize to 0–1000 scale, store in short (max 32767)
        long max = 0;
        for (long c : counts) max = Math.max(max, c);
        short[] hist = new short[256];
        for (int i = 0; i < 256; i++) {
            // long → short narrowing: safe only if value ≤ 32767
            long normalized = max == 0 ? 0 : (counts[i] * 1000 / max);
            hist[i] = (short) normalized;   // narrowing long → short
        }
        return hist;
    }

    public static void main(String[] args) {
        // Generate synthetic pixels
        int[] pixels = new int[500];
        Random rng = new Random(99);
        for (int i = 0; i < pixels.length; i++) {
            int r = rng.nextInt(256), g = rng.nextInt(256), b = rng.nextInt(256);
            pixels[i] = (0xFF << 24) | (r << 16) | (g << 8) | b;
        }

        byte[] red  = extractChannels(pixels, 0);
        short[] hist = buildHistogram(red);

        // Find peak bin (int accumulation, narrowing at the end)
        int peak = 0;
        for (short h : hist) { peak = Math.max(peak, h & 0xFFFF); }
        System.out.println("Red histogram peak scaled value: " + peak);

        // Math.toIntExact: throws ArithmeticException if value overflows int
        long totalPixels = pixels.length;
        try {
            int exact = Math.toIntExact(totalPixels);  // safe alternative to (int)
            System.out.println("Pixel count as int: " + exact);
        } catch (ArithmeticException e) {
            System.out.println("Too large for int");
        }

        // float → double → int drift demo
        float  f  = 1.1f;
        double fd = f;         // float → double widening — but 1.1f is not exactly 1.1
        System.out.printf("float 1.1f as double: %.20f%n", fd);  // not exactly 1.1
        int truncated = (int)(f * 10);     // might be 10 or 11 depending on representation
        System.out.println("(int)(1.1f * 10) = " + truncated);
    }
}
```

**How to run:** `java NarrowingAdvanced.java`

`extractChannels` casts `int → byte` for each pixel channel — values 128–255 become negative bytes but are bit-correct. `buildHistogram` computes `long normalized` in range 0–1000 and narrows to `short` — safe because 1000 < 32767. `hist[i] & 0xFFFF` when reading converts the signed short back to an unsigned int for comparison. `Math.toIntExact(totalPixels)` is the safe alternative to `(int) totalPixels` — it throws rather than silently wrapping. The float drift demo shows that `1.1f` is not the same value as `1.1` — widening `float` to `double` exposes the float's existing imprecision.

## 6. Walkthrough

Trace `extractChannels(pixels, 0)` for one pixel `0xFF_C8_3C_14`:

**Shift and mask.** `shift = (2 - 0) * 8 = 16`. `pixels[0] >> 16 = 0x0000_FFC8` (arithmetic right-shift for int; but we mask anyway). `& 0xFF = 0xC8 = 200`.

**Narrowing cast `(byte) 200`.** 200 in binary: `1100 1000`. This 8-bit pattern in Java's signed `byte` is interpreted as `-56` (since bit 7 = 1, the value is `200 - 256 = -56`). The cast stores the bit pattern correctly — no information is lost in the bits, only in the interpretation.

**Unsigned recovery `b & 0xFF`.** When `buildHistogram` does `counts[b & 0xFF]++`, the expression `b & 0xFF` widens `-56` (signed byte) to `int` via sign extension → `0xFFFF_FFC8`, then `& 0xFF` masks to `0x0000_00C8 = 200`. The correct unsigned bin 200 is incremented.

```
int  200: 0000 0000 1100 1000   (32 bits)
(byte) →: keeping low 8 bits
byte -56: 1100 1000             (8 bits, bit 7 set → negative in two's complement)
& 0xFF  : 0000 0000 1100 1000   (back to 200 when widened to int)
```

## 7. Gotchas & takeaways

> **`(int) doubleValue` truncates toward zero, not down (floor).** `(int) -3.9` is `-3`, not `-4`. Use `Math.floor` and then cast if you need floor semantics: `(int) Math.floor(-3.9)` is `-4`.

> **`(byte)` on an `int` in range 128–255 always yields a negative value.** Java `byte` is signed. The bit pattern is preserved; the sign changes. Always recover unsigned value with `b & 0xFF` when treating the byte as unsigned.

> **Narrowing never throws.** NaN cast to int gives 0. Infinity cast to int gives `Integer.MAX_VALUE` (or `MIN_VALUE` for negative infinity). There is no exception to catch — validate before casting.

- Every narrowing conversion requires an explicit `(targetType)` cast.
- `double/float → int/long`: fraction truncated toward zero; out-of-range values clamp to `MAX_VALUE`/`MIN_VALUE`; NaN → 0.
- `long/int → smaller integer`: low-order bits kept; upper bits discarded; result may wrap or change sign.
- Safe narrowing idiom: `Math.min`/`Math.max` clamp, then cast; or use `Math.toIntExact` for long → int with overflow detection.
- Unsigned byte extraction: `(byte) (value & 0xFF)` stores bits; `storedByte & 0xFF` recovers unsigned int.
