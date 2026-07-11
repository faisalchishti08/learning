---
card: spring-data
gi: 143
slug: highlighting
title: "Highlighting"
---

## 1. What it is

**Highlighting** returns, alongside each search hit, the specific snippet of text where the query matched — with the matching terms wrapped in marker tags (`<em>`, by default) — so a UI can show *why* a document matched, the way a search engine's results page bolds your search terms within each result's preview text.

```java
Query query = Query.of(q -> q.match(m -> m.field("description").query("wireless mouse")))
    .setHighlightQuery(new HighlightQuery(new Highlight(List.of(new HighlightField("description"))), Order.class));

SearchHits<Order> hits = elasticsearchOperations.search(query, Order.class);
for (SearchHit<Order> hit : hits) {
    List<String> snippets = hit.getHighlightField("description"); // e.g. ["<em>Wireless</em> <em>mouse</em>, ergonomic design"]
}
```

## 2. Why & when

A relevance score (from earlier cards) tells you *that* a document matched well, but not *where* or *why* — for a user reading search results, seeing the matched terms highlighted within a preview snippet is what makes results scannable and trustworthy, rather than a bare list of titles the user has to open each one to understand. Highlighting computes this snippet-with-markup server-side, using the same tokenization and matching logic that produced the relevance score in the first place.

Reach for highlighting when:

- Building any user-facing search results page — highlighting matched terms within a snippet is the standard, expected UX for search results.
- You want to show *why* a document matched a fuzzy or relevance-based query, not just that it did — especially useful for full-text searches where the match might not be obvious from the title alone.
- You need a short, relevant excerpt from a long document (an article body, a product description) rather than displaying the entire field's content in a results list.

## 3. Core concept

```
 description = "Wireless mouse, ergonomic design, USB receiver included"
 query: match "wireless mouse"

 WITHOUT highlighting:  hit.getContent().description = "Wireless mouse, ergonomic design, USB receiver included"
                          -- caller has to figure out WHY this matched, and WHERE, on its own

 WITH highlighting:      hit.getHighlightField("description") =
                            ["<em>Wireless</em> <em>mouse</em>, ergonomic design, USB receiver included"]
                          -- the matched terms are marked directly, ready to render
```

The highlighted snippet is computed server-side from the same analysis used for matching, and returned as extra metadata alongside (not instead of) the original document.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A search hit carries both its original document content and a separate highlighted snippet showing where the match occurred">
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="43" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">query: match "wireless mouse" against description field</text>

  <rect x="40" y="80" width="260" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">hit.getContent().description</text>
  <text x="170" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">original, unmodified field value</text>

  <rect x="340" y="80" width="260" height="50" rx="8" fill="#6db33f22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">hit.getHighlightField("description")</text>
  <text x="470" y="115" fill="#3fb950" font-size="7.5" text-anchor="middle" font-family="sans-serif">&lt;em&gt;Wireless&lt;/em&gt; &lt;em&gt;mouse&lt;/em&gt;, ...</text>
</svg>

The highlighted snippet is separate, additional metadata on the search hit — not a replacement for the document's actual stored value.

## 5. Runnable example

The scenario: highlighting matched terms in search results, evolving from a basic single-term highlight, to highlighting multiple query terms within a longer field, to customizing the highlight markup tags — matching `Highlight`'s configurable pre/post tags.

### Level 1 — Basic

Model highlighting a single matched term within a field.

```java
import java.util.*;

public class HighlightingLevel1 {
    public static void main(String[] args) {
        String description = "Wireless mouse, ergonomic design";
        String queryTerm = "mouse";

        String highlighted = highlight(description, List.of(queryTerm), "<em>", "</em>");
        System.out.println("Original:    " + description);
        System.out.println("Highlighted: " + highlighted);
    }

    // Mirrors Elasticsearch's highlighter wrapping each matched term with the configured pre/post tags.
    static String highlight(String text, List<String> terms, String preTag, String postTag) {
        String result = text;
        for (String term : terms) {
            // Case-insensitive match, preserving the ORIGINAL casing of the matched text in the output.
            result = result.replaceAll("(?i)(" + term + ")", preTag + "$1" + postTag);
        }
        return result;
    }
}
```

How to run: `java HighlightingLevel1.java`

`highlight` wraps every case-insensitive occurrence of a query term with `<em>`/`</em>`, mirroring Elasticsearch's default highlighter behavior on a matched field — the original casing (`"mouse"` vs. `"Mouse"`) is preserved inside the markup, since highlighting marks *where* the match occurred without altering the underlying text.

### Level 2 — Intermediate

Highlight **multiple** query terms within a longer field, matching a multi-word `match` query against `description`.

```java
import java.util.*;

public class HighlightingLevel2 {
    public static void main(String[] args) {
        String description = "Wireless mouse, ergonomic design, USB receiver included";
        List<String> queryTerms = List.of("wireless", "mouse", "usb");

        String highlighted = highlight(description, queryTerms, "<em>", "</em>");
        System.out.println("Original:    " + description);
        System.out.println("Highlighted: " + highlighted);
    }

    static String highlight(String text, List<String> terms, String preTag, String postTag) {
        String result = text;
        for (String term : terms) {
            result = result.replaceAll("(?i)(" + term + ")", preTag + "$1" + postTag);
        }
        return result;
    }
}
```

How to run: `java HighlightingLevel2.java`

Every one of the three query terms — `"wireless"`, `"mouse"`, `"usb"` — gets independently highlighted wherever it appears in the description, matching how a real multi-word `match` query highlights *all* the terms that contributed to the match, not just the first one found. This is what lets a user scanning search results immediately see every part of a longer field that made it relevant.

### Level 3 — Advanced

Customize the highlight markup tags (a common real requirement — `<em>` might conflict with existing page styling) and truncate to a fragment around the match, matching Elasticsearch's `fragment_size`/`number_of_fragments` options for showing a short excerpt rather than an entire long field.

```java
import java.util.*;
import java.util.regex.*;

public class HighlightingLevel3 {
    public static void main(String[] args) {
        String longDescription = "This premium wireless mouse features an ergonomic design, "
            + "a rechargeable battery lasting up to 6 months, silent click buttons, and a compact "
            + "USB-C receiver, making it ideal for both office and travel use.";

        // Customize markup tags -- matches Highlight configured with custom preTags/postTags.
        String customTagged = highlight(longDescription, List.of("wireless", "mouse"), "**", "**");
        System.out.println("Custom tags:\n" + customTagged);

        // Extract a SHORT fragment around the first match, matching fragment_size -- not the whole field.
        String fragment = extractFragment(longDescription, "rechargeable battery", 40, "<em>", "</em>");
        System.out.println("\nFragment (around 'rechargeable battery'):\n" + fragment);
    }

    static String highlight(String text, List<String> terms, String preTag, String postTag) {
        String result = text;
        for (String term : terms) result = result.replaceAll("(?i)(" + term + ")", preTag + "$1" + postTag);
        return result;
    }

    // Mirrors fragment_size: return only a WINDOW of text around the match, not the entire field.
    static String extractFragment(String text, String term, int windowChars, String preTag, String postTag) {
        Matcher matcher = Pattern.compile("(?i)" + Pattern.quote(term)).matcher(text);
        if (!matcher.find()) return null;
        int matchStart = matcher.start(), matchEnd = matcher.end();
        int fragmentStart = Math.max(0, matchStart - windowChars);
        int fragmentEnd = Math.min(text.length(), matchEnd + windowChars);
        String fragment = text.substring(fragmentStart, fragmentEnd);
        String highlighted = highlight(fragment, List.of(term), preTag, postTag);
        return (fragmentStart > 0 ? "..." : "") + highlighted + (fragmentEnd < text.length() ? "..." : "");
    }
}
```

How to run: `java HighlightingLevel3.java`

`highlight` with custom tags (`"**"` instead of `<em>`/`</em>`) demonstrates configuring `Highlight`'s pre/post tags for a UI that needs different markup than the default. `extractFragment` mirrors `fragment_size`: rather than returning the entire (potentially very long) field, it returns only a window of text around the match, with `"..."` markers where the fragment was truncated — exactly the behavior that keeps search result snippets short and scannable instead of dumping an entire article body into every result row.

## 6. Walkthrough

Execution starts in `main` for Level 3. `longDescription` is a multi-sentence string. `extractFragment(longDescription, "rechargeable battery", 40, "<em>", "</em>")` is called.

Inside `extractFragment`, a case-insensitive regex `Matcher` searches for `"rechargeable battery"` within `longDescription`. `matcher.find()` succeeds, and `matchStart`/`matchEnd` capture the character positions where the phrase begins and ends. `fragmentStart` is computed as `matchStart - 40`, clamped to `0` if that would go negative; `fragmentEnd` is `matchEnd + 40`, clamped to the string's actual length. `text.substring(fragmentStart, fragmentEnd)` extracts just that window of characters — not the whole `longDescription`.

`highlight(fragment, List.of("rechargeable battery"), "<em>", "</em>")` is then called on just this extracted window, wrapping the matched phrase in `<em>` tags within the already-shortened fragment. Finally, `"..."` is prepended if `fragmentStart > 0` (meaning the fragment doesn't start at the very beginning of the original text) and appended if `fragmentEnd < text.length()` (meaning it doesn't reach the very end) — signaling to a reader that the snippet was truncated from a longer field.

```
Custom tags:
This premium **wireless** **mouse** features an ergonomic design, a rechargeable battery lasting up to 6 months, silent click buttons, and a compact USB-C receiver, making it ideal for both office and travel use.

Fragment (around 'rechargeable battery'):
...ergonomic design, a <em>rechargeable battery</em> lasting up to 6 months, silent click...
```

In real Elasticsearch, `Highlight` configuration exposes `fragmentSize` (roughly how many characters per fragment), `numberOfFragments` (how many separate fragments to return per field, for fields with multiple matches spread far apart), and `preTags`/`postTags` (the markup wrapping matched terms) — `hit.getHighlightField("description")` then returns a `List<String>` of these pre-computed, already-truncated, already-marked-up fragments, ready to render directly in a search results UI without the application needing to do any of this extraction itself.

## 7. Gotchas & takeaways

> Gotcha: highlighting requires the field either be stored with `store: true` or, more commonly, rely on Elasticsearch re-analyzing the original `_source` document at query time — for very large documents or very frequent highlighted searches, this can add meaningful query-time cost; it's not free the way retrieving an already-indexed field value is.

> Gotcha: highlight markup (`<em>`, or custom tags) must be treated as trusted-but-still-render-carefully content — if the highlighted field's *original* content ever includes user-submitted text, the highlighted snippet contains that text verbatim (just wrapped in extra tags), so the same output-encoding precautions that apply to any user-generated content still apply when rendering a highlight snippet in HTML.

- Highlighting returns a separate, additional snippet showing exactly where and how a query matched within a field — it doesn't modify or replace the document's actual stored value.
- Multiple matched terms within the same field are each highlighted independently, letting a user see every part of a longer field that contributed to the match.
- `fragmentSize`/`numberOfFragments` control returning a short, relevant excerpt rather than an entire long field, keeping search result snippets scannable.
- Custom `preTags`/`postTags` let highlight markup match whatever a specific UI's styling conventions require, instead of Elasticsearch's `<em>` default.
