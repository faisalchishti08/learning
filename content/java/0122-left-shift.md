---
card: java
gi: 122
slug: left-shift
title: Left shift <<
---

## 1. What it is

`<<` shifts the bits of its left operand toward the higher-order (left) end by the number of positions given by its right operand, filling the vacated low-order bits with `0`. Shifting left by `n` positions is mathematically equivalent to multiplying by `2^n`, as long as the result does not overflow the type's range. Unlike arithmetic operators, the right operand of a shift is **not** used directly — Java masks it against the left operand's bit-width minus one before applying it: for `int` (32 bits), the shift amount is taken modulo 32 (using only its low 5 bits); for `long` (64 bits), modulo 64 (its low 6 bits).

```java
int x = 1;
System.out.println(x << 3);    // 8  (1 * 2^3)
System.out.println(5 << 1);     // 10 (5 * 2)

// The shift-amount masking gotcha
System.out.println(1 << 32);     // 1, NOT 0! shift amount 32 is masked to 32 % 32 = 0
System.out.println(1 << 33);     // 2, because 33 % 32 = 1
System.out.println(1L << 64);     // 1L, because for long, 64 % 64 = 0
```

The masking behavior is a frequent source of confusion: a beginner might expect `1 << 32` on an `int` to shift the single bit entirely out of range, producing `0`, but Java only uses the low 5 bits of `32` (which is `0`), so the shift amount actually applied is `0`, leaving the value unchanged.

## 2. Why & when

`<<` is used for:

- Fast multiplication by powers of two: `x << 1` doubles `x`, `x << 3` multiplies by 8 — occasionally used for performance-sensitive code, though modern JIT compilers often perform this optimization automatically for literal constant shifts.
- Building bitmasks and packed values: `1 << n` produces a value with only the `n`-th bit set, the standard way to construct an individual flag constant (`FLAG_A = 1 << 0`, `FLAG_B = 1 << 1`, `FLAG_C = 1 << 2`, and so on).
- Packing multiple smaller values into one larger integer: `(r << 16) | (g << 8) | b` packs three 8-bit color channels into a single 24-bit RGB integer.

You must watch for overflow: shifting a value left far enough will eventually shift significant bits out of the type's range entirely, silently discarding them — `<<` never widens the type to accommodate the growing magnitude.

## 3. Core concept

```java
public class LeftShiftDemo {
    public static void main(String[] args) {
        // Basic shift-as-multiplication
        int x = 1;
        System.out.println("1 << 3 = " + (x << 3));    // 8
        System.out.println("5 << 2 = " + (5 << 2));      // 20 (5 * 4)

        // Building individual flag bits
        int FLAG_A = 1 << 0;   // 1
        int FLAG_B = 1 << 1;    // 2
        int FLAG_C = 1 << 2;     // 4
        System.out.println("FLAG_A=" + FLAG_A + " FLAG_B=" + FLAG_B + " FLAG_C=" + FLAG_C);

        // The shift-amount masking gotcha
        System.out.println("1 << 32 = " + (1 << 32));    // 1, NOT 0! (32 % 32 == 0)
        System.out.println("1 << 33 = " + (1 << 33));      // 2 (33 % 32 == 1)
        System.out.println("1L << 64 = " + (1L << 64));     // 1L (64 % 64 == 0 for long)

        // Overflow: shifting significant bits out of range
        int big = 1 << 30;
        System.out.println("1 << 30 = " + big);
        System.out.println("1 << 31 = " + (1 << 31));       // Integer.MIN_VALUE — the sign bit gets set!
        System.out.println("1 << 32 would wrap back to 1 (see above), not overflow further");
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Left shift diagram: shifting the value 1 left by 3 positions moves the single set bit three places toward the high end, filling the vacated low positions with zero, resulting in the value 8.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1 &lt;&lt; 3 — the set bit moves left, zeros fill in from the right</text>

  <text x="20" y="52" fill="#8b949e" font-size="9" font-family="monospace">before:</text>
  <text x="120" y="52" fill="#e6edf3" font-size="12" font-family="monospace">0000 0001</text>

  <path d="M 250 44 L 320 44" stroke="#6db33f" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="285" y="36" fill="#6db33f" font-size="8" text-anchor="middle">&lt;&lt; 3</text>

  <text x="20" y="90" fill="#8b949e" font-size="9" font-family="monospace">after:</text>
  <text x="120" y="90" fill="#6db33f" font-size="12" font-family="monospace">0000 1000</text>
  <text x="300" y="90" fill="#79c0ff" font-size="10" font-family="monospace">= 8  (1 * 2^3)</text>

  <text x="120" y="112" fill="#8b949e" font-size="7.5" font-family="sans-serif">↑bit moved 3 places left</text>
  <text x="245" y="112" fill="#8b949e" font-size="7.5" font-family="sans-serif">↑vacated positions filled with 0</text>

  <text x="350" y="140" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Shift amount is masked: for int, only the low 5 bits of the right operand are used (mod 32)</text>
</svg>

Left shift moves bits toward the high end and always fills the newly vacated low bits with zero.

## 5. Runnable example

Scenario: a simple RGB color packer/unpacker for a graphics application — the classic real-world use of `<<` for combining separate byte-sized fields into one integer, extended to handle alpha channel and validate against accidental overflow of the packed format.

### Level 1 — Basic

```java
public class ColorPackBasic {
    public static void main(String[] args) {
        int red = 255, green = 128, blue = 64;

        // Pack three 8-bit channels into one 24-bit RGB integer
        int packed = (red << 16) | (green << 8) | blue;
        System.out.printf("Packed color: #%06X%n", packed);
    }
}
```

**How to run:** `java ColorPackBasic.java`

`red << 16` shifts the red channel's 8 bits up to occupy bit positions 16–23 (the highest byte of the 24-bit result). `green << 8` shifts green up to occupy bits 8–15. `blue` is left in place, occupying bits 0–7. OR-ing all three together combines them without overlap, since each channel's shifted range occupies entirely distinct bit positions — this only works correctly because each channel value is constrained to fit within 8 bits (`0`–`255`) before shifting.

### Level 2 — Intermediate

Same color packer, now adding an alpha channel (4 fields packed into 32 bits total, using the full `int` range) and validating each input channel is within the valid 8-bit range before packing, since an out-of-range value would corrupt adjacent fields when shifted.

```java
public class ColorPackIntermediate {

    static int packARGB(int alpha, int red, int green, int blue) {
        validateChannel("alpha", alpha);
        validateChannel("red", red);
        validateChannel("green", green);
        validateChannel("blue", blue);
        return (alpha << 24) | (red << 16) | (green << 8) | blue;
    }

    static void validateChannel(String name, int value) {
        if (value < 0 || value > 255) {
            throw new IllegalArgumentException(name + " channel out of range [0,255]: " + value);
        }
    }

    public static void main(String[] args) {
        int packed = packARGB(255, 255, 128, 64);
        System.out.printf("Packed ARGB: #%08X%n", packed);

        try {
            packARGB(255, 300, 128, 64);   // red is out of range — would corrupt the alpha field if unchecked
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ColorPackIntermediate.java`

`validateChannel` catches an out-of-range value *before* it reaches the shift-and-pack step: without this check, a `red` value of `300` (which needs 9 bits, `0b1_0010_1100`) shifted left by 16 would spill its extra high bit into bit position 24 — exactly where the `alpha` channel lives — silently corrupting the alpha value with a stray bit from an invalid red input. This demonstrates why bit-packing code must validate each field's range independently before combining them; the shift-and-OR operation itself has no way to detect or prevent this kind of cross-field bleed.

### Level 3 — Advanced

Same packer, now building a general-purpose, reusable bit-field packer/unpacker that computes shift amounts and masks from field widths (rather than hardcoding `16`, `8`, `24`), demonstrating how `<<` combines with field-width arithmetic in real serialization code, and validating against the classic `1 << 31` sign-bit gotcha.

```java
public class ColorPackAdvanced {

    // Generic bit-field packer: fields are packed from the LEAST significant bit upward,
    // each field described by its width in bits.
    static int packFields(int[] values, int[] widths) {
        int result = 0;
        int shift = 0;
        for (int i = 0; i < values.length; i++) {
            int maxValueForWidth = (1 << widths[i]) - 1;   // e.g., width 8 -> (1<<8)-1 = 255
            if (values[i] < 0 || values[i] > maxValueForWidth) {
                throw new IllegalArgumentException(
                    "Field " + i + " value " + values[i] + " exceeds " + widths[i] + "-bit range");
            }
            result |= (values[i] << shift);
            shift += widths[i];
        }
        return result;
    }

    public static void main(String[] args) {
        // Pack blue(8 bits), green(8 bits), red(8 bits), alpha(8 bits) — LSB first ordering
        int packed = packFields(new int[]{ 64, 128, 255, 255 }, new int[]{ 8, 8, 8, 8 });
        System.out.printf("Packed (generic): #%08X%n", packed);

        // The sign-bit gotcha: shifting a 1 into bit position 31 makes the int NEGATIVE
        int signBitSet = 1 << 31;
        System.out.println("1 << 31 = " + signBitSet);           // Integer.MIN_VALUE, a large negative number
        System.out.println("As unsigned: " + Integer.toUnsignedLong(signBitSet));  // 2147483648, the "intended" positive value

        // Demonstrating maxValueForWidth itself hitting this edge case for width=31 or 32
        try {
            int maxFor32 = (1 << 32) - 1;   // 32 masked to 0 -> (1<<0)-1 = 0, NOT the expected all-ones pattern!
            System.out.println("Buggy max for 32-bit width: " + maxFor32);
        } catch (Exception e) {
            System.out.println("Unexpected: " + e);
        }
    }
}
```

**How to run:** `java ColorPackAdvanced.java`

`packFields` generalizes the hardcoded shift amounts into a loop that accumulates `shift` by each field's width as it processes them, and computes each field's maximum valid value as `(1 << width) - 1` (a mask of `width` consecutive `1` bits) to validate the input before shifting — this is a real pattern used in binary protocol serialization and hardware register packing. The final section exposes two related gotchas: `1 << 31` sets the sign bit of a 32-bit `int`, producing `Integer.MIN_VALUE` (a large *negative* number) rather than the large positive value `2^31` a reader might naively expect — `Integer.toUnsignedLong` is needed to view it as the intended unsigned magnitude. And `(1 << 32) - 1`, intended to build a 32-bit "all ones" mask, actually computes `(1 << 0) - 1 = 0` because the shift amount `32` is masked to `0` for `int` — this is precisely the shift-amount-masking gotcha from Section 1, showing it can bite even in code that looks like it should obviously work, and is why a genuine "all 32 bits set" mask must be written as `0xFFFFFFFF` or `-1` directly, not derived via `(1 << 32) - 1`.

## 6. Walkthrough

Trace `packFields` for the two-field simplified case `values = {64, 128}, widths = {8, 8}` (blue then green):

**Initialize.** `result = 0`, `shift = 0`.

**First field: `values[0] = 64, widths[0] = 8`.** `maxValueForWidth = (1 << 8) - 1 = 256 - 1 = 255`. `64` is within `[0, 255]`, so validation passes. `result |= (64 << 0)` computes `result = 0 | 64 = 64`. `shift` becomes `0 + 8 = 8`.

**Second field: `values[1] = 128, widths[1] = 8`.** `maxValueForWidth = 255` again. `128` is within range. `result |= (128 << 8)` computes `128 << 8 = 32768` (`128` shifted up by one full byte), then `result = 64 | 32768 = 32832`. `shift` becomes `8 + 8 = 16`.

```
Field 0: value=64,  shift=0  -> 64 << 0  = 0000000001000000   (occupies bits 0-7)
Field 1: value=128, shift=8  -> 128 << 8 = 0000000100000000 << (wait, let's show combined)

result after field 0: 00000000 01000000                (64)
result after field 1: 00000000 01000000
                     | 10000000 00000000    (128 << 8)
                     = 10000000 01000000    (32832)
```

**Why no overlap occurs.** Because each field's value was validated to fit within its declared width (`8` bits, max `255`) *before* shifting, shifting it left by the accumulated `shift` amount places it entirely within its own reserved 8-bit region of `result` — it can never "spill" into the bits reserved for a different field, which is exactly the invariant the validation step protects.

**Final output.** With all four fields (blue, green, red, alpha) packed the same way, the program prints the combined 32-bit hex value, then demonstrates the `1 << 31` sign-bit surprise and the `(1 << 32) - 1` shift-masking trap, both printed with clear before/after context so the discrepancy from naive expectations is directly visible.

## 7. Gotchas & takeaways

> **The shift amount is masked (taken modulo the type's bit width) before being applied — it is never used as-is for amounts at or beyond the type's width.** `1 << 32` on an `int` does *not* shift the bit entirely out of range to produce `0`; it applies a shift of `32 % 32 = 0`, leaving the value unchanged. This breaks naive derivations like `(1 << width) - 1` when `width` equals the type's full bit count.

> **Shifting a `1` into the highest bit position (`1 << 31` for `int`, `1L << 63` for `long`) sets the sign bit, producing a large negative number, not the large positive magnitude a reader might expect.** Use `Integer.toUnsignedLong`/`Long.toUnsignedString` to view the value as an unsigned magnitude when that's the intended meaning.

- `x << n` is equivalent to `x * 2^n`, as long as no significant bits are shifted out of the type's range.
- `1 << n` is the standard idiom for constructing an individual flag bit at position `n`; `(1 << n) - 1` constructs a mask of `n` consecutive low-order `1` bits (except when `n` equals the type's full bit width, due to shift-amount masking).
- Always validate the ranges of individual fields before packing them with `<<` and `|` — an out-of-range field can silently spill bits into an adjacent field's reserved bit positions.
- Building a genuine "all bits set" mask for a full-width type requires a literal like `0xFFFFFFFF` or `-1`, not a shift-derived formula that assumes the shift amount equals the type's bit width.
