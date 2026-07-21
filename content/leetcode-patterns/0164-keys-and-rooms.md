---
card: leetcode-patterns
gi: 164
slug: keys-and-rooms
title: Keys and Rooms
---

## 1. What it is

There are `n` rooms, numbered `0` to `n-1`. Room `0` is unlocked and you start there; `rooms[i]` is a list of keys found in room `i`, where each key `k` lets you unlock and enter room `k`. Return `true` if you can visit every room. Example: `rooms = [[1],[2],[3],[]]` → `true` (room 0 gives a key to room 1, which gives a key to room 2, which gives a key to room 3).

## 2. Why & when

This is a pure "can every node be reached from a single starting node" question — exactly what DFS or BFS answers directly. It belongs in Graph BFS/DFS as one of the simplest possible instances: rooms are nodes, keys are directed edges (room `i` having key `k` means a directed edge from `i` to `k`), and the question is just "does a traversal starting at node `0` reach every node."

## 3. Core concept

**Key idea:** treat this as a directed graph reachability problem. Starting from room `0`, DFS (or BFS) into every room reachable via the keys found so far, marking each visited room. At the end, check if the number of visited rooms equals `n`.

**Steps:**
1. Create a `visited` boolean array of size `n`, all `false`.
2. DFS (or BFS) from room `0`: mark it visited.
3. For each key `k` in `rooms[current]`: if room `k` has not been visited, mark it visited and recurse/enqueue into it.
4. After the traversal completes, count how many rooms are marked visited (or track a running count during the traversal).
5. Return `true` if the visited count equals `n`, `false` otherwise.

**Why it is correct:** a room can only be entered if you have found its key somewhere along a path of rooms already opened starting from room `0`, which is precisely what a graph traversal starting at node `0` explores — so "every room visited by the traversal" is exactly "every room reachable, and therefore enterable, starting from room 0."

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each key found is a directed edge to another room">
  <g font-family="sans-serif" font-size="12">
    <circle cx="80" cy="90" r="18" fill="#161b22" stroke="#3fb950"/><text x="80" y="94" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="200" cy="90" r="18" fill="#161b22" stroke="#3fb950"/><text x="200" y="94" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="320" cy="90" r="18" fill="#161b22" stroke="#3fb950"/><text x="320" y="94" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="440" cy="90" r="18" fill="#161b22" stroke="#3fb950"/><text x="440" y="94" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="98" y1="90" x2="182" y2="90" stroke="#8b949e" marker-end="url(#arrowk)"/>
    <line x1="218" y1="90" x2="302" y2="90" stroke="#8b949e" marker-end="url(#arrowk)"/>
    <line x1="338" y1="90" x2="422" y2="90" stroke="#8b949e" marker-end="url(#arrowk)"/>
    <defs><marker id="arrowk" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="10" y="15" fill="#e6edf3">Room 0 -&gt; key to room 1 -&gt; key to room 2 -&gt; key to room 3: all 4 rooms reachable, answer true</text>
  </g>
</svg>

Each room's key list forms a directed edge; visiting all 4 rooms confirms every room can be unlocked starting from room `0`.

## 5. Runnable example

```java
// KeysAndRooms.java
import java.util.*;

public class KeysAndRooms {

    // Level 1 -- Brute force: repeatedly scan ALL rooms, and if any
    // unvisited room has a key already held from a visited room, mark
    // it visited; repeat until a full pass makes no changes. O(n^2)
    // time in the worst case (a chain of rooms needs n passes, each
    // scanning all n rooms), versus a single traversal.
    static boolean bruteForce(List<List<Integer>> rooms) {
        int n = rooms.size();
        boolean[] visited = new boolean[n];
        visited[0] = true;
        while (true) {
            boolean changed = false;
            for (int i = 0; i < n; i++) {
                if (!visited[i]) continue;
                for (int key : rooms.get(i)) {
                    if (!visited[key]) { visited[key] = true; changed = true; }
                }
            }
            if (!changed) break;
        }
        for (boolean v : visited) if (!v) return false;
        return true;
    }

    // KEY INSIGHT: this is just reachability from a single start node --
    // one DFS or BFS pass visits every reachable room directly, with no
    // need to repeatedly rescan the whole room list.

    // Level 2 -- Optimal: DFS from room 0, marking visited rooms.
    // O(n + total keys) time, O(n) space (visited array plus recursion stack).
    public static boolean canVisitAllRooms(List<List<Integer>> rooms) {
        boolean[] visited = new boolean[rooms.size()];
        dfs(rooms, 0, visited);
        for (boolean v : visited) if (!v) return false;
        return true;
    }

    static void dfs(List<List<Integer>> rooms, int room, boolean[] visited) {
        visited[room] = true;
        for (int key : rooms.get(room)) {
            if (!visited[key]) dfs(rooms, key, visited);
        }
    }

    // Level 3 -- Hardened: a room whose key list contains a key to
    // itself, or to an already-visited room, must not cause infinite
    // recursion, since the visited check guards every recursive call.
    static boolean hardened(List<List<Integer>> rooms) {
        return canVisitAllRooms(rooms);
    }

    public static void main(String[] args) {
        List<List<Integer>> reachable = List.of(List.of(1), List.of(2), List.of(3), List.of());
        List<List<Integer>> unreachable = List.of(List.of(1, 3), List.of(3, 0, 1), List.of(2), List.of(1, 3, 1));

        System.out.println(bruteForce(reachable));
        System.out.println(canVisitAllRooms(reachable));
        System.out.println(hardened(unreachable));
    }
}
```

How to run: save as `KeysAndRooms.java`, then run `java KeysAndRooms.java`.

## 6. Walkthrough

Dry run of `dfs` on `rooms = [[1],[2],[3],[]]`:

| call | room | visited before | keys found | recurse into |
|---|---|---|---|---|
| dfs(0) | 0 | [F,F,F,F] | [1] | dfs(1) |
| dfs(1) | 1 | [T,F,F,F] | [2] | dfs(2) |
| dfs(2) | 2 | [T,T,F,F] | [3] | dfs(3) |
| dfs(3) | 3 | [T,T,T,F] | [] (no keys) | none |

Final `visited = [T,T,T,T]` — every room marked, so `canVisitAllRooms` returns `true`. Time complexity: O(n + total number of keys across all rooms), each room visited once and each key examined once. Space complexity: O(n) for the visited array plus the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: a room can contain DUPLICATE keys, or a key to a room already visited (even room `0` itself) — the `visited` check before recursing is what prevents redundant work or infinite recursion from these duplicate/self-referential keys, so it must never be skipped.

- This is one of the simplest Graph DFS/BFS problems precisely because it only asks "is every node reachable," with no shortest-path, counting, or structural requirement beyond that — a single traversal plus a final scan of the `visited` array is the entire solution.
- Related problems: Number of Provinces (also checks reachability, but for an UNDIRECTED graph and counting multiple components instead of checking one component covers everything), Find if Path Exists in Graph (checks reachability between two SPECIFIC nodes rather than "does one traversal reach everything").
