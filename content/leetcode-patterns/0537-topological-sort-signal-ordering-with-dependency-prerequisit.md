---
card: leetcode-patterns
gi: 537
slug: topological-sort-signal-ordering-with-dependency-prerequisit
title: Topological Sort — signal: ordering with dependency (prerequisite) constraints
---

## 1. What it is

A topological sort orders the nodes of a **directed acyclic graph** (DAG — a directed graph with no cycles) so that every edge `u -> v` places `u` before `v` in the output. It answers "in what order can these tasks run, given that some tasks must finish before others start."

## 2. Why & when

Reach for topological sort whenever a problem describes tasks, courses, or steps, some of which must come before others, and asks for a valid order (or whether one even exists). A cycle in the dependency graph means no valid order exists — a task would depend, directly or indirectly, on itself.

Learn to recognize these signals in a problem statement:

- **"Course A requires course B first"** — the direct definition: build an edge `B -> A`, then find an order where every prerequisite appears before its dependent course.
- **"Can all tasks be finished?"** — this is really asking "does this dependency graph contain a cycle?" A valid topological order exists if and only if the graph is acyclic.
- **"Build order," "compilation order," "task scheduling with dependencies"** — same shape: produce one valid linear order respecting every "must come before" constraint.
- **"Letters in an alien language, inferred from sorted words"** — comparing adjacent words letter-by-letter yields ordering constraints between characters, which is a topological sort over the alphabet.
- **"Minimum height tree" or "peel away leaves"** — a repeated-leaf-removal process is Kahn's algorithm (BFS-based topological sort) applied layer by layer.

The alternative is trying every permutation of tasks and checking which ones satisfy all constraints — factorial time. Topological sort produces one valid order (or detects impossibility) in linear time.

## 3. Core concept

**Key idea:** a topological order always exists for a DAG, and it is found by repeatedly choosing a node with no remaining unprocessed dependencies (in Kahn's algorithm, a node whose in-degree — count of incoming edges — has dropped to zero), placing it next in the output, and removing its outgoing edges from consideration.

**Why a cycle blocks any valid order:** if nodes `A -> B -> C -> A` form a cycle, every one of them has at least one unprocessed dependency at all times — no node in the cycle can ever reach in-degree zero, so Kahn's algorithm gets stuck with nodes left over. That leftover is exactly how you detect "no valid order exists" (the classic "can you finish all courses" question).

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A dependency graph where B and C both require A, and D requires both B and C">
  <g font-family="sans-serif" font-size="13">
    <circle cx="150" cy="30" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="150" y="35" fill="#e6edf3" text-anchor="middle">A</text>
    <circle cx="80" cy="100" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="80" y="105" fill="#e6edf3" text-anchor="middle">B</text>
    <circle cx="220" cy="100" r="16" fill="#161b22" stroke="#30363d"/>
    <text x="220" y="105" fill="#e6edf3" text-anchor="middle">C</text>
    <circle cx="150" cy="160" r="16" fill="#161b22" stroke="#f0883e"/>
    <text x="150" y="165" fill="#e6edf3" text-anchor="middle">D</text>
    <line x1="138" y1="42" x2="92" y2="88" stroke="#8b949e" marker-end="url(#arr)"/>
    <line x1="162" y1="42" x2="208" y2="88" stroke="#8b949e" marker-end="url(#arr)"/>
    <line x1="90" y1="112" x2="140" y2="150" stroke="#8b949e" marker-end="url(#arr)"/>
    <line x1="210" y1="112" x2="160" y2="150" stroke="#8b949e" marker-end="url(#arr)"/>
    <defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="450" y="100" fill="#79c0ff">valid order: A, B, C, D (or A, C, B, D)</text>
  </g>
</svg>

`A` has no prerequisites, so it must come first. `B` and `C` both depend only on `A`, so either can come next. `D` depends on both `B` and `C`, so it must come last.

## 5. Runnable example

The artifact below is a reusable signal-checker: it builds a dependency graph and reports whether a valid order exists, using in-degree tracking.

### Signal-checker

```java
// TopoSortSignal.java
import java.util.*;

public class TopoSortSignal {

    static boolean hasValidOrder(int n, int[][] prerequisites) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        int[] inDegree = new int[n];

        for (int[] p : prerequisites) {
            int course = p[0], prereq = p[1];
            graph.get(prereq).add(course);
            inDegree[course]++;
        }

        Deque<Integer> queue = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            if (inDegree[i] == 0) queue.add(i);
        }

        int processed = 0;
        while (!queue.isEmpty()) {
            int node = queue.poll();
            processed++;
            for (int next : graph.get(node)) {
                if (--inDegree[next] == 0) queue.add(next);
            }
        }
        return processed == n; // all nodes processed means no cycle
    }

    public static void main(String[] args) {
        System.out.println("A->B->C->D chain has valid order: " +
                hasValidOrder(4, new int[][]{{1, 0}, {2, 1}, {3, 2}}));
        System.out.println("A->B->A cycle has valid order: " +
                hasValidOrder(2, new int[][]{{0, 1}, {1, 0}}));
    }
}
```

**How to run:** save as `TopoSortSignal.java`, then run `java TopoSortSignal.java`.

## 6. Walkthrough

1. You read a problem describing prerequisites or dependencies between tasks, then asking for a valid execution order (or whether one exists). That is the direct topological sort signal.
2. For the chain `1<-0`, `2<-1`, `3<-2` (meaning `0` before `1` before `2` before `3`), every node starts with in-degree 0 except its immediate successor — the queue processes `0, 1, 2, 3` one at a time, each unlocking the next.
3. `processed` reaches `4`, matching `n` — a valid order exists.
4. For the 2-node cycle `0<-1`, `1<-0`, both nodes start with in-degree `1` (each depends on the other) — the queue starts empty, and `processed` stays `0`.
5. `processed (0) != n (2)`, so no valid order exists — the cycle is correctly detected.

## 7. Gotchas & takeaways

> Gotcha: confusing the edge direction — "A requires B" means B must come before A, so the edge for scheduling purposes should point `B -> A` (B unlocks A), not `A -> B`. Getting this backwards silently produces an order that violates every dependency.

- Signal words: "prerequisite," "must come before," "dependency," "build order," "can you finish all tasks," "inferred ordering from examples" (alien dictionary).
- A topological order exists if and only if the graph is a DAG (directed, acyclic); Kahn's algorithm processing fewer than `n` nodes is the standard cycle-detection check.
- Alternative: trying all permutations is factorial time; topological sort finds a valid order (or detects impossibility) in O(V + E) time.
