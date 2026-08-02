---
card: data-structures
gi: 145
slug: depth-first-search-dfs
title: Depth-first search (DFS)
---

## 1. What it is

**Depth-first search (DFS)** explores a graph by going as deep as possible along one path before backtracking — it fully explores one neighbor's entire reachable subgraph before ever trying the next neighbor, using either recursion (the call stack) or an explicit stack.

## 2. Why & when

DFS is the natural tool whenever you need to explore *every* reachable vertex, detect a cycle, or reason about a path's full structure — it does not care about finding the shortest route, only about exhaustively exploring. Use it for cycle detection, topological sort, counting connected components, and any "explore everything reachable" task where distance from the start does not matter.

## 3. Core concept

**How the operation works (recursive form).** Mark the current vertex visited, then process it (however the algorithm needs). For each of its neighbors, if unvisited, recursively call DFS on that neighbor. The recursion naturally goes as deep as possible before returning, since each recursive call only returns after its *entire* subtree has been fully explored.

**How the operation works (iterative form).** Push the start vertex onto an explicit stack. Repeatedly pop a vertex; if unvisited, mark it visited, process it, and push all of its neighbors. Because a stack is LIFO, the most recently pushed neighbor is explored next — the same "go deep first" behavior as recursion, without relying on the call stack.

**DFS versus BFS — the key structural difference.** Both algorithms share nearly identical code, differing only in the data structure used to hold "vertices to process next": BFS uses a **queue** (FIFO — explores in the order discovered, level by level); DFS uses a **stack**, or the equivalent recursive call stack (LIFO — explores the most recently discovered vertex next, going deep before wide).

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS from A going all the way down through B and D before backtracking to explore C, contrasted with BFS which would visit B and C before D">
  <g font-family="sans-serif" font-size="11">
    <circle cx="150" cy="30" r="16" fill="#0d1117" stroke="#f0883e"/><text x="150" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="100" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="100" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="200" cy="90" r="16" fill="#161b22" stroke="#8b949e"/><text x="200" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="100" cy="150" r="16" fill="#161b22" stroke="#79c0ff"/><text x="100" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <line x1="138" y1="42" x2="112" y2="78" stroke="#79c0ff" stroke-width="2"/>
    <line x1="162" y1="42" x2="188" y2="78" stroke="#8b949e" stroke-width="2"/>
    <line x1="100" y1="106" x2="100" y2="134" stroke="#79c0ff" stroke-width="2"/>
    <text x="330" y="60" fill="#79c0ff" font-size="10">DFS order: A -&gt; B -&gt; D (fully explored), THEN back up to C</text>
    <text x="330" y="90" fill="#8b949e" font-size="10">BFS order (for contrast): A -&gt; B -&gt; C (level 1), THEN D (level 2)</text>
  </g>
</svg>

DFS from `A` commits to the `B` branch entirely — reaching `D` — before ever backtracking to try `C`. BFS, by contrast, would visit both of `A`'s direct neighbors (`B`, `C`) before going any deeper to `D`.

## 5. Runnable example

```java
// DepthFirstSearch.java
import java.util.*;

public class DepthFirstSearch {

    // Basic: recursive DFS traversal order.
    static void dfsRecursive(Map<String, List<String>> graph, String current, Set<String> visited, List<String> order) {
        visited.add(current);
        order.add(current);
        for (String neighbor : graph.getOrDefault(current, List.of())) {
            if (!visited.contains(neighbor)) {
                dfsRecursive(graph, neighbor, visited, order); // goes all the way down before returning to try the next neighbor
            }
        }
    }

    static void basicLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("D"),
            "C", List.of(),
            "D", List.of());

        List<String> order = new ArrayList<>();
        dfsRecursive(graph, "A", new HashSet<>(), order);
        System.out.println("basic: recursive DFS order from A -> " + order + " (goes A->B->D fully before trying C)");
    }

    // Intermediate: iterative DFS using an explicit stack -- same "go deep first" behavior, no recursion.
    static List<String> dfsIterative(Map<String, List<String>> graph, String start) {
        List<String> order = new ArrayList<>();
        Set<String> visited = new HashSet<>();
        Deque<String> stack = new ArrayDeque<>();

        stack.push(start);
        while (!stack.isEmpty()) {
            String current = stack.pop();
            if (visited.contains(current)) continue; // may have been pushed more than once -- skip if already processed
            visited.add(current);
            order.add(current);
            for (String neighbor : graph.getOrDefault(current, List.of())) {
                if (!visited.contains(neighbor)) stack.push(neighbor);
            }
        }
        return order;
    }

    static void intermediateLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("D"),
            "C", List.of(),
            "D", List.of());

        System.out.println("intermediate: iterative DFS order from A -> " + dfsIterative(graph, "A"));
    }

    // Advanced: use DFS to count connected components -- restart from every unvisited vertex.
    static int countComponentsDFS(Map<String, List<String>> graph, Set<String> allVertices) {
        Set<String> visited = new HashSet<>();
        int components = 0;
        for (String vertex : allVertices) {
            if (!visited.contains(vertex)) {
                components++;
                dfsRecursive(graph, vertex, visited, new ArrayList<>()); // order not needed here, only the visited marking
            }
        }
        return components;
    }

    static void advancedLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B"), "B", List.of("A"),
            "C", List.of("D"), "D", List.of("C"),
            "E", List.of());

        int components = countComponentsDFS(graph, Set.of("A", "B", "C", "D", "E"));
        System.out.println("advanced: connected components -> " + components + " (expected 3: {A,B}, {C,D}, {E})");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `DepthFirstSearch.java`, then run `java DepthFirstSearch.java`.

## 6. Walkthrough

1. `basicLevel()` starts at `A`, visits it, then recurses into its first unvisited neighbor, `B`. From `B`, it recurses into `D` (a leaf, so it immediately returns). Only after that entire `B -> D` branch is fully explored does the recursion return to `A`'s loop and try the next neighbor, `C`. Final order: `A, B, D, C`.
2. `intermediateLevel()` performs the same traversal with an explicit stack instead of recursion. Pushing `A`, then popping it and pushing its neighbors `B` and `C` (in that order — so `C` ends up on top), the next pop retrieves `C` first, *not* `B` — the exact order depends on how neighbors are pushed, since a stack reverses the push order relative to recursion's natural left-to-right exploration. This is a common subtlety: iterative and recursive DFS can visit siblings in a different relative order, though both share the same "go deep before wide" character.
3. `advancedLevel()` reuses the same DFS helper to count connected components: it restarts DFS from every vertex not yet visited by a previous call. `{A, B}` get marked together in one DFS call, `{C, D}` in a second, and `{E}` (an isolated vertex with no edges) in a third — correctly reporting `3` components.

## 7. Gotchas & takeaways

> Gotcha: iterative DFS (stack-based) and recursive DFS can visit sibling branches in a different order, because pushing multiple neighbors onto a stack reverses their relative processing order compared to a simple recursive loop — if your algorithm's correctness depends on visiting neighbors in a specific order, verify which form you are actually using.

- DFS goes deep before wide, using a stack (explicit or via recursion); BFS goes wide before deep, using a queue — otherwise the algorithms are nearly identical in structure.
- DFS is the right tool for exhaustive exploration tasks: cycle detection, topological sort, and counting connected components — not for shortest-path-by-edge-count, which is BFS's job.
- An iterative, stack-based DFS avoids recursion depth limits, useful for very deep or very large graphs where recursive DFS could overflow the call stack.
- Related concepts: [Breadth-first search (BFS)](0144-breadth-first-search-bfs.md), [Topological sort](0146-topological-sort.md), [Connectivity & components](0138-connectivity-components.md).
