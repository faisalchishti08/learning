---
card: leetcode-patterns
gi: 599
slug: palindrome-number
title: Palindrome Number
---

## 1. What it is

Given an integer `x`, return `true` if `x` reads the same forwards and backwards (a palindrome), and `false` otherwise, **without converting `x` to a string**. Example: `x=121` → `true`; `x=-121` → `false` (a negative sign at the front cannot mirror at the end: reading it backward would give `121-`, not a valid comparison); `x=10` → `false` (reads `01` backward, and leading zeros are not meaningful).

## 2. Why & when

This is the canonical [Math & Geometry — digit-by-digit arithmetic](0596-math-geometry-signal-number-theory-matrix-manipulation-or-co.md) problem: the "without converting to a string" constraint directly signals that digit extraction via `% 10` and `/ 10` is expected. Constraints: `x` fits in a 32-bit signed integer.

## 3. Core concept

**Key idea:** reverse only the **second half** of the number's digits, and compare it against the remaining first half — once the reversed half is at least as large as what remains, the midpoint has been reached, and no string or full reversal is ever needed.

**Steps:**
1. Handle edge cases immediately: any negative number is not a palindrome (the sign only appears at the front). Any positive number ending in `0` (except `0` itself) is not a palindrome, since a valid palindrome cannot have a leading zero, and its last digit would have to equal its first digit.
2. Build `reversedHalf` by repeatedly taking `x`'s last digit (`x % 10`) and appending it (`reversedHalf = reversedHalf * 10 + digit`), while shrinking `x` (`x /= 10`), **until `x <= reversedHalf`**.
3. At that point, `x` holds the (possibly empty) first half, and `reversedHalf` holds the reversed second half. For an even total digit count, they should be exactly equal. For an odd total digit count, `reversedHalf` has one extra middle digit, so compare `x` to `reversedHalf / 10` (dropping that middle digit) instead.

**Why stopping at the midpoint, not reversing the whole number, is the key improvement:** reversing the entire number risks 32-bit integer overflow for numbers near `Integer.MAX_VALUE`, and does twice the necessary work. Stopping once `x <= reversedHalf` guarantees `reversedHalf` never needs to hold more digits than roughly half of the original number.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversing only the second half of 1221's digits while shrinking the first half, until they meet in the middle">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">x shrinking (first half)</text>
    <rect x="60" y="30" width="180" height="35" fill="#161b22" stroke="#3fb950"/><text x="150" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">x=12 -&gt; x=1</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">reversedHalf growing</text>
    <rect x="440" y="30" width="180" height="35" fill="#161b22" stroke="#f0883e"/><text x="530" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">reversedHalf=2 -&gt; 21</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">stop when x &lt;= reversedHalf: x=1, reversedHalf=21? no - stop at x=12,rev=2 then x=1,rev=21</text>
    <text x="350" y="135" fill="#8b949e" text-anchor="middle" font-size="11">x(1) == reversedHalf/10 (21/10=2)? adjust for odd-length case</text>
  </g>
</svg>

Only about half the digits are ever reversed — the loop stops the moment the shrinking first half meets or passes the growing reversed second half.

## 5. Runnable example

**Level 1 — Brute force.** Convert `x` to a `String`, then compare it to its own reverse. Simple, but violates the "without converting to a string" constraint and uses O(digits) extra space for the string.

**KEY INSIGHT:** a palindrome's second half is the mirror of its first half — reversing only the second half arithmetically, and comparing it to the shrinking first half, confirms the palindrome property without ever materializing a string or fully reversing the number.

**Level 2 — Optimal.** Half-reversal via `% 10`/`/ 10`, stopping at the midpoint, O(digits) time, O(1) space.

**Level 3 — Hardened.** Correctly rejects negative numbers and positive multiples of 10 (other than 0) up front, and correctly handles the odd-digit-count case by dropping `reversedHalf`'s extra middle digit before comparing.

```java
// PalindromeNumber.java
public class PalindromeNumber {

    public static boolean isPalindrome(int x) {
        if (x < 0 || (x % 10 == 0 && x != 0)) return false;

        int reversedHalf = 0;
        while (x > reversedHalf) {
            reversedHalf = reversedHalf * 10 + x % 10;
            x /= 10;
        }

        return x == reversedHalf || x == reversedHalf / 10;
    }

    public static void main(String[] args) {
        System.out.println(isPalindrome(121));  // true
        System.out.println(isPalindrome(-121)); // false
        System.out.println(isPalindrome(10));   // false
        System.out.println(isPalindrome(12321)); // true, odd digit count
    }
}
```

**How to run:** save as `PalindromeNumber.java`, then run `java PalindromeNumber.java`.

## 6. Walkthrough

Dry-run `isPalindrome(1221)`:

| step | x | reversedHalf | x > reversedHalf? |
|---|---|---|---|
| start | 1221 | 0 | yes |
| iter 1 | 122 | 1 | yes |
| iter 2 | 12 | 12 | no, stop |

Loop stops with `x=12`, `reversedHalf=12`. `x == reversedHalf` (`12 == 12`) is `true`, so `1221` is a palindrome.

For the odd-length case `12321`, the loop runs three iterations: `x=1232,rev=1` → `x=123,rev=12` → `x=12,rev=123`, stopping once `x(12) <= reversedHalf(123)`. Here `x != reversedHalf` (`12 != 123`), so the odd-length check applies: `x == reversedHalf / 10` (`12 == 123/10 = 12`) is `true` — the extra middle digit (`3`) in `reversedHalf` is dropped before comparing.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `x % 10 == 0 && x != 0` check lets a number like `10` slip through the main loop and incorrectly report `true` or crash — a positive number ending in zero (other than zero itself) can never be a palindrome, since its first digit cannot be zero.

- Signal: "without converting to a string" is the direct digit-by-digit arithmetic signal (mod/div extraction).
- Reversing only half the digits, not the whole number, avoids potential overflow and halves the work.
- Related problems: Reverse Integer (the full-reversal version of this same digit-extraction technique, with explicit overflow handling).
