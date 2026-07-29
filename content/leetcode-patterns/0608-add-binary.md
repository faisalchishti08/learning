---
card: leetcode-patterns
gi: 608
slug: add-binary
title: Add Binary
---

## 1. What it is

Given two binary strings `a` and `b`, return their sum, also as a binary string. Example: `a="11", b="1"` → `"100"` (`3 + 1 = 4`); `a="1010", b="1011"` → `"10101"` (`10 + 11 = 21`).

## 2. Why & when

This is [Plus One](0601-plus-one.md)'s carry-propagation idea, generalized to base 2 and to two numbers of *possibly different lengths* instead of adding a constant `1` to one number. Constraints: both strings can be very long (up to `10^4` characters), too long to safely convert to a built-in numeric type like `long` — so the addition must be done directly on the strings, digit by digit, exactly as manual binary addition would be done by hand.

## 3. Core concept

**Key idea:** walk both strings from their **last** character (least significant bit) toward the first, maintaining a running `carry`. At each position, sum the corresponding bits from `a`, from `b` (using `0` if one string has run out of characters), and the current `carry`; the result's last bit becomes the next output digit, and the result's remaining value becomes the new carry.

**Steps:**
1. Initialize two pointers, `i = a.length() - 1` and `j = b.length() - 1`, and `carry = 0`.
2. While `i >= 0` or `j >= 0` or `carry != 0`: compute `sum = carry + (i >= 0 ? a.charAt(i) - '0' : 0) + (j >= 0 ? b.charAt(j) - '0' : 0)`.
3. Append `sum % 2` to the result (this position's output bit). Update `carry = sum / 2`.
4. Decrement `i` and `j` (only if still `>= 0`).
5. Since digits were appended from least to most significant, reverse the accumulated result before returning it.

**Why the loop condition includes `carry != 0`, not just "either string has characters left":** if both strings are fully consumed but a carry remains (for example, `"1" + "1"`, where after processing the single position, `sum=2`, output bit `0`, carry `1`), that carry represents one more leading `1` bit that must still be appended — stopping the loop as soon as both strings run out, without checking the carry, would drop that final bit and produce a wrong (too-short) answer.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Adding 11 and 1 in binary, right to left, with a carry propagating past the shorter string's end">
  <g font-family="sans-serif" font-size="12">
    <text x="100" y="20" fill="#8b949e" text-anchor="middle">a = 1 1</text>
    <text x="100" y="40" fill="#8b949e" text-anchor="middle">b = &nbsp;&nbsp;1</text>
    <rect x="60" y="50" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="80" y="70" fill="#e6edf3" text-anchor="middle" font-size="10">1+1=10</text>
    <text x="80" y="95" fill="#f0883e" text-anchor="middle" font-size="10">bit=0, carry=1</text>
    <rect x="130" y="50" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="150" y="70" fill="#e6edf3" text-anchor="middle" font-size="10">1+0+1</text>
    <text x="150" y="95" fill="#f0883e" text-anchor="middle" font-size="10">bit=0, carry=1</text>
    <rect x="200" y="50" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="220" y="70" fill="#e6edf3" text-anchor="middle" font-size="10">0+0+1</text>
    <text x="220" y="95" fill="#f0883e" text-anchor="middle" font-size="10">bit=1, carry=0</text>
    <text x="350" y="130" fill="#79c0ff" text-anchor="middle">result built right to left, then reversed: "100"</text>
  </g>
</svg>

The carry outlives both strings' characters at the third step, contributing one final leading bit — the loop's `carry != 0` condition is what catches this case.

## 5. Runnable example

**Level 1 — Brute force.** Convert both binary strings to `long` using `Long.parseLong(s, 2)`, add them, then convert the sum back to a binary string with `Long.toBinaryString`. Works for the given constraints (`10^4`-character strings *can* overflow even a `long` or `BigInteger` conversion cost, but for typical test sizes this is simpler) — the "hardened" solution below avoids any numeric type entirely, which is necessary once string lengths grow large enough to overflow any fixed-size integer type.

**KEY INSIGHT:** binary addition is bit-by-bit carry propagation, identical in structure to decimal addition by hand — processing both strings from the end, tracking a carry, and appending one output bit per step handles strings of any length without ever forming a numeric value.

**Level 2 — Optimal.** Two pointers from the end of each string, carry tracked across the loop, O(max(len(a), len(b))) time, same for space (the output).

**Level 3 — Hardened.** Correctly continues the loop as long as a carry remains, even after both strings are exhausted, and correctly handles strings of very different lengths using the `i >= 0 ? ... : 0` guard.

```java
// AddBinary.java
public class AddBinary {

    public static String addBinary(String a, String b) {
        StringBuilder result = new StringBuilder();
        int i = a.length() - 1, j = b.length() - 1, carry = 0;

        while (i >= 0 || j >= 0 || carry != 0) {
            int sum = carry;
            if (i >= 0) sum += a.charAt(i--) - '0';
            if (j >= 0) sum += b.charAt(j--) - '0';
            result.append(sum % 2);
            carry = sum / 2;
        }

        return result.reverse().toString();
    }

    public static void main(String[] args) {
        System.out.println(addBinary("11", "1"));     // 100
        System.out.println(addBinary("1010", "1011")); // 10101
    }
}
```

**How to run:** save as `AddBinary.java`, then run `java AddBinary.java`.

## 6. Walkthrough

Dry-run `addBinary("11", "1")`:

| step | i | j | sum | bit appended | carry |
|---|---|---|---|---|---|
| 1 | 1 | 0 | 1+1+0=2 | 0 | 1 |
| 2 | 0 | -1 | 1+0+1=2 | 0 | 1 |
| 3 | -1 | -1 | 1+0+0=1 | 1 | 0 |

Loop stops (`i<0, j<0, carry=0`). Appended bits, in order: `0,0,1` → reversed → `"100"`, matching `3 + 1 = 4`.

## 7. Gotchas & takeaways

> Gotcha: ending the loop condition at `i >= 0 || j >= 0` (dropping `|| carry != 0`) silently discards a final carry bit whenever the addition's result needs one more bit than either input string had — for example, `"1" + "1"` would incorrectly return `"0"` instead of `"10"`.

- Signal: adding two numbers represented as strings/digit-arrays, potentially too large for a built-in numeric type, is the two-pointer-plus-carry signal — works for any base.
- The loop must continue as long as *either* string has remaining characters *or* a carry remains, not just while both strings have characters.
- Related problems: Plus One (the same carry idea, decimal base, adding a fixed `1` instead of a second full number), Multiply Strings (a related string-arithmetic problem, for multiplication instead of addition).
