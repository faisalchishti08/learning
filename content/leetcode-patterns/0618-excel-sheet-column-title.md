---
card: leetcode-patterns
gi: 618
slug: excel-sheet-column-title
title: Excel Sheet Column Title
---

## 1. What it is

Given an integer `columnNumber`, return its corresponding Excel column title, the reverse of [Excel Sheet Column Number](0602-excel-sheet-column-number.md): `1 -> "A"`, `26 -> "Z"`, `27 -> "AA"`, `28 -> "AB"`. Example: `columnNumber=701` → `"ZY"`.

## 2. Why & when

This is base-26 conversion in the opposite direction from the earlier problem — number to letters instead of letters to number. Because Excel's column naming has no symbol for "zero" (letters run `1..26`, not `0..25`), the standard "repeatedly take `% base`, then `/ base`" conversion needs a one-step adjustment at each digit, or it produces wrong results whenever a "26" (which should map to `Z`) would otherwise compute as digit `0`.

## 3. Core concept

**Key idea:** at each step, extract the current least-significant letter using `(columnNumber - 1) % 26`, mapping the result (`0..25`) to a letter (`'A'..'Z'`) by adding `'A'`. Then advance to the next digit with `columnNumber = (columnNumber - 1) / 26`. The `- 1` in both places is what shifts the range from the natural `1..26` into a `0..25` range that standard modular arithmetic can cleanly extract, before shifting back by adding `'A'`.

**Steps:**
1. Initialize an empty result (built up in reverse, since digits come out least-significant first, just like decimal-to-string conversion).
2. While `columnNumber > 0`: compute `remainder = (columnNumber - 1) % 26`. Prepend (or append, then reverse at the end) the character `(char)('A' + remainder)`.
3. Update `columnNumber = (columnNumber - 1) / 26`.
4. Repeat until `columnNumber` reaches `0`. Return the accumulated characters (reversed, if appended rather than prepended).

**Why the `-1` adjustment is required, worked through on `columnNumber=26`:** without the adjustment, `26 % 26 = 0`, which would map to `'A'` — wrong, since `26` should be `'Z'`. With the adjustment: `(26-1) % 26 = 25`, mapping correctly to `'A' + 25 = 'Z'`. Then `(26-1)/26 = 0`, correctly ending the loop with no further (incorrect) leading digit — without the `-1` in the division step too, `26/26=1` would incorrectly continue the loop for one more (spurious) digit.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Converting 28 to AB: without the minus-one adjustment the naive mod-26 conversion gives the wrong letter">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">naive: 28 % 26 = 2 -&gt; 'C' (wrong)</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">adjusted: (28-1) % 26 = 1 -&gt; 'B' (correct)</text>
    <rect x="60" y="40" width="180" height="30" fill="#161b22" stroke="#f85149"/><text x="150" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">naive gives "C" for last letter</text>
    <rect x="440" y="40" width="180" height="30" fill="#161b22" stroke="#3fb950"/><text x="530" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">adjusted gives "B" for last letter</text>
    <text x="350" y="120" fill="#79c0ff" text-anchor="middle">28 = "AB": the -1 shift is what correctly produces "B", not "C"</text>
  </g>
</svg>

The `-1` shift before taking `% 26` and before dividing is what correctly accounts for Excel's 1-indexed (no-zero) letter system at every digit position.

## 5. Runnable example

**Level 1 — Brute force.** Precompute powers of 26 and figure out, digit position by digit position, how many letters fit — a more complex, error-prone way to arrive at the same bijective base-26 conversion, essentially re-deriving the `-1` adjustment through a different (harder to get right) route.

**KEY INSIGHT:** shifting `columnNumber` down by `1` before both the modulus and the division operations is the single, minimal change needed to adapt the standard "repeatedly mod and divide by the base" conversion to a number system with no symbol for zero.

**Level 2 — Optimal.** Loop with the `-1` adjustment at each step, O(log₂₆(columnNumber)) time, same for space (the output string length).

**Level 3 — Hardened.** Correctly builds the result in the right order (either by prepending, or appending then reversing), and correctly terminates exactly when `columnNumber` reaches `0` after the adjusted division.

```java
// ExcelSheetColumnTitle.java
public class ExcelSheetColumnTitle {

    public static String convertToTitle(int columnNumber) {
        StringBuilder sb = new StringBuilder();
        while (columnNumber > 0) {
            int remainder = (columnNumber - 1) % 26;
            sb.append((char) ('A' + remainder));
            columnNumber = (columnNumber - 1) / 26;
        }
        return sb.reverse().toString();
    }

    public static void main(String[] args) {
        System.out.println(convertToTitle(1));   // A
        System.out.println(convertToTitle(28));  // AB
        System.out.println(convertToTitle(701)); // ZY
    }
}
```

**How to run:** save as `ExcelSheetColumnTitle.java`, then run `java ExcelSheetColumnTitle.java`.

## 6. Walkthrough

Dry-run `convertToTitle(28)`:

| step | columnNumber | remainder=(cn-1)%26 | char appended | next columnNumber=(cn-1)/26 |
|---|---|---|---|---|
| 1 | 28 | 27%26=1 | 'B' | 27/26=1 |
| 2 | 1 | 0%26=0 | 'A' | 0/26=0 |

Loop ends (`columnNumber=0`). Appended characters in order: `'B', 'A'` → reversed → `"AB"`, matching the expected column title for `28`.

## 7. Gotchas & takeaways

> Gotcha: applying the `-1` adjustment to the modulus but forgetting it in the division step (using `columnNumber /= 26` instead of `columnNumber = (columnNumber - 1) / 26`) produces an extra spurious leading digit for values that are exact multiples of `26` (like `26` itself), since the unadjusted division does not correctly signal "no more digits remain."

- Signal: converting a number to a positional string representation where the alphabet has no zero symbol is the bijective (bias-adjusted) base conversion signal.
- The `-1` shift must be applied consistently at *both* the modulus and the division steps, not just one.
- Related problems: Excel Sheet Column Number (the reverse conversion, letters to number, which needs no such adjustment since standard positional accumulation already handles a 1-indexed digit range correctly in that direction).
