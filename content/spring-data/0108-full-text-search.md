---
card: spring-data
gi: 108
slug: full-text-search
title: "Full-text search"
---

## 1. What it is

MongoDB's text index (`@TextIndexed`) enables relevance-ranked, multi-word search across one or more string fields — fundamentally different from the `$regex` pattern-matching covered in the derived-and-JSON-queries card, since a text index tokenizes text into words, ignores common "stop words," supports stemming (matching "running" when searching for "run"), and scores results by relevance rather than just returning a yes/no match.

```java
@Document("orders")
class Order {
    @TextIndexed String notes; // included in the collection's text index
}

interface OrderRepository extends MongoRepository<Order, String> {
    @Query("{ $text: { $search: ?0 } }")
    List<Order> searchNotes(String searchTerm);
}
```

## 2. Why & when

The derived-and-JSON-queries card's `$regex` condition matches literal patterns — useful, but it has no concept of "relevance," doesn't handle word variations, and doesn't ignore filler words like "the" or "and." Full-text search is for genuine search-box functionality: multi-word queries where the best-matching documents should rank first, not just any document containing a literal substring.

Reach for full-text search specifically when:

- Building actual search functionality (a search box, "find related notes/comments/descriptions") where users type multiple words and expect relevance-ranked results, not exact substring matches.
- `$regex` searches are proving too literal — missing plural/singular variations, or false-positive-prone since regex has no concept of "these are the same word, just conjugated differently."
- You need results ordered by how well they match the search terms — `$text` queries can be sorted by MongoDB's computed relevance score (`textScore`), something `$regex` has no equivalent for.

## 3. Core concept

```
 @TextIndexed String notes;   -- builds a text index: tokenizes, removes stop words, stems

 $regex search for "run":           $text search for "run":
   matches ONLY literal "run"          matches "run", "running", "ran" (stemmed)
   no relevance ranking                 results can be ORDERED by relevance score
   no stop-word handling                 ignores "the"/"and"/"a" automatically in the query
```

A text index understands language structure (stemming, stop words) and computes relevance; a regex only ever checks for a literal pattern match.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A text index tokenizes and stems words, then scores documents by relevance, while regex only matches literal patterns">
  <rect x="20" y="20" width="270" height="100" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">$regex "run"</text>
  <text x="35" y="65" fill="#8b949e" font-size="8.5" font-family="sans-serif">matches ONLY literal "run"</text>
  <text x="35" y="83" fill="#8b949e" font-size="8.5" font-family="sans-serif">no relevance score</text>
  <text x="35" y="101" fill="#8b949e" font-size="8.5" font-family="sans-serif">no stemming, no stop words</text>

  <rect x="350" y="20" width="270" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">$text "run"</text>
  <text x="365" y="65" fill="#8b949e" font-size="8.5" font-family="sans-serif">matches run/running/ran (stemmed)</text>
  <text x="365" y="83" fill="#8b949e" font-size="8.5" font-family="sans-serif">results scored by relevance</text>
  <text x="365" y="101" fill="#8b949e" font-size="8.5" font-family="sans-serif">ignores stop words automatically</text>
</svg>

The same search term produces a narrow, literal match under `$regex`, versus a broader, relevance-ranked match under `$text`.

## 5. Runnable example

The scenario: searching order notes for keywords, evolving from a naive substring search (mirroring `$regex`'s limitations), to a simplified `$text`-style search with basic stemming, to relevance-scored, ranked results.

### Level 1 — Basic

Model the `$regex` limitation directly: a literal substring search misses word variations entirely.

```java
import java.util.*;
import java.util.stream.*;

class Order { String id; String notes; Order(String id, String notes) { this.id = id; this.notes = notes; } }

public class FullTextLevel1 {
    // Simulates $regex: literal substring matching only.
    static List<Order> regexSearch(List<Order> orders, String literalTerm) {
        return orders.stream().filter(o -> o.notes.toLowerCase().contains(literalTerm.toLowerCase()))
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "Customer is running late, please expedite"),
            new Order("2", "Ran out of stock, backordered"),
            new Order("3", "Standard delivery, no rush")
        );

        List<Order> results = regexSearch(orders, "run");
        System.out.println("$regex 'run' matches: " + results.size() + " order(s) (misses 'Ran' entirely!)");
    }
}
```

How to run: `java FullTextLevel1.java`

`regexSearch` finds order 1 ("running" contains the literal substring "run") but misses order 2 entirely ("Ran" is a different word, not a substring match for "run") — this is the core limitation `$regex` has: no understanding that "run," "running," and "ran" are related forms of the same word.

### Level 2 — Intermediate

Model a simplified stemming-aware search, standing in for `$text`'s word-form matching — reducing words to a common root before comparing.

```java
import java.util.*;
import java.util.stream.*;

class Order { String id; String notes; Order(String id, String notes) { this.id = id; this.notes = notes; } }

public class FullTextLevel2 {
    // Drastically simplified "stemming": strips common suffixes to approximate a word's root form.
    static String stem(String word) {
        String w = word.toLowerCase();
        if (w.endsWith("ning")) return w.substring(0, w.length() - 4); // "running" -> "run"
        if (w.endsWith("ed")) return w.substring(0, w.length() - 2);    // "backordered" -> "backorder"
        return w;
    }

    static boolean containsStemmedMatch(String text, String searchTerm) {
        String searchStem = stem(searchTerm);
        return Arrays.stream(text.split("\\s+")).map(FullTextLevel2::stem).anyMatch(w -> w.equals(searchStem));
    }

    // Simulates: @Query("{ $text: { $search: ?0 } }")
    static List<Order> textSearch(List<Order> orders, String searchTerm) {
        return orders.stream().filter(o -> containsStemmedMatch(o.notes, searchTerm)).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "Customer is running late, please expedite"),
            new Order("2", "Ran out of stock, backordered"),
            new Order("3", "Standard delivery, no rush")
        );

        List<Order> results = textSearch(orders, "running");
        System.out.println("$text 'running' matches: " + results.stream().map(o -> o.id).toList());
    }
}
```

How to run: `java FullTextLevel2.java`

`stem("running")` reduces to `"run"`, and order 1's word "running" also stems to `"run"` — a direct match. This simplified stemmer doesn't correctly handle "Ran" (irregular verb forms are genuinely hard to stem without a real linguistic model), but it demonstrates the core idea: `$text` search compares word *roots*, not literal strings, catching variations `$regex` would miss.

### Level 3 — Advanced

Add relevance scoring: count how many of the search term's words appear in each document, and sort results by that score descending — standing in for MongoDB's `textScore` and `$meta: "textScore"` sort.

```java
import java.util.*;
import java.util.stream.*;

class Order { String id; String notes; Order(String id, String notes) { this.id = id; this.notes = notes; } }
record ScoredResult(Order order, int relevanceScore) {}

public class FullTextLevel3 {
    static String stem(String word) {
        String w = word.toLowerCase().replaceAll("[^a-z]", "");
        if (w.endsWith("ning")) return w.substring(0, w.length() - 4);
        if (w.endsWith("ed")) return w.substring(0, w.length() - 2);
        return w;
    }

    // Counts how many distinct search-term words appear (in stemmed form) in the document -- a simplified relevance score.
    static int relevanceScore(String text, List<String> searchWords) {
        Set<String> documentStems = Arrays.stream(text.split("\\s+")).map(FullTextLevel3::stem).collect(Collectors.toSet());
        Set<String> searchStems = searchWords.stream().map(FullTextLevel3::stem).collect(Collectors.toSet());
        documentStems.retainAll(searchStems); // intersection: words present in BOTH
        return documentStems.size();
    }

    // Simulates: @Query("{ $text: { $search: ?0 } }") with a sort by { score: { $meta: "textScore" } }
    static List<ScoredResult> textSearchRanked(List<Order> orders, String searchPhrase) {
        List<String> searchWords = Arrays.asList(searchPhrase.split("\\s+"));
        return orders.stream()
            .map(o -> new ScoredResult(o, relevanceScore(o.notes, searchWords)))
            .filter(r -> r.relevanceScore() > 0) // only documents matching at least one search word
            .sorted(Comparator.comparingInt(ScoredResult::relevanceScore).reversed()) // highest relevance first
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "Customer is running late, expedite urgent delivery"),
            new Order("2", "Urgent backordered item, expedite processing"),
            new Order("3", "Standard delivery, no rush at all")
        );

        List<ScoredResult> results = textSearchRanked(orders, "urgent expedite");
        for (ScoredResult r : results) System.out.println("Order " + r.order().id + ": score=" + r.relevanceScore());
    }
}
```

How to run: `java FullTextLevel3.java`

Order 2 matches both search words ("urgent" and "expedite"), scoring `2`; order 1 also matches both, scoring `2` as well; order 3 matches neither and is excluded entirely (`relevanceScore() > 0` filters it out). Both matching orders tie at score `2` in this simplified model — real MongoDB relevance scoring also weighs term frequency and field length, producing finer-grained ranking than this simplified word-count approach.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, three orders are built with varying notes text, and `textSearchRanked(orders, "urgent expedite")` is called, splitting the search phrase into `["urgent", "expedite"]`.

For order 1 ("Customer is running late, expedite urgent delivery"), `relevanceScore` splits the notes into words, stems each one, and computes the intersection with the stemmed search words: `"expedite"` and `"urgent"` both appear directly in the text (case-insensitively, after basic stemming), so the intersection size is `2`.

For order 2 ("Urgent backordered item, expedite processing"), the same computation finds both `"urgent"` and `"expedite"` present, also scoring `2`.

For order 3 ("Standard delivery, no rush at all"), neither search word appears anywhere in the notes, so the intersection is empty — `relevanceScore` returns `0`, and the `.filter(r -> r.relevanceScore() > 0)` step excludes it from the results entirely.

The remaining two results (orders 1 and 2, both scoring `2`) are sorted descending by score — since they're tied, their relative order depends on the stream's stability, but both appear in the final printed output with their score of `2`, while order 3 never appears at all.

```
textSearchRanked(["urgent", "expedite"]):
  order1: contains "expedite","urgent" -> score=2 -> INCLUDED
  order2: contains "urgent","expedite" -> score=2 -> INCLUDED
  order3: contains neither              -> score=0 -> EXCLUDED (filtered out)
  result (sorted desc by score): [order1(2), order2(2)] (or order2, order1 -- tied)
```

In a real Spring Data MongoDB application, `@Query("{ $text: { $search: ?0 } }")` combined with a `@TextIndexed` field triggers MongoDB's actual text-search engine: tokenization, stop-word removal, proper linguistic stemming (handling irregular forms correctly, unlike this example's simplified suffix-stripping), and a genuine TF-IDF-style relevance score computed server-side. Sorting by `Sort.by(Sort.Direction.DESC, "score").and(TextCriteria...)` (or the equivalent `$meta: "textScore"` projection) returns documents ordered by how well they actually match the search phrase — far more sophisticated than this example's word-intersection-count approximation, but built on the exact same underlying idea: match on word meaning, not literal substrings, and rank by relevance.

## 7. Gotchas & takeaways

> Gotcha: a MongoDB collection can have only **one** text index (covering one or more fields together), unlike regular indexes where you can have as many as you want — designing which fields belong in the text index (and in what combination) is a one-time decision that's more constrained than ordinary indexing.

- Full-text search (`@TextIndexed` + `$text`) understands word structure — stemming, stop words — and computes relevance scores, fundamentally different from `$regex`'s literal pattern matching.
- Reach for full-text search when building genuine search-box functionality where users expect relevance-ranked, multi-word results, not exact substring matches.
- Results can be sorted by MongoDB's computed relevance score, letting the best-matching documents surface first — something `$regex` conditions have no equivalent for.
- A MongoDB collection supports only one text index total (though it can span multiple fields) — this is a real design constraint to plan around upfront, unlike ordinary secondary indexes.
