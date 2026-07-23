---
card: leetcode-patterns
gi: 223
slug: palindrome-partitioning
title: Palindrome Partitioning
---

## 1. What it is

Given a string `s`, split it into pieces so that every piece reads the same forwards and backwards (a palindrome). Return every way to do this split. Example: `s = "aab"` → `[["a","a","b"], ["aa","b"]]`.

## 2. Why & when

This is the "generate all splits" version of subsets. Instead of choosing which elements to include, you choose where to cut the string. Use it whenever a problem asks for every valid way to break a string into parts, and each part must pass a check (here, "is this part a palindrome?").

## 3. Core concept

**Key idea:** at each position in the string, try every possible next cut. Only take a cut if the substring it creates is a palindrome. Recurse on the rest of the string. When you reach the end, the current list of pieces is one valid answer.

**Steps:**
1. Start a recursive helper at index `0` with an empty list of pieces.
2. At index `start`, loop `end` from `start + 1` to the length of `s`.
3. Take the substring `s[start:end]`. If it is a palindrome, add it to the current path.
4. Recurse with `start = end`. When the recursion returns, remove the piece (backtrack) and try the next `end`.
5. When `start` reaches the length of `s`, the path is a complete partition. Save a copy of it.

**Why it is correct:** every recursive call fixes the next cut boundary. Trying every `end` value at every `start` covers every possible way to split the remaining string. The palindrome check prunes any branch that could never lead to a valid answer, so the recursion only explores splits that are still possible.

## 4. Diagram

<svg viewBox="0 0 460 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tree of cuts over the string aab, only palindrome substrings are kept">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">"aab"</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle">a</text>
    <text x="50" y="47">cut after "a" (palindrome)</text>
    <rect x="10" y="64" width="60" height="24" fill="#3fb950"/><text x="40" y="81" fill="#0d1117" text-anchor="middle">aa</text>
    <text x="80" y="81">cut after "aa" (palindrome)</text>
    <rect x="90" y="30" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="105" y="47" fill="#e6edf3" text-anchor="middle">ab</text>
    <text x="130" y="47" fill="#f85149">not a palindrome, skip</text>
    <text x="10" y="130">from "a": next piece "a" then "b" -&gt; ["a","a","b"]</text>
    <text x="10" y="150">from "aa": next piece "b" -&gt; ["aa","b"]</text>
  </g>
</svg>

Each level of the tree picks the next cut. A branch that is not a palindrome stops immediately instead of recursing further.

## 5. Runnable example

```java
// PalindromePartitioning.java
import java.util.*;

public class PalindromePartitioning {

    // Level 1 -- Brute force: generate every possible split of the
    // string into any number of pieces (like subsets between gaps),
    // then filter out the splits where any piece is not a palindrome.
    // Wastes time building splits that fail early on the first piece.

    // KEY INSIGHT: check the palindrome condition WHILE building the
    // split, not after. If a prefix piece fails, stop that branch
    // immediately instead of finishing the split and checking later.

    // Level 2 -- Optimal: backtrack over cut positions, checking each
    // candidate piece as soon as it is proposed.
    static List<List<String>> partition(String s) {
        List<List<String>> result = new ArrayList<>();
        dfs(s, 0, new ArrayList<>(), result);
        return result;
    }

    static void dfs(String s, int start, List<String> path, List<List<String>> result) {
        if (start == s.length()) {
            result.add(new ArrayList<>(path));
            return;
        }
        for (int end = start + 1; end <= s.length(); end++) {
            String piece = s.substring(start, end);
            if (isPalindrome(piece)) {
                path.add(piece);
                dfs(s, end, path, result);
                path.remove(path.size() - 1);
            }
        }
    }

    static boolean isPalindrome(String p) {
        int i = 0, j = p.length() - 1;
        while (i < j) {
            if (p.charAt(i) != p.charAt(j)) return false;
            i++;
            j--;
        }
        return true;
    }

    // Level 3 -- Hardened: for long strings with many repeated
    // characters, precompute a table isPal[i][j] with dynamic
    // programming before the DFS, so each palindrome check becomes
    // O(1) instead of O(n) per substring.

    public static void main(String[] args) {
        System.out.println(partition("aab"));
        // [[a, a, b], [aa, b]]
    }
}
```

**How to run:** `java PalindromePartitioning.java`

## 6. Walkthrough

Trace `dfs` on `s = "aab"`, `start = 0`:

| start | end tried | piece | palindrome? | action |
|---|---|---|---|---|
| 0 | 1 | "a" | yes | add "a", recurse with start=1 |
| 1 | 2 | "a" | yes | add "a", recurse with start=2 |
| 2 | 3 | "b" | yes | add "b", recurse with start=3, save `["a","a","b"]` |
| 0 | 2 | "aa" | yes | add "aa", recurse with start=2 |
| 2 | 3 | "b" | yes | add "b", recurse with start=3, save `["aa","b"]` |
| 0 | 3 | "aab" | no | skip |

Both valid partitions are found. Time complexity is O(n · 2^n) in the worst case, since there are up to 2^n ways to split a string of length n and each palindrome check costs up to O(n). Space is O(n) for the recursion stack and the current path.

## 7. Gotchas & takeaways

> Gotcha: checking `isPalindrome` from scratch on every candidate piece is correct but slow on long strings with many repeats. Precomputing a palindrome table with dynamic programming turns each check into O(1) and speeds up the whole search.

- This is the subsets pattern applied to string positions instead of array elements: at each step you choose "where does the next piece end," not "is this element in or out."
- The backtracking shape (add, recurse, remove) is identical to Subsets and Combination Sum; only the validity check changes.
- Related problems: Palindrome Partitioning II (minimum cuts, a dynamic programming variant), Word Break (same cut-position recursion, different validity check).
