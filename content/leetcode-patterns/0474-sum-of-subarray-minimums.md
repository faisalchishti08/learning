---
card: leetcode-patterns
gi: 474
slug: sum-of-subarray-minimums
title: Sum of Subarray Minimums
---

## 1. What it is

Given an array `arr`, find the sum of the minimum value of every contiguous subarray, modulo `10^9 + 7` (the true sum can be astronomically large). Example: `arr = [3, 1, 2, 4]` → subarrays `[3],[1],[2],[4],[3,1],[1,2],[2,4],[3,1,2],[1,2,4],[3,1,2,4]` have minimums `3,1,2,4,1,1,2,1,1,1`, summing to `17`.

## 2. Why & when

There are `n(n+1)/2` subarrays, so computing each one's minimum directly is O(n²) or worse. The trick is to instead ask, for each element, "in how many subarrays is *this* element the minimum?" — a question a monotonic stack answers by finding each element's nearest smaller neighbor on both sides, part of the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family. Constraints: up to 30,000 elements.

## 3. Core concept

**Key idea:** for each element `arr[i]`, count how many subarrays have `arr[i]` as their minimum. That count is `left * right`, where `left` is the number of choices for the subarray's start (from just after the previous smaller-or-equal element, up to and including `i`) and `right` is the number of choices for the subarray's end (from `i` up to just before the next strictly smaller element). Each element's contribution to the total sum is `arr[i] * left * right`.

**Steps:**
1. For each index `i`, compute `previousSmallerOrEqual[i]`: the index of the nearest element to the left that is smaller than or equal to `arr[i]` (or `-1` if none). Use an increasing monotonic stack scanning left to right.
2. Compute `nextSmaller[i]`: the index of the nearest element to the right that is strictly smaller than `arr[i]` (or `n` if none). Use an increasing monotonic stack scanning right to left.
3. `left = i - previousSmallerOrEqual[i]`, `right = nextSmaller[i] - i`.
4. Sum `arr[i] * left * right` for every `i`, modulo `10^9 + 7`.

**Why one side uses "or equal" and the other doesn't:** using a strict inequality on both sides would double-count subarrays when duplicate values exist (two equal minimums would each claim the same subarray). Breaking the tie by treating one direction as "or equal" ensures every subarray is counted exactly once, by exactly one of its equal-valued minimums.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each element's contribution window bounded by nearer smaller neighbors on each side">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">arr = [3, 1, 2, 4], element at index 2 (value 2)</text>
    <rect x="20" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="40" width="50" height="34" fill="#161b22" stroke="#f0883e"/>
    <rect x="120" y="40" width="50" height="34" fill="#161b22" stroke="#79c0ff"/>
    <rect x="170" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="95" y="63" fill="#f0883e" text-anchor="middle">1</text>
    <text x="145" y="63" fill="#79c0ff" text-anchor="middle">2</text>
    <text x="195" y="63" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="20" y="100" fill="#8b949e">previous smaller-or-equal of index 2: index 1 (value 1) -&gt; left = 2-1 = 1</text>
    <text x="20" y="120" fill="#8b949e">next smaller of index 2: none (n=4) -&gt; right = 4-2 = 2</text>
    <text x="20" y="145" fill="#3fb950">index 2 is the minimum of left*right = 2 subarrays: [2] and [2,4]</text>
  </g>
</svg>

The stack finds the nearest smaller neighbor on each side, which bounds every subarray where this element is the minimum.

## 5. Runnable example

**Level 1 — Brute force.** Compute every subarray's minimum directly. O(n²) or O(n³) depending on how the minimum is tracked.

**KEY INSIGHT:** instead of computing the minimum of every subarray, compute for each element how many subarrays it is the minimum OF, using its nearest smaller neighbor on each side — this turns an O(n²) enumeration into an O(n) contribution sum.

**Level 2 — Optimal.** Two monotonic-stack passes (previous smaller-or-equal, next smaller), then a contribution sum, O(n).

**Level 3 — Hardened.** Handles duplicate values (via the "or equal" tie-break) and the modulo arithmetic.

```java
// SumOfSubarrayMinimums.java
import java.util.*;

public class SumOfSubarrayMinimums {

    static final int MOD = 1_000_000_007;

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] arr) {
        long total = 0;
        for (int i = 0; i < arr.length; i++) {
            int min = arr[i];
            for (int j = i; j < arr.length; j++) {
                min = Math.min(min, arr[j]);
                total = (total + min) % MOD;
            }
        }
        return (int) total;
    }

    // Level 2 & 3: monotonic stack contribution counting, O(n)
    static int sumSubarrayMins(int[] arr) {
        int n = arr.length;
        int[] previousSmallerOrEqual = new int[n];
        int[] nextSmaller = new int[n];

        Deque<Integer> stack = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && arr[stack.peek()] > arr[i]) {
                stack.pop();
            }
            previousSmallerOrEqual[i] = stack.isEmpty() ? -1 : stack.peek();
            stack.push(i);
        }

        stack.clear();
        for (int i = n - 1; i >= 0; i--) {
            while (!stack.isEmpty() && arr[stack.peek()] >= arr[i]) {
                stack.pop();
            }
            nextSmaller[i] = stack.isEmpty() ? n : stack.peek();
            stack.push(i);
        }

        long total = 0;
        for (int i = 0; i < n; i++) {
            long left = i - previousSmallerOrEqual[i];
            long right = nextSmaller[i] - i;
            total = (total + arr[i] * left % MOD * right) % MOD;
        }
        return (int) total;
    }

    public static void main(String[] args) {
        int[] arr = {3, 1, 2, 4};
        System.out.println("brute force: " + bruteForce(arr));
        System.out.println("optimal:     " + sumSubarrayMins(arr));

        int[] withDuplicates = {2, 2, 2};
        System.out.println("duplicates, brute force: " + bruteForce(withDuplicates));
        System.out.println("duplicates, optimal:     " + sumSubarrayMins(withDuplicates));
    }
}
```

**How to run:** save as `SumOfSubarrayMinimums.java`, then run `java SumOfSubarrayMinimums.java`.

## 6. Walkthrough

Trace `sumSubarrayMins({3, 1, 2, 4})`:

Previous smaller-or-equal pass (increasing stack, left to right):

| i | arr[i] | stack before | pops | previousSmallerOrEqual[i] | stack after |
|---|---|---|---|---|---|
| 0 | 3 | [] | none | -1 | [0] |
| 1 | 1 | [0] | pop 0 (3>1) | -1 | [1] |
| 2 | 2 | [1] | none (1 not > 2) | 1 | [1,2] |
| 3 | 4 | [1,2] | none (2 not > 4) | 2 | [1,2,3] |

Next smaller pass (increasing stack, right to left, using `>=` to break ties):

| i | arr[i] | stack before | pops | nextSmaller[i] | stack after |
|---|---|---|---|---|---|
| 3 | 4 | [] | none | 4 (n) | [3] |
| 2 | 2 | [3] | pop 3 (4>=2) | 4 (n) | [2] |
| 1 | 1 | [2] | pop 2 (2>=1) | 4 (n) | [1] |
| 0 | 3 | [1] | none (1 not >= 3) | 1 | [1,0] |

Contributions: index 0: `3 * (0-(-1)) * (1-0) = 3*1*1 = 3`. index 1: `1 * (1-(-1)) * (4-1) = 1*2*3 = 6`. index 2: `2 * (2-1) * (4-2) = 2*1*2 = 4`. index 3: `4 * (3-2) * (4-3) = 4*1*1 = 4`. Total: `3+6+4+4 = 17`, matching the expected sum.

## 7. Gotchas & takeaways

> Gotcha: using the same tie-break direction (both "or equal") on both sides double-counts subarrays where the minimum value repeats — each equal-valued minimum would claim the same subarray. Use "or equal" on exactly one side only.

- Reframe "sum of all subarray minimums" as "sum of (value × number of subarrays where it is the minimum)" — a per-element contribution count, not a per-subarray computation.
- Two monotonic-stack passes find the nearest smaller neighbor on each side; multiplying the two gaps gives the contribution window.
- Time: O(n) — three linear passes (two stack scans, one summation); remember the modulo on every multiplication to avoid overflow.
