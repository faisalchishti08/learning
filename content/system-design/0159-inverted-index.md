---
card: system-design
gi: 159
slug: inverted-index
title: Inverted index
---

## 1. What it is

An **inverted index** maps each unique word (term) to the list of documents that contain it, instead of mapping each document to the words it contains (a "forward" index). This is the data structure that makes full-text search fast: to find every document containing "database", you look up "database" directly in the index and get back a ready-made list of matching document IDs, instead of scanning every document's text one by one.

## 2. Why & when

Searching by scanning every document's full text for a query word is a linear scan — it gets slower as the collection grows, and becomes impossibly slow at web scale. An inverted index flips the problem: build the term-to-documents mapping once, up front, and every future search becomes one fast lookup instead of a full scan. Use an inverted index for any full-text search feature — searching articles, product catalogs, log messages, or any dataset where users search by keyword rather than by exact ID or a structured filter.

## 3. Core concept

- **Postings list:** the list of document IDs (and often additional info, like term position or frequency) stored against each term — this is the "list of documents containing this word."
- **Building the index:** for each document, split its text into terms (see [tokenization](0160-tokenization-stemming-analyzers.md)), then for each term, add the document's ID to that term's postings list.
- **Query as a lookup, not a scan:** a single-word query is one hash-map (or B-tree) lookup, returning its postings list directly.
- **Multi-word queries via intersection:** an "AND" query for two words looks up both terms' postings lists, then intersects them — a document must appear in *both* lists to match.
- **Index size vs. document collection size:** the index itself takes real storage, roughly proportional to the number of unique (term, document) pairs, but it is looked up, not scanned, which is what makes it fast regardless of how many documents exist.

## 4. Diagram

```
   forward index (document -> words):          inverted index (word -> documents):
   doc1: "the cat sat"                          "the"  -> [doc1, doc2]
   doc2: "the dog ran"                          "cat"  -> [doc1]
   doc3: "cats and dogs"                        "sat"  -> [doc1]
                                                 "dog"  -> [doc2]
                                                 "ran"  -> [doc2]
                                                 "cats" -> [doc3]
                                                 "dogs" -> [doc3]

   query "dog" -> lookup postings["dog"] -> [doc2]   (one lookup, not a scan of doc1/doc2/doc3)
```
*Caption: the index is built once by flipping document-to-words into word-to-documents; every future search is a direct lookup on this flipped structure.*

## 5. Runnable example

**Level 1 — Basic.** Build an inverted index from a small set of documents.

**Level 2 — Single-word query.** Look up a term directly, instead of scanning every document.

**Level 3 — Multi-word "AND" query via postings-list intersection.** Find documents containing every given word.

```java
// InvertedIndexDemo.java
import java.util.*;

public class InvertedIndexDemo {

    // Level 1: term -> sorted set of document IDs containing that term.
    static Map<String, TreeSet<Integer>> index = new HashMap<>();

    static void addDocument(int docId, String text) {
        String[] terms = text.toLowerCase().split("\\s+");
        for (String term : terms) {
            index.computeIfAbsent(term, t -> new TreeSet<>()).add(docId);
        }
    }

    // Level 2: a single-term query is one direct lookup.
    static Set<Integer> query(String term) {
        return index.getOrDefault(term.toLowerCase(), new TreeSet<>());
    }

    // Level 3: an "AND" query - intersect the postings lists of every given term.
    static Set<Integer> queryAnd(String... terms) {
        Set<Integer> result = null;
        for (String term : terms) {
            Set<Integer> postings = query(term);
            if (result == null) {
                result = new TreeSet<>(postings);
            } else {
                result.retainAll(postings); // intersection: keep only documents present in BOTH lists
            }
        }
        return result == null ? Set.of() : result;
    }

    public static void main(String[] args) {
        addDocument(1, "the cat sat on the mat");
        addDocument(2, "the dog ran in the park");
        addDocument(3, "cats and dogs are friends");

        System.out.println("index built. postings for \"the\": " + query("the"));
        System.out.println("postings for \"dog\": " + query("dog"));
        System.out.println("postings for \"cats\": " + query("cats"));

        System.out.println("AND query [\"the\", \"cat\"]: " + queryAnd("the", "cat"));
        System.out.println("AND query [\"the\", \"dog\"]: " + queryAnd("the", "dog"));
        System.out.println("AND query [\"cat\", \"dog\"]: " + queryAnd("cat", "dog"));
    }
}
```

**How to run:** save as `InvertedIndexDemo.java`, then run `java InvertedIndexDemo.java`.

## 6. Walkthrough

1. Each call to `addDocument` splits the document's text into lowercase words and, for every word, adds the document's ID into that word's `TreeSet<Integer>` inside `index` — after all three calls, `index.get("the")` holds `{1, 2}`, since only doc1 and doc2 contain "the".
2. `query("the")` performs `index.getOrDefault("the", ...)`, a single direct map lookup, returning `{1, 2}` without inspecting doc3's text at all.
3. `query("dog")` similarly returns `{2}` directly, and `query("cats")` returns `{3}` — each is one lookup, regardless of how many total documents exist in the index.
4. `queryAnd("the", "cat")` looks up postings for `"the"` (`{1, 2}`) and `"cat"` (`{1}`); the second iteration calls `result.retainAll(postings)`, keeping only IDs present in both sets, leaving `{1}` — the one document containing both words.
5. `queryAnd("cat", "dog")` intersects `{1}` and `{2}`, which share no common element, so `retainAll` empties the set, correctly returning `{}` since no single document contains both "cat" and "dog".

## 7. Gotchas & takeaways

> Gotcha: this simple index ignores word order and position entirely — it can answer "does this document contain both words" but not "does it contain them as an exact phrase, next to each other." Real search engines store each term's position within the document in its postings entry specifically to support phrase queries; a plain term-to-documents index alone cannot distinguish "the cat sat" from "sat the cat" appearing in different documents.

- An inverted index turns full-text search from a linear scan into a direct lookup, by flipping the natural document-to-words mapping around.
- Multi-word "AND" queries are answered by intersecting each word's postings list, not by re-scanning documents.
- This basic version has no notion of word order, relevance, or ranking — those are added by [tokenization/analyzers](0160-tokenization-stemming-analyzers.md) and [relevance ranking](0161-relevance-ranking-tf-idf-bm25.md) on top.
- Related concepts: [Relevance ranking (TF-IDF / BM25)](0161-relevance-ranking-tf-idf-bm25.md) (ranking the documents this index returns), [Elasticsearch cluster basics (shards & replicas)](0165-elasticsearch-cluster-basics-shards-replicas.md) (how a real search engine scales this index across many machines), [Autocomplete / typeahead](0163-autocomplete-typeahead.md) (a related but distinct indexing structure for prefix search).
