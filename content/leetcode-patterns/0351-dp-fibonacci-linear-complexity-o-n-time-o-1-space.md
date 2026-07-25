---
card: leetcode-patterns
gi: 351
slug: dp-fibonacci-linear-complexity-o-n-time-o-1-space
title: "DP: Fibonacci / Linear — complexity: O(n) time, O(1) space"
---

## 1. What it is

This page states and justifies the complexity of the Fibonacci/Linear DP pattern, and lists the problems that use it, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. If `n` can be up to `10^5` or higher, an O(n) solution with O(1) space runs comfortably fast with almost no memory overhead. A naive recursive solution without memoization is exponential and will time out on the same input.

## 3. Core concept

**Time complexity: O(n).** The DP makes exactly one pass over the input, computing one new value per position from a small, fixed number of earlier values. That is O(1) work per position, times `n` positions, giving O(n).

**Space complexity: O(1)**, when rolling variables replace the array (O(n) if the full array is kept, e.g. for reconstruction or debugging). Since each `dp[i]` only ever needs the last one or two values, nothing further back needs to stay in memory.

**Why it is NOT exponential like naive recursion:** naive recursive Fibonacci re-solves the same sub-problem many times — `fib(5)` calls `fib(4)` and `fib(3)`, but `fib(4)` ALSO calls `fib(3)`, so `fib(3)` gets computed twice, `fib(2)` even more times, and so on, doubling roughly at each level (O(2^n)). The DP computes each `dp[i]` exactly once, in order, and reuses it directly — no repeated work.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="comparison of naive recursion tree branching exponentially versus a single linear pass computing each value once">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">naive recursion: fib(5) re-solves fib(3) twice, fib(2) three times</text>
    <text x="10" y="45">-&gt; O(2^n) calls, exponential blowup</text>
    <text x="10" y="75" font-weight="bold">linear DP: one pass, each dp[i] computed exactly once</text>
    <rect x="10" y="90" width="260" height="24" fill="#3fb950"/><text x="140" y="107" fill="#0d1117" text-anchor="middle" font-size="10">total time = O(n), space = O(1)</text>
  </g>
</svg>

Reusing each computed value once, instead of re-deriving it from scratch, is what collapses exponential recursion into a single linear pass.

## 5. Runnable example

```java
// FibonacciLinearComplexity.java
public class FibonacciLinearComplexity {

    // Confirms O(n): counts loop iterations done.
    static int climbStairsWithCounter(int n, long[] ops) {
        if (n <= 2) return n;
        int prev2 = 1, prev1 = 2;
        for (int i = 3; i <= n; i++) {
            int curr = prev1 + prev2;
            prev2 = prev1;
            prev1 = curr;
            ops[0]++;
        }
        return prev1;
    }

    public static void main(String[] args) {
        int n = 20;
        long[] ops = {0};
        int ways = climbStairsWithCounter(n, ops);
        System.out.println("ways=" + ways + " ops=" + ops[0]);
        // ways is bounded by exactly n-2 iterations for n > 2
    }
}
```

**How to run:** `java FibonacciLinearComplexity.java`

## 6. Walkthrough

1. `climbStairsWithCounter` runs the standard rolling-variable template while counting every loop iteration in `ops`.
2. For `n=20`, the printed `ops` count is exactly `n - 2 = 18`, confirming the loop runs linearly in `n`, with no hidden nested loop or repeated recomputation.
3. Each iteration does constant work (one addition, two assignments), so total work scales linearly with `n`.
4. Compare this to a naive recursive solution with no memoization: it would re-explore the same smaller sub-problems from many different call paths, multiplying work exponentially instead of linearly.
5. This confirms the pattern is efficient enough for any typical constraint on `n` (even up to `10^7` or more), which is the check you should run before committing to this approach on a new problem.

## 7. Gotchas & takeaways

> Gotcha: memoizing a naive recursive solution (top-down, with a cache) also achieves O(n) time, but still uses O(n) space for the recursion stack and the cache — the iterative rolling-variable version is strictly better when only the final answer is needed, since it avoids both.

- Time: O(n); space: O(1) with rolling variables, O(n) if the full array is kept (needed only for reconstruction, like decoding the actual sequence of moves).
- This is the cheapest DP shape you will encounter — always check first whether a problem's dependencies are this narrow before reaching for a heavier 2D table.
- Problems that use this pattern: Climbing Stairs, Fibonacci Number, N-th Tribonacci Number, Min Cost Climbing Stairs, Get Maximum in Generated Array, House Robber, House Robber II, Delete and Earn, Decode Ways.
