---
card: leetcode-patterns
gi: 119
slug: all-nodes-distance-k-in-binary-tree
title: All Nodes Distance K in Binary Tree
---

## 1. What it is

Given the `root` of a binary tree, a `target` node inside it, and an integer `k`, return the values of all nodes that are exactly `k` edges away from `target`. Distance can go up through parents, not only down through children. Example: `root = [3,5,1,6,2,0,8,null,null,7,4]`, `target = 5`, `k = 2` → `[7,4,1]`.

## 2. Why & when

A binary tree only stores child pointers, so going "up" from `target` is not directly possible. The trick is to first build parent pointers with one BFS pass, turning the tree into an undirected graph, then run a second BFS from `target` that can move in any direction (left, right, or parent) and stop exactly at distance `k`. This lands in the Tree BFS section because both passes reuse the same level-by-level queue draining you already know, just on a graph instead of a strictly downward tree.

## 3. Core concept

**Key idea:** map every node to its parent with one BFS. Then run a second BFS from `target`, treating left child, right child, and parent as three equal neighbours, and stop expanding once the current frontier is at distance `k`.

**Steps:**
1. BFS (or DFS) once over the whole tree, recording `parentOf[node] = parent` for every node.
2. Start a second BFS from `target` with `distance = 0` and a `visited` set containing `target`.
3. While `distance < k`: save `levelSize = queue.size()`; for each of the `levelSize` nodes, push its unvisited neighbours (left, right, parent) and mark them visited; increment `distance`.
4. Once `distance == k`, every node still in the queue is at exactly distance `k` from `target` — collect their values.

**Why it is correct:** the `levelSize` snapshot again isolates one distance "ring" per BFS iteration, this time over a graph where edges go in three directions instead of two, so after `k` full rings the queue holds exactly the nodes at distance `k`.

## 4. Diagram

<svg viewBox="0 0 500 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS from target treating parent and children as equal neighbours">
  <g font-family="sans-serif" font-size="12">
    <circle cx="250" cy="35" r="16" fill="#161b22" stroke="#79c0ff"/><text x="250" y="40" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="180" cy="90" r="16" fill="#161b22" stroke="#f85149"/><text x="180" y="95" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="320" cy="90" r="16" fill="#161b22" stroke="#79c0ff"/><text x="320" y="95" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="140" cy="145" r="16" fill="#161b22" stroke="#79c0ff"/><text x="140" y="150" fill="#e6edf3" text-anchor="middle">6</text>
    <circle cx="220" cy="145" r="16" fill="#161b22" stroke="#3fb950"/><text x="220" y="150" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="242" y1="49" x2="188" y2="77" stroke="#3fb950" stroke-width="2"/>
    <line x1="258" y1="49" x2="312" y2="77" stroke="#8b949e"/>
    <line x1="172" y1="104" x2="148" y2="132" stroke="#8b949e"/>
    <line x1="188" y1="104" x2="212" y2="132" stroke="#3fb950" stroke-width="2"/>
    <text x="10" y="185" fill="#e6edf3">k=2 from 5: up to 3 (dist 1) then to 1 (dist 2); down to 2 (dist 1) then children (dist 2)</text>
  </g>
</svg>

The parent edge (green, upward) is walked exactly like a child edge — that is what lets BFS reach `k` distance in any direction.

## 5. Runnable example

```java
// AllNodesDistanceK.java
import java.util.*;

public class AllNodesDistanceK {

    static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: DFS from root recording the path to target,
    // then for each ancestor on that path, DFS downward to depth (k -
    // distance from target) skipping the direction already visited.
    // O(n) time but juggles two different traversal directions and path
    // bookkeeping instead of one uniform BFS.
    static List<Integer> bruteForce(TreeNode root, TreeNode target, int k) {
        List<TreeNode> path = new ArrayList<>();
        findPath(root, target, path);
        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < path.size(); i++) {
            int remaining = k - (path.size() - 1 - i);
            TreeNode skip = i + 1 < path.size() ? path.get(i + 1) : null;
            collectAtDepth(path.get(i), remaining, skip, result);
        }
        return result;
    }

    static boolean findPath(TreeNode node, TreeNode target, List<TreeNode> path) {
        if (node == null) return false;
        path.add(node);
        if (node == target) return true;
        if (findPath(node.left, target, path) || findPath(node.right, target, path)) return true;
        path.remove(path.size() - 1);
        return false;
    }

    static void collectAtDepth(TreeNode node, int remaining, TreeNode skip, List<Integer> result) {
        if (node == null || node == skip) return;
        if (remaining < 0) return;
        if (remaining == 0) { result.add(node.val); return; }
        collectAtDepth(node.left, remaining - 1, skip, result);
        collectAtDepth(node.right, remaining - 1, skip, result);
    }

    // KEY INSIGHT: recording each node's parent turns the tree into an
    // undirected graph, so a single uniform BFS (left, right, parent as
    // equal neighbours) replaces the two-direction path logic above.

    // Level 2 -- Optimal: build parent map with BFS, then BFS from target
    // for exactly k rings. O(n) time, O(n) space for the parent map.
    public static List<Integer> distanceK(TreeNode root, TreeNode target, int k) {
        Map<TreeNode, TreeNode> parentOf = new IdentityHashMap<>();
        buildParents(root, null, parentOf);

        Queue<TreeNode> queue = new LinkedList<>();
        Set<TreeNode> visited = new HashSet<>();
        queue.offer(target);
        visited.add(target);

        int distance = 0;
        while (!queue.isEmpty() && distance < k) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.poll();
                for (TreeNode neighbour : new TreeNode[]{node.left, node.right, parentOf.get(node)}) {
                    if (neighbour != null && !visited.contains(neighbour)) {
                        visited.add(neighbour);
                        queue.offer(neighbour);
                    }
                }
            }
            distance++;
        }

        List<Integer> result = new ArrayList<>();
        for (TreeNode node : queue) result.add(node.val);
        return result;
    }

    static void buildParents(TreeNode node, TreeNode parent, Map<TreeNode, TreeNode> parentOf) {
        if (node == null) return;
        parentOf.put(node, parent);
        buildParents(node.left, node, parentOf);
        buildParents(node.right, node, parentOf);
    }

    // Level 3 -- Hardened: k = 0 must return only the target itself, and
    // target being the root (no parent) must not throw a null lookup.
    static List<Integer> hardened(TreeNode root, TreeNode target, int k) {
        return distanceK(root, target, k);
    }

    public static void main(String[] args) {
        TreeNode root = new TreeNode(3);
        TreeNode five = new TreeNode(5);
        TreeNode one = new TreeNode(1);
        root.left = five; root.right = one;
        TreeNode six = new TreeNode(6), two = new TreeNode(2);
        five.left = six; five.right = two;
        TreeNode zero = new TreeNode(0), eight = new TreeNode(8);
        one.left = zero; one.right = eight;
        TreeNode seven = new TreeNode(7), four = new TreeNode(4);
        two.left = seven; two.right = four;

        System.out.println(bruteForce(root, five, 2));
        System.out.println(distanceK(root, five, 2));
        System.out.println(hardened(root, five, 0));
    }
}
```

How to run: save as `AllNodesDistanceK.java`, then run `java AllNodesDistanceK.java`.

## 6. Walkthrough

Dry run of `distanceK(root, target=5, k=2)`:

| ring (distance) | queue at start | neighbours pushed | visited added |
|---|---|---|---|
| 0 -> 1 | [5] | 3 (parent), 6, 2 | 3, 6, 2 |
| 1 -> 2 | [3, 6, 2] | 1 (from 3), 7, 4 (from 2); 6 has no unvisited neighbours | 1, 7, 4 |

Loop stops once `distance == k == 2`. The queue now holds `[1, 7, 4]`, matching the expected `[7,4,1]` (order may differ). Time complexity: O(n), building parents plus the second BFS both visit each node once. Space complexity: O(n) for the parent map and the visited set.

## 7. Gotchas & takeaways

> Gotcha: forgetting to mark nodes visited (or forgetting the parent direction entirely) causes the second BFS to walk back and forth between a node and its parent forever, or to miss ancestors reachable only by going up.

- Treating `parentOf.get(node)` as just another neighbour, alongside `left` and `right`, is what turns a directed tree into an undirected graph BFS can search in any direction.
- Related problems: Binary Tree Level Order Traversal (BFS on the tree only, no parent edges needed), Lowest Common Ancestor of a Binary Tree (also needs upward reasoning, but via ancestor paths instead of BFS rings).
