---
card: leetcode-patterns
gi: 347
slug: word-break
title: Word Break
---

## 1. What it is

Given a string `s` and a list of strings `wordDict`, return `true` if `s` can be split into a space-separated sequence of ONE OR MORE dictionary words. Each dictionary word can be reused any number of times. Example: `s = "leetcode"`, `wordDict = ["leet","code"]` → `true` (`"leet" + "code"`).

## 2. Why & when

This is Unbounded Knapsack's REACHABILITY variant, applied to STRING positions instead of numeric amounts: the "items" are dictionary words (reusable), and the "capacity" is the length of `s`. Recognize this shape whenever a problem asks if a sequence (string, or a list) can be fully partitioned into reusable chunks drawn from a given set.

## 3. Core concept

**Key idea:** build `dp[i]` = `true` if the PREFIX `s[0..i)` (the first `i` characters) can be fully split into dictionary words, for every `i` from `0` to `s.length()`.

**Steps:**
1. Create `dp[s.length() + 1]`, all `false`, with `dp[0] = true` (an empty prefix is trivially "already split").
2. For `i` from `1` to `s.length()`, for each `j` from `0` to `i - 1`: if `dp[j]` is `true` AND `s.substring(j, i)` is in `wordDict`, set `dp[i] = true` and stop checking further `j` for this `i`.
3. Return `dp[s.length()]`.

**Why it is correct:** `dp[i]` is reachable if SOME earlier reachable prefix `dp[j]` can be extended by one more dictionary word covering `s[j..i)`. Trying every possible split point `j` and checking both "is the earlier part breakable" and "is the remaining chunk a dictionary word" covers every possible way to build up to position `i`, since any valid full split has a well-defined LAST word, and that word's start position is exactly the `j` that makes this check succeed.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array over string positions for leetcode split into leet and code, showing dp of 4 and dp of 8 both true">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s="leetcode", wordDict={"leet","code"}</text>
    <text x="10" y="45">dp[0]=true (empty prefix)</text>
    <text x="10" y="65">dp[4]=true: dp[0]=true AND s[0..4)="leet" is in dict</text>
    <text x="10" y="85">dp[8]=true: dp[4]=true AND s[4..8)="code" is in dict</text>
    <rect x="10" y="105" width="260" height="24" fill="#3fb950"/><text x="140" y="122" fill="#0d1117" text-anchor="middle" font-size="10">dp[8] = true -&gt; whole string breakable</text>
  </g>
</svg>

Each reachable prefix chains into the next by matching one more dictionary word onto the end.

## 5. Runnable example

```java
// WordBreak.java
import java.util.List;

public class WordBreak {

    // KEY INSIGHT: unbounded-knapsack REACHABILITY over string
    // positions -- dp[i] is true if some earlier reachable prefix dp[j]
    // plus a dictionary word exactly covers s[j..i).

    static boolean wordBreak(String s, List<String> wordDict) {
        java.util.Set<String> dict = new java.util.HashSet<>(wordDict);
        boolean[] dp = new boolean[s.length() + 1];
        dp[0] = true;

        for (int i = 1; i <= s.length(); i++) {
            for (int j = 0; j < i; j++) {
                if (dp[j] && dict.contains(s.substring(j, i))) {
                    dp[i] = true;
                    break;
                }
            }
        }
        return dp[s.length()];
    }

    public static void main(String[] args) {
        System.out.println(wordBreak("leetcode", List.of("leet", "code")));
        // true
        System.out.println(wordBreak("catsandog", List.of("cats", "dog", "sand", "and", "cat")));
        // false
    }
}
```

**How to run:** `java WordBreak.java`

## 6. Walkthrough

Trace `wordBreak("leetcode", ["leet","code"])`:

| i | j checked | match found | dp[i] |
|---|---|---|---|
| 4 | j=0: s[0..4)="leet", dp[0]=true | yes | true |
| 8 | j=4: s[4..8)="code", dp[4]=true | yes | true |

`dp[8] = true` (`s.length() = 8`), matching the split `"leet" + "code"`. Time complexity is O(n^2) for the double loop, plus O(1) average per substring lookup with a hash set (or O(n) per substring creation, giving O(n^3) worst case with naive substring hashing). Space is O(n) for `dp`, plus O(k) for the dictionary set.

## 7. Gotchas & takeaways

> Gotcha: checking dictionary membership with a `List.contains` call instead of converting to a `HashSet` first turns each lookup from O(1) average into O(k) (where `k` is the dictionary size), silently degrading the whole algorithm from roughly O(n^2) to O(n^2 · k).

- `dp[j] && dict.contains(...)`, checked for every split point `j < i`: the general reachability template, adapted from numeric amounts to string positions.
- The `break` after finding one match is an optimization, not a correctness requirement — `dp[i]` only needs to become `true` once.
- Related problems: Word Break II (return every valid split, not just whether one exists — needs backtracking with memoization instead of a boolean array), Coin Change (same reachability shape, over numeric amounts instead of string prefixes).
