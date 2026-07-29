---
card: leetcode-patterns
gi: 609
slug: self-dividing-numbers
title: Self Dividing Numbers
---

## 1. What it is

A **self-dividing number** is a positive integer that is evenly divisible by every one of its own digits, with no digit equal to `0` (since dividing by `0` is undefined). Given a range `[left, right]`, return a list of every self-dividing number in that range. Example: `left=1, right=22` → `[1,2,3,4,5,6,7,8,9,11,12,15,22]` (`10` is excluded, since it contains a `0`; `14` is excluded, since `14 % 4 != 0`).

## 2. Why & when

This combines [digit extraction](0596-math-geometry-signal-number-theory-matrix-manipulation-or-co.md) (walking a number's digits via `% 10`/`/ 10`) with a simple per-digit divisibility check, applied across a range. There is no shortcut formula here — every candidate number in the range must be individually checked digit by digit — so the problem is a direct, if slightly compound, application of the digit-walk template.

## 3. Core concept

**Key idea:** for each candidate number `n` in `[left, right]`, extract its digits one at a time. If any digit is `0`, or if `n` is not evenly divisible by that digit, `n` fails and is excluded. If every digit passes, `n` is self-dividing.

**Steps:**
1. For each `n` from `left` to `right`:
2. Check `n` using a helper: copy `n` into a temporary variable `temp` (so the original `n` is preserved for the modulus checks throughout).
3. While `temp != 0`: extract `digit = temp % 10`; if `digit == 0` or `n % digit != 0`, `n` fails — stop checking and move to the next candidate.
4. Shrink `temp /= 10` and continue until all digits are checked.
5. If every digit passed, add `n` to the result list.

**Why the check must use `n % digit`, not `temp % digit`:** `temp` is being *destroyed* by the digit-extraction loop (shrinking toward `0`), but the divisibility check needs to test against the **original**, full value of `n` against each of its own digits — using a separate variable for extraction, while checking divisibility against the untouched `n`, is what keeps this correct.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Checking 128: extracting each digit from a shrinking copy, but checking divisibility against the original unchanged n">
  <g font-family="sans-serif" font-size="12">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">n=128 (unchanged, used for %)</text>
    <text x="450" y="20" fill="#8b949e" text-anchor="middle">temp=128 (shrinks: 128-&gt;12-&gt;1)</text>
    <rect x="60" y="30" width="60" height="35" fill="#161b22" stroke="#3fb950"/><text x="90" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">128%8=0</text>
    <rect x="140" y="30" width="60" height="35" fill="#161b22" stroke="#3fb950"/><text x="170" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">128%2=0</text>
    <rect x="220" y="30" width="60" height="35" fill="#161b22" stroke="#3fb950"/><text x="250" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">128%1=0</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">all three digit checks pass -&gt; 128 is self-dividing</text>
  </g>
</svg>

`temp` is consumed to walk the digits, but every divisibility check reads from the untouched original `n` — mixing the two up would break the check after the first digit.

## 5. Runnable example

**Level 1 — Brute force.** Convert `n` to a `String` for digit extraction, then parse each character back to an integer for the divisibility check. Works, but does unnecessary string conversion for what is fundamentally an arithmetic check.

**KEY INSIGHT:** the only subtlety is keeping the original `n` intact for the modulus checks while a separate copy is consumed to walk the digits — beyond that, this is a direct nested application of the digit-extraction template inside a range loop.

**Level 2 — Optimal.** Digit extraction via `% 10`/`/ 10` on a temporary copy, checked against the original `n`, O((right-left) x digits) time overall.

**Level 3 — Hardened.** Correctly excludes any number containing the digit `0` (avoiding a division-by-zero), and correctly stops checking a candidate's remaining digits as soon as one digit fails, rather than continuing needlessly.

```java
// SelfDividingNumbers.java
import java.util.*;

public class SelfDividingNumbers {

    static boolean isSelfDividing(int n) {
        int temp = n;
        while (temp != 0) {
            int digit = temp % 10;
            if (digit == 0 || n % digit != 0) {
                return false;
            }
            temp /= 10;
        }
        return true;
    }

    public static List<Integer> selfDividingNumbers(int left, int right) {
        List<Integer> result = new ArrayList<>();
        for (int n = left; n <= right; n++) {
            if (isSelfDividing(n)) {
                result.add(n);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(selfDividingNumbers(1, 22));
        // [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 15, 22]
    }
}
```

**How to run:** save as `SelfDividingNumbers.java`, then run `java SelfDividingNumbers.java`.

## 6. Walkthrough

Dry-run `isSelfDividing(14)`:

| step | temp | digit | n % digit | result |
|---|---|---|---|---|
| 1 | 14 | 4 | 14 % 4 = 2 (not 0) | fail, return false immediately |

The loop stops at the very first digit that fails — `14` is not divisible by its own digit `4`, so it is immediately excluded, without ever checking the digit `1`.

## 7. Gotchas & takeaways

> Gotcha: checking `temp % digit` instead of `n % digit` breaks the algorithm after the first digit — since `temp` has already been divided down, checking a later digit against the shrunken `temp` instead of the full original `n` gives a wrong (and inconsistent) result.

- Signal: "check a property of every digit against the whole original number" requires keeping the original value untouched while a separate copy is consumed for digit extraction.
- Digit `0` must always be excluded up front, since checking `n % 0` would throw an `ArithmeticException`.
- Related problems: Add Digits (digit extraction feeding a sum instead of a divisibility check), Palindrome Number (digit extraction feeding a comparison instead of a divisibility check).
