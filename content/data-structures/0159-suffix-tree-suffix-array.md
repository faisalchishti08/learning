---
card: data-structures
gi: 159
slug: suffix-tree-suffix-array
title: Suffix tree & suffix array
---

## 1. What it is

A **suffix array** is a sorted list of every starting position of every suffix of a string. A **suffix tree** is a compressed [trie](0126-prefix-tree-trie-structure.md) that holds every suffix of a string as a root-to-leaf path, with common prefixes merged into shared edges. Both let you search a text for any pattern far faster than scanning the text each time.

## 2. Why & when

Use these when you must run **many** substring searches against the **same** text — a genome, a large document corpus, a codebase search index. A naive substring search costs `O(n * m)` for text length `n` and pattern length `m`, repeated for every query. Building a suffix array once costs `O(n log n)`, after which each pattern search costs only `O(m log n)`. A suffix tree does even better, `O(m)` per search after an `O(n)` build, at the cost of much more memory and a fiddlier implementation.

## 3. Core concept

**The suffix array's shape.** For a string `s` of length `n`, list all `n` suffixes: `s[0..]`, `s[1..]`, ..., `s[n-1..]`. Sort them alphabetically. The suffix array stores only the **starting index** of each suffix, in sorted order — not the suffixes themselves, which would waste `O(n^2)` space.

**The invariant.** Because the array is sorted, every occurrence of a pattern `p` in `s` corresponds to a **contiguous block** of suffixes in the array — every suffix in that block starts with `p`. This is what makes binary search possible: search for the first and last suffix that could start with `p`, the same way you binary-search a sorted array for a range of equal values.

**The suffix tree's shape.** A trie of all suffixes, but with non-branching chains of edges compressed into a single edge labeled with a substring instead of one character. This compression is what keeps the tree at `O(n)` nodes instead of `O(n^2)` characters.

**Why it makes search fast.** Searching a suffix array for pattern `p` uses **binary search**: compare `p` against the middle suffix; since the array is sorted, decide to go left or right, exactly like binary search in a sorted array. `O(log n)` comparisons, each costing up to `O(m)` to compare characters, gives `O(m log n)` total. A suffix tree instead **walks down from the root** one edge at a time, matching characters of `p` against edge labels; because look-ups down a trie are direct (no comparison needed, just a child lookup), this costs only `O(m)`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Suffix array for the string banana with sorted suffixes, and a binary search range for pattern an">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">string: b a n a n a $ (indices 0-6)</text>

    <g>
      <text x="30" y="60">idx</text><text x="90" y="60">suffix</text>
      <text x="30" y="80">6</text><text x="90" y="80">$</text>
      <text x="30" y="100">5</text><text x="90" y="100">a$</text>
      <text x="30" y="120" fill="#f0883e">3</text><text x="90" y="120" fill="#f0883e">ana$</text>
      <text x="30" y="140" fill="#f0883e">1</text><text x="90" y="140" fill="#f0883e">anana$</text>
      <text x="30" y="160">0</text><text x="90" y="160">banana$</text>
      <text x="30" y="180">4</text><text x="90" y="180">na$</text>
      <text x="30" y="200">2</text><text x="90" y="200">nana$</text>
    </g>

    <rect x="20" y="108" width="140" height="42" fill="none" stroke="#f0883e" stroke-dasharray="3,3"/>
    <text x="300" y="120" fill="#f0883e" font-size="9">pattern "an" matches a contiguous</text>
    <text x="300" y="135" fill="#f0883e" font-size="9">block: suffix array rows 2-3</text>
    <text x="300" y="155" font-size="9" fill="#8b949e">binary search finds this block in O(log n) steps</text>
  </g>
</svg>

Sorting turns "does the pattern occur?" into "binary search for a contiguous block."

## 5. Runnable example

```java
// SuffixArray.java
import java.util.*;

public class SuffixArray {

    // Basic: build a suffix array the simple way (sort all suffixes) and check if a pattern exists.
    static class SimpleSuffixArray {
        String text;
        Integer[] suffixArray;

        SimpleSuffixArray(String text) {
            this.text = text + "$"; // sentinel, sorts before all real characters
            int n = this.text.length();
            suffixArray = new Integer[n];
            for (int i = 0; i < n; i++) suffixArray[i] = i;
            Arrays.sort(suffixArray, (a, b) -> this.text.substring(a).compareTo(this.text.substring(b)));
        }

        boolean contains(String pattern) {
            int lo = 0, hi = suffixArray.length - 1;
            while (lo <= hi) {
                int mid = (lo + hi) / 2;
                String suffix = text.substring(suffixArray[mid]);
                int cmp = suffix.length() >= pattern.length()
                    ? suffix.substring(0, pattern.length()).compareTo(pattern)
                    : suffix.compareTo(pattern.substring(0, Math.min(pattern.length(), suffix.length())));
                if (cmp == 0) return true;
                if (cmp < 0) lo = mid + 1; else hi = mid - 1;
            }
            return false;
        }
    }

    static void basicLevel() {
        SimpleSuffixArray sa = new SimpleSuffixArray("banana");
        System.out.println("basic: contains(\"ana\") -> " + sa.contains("ana"));
        System.out.println("basic: contains(\"xyz\") -> " + sa.contains("xyz"));
    }

    // Intermediate: count how many times a pattern occurs, using the contiguous-block property.
    static class CountingSuffixArray extends SimpleSuffixArray {
        CountingSuffixArray(String text) { super(text); }

        int countOccurrences(String pattern) {
            int count = 0;
            for (int idx : suffixArray) {
                String suffix = text.substring(idx);
                if (suffix.startsWith(pattern)) count++;
            }
            return count;
        }
    }

    static void intermediateLevel() {
        CountingSuffixArray sa = new CountingSuffixArray("banana");
        System.out.println("intermediate: occurrences of \"ana\" -> " + sa.countOccurrences("ana"));
        System.out.println("intermediate: occurrences of \"a\" -> " + sa.countOccurrences("a"));
    }

    // Advanced: the longest repeated substring, found via adjacent suffixes' longest common prefix (LCP).
    static int longestCommonPrefix(String a, String b) {
        int len = Math.min(a.length(), b.length());
        int i = 0;
        while (i < len && a.charAt(i) == b.charAt(i)) i++;
        return i;
    }

    static String longestRepeatedSubstring(String text) {
        SimpleSuffixArray sa = new SimpleSuffixArray(text);
        int bestLen = 0, bestStart = 0;
        for (int i = 1; i < sa.suffixArray.length; i++) {
            String s1 = sa.text.substring(sa.suffixArray[i - 1]);
            String s2 = sa.text.substring(sa.suffixArray[i]);
            int lcp = longestCommonPrefix(s1, s2);
            if (lcp > bestLen) { bestLen = lcp; bestStart = sa.suffixArray[i]; }
        }
        return bestLen == 0 ? "" : sa.text.substring(bestStart, bestStart + bestLen);
    }

    static void advancedLevel() {
        System.out.println("advanced: longest repeated substring of \"banana\" -> \"" + longestRepeatedSubstring("banana") + "\"");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java SuffixArray.java`

## 6. Walkthrough

Build the suffix array for `"banana$"` (the `$` sentinel is smaller than every real character, and guarantees no suffix is a prefix of another). List all 7 suffixes, then sort:

```
$          (index 6)
a$         (index 5)
ana$       (index 3)
anana$     (index 1)
banana$    (index 0)
na$        (index 4)
nana$      (index 2)
```

Now search for pattern `"ana"`. Binary search starts at the middle (index 3 in the sorted list, suffix `"anana$"`). Compare the first 3 characters, `"ana"` vs pattern `"ana"`: equal, so return `true` immediately (in the full version, this narrows to a block and both `"ana$"` and `"anana$"` match).

Count occurrences of `"ana"`: scan the sorted array for every suffix starting with `"ana"` — `"ana$"` and `"anana$"` both qualify, giving `2` (these correspond to `"ana"` starting at index 1 and index 3 in the original string).

Find the longest repeated substring: compare each pair of **adjacent** suffixes in the sorted array (since repeats sort next to each other) and take their longest common prefix. `"ana$"` and `"anana$"` share the prefix `"ana"`, length `3` — the longest of any adjacent pair — so the answer is `"ana"`.

**Complexity.** Naive suffix array build (sorting full substrings): `O(n^2 log n)`. A proper build (using radix sort on ranks) achieves `O(n log n)`. Pattern search: `O(m log n)`. A suffix tree builds in `O(n)` (Ukkonen's algorithm) and searches in `O(m)`, but uses far more memory per character than a suffix array.

## 7. Gotchas & takeaways

> The naive `String.substring()` + `compareTo()` approach shown above is `O(n)` per comparison and `O(n log n)` comparisons, making the whole build `O(n^2 log n)` — fine for teaching and small strings, but too slow for a real genome or large corpus. Production code builds ranks incrementally (the DC3/skew algorithm, or Ukkonen's algorithm for suffix trees) to reach `O(n log n)` or `O(n)`.

- Always append a sentinel character (like `$`) smaller than every real character. Without it, one suffix can be a prefix of another, which breaks some algorithms' assumptions.
- Prefer a suffix **array** in practice: it uses far less memory than a suffix tree (roughly `4n` bytes vs `20n`+ for a tree), and with an added LCP (longest common prefix) array, it matches most of a suffix tree's query power.
- Reach for a suffix tree only when you need `O(m)` (not `O(m log n)`) pattern matching and can afford the memory — for example, matching millions of short queries against one huge, unchanging text.
