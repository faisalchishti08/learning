---
card: leetcode-patterns
gi: 202
slug: single-threaded-cpu
title: Single-Threaded CPU
---

## 1. What it is

Given `tasks` where `tasks[i] = [enqueueTimei, processingTimei]`, a single-threaded CPU processes one task at a time. When idle, it picks the AVAILABLE task (enqueue time already passed) with the shortest processing time, breaking ties by the smallest original index. Return the order in which tasks are processed. Example: `tasks = [[1,2],[2,4],[3,2],[4,1]]` → `[0,2,3,1]`.

## 2. Why & when

Two competing orders are at play: tasks become AVAILABLE in order of enqueue time, but among available tasks, the CPU picks by shortest processing time. This "become available over time, then greedily pick the best of what's available" shape is a two-structure pattern: sort by enqueue time to know what's available, and use a min-heap ordered by processing time to pick the next task to run.

## 3. Core concept

**Key idea:** sort tasks by enqueue time so you can advance a pointer through them as time passes. Maintain a min-heap of `[processingTime, originalIndex]` for tasks that have become available but not yet run. At each step, if no task is available yet, jump the clock forward to the next task's enqueue time; otherwise, pop the heap's shortest-processing-time task, run it, and advance the clock by its duration.

**Steps:**
1. Sort tasks by `enqueueTime`, keeping track of each task's original index.
2. Use a pointer to track which sorted tasks have been added to the heap so far, and a `currentTime` variable starting at the first task's enqueue time.
3. Loop until all tasks are processed: add every task whose `enqueueTime <= currentTime` to the min-heap (ordered by processing time, tie-broken by original index).
4. If the heap is empty (no task available yet), jump `currentTime` forward to the next unprocessed task's enqueue time.
5. Otherwise, pop the heap's top, append its index to the result, and advance `currentTime` by its processing time.
6. Repeat until every task has been processed.

**Why it is correct:** the CPU is defined to always pick the shortest available task, so tracking "currently available tasks" via a min-heap by processing time directly mirrors the rule. Advancing the clock exactly to the next task's enqueue time when idle (rather than any smaller step) is safe because no task becomes available in between, so nothing is missed by skipping ahead.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tasks enter a min-heap as they become available; CPU always picks the shortest available task">
  <g font-family="sans-serif" font-size="12">
    <line x1="20" y1="100" x2="440" y2="100" stroke="#8b949e"/>
    <circle cx="60" cy="100" r="4" fill="#3fb950"/><text x="60" y="90" fill="#e6edf3" text-anchor="middle">t=1</text>
    <circle cx="140" cy="100" r="4" fill="#79c0ff"/><text x="140" y="90" fill="#e6edf3" text-anchor="middle">t=2</text>
    <circle cx="220" cy="100" r="4" fill="#e3b341"/><text x="220" y="90" fill="#e6edf3" text-anchor="middle">t=3</text>
    <text x="10" y="140" fill="#e6edf3">as clock advances, newly available tasks enter the min-heap; CPU always pulls the shortest one</text>
  </g>
</svg>

Tasks join the min-heap as their enqueue time passes; the CPU always processes whichever available task has the shortest duration.

## 5. Runnable example

```java
// SingleThreadedCPU.java
import java.util.*;

public class SingleThreadedCPU {

    // Level 1 -- Brute force: at each time step, linearly scan ALL
    // tasks to find the shortest AVAILABLE, not-yet-processed one.
    // Correct, but re-scanning every task at every decision point is
    // O(n) per pick, O(n^2) total, instead of O(log n) per pick.

    // KEY INSIGHT: maintain a MIN-HEAP of just the currently available
    // tasks, ordered by processing time -- this turns "find the
    // shortest available task" from an O(n) scan into an O(log n) heap
    // operation.

    // Level 2 -- Optimal: sorted enqueue order + min-heap of available
    // tasks.
    static int[] getOrder(int[][] tasks) {
        int n = tasks.length;
        Integer[] order = new Integer[n];
        for (int i = 0; i < n; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> tasks[a][0] - tasks[b][0]);

        PriorityQueue<int[]> available = new PriorityQueue<>(
            (a, b) -> a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]
        );

        int[] result = new int[n];
        int resultIdx = 0, taskPtr = 0;
        long currentTime = tasks[order[0]][0];

        while (resultIdx < n) {
            while (taskPtr < n && tasks[order[taskPtr]][0] <= currentTime) {
                int idx = order[taskPtr];
                available.add(new int[]{tasks[idx][1], idx});
                taskPtr++;
            }
            if (available.isEmpty()) {
                currentTime = tasks[order[taskPtr]][0];
                continue;
            }
            int[] next = available.poll();
            result[resultIdx++] = next[1];
            currentTime += next[0];
        }
        return result;
    }

    // Level 3 -- Hardened: `currentTime` uses `long` to avoid overflow
    // when processing times accumulate across many large tasks, and
    // the empty-heap check correctly jumps the clock forward instead
    // of looping forever when there is a gap with no available task.

    public static void main(String[] args) {
        System.out.println(Arrays.toString(getOrder(new int[][]{{1,2},{2,4},{3,2},{4,1}}))); // [0, 2, 3, 1]
        System.out.println(Arrays.toString(getOrder(new int[][]{{7,10},{7,12},{7,5},{7,4},{7,2}}))); // [4, 3, 2, 0, 1]
    }
}
```

**How to run:** `java SingleThreadedCPU.java`

## 6. Walkthrough

Trace `tasks = [[1,2],[2,4],[3,2],[4,1]]`, sorted by enqueue time (already in order 0,1,2,3):

| currentTime | Tasks added to heap | Heap top popped | New currentTime |
|---|---|---|---|
| 1 | task0 [2,idx0] available | pop [2,0] | 1+2=3 |
| 3 | task1 [4,idx1], task2 [2,idx2] available (enqueue <= 3) | pop [2,2] (shorter than 4) | 3+2=5 |
| 5 | task3 [1,idx3] available | pop [1,3] (shorter than 4) | 5+1=6 |
| 6 | (task1 still in heap) | pop [4,1] | 6+4=10 |

Result order: `[0, 2, 3, 1]`, matching the expected output. Time complexity is O(n log n), for sorting plus each task's single heap push/pop; space is O(n) for the heap and order array.

## 7. Gotchas & takeaways

> Gotcha: forgetting to jump `currentTime` forward when the heap is EMPTY (no task available yet) causes an infinite loop, since the inner `while` adding tasks never finds anything new to add at a `currentTime` that never advances.

- Advance the clock to exactly the NEXT unprocessed task's enqueue time when idle — not by an arbitrary or fixed step — since nothing becomes available before that point.
- The tie-break (smallest original index for equal processing times) must be built into the heap's comparator, or ties will be resolved arbitrarily by the `PriorityQueue`'s internal implementation.
- Related problems: Process Tasks Using Servers (similar two-structure availability pattern with two heaps instead of one), Furthest Building You Can Reach (single heap greedy, different domain).
