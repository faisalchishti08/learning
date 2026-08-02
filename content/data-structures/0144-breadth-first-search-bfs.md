---
card: data-structures
gi: 144
slug: breadth-first-search-bfs
title: Breadth-first search (BFS)
---

## 1. What it is

**Breadth-first search (BFS)** explores a graph level by level: it visits every neighbor of the start vertex first, then every neighbor of those neighbors, and so on — expanding outward in "rings" of increasing distance from the start, using a queue to process vertices in the order they were discovered.

## 2. Why & when

BFS is the correct algorithm whenever "shortest path" means "fewest edges" — an unweighted graph's shortest path, the minimum number of moves in a puzzle, or the fewest connections between two people in a social network. Because it explores in strict distance order (everything at distance `1` before anything at distance `2`), the *first* time BFS reaches a vertex, it has found the shortest possible path to it — no shorter path could exist, or BFS would have found it already.

## 3. Core concept

**How the operation works.** Start by enqueueing the start vertex and marking it visited. Repeatedly: dequeue a vertex, and for each of its unvisited neighbors, mark them visited and enqueue them. Continue until the queue is empty.

**Why marking "visited" at enqueue time, not dequeue time, matters.** If you mark a vertex visited only when you dequeue it, the same vertex can be enqueued multiple times by different neighbors before any of those copies is processed — wasting work, and in the worst case, breaking the shortest-path guarantee, since a vertex might be enqueued at the wrong (larger) distance from a later-processed neighbor. Marking visited immediately at enqueue time guarantees each vertex is enqueued exactly once, at its true shortest distance.

**Using BFS for shortest path.** Track each vertex's distance as it is discovered: the start vertex has distance `0`; any vertex first discovered while processing a vertex at distance `d` gets distance `d + 1`. Because BFS processes the queue in FIFO order, every vertex at distance `d` is fully processed before any vertex at distance `d + 1` is discovered — this is what guarantees correctness.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS expanding outward from vertex A in rings: A at distance 0, B and C at distance 1, D at distance 2, visiting every vertex at one distance before moving to the next">
  <g font-family="sans-serif" font-size="11">
    <circle cx="150" cy="100" r="18" fill="#0d1117" stroke="#f0883e"/><text x="150" y="104" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <text x="150" y="130" fill="#f0883e" text-anchor="middle" font-size="9">dist 0</text>
    <circle cx="300" cy="50" r="18" fill="#161b22" stroke="#79c0ff"/><text x="300" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <text x="300" y="80" fill="#79c0ff" text-anchor="middle" font-size="9">dist 1</text>
    <circle cx="300" cy="150" r="18" fill="#161b22" stroke="#79c0ff"/><text x="300" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <text x="300" y="180" fill="#79c0ff" text-anchor="middle" font-size="9">dist 1</text>
    <circle cx="450" cy="50" r="18" fill="#161b22" stroke="#8b949e"/><text x="450" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <text x="450" y="80" fill="#8b949e" text-anchor="middle" font-size="9">dist 2</text>
    <line x1="166" y1="90" x2="284" y2="58" stroke="#79c0ff" stroke-width="2"/>
    <line x1="166" y1="110" x2="284" y2="142" stroke="#79c0ff" stroke-width="2"/>
    <line x1="318" y1="50" x2="432" y2="50" stroke="#8b949e" stroke-width="2"/>
    <text x="300" y="20" fill="#8b949e" text-anchor="middle" font-size="9">queue processes A, then B,C (dist 1), THEN D (dist 2) -- never out of order</text>
  </g>
</svg>

BFS fully processes every vertex at distance `1` (`B`, `C`) before discovering any vertex at distance `2` (`D`) — the FIFO queue enforces this strict, level-by-level order.

## 5. Runnable example

```java
// BreadthFirstSearch.java
import java.util.*;

public class BreadthFirstSearch {

    // Basic: plain BFS traversal order.
    static List<String> bfsOrder(Map<String, List<String>> graph, String start) {
        List<String> order = new ArrayList<>();
        Set<String> visited = new HashSet<>();
        Queue<String> queue = new LinkedList<>();

        queue.offer(start);
        visited.add(start); // mark visited at ENQUEUE time, not dequeue time

        while (!queue.isEmpty()) {
            String current = queue.poll();
            order.add(current);
            for (String neighbor : graph.getOrDefault(current, List.of())) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    queue.offer(neighbor);
                }
            }
        }
        return order;
    }

    static void basicLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("A", "D"),
            "C", List.of("A", "D"),
            "D", List.of("B", "C"));

        System.out.println("basic: BFS order from A -> " + bfsOrder(graph, "A"));
    }

    // Intermediate: BFS for shortest-path DISTANCE (fewest edges), tracking each vertex's discovery distance.
    static Map<String, Integer> bfsDistances(Map<String, List<String>> graph, String start) {
        Map<String, Integer> distance = new HashMap<>();
        Queue<String> queue = new LinkedList<>();

        distance.put(start, 0);
        queue.offer(start);

        while (!queue.isEmpty()) {
            String current = queue.poll();
            for (String neighbor : graph.getOrDefault(current, List.of())) {
                if (!distance.containsKey(neighbor)) {
                    distance.put(neighbor, distance.get(current) + 1); // one more edge than the current vertex
                    queue.offer(neighbor);
                }
            }
        }
        return distance;
    }

    static void intermediateLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("A", "D"),
            "C", List.of("A", "D"),
            "D", List.of("B", "C"));

        System.out.println("intermediate: distances from A -> " + bfsDistances(graph, "A"));
    }

    // Advanced: reconstruct the actual shortest PATH (not just distance), by tracking each vertex's predecessor.
    static List<String> shortestPath(Map<String, List<String>> graph, String start, String target) {
        Map<String, String> predecessor = new HashMap<>();
        Queue<String> queue = new LinkedList<>();
        Set<String> visited = new HashSet<>();

        queue.offer(start);
        visited.add(start);

        while (!queue.isEmpty()) {
            String current = queue.poll();
            if (current.equals(target)) break;
            for (String neighbor : graph.getOrDefault(current, List.of())) {
                if (!visited.contains(neighbor)) {
                    visited.add(neighbor);
                    predecessor.put(neighbor, current);
                    queue.offer(neighbor);
                }
            }
        }

        LinkedList<String> path = new LinkedList<>();
        String step = target;
        while (step != null) {
            path.addFirst(step);
            step = predecessor.get(step);
        }
        return path;
    }

    static void advancedLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("B", "C"),
            "B", List.of("A", "D"),
            "C", List.of("A", "D"),
            "D", List.of("B", "C"));

        System.out.println("advanced: shortest path A to D -> " + shortestPath(graph, "A", "D"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BreadthFirstSearch.java`, then run `java BreadthFirstSearch.java`.

## 6. Walkthrough

1. `basicLevel()` starts BFS at `A`. `A` is dequeued first and its unvisited neighbors, `B` and `C`, are marked visited and enqueued. Next, `B` is dequeued; its neighbor `D` is unvisited, so it is marked visited and enqueued. `C` is dequeued next; its neighbor `D` is *already* visited (marked when `B` enqueued it), so it is correctly skipped, avoiding a duplicate enqueue. Final order: `A, B, C, D`.
2. `intermediateLevel()` tracks distance instead of just order. `A` starts at distance `0`. `B` and `C`, discovered while processing `A`, get distance `1`. `D`, discovered while processing `B` (or `C` — whichever is dequeued first), gets distance `2`. The result correctly shows `A:0, B:1, C:1, D:2`.
3. `advancedLevel()` additionally tracks each vertex's predecessor — the vertex that first discovered it. Working backward from `D` (predecessor `B`, whose predecessor is `A`) and reversing the resulting chain reconstructs the actual shortest path: `[A, B, D]`.

## 7. Gotchas & takeaways

> Gotcha: marking a vertex "visited" when it is *dequeued*, instead of when it is *enqueued*, lets the same vertex be added to the queue multiple times before being processed — this wastes work and, in graphs with many shared neighbors, can be a significant and easily overlooked inefficiency.

- BFS explores level by level using a FIFO queue, guaranteeing the first time it reaches any vertex is via a shortest (fewest-edges) path.
- Always mark a vertex visited at enqueue time, not dequeue time, to avoid duplicate enqueues and preserve the shortest-path guarantee.
- Tracking each vertex's discovery distance (or predecessor) turns plain BFS traversal into a full shortest-path (or shortest-path-reconstruction) algorithm.
- Related concepts: [Depth-first search (DFS)](0145-depth-first-search-dfs.md), [Weighted vs unweighted graphs](0136-weighted-vs-unweighted-graphs.md).
