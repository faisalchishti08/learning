---
card: system-design
gi: 160
slug: tokenization-stemming-analyzers
title: Tokenization, stemming & analyzers
---

## 1. What it is

**Tokenization** splits raw text into individual terms (tokens) — usually words, by splitting on whitespace and punctuation. **Stemming** reduces a word to its root form (e.g. "running", "runs", and "ran" might all reduce toward "run"), so a search for one form matches documents containing another. An **analyzer** is the full pipeline that combines tokenization, lowercasing, stemming, and removing common "stop words" (like "the", "a", "is") into one repeatable process, applied consistently both when indexing documents and when parsing search queries.

## 2. Why & when

Without this processing, a search for "running" would only match documents containing the exact literal string "running" — missing documents that say "runs" or "ran", even though a human searcher would consider those the same search intent. An analyzer normalizes both the indexed text and the query text through the same steps, so equivalent words match regardless of their exact grammatical form. Use an analyzer any time you build an [inverted index](0159-inverted-index.md) for full-text search — the analyzer is what decides what actually counts as a "term" in that index.

## 3. Core concept

- **Tokenization:** splitting "The Quick-Brown Fox!" into tokens like `["the", "quick", "brown", "fox"]`, handling punctuation and case.
- **Lowercasing:** normalizing case so "Database" and "database" are treated as the same term.
- **Stop-word removal:** dropping extremely common words ("the", "a", "is") that appear in nearly every document and add little value to a search, reducing index size and query noise.
- **Stemming:** reducing inflected word forms toward a common root, using rule-based suffix stripping (e.g. the classic Porter stemmer removes "-ing", "-ed", "-s" under certain conditions).
- **Same pipeline for indexing and querying:** the exact same analyzer must run over both the document text (at index time) and the query text (at search time) — if they diverge, a perfectly reasonable query will fail to match documents it logically should.

## 4. Diagram

```
   raw text: "The Runners are Running quickly!"
        |
        v
   tokenize (split on whitespace/punctuation)
        |
   ["The", "Runners", "are", "Running", "quickly"]
        |
        v
   lowercase
        |
   ["the", "runners", "are", "running", "quickly"]
        |
        v
   remove stop words ("the", "are")
        |
   ["runners", "running", "quickly"]
        |
        v
   stem each token
        |
   ["runner", "run", "quick"]     <- these are the TERMS that go into the inverted index
```
*Caption: raw text passes through several normalizing steps before becoming the terms an inverted index actually stores and searches on.*

## 5. Runnable example

**Level 1 — Basic.** Tokenize and lowercase raw text.

**Level 2 — Stop-word removal.** Drop common, low-value words from the token stream.

**Level 3 — A simple rule-based stemmer, and running the full analyzer pipeline on both a document and a query.** Show that a document and a differently-worded query reduce to matching terms.

```java
// AnalyzerDemo.java
import java.util.*;
import java.util.stream.*;

public class AnalyzerDemo {

    static final Set<String> STOP_WORDS = Set.of("the", "a", "an", "is", "are", "in", "on", "at");

    // Level 1: split on anything that isn't a letter or digit, then lowercase.
    static List<String> tokenize(String text) {
        return Arrays.stream(text.toLowerCase().split("[^a-z0-9]+"))
                     .filter(t -> !t.isEmpty())
                     .collect(Collectors.toList());
    }

    // Level 2: drop stop words from the token stream.
    static List<String> removeStopWords(List<String> tokens) {
        return tokens.stream().filter(t -> !STOP_WORDS.contains(t)).collect(Collectors.toList());
    }

    // Level 3: a minimal rule-based stemmer - strips common suffixes in a fixed priority order.
    static String stem(String token) {
        if (token.endsWith("ies") && token.length() > 4) return token.substring(0, token.length() - 3) + "y";
        if (token.endsWith("ing") && token.length() > 5) return token.substring(0, token.length() - 3);
        if (token.endsWith("ed") && token.length() > 4) return token.substring(0, token.length() - 2);
        if (token.endsWith("es") && token.length() > 4) return token.substring(0, token.length() - 2);
        if (token.endsWith("s") && token.length() > 3) return token.substring(0, token.length() - 1);
        return token;
    }

    // The full analyzer pipeline: tokenize -> remove stop words -> stem.
    static List<String> analyze(String text) {
        return removeStopWords(tokenize(text)).stream().map(AnalyzerDemo::stem).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        String document = "The Runners are Running quickly through the parks";
        String query = "runner runs quick park";

        List<String> documentTerms = analyze(document);
        List<String> queryTerms = analyze(query);

        System.out.println("document terms: " + documentTerms);
        System.out.println("query terms:    " + queryTerms);

        Set<String> matchingTerms = new TreeSet<>(documentTerms);
        matchingTerms.retainAll(queryTerms);
        System.out.println("matching terms between document and query: " + matchingTerms);
    }
}
```

**How to run:** save as `AnalyzerDemo.java`, then run `java AnalyzerDemo.java`.

## 6. Walkthrough

1. `analyze(document)` first calls `tokenize`, which lowercases the text and splits on non-alphanumeric characters, producing `["the", "runners", "are", "running", "quickly", "through", "the", "parks"]`.
2. `removeStopWords` filters out `"the"` (twice) and `"are"`, leaving `["runners", "running", "quickly", "through", "parks"]`.
3. Each remaining token passes through `stem`: `"runners"` ends in `"s"` and is long enough, becoming `"runner"`; `"running"` ends in `"ing"`, becoming `"run"`; `"quickly"` matches none of the suffix rules and is returned unchanged; `"through"` is unchanged; `"parks"` ends in `"s"`, becoming `"park"`.
4. The same pipeline runs on the `query` string "runner runs quick park": tokenizing and stop-word removal leave all four words untouched (none are stop words), and stemming reduces `"runs"` (ends in `"s"`) to `"run"`, while `"runner"`, `"quick"`, and `"park"` pass through unchanged since none match a suffix rule.
5. The final intersection, `matchingTerms`, finds `"run"` and `"park"` present in both the document's stemmed terms and the query's stemmed terms — even though the original raw text used completely different grammatical forms ("Running" vs. "runs", "parks" vs. "park"), the shared analyzer pipeline normalized both sides down to the same matching terms.

## 7. Gotchas & takeaways

> Gotcha: over-aggressive stemming can merge words that are actually different in meaning (e.g. a naive stemmer might reduce both "universal" and "university" toward "univers"), causing unrelated documents to match a query — always test a stemmer against real vocabulary from your domain, and consider a lighter-touch approach (or no stemming) when precision matters more than broad recall.

- An analyzer is a pipeline (tokenize, lowercase, remove stop words, stem), not a single step — and every step changes what actually counts as a "term."
- The exact same analyzer must run over both indexed documents and incoming queries, or otherwise-matching content will silently fail to match.
- Stemming trades precision for recall: it helps different word forms match, but risks conflating genuinely different words that happen to share a suffix.
- Related concepts: [Inverted index](0159-inverted-index.md) (the structure these normalized terms are stored in), [Fuzzy search & typo tolerance](0162-fuzzy-search-typo-tolerance.md) (handling misspellings an analyzer alone cannot fix), [Relevance ranking (TF-IDF / BM25)](0161-relevance-ranking-tf-idf-bm25.md) (scoring matches found via these normalized terms).
