---
card: leetcode-patterns
gi: 90
slug: find-all-duplicates-in-an-array
title: Find All Duplicates in an Array
---

## 1. What it is

Given an integer array `nums` of length `n` where every integer is in the range `[1, n]`, and each integer appears either once or twice, return an array of all the integers that appear twice. Example: `nums = [4,3,2,7,8,2,3,1]` → `[2, 3]`.

## 2. Why & when

This is the mirror image of Find All Numbers Disappeared: instead of reporting which expected values never arrived, this problem reports which values arrived twice. The same cyclic sort placement reveals both — a mismatch after placement can be read either as "the expected value is missing" or "the value sitting there is a duplicate," depending on which side of the mismatch the question asks about.

## 3. Core concept

**Key idea:** run cyclic sort to place each value `v` at index `v - 1`. Because every value appears at most twice, a duplicate can occupy only one of its two "wanted" positions — the other copy is left stranded wherever the placement loop could not move it further. After placement, any index `i` where `nums[i] != i + 1` holds a duplicate value.

**Steps:**
1. Set `i = 0`.
2. While `i < n`:
   - Compute `correct = nums[i] - 1`.
   - If `nums[i] != nums[correct]`, swap `nums[i]` and `nums[correct]`.
   - Otherwise, advance `i++` (this also naturally skips a duplicate that has already found one of its two homes).
3. Scan the array: for each index `i` where `nums[i] != i + 1`, add `nums[i]` (the value stranded there) to the result.

**Why it is correct:** cyclic sort guarantees every value that *can* reach its correct index does so. When a value appears twice, one copy settles at index `value - 1`, and the second copy — having nowhere left to go, since its slot is already correctly filled — stays wherever it lands. That leftover copy is exactly what the mismatch scan reports.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cyclic sort revealing duplicate values via leftover mismatches">
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
    <text x="20" y="130" fill="#8b949e">index 4 holds 3 (a duplicate); index 5 holds 2 (a duplicate) -&gt; duplicates: 3 and 2</text>
  </g>
</svg>

The same leftover values that flagged `5` and `6` as missing (in Find All Numbers Disappeared) are themselves the duplicates being reported here — `3` and `2` each appear twice.

## 5. Runnable example

```java
// FindAllDuplicates.java
import java.util.*;

public class FindAllDuplicates {

    // Level 1 -- Brute force: hash map counting occurrences, then
    // collect values with count 2. O(n) time, O(n) space -- wastes
    // memory the cyclic-sort in-place approach does not need.
    static List<Integer> bruteForce(int[] nums) {
        Map<Integer, Integer> count = new HashMap<>();
        for (int v : nums) count.merge(v, 1, Integer::sum);
        List<Integer> result = new ArrayList<>();
        for (Map.Entry<Integer, Integer> e : count.entrySet()) {
            if (e.getValue() == 2) result.add(e.getKey());
        }
        return result;
    }

    // KEY INSIGHT: cyclic sort places every value it can at its own
    // index; a duplicate can only occupy ONE of its two target slots, so
    // the leftover copy stranded elsewhere is directly revealed by the
    // mismatch scan.

    // Level 2 -- Optimal: cyclic sort placement, then scan for
    // mismatches. O(n) time, O(1) extra space (excluding the output).
    public static List<Integer> findDuplicates(int[] nums) {
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
        List<Integer> result = new ArrayList<>();
        for (i = 0; i < n; i++) {
            if (nums[i] != i + 1) result.add(nums[i]);
        }
        return result;
    }

    // Level 3 -- Hardened: no duplicates at all (every value 1..n
    // appears exactly once) -- returns an empty list.
    static List<Integer> hardened(int[] nums) {
        return findDuplicates(nums);
    }

    public static void main(String[] args) {
        int[] a = {4, 3, 2, 7, 8, 2, 3, 1};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + findDuplicates(a));

        int[] noDuplicates = {1, 2, 3, 4};
        System.out.println("none duplicated: " + hardened(noDuplicates));
    }
}
```

How to run: save as `FindAllDuplicates.java`, then run `java FindAllDuplicates.java`.

## 6. Walkthrough

Using the same placed array from the diagram, `{1,2,3,4,3,2,7,8}`:

| index | value | expected (i+1) | match? | reported |
|---|---|---|---|---|
| 0 | 1 | 1 | yes | — |
| 1 | 2 | 2 | yes | — |
| 2 | 3 | 3 | yes | — |
| 3 | 4 | 4 | yes | — |
| 4 | 3 | 5 | no | duplicate 3 |
| 5 | 2 | 6 | no | duplicate 2 |
| 6 | 7 | 7 | yes | — |
| 7 | 8 | 8 | yes | — |

Result: `[3, 2]`. Time complexity: O(n). Space complexity: O(1) extra space, not counting the output list.

## 7. Gotchas & takeaways

> Gotcha: this problem and Find All Numbers Disappeared use the *identical* placement loop — the only difference is whether the scan collects `nums[i]` (the stranded value, for duplicates) or `i + 1` (the expected value, for missing numbers). Mixing these up silently swaps the two answers.

- Recognizing that duplicates and missing values are two views of the same leftover mismatches after cyclic sort is the key insight — one placement pass answers both kinds of questions.
- Related problems: Find All Numbers Disappeared in an Array (the mirror question), Set Mismatch (the single-duplicate, single-missing special case).
