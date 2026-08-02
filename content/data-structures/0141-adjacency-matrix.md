---
card: data-structures
gi: 141
slug: adjacency-matrix
title: Adjacency matrix
---

## 1. What it is

An **adjacency matrix** represents a graph with a 2D array (or grid) of size `V x V`, for `V` vertices. Cell `matrix[i][j]` holds whether an edge exists from vertex `i` to vertex `j` — often a boolean, or the edge's weight for a weighted graph (using a sentinel like `0` or infinity to mean "no edge").

## 2. Why & when

An adjacency matrix answers "does an edge from `i` to `j` exist?" in guaranteed `O(1)`, with no scanning at all — a fixed array lookup. It also makes some algorithms (like certain graph-based matrix operations, or Floyd-Warshall's all-pairs shortest path) naturally expressible as matrix operations. It costs `O(V^2)` memory regardless of how many edges actually exist, which makes it wasteful for **sparse** graphs but reasonable, or even ideal, for **dense** graphs (where a large fraction of possible vertex pairs are connected).

## 3. Core concept

**The structure's shape.** A `V x V` grid, indexed by vertex (using either integer indices directly, or a map from vertex name to a fixed index). For an undirected graph, the matrix is symmetric: `matrix[i][j] == matrix[j][i]` always. For a directed graph, it need not be.

**How the layout makes edge-existence checks fast.** Because every possible vertex pair has a dedicated, pre-allocated cell, checking an edge is just indexing into the array twice (`matrix[i][j]`) — no traversal, no hashing, guaranteed `O(1)`, regardless of how many edges the graph actually has.

**The tradeoff: listing neighbors is slower.** "Who are vertex `i`'s neighbors?" requires scanning an entire row (`O(V)`), checking every possible other vertex, even the ones with no edge — much worse than an adjacency list's `O(degree)` for the same query, especially when `V` is large and the graph is sparse (most row entries are "no edge").

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small graph next to its adjacency matrix, a 4 by 4 grid where most cells are zero except where an actual edge connects two vertices">
  <g font-family="sans-serif" font-size="11">
    <circle cx="100" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="100" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="200" cy="30" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="200" cy="90" r="16" fill="#161b22" stroke="#8b949e"/><text x="200" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <line x1="112" y1="50" x2="188" y2="35" stroke="#79c0ff" stroke-width="2"/>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">matrix[i][j] -- rows/cols: A, B, C</text>
    <rect x="410" y="25" width="30" height="24" fill="#161b22" stroke="#8b949e"/><text x="425" y="41" fill="#e6edf3" text-anchor="middle" font-size="8">0</text>
    <rect x="440" y="25" width="30" height="24" fill="#0d1117" stroke="#f0883e"/><text x="455" y="41" fill="#e6edf3" text-anchor="middle" font-size="8">1</text>
    <rect x="470" y="25" width="30" height="24" fill="#161b22" stroke="#8b949e"/><text x="485" y="41" fill="#e6edf3" text-anchor="middle" font-size="8">0</text>
    <rect x="410" y="49" width="30" height="24" fill="#0d1117" stroke="#f0883e"/><text x="425" y="65" fill="#e6edf3" text-anchor="middle" font-size="8">1</text>
    <rect x="440" y="49" width="30" height="24" fill="#161b22" stroke="#8b949e"/><text x="455" y="65" fill="#e6edf3" text-anchor="middle" font-size="8">0</text>
    <rect x="470" y="49" width="30" height="24" fill="#161b22" stroke="#8b949e"/><text x="485" y="65" fill="#e6edf3" text-anchor="middle" font-size="8">0</text>
    <rect x="410" y="73" width="30" height="24" fill="#161b22" stroke="#8b949e"/><text x="425" y="89" fill="#e6edf3" text-anchor="middle" font-size="8">0</text>
    <rect x="440" y="73" width="30" height="24" fill="#161b22" stroke="#8b949e"/><text x="455" y="89" fill="#e6edf3" text-anchor="middle" font-size="8">0</text>
    <rect x="470" y="73" width="30" height="24" fill="#161b22" stroke="#8b949e"/><text x="485" y="89" fill="#e6edf3" text-anchor="middle" font-size="8">0</text>
    <text x="450" y="130" fill="#8b949e" text-anchor="middle" font-size="9">only A-B has an edge; every other cell is 0 (no edge) -- most of the matrix is wasted for this sparse graph</text>
  </g>
</svg>

Only one edge (`A-B`) exists among three vertices, yet the matrix allocates all 9 cells (`3 x 3`) regardless — most are `0`, a direct illustration of the `O(V^2)` cost even for a sparse graph.

## 5. Runnable example

```java
// AdjacencyMatrix.java
import java.util.*;

public class AdjacencyMatrix {

    static class Graph {
        List<String> vertices;
        Map<String, Integer> indexOf = new HashMap<>();
        int[][] matrix;

        Graph(List<String> vertices) {
            this.vertices = vertices;
            for (int i = 0; i < vertices.size(); i++) indexOf.put(vertices.get(i), i);
            matrix = new int[vertices.size()][vertices.size()]; // all cells start at 0 -- "no edge"
        }

        // Basic: add an edge -- for undirected, set both [i][j] and [j][i].
        void addEdge(String a, String b) {
            int i = indexOf.get(a), j = indexOf.get(b);
            matrix[i][j] = 1;
            matrix[j][i] = 1; // symmetric for an undirected graph
        }

        boolean hasEdge(String a, String b) {
            return matrix[indexOf.get(a)][indexOf.get(b)] == 1;
        }
    }

    static void basicLevel() {
        Graph graph = new Graph(List.of("A", "B", "C"));
        graph.addEdge("A", "B");

        System.out.println("basic: hasEdge(A, B) -> " + graph.hasEdge("A", "B") + " (O(1) direct lookup)");
        System.out.println("basic: hasEdge(A, C) -> " + graph.hasEdge("A", "C"));
    }

    // Intermediate: listing neighbors requires scanning an ENTIRE row, unlike an adjacency list's direct lookup.
    static List<String> neighborsOf(Graph graph, String vertex) {
        List<String> neighbors = new ArrayList<>();
        int row = graph.indexOf.get(vertex);
        for (int col = 0; col < graph.matrix[row].length; col++) { // must check every column, even ones with no edge
            if (graph.matrix[row][col] == 1) neighbors.add(graph.vertices.get(col));
        }
        return neighbors;
    }

    static void intermediateLevel() {
        Graph graph = new Graph(List.of("A", "B", "C", "D", "E"));
        graph.addEdge("A", "B");
        graph.addEdge("A", "E");

        System.out.println("intermediate: neighbors of A -> " + neighborsOf(graph, "A")
            + " (found by scanning all 5 columns of A's row, even the 3 with no edge)");
    }

    // Advanced: a weighted adjacency matrix, using a sentinel (Integer.MAX_VALUE) to mean "no edge".
    static class WeightedGraph {
        List<String> vertices;
        Map<String, Integer> indexOf = new HashMap<>();
        int[][] weights;
        static final int NO_EDGE = Integer.MAX_VALUE;

        WeightedGraph(List<String> vertices) {
            this.vertices = vertices;
            for (int i = 0; i < vertices.size(); i++) indexOf.put(vertices.get(i), i);
            weights = new int[vertices.size()][vertices.size()];
            for (int[] row : weights) Arrays.fill(row, NO_EDGE);
        }

        void addEdge(String a, String b, int weight) {
            weights[indexOf.get(a)][indexOf.get(b)] = weight; // directed: only one direction set
        }
    }

    static void advancedLevel() {
        WeightedGraph graph = new WeightedGraph(List.of("A", "B", "C"));
        graph.addEdge("A", "B", 5);
        graph.addEdge("A", "C", 2);

        int weightAB = graph.weights[graph.indexOf.get("A")][graph.indexOf.get("B")];
        int weightBA = graph.weights[graph.indexOf.get("B")][graph.indexOf.get("A")];
        System.out.println("advanced: weight(A->B) -> " + weightAB + ", weight(B->A) -> "
            + (weightBA == WeightedGraph.NO_EDGE ? "NO_EDGE (directed -- no reverse edge was added)" : weightBA));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `AdjacencyMatrix.java`, then run `java AdjacencyMatrix.java`.

## 6. Walkthrough

1. `basicLevel()` adds one edge, `A-B`, setting both `matrix[indexOf(A)][indexOf(B)]` and its mirror to `1`. `hasEdge("A", "B")` is a single array lookup, `O(1)` — no scanning at all. `hasEdge("A", "C")` is the same guaranteed `O(1)` lookup, correctly returning `false`, since that cell was never set.
2. `intermediateLevel()` finds `A`'s neighbors by scanning its *entire* row across all 5 vertices, checking each column for a `1`. Even though `A` has only 2 real neighbors, the scan touches all 5 columns — the `O(V)` cost that makes an adjacency matrix worse than a list for this particular query.
3. `advancedLevel()` uses `Integer.MAX_VALUE` as a sentinel meaning "no edge" in a weighted, directed graph. `weight(A -> B)` correctly returns `5`. `weight(B -> A)` returns the sentinel, since only the `A -> B` direction was ever added — directed edges do not automatically populate the mirrored cell, unlike the undirected case in `basicLevel`.

## 7. Gotchas & takeaways

> Gotcha: allocating a `V x V` matrix for a graph with millions of vertices but relatively few edges can exhaust memory instantly (`V^2` grows quadratically) — always check whether the graph is actually dense before choosing a matrix; for sparse graphs, an [adjacency list](0140-adjacency-list.md) is almost always the better choice.

- An adjacency matrix gives guaranteed `O(1)` edge-existence checks, at the cost of `O(V^2)` memory regardless of how many edges actually exist.
- Listing a vertex's neighbors costs `O(V)` (scanning a full row), worse than an adjacency list's `O(degree)`.
- Best suited to dense graphs, or algorithms that are naturally matrix-shaped (e.g. Floyd-Warshall's all-pairs shortest path).
- Related concepts: [Adjacency list](0140-adjacency-list.md), [Edge list](0142-edge-list.md).
