---
card: leetcode-patterns
gi: 37
slug: max-consecutive-ones-iii
title: Max Consecutive Ones III
---

## 1. What it is

Given a binary array `nums` and an integer `k`, return the maximum number of consecutive `1`s you can get if you flip at most `k` zeroes to ones. Example: `nums = [1,1,1,0,0,0,1,1,1,1,0]`, `k = 2` → answer `6`, from flipping the two zeroes at indices 3 and 4 (or 9 and 10), extending a run of six consecutive ones.

## 2. Why & when

This is Longest Repeating Character Replacement with the alphabet fixed to just `{0, 1}` and the "target majority letter" fixed as `1`: the window is achievable exactly when the count of zeroes inside it is at most `k`.

## 3. Core concept

**Key idea:** a window is valid exactly when `zerosInWindow <= k`. Expand `right`; if the window has too many zeroes, shrink `left` until it is valid again.

**Steps:**
1. Set `left = 0`, `zeros = 0`, `best = 0`.
2. For each index `right` from 0 to `length - 1`:
   - If `nums[right] == 0`, increment `zeros`.
   - While `zeros > k`: if `nums[left] == 0`, decrement `zeros`; then `left++`.
   - Update `best = max(best, right - left + 1)`.
3. Return `best`.

**Why it is correct:** every zero in the window represents one flip needed; the window is achievable precisely when the number of flips needed does not exceed the budget `k`. Shrinking from the left only when `zeros > k` guarantees the window always represents a *feasible* flip plan, and tracking the max length across every valid state finds the longest one.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max consecutive ones sliding window counting zeroes">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [1,1,1,0,0,0,1,1,1,1,0], k = 2</text>
    <rect x="140" y="40" width="30" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="170" y="40" width="30" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="200" y="40" width="30" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="155" y="60" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="185" y="60" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="215" y="60" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="20" y="95" fill="#8b949e">window includes zeroes at index 3,4: zeros=2 &lt;= k -&gt; valid, keep expanding right</text>
    <text x="20" y="118" fill="#8b949e">right hits index 5 (third zero): zeros=3 &gt; k -&gt; shrink left until zeros=2 again</text>
  </g>
</svg>

The window tracks a running count of zeroes; it shrinks only when that count exceeds the flip budget `k`.

## 5. Runnable example

```java
// MaxConsecutiveOnesIII.java
public class MaxConsecutiveOnesIII {

    // Level 1 -- Brute force: for every window start, expand right while
    // counting zeroes from scratch, checking the budget. O(n^2) time,
    // O(1) space.
    static int bruteForce(int[] nums, int k) {
        int best = 0;
        for (int i = 0; i < nums.length; i++) {
            int zeros = 0;
            for (int j = i; j < nums.length; j++) {
                if (nums[j] == 0) zeros++;
                if (zeros > k) break;
                best = Math.max(best, j - i + 1);
            }
        }
        return best;
    }

    // KEY INSIGHT: tracking a running zero count and shrinking only when
    // it exceeds k turns the "at most k flips" condition into a single
    // linear sliding-window scan.

    // Level 2 -- Optimal: sliding window counting zeroes. O(n) time,
    // O(1) space.
    public static int longestOnes(int[] nums, int k) {
        int left = 0, zeros = 0, best = 0;
        for (int right = 0; right < nums.length; right++) {
            if (nums[right] == 0) zeros++;
            while (zeros > k) {
                if (nums[left] == 0) zeros--;
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: k >= number of zeroes in the whole array means
    // the entire array becomes one valid window, since the shrink
    // condition never triggers.
    static int hardened(int[] nums, int k) {
        if (nums == null || k < 0) throw new IllegalArgumentException("invalid input");
        return longestOnes(nums, k);
    }

    public static void main(String[] args) {
        int[] nums = {1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0};
        System.out.println("brute force: " + bruteForce(nums, 2));
        System.out.println("optimal:     " + longestOnes(nums, 2));
        System.out.println("k covers all zeroes: " + hardened(nums, 4));
    }
}
```

How to run: save as `MaxConsecutiveOnesIII.java`, then run `java MaxConsecutiveOnesIII.java`.

## 6. Walkthrough

Dry run of `longestOnes({1,1,1,0,0,0,1,1,1,1,0}, k = 2)`, focused on the window that produces the answer:

| right | nums[right] | zeros | window [left,right] | length |
|---|---|---|---|---|
| 4 | 0 | 2 | [0,4] | 5 |
| 5 | 0 | 3 (over budget) | shrinks to [4,5] | 2 |
| 6 | 1 | 2 | [4,6] | 3 |
| 7 | 1 | 2 | [4,7] | 4 |
| 8 | 1 | 2 | [4,8] | 5 |
| 9 | 1 | 2 | [4,9] | 6 |
| 10 | 0 | 3 (over budget) | shrinks to [5,10] | 6 |

At `right = 5`, `zeros` hits `3`, exceeding `k = 2`, so `left` advances from `0` to `4`, dropping the three `1`s and the zero at index 3 until only the zero at index 4 remains (`zeros = 2`). The window `[4, 9]` then grows undisturbed to length `6`, the best seen. At `right = 10` another zero pushes the count over budget again, but the resulting window can only reach length `6`, not beating the existing best. Final answer: `6`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: decrementing `zeros` unconditionally when shrinking (instead of only when `nums[left] == 0`) undercounts the zeroes still in the window, since not every character leaving the window on the left is necessarily a zero.

- Recognize this as Longest Repeating Character Replacement specialized to a binary alphabet with a fixed target letter (`1`) — the same "window length minus majority count" reasoning applies, simplified to "window length minus ones count = zeros count."
- Related problems: Max Consecutive Ones, Max Consecutive Ones II, Longest Repeating Character Replacement.
