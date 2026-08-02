---
card: data-structures
gi: 138
slug: connectivity-components
title: Connectivity & components
---

## 1. What it is

A graph is **connected** if there is a path between every pair of vertices. If it is not fully connected, it breaks apart into **connected components** — maximal groups of vertices where every vertex can reach every other vertex within the same group, but not any vertex outside it. For directed graphs, this idea splits further into **weakly connected** (connected if you ignore edge direction) and **strongly connected** (connected even respecting edge direction, both ways).

## 2. Why & when

Many real questions reduce to "is everything reachable from everything else?" or "how many separate clusters exist?" — social network friend groups, whether a computer network has an isolated segment, or whether a maze has an unreachable region. Counting connected components is also the basis for detecting cycles in an undirected graph via Union-Find, and for deciding whether adding one more edge would ever create a cycle.

## 3. Core concept

**Finding connected components (undirected graphs).** Run a traversal (BFS or DFS) from any unvisited vertex; every vertex reached in that traversal belongs to the same component. Repeat from the next unvisited vertex, and so on — the number of times you have to restart the traversal equals the number of connected components.

**Weakly vs strongly connected (directed graphs).** A directed graph is **weakly connected** if replacing every directed edge with an undirected one would make it connected — meaning the vertices are "reachable from each other" only if you allow travel against edge direction. It is **strongly connected** if you can travel from any vertex to any other *following edge direction correctly, in both directions* — a much stronger requirement.

**Why strong connectivity is harder to check.** Weak connectivity only needs one traversal, ignoring direction. Strong connectivity needs to confirm every vertex can reach every other vertex *respecting direction* both ways — the standard approach runs a DFS from one vertex (following normal edges), then a second DFS on the graph with every edge reversed, and checks that both traversals reach every vertex.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An undirected graph split into two connected components: one with vertices A, B, C connected together, and a separate isolated component with just vertex D">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#79c0ff" text-anchor="middle">component 1: {A, B, C}</text>
    <circle cx="100" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="200" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="150" cy="130" r="16" fill="#161b22" stroke="#79c0ff"/><text x="150" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="116" y1="60" x2="184" y2="60" stroke="#79c0ff" stroke-width="2"/>
    <line x1="112" y1="72" x2="138" y2="118" stroke="#79c0ff" stroke-width="2"/>
    <line x1="188" y1="72" x2="162" y2="118" stroke="#79c0ff" stroke-width="2"/>

    <text x="480" y="16" fill="#f0883e" text-anchor="middle">component 2: {D} (isolated)</text>
    <circle cx="480" cy="80" r="16" fill="#161b22" stroke="#f0883e"/><text x="480" y="84" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <text x="330" y="170" fill="#8b949e" text-anchor="middle" font-size="10">no edge connects the two groups -- 2 separate connected components</text>
  </g>
</svg>

`A`, `B`, `C` are mutually reachable, forming one component. `D` has no edges to any of them, forming its own separate, single-vertex component — the graph has exactly 2 connected components.

## 5. Runnable example

```java
// ConnectivityComponents.java
import java.util.*;

public class ConnectivityComponents {

    // Basic: count connected components in an undirected graph, using BFS restarted from each unvisited vertex.
    static int countComponents(Map<String, List<String>> graph, Set<String> allVertices) {
        Set<String> visited = new HashSet<>();
        int components = 0;

        for (String vertex : allVertices) {
            if (!visited.contains(vertex)) {
                components++;
                bfsMarkComponent(graph, vertex, visited);
            }
        }
        return components;
    }

    static void bfsMarkComponent(Map<String, List<String>> graph, String start, Set<String> visited) {
        Queue<String> queue = new LinkedList<>();
        queue.offer(start);
        visited.add(start);
        while (!queue.isEmpty()) {
            String current = queue.poll();
            for (String neighbor : graph.getOrDefault(current, List.of())) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    queue.offer(neighbor);
                }
            }
        }
    }

    static void basicLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B", "C"), "B", List.of("A", "C"), "C", List.of("A", "B"),
            "D", List.of());
        Set<String> allVertices = Set.of("A", "B", "C", "D");

        System.out.println("basic: connected components -> " + countComponents(graph, allVertices) + " (expected 2: {A,B,C} and {D})");
    }

    // Intermediate: weak connectivity in a directed graph -- ignore direction entirely.
    static boolean isWeaklyConnected(Map<String, List<String>> directedGraph, Set<String> allVertices) {
        Map<String, List<String>> undirectedView = new HashMap<>();
        for (String from : directedGraph.keySet()) {
            for (String to : directedGraph.get(from)) {
                undirectedView.computeIfAbsent(from, key -> new ArrayList<>()).add(to);
                undirectedView.computeIfAbsent(to, key -> new ArrayList<>()).add(from); // add the reverse too -- ignore direction
            }
        }
        return countComponents(undirectedView, allVertices) == 1;
    }

    static void intermediateLevel() {
        Map<String, List<String>> directedGraph = Map.of(
            "A", List.of("B"), "B", List.of("C")); // A->B->C, but no way back -- not strongly connected

        System.out.println("intermediate: A->B->C weakly connected? -> " + isWeaklyConnected(directedGraph, Set.of("A", "B", "C")));
    }

    // Advanced: strong connectivity -- must reach everyone in the ORIGINAL graph AND in the reversed graph.
    static boolean isStronglyConnected(Map<String, List<String>> directedGraph, Set<String> allVertices, String start) {
        Set<String> visitedForward = new HashSet<>();
        bfsMarkComponent(directedGraph, start, visitedForward);

        Map<String, List<String>> reversed = new HashMap<>();
        for (String from : directedGraph.keySet()) {
            for (String to : directedGraph.get(from)) {
                reversed.computeIfAbsent(to, key -> new ArrayList<>()).add(from); // flip every edge
            }
        }
        Set<String> visitedBackward = new HashSet<>();
        bfsMarkComponent(reversed, start, visitedBackward);

        return visitedForward.containsAll(allVertices) && visitedBackward.containsAll(allVertices);
    }

    static void advancedLevel() {
        Map<String, List<String>> cycle = Map.of(
            "A", List.of("B"), "B", List.of("C"), "C", List.of("A")); // A->B->C->A: a genuine cycle back to the start

        Map<String, List<String>> chain = Map.of(
            "A", List.of("B"), "B", List.of("C")); // A->B->C, no way back

        System.out.println("advanced: A->B->C->A strongly connected? -> " + isStronglyConnected(cycle, Set.of("A", "B", "C"), "A"));
        System.out.println("advanced: A->B->C (no cycle) strongly connected? -> " + isStronglyConnected(chain, Set.of("A", "B", "C"), "A"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ConnectivityComponents.java`, then run `java ConnectivityComponents.java`.

## 6. Walkthrough

1. `basicLevel()` runs BFS starting from each unvisited vertex in turn. Starting from `A` marks `A`, `B`, `C` as visited in one traversal (one component). `D` remains unvisited, so a second traversal starts there, marking only `D` (a second, separate component). Total: `2` components.
2. `intermediateLevel()` builds an undirected "view" of the directed chain `A -> B -> C`, adding the reverse of every edge. This makes `A`, `B`, `C` all mutually reachable while ignoring direction, so `countComponents` on that view returns `1`, confirming the graph is weakly connected — even though, respecting direction, you cannot get from `C` back to `A`.
3. `advancedLevel()` checks strong connectivity on two graphs: a genuine cycle (`A -> B -> C -> A`) and a plain chain (`A -> B -> C`). For the cycle, both a forward BFS from `A` and a backward BFS on the reversed graph reach every vertex — correctly strongly connected. For the chain, the reversed-graph BFS from `A` only reaches `A` itself (no edges point *into* `A` in the reversed graph, since nothing pointed to `A` originally), so `visitedBackward` does not contain `B` or `C` — correctly reporting the chain is not strongly connected.

## 7. Gotchas & takeaways

> Gotcha: weak connectivity is a much weaker guarantee than strong connectivity — a directed graph can be weakly connected (every vertex reachable if you ignore direction) while having entire vertices you can never actually reach from certain starting points when direction is respected.

- Connected components partition an undirected graph's vertices into maximal mutually-reachable groups; counting them just needs one traversal per unvisited vertex.
- Weak connectivity (directed graph, ignoring direction) only needs one traversal on an "undirected view"; strong connectivity needs two traversals — forward and on the reversed graph — both reaching every vertex.
- A directed cycle through all vertices guarantees strong connectivity for those vertices; a directed acyclic chain never can be strongly connected (there is no way back to the start).
- Related concepts: [Cyclic vs acyclic (DAG)](0137-cyclic-vs-acyclic-dag.md), [Breadth-first search (BFS)](0144-breadth-first-search-bfs.md).
