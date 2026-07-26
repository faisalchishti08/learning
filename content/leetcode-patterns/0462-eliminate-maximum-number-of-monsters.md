---
card: leetcode-patterns
gi: 462
slug: eliminate-maximum-number-of-monsters
title: Eliminate Maximum Number of Monsters
---

## 1. What it is

Monsters approach a city, each at a given `distance` and `speed`. You have a weapon that can eliminate exactly ONE monster per MINUTE. If any monster REACHES the city (distance `0`) before you eliminate it, you lose. Return the MAXIMUM number of monsters you can eliminate before losing (or all of them, if you can survive). Example: `dist = [1,3,4]`, `speed = [1,1,1]` → `3`.

## 2. Why & when

Use this shape whenever a problem gives a set of "deadlines" (here, each monster's arrival time) and a fixed processing RATE (one elimination per minute), asking how many deadlines can be met. The greedy rule: compute every monster's ARRIVAL TIME, sort them ascending, and process (eliminate) them in that order — the monster arriving SOONEST is always the most urgent one to handle first.

## 3. Core concept

**Key idea:** compute each monster's arrival time as `distance / speed`. Sort these arrival times ascending. Process monsters in this order, one per minute; the moment a monster's arrival time is LESS THAN OR EQUAL TO the CURRENT minute (meaning it reaches the city before or exactly when you would get to it), you lose.

**Steps:**
1. Compute `arrival[i] = dist[i] / speed[i]` for every monster (as a floating-point value, to correctly capture "arrives partway through a minute").
2. Sort `arrival` ascending.
3. For `minute` from `0` to `n-1`: if `arrival[minute] <= minute`, this monster (the SOONEST-arriving one still unhandled) reaches the city before you can eliminate it — stop and return `minute` (the count eliminated so far).
4. If the loop completes without failing, return `n` (every monster eliminated).

**Why processing the SOONEST-arriving monster first is correct:** eliminating monsters in any OTHER order can only make things WORSE — delaying the most urgent (soonest-arriving) monster to handle a later one first risks that urgent monster reaching the city while you were busy elsewhere, whereas handling it FIRST (as soon as possible) gives every monster the best possible chance of being reached in time. This is a direct application of "always resolve the most urgent deadline first."

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="monsters sorted by arrival time processed one per minute failing the moment a sorted arrival time is not later than the current minute">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">dist = [1,3,4], speed = [1,1,1] -- arrival times: [1, 3, 4] (already sorted)</text>
    <text x="10" y="45">minute 0: arrival[0]=1 &gt; 0 -- eliminate; minute 1: arrival[1]=3 &gt; 1 -- eliminate</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">minute 2: arrival[2]=4 &gt; 2 -- eliminate; all 3 survived</text>
  </g>
</svg>

Processing monsters in order of soonest arrival gives every one the best possible chance of being eliminated in time.

## 5. Runnable example

```java
// EliminateMaximumNumberOfMonsters.java
import java.util.Arrays;

public class EliminateMaximumNumberOfMonsters {

    // KEY INSIGHT: eliminate the SOONEST-arriving monster first --
    // handling any other order first only risks the most urgent
    // monster reaching the city while you were busy elsewhere.

    static int eliminateMaximum(int[] dist, int[] speed) {
        int n = dist.length;
        double[] arrival = new double[n];
        for (int i = 0; i < n; i++) arrival[i] = (double) dist[i] / speed[i];
        Arrays.sort(arrival);

        for (int minute = 0; minute < n; minute++) {
            if (arrival[minute] <= minute) return minute;
        }
        return n;
    }

    public static void main(String[] args) {
        System.out.println(eliminateMaximum(new int[]{1, 3, 4}, new int[]{1, 1, 1}));
        // 3
        System.out.println(eliminateMaximum(new int[]{3, 2, 4}, new int[]{5, 3, 2}));
        // 1
    }
}
```

**How to run:** `java EliminateMaximumNumberOfMonsters.java`

## 6. Walkthrough

Trace `eliminateMaximum([3,2,4], [5,3,2])` (arrival times: `3/5=0.6`, `2/3=0.667`, `4/2=2.0`; sorted ascending: `[0.6, 0.667, 2.0]`):

| minute | arrival[minute] | arrival <= minute? | action |
|---|---|---|---|
| 0 | 0.6 | 0.6 <= 0? no | eliminate this monster |
| 1 | 0.667 | 0.667 <= 1? YES | this monster reaches the city first — lose |

The function returns `1`, matching the expected answer: only one monster (the fastest arrival, at minute `0`) could be eliminated before a second monster's arrival time caught up. Time complexity is O(n log n) (dominated by the sort). Space is O(n) for the arrival array.

## 7. Gotchas & takeaways

> Gotcha: using INTEGER division for `dist[i] / speed[i]` instead of floating-point division can silently produce the WRONG answer — a monster arriving at `2/3 ≈ 0.667` minutes is a real, urgent threat well before minute `1`, but integer division would round it down to `0`, misrepresenting how soon it actually arrives.

- Computing arrival times, sorting them ascending, and checking each against its OWN position in that order: the exact same shape as any "process deadlines in order of urgency" greedy problem.
- The check `arrival[minute] <= minute` (not `<`) correctly treats a monster arriving EXACTLY when you would get to it as too late, since you eliminate at most one monster PER minute, and this one reaches the city AT that minute mark.
- Related problems: Gas Station (a different feasibility greedy, tracking a running balance rather than sorted deadlines), Minimum Number of Refueling Stops (also processes items greedily as they become relevant, but uses a max-heap instead of a full sort, since options accumulate dynamically over the journey).
