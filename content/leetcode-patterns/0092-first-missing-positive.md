---
card: leetcode-patterns
gi: 92
slug: first-missing-positive
title: First Missing Positive
---

## 1. What it is

Given an unsorted integer array `nums`, find the smallest missing positive integer, using O(n) time and O(1) extra space. Example: `nums = [3,4,-1,1]` → the array contains `1`, `3`, and `4`, but not `2` → the smallest missing positive is `2`.

## 2. Why & when

This is the hardest cyclic sort problem in the section, because the array is not restricted to values `[1, n]` — it can contain negatives, zeros, and values far larger than `n`. The key realization is that only values in the range `[1, n]` can possibly matter: the answer is always at most `n + 1`, so anything outside `[1, n]` can be treated as "unplaceable" and safely ignored during placement.

## 3. Core concept

**Key idea:** run cyclic sort, but only attempt to place values that fall within `[1, n]` — skip negatives, zero, and values greater than `n` entirely, since they can never be the answer. After placement, the first index `i` where `nums[i] != i + 1` reveals the smallest missing positive; if every index matches, the answer is `n + 1`.

**Steps:**
1. Set `i = 0`, `n = nums.length`.
2. While `i < n`:
   - Compute `correct = nums[i] - 1`.
   - If `nums[i] >= 1 && nums[i] <= n && nums[i] != nums[correct]`, swap `nums[i]` and `nums[correct]`.
   - Otherwise, advance `i++` (this naturally skips out-of-range values).
3. Scan the array: return the first index `i` where `nums[i] != i + 1`, as `i + 1`.
4. If every index matches, return `n + 1`.

**Why it is correct:** if `nums` contained every value from `1` to `n`, the answer would have to be `n + 1` (the very next integer). Since the array has only `n` slots, the smallest missing positive can never exceed `n + 1`. Any value outside `[1, n]` is therefore irrelevant to the answer and can be ignored, letting the same cyclic sort placement and mismatch scan from earlier problems apply directly.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cyclic sort ignoring out-of-range values to find the smallest missing positive">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [3, 4, -1, 1], n = 4</text>
    <text x="20" y="45" fill="#8b949e">-1 is out of range [1,4] -&gt; skipped during placement</text>
    <text x="20" y="70" fill="#8b949e">after placement: [1, -1, 3, 4] (index 1 has no valid value to hold)</text>
    <rect x="20" y="85" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="35" y="101" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="50" y="85" width="30" height="24" fill="#161b22" stroke="#f0883e"/><text x="65" y="101" fill="#e6edf3" text-anchor="middle" font-size="10">-1</text>
    <rect x="80" y="85" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="95" y="101" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <rect x="110" y="85" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="125" y="101" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <text x="20" y="140" fill="#8b949e">index 1 expects value 2 but holds -1 -&gt; smallest missing positive is 2</text>
  </g>
</svg>

`-1` can never satisfy any index's requirement, so index `1` (expecting the value `2`) is left holding the leftover `-1` — revealing `2` as the smallest missing positive.

## 5. Runnable example

```java
// FirstMissingPositive.java
import java.util.*;

public class FirstMissingPositive {

    // Level 1 -- Brute force: hash set of all values, then check 1, 2,
    // 3, ... in order until one is not in the set. O(n) time, O(n) space
    // -- wastes memory the cyclic-sort in-place approach does not need.
    static int bruteForce(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int v : nums) seen.add(v);
        int candidate = 1;
        while (seen.contains(candidate)) candidate++;
        return candidate;
    }

    // KEY INSIGHT: the answer can never exceed n + 1, so any value
    // outside [1, n] is irrelevant and can be skipped entirely during
    // placement -- the same cyclic sort mismatch scan from Missing
    // Number then finds the answer directly.

    // Level 2 -- Optimal: cyclic sort placement restricted to [1, n],
    // then scan. O(n) time, O(1) extra space.
    public static int firstMissingPositive(int[] nums) {
        int n = nums.length;
        int i = 0;
        while (i < n) {
            int correct = nums[i] - 1;
            if (nums[i] >= 1 && nums[i] <= n && nums[i] != nums[correct]) {
                int temp = nums[i];
                nums[i] = nums[correct];
                nums[correct] = temp;
            } else {
                i++;
            }
        }
        for (i = 0; i < n; i++) {
            if (nums[i] != i + 1) return i + 1;
        }
        return n + 1;
    }

    // Level 3 -- Hardened: an array that already contains exactly
    // 1..n in some order -- the answer must be n + 1.
    static int hardened(int[] nums) {
        return firstMissingPositive(nums);
    }

    public static void main(String[] args) {
        int[] a = {3, 4, -1, 1};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + firstMissingPositive(a));

        int[] complete = {2, 1, 3};
        System.out.println("complete 1..n (expect 4): " + hardened(complete));
    }
}
```

How to run: save as `FirstMissingPositive.java`, then run `java FirstMissingPositive.java`.

## 6. Walkthrough

Dry run of `firstMissingPositive({3, 4, -1, 1})`, `n = 4`:

| step | i | nums[i] | in range? | correct | nums[correct] | action |
|---|---|---|---|---|---|---|
| 1 | 0 | 3 | yes | 2 | -1 | swap -> [-1,4,3,1] |
| 2 | 0 | -1 | no | — | — | advance |
| 3 | 1 | 4 | yes | 3 | 1 | swap -> [-1,1,3,4] |
| 4 | 1 | 1 | yes | 0 | -1 | swap -> [1,-1,3,4] |
| 5 | 1 | -1 | no | — | — | advance |
| 6 | 2 | 3 | yes | 2 | 3 | already correct, advance |
| 7 | 3 | 4 | yes | 3 | 4 | already correct, advance |

Placement ends: `[1, -1, 3, 4]`. Scan: index `0` matches (`1`), index `1` mismatches (expects `2`, holds `-1`). Return `2`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting the upper-bound check (`nums[i] <= n`) lets a large out-of-range value like `1000000` attempt to index far outside the array, causing an `ArrayIndexOutOfBoundsException` — always bound-check both sides before treating a value as placeable.

- This is the most general cyclic sort problem in the section: the "ignore anything outside `[1,n]`" filter is what lets an otherwise-unrestricted array still benefit from the O(1)-space technique.
- Related problems: Missing Number (a cleaner, pre-bounded version of this same idea), Find All Numbers Disappeared in an Array (same mechanics, reports all gaps instead of just the first).
