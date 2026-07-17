---
card: leetcode-patterns
gi: 46
slug: longest-turbulent-subarray
title: Longest Turbulent Subarray
---

## 1. What it is

Given an integer array `arr`, a subarray is "turbulent" if the comparison sign between consecutive elements alternates: greater, then less, then greater, then less, and so on (or the reverse pattern). Return the length of the longest turbulent subarray. Example: `arr = [9, 4, 2, 10, 7, 8, 8, 1, 9]` → answer `5`, from `[4, 2, 10, 7, 8]`.

## 2. Why & when

Turbulence is a condition on *consecutive pairs*, not on the window's aggregate content — it breaks the moment two consecutive comparisons have the same direction (or are equal). That makes this a sliding window where the shrink decision depends on comparing the newest element to the one before it, not on a running sum or count.

## 3. Core concept

**Key idea:** track the comparison sign between the two most recently added elements. As long as the new comparison alternates from the previous one, the window keeps growing; the moment it does not alternate (same direction twice in a row, or an equal pair), the window must restart — but not entirely from scratch, since a plateau of length 2 is always still valid on its own.

**Steps:**
1. Set `left = 0`, `best = 1` (a single element is trivially turbulent, length 1).
2. For each index `right` from 1 to `length - 1`:
   - Compare `arr[right]` to `arr[right - 1]`.
   - If they are equal, the turbulence breaks completely — set `left = right` (restart the window at this element).
   - Else if this comparison's direction is the same as the previous comparison's direction (both "greater" or both "less"), the window must shrink to just the last pair — set `left = right - 1`.
   - Otherwise, the comparison correctly alternates — the window keeps growing, no `left` change needed.
   - Update `best = max(best, right - left + 1)`.
3. Return `best`.

**Why it is correct:** turbulence is a strictly local, pairwise property — checking only the two most recent comparisons is enough, because if the last two comparisons alternate correctly, and all comparisons before that were already verified to alternate (by induction from earlier steps), the whole window remains turbulent. Restarting at the right point (either `right` for an equal pair, or `right - 1` for a repeated direction) is the minimal shrink that keeps the window valid without losing any usable elements.

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Longest turbulent subarray alternating comparison directions">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">arr = [9, 4, 2, 10, 7, 8, 8, 1, 9]</text>
    <polyline points="20,100 60,130 100,150 140,50 180,90 220,70 260,70 300,150 340,50" fill="none" stroke="#8b949e" stroke-width="2"/>
    <text x="20" y="140" fill="#79c0ff">9&gt;4 (down), 4&gt;2 (down again) -&gt; same direction twice, shrink to the last pair</text>
    <text x="220" y="30" fill="#f0883e">8==8 -&gt; equal pair breaks turbulence entirely, restart at that index</text>
  </g>
</svg>

Each new comparison's direction must differ from the previous one; a repeat or a tie forces the window to shrink to the minimal still-valid suffix.

## 5. Runnable example

```java
// LongestTurbulentSubarray.java
public class LongestTurbulentSubarray {

    // Level 1 -- Brute force: for every starting index, extend as far as
    // the alternating condition holds, re-verifying from scratch. O(n^2)
    // time, O(1) space.
    static int bruteForce(int[] arr) {
        int best = 1;
        for (int i = 0; i < arr.length; i++) {
            int j = i;
            Integer prevSign = null;
            while (j + 1 < arr.length) {
                int diff = arr[j + 1] - arr[j];
                if (diff == 0) break;
                int sign = diff > 0 ? 1 : -1;
                if (prevSign != null && sign == prevSign) break;
                prevSign = sign;
                j++;
            }
            best = Math.max(best, j - i + 1);
        }
        return best;
    }

    // KEY INSIGHT: turbulence only depends on the two most recent
    // comparisons, so a single forward pass can track just the previous
    // comparison's direction and adjust the window's left edge in O(1)
    // per step, instead of re-verifying from each start.

    // Level 2 -- Optimal: one pass, tracking previous comparison sign.
    // O(n) time, O(1) space.
    public static int maxTurbulenceSize(int[] arr) {
        int left = 0, best = 1;
        for (int right = 1; right < arr.length; right++) {
            int cmp = Integer.compare(arr[right], arr[right - 1]);
            if (cmp == 0) {
                left = right;
            } else if (right >= 2 && cmp == Integer.compare(arr[right - 1], arr[right - 2])) {
                left = right - 1;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: a single-element array skips the loop entirely,
    // correctly returning the initial best of 1; a strictly monotonic
    // array never alternates, so the window keeps resetting to size 2.
    static int hardened(int[] arr) {
        if (arr == null || arr.length == 0) return 0;
        return maxTurbulenceSize(arr);
    }

    public static void main(String[] args) {
        int[] arr = {9, 4, 2, 10, 7, 8, 8, 1, 9};
        System.out.println("brute force: " + bruteForce(arr));
        System.out.println("optimal:     " + maxTurbulenceSize(arr));
        System.out.println("single elem: " + hardened(new int[] {5}));
    }
}
```

How to run: save as `LongestTurbulentSubarray.java`, then run `java LongestTurbulentSubarray.java`.

## 6. Walkthrough

Dry run of `maxTurbulenceSize({9, 4, 2, 10, 7, 8, 8, 1, 9})`:

| right | comparison | previous comparison | action | left | best |
|---|---|---|---|---|---|
| 1 | 4<9 (down) | none | first comparison, keep | 0 | 2 |
| 2 | 2<4 (down) | down | same direction -> left=1 | 1 | 2 |
| 3 | 10>2 (up) | down | alternates, keep | 1 | 3 |
| 4 | 7<10 (down) | up | alternates, keep | 1 | 4 |
| 5 | 8>7 (up) | down | alternates, keep | 1 | 5 |
| 6 | 8==8 (equal) | — | tie breaks entirely -> left=6 | 6 | 5 |
| 7 | 1<8 (down) | none (restarted) | keep | 6 | 2 |
| 8 | 9>1 (up) | down | alternates, keep | 6 | 3 |

Final best: `5`, from the window `[1, 5]` = `[4, 2, 10, 7, 8]`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: treating an equal pair (`cmp == 0`) the same as a repeated-direction pair is wrong — an equal pair breaks turbulence completely (restart at `right`), while a repeated direction only needs to discard the earlier of the two comparisons (restart at `right - 1`, keeping the pair itself as a valid length-2 window).

- This is a "local pairwise condition" sliding window — a different flavor from sum-based or count-based windows, but the same overall shape: track just enough state to decide, in O(1), whether the window is still valid.
- Related problems: Longest Mountain in Array (a related local-comparison pattern), Wiggle Subsequence.
