---
card: leetcode-patterns
gi: 353
slug: fibonacci-number
title: Fibonacci Number
---

## 1. What it is

The Fibonacci numbers form a sequence where `F(0) = 0`, `F(1) = 1`, and each later term is the sum of the two before it: `F(n) = F(n-1) + F(n-2)`. Given `n`, return `F(n)`. Example: `n = 4` → `3` (sequence: `0,1,1,2,3`).

## 2. Why & when

This problem IS the pattern in its purest form — no story to translate, just the recurrence directly. Use it as the reference point for recognizing "look back 1 or 2 positions" recurrences buried inside other problems' wording (stairs, robbers, decoding).

## 3. Core concept

**Key idea:** build `dp[i]` = `F(i)`, for every `i` from `0` to `n`, using the two immediately preceding values.

**Steps:**
1. Base cases: `dp[0] = 0`, `dp[1] = 1`.
2. For `i` from `2` to `n`: `dp[i] = dp[i-1] + dp[i-2]`.
3. Return `dp[n]`.

**Why it is correct:** this is a direct implementation of the mathematical definition — no derivation needed, since the recurrence IS the definition of the sequence.

## 4. Diagram

<svg viewBox="0 0 480 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sequence of fibonacci numbers 0 1 1 2 3 5 each built from the two before it">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">F: 0, 1, 1, 2, 3, 5, ...</text>
    <text x="10" y="45">F(4) = F(3) + F(2) = 2 + 1 = 3</text>
    <rect x="10" y="65" width="200" height="24" fill="#3fb950"/><text x="110" y="82" fill="#0d1117" text-anchor="middle" font-size="10">F(4) = 3</text>
  </g>
</svg>

Each term sums the two directly before it, starting from the fixed base pair `0, 1`.

## 5. Runnable example

```java
// FibonacciNumber.java
public class FibonacciNumber {

    // KEY INSIGHT: the recurrence F(n) = F(n-1) + F(n-2) is the
    // definition itself -- no derivation, just direct rolling-variable
    // computation.

    static int fib(int n) {
        if (n < 2) return n;
        int prev2 = 0, prev1 = 1;
        for (int i = 2; i <= n; i++) {
            int curr = prev1 + prev2;
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(fib(4));
        // 3
        System.out.println(fib(10));
        // 55
    }
}
```

**How to run:** `java FibonacciNumber.java`

## 6. Walkthrough

Trace `fib(4)`:

| i | prev2 | prev1 | curr |
|---|---|---|---|
| start | 0 | 1 | - |
| 2 | 1 | 1 | 1 |
| 3 | 1 | 2 | 2 |
| 4 | 2 | 3 | 3 |

Final `prev1 = 3`, matching `F(4) = 3`. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: `n = 0` and `n = 1` are valid inputs whose answers ARE `n` itself (`F(0)=0`, `F(1)=1`) — returning early for `n < 2` before entering the loop avoids an off-by-one error in the loop bounds.

- `dp[i] = dp[i-1] + dp[i-2]` with base cases `dp[0]=0, dp[1]=1`: the canonical Fibonacci/Linear template.
- For very large `n`, matrix exponentiation computes `F(n)` in O(log n) time, but the linear O(n) approach is simpler and sufficient for typical constraints (`n <= 30` on LeetCode).
- Related problems: Climbing Stairs (the exact same recurrence, arrived at from a different story), N-th Tribonacci Number (the three-term generalization of this same idea).
