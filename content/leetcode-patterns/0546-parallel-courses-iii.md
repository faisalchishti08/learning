---
card: leetcode-patterns
gi: 546
slug: parallel-courses-iii
title: Parallel Courses III
---

## 1. What it is

There are `n` courses, each with a `time[i]` to complete. `relations[i] = [prevCourse, nextCourse]` means `prevCourse` must finish before `nextCourse` can start. You may take unlimited courses in parallel, as long as their prerequisites are done. Return the **minimum time** needed to complete all courses. Example: `n = 3`, `relations = [[1,3],[2,3]]`, `time = [3,2,5]` → `8` (courses `1` and `2` run in parallel, taking `max(3,2)=3`; course `3` then takes `5` more, starting after both finish: `3 + 5 = 8`).

## 2. Why & when

This extends the [topological sort signal](0537-topological-sort-signal-ordering-with-dependency-prerequisit.md): instead of just producing *an* order, you compute, for each course, the earliest time it can finish, based on the latest-finishing prerequisite. Processing courses in topological order guarantees every prerequisite's finish time is already known when you need it. Constraints: up to 50,000 courses and relations.

## 3. Core concept

**Key idea:** a course can only start once *all* of its prerequisites are done, so its finish time is `time[course] + max(finish time of all its prerequisites)` (or just `time[course]` if it has none). Computing this bottom-up, in topological order, guarantees every prerequisite's finish time is already finalized before it is needed.

**Steps:**
1. Build the graph (`prevCourse -> nextCourse`) and `inDegree[]` exactly as in Course Schedule.
2. Initialize `finishTime[i] = time[i]` for every course (assuming no prerequisites yet).
3. Push every zero-in-degree course into the queue.
4. Repeatedly pop a course `u`; for each course `v` it unlocks: update `finishTime[v] = max(finishTime[v], finishTime[u] + time[v])`, then decrement `inDegree[v]`, pushing it if it reaches zero.
5. Return the maximum value across all of `finishTime[]` — the last course to finish determines the total time.

**Why taking the max (not the sum) across parallel prerequisites is correct:** courses with no dependency between each other run simultaneously, so only the slowest one among a set of prerequisites determines when their shared dependent can begin — waiting for the others in parallel costs nothing extra, since they overlap in time rather than stacking up.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Courses 1 (time 3) and 2 (time 2) run in parallel, both finishing before course 3 (time 5) can start, giving total time 3 + 5 = 8">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="150" height="30" fill="#3fb950" opacity="0.6"/>
    <text x="95" y="40" fill="#0d1117" text-anchor="middle" font-size="11">course 1 (time 3)</text>
    <rect x="20" y="60" width="100" height="30" fill="#79c0ff" opacity="0.6"/>
    <text x="70" y="80" fill="#0d1117" text-anchor="middle" font-size="11">course 2 (t 2)</text>
    <rect x="170" y="40" width="250" height="30" fill="#f0883e" opacity="0.6"/>
    <text x="295" y="60" fill="#0d1117" text-anchor="middle" font-size="11">course 3 (time 5), starts at t=3</text>
    <text x="300" y="130" fill="#e6edf3" text-anchor="middle">finish(1)=3, finish(2)=2, finish(3)=max(3,2)+5=8</text>
  </g>
</svg>

Courses `1` and `2` run in parallel; course `3` waits for the *later* of the two (`max(3,2)=3`), then adds its own `5`, giving a total of `8`.

## 5. Runnable example

**Level 1 — Brute force.** Recompute each course's finish time recursively, without memoization, re-deriving shared prerequisite finish times repeatedly. Exponential blowup on graphs with shared ancestors.

**KEY INSIGHT:** processing courses in topological order guarantees each prerequisite's finish time is already finalized exactly once, before any dependent needs it — the same guarantee that also makes plain topological sort correct.

**Level 2 — Optimal.** Kahn's algorithm augmented with a running `finishTime[]` array, O(V + E).

**Level 3 — Hardened.** Handles courses with no prerequisites (finish time equals their own duration) and courses that unlock multiple downstream courses with different durations.

```java
// ParallelCoursesIII.java
import java.util.*;

public class ParallelCoursesIII {

    static int minimumTime(int n, int[][] relations, int[] time) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i <= n; i++) graph.add(new ArrayList<>()); // 1-indexed courses
        int[] inDegree = new int[n + 1];

        for (int[] r : relations) {
            graph.get(r[0]).add(r[1]);
            inDegree[r[1]]++;
        }

        int[] finishTime = new int[n + 1];
        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 1; i <= n; i++) {
            finishTime[i] = time[i - 1];
            if (inDegree[i] == 0) queue.add(i);
        }

        int result = 0;
        while (!queue.isEmpty()) {
            int u = queue.poll();
            result = Math.max(result, finishTime[u]);
            for (int v : graph.get(u)) {
                finishTime[v] = Math.max(finishTime[v], finishTime[u] + time[v - 1]);
                if (--inDegree[v] == 0) queue.add(v);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(minimumTime(3, new int[][]{{1, 3}, {2, 3}}, new int[]{3, 2, 5})); // 8
        System.out.println(minimumTime(5,
                new int[][]{{1, 5}, {2, 5}, {3, 5}, {3, 4}, {4, 5}},
                new int[]{1, 2, 3, 4, 5})); // 12
    }
}
```

**How to run:** save as `ParallelCoursesIII.java`, then run `java ParallelCoursesIII.java`.

## 6. Walkthrough

Trace `minimumTime(3, [[1,3],[2,3]], [3,2,5])`:

| step | finishTime | queue | result |
|---|---|---|---|
| init | `[_,3,2,5]` (index 1..3) | `[1,2]` (both have inDegree 0) | 0 |
| pop 1 | unchanged | update course 3: `finishTime[3] = max(5, 3+5)=8`; inDegree[3] drops to 1 | result=max(0,3)=3 |
| pop 2 | unchanged | update course 3: `finishTime[3] = max(8, 2+5)=8` (no change); inDegree[3] drops to 0, joins queue | result=max(3,2)=3 |
| pop 3 | unchanged | no further courses to unlock | result=max(3,8)=8 |

Final result: `8`, matching `max(3,2) + 5`.

## 7. Gotchas & takeaways

> Gotcha: initializing `finishTime[v]` to `0` instead of `time[v]` before any updates arrive gives a wrong result for courses with prerequisites — always seed `finishTime[i] = time[i]` up front, so the `max` comparison during propagation is comparing real candidate finish times, not zero.

- Signal: "minimum time to complete all tasks, tasks run in parallel when possible" is a topological sort where each node also carries a running "earliest finish time," updated via `max`.
- Take the `max` over parallel prerequisites (they overlap in time), not a `sum` — summing would incorrectly treat concurrent work as sequential.
- Related problems: Course Schedule II, Sort Items by Groups Respecting Dependencies.
