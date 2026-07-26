---
card: leetcode-patterns
gi: 460
slug: two-city-scheduling
title: Two City Scheduling
---

## 1. What it is

`2n` people must be split into two EQUAL-SIZED groups: `n` fly to city A, `n` fly to city B. Person `i` costs `costs[i][0]` to fly to A, or `costs[i][1]` to fly to B. Return the MINIMUM total cost. Example: `costs = [[10,20],[30,200],[400,50],[30,20]]` → `110`.

## 2. Why & when

Use this shape whenever a problem splits items into two EQUAL groups to minimize a total cost, where each item has a DIFFERENT cost depending on which group it joins. The greedy rule: sort people by how much CHEAPER city A is versus city B (the DIFFERENCE `costs[i][0] - costs[i][1]`), then send the first half (biggest savings from choosing A) to A, and the rest to B.

## 3. Core concept

**Key idea:** for each person, compute `costs[i][0] - costs[i][1]` — a NEGATIVE value means A is cheaper (and by how much); a POSITIVE value means B is cheaper. Sort people by this difference, ASCENDING.

**Steps:**
1. Sort the `costs` array by `costs[i][0] - costs[i][1]`, ascending (most A-favoring first).
2. Send the FIRST `n` people (in this sorted order) to city A, paying their `costs[i][0]`.
3. Send the REMAINING `n` people to city B, paying their `costs[i][1]`.
4. Sum all the chosen costs for the total.

**Why sorting by the DIFFERENCE (not by either raw cost alone) is correct:** the DECISION that matters for each person is not "how expensive is A" or "how expensive is B" in isolation, but how much is SAVED by choosing A over B specifically. Assigning the `n` people with the BIGGEST A-savings to A, and letting everyone else go to B, minimizes the TOTAL cost — swapping any single assignment between these two groups would only ever increase the total, since it would either give up a large savings opportunity or take on a needlessly expensive one (this is the exchange argument: any alternative valid split can be transformed into this one through a sequence of swaps that never increases cost).

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="people sorted by how much cheaper city a is versus city b with the first half assigned to a and the rest to b">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">costs[i][0] - costs[i][1], sorted ascending (most A-favoring first)</text>
    <rect x="20" y="40" width="140" height="26" fill="#3fb950"/><text x="90" y="58" text-anchor="middle" font-size="10" fill="#0d1117">first n: send to A</text>
    <rect x="180" y="40" width="140" height="26" fill="#30363d" stroke="#8b949e"/><text x="250" y="58" text-anchor="middle" font-size="10">last n: send to B</text>
    <rect x="10" y="80" width="330" height="24" fill="#3fb950"/><text x="175" y="97" fill="#0d1117" text-anchor="middle" font-size="10">the DIFFERENCE, not either raw cost, is what should be sorted</text>
  </g>
</svg>

Sorting by the savings of choosing A over B (not either raw cost alone) is what makes the split provably optimal.

## 5. Runnable example

```java
// TwoCityScheduling.java
import java.util.Arrays;

public class TwoCityScheduling {

    // KEY INSIGHT: sort by the DIFFERENCE (A cost minus B cost), not
    // either raw cost alone -- the biggest A-savings go to A, and
    // everyone else goes to B.

    static int twoCitySchedCost(int[][] costs) {
        Arrays.sort(costs, (a, b) -> (a[0] - a[1]) - (b[0] - b[1]));
        int n = costs.length / 2;
        int total = 0;
        for (int i = 0; i < costs.length; i++) {
            total += (i < n) ? costs[i][0] : costs[i][1];
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(twoCitySchedCost(new int[][]{{10, 20}, {30, 200}, {400, 50}, {30, 20}}));
        // 110
    }
}
```

**How to run:** `java TwoCityScheduling.java`

## 6. Walkthrough

Trace `twoCitySchedCost([[10,20],[30,200],[400,50],[30,20]])` (differences: `10-20=-10`, `30-200=-170`, `400-50=350`, `30-20=10`; sorted ascending: `[30,200]` (-170), `[10,20]` (-10), `[30,20]` (10), `[400,50]` (350)):

| position | person | assigned city | cost |
|---|---|---|---|
| 0 (first n=2) | [30,200] | A | 30 |
| 1 (first n=2) | [10,20] | A | 10 |
| 2 (last n=2) | [30,20] | B | 20 |
| 3 (last n=2) | [400,50] | B | 50 |

Total `= 30 + 10 + 20 + 50 = 110`, matching the expected answer. Time complexity is O(n log n) (dominated by the sort). Space is O(1) beyond the sort's own space.

## 7. Gotchas & takeaways

> Gotcha: sorting by `costs[i][0]` alone (city A's raw cost) instead of the DIFFERENCE is a common but incorrect simplification — a person with a moderately cheap A cost but an EVEN CHEAPER B cost should still go to B, which only the difference-based sort correctly captures.

- Sorting by the per-person DIFFERENCE, then splitting the sorted list exactly in half: the entire greedy insight for this two-group equal-split cost problem.
- The exchange argument here relies on the group sizes being FIXED and EQUAL (`n` each) — a version of this problem with flexible group sizes would need a different approach entirely.
- Related problems: Advantage Shuffle (a different matching-based greedy — comparing against a target array rather than splitting into two fixed-size groups), Assign Cookies (also a sort-then-match greedy, but for a maximization-of-matches goal rather than a total-cost minimization).
