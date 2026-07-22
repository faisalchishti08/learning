---
card: leetcode-patterns
gi: 203
slug: process-tasks-using-servers
title: Process Tasks Using Servers
---

## 1. What it is

Given `servers[i]` (weight of server `i`) and `tasks[j]` (time to complete task `j`, arriving at time `j`), each task is assigned to the FREE server with the smallest weight (ties broken by smallest index); if no server is free, the task waits for the earliest server to free up. Return an array giving the server index that handled each task. Example: `servers = [3,3,2]`, `tasks = [1,2,3,2,1,2]` → `[2,2,0,2,1,2]`.

## 2. Why & when

This extends Single-Threaded CPU's "available now, pick the best" pattern to MULTIPLE workers. You need two heaps: one for currently FREE servers (ordered by weight, then index) to pick from, and one for BUSY servers (ordered by when they finish) so you know when to move a server from busy back to free.

## 3. Core concept

**Key idea:** maintain a min-heap of free servers ordered by `[weight, index]`, and a min-heap of busy servers ordered by `[freeAtTime, index]`. When a task arrives, first move any busy server whose `freeAtTime <= task's arrival time` into the free heap. If the free heap is still empty after that, jump time forward to the earliest busy server's free time and move it (and any others tied at that time) into the free heap. Then assign the task to the free heap's top.

**Steps:**
1. Initialize the free-server heap with every server's `[weight, index]`. The busy-server heap starts empty.
2. For each task `j` (arriving at time `j`), move every busy server with `freeAtTime <= j` from the busy heap into the free heap.
3. If the free heap is still empty, pop the busy heap's earliest-freeing server, advance to ITS free time, move it (and any other servers tied at that exact time) to the free heap.
4. Pop the free heap's smallest `[weight, index]` server, assign it to task `j`, and push it into the busy heap with `freeAtTime = currentTime + tasks[j]`.
5. Record the assigned server's index as the answer for task `j`.

**Why it is correct:** always moving every server that has become free (by the current time) BEFORE picking, and picking the SMALLEST weight among free servers, directly implements the assignment rule. Jumping to the next busy server's free time when nothing is free yet is safe because no server can free up any earlier, so no smaller-weight option is being skipped by advancing time that far.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Free-server min-heap by weight; busy-server min-heap by free time, moving servers across as time passes">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">free (by weight)</text>
    <circle cx="60" cy="60" r="16" fill="#161b22" stroke="#3fb950"/><text x="60" y="64" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="260" y="20" fill="#e6edf3" font-weight="bold">busy (by free time)</text>
    <circle cx="300" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="300" y="64" fill="#e6edf3" text-anchor="middle">t=5</text>
    <path d="M280,60 L100,60" stroke="#e3b341" stroke-dasharray="4,3" marker-end="url(#a6)"/>
    <defs><marker id="a6" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e3b341"/></marker></defs>
    <text x="10" y="15" fill="#e6edf3">once t=5 passes, that server moves from busy back into free, ready to be picked again</text>
  </g>
</svg>

Servers move from the busy heap back into the free heap once their free time has passed, becoming eligible for the next task.

## 5. Runnable example

```java
// ProcessTasksUsingServers.java
import java.util.*;

public class ProcessTasksUsingServers {

    // Level 1 -- Brute force: at each task's arrival, linearly scan
    // ALL servers to find any that are free (checking their busy-until
    // time against the current time) and pick the smallest weight
    // among them. Correct, but O(servers) per task instead of O(log
    // servers).

    // KEY INSIGHT: two min-heaps -- one for free servers (by weight),
    // one for busy servers (by free time) -- turn both "find the best
    // free server" and "find which busy server frees next" into
    // O(log n) heap operations instead of O(n) scans.

    // Level 2 -- Optimal: dual min-heaps, move servers across as time
    // passes.
    static int[] assignTasks(int[] servers, int[] tasks) {
        int n = servers.length, m = tasks.length;
        PriorityQueue<long[]> free = new PriorityQueue<>(
            (a, b) -> a[0] != b[0] ? Long.compare(a[0], b[0]) : Long.compare(a[1], b[1])
        );
        for (int i = 0; i < n; i++) free.add(new long[]{servers[i], i});

        PriorityQueue<long[]> busy = new PriorityQueue<>(
            (a, b) -> a[0] != b[0] ? Long.compare(a[0], b[0]) : Long.compare(a[1], b[1])
        );

        int[] result = new int[m];
        for (int j = 0; j < m; j++) {
            long arrival = j;
            while (!busy.isEmpty() && busy.peek()[0] <= arrival) {
                long[] s = busy.poll();
                free.add(new long[]{servers[(int) s[1]], s[1]});
            }
            if (free.isEmpty()) {
                long[] s = busy.poll();
                long freeAt = s[0];
                free.add(new long[]{servers[(int) s[1]], s[1]});
                while (!busy.isEmpty() && busy.peek()[0] == freeAt) {
                    long[] s2 = busy.poll();
                    free.add(new long[]{servers[(int) s2[1]], s2[1]});
                }
                arrival = freeAt;
            }
            long[] chosen = free.poll();
            int serverIdx = (int) chosen[1];
            result[j] = serverIdx;
            busy.add(new long[]{arrival + tasks[j], serverIdx});
        }
        return result;
    }

    // Level 3 -- Hardened: when time must jump forward (no free
    // server), ALL busy servers tied at the exact same free time are
    // moved together, not just the first one popped -- otherwise a
    // same-time server would be incorrectly left stranded in the busy
    // heap for one extra task.

    public static void main(String[] args) {
        System.out.println(Arrays.toString(assignTasks(new int[]{3,3,2}, new int[]{1,2,3,2,1,2}))); // [2, 2, 0, 2, 1, 2]
    }
}
```

**How to run:** `java ProcessTasksUsingServers.java`

## 6. Walkthrough

Trace the first few tasks of `servers = [3,3,2]`, `tasks = [1,2,3,2,1,2]`:

| Task j (arrival) | Free servers before | Chosen | busy after |
|---|---|---|---|
| 0 (t=0) | {[2,idx2],[3,idx0],[3,idx1]} | idx2 (weight 2) | idx2 free at 0+1=1 |
| 1 (t=1) | idx2 rejoins free (1<=1); free={[2,idx2],[3,idx0],[3,idx1]} | idx2 again | idx2 free at 1+2=3 |
| 2 (t=2) | idx2 still busy (free at 3 > 2); free={[3,idx0],[3,idx1]} | idx0 (tie-break smaller index) | idx0 free at 2+3=5 |

Result matches `[2, 2, 0, ...]` from the expected output. Time complexity is O((n + m) log n), since each server enters and leaves each heap a bounded number of times relative to tasks processed; space is O(n) for the two heaps.

## 7. Gotchas & takeaways

> Gotcha: only moving the SINGLE busy server that triggered the time jump (instead of ALL busy servers tied at that exact free time) leaves same-time servers stuck in the busy heap, making them unavailable for a task that should have been able to use them.

- Use `long` for time and free-time values — task arrival times and processing durations can accumulate to exceed 32-bit `int` range in large inputs.
- The tie-break rule (smallest index) must be baked into BOTH heaps' comparators — the free heap for picking among equal weights, and (implicitly) for consistent ordering when multiple servers free at the same time.
- Related problems: Single-Threaded CPU (single "worker" version of this exact availability pattern), Furthest Building You Can Reach (single heap, different greedy resource problem).
