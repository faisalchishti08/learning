---
card: leetcode-patterns
gi: 350
slug: dp-fibonacci-linear-template-dp-i-from-dp-i-1-dp-i-2-rolling
title: "DP: Fibonacci / Linear — template: dp[i] from dp[i-1], dp[i-2] (rolling variables)"
---

## 1. What it is

This page gives the reusable template for Fibonacci/Linear DP problems: an array-based version for learning and debugging, and the SPACE-OPTIMIZED rolling-variable version you should default to once the pattern is clear.

## 2. Why & when

Use the array version when you are first working out the recurrence, or when you need to look back at every intermediate value (for debugging or reconstruction). Use the rolling-variable version once the recurrence is confirmed, since it cuts memory from O(n) to O(1) with no loss of correctness.

## 3. Core concept

**Template A — array.**
1. Create `dp[n+1]`. Set the base cases explicitly (e.g. `dp[0]` and `dp[1]`).
2. For `i` from `2` (or `3`, depending on how many base cases exist) to `n`: `dp[i] = combine(dp[i-1], dp[i-2])`.
3. The answer is `dp[n]`.

**Template B — rolling variables.**
1. Set `prev2` and `prev1` to the base-case values.
2. For `i` from the first non-base index to `n`: compute `curr = combine(prev1, prev2)`, then shift: `prev2 = prev1; prev1 = curr`.
3. The answer is `prev1` after the loop ends.

**Why the rolling version is correct:** at every step, the recurrence only ever reads the immediately preceding one or two values. Once `dp[i]` is computed, `dp[i-2]` is never read again by any FUTURE step — so instead of keeping the whole array, two variables that "slide forward" one position at a time hold everything the computation still needs.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="rolling variables sliding forward through a sequence, each step discarding the oldest value">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">step i: prev2=dp[i-2], prev1=dp[i-1]</text>
    <text x="10" y="45">curr = prev1 + prev2</text>
    <text x="10" y="65">shift: prev2 &lt;- prev1, prev1 &lt;- curr</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">window slides forward by one each iteration</text>
  </g>
</svg>

Two variables replace an entire array, since only the last two positions are ever needed.

## 5. Runnable example

```java
// FibonacciLinearTemplate.java
public class FibonacciLinearTemplate {

    // Template A: array version.
    static int fibArray(int n) {
        if (n <= 1) return n;
        int[] dp = new int[n + 1];
        dp[0] = 0;
        dp[1] = 1;
        for (int i = 2; i <= n; i++) {
            dp[i] = dp[i - 1] + dp[i - 2];
        }
        return dp[n];
    }

    // Template B: rolling-variable version -- O(1) space.
    static int fibRolling(int n) {
        if (n <= 1) return n;
        int prev2 = 0, prev1 = 1;
        for (int i = 2; i <= n; i++) {
            int curr = prev1 + prev2;
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(fibArray(10));
        // 55
        System.out.println(fibRolling(10));
        // 55
    }
}
```

**How to run:** `java FibonacciLinearTemplate.java`

## 6. Walkthrough

1. `fibArray` fills an array of size `11`, each cell built from the two cells before it, keeping every intermediate value.
2. `fibRolling` computes the SAME sequence of values using only two integer variables, overwritten each iteration.
3. Both return `55` for `n=10`, confirming the space-optimized version computes the identical answer.
4. Tracing `fibRolling`: start `prev2=0, prev1=1`; after `i=2`, `curr=1, prev2=1, prev1=1`; after `i=3`, `curr=2, prev2=1, prev1=2`; this continues until `prev1=55` at `i=10`.
5. This template applies directly to Climbing Stairs, Fibonacci Number, House Robber, and Decode Ways — only the `combine` step (`+`, `max`, or a conditional sum) and the number of base cases change per problem.

## 7. Gotchas & takeaways

> Gotcha: forgetting to shift BOTH variables (`prev2 = prev1` before overwriting `prev1`) or shifting them in the WRONG ORDER silently corrupts the sequence — always compute `curr` first, using the OLD `prev1` and `prev2`, before overwriting either one.

- Array version: easier to debug and to see every intermediate value; O(n) space.
- Rolling version: same answer, O(1) space; requires careful ordering when updating the rolling variables.
- If the recurrence needs THREE previous states (Tribonacci), extend to three rolling variables (`prev3, prev2, prev1`) with the same shifting discipline.
