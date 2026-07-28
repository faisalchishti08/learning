---
card: leetcode-patterns
gi: 529
slug: most-stones-removed-with-same-row-or-column
title: Most Stones Removed with Same Row or Column
---

## 1. What it is

Stones sit on a 2D grid at given `(row, col)` positions. You may remove a stone if another stone still remains in its same row or its same column. Return the maximum number of stones you can remove. Example: `stones = [[0,0],[0,1],[1,0],[1,2],[2,1],[2,2]]` → `5` (you can remove all but one stone, since every stone shares a row or column with some other stone).

## 2. Why & when

This problem hides its structure: it looks like a removal-simulation problem, but "can remove if it shares a row or column with a surviving stone" really means "within each connected group of stones (connected through shared rows/columns), you can always reduce it down to exactly one survivor." That reframing is the [union-find signal](0523-union-find-signal-dynamic-connectivity-or-grouping-by-equiva.md): group stones by shared row or column, and the answer falls out of the group sizes. Constraints: up to 1,000 stones.

## 3. Core concept

**Key idea:** two stones sharing a row or column can always be reduced to one survivor by removing the other first (removal order does not reduce the achievable count, since the last stone standing in a connected group can always be the same one). So within a connected group of `s` stones, you can remove `s - 1` of them, leaving exactly 1. The total answer is `(total stones) - (number of groups)`.

**Steps:**
1. Union every pair of stones that share a row or a column. A convenient trick: treat row indices and column indices as *separate* union-find items (e.g. encode a row `r` as `r` and a column `c` as `~c` or `c + 10001`, so they never collide), then union each stone's row-item with its column-item.
2. Count the number of distinct groups (representatives) that actually contain at least one stone.
3. Return `totalStones - groupCount`.

**Why unioning row-items and column-items (not stone-to-stone) is simpler:** directly unioning every pair of stones sharing a row would need an O(n²) scan of all pairs. Instead, routing every stone's row and column through the *same* union-find structure means two stones automatically end up in the same group the moment they share a row-item or a column-item, in a single O(n) pass over stones.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stones and their rows/columns as union-find items, merging into one connected group">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">stones: (0,0) (0,1) (1,0)</text>
    <circle cx="80" cy="70" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="80" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">row0</text>
    <circle cx="200" cy="70" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="200" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">col0</text>
    <circle cx="80" cy="150" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="80" y="155" fill="#e6edf3" text-anchor="middle" font-size="11">col1</text>
    <circle cx="200" cy="150" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="200" y="155" fill="#e6edf3" text-anchor="middle" font-size="11">row1</text>
    <line x1="94" y1="78" x2="186" y2="78" stroke="#f0883e"/>
    <text x="140" y="65" fill="#f0883e" font-size="10">stone(0,0)</text>
    <line x1="80" y1="86" x2="80" y2="134" stroke="#f0883e"/>
    <text x="60" y="115" fill="#f0883e" font-size="10">stone(0,1)</text>
    <line x1="200" y1="86" x2="200" y2="134" stroke="#f0883e"/>
    <text x="220" y="115" fill="#f0883e" font-size="10">stone(1,0)</text>
    <text x="400" y="100" fill="#79c0ff">all four items merge into 1 group -&gt; 3 stones, 1 group -&gt; remove 2</text>
  </g>
</svg>

Each stone unions its row-item with its column-item. Sharing a row or column chains all three stones into one group, so 2 of the 3 stones can be removed.

## 5. Runnable example

**Level 1 — Brute force.** Repeatedly scan all stones for one that shares a row or column with another remaining stone, remove it, and repeat until no more removals are possible. O(n³) or worse in the worst case.

**KEY INSIGHT:** the maximum removable count only depends on how many connected groups the stones form — you never need to actually simulate the removal order.

**Level 2 — Optimal.** Union-find over encoded row/column items, O(n · α(n)).

**Level 3 — Hardened.** Handles stones that share neither a row nor a column with any other stone (each is its own group of size 1, contributing 0 removals).

```java
// RemoveStones.java
import java.util.*;

public class RemoveStones {

    static class DSU {
        Map<Integer, Integer> parent = new HashMap<>();
        int groupCount = 0;

        int find(int x) {
            parent.putIfAbsent(x, x);
            if (parent.get(x) != x) return find(parent.get(x));
            return x;
        }

        void union(int a, int b) {
            boolean newA = !parent.containsKey(a);
            boolean newB = !parent.containsKey(b);
            int rootA = find(a);
            int rootB = find(b);
            if (newA) groupCount++;
            if (newB) groupCount++;
            if (rootA != rootB) {
                parent.put(rootA, rootB);
                groupCount--;
            }
        }
    }

    static int removeStones(int[][] stones) {
        DSU dsu = new DSU();
        for (int[] stone : stones) {
            int row = stone[0];
            int col = ~stone[1]; // bitwise complement keeps columns disjoint from rows
            dsu.union(row, col);
        }
        return stones.length - dsu.groupCount;
    }

    public static void main(String[] args) {
        int[][] stones1 = {{0, 0}, {0, 1}, {1, 0}, {1, 2}, {2, 1}, {2, 2}};
        System.out.println(removeStones(stones1)); // 5

        int[][] stones2 = {{0, 0}, {0, 2}, {1, 1}, {2, 0}, {2, 2}};
        System.out.println(removeStones(stones2)); // 3

        int[][] stones3 = {{0, 0}};
        System.out.println(removeStones(stones3)); // 0, one stone, one group
    }
}
```

**How to run:** save as `RemoveStones.java`, then run `java RemoveStones.java`.

## 6. Walkthrough

Trace `removeStones([[0,0],[0,1],[1,0],[1,2],[2,1],[2,2]])`:

1. Stone `(0,0)`: unions row `0` with column `~0`. Both are new items, so `groupCount` becomes 2, then the union merges them back to 1.
2. Stone `(0,1)`: unions row `0` (already exists) with column `~1` (new). `groupCount` rises to 2, then the union merges them: `groupCount` back to 1.
3. Stone `(1,0)`: unions row `1` (new) with column `~0` (already exists, already in the group). `groupCount` rises to 2, then merges to 1.
4. Continuing through stones `(1,2)`, `(2,1)`, `(2,2)` keeps merging every new row/column item into the same single group.
5. After all 6 stones, `groupCount = 1`. Answer: `6 - 1 = 5`.

## 7. Gotchas & takeaways

> Gotcha: unioning row index `r` and column index `c` directly (without separating their number spaces) is wrong whenever a row index equals a column index — e.g. row `1` and column `1` would collide and be treated as the same item, merging unrelated stones. Encoding columns as `~c` (or `c + rowCount`) keeps the two spaces disjoint.

- Signal: "can act on an item if it shares a property with another surviving item" often reframes as "count connected groups by that shared property," answered by `total - groupCount`.
- Route both properties (row and column) through one union-find structure by unioning them per stone, instead of unioning stones pairwise.
- Related problems: Accounts Merge (same "route through a shared-key union-find" trick), Number of Connected Components in an Undirected Graph.
