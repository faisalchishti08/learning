---
card: leetcode-patterns
gi: 478
slug: car-fleet
title: Car Fleet
---

## 1. What it is

`n` cars drive toward the same destination on a one-lane road. Each car has a `position` and a `speed`. A car that catches up to a slower car ahead cannot pass it — it slows down and joins that car's "fleet," traveling together at the slower speed from then on. Return the number of distinct fleets that arrive at the destination. Example: `target = 12`, `position = [10, 8, 0, 5, 3]`, `speed = [2, 4, 1, 1, 3]` → `3`.

## 2. Why & when

Sort the cars by position, then process them from the one **closest to the target** backward. Whether a car catches the fleet ahead depends only on comparing its arrival time to the time of the fleet directly in front of it — this "does the next one behind me ever catch up" question is exactly the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) shape, using a stack of arrival times instead of raw values. Constraints: up to 100,000 cars, all positions distinct.

## 3. Core concept

**Key idea:** compute each car's arrival time at `target` as `(target - position) / speed`. Sort cars by position descending (closest to target first). Scan in that order, keeping a stack of arrival times of confirmed fleet leaders. A car merges into the fleet ahead of it if its own arrival time is **less than or equal to** that fleet's time (it would arrive at the same time or sooner, so it is forced to slow down and join); otherwise it becomes a new fleet leader.

**Steps:**
1. Pair each car's `(position, speed)`, compute `time = (target - position) / speed` as a double.
2. Sort cars by `position` in descending order.
3. Maintain a stack of arrival times, representing confirmed fleet leaders processed so far (closest-to-target first).
4. For each car in order: if the stack is empty, or this car's time is strictly greater than the time on top of the stack, push its time (it is a new, slower fleet that never catches the one ahead).
5. Otherwise (this car's time is less than or equal to the top), it catches up to and merges into that fleet — do not push anything new.
6. The final stack size is the number of fleets.

**Why "greater than" (not "greater than or equal to") keeps a new fleet separate:** if a car's time strictly exceeds the fleet ahead, it arrives later and never physically reaches that fleet before the destination, so it must be traveling as its own, slower fleet.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cars processed closest-to-target first, merging into the fleet ahead when their arrival time does not exceed it">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">target=12, positions=[10,8,0,5,3], speeds=[2,4,1,1,3]</text>
    <text x="20" y="45" fill="#8b949e">sorted by position desc: (10,2)t=1.0, (8,4)t=1.0, (5,1)t=7.0, (3,3)t=3.0, (0,1)t=12.0</text>
    <text x="20" y="70" fill="#8b949e">(10,2) t=1.0: stack empty, push. fleets=[1.0]</text>
    <text x="20" y="90" fill="#8b949e">(8,4) t=1.0: 1.0 not &gt; 1.0 -&gt; merges into fleet ahead. fleets=[1.0]</text>
    <text x="20" y="110" fill="#8b949e">(5,1) t=7.0: 7.0 &gt; 1.0 -&gt; new fleet. fleets=[1.0, 7.0]</text>
    <text x="20" y="130" fill="#8b949e">(3,3) t=3.0: 3.0 not &gt; 7.0 -&gt; merges. fleets=[1.0, 7.0]</text>
    <text x="20" y="150" fill="#3fb950">(0,1) t=12.0: 12.0 &gt; 7.0 -&gt; new fleet. total fleets = 3</text>
  </g>
</svg>

Each car either merges into the fleet directly ahead (same or earlier arrival) or becomes a new, slower fleet of its own.

## 5. Runnable example

**Level 1 — Brute force.** Simulate every car's position over tiny time steps and check for merges. Imprecise and far too slow for large inputs.

**KEY INSIGHT:** once cars are ordered by position, whether a car merges depends only on comparing its own arrival time to the nearest fleet ahead — a single backward-to-forward scan with a stack of "confirmed fleet" times resolves every car in O(n log n) (dominated by the sort).

**Level 2 — Optimal.** Sort by position, scan closest-to-target first, monotonic stack of arrival times.

**Level 3 — Hardened.** Handles cars that start already at the same position-order tie broken by input, and a single car (always one fleet).

```java
// CarFleet.java
import java.util.*;

public class CarFleet {

    // Level 2 & 3: sort + monotonic stack of arrival times, O(n log n)
    static int carFleet(int target, int[] position, int[] speed) {
        int n = position.length;
        Integer[] indices = new Integer[n];
        for (int i = 0; i < n; i++) indices[i] = i;

        Arrays.sort(indices, (a, b) -> position[b] - position[a]); // closest to target first

        Deque<Double> stack = new ArrayDeque<>();
        for (int idx : indices) {
            double time = (double) (target - position[idx]) / speed[idx];
            if (stack.isEmpty() || time > stack.peek()) {
                stack.push(time); // strictly slower than the fleet ahead -> new fleet
            }
            // else: time <= stack.peek(), this car catches up and merges, push nothing
        }
        return stack.size();
    }

    public static void main(String[] args) {
        System.out.println(carFleet(12, new int[]{10, 8, 0, 5, 3}, new int[]{2, 4, 1, 1, 3})); // 3
        System.out.println(carFleet(10, new int[]{3}, new int[]{3}));                          // 1
        System.out.println(carFleet(100, new int[]{0, 2, 4}, new int[]{4, 2, 1}));             // 1
    }
}
```

**How to run:** save as `CarFleet.java`, then run `java CarFleet.java`.

## 6. Walkthrough

Trace `carFleet(12, [10,8,0,5,3], [2,4,1,1,3])`. Arrival times: index 0 (pos 10, speed 2) → `1.0`; index 1 (pos 8, speed 4) → `1.0`; index 2 (pos 0, speed 1) → `12.0`; index 3 (pos 5, speed 1) → `7.0`; index 4 (pos 3, speed 3) → `3.0`. Sorted by position descending: indices `[0, 1, 3, 4, 2]` (positions `10, 8, 5, 3, 0`).

| car (pos, time) | stack before | comparison | action | stack after |
|---|---|---|---|---|
| (10, 1.0) | [] | stack empty | push 1.0 | [1.0] |
| (8, 1.0) | [1.0] | `1.0 > 1.0`? no | merge, no push | [1.0] |
| (5, 7.0) | [1.0] | `7.0 > 1.0`? yes | push 7.0 | [1.0, 7.0] |
| (3, 3.0) | [1.0, 7.0] | `3.0 > 7.0`? no | merge, no push | [1.0, 7.0] |
| (0, 12.0) | [1.0, 7.0] | `12.0 > 7.0`? yes | push 12.0 | [1.0, 7.0, 12.0] |

Final stack size: `3`, matching the expected number of fleets.

## 7. Gotchas & takeaways

> Gotcha: sorting by speed or by array index instead of by position gives meaningless comparisons — the merge rule only makes sense when cars are processed in the order they will physically reach the destination, closest first.

- The "does this car ever catch the one ahead" question depends only on the immediately preceding (closer-to-target) fleet, which is exactly what a stack tracks.
- A car merges (no push) when its time is less than or equal to the fleet ahead; it becomes a new fleet leader (push) only when strictly slower.
- Time: O(n log n), dominated by the sort; the scan itself is O(n).
