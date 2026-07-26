---
card: leetcode-patterns
gi: 441
slug: maximum-profit-in-job-scheduling
title: Maximum Profit in Job Scheduling
---

## 1. What it is

Given `n` jobs, each with a start time, an end time, and a profit, choose a subset of NON-OVERLAPPING jobs to maximize total profit. Example: `startTime = [1,2,3,3]`, `endTime = [3,4,5,6]`, `profit = [50,10,40,70]` → `120` (jobs `0` and `3`: `50 + 70`).

## 2. Why & when

Use this shape whenever a problem asks you to select a MAXIMUM-VALUE, NON-OVERLAPPING subset of weighted intervals along a timeline. This is a sequential-decision state machine in disguise: sort jobs by end time, and at each job, the choice is binary — take it (and jump back to the LATEST job that finishes before it starts), or skip it.

## 3. Core concept

**Key idea:** sort all jobs by END time. Build `dp[i]` = the maximum profit achievable using only the first `i` jobs (in sorted order).

**Steps:**
1. Sort jobs by `endTime`.
2. `dp[0] = 0` (no jobs considered yet).
3. For each job `i` (1-indexed, `1` to `n`): find `p` = the number of EARLIER jobs (in the sorted order) whose end time is `<= ` this job's start time, using BINARY SEARCH on the sorted end times (since they are already sorted). `dp[i] = max(dp[i-1], profit[i] + dp[p])`.
4. The answer is `dp[n]`.

**Why sorting by end time enables binary search:** once jobs are sorted by end time, the question "which earlier jobs finish before job `i` starts" becomes a search for the RIGHTMOST position in a SORTED array of end times — exactly what binary search is built for. Without this sort, no such search would be valid, since "earlier in the input" would not correspond to "finishes earlier."

**Why the transition is correct:** for each job `i`, you either SKIP it (`dp[i-1]`, its profit already accounts for the best subset among the first `i-1` jobs) or TAKE it (`profit[i]` plus the best subset among jobs that are fully done before it starts, `dp[p]`). Taking the maximum of these two covers every possible decision for job `i`.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jobs sorted by end time with a binary search finding the latest job that ends before the current jobs start time">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">jobs sorted by end time -- binary search for latest non-overlapping job</text>
    <rect x="20" y="40" width="80" height="26" fill="#30363d" stroke="#8b949e"/><text x="60" y="58" text-anchor="middle" font-size="10">job A: ends 3</text>
    <rect x="150" y="40" width="80" height="26" fill="#3fb950"/><text x="190" y="58" text-anchor="middle" font-size="10" fill="#0d1117">job D: starts 3</text>
    <rect x="10" y="80" width="330" height="24" fill="#3fb950"/><text x="175" y="97" fill="#0d1117" text-anchor="middle" font-size="10">dp[i] = max(skip this job, take it + dp[latest compatible job])</text>
  </g>
</svg>

Binary search over sorted end times quickly locates the best earlier job compatible with the current one.

## 5. Runnable example

```java
// MaximumProfitInJobScheduling.java
import java.util.*;

public class MaximumProfitInJobScheduling {

    // KEY INSIGHT: sorting by end time turns "find compatible earlier
    // jobs" into a binary search, and dp[i] is a simple skip-or-take
    // choice, exactly like a two-state machine per job.

    static int jobScheduling(int[] startTime, int[] endTime, int[] profit) {
        int n = startTime.length;
        Integer[] idx = new Integer[n];
        for (int i = 0; i < n; i++) idx[i] = i;
        Arrays.sort(idx, (a, b) -> endTime[a] - endTime[b]);

        int[][] jobs = new int[n][3]; // start, end, profit -- sorted by end
        for (int i = 0; i < n; i++) {
            int j = idx[i];
            jobs[i] = new int[]{startTime[j], endTime[j], profit[j]};
        }

        int[] dp = new int[n + 1];
        for (int i = 1; i <= n; i++) {
            int start = jobs[i - 1][0];
            int lo = 0, hi = i - 1;
            while (lo < hi) {
                int mid = (lo + hi) / 2;
                if (jobs[mid][1] <= start) lo = mid + 1; else hi = mid;
            }
            dp[i] = Math.max(dp[i - 1], jobs[i - 1][2] + dp[lo]);
        }
        return dp[n];
    }

    public static void main(String[] args) {
        System.out.println(jobScheduling(new int[]{1, 2, 3, 3}, new int[]{3, 4, 5, 6}, new int[]{50, 10, 40, 70}));
        // 120
    }
}
```

**How to run:** `java MaximumProfitInJobScheduling.java`

## 6. Walkthrough

Trace `jobScheduling` for the example (sorted by end time, ties broken arbitrarily): jobs become `(1,3,50)`, `(2,4,10)`, `(3,5,40)`, `(3,6,70)`.

| i | job (start,end,profit) | compatible jobs before (binary search) | dp[i] |
|---|---|---|---|
| 1 | (1,3,50) | none (p=0) | max(0, 50+0)=50 |
| 2 | (2,4,10) | none end <= 2 (p=0) | max(50, 10+0)=50 |
| 3 | (3,5,40) | job 1 ends at 3 <= 3 (p=1) | max(50, 40+50)=90 |
| 4 | (3,6,70) | job 1 ends at 3 <= 3 (p=1) | max(90, 70+50)=120 |

`dp[4] = 120`, matching the expected answer (jobs `(1,3,50)` and `(3,6,70)`). Time complexity is O(n log n) (sorting, plus a binary search per job). Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: the binary search must find jobs with `end <= start` (a job ending EXACTLY when the next one starts is allowed to be compatible, since intervals are typically treated as non-overlapping at a shared endpoint) — using a strict `<` instead would incorrectly reject valid back-to-back scheduling.

- Sorting by END time (not start time) is what makes the binary search valid — this is the detail that turns an O(n^2) brute-force scan into an O(n log n) solution.
- The `dp[i] = max(skip, take)` choice at each job is structurally a two-state machine, just applied over SORTED JOBS instead of over calendar days.
- Related problems: Best Time to Buy and Sell Stock (also a sequential skip-or-take decision, but over a plain array of prices instead of a sorted list of weighted intervals).
