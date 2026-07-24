---
card: leetcode-patterns
gi: 333
slug: filling-bookcase-shelves
title: Filling Bookcase Shelves
---

## 1. What it is

Given an array `books`, where `books[i] = [thickness, height]`, and a shelf width `shelfWidth`, place the books IN ORDER onto shelves: each shelf holds a consecutive run of books whose total thickness fits within `shelfWidth`, and a shelf's height equals its TALLEST book. Return the minimum possible total height of all shelves used. Example: `books = [[1,1],[2,3],[2,3],[1,1],[1,1],[1,1],[1,2]]`, `shelfWidth = 4` → `6`.

## 2. Why & when

This is grouped-choice DP over CONSECUTIVE runs (unlike Maximum Value of K Coins From Piles, which grouped by pile): decide where each "shelf break" goes, and each shelf's cost is its tallest book, not a sum. Use this shape whenever a problem partitions a SEQUENCE into consecutive groups, where each group's cost depends on some aggregate (max, sum) of its members, and groups must respect a capacity limit.

## 3. Core concept

**Key idea:** `dp[i]` = the minimum total height to shelve the first `i` books. For each `i`, try every possible LAST SHELF: it could start right after book `j` (i.e., contain books `j+1` through `i`), as long as their combined thickness fits `shelfWidth`.

**Steps:**
1. Create `dp[n+1]`, with `dp[0] = 0` (zero books need zero height).
2. For `i` from `1` to `n`: initialize `dp[i] = infinity`. Try `j` from `i - 1` DOWN TO `0`: track `runningWidth` (sum of thicknesses of books `j+1..i`) and `runningHeight` (max height of books `j+1..i`), updated incrementally as `j` decreases.
3. If `runningWidth > shelfWidth`, STOP the inner loop (no smaller `j` could fit either, since thickness only grows as more books are added).
4. Otherwise, `dp[i] = min(dp[i], dp[j] + runningHeight)` (the best way to shelve the first `j` books, plus this last shelf's height).
5. Return `dp[n]`.

**Why it is correct:** trying every possible "last shelf" boundary `j` covers every valid way to partition the first `i` books into shelves, since ANY valid shelving has SOME specific last shelf, and that shelf's own books (`j+1..i`) must independently fit within `shelfWidth`. Tracking `runningWidth` incrementally, and stopping the inner loop the moment it exceeds `shelfWidth`, is a valid prune: since books are considered in order (i.e., adding MORE books can only increase width, never decrease it), no smaller `j` could ever produce a narrower shelf.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Computing dp at position i by trying every possible last shelf ending at i, tracking running width and height as j decreases">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">books[0..3] (1-indexed 1..4), shelfWidth=4, computing dp[4]</text>
    <text x="10" y="45">try j=3 (last shelf = book 4 alone): width=1&lt;=4, height=1 -&gt; dp[3]+1</text>
    <text x="10" y="65">try j=2 (last shelf = books 3,4): width=2+1=3&lt;=4, height=max(3,1)=3 -&gt; dp[2]+3</text>
    <text x="10" y="85">try j=1 (last shelf = books 2,3,4): width=2+2+1=5&gt;4 -&gt; stop</text>
    <rect x="10" y="100" width="200" height="24" fill="#3fb950"/><text x="110" y="117" fill="#0d1117" text-anchor="middle" font-size="10">dp[4] = min of valid candidates</text>
  </g>
</svg>

The inner loop stops as soon as the running shelf width exceeds the limit, since adding earlier books can only make it wider.

## 5. Runnable example

```java
// FillingBookcaseShelves.java
public class FillingBookcaseShelves {

    // KEY INSIGHT: dp[i] tries every possible LAST SHELF ending at
    // book i, tracking running width/height as the shelf's starting
    // point j moves backward -- stopping the moment width overflows,
    // since width only grows as more books are added.

    static int minHeightShelves(int[][] books, int shelfWidth) {
        int n = books.length;
        int[] dp = new int[n + 1];
        dp[0] = 0;

        for (int i = 1; i <= n; i++) {
            dp[i] = Integer.MAX_VALUE;
            int runningWidth = 0, runningHeight = 0;

            for (int j = i - 1; j >= 0; j--) {
                int thickness = books[j][0], height = books[j][1];
                runningWidth += thickness;
                if (runningWidth > shelfWidth) break; // prune: too wide

                runningHeight = Math.max(runningHeight, height);
                dp[i] = Math.min(dp[i], dp[j] + runningHeight);
            }
        }
        return dp[n];
    }

    public static void main(String[] args) {
        int[][] books = {{1,1},{2,3},{2,3},{1,1},{1,1},{1,1},{1,2}};
        System.out.println(minHeightShelves(books, 4));
        // 6
    }
}
```

**How to run:** `java FillingBookcaseShelves.java`

## 6. Walkthrough

Trace the computation of `dp[4]` (first 4 books: `[1,1],[2,3],[2,3],[1,1]`), using the already-computed values `dp[0]=0, dp[1]=1, dp[2]=3, dp[3]=4`:

| j (shelf starts after book j) | runningWidth | runningHeight | candidate dp[j] + runningHeight |
|---|---|---|---|
| 3 (last shelf = book 4 only) | 1 | 1 | dp[3] + 1 = 4 + 1 = 5 |
| 2 (last shelf = books 3,4) | 2+1=3 | max(3,1)=3 | dp[2] + 3 = 3 + 3 = 6 |
| 1 (last shelf = books 2,3,4) | 2+2+1=5 &gt; 4 | — | prune, loop stops |

`dp[4] = min(5, 6) = 5`, matching the actual computed value. The full run continues the same way through `dp[7] = 6`, the final answer. Time complexity is O(n²) in the worst case, since for each of `n` positions, the inner loop can scan back up to `n` books (though the width-overflow prune often cuts this short). Space is O(n), for the `dp` array.

## 7. Gotchas & takeaways

> Gotcha: the inner loop's `break` on width overflow is only safe because books are considered in a FIXED, GIVEN ORDER — if the problem allowed REORDERING books before shelving, this width-only-grows argument would no longer hold, and a different approach would be needed.

- This is sequence-partitioning DP: similar in spirit to 0/1 knapsack's "try every choice, keep the best," but the "choice" here is WHERE to place the previous shelf boundary, not whether to include a single item.
- Tracking `runningWidth` and `runningHeight` INCREMENTALLY as `j` decreases (rather than resumming the whole range each time) is what keeps the inner loop efficient.
- Related problems: Maximum Value of K Coins From Piles (grouped-choice DP over piles instead of consecutive runs), Word Break (sequence-partitioning DP with a dictionary-membership rule instead of a width/height rule).
