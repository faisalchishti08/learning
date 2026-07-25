---
card: leetcode-patterns
gi: 366
slug: student-attendance-record-ii
title: Student Attendance Record II
---

## 1. What it is

An attendance record of length `n` uses three characters: `'A'` (absent), `'L'` (late), `'P'` (present). A record is ELIGIBLE for a reward if it has FEWER than 2 `'A'`s total, and NEVER has 3 or more consecutive `'L'`s. Return the number of eligible records of length `n`, modulo `10^9 + 7`. Example: `n = 2` → `8`.

## 2. Why & when

This is a multi-axis linear DP: each day's choice depends on a SMALL amount of state carried from the previous day — how many absences have occurred so far (`0` or `1`, since `2` makes the record ineligible), and how many consecutive lates immediately precede today (`0`, `1`, or `2`, since `3` makes it ineligible). Use this shape whenever a problem counts sequences under a "running total capped at a small limit" rule PLUS a "consecutive-run capped at a small limit" rule.

## 3. Core concept

**Key idea:** build `dp[absences][lateStreak]` = number of eligible records so far, ending in that specific `(absences, lateStreak)` combination, and update all 6 combinations (`2` absence values times `3` streak values) for each day added.

**Steps:**
1. Initialize `dp[0][0] = 1` (zero days processed: one empty record, no absences, no late streak) and every other combination to `0`.
2. For each of the `n` days, compute a FRESH `next` table from the current `dp`, considering all three possible characters for the new day:
   - Add `'P'`: from `dp[a][l]`, contributes to `next[a][0]` (present resets the late streak).
   - Add `'A'` (only if `a == 0`): from `dp[a][l]`, contributes to `next[a+1][0]` (absence resets the late streak too, and increments the absence count).
   - Add `'L'` (only if `l < 2`): from `dp[a][l]`, contributes to `next[a][l+1]` (late extends the streak by one).
3. After `n` days, return the sum of `dp[a][l]` over all `a` in `{0,1}` and `l` in `{0,1,2}`, modulo `10^9 + 7`.

**Why it is correct:** every eligible record of length `i` is an eligible record of length `i-1` with exactly one more valid character appended, and "valid" depends ONLY on the current absence count and current late streak — not on which specific earlier days had which characters. Tracking just these two small numbers (instead of the full history) is enough because the eligibility rules themselves only ever look at these two aggregates.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="six state dp table for absences 0 or 1 and late streak 0 1 or 2 showing transitions for adding P A or L">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">state (absences=0, lateStreak=1); add a character:</text>
    <text x="10" y="45">'P' -&gt; next(0,0);  'A' -&gt; next(1,0);  'L' -&gt; next(0,2)</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="150" y="82" fill="#0d1117" text-anchor="middle" font-size="10">each old state feeds up to 3 new states</text>
  </g>
</svg>

Each of the 6 states branches into up to 3 next-day states, depending on which characters stay eligible.

## 5. Runnable example

```java
// StudentAttendanceRecordII.java
public class StudentAttendanceRecordII {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: track only the two aggregates the eligibility rule
    // actually cares about -- total absences (capped at the failing
    // value) and the current consecutive-late streak (capped at the
    // failing value) -- not the full day-by-day history.

    static int checkRecord(int n) {
        long[][] dp = new long[2][3];
        dp[0][0] = 1;

        for (int day = 0; day < n; day++) {
            long[][] next = new long[2][3];
            for (int a = 0; a < 2; a++) {
                for (int l = 0; l < 3; l++) {
                    long ways = dp[a][l];
                    if (ways == 0) continue;

                    next[a][0] = (next[a][0] + ways) % MOD; // add 'P'
                    if (a < 1) {
                        next[a + 1][0] = (next[a + 1][0] + ways) % MOD; // add 'A'
                    }
                    if (l < 2) {
                        next[a][l + 1] = (next[a][l + 1] + ways) % MOD; // add 'L'
                    }
                }
            }
            dp = next;
        }

        long total = 0;
        for (int a = 0; a < 2; a++) {
            for (int l = 0; l < 3; l++) {
                total = (total + dp[a][l]) % MOD;
            }
        }
        return (int) total;
    }

    public static void main(String[] args) {
        System.out.println(checkRecord(2));
        // 8
        System.out.println(checkRecord(1));
        // 3
    }
}
```

**How to run:** `java StudentAttendanceRecordII.java`

## 6. Walkthrough

Trace `checkRecord(1)`, one day, starting from `dp[0][0]=1`:

| new character | resulting state | count |
|---|---|---|
| 'P' | (0,0) | 1 |
| 'A' | (1,0) | 1 |
| 'L' | (0,1) | 1 |

Sum: `1+1+1 = 3`, matching the expected `3` (the records `"A"`, `"L"`, `"P"`). Time complexity is O(n) (each day updates a fixed 6-state table, constant work per day). Space is O(1) extra (fixed `2x3` tables).

## 7. Gotchas & takeaways

> Gotcha: computing `next` by updating `dp` IN PLACE (instead of building a fresh table) would let one day's newly-added transitions feed into the SAME day's other transitions, double-counting characters — always compute the full `next` table from the unmodified `dp`, then replace `dp` with `next` after the day is fully processed.

- Capping tracked state to only the values that matter for eligibility (`absences` capped at `2`, `lateStreak` capped at `3`) keeps the state space small and constant-size, regardless of `n`.
- Summing over ALL final states (not just `dp[0][0]`) is required here, since many different final `(absences, lateStreak)` combinations are all individually eligible.
- Related problems: House Robber (a simpler 2-state linear DP, without the extra absence-count axis), Number of Dice Rolls With Target Sum (a similar multi-axis DP, but summing to an exact target instead of counting all eligible states).
