---
card: leetcode-patterns
gi: 456
slug: wiggle-subsequence
title: Wiggle Subsequence
---

## 1. What it is

A WIGGLE sequence alternates strictly between rising and falling: each difference between consecutive elements switches sign. Given an array, return the length of its LONGEST wiggle subsequence (elements chosen in order, not necessarily contiguous). Example: `nums = [1,7,4,9,2,5]` → `6` (the whole array already wiggles).

## 2. Why & when

Use this shape whenever a problem asks for the longest subsequence that ALTERNATES between two opposite conditions (rising/falling, greater/smaller). The greedy rule: track two running counts, `up` (the longest wiggle subsequence ending on a RISE) and `down` (ending on a FALL), and update whichever one applies as you scan once, left to right.

## 3. Core concept

**Key idea:** track `up` and `down`, both starting at `1` (a single element is trivially a wiggle sequence of length `1`, with no direction committed yet).

**Steps:**
1. For each `i` from `1` to `n-1`: if `nums[i] > nums[i-1]` (a rise), set `up = down + 1` (extending the LONGEST FALL-ending sequence found so far with this new rise).
2. If `nums[i] < nums[i-1]` (a fall), set `down = up + 1` (extending the LONGEST RISE-ending sequence found so far with this new fall).
3. If `nums[i] == nums[i-1]` (no change), do nothing — a flat step cannot extend either sequence.
4. The answer is `max(up, down)` after the scan.

**Why extending `down` (not `up`) on a rise is correct:** a NEW rise can only validly extend a subsequence that PREVIOUSLY ended on a FALL (since a wiggle must alternate) — so the best possible sequence ending on this rise is the best FALL-ending sequence, plus one. `up` itself is not updated based on its OWN previous value, since two rises in a row cannot both be kept in a valid wiggle subsequence (only the LATER, more useful one is worth keeping, which this transition automatically achieves).

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a rise extending the best fall ending sequence and a fall extending the best rise ending sequence each incrementing by one">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1, 7, 4, 9, 2, 5]</text>
    <text x="10" y="45">1-&gt;7 rise: up=down+1=2; 7-&gt;4 fall: down=up+1=3; 4-&gt;9 rise: up=down+1=4</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">continues alternating -- final max(up,down) = 6</text>
  </g>
</svg>

Each rise extends the best fall-ending count, and each fall extends the best rise-ending count, by exactly one.

## 5. Runnable example

```java
// WiggleSubsequence.java
public class WiggleSubsequence {

    // KEY INSIGHT: a rise can only validly extend a sequence that
    // previously ended on a fall (and vice versa) -- track both
    // running counts and update only the one that applies.

    static int wiggleMaxLength(int[] nums) {
        if (nums.length < 2) return nums.length;
        int up = 1, down = 1;
        for (int i = 1; i < nums.length; i++) {
            if (nums[i] > nums[i - 1]) {
                up = down + 1;
            } else if (nums[i] < nums[i - 1]) {
                down = up + 1;
            }
        }
        return Math.max(up, down);
    }

    public static void main(String[] args) {
        System.out.println(wiggleMaxLength(new int[]{1, 7, 4, 9, 2, 5}));
        // 6
        System.out.println(wiggleMaxLength(new int[]{1, 17, 5, 10, 13, 15, 10, 5, 16, 8}));
        // 7
    }
}
```

**How to run:** `java WiggleSubsequence.java`

## 6. Walkthrough

Trace `wiggleMaxLength([1,7,4,9,2,5])`:

| i | nums[i-1] -> nums[i] | direction | up | down |
|---|---|---|---|---|
| 1 | 1 -> 7 | rise | 2 | 1 |
| 2 | 7 -> 4 | fall | 2 | 3 |
| 3 | 4 -> 9 | rise | 4 | 3 |
| 4 | 9 -> 2 | fall | 4 | 5 |
| 5 | 2 -> 5 | rise | 6 | 5 |

Final `max(up=6, down=5) = 6`, matching the expected answer. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: a FLAT step (`nums[i] == nums[i-1]`) must leave BOTH `up` and `down` unchanged — a run of equal values only counts as ONE usable element in the wiggle subsequence, so incrementing anything on a flat step would overcount.

- Two running counts, each updated ONLY when its opposite direction just occurred: the core insight that avoids needing an explicit DP array or full subsequence enumeration.
- This achieves the same result as a full `dp[i]` table (one entry per index, tracking best-ending-in-rise / best-ending-in-fall), but collapses it to two rolling variables, since each index only ever needs the immediately preceding values.
- Related problems: Non-decreasing Array (a different single-pass property check, focused on a single allowed violation rather than counting alternations), Best Time to Buy and Sell Stock II (a related "count profitable direction changes" idea, applied to summing price gains instead of counting alternation length).
