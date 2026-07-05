---
card: java
gi: 77
slug: sizes-ranges-of-each-primitive
title: Sizes & ranges of each primitive
---

## 1. What it is

Java's eight primitive types have fixed, platform-independent sizes and ranges defined by the Java Language Specification. Unlike C or C++, where `int` size depends on the platform, a Java `int` is always 32 bits on every JVM. The ranges follow directly from the bit width and the encoding (two's complement for integers, IEEE 754 for floating-point, unsigned 16-bit for `char`).

| Type      | Size     | Min value              | Max value              |
|-----------|----------|------------------------|------------------------|
| `boolean` | 1 bit*   | —                      | —                      |
| `byte`    | 8 bits   | −128                   | 127                    |
| `short`   | 16 bits  | −32 768                | 32 767                 |
| `int`     | 32 bits  | −2 147 483 648         | 2 147 483 647          |
| `long`    | 64 bits  | −9 223 372 036 854 775 808 | 9 223 372 036 854 775 807 |
| `float`   | 32 bits  | ≈ −3.4×10³⁸            | ≈ 3.4×10³⁸             |
| `double`  | 64 bits  | ≈ −1.8×10³⁰⁸           | ≈ 1.8×10³⁰⁸            |
| `char`    | 16 bits  | 0 (`'\0'`)             | 65 535 (`'￿'`)    |

\* `boolean` stores a logical value; the JVM may use more space internally (e.g., `boolean[]` uses bytes).

The `MIN_VALUE` and `MAX_VALUE` constants in each wrapper class (`Byte`, `Short`, `Integer`, `Long`, `Float`, `Double`, `Character`) are the canonical, always-correct way to reference these bounds.

## 2. Why & when

Knowing the sizes and ranges matters when:
- **Overflow prevention** — `int` silently wraps when it overflows. A population count or file offset can exceed 2 billion; using `long` avoids silent corruption.
- **Type selection** — choosing the smallest type that fits avoids overflow and reduces memory in large arrays.
- **Interoperability** — protocol parsing, file formats, and network frames often specify field widths in bits; matching Java types to those widths avoids unnecessary masking.
- **Boundary tests** — unit tests should include `MIN_VALUE` and `MAX_VALUE` as boundary cases to catch overflow or edge-case logic.

## 3. Core concept

```java
// ---- Constants from wrapper classes — always use these, never hard-code ----
System.out.println("byte   : " + Byte.MIN_VALUE    + " to " + Byte.MAX_VALUE);
System.out.println("short  : " + Short.MIN_VALUE   + " to " + Short.MAX_VALUE);
System.out.println("int    : " + Integer.MIN_VALUE + " to " + Integer.MAX_VALUE);
System.out.println("long   : " + Long.MIN_VALUE    + " to " + Long.MAX_VALUE);
System.out.println("float  : " + Float.MIN_VALUE   + " to " + Float.MAX_VALUE);
System.out.println("double : " + Double.MIN_VALUE  + " to " + Double.MAX_VALUE);
System.out.println("char   : " + (int)Character.MIN_VALUE + " to " + (int)Character.MAX_VALUE);

// ---- Integer overflow wraps silently (no exception) ----
int maxInt = Integer.MAX_VALUE;
System.out.println(maxInt + 1);    // -2147483648  — wraps to MIN_VALUE

long bigInt = (long) Integer.MAX_VALUE + 1;  // promote to long first
System.out.println(bigInt);                  // 2147483648  — correct

// ---- Bit widths ----
System.out.println(Integer.SIZE);    // 32 (bits)
System.out.println(Long.SIZE);       // 64
System.out.println(Float.SIZE);      // 32
System.out.println(Double.SIZE);     // 64
System.out.println(Character.SIZE);  // 16

// ---- Byte sizes ----
System.out.println(Integer.BYTES);   // 4
System.out.println(Long.BYTES);      // 8

// ---- Two's complement: MIN_VALUE has no positive counterpart ----
System.out.println(Math.abs(Integer.MIN_VALUE));  // -2147483648!  same value (overflow)
System.out.println(-Integer.MIN_VALUE);           // -2147483648 (same reason)

// ---- Float.MIN_VALUE is the smallest POSITIVE non-zero float, NOT the most negative ----
System.out.println(Float.MIN_VALUE);   // 1.4E-45   (NOT -3.4e38)
System.out.println(-Float.MAX_VALUE);  // -3.4028235E38  (most negative finite float)
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Visual size comparison of Java's 8 primitive types as horizontal bars proportional to bit width, with min/max labels">
  <rect x="8" y="8" width="684" height="194" rx="8" fill="#0d1117"/>

  <text x="350" y="26" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Primitive type sizes (bar width ∝ bit width) and key ranges</text>

  <!-- boolean -->
  <text x="68" y="45" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">boolean</text>
  <rect x="72" y="36" width="4" height="14" rx="1" fill="#8b949e"/>
  <text x="80" y="47" fill="#8b949e" font-size="7" font-family="monospace">1-bit (logical)</text>

  <!-- byte -->
  <text x="68" y="65" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">byte</text>
  <rect x="72" y="56" width="16" height="14" rx="1" fill="#79c0ff" opacity="0.7"/>
  <text x="92" y="67" fill="#8b949e" font-size="7" font-family="monospace">8-bit   −128 … 127</text>

  <!-- short -->
  <text x="68" y="85" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">short</text>
  <rect x="72" y="76" width="32" height="14" rx="1" fill="#79c0ff" opacity="0.7"/>
  <text x="108" y="87" fill="#8b949e" font-size="7" font-family="monospace">16-bit   −32 768 … 32 767</text>

  <!-- char -->
  <text x="68" y="105" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">char</text>
  <rect x="72" y="96" width="32" height="14" rx="1" fill="#6db33f" opacity="0.7"/>
  <text x="108" y="107" fill="#8b949e" font-size="7" font-family="monospace">16-bit unsigned   0 … 65 535</text>

  <!-- int -->
  <text x="68" y="125" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">int</text>
  <rect x="72" y="116" width="64" height="14" rx="1" fill="#6db33f" opacity="0.85"/>
  <text x="140" y="127" fill="#8b949e" font-size="7" font-family="monospace">32-bit   −2.1B … 2.1B</text>

  <!-- float -->
  <text x="68" y="145" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">float</text>
  <rect x="72" y="136" width="64" height="14" rx="1" fill="#8b949e" opacity="0.6"/>
  <text x="140" y="147" fill="#8b949e" font-size="7" font-family="monospace">32-bit IEEE 754  ≈±3.4×10³⁸  ~7 digits</text>

  <!-- long -->
  <text x="68" y="165" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">long</text>
  <rect x="72" y="156" width="128" height="14" rx="1" fill="#6db33f"/>
  <text x="204" y="167" fill="#8b949e" font-size="7" font-family="monospace">64-bit   ≈±9.2×10¹⁸</text>

  <!-- double -->
  <text x="68" y="185" fill="#e6edf3" font-size="8" text-anchor="end" font-family="monospace">double</text>
  <rect x="72" y="176" width="128" height="14" rx="1" fill="#8b949e" opacity="0.8"/>
  <text x="204" y="187" fill="#8b949e" font-size="7" font-family="monospace">64-bit IEEE 754  ≈±1.8×10³⁰⁸  ~15 digits</text>
</svg>

The integer types use two's complement (signed), `char` is unsigned 16-bit, and the floating-point types follow IEEE 754; `long` and `double` share 64-bit width but represent completely different value domains.

## 5. Runnable example

Scenario: a data packet decoder for a hypothetical binary network protocol — each field in the packet has a defined bit width, and the decoder must choose the right Java primitive to hold each value without overflow. The scenario grows from reading simple fixed-width fields, to detecting overflow on `int`, to a full boundary-value test that exercises `MIN_VALUE` and `MAX_VALUE` for each type.

### Level 1 — Basic

```java
public class RangesBasic {
    public static void main(String[] args) {
        // Simulate a decoded network packet with fixed-width fields
        byte  statusCode  = 127;          // 8-bit signed: max is 127
        short portNumber  = 32_767;       // 16-bit signed: max is 32 767
        int   ipHash      = 2_147_483_647;// 32-bit signed max
        long  timestamp   = 9_223_372_036_854_775_807L; // 64-bit max

        System.out.println("Packet fields:");
        System.out.printf("  statusCode (byte)  : %d   (max %d)%n", statusCode, Byte.MAX_VALUE);
        System.out.printf("  portNumber (short) : %d   (max %d)%n", portNumber, Short.MAX_VALUE);
        System.out.printf("  ipHash     (int)   : %d   (max %d)%n", ipHash, Integer.MAX_VALUE);
        System.out.printf("  timestamp  (long)  : %d (max %d)%n", timestamp, Long.MAX_VALUE);

        // Show wrap-around on overflow
        byte overflowed = (byte) (statusCode + 1);
        System.out.println();
        System.out.println("byte 127 + 1 = " + overflowed + "  (wraps to -128)");
    }
}
```

**How to run:** `java RangesBasic.java`

Each field is assigned the smallest type that can hold its maximum value: `byte` for status codes (0–127), `short` for port numbers (up to 32 767), `int` for a 32-bit hash, and `long` for a 64-bit nanosecond timestamp. Adding `1` to a `byte` holding `127` silently wraps to `-128` — two's complement overflow. The cast `(byte)(statusCode + 1)` triggers this: Java promotes `statusCode` to `int` for the addition, then the explicit cast truncates back to 8 bits.

### Level 2 — Intermediate

Same packet decoder: handle a field that arrives as an unsigned 16-bit value (which `short` cannot represent correctly because `short` is signed) and a field that would overflow `int` — both need careful type promotion.

```java
public class RangesIntermediate {

    // Read a 16-bit field as unsigned (0..65535); short would overflow above 32767
    static int readUnsigned16(short rawShort) {
        return Short.toUnsignedInt(rawShort);
    }

    public static void main(String[] args) {
        // Simulate a packet carrying unsigned 16-bit payload length (0..65535)
        short rawLength = (short) 60_000;   // bit pattern for 60000; stored as -5536 in signed short
        int   actualLength = readUnsigned16(rawLength);
        System.out.println("raw short bits  : " + rawLength);      // -5536 (signed interpretation)
        System.out.println("unsigned length : " + actualLength);   // 60000 (correct)

        // Overflow: summing two large ints overflows silently
        int a = 2_000_000_000;
        int b = 2_000_000_000;
        int sumInt  = a + b;           // OVERFLOW — wraps to -294967296
        long sumLong = (long) a + b;   // CORRECT — promote before addition

        System.out.println();
        System.out.println("int  + int  (overflow): " + sumInt);
        System.out.println("long + int  (correct) : " + sumLong);

        // Math.addExact throws on overflow — safe arithmetic
        try {
            int safe = Math.addExact(a, b);
            System.out.println("Math.addExact: " + safe);
        } catch (ArithmeticException e) {
            System.out.println("Math.addExact threw: " + e.getMessage());
        }

        // Character range: char is unsigned 16-bit (0..65535)
        char maxChar = Character.MAX_VALUE;
        System.out.println();
        System.out.printf("char MAX_VALUE: %d (0x%04X)%n", (int) maxChar, (int) maxChar);
        char overflow = (char) (maxChar + 1);
        System.out.printf("char MAX+1   : %d (wraps to \\u0000)%n", (int) overflow);
    }
}
```

**How to run:** `java RangesIntermediate.java`

Java has no unsigned integer types except `char`. When a protocol field is defined as unsigned 16-bit (0–65 535), it must be stored in an `int` after conversion. `Short.toUnsignedInt(raw)` reinterprets the 16-bit pattern as unsigned, adding 65 536 to any negative `short` value. `(long) a + b` promotes `a` to `long` before the addition so the arithmetic never exceeds `long`'s range. `Math.addExact` is the safe alternative: it throws `ArithmeticException` on overflow instead of silently wrapping, which is invaluable for security-sensitive code.

### Level 3 — Advanced

Same system: a comprehensive boundary tester that exercises `MIN_VALUE`, `MAX_VALUE`, and wrap-around for every integer type, and shows the `Float.MIN_VALUE` naming trap.

```java
public class RangesAdvanced {

    record TypeBounds(String name, long min, long max, int bits) {}

    public static void main(String[] args) {
        var bounds = java.util.List.of(
            new TypeBounds("byte",  Byte.MIN_VALUE,    Byte.MAX_VALUE,    8),
            new TypeBounds("short", Short.MIN_VALUE,   Short.MAX_VALUE,  16),
            new TypeBounds("int",   Integer.MIN_VALUE, Integer.MAX_VALUE, 32),
            new TypeBounds("char",  Character.MIN_VALUE, Character.MAX_VALUE, 16)
            // long omitted here — fits in long but can't be stored in a 'long' record without boxing
        );

        System.out.printf("%-8s  %6s  %25s  %25s%n", "Type", "Bits", "MIN_VALUE", "MAX_VALUE");
        System.out.println("-".repeat(72));
        for (var b : bounds) {
            System.out.printf("%-8s  %6d  %25d  %25d%n",
                b.name(), b.bits(), b.min(), b.max());
        }
        System.out.printf("%-8s  %6d  %25d  %25d%n", "long", 64, Long.MIN_VALUE, Long.MAX_VALUE);

        // Demonstrate MIN_VALUE trap for floating-point
        System.out.println();
        System.out.println("=== Float/Double MIN_VALUE trap ===");
        System.out.printf("Float.MIN_VALUE  = %.2e  (smallest positive, NOT most negative)%n",
            Float.MIN_VALUE);
        System.out.printf("-Float.MAX_VALUE = %.2e  (most negative finite float)%n",
            -Float.MAX_VALUE);
        System.out.printf("Double.MIN_VALUE = %.2e  (smallest positive double)%n",
            Double.MIN_VALUE);

        // Confirm wrap-around arithmetic for each integer type
        System.out.println();
        System.out.println("=== Overflow wrap-around ===");
        System.out.println("Byte.MAX_VALUE  + 1 = " + (byte)(Byte.MAX_VALUE   + 1));   // -128
        System.out.println("Short.MAX_VALUE + 1 = " + (short)(Short.MAX_VALUE  + 1));  // -32768
        System.out.println("Integer.MAX_VALUE+1 = " + (Integer.MAX_VALUE + 1));        // -2147483648
        System.out.println("Long.MAX_VALUE  + 1 = " + (Long.MAX_VALUE   + 1L));        // min long

        // Math.abs(MIN_VALUE) does NOT give MAX_VALUE
        System.out.println();
        System.out.println("Math.abs(Integer.MIN_VALUE) = " + Math.abs(Integer.MIN_VALUE));
        System.out.println("  ^ Expected MAX_VALUE but got MIN_VALUE — two's complement asymmetry");
    }
}
```

**How to run:** `java RangesAdvanced.java`

In two's complement encoding, the minimum value (`-2^(n-1)`) has no positive counterpart within the same `n`-bit type: `Byte.MIN_VALUE` is `-128` but `Byte.MAX_VALUE` is only `127`. Negating `-128` would produce `128`, which overflows back to `-128`. This is why `Math.abs(Integer.MIN_VALUE)` returns `Integer.MIN_VALUE` — the result overflows. `Float.MIN_VALUE` is a counterintuitive name: for `float` (and `double`) it is the smallest *positive* non-zero value (denormal), not the most negative value. The most negative finite float is `-Float.MAX_VALUE`.

## 6. Walkthrough

Execution trace through `RangesAdvanced.main`:

**Bounds table.** A `List<TypeBounds>` holds the min and max as `long` values (which can represent all `byte`, `short`, `int`, and `char` boundaries exactly). For `char`, `Character.MIN_VALUE` is `'\0'` (widened to `long` 0) and `Character.MAX_VALUE` is `'￿'` (widened to `long` 65 535). `long`'s own bounds are printed separately because they cannot be widened to `long` without loss — they are already `long`.

**`Float.MIN_VALUE` trap.** For integer types, `MIN_VALUE` is the most negative representable value. For `float` and `double`, `MIN_VALUE` follows a different convention: it is the smallest positive non-zero value (`1.4E-45f` for float). The most negative finite float is `-Float.MAX_VALUE` (approximately `-3.4×10³⁸`). This naming inconsistency is a long-standing Java API quirk; always check the Javadoc when using `MIN_VALUE` on a floating-point wrapper.

**Overflow wrap-around.** Each integer type uses two's complement. Adding `1` to `MAX_VALUE` sets all bits to zero in the sign position and wraps to `MIN_VALUE`. The expression `(byte)(Byte.MAX_VALUE + 1)` first widens `127` to `int` (result `128` = `0x80`), then truncates back to 8 bits (`0x80` = `-128` in two's complement). The same pattern applies to `short`, `int`, and `long`. Long overflow is particularly subtle: there is no automatic widening to a wider type — the result silently wraps within 64 bits.

**Two's complement asymmetry.** The range of an `n`-bit signed type is `[−2^(n-1), 2^(n-1)−1]`. There are more negative values than positive ones — `MIN_VALUE` has magnitude one greater than `MAX_VALUE`. Negating `MIN_VALUE` would produce a value just outside the positive range, causing overflow back to `MIN_VALUE`. This means `Math.abs(Integer.MIN_VALUE) == Integer.MIN_VALUE`.

```
8-bit two's complement:
  0111 1111 = 127 (MAX_VALUE)
  0000 0000 = 0
  1111 1111 = -1
  1000 0000 = -128 (MIN_VALUE)

  MAX+1: 0111 1111 + 1 = 1000 0000 = -128 (wraps)
  -MIN:  negate 1000 0000 = 0111 1111 + 1 = 1000 0000 = -128 (same — overflow)
```

## 7. Gotchas & takeaways

> **`Float.MIN_VALUE` and `Double.MIN_VALUE` are NOT the most-negative values.** They are the smallest positive non-zero values (denormal floats). The most-negative finite float is `-Float.MAX_VALUE`. This naming is inconsistent with the integer wrappers, where `MIN_VALUE` is truly the minimum (most negative) value.

> **Integer overflow is silent in Java.** No exception is thrown when `int` or `long` arithmetic wraps around. Use `Math.addExact`, `Math.subtractExact`, and `Math.multiplyExact` to detect overflow via `ArithmeticException`, especially in security-sensitive code.

- Java's primitive sizes are platform-independent: `int` is always 32 bits, `long` always 64 bits.
- Use `Byte.MIN_VALUE`, `Integer.MAX_VALUE`, etc. — never hard-code magic numbers.
- `char` is an unsigned 16-bit type (0–65 535); it is the only unsigned integer primitive.
- Two's complement means `MIN_VALUE` has no positive counterpart: `Math.abs(Integer.MIN_VALUE) == Integer.MIN_VALUE`.
- `Float.MIN_VALUE` / `Double.MIN_VALUE` = smallest positive non-zero value, not the most negative.
- `Integer.SIZE` / `Integer.BYTES` give the bit/byte width; use these instead of hard-coded `4`.
- Promotion rules: arithmetic on `byte`/`short`/`char` widens to `int` first, which can mask truncation bugs if the result is not cast back.
