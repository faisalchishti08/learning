---
card: leetcode-patterns
gi: 316
slug: numbers-with-same-consecutive-differences
title: Numbers With Same Consecutive Differences
---

## 1. What it is

Given two integers `n` and `k`, return all `n`-digit positive integers where EVERY pair of adjacent digits has an absolute difference of exactly `k`. Numbers may not have leading zeros. Return the results in any order. Example: `n = 3`, `k = 7` → `[181,292,707,818,929]`.

## 2. Why & when

This is a digit-by-digit backtracking problem: build a number one digit at a time, choosing only digits that differ from the previous one by exactly `k`. Use this shape whenever a problem builds a fixed-length sequence where each new element's valid choices depend on the PREVIOUS element already chosen.

## 3. Core concept

**Key idea:** start with each digit `1` through `9` as the first digit (no leading zero allowed). From each current last digit `d`, the only valid next digits are `d + k` and `d - k` (if they are still within `0`–`9`), because those are exactly the digits with absolute difference `k` from `d`.

**Steps:**
1. Define `backtrack(currentNumber, remainingDigits)`.
2. **Base case:** if `remainingDigits == 0`, record `currentNumber` as a result, and return.
3. **Loop:** let `lastDigit = currentNumber % 10`. For each `nextDigit` in `{lastDigit + k, lastDigit - k}` (deduplicated if `k == 0`): if `nextDigit` is outside `0`–`9`, skip (prune).
4. Choose `nextDigit` (append it: `currentNumber * 10 + nextDigit`), recurse with `remainingDigits - 1`. No explicit un-choose is needed, since each recursive call receives a NEW number value rather than mutating shared state.
5. For the very first digit, loop `1` to `9` (skip `0`, since no leading zero is allowed) and start the recursion from there.

**Why it is correct:** restricting every next digit to exactly `lastDigit + k` or `lastDigit - k` directly encodes the problem's own rule (adjacent digits differ by exactly `k`), so every fully-built number automatically satisfies the constraint at every position, with no need for a separate validity check at the end. Passing the growing number BY VALUE (not mutating a shared array) means there is nothing to undo — each recursive call is independent, which is a common simplification when the "state" being built is a single primitive value.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Building 3-digit numbers with consecutive digit difference 7, starting from digit 1, branching to 8, then to 1 (since 8+7=15 is invalid)">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n=3, k=7</text>
    <text x="10" y="45">start digit 1 -&gt; number=1</text>
    <text x="10" y="65">from 1: try 1+7=8 (valid), 1-7=-6 (invalid) -&gt; number=18</text>
    <text x="10" y="85">from 8: try 8+7=15 (invalid), 8-7=1 (valid) -&gt; number=181</text>
    <rect x="10" y="100" width="130" height="24" fill="#3fb950"/><text x="75" y="117" fill="#0d1117" text-anchor="middle" font-size="10">181 is one result</text>
  </g>
</svg>

At each step, only digits exactly `k` away from the last digit are valid next choices.

## 5. Runnable example

```java
// NumbersWithSameConsecutiveDifferences.java
import java.util.*;

public class NumbersWithSameConsecutiveDifferences {

    // KEY INSIGHT: the next digit is fully determined by "lastDigit +
    // k" or "lastDigit - k" -- no other digit could ever be valid, so
    // the branching factor is at most 2 (or 1 when k == 0).

    static int[] numsSameConsecDiff(int n, int k) {
        List<Integer> results = new ArrayList<>();
        for (int digit = 1; digit <= 9; digit++) {
            backtrack(digit, n - 1, k, results);
        }
        return results.stream().mapToInt(Integer::intValue).toArray();
    }

    static void backtrack(int currentNumber, int remainingDigits, int k, List<Integer> results) {
        if (remainingDigits == 0) {
            results.add(currentNumber);
            return;
        }
        int lastDigit = currentNumber % 10;
        Set<Integer> nextDigits = new HashSet<>();
        if (lastDigit + k <= 9) nextDigits.add(lastDigit + k);
        if (lastDigit - k >= 0) nextDigits.add(lastDigit - k);

        for (int nextDigit : nextDigits) {
            backtrack(currentNumber * 10 + nextDigit, remainingDigits - 1, k, results);
        }
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(numsSameConsecDiff(3, 7)));
        // [181, 292, 707, 818, 929] (order may vary)
        System.out.println(Arrays.toString(numsSameConsecDiff(2, 1)));
        // [10, 12, 21, 23, 32, 34, 43, 45, 54, 56, 65, 67, 76, 78, 87, 89, 98] (order may vary)
    }
}
```

**How to run:** `java NumbersWithSameConsecutiveDifferences.java`

## 6. Walkthrough

Trace `numsSameConsecDiff(3, 7)` for the starting digit `1`:

| currentNumber | remainingDigits | lastDigit | nextDigits | recurse into |
|---|---|---|---|---|
| 1 | 2 | 1 | {8} (1-7=-6 invalid) | 18 |
| 18 | 1 | 8 | {1} (8+7=15 invalid) | 181 |
| 181 | 0 | — | — | record 181 |

Starting from digit `9` similarly produces `929` (`9 → 2 → 9`, since `9-7=2` and `2+7=9`). Time complexity is O(2^n) in the worst case, since each digit branches into at most 2 choices. Space is O(n), for the recursion depth (the number itself is passed by value, not stored in shared state).

## 7. Gotchas & takeaways

> Gotcha: when `k == 0`, both candidate next digits (`lastDigit + 0` and `lastDigit - 0`) are the SAME value — using a `Set` (as shown) instead of trying both separately avoids adding the identical branch twice, which would otherwise produce duplicate results.

- Passing the growing number as a VALUE parameter (not a shared mutable array) is a simplification available whenever the "current partial solution" is small and copyable — no un-choose step is needed.
- The branching factor here is at most 2, far smaller than typical backtracking problems, which is why this runs efficiently even without extra pruning logic.
- Related problems: Letter Case Permutation (a similar fixed-branching-factor-per-position backtracking problem), Beautiful Arrangement (branching factor depends on a divisibility rule instead of a fixed offset).
