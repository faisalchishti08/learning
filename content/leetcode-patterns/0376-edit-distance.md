---
card: leetcode-patterns
gi: 376
slug: edit-distance
title: Edit Distance
---

## 1. What it is

Given two strings `word1` and `word2`, return the MINIMUM number of operations to convert `word1` into `word2`, where each operation is an INSERT, a DELETE, or a REPLACE of a single character. Example: `word1 = "horse"`, `word2 = "ros"` → `3` (replace `'h'`→`'r'`, delete `'r'`, delete `'e'`).

## 2. Why & when

This is the LCS-family pattern extended with THREE operation types instead of a plain match/mismatch check. Use this shape whenever a problem allows insert, delete, AND replace (not just delete alone, which would be Delete Operation for Two Strings) to transform one string into another.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the minimum number of operations to convert the first `i` characters of `word1` into the first `j` characters of `word2`, for every `i, j`.

**Steps:**
1. Base cases: `dp[i][0] = i` (delete all `i` characters of `word1`'s prefix to reach an empty string). `dp[0][j] = j` (insert all `j` characters to build `word2`'s prefix from empty).
2. For `i` from `1` to `m`, for `j` from `1` to `n`: if `word1.charAt(i-1) == word2.charAt(j-1)`, `dp[i][j] = dp[i-1][j-1]` (no operation needed — characters already match). Else, `dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])` (delete from `word1`, insert into `word1`, or replace, whichever costs least).
3. Return `dp[m][n]`.

**Why it is correct:** at a MISMATCH, exactly one of three actions must happen to make progress: DELETE `word1`'s current character (move to `dp[i-1][j]`, since `word1` shrinks by one), INSERT a character matching `word2`'s current one (move to `dp[i][j-1]`, since `word2`'s prefix is now satisfied one further), or REPLACE `word1`'s current character with `word2`'s (move to `dp[i-1][j-1]`, since both prefixes advance together). Each costs `1` operation plus whatever the corresponding smaller sub-problem costs; taking the minimum of the three finds the cheapest path.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp cell for mismatched characters showing three possible operations delete insert and replace each mapping to a neighbor cell">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">word1[i-1] != word2[j-1] -- three options, each costs 1 + neighbor</text>
    <text x="10" y="45">delete word1 char: 1 + dp[i-1][j]</text>
    <text x="10" y="65">insert word2 char: 1 + dp[i][j-1]</text>
    <text x="10" y="85">replace word1 char with word2 char: 1 + dp[i-1][j-1]</text>
    <rect x="10" y="105" width="280" height="24" fill="#3fb950"/><text x="150" y="122" fill="#0d1117" text-anchor="middle" font-size="10">dp[i][j] = 1 + min of the three</text>
  </g>
</svg>

Every mismatch chooses the cheapest of three ways to make one unit of progress toward alignment.

## 5. Runnable example

```java
// EditDistance.java
public class EditDistance {

    // KEY INSIGHT: a mismatch allows THREE moves (delete, insert,
    // replace), each mapping to a different neighbor cell plus 1 --
    // take the minimum of all three.

    static int minDistance(String word1, String word2) {
        int m = word1.length(), n = word2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 0; i <= m; i++) dp[i][0] = i;
        for (int j = 0; j <= n; j++) dp[0][j] = j;

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (word1.charAt(i - 1) == word2.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    int delete = dp[i - 1][j];
                    int insert = dp[i][j - 1];
                    int replace = dp[i - 1][j - 1];
                    dp[i][j] = 1 + Math.min(delete, Math.min(insert, replace));
                }
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(minDistance("horse", "ros"));
        // 3
        System.out.println(minDistance("intention", "execution"));
        // 5
    }
}
```

**How to run:** `java EditDistance.java`

## 6. Walkthrough

Trace key cells for `minDistance("horse", "ros")`, `m=5, n=3`:

| i,j | chars | match? | dp[i][j] |
|---|---|---|---|
| 1,1 | 'h','r' | no | 1+min(dp[0][1],dp[1][0],dp[0][0]) = 1+min(1,1,0)=1 |
| 2,2 | 'o','o' | yes | dp[1][1]=1 |
| 5,3 | 'e','s' | no | (final answer builds to) 3 |

`dp[5][3] = 3`, matching the expected `3` operations. Time complexity is O(m · n). Space is O(m · n) (reducible to O(min(m,n))).

## 7. Gotchas & takeaways

> Gotcha: forgetting the base row and column (`dp[i][0]=i`, `dp[0][j]=j`) breaks the recurrence at the edges — converting a non-empty prefix to an empty string always costs exactly its own length in deletions, and vice versa for insertions.

- `dp[i][j] = dp[i-1][j-1]` on match, `1 + min(delete, insert, replace)` on mismatch: the three-operation extension of the LCS-family template.
- This is DIFFERENT from Minimum ASCII Delete Sum, which only allows DELETE (no insert or replace) — always confirm exactly which operations a problem permits before choosing the transition.
- Related problems: Delete Operation for Two Strings (the delete-only special case, solvable via LCS length arithmetic), One Edit Distance (a simpler decision problem asking only whether the distance is AT MOST 1, solvable without a full DP table).
