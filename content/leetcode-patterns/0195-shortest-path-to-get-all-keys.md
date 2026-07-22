---
card: leetcode-patterns
gi: 195
slug: shortest-path-to-get-all-keys
title: Shortest Path to Get All Keys
---

## 1. What it is

Given a grid with walls (`#`), empty space (`.`), a starting point (`@`), lowercase letters (keys), and matching uppercase letters (locks that need their key first), return the minimum number of moves to collect ALL keys. Return `-1` if impossible. Example: `grid = ["@.a.#","###.#","b.A.B"]` → `8`.

## 2. Why & when

Plain BFS tracks "have I visited this cell before," but here whether you CAN revisit a cell depends on which keys you are currently carrying — the same cell can be safely re-entered later once you have the right key, even if an earlier visit without it was blocked. This needs BFS over an EXPANDED state space: `(row, col, keys collected so far)`, not just `(row, col)`.

## 3. Core concept

**Key idea:** represent each BFS state as a triple `(row, col, keyBitmask)`, where `keyBitmask` is an integer whose bits track which keys have been collected. Two visits to the SAME cell with DIFFERENT key sets are genuinely different states and must both be explored; only revisiting the exact same `(row, col, keyBitmask)` combination is wasted work.

**Steps:**
1. Scan the grid once to find the start `@`, and count the total number of keys (to know the target bitmask, e.g. `(1 << totalKeys) - 1`).
2. Start BFS from `(startRow, startCol, 0)` (no keys yet), at distance `0`.
3. For each state dequeued, if the key bitmask already equals the target (all keys collected), return the current distance.
4. Otherwise, try all 4 neighbor cells: skip walls; skip locked doors unless the corresponding key bit is already set; if a neighbor has a key, set that bit in a NEW bitmask for the resulting state.
5. Mark each `(row, col, newBitmask)` combination visited (e.g. using a 3D visited array or a set of encoded triples) before enqueuing, exactly like standard BFS.
6. If the queue empties without ever reaching the full bitmask, return `-1`.

**Why it is correct:** BFS over the expanded `(row, col, keys)` state space still explores states in strict order of distance, because each state transition (one grid move) still costs exactly one step. The bitmask correctly captures "am I now able to pass a lock I couldn't before" without needing to re-derive it from the whole path history, since the mask alone determines every future door-passing decision.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same grid cell explored twice, once with no keys and once with a key, are treated as distinct BFS states">
  <g font-family="sans-serif" font-size="12">
    <circle cx="140" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="140" y="64" fill="#e6edf3" text-anchor="middle" font-size="9">(2,2,00)</text>
    <circle cx="140" cy="140" r="18" fill="#161b22" stroke="#e3b341"/><text x="140" y="144" fill="#e6edf3" text-anchor="middle" font-size="9">(2,2,01)</text>
    <text x="10" y="15" fill="#e6edf3">same cell (2,2), different key bitmasks -- two distinct, both-explorable BFS states</text>
  </g>
</svg>

Reaching the same cell with a different set of collected keys represents a genuinely different, separately trackable BFS state.

## 5. Runnable example

```java
// ShortestPathToGetAllKeys.java
import java.util.*;

public class ShortestPathToGetAllKeys {

    // Level 1 -- Brute force: plain BFS over (row, col) only, treating
    // a locked door as always impassable, then separately retry the
    // whole search after "conceptually" collecting each key in some
    // order. Fails to be correct in general -- it cannot properly
    // represent "this cell is now passable because of a key gained via
    // a DIFFERENT route," since plain (row, col) visited-tracking
    // conflates paths with different key sets into one.

    // KEY INSIGHT: expand the STATE to (row, col, keyBitmask) --
    // visiting the same cell with a different key set is a genuinely
    // different, separately explorable state, not a duplicate.

    // Level 2 -- Optimal: BFS over the expanded state space.
    static int shortestPathAllKeys(String[] grid) {
        int rows = grid.length, cols = grid[0].length();
        int startR = 0, startC = 0, totalKeys = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                char ch = grid[r].charAt(c);
                if (ch == '@') { startR = r; startC = c; }
                if (Character.isLowerCase(ch)) totalKeys++;
            }
        }

        int target = (1 << totalKeys) - 1;
        boolean[][][] visited = new boolean[rows][cols][1 << totalKeys];
        Queue<int[]> queue = new LinkedList<>();
        queue.add(new int[]{startR, startC, 0});
        visited[startR][startC][0] = true;
        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        int steps = 0;

        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                int[] cur = queue.poll();
                int r = cur[0], c = cur[1], keys = cur[2];
                if (keys == target) return steps;

                for (int[] d : dirs) {
                    int nr = r + d[0], nc = c + d[1];
                    if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                    char ch = grid[nr].charAt(nc);
                    if (ch == '#') continue;
                    int newKeys = keys;
                    if (Character.isUpperCase(ch)) {
                        int need = 1 << (ch - 'A');
                        if ((keys & need) == 0) continue; // locked, no key
                    }
                    if (Character.isLowerCase(ch)) {
                        newKeys = keys | (1 << (ch - 'a'));
                    }
                    if (!visited[nr][nc][newKeys]) {
                        visited[nr][nc][newKeys] = true;
                        queue.add(new int[]{nr, nc, newKeys});
                    }
                }
            }
            steps++;
        }
        return -1;
    }

    // Level 3 -- Hardened: the target-check happens on DEQUEUE (not
    // enqueue), and the visited array is sized [rows][cols][1 <<
    // totalKeys] to correctly separate all reachable key combinations,
    // even ones that skip an "obvious" order (e.g. finding key 'b'
    // before key 'a').

    public static void main(String[] args) {
        System.out.println(shortestPathAllKeys(new String[]{"@.a.#","###.#","b.A.B"})); // 8
        System.out.println(shortestPathAllKeys(new String[]{"@..aA","..B#.","....."})); // 6
    }
}
```

**How to run:** `java ShortestPathToGetAllKeys.java`

## 6. Walkthrough

Trace a simplified case reaching key `'a'` then door `'A'`:

| Step | State (r,c,mask) | Cell | Action |
|---|---|---|---|
| 1 | (0,0,00) | `@` | dequeue, not target, expand neighbors |
| 2 | (0,1,00) | `.` | enqueue |
| 3 | (0,2,01) | `a` | key found, newKeys = 0b01, enqueue as NEW state |
| 4 | (2,2,01) | `A` | `(keys & need) != 0` since bit 0 is set → door passable, continue exploring |

Each key pickup creates a genuinely new state tuple, letting BFS correctly track which doors are currently passable. Time complexity is O(rows × cols × 2^keys), since that is the total number of distinct states; space is the same, for the visited array and queue.

## 7. Gotchas & takeaways

> Gotcha: using a plain 2D `visited[row][col]` array (ignoring the key bitmask) incorrectly blocks a LATER visit to a cell that is now reachable because a key was collected via a different path since the first visit — the bitmask must be part of the visited state, not just the coordinates.

- The number of keys is small in practice (at most 6 in this problem's constraints), keeping `2^keys` a small, manageable multiplier on the state space.
- Checking `keys == target` on DEQUEUE (not on every neighbor expansion) is simpler and equally correct, since BFS order guarantees the first dequeue of a target state is via the shortest path.
- Related problems: Open the Lock (BFS over a different kind of expanded state, digit combinations), Word Ladder (BFS over string states, no extra dimension needed).
