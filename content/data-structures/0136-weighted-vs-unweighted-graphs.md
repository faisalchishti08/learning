---
card: data-structures
gi: 136
slug: weighted-vs-unweighted-graphs
title: Weighted vs unweighted graphs
---

## 1. What it is

In an **unweighted** graph, every edge is treated as equally "costly" — traveling across any single edge counts the same as traveling across any other. In a **weighted** graph, each edge carries a numeric **weight** (a cost, distance, time, or capacity), and different edges can cost different amounts to traverse.

## 2. Why & when

The distinction determines which shortest-path algorithm is correct. "Shortest path" in an unweighted graph means "fewest edges" — found with a plain breadth-first search (BFS). "Shortest path" in a weighted graph means "lowest total weight," which BFS gets wrong, since it only counts edges, not their costs — you need Dijkstra's algorithm (or Bellman-Ford, for negative weights) instead. Road networks (distance or time per road), flight networks (cost or duration per flight), and network routing (latency per link) are all naturally weighted.

## 3. Core concept

**The structural difference.** An unweighted edge is just a pair `(from, to)` (or `{a, b}` if undirected). A weighted edge is a triple `(from, to, weight)` — the same connectivity information, plus one extra number.

**Why BFS breaks on weighted graphs.** BFS explores level by level, guaranteeing it finds the target using the fewest *edges* — correct exactly when every edge costs the same. On a weighted graph, a path using more edges can still have a lower total weight than a path using fewer, larger-weight edges. BFS has no way to account for that, since it only counts hops, not weight.

**Dijkstra's algorithm, briefly.** Dijkstra's uses a min-heap keyed by "total distance so far," always expanding the currently-cheapest-known vertex next, and relaxing (updating) neighbors' distances if a cheaper path through the current vertex is found. This correctly accounts for varying edge weights, as long as no edge weight is negative.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A graph where the direct edge from A to C costs 10, but the two hop path through B costs 1 plus 1 equals 2, making the longer path cheaper overall despite BFS preferring the direct edge">
  <g font-family="sans-serif" font-size="11">
    <circle cx="100" cy="100" r="18" fill="#161b22" stroke="#79c0ff"/><text x="100" y="104" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="300" cy="50" r="18" fill="#161b22" stroke="#79c0ff"/><text x="300" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="500" cy="100" r="18" fill="#161b22" stroke="#f0883e"/><text x="500" y="104" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="118" y1="100" x2="482" y2="100" stroke="#f0883e" stroke-width="2"/>
    <text x="300" y="90" fill="#f0883e" text-anchor="middle" font-size="9">weight 10 (1 edge -- BFS would pick this)</text>
    <line x1="115" y1="88" x2="285" y2="58" stroke="#79c0ff" stroke-width="2"/>
    <line x1="315" y1="58" x2="485" y2="88" stroke="#79c0ff" stroke-width="2"/>
    <text x="200" y="55" fill="#79c0ff" font-size="9">weight 1</text>
    <text x="400" y="55" fill="#79c0ff" font-size="9">weight 1</text>
    <text x="300" y="150" fill="#79c0ff" text-anchor="middle" font-size="10">A-&gt;B-&gt;C costs 1+1=2, cheaper than the direct A-&gt;C edge (10), despite using MORE edges</text>
  </g>
</svg>

BFS would prefer the direct `A -> C` edge (fewest edges: 1), but Dijkstra's correctly finds `A -> B -> C` as cheaper overall (total weight 2 versus 10), since it accounts for the actual edge weights, not just the hop count.

## 5. Runnable example

```java
// WeightedVsUnweighted.java
import java.util.*;

public class WeightedVsUnweighted {

    // Basic: unweighted graph -- BFS finds the path with the FEWEST edges, correctly, when all edges cost the same.
    static int bfsShortestHopCount(Map<String, List<String>> graph, String start, String target) {
        Queue<String> queue = new LinkedList<>();
        Map<String, Integer> distance = new HashMap<>();
        queue.offer(start);
        distance.put(start, 0);

        while (!queue.isEmpty()) {
            String current = queue.poll();
            if (current.equals(target)) return distance.get(current);
            for (String neighbor : graph.getOrDefault(current, List.of())) {
                if (!distance.containsKey(neighbor)) {
                    distance.put(neighbor, distance.get(current) + 1);
                    queue.offer(neighbor);
                }
            }
        }
        return -1;
    }

    static void basicLevel() {
        Map<String, List<String>> graph = Map.of(
            "A", List.of("C", "B"),
            "B", List.of("C"));
        System.out.println("basic: unweighted A->C, fewest edges -> " + bfsShortestHopCount(graph, "A", "C") + " (the direct edge, 1 hop)");
    }

    // Intermediate: the SAME graph shape, but now weighted -- BFS's "fewest edges" answer is no longer the cheapest.
    record Edge(String to, int weight) {}

    static int dijkstraShortestWeight(Map<String, List<Edge>> graph, String start, String target) {
        PriorityQueue<Edge> minHeap = new PriorityQueue<>(Comparator.comparingInt(Edge::weight));
        Map<String, Integer> best = new HashMap<>();
        minHeap.offer(new Edge(start, 0));

        while (!minHeap.isEmpty()) {
            Edge current = minHeap.poll();
            if (best.containsKey(current.to())) continue; // already finalized with a lower or equal cost
            best.put(current.to(), current.weight());
            if (current.to().equals(target)) return current.weight();

            for (Edge edge : graph.getOrDefault(current.to(), List.of())) {
                minHeap.offer(new Edge(edge.to(), current.weight() + edge.weight()));
            }
        }
        return -1;
    }

    static void intermediateLevel() {
        Map<String, List<Edge>> graph = Map.of(
            "A", List.of(new Edge("C", 10), new Edge("B", 1)),
            "B", List.of(new Edge("C", 1)));

        System.out.println("intermediate: weighted A->C, lowest total weight -> " + dijkstraShortestWeight(graph, "A", "C")
            + " (via A->B->C: 1+1=2, cheaper than the direct edge's weight of 10)");
    }

    // Advanced: show BFS gives the WRONG answer if naively reused on a weighted graph (it would report the direct edge, weight 10).
    static void advancedLevel() {
        Map<String, List<String>> unweightedView = Map.of(
            "A", List.of("C", "B"), // same connectivity, weights ignored
            "B", List.of("C"));

        int bfsHops = bfsShortestHopCount(unweightedView, "A", "C"); // BFS only sees "1 hop" via the direct edge
        Map<String, List<Edge>> weightedGraph = Map.of(
            "A", List.of(new Edge("C", 10), new Edge("B", 1)),
            "B", List.of(new Edge("C", 1)));
        int trueWeight = dijkstraShortestWeight(weightedGraph, "A", "C");

        System.out.println("advanced: BFS reports fewest-edges path uses " + bfsHops + " hop(s) (the direct edge, cost 10)");
        System.out.println("advanced: Dijkstra's correctly reports the true cheapest total weight -> " + trueWeight
            + " -- BFS's hop count does not reflect actual cost at all");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `WeightedVsUnweighted.java`, then run `java WeightedVsUnweighted.java`.

## 6. Walkthrough

1. `basicLevel()` runs BFS on an unweighted graph where `A` connects directly to `C`, and also to `B`, which connects to `C`. BFS correctly reports the fewest-edges path uses `1` hop — the direct `A -> C` edge — which is the right answer when every edge counts the same.
2. `intermediateLevel()` runs the same connectivity, but now each edge carries a weight: the direct `A -> C` edge costs `10`, while `A -> B -> C` costs `1 + 1 = 2`. Dijkstra's algorithm correctly finds the two-hop path as cheaper overall, since it tracks accumulated weight, not hop count.
3. `advancedLevel()` runs both algorithms side by side on the equivalent data, making the mismatch explicit: BFS's "fewest edges" answer (the direct edge, cost `10`) is not the cheapest path once weights are considered, while Dijkstra's total-weight answer (`2`) correctly reflects the true cheapest cost.

## 7. Gotchas & takeaways

> Gotcha: running BFS on a weighted graph, ignoring the weights, is a common but incorrect shortcut — it will confidently report a "shortest path" that is only shortest by *edge count*, which can be far more expensive than the true cheapest path in total weight.

- Unweighted "shortest path" means fewest edges (solved correctly by BFS); weighted "shortest path" means lowest total weight (needs Dijkstra's or Bellman-Ford).
- A weighted edge is just an unweighted edge plus one extra number; the graph's connectivity structure is otherwise identical.
- Dijkstra's algorithm requires non-negative weights; Bellman-Ford handles negative weights (at a higher time cost), and can also detect negative cycles.
- Related concepts: [Directed vs undirected graphs](0135-directed-vs-undirected-graphs.md), [Breadth-first search (BFS)](0144-breadth-first-search-bfs.md).
