---
card: leetcode-patterns
gi: 85
slug: missing-number
title: Missing Number
---

## 1. What it is

Given an array `nums` containing `n` distinct numbers taken from the range `[0, n]`, find the one number in that range that is missing from the array. Example: `nums = [3,0,1]` → `n = 3`, range is `[0,3]`, missing number is `2`.

## 2. Why & when

A hash set of seen values, checked against every number in `[0, n]`, finds the missing number in O(n) time but O(n) space. This problem's range `[0, n]` (with `n + 1` possible values but only `n` array slots) is a direct match for cyclic sort's signal, letting you find the gap in O(1) extra space.

## 3. Core concept

**Key idea:** place each value `v` (where `0 <= v < n`) at index `v` using cyclic sort. Values equal to `n` cannot be placed (there is no index `n` in a 0-indexed array of length `n`), so they are simply skipped. After placement, scan for the one index whose value does not match — that index is the missing number.

**Steps:**
1. Set `i = 0`.
2. While `i < n`:
   - If `nums[i] < n` and `nums[i] != nums[nums[i]]`, swap `nums[i]` with `nums[nums[i]]`.
   - Otherwise, advance `i++` (this also skips any value equal to `n`, since it has no valid target index).
3. Scan the array: the first index `i` where `nums[i] != i` is the missing number. If every index matches, the missing number is `n` itself.

**Why it is correct:** cyclic sort correctly places every value in `[0, n-1]` at its matching index. The one value that never gets placed is exactly the missing one — either because it was `n` (a valid range member, but not a valid index) or because its "slot" ended up holding `n` instead.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cyclic sort finding the missing number by index mismatch">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [3, 0, 1], n = 3, range [0,3]</text>
    <text x="20" y="50" fill="#8b949e">after cyclic sort placement: [0, 1, 3] (3 cannot go to index 3, out of bounds)</text>
    <rect x="20" y="70" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="40" y="88" fill="#e6edf3" text-anchor="middle">0</text>
    <rect x="60" y="70" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="80" y="88" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="100" y="70" width="40" height="26" fill="#161b22" stroke="#f0883e"/><text x="120" y="88" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="20" y="120" fill="#8b949e">index 2 expects value 2, but holds 3 -&gt; 2 is the missing number</text>
  </g>
</svg>

Index `2` is the first index whose value does not match its own position — that mismatch reveals the missing number, `2`.

## 5. Runnable example

```java
// MissingNumber.java
import java.util.*;

public class MissingNumber {

    // Level 1 -- Brute force: sum 0..n via the arithmetic series formula,
    // subtract the actual array sum. O(n) time, O(1) space -- works, but
    // risks overflow for very large n and does not generalize to
    // "find all missing" variants the way cyclic sort does.
    static int bruteForce(int[] nums) {
        int n = nums.length;
        int expectedSum = n * (n + 1) / 2;
        int actualSum = 0;
        for (int v : nums) actualSum += v;
        return expectedSum - actualSum;
    }

    // KEY INSIGHT: cyclic sort places every value in [0, n-1] at its
    // matching index in one pass -- whatever index ends up NOT matching
    // its own value is exactly the missing number.

    // Level 2 -- Optimal: cyclic sort placement, then scan for mismatch.
    // O(n) time, O(1) space.
    public static int missingNumber(int[] nums) {
        int n = nums.length;
        int i = 0;
        while (i < n) {
            if (nums[i] < n && nums[i] != nums[nums[i]]) {
                int temp = nums[i];
                nums[i] = nums[temp];
                nums[temp] = temp;
            } else {
                i++;
            }
        }
        for (i = 0; i < n; i++) {
            if (nums[i] != i) return i;
        }
        return n;
    }

    // Level 3 -- Hardened: the missing number is 0 (first index), or the
    // missing number is n itself (last, out-of-bounds value).
    static int hardened(int[] nums) {
        return missingNumber(nums);
    }

    public static void main(String[] args) {
        int[] a = {3, 0, 1};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + missingNumber(a));

        System.out.println("missing is 0: " + hardened(new int[] {1, 2}));
        System.out.println("missing is n: " + hardened(new int[] {0, 1}));
    }
}
```

How to run: save as `MissingNumber.java`, then run `java MissingNumber.java`.

## 6. Walkthrough

Dry run of `missingNumber({3, 0, 1})`, `n = 3`:

| step | i | nums[i] | condition | action | array after |
|---|---|---|---|---|---|
| 1 | 0 | 3 | 3 < 3? no | advance | [3,0,1] |
| 2 | 1 | 0 | 0<3, nums[1]=0==nums[0]=3? no | swap nums[1],nums[0] | [0,3,1] |
| 3 | 1 | 3 | 3 < 3? no | advance | [0,3,1] |
| 4 | 2 | 1 | 1<3, nums[2]=1==nums[1]=3? no | swap nums[2],nums[1] | [0,1,3] |
| 5 | 2 | 3 | 3 < 3? no | advance | [0,1,3] |

Placement loop ends (`i = 3 = n`). Scan: index `0` holds `0` (match), index `1` holds `1` (match), index `2` holds `3` (mismatch — expected `2`). Return `2`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting the `nums[i] < n` bounds check before indexing `nums[nums[i]]` throws an `ArrayIndexOutOfBoundsException` when the array contains the value `n` itself, since `n` is a valid range member but not a valid array index.

- This is the most direct application of the cyclic sort template — the "special" out-of-range value (`n`) is what makes the scan-for-mismatch step necessary, instead of a pure swap-until-sorted loop.
- Related problems: Find All Numbers Disappeared in an Array (the "find all missing" generalization), First Missing Positive (a stricter range and a different missing-value definition).
