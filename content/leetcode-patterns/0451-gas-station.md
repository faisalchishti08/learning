---
card: leetcode-patterns
gi: 451
slug: gas-station
title: Gas Station
---

## 1. What it is

There are `n` gas stations in a circle, each with `gas[i]` fuel and a cost `cost[i]` to travel from station `i` to the next. Starting at some station with an empty tank, find the ONE starting station that lets you complete the full circuit, or return `-1` if none exists (the starting station is guaranteed unique if one exists). Example: `gas = [1,2,3,4,5]`, `cost = [3,4,5,1,2]` → `3`.

## 2. Why & when

Use this shape whenever a problem asks for a FEASIBLE starting point in a circular sequence, based on a running BALANCE that must never go negative. The greedy rule: track a cumulative tank balance as you scan; the moment it goes negative, NONE of the stations tried so far (including the current one) can be a valid start — restart the candidate from the very next station.

## 3. Core concept

**Key idea:** track two running values: `total` (the sum of `gas[i] - cost[i]` over the WHOLE circuit, which determines overall FEASIBILITY) and `tank` (the running balance since the current CANDIDATE starting station).

**Steps:**
1. Initialize `total = 0`, `tank = 0`, `start = 0`.
2. For each station `i`: let `diff = gas[i] - cost[i]`. Add `diff` to both `total` and `tank`.
3. If `tank` drops BELOW `0`, no station from `start` through `i` (inclusive) can be a valid starting point — set `start = i + 1`, and reset `tank = 0`.
4. After the full scan, if `total >= 0`, return `start` (the answer is guaranteed valid); otherwise return `-1` (no starting point exists anywhere).

**Why resetting the candidate to `i + 1` (not just `i`) is correct:** if the tank goes negative arriving at station `i`, that means NO station between the current `start` and `i` (inclusive) could have completed the trip TO `i` — including station `i` itself, since anything starting there would inherit exactly the same deficit accumulated by stations before it (a formal exchange argument: for any station `j` strictly between `start` and `i`, the balance starting from `j` is `tank` minus the (non-negative, by construction) prefix sum up to `j`, which is still negative by the time it reaches `i`). This is exactly why jumping the candidate straight to `i + 1`, skipping every station in between, never misses a possible answer.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a running tank balance dropping below zero at some station causing the candidate start to reset to the very next station">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">gas = [1,2,3,4,5]; cost = [3,4,5,1,2]; diffs = [-2,-2,-2,3,3]</text>
    <text x="10" y="45">tank after each station: -2 (reset, start=1), -2 (reset, start=2), -2 (reset, start=3), 3, 6</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">total = 3 &gt;= 0, so start=3 is the valid answer</text>
  </g>
</svg>

Every time the running tank goes negative, the candidate start jumps straight past the station that caused the deficit.

## 5. Runnable example

```java
// GasStation.java
public class GasStation {

    // KEY INSIGHT: whenever the running tank goes negative, no station
    // scanned so far -- including the one that just failed -- can be
    // the answer, so the candidate start jumps to the very next one.

    static int canCompleteCircuit(int[] gas, int[] cost) {
        int total = 0, tank = 0, start = 0;
        for (int i = 0; i < gas.length; i++) {
            int diff = gas[i] - cost[i];
            total += diff;
            tank += diff;
            if (tank < 0) {
                start = i + 1;
                tank = 0;
            }
        }
        return total >= 0 ? start : -1;
    }

    public static void main(String[] args) {
        System.out.println(canCompleteCircuit(new int[]{1, 2, 3, 4, 5}, new int[]{3, 4, 5, 1, 2}));
        // 3
        System.out.println(canCompleteCircuit(new int[]{2, 3, 4}, new int[]{3, 4, 3}));
        // -1
    }
}
```

**How to run:** `java GasStation.java`

## 6. Walkthrough

Trace `canCompleteCircuit([1,2,3,4,5], [3,4,5,1,2])`:

| i | diff | tank before | tank after | reset? | start after |
|---|---|---|---|---|---|
| 0 | -2 | 0 | -2 | yes | 1 |
| 1 | -2 | 0 | -2 | yes | 2 |
| 2 | -2 | 0 | -2 | yes | 3 |
| 3 | 3 | 0 | 3 | no | 3 |
| 4 | 3 | 3 | 6 | no | 3 |

`total = -2-2-2+3+3 = 0`, which is `>= 0`, so `start = 3` is returned, matching the expected answer. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: the algorithm returns a station index EVEN IF `total < 0` unless you explicitly check `total >= 0` at the end — always guard the final return with the total-feasibility check, since a `start` value can be computed even when NO valid starting point actually exists anywhere in the circuit.

- Two running values (`total` for overall feasibility, `tank` for the current candidate) working together: `total` answers "does an answer exist at all," while `tank`'s resets find WHERE it is.
- Resetting the candidate to `i + 1` (skipping every station between the old and new candidate) is the specific exchange argument that makes this an O(n) single pass instead of an O(n^2) "try every starting station" brute force.
- Related problems: Jump Game and Jump Game II (also single-pass greedy over a running value, but tracking a farthest-reach index instead of a cumulative balance).
