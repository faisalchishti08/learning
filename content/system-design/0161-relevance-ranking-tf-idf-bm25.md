---
card: system-design
gi: 161
slug: relevance-ranking-tf-idf-bm25
title: Relevance ranking (TF-IDF / BM25)
---

## 1. What it is

**Relevance ranking** decides the order search results are shown in, scoring each matching document by how well it matches the query, not just whether it matches at all. **TF-IDF** (Term Frequency - Inverse Document Frequency) scores a term higher in a document if it appears often in that document (Term Frequency), but lower overall if it appears in almost every document in the collection (Inverse Document Frequency, which discounts common, low-information words). **BM25** is a more refined, widely-used formula built on the same TF-IDF intuition, adding better handling of document length and diminishing returns for repeated terms.

## 2. Why & when

An [inverted index](0159-inverted-index.md) tells you *which* documents contain a query term, but not *how relevant* each one actually is — a document mentioning "database" once in a long article is a weaker match than one whose entire short title is "Database Design," yet both would appear in the same unordered match set. TF-IDF and BM25 give every matching document a numeric relevance score, letting you sort results best-first. Use this scoring whenever a search feature returns more than a handful of results and users expect the most relevant ones to appear near the top, not in arbitrary or match-count order.

## 3. Core concept

- **Term Frequency (TF):** how often a term appears in a specific document — a document mentioning the query term 5 times is treated as a stronger match than one mentioning it once, though with diminishing returns (the difference between 1 and 2 occurrences matters more than between 20 and 21).
- **Inverse Document Frequency (IDF):** a term appearing in nearly every document (like "the") carries little discriminating power and gets a low weight; a rare term appearing in only a few documents is highly informative when found and gets a high weight. A common formula is `IDF(term) = log(totalDocuments / documentsContainingTerm)`.
- **TF-IDF score:** for a document and a query term, `score = TF * IDF` — combining "how much this document emphasizes the term" with "how rare and informative the term is overall."
- **BM25 improvements over plain TF-IDF:** BM25 caps the benefit of very high term frequency (saturating rather than growing linearly), and normalizes for document length (a term appearing twice in a short document is a stronger signal than twice in a very long one).
- **Multi-term queries:** for a query with several words, the document's total score is the sum of its per-term scores across all query terms, so documents matching more (and rarer) query terms rank higher.

## 4. Diagram

```
   query: "database performance"
   collection: 100 documents, 40 contain "database", 5 contain "performance"

   doc A: "database" appears 3 times, "performance" appears 2 times, short document
   doc B: "database" appears 1 time,  "performance" appears 0 times, long document

   IDF("database")    = log(100/40)  = low  (common term, low information)
   IDF("performance")  = log(100/5)   = high (rare term, high information)

   doc A score = TF(database,A)*IDF(database) + TF(performance,A)*IDF(performance)  <- HIGH (matches rare term too)
   doc B score = TF(database,B)*IDF(database) + 0                                    <- LOWER (misses the rare, informative term)

   ranked results: [doc A, doc B, ...]
```
*Caption: a rare, informative term ("performance") contributes far more to a document's score than a common one ("database"), so documents matching the rarer term rank higher.*

## 5. Runnable example

**Level 1 — Basic.** Compute term frequency per document.

**Level 2 — Add inverse document frequency across the whole collection.** Combine TF and IDF into a full TF-IDF score.

**Level 3 — Rank multiple documents for a multi-term query and sort by total score.** Show a rare, informative term outweighing a common one.

```java
// RelevanceRankingDemo.java
import java.util.*;
import java.util.stream.*;

public class RelevanceRankingDemo {

    static Map<Integer, List<String>> documents = new HashMap<>();

    static void addDocument(int docId, String text) {
        documents.put(docId, Arrays.asList(text.toLowerCase().split("\\s+")));
    }

    // Level 1: how many times does `term` appear in this document's terms?
    static long termFrequency(int docId, String term) {
        return documents.get(docId).stream().filter(t -> t.equals(term)).count();
    }

    // Level 2: how many documents in the WHOLE collection contain this term at least once?
    static long documentFrequency(String term) {
        return documents.values().stream().filter(terms -> terms.contains(term)).count();
    }

    static double inverseDocumentFrequency(String term) {
        long df = documentFrequency(term);
        if (df == 0) return 0;
        return Math.log((double) documents.size() / df);
    }

    static double tfIdf(int docId, String term) {
        return termFrequency(docId, term) * inverseDocumentFrequency(term);
    }

    // Level 3: score a document against ALL query terms, and rank every document by total score.
    static double scoreForQuery(int docId, String[] queryTerms) {
        double total = 0;
        for (String term : queryTerms) total += tfIdf(docId, term);
        return total;
    }

    public static void main(String[] args) {
        addDocument(1, "database performance database database tuning tips");
        addDocument(2, "database backup and database restore guide");
        addDocument(3, "improving performance for high traffic systems");
        addDocument(4, "a general introduction to databases");

        String[] query = {"database", "performance"};
        System.out.println("IDF(database) = " + String.format("%.3f", inverseDocumentFrequency("database")));
        System.out.println("IDF(performance) = " + String.format("%.3f", inverseDocumentFrequency("performance")));

        List<Integer> ranked = documents.keySet().stream()
            .sorted((a, b) -> Double.compare(scoreForQuery(b, query), scoreForQuery(a, query)))
            .collect(Collectors.toList());

        for (int docId : ranked) {
            System.out.println("doc" + docId + ": score = " + String.format("%.3f", scoreForQuery(docId, query)));
        }
    }
}
```

**How to run:** save as `RelevanceRankingDemo.java`, then run `java RelevanceRankingDemo.java`.

## 6. Walkthrough

1. `documentFrequency("database")` finds "database" appears in documents 1, 2, and 4 (`df=3` out of 4 total), giving a relatively low `inverseDocumentFrequency`; `documentFrequency("performance")` finds it only in documents 1 and 3 (`df=2` out of 4), giving a higher IDF since it is rarer.
2. `scoreForQuery(1, query)` sums `tfIdf(1, "database")` (term frequency 3, times the low database IDF) and `tfIdf(1, "performance")` (term frequency 1, times the higher performance IDF) — doc1 benefits from both a high term frequency on the common term and a hit on the rarer, more informative term.
3. `scoreForQuery(2, query)` sums a high term-frequency contribution from "database" (appearing twice) but zero from "performance" (`termFrequency(2, "performance") == 0`), so its total score misses out on the higher-value rare-term contribution entirely.
4. `scoreForQuery(3, query)` gets zero from "database" (never appears) but a solid contribution from "performance" (appears once, weighted by the higher IDF) — showing that matching the rarer term alone can still produce a meaningful score.
5. Sorting all four documents by `scoreForQuery` descending places doc1 first (it matches both terms, including the rare one), followed by a ranking among doc2, doc3, and doc4 driven by how many terms they matched and how rare those terms are — demonstrating that the final order reflects genuine relevance, not simply which documents matched at all.

## 7. Gotchas & takeaways

> Gotcha: plain TF-IDF's term frequency component grows linearly and without limit, so a document that (accidentally or deliberately) repeats a query term hundreds of times can dominate the rankings purely through repetition, regardless of actual relevance — this is exactly the weakness BM25 fixes by making the term-frequency contribution saturate, so past a certain point, more repetitions barely increase the score further.

- TF-IDF (and its refinement, BM25) score how relevant a document is to a query, not merely whether it matches — this ordering is what makes a search feature actually useful at scale.
- Rare, informative terms contribute far more to a document's score than extremely common ones, which is exactly what IDF captures.
- BM25 improves on plain TF-IDF by capping the benefit of term repetition and normalizing for document length, both of which plain TF-IDF handles poorly.
- Related concepts: [Inverted index](0159-inverted-index.md) (the structure that finds the candidate documents these scores rank), [Tokenization, stemming & analyzers](0160-tokenization-stemming-analyzers.md) (determines exactly what a "term" is, before any scoring happens), [Fuzzy search & typo tolerance](0162-fuzzy-search-typo-tolerance.md) (a separate concern: finding near-matches, not ranking exact ones).
