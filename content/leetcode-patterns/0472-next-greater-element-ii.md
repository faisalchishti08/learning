---
card: leetcode-patterns
gi: 472
slug: next-greater-element-ii
title: Next Greater Element II
---

## 1. What it is

You get a **circular** array `nums`: after the last element, the search for a next greater element wraps around to the front. For each element, return the next greater element found by scanning forward, wrapping once if needed; return `-1` if none exists even after wrapping. Example: `nums = [1, 2, 1]` → `[2, -1, 2]` (the last `1` wraps around and finds `2` at index 1).

## 2. Why & when

This extends the basic [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) with a circularity twist: the word "circular" (or "wraps around") tells you to simulate a longer array without actually doubling memory for it. Constraints: up to 10,000 elements.

## 3. Core concept

**Key idea:** simulate scanning the array twice (indices `0` to `2n - 1`) but always take the *value* at `i % n`. Use the same decreasing monotonic stack of indices as the plain version, but only ever push and pop indices in the range `0` to `n - 1` (the second pass is purely for resolving wraparound answers, not for adding new elements to search for).

**Steps:**
1. Create a `result` array of size `n`, initialized to `-1`.
2. Maintain a decreasing stack of indices (only indices from the *original* array, `0` to `n - 1`).
3. Loop `i` from `0` to `2n - 1`. Compute `value = nums[i % n]`.
4. While the stack is not empty and `nums[stack.peek()] < value`, pop index `j` and set `result[j] = value`.
5. Only push `i % n` onto the stack when `i < n` (the first pass) — the second pass exists only to pop, not to add new candidates, because otherwise you would push duplicate indices.

**Why the second pass does not push:** every index only needs to be resolved once. If you also pushed during the second pass, the same index could be pushed twice, corrupting the stack's monotonic invariant and its indices.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scanning a circular array twice, resolving wraparound next-greater answers">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, 2, 1] (indices 0,1,2, then wrap: 0,1,2 again)</text>
    <text x="20" y="45" fill="#8b949e">i=0 (val 1): push 0. stack=[0]</text>
    <text x="20" y="65" fill="#8b949e">i=1 (val 2): pop 0 (1&lt;2) -&gt; result[0]=2. push 1. stack=[1]</text>
    <text x="20" y="85" fill="#8b949e">i=2 (val 1): 2 not &lt; 1, push 2. stack=[1,2]</text>
    <text x="20" y="105" fill="#8b949e">i=3 (val nums[0]=1, second pass, no push): 1 not &lt; 1, no pop</text>
    <text x="20" y="125" fill="#8b949e">i=4 (val nums[1]=2, second pass): pop 2 (1&lt;2) -&gt; result[2]=2</text>
    <text x="20" y="150" fill="#3fb950">final: [2, -1, 2] -- index 1 (value 2) never finds anything bigger</text>
  </g>
</svg>

The second pass over the array only resolves leftover indices from the stack; it never adds new ones.

## 5. Runnable example

**Level 1 — Brute force.** For each index, scan forward up to `2n - 1` positions (wrapping with modulo) for the first bigger value. O(n²).

**KEY INSIGHT:** simulating the wraparound with `i % n` over a `2n`-length loop lets the same monotonic-stack technique from the linear version resolve circular "next greater" queries, without physically duplicating the array.

**Level 2 — Optimal.** Single monotonic-stack pass over `2n` virtual positions, O(n).

**Level 3 — Hardened.** Handles all-equal elements (answer all `-1`) and a single-element array (wraps to itself, so answer is `-1`).

```java
// NextGreaterElementII.java
import java.util.*;

public class NextGreaterElementII {

    // Level 1: brute force, O(n^2)
    static int[] bruteForce(int[] nums) {
        int n = nums.length;
        int[] result = new int[n];
        Arrays.fill(result, -1);
        for (int i = 0; i < n; i++) {
            for (int step = 1; step < n; step++) {
                int j = (i + step) % n;
                if (nums[j] > nums[i]) { result[i] = nums[j]; break; }
            }
        }
        return result;
    }

    // Level 2 & 3: monotonic stack over 2n virtual positions, O(n)
    static int[] nextGreaterElements(int[] nums) {
        int n = nums.length;
        int[] result = new int[n];
        Arrays.fill(result, -1);
        Deque<Integer> stack = new ArrayDeque<>(); // decreasing values, holds original indices

        for (int i = 0; i < 2 * n; i++) {
            int value = nums[i % n];
            while (!stack.isEmpty() && nums[stack.peek()] < value) {
                result[stack.pop()] = value;
            }
            if (i < n) {
                stack.push(i); // only push original indices, only during the first pass
            }
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 1};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums)));
        System.out.println("optimal:     " + Arrays.toString(nextGreaterElements(nums)));

        System.out.println("all equal:    " + Arrays.toString(nextGreaterElements(new int[]{5, 5, 5})));
        System.out.println("single elem:  " + Arrays.toString(nextGreaterElements(new int[]{7})));
    }
}
```

**How to run:** save as `NextGreaterElementII.java`, then run `java NextGreaterElementII.java`.

## 6. Walkthrough

Trace `nextGreaterElements({1, 2, 1})`, `n = 3`, loop runs `i = 0` to `5`:

| i | i%n | value | stack before | action | stack after |
|---|---|---|---|---|---|
| 0 | 0 | 1 | [] | push 0 (i<n) | [0] |
| 1 | 1 | 2 | [0] | pop 0 → result[0]=2; push 1 | [1] |
| 2 | 2 | 1 | [1] | `nums[1]=2` not < 1; push 2 | [1,2] |
| 3 | 0 | 1 | [1,2] | `nums[2]=1` not < 1; i>=n, no push | [1,2] |
| 4 | 1 | 2 | [1,2] | pop 2 → result[2]=2; `nums[1]=2` not < 2; no push | [1] |
| 5 | 2 | 1 | [1] | `nums[1]=2` not < 1; no push | [1] |

Index `1` (value `2`) is never popped — it stays `-1`. Final: `[2, -1, 2]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: pushing `i % n` (instead of skipping the push) during the second pass (`i >= n`) re-adds indices that are already resolved or already on the stack, breaking the monotonic invariant and producing wrong answers. Only push during the first pass (`i < n`).

- "Circular" or "wraps around" is the signal to scan `2n` virtual positions with `i % n`, not to physically duplicate the array.
- Only push indices during the first pass; both passes may pop.
- Time: O(n) — the loop runs `2n` times, but total pushes and pops are still bounded by `n` each.
