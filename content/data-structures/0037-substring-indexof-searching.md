---
card: data-structures
gi: 37
slug: substring-indexof-searching
title: Substring, indexOf & searching
---

## 1. What it is

`substring(begin, end)` extracts a portion of a string as a new `String`. `indexOf(target)` searches for the first occurrence of a character or sub-string and returns its position, or `-1` if not found. Both are core building blocks for text-processing code — extracting a piece, or locating where a piece begins.

## 2. Why & when

Reach for `substring` whenever you need to pull out a known portion of text — a date's year from `"2026-07-31"`, or a filename without its extension. Reach for `indexOf`/`lastIndexOf`/`contains` whenever you need to locate or test for a sub-string before deciding what to do next — these are the simplest tools before reaching for more advanced pattern matching (covered in [Pattern matching (naive, KMP, Rabin-Karp overview)](0041-pattern-matching-naive-kmp-rabin-karp-overview.md)).

## 3. Core concept

**`substring(begin, end)` uses a half-open range.** `begin` is inclusive, `end` is exclusive — `"hello".substring(1, 4)` returns `"ell"` (indices 1, 2, 3), not including index 4. `substring(begin)` alone extracts from `begin` to the end of the string.

**`substring` since Java 7 always copies.** Older Java versions let `substring` share the original string's backing array (a fast O(1) operation, but one that could leak memory by keeping a huge original string alive through a tiny substring reference). Modern Java always copies the extracted range into a new array — O(k) for a result of length `k`, safer but no longer free.

**`indexOf` is a linear scan, O(n).** Searching for a single character checks each position until a match; searching for a sub-string of length `m` in a string of length `n` costs up to O(n·m) in the worst case with the naive approach `String.indexOf` actually uses (checking a full potential match at every position) — fine for typical short patterns, but not the fastest possible for very long patterns.

**`indexOf(target, fromIndex)` searches starting at a given position.** This lets you find *all* occurrences by looping: search, note the position, then search again starting just after it — the classic "find every match" pattern.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="substring(1,4) extracting indices 1 through 3 (end exclusive) from a string">
  <g font-family="sans-serif" font-size="12">
    <rect x="60" y="30" width="40" height="30" fill="#161b22" stroke="#8b949e"/><text x="80" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">h</text>
    <rect x="100" y="30" width="40" height="30" fill="#0d1117" stroke="#3fb950"/><text x="120" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">e</text>
    <rect x="140" y="30" width="40" height="30" fill="#0d1117" stroke="#3fb950"/><text x="160" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">l</text>
    <rect x="180" y="30" width="40" height="30" fill="#0d1117" stroke="#3fb950"/><text x="200" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">l</text>
    <rect x="220" y="30" width="40" height="30" fill="#161b22" stroke="#8b949e"/><text x="240" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">o</text>
    <text x="80" y="80" fill="#8b949e" text-anchor="middle" font-size="10">idx 0</text>
    <text x="240" y="80" fill="#8b949e" text-anchor="middle" font-size="10">idx 4</text>
    <text x="160" y="110" fill="#79c0ff" text-anchor="middle" font-size="10">substring(1, 4) -&gt; "ell" (begin inclusive, end exclusive)</text>
  </g>
</svg>

`substring(1, 4)` includes index 1 through 3, and stops before index 4 — the highlighted "ell".

## 5. Runnable example

```java
// SubstringIndexOfSearching.java
import java.util.ArrayList;
import java.util.List;

public class SubstringIndexOfSearching {

    // Basic: substring with the half-open [begin, end) range.
    static void basicLevel() {
        String s = "hello world";
        System.out.println("basic: substring(1,4) -> " + s.substring(1, 4));   // "ell"
        System.out.println("basic: substring(6) -> " + s.substring(6));        // "world"
    }

    // Intermediate: indexOf, lastIndexOf, and contains for locating and testing.
    static void intermediateLevel() {
        String s = "the quick brown fox jumps over the lazy dog";
        System.out.println("intermediate: indexOf(\"the\") -> " + s.indexOf("the"));         // first "the"
        System.out.println("intermediate: lastIndexOf(\"the\") -> " + s.lastIndexOf("the"));  // last "the"
        System.out.println("intermediate: contains(\"fox\") -> " + s.contains("fox"));
        System.out.println("intermediate: indexOf(\"cat\") (absent) -> " + s.indexOf("cat")); // -1
    }

    // Advanced: find every occurrence of a sub-string using indexOf(target, fromIndex) in a loop.
    static List<Integer> findAllOccurrences(String text, String pattern) {
        List<Integer> positions = new ArrayList<>();
        int from = 0;
        while (true) {
            int found = text.indexOf(pattern, from);
            if (found == -1) break;
            positions.add(found);
            from = found + 1; // move past this match to find overlapping or later occurrences
        }
        return positions;
    }

    static void advancedLevel() {
        String text = "abababab";
        List<Integer> positions = findAllOccurrences(text, "aba");
        System.out.println("advanced: all \"aba\" occurrences in \"" + text + "\" -> " + positions);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SubstringIndexOfSearching.java`, then run `java SubstringIndexOfSearching.java`.

## 6. Walkthrough

1. `basicLevel()` calls `s.substring(1, 4)` on `"hello world"`, extracting indices 1, 2, and 3 — the letters `'e'`, `'l'`, `'l'` — giving `"ell"`. `substring(6)` extracts from index 6 to the end, giving `"world"`.
2. `intermediateLevel()` calls `indexOf("the")`, which scans forward and returns the position of the first match; `lastIndexOf("the")` scans backward conceptually and returns the last match's position. `contains("fox")` internally just checks `indexOf("fox") != -1`.
3. `indexOf("cat")` finds no match anywhere in the string and returns `-1`, the standard "not found" sentinel for these methods.
4. `advancedLevel()`'s `findAllOccurrences` searches `"abababab"` for `"aba"`. It finds the first match at index 0, then searches again starting at index 1 (`found + 1`, not `found + pattern.length()`, so overlapping matches are not skipped), finding the next match at index 2, then index 4, giving `[0, 2, 4]`.

## 7. Gotchas & takeaways

> Gotcha: `substring(begin, end)` throws `StringIndexOutOfBoundsException` if `begin < 0`, `end > length()`, or `begin > end` — always double-check computed indices (especially `end`) before calling it, particularly when `end` comes from another search like `indexOf`.

- `substring(begin, end)` is a half-open range: `begin` inclusive, `end` exclusive, and it always allocates a new copy in modern Java.
- `indexOf`/`lastIndexOf` are O(n)-ish linear scans that return `-1` when nothing matches — always check for `-1` before using the result as an index.
- Use `indexOf(target, fromIndex)` in a loop to find every occurrence of a pattern in a string.
- Related concepts: [Pattern matching (naive, KMP, Rabin-Karp overview)](0041-pattern-matching-naive-kmp-rabin-karp-overview.md), [String methods (split, replace, chars)](0043-string-methods-split-replace-chars.md).
