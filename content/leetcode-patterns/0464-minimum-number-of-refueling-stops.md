---
card: leetcode-patterns
gi: 464
slug: minimum-number-of-refueling-stops
title: Minimum Number of Refueling Stops
---

## 1. What it is

A car starts with `startFuel` and must reach `target`, passing gas stations (each at a `distance` with some `fuel` amount) along the way. Return the MINIMUM number of refueling stops needed, or `-1` if it is impossible. Example: `target = 100`, `startFuel = 10`, `stations = [[10,60],[20,30],[30,30]]` → `2`.

## 2. Why & when

Use this shape whenever a problem lets you make a decision (here, whether to refuel) using options that only become available OVER TIME (as the car passes each station), and you want to MINIMIZE how many of those decisions you make. The greedy rule: drive as far as possible without committing to any specific refuel, and only refuel — using the LARGEST fuel option passed SO FAR — the moment you would otherwise get stuck.

## 3. Core concept

**Key idea:** use a MAX-HEAP to hold the fuel amounts of every station passed so far (but not yet necessarily used). Drive forward; whenever the current fuel runs out before reaching the target, pull the LARGEST available fuel amount from the heap (a stop you did not have to decide about in advance).

**Steps:**
1. Maintain a max-heap of "fuel amounts available to use," a running `fuel` level (starting at `startFuel`), a stop counter, and a pointer into the stations array (sorted by distance, or assumed pre-sorted).
2. While `fuel < target`: first, push the fuel amounts of every station whose DISTANCE is `<= ` the current `fuel` level into the heap (these stations are now "reachable," so their fuel becomes an option).
3. If the heap is empty at this point, no more options exist, but the target is not yet reached — return `-1`.
4. Otherwise, pop the LARGEST fuel amount from the heap, add it to `fuel`, and increment the stop counter.
5. Once `fuel >= target`, return the stop counter.

**Why delaying the refuel DECISION (but not the stop's availability) until it is NEEDED is correct:** you never know, while driving past an early station, whether a LATER station's fuel amount might be even better — so instead of deciding "should I stop here" AT that moment, you defer the choice, and once fuel is genuinely needed, you retroactively pick the BEST option among every station already passed. This is why a max-heap (not a running single "best so far" value) is required: multiple future emergencies might each need to pull from the SAME pool of already-passed stations, in a different order of size.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a max heap accumulating fuel options as stations become reachable with the largest option pulled only when the current fuel runs out">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">target=100, startFuel=10, stations=[[10,60],[20,30],[30,30]]</text>
    <text x="10" y="45">fuel=10: station at 10 reachable -- push 60 into heap; fuel(10) &lt; target -- pop 60, fuel=70</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">push 30,30 (both reachable) -- fuel=70 &lt; 100 -- pop 30, fuel=100 -- 2 stops</text>
  </g>
</svg>

Options accumulate in a max-heap as stations become reachable; only when fuel actually runs low is the best available option pulled.

## 5. Runnable example

```java
// MinimumNumberOfRefuelingStops.java
import java.util.Collections;
import java.util.PriorityQueue;

public class MinimumNumberOfRefuelingStops {

    // KEY INSIGHT: defer the refuel decision until fuel actually runs
    // low -- a max-heap of every station's fuel passed so far lets you
    // retroactively pick the BEST option, not just the first available one.

    static int minRefuelStops(int target, int startFuel, int[][] stations) {
        PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());
        int fuel = startFuel, stops = 0, i = 0, n = stations.length;

        while (fuel < target) {
            while (i < n && stations[i][0] <= fuel) {
                maxHeap.add(stations[i][1]);
                i++;
            }
            if (maxHeap.isEmpty()) return -1;
            fuel += maxHeap.poll();
            stops++;
        }
        return stops;
    }

    public static void main(String[] args) {
        System.out.println(minRefuelStops(100, 10, new int[][]{{10, 60}, {20, 30}, {30, 30}}));
        // 2
    }
}
```

**How to run:** `java MinimumNumberOfRefuelingStops.java`

## 6. Walkthrough

Trace `minRefuelStops(100, 10, [[10,60],[20,30],[30,30]])`:

| iteration | fuel before | stations pushed (distance <= fuel) | heap contents | fuel after pop | stops |
|---|---|---|---|---|---|
| 1 | 10 | station at 10 (fuel 60) | [60] | 10+60=70 | 1 |
| 2 | 70 | stations at 20, 30 (fuel 30, 30) | [30, 30] | 70+30=100 | 2 |

`fuel = 100 >= target`, so the loop ends, returning `stops = 2`, matching the expected answer. Time complexity is O(n log n) (each station is pushed to the heap at most once, each push/pop costing O(log n)). Space is O(n) for the heap.

## 7. Gotchas & takeaways

> Gotcha: pushing a station into the heap ONLY when its distance is `<= ` the CURRENT fuel level (not all stations up front) is essential — a station whose fuel would be great to use might not actually be REACHABLE yet, and using it before you have physically gotten there would be an invalid move.

- A max-heap for "every option passed so far, best one retrievable in O(log n)": the key structural choice, letting the decision of WHICH stop to use be delayed until it is actually needed.
- This differs from a simple greedy running-maximum (like Jump Game) because the "best option" here can only be used ONCE it is pulled from the heap — multiple refuels may be needed, each drawing from the same shared pool.
- Related problems: Eliminate Maximum Number of Monsters (a related "process options in the order they become urgent" greedy, but using a full sort instead of a dynamically growing heap), Maximum Number of Events That Can Be Attended II (a related "choose the best of several arriving options" problem, but one that needs DP, not a simple greedy heap, because of an added selection-count limit).
