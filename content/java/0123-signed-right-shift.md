---
card: java
gi: 123
slug: signed-right-shift
title: Signed right shift >>
---

## 1. What it is

`>>` shifts the bits of its left operand toward the lower-order (right) end by the number of positions given by its right operand, filling the vacated high-order bits with copies of the **original sign bit** — this is called an *arithmetic* shift, and it is what makes `>>` "signed": the sign of the value is preserved through the shift. For a non-negative number, the sign bit is `0`, so the vacated bits fill with `0`s, and `x >> n` behaves like integer division by `2^n`. For a negative number, the sign bit is `1`, so the vacated bits fill with `1`s, preserving the value's negativity.

```java
int a = 16;
System.out.println(a >> 2);    // 4  (16 / 4, positive: fills with 0s)

int b = -16;
System.out.println(b >> 2);     // -4 (fills with 1s, preserving the sign)

int c = -1;
System.out.println(c >> 1);      // -1 — all bits are already 1, shifting right keeps them all 1
```

Just like `<<`, the shift amount is masked against the operand's bit-width minus one before being applied (modulo 32 for `int`, modulo 64 for `long`).

## 2. Why & when

`>>` is used for:

- Fast division by powers of two for non-negative values: `total >> 1` halves `total` (equivalent to `total / 2` for non-negative `total`, but note the truncation direction differs for negative values — see the walkthrough).
- Extracting a sub-field from a packed value by moving it down to the low-order bits before masking: `(packed >> 8) & 0xFF` extracts an 8-bit field that starts at bit position 8.
- Preserving sign when working with negative numbers in bit-level algorithms, where the alternative unsigned shift (`>>>`, covered separately) would incorrectly turn a negative number into a huge positive one.

The key pitfall: `x >> n` for negative `x` does **not** always equal `x / 2^n` due to rounding direction — integer division truncates toward zero, while `>>` on a negative number rounds toward negative infinity (equivalent to `Math.floorDiv`), so `-7 >> 1` is `-4`, not `-3`.

## 3. Core concept

```java
public class SignedRightShiftDemo {
    public static void main(String[] args) {
        // Positive numbers: >> behaves like division by 2^n
        int a = 16;
        System.out.println("16 >> 2 = " + (a >> 2));   // 4

        // Negative numbers: sign bit is preserved (fills with 1s)
        int b = -16;
        System.out.println("-16 >> 2 = " + (b >> 2));    // -4

        // -1 stays -1 no matter how far you shift: all bits are already 1
        System.out.println("-1 >> 5 = " + (-1 >> 5));     // -1

        // The truncation-vs-floor divergence for negative numbers
        int c = -7;
        System.out.println("-7 / 2  = " + (c / 2));         // -3 (truncates toward zero)
        System.out.println("-7 >> 1 = " + (c >> 1));         // -4 (rounds toward negative infinity)

        // Extracting a sub-field: shift down, then mask
        int packed = 0xAABBCCDD;
        int secondByte = (packed >> 16) & 0xFF;
        System.out.printf("Byte at position 16: 0x%02X%n", secondByte);  // 0xBB
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Signed right shift diagram: shifting negative 16 right by 2 positions moves all bits toward the low end and fills the vacated high bits with copies of the sign bit, which is 1 for a negative number, preserving the negative sign and producing negative 4.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-16 &gt;&gt; 2 — vacated high bits fill with the SIGN bit (1, since the value is negative)</text>

  <text x="20" y="52" fill="#8b949e" font-size="9" font-family="monospace">before (-16):</text>
  <text x="150" y="52" fill="#e6edf3" font-size="11" font-family="monospace">1111...11110000</text>
  <text x="20" y="72" fill="#8b949e" font-size="7.5" font-family="sans-serif">(two's complement: sign bit = 1)</text>

  <path d="M 300 44 L 370 44" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="36" fill="#6db33f" font-size="8" text-anchor="middle">&gt;&gt; 2</text>

  <text x="20" y="100" fill="#8b949e" font-size="9" font-family="monospace">after:</text>
  <text x="150" y="100" fill="#6db33f" font-size="11" font-family="monospace">1111...111111100</text>
  <text x="150" y="120" fill="#79c0ff" font-size="7.5" font-family="sans-serif">↑ two new 1s copied in from the sign bit (not zeros!)</text>

  <text x="350" y="148" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">= -4  (sign preserved throughout the shift)</text>
</svg>

`>>` copies the original sign bit into every newly vacated high-order position, keeping negative values negative.

## 5. Runnable example

Scenario: a fixed-point arithmetic utility (common in embedded/graphics code that avoids floating-point for performance) that scales values by shifting, extended to handle negative scaled values correctly and to extract packed sub-fields from a signed value.

### Level 1 — Basic

```java
public class FixedPointBasic {
    public static void main(String[] args) {
        // Fixed-point representation: store a value scaled by 2^8 (i.e., << 8) to keep 8 fractional bits
        int scaled = 300 << 8;    // represents 300.0 in 8.8 fixed-point format

        // To read it back as a whole number, shift right by the same amount
        int wholePart = scaled >> 8;
        System.out.println("Scaled representation: " + scaled);
        System.out.println("Whole part recovered:  " + wholePart);   // 300, correctly recovered
    }
}
```

**How to run:** `java FixedPointBasic.java`

`300 << 8` encodes `300` in a fixed-point format with 8 fractional bits reserved (multiplying by `256`). `scaled >> 8` reverses this exactly for a positive value, dividing back by `256` and recovering `300` — for positive numbers, `>>` and integer division by the same power of two always agree, since there is no sign-related rounding difference to worry about.

### Level 2 — Intermediate

Same fixed-point utility, now handling negative values (e.g., a negative velocity or offset), showing where `>>` and `/` diverge, and choosing the correct one deliberately based on which rounding behavior the application actually needs.

```java
public class FixedPointIntermediate {

    static int toFixedPoint(int whole) {
        return whole << 8;
    }

    static int fixedPointToWholeFloor(int scaled) {
        return scaled >> 8;   // rounds toward negative infinity — consistent "floor" semantics
    }

    static int fixedPointToWholeTruncate(int scaled) {
        return scaled / 256;   // truncates toward zero — different semantics for negative values
    }

    public static void main(String[] args) {
        int negativeVelocity = toFixedPoint(-3);   // represents -3.0 in fixed point, but let's inspect a fractional case
        int fractionalNegative = (-3 << 8) - 100;   // simulate a slightly-more-negative fractional fixed-point value

        System.out.println("Floor (>>):     " + fixedPointToWholeFloor(fractionalNegative));
        System.out.println("Truncate (/):    " + fixedPointToWholeTruncate(fractionalNegative));
        // These can differ! >> always rounds toward negative infinity; / truncates toward zero.
    }
}
```

**How to run:** `java FixedPointIntermediate.java`

`fractionalNegative` represents a value slightly more negative than `-3.0` in fixed-point form. `fixedPointToWholeFloor` uses `>>`, which (as an arithmetic right shift) always rounds toward negative infinity — for a value representing something like `-3.4`, flooring gives `-4`. `fixedPointToWholeTruncate` uses `/`, which truncates toward zero — for the same value, truncating gives `-3`. Neither is "wrong" in isolation; they are different, well-defined rounding rules, and a fixed-point math library must choose deliberately and document which one it uses, since silently mixing `>>`-based and `/`-based conversions in the same codebase produces off-by-one inconsistencies for negative values specifically.

### Level 3 — Advanced

A genuinely practical use of `>>`: extracting signed sub-fields from a packed sensor reading (e.g., a 16-bit signed temperature delta packed into a larger 32-bit sensor frame), where sign-extension must be handled correctly to recover the original signed value — contrasted with the unsigned extraction that would be needed for a genuinely unsigned field.

```java
public class FixedPointAdvanced {

    // Simulates a 32-bit sensor frame: bits 31-16 = signed 16-bit temperature delta, bits 15-0 = unsigned sensor ID
    static int buildFrame(short temperatureDelta, int sensorId) {
        return (temperatureDelta << 16) | (sensorId & 0xFFFF);
    }

    static int extractTemperatureDelta(int frame) {
        // Shift the field down to occupy the low 16 bits, then let >> sign-extend it correctly
        // because the field originally occupied the HIGH bits, shifting right brings the sign bit down naturally
        return frame >> 16;
    }

    static int extractSensorId(int frame) {
        // Sensor ID is unsigned — mask directly, no sign extension wanted
        return frame & 0xFFFF;
    }

    public static void main(String[] args) {
        int positiveFrame = buildFrame((short) 25, 1001);     // +25 degrees, sensor 1001
        int negativeFrame = buildFrame((short) -18, 1002);     // -18 degrees, sensor 1002

        System.out.println("Positive frame temp: " + extractTemperatureDelta(positiveFrame) + ", sensor: " + extractSensorId(positiveFrame));
        System.out.println("Negative frame temp: " + extractTemperatureDelta(negativeFrame) + ", sensor: " + extractSensorId(negativeFrame));
    }
}
```

**How to run:** `java FixedPointAdvanced.java`

`buildFrame` packs a signed 16-bit `temperatureDelta` into the high 16 bits of the frame using `<<`, and an unsigned `sensorId` into the low 16 bits using `& 0xFFFF` (to ensure only its low 16 bits contribute, avoiding any bleed into the temperature field). `extractTemperatureDelta` uses `>>` (not `>>>`) specifically *because* the temperature field is signed and sits at the very top of the `int`: shifting right by 16 naturally sign-extends the value, since the sign bit of the packed `int` (bit 31) is exactly the sign bit of the original `short` temperature (which occupied bits 16–31), and `>>` copies that same sign bit into the vacated high positions during the shift — the result correctly reconstructs the original signed value, including its sign, without any additional masking needed. `extractSensorId`, by contrast, uses plain `&` masking with no shift needed (the field is already at the bottom) and no `>>` involved at all, since that field is unsigned and needs no sign-related handling.

## 6. Walkthrough

Trace `extractTemperatureDelta(negativeFrame)` where `negativeFrame = buildFrame((short) -18, 1002)`:

**Building the frame.** `(short) -18` in two's complement 16-bit form is `1111111111101110`. `temperatureDelta << 16` shifts this pattern up so it occupies bits 16–31 of the 32-bit `int`: `11111111111011100000000000000000` — wait, more precisely, the shift takes the 16-bit pattern and places it in the upper half, giving a 32-bit value whose top 16 bits are `1111111111101110` and whose bottom 16 bits are (before the OR) all zero. `sensorId & 0xFFFF` computes `1002`'s low 16 bits (`1002` fits entirely within 16 bits, so this is just `1002` itself as a 16-bit pattern, `0000001111101010`). OR-ing the two together combines them into one 32-bit frame with the temperature's bit pattern in the top half and the sensor ID's bit pattern in the bottom half.

**Extracting.** `frame >> 16` shifts the entire 32-bit frame right by 16 positions. This moves what was in bits 16–31 (the temperature delta's bit pattern) down into bits 0–15 of the result. Because `>>` is a signed shift, the vacated high 16 bits (bits 16–31 of the result) are filled with copies of the frame's original sign bit — bit 31 — which was `1` (since the temperature was negative, its sign bit occupied the very top of the frame).

**Sign extension in action.** The result of the shift has its top 16 bits filled with `1`s (from sign extension) and its bottom 16 bits equal to the original temperature pattern (`1111111111101110`). Taken together as a 32-bit two's-complement number, this is exactly `-18` again — the sign extension during the shift correctly reconstructs the full 32-bit negative representation from what was originally only a 16-bit negative value.

```
short -18 (16-bit): 1111111111101110

buildFrame: temperatureDelta << 16 places this pattern in bits 16-31:
  11111111 11101110 00000000 00000000
  | sensorId (1002, in low 16 bits)
  = 11111111 11101110 00000011 11101010   (negativeFrame)

extractTemperatureDelta: negativeFrame >> 16 (signed shift, sign-extends from bit 31 = 1)
  11111111 11111111 11111111 11101110   <- top 16 bits filled with 1s (sign extension)
  = -18  (correctly recovered as a full 32-bit signed value)
```

**Final output.** The program prints both frames' extracted temperature (correctly showing `25` and `-18` respectively) and sensor ID (`1001` and `1002`), demonstrating that `>>` correctly recovers a signed sub-field's sign through sign extension, while plain `&` masking correctly recovers an unsigned sub-field without any sign-related concerns.

## 7. Gotchas & takeaways

> **`>>` on a negative number rounds toward negative infinity, while integer `/` truncates toward zero — they disagree for negative operands.** `-7 >> 1` is `-4`, but `-7 / 2` is `-3`. Choose deliberately based on which rounding behavior your calculation actually needs, and never assume they are interchangeable for negative values.

> **`>>` is the correct shift for extracting a signed sub-field that occupies the highest bits of a value, because it naturally sign-extends during the shift.** Using `>>>` (unsigned right shift) here instead would incorrectly zero-fill the high bits, turning a negative sub-field into a large, incorrect positive number.

- `>>` shifts bits toward the low end and fills vacated high bits with copies of the original sign bit, preserving the value's sign throughout.
- For non-negative operands, `x >> n` equals `x / 2^n`; for negative operands, it equals `Math.floorDiv(x, 2^n)`, which can differ from `x / 2^n`.
- `(packed >> shift) & mask` is the standard idiom for extracting a signed sub-field that needs correct sign extension; use `>>>` instead when the field is unsigned.
- The shift amount is masked modulo the type's bit width, exactly as with `<<`.
