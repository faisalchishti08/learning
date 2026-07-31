---
card: data-structures
gi: 41
slug: pattern-matching-naive-kmp-rabin-karp-overview
title: Pattern matching (naive, KMP, Rabin-Karp overview)
---

## 1. What it is

**String pattern matching** finds every position where a shorter pattern string occurs inside a longer text string. There are three well-known approaches, each with a different tradeoff: the **naive** approach checks every possible starting position directly; **KMP** (Knuth-Morris-Pratt) uses a precomputed table to skip re-checking characters it already knows will match; **Rabin-Karp** uses a rolling hash to compare candidate positions in O(1) per position, only falling back to a full character check when hashes match.

## 2. Why & when

The naive approach is simple and fine for short texts or patterns. KMP guarantees worst-case O(n + m) time, making it the right choice when the text can be adversarial (many near-matches, like searching for `"aaaaab"` inside a long run of `"aaaa...a"`). Rabin-Karp shines when you need to search for *many* patterns at once, or check for the presence of any of several patterns, because its hash-based comparison generalizes well.

## 3. Core concept

**Naive: check every start position fully — O(n·m) worst case.** At each of the `n - m + 1` possible starting positions in the text (length `n`), compare up to `m` characters against the pattern. If a mismatch occurs, move to the next starting position and start the character comparison over from scratch — no memory of prior work is kept.

**KMP: never re-check characters the pattern has already matched.** KMP precomputes a "failure table" (also called the longest-prefix-suffix table) for the pattern itself, in O(m). This table tells the algorithm, on a mismatch, exactly how far it can safely shift the pattern without missing a possible match — using the fact that the pattern's own internal structure (a prefix that's also a suffix) rules out redundant re-checks. This guarantees O(n + m) total time, with the text pointer never moving backward.

**Rabin-Karp: compare hashes first, characters only on a hash match.** Compute a hash of the pattern once, and a **rolling hash** of each `m`-length window of the text — updating it in O(1) as the window slides one position, by removing the outgoing character's contribution and adding the incoming character's. If a window's hash matches the pattern's hash, verify with a full character comparison (hash collisions are possible, so this check is required) — average case O(n + m), though a poor hash function can degrade to O(n·m) worst case.

**Complexity summary.** Naive: O(n·m) worst case, O(1) extra space. KMP: O(n + m) worst case, O(m) extra space for the failure table. Rabin-Karp: O(n + m) average case, O(1) extra space (beyond the rolling hash value itself), but O(n·m) worst case on adversarial input or hash collisions.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Naive matching restarting from scratch on every mismatch, versus KMP using a failure table to skip already-matched characters">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">naive: mismatch -&gt; restart comparison from scratch</text>
    <text x="160" y="40" fill="#e6edf3" text-anchor="middle">text:    a a a a b</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">pattern: a a b</text>
    <text x="160" y="80" fill="#f0883e" text-anchor="middle">mismatch at position 2 -&gt; naive restarts pattern at text position 1</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">KMP: use failure table to skip re-checking</text>
    <text x="480" y="40" fill="#e6edf3" text-anchor="middle">text:    a a a a b</text>
    <text x="480" y="60" fill="#e6edf3" text-anchor="middle">pattern:   a a b</text>
    <text x="480" y="80" fill="#3fb950" text-anchor="middle">table says: keep the matched "a" prefix, shift smartly, no re-check</text>
    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">KMP never moves the text pointer backward -- guaranteed O(n+m)</text>
  </g>
</svg>

Naive matching throws away all progress on a mismatch. KMP's failure table preserves useful information about the pattern's own structure to avoid redundant comparisons.

## 5. Runnable example

```java
// PatternMatchingOverview.java
import java.util.ArrayList;
import java.util.List;

public class PatternMatchingOverview {

    // Basic: naive pattern matching -- check every starting position fully.
    static List<Integer> naiveSearch(String text, String pattern) {
        List<Integer> matches = new ArrayList<>();
        int n = text.length(), m = pattern.length();
        for (int i = 0; i <= n - m; i++) {
            int j = 0;
            while (j < m && text.charAt(i + j) == pattern.charAt(j)) j++;
            if (j == m) matches.add(i); // matched all m characters
        }
        return matches;
    }

    static void basicLevel() {
        System.out.println("basic: naive matches -> " + naiveSearch("abababab", "aba"));
    }

    // Intermediate: KMP -- build the failure table, then scan the text without ever backtracking it.
    static int[] buildFailureTable(String pattern) {
        int m = pattern.length();
        int[] table = new int[m];
        int len = 0; // length of the current matching prefix/suffix
        for (int i = 1; i < m; i++) {
            while (len > 0 && pattern.charAt(i) != pattern.charAt(len)) {
                len = table[len - 1]; // fall back using the table itself
            }
            if (pattern.charAt(i) == pattern.charAt(len)) len++;
            table[i] = len;
        }
        return table;
    }

    static List<Integer> kmpSearch(String text, String pattern) {
        List<Integer> matches = new ArrayList<>();
        int[] table = buildFailureTable(pattern);
        int n = text.length(), m = pattern.length();
        int j = 0; // characters of the pattern matched so far
        for (int i = 0; i < n; i++) {
            while (j > 0 && text.charAt(i) != pattern.charAt(j)) {
                j = table[j - 1]; // use the table instead of restarting from i's neighbor
            }
            if (text.charAt(i) == pattern.charAt(j)) j++;
            if (j == m) {
                matches.add(i - m + 1);
                j = table[j - 1];
            }
        }
        return matches;
    }

    static void intermediateLevel() {
        System.out.println("intermediate: KMP matches -> " + kmpSearch("abababab", "aba"));
    }

    // Advanced: Rabin-Karp -- rolling hash to compare windows in O(1), verify only on a hash match.
    static List<Integer> rabinKarpSearch(String text, String pattern) {
        List<Integer> matches = new ArrayList<>();
        int n = text.length(), m = pattern.length();
        if (m > n) return matches;
        long base = 256, mod = 1_000_000_007L;

        long patternHash = 0, windowHash = 0, highOrder = 1;
        for (int i = 0; i < m - 1; i++) highOrder = (highOrder * base) % mod; // base^(m-1) mod, for removing the leading char later

        for (int i = 0; i < m; i++) {
            patternHash = (patternHash * base + pattern.charAt(i)) % mod;
            windowHash = (windowHash * base + text.charAt(i)) % mod;
        }

        for (int i = 0; i <= n - m; i++) {
            if (windowHash == patternHash && text.substring(i, i + m).equals(pattern)) {
                matches.add(i); // verify on hash match, since collisions are possible
            }
            if (i < n - m) {
                windowHash = ((windowHash - text.charAt(i) * highOrder % mod + mod) * base + text.charAt(i + m)) % mod;
            }
        }
        return matches;
    }

    static void advancedLevel() {
        System.out.println("advanced: Rabin-Karp matches -> " + rabinKarpSearch("abababab", "aba"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PatternMatchingOverview.java`, then run `java PatternMatchingOverview.java`.

## 6. Walkthrough

1. `basicLevel()`'s `naiveSearch` checks each of the 6 possible starting positions in `"abababab"` for the pattern `"aba"`, comparing up to 3 characters each time. It finds matches at indices 0, 2, and 4 — every overlapping occurrence.
2. `intermediateLevel()`'s `buildFailureTable("aba")` computes `[0, 0, 1]`: position 2 (`'a'`) matches the pattern's own first character, so the table records a fallback length of 1, meaning "if a later mismatch happens right after matching this much, you can resume as if 1 character were already matched" instead of restarting from zero.
3. `kmpSearch` scans the text once, using `table` to decide how far to fall back `j` on a mismatch, without ever moving the text pointer `i` backward — this is what guarantees the O(n + m) bound, and it finds the same matches `[0, 2, 4]`.
4. `advancedLevel()`'s `rabinKarpSearch` computes a rolling hash for the pattern and for the first window of the text, then slides the window one character at a time, updating the hash in O(1) by removing the outgoing character's contribution (using the precomputed `highOrder` value) and adding the incoming character.
5. Each time a window's hash equals the pattern's hash, the code does one full string comparison to confirm a true match (guarding against hash collisions) before recording the position — again finding `[0, 2, 4]`.

## 7. Gotchas & takeaways

> Gotcha: Rabin-Karp's speed depends entirely on the hash function spreading values well — a poor hash (or an adversarial input crafted to cause many collisions) degrades it to the same O(n·m) worst case as the naive approach, since every hash match still triggers a full character-by-character verification.

- Naive matching is simple but can be O(n·m) in the worst case, re-checking from scratch after every mismatch.
- KMP guarantees O(n + m) by precomputing a failure table from the pattern's own internal structure, avoiding any backward movement through the text.
- Rabin-Karp uses an O(1)-per-step rolling hash to filter candidate positions cheaply, verifying with a real comparison only when hashes match.
- Related concepts: [Substring, indexOf & searching](0037-substring-indexof-searching.md), [Two-pointer & sliding-window on arrays](0021-two-pointer-sliding-window-on-arrays.md).
