---
card: data-structures
gi: 146
slug: topological-sort
title: Topological sort
---

## 1. What it is

A **topological sort** orders the vertices of a directed acyclic graph (DAG) so that every edge points from an earlier vertex to a later one in the ordering. If task `A` must finish before task `B` (an edge `A -> B`), a valid topological order always lists `A` before `B`. Multiple valid orderings can exist for the same DAG; topological sort finds *one* of them, not necessarily a unique answer.

## 2. Why & when

Topological sort is exactly the tool for "what order should these dependent tasks run in?" — build systems (compile dependencies before the things that need them), course scheduling (prerequisites before the course), and package installation (install dependencies before the package). It only works on a DAG: a cycle would require some vertex to come both before and after another, which is logically impossible.

## 3. Core concept

**Kahn's algorithm (BFS-based).** Compute every vertex's **in-degree** (how many edges point into it). Start with all vertices that have in-degree `0` (nothing depends on them being done first) in a queue. Repeatedly dequeue a vertex, add it to the result, and decrement the in-degree of each of its neighbors; whenever a neighbor's in-degree drops to `0`, enqueue it. If the result includes every vertex, the sort succeeded; if not, a cycle exists somewhere, and no valid order is possible.

**DFS-based approach (postorder reversal).** Run DFS from every unvisited vertex. Each time a vertex's DFS call *finishes* (all its descendants have been fully explored), push it onto a stack. After all DFS calls complete, popping the stack gives a valid topological order — this works because a vertex only finishes after everything reachable from it has already finished, so it is correctly placed *before* everything it depends on being placed after it.

**Why Kahn's algorithm doubles as cycle detection.** If a cycle exists, every vertex in that cycle always has in-degree at least `1` contributed by another vertex in the same cycle — none of them can ever reach in-degree `0` through the normal process, so they never get enqueued. If the final result list has fewer vertices than the graph, a cycle is present.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A dependency graph where compile must happen before both test and lint, and test must happen before deploy, showing one valid topological order: compile, lint, test, deploy">
  <g font-family="sans-serif" font-size="11">
    <circle cx="120" cy="100" r="20" fill="#0d1117" stroke="#f0883e"/><text x="120" y="98" fill="#e6edf3" text-anchor="middle" font-size="7">compile</text><text x="120" y="108" fill="#e6edf3" text-anchor="middle" font-size="6">in=0</text>
    <circle cx="280" cy="50" r="20" fill="#161b22" stroke="#79c0ff"/><text x="280" y="48" fill="#e6edf3" text-anchor="middle" font-size="7">lint</text><text x="280" y="58" fill="#e6edf3" text-anchor="middle" font-size="6">in=1</text>
    <circle cx="280" cy="150" r="20" fill="#161b22" stroke="#79c0ff"/><text x="280" y="148" fill="#e6edf3" text-anchor="middle" font-size="7">test</text><text x="280" y="158" fill="#e6edf3" text-anchor="middle" font-size="6">in=1</text>
    <circle cx="450" cy="150" r="20" fill="#161b22" stroke="#8b949e"/><text x="450" y="148" fill="#e6edf3" text-anchor="middle" font-size="6">deploy</text><text x="450" y="158" fill="#e6edf3" text-anchor="middle" font-size="6">in=1</text>
    <line x1="138" y1="88" x2="262" y2="60" stroke="#79c0ff" stroke-width="2" marker-end="url(#a3)"/>
    <line x1="138" y1="112" x2="262" y2="140" stroke="#79c0ff" stroke-width="2" marker-end="url(#a3)"/>
    <line x1="300" y1="150" x2="430" y2="150" stroke="#8b949e" stroke-width="2" marker-end="url(#a3)"/>
    <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="300" y="195" fill="#79c0ff" text-anchor="middle" font-size="10">valid order: compile, lint, test, deploy (or compile, test, lint, deploy)</text>
  </g>
</svg>

`compile` has in-degree `0`, so it goes first. Once `compile` is removed, both `lint` and `test` drop to in-degree `0` — either order between them is valid. `deploy` can only follow once `test` is done.

## 5. Runnable example

```java
// TopologicalSort.java
import java.util.*;

public class TopologicalSort {

    // Basic: Kahn's algorithm -- BFS driven by in-degree, processing in-degree-0 vertices first.
    static List<String> topologicalSort(Map<String, List<String>> graph, Set<String> allVertices) {
        Map<String, Integer> inDegree = new HashMap<>();
        for (String vertex : allVertices) inDegree.put(vertex, 0);
        for (List<String> neighbors : graph.values()) {
            for (String neighbor : neighbors) inDegree.merge(neighbor, 1, Integer::sum);
        }

        Queue<String> queue = new LinkedList<>();
        for (String vertex : allVertices) if (inDegree.get(vertex) == 0) queue.offer(vertex);

        List<String> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            String current = queue.poll();
            order.add(current);
            for (String neighbor : graph.getOrDefault(current, List.of())) {
                inDegree.merge(neighbor, -1, Integer::sum);
                if (inDegree.get(neighbor) == 0) queue.offer(neighbor);
            }
        }
        return order;
    }

    static void basicLevel() {
        Map<String, List<String>> graph = Map.of(
            "compile", List.of("lint", "test"),
            "lint", List.of(),
            "test", List.of("deploy"),
            "deploy", List.of());
        Set<String> allVertices = Set.of("compile", "lint", "test", "deploy");

        System.out.println("basic: one valid topological order -> " + topologicalSort(graph, allVertices));
    }

    // Intermediate: detect that a graph has NO valid order, because it contains a cycle.
    static void intermediateLevel() {
        Map<String, List<String>> cyclicGraph = Map.of(
            "A", List.of("B"),
            "B", List.of("C"),
            "C", List.of("A")); // closes a cycle back to A

        List<String> order = topologicalSort(cyclicGraph, Set.of("A", "B", "C"));
        System.out.println("intermediate: order length -> " + order.size() + " out of 3 vertices -> "
            + (order.size() < 3 ? "cycle detected -- no valid topological order exists" : "success"));
    }

    // Advanced: DFS-based approach (postorder reversal), producing an equally valid (possibly different) order.
    static void dfsTopoHelper(Map<String, List<String>> graph, String current, Set<String> visited, Deque<String> stack) {
        visited.add(current);
        for (String neighbor : graph.getOrDefault(current, List.of())) {
            if (!visited.contains(neighbor)) dfsTopoHelper(graph, neighbor, visited, stack);
        }
        stack.push(current); // push AFTER all descendants are fully explored
    }

    static List<String> topologicalSortDFS(Map<String, List<String>> graph, Set<String> allVertices) {
        Set<String> visited = new HashSet<>();
        Deque<String> stack = new ArrayDeque<>();
        for (String vertex : allVertices) {
            if (!visited.contains(vertex)) dfsTopoHelper(graph, vertex, visited, stack);
        }
        List<String> order = new ArrayList<>();
        while (!stack.isEmpty()) order.add(stack.pop()); // popping reverses postorder into a valid topological order
        return order;
    }

    static void advancedLevel() {
        Map<String, List<String>> graph = Map.of(
            "compile", List.of("lint", "test"),
            "lint", List.of(),
            "test", List.of("deploy"),
            "deploy", List.of());
        Set<String> allVertices = Set.of("compile", "lint", "test", "deploy");

        System.out.println("advanced: DFS-based topological order -> " + topologicalSortDFS(graph, allVertices));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TopologicalSort.java`, then run `java TopologicalSort.java`.

## 6. Walkthrough

1. `basicLevel()` computes in-degrees: `compile` has in-degree `0` (nothing points to it); `lint` and `test` each have in-degree `1` (from `compile`); `deploy` has in-degree `1` (from `test`). `compile` starts in the queue alone. Processing it decrements `lint`'s and `test`'s in-degrees to `0`, enqueueing both. Processing `lint` (or `test`, depending on queue order) does not unlock anything new (its own neighbor list is empty). Processing `test` decrements `deploy`'s in-degree to `0`, enqueueing it last. Final order: `compile, lint, test, deploy` (or `compile, test, lint, deploy` — both are valid).
2. `intermediateLevel()` runs the same algorithm on a 3-vertex cycle. Every vertex has in-degree `1` (each is pointed to by exactly one other vertex in the cycle), so *none* of them ever reaches in-degree `0` — the queue starts empty, and the algorithm terminates immediately with an empty result. Since `order.size() = 0 < 3`, this correctly signals a cycle, with no valid topological order possible.
3. `advancedLevel()` uses the DFS-based approach on the same dependency graph from `basicLevel()`. DFS from `compile` recurses into `lint` (a leaf, pushed first), returns, then recurses into `test`, which recurses into `deploy` (a leaf, pushed next), then `test` is pushed, and finally `compile` is pushed last. Popping the stack in LIFO order yields `compile, test, deploy, lint` (or a similar valid variant) — a different order from Kahn's algorithm's result, but equally valid, since both satisfy every dependency edge.

## 7. Gotchas & takeaways

> Gotcha: a topological order is not unique — different valid orderings can exist for the same DAG (e.g. `lint` and `test` above could run in either order relative to each other), so do not assume there is one "correct" answer to compare against; any order where every edge points forward is correct.

- Kahn's algorithm (BFS by in-degree) and DFS-with-postorder-reversal both produce valid topological orders; they may differ from each other, and both are correct.
- Topological sort only works on a DAG — if the result includes fewer vertices than the graph has, a cycle exists and no valid order is possible.
- This doubles as a cycle-detection technique for directed graphs: an incomplete Kahn's-algorithm result proves a cycle exists.
- Related concepts: [Cyclic vs acyclic (DAG)](0137-cyclic-vs-acyclic-dag.md), [Breadth-first search (BFS)](0144-breadth-first-search-bfs.md), [Depth-first search (DFS)](0145-depth-first-search-dfs.md).
