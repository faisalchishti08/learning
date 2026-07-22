---
card: leetcode-patterns
gi: 201
slug: maximum-average-pass-ratio
title: Maximum Average Pass Ratio
---

## 1. What it is

Given `classes`, where `classes[i] = [passi, totali]` (students currently passing / total students), and `extraStudents` guaranteed-to-pass students to distribute, maximize the AVERAGE pass ratio across all classes by choosing where to add each extra student. Example: `classes = [[1,2],[3,5]]`, `extraStudents = 2` → `0.675` (both extra students go to the first class: `1/2 → 2/3 → 3/4`, giving an average of `(0.75 + 0.6) / 2`).

## 2. Why & when

Each extra student added to a class increases that class's pass ratio by an amount that depends on the class's CURRENT ratio — the gain is largest for classes where a marginal student helps the most, which is not always the class with the lowest ratio. A max-heap ordered by "gain from adding one more student" lets you always pick the single best next placement, one at a time.

## 3. Core concept

**Key idea:** compute, for every class, how much its ratio would IMPROVE from adding one more passing student: `gain = (pass+1)/(total+1) - pass/total`. Push every class into a max-heap ordered by this gain. Repeatedly pop the class with the highest gain, add one student to it (update `pass` and `total`), recompute ITS new gain, and push it back — repeat `extraStudents` times.

**Steps:**
1. For each class, compute its current gain from one more passing student, and push `[gain, pass, total]` into a max-heap.
2. Pop the class with the highest gain.
3. Increment both `pass` and `total` by 1 (add the extra student, who is guaranteed to pass).
4. Recompute this class's NEW gain (using the updated `pass`/`total`), and push it back into the heap.
5. Repeat steps 2–4 for each of the `extraStudents` students.
6. After all students are placed, compute the average of `pass/total` across all classes.

**Why it is correct:** the marginal gain of adding one student to a class DECREASES as more students are added to it (diminishing returns), so always picking the currently-highest-gain class for the NEXT student is a valid greedy strategy — exchanging a placement with any other choice at any step could only be equal or worse for the sum of ratios, since the heap always offers the single largest available improvement at that moment.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max-heap of per-class marginal gain; always add the next student to the currently highest-gain class">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="90" height="30" fill="#3fb950"/><text x="65" y="50" fill="#0d1117" text-anchor="middle">gain=0.17</text>
    <rect x="20" y="70" width="70" height="30" fill="#161b22" stroke="#30363d"/><text x="55" y="90" fill="#e6edf3" text-anchor="middle">gain=0.08</text>
    <text x="130" y="50" fill="#e6edf3">pop highest, add student, recompute, push back</text>
    <text x="10" y="15" fill="#e6edf3">the class with the biggest marginal gain gets the next extra student</text>
  </g>
</svg>

The max-heap always exposes whichever class currently benefits most from one more passing student.

## 5. Runnable example

```java
// MaximumAveragePassRatio.java
import java.util.*;

public class MaximumAveragePassRatio {

    // Level 1 -- Brute force: try every way to distribute
    // extraStudents students across classes (a combinatorial search),
    // computing the resulting average for each distribution and taking
    // the best. Correct, but combinatorially explosive -- there are far
    // too many distributions to try directly.

    // KEY INSIGHT: greedily place ONE student at a time onto whichever
    // class currently has the HIGHEST marginal gain -- a max-heap
    // makes finding that class, and updating it after the placement,
    // an O(log n) operation instead of a full re-scan.

    // Level 2 -- Optimal: max-heap of marginal gain, greedy one-at-a-
    // time placement.
    static double maxAverageRatio(int[][] classes, int extraStudents) {
        PriorityQueue<double[]> heap = new PriorityQueue<>(
            (a, b) -> Double.compare(gain(b[0], b[1]), gain(a[0], a[1]))
        );
        for (int[] c : classes) heap.add(new double[]{c[0], c[1]});

        for (int i = 0; i < extraStudents; i++) {
            double[] top = heap.poll();
            double pass = top[0] + 1, total = top[1] + 1;
            heap.add(new double[]{pass, total});
        }

        double sum = 0;
        for (double[] c : heap) sum += c[0] / c[1];
        return sum / classes.length;
    }

    static double gain(double pass, double total) {
        return (pass + 1) / (total + 1) - pass / total;
    }

    // Level 3 -- Hardened: storing pass/total as `double` (not `int`)
    // in the heap elements avoids integer division bugs when computing
    // gain and the final ratio.

    public static void main(String[] args) {
        System.out.printf("%.5f%n", maxAverageRatio(new int[][]{{1,2},{3,5}}, 2)); // 0.67500
        System.out.printf("%.5f%n", maxAverageRatio(new int[][]{{2,4},{3,9},{4,5},{2,10}}, 4)); // 0.53485
    }
}
```

**How to run:** `java MaximumAveragePassRatio.java`

## 6. Walkthrough

Trace `classes = [[1,2],[3,5]]`, `extraStudents = 2`:

| Step | Class states | gain(class0)=gain(1,2) | gain(class1)=gain(3,5) | Pick |
|---|---|---|---|---|
| start | [1,2], [3,5] | (2/3 - 1/2) = 0.167 | (4/6 - 3/5) = 0.067 | class0 higher |
| 1 | pop [1,2], push [2,3] | new gain(2,3) = (3/4 - 2/3) = 0.083 | 0.067 | class0 (0.083) still higher |
| 2 | pop [2,3], push [3,4] | — | — | done, 2 students placed |

Final heap: `{[3,4], [3,5]}`. Average = `(3/4 + 3/5) / 2 = (0.75 + 0.6) / 2 = 0.675`, matching the expected result. Time complexity is O((n + extraStudents) log n), for the initial heap build plus each of the `extraStudents` pop/push cycles; space is O(n) for the heap.

## 7. Gotchas & takeaways

> Gotcha: comparing raw ratios (`pass/total`) instead of MARGINAL GAIN when deciding where to place the next student is a common but incorrect greedy — the class with the lowest current ratio is not always the one that benefits most from one more student (a small class near 0% can gain more per student than a huge class near 50%).

- Use `double` arithmetic throughout — integer division in `pass/total` silently truncates and corrupts both the gain formula and the final average.
- The heap must be re-pushed with the UPDATED `[pass, total]` after each placement, not the original values — this is what lets diminishing returns correctly steer later placements to other classes once one class's gain drops enough.
- Related problems: Furthest Building You Can Reach (greedy heap-based resource allocation), IPO (max-heap greedy selection under a different constraint).
