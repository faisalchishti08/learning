---
card: leetcode-patterns
gi: 490
slug: running-sum-of-1d-array
title: Running Sum of 1d Array
---

## 1. What it is

Given an array `nums`, return an array `runningSum` where `runningSum[i]` is the sum of `nums[0..i]` (inclusive). Example: `nums = [1, 2, 3, 4]` → `[1, 3, 6, 10]`.

## 2. Why & when

This is the most direct application of the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md): the output *is* the prefix sum array itself (just 0-indexed instead of the padded 1-indexed convention). Constraints: up to 1000 elements.

## 3. Core concept

**Key idea:** each output value is the previous output value plus the current input value: `runningSum[i] = runningSum[i-1] + nums[i]` (with `runningSum[0] = nums[0]`).

**Steps:**
1. Copy `nums` into `runningSum` (or modify in place).
2. For each index `i` starting from `1`, add `runningSum[i-1]` to `runningSum[i]`.
3. Return the result.

**Why in-place update works:** by the time you compute `runningSum[i]`, `runningSum[i-1]` already holds the correct cumulative total for everything before it — you never need to look further back than one position.

## 4. Diagram

<svg viewBox="0 0 700 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each running sum built from the previous one plus the current value">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, 2, 3, 4]</text>
    <text x="20" y="45" fill="#8b949e">runningSum[0] = 1</text>
    <text x="20" y="65" fill="#8b949e">runningSum[1] = runningSum[0] + 2 = 3</text>
    <text x="20" y="85" fill="#8b949e">runningSum[2] = runningSum[1] + 3 = 6</text>
    <text x="20" y="105" fill="#3fb950">runningSum[3] = runningSum[2] + 4 = 10 -&gt; [1, 3, 6, 10]</text>
  </g>
</svg>

Each cumulative total builds directly on the one just computed before it.

## 5. Runnable example

**Level 1 — Brute force.** For each index, sum everything from the start up to it. O(n²).

**KEY INSIGHT:** the running sum at index `i` is just the running sum at `i-1` plus `nums[i]` — no need to re-add everything from the start each time.

**Level 2 — Optimal.** Single pass, updating in place, O(n).

**Level 3 — Hardened.** Handles a single-element array and negative numbers.

```java
// RunningSum.java
import java.util.Arrays;

public class RunningSum {

    // Level 1: brute force, O(n^2)
    static int[] bruteForce(int[] nums) {
        int[] result = new int[nums.length];
        for (int i = 0; i < nums.length; i++) {
            int sum = 0;
            for (int j = 0; j <= i; j++) sum += nums[j];
            result[i] = sum;
        }
        return result;
    }

    // Level 2 & 3: single pass, O(n)
    static int[] runningSum(int[] nums) {
        int[] result = nums.clone();
        for (int i = 1; i < result.length; i++) {
            result[i] += result[i - 1];
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 4};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums)));
        System.out.println("optimal:     " + Arrays.toString(runningSum(nums)));

        System.out.println("single:   " + Arrays.toString(runningSum(new int[]{5})));
        System.out.println("negative: " + Arrays.toString(runningSum(new int[]{-1, 2, -3, 4})));
    }
}
```

**How to run:** save as `RunningSum.java`, then run `java RunningSum.java`.

## 6. Walkthrough

Trace `runningSum({1, 2, 3, 4})`:

| i | nums[i] | result[i-1] | result[i] |
|---|---|---|---|
| 0 | 1 | — | 1 |
| 1 | 2 | 1 | 3 |
| 2 | 3 | 3 | 6 |
| 3 | 4 | 6 | 10 |

Final result: `[1, 3, 6, 10]`, matching the expected output. Time: O(n), space: O(n) for the output (O(1) extra if modifying in place).

## 7. Gotchas & takeaways

> Gotcha: computing `result[i]` from the original `nums` array instead of the already-updated `result[i-1]` reintroduces the O(n²) brute force by accident — always add to the previous *output* value, not re-sum the input.

- This problem is the prefix sum array itself, with no subtraction step needed — the simplest possible use of the pattern.
- In-place update works because each step only needs the immediately preceding cumulative total.
- Time: O(n), space: O(1) extra if updating `nums` in place instead of allocating a new array.
