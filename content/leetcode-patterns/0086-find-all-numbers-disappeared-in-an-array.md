---
card: leetcode-patterns
gi: 86
slug: find-all-numbers-disappeared-in-an-array
title: Find All Numbers Disappeared in an Array
---

## 1. What it is

Given an array `nums` of `n` integers where each value is in the range `[1, n]`, some values appear twice and others do not appear at all. Return a list of all the numbers in `[1, n]` that never appear in `nums`. Example: `nums = [4,3,2,7,8,2,3,1]` → `[5, 6]`.

## 2. Why & when

This is Missing Number's multi-value generalization: instead of exactly one missing number out of `n+1` possible values, there can be multiple missing numbers out of `n` possible values (with duplicates filling the gaps). Cyclic sort places every value it can, and the leftover mismatches after placement reveal every missing number, not just one.

## 3. Core concept

**Key idea:** run cyclic sort to place each value `v` at index `v - 1`. Duplicates naturally cannot both be placed at the same index, so they stay elsewhere in the array. After placement, any index `i` where `nums[i] != i + 1` means the value `i + 1` never made it into the array — it is missing.

**Steps:**
1. Set `i = 0`.
2. While `i < n`:
   - Compute `correct = nums[i] - 1`.
   - If `nums[i] != nums[correct]`, swap `nums[i]` and `nums[correct]`.
   - Otherwise, advance `i++`.
3. Scan the array: for each index `i` where `nums[i] != i + 1`, add `i + 1` to the result list.

**Why it is correct:** cyclic sort guarantees that every value which *can* reach its correct index does so. A duplicate value can only occupy one of the two (or more) indices it "wants," leaving the other index holding some other, wrong value — which is exactly the signal that the true owner of that index is missing.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cyclic sort revealing multiple missing numbers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [4,3,2,7,8,2,3,1], n = 8</text>
    <text x="20" y="45" fill="#8b949e">after cyclic sort: [1,2,3,4,3,2,7,8]</text>
    <rect x="20" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="35" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="50" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="65" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="80" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="95" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <rect x="110" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="125" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <rect x="140" y="60" width="30" height="24" fill="#161b22" stroke="#f0883e"/><text x="155" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <rect x="170" y="60" width="30" height="24" fill="#161b22" stroke="#f0883e"/><text x="185" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="200" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="215" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">7</text>
    <rect x="230" y="60" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="245" y="76" fill="#e6edf3" text-anchor="middle" font-size="10">8</text>
    <text x="20" y="130" fill="#8b949e">index 4 (expects 5) holds 3; index 5 (expects 6) holds 2 -&gt; missing: 5 and 6</text>
  </g>
</svg>

Duplicate `3` and `2` each occupy an extra slot, bumping `5` and `6` out entirely — the mismatch scan catches both missing values in one pass.

## 5. Runnable example

```java
// FindAllNumbersDisappeared.java
import java.util.*;

public class FindAllNumbersDisappeared {

    // Level 1 -- Brute force: hash set of seen values, then scan [1,n]
    // for absentees. O(n) time, O(n) space -- wastes memory the
    // cyclic-sort in-place approach does not need.
    static List<Integer> bruteForce(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int v : nums) seen.add(v);
        List<Integer> missing = new ArrayList<>();
        for (int v = 1; v <= nums.length; v++) {
            if (!seen.contains(v)) missing.add(v);
        }
        return missing;
    }

    // KEY INSIGHT: cyclic sort places every reachable value at its own
    // index; duplicates can only occupy one of their two target slots,
    // so scanning for index/value mismatches after placement finds
    // EVERY missing number, not just one.

    // Level 2 -- Optimal: cyclic sort placement, then scan. O(n) time,
    // O(1) extra space (the output list itself is not counted).
    public static List<Integer> findDisappearedNumbers(int[] nums) {
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
        List<Integer> missing = new ArrayList<>();
        for (i = 0; i < n; i++) {
            if (nums[i] != i + 1) missing.add(i + 1);
        }
        return missing;
    }

    // Level 3 -- Hardened: no numbers missing at all (every value 1..n
    // appears exactly once) -- returns an empty list.
    static List<Integer> hardened(int[] nums) {
        return findDisappearedNumbers(nums);
    }

    public static void main(String[] args) {
        int[] a = {4, 3, 2, 7, 8, 2, 3, 1};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + findDisappearedNumbers(a));

        int[] complete = {1, 2, 3, 4};
        System.out.println("none missing: " + hardened(complete));
    }
}
```

How to run: save as `FindAllNumbersDisappeared.java`, then run `java FindAllNumbersDisappeared.java`.

## 6. Walkthrough

After the cyclic sort placement loop, the array `{4,3,2,7,8,2,3,1}` becomes `{1,2,3,4,3,2,7,8}` (traced position by position, each value swapped toward its own index until no further correct swap is possible).

Scanning the result:

| index | value | expected (i+1) | match? |
|---|---|---|---|
| 0 | 1 | 1 | yes |
| 1 | 2 | 2 | yes |
| 2 | 3 | 3 | yes |
| 3 | 4 | 4 | yes |
| 4 | 3 | 5 | **no -> 5 missing** |
| 5 | 2 | 6 | **no -> 6 missing** |
| 6 | 7 | 7 | yes |
| 7 | 8 | 8 | yes |

Result: `[5, 6]`. Time complexity: O(n) for both the placement loop and the scan. Space complexity: O(1) extra space.

## 7. Gotchas & takeaways

> Gotcha: the placement loop's swap condition must compare *values* (`nums[i] != nums[correct]`), not indices (`i != correct`) — comparing indices would loop forever on a duplicate value that keeps trying to swap with itself.

- This problem is the direct multi-value generalization of Missing Number — same cyclic sort mechanics, a scan that collects every mismatch instead of stopping at the first one.
- Related problems: Missing Number (single missing value, different range), Find All Duplicates in an Array (the mirror problem — same mismatches, but reporting the duplicates instead of the missing values).
