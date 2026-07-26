---
card: leetcode-patterns
gi: 465
slug: maximum-number-of-events-that-can-be-attended-ii
title: Maximum Number of Events That Can Be Attended II
---

## 1. What it is

Given events, each `[startDay, endDay, value]`, and a maximum of `k` events you may attend (no two attended events may overlap), return the MAXIMUM total value achievable. Example: `events = [[1,2,4],[3,4,3],[2,3,1]]`, `k = 2` → `7` (attend events with values `4` and `3`).

## 2. Why & when

This problem LOOKS like it belongs with the other greedy problems in this section (it involves choosing non-overlapping intervals, like Job Scheduling), but it actually needs a DIFFERENT tool: DYNAMIC PROGRAMMING, not a pure greedy commitment. The reason: a simple "always take the best available event" rule can fail here, because taking a high-value event NOW might block a BETTER combination of two or more events later, and the LIMIT on how many events you may attend (`k`) means you must weigh combinations, not just commit greedily one event at a time.

## 3. Core concept

**Key idea:** sort events by END day. Build `dp[i][j]` = the maximum value achievable using events among the first `i` (sorted) events, attending AT MOST `j` of them.

**Steps:**
1. Sort events by `endDay`.
2. For each event `i` (1-indexed, `1` to `n`), find `p` = the count of EARLIER events (by sorted order) whose end day is STRICTLY LESS than event `i`'s start day, using BINARY SEARCH (the same technique as Job Scheduling).
3. For each `j` from `1` to `k`: `dp[i][j] = max(dp[i-1][j], value[i] + dp[p][j-1])` — either skip event `i` (carry forward `dp[i-1][j]`), or take it (add its value to the best achievable using `j-1` MORE events among the compatible earlier ones).
4. The answer is `dp[n][k]`.

**Why this needs the FULL `dp[i][j]` table, not a greedy shortcut:** the decision "should I attend this event" cannot be made in isolation — it depends on how many attendance SLOTS remain (`j`) and what the BEST combination of REMAINING events looks like, which a single "value" or "end time" comparison cannot capture. Unlike Job Scheduling (this section's greedy-DP-adjacent problem, but with UNLIMITED attendances), the `k` LIMIT here forces you to compare across DIFFERENT possible counts of remaining events, which is exactly what the extra `j` dimension in the DP table exists to resolve.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a two dimensional table indexed by event count and remaining attendance slots contrasted with a pure greedy single choice">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">dp[i][j] = max(skip event i, take event i + dp[compatible earlier][j-1])</text>
    <rect x="10" y="40" width="330" height="24" fill="#3fb950"/><text x="175" y="57" fill="#0d1117" text-anchor="middle" font-size="10">a full 2D table is needed -- NOT a single greedy running value</text>
    <text x="10" y="80">unlike Job Scheduling's unlimited-attendance dp[i], this needs the extra "j slots remaining" dimension</text>
  </g>
</svg>

The limit on attendance count forces a two-dimensional DP table, unlike the single-dimension greedy-adjacent Job Scheduling problem.

## 5. Runnable example

```java
// MaximumNumberOfEventsThatCanBeAttendedII.java
import java.util.Arrays;

public class MaximumNumberOfEventsThatCanBeAttendedII {

    // KEY INSIGHT: unlike Job Scheduling (unlimited attendances), the
    // cap of k events forces a genuine dp[i][j] table -- a greedy
    // single choice per event is not enough here.

    static int maxValue(int[][] events, int k) {
        int n = events.length;
        Arrays.sort(events, (a, b) -> a[1] - b[1]); // sort by end day
        int[] end = new int[n];
        for (int i = 0; i < n; i++) end[i] = events[i][1];

        int[][] dp = new int[n + 1][k + 1];
        for (int i = 1; i <= n; i++) {
            int start = events[i - 1][0];
            int lo = 0, hi = i - 1;
            while (lo < hi) {
                int mid = (lo + hi) / 2;
                if (end[mid] < start) lo = mid + 1; else hi = mid;
            }
            int p = lo; // count of compatible earlier events
            for (int j = 1; j <= k; j++) {
                dp[i][j] = Math.max(dp[i - 1][j], events[i - 1][2] + dp[p][j - 1]);
            }
        }
        return dp[n][k];
    }

    public static void main(String[] args) {
        System.out.println(maxValue(new int[][]{{1, 2, 4}, {3, 4, 3}, {2, 3, 1}}, 2));
        // 7
    }
}
```

**How to run:** `java MaximumNumberOfEventsThatCanBeAttendedII.java`

## 6. Walkthrough

Trace for `events = [[1,2,4],[3,4,3],[2,3,1]]`, `k=2` (sorted by end day: `[1,2,4]`, `[2,3,1]`, `[3,4,3]`):

| i | event (start,end,value) | compatible earlier count (p) | dp[i][1] | dp[i][2] |
|---|---|---|---|---|
| 1 | (1,2,4) | 0 | max(0, 4+dp[0][0])=4 | max(0, 4+dp[0][1])=4 |
| 2 | (2,3,1) | 0 (end 2 not &lt; start 2) | max(4, 1+0)=4 | max(4, 1+0)=4 |
| 3 | (3,4,3) | 2 (events 1,2 both end &lt; 3) | max(4, 3+dp[2][0])=4 | max(4, 3+dp[2][1])=max(4,3+4)=7 |

`dp[3][2] = 7`, matching the expected answer: attend event `(1,2,4)` and event `(3,4,3)`, total value `4 + 3 = 7`. Time complexity is O(n log n · k) (sorting, plus a binary search and O(k) work per event). Space is O(n·k).

## 7. Gotchas & takeaways

> Gotcha: reaching for a pure greedy "always take the highest-value compatible event" rule (the way Job Scheduling greedily builds `dp[i]` with no attendance limit) FAILS here — the `k` cap means sometimes SKIPPING a high-value event is correct, if it frees up a slot for a BETTER pair of smaller events later; only comparing across the FULL `dp[i][j]` table catches this.

- This problem is intentionally placed alongside this section's true greedy problems as a CONTRAST: recognizing when a "greedy-looking" interval problem actually needs DP (because of an added count LIMIT) is as important a skill as recognizing when greedy genuinely applies.
- The binary search for compatible earlier events is identical to Job Scheduling's technique — only the transition (adding a `j` dimension) changes.
- Related problems: Maximum Profit in Job Scheduling (the unlimited-attendance version, solvable with a single-dimension `dp[i]`, no `k` needed), Best Time to Buy and Sell Stock IV (a different problem with a similar "add a count-limit dimension to an otherwise simpler DP" structure).
