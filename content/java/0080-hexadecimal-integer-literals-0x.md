---
card: java
gi: 80
slug: hexadecimal-integer-literals-0x
title: Hexadecimal integer literals (0x…)
---

## 1. What it is

A hexadecimal integer literal starts with the prefix `0x` (or `0X`) followed by one or more hex digits (`0`–`9`, `a`–`f`, `A`–`F`). It represents a base-16 integer value. Like decimal and octal literals, it is an `int` by default and becomes a `long` with the `L` suffix. Case of letters is insignificant: `0xFF` and `0xff` and `0XFF` are identical.

```java
int  red      = 0xFF0000;   // 16711680 — 24-bit RGB red
int  mask     = 0xFF;       // 255 — low-byte mask
long deadbeef = 0xDEADBEEFL;// well-known test constant
int  status   = 0x1A4;      // 420 — same as decimal 420
```

Hex is the preferred notation whenever the meaning of a value is tied to its bit pattern, because one hex digit maps to exactly four bits (one nibble), making the relationship between hex digits and binary transparent.

## 2. Why & when

Use hex literals when:
- **Bit masks** — `0xFF` clearly means "lowest 8 bits"; `0xFF000000` means "top byte of a 32-bit value".
- **Color values** — RGB triplets (`0x1E90FF` = `dodgerblue`) are universally written in hex.
- **Protocol constants and magic numbers** — file format signatures, error codes, and hardware register addresses are documented and remembered in hex.
- **Unicode code points** — `0x1F600` for the 😀 emoji, `0x20AC` for the `€` sign.
- **Hash / CRC values** — 32- and 64-bit digests are conventionally displayed in hex.

Decimal is better when the value is a human-readable count or measurement. Hex is better when the value is a pattern of bits.

## 3. Core concept

```java
// ---- Basic hex literals ----
int a = 0x0F;    // 15
int b = 0x10;    // 16
int c = 0xFF;    // 255
int d = 0xFFFF;  // 65535  (full 16-bit mask)

// ---- Case-insensitive hex digits ----
System.out.println(0xA == 0xa);    // true
System.out.println(0xFF == 0xff);  // true

// ---- Long hex literal ----
long maxUnsigned32 = 0xFFFFFFFFL;   // 4294967295 — can't fit in int
int  signedNeg     = 0xFFFFFFFF;    // -1 as a signed 32-bit int

System.out.println(0xFFFFFFFF);     // -1  (int with all bits set = -1 in two's complement)
System.out.println(0xFFFFFFFFL);    // 4294967295  (long)

// ---- Bit masking ----
int colour = 0x1E90FF;   // dodgerblue #1E90FF
int r = (colour >> 16) & 0xFF;  // 0x1E = 30
int g = (colour >>  8) & 0xFF;  // 0x90 = 144
int bv= colour          & 0xFF;  // 0xFF = 255
System.out.printf("R=%d G=%d B=%d%n", r, g, bv);   // R=30 G=144 B=255

// ---- Conversion: int ↔ hex string ----
System.out.println(Integer.toHexString(255));       // ff
System.out.println(Integer.toHexString(0x1E90FF));  // 1e90ff
System.out.printf("0x%08X%n", 0x1E90FF);            // 0x001E90FF  (8-digit padded)

int fromHexStr = Integer.parseInt("1E90FF", 16);    // 2003199
System.out.println(fromHexStr == 0x1E90FF);         // true

// ---- Underscores for readability ----
long guid = 0x550E_8400_E29B_41D4L;   // UUID-style grouping
int  mask2 = 0xFF_FF_FF_FF;           // four bytes clearly delimited (-1 as int)
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hexadecimal literal anatomy: 0x prefix, hex digits, nibble-to-bit mapping, and RGB colour extraction example">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>

  <!-- Token anatomy -->
  <rect x="16" y="18" width="668" height="55" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Hex literal 0x1E90FF and nibble–bit correspondence</text>

  <!-- 0x prefix -->
  <rect x="80" y="38" width="40" height="26" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="100" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">0x</text>

  <!-- 1E -->
  <rect x="124" y="38" width="40" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="144" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">1E</text>

  <!-- 90 -->
  <rect x="168" y="38" width="40" height="26" rx="3" fill="#79c0ff" opacity="0.5"/>
  <text x="188" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">90</text>

  <!-- FF -->
  <rect x="212" y="38" width="40" height="26" rx="3" fill="#79c0ff" opacity="0.3"/>
  <text x="232" y="55" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">FF</text>

  <!-- annotations -->
  <text x="100"  y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">prefix</text>
  <text x="144"  y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">R=30</text>
  <text x="188"  y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">G=144</text>
  <text x="232"  y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">B=255</text>

  <text x="420"  y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1 hex digit = 4 bits (1 nibble)</text>
  <text x="420"  y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2 hex digits = 1 byte (8 bits)</text>

  <!-- Nibble table -->
  <rect x="16" y="92" width="330" height="74" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="181" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Hex digit → 4 bits (nibble)</text>
  <line x1="26" y1="114" x2="336" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="128" fill="#e6edf3" font-size="7.5" font-family="monospace">0=0000  1=0001  2=0010  3=0011</text>
  <text x="26" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">4=0100  5=0101  6=0110  7=0111</text>
  <text x="26" y="154" fill="#e6edf3" font-size="7.5" font-family="monospace">8=1000  9=1001  A=1010  B=1011</text>
  <text x="26" y="167" fill="#e6edf3" font-size="7.5" font-family="monospace">C=1100  D=1101  E=1110  F=1111</text>

  <!-- Mask patterns box -->
  <rect x="358" y="92" width="326" height="74" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="521" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Common bitmask patterns</text>
  <line x1="368" y1="114" x2="674" y2="114" stroke="#8b949e" stroke-width="0.5"/>
  <text x="368" y="128" fill="#e6edf3" font-size="7.5" font-family="monospace">0xFF       → low 8 bits</text>
  <text x="368" y="141" fill="#e6edf3" font-size="7.5" font-family="monospace">0xFFFF     → low 16 bits</text>
  <text x="368" y="154" fill="#e6edf3" font-size="7.5" font-family="monospace">0xFF000000 → top byte of int</text>
  <text x="368" y="167" fill="#8b949e" font-size="7.5" font-family="monospace">0xFFFFFFFFL → all 32 bits (long)</text>
</svg>

Each hex digit maps to exactly 4 bits, making `0x1E90FF` a self-documenting 24-bit RGB value where each byte-pair is a colour channel.

## 5. Runnable example

Scenario: a 24-bit RGB colour utilities library — packs, unpacks, blends, and displays colours using hex literals. The scenario grows from simple packing/unpacking to alpha-blended composition and finally to a web-hex formatter and named-colour lookup.

### Level 1 — Basic

```java
public class HexLiteralsBasic {

    static int rgb(int r, int g, int b) {
        return (r << 16) | (g << 8) | b;
    }

    static int red(int colour)   { return (colour >> 16) & 0xFF; }
    static int green(int colour) { return (colour >>  8) & 0xFF; }
    static int blue(int colour)  { return  colour        & 0xFF; }

    public static void main(String[] args) {
        // Colour constants as hex literals
        int RED     = 0xFF0000;
        int GREEN   = 0x00FF00;
        int BLUE    = 0x0000FF;
        int WHITE   = 0xFFFFFF;
        int BLACK   = 0x000000;
        int CYAN    = 0x00FFFF;

        int[] colours = {RED, GREEN, BLUE, WHITE, BLACK, CYAN};
        String[] names = {"RED", "GREEN", "BLUE", "WHITE", "BLACK", "CYAN"};

        System.out.printf("%-8s  %8s  %4s  %4s  %4s%n", "Name", "Hex", "R", "G", "B");
        System.out.println("-".repeat(36));
        for (int i = 0; i < colours.length; i++) {
            System.out.printf("%-8s  #%06X  %4d  %4d  %4d%n",
                names[i], colours[i], red(colours[i]), green(colours[i]), blue(colours[i]));
        }

        // Pack from RGB components
        int custom = rgb(100, 149, 237);   // cornflower blue
        System.out.printf("%nCustom #%06X : R=%d G=%d B=%d%n",
            custom, red(custom), green(custom), blue(custom));
    }
}
```

**How to run:** `java HexLiteralsBasic.java`

`0xFF0000` is decimal 16 711 680. The `red` extractor shifts right 16 bits and masks with `0xFF` to isolate the top 8 bits. `0xFF` is the ideal mask constant because it is self-documenting: one `F` per nibble, two nibbles per byte, so `0xFF` = `255` = all 8 bits set. `%06X` in `printf` formats an integer as uppercase hex with at least 6 digits, zero-padded — the web `#RRGGBB` convention.

### Level 2 — Intermediate

Same colour utility: add an alpha channel (ARGB) using the top 8 bits, demonstrate `0xFFFFFFFF` as `-1` in a signed `int`, and use `Long` to work with ARGB values correctly.

```java
public class HexLiteralsIntermediate {

    static int argb(int a, int r, int g, int b) {
        return (a << 24) | (r << 16) | (g << 8) | b;
    }

    static int alpha(int colour) { return (colour >>> 24) & 0xFF; }
    static int red(int colour)   { return (colour >> 16)  & 0xFF; }
    static int green(int colour) { return (colour >>  8)  & 0xFF; }
    static int blue(int colour)  { return  colour         & 0xFF; }

    static String toHexARGB(int argbVal) {
        return String.format("#%08X", argbVal);
    }

    public static void main(String[] args) {
        int opaqueRed       = 0xFFFF0000;   // fully opaque red — but this is -65536 as signed int!
        int semiTransparent = 0x80FF0000;   // 50% transparent red

        System.out.println("0xFFFF0000 as signed int : " + opaqueRed);       // -65536
        System.out.println("0xFFFF0000 unsigned (long): " + (opaqueRed & 0xFFFFFFFFL)); // 4294901760

        System.out.printf("%nopaque red   : %s  alpha=%d r=%d g=%d b=%d%n",
            toHexARGB(opaqueRed),
            alpha(opaqueRed), red(opaqueRed), green(opaqueRed), blue(opaqueRed));

        System.out.printf("semi-trans   : %s  alpha=%d r=%d g=%d b=%d%n",
            toHexARGB(semiTransparent),
            alpha(semiTransparent), red(semiTransparent),
            green(semiTransparent), blue(semiTransparent));

        // Unsigned right-shift vs signed right-shift for the alpha channel
        int packed = 0xCC_10_20_30;
        System.out.println();
        System.out.println("Packed ARGB: " + String.format("0x%08X", packed));
        System.out.println(">> 24  (signed)  : " + (packed >> 24));    // -52 (sign-extended)
        System.out.println(">>> 24 (unsigned): " + (packed >>> 24));   // 204  (0xCC)
        System.out.println("& 0xFF after >>>  : " + ((packed >>> 24) & 0xFF));  // 204
    }
}
```

**How to run:** `java HexLiteralsIntermediate.java`

`0xFFFF0000` has all bits set in the top half, so as a signed `int` it is negative (`-65536`). To get the unsigned interpretation, widen to `long` and mask: `opaqueRed & 0xFFFFFFFFL`. When extracting the alpha channel with `>>`, the signed right-shift propagates the sign bit — for `0xCC_...` (top bit set) this gives `-52`. The unsigned right-shift `>>>` fills the top bits with zeros, giving `0xCC = 204`. Always mask with `& 0xFF` after any shift when extracting a single byte.

### Level 3 — Advanced

Same system: build a complete ARGB colour class that handles hex string parsing, blending two colours with a given ratio, and demonstrates `0xFFFFFFFF` stored in a `long`.

```java
import java.util.Map;

public class HexLiteralsAdvanced {

    record Colour(int argb) {
        int alpha() { return (argb >>> 24) & 0xFF; }
        int red()   { return (argb >> 16)  & 0xFF; }
        int green() { return (argb >>  8)  & 0xFF; }
        int blue()  { return  argb         & 0xFF; }

        // Parse "#RRGGBB" or "#AARRGGBB"
        static Colour parse(String hex) {
            String clean = hex.startsWith("#") ? hex.substring(1) : hex;
            int len = clean.length();
            if (len != 6 && len != 8)
                throw new IllegalArgumentException("Expected 6 or 8 hex digits: " + hex);
            long raw = Long.parseLong(clean, 16);
            int value = (len == 6) ? (int)(0xFF000000L | raw) : (int) raw;
            return new Colour(value);
        }

        // Blend: t=0 → this, t=1 → other
        Colour blend(Colour other, double t) {
            int a = lerp(alpha(), other.alpha(), t);
            int r = lerp(red(),   other.red(),   t);
            int g = lerp(green(), other.green(), t);
            int b = lerp(blue(),  other.blue(),  t);
            return new Colour((a << 24) | (r << 16) | (g << 8) | b);
        }

        static int lerp(int from, int to, double t) {
            return (int) Math.round(from + (to - from) * t);
        }

        @Override public String toString() {
            return String.format("#%02X%02X%02X%02X", alpha(), red(), green(), blue());
        }
    }

    public static void main(String[] args) {
        // Named colours
        Map<String, Colour> palette = Map.of(
            "dodgerblue", Colour.parse("#1E90FF"),
            "tomato",     Colour.parse("#FF6347"),
            "black",      Colour.parse("#000000")
        );

        System.out.println("=== Colour palette ===");
        palette.forEach((name, c) ->
            System.out.printf("%-14s  %s  R=%3d G=%3d B=%3d  alpha=%3d%n",
                name, c, c.red(), c.green(), c.blue(), c.alpha()));

        // Blend dodgerblue → tomato in 5 steps
        Colour from = palette.get("dodgerblue");
        Colour to   = palette.get("tomato");
        System.out.println("\n=== Gradient: dodgerblue → tomato ===");
        for (int i = 0; i <= 4; i++) {
            double t = i / 4.0;
            Colour blended = from.blend(to, t);
            System.out.printf("  t=%.2f  %s%n", t, blended);
        }

        // Long hex literals for 64-bit patterns
        System.out.println("\n=== 64-bit hex patterns ===");
        long mask32  = 0xFFFFFFFFL;    // all 32 low bits set
        long hiBytes = 0xFF00_FF00_FF00_FF00L;
        System.out.printf("0xFFFFFFFFL   = %,d%n", mask32);
        System.out.printf("0xFF00FF00... = 0x%016X%n", hiBytes);
    }
}
```

**How to run:** `java HexLiteralsAdvanced.java`

`Long.parseLong(clean, 16)` parses a hex string as a `long` — using `Long` (not `Integer`) avoids overflow when the string represents values above `0x7FFFFFFF`. The cast to `int` is safe because the value fits after the parse. `0xFF000000L | raw` fills in an opaque alpha byte when the input string is only 6 hex digits. The `lerp` function linearly interpolates between two integer values using a `double` fraction `t`, which provides smooth blending. The 64-bit constant `0xFF00_FF00_FF00_FF00L` requires the `L` suffix because it is larger than `Integer.MAX_VALUE`; without `L` the compiler reports "integer number too large."

## 6. Walkthrough

Execution trace through `HexLiteralsAdvanced.main` for `Colour.parse("#1E90FF")`:

**Strip prefix.** `clean = "1E90FF"`, `len = 6`.

**Parse.** `Long.parseLong("1E90FF", 16)` = `1E90FF` base 16 = `1 × 16⁵ + 14 × 16⁴ + 9 × 16³ + 0 × 16² + 15 × 16¹ + 15 × 16⁰` = `1 048 576 + 917 504 + 36 864 + 0 + 240 + 15` = `2 003 199`.

**Opaque fill.** `0xFF000000L | 2_003_199L` = `0xFF1E90FF` = `-7 892 993` as a signed `int`. Cast to `int`: still `-7 892 993`.

**Component extraction.** `red()`: `((-7892993) >> 16) & 0xFF` = `0xFF1E >> 0 ... ` — more precisely: `argb = 0xFF1E90FF`. `argb >> 16 = 0xFFFF1E` (sign-extended), `& 0xFF = 0x1E = 30`. `green()`: `argb >> 8 = 0xFF1E90`, `& 0xFF = 0x90 = 144`. `blue()`: `argb & 0xFF = 0xFF = 255`.

**Blend step at `t = 0.5`.** `lerp(30, 255, 0.5) = round(30 + 112.5) = 143`. `lerp(144, 99, 0.5) = round(144 − 22.5) = 122`. `lerp(255, 71, 0.5) = round(255 − 92) = 163`. Result: `#FF8F7AA3` — a purple-ish midpoint.

```
Colour.parse("#1E90FF"):
  clean  = "1E90FF"
  raw    = Long.parseLong("1E90FF", 16) = 2003199
  argb   = (int)(0xFF000000L | 2003199) = 0xFF1E90FF = -7892993

  .red()   = (0xFF1E90FF >> 16) & 0xFF = 0x1E = 30
  .green() = (0xFF1E90FF >>  8) & 0xFF = 0x90 = 144
  .blue()  =  0xFF1E90FF        & 0xFF = 0xFF = 255
```

## 7. Gotchas & takeaways

> **`0xFFFFFFFF` is `-1` as a signed `int`, not `4 294 967 295`.** Java `int` is always signed. When a hex literal has all 32 bits set, it is interpreted as the two's complement value `-1`. To get the unsigned `4 294 967 295`, use `0xFFFFFFFFL` (a `long` literal) or `Integer.toUnsignedLong(i)`.

> **Always use `>>>` (unsigned right-shift) when extracting a high byte from a negative int.** `signed >> 24` sign-extends the result, giving a negative number. `unsigned >>> 24` fills high bits with zeros, giving the raw byte value. Follow with `& 0xFF` to isolate exactly 8 bits.

- Hex literals start with `0x` or `0X`; case of the hex digits (`a`–`f` vs `A`–`F`) does not matter.
- One hex digit = 4 bits (one nibble); two hex digits = one byte — making bit patterns self-documenting.
- Append `L` for hex values that need more than 32 bits: `0xFFFFFFFFL`.
- `Integer.toHexString(n)` converts to a hex string without the `0x` prefix and without padding.
- `String.format("0x%08X", n)` produces an 8-digit uppercase hex string with the `0x` prefix.
- `Integer.parseInt(s, 16)` and `Long.parseLong(s, 16)` parse hex strings at runtime.
- Use underscores to group bytes: `0xFF_AA_BB_CC` clearly shows four independent bytes.
