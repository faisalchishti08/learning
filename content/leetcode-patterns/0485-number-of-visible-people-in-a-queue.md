---
card: leetcode-patterns
gi: 485
slug: number-of-visible-people-in-a-queue
title: Number of Visible People in a Queue
---

## 1. What it is

You get an array `heights` of distinct people standing in a queue, all facing the front. Person `i` can see person `j` (where `j > i`) if everyone standing between them is shorter than **both** of them. For each person, count how many people they can see to their right. Example: `heights = [10, 6, 8, 5, 11, 9]` → `[3, 1, 2, 1, 1, 0]`.

## 2. Why & when

This is another simulation-style problem answered by the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family: scanning from the right with a decreasing stack, each person "sees" every shorter person popped off the stack, plus possibly one taller person that finally blocks their view. Constraints: up to 100,000 people, all heights distinct.

## 3. Core concept

**Key idea:** scan right to left, keeping a decreasing stack of heights (people not yet blocked from view by someone taller further right). For each person, pop every shorter person off the stack — the current person can see each one of them (nothing taller stands between, since they were already removed as "visible-and-shorter"). After popping all shorter people, if the stack is not empty, the current person can also see that one taller (or equal, but heights are distinct so strictly taller) person before their view is blocked — count that as one more visible person.

**Steps:**
1. Maintain a decreasing stack of heights, scanning from the last person to the first.
2. For each person `i`: initialize `count = 0`.
3. While the stack is not empty and its top is less than `heights[i]`, pop it and increment `count` (this shorter person is visible).
4. If the stack is not empty after the pops, increment `count` once more (the remaining taller person is also visible — they block the view of anyone beyond them, but are themselves visible).
5. Push `heights[i]` onto the stack.
6. `result[i] = count`.

**Why the one extra taller person still counts as visible:** the rule says person `i` can see person `j` if everyone *between* them is shorter than both — a taller person `j` blocking the view satisfies "everyone between `i` and `j` is shorter than both" vacuously if `j` is the very next taller-or-equal person, so `j` itself is visible even though `j` then blocks everyone beyond.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Right to left scan counting visible shorter people plus one blocking taller person">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">heights = [10, 6, 8, 5, 11, 9] (scan right to left)</text>
    <text x="20" y="45" fill="#8b949e">9: stack empty, count=0. push 9. stack=[9]</text>
    <text x="20" y="65" fill="#8b949e">11: pop 9 (9&lt;11), count=1. stack empty, no extra. push 11. stack=[11]</text>
    <text x="20" y="85" fill="#8b949e">5: 11 not &lt; 5, count=0. stack not empty -&gt; count=1 (sees 11). push 5. stack=[11,5]</text>
    <text x="20" y="105" fill="#8b949e">8: pop 5 (5&lt;8), count=1. stack has 11 left -&gt; count=2 (sees 11 too). push 8. stack=[11,8]</text>
    <text x="20" y="130" fill="#8b949e">6: 8 not &lt; 6, count=0. stack not empty -&gt; count=1 (sees 8). push 6. stack=[11,8,6]</text>
    <text x="20" y="155" fill="#3fb950">10: pop 6,8 (both&lt;10), count=2. stack has 11 left -&gt; count=3. result=[3,1,2,1,1,0]</text>
  </g>
</svg>

Every popped shorter person is visible; one remaining taller person, if any, is visible too, right before it blocks the rest.

## 5. Runnable example

**Level 1 — Brute force.** For each person, scan right, tracking the tallest person seen so far, counting visible people until the view is blocked. O(n²).

**KEY INSIGHT:** scanning from the right with a decreasing stack, every person a new arrival pops off is visible to it, and exactly one more (the person who finally blocks it, if any) is also visible.

**Level 2 — Optimal.** Right-to-left decreasing stack, O(n).

**Level 3 — Hardened.** Handles the tallest person overall (sees everyone shorter until the end, `count` grows large) and a strictly increasing-from-left queue.

```java
// NumberOfVisiblePeopleInAQueue.java
import java.util.*;

public class NumberOfVisiblePeopleInAQueue {

    // Level 1: brute force, O(n^2)
    static int[] bruteForce(int[] heights) {
        int n = heights.length;
        int[] result = new int[n];
        for (int i = 0; i < n; i++) {
            int tallestSoFar = -1;
            for (int j = i + 1; j < n; j++) {
                if (heights[j] > tallestSoFar) {
                    result[i]++;
                    tallestSoFar = heights[j];
                }
                if (heights[j] > heights[i]) break;
            }
        }
        return result;
    }

    // Level 2 & 3: right-to-left decreasing stack, O(n)
    static int[] canSeePersonsCount(int[] heights) {
        int n = heights.length;
        int[] result = new int[n];
        Deque<Integer> stack = new ArrayDeque<>(); // decreasing heights

        for (int i = n - 1; i >= 0; i--) {
            int count = 0;
            while (!stack.isEmpty() && stack.peek() < heights[i]) {
                stack.pop();
                count++;
            }
            if (!stack.isEmpty()) {
                count++; // the remaining taller person is also visible, right before blocking
            }
            result[i] = count;
            stack.push(heights[i]);
        }
        return result;
    }

    public static void main(String[] args) {
        int[] heights = {10, 6, 8, 5, 11, 9};
        System.out.println("brute force: " + Arrays.toString(bruteForce(heights)));
        System.out.println("optimal:     " + Arrays.toString(canSeePersonsCount(heights)));

        int[] increasing = {1, 2, 3, 4};
        System.out.println("increasing: " + Arrays.toString(canSeePersonsCount(increasing)));
    }
}
```

**How to run:** save as `NumberOfVisiblePeopleInAQueue.java`, then run `java NumberOfVisiblePeopleInAQueue.java`.

## 6. Walkthrough

Trace `canSeePersonsCount({10, 6, 8, 5, 11, 9})`, scanning `i = 5` down to `0`:

| i | height | stack before | pops (count) | extra taller visible? | result[i] | stack after |
|---|---|---|---|---|---|---|
| 5 | 9 | [] | 0 | no (stack empty) | 0 | [9] |
| 4 | 11 | [9] | pop 9 (1) | no (stack empty after) | 1 | [11] |
| 3 | 5 | [11] | 0 (11 not < 5) | yes (+1) | 1 | [11, 5] |
| 2 | 8 | [11, 5] | pop 5 (1) | yes, sees 11 (+1) | 2 | [11, 8] |
| 1 | 6 | [11, 8] | 0 (8 not < 6) | yes (+1) | 1 | [11, 8, 6] |
| 0 | 10 | [11, 8, 6] | pop 6, pop 8 (2) | yes, sees 11 (+1) | 3 | [11, 10]* |

*Note: pushing continues after each step; the final `result`, read from index 0 to 5, is `[3, 1, 2, 1, 1, 0]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: forgetting the "+1 for the remaining taller person" step undercounts every position that has a taller person somewhere to its right — that blocking person is still visible, only the people beyond them are not.

- Scanning right to left with a decreasing stack directly encodes "who is visible before something taller blocks the view."
- Every popped person is visible (shorter, no obstruction); at most one more (taller) person is visible right after.
- Time: O(n) — the usual amortized push/pop bound for any monotonic-stack pattern.
