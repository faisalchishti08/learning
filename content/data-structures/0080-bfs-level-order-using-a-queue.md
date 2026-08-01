---
card: data-structures
gi: 80
slug: bfs-level-order-using-a-queue
title: BFS level-order using a queue
---

## 1. What it is

**Breadth-first search (BFS)** visits a tree or graph level by level: all nodes at distance 1 from the start before any node at distance 2, all at distance 2 before any at distance 3, and so on. A **queue** is the structure that makes this happen automatically — nodes are visited in exactly the order they were discovered, which is precisely FIFO order.

## 2. Why & when

BFS with a queue is how you find the shortest path in an unweighted graph, print a tree level by level, or compute the minimum number of steps between two states in a search space. Use it whenever "closest first" or "fewest steps first" matters — depth-first search does not give this guarantee, since it can plunge deep down one branch before backtracking.

## 3. Core concept

**Why a queue, not a stack.** If you used a stack (LIFO) instead of a queue (FIFO) for this traversal, you would get depth-first order instead — the most *recently* discovered node would be visited next, diving deep down one path instead of spreading out level by level. The queue's FIFO order is what forces "oldest discovered, visited first," which is exactly level-order.

**The algorithm, step by step.**
1. Push the start node into the queue, and mark it visited (for a graph, to avoid revisiting).
2. While the queue is not empty: dequeue a node, process it, then enqueue all of its unvisited neighbors (marking each visited immediately, as it is enqueued).
3. Because all of level `n`'s nodes were enqueued before any of level `n+1`'s nodes (they were only just discovered), the queue always finishes dequeuing an entire level before starting the next one.

**Tracking level boundaries.** To process the tree level by level (not just node by node in discovery order), record `levelSize = queue.size()` at the start of each iteration of the outer loop, then dequeue exactly that many nodes before moving to the next level — those `levelSize` dequeues are guaranteed to be exactly the current level's nodes, since every earlier level was already fully drained.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small tree with root A, children B and C, and grandchildren D, E, showing the queue state as breadth first search dequeues A, enqueues B and C, dequeues B, enqueues D and E">
  <g font-family="sans-serif" font-size="11">
    <circle cx="320" cy="30" r="18" fill="#0d1117" stroke="#f0883e"/><text x="320" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <circle cx="240" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="240" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <circle cx="400" cy="90" r="18" fill="#161b22" stroke="#8b949e"/><text x="400" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <circle cx="200" cy="150" r="18" fill="#161b22" stroke="#8b949e"/><text x="200" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <circle cx="280" cy="150" r="18" fill="#161b22" stroke="#8b949e"/><text x="280" y="154" fill="#e6edf3" text-anchor="middle" font-size="9">E</text>
    <line x1="308" y1="42" x2="252" y2="78" stroke="#8b949e"/>
    <line x1="332" y1="42" x2="388" y2="78" stroke="#8b949e"/>
    <line x1="228" y1="102" x2="208" y2="138" stroke="#8b949e"/>
    <line x1="252" y1="102" x2="272" y2="138" stroke="#8b949e"/>
    <text x="320" y="185" fill="#79c0ff" text-anchor="middle" font-size="9">visit order: A, B, C, D, E -- level 0, then level 1, then level 2</text>
  </g>
</svg>

Dequeue `A`, enqueue `B, C`. Dequeue `B`, enqueue `D, E`. Dequeue `C` (no children). Dequeue `D`, then `E` — every node at one depth is visited before any node at the next depth.

## 5. Runnable example

```java
// BfsLevelOrder.java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Queue;

public class BfsLevelOrder {

    static class TreeNode {
        int value;
        List<TreeNode> children = new ArrayList<>();
        TreeNode(int value) { this.value = value; }
    }

    // Basic: plain BFS, one flat visit order (not grouped by level).
    static List<Integer> bfsFlat(TreeNode root) {
        List<Integer> order = new ArrayList<>();
        Queue<TreeNode> queue = new ArrayDeque<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            order.add(node.value);
            for (TreeNode child : node.children) queue.offer(child);
        }
        return order;
    }

    static void basicLevel() {
        TreeNode a = new TreeNode(1), b = new TreeNode(2), c = new TreeNode(3), d = new TreeNode(4), e = new TreeNode(5);
        a.children.add(b); a.children.add(c);
        b.children.add(d); b.children.add(e);

        System.out.println("basic: BFS visit order -> " + bfsFlat(a));
    }

    // Intermediate: level-by-level grouping, using levelSize = queue.size() at the start of each round.
    static List<List<Integer>> bfsByLevel(TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        Queue<TreeNode> queue = new ArrayDeque<>();
        queue.offer(root);

        while (!queue.isEmpty()) {
            int levelSize = queue.size(); // exactly the number of nodes in the current level
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                level.add(node.value);
                for (TreeNode child : node.children) queue.offer(child);
            }
            levels.add(level);
        }
        return levels;
    }

    static void intermediateLevel() {
        TreeNode a = new TreeNode(1), b = new TreeNode(2), c = new TreeNode(3), d = new TreeNode(4), e = new TreeNode(5);
        a.children.add(b); a.children.add(c);
        b.children.add(d); b.children.add(e);

        System.out.println("intermediate: BFS grouped by level -> " + bfsByLevel(a));
    }

    // Advanced: shortest path (fewest edges) in an unweighted graph, using BFS with a visited set.
    static int shortestPath(java.util.Map<Integer, List<Integer>> graph, int start, int target) {
        java.util.Set<Integer> visited = new java.util.HashSet<>();
        Queue<Integer> queue = new ArrayDeque<>();
        queue.offer(start);
        visited.add(start);
        int distance = 0;

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                int node = queue.poll();
                if (node == target) return distance;
                for (int neighbor : graph.getOrDefault(node, List.of())) {
                    if (visited.add(neighbor)) queue.offer(neighbor); // add() returns false if already present
                }
            }
            distance++;
        }
        return -1; // target unreachable
    }

    static void advancedLevel() {
        java.util.Map<Integer, List<Integer>> graph = java.util.Map.of(
            1, List.of(2, 3),
            2, List.of(4),
            3, List.of(4),
            4, List.of(5)
        );
        System.out.println("advanced: shortest path 1 -> 5 -> " + shortestPath(graph, 1, 5) + " edges");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BfsLevelOrder.java`, then run `java BfsLevelOrder.java`.

## 6. Walkthrough

1. `basicLevel()` enqueues the root `A`, then repeatedly dequeues a node, visits it, and enqueues its children. Visit order comes out `1, 2, 3, 4, 5` (`A, B, C, D, E`) — level 0 (`A`), then level 1 (`B, C`), then level 2 (`D, E`), because children are always enqueued after their parent, so they can never be dequeued before it or before their same-level siblings.
2. `intermediateLevel()` adds level tracking: at the start of each outer-loop round, `levelSize = queue.size()` captures exactly how many nodes belong to the current level (every earlier level has already been fully dequeued and its children enqueued). Dequeuing exactly `levelSize` times processes exactly that level, giving `[[1], [2,3], [4,5]]`.
3. `advancedLevel()` applies the same shape to shortest-path: `distance` increments once per fully-drained level, and a node's `distance` when first dequeued is guaranteed to be its shortest distance from `start`, since BFS discovers nodes in strictly non-decreasing distance order. `visited.add(neighbor)` doubles as both the "already seen" check and the insertion, since `Set.add` returns `false` if the element was already present.

## 7. Gotchas & takeaways

> Gotcha: forgetting to mark a node visited *at the moment it is enqueued* (rather than when it is dequeued) lets the same node be enqueued multiple times by different parents before it is ever processed, wasting work and potentially causing incorrect distances in shortest-path BFS. Always mark visited on enqueue, not on dequeue.

- BFS uses a queue specifically because FIFO order guarantees nodes are visited in the order they were discovered — closest first.
- `levelSize = queue.size()` at the start of each round is the standard trick to process one level at a time.
- For graphs (unlike trees), track visited nodes and mark them visited at enqueue time, to avoid revisiting and to get correct shortest distances.
- Related concepts: [FIFO semantics](0072-fifo-semantics.md), [enqueue / dequeue / peek](0077-enqueue-dequeue-peek.md).
