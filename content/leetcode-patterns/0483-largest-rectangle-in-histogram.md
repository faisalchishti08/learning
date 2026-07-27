---
card: leetcode-patterns
gi: 483
slug: largest-rectangle-in-histogram
title: Largest Rectangle in Histogram
---

## 1. What it is

Given an array `heights` representing the bar heights of a histogram (each bar has width 1), find the area of the largest rectangle that fits entirely inside the histogram's outline. Example: `heights = [2, 1, 5, 6, 2, 3]` → `10` (the rectangle spans bars of height `5` and `6`, width `2`, area `10`).

## 2. Why & when

For every bar, the biggest rectangle that uses that bar as its shortest (limiting) height extends left and right until it hits a bar shorter than it. That is a "nearest strictly smaller element on both sides" question — the histogram problem is the flagship example in the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family. Constraints: up to 100,000 bars.

## 3. Core concept

**Key idea:** for each bar, find the nearest shorter bar to its left and the nearest shorter bar to its right (both using an increasing monotonic stack, similar to [Sum of Subarray Minimums](0474-sum-of-subarray-minimums.md)). The width of the rectangle where this bar is the limiting height is `rightBoundary - leftBoundary - 1`; the area is `height * width`. Take the maximum over every bar.

**Steps:**
1. Scan left to right with an increasing stack of indices. When the current bar is shorter than the stack's top, the top bar has just found its right boundary (the current index) — pop it and compute its rectangle area using the new top of the stack as its left boundary (or `-1` if the stack is empty).
2. Area for a popped bar at index `j`: `height[j] * (i - stack.peek() - 1)` where `i` is the current index (its right boundary) and `stack.peek()` is the index now on top (its left boundary), or `-1` if empty.
3. Push the current index.
4. After the scan, append a sentinel bar of height `0` (or repeat the pop logic for whatever remains on the stack), so every remaining bar gets popped and its area computed using `n` as its right boundary.
5. Track the maximum area seen across all pops.

**Why one pass resolves both boundaries:** a bar's *right* boundary is discovered the moment a shorter bar arrives (standard monotonic-stack pop). Its *left* boundary is exactly whatever remains on the stack at that moment — because the stack, kept increasing, always holds bars shorter than the one being popped, and the nearest one still on the stack is by construction the nearest shorter bar to the left.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Increasing stack resolving both left and right boundaries for each bar as it is popped">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">heights = [2, 1, 5, 6, 2, 3]</text>
    <rect x="20" y="120" width="30" height="40" fill="#161b22" stroke="#30363d"/>
    <rect x="50" y="140" width="30" height="20" fill="#161b22" stroke="#30363d"/>
    <rect x="80" y="20" width="30" height="140" fill="#161b22" stroke="#79c0ff"/>
    <rect x="110" y="0" width="30" height="160" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="100" width="30" height="60" fill="#161b22" stroke="#30363d"/>
    <rect x="170" y="80" width="30" height="80" fill="#161b22" stroke="#30363d"/>
    <text x="95" y="185" fill="#79c0ff" text-anchor="middle" font-size="11">bars of height 5,6</text>
    <text x="95" y="200" fill="#3fb950" text-anchor="middle" font-size="11">width 2, area 10 (the answer)</text>
  </g>
</svg>

The tallest rectangle spans the bars of height `5` and `6`, both at least `5` tall, giving width `2` and area `10`.

## 5. Runnable example

**Level 1 — Brute force.** For every pair of bars, expand a rectangle using the shorter one as the limiting height. O(n²).

**KEY INSIGHT:** an increasing monotonic stack resolves, for every bar, exactly the moment its left and right "shorter neighbor" boundaries become known — turning an O(n²) pairwise search into one O(n) pass.

**Level 2 — Optimal.** Single-pass increasing stack with a sentinel `0`-height bar appended, O(n).

**Level 3 — Hardened.** Handles a strictly increasing histogram (answer determined only at the sentinel pass) and a single bar.

```java
// LargestRectangleInHistogram.java
import java.util.*;

public class LargestRectangleInHistogram {

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] heights) {
        int maxArea = 0;
        for (int i = 0; i < heights.length; i++) {
            int minHeight = heights[i];
            for (int j = i; j < heights.length; j++) {
                minHeight = Math.min(minHeight, heights[j]);
                maxArea = Math.max(maxArea, minHeight * (j - i + 1));
            }
        }
        return maxArea;
    }

    // Level 2 & 3: increasing monotonic stack with a sentinel, O(n)
    static int largestRectangleArea(int[] heights) {
        Deque<Integer> stack = new ArrayDeque<>(); // increasing heights, holds indices
        int maxArea = 0;
        int n = heights.length;

        for (int i = 0; i <= n; i++) {
            int currentHeight = (i == n) ? 0 : heights[i]; // sentinel forces final pops
            while (!stack.isEmpty() && heights[stack.peek()] > currentHeight) {
                int height = heights[stack.pop()];
                int leftBoundary = stack.isEmpty() ? -1 : stack.peek();
                int width = i - leftBoundary - 1;
                maxArea = Math.max(maxArea, height * width);
            }
            stack.push(i);
        }
        return maxArea;
    }

    public static void main(String[] args) {
        int[] heights = {2, 1, 5, 6, 2, 3};
        System.out.println("brute force: " + bruteForce(heights));
        System.out.println("optimal:     " + largestRectangleArea(heights));

        System.out.println("increasing:  " + largestRectangleArea(new int[]{1, 2, 3, 4, 5}));
        System.out.println("single bar:  " + largestRectangleArea(new int[]{7}));
    }
}
```

**How to run:** save as `LargestRectangleInHistogram.java`, then run `java LargestRectangleInHistogram.java`.

## 6. Walkthrough

Trace `largestRectangleArea({2, 1, 5, 6, 2, 3})` (index `6` is the sentinel, height `0`):

| i | height | stack before | pops (height, leftBoundary, width, area) | stack after | maxArea |
|---|---|---|---|---|---|
| 0 | 2 | [] | none | [0] | 0 |
| 1 | 1 | [0] | pop 0: h=2, left=-1, width=1-(-1)-1=1, area=2 | [1] | 2 |
| 2 | 5 | [1] | none (1 not > 5) | [1,2] | 2 |
| 3 | 6 | [1,2] | none (5 not > 6) | [1,2,3] | 2 |
| 4 | 2 | [1,2,3] | pop 3: h=6, left=2, width=4-2-1=1, area=6. pop 2: h=5, left=1, width=4-1-1=2, area=10 | [1,4] | 10 |
| 5 | 3 | [1,4] | none (2 not > 3) | [1,4,5] | 10 |
| 6 (sentinel) | 0 | [1,4,5] | pop 5: h=3,left=4,width=6-4-1=1,area=3. pop 4: h=2,left=1,width=6-1-1=4,area=8. pop 1: h=1,left=-1,width=6-(-1)-1=6,area=6 | [] | 10 |

Maximum area found: `10`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: forgetting the sentinel `0`-height bar at the end leaves any bars still on the stack unresolved — their rectangles (using the array's end as the right boundary) never get computed.

- The width formula `i - leftBoundary - 1` counts exactly the bars strictly between the two shorter boundaries (exclusive on both ends).
- This is the foundation for [Maximal Rectangle](0484-maximal-rectangle.md), which reuses this exact function per row of a 2D grid.
- Time: O(n) — every index is pushed once and popped at most once, plus one extra sentinel iteration.
