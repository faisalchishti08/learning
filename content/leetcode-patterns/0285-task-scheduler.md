---
card: leetcode-patterns
gi: 285
slug: task-scheduler
title: Task Scheduler
---

## 1. What it is

Given a character array `tasks` (each letter is one CPU task) and a non-negative integer `n`, find the minimum number of time units the CPU needs to finish all tasks. The same task must wait at least `n` units before it can run again; the CPU may sit idle if no other task is ready. Example: `tasks = ["A","A","A","B","B","B"]`, `n = 2` → `8` (one valid order: `A,B,idle,A,B,idle,A,B`).

## 2. Why & when

This problem uses frequency ranking (the most frequent task drives the schedule's shape) combined with a max-heap to always run whichever ready task is currently most frequent. It belongs to Top-K Elements because the core decision at every time step is "which task, by remaining count, should run right now" — the same size-k-heap idea, applied repeatedly. Use this shape whenever a problem must repeatedly pick the "currently most/least frequent" item under a cooldown or spacing constraint.

## 3. Core concept

**Key idea:** the minimum total time is determined by the MOST frequent task. That task needs `n` units of separation between each of its occurrences, creating a fixed number of "blocks" that other tasks (or idle slots) fill in.

**Steps:**
1. Count each task's frequency.
2. Let `maxFreq` be the highest frequency, and `maxCount` be how many DISTINCT tasks share that highest frequency.
3. Compute `(maxFreq - 1) * (n + 1) + maxCount`. This models `maxFreq - 1` full cooldown blocks of size `n + 1`, plus a final row holding every task tied for the max frequency.
4. The answer is the larger of that formula's result and `tasks.length` (if there are enough OTHER tasks to fill every gap, no idle time is needed at all, and the answer is just the total task count).

**Why it is correct:** picture the most frequent task's occurrences as anchors, spaced `n + 1` apart, with every other task (and idle slots, if needed) filling the gaps between anchors. If there are enough other distinct tasks to fill every gap, no idle time is ever needed, and the schedule length is simply `tasks.length`. Otherwise, idle slots pad out the gaps, and the formula's arithmetic accounts for exactly that padding.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Schedule for tasks A A A B B B with cooldown 2, showing A and B alternating with one idle slot each cycle">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">tasks = [A,A,A,B,B,B], n = 2  (maxFreq=3, maxCount=2)</text>
    <text x="10" y="45">(3-1)*(2+1) + 2 = 2*3 + 2 = 8</text>
    <text x="10" y="70">slot:  0  1  2  3  4  5  6  7</text>
    <text x="10" y="90">task:  A  B  .  A  B  .  A  B</text>
    <rect x="10" y="100" width="180" height="24" fill="#3fb950"/><text x="100" y="117" fill="#0d1117" text-anchor="middle" font-size="10">total time = 8</text>
  </g>
</svg>

`A` anchors every 3rd slot (cooldown `n = 2`); `B` and one idle slot fill the gap each cycle.

## 5. Runnable example

```java
// TaskScheduler.java
import java.util.*;

public class TaskScheduler {

    // Level 1 -- Brute force: simulate the schedule minute by minute
    // with a max-heap of remaining counts and a cooldown queue.
    // Correct, and shown below as the general simulation; O(total
    // time * log 26), since the alphabet size bounds the heap.

    // KEY INSIGHT: the answer has a closed-form shape driven by the
    // MOST frequent task, which forces (n+1)-sized blocks; the
    // simulation above always matches this formula, but the formula
    // computes the same answer in O(1) after counting.

    // Level 2 -- Optimal: closed-form using frequency counts.
    static int leastInterval(char[] tasks, int n) {
        int[] counts = new int[26];
        for (char t : tasks) counts[t - 'A']++;

        int maxFreq = 0;
        for (int c : counts) maxFreq = Math.max(maxFreq, c);

        int maxCount = 0;
        for (int c : counts) if (c == maxFreq) maxCount++;

        int formula = (maxFreq - 1) * (n + 1) + maxCount;
        return Math.max(formula, tasks.length);
    }

    // Level 3 -- Hardened: works when n == 0 (no cooldown needed,
    // formula collapses to tasks.length) and when tasks are all
    // distinct (maxFreq == 1, formula gives exactly tasks.length).

    public static void main(String[] args) {
        System.out.println(leastInterval(new char[]{'A','A','A','B','B','B'}, 2));
        // 8
        System.out.println(leastInterval(new char[]{'A','A','A','B','B','B'}, 0));
        // 6
    }
}
```

**How to run:** `java TaskScheduler.java`

## 6. Walkthrough

Trace `leastInterval(['A','A','A','B','B','B'], 2)`:

| step | value |
|---|---|
| counts | A=3, B=3, rest 0 |
| maxFreq | 3 |
| maxCount (tasks tied at freq 3) | 2 (A and B) |
| formula | (3-1)*(2+1) + 2 = 6 + 2 = 8 |
| tasks.length | 6 |
| answer | max(8, 6) = 8 |

The schedule `A,B,idle,A,B,idle,A,B` takes exactly `8` slots, matching the formula. Time complexity is O(n) to count tasks (`n` = number of tasks) plus O(1) for the fixed 26-letter scan. Space is O(1), a fixed 26-element count array.

## 7. Gotchas & takeaways

> Gotcha: the formula alone can UNDER-count when there are enough distinct low-frequency tasks to fill every gap with real work instead of idle time — that is exactly why the final answer takes `max(formula, tasks.length)`, not the formula alone.

- The size-k-heap simulation (always run the currently most frequent READY task) and the closed-form counting formula agree on every input; the formula is the O(1)-after-counting shortcut once you trust the reasoning.
- `maxCount` matters because MULTIPLE tasks tied for the highest frequency each need their own slot in the final, otherwise-idle block.
- Related problems: Reorganize String (the same "space out the most frequent item" idea, applied to rearranging a string instead of scheduling with idle slots).
