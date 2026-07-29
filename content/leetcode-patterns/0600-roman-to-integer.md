---
card: leetcode-patterns
gi: 600
slug: roman-to-integer
title: Roman to Integer
---

## 1. What it is

Given a string `s` representing a Roman numeral, convert it to an integer. Roman numerals use symbols `I=1, V=5, X=10, L=50, C=100, D=500, M=1000`, normally added left to right, except when a smaller symbol appears **before** a larger one, which means subtract the smaller value instead (`IV=4`, not `6`). Example: `s="III"` → `3`; `s="LVIII"` → `58` (`L=50, V=5, III=3`, all added); `s="MCMXCIV"` → `1994` (`M=1000`, `CM=900` (subtractive), `XC=90` (subtractive), `IV=4` (subtractive)).

## 2. Why & when

This is a direct single-pass parsing problem: the value of each symbol depends only on itself and, sometimes, the symbol immediately after it — no lookahead beyond one position is ever needed, since Roman numeral subtractive notation only ever involves exactly two adjacent symbols. Constraints: `s` is a valid Roman numeral between `1` and `3999`.

## 3. Core concept

**Key idea:** scan the string once. For each symbol, compare its value to the value of the *next* symbol (if one exists). If the current symbol's value is **less than** the next symbol's value, this is a subtractive pair — subtract the current value from the running total. Otherwise, add the current value.

**Steps:**
1. Map each Roman symbol to its integer value (`I→1, V→5, X→10, L→50, C→100, D→500, M→1000`).
2. Walk the string left to right, index `i` from `0` to `s.length()-1`.
3. At each position, look up `value = map[s.charAt(i)]`. If `i` is not the last character and `value < map[s.charAt(i+1)]`, subtract `value` from the total (this position is the smaller half of a subtractive pair). Otherwise, add `value` to the total.
4. Return the total after the full scan.

**Why comparing to the *next* character (not the previous) correctly handles subtraction:** in `"IV"`, when the scan reaches `I` (value `1`), it checks the next character, `V` (value `5`). Since `1 < 5`, this signals a subtractive pair, so `1` is subtracted. When the scan then reaches `V` itself, there is no special case — it is simply added normally. This means each subtractive pair is detected exactly once, at its *first* (smaller) symbol, with no need to look backward or to consume two characters at once.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scanning MCMXCIV left to right, comparing each symbol to the next to decide add or subtract">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="60" height="35" fill="#161b22" stroke="#3fb950"/><text x="50" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">M=1000</text>
    <rect x="90" y="30" width="60" height="35" fill="#161b22" stroke="#f0883e"/><text x="120" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">C</text>
    <rect x="150" y="30" width="60" height="35" fill="#161b22" stroke="#f0883e"/><text x="180" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">M</text>
    <text x="150" y="20" fill="#f0883e" text-anchor="middle" font-size="10">C&lt;M: subtract 100</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">"CM" = -100 + 1000 = 900, detected when scanning C (the smaller, first symbol)</text>
  </g>
</svg>

Each position only ever compares itself to its immediate successor — a subtractive pair is fully resolved at the moment the scan reaches its smaller (first) symbol.

## 5. Runnable example

**Level 1 — Brute force.** Scan for known two-character subtractive substrings (`"IV"`, `"IX"`, `"XL"`, `"XC"`, `"CD"`, `"CM"`) first, replace each with its correct numeric contribution directly, then sum the rest. Works, but requires enumerating all six subtractive pairs explicitly and careful substring replacement.

**KEY INSIGHT:** comparing each symbol only to its immediate next neighbor, in a single left-to-right pass, detects every subtractive pair automatically — no need to enumerate the six specific pairs by name, since the general rule ("smaller before larger means subtract") covers all of them uniformly.

**Level 2 — Optimal.** Single pass, one comparison per character, O(n) time, O(1) extra space (beyond the fixed symbol-value map).

**Level 3 — Hardened.** Correctly handles the last character (no next character to compare against — always add), and correctly processes multiple subtractive pairs within one numeral (like `"MCMXCIV"`, which has three).

```java
// RomanToInteger.java
import java.util.*;

public class RomanToInteger {

    public static int romanToInt(String s) {
        Map<Character, Integer> values = new HashMap<>();
        values.put('I', 1);
        values.put('V', 5);
        values.put('X', 10);
        values.put('L', 50);
        values.put('C', 100);
        values.put('D', 500);
        values.put('M', 1000);

        int total = 0;
        for (int i = 0; i < s.length(); i++) {
            int value = values.get(s.charAt(i));
            if (i + 1 < s.length() && value < values.get(s.charAt(i + 1))) {
                total -= value;
            } else {
                total += value;
            }
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(romanToInt("III"));     // 3
        System.out.println(romanToInt("LVIII"));    // 58
        System.out.println(romanToInt("MCMXCIV"));  // 1994
    }
}
```

**How to run:** save as `RomanToInteger.java`, then run `java RomanToInteger.java`.

## 6. Walkthrough

Dry-run `romanToInt("MCMXCIV")`:

| i | char | value | next char | value < next? | action | total |
|---|---|---|---|---|---|---|
| 0 | M | 1000 | C(100) | no | +1000 | 1000 |
| 1 | C | 100 | M(1000) | yes | -100 | 900 |
| 2 | M | 1000 | X(10) | no | +1000 | 1900 |
| 3 | X | 10 | C(100) | yes | -10 | 1890 |
| 4 | C | 100 | I(1) | no | +100 | 1990 |
| 5 | I | 1 | V(5) | yes | -1 | 1989 |
| 6 | V | 5 | (none) | — | +5 | 1994 |

Final total: `1994`, matching `M(1000) + CM(900, i.e. -100+1000) + XC(90, i.e. -10+100) + IV(4, i.e. -1+5)`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the bounds check `i + 1 < s.length()` before looking up `s.charAt(i+1)` throws a `StringIndexOutOfBoundsException` on the last character — the last symbol never has a "next" character to compare against, so it must always be added.

- Signal: parsing a string where each token's meaning depends only on itself and its immediate neighbor is a single-pass, lookahead-by-one signal.
- The general rule ("smaller value before a larger one means subtract") replaces memorizing all six specific subtractive pairs.
- Related problems: Integer to Roman (the reverse conversion, usually solved by greedily subtracting the largest fitting value-symbol pair, including the six subtractive combinations as explicit entries).
