---
card: leetcode-patterns
gi: 158
slug: clone-graph
title: Clone Graph
---

## 1. What it is

Given a reference to a node in a connected undirected graph, return a deep copy (clone) of the entire graph. Each node has a value and a list of neighbors; the clone must have the same structure, with all-new node objects (not references to the originals). Example: a graph `1 -- 2 -- 3 -- 4 -- 1` (a 4-cycle) must be cloned into an entirely separate 4-cycle with the same connections.

## 2. Why & when

Because the graph can contain cycles, a naive recursive copy ("clone this node, then recursively clone each neighbor") would loop forever, re-cloning the same nodes repeatedly. This is the canonical reason Graph DFS/BFS needs a `visited` map here: it must map each ORIGINAL node to its ALREADY-CREATED clone, so that when a cycle leads back to a node already being processed, the existing clone is reused instead of creating a duplicate or recursing infinitely.

## 3. Core concept

**Key idea:** use a map from original node to its clone. When visiting an original node for the first time, immediately create its clone and store the mapping BEFORE recursing into its neighbors — this is what breaks the cycle, since a later visit to the same original node (via a different path) finds the mapping already present and returns the existing clone instead of recursing again.

**Steps:**
1. Keep a map `cloneOf: Map<Node, Node>`.
2. Define `clone(node)`: if `node == null`, return `null`. If `cloneOf` already contains `node`, return `cloneOf.get(node)` (already cloned, or currently being cloned — either way, reuse it).
3. Otherwise: create `nodeClone = new Node(node.val)`, and IMMEDIATELY store `cloneOf.put(node, nodeClone)` before recursing.
4. For each neighbor in `node.neighbors`: append `clone(neighbor)` to `nodeClone.neighbors`.
5. Return `nodeClone`.

**Why it is correct:** storing the mapping BEFORE recursing into neighbors means that if a neighbor's own neighbor list eventually points back to `node` (a cycle), the recursive call for `node` finds it already in the map and returns immediately, rather than recursing into `node` a second time and looping forever.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Recording a node's clone before recursing into neighbors breaks a cycle">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="40" r="16" fill="#161b22" stroke="#3fb950"/><text x="100" y="44" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="200" cy="40" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="44" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="200" cy="120" r="16" fill="#161b22" stroke="#79c0ff"/><text x="200" y="124" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="100" cy="120" r="16" fill="#161b22" stroke="#79c0ff"/><text x="100" y="124" fill="#e6edf3" text-anchor="middle">4</text>
    <line x1="116" y1="40" x2="184" y2="40" stroke="#8b949e"/>
    <line x1="200" y1="56" x2="200" y2="104" stroke="#8b949e"/>
    <line x1="184" y1="120" x2="116" y2="120" stroke="#8b949e"/>
    <line x1="100" y1="104" x2="100" y2="56" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="15" fill="#e6edf3">Cloning 1 -&gt; 2 -&gt; 3 -&gt; 4 -&gt; back to 1 (green edge): map already has 1's clone, so return it directly</text>
  </g>
</svg>

By the time the recursion reaches `4`'s neighbor `1` again, `1`'s clone is already recorded in the map, so no infinite loop occurs.

## 5. Runnable example

```java
// CloneGraph.java
import java.util.*;

public class CloneGraph {

    static class Node {
        int val;
        List<Node> neighbors;
        Node(int val) { this.val = val; this.neighbors = new ArrayList<>(); }
    }

    // Level 1 -- Brute force: first collect every reachable node via a
    // separate DFS pass, create ALL clones up front (with empty
    // neighbor lists), then do a second pass to wire up each clone's
    // neighbors using the map. O(V + E) time but two full passes and
    // extra bookkeeping, versus doing it in one recursive pass.
    static Node bruteForce(Node start) {
        if (start == null) return null;
        Map<Node, Node> cloneOf = new HashMap<>();
        List<Node> allNodes = new ArrayList<>();
        collectNodes(start, new HashSet<>(), allNodes);
        for (Node original : allNodes) cloneOf.put(original, new Node(original.val));
        for (Node original : allNodes) {
            for (Node neighbor : original.neighbors) {
                cloneOf.get(original).neighbors.add(cloneOf.get(neighbor));
            }
        }
        return cloneOf.get(start);
    }

    static void collectNodes(Node node, Set<Node> visited, List<Node> allNodes) {
        if (visited.contains(node)) return;
        visited.add(node);
        allNodes.add(node);
        for (Node neighbor : node.neighbors) collectNodes(neighbor, visited, allNodes);
    }

    // KEY INSIGHT: recording a node's clone in the map BEFORE recursing
    // into its neighbors lets a single recursive pass handle cycles
    // safely -- no separate "collect all nodes first" pass is needed.

    // Level 2 -- Optimal: one DFS pass, map records clone before
    // recursing. O(V + E) time, O(V) space (the map plus recursion stack).
    static Map<Node, Node> cloneOf = new HashMap<>();

    public static Node cloneGraph(Node node) {
        cloneOf.clear();
        return clone(node);
    }

    static Node clone(Node node) {
        if (node == null) return null;
        if (cloneOf.containsKey(node)) return cloneOf.get(node);

        Node nodeClone = new Node(node.val);
        cloneOf.put(node, nodeClone);
        for (Node neighbor : node.neighbors) {
            nodeClone.neighbors.add(clone(neighbor));
        }
        return nodeClone;
    }

    // Level 3 -- Hardened: a graph with a single node and NO neighbors
    // (a self-contained isolated node) must clone correctly without
    // infinite recursion, and a null input must return null.
    static Node hardened(Node start) {
        return cloneGraph(start);
    }

    public static void main(String[] args) {
        Node n1 = new Node(1), n2 = new Node(2), n3 = new Node(3), n4 = new Node(4);
        n1.neighbors.addAll(List.of(n2, n4));
        n2.neighbors.addAll(List.of(n1, n3));
        n3.neighbors.addAll(List.of(n2, n4));
        n4.neighbors.addAll(List.of(n3, n1));

        Node a = bruteForce(n1);
        System.out.println(a.val + " neighbors=" + a.neighbors.size());

        Node b = cloneGraph(n1);
        System.out.println(b.val + " neighbors=" + b.neighbors.size() + " isSameObject=" + (b == n1));

        Node isolated = new Node(9);
        Node c = hardened(isolated);
        System.out.println(c.val + " neighbors=" + c.neighbors.size());
    }
}
```

How to run: save as `CloneGraph.java`, then run `java CloneGraph.java`.

## 6. Walkthrough

Dry run of `clone(n1)` on the 4-cycle `1-2-3-4-1`:

| call | cloneOf before | action |
|---|---|---|
| clone(1) | {} | not in map; create clone(1); `cloneOf = {1: clone1}`; recurse into neighbors 2 and 4 |
| clone(2) | {1: clone1} | not in map; create clone(2); `cloneOf = {1:.., 2: clone2}`; recurse into neighbors 1 and 3 |
| clone(1) [again, from 2's neighbor list] | {1:.., 2:..} | ALREADY in map — return `clone1` directly, no new recursion |
| clone(3) | {1:.., 2:..} | not in map; create clone(3); recurse into 2 and 4 |
| clone(2) [again] | - | already in map — return `clone2` |
| clone(4) | {1:.., 2:.., 3:..} | not in map; create clone(4); recurse into 3 and 1 |
| clone(3), clone(1) [again] | - | both already in map — return existing clones |

The recursion terminates because every node is cloned exactly once, and every SECOND visit to an already-cloned node returns immediately via the map. Time complexity: O(V + E), each node processed once and each edge examined once. Space complexity: O(V) for the map plus the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: creating the clone and storing it in the map AFTER recursing into all neighbors (instead of before) reintroduces infinite recursion — if a cycle leads back to the current node before its own clone is registered, the recursion calls itself again with no base case to stop it.

- The map serves double duty: it is both the "have I visited this node" check (like a plain `visited` set) AND the lookup table for "what is this node's clone" — a single data structure handles both jobs.
- Related problems: Number of Provinces (also explores a graph with cycles, but only needs to COUNT connected components, not build a parallel structure), Keys and Rooms (a directed-graph reachability question, simpler since it never needs to build anything, only check "can I reach everything").
