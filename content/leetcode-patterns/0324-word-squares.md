---
card: leetcode-patterns
gi: 324
slug: word-squares
title: Word Squares
---

## 1. What it is

A "word square" is a set of words arranged in a grid where the `k`-th row and the `k`-th column spell the SAME word, for every `k`. Given an array of UNIQUE strings `words`, all the same length, return all word squares that can be built using words from `words` (a word may be reused). Example: `words = ["area","lead","wall","lady","ball"]` → `[["wall","area","lead","lady"],["ball","area","lead","lady"]]`.

## 2. Why & when

This is placement backtracking with a PREFIX-MATCHING constraint: each new row must start with the letters already implied by the columns built so far. Use this shape whenever a problem builds a grid or sequence row by row, and each new row's VALID CHOICES are constrained by a prefix derived from earlier rows.

## 3. Core concept

**Key idea:** place words one row at a time. Before placing row `r`, compute the REQUIRED PREFIX for row `r` by reading down column `r` across the already-placed rows. Only words in `words` that start with this exact prefix are valid candidates for row `r`.

**Steps:**
1. Precompute a `Map<String, List<String>>` from every possible PREFIX to the list of words in `words` starting with that prefix (built by taking every prefix length of every word).
2. Define `backtrack(rowIndex, squareSoFar)`. **Base case:** if `rowIndex == wordLength`, record `squareSoFar` as one valid result.
3. **Compute the required prefix** for row `rowIndex`: for each already-placed row `i` from `0` to `rowIndex - 1`, take the character at position `rowIndex` of that row's word — these characters, concatenated, form the required prefix.
4. **Look up** candidates for that prefix in the precomputed map. For each candidate word: choose it (append to `squareSoFar`), recurse to `rowIndex + 1`, then un-choose (remove it).

**Why it is correct:** a word square's definition means row `r`'s characters at columns `0..rowIndex-1` must exactly equal column `r`'s characters at rows `0..rowIndex-1` — which is exactly the "required prefix" computed from the already-placed rows. Restricting each row's candidates to only words matching that exact prefix (via the precomputed prefix map) guarantees every partial grid built during the search satisfies the word-square property so far, so a complete grid at the base case is automatically fully valid.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Building a word square row by row, computing each row's required prefix by reading down the columns of already-placed rows">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">row 0 = "wall"</text>
    <text x="10" y="45">row 1 needs prefix = column 1 of row 0 = "a" -&gt; candidates starting with "a": "area"</text>
    <text x="10" y="65">row 1 = "area"</text>
    <text x="10" y="85">row 2 needs prefix = col 2 of rows 0,1 = "l","e" = "le" -&gt; candidates: "lead"</text>
    <text x="10" y="105">row 2 = "lead"</text>
    <text x="10" y="125">row 3 needs prefix = col 3 of rows 0,1,2 = "l","a","d" = "lad" -&gt; candidates: "lady"</text>
    <rect x="10" y="140" width="220" height="24" fill="#3fb950"/><text x="120" y="157" fill="#0d1117" text-anchor="middle" font-size="10">[wall, area, lead, lady]</text>
  </g>
</svg>

Each new row's required prefix comes directly from reading down the corresponding column of the rows already placed.

## 5. Runnable example

```java
// WordSquares.java
import java.util.*;

public class WordSquares {

    // KEY INSIGHT: precomputing a prefix-to-words map turns "find
    // every word matching this required prefix" into an O(1) lookup,
    // instead of scanning all of `words` at every row.

    static List<List<String>> wordSquares(String[] words) {
        Map<String, List<String>> prefixMap = new HashMap<>();
        for (String word : words) {
            for (int i = 1; i <= word.length(); i++) {
                prefixMap.computeIfAbsent(word.substring(0, i), k -> new ArrayList<>()).add(word);
            }
        }

        List<List<String>> results = new ArrayList<>();
        int wordLength = words[0].length();
        for (String word : words) {
            List<String> square = new ArrayList<>();
            square.add(word);
            backtrack(1, wordLength, square, prefixMap, results);
        }
        return results;
    }

    static void backtrack(int rowIndex, int wordLength, List<String> square,
                           Map<String, List<String>> prefixMap, List<List<String>> results) {
        if (rowIndex == wordLength) {
            results.add(new ArrayList<>(square));
            return;
        }

        StringBuilder prefixBuilder = new StringBuilder();
        for (String row : square) prefixBuilder.append(row.charAt(rowIndex));
        String prefix = prefixBuilder.toString();

        List<String> candidates = prefixMap.getOrDefault(prefix, Collections.emptyList());
        for (String candidate : candidates) {
            square.add(candidate);                                        // choose
            backtrack(rowIndex + 1, wordLength, square, prefixMap, results); // recurse
            square.remove(square.size() - 1);                             // un-choose
        }
    }

    public static void main(String[] args) {
        List<List<String>> result = wordSquares(new String[]{"area", "lead", "wall", "lady", "ball"});
        for (List<String> square : result) System.out.println(square);
        // [wall, area, lead, lady]
        // [ball, area, lead, lady]
    }
}
```

**How to run:** `java WordSquares.java`

## 6. Walkthrough

Trace building the square starting with `"wall"`:

| rowIndex | required prefix (from earlier rows) | candidates | chosen |
|---|---|---|---|
| 1 | column 1 of ["wall"] = "a" | ["area"] | "area" |
| 2 | column 2 of ["wall","area"] = "l"+"e" = "le" | ["lead"] | "lead" |
| 3 | column 3 of ["wall","area","lead"] = "l"+"a"+"d" = "lad" | ["lady"] | "lady" |
| 4 (rowIndex==wordLength) | — | — | record ["wall","area","lead","lady"] |

Final result includes this square, plus `["ball","area","lead","lady"]` from a different starting word. Time complexity is O(n · 26^L · L) in the worst case, where `n` is the number of words and `L` is the word length — dominated by how many words share each prefix, heavily reduced by the prefix map lookup. Space is O(n · L), for the prefix map.

## 7. Gotchas & takeaways

> Gotcha: the prefix map must be built from EVERY prefix length of every word (not just the full word), since a partial square's required "prefix" is usually SHORTER than a full word — looking up only full-word entries would find zero candidates for any row before the last one.

- This is placement backtracking where the PRUNE is implicit in the lookup itself: any word not matching the required prefix simply never appears in `candidates`, so no separate validity check is needed inside the loop.
- Computing the required prefix by reading down a column of already-placed rows is a reusable technique for any grid problem where rows and columns must satisfy a shared relationship.
- Related problems: N-Queens (grid placement backtracking with column/diagonal constraints instead of prefix constraints), Sudoku Solver (grid placement with row/column/box uniqueness constraints).
