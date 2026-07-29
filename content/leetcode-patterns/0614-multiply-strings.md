---
card: leetcode-patterns
gi: 614
slug: multiply-strings
title: Multiply Strings
---

## 1. What it is

Given two non-negative integers `num1` and `num2` represented as strings, return their product, also as a string, **without converting the inputs directly to integers**. Example: `num1="2", num2="3"` → `"6"`; `num1="123", num2="456"` → `"56088"`.

## 2. Why & when

Constraints allow both strings to be up to `200` digits long — far too large for any built-in numeric type (`long`, even `double`), so the multiplication must be done digit by digit, exactly like manual long multiplication learned in school. The key structural insight is knowing, in advance, **exactly which output position** each pair of input digits contributes to, so the whole result can be built in a single pass over all digit pairs, using an array instead of adding up partial products one row at a time.

## 3. Core concept

**Key idea:** for two numbers with `m` and `n` digits, the product has at most `m + n` digits. Multiplying the digit at position `i` in `num1` (from the right, 0-indexed) by the digit at position `j` in `num2` contributes to output positions `i + j` (the low digit of that pairwise product) and `i + j + 1` (the high digit, i.e., any carry). Accumulating every pairwise product directly into a shared result array at these positions, then resolving carries across the whole array afterward, replaces the school-method's "compute one row per digit, then add all rows" with a single combined accumulation pass.

**Steps:**
1. Create an integer array `result` of size `num1.length() + num2.length()`, initialized to `0`.
2. For each digit `num1[i]` (indices `0..len1-1`) and each digit `num2[j]` (indices `0..len2-1`): compute `product = digit1 * digit2`. Add it to whatever is already stored at `result[i+j+1]`, giving `sum`. Store `sum % 10` back at `result[i+j+1]`, and add `sum / 10` (the carry) into `result[i+j]`.
3. Because every pair's carry is folded into `result[i+j]` immediately, and that position is itself later revisited by other pairs before the loop finishes, carries correctly cascade leftward as the double loop proceeds — no separate final carry-resolution pass is needed.
4. Convert `result` to a string, skipping any leading zero (which can occur if the true product has fewer digits than the maximum possible `m+n`), and handle the special case where the entire result is zero.

**Why position `i+j+1` (using indices from the left of each string), not a more complex offset:** if `i` and `j` are measured from the *left* of each string (standard string indexing), the digit at `num1[i]` represents a place value of `10^(len1-1-i)`, and similarly for `num2[j]`. Their product's place value is `10^(len1-1-i) * 10^(len2-1-j) = 10^(len1+len2-2-i-j)`. In a result array of length `len1+len2`, indexed from the left, that place value corresponds exactly to array index `i+j+1` — a fixed, simple formula that requires no separate tracking of place values.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiplying 23 by 45: each digit pair contributes to two adjacent positions in a shared result array">
  <g font-family="sans-serif" font-size="12">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">num1="23" (i=0,1), num2="45" (j=0,1)</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">result array, length 4</text>
    <rect x="440" y="30" width="50" height="35" fill="#161b22" stroke="#30363d"/><text x="465" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">idx0</text>
    <rect x="490" y="30" width="50" height="35" fill="#161b22" stroke="#f0883e"/><text x="515" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">idx1</text>
    <rect x="540" y="30" width="50" height="35" fill="#161b22" stroke="#f0883e"/><text x="565" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">idx2</text>
    <rect x="590" y="30" width="50" height="35" fill="#161b22" stroke="#30363d"/><text x="615" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">idx3</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">digit '3' (i=1) x digit '5' (j=1): product 15 -&gt; idx (1+1+1)=3 low, idx (1+1)=2 carry-in</text>
    <text x="350" y="140" fill="#8b949e" text-anchor="middle">all pairwise products accumulate first; carries resolve in one pass afterward</text>
  </g>
</svg>

Every digit pair writes into exactly two adjacent output positions, determined purely by their string indices — no separate row-by-row addition is needed.

## 5. Runnable example

**Level 1 — Brute force.** Convert both strings to `BigInteger`, multiply, convert back to a string. Trivially correct in Java (unlike languages without arbitrary-precision types), but sidesteps the actual algorithmic exercise of implementing multiplication manually, which the problem intends.

**KEY INSIGHT:** every pairwise digit product has a fixed, predictable destination in the output array based purely on the two digits' positions — accumulating all pairwise products first, then resolving carries in one final pass, avoids the bookkeeping of adding partial-product "rows" one at a time.

**Level 2 — Optimal.** Single accumulation array of size `len1+len2`, filled by all digit pairs, then one right-to-left carry-resolution pass. O(len1 x len2) time (each digit pair is visited once), O(len1+len2) space.

**Level 3 — Hardened.** Correctly strips leading zeroes from the final result, and correctly returns `"0"` (not an empty string) when either input is `"0"`.

```java
// MultiplyStrings.java
public class MultiplyStrings {

    public static String multiply(String num1, String num2) {
        if (num1.equals("0") || num2.equals("0")) return "0";

        int len1 = num1.length(), len2 = num2.length();
        int[] result = new int[len1 + len2];

        for (int i = len1 - 1; i >= 0; i--) {
            for (int j = len2 - 1; j >= 0; j--) {
                int product = (num1.charAt(i) - '0') * (num2.charAt(j) - '0');
                int lowPos = i + j + 1;
                int highPos = i + j;
                int sum = product + result[lowPos];
                result[lowPos] = sum % 10;
                result[highPos] += sum / 10;
            }
        }

        StringBuilder sb = new StringBuilder();
        for (int digit : result) {
            if (!(sb.length() == 0 && digit == 0)) { // skip leading zeroes
                sb.append(digit);
            }
        }
        return sb.length() == 0 ? "0" : sb.toString();
    }

    public static void main(String[] args) {
        System.out.println(multiply("2", "3"));     // 6
        System.out.println(multiply("123", "456")); // 56088
    }
}
```

**How to run:** save as `MultiplyStrings.java`, then run `java MultiplyStrings.java`.

## 6. Walkthrough

Trace `multiply("23", "45")` (indices `i,j` from the left; `len1=len2=2`, result array size `4`, code processes `i=1,j=1` then `i=1,j=0` then `i=0,j=1` then `i=0,j=0`):

| pair (i,j) | digits | product | lowPos | highPos | sum=product+result[lowPos] | result array after |
|---|---|---|---|---|---|---|
| (1,1) | 3x5 | 15 | 3 | 2 | 15+0=15 | [0,0,1,5] |
| (1,0) | 3x4 | 12 | 2 | 1 | 12+1=13 | [0,1,3,5] |
| (0,1) | 2x5 | 10 | 2 | 1 | 10+3=13 | [0,2,3,5] |
| (0,0) | 2x4 | 8 | 1 | 0 | 8+2=10 | [1,0,3,5] |

Each pair writes `sum % 10` into `lowPos` and adds `sum / 10` into `highPos`, so carries resolve incrementally as each pair is processed — no separate final carry pass is needed. Final array `[1,0,3,5]` has no leading zero, giving the string `"1035"`, matching `23 x 45 = 1035`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to add into `result[highPos]` cumulatively (using `+=` rather than `=`) loses previously accumulated carry contributions from earlier digit pairs that also write to that same position — each array position can receive contributions from multiple different digit pairs across the full double loop, not just one.

- Signal: multiplying two numbers too large for any built-in numeric type is the digit-array-with-shared-accumulation signal — index arithmetic replaces row-by-row partial-product addition.
- Each digit pair `(i,j)` (indexed from the left of each string) contributes to output positions `i+j` and `i+j+1` — a fixed formula, not something recomputed per pair.
- Related problems: Add Binary (a simpler, single-loop version of digit-array arithmetic, for addition instead of multiplication), Plus One (the simplest carry-propagation case, adding a constant 1).
