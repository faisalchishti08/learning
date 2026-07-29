---
card: leetcode-patterns
gi: 606
slug: reverse-integer
title: Reverse Integer
---

## 1. What it is

Given a signed 32-bit integer `x`, return `x` with its digits reversed. If reversing causes the result to fall outside the signed 32-bit integer range (`[-2147483648, 2147483647]`), return `0`. Example: `x=123` → `321`; `x=-123` → `-321`; `x=120` → `21` (the trailing zero disappears, since a reversed number has no meaningful leading zero); `x=1534236469` → `0` (the true reversal, `9646324351`, overflows a 32-bit int).

## 2. Why & when

This extends the [Palindrome Number](0599-palindrome-number.md) digit-extraction template to build a *fully* reversed number instead of stopping halfway, adding one new requirement: detecting overflow **before** it happens, since Java's `int` silently wraps around on overflow rather than throwing an error, which would otherwise produce a wrong (but not obviously wrong) answer.

## 3. Core concept

**Key idea:** extract digits from `x` one at a time using `% 10` and `/ 10` (this naturally handles negative `x` correctly in Java, since `%` preserves the sign of the dividend). Build the reversed number by repeatedly doing `result = result * 10 + digit`. Before each multiplication, check whether it **would** overflow, and return `0` immediately if so — checking after the fact is too late, since the overflow has already silently corrupted the value.

**Steps:**
1. Initialize `result = 0`.
2. While `x != 0`: extract `digit = x % 10`; shrink `x /= 10`.
3. **Before** updating `result`, check for overflow: if `result > Integer.MAX_VALUE / 10`, or (`result == Integer.MAX_VALUE / 10` and `digit > 7`), the next multiplication would overflow past `Integer.MAX_VALUE` — return `0`. A symmetric check applies for the negative boundary (`Integer.MIN_VALUE`).
4. Otherwise, update `result = result * 10 + digit`.
5. After the loop, return `result`.

**Why checking `result > MAX/10` before multiplying, instead of checking `result*10+digit > MAX` after, is necessary:** in Java, `int` arithmetic that overflows wraps around silently (it does not throw), so computing `result * 10 + digit` when it *would* exceed `Integer.MAX_VALUE` produces a garbage wrapped-around value — checking the condition *before* performing the multiplication avoids ever computing that invalid value in the first place.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Building up a reversed number digit by digit, with an overflow check performed before each multiplication">
  <g font-family="sans-serif" font-size="12">
    <rect x="40" y="30" width="120" height="35" fill="#161b22" stroke="#3fb950"/><text x="100" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">result=32</text>
    <rect x="220" y="30" width="180" height="35" fill="#161b22" stroke="#f0883e"/><text x="310" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">check: 32 &gt; MAX/10? no</text>
    <rect x="460" y="30" width="120" height="35" fill="#161b22" stroke="#3fb950"/><text x="520" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">result=321</text>
    <line x1="160" y1="47" x2="220" y2="47" stroke="#8b949e" marker-end="url(#a14)"/>
    <line x1="400" y1="47" x2="460" y2="47" stroke="#8b949e" marker-end="url(#a14)"/>
    <defs><marker id="a14" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">the check happens before multiplying, so an overflowing value is never actually computed</text>
  </g>
</svg>

Each digit is appended only after confirming the multiplication would not overflow — the check always precedes the update, never follows it.

## 5. Runnable example

**Level 1 — Brute force.** Convert `x` to a `String`, reverse it, then parse it back with `Long.parseLong` and check if the result exceeds `int` bounds. Works, and using `long` avoids the overflow-detection subtlety, but relies on string conversion, which the "no string conversion" spirit of this section's problems typically discourages.

**KEY INSIGHT:** checking for overflow *before* performing the multiplication that would cause it — by comparing against `Integer.MAX_VALUE / 10` (and the boundary digit `7`, since `Integer.MAX_VALUE` ends in `7`) — avoids ever computing an invalid wrapped-around value.

**Level 2 — Optimal.** Digit-by-digit accumulation via `% 10`/`/ 10`, with a pre-multiplication overflow check, O(digits) time, O(1) space.

**Level 3 — Hardened.** Handles both the positive overflow boundary (`Integer.MAX_VALUE = 2147483647`) and the negative boundary (`Integer.MIN_VALUE = -2147483648`) correctly, and confirms trailing zeros in the input (like `120`) naturally disappear in the output with no special-casing.

```java
// ReverseInteger.java
public class ReverseInteger {

    public static int reverse(int x) {
        int result = 0;
        while (x != 0) {
            int digit = x % 10;
            x /= 10;

            if (result > Integer.MAX_VALUE / 10 ||
                (result == Integer.MAX_VALUE / 10 && digit > 7)) {
                return 0; // would overflow past Integer.MAX_VALUE
            }
            if (result < Integer.MIN_VALUE / 10 ||
                (result == Integer.MIN_VALUE / 10 && digit < -8)) {
                return 0; // would overflow past Integer.MIN_VALUE
            }
            result = result * 10 + digit;
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(reverse(123));        // 321
        System.out.println(reverse(-123));       // -321
        System.out.println(reverse(120));        // 21
        System.out.println(reverse(1534236469)); // 0, would overflow
    }
}
```

**How to run:** save as `ReverseInteger.java`, then run `java ReverseInteger.java`.

## 6. Walkthrough

Dry-run `reverse(120)`:

| step | x | digit | result before | overflow check | result after |
|---|---|---|---|---|---|
| 1 | 120 -> 12 | 0 | 0 | no | 0*10+0 = 0 |
| 2 | 12 -> 1 | 2 | 0 | no | 0*10+2 = 2 |
| 3 | 1 -> 0 | 1 | 2 | no | 2*10+1 = 21 |

Loop ends (`x == 0`). Result: `21`. The leading `0` digit extracted in step 1 contributes nothing to the final result (since `result` was still `0` at that point), which is exactly why a trailing zero in the input silently vanishes from the reversed output.

## 7. Gotchas & takeaways

> Gotcha: checking for overflow *after* computing `result * 10 + digit` (instead of before) is too late in Java — the overflowing arithmetic itself wraps around silently to a valid-looking but wrong `int`, so the check must compare `result` against `Integer.MAX_VALUE / 10` (and the boundary digit) *before* the multiplication ever happens.

- Signal: "reverse the digits of a number, watch for overflow" is the digit-extraction-plus-pre-check-accumulation signal.
- `%` in Java preserves the sign of the dividend, so negative `x` extracts negative digits directly, without needing to special-case the sign separately.
- Related problems: Palindrome Number (the same digit-extraction idea, stopping at the midpoint instead of reversing fully), String to Integer (atoi) (a related overflow-detection problem, but on parsed string input instead of a given int).
