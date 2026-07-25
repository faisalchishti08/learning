---
card: leetcode-patterns
gi: 354
slug: n-th-tribonacci-number
title: N-th Tribonacci Number
---

## 1. What it is

The Tribonacci sequence extends Fibonacci to THREE terms: `T(0) = 0`, `T(1) = 1`, `T(2) = 1`, and each later term sums the THREE before it: `T(n) = T(n-1) + T(n-2) + T(n-3)`. Given `n`, return `T(n)`. Example: `n = 4` → `4` (sequence: `0,1,1,2,4`).

## 2. Why & when

This is the direct generalization of the Fibonacci/Linear pattern from a 2-term look-back to a 3-term look-back. Use this shape whenever a recurrence explicitly sums three (or more) preceding terms — the SAME rolling-variable technique applies, just with one more variable to track.

## 3. Core concept

**Key idea:** build `dp[i]` = `T(i)`, for every `i` from `0` to `n`, using the three immediately preceding values.

**Steps:**
1. Base cases: `dp[0] = 0`, `dp[1] = 1`, `dp[2] = 1`.
2. For `i` from `3` to `n`: `dp[i] = dp[i-1] + dp[i-2] + dp[i-3]`.
3. Return `dp[n]`.

**Why it is correct:** this directly implements the given mathematical definition, extended from Fibonacci's two-term sum to a three-term sum — each term simply needs one more piece of history than before.

## 4. Diagram

<svg viewBox="0 0 480 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="tribonacci sequence 0 1 1 2 4 7 each built from the three before it">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">T: 0, 1, 1, 2, 4, 7, ...</text>
    <text x="10" y="45">T(4) = T(3) + T(2) + T(1) = 2 + 1 + 1 = 4</text>
    <rect x="10" y="65" width="220" height="24" fill="#3fb950"/><text x="120" y="82" fill="#0d1117" text-anchor="middle" font-size="10">T(4) = 4</text>
  </g>
</svg>

Each term sums the three directly before it, one more term of history than plain Fibonacci.

## 5. Runnable example

```java
// NthTribonacciNumber.java
public class NthTribonacciNumber {

    // KEY INSIGHT: same rolling-variable technique as Fibonacci, with
    // one extra variable to hold the third preceding term.

    static int tribonacci(int n) {
        if (n == 0) return 0;
        if (n <= 2) return 1;
        int prev3 = 0, prev2 = 1, prev1 = 1;
        for (int i = 3; i <= n; i++) {
            int curr = prev1 + prev2 + prev3;
            prev3 = prev2;
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(tribonacci(4));
        // 4
        System.out.println(tribonacci(25));
        // 1389537
    }
}
```

**How to run:** `java NthTribonacciNumber.java`

## 6. Walkthrough

Trace `tribonacci(4)`:

| i | prev3 | prev2 | prev1 | curr |
|---|---|---|---|---|
| start | 0 | 1 | 1 | - |
| 3 | 1 | 1 | 2 | 2 |
| 4 | 1 | 2 | 4 | 4 |

Final `prev1 = 4`, matching `T(4) = 4`. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: shifting the THREE rolling variables in the wrong order (or forgetting to shift `prev3`) silently corrupts the sequence after just one or two iterations — always compute `curr` first from the OLD values, then shift `prev3 <- prev2 <- prev1 <- curr`, in that exact order.

- `dp[i] = dp[i-1] + dp[i-2] + dp[i-3]` with three base cases: the three-term generalization of the Fibonacci/Linear template.
- The technique scales to ANY fixed look-back width `k` — just keep `k` rolling variables and shift them all each iteration.
- Related problems: Fibonacci Number (the two-term version of this exact idea), Climbing Stairs (a two-term recurrence with a step-counting story instead of a direct math definition).
