---
card: leetcode-patterns
gi: 348
slug: word-break-ii
title: Word Break II
---

## 1. What it is

Given a string `s` and a list of strings `wordDict`, return ALL possible ways to split `s` into a space-separated sequence of dictionary words, as a list of sentences. Each dictionary word can be reused any number of times. Example: `s = "catsanddog"`, `wordDict = ["cat","cats","and","sand","dog"]` → `["cats and dog", "cat sand dog"]`.

## 2. Why & when

Word Break (the earlier page) only asks "CAN `s` be split" — a reachability check. This problem asks for EVERY way, which means you cannot collapse the answer into a single boolean; you must build up actual sentences. Recognize this shape whenever a "can this be done" DP problem is upgraded to "list every way it can be done" — the fix is to memoize a LIST OF RESULTS per state instead of a single true/false or count.

## 3. Core concept

**Key idea:** for each starting position `start` in `s`, find every dictionary word that matches `s` beginning at `start`, then recursively find every way to break the REST of the string, and prepend the matched word to each of those results. Memoize by `start` so overlapping suffixes are solved only once.

**Steps:**
1. Define `breakFrom(start)`, returning the list of all valid sentences for `s.substring(start)`.
2. If `start == s.length()`, return a list containing one empty sentence (the base case: nothing left to break).
3. If `start` is already memoized, return the cached list.
4. Otherwise, for each `end` from `start + 1` to `s.length()`: if `s.substring(start, end)` is in the dictionary, recursively call `breakFrom(end)`, and for each resulting suffix sentence, prepend this word (with a space if the suffix is non-empty) to build a full sentence for `start`.
5. Store and return the combined list for `start`.

**Why memoization is essential here:** without it, overlapping suffixes (e.g. the suffix starting at position `4` might be reached from multiple different first words) get RE-SOLVED from scratch every time, causing exponential blowup — memoizing by `start` ensures each suffix's full list of sentences is computed exactly once, then reused by every path that reaches that same `start`.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="recursion tree for catsanddog showing two paths cat then sanddog and cats then anddog both reaching the shared suffix dog">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">s="catsanddog", dict={"cat","cats","and","sand","dog"}</text>
    <text x="10" y="45">breakFrom(0): word="cat" -&gt; breakFrom(3); word="cats" -&gt; breakFrom(4)</text>
    <text x="10" y="65">breakFrom(3): word="sand" -&gt; breakFrom(7)</text>
    <text x="10" y="85">breakFrom(4): word="and" -&gt; breakFrom(7)  (SAME memoized call as above)</text>
    <text x="10" y="105">breakFrom(7): word="dog" -&gt; breakFrom(10) -&gt; [""]</text>
    <rect x="10" y="125" width="300" height="24" fill="#3fb950"/><text x="160" y="142" fill="#0d1117" text-anchor="middle" font-size="10">breakFrom(7) computed ONCE, reused by both paths</text>
  </g>
</svg>

Both `"cat"+"sand"` and `"cats"+"and"` reach position `7` and share the memoized result for the rest of the string.

## 5. Runnable example

```java
// WordBreakII.java
import java.util.*;

public class WordBreakII {

    // KEY INSIGHT: "list every way" upgrades the reachability DP into
    // a memoized recursion where each state caches a LIST of sentences,
    // not a boolean -- shared suffixes are still solved only once.

    static List<String> wordBreak(String s, List<String> wordDict) {
        Set<String> dict = new HashSet<>(wordDict);
        Map<Integer, List<String>> memo = new HashMap<>();
        return breakFrom(s, 0, dict, memo);
    }

    static List<String> breakFrom(String s, int start, Set<String> dict,
                                   Map<Integer, List<String>> memo) {
        if (start == s.length()) {
            List<String> base = new ArrayList<>();
            base.add("");
            return base;
        }
        if (memo.containsKey(start)) {
            return memo.get(start);
        }

        List<String> result = new ArrayList<>();
        for (int end = start + 1; end <= s.length(); end++) {
            String word = s.substring(start, end);
            if (dict.contains(word)) {
                for (String suffixSentence : breakFrom(s, end, dict, memo)) {
                    String sentence = suffixSentence.isEmpty()
                            ? word
                            : word + " " + suffixSentence;
                    result.add(sentence);
                }
            }
        }
        memo.put(start, result);
        return result;
    }

    public static void main(String[] args) {
        List<String> result = wordBreak("catsanddog",
                List.of("cat", "cats", "and", "sand", "dog"));
        System.out.println(result);
        // [cats and dog, cat sand dog]
    }
}
```

**How to run:** `java WordBreakII.java`

## 6. Walkthrough

Trace `breakFrom("catsanddog", 0, ...)`:

| call | matched word tried | recurses into | contributes |
|---|---|---|---|
| breakFrom(0) | "cat" (0..3) | breakFrom(3) | "cat" + each result of breakFrom(3) |
| breakFrom(0) | "cats" (0..4) | breakFrom(4) | "cats" + each result of breakFrom(4) |
| breakFrom(3) | "sand" (3..7) | breakFrom(7) | "sand" + each result of breakFrom(7) |
| breakFrom(4) | "and" (4..7) | breakFrom(7) (MEMOIZED, reused) | "and" + each result of breakFrom(7) |
| breakFrom(7) | "dog" (7..10) | breakFrom(10) → [""] | "dog" |

Final result: `["cats and dog", "cat sand dog"]`. Time complexity is O(2^n) in the worst case (a string that breaks in exponentially many ways, like `"aaaa...a"` with dictionary `["a","aa",...]`), since the OUTPUT itself can be exponentially large; memoization only prevents redundant work on shared sub-suffixes, not on the final combinatorial output size. Space is O(n) for the recursion depth, plus the memoized results.

## 7. Gotchas & takeaways

> Gotcha: unlike Word Break, memoization here does NOT guarantee polynomial time — if the number of valid sentences itself grows exponentially (e.g. `s` of all the same character with a dictionary containing every prefix length), the output size alone forces exponential time and space, regardless of memoization.

- Memoize a LIST per state, not a boolean or count — this is the general fix for upgrading a reachability/counting DP into an "enumerate all ways" problem.
- Building sentences bottom-up (suffix results computed first, then prefixed with each matching word) avoids reconstructing paths after the fact with a separate backtracking pass.
- Related problems: Word Break (the reachability-only version — check this first, since if it returns `false`, Word Break II should return an empty list immediately without running the full enumeration).
