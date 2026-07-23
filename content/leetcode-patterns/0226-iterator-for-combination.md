---
card: leetcode-patterns
gi: 226
slug: iterator-for-combination
title: Iterator for Combination
---

## 1. What it is

Design a class `CombinationIterator` that, given a string `characters` (sorted, distinct letters) and a number `combinationLength`, produces every combination of that length, one at a time, in lexicographical order. It needs a `next()` method that returns the next combination, and a `hasNext()` method that says whether one remains. Example: `characters = "abc"`, `combinationLength = 2` → combinations in order are `"ab"`, `"ac"`, `"bc"`.

## 2. Why & when

This is the Combinations pattern wrapped behind an iterator interface instead of a method that returns everything at once. Use this shape whenever a caller wants results one at a time — for example to stop early, or to avoid holding every combination in memory at once — instead of getting a full list up front.

## 3. Core concept

**Key idea:** you can still use ordinary backtracking to generate every combination, since `combinationLength` is small enough that the full list is manageable. Generate them all once, in the constructor, in lexicographical order (which the standard combinations backtracking already produces when the input is sorted). Then `next()` and `hasNext()` just walk a pointer through that precomputed list.

**Steps:**
1. In the constructor, run the standard Combinations backtracking: DFS with a `start` index, adding one character at a time, saving a copy of `path` (joined into a string) whenever `path` reaches `combinationLength`.
2. Store all saved combinations in a list, in the order backtracking naturally produced them (already lexicographical, because the loop scans characters left to right and `characters` is sorted).
3. Keep an index pointer starting at `0`.
4. `next()` returns the combination at the pointer, then advances the pointer.
5. `hasNext()` returns whether the pointer is still less than the list size.

**Why it is correct:** because `characters` is sorted and the DFS loop always tries the smallest available next character first, the order combinations are saved in is exactly lexicographical order. Precomputing the whole list up front turns `next()` and `hasNext()` into simple O(1) pointer operations, which matches what an iterator interface should provide.

## 4. Diagram

<svg viewBox="0 0 440 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Precomputed list ab, ac, bc walked by a pointer that next() advances">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">precomputed list (built once, in the constructor):</text>
    <rect x="10" y="30" width="50" height="26" fill="#3fb950"/><text x="35" y="48" fill="#0d1117" text-anchor="middle">ab</text>
    <rect x="65" y="30" width="50" height="26" fill="#161b22" stroke="#58a6ff"/><text x="90" y="48" fill="#e6edf3" text-anchor="middle">ac</text>
    <rect x="120" y="30" width="50" height="26" fill="#161b22" stroke="#58a6ff"/><text x="145" y="48" fill="#e6edf3" text-anchor="middle">bc</text>
    <text x="10" y="90">pointer = 0: hasNext() -&gt; true</text>
    <text x="10" y="110">next() returns "ab", pointer becomes 1</text>
    <text x="10" y="130">next() returns "ac", pointer becomes 2</text>
    <text x="10" y="150">next() returns "bc", pointer becomes 3; hasNext() -&gt; false</text>
  </g>
</svg>

The backtracking work happens once, up front. Each call to `next()` afterward is just reading the list and moving the pointer forward.

## 5. Runnable example

```java
// CombinationIterator.java
import java.util.*;

public class CombinationIterator {

    // Level 1 -- Brute force: generate every subset of `characters` of
    // ANY length using full subsets backtracking, filter to only the
    // ones of length combinationLength, then sort the filtered list.
    // Wastes time building and discarding subsets of the wrong length.

    // KEY INSIGHT: generate ONLY combinations of the target length
    // directly, using the standard Combinations backtracking, which
    // already produces lexicographical order for free when the input
    // is sorted -- no separate sort step needed afterward.

    // Level 2 -- Optimal: precompute all combinations once, then serve
    // them from a list with a pointer.
    private final List<String> combos = new ArrayList<>();
    private int pointer = 0;

    public CombinationIterator(String characters, int combinationLength) {
        dfs(characters, combinationLength, 0, new StringBuilder());
    }

    private void dfs(String characters, int length, int start, StringBuilder path) {
        if (path.length() == length) {
            combos.add(path.toString());
            return;
        }
        for (int i = start; i < characters.length(); i++) {
            path.append(characters.charAt(i));
            dfs(characters, length, i + 1, path);
            path.deleteCharAt(path.length() - 1);
        }
    }

    public String next() {
        return combos.get(pointer++);
    }

    public boolean hasNext() {
        return pointer < combos.size();
    }

    // Level 3 -- Hardened: for very large characters/combinationLength
    // combinations where precomputing all of them would use too much
    // memory, track indices of the current combination directly and
    // advance them like an odometer inside next(), generating each
    // combination lazily instead of storing the full list.

    public static void main(String[] args) {
        CombinationIterator it = new CombinationIterator("abc", 2);
        while (it.hasNext()) {
            System.out.println(it.next());
        }
        // ab
        // ac
        // bc
    }
}
```

**How to run:** `java CombinationIterator.java`

## 6. Walkthrough

Construction: `dfs("abc", 2, 0, "")` runs the standard combinations backtracking:

| path built | length reached? | saved combo |
|---|---|---|
| "a" → "ab" | yes | "ab" |
| "a" → "ac" | yes | "ac" |
| "b" → "bc" | yes | "bc" |

So `combos = ["ab", "ac", "bc"]`, `pointer = 0`.

Calling the iterator:

| Call | pointer before | Return value | pointer after |
|---|---|---|---|
| `hasNext()` | 0 | true | 0 |
| `next()` | 0 | "ab" | 1 |
| `hasNext()` | 1 | true | 1 |
| `next()` | 1 | "ac" | 2 |
| `hasNext()` | 2 | true | 2 |
| `next()` | 2 | "bc" | 3 |
| `hasNext()` | 3 | false | 3 |

Constructor time is O(C(n, k) · k), where `n` is the length of `characters` and `k` is `combinationLength`, for generating and copying each combination. `next()` and `hasNext()` are both O(1). Space is O(C(n, k) · k) to store every combination.

## 7. Gotchas & takeaways

> Gotcha: precomputing the full list makes `next()` and `hasNext()` trivially fast, but it uses memory proportional to the total number of combinations up front, which does not scale if `characters` is long and `combinationLength` is near half its length (where the combination count peaks). A lazy, index-advancing version trades simpler code for less memory.

- The design mirrors a database cursor or a paginated API: do the expensive work once, then serve cheap, repeated reads from the cached result.
- Because `characters` is sorted and the backtracking loop always tries the next available character in order, no explicit sort is needed to get lexicographical order.
- Related problems: Combinations (the same backtracking core, returned as one list instead of wrapped in an iterator), Peeking Iterator (another iterator-design problem built on wrapping an existing iterator).
