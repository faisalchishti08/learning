---
card: system-design
gi: 162
slug: fuzzy-search-typo-tolerance
title: Fuzzy search & typo tolerance
---

## 1. What it is

**Fuzzy search** finds matches for a query even when it does not exactly match any indexed term, typically by measuring **edit distance** (also called Levenshtein distance) — the minimum number of single-character insertions, deletions, or substitutions needed to turn one string into another. If a user types "recieve" instead of "receive," fuzzy search still finds documents containing "receive," because the edit distance between the two words is small (a typo tolerance, usually 1 or 2 edits).

## 2. Why & when

An exact-match [inverted index](0159-inverted-index.md) lookup for "recieve" simply fails to find anything, because no document literally contains that misspelled string — even though the user's intent is completely clear to a human reader. Fuzzy search closes this gap by tolerating a small number of character-level differences between the query and indexed terms. Use it for any user-facing search box, since typos are common and a search that fails outright on a typo feels broken, especially compared to competitors that handle it gracefully.

## 3. Core concept

- **Edit distance (Levenshtein distance):** the minimum number of single-character insert/delete/substitute operations to transform one string into another — "kitten" to "sitting" has an edit distance of 3.
- **Typo tolerance threshold:** a maximum allowed edit distance (commonly 1 or 2) for a term to be considered a fuzzy match — larger thresholds catch more typos but also risk matching genuinely unrelated words.
- **Computing edit distance efficiently:** the classic algorithm builds a 2D dynamic-programming table, where each cell represents the edit distance between prefixes of the two strings, built up from smaller subproblems.
- **Scaling fuzzy search:** computing edit distance against every single term in a large index is too slow; real search engines use specialized structures (like a BK-tree, or Lucene/Elasticsearch's finite-state-transducer-based fuzzy query) to narrow down candidates quickly before computing exact edit distances on just those.
- **Fuzzy matching is a filter, not a ranking:** it decides *which* terms count as close enough to match; [relevance ranking](0161-relevance-ranking-tf-idf-bm25.md) still decides in what order the resulting documents are shown.

## 4. Diagram

```
   query: "recieve"                     index terms: ["receive", "received", "deceive", "relieve"]

   edit distance("recieve", "receive")  = 2   (swap "ie" -> "ei": 2 substitutions)
   edit distance("recieve", "received") = 4
   edit distance("recieve", "deceive")  = 2
   edit distance("recieve", "relieve")  = 3

   threshold = 2  -> matches: ["receive", "deceive"]
                     ("received" and "relieve" are too far away)
```
*Caption: only terms within the allowed edit-distance threshold count as fuzzy matches for the misspelled query.*

## 5. Runnable example

**Level 1 — Basic.** Compute edit distance between two strings using dynamic programming.

**Level 2 — Apply a typo-tolerance threshold.** Decide whether two strings are "close enough" to count as a match.

**Level 3 — Fuzzy search over a small index.** Find every indexed term within the threshold of a misspelled query, and use those to look up matching documents.

```java
// FuzzySearchDemo.java
import java.util.*;

public class FuzzySearchDemo {

    // Level 1: classic dynamic-programming edit distance (Levenshtein distance).
    static int editDistance(String a, String b) {
        int[][] dp = new int[a.length() + 1][b.length() + 1];
        for (int i = 0; i <= a.length(); i++) dp[i][0] = i;       // deleting all of a's first i chars
        for (int j = 0; j <= b.length(); j++) dp[0][j] = j;       // inserting all of b's first j chars
        for (int i = 1; i <= a.length(); i++) {
            for (int j = 1; j <= b.length(); j++) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1]; // characters match, no edit needed here
                } else {
                    dp[i][j] = 1 + Math.min(dp[i - 1][j - 1],      // substitute
                                    Math.min(dp[i - 1][j],          // delete from a
                                             dp[i][j - 1]));        // insert into a
                }
            }
        }
        return dp[a.length()][b.length()];
    }

    // Level 2: is this term within the allowed typo-tolerance threshold?
    static boolean isFuzzyMatch(String query, String term, int threshold) {
        return editDistance(query, term) <= threshold;
    }

    // Level 3: a tiny inverted index, plus fuzzy lookup instead of exact lookup.
    static Map<String, List<Integer>> index = Map.of(
        "receive", List.of(1, 2),
        "received", List.of(3),
        "deceive", List.of(4),
        "relieve", List.of(5)
    );

    static Set<Integer> fuzzySearch(String query, int threshold) {
        Set<Integer> results = new TreeSet<>();
        for (Map.Entry<String, List<Integer>> entry : index.entrySet()) {
            int distance = editDistance(query, entry.getKey());
            if (distance <= threshold) {
                System.out.println("  matched term \"" + entry.getKey() + "\" (edit distance " + distance + ")");
                results.addAll(entry.getValue());
            }
        }
        return results;
    }

    public static void main(String[] args) {
        System.out.println("editDistance(kitten, sitting) = " + editDistance("kitten", "sitting"));
        System.out.println("isFuzzyMatch(recieve, receive, threshold=2) = " + isFuzzyMatch("recieve", "receive", 2));
        System.out.println("isFuzzyMatch(recieve, received, threshold=2) = " + isFuzzyMatch("recieve", "received", 2));

        System.out.println("fuzzy searching for \"recieve\" (threshold=2):");
        Set<Integer> matchingDocs = fuzzySearch("recieve", 2);
        System.out.println("documents found: " + matchingDocs);
    }
}
```

**How to run:** save as `FuzzySearchDemo.java`, then run `java FuzzySearchDemo.java`.

## 6. Walkthrough

1. `editDistance("kitten", "sitting")` builds a table where `dp[i][j]` holds the edit distance between the first `i` characters of "kitten" and the first `j` characters of "sitting"; the final cell, `dp[6][7]`, comes out to 3, matching the well-known example.
2. `isFuzzyMatch("recieve", "receive", 2)` computes `editDistance` between the two, which is 2 (the "ie"/"ei" swap costs two substitutions), and since `2 <= 2`, the method returns `true`.
3. `isFuzzyMatch("recieve", "received", 2)` computes a larger edit distance (4, from the extra characters), and since `4 <= 2` is false, it returns `false` — "received" is too different to count as a typo of "recieve" under this threshold.
4. `fuzzySearch("recieve", 2)` iterates every term in the small `index`, computing `editDistance` against each; `"receive"` (distance 2) and `"deceive"` (distance 2) both pass the `<= 2` check and get printed as matches, while `"received"` (distance 4) and `"relieve"` (distance 3) are silently skipped.
5. The method accumulates the document IDs from every matching term's postings list into one `TreeSet`, so the final `matchingDocs` combines documents 1 and 2 (from "receive") with document 4 (from "deceive") — a query that would have returned zero results under exact matching now correctly surfaces three relevant documents.

## 7. Gotchas & takeaways

> Gotcha: computing edit distance against every single term in a large real-world index, as this demo's `fuzzySearch` does, does not scale — with millions of indexed terms, that is millions of dynamic-programming computations per query. Real search engines pre-filter candidate terms using a specialized structure (an n-gram index or a finite-state transducer) before ever computing exact edit distance, and this optimization is essential, not optional, at scale.

- Fuzzy search tolerates small character-level differences between a query and indexed terms, closing the gap exact matching leaves for typos.
- Edit distance (Levenshtein distance) is the standard measure of "how different" two strings are, computed efficiently via dynamic programming.
- The typo-tolerance threshold is a real tuning knob: too tight misses real typos, too loose starts matching unrelated words.
- Related concepts: [Inverted index](0159-inverted-index.md) (fuzzy matching still needs to find candidate documents afterward), [Autocomplete / typeahead](0163-autocomplete-typeahead.md) (a related but distinct prefix-matching problem), [Relevance ranking (TF-IDF / BM25)](0161-relevance-ranking-tf-idf-bm25.md) (still needed to order the fuzzy matches found).
