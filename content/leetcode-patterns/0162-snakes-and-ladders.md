---
card: leetcode-patterns
gi: 162
slug: snakes-and-ladders
title: Snakes and Ladders
---

## 1. What it is

Given an `n x n` board numbered `1` to `n*n` in a boustrophedon (back-and-forth) pattern starting at the bottom-left, where some squares hold a snake or ladder (a value pointing to a different square), return the minimum number of dice rolls (`1`-`6` each) to go from square `1` to square `n*n`, or `-1` if impossible. Example: a `6x6` board with several ladders → some minimum roll count like `4`.

## 2. Why & when

"Minimum number of moves" in an unweighted setting (every dice roll counts as exactly one "move," regardless of which of the 6 values is rolled) is the signature phrase for BFS: treat each square as a graph node, with an edge from square `i` to squares `i+1` through `i+6` (or wherever a snake/ladder redirects you). BFS explores the reachable squares in strict order of "number of rolls used," so the first time it reaches `n*n`, that is guaranteed to be the minimum.

## 3. Core concept

**Key idea:** convert the board into a flat 1D array of values (undoing the boustrophedon numbering), then BFS from square `1`: for each square, the reachable squares in one more roll are `current + 1` through `current + 6` (capped at `n*n`), except if a square has a snake/ladder value other than `-1`, you land wherever it points instead.

**Steps:**
1. Flatten the 2D board into `values[1..n*n]`, converting the zigzag row order into straight square-number order.
2. BFS from square `1`: `distance[1] = 0`, enqueue `1`, mark it visited.
3. Dequeue `current`. For `next` in `current+1` to `min(current+6, n*n)`: determine the actual destination — if `values[next] != -1`, the destination is `values[next]` (a snake or ladder); otherwise it is `next` itself.
4. If the destination has not been visited: mark it visited, record `distance[destination] = distance[current] + 1`, enqueue it.
5. Stop as soon as `n*n` is dequeued (or reached) — return its distance. If the queue empties without reaching `n*n`, return `-1`.

**Why it is correct:** every dice roll costs exactly one "step" regardless of its face value, so this is an unweighted graph where BFS is guaranteed to find the shortest path (fewest rolls) — the snake/ladder redirection is simply a special edge from `next` straight to wherever it lands, still costing one roll to traverse.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each square connects to up to 6 next squares, or is redirected by a snake/ladder">
  <g font-family="sans-serif" font-size="12">
    <circle cx="60" cy="90" r="16" fill="#161b22" stroke="#3fb950"/><text x="60" y="94" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="150" cy="50" r="14" fill="#161b22" stroke="#79c0ff"/><text x="150" y="54" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="150" cy="90" r="14" fill="#161b22" stroke="#79c0ff"/><text x="150" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="150" cy="130" r="14" fill="#161b22" stroke="#f85149"/><text x="150" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="300" cy="130" r="14" fill="#161b22" stroke="#f85149"/><text x="300" y="134" fill="#e6edf3" text-anchor="middle" font-size="11">20</text>
    <line x1="76" y1="90" x2="136" y2="55" stroke="#8b949e"/>
    <line x1="76" y1="90" x2="136" y2="90" stroke="#8b949e"/>
    <line x1="76" y1="94" x2="136" y2="125" stroke="#8b949e"/>
    <line x1="164" y1="130" x2="286" y2="130" stroke="#f85149" stroke-dasharray="4,3"/>
    <text x="10" y="15" fill="#e6edf3">From square 1, one roll reaches squares 2, 3, or 4 (values 2-6 shown partially)</text>
    <text x="200" y="150" fill="#f85149">Square 4 has a ladder to square 20 -- landing on 4 means you are actually at 20</text>
  </g>
</svg>

Landing on square `4` immediately redirects to square `20` via the ladder, costing the same single roll.

## 5. Runnable example

```java
// SnakesAndLadders.java
import java.util.*;

public class SnakesAndLadders {

    // Level 1 -- Brute force: DFS trying every possible sequence of
    // rolls, tracking the minimum rolls to reach n*n across all paths.
    // Exponential time in the worst case (up to 6 branches per square,
    // explored without memoization), since the same square can be
    // reached via many different roll sequences, each explored anew.
    static int bruteForce(int[][] board) {
        int n = board.length;
        int[] values = flatten(board);
        int[] best = {Integer.MAX_VALUE};
        dfsExplore(values, 1, 0, new HashSet<>(), best, n * n);
        return best[0] == Integer.MAX_VALUE ? -1 : best[0];
    }

    static void dfsExplore(int[] values, int current, int rolls, Set<Integer> path, int[] best, int target) {
        if (current == target) { best[0] = Math.min(best[0], rolls); return; }
        if (rolls >= best[0] || path.contains(current)) return;
        path.add(current);
        for (int step = 1; step <= 6 && current + step <= target; step++) {
            int next = current + step;
            int destination = values[next] == -1 ? next : values[next];
            dfsExplore(values, destination, rolls + 1, path, best, target);
        }
        path.remove(current);
    }

    // KEY INSIGHT: every roll costs exactly one step regardless of face
    // value, so this is an UNWEIGHTED shortest-path question -- BFS
    // guarantees the first time n*n is reached is via the minimum
    // number of rolls, with no need to explore every possible sequence.

    // Level 2 -- Optimal: BFS over flattened squares 1..n*n.
    // O(n^2) time (each square visited once, 6 edges checked each),
    // O(n^2) space (queue and visited array).
    public static int snakesAndLadders(int[][] board) {
        int n = board.length;
        int[] values = flatten(board);
        int target = n * n;

        boolean[] visited = new boolean[target + 1];
        Queue<Integer> queue = new LinkedList<>();
        queue.offer(1);
        visited[1] = true;
        int rolls = 0;

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                int current = queue.poll();
                if (current == target) return rolls;
                for (int step = 1; step <= 6 && current + step <= target; step++) {
                    int next = current + step;
                    int destination = values[next] == -1 ? next : values[next];
                    if (!visited[destination]) {
                        visited[destination] = true;
                        queue.offer(destination);
                    }
                }
            }
            rolls++;
        }
        return -1;
    }

    static int[] flatten(int[][] board) {
        int n = board.length;
        int[] values = new int[n * n + 1];
        int square = 1;
        for (int row = n - 1; row >= 0; row--) {
            if ((n - 1 - row) % 2 == 0) {
                for (int col = 0; col < n; col++) values[square++] = board[row][col];
            } else {
                for (int col = n - 1; col >= 0; col--) values[square++] = board[row][col];
            }
        }
        return values;
    }

    // Level 3 -- Hardened: a 2x2 board with no snakes or ladders
    // (all -1) must still compute the minimum roll count using only
    // plain forward movement.
    static int hardened(int[][] board) {
        return snakesAndLadders(board);
    }

    public static void main(String[] args) {
        int[][] board = {
            {-1,-1,-1,-1,-1,-1},
            {-1,-1,-1,-1,-1,-1},
            {-1,-1,-1,-1,-1,-1},
            {-1,35,-1,-1,13,-1},
            {-1,-1,-1,-1,-1,-1},
            {-1,15,-1,-1,-1,-1}
        };

        System.out.println(bruteForce(board));
        System.out.println(snakesAndLadders(board));

        int[][] noLaddersBoard = {{-1,-1},{-1,-1}};
        System.out.println(hardened(noLaddersBoard));
    }
}
```

How to run: save as `SnakesAndLadders.java`, then run `java SnakesAndLadders.java`.

## 6. Walkthrough

Trace of `snakesAndLadders` conceptually on a small board (square `1` to `n*n`, with a ladder from square `4` to square `20`):

| rolls | queue at start | processing | newly enqueued |
|---|---|---|---|
| 0 | [1] | dequeue 1; steps to 2,3,4,5,6,7; square 4 redirects to 20 | 2, 3, 20, 5, 6, 7 |
| 1 | [2,3,20,5,6,7] | dequeue each; check if target reached; expand further | (continues) |

The BFS discovers square `20` after just ONE roll (via the ladder at square `4`), even though `20` is far from `1` in raw square-number distance — this is exactly why BFS (not a direct distance calculation) is needed: the graph's edges are NOT simply "adjacent numbers," due to the snakes and ladders. Time complexity: O(n^2), since there are `n*n` squares, each with up to 6 outgoing edges. Space complexity: O(n^2) for the visited array and queue.

## 7. Gotchas & takeaways

> Gotcha: flattening the board incorrectly (forgetting that alternate rows read right-to-left in the boustrophedon pattern) silently shifts every square's number, giving wrong edges everywhere — carefully alternate the column direction based on which row (counting from the bottom) is being flattened.

- Checking `current == target` immediately after dequeuing (before trying to roll further) lets the BFS return as soon as the target is reached, without needing a separate distance array.
- Related problems: Rotting Oranges (the same "one BFS level = one unit of real-world time/steps" mapping, there for minutes instead of dice rolls), Minimum Genetic Mutation (also treats "one allowed change" as one BFS edge, finding the shortest sequence of such changes).
