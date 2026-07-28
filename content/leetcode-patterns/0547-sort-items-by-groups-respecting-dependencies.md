---
card: leetcode-patterns
gi: 547
slug: sort-items-by-groups-respecting-dependencies
title: Sort Items by Groups Respecting Dependencies
---

## 1. What it is

There are `n` items, each optionally belonging to a group (`group[i] == -1` means ungrouped). `beforeItems[i]` lists items that must come before item `i`. Return a valid ordering of all items such that: every item-level dependency is respected, AND items in the same group appear together as one contiguous block. Return an empty array if no valid ordering exists. Example: items grouped into group `0` and group `1`, with cross-item dependencies — the output interleaves the two groups as whole blocks, in whichever relative order their cross-group dependencies require.

## 2. Why & when

This combines two levels of the [topological sort signal](0537-topological-sort-signal-ordering-with-dependency-prerequisit.md): item-level dependencies (which item must come before which) AND group-level dependencies (which group's items must come before another group's items, derived from cross-group item dependencies). Solve it by running topological sort **twice**: once on groups, once on items — a common pattern called two-level (hierarchical) topological sort. Constraints: up to 3 x 10^4 items.

## 3. Core concept

**Key idea:** first assign every ungrouped item its own unique group ID (so it can be treated uniformly). Then build two separate graphs: an **item graph** (item `a` depends on item `b`) and a **group graph** (group `X` depends on group `Y`, derived whenever an item in `X` depends on an item in `Y`). Topologically sort the groups first, then topologically sort the items *within* each group, and finally concatenate the items group-by-group in the groups' topological order.

**Steps:**
1. For every `group[i] == -1`, assign it a fresh unique group ID (e.g. counting upward from the existing max group ID).
2. Build the item-level graph and in-degrees from `beforeItems`.
3. Build the group-level graph: for every dependency `item b before item a`, if `group[a] != group[b]`, add an edge `group[b] -> group[a]` (deduplicated) and track group in-degrees.
4. Topologically sort the groups (Kahn's algorithm). If it fails (cycle), return `[]`.
5. Topologically sort the items *within each group* (a separate Kahn's run scoped to just that group's items and their internal dependencies). If any group's internal sort fails, return `[]`.
6. Concatenate: for each group in the groups' topological order, append that group's items in their own topological order.

**Why two separate topological sorts are needed, not one:** a single flat topological sort over all items would not guarantee that same-group items stay contiguous — items from different groups could interleave freely as long as individual item dependencies are satisfied. Sorting groups first fixes the group blocks' relative order; sorting items within each group afterward fixes the order inside each block, satisfying both constraints at once.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Group graph sorted first (group 0 before group 1), then items sorted within each group block">
  <g font-family="sans-serif" font-size="13">
    <rect x="30" y="30" width="180" height="60" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="55" fill="#e6edf3" text-anchor="middle">group 0</text>
    <text x="120" y="75" fill="#8b949e" text-anchor="middle" font-size="11">items sorted internally</text>
    <rect x="280" y="30" width="180" height="60" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="370" y="55" fill="#e6edf3" text-anchor="middle">group 1</text>
    <text x="370" y="75" fill="#8b949e" text-anchor="middle" font-size="11">items sorted internally</text>
    <line x1="212" y1="60" x2="278" y2="60" stroke="#8b949e" marker-end="url(#a7)"/>
    <defs><marker id="a7" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="300" y="130" fill="#79c0ff" text-anchor="middle">final order: [all of group 0's items, in their internal order] + [all of group 1's items, in their internal order]</text>
  </g>
</svg>

Groups are ordered first as whole blocks; within each block, items are ordered by their own internal dependencies.

## 5. Runnable example

**Level 1 — Brute force.** Try every permutation of items and check both the item-dependency constraints and the group-contiguity constraint. Factorial time.

**KEY INSIGHT:** running topological sort at two separate levels — groups, then items within each group — satisfies both the cross-group ordering and the intra-group ordering independently and correctly.

**Level 2 — Optimal.** Two-level Kahn's algorithm, O(n + m) where n is item count and m is dependency count.

**Level 3 — Hardened.** Handles ungrouped items (each becomes its own singleton group) and a cycle at either the group level or the item level (both must be checked).

```java
// SortItemsByGroups.java
import java.util.*;

public class SortItemsByGroups {

    static int[] sortItems(int n, int m, int[] group, List<List<Integer>> beforeItems) {
        int groupCount = m;
        for (int i = 0; i < n; i++) {
            if (group[i] == -1) group[i] = groupCount++;
        }

        List<List<Integer>> itemGraph = new ArrayList<>();
        int[] itemInDegree = new int[n];
        for (int i = 0; i < n; i++) itemGraph.add(new ArrayList<>());

        List<Set<Integer>> groupGraph = new ArrayList<>();
        int[] groupInDegree = new int[groupCount];
        for (int i = 0; i < groupCount; i++) groupGraph.add(new HashSet<>());

        for (int i = 0; i < n; i++) {
            for (int before : beforeItems.get(i)) {
                itemGraph.get(before).add(i);
                itemInDegree[i]++;
                if (group[before] != group[i] && groupGraph.get(group[before]).add(group[i])) {
                    groupInDegree[group[i]]++;
                }
            }
        }

        List<Integer> groupOrder = kahnSort(rangeList(groupCount), groupGraph, groupInDegree);
        if (groupOrder.size() != groupCount) return new int[0];

        List<Integer> itemOrder = kahnSort(rangeList(n), itemGraph, itemInDegree);
        if (itemOrder.size() != n) return new int[0];

        Map<Integer, List<Integer>> itemsByGroup = new HashMap<>();
        for (int item : itemOrder) {
            itemsByGroup.computeIfAbsent(group[item], k -> new ArrayList<>()).add(item);
        }

        int[] result = new int[n];
        int idx = 0;
        for (int g : groupOrder) {
            for (int item : itemsByGroup.getOrDefault(g, Collections.emptyList())) {
                result[idx++] = item;
            }
        }
        return result;
    }

    static List<Integer> rangeList(int n) {
        List<Integer> list = new ArrayList<>();
        for (int i = 0; i < n; i++) list.add(i);
        return list;
    }

    static List<Integer> kahnSort(List<Integer> nodes, List<? extends Collection<Integer>> graph, int[] inDegree) {
        Deque<Integer> queue = new ArrayDeque<>();
        for (int node : nodes) if (inDegree[node] == 0) queue.add(node);

        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            int u = queue.poll();
            order.add(u);
            for (int v : graph.get(u)) {
                if (--inDegree[v] == 0) queue.add(v);
            }
        }
        return order;
    }

    public static void main(String[] args) {
        int n = 8, m = 2;
        int[] group = {-1, -1, 1, 0, 0, 1, 0, -1};
        List<List<Integer>> beforeItems = Arrays.asList(
                Arrays.asList(), Arrays.asList(6), Arrays.asList(5),
                Arrays.asList(6), Arrays.asList(3, 6), Arrays.asList(),
                Arrays.asList(), Arrays.asList());
        System.out.println(Arrays.toString(sortItems(n, m, group, beforeItems)));
    }
}
```

**How to run:** save as `SortItemsByGroups.java`, then run `java SortItemsByGroups.java`.

## 6. Walkthrough

1. Ungrouped items (`group[i] == -1`, items `0`, `1`, `7`) each get a fresh unique group ID: `2`, `3`, `4`.
2. Build the item graph from `beforeItems`, and simultaneously derive group edges whenever a dependency crosses group boundaries (e.g. item `1` depends on item `6`, and item `1` is in a different group than item `6`, so an edge is added between their groups).
3. Topologically sort the 5 groups (original groups `0`, `1`, plus the 3 fresh singleton groups) using their cross-group dependency edges.
4. Topologically sort all 8 items using their item-level dependencies, ignoring group boundaries entirely at this step.
5. Bucket the item order by group, then walk the group order, appending each group's items (in their already-computed relative order) to the final result.

## 7. Gotchas & takeaways

> Gotcha: adding a group-level edge for *every* cross-group item dependency (without deduplicating with a `Set`) inflates `groupInDegree` incorrectly, since the same group pair could be connected by several different item-level dependencies — always guard the edge addition with a "have we already added this exact group edge" check.

- Signal: "order items so that same-group items stay contiguous, while respecting individual dependencies" needs two separate topological sorts — one for groups, one for items — not a single flat sort.
- Assign ungrouped items their own unique singleton group so the same two-level algorithm handles them uniformly.
- Related problems: Course Schedule II, Parallel Courses III.
