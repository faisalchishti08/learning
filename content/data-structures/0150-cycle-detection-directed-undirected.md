---
card: data-structures
gi: 150
slug: cycle-detection-directed-undirected
title: Cycle detection (directed & undirected)
---

## 1. What it is

Detecting a cycle means different code depending on whether the graph is directed or undirected. [Cyclic vs acyclic (DAG)](0137-cyclic-vs-acyclic-dag.md) covered the directed case (three-state DFS: unvisited, in-stack, done). This topic covers the **undirected** case, which needs a different trick — and contrasts it directly against the directed version, since naively reusing directed-graph logic on an undirected graph gives wrong answers.

## 2. Why & when

Applying directed-graph cycle detection to an undirected graph produces false positives: in an undirected graph, every edge `{A, B}` is stored as *two* directed entries (`A -> B` and `B -> A`), so a naive DFS would immediately see the edge back to the vertex it just came from and incorrectly report a cycle — even for a graph as simple as two vertices connected by one edge. Correct undirected cycle detection needs to explicitly ignore "the edge you just arrived through."

## 3. Core concept

**Undirected cycle detection via DFS, tracking the parent.** Run DFS, but pass along the vertex you arrived *from* (the parent in the DFS tree). For each neighbor: if the neighbor is unvisited, recurse into it (passing the current vertex as its parent). If the neighbor **is** visited **and is not the parent you just came from**, you have found a genuine cycle — an edge connecting back to some other already-visited vertex, not just the immediate edge you arrived on.

**Why tracking the parent (not just "visited") is required.** Every undirected edge `{A, B}` is stored as both `A -> B` and `B -> A`. When DFS moves from `A` to `B`, `B`'s neighbor list includes `A` — the *very edge just used*, in reverse. Without excluding the parent, this reverse entry always looks like "a visited neighbor," incorrectly flagging every single edge as a cycle.

**Directed cycle detection, contrasted.** A directed graph has no such reverse-edge artifact (an edge `A -> B` does not imply `B -> A` exists at all), so directed cycle detection instead needs the three-state approach: distinguishing a vertex still on the current DFS path (`IN_STACK`) from one fully finished (`DONE`) — see [Cyclic vs acyclic (DAG)](0137-cyclic-vs-acyclic-dag.md) for the full mechanism. The undirected version only needs two states (visited or not) plus the parent check, since there is no equivalent "still in progress vs finished" distinction to make.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An undirected graph with a single edge A-B: DFS from A to B sees the reverse edge back to A, which is correctly ignored because A is B's parent, not a cycle">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#79c0ff" text-anchor="middle">A-B (single edge, no cycle)</text>
    <circle cx="100" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="220" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="220" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <line x1="118" y1="60" x2="202" y2="60" stroke="#79c0ff" stroke-width="2"/>
    <text x="160" y="100" fill="#79c0ff" text-anchor="middle" font-size="9">DFS: A-&gt;B, sees B's edge back to A -- A is B's PARENT, correctly ignored</text>

    <text x="480" y="16" fill="#f0883e" text-anchor="middle">A-B-C-A (genuine cycle)</text>
    <circle cx="480" cy="50" r="16" fill="#161b22" stroke="#f0883e"/><text x="480" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="430" cy="130" r="16" fill="#161b22" stroke="#f0883e"/><text x="430" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="530" cy="130" r="16" fill="#161b22" stroke="#f0883e"/><text x="530" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="468" y1="62" x2="442" y2="118" stroke="#f0883e" stroke-width="2"/>
    <line x1="446" y1="130" x2="514" y2="130" stroke="#f0883e" stroke-width="2"/>
    <line x1="518" y1="118" x2="492" y2="62" stroke="#f0883e" stroke-width="2"/>
    <text x="480" y="180" fill="#f0883e" text-anchor="middle" font-size="9">DFS: A-&gt;B-&gt;C sees C's edge to A -- A is NOT C's parent (B is) -- genuine cycle</text>
  </g>
</svg>

Left: a single edge, no cycle — `B`'s edge back to `A` is correctly ignored, since `A` is `B`'s parent in the DFS tree. Right: a triangle — `C`'s edge back to `A` is a genuine cycle, since `C`'s parent is `B`, not `A`.

## 5. Runnable example

```java
// CycleDetectionBoth.java
import java.util.*;

public class CycleDetectionBoth {

    // Basic: undirected cycle detection -- track the parent, ignore the immediate reverse edge.
    static boolean hasUndirectedCycle(Map<String, List<String>> graph, Set<String> allVertices) {
        Set<String> visited = new HashSet<>();
        for (String vertex : allVertices) {
            if (!visited.contains(vertex)) {
                if (dfsUndirected(graph, vertex, null, visited)) return true;
            }
        }
        return false;
    }

    static boolean dfsUndirected(Map<String, List<String>> graph, String current, String parent, Set<String> visited) {
        visited.add(current);
        for (String neighbor : graph.getOrDefault(current, List.of())) {
            if (neighbor.equals(parent)) continue; // the edge just arrived on -- NOT a cycle, always skip it
            if (visited.contains(neighbor)) return true; // a visited vertex that is NOT the parent -- genuine cycle
            if (dfsUndirected(graph, neighbor, current, visited)) return true;
        }
        return false;
    }

    static void basicLevel() {
        Map<String, List<String>> singleEdge = Map.of("A", List.of("B"), "B", List.of("A"));
        System.out.println("basic: single edge A-B has a cycle? -> " + hasUndirectedCycle(singleEdge, Set.of("A", "B")));
    }

    // Intermediate: the triangle case -- a genuine undirected cycle.
    static void intermediateLevel() {
        Map<String, List<String>> triangle = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("A", "C"),
            "C", List.of("A", "B"));

        System.out.println("intermediate: triangle A-B-C has a cycle? -> " + hasUndirectedCycle(triangle, Set.of("A", "B", "C")));
    }

    // Advanced: directed cycle detection (three-state DFS), contrasted directly against the undirected version on similar-looking data.
    enum State { UNVISITED, IN_STACK, DONE }

    static boolean hasDirectedCycle(Map<String, List<String>> graph, Set<String> allVertices) {
        Map<String, State> state = new HashMap<>();
        for (String v : allVertices) state.put(v, State.UNVISITED);

        for (String vertex : allVertices) {
            if (state.get(vertex) == State.UNVISITED && dfsDirected(graph, vertex, state)) return true;
        }
        return false;
    }

    static boolean dfsDirected(Map<String, List<String>> graph, String current, Map<String, State> state) {
        state.put(current, State.IN_STACK);
        for (String neighbor : graph.getOrDefault(current, List.of())) {
            State neighborState = state.getOrDefault(neighbor, State.UNVISITED);
            if (neighborState == State.IN_STACK) return true;
            if (neighborState == State.UNVISITED && dfsDirected(graph, neighbor, state)) return true;
        }
        state.put(current, State.DONE);
        return false;
    }

    static void advancedLevel() {
        // The SAME connectivity as the triangle above, but stored as ONE-WAY directed edges -- no cycle exists directed-wise.
        Map<String, List<String>> directedTriangleShape = Map.of(
            "A", List.of("B"),
            "B", List.of("C"),
            "C", List.of()); // no edge back to A -- NOT a directed cycle, unlike the undirected triangle

        System.out.println("advanced: directed A->B->C (no edge back) has a directed cycle? -> "
            + hasDirectedCycle(directedTriangleShape, Set.of("A", "B", "C")));
        System.out.println("advanced: but treating the SAME 3 vertices as undirected with all 3 edges IS a cycle -- "
            + "the direction of edges fundamentally changes the answer, not just the algorithm used");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CycleDetectionBoth.java`, then run `java CycleDetectionBoth.java`.

## 6. Walkthrough

1. `basicLevel()` checks a single undirected edge `A-B` (stored as both `A -> B` and `B -> A`). DFS starts at `A` (parent `null`), visits `B` (parent `A`). From `B`, its only neighbor is `A` — which equals `B`'s parent, so it is explicitly skipped via `continue`. No cycle is found, correctly.
2. `intermediateLevel()` checks a triangle: `A-B`, `B-C`, `A-C`. DFS from `A` (parent `null`) visits `B` (parent `A`), then from `B` visits `C` (parent `B`). From `C`, its neighbors are `A` and `B`. `B` equals `C`'s parent, skipped. But `A` is visited and is **not** `C`'s parent (`B` is) — this correctly triggers `true`, a genuine cycle.
3. `advancedLevel()` takes the same three vertices, but with edges stored as one-way directed entries (`A -> B -> C`, no edge back to `A`). Running the three-state directed cycle check finds no cycle at all — `C` finishes with no back edge to any `IN_STACK` vertex. This makes the key point explicit: the *same three vertices* can be cyclic or acyclic depending purely on whether the connections are directed or undirected — the algorithm must match the graph's actual nature, not just be "a cycle detector."

## 7. Gotchas & takeaways

> Gotcha: applying directed-graph cycle detection (or vice versa) to the wrong kind of graph gives wrong answers, not just suboptimal ones — an undirected graph run through naive directed-style checking (without the parent-skip) reports a cycle on nearly every edge, since the automatically-added reverse edge always looks like a back-reference.

- Undirected cycle detection needs to track and skip the parent vertex — visiting a vertex that is *not* the parent, but already visited, is the correct signal for a genuine cycle.
- Directed cycle detection needs three states (unvisited, in-stack, done), since a directed graph has no automatic reverse edge to filter out.
- The same set of vertices can be cyclic as an undirected graph but acyclic as a directed graph (or vice versa) — direction is not a detail, it changes the actual answer.
- Related concepts: [Cyclic vs acyclic (DAG)](0137-cyclic-vs-acyclic-dag.md), [Connectivity & components](0138-connectivity-components.md), [Depth-first search (DFS)](0145-depth-first-search-dfs.md).
