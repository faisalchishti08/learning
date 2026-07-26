---
card: leetcode-patterns
gi: 427
slug: strange-printer
title: Strange Printer
---

## 1. What it is

A strange printer can only print a SEQUENCE of the same character each turn, anywhere in the string, possibly overwriting existing characters. Given a target string, return the MINIMUM number of turns needed to print it. Example: `s = "aaabbb"` → `2` (print `"aaa"`, then print `"bbb"`). Example: `s = "aba"` → `2` (print `"aaa"`, then print `"b"` in the middle).

## 2. Why & when

Use this shape whenever a problem lets you "merge" the cost of handling a repeated character across a range, by recognizing that MATCHING a later character to an earlier one can save a full extra turn. The signal: a minimization problem over a STRING, where reusing an earlier print run (instead of starting a fresh one) is the whole source of savings.

## 3. Core concept

**Key idea:** build `dp[i][j]` = the minimum turns needed to print exactly `s[i..j]`.

**Steps:**
1. Base case: `dp[i][i] = 1` (a single character always needs exactly one turn).
2. Default case: `dp[i][j] = dp[i][j-1] + 1` (print `s[i..j-1]` optimally, then print `s[j]` as one MORE separate turn).
3. Improvement: for every `k` from `i` to `j-1`, if `s[k] == s[j]`, then the LAST character `s[j]` can be printed AS PART OF the same run that already covers `s[k]` (by printing that run a bit longer, all the way to `j`, letting later characters overwrite the middle as needed) — so `dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j-1])`, where `dp[k+1][j-1]` is `0` if the range is empty.
4. The answer is `dp[0][n-1]`.

**Why matching `s[k] == s[j]` saves a turn:** if some earlier position `k` in the range holds the SAME character as the last position `j`, you can print the run covering `s[k]` a little "wider" — long enough to also reach position `j` — and let the CHARACTERS IN BETWEEN be printed afterward, on top of it. This merges what would have been TWO separate turns (one for `s[k]`'s run, one for `s[j]`'s run) into effectively one, since `s[j]` rides along with `s[k]`'s original print for free.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an earlier matching character at position k lets the last character at position j ride along on the same print run">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">s = "aba" -- s[0]='a' matches s[2]='a'</text>
    <text x="10" y="45">print "aaa" across the whole range (covers position 0 AND position 2 for free)</text>
    <text x="10" y="65">then print "b" on top, in the middle, as a second turn</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">total: 2 turns, not 3</text>
  </g>
</svg>

Matching an earlier character lets the final position "ride along" on that earlier print run, saving a turn.

## 5. Runnable example

```java
// StrangePrinter.java
public class StrangePrinter {

    // KEY INSIGHT: if s[k] == s[j] for some k < j, position j can ride
    // along on the print run that already covers position k, merging
    // what would otherwise be two separate turns into one.

    static int strangePrinter(String s) {
        int n = s.length();
        int[][] dp = new int[n][n];
        for (int i = 0; i < n; i++) dp[i][i] = 1;

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                dp[i][j] = dp[i][j - 1] + 1;
                for (int k = i; k < j; k++) {
                    if (s.charAt(k) == s.charAt(j)) {
                        int mid = (k + 1 <= j - 1) ? dp[k + 1][j - 1] : 0;
                        dp[i][j] = Math.min(dp[i][j], dp[i][k] + mid);
                    }
                }
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(strangePrinter("aaabbb"));
        // 2
        System.out.println(strangePrinter("aba"));
        // 2
    }
}
```

**How to run:** `java StrangePrinter.java`

## 6. Walkthrough

Trace `dp` for `s = "aba"` (`i=0, j=2`):

| range | default (dp[i][j-1]+1) | match check | final dp[i][j] |
|---|---|---|---|
| [0,0] | — | — | 1 |
| [1,1] | — | — | 1 |
| [0,1] | dp[0][0]+1 = 2 | s[0]='a' != s[1]='b' | 2 |
| [0,2] | dp[0][1]+1 = 3 | s[0]='a' == s[2]='a': dp[0][0] + dp[1][1] = 1+1 = 2 | 2 |

`dp[0][2] = 2`, matching the expected answer: print `"aaa"`, then `"b"`. Time complexity is O(n^3) (O(n^2) ranges, each scanning O(n) positions for a match). Space is O(n^2).

## 7. Gotchas & takeaways

> Gotcha: when `s[k] == s[j]` and `k + 1 > j - 1` (the matched positions are adjacent, `k = j - 1`), the "middle" range is EMPTY — treat `dp[k+1][j-1]` as `0` in that case, not as an out-of-bounds lookup.

- `dp[i][j] = min(dp[i][j-1] + 1, min over matching k of dp[i][k] + dp[k+1][j-1])`: the "reuse an earlier run" idea is the entire savings mechanism in this problem.
- This differs from most interval-DP problems in this section by not summing two FULL sub-ranges plus a boundary cost — instead, one "wing" (`dp[k+1][j-1]`) can be empty, and the improvement is a MERGE, not a split.
- Related problems: Remove Boxes (a related "match a later position to an earlier one for a bonus" idea, but scoring SQUARED counts of merged boxes instead of counting print turns).
