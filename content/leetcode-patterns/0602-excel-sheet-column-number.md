---
card: leetcode-patterns
gi: 602
slug: excel-sheet-column-number
title: Excel Sheet Column Number
---

## 1. What it is

Given a string `columnTitle` representing an Excel spreadsheet column header (`"A", "B", ..., "Z", "AA", "AB", ...`), return its corresponding column number, where `A=1, B=2, ..., Z=26, AA=27, AB=28`, and so on. Example: `columnTitle="A"` → `1`; `columnTitle="AB"` → `28`; `columnTitle="ZY"` → `701`.

## 2. Why & when

This is base-26 number conversion, but with a twist: standard base conversion (like binary or decimal) uses digits `0` through `base-1`, but Excel's column naming uses `1` through `26` (`A=1`, not `A=0`) — there is no symbol for "zero." Recognizing this as a **bijective base-26** system (as opposed to a standard positional base-26 system) is the key to writing the conversion correctly, rather than treating each letter as if `A` meant `0`.

## 3. Core concept

**Key idea:** process the string left to right, exactly like converting a normal base-`b` number to decimal: `result = result * 26 + digitValue`, where `digitValue` for a letter is `(letter - 'A' + 1)` — mapping `A→1, B→2, ..., Z→26`, matching the problem's 1-indexed letter values directly.

**Steps:**
1. Initialize `result = 0`.
2. For each character `c` in `columnTitle`, left to right: compute `digitValue = c - 'A' + 1`.
3. Update `result = result * 26 + digitValue`.
4. After processing every character, `result` holds the final column number.

**Why this differs from a normal base-26 conversion:** in a standard positional base-`b` system, each digit ranges over `0..b-1`. Here, each "digit" (letter) ranges over `1..26` instead, since there is no symbol for zero. The same accumulation formula still works correctly with this shifted range. The recurrence does not care whether digits start at `0` or `1` — it only needs them to stay within a fixed, consistent range at every position.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Converting AB to a column number: A contributes 1 times 26, B contributes 2, totaling 28">
  <g font-family="sans-serif" font-size="12">
    <rect x="60" y="30" width="60" height="35" fill="#161b22" stroke="#3fb950"/><text x="90" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">A=1</text>
    <rect x="140" y="30" width="60" height="35" fill="#161b22" stroke="#f0883e"/><text x="170" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">B=2</text>
    <text x="400" y="45" fill="#79c0ff" text-anchor="middle">result = 0*26+1 = 1, then 1*26+2 = 28</text>
    <text x="350" y="100" fill="#8b949e" text-anchor="middle">same accumulation formula as decimal-to-int, but each digit ranges 1..26, not 0..25</text>
  </g>
</svg>

Each new letter multiplies the running result by 26 (shifting up one "place") and adds the new letter's 1-indexed value — identical in shape to converting any base-`b` string to an integer.

## 5. Runnable example

**Level 1 — Brute force.** Precompute powers of 26 for each position, then sum `digitValue x 26^position` for every character. Correct, but requires computing powers explicitly and iterating twice (or tracking position math) — more code for the same result.

**KEY INSIGHT:** the standard left-to-right "multiply running total by the base, add the new digit" accumulation formula (used for any base conversion) works here unmodified, once `digitValue` is defined as the letter's 1-indexed value (`'A'` maps to `1`, not `0`).

**Level 2 — Optimal.** Single left-to-right pass, `result = result * 26 + digitValue`, O(length) time, O(1) space.

**Level 3 — Hardened.** Correctly handles multi-letter titles of any length (not just two letters), and correctly computes `digitValue` using `'A' + 1` as the base offset (not `'A'`, which would be the standard-base-26 offset and give wrong answers).

```java
// ExcelSheetColumnNumber.java
public class ExcelSheetColumnNumber {

    public static int titleToNumber(String columnTitle) {
        int result = 0;
        for (char c : columnTitle.toCharArray()) {
            int digitValue = c - 'A' + 1;
            result = result * 26 + digitValue;
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(titleToNumber("A"));  // 1
        System.out.println(titleToNumber("AB")); // 28
        System.out.println(titleToNumber("ZY")); // 701
    }
}
```

**How to run:** save as `ExcelSheetColumnNumber.java`, then run `java ExcelSheetColumnNumber.java`.

## 6. Walkthrough

Dry-run `titleToNumber("ZY")`:

| char | digitValue | result before | result after |
|---|---|---|---|
| Z | 26 | 0 | 0*26 + 26 = 26 |
| Y | 25 | 26 | 26*26 + 25 = 701 |

Final result: `701`. Each step shifts the running total up one "place" (multiply by 26) before adding the next letter's 1-indexed value — the same mechanical process as converting `"XY"` from any positional base to decimal.

## 7. Gotchas & takeaways

> Gotcha: computing `digitValue` as `c - 'A'` (giving `A=0, B=1, ..., Z=25`, the standard base-26 mapping) instead of `c - 'A' + 1` produces wrong answers for every multi-letter title — Excel's column naming has no symbol for zero, so the 1-indexed mapping is required, not the conventional 0-indexed one.

- Signal: converting a letter-based positional string to a number, where the alphabet has no "zero" symbol, is a bijective (1-indexed) base conversion, distinct from standard base conversion.
- The accumulation formula (`result = result * base + digitValue`) is identical to any base conversion — only the digit-value mapping changes.
- Related problems: Excel Sheet Column Title (the reverse conversion, number to letters, which needs a matching adjustment: subtract 1 before taking `% 26`, precisely because there is no digit zero).
