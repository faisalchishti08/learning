---
card: leetcode-patterns
gi: 69
slug: summary-ranges
title: Summary Ranges
---

## 1. What it is

Given a sorted, unique array of integers `nums`, return the smallest sorted list of ranges that cover exactly the numbers in the array. Each range `[a, b]` is written as `"a->b"` if `a != b`, or just `"a"` if `a == b`. Example: `nums = [0,1,2,4,5,7]` → `["0->2","4->5","7"]`.

## 2. Why & when

Checking every possible pair of numbers for whether they belong in the same range is unnecessary — since the array is already sorted, consecutive numbers either continue the current run (each is exactly one more than the last) or start a new range. This is the simplest possible Merge Intervals problem: no explicit `[start, end]` pairs are given, but the values themselves define implicit unit-length intervals that get merged when consecutive.

## 3. Core concept

**Key idea:** scan the sorted array once. Track the start of the current range. Whenever the next number is not exactly one more than the current number, the current range ends — record it and start a new one.

**Steps:**
1. If the array is empty, return an empty list.
2. Set `rangeStart = nums[0]`.
3. For each index `i` from `1` to `n - 1`:
   - If `nums[i] != nums[i - 1] + 1`, the range `[rangeStart, nums[i - 1]]` is finished — format and add it. Set `rangeStart = nums[i]`.
4. After the loop, format and add the final range `[rangeStart, nums[n - 1]]`.

**Why it is correct:** because the array is sorted and contains unique values, any break in consecutiveness (`nums[i] != nums[i-1] + 1`) is the only place a range can end — everywhere else, the numbers form an unbroken run and belong in the same output range.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Grouping consecutive numbers into ranges">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [0, 1, 2, 4, 5, 7]</text>
    <rect x="20" y="40" width="30" height="26" fill="#161b22" stroke="#3fb950"/><text x="35" y="58" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <rect x="50" y="40" width="30" height="26" fill="#161b22" stroke="#3fb950"/><text x="65" y="58" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <rect x="80" y="40" width="30" height="26" fill="#161b22" stroke="#3fb950"/><text x="95" y="58" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <rect x="130" y="40" width="30" height="26" fill="#161b22" stroke="#f0883e"/><text x="145" y="58" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <rect x="160" y="40" width="30" height="26" fill="#161b22" stroke="#f0883e"/><text x="175" y="58" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <rect x="210" y="40" width="30" height="26" fill="#161b22" stroke="#79c0ff"/><text x="225" y="58" fill="#e6edf3" text-anchor="middle" font-size="11">7</text>
    <text x="20" y="100" fill="#8b949e">break between 2 and 4 (gap of 2, not 1) -&gt; new range; break between 5 and 7 -&gt; new range</text>
    <text x="20" y="125" fill="#8b949e">result: ["0-&gt;2", "4-&gt;5", "7"]</text>
  </g>
</svg>

Each color marks one output range; a break in consecutiveness is the signal that starts a new group.

## 5. Runnable example

```java
// SummaryRanges.java
import java.util.*;

public class SummaryRanges {

    // Level 1 -- Brute force: for every index, look ahead as far as
    // possible while consecutive, using a nested loop. O(n^2) worst case
    // (each range re-scans from its start) -- wastes repeated look-aheads.
    static List<String> bruteForce(int[] nums) {
        List<String> result = new ArrayList<>();
        int i = 0;
        while (i < nums.length) {
            int j = i;
            while (j + 1 < nums.length) {
                boolean consecutive = false;
                for (int k = i; k <= j; k++) {
                    if (nums[j + 1] == nums[k] + (j + 1 - k)) consecutive = true;
                }
                if (!consecutive) break;
                j++;
            }
            result.add(format(nums[i], nums[j]));
            i = j + 1;
        }
        return result;
    }

    // KEY INSIGHT: a sorted, unique array only breaks its "consecutive run"
    // at one specific point -- where nums[i] != nums[i-1] + 1 -- so a
    // single forward scan finds every range boundary directly.

    // Level 2 -- Optimal: single pass, checking the +1 rule. O(n) time,
    // O(1) extra space (excluding the output).
    public static List<String> summaryRanges(int[] nums) {
        List<String> result = new ArrayList<>();
        if (nums.length == 0) return result;

        int rangeStart = nums[0];
        for (int i = 1; i < nums.length; i++) {
            if (nums[i] != nums[i - 1] + 1) {
                result.add(format(rangeStart, nums[i - 1]));
                rangeStart = nums[i];
            }
        }
        result.add(format(rangeStart, nums[nums.length - 1]));
        return result;
    }

    static String format(int start, int end) {
        return (start == end) ? String.valueOf(start) : start + "->" + end;
    }

    // Level 3 -- Hardened: empty array and single-element array.
    static List<String> hardened(int[] nums) {
        return summaryRanges(nums);
    }

    public static void main(String[] args) {
        int[] nums = {0, 1, 2, 4, 5, 7};
        System.out.println("brute force: " + bruteForce(nums));
        System.out.println("optimal:     " + summaryRanges(nums));
        System.out.println("empty:       " + hardened(new int[] {}));
        System.out.println("single:      " + hardened(new int[] {5}));
    }
}
```

How to run: save as `SummaryRanges.java`, then run `java SummaryRanges.java`.

## 6. Walkthrough

Dry run of `summaryRanges({0,1,2,4,5,7})`:

| i | nums[i] | nums[i-1]+1 | consecutive? | action |
|---|---|---|---|---|
| 1 | 1 | 1 | yes | continue range |
| 2 | 2 | 2 | yes | continue range |
| 3 | 4 | 3 | no | close [0,2] -> "0->2"; rangeStart=4 |
| 4 | 5 | 5 | yes | continue range |
| 5 | 7 | 6 | no | close [4,5] -> "4->5"; rangeStart=7 |
| end | — | — | — | close [7,7] -> "7" |

Result: `["0->2", "4->5", "7"]`. Time complexity: O(n), one pass. Space complexity: O(1) extra space, not counting the output list.

## 7. Gotchas & takeaways

> Gotcha: forgetting to add the final range after the loop ends drops the last group entirely — the loop only closes a range when it *sees* a break, so the very last range needs an explicit add after the loop.

- This is the simplest Merge Intervals problem: the "intervals" are implicit unit values rather than explicit `[start, end]` pairs, but the same "sorted input, single scan" idea applies.
- Related problems: Merge Intervals (explicit interval pairs instead of single numbers), Missing Ranges (the complement of this problem).
