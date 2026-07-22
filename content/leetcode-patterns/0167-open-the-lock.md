---
card: leetcode-patterns
gi: 167
slug: open-the-lock
title: Open the Lock
---

## 1. What it is

A lock has 4 wheels, each showing a digit `0`-`9`. One move turns one wheel by one step, up or down (`9` wraps to `0` and back). Given a list of `deadends` (combinations that lock the wheel forever if reached) and a `target` combination, return the minimum number of moves from `"0000"` to `target`. Return `-1` if it cannot be reached. Example: `deadends = ["0201","0101","0102","1212","2002"]`, `target = "0202"` → `6`.

## 2. Why & when

Each 4-digit state is a node. Turning one wheel one step is an edge to a neighboring state. Finding the *minimum* number of moves between two nodes in an unweighted graph is exactly what breadth-first search (BFS) is built for — BFS explores states in layers of increasing distance, so the first time it reaches `target` is guaranteed to be the shortest path.

## 3. Core concept

**Key idea:** treat every 4-digit string as a graph node with up to 8 neighbors (each of 4 wheels can turn up or down). Run BFS from `"0000"`, skipping deadends, and return the layer number where `target` first appears.

**Steps:**
1. Put all `deadends` in a set for O(1) lookup. If `"0000"` is a deadend, return `-1` immediately.
2. Start BFS with `"0000"` at distance 0, marking it visited.
3. For each state dequeued, generate its 8 neighbors: for each of the 4 positions, turn the digit up by one and down by one (with wraparound).
4. Skip a neighbor if it is a deadend or already visited; otherwise enqueue it with distance + 1.
5. If a dequeued state equals `target`, return its distance.
6. If the queue empties without finding `target`, return `-1`.

**Why it is correct:** BFS visits nodes in strict order of distance from the start. The first time `target` is dequeued, no shorter path could exist — every state at a smaller distance was already fully explored.

## 4. Diagram

<svg viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS layers expanding outward from 0000, deadends blocked">
  <g font-family="sans-serif" font-size="12">
    <circle cx="60" cy="100" r="18" fill="#161b22" stroke="#3fb950"/><text x="60" y="104" fill="#e6edf3" text-anchor="middle">0000</text>
    <circle cx="180" cy="50" r="18" fill="#161b22" stroke="#79c0ff"/><text x="180" y="54" fill="#e6edf3" text-anchor="middle">1000</text>
    <circle cx="180" cy="150" r="18" fill="#161b22" stroke="#f85149"/><text x="180" y="154" fill="#e6edf3" text-anchor="middle">0100</text>
    <line x1="76" y1="90" x2="164" y2="58" stroke="#8b949e"/>
    <line x1="76" y1="110" x2="164" y2="142" stroke="#8b949e" stroke-dasharray="3,3"/>
    <circle cx="320" cy="50" r="18" fill="#161b22" stroke="#e3b341"/><text x="320" y="54" fill="#e6edf3" text-anchor="middle">1100</text>
    <line x1="196" y1="50" x2="304" y2="50" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">green=start, blue=layer 1, gold=layer 2, red dashed=deadend (skipped)</text>
  </g>
</svg>

BFS expands outward in layers; the dashed red edge into a deadend is never taken.

## 5. Runnable example

```java
// OpenTheLock.java
import java.util.*;

public class OpenTheLock {

    // Level 1 -- Brute force: DFS trying every sequence of moves up to
    // some depth limit, tracking the minimum length that reaches
    // target. Correct but wasteful -- it can revisit the same state
    // many times via different paths and has no natural stopping point
    // for "shortest," since DFS finds A path, not the SHORTEST one,
    // without extra bookkeeping.

    // KEY INSIGHT: this is shortest-path-in-an-unweighted-graph, which
    // BFS solves directly and optimally by exploring in distance order
    // -- the first time target is reached IS the shortest distance.

    // Level 2 -- Optimal: BFS over the state graph, skipping deadends.
    static int openLock(String[] deadends, String target) {
        Set<String> dead = new HashSet<>(Arrays.asList(deadends));
        if (dead.contains("0000")) return -1;
        if (target.equals("0000")) return 0;

        Set<String> visited = new HashSet<>();
        visited.add("0000");
        Queue<String> queue = new LinkedList<>();
        queue.add("0000");
        int moves = 0;

        while (!queue.isEmpty()) {
            moves++;
            int layerSize = queue.size();
            for (int i = 0; i < layerSize; i++) {
                String cur = queue.poll();
                for (String next : neighbors(cur)) {
                    if (dead.contains(next) || visited.contains(next)) continue;
                    if (next.equals(target)) return moves;
                    visited.add(next);
                    queue.add(next);
                }
            }
        }
        return -1;
    }

    static List<String> neighbors(String state) {
        List<String> result = new ArrayList<>();
        char[] chars = state.toCharArray();
        for (int i = 0; i < 4; i++) {
            char original = chars[i];
            chars[i] = (char) ('0' + (original - '0' + 1) % 10);
            result.add(new String(chars));
            chars[i] = (char) ('0' + (original - '0' + 9) % 10);
            result.add(new String(chars));
            chars[i] = original;
        }
        return result;
    }

    // Level 3 -- Hardened: handle "0000" itself being a deadend, and
    // target == "0000" as a zero-move answer, both checked up front
    // before the BFS starts.

    public static void main(String[] args) {
        System.out.println(openLock(new String[]{"0201","0101","0102","1212","2002"}, "0202")); // 6
        System.out.println(openLock(new String[]{"8888"}, "0009")); // 1
        System.out.println(openLock(new String[]{"8887","8889","8878","8898","8788","8988","7888","9888"}, "8888")); // -1
    }
}
```

**How to run:** `java OpenTheLock.java`

## 6. Walkthrough

Trace `deadends = ["0201","0101","0102","1212","2002"]`, `target = "0202"`:

| Step | State dequeued | Distance | Notes |
|---|---|---|---|
| 1 | `0000` | 0 | start, mark visited |
| 2 | `1000`, `9000`, `0100`, ... | 1 | 8 neighbors of `0000` enqueued |
| 3 | ... expands layer 2 ... | 2 | `0101` skipped (deadend) |
| 4 | ... | ... | search continues, avoiding all 5 deadends |
| 5 | `0202` found | 6 | return 6 |

Time complexity is O(10000) in the worst case, since there are only `10^4` possible 4-digit states; space is O(10000) for the visited set and queue.

## 7. Gotchas & takeaways

> Forgetting to check `"0000"` against `deadends` before starting BFS causes the algorithm to expand from an already-dead state, giving a wrong answer instead of `-1`.

- Check `target == "0000"` as a zero-move shortcut before running BFS.
- Mark states visited when you enqueue them, not when you dequeue them — otherwise the same state can be added to the queue multiple times.
- Related problems: Word Ladder (BFS over transformed strings), Minimum Genetic Mutation (identical structure, different alphabet).
