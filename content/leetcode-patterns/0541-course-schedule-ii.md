---
card: leetcode-patterns
gi: 541
slug: course-schedule-ii
title: Course Schedule II
---

## 1. What it is

Same setup as [Course Schedule](0540-course-schedule.md): `numCourses` courses and `prerequisites[i] = [a, b]` meaning `b` before `a`. This time, return **one valid order** in which to take all courses, or an empty array if it is impossible. Example: `numCourses = 4`, `prerequisites = [[1,0],[2,0],[3,1],[3,2]]` → `[0,1,2,3]` (or `[0,2,1,3]` — either is valid).

## 2. Why & when

This is Course Schedule with the actual order requested instead of just a yes/no answer — the same [topological sort signal](0537-topological-sort-signal-ordering-with-dependency-prerequisit.md), but now you must collect and return the order Kahn's algorithm naturally produces, rather than just counting how many courses it processes.

## 3. Core concept

**Key idea:** run Kahn's algorithm exactly as in Course Schedule, but instead of only counting completed courses, append each popped course to a result list. If a cycle exists, that list ends up shorter than `numCourses`, signaling impossibility.

**Steps:**
1. Build the graph and `inDegree[]` exactly as before.
2. Push every zero-in-degree course into the queue.
3. Repeatedly pop a course, **append it to the result list**, and decrement its dependents' in-degrees, pushing any that reach zero.
4. If the result list's size equals `numCourses`, return it. Otherwise return an empty array — a cycle blocked some courses from ever being reachable.

**Why the order the queue produces is always valid:** every course is only appended after all of its prerequisites have already been appended (its in-degree only reaches zero once every prerequisite has already been popped and processed) — that is precisely the definition of a valid topological order.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Course 0 unlocks both 1 and 2, which both unlock course 3">
  <g font-family="sans-serif" font-size="13">
    <circle cx="120" cy="80" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="85" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="300" cy="30" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="300" y="35" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="300" cy="130" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="300" y="135" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="480" cy="80" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="480" y="85" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="132" y1="70" x2="285" y2="38" stroke="#8b949e" marker-end="url(#a3)"/>
    <line x1="132" y1="90" x2="285" y2="122" stroke="#8b949e" marker-end="url(#a3)"/>
    <line x1="315" y1="38" x2="468" y2="72" stroke="#8b949e" marker-end="url(#a3)"/>
    <line x1="315" y1="122" x2="468" y2="88" stroke="#8b949e" marker-end="url(#a3)"/>
    <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="300" y="165" fill="#79c0ff" text-anchor="middle">order: 0, then 1 and 2 (either order), then 3</text>
  </g>
</svg>

Course `0` must come first; `1` and `2` can be taken in either order once `0` is done; `3` must come last, after both.

## 5. Runnable example

**Level 1 — Brute force.** Repeatedly scan for any course whose prerequisites are all already scheduled, append it, and repeat. O(n²) or worse.

**KEY INSIGHT:** the order Kahn's algorithm naturally dequeues courses in is already a valid topological order — no extra reconstruction step is needed beyond collecting the pop order.

**Level 2 — Optimal.** Kahn's algorithm collecting the pop order, O(V + E).

**Level 3 — Hardened.** Handles a cycle (returns empty array), and courses with no prerequisites (can appear anywhere before their own dependents).

```java
// CourseScheduleII.java
import java.util.*;

public class CourseScheduleII {

    static int[] findOrder(int numCourses, int[][] prerequisites) {
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

        int[] order = new int[numCourses];
        int idx = 0;
        while (!queue.isEmpty()) {
            int course = queue.poll();
            order[idx++] = course;
            for (int next : graph.get(course)) {
                if (--inDegree[next] == 0) queue.add(next);
            }
        }
        return idx == numCourses ? order : new int[0];
    }

    public static void main(String[] args) {
        int[][] prereqs = {{1, 0}, {2, 0}, {3, 1}, {3, 2}};
        System.out.println(Arrays.toString(findOrder(4, prereqs))); // [0, 1, 2, 3]

        int[][] cyclic = {{1, 0}, {0, 1}};
        System.out.println(Arrays.toString(findOrder(2, cyclic))); // []
    }
}
```

**How to run:** save as `CourseScheduleII.java`, then run `java CourseScheduleII.java`.

## 6. Walkthrough

Trace `findOrder(4, [[1,0],[2,0],[3,1],[3,2]])`:

| step | inDegree | queue | order so far |
|---|---|---|---|
| build | `[0,1,1,2]` | `[0]` (only 0 starts at 0) | `[]` |
| pop 0 | `[0,0,0,2]` (1 and 2 both drop to 0) | `[1,2]` | `[0]` |
| pop 1 | `[0,0,0,1]` (3 drops from 2 to 1) | `[2]` | `[0,1]` |
| pop 2 | `[0,0,0,0]` (3 drops from 1 to 0) | `[3]` | `[0,1,2]` |
| pop 3 | unchanged | empty | `[0,1,2,3]` |

`idx (4) == numCourses (4)`, so the full order `[0,1,2,3]` is returned.

## 7. Gotchas & takeaways

> Gotcha: returning the order collected so far without checking `idx == numCourses` silently returns a partial, invalid order when a cycle exists instead of the required empty array — always check the count before returning.

- Signal: "return a valid order" (not just yes/no) means collect Kahn's pop order directly — it is already valid, no post-processing needed.
- Multiple valid orders often exist (siblings with no dependency between them can appear in either order); any one of them is accepted.
- Related problems: Course Schedule, Sort Items by Groups Respecting Dependencies (two-level version), Alien Dictionary.
