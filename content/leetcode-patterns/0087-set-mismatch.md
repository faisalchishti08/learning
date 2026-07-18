---
card: leetcode-patterns
gi: 87
slug: set-mismatch
title: Set Mismatch
---

## 1. What it is

You have a set of numbers `1` to `n`. Due to a data error, one number got duplicated and, as a result, another number is missing. Given the corrupted array `nums`, return `[duplicate, missing]`. Example: `nums = [1,2,2,4]` → `[2, 3]` (`2` is duplicated, `3` is missing).

## 2. Why & when

This is Find All Numbers Disappeared combined with duplicate detection, specialized to the case of exactly one duplicate and exactly one missing value. Cyclic sort places every value it can; the one leftover mismatch after placement directly reveals both the duplicate (the value sitting in the wrong slot) and the missing number (the slot's own expected value).

## 3. Core concept

**Key idea:** run cyclic sort to place each value `v` at index `v - 1`. Because there is exactly one duplicate, the placement loop naturally leaves exactly one index holding a value that is not its own index-plus-one — that value is the duplicate, and the index's expected value is the missing number.

**Steps:**
1. Set `i = 0`.
2. While `i < n`:
   - Compute `correct = nums[i] - 1`.
   - If `nums[i] != nums[correct]`, swap `nums[i]` and `nums[correct]`.
   - Otherwise, advance `i++`.
3. Scan the array for the one index `i` where `nums[i] != i + 1`. The duplicate is `nums[i]`; the missing number is `i + 1`.

**Why it is correct:** with exactly one duplicate and one missing number, cyclic sort successfully places every other value at its correct index. The single index left "wrong" holds the duplicate value (since the duplicate's true partner already occupies its rightful spot), and that index's own rightful value is exactly the one missing from the whole array.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One mismatch revealing both the duplicate and the missing number">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [1, 2, 2, 4], n = 4</text>
    <text x="20" y="45" fill="#8b949e">after cyclic sort: [1, 2, 2, 4] (already stable -- 2 cannot displace itself)</text>
    <rect x="20" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="35" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="50" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="65" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="80" y="60" width="30" height="24" fill="#161b22" stroke="#f0883e"/><text x="95" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="110" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="125" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <text x="20" y="120" fill="#8b949e">index 2 expects 3 but holds 2 -&gt; duplicate=2, missing=3</text>
  </g>
</svg>

Index `2` is the only mismatch: it holds `2` (the duplicate) instead of its expected value `3` (the missing number) — both answers come from this single mismatched slot.

## 5. Runnable example

```java
// SetMismatch.java
import java.util.*;

public class SetMismatch {

    // Level 1 -- Brute force: count occurrences of every value with an
    // array of counters, scan for the count-2 (duplicate) and count-0
    // (missing) entries. O(n) time, O(n) space -- wastes memory the
    // cyclic-sort in-place approach does not need.
    static int[] bruteForce(int[] nums) {
        int n = nums.length;
        int[] count = new int[n + 1];
        for (int v : nums) count[v]++;
        int duplicate = -1, missing = -1;
        for (int v = 1; v <= n; v++) {
            if (count[v] == 2) duplicate = v;
            if (count[v] == 0) missing = v;
        }
        return new int[] {duplicate, missing};
    }

    // KEY INSIGHT: with exactly one duplicate and one missing value,
    // cyclic sort placement leaves EXACTLY one index mismatched -- that
    // single slot directly reveals both answers.

    // Level 2 -- Optimal: cyclic sort placement, then find the one
    // mismatch. O(n) time, O(1) extra space.
    public static int[] findErrorNums(int[] nums) {
        int n = nums.length;
        int i = 0;
        while (i < n) {
            int correct = nums[i] - 1;
            if (nums[i] != nums[correct]) {
                int temp = nums[i];
                nums[i] = nums[correct];
                nums[correct] = temp;
            } else {
                i++;
            }
        }
        for (i = 0; i < n; i++) {
            if (nums[i] != i + 1) {
                return new int[] {nums[i], i + 1};
            }
        }
        return new int[] {-1, -1};
    }

    // Level 3 -- Hardened: the duplicate and missing values are adjacent
    // (e.g. duplicate=1, missing=2), a common edge case for off-by-one
    // errors in the mismatch scan.
    static int[] hardened(int[] nums) {
        return findErrorNums(nums);
    }

    public static void main(String[] args) {
        int[] a = {1, 2, 2, 4};
        System.out.println("brute force: " + Arrays.toString(bruteForce(a.clone())));
        System.out.println("optimal:     " + Arrays.toString(findErrorNums(a)));

        int[] adjacent = {1, 1, 3};
        System.out.println("adjacent case (expect [1,2]): " + Arrays.toString(hardened(adjacent)));
    }
}
```

How to run: save as `SetMismatch.java`, then run `java SetMismatch.java`.

## 6. Walkthrough

Dry run of `findErrorNums({1, 2, 2, 4})`, `n = 4`:

| step | i | nums[i] | correct | nums[correct] | equal? | action |
|---|---|---|---|---|---|---|
| 1 | 0 | 1 | 0 | 1 | yes | advance |
| 2 | 1 | 2 | 1 | 2 | yes | advance |
| 3 | 2 | 2 | 1 | 2 | yes | advance (2 already matches its own target from index 1) |
| 4 | 3 | 4 | 3 | 4 | yes | advance |

Placement loop ends without changes (the array was already stable, since `2`'s duplicate cannot displace the correctly-placed `2` at index `1`). Scan: index `2` holds `2` but expects `3` — mismatch found. Return `[2, 3]` (duplicate `2`, missing `3`). Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: assuming the mismatch scan will always find the duplicate at the index matching its *first* occurrence — actually, cyclic sort settles the duplicate at whichever index its "correct" slot naturally computes to, which may not be either of the duplicate's original two positions in the input array.

- This problem shows how a single leftover mismatch after cyclic sort placement can answer two different questions (duplicate and missing) simultaneously — no separate pass needed for each.
- Related problems: Find All Numbers Disappeared in an Array (multiple missing, no duplicate reporting), Find the Missing and Repeated Values (the same idea generalized to a 2D grid).
