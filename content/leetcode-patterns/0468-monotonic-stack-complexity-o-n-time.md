---
card: leetcode-patterns
gi: 468
slug: monotonic-stack-complexity-o-n-time
title: Monotonic Stack — complexity: O(n) time
---

## 1. What it is

This page explains why a monotonic stack runs in O(n) time despite the `while` loop nested inside the `for` loop looking like it could be O(n²), and lists the named problems that use the pattern.

## 2. Why & when

Interviewers will ask you to justify the time complexity, not just state it. "It's O(n) because we use a stack" is not enough — the code visibly has a loop inside a loop, and you need to explain why that does not multiply out to O(n²). This distinction matters most when comparing against the brute-force alternative, which really is O(n²).

## 3. Core concept

**Time — O(n), by amortized analysis.** Each element in the array is pushed onto the stack exactly once, during its own iteration of the `for` loop. Each element can also be popped at most once, ever, because once it is popped it is gone and cannot come back. So across the *entire* run, the total number of pushes is exactly n, and the total number of pops is at most n. The `while` loop's iterations, summed over the whole algorithm, are bounded by the total pop count — at most n. Adding the `for` loop's n iterations and the `while` loop's at most n total pop iterations gives at most 2n operations overall, which is O(n).

This is called an **amortized** analysis: any single iteration of the `for` loop might trigger many pops (in the worst case, one iteration pops the entire stack), but that cost is "paid for" by all the earlier pushes that put those elements on the stack in the first place. The expensive iteration is rare and is balanced out by the many cheap iterations (just one push, no pops) elsewhere in the run.

**Space — O(n).** The stack can hold up to n elements in the worst case, such as when the input is already sorted in the stack's monotonic direction (nothing gets popped until the very end, or never at all).

**Contrast with the brute-force alternative.** The naive "next greater element" solution scans forward from every index until it finds a bigger value, an O(n) scan repeated n times, giving O(n²). The monotonic stack replaces every one of those repeated forward scans with O(1) amortized work per element.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Amortized cost of pushes and pops across a monotonic stack run">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Each element: pushed once, popped at most once</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="180" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">push</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">push</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">push</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">push</text>
    <text x="200" y="60" fill="#e6edf3" text-anchor="middle" font-size="11">push</text>
    <text x="20" y="100" fill="#8b949e">total pushes across whole run = n</text>
    <text x="20" y="120" fill="#8b949e">total pops across whole run &lt;= n (each element popped at most once)</text>
    <text x="20" y="150" fill="#3fb950">total work = pushes + pops &lt;= 2n = O(n)</text>
    <text x="20" y="180" fill="#f0883e">one iteration CAN pop many elements at once -- but that cost was pre-paid by their earlier, individual pushes</text>
  </g>
</svg>

The amortized argument: expensive iterations (many pops) are balanced out across the run by cheap ones (only a push), because every pop consumes a push that happened earlier.

## 5. Runnable example

An instrumented "next greater element" run that counts total pushes and pops, so you can confirm the `2n` bound holds on real input, including the worst case where every element pops the entire stack at once.

```java
// MonotonicStackComplexity.java
import java.util.*;

public class MonotonicStackComplexity {

    static int runAndCountOperations(int[] arr) {
        Deque<Integer> stack = new ArrayDeque<>();
        int operations = 0;
        for (int i = 0; i < arr.length; i++) {
            while (!stack.isEmpty() && arr[stack.peek()] < arr[i]) {
                stack.pop();
                operations++;
            }
            stack.push(i);
            operations++;
        }
        return operations;
    }

    public static void main(String[] args) {
        int[] increasing = {1, 2, 3, 4, 5}; // every push triggers no pops until the end
        int[] worstCasePop = {5, 4, 3, 2, 1, 100}; // last element pops everything at once

        System.out.println("n = " + increasing.length + ", operations = "
            + runAndCountOperations(increasing) + " (bound: " + (2 * increasing.length) + ")");
        System.out.println("n = " + worstCasePop.length + ", operations = "
            + runAndCountOperations(worstCasePop) + " (bound: " + (2 * worstCasePop.length) + ")");
    }
}
```

**How to run:** save as `MonotonicStackComplexity.java`, then run `java MonotonicStackComplexity.java`.

## 6. Walkthrough

1. For `increasing = {1, 2, 3, 4, 5}`, each element is bigger than the last, so the stack never pops anything — every iteration does exactly one push. Total operations: 5, well under the `2n = 10` bound.
2. For `worstCasePop = {5, 4, 3, 2, 1, 100}`, the first five iterations only push (each new element is smaller than the one before, so the decreasing stack stays valid). Total pushes so far: 5.
3. On the sixth iteration (`100`), the `while` loop pops all five previous elements in one burst, because `100` is bigger than every one of them. Five pops, then one push for `100` itself. Total operations for this iteration: 6.
4. Summed across the whole run: 5 pushes (iterations 1–5) plus 6 operations (iteration 6) equals 11 operations, still within the `2n = 12` bound.
5. This confirms the amortized argument: the one expensive iteration (5 pops at once) is paid for by the 5 earlier iterations that each only pushed, never exceeding a total of `2n` operations across the whole run.

## 7. Gotchas & takeaways

> Gotcha: do not multiply the `for` loop's n iterations by the `while` loop's worst-case pop count and conclude O(n²). The `while` loop's total iterations across the *entire* run are bounded by n (the total number of pops), not by n per outer iteration.

- Time: O(n), by amortized analysis — every element is pushed once and popped at most once, so total pushes plus pops is at most 2n.
- Space: O(n) worst case, when the stack ends up holding most or all elements.
- Reference problems that use this pattern: Next Greater Element I, Next Greater Element II, Daily Temperatures, Online Stock Span, Sum of Subarray Minimums, Largest Rectangle in Histogram, Remove K Digits, Remove Duplicate Letters, Asteroid Collision.
