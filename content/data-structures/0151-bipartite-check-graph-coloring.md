---
card: data-structures
gi: 151
slug: bipartite-check-graph-coloring
title: Bipartite check (graph coloring)
---

## 1. What it is

A graph is **bipartite** if its vertices can be split into two groups such that every edge connects a vertex in one group to a vertex in the other — never two vertices within the same group. Checking this is done with a simple form of **graph coloring**: assign each vertex one of two colors, alternating colors across every edge, and check whether that is ever impossible.

## 2. Why & when

Bipartite graphs model any "two-sided" relationship: students and courses (a student "connects" to the courses they take), workers and jobs (for bipartite matching problems), or simply detecting whether a graph has any odd-length cycle at all (a graph is bipartite if and only if it has no odd cycle). This check is also a common building block: many matching and scheduling algorithms only work correctly on bipartite graphs, so verifying bipartiteness is often the first step.

## 3. Core concept

**How the operation works.** Run BFS or DFS from any unvisited vertex, assigning it color `0`. For every neighbor: if uncolored, assign it the *opposite* color of the current vertex and continue. If it is already colored, check that its color is indeed the opposite of the current vertex's color — if not, the graph is not bipartite. Repeat from every unvisited vertex (a graph can have multiple disconnected pieces, each needing its own check).

**Why this equals "no odd cycle."** Alternating colors along any path means a cycle can only close correctly (ending on the opposite color from where it started, as required) if the cycle has an **even** number of edges. An odd cycle forces the last vertex before returning to the start to end up the *same* color as the start — an unavoidable coloring conflict, which is exactly what the algorithm detects.

**Coloring conflict, precisely.** The conflict is detected the moment BFS/DFS finds an edge connecting two vertices that have already been assigned the *same* color — this can only happen if some cycle in the graph has odd length, since an even-length cycle always alternates back to the correct opposite color by the time it closes.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A 4 cycle graph correctly 2 colored with alternating colors around the whole cycle, versus a 3 cycle graph where the coloring conflicts because an odd cycle cannot alternate correctly">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#79c0ff" text-anchor="middle">4-cycle: bipartite (even length)</text>
    <circle cx="100" cy="50" r="16" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="100" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="200" cy="50" r="16" fill="#161b22" stroke="#79c0ff" stroke-width="2"/><text x="200" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="200" cy="130" r="16" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="200" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="100" cy="130" r="16" fill="#161b22" stroke="#79c0ff" stroke-width="2"/><text x="100" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <line x1="116" y1="50" x2="184" y2="50" stroke="#8b949e" stroke-width="2"/>
    <line x1="200" y1="66" x2="200" y2="114" stroke="#8b949e" stroke-width="2"/>
    <line x1="184" y1="130" x2="116" y2="130" stroke="#8b949e" stroke-width="2"/>
    <line x1="100" y1="114" x2="100" y2="66" stroke="#8b949e" stroke-width="2"/>
    <text x="150" y="175" fill="#79c0ff" text-anchor="middle" font-size="9">colors alternate perfectly all the way around</text>

    <text x="480" y="16" fill="#f0883e" text-anchor="middle">3-cycle: NOT bipartite (odd length)</text>
    <circle cx="480" cy="50" r="16" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="480" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="430" cy="130" r="16" fill="#161b22" stroke="#79c0ff" stroke-width="2"/><text x="430" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="530" cy="130" r="16" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="530" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="468" y1="62" x2="442" y2="118" stroke="#8b949e" stroke-width="2"/>
    <line x1="446" y1="130" x2="514" y2="130" stroke="#8b949e" stroke-width="2"/>
    <line x1="518" y1="118" x2="492" y2="62" stroke="#f0883e" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="480" y="175" fill="#f0883e" text-anchor="middle" font-size="9">C-A edge: both are the SAME color -- conflict</text>
  </g>
</svg>

The 4-cycle alternates colors perfectly all the way around. In the 3-cycle, `A` and `C` end up the same color once the alternation wraps around — the closing edge `C-A` conflicts, correctly proving an odd cycle is not bipartite.

## 5. Runnable example

```java
// BipartiteCheck.java
import java.util.*;

public class BipartiteCheck {

    // Basic: BFS-based 2-coloring, checking every edge for a same-color conflict.
    static boolean isBipartite(Map<String, List<String>> graph, Set<String> allVertices) {
        Map<String, Integer> color = new HashMap<>();

        for (String start : allVertices) {
            if (color.containsKey(start)) continue; // already colored via an earlier component
            color.put(start, 0);
            Queue<String> queue = new LinkedList<>();
            queue.offer(start);

            while (!queue.isEmpty()) {
                String current = queue.poll();
                for (String neighbor : graph.getOrDefault(current, List.of())) {
                    if (!color.containsKey(neighbor)) {
                        color.put(neighbor, 1 - color.get(current)); // opposite color of the current vertex
                        queue.offer(neighbor);
                    } else if (color.get(neighbor).equals(color.get(current))) {
                        return false; // same color on both ends of an edge -- conflict, not bipartite
                    }
                }
            }
        }
        return true;
    }

    static void basicLevel() {
        Map<String, List<String>> fourCycle = Map.of(
            "A", List.of("B", "D"),
            "B", List.of("A", "C"),
            "C", List.of("B", "D"),
            "D", List.of("C", "A"));

        System.out.println("basic: 4-cycle (A-B-C-D-A) is bipartite? -> " + isBipartite(fourCycle, Set.of("A", "B", "C", "D")));
    }

    // Intermediate: an odd cycle -- must correctly report NOT bipartite.
    static void intermediateLevel() {
        Map<String, List<String>> triangle = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("A", "C"),
            "C", List.of("A", "B"));

        System.out.println("intermediate: 3-cycle (triangle) is bipartite? -> " + isBipartite(triangle, Set.of("A", "B", "C")));
    }

    // Advanced: return the actual 2-coloring (the two groups), useful for downstream bipartite-matching algorithms.
    static Map<Integer, List<String>> getBipartiteGroups(Map<String, List<String>> graph, Set<String> allVertices) {
        Map<String, Integer> color = new HashMap<>();
        for (String start : allVertices) {
            if (color.containsKey(start)) continue;
            color.put(start, 0);
            Queue<String> queue = new LinkedList<>();
            queue.offer(start);
            while (!queue.isEmpty()) {
                String current = queue.poll();
                for (String neighbor : graph.getOrDefault(current, List.of())) {
                    if (!color.containsKey(neighbor)) {
                        color.put(neighbor, 1 - color.get(current));
                        queue.offer(neighbor);
                    }
                }
            }
        }

        Map<Integer, List<String>> groups = new HashMap<>();
        groups.put(0, new ArrayList<>());
        groups.put(1, new ArrayList<>());
        for (Map.Entry<String, Integer> entry : color.entrySet()) groups.get(entry.getValue()).add(entry.getKey());
        return groups;
    }

    static void advancedLevel() {
        Map<String, List<String>> studentsAndCourses = Map.of(
            "student1", List.of("courseA", "courseB"),
            "student2", List.of("courseB"),
            "courseA", List.of("student1"),
            "courseB", List.of("student1", "student2"));

        Map<Integer, List<String>> groups = getBipartiteGroups(studentsAndCourses,
            Set.of("student1", "student2", "courseA", "courseB"));
        System.out.println("advanced: group 0 -> " + groups.get(0));
        System.out.println("advanced: group 1 -> " + groups.get(1));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BipartiteCheck.java`, then run `java BipartiteCheck.java`.

## 6. Walkthrough

1. `basicLevel()` colors the 4-cycle starting at `A` (color `0`). BFS colors `B` and `D` (both `A`'s neighbors) as `1`, then `C` (neighbor of both `B` and `D`) as `0`. Every edge connects opposite colors (`A`-`B`: `0`-`1`; `B`-`C`: `1`-`0`; `C`-`D`: `0`-`1`; `D`-`A`: `1`-`0`), so `isBipartite` correctly returns `true`.
2. `intermediateLevel()` colors the triangle starting at `A` (color `0`). `B` and `C` (both `A`'s neighbors) get color `1`. But `B` and `C` are also neighbors of *each other* — both already colored `1`, the same color — triggering the conflict check and correctly returning `false`.
3. `advancedLevel()` models a students-and-courses relationship and extracts the actual two groups from the coloring, rather than just a yes/no answer. Since students only connect to courses (never to other students directly), the coloring naturally separates them into `group 0` (all students) and `group 1` (all courses) — exactly the two "sides" a real bipartite matching algorithm (like matching students to available course seats) would need as its input.

## 7. Gotchas & takeaways

> Gotcha: forgetting to check every disconnected component (not just running BFS once from an arbitrary start vertex) can miss a conflict entirely if the graph has multiple disconnected pieces — one piece might be perfectly bipartite while another, unreached piece contains an odd cycle.

- A graph is bipartite exactly when it contains no odd-length cycle — the 2-coloring check and "no odd cycle" are two ways of stating the same fact.
- The algorithm is BFS/DFS with a twist: assign the opposite color to every uncolored neighbor, and flag a conflict the instant two already-colored, connected vertices share the same color.
- Check every disconnected component separately — a single starting vertex's BFS/DFS only covers its own component.
- Related concepts: [Breadth-first search (BFS)](0144-breadth-first-search-bfs.md), [Cycle detection (directed & undirected)](0150-cycle-detection-directed-undirected.md).
