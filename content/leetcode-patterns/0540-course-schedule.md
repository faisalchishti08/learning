---
card: leetcode-patterns
gi: 540
slug: course-schedule
title: Course Schedule
---

## 1. What it is

There are `numCourses` courses, labeled `0` to `numCourses - 1`. `prerequisites[i] = [a, b]` means you must take course `b` before course `a`. Return `true` if you can finish all courses, or `false` if it is impossible. Example: `numCourses = 2`, `prerequisites = [[1,0]]` → `true` (take `0`, then `1`). `numCourses = 2`, `prerequisites = [[1,0],[0,1]]` → `false` (each requires the other).

## 2. Why & when

"Can all tasks be finished, given these prerequisite pairs" is the canonical phrasing of "does this dependency graph contain a cycle." This is the direct [topological sort signal](0537-topological-sort-signal-ordering-with-dependency-prerequisit.md): build a graph from prerequisites, then check whether a full topological order exists. Constraints: up to 2,000 courses and 5,000 prerequisite pairs.

## 3. Core concept

**Key idea:** build a directed graph where an edge `b -> a` means "b must be taken before a" (from prerequisite pair `[a, b]`). Run Kahn's algorithm: repeatedly remove courses with zero remaining prerequisites. If every course gets removed, all courses can be finished; if some are left over, they are stuck in a cycle.

**Steps:**
1. Build an adjacency list: for each `[a, b]`, add edge `b -> a`, and increment `inDegree[a]`.
2. Push every course with `inDegree == 0` (no prerequisites) into a queue.
3. Repeatedly pop a course, increment a `completed` counter, and decrement the in-degree of each course that depends on it; push any course whose in-degree just hit `0`.
4. Return `completed == numCourses`.

**Why this exact check detects a cycle:** a course stuck in a cycle always has at least one prerequisite that itself depends (directly or indirectly) back on it, so its in-degree can never reach zero through this process. It is never pushed to the queue, and `completed` ends up short of `numCourses` — exactly the signal that no valid order exists.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Course 0 with no prerequisites unlocks course 1, which unlocks course 2">
  <g font-family="sans-serif" font-size="13">
    <circle cx="100" cy="70" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="100" y="75" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="300" cy="70" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="300" y="75" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="500" cy="70" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="500" y="75" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="118" y1="70" x2="282" y2="70" stroke="#8b949e" marker-end="url(#a2)"/>
    <line x1="318" y1="70" x2="482" y2="70" stroke="#8b949e" marker-end="url(#a2)"/>
    <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="300" y="120" fill="#3fb950" text-anchor="middle">all in-degrees reach 0 eventually -&gt; can finish all courses</text>
  </g>
</svg>

Course `0` unlocks course `1`, which unlocks course `2` — no cycle, so every course eventually reaches in-degree zero.

## 5. Runnable example

**Level 1 — Brute force.** Repeatedly scan all courses for one with all prerequisites already completed, mark it completed, and repeat until no progress is made. O(n²) or worse.

**KEY INSIGHT:** a queue of zero-in-degree courses lets you process exactly the courses that just became available, without re-scanning every course on every step.

**Level 2 — Optimal.** Kahn's algorithm, O(V + E) where V is `numCourses` and E is the number of prerequisite pairs.

**Level 3 — Hardened.** Handles a course with no prerequisites at all, self-referencing prerequisites (`[0,0]`), and disconnected groups of courses.

```java
// CourseSchedule.java
import java.util.*;

public class CourseSchedule {

    static boolean canFinish(int numCourses, int[][] prerequisites) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < numCourses; i++) graph.add(new ArrayList<>());
        int[] inDegree = new int[numCourses];

        for (int[] p : prerequisites) {
            int course = p[0], prereq = p[1];
            graph.get(prereq).add(course);
            inDegree[course]++;
        }

        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < numCourses; i++) {
            if (inDegree[i] == 0) queue.add(i);
        }

        int completed = 0;
        while (!queue.isEmpty()) {
            int course = queue.poll();
            completed++;
            for (int next : graph.get(course)) {
                if (--inDegree[next] == 0) queue.add(next);
            }
        }
        return completed == numCourses;
    }

    public static void main(String[] args) {
        System.out.println(canFinish(2, new int[][]{{1, 0}}));           // true
        System.out.println(canFinish(2, new int[][]{{1, 0}, {0, 1}}));   // false
        System.out.println(canFinish(3, new int[][]{}));                  // true, no prerequisites at all
        System.out.println(canFinish(1, new int[][]{{0, 0}}));            // false, self-cycle
    }
}
```

**How to run:** save as `CourseSchedule.java`, then run `java CourseSchedule.java`.

## 6. Walkthrough

Trace `canFinish(2, [[1,0],[0,1]])`:

| step | inDegree | queue | completed |
|---|---|---|---|
| build graph | `[1, 1]` (each course depends on the other) | — | 0 |
| initial scan | `[1, 1]` | empty, no course has inDegree 0 | 0 |
| loop | queue stays empty, loop never runs | — | 0 |
| final check | `completed (0) != numCourses (2)` | — | return `false` |

Both courses depend on each other, so neither ever reaches in-degree zero — correctly reported as impossible.

## 7. Gotchas & takeaways

> Gotcha: building the edge in the wrong direction (`a -> b` instead of `b -> a` for prerequisite pair `[a, b]`) silently inverts the whole dependency graph, producing wrong cycle detection and a wrong order if you also tried to reconstruct one.

- Signal: "can you finish all tasks given these prerequisite pairs" is a pure cycle-detection question, answered by comparing the count of successfully processed nodes against the total.
- `prerequisites[i] = [a, b]` means "b before a" — the graph edge goes `b -> a`, the opposite of the pair's listed order.
- Related problems: Course Schedule II (reconstructs the actual order), Alien Dictionary, Parallel Courses III.
