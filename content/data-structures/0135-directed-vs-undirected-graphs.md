---
card: data-structures
gi: 135
slug: directed-vs-undirected-graphs
title: Directed vs undirected graphs
---

## 1. What it is

A **graph** is a set of **vertices** (nodes) connected by **edges**. In an **undirected** graph, an edge between `A` and `B` means the connection goes both ways — you can travel from `A` to `B` and from `B` to `A`. In a **directed** graph (a **digraph**), an edge has a direction — an edge from `A` to `B` lets you travel `A -> B`, but not necessarily `B -> A`.

## 2. Why & when

The choice of directed versus undirected is not a technical detail — it is a modeling decision that must match the real relationship you are representing. A friendship on a social network is naturally undirected (if `A` is friends with `B`, `B` is friends with `A`). A "follows" relationship, a one-way street, or a dependency ("task A must finish before task B") is naturally directed, since the relationship does not automatically reverse.

## 3. Core concept

**The structural difference.** An undirected edge `{A, B}` is symmetric — it represents one connection, usable in both directions. A directed edge `(A, B)` is asymmetric — it represents a connection usable only from `A` to `B`; a separate edge `(B, A)` would be needed for the reverse to also be possible.

**How this changes adjacency.** In an undirected graph, if `B` is a neighbor of `A`, then `A` is always also a neighbor of `B` — the "neighbor" relationship is symmetric. In a directed graph, `B` being reachable from `A` (via an outgoing edge) says nothing about whether `A` is reachable from `B` — you must track **out-edges** and **in-edges** separately if both directions matter.

**Representing an undirected graph as directed.** Any undirected graph can be modeled as a directed graph by adding *two* directed edges for every undirected one — `(A, B)` and `(B, A)`. This is a common implementation trick: many graph libraries only implement directed-graph logic internally, and simulate "undirected" by always inserting edges in both directions.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An undirected graph with a plain line between A and B usable both ways, next to a directed graph with an arrow from A to B usable only one way">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#8b949e" text-anchor="middle">undirected: A -- B (both ways)</text>
    <circle cx="100" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="220" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="220" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <line x1="118" y1="60" x2="202" y2="60" stroke="#79c0ff" stroke-width="2"/>
    <text x="160" y="100" fill="#79c0ff" text-anchor="middle" font-size="9">A-&gt;B and B-&gt;A both valid</text>

    <text x="480" y="16" fill="#f0883e" text-anchor="middle">directed: A -&gt; B (one way only)</text>
    <circle cx="430" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="430" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="550" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="550" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <line x1="448" y1="60" x2="530" y2="60" stroke="#f0883e" stroke-width="2" marker-end="url(#arrow)"/>
    <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
    <text x="490" y="100" fill="#f0883e" text-anchor="middle" font-size="9">only A-&gt;B valid; B-&gt;A needs a separate edge</text>
  </g>
</svg>

The undirected edge is symmetric by definition; the directed edge only allows travel in the direction the arrow points, unless a second, separate edge is added for the reverse.

## 5. Runnable example

```java
// DirectedVsUndirected.java
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class DirectedVsUndirected {

    // Basic: an undirected graph, implemented by adding BOTH directions for every edge added.
    static class UndirectedGraph {
        Map<String, Set<String>> adjacency = new HashMap<>();

        void addEdge(String a, String b) {
            adjacency.computeIfAbsent(a, key -> new HashSet<>()).add(b);
            adjacency.computeIfAbsent(b, key -> new HashSet<>()).add(a); // the reverse direction, added automatically
        }

        boolean isConnected(String a, String b) {
            return adjacency.getOrDefault(a, Set.of()).contains(b);
        }
    }

    static void basicLevel() {
        UndirectedGraph graph = new UndirectedGraph();
        graph.addEdge("A", "B");

        System.out.println("basic: isConnected(A, B) -> " + graph.isConnected("A", "B"));
        System.out.println("basic: isConnected(B, A) -> " + graph.isConnected("B", "A") + " (symmetric, as expected)");
    }

    // Intermediate: a directed graph, adding only ONE direction per addEdge call.
    static class DirectedGraph {
        Map<String, Set<String>> outEdges = new HashMap<>();

        void addEdge(String from, String to) {
            outEdges.computeIfAbsent(from, key -> new HashSet<>()).add(to); // ONLY this direction
        }

        boolean hasPath(String from, String to) {
            return outEdges.getOrDefault(from, Set.of()).contains(to);
        }
    }

    static void intermediateLevel() {
        DirectedGraph graph = new DirectedGraph();
        graph.addEdge("A", "B"); // "A follows B", say

        System.out.println("intermediate: hasPath(A, B) -> " + graph.hasPath("A", "B"));
        System.out.println("intermediate: hasPath(B, A) -> " + graph.hasPath("B", "A") + " (NOT symmetric -- no reverse edge exists)");
    }

    // Advanced: track BOTH in-edges and out-edges for a directed graph -- needed whenever "who points to me" matters too.
    static class DirectedGraphWithInEdges {
        Map<String, Set<String>> outEdges = new HashMap<>();
        Map<String, Set<String>> inEdges = new HashMap<>();

        void addEdge(String from, String to) {
            outEdges.computeIfAbsent(from, key -> new HashSet<>()).add(to);
            inEdges.computeIfAbsent(to, key -> new HashSet<>()).add(from); // track the reverse lookup separately
        }
    }

    static void advancedLevel() {
        DirectedGraphWithInEdges graph = new DirectedGraphWithInEdges();
        graph.addEdge("A", "C"); // A follows C
        graph.addEdge("B", "C"); // B follows C

        System.out.println("advanced: who does C follow (out-edges) -> " + graph.outEdges.getOrDefault("C", Set.of()));
        System.out.println("advanced: who follows C (in-edges) -> " + graph.inEdges.get("C"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `DirectedVsUndirected.java`, then run `java DirectedVsUndirected.java`.

## 6. Walkthrough

1. `basicLevel()` adds one undirected edge between `A` and `B`. Internally, `addEdge` inserts `B` into `A`'s set *and* `A` into `B`'s set — a single logical edge becomes two directed entries under the hood. `isConnected` therefore returns `true` in both directions, matching the symmetric nature of an undirected edge.
2. `intermediateLevel()` adds one directed edge from `A` to `B`, modeling "A follows B." `addEdge` only ever inserts into `outEdges.get("A")`, never touching `B`'s entry. `hasPath("A", "B")` is `true`, but `hasPath("B", "A")` is `false` — there is no edge in that direction at all, unless it was explicitly added.
3. `advancedLevel()` shows why a directed graph often needs to track edges in both directions internally (not to make it undirected, but to answer both "who do I point to" and "who points to me"). `A` and `B` both follow `C`; `C`'s `outEdges` correctly shows nobody (C follows no one), while `C`'s `inEdges` correctly lists both `A` and `B` as followers.

## 7. Gotchas & takeaways

> Gotcha: modeling a naturally directed relationship (like "follows" or "depends on") as undirected — by always adding both directions — silently creates relationships that do not exist in the real data (e.g. implying `B` follows `A` just because `A` follows `B`), which can corrupt any algorithm relying on the direction being meaningful.

- An undirected edge is symmetric (`A-B` implies `B-A`); a directed edge is not — the reverse only exists if explicitly added.
- Any undirected graph can be simulated as a directed graph by adding both directions for every edge.
- A directed graph often needs separate in-edge and out-edge tracking, depending on which direction(s) your algorithms need to query.
- Related concepts: [Weighted vs unweighted graphs](0136-weighted-vs-unweighted-graphs.md), [Cyclic vs acyclic (DAG)](0137-cyclic-vs-acyclic-dag.md), [Modeling a graph in Java (Map<V, List<V>>)](0143-modeling-a-graph-in-java-map-v-list-v.md).
