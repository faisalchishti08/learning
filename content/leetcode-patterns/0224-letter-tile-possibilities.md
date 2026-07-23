---
card: leetcode-patterns
gi: 224
slug: letter-tile-possibilities
title: Letter Tile Possibilities
---

## 1. What it is

You have a set of tiles, each printed with a letter (letters can repeat, e.g. `"AAB"`). Count how many non-empty sequences of letters you can make by arranging some or all of the tiles. Example: `tiles = "AAB"` → `8` (A, B, AA, AB, BA, AAB, ABA, BAA).

## 2. Why & when

This is a permutations problem with duplicate elements, but instead of listing the permutations, you count how many DISTINCT sequences exist at every length, not just the full length. Use this pattern whenever letters or items can repeat and order matters, and you need a count rather than a full listing that could contain accidental duplicates.

## 3. Core concept

**Key idea:** count each distinct letter's remaining supply instead of tracking used indices. At each step, try every letter that still has tiles left. Using counts instead of a `used[]` array over indices automatically prevents counting the same sequence twice when a letter repeats.

**Steps:**
1. Build a frequency map of each letter in `tiles` (e.g. `{A: 2, B: 1}`).
2. Define a recursive helper that, on each call, loops over every letter with count greater than 0.
3. For each such letter: decrement its count, add 1 to the answer (this placement itself is one valid sequence), recurse (which will try extending it further), then increment the count back (backtrack).
4. The total answer accumulates one count for every non-empty sequence produced, at every length.

**Why it is correct:** counting by letter, not by tile index, means two identical tiles (like the two `A`s) are never distinguished, so `"AA"` is counted once, not twice. Every recursive call that decrements a count and returns represents exactly one valid sequence of tiles, and every prefix along the recursion is counted, giving all lengths at once.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Frequency map A:2 B:1 explored by count, not by tile index">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">counts: A=2, B=1</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle">A</text>
    <text x="50" y="47">use A (count A: 2-&gt;1) +1 to answer</text>
    <rect x="10" y="64" width="30" height="24" fill="#3fb950"/><text x="25" y="81" fill="#0d1117" text-anchor="middle">A</text>
    <text x="50" y="81">use A again (count A: 1-&gt;0) "AA" +1</text>
    <rect x="10" y="98" width="30" height="24" fill="#3fb950"/><text x="25" y="115" fill="#0d1117" text-anchor="middle">B</text>
    <text x="50" y="115">use B (count B: 1-&gt;0) "AAB" +1</text>
    <text x="10" y="150">backtrack restores counts before trying B first at the top level</text>
  </g>
</svg>

Each box is one placement decision. The recursion counts a new sequence at every node it enters, not only at the leaves.

## 5. Runnable example

```java
// LetterTilePossibilities.java
import java.util.*;

public class LetterTilePossibilities {

    // Level 1 -- Brute force: generate every permutation of every
    // subset of tile INDICES, collect the resulting strings in a
    // Set<String> to remove duplicates caused by repeated letters,
    // then return the set size. Correct but wastes time building and
    // discarding many duplicate strings before deduplicating.

    // KEY INSIGHT: track remaining supply PER LETTER instead of per
    // tile index. This makes duplicate letters indistinguishable by
    // construction, so no sequence is ever generated twice.

    // Level 2 -- Optimal: backtrack over a letter -> count map.
    static int numTilePossibilities(String tiles) {
        Map<Character, Integer> counts = new HashMap<>();
        for (char c : tiles.toCharArray()) {
            counts.merge(c, 1, Integer::sum);
        }
        return dfs(counts);
    }

    static int dfs(Map<Character, Integer> counts) {
        int total = 0;
        for (char c : counts.keySet()) {
            int count = counts.get(c);
            if (count == 0) continue;
            total++; // this placement is one valid sequence
            counts.put(c, count - 1);
            total += dfs(counts);
            counts.put(c, count); // backtrack
        }
        return total;
    }

    // Level 3 -- Hardened: for very large tile sets, iterate the map
    // keys in a fixed order (e.g. a TreeMap) so results are
    // deterministic across runs; the count is unaffected either way.

    public static void main(String[] args) {
        System.out.println(numTilePossibilities("AAB"));
        // 8
    }
}
```

**How to run:** `java LetterTilePossibilities.java`

## 6. Walkthrough

Trace `dfs` on `counts = {A: 2, B: 1}`:

| Call | Letter tried | New count | total added here | Running total |
|---|---|---|---|---|
| top | A | A: 2→1 | 1 (for "A") | 1 |
| after A | A | A: 1→0 | 1 (for "AA") | 2 |
| after AA | B | B: 1→0 | 1 (for "AAB") | 3 |
| after A | B | B: 1→0 | 1 (for "AB") | 4 |
| after AB | A | A: 1→0 | 1 (for "ABA") | 5 |
| top (backtracked) | B | B: 1→0 | 1 (for "B") | 6 |
| after B | A | A: 2→1 | 1 (for "BA") | 7 |
| after BA | A | A: 1→0 | 1 (for "BAA") | 8 |

The final total is `8`, matching the expected answer. Time complexity is bounded by the number of distinct sequences produced, which is at most O(n · n!) for n tiles; space is O(n) for the recursion depth plus the frequency map.

## 7. Gotchas & takeaways

> Gotcha: using a `used[]` boolean array over tile indices (the standard Permutations II trick) also works here if you first sort the tiles and skip same-level duplicates, but the letter-count map is simpler and avoids the sort-and-skip logic entirely.

- Every recursive call that places a letter counts as a new answer immediately, not just the calls that reach a "full" arrangement, because the problem asks for sequences of ANY length.
- Decrementing and restoring a shared count map is the backtracking step, exactly like adding and removing an element from a path list in other subset or combination problems.
- Related problems: Permutations II (duplicate handling via sorting and index skips), Subsets II (same duplicate-avoidance goal, different structure).
