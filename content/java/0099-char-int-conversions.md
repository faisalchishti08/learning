---
card: java
gi: 99
slug: char-int-conversions
title: char ↔ int conversions
---

## 1. What it is

A Java `char` is a 16-bit unsigned type holding a Unicode code point in the Basic Multilingual Plane (U+0000 to U+FFFF). Because its bit representation is a non-negative integer, `char` and integer types interconvert:

- **`char` → `int`** (and wider): implicit widening. The code point value is zero-extended. `'A'` → 65.
- **`int` → `char`**: requires an explicit narrowing cast `(char)`. Only the low 16 bits are kept.
- **`char` in arithmetic**: unary/binary promotion makes `char` an `int` immediately — `'A' + 1` is `int 66`, not `char 'B'`.

```java
char  c = 'A';
int   i = c;            // implicit widening: 65
char  c2 = (char)(c + 1);  // int 66 narrowed back to char 'B'
System.out.println(c2);    // B
```

## 2. Why & when

`char` ↔ `int` conversions are used when:
- Computing with character codes (Caesar cipher, ASCII manipulation, digit extraction).
- Converting between a digit character and its numeric value: `'5' - '0'` gives `int 5`.
- Iterating through a range of characters: `for (char c = 'a'; c <= 'z'; c++)`.
- Working with Unicode code points beyond BMP: supplementary characters require `int` code points and the `codePointAt` / `codePoints()` API.

## 3. Core concept

```java
public class CharIntConversions {

    public static void main(String[] args) {
        // ---- char → int: implicit widening ----
        char  a = 'A';
        int   code = a;           // 65
        System.out.println("'A' code point: " + code);

        // ---- int → char: explicit narrowing cast ----
        int   n = 66;
        char  b = (char) n;       // 'B'
        System.out.println("66 as char: " + b);

        // ---- arithmetic promotes char to int ----
        char  c  = 'c';
        // char upper = c - 32;   // COMPILE ERROR: int, not char
        char  upper = (char)(c - 32);  // 'C'
        System.out.println("lowercase → uppercase: " + upper);

        // ---- digit char → int value ----
        char  digit = '7';
        int   value = digit - '0';   // 55 - 48 = 7
        System.out.println("Digit char '7' → int: " + value);

        // ---- int → char for range iteration ----
        System.out.print("Alphabet: ");
        for (int i = 0; i < 26; i++) {
            System.out.print((char)('a' + i));   // int 'a'+i cast to char
        }
        System.out.println();

        // ---- char comparison with int ----
        char ch = 'A';   // same as 'A'
        System.out.println("'\\u0041' == 'A': " + (ch == 'A'));  // true

        // ---- String.charAt returns char; codePointAt returns int (for supplementary) ----
        String s = "Hello";
        char   first = s.charAt(0);    // 'H'
        int    cp    = s.codePointAt(0);  // 72 (same here, but needed for emoji/supplementary)
        System.out.printf("charAt: %c  codePointAt: %d%n", first, cp);

        // ---- out-of-range int → char wraps ----
        int  outOfRange = 65536;   // 0x10000 — just above 0xFFFF
        char wrapped    = (char) outOfRange;   // 0x0000 = '\0'
        System.out.printf("(char) 65536 = U+%04X%n", (int) wrapped);  // U+0000
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="char to int: implicit widening, zero-extension, code point 65 for A. int to char: explicit cast, low 16 bits, 66 gives B. Arithmetic: char promoted to int before any operator.">
  <rect x="8" y="8" width="684" height="154" rx="8" fill="#0d1117"/>

  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">char ↔ int — code point ↔ character conversions</text>

  <!-- char → int -->
  <rect x="16" y="32" width="206" height="112" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="119" y="48" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">char → int (implicit widening)</text>
  <text x="24" y="64" fill="#e6edf3" font-size="8" font-family="monospace">char c = 'A';  // U+0041</text>
  <text x="24" y="79" fill="#e6edf3" font-size="8" font-family="monospace">int  i = c;    // 65</text>
  <text x="24" y="96" fill="#8b949e" font-size="7" font-family="sans-serif">Zero-extends 16-bit code point</text>
  <text x="24" y="109" fill="#8b949e" font-size="7" font-family="sans-serif">into 32-bit int. Always ≥ 0.</text>
  <text x="24" y="122" fill="#8b949e" font-size="7" font-family="monospace">0000 0041  →  0000 0041</text>
  <text x="24" y="135" fill="#6db33f" font-size="7" font-family="sans-serif">No cast needed.</text>

  <!-- int → char -->
  <rect x="234" y="32" width="206" height="112" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="337" y="48" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">int → char (explicit cast)</text>
  <text x="242" y="64" fill="#e6edf3" font-size="8" font-family="monospace">int  n = 66;</text>
  <text x="242" y="79" fill="#e6edf3" font-size="8" font-family="monospace">char b = (char) n; // 'B'</text>
  <text x="242" y="96" fill="#8b949e" font-size="7" font-family="sans-serif">Keeps low 16 bits only.</text>
  <text x="242" y="109" fill="#8b949e" font-size="7" font-family="sans-serif">Values > 65535 wrap.</text>
  <text x="242" y="122" fill="#8b949e" font-size="7" font-family="monospace">0000 0042  →  0042  = 'B'</text>
  <text x="242" y="135" fill="#8b949e" font-size="7" font-family="sans-serif">Cast required.</text>

  <!-- arithmetic promotion -->
  <rect x="452" y="32" width="234" height="112" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="569" y="48" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">char in arithmetic → int</text>
  <text x="460" y="64" fill="#e6edf3" font-size="8" font-family="monospace">char c = 'c'; // 99</text>
  <text x="460" y="79" fill="#8b949e" font-size="8" font-family="monospace">// char u = c - 32; // ERROR</text>
  <text x="460" y="94" fill="#e6edf3" font-size="8" font-family="monospace">char u = (char)(c-32); // 'C'</text>
  <text x="460" y="109" fill="#8b949e" font-size="7" font-family="sans-serif">Any op on char gives int.</text>
  <text x="460" y="122" fill="#8b949e" font-size="7" font-family="sans-serif">Must cast back to char.</text>
  <text x="460" y="135" fill="#79c0ff" font-size="7" font-family="sans-serif">Compound += hides the cast.</text>
</svg>

`char` is a numeric type — it stores a code point, and arithmetic promotes it to `int` automatically.

## 5. Runnable example

Scenario: a text encoding tool that applies a Caesar cipher to ASCII letters, validates digit characters, and decodes Unicode escape sequences — all operations hinge on `char ↔ int` conversions.

### Level 1 — Basic

```java
public class CharIntBasic {

    // Caesar cipher: shift each letter by 'shift' positions
    static char shiftChar(char c, int shift) {
        if (c >= 'A' && c <= 'Z') {
            return (char)(((c - 'A' + shift) % 26 + 26) % 26 + 'A');
        }
        if (c >= 'a' && c <= 'z') {
            return (char)(((c - 'a' + shift) % 26 + 26) % 26 + 'a');
        }
        return c;  // non-letter unchanged
    }

    public static void main(String[] args) {
        String message = "Hello, World!";
        int shift = 3;

        // Encode: char → int (widening), arithmetic, int → char (cast)
        StringBuilder encoded = new StringBuilder();
        for (char c : message.toCharArray()) {
            encoded.append(shiftChar(c, shift));
        }
        System.out.println("Original: " + message);
        System.out.println("Encoded : " + encoded);

        // Decode: shift by -3 (negative shift handled by (%26+26)%26 pattern)
        StringBuilder decoded = new StringBuilder();
        for (char c : encoded.toString().toCharArray()) {
            decoded.append(shiftChar(c, -shift));
        }
        System.out.println("Decoded : " + decoded);

        // Digit extraction: char → int
        String number = "2024";
        int result = 0;
        for (char d : number.toCharArray()) {
            result = result * 10 + (d - '0');   // char - char → int, then int arithmetic
        }
        System.out.println("Parsed: " + result);
    }
}
```

**How to run:** `java CharIntBasic.java`

`c - 'A'` subtracts two `char` values — both are promoted to `int` by binary promotion. The result is an `int` giving the 0-based position in the alphabet. After adding the shift and taking mod 26, `+ 'A'` adds the base code point (65) back. The final `(char)` cast narrows the `int` result to a `char`. `d - '0'` extracts a digit's numeric value: `'7' - '0' = 55 - 48 = 7`. The `(% 26 + 26) % 26` pattern ensures a non-negative result for negative shifts.

### Level 2 — Intermediate

Same tool: validate and classify characters, convert between uppercase and lowercase, and compute a checksum from character code points.

```java
public class CharIntIntermediate {

    static String classify(char c) {
        int code = c;  // implicit widening
        if (code >= 'A' && code <= 'Z') return "uppercase";
        if (code >= 'a' && code <= 'z') return "lowercase";
        if (code >= '0' && code <= '9') return "digit";
        if (code < 32)  return "control";
        if (code < 128) return "punctuation/space";
        return "extended (U+" + String.format("%04X", code) + ")";
    }

    static char toggleCase(char c) {
        if (c >= 'A' && c <= 'Z') return (char)(c + 32);  // int + int → int, cast to char
        if (c >= 'a' && c <= 'z') return (char)(c - 32);
        return c;
    }

    static int checksum(String text) {
        int sum = 0;
        for (char c : text.toCharArray()) {
            sum += c;   // char widened to int for +=
        }
        return sum % 256;
    }

    public static void main(String[] args) {
        String sample = "Hello42!é";
        System.out.println("Character analysis:");
        for (char c : sample.toCharArray()) {
            System.out.printf("  '%s' (U+%04X) → %s%n",
                c, (int) c, classify(c));
        }

        System.out.println("\nCase toggle:");
        StringBuilder toggled = new StringBuilder();
        for (char c : "Hello World".toCharArray()) {
            toggled.append(toggleCase(c));
        }
        System.out.println("  " + toggled);  // hELLO wORLD

        System.out.println("\nChecksum of 'ABC': " + checksum("ABC"));
        // 65 + 66 + 67 = 198; 198 % 256 = 198
    }
}
```

**How to run:** `java CharIntIntermediate.java`

`int code = c` converts the `char` to its code point via implicit widening. Comparing `code >= 'A'` compares two `int` values — `'A'` is a `char` literal that widens to `int(65)` on each comparison. `(char)(c + 32)` converts uppercase to lowercase: `'A'(65) + 32 = 97 = 'a'`. The `(char)` cast is required because `+` promotes `c` to `int`. `sum += c` widens `c` to `int` before addition — `sum` accumulates all code points.

### Level 3 — Advanced

Same tool: process Unicode beyond the BMP using code points (require `int`), encode to UTF-16 surrogate pairs, and build a frequency map using `char` as array index.

```java
import java.util.*;

public class CharIntAdvanced {

    // Frequency table using char value as array index (BMP only, 0–65535)
    static int[] buildFrequency(String text) {
        int[] freq = new int[65536];
        for (int i = 0; i < text.length(); ) {
            int cp = text.codePointAt(i);   // int code point (may be > 0xFFFF)
            if (cp < 65536) {
                freq[cp]++;
            }
            i += Character.charCount(cp);   // 1 for BMP, 2 for supplementary
        }
        return freq;
    }

    // Encode int code point to char[] (BMP → single char, supplementary → surrogate pair)
    static char[] codePointToChars(int cp) {
        if (cp <= 0xFFFF) {
            return new char[]{(char) cp};  // int → char narrowing
        }
        // Supplementary: compute surrogate pair
        int adjusted = cp - 0x10000;
        char high = (char)(0xD800 + (adjusted >> 10));    // high surrogate
        char low  = (char)(0xDC00 + (adjusted & 0x3FF));  // low surrogate
        return new char[]{high, low};
    }

    public static void main(String[] args) {
        String text = "café résumé naïve";
        int[] freq = buildFrequency(text);

        // Report non-ASCII characters
        System.out.println("Non-ASCII characters:");
        for (int cp = 128; cp < 65536; cp++) {
            if (freq[cp] > 0) {
                System.out.printf("  U+%04X '%s' × %d%n", cp, (char) cp, freq[cp]);
            }
        }

        // Supplementary character demo (U+1F600 GRINNING FACE)
        int emoji = 0x1F600;
        char[] surrogates = codePointToChars(emoji);
        System.out.printf("%nU+%X encodes as %d UTF-16 code unit(s)%n",
            emoji, surrogates.length);
        System.out.printf("  High surrogate: U+%04X%n", (int) surrogates[0]);
        System.out.printf("  Low  surrogate: U+%04X%n", (int) surrogates[1]);
        String emojiStr = new String(surrogates);
        System.out.println("  Reconstructed: " + emojiStr +
            "  length=" + emojiStr.length() +  // 2 (two char units)
            "  codePointCount=" + emojiStr.codePointCount(0, emojiStr.length()));

        // Round-trip: String → int code points → char[] → String
        System.out.println("\nCode points of '" + text + "':");
        text.codePoints().forEach(cp -> System.out.printf("U+%04X ", cp));
        System.out.println();
    }
}
```

**How to run:** `java CharIntAdvanced.java`

`text.codePointAt(i)` returns an `int` — for BMP characters (≤ U+FFFF) this equals `(int) text.charAt(i)`, but for supplementary characters it returns the full code point > 65535. `Character.charCount(cp)` returns 1 for BMP, 2 for supplementary — used to advance the index correctly. In `codePointToChars`, `(char) cp` narrows `int` to `char` — valid only for cp ≤ 65535. The surrogate pair calculation uses `int` arithmetic throughout, with `(char)` casts at the end to narrow each 16-bit surrogate value. `(int) surrogates[0]` widens a `char` to `int` to display the surrogate code point numerically.

## 6. Walkthrough

Trace `shiftChar('z', 3)` (shifts 'z' forward 3 positions, wrapping to 'c'):

**Identify branch.** `c = 'z'`, code point 122. `c >= 'a' && c <= 'z'` → true.

**Compute new position.** `c - 'a'` → `int(122) - int(97) = int(25)`. `25 + 3 = 28`. `28 % 26 = 2`. `(2 + 26) % 26 = 2` (positive-mod safety pattern). `2 + 'a'` → `2 + 97 = 99`.

**Cast.** `(char) 99 = 'c'`. Return `'c'`.

**String concatenation.** When `shiftChar` is used in `encoded.append(shiftChar(...))`, the `char` result is appended directly to the `StringBuilder`. The `StringBuilder.append(char)` overload accepts `char` — no int conversion visible to the caller.

```
char 'z' = 122
'z' - 'a' = 122 - 97 = 25   (both promoted to int, result is int)
25 + 3 = 28
28 % 26 = 2
(2 + 26) % 26 = 2
2 + 'a' = 2 + 97 = 99       ('a' promoted to int)
(char) 99 = 'c'
```

## 7. Gotchas & takeaways

> **`char + char` or `char + int` gives `int`, not `char`.** String concatenation `"" + 'A' + 1` gives `"A1"` (char appended then int appended), but `'A' + 1` gives `66` (int). Use `(char)('A' + 1)` to get `'B'`.

> **`char` is unsigned; `byte` is signed.** `(char)(byte)-1` is `0xFFFF = 65535` (sign-extended byte -1 to int, then low 16 bits as unsigned char). This is often surprising when combining byte streams and char buffers.

> **For Unicode beyond U+FFFF, use `codePointAt` and `codePoints()` instead of `charAt`.** A single emoji may take 2 `char` positions in a Java String. Always test `Character.charCount(cp)` when iterating by code point.

- `char` → `int`: implicit, zero-extension, value is the Unicode code point.
- `int` → `char`: explicit `(char)` cast required; keeps low 16 bits; values > 65535 wrap.
- `char` in arithmetic → always promoted to `int`; cast back with `(char)` to store in `char`.
- `'digit' - '0'` extracts digit value; `'A' - 'a'` (or `+32`/`-32`) flips case (ASCII only).
- Supplementary code points (> U+FFFF) need `int` storage and the `codePointAt` API.
