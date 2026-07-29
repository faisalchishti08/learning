---
card: leetcode-patterns
gi: 615
slug: integer-to-roman
title: Integer to Roman
---

## 1. What it is

Given an integer `num` (between `1` and `3999`), convert it to a Roman numeral string. Example: `num=3` → `"III"`; `num=58` → `"LVIII"` (`L=50, V=5, III=3`); `num=1994` → `"MCMXCIV"` (`M=1000`, `CM=900`, `XC=90`, `IV=4`).

## 2. Why & when

This is the reverse of [Roman to Integer](0600-roman-to-integer.md): instead of parsing symbols into a value, it builds symbols from a value. The direct technique is **greedy**: repeatedly subtract the largest possible Roman value (from a table that includes the six subtractive combinations, like `CM=900` and `IV=4`, as if they were single symbols) and append its corresponding string, until the number reaches `0`.

## 3. Core concept

**Key idea:** define a table of value-symbol pairs, sorted from largest to smallest, that includes **both** the seven basic symbols (`M=1000, D=500, C=100, L=50, X=10, V=5, I=1`) **and** the six subtractive combinations (`CM=900, CD=400, XC=90, XL=40, IX=9, IV=4`) as if each were its own atomic unit. Walk this table from largest to smallest; for each entry, append its symbol and subtract its value from `num` as many times as it fits, before moving to the next (smaller) entry.

**Steps:**
1. Build the table as parallel arrays (or a list of pairs), ordered from largest value to smallest: `[1000,"M"], [900,"CM"], [500,"D"], [400,"CD"], [100,"C"], [90,"XC"], [50,"L"], [40,"XL"], [10,"X"], [9,"IX"], [5,"V"], [4,"IV"], [1,"I"]`.
2. For each `(value, symbol)` pair in this order: while `num >= value`, append `symbol` to the result and subtract `value` from `num`.
3. Continue to the next pair once the current one no longer fits. Stop once `num` reaches `0`.

**Why including the six subtractive combinations as their own table entries (rather than trying to detect subtractive cases separately) is the simplifying trick:** treating `"CM"` as just another symbol worth `900`, at the correct position in the sorted table, means the exact same greedy "subtract the largest fitting value" loop handles both regular and subtractive numerals uniformly — there is no special-case logic needed to decide "should this be subtractive," since the table itself already encodes every valid subtractive combination as a single unit.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Greedily subtracting the largest fitting table value for 1994: 1000, then 900, then 90, then 4">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="100" height="35" fill="#161b22" stroke="#3fb950"/><text x="70" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">1994-1000=994 "M"</text>
    <rect x="140" y="30" width="100" height="35" fill="#161b22" stroke="#f0883e"/><text x="190" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">994-900=94 "CM"</text>
    <rect x="260" y="30" width="100" height="35" fill="#161b22" stroke="#79c0ff"/><text x="310" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">94-90=4 "XC"</text>
    <rect x="380" y="30" width="100" height="35" fill="#161b22" stroke="#8b949e"/><text x="430" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">4-4=0 "IV"</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">"M"+"CM"+"XC"+"IV" = "MCMXCIV"</text>
  </g>
</svg>

Each table entry is tried in order from largest to smallest; whenever it fits, its symbol is appended and its value subtracted — subtractive combinations are handled by the exact same rule as basic symbols.

## 5. Runnable example

**Level 1 — Brute force.** Handle each of the four digit places (thousands, hundreds, tens, ones) with separate lookup tables (each mapping `0-9` to the correct Roman substring for that place). Correct, and arguably clearer for some, but requires four separate small tables instead of one unified greedy loop.

**KEY INSIGHT:** including the six subtractive combinations directly in one master table, sorted by value, lets a single greedy "take the largest fitting value" loop produce correct Roman numerals uniformly, without separately reasoning about subtractive cases.

**Level 2 — Optimal.** Greedy walk over one combined table of 13 value-symbol pairs, O(1) iterations in practice (bounded by a small constant, since `num <= 3999`), technically O(number of symbols in output).

**Level 3 — Hardened.** Correctly handles values needing multiple repeats of the same basic symbol (like `III` for `3`, three repeats of `I`), and correctly stops the outer walk once `num` reaches `0`, without needing to check every table entry explicitly.

```java
// IntegerToRoman.java
public class IntegerToRoman {

    private static final int[] VALUES = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1};
    private static final String[] SYMBOLS = {"M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"};

    public static String intToRoman(int num) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < VALUES.length && num > 0; i++) {
            while (num >= VALUES[i]) {
                result.append(SYMBOLS[i]);
                num -= VALUES[i];
            }
        }
        return result.toString();
    }

    public static void main(String[] args) {
        System.out.println(intToRoman(3));    // III
        System.out.println(intToRoman(58));   // LVIII
        System.out.println(intToRoman(1994)); // MCMXCIV
    }
}
```

**How to run:** save as `IntegerToRoman.java`, then run `java IntegerToRoman.java`.

## 6. Walkthrough

Dry-run `intToRoman(58)`:

| table entry | num before | fits? | action | num after |
|---|---|---|---|---|
| 1000 "M" | 58 | no | skip | 58 |
| 900 "CM" ... 100 "C" | 58 | no (all skipped) | skip | 58 |
| 50 "L" | 58 | yes | append "L", subtract 50 | 8 |
| 40 "XL" | 8 | no | skip | 8 |
| 10 "X" | 8 | no | skip | 8 |
| 9 "IX" | 8 | no | skip | 8 |
| 5 "V" | 8 | yes | append "V", subtract 5 | 3 |
| 4 "IV" | 3 | no | skip | 3 |
| 1 "I" | 3 | yes, 3 times | append "I","I","I", subtract 1 each | 0 |

Result: `"L" + "V" + "III" = "LVIII"`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: omitting the six subtractive combinations from the table (using only the seven basic symbols) produces invalid Roman numerals for numbers like `4` — the greedy loop would instead output `"IIII"` (four repeated `I`s), which is not standard Roman numeral notation; the subtractive entries must be present in the table at their correct sorted position.

- Signal: "build a representation greedily from the largest fitting unit downward" is the sorted-table-greedy signal, the mirror image of parsing (as in Roman to Integer).
- Including subtractive combinations as their own table entries avoids any special-case logic — the same loop handles every case uniformly.
- Related problems: Roman to Integer (the reverse conversion, parsing a Roman numeral back into an integer).
