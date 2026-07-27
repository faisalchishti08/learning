---
card: leetcode-patterns
gi: 494
slug: contiguous-array
title: Contiguous Array
---

## 1. What it is

Given a binary array `nums` (only `0`s and `1`s), find the maximum length of a contiguous subarray with an equal number of `0`s and `1`s. Example: `nums = [0, 1, 0]` → `2` (the subarray `[0,1]` or `[1,0]`, either has one `0` and one `1`).

## 2. Why & when

Reframe "equal count of 0s and 1s" as a prefix-sum-zero condition: treat every `0` as `-1` and every `1` as `+1`. A subarray has an equal count of each exactly when its transformed sum is `0`, which happens exactly when two prefix sums are equal — the balance-condition variant of the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md). Constraints: up to 100,000 elements.

## 3. Core concept

**Key idea:** map `0 -> -1`, `1 -> +1`, and track a running sum as you scan. Two indices `i < j` have an equal count of `0`s and `1`s between them exactly when `runningSum` at `j` equals `runningSum` at `i` (the `+1`s and `-1`s in between cancel out). Use a hash map from "prefix sum value" to "the *first* index where it occurred" (not a count, since you want the longest span, not the total number of matches).

**Steps:**
1. Initialize `firstIndexOf = {0: -1}` (a running sum of `0` occurs "before index 0," at the imaginary index `-1`, so a subarray starting at index 0 can still be measured).
2. Scan the array, maintaining `runningSum` (add `+1` for a `1`, subtract `1` for a `0`).
3. At each index `i`: if `runningSum` has been seen before, the subarray between that earlier index and `i` has an equal count of `0`s and `1`s — its length is `i - firstIndexOf[runningSum]`. Track the maximum such length.
4. If `runningSum` has not been seen before, record `firstIndexOf[runningSum] = i` (only the *first* occurrence matters, since later occurrences would only shrink the span).

**Why storing the first index (not every index, and not a count) is essential here:** unlike counting subarrays (Subarray Sum Equals K), this problem wants the longest span. The longest possible span for a given running-sum value always starts at the earliest index where that value occurred — recording later occurrences would never improve the answer, only shrink it.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mapping 0 to -1 and 1 to +1, tracking the first index of each running sum">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [0, 1, 0], mapped to [-1, +1, -1]</text>
    <text x="20" y="45" fill="#8b949e">firstIndexOf = {0: -1}. runningSum=0.</text>
    <text x="20" y="65" fill="#8b949e">i=0 (-1): runningSum=-1, not seen -&gt; firstIndexOf={0:-1, -1:0}</text>
    <text x="20" y="85" fill="#8b949e">i=1 (+1): runningSum=0, seen at -1 -&gt; length=1-(-1)=2. maxLen=2</text>
    <text x="20" y="105" fill="#8b949e">i=2 (-1): runningSum=-1, seen at 0 -&gt; length=2-0=2. maxLen=2</text>
    <text x="20" y="135" fill="#3fb950">final answer: maxLen = 2</text>
  </g>
</svg>

Two equal running sums bound a subarray with an equal count of `0`s and `1`s between them.

## 5. Runnable example

**Level 1 — Brute force.** For every subarray, count its `0`s and `1`s directly and check for equality. O(n²).

**KEY INSIGHT:** mapping `0` to `-1` turns "equal counts" into "prefix sum returns to a value seen before" — a hash map of the *first* index for each running sum finds the longest such span in one pass.

**Level 2 — Optimal.** Running sum with `+1`/`-1` mapping and a first-index hash map, O(n).

**Level 3 — Hardened.** Handles an array with no balanced subarray (answer `0`) and an already-balanced full array.

```java
// ContiguousArray.java
import java.util.*;

public class ContiguousArray {

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] nums) {
        int maxLen = 0;
        for (int i = 0; i < nums.length; i++) {
            int zeros = 0, ones = 0;
            for (int j = i; j < nums.length; j++) {
                if (nums[j] == 0) zeros++; else ones++;
                if (zeros == ones) maxLen = Math.max(maxLen, j - i + 1);
            }
        }
        return maxLen;
    }

    // Level 2 & 3: running sum with +1/-1 mapping, O(n)
    static int findMaxLength(int[] nums) {
        Map<Integer, Integer> firstIndexOf = new HashMap<>();
        firstIndexOf.put(0, -1);
        int runningSum = 0;
        int maxLen = 0;

        for (int i = 0; i < nums.length; i++) {
            runningSum += (nums[i] == 1) ? 1 : -1;
            if (firstIndexOf.containsKey(runningSum)) {
                maxLen = Math.max(maxLen, i - firstIndexOf.get(runningSum));
            } else {
                firstIndexOf.put(runningSum, i);
            }
        }
        return maxLen;
    }

    public static void main(String[] args) {
        System.out.println(bruteForce(new int[]{0, 1, 0}));        // 2
        System.out.println(findMaxLength(new int[]{0, 1, 0}));      // 2
        System.out.println(findMaxLength(new int[]{0, 1}));         // 2
        System.out.println(findMaxLength(new int[]{0, 0, 1, 1}));   // 4
        System.out.println(findMaxLength(new int[]{0, 0, 0}));      // 0 (never balanced)
    }
}
```

**How to run:** save as `ContiguousArray.java`, then run `java ContiguousArray.java`.

## 6. Walkthrough

Trace `findMaxLength({0, 1, 0})`, mapped values `[-1, +1, -1]`, `firstIndexOf = {0: -1}` initially:

| i | mapped value | runningSum | seen before? | maxLen | firstIndexOf after |
|---|---|---|---|---|---|
| 0 | -1 | -1 | no | 0 | {0:-1, -1:0} |
| 1 | +1 | 0 | yes, at -1 | max(0, 1-(-1))=2 | unchanged |
| 2 | -1 | -1 | yes, at 0 | max(2, 2-0)=2 | unchanged |

Final `maxLen = 2`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: updating `firstIndexOf[runningSum]` every time that value appears (instead of only the first time) makes later spans look shorter than they really are — always keep the earliest recorded index for each running-sum value.

- The `0 -> -1` mapping turns "equal counts" into "prefix sum returns to a previously seen value" — the same core idea as [Subarray Sum Equals K](0493-subarray-sum-equals-k.md), but tracking first-seen index instead of a count, because the goal is length, not quantity.
- Seed the map with `{0: -1}` so a balanced subarray starting at index 0 is measured correctly.
- Time: O(n) — one pass, O(1) amortized hash map operations per step.
