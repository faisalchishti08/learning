---
card: java
gi: 435
slug: underscores-in-numeric-literals-1-000-000
title: Underscores in numeric literals (1_000_000)
---

## 1. What it is

Java 7 allowed underscores to be placed **between digits** in any numeric literal — decimal, hexadecimal, octal, or binary — purely to improve readability. `1_000_000` is exactly the same `int` as `1000000`; the underscores are stripped by the compiler before the value is interpreted, leaving no trace in the compiled bytecode or runtime value whatsoever.

## 2. Why & when

A long, unbroken run of digits is genuinely hard to read at a glance — `1000000000` requires counting zeros carefully to be sure it's a billion and not a hundred million. Most numbering systems solve this with grouping separators (commas in English: `1,000,000,000`), but commas aren't valid inside a numeric literal's syntax. Underscores fill exactly that role in source code: `1_000_000_000` is instantly readable as one billion, with zero risk of miscounting digits, and — since it's purely a compile-time notation — zero runtime cost or behavioral difference.

You reach for this any time a numeric literal is long enough that miscounting digits becomes a real risk: large monetary amounts, timestamps in milliseconds, byte-count constants, or (as the previous tutorial on binary literals showed) grouping bit patterns into readable chunks like bytes or nibbles.

## 3. Core concept

```java
int oneMillion = 1_000_000;              // clearly "one million" at a glance
long worldPopulation = 8_100_000_000L;   // clearly "8.1 billion"

int hexAddress = 0xFF_EC_A4_10;          // groups hex digits into byte pairs
int binaryFlags = 0b1010_0110;           // groups binary digits into a byte

System.out.println(oneMillion);          // 1000000 -- underscores are gone, purely a source-code convenience
```

The underscores exist **only** in the source text; once compiled, `1_000_000` and `1000000` produce byte-for-byte identical bytecode.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Underscores placed between digits in a numeric literal group it visually, like a comma separator, but are removed entirely by the compiler before the value is interpreted">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">Source code (readable):</text>
  <rect x="30" y="38" width="220" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="140" y="58" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">1_000_000_000</text>

  <text x="20" y="95" fill="#e6edf3" font-size="11" font-family="sans-serif">Compiled value (identical either way):</text>
  <rect x="30" y="107" width="220" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="140" y="127" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">1000000000 (int)</text>

  <text x="470" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The underscores never survive compilation --</text>
  <text x="470" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">a purely readability-only source feature.</text>
</svg>

Underscores are stripped entirely at compile time — the resulting value is byte-for-byte identical to the same digits written without them.

## 5. Runnable example

Scenario: a set of large, easy-to-miscount financial and technical constants — the same underscore grouping technique, evolved from a basic large integer, through an annual revenue calculation combining several grouped literals, to grouping hexadecimal and binary literals into meaningful byte-sized chunks.

### Level 1 — Basic

```java
public class UnderscoreBasic {
    public static void main(String[] args) {
        int oneMillion = 1_000_000;
        long worldPopulation = 8_100_000_000L;
        System.out.println("One million: " + oneMillion);
        System.out.println("World population: " + worldPopulation);
    }
}
```

**How to run:** `java UnderscoreBasic.java`

`1_000_000` and `8_100_000_000L` are immediately readable as "one million" and "8.1 billion" respectively — compare this to `1000000` and `8100000000L`, where you'd need to carefully count zeros to be confident of the magnitude.

### Level 2 — Intermediate

```java
public class RevenueCalc {
    public static void main(String[] args) {
        long q1_revenue = 1_250_000;
        long q2_revenue = 1_430_500;
        long q3_revenue = 1_610_250;
        long q4_revenue = 2_005_000;

        long annualTotal = q1_revenue + q2_revenue + q3_revenue + q4_revenue;
        System.out.printf("Annual total: $%,d%n", annualTotal);

        double taxRate = 0.21;
        double afterTax = annualTotal * (1 - taxRate);
        System.out.printf("After 21%% tax: $%,.2f%n", afterTax);
    }
}
```

**How to run:** `java RevenueCalc.java`

Each quarterly figure is grouped into thousands, making the source code itself easy to audit at a glance — and note the `%,d`/`%,.2f` format specifiers in `printf` (covered in the `java.util.Formatter` tutorial) add the *display-time* comma grouping, a separate mechanism from the *source-code* underscores used to write the literals.

### Level 3 — Advanced

```java
public class MemoryAddressGrouping {
    public static void main(String[] args) {
        // Underscores group hex digits into byte pairs, making a 32-bit address readable at a glance
        int memoryAddress = 0xFF_EC_A4_10;
        System.out.println("Address: 0x" + Integer.toHexString(memoryAddress).toUpperCase());

        // Underscores work with binary literals too, grouping into bytes
        int flagsByte = 0b1010_0110;
        System.out.println("Flags byte: " + Integer.toBinaryString(flagsByte));

        // Underscores can appear ANYWHERE between digits, including breaking up a long constant unevenly
        long serialNumber = 123_456_789_012L;
        System.out.println("Serial number: " + serialNumber);
    }
}
```

**How to run:** `java MemoryAddressGrouping.java`

`0xFF_EC_A4_10` groups a 32-bit address into its four constituent bytes, and `0b1010_0110` groups a binary literal the same way — both make the underlying byte structure visually obvious. `123_456_789_012L` shows that grouping doesn't have to follow any fixed rule (like always every three digits) — underscores can be placed between *any* two adjacent digits, wherever it best aids readability.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `memoryAddress` is assigned `0xFF_EC_A4_10` — the compiler strips the underscores, leaving the hexadecimal value `0xFFECA410`, an ordinary 32-bit `int` (its two's-complement bit pattern happens to represent a negative number if interpreted as signed, but that's incidental to this example — the address value itself is `0xFFECA410`).

`Integer.toHexString(memoryAddress)` converts that `int` back to a hexadecimal `String`, which is uppercased and printed with a `"0x"` prefix, reconstructing exactly the same digits the literal was written with (though without the grouping underscores, since `toHexString` has no notion of them — they existed only in the source).

`flagsByte` is assigned `0b1010_0110` — stripped of its underscore, this is the binary value `0b10100110`, decimal `166`. `Integer.toBinaryString(flagsByte)` prints it back as `"10100110"`.

`serialNumber` is assigned `123_456_789_012L` — stripped of its underscores (which happen to fall every three digits here, though that's just this example's choice, not a requirement), this is the `long` value `123456789012`, printed directly.

Expected output:
```
Address: 0xFFECA410
Flags byte: 10100110
Serial number: 123456789012
```

## 7. Gotchas & takeaways

> Underscores can only appear **between** digits — never at the very start or end of the digit sequence, never immediately adjacent to a decimal point, and never immediately before a type suffix like `L`, `f`, or `d`. `1_000._05` (underscore touching the decimal point) and `_1000` (leading underscore) are both compile errors, not silently-ignored typos — the compiler rejects them outright with an "illegal underscore" message.

- Underscores in numeric literals are a purely compile-time readability aid — they're stripped before the value is interpreted, with zero effect on the compiled bytecode or runtime behavior.
- They work in decimal, hexadecimal, octal, and binary literals alike, and can be placed between any two adjacent digits, not just at fixed intervals.
- Placement rules matter: never at the start or end of the digit sequence, never touching a decimal point, and never immediately before a type suffix (`L`, `f`, `d`) — violating any of these is a compile error.
- Grouping choices should reflect what's meaningful for the value: three-digit groups for large decimal counts (matching how humans read large numbers), or byte/nibble-sized groups for hex or binary bit patterns.
- This feature pairs naturally with binary literals (the previous tutorial) — together, they make bit-level and byte-level constants dramatically easier to read and verify correctly in source code.
