---
card: spring-data
gi: 138
slug: document-mapping-document-field-id
title: "Document mapping (@Document, @Field, @Id)"
---

## 1. What it is

`@Document` marks a Java class as mapped to an Elasticsearch index, `@Id` marks its identifier field, and `@Field` configures how each individual field is stored and searched — most importantly its `type` (`text` for analyzed full-text search, `keyword` for exact matching, `Date`, `Integer`, and so on). This mapping is what determines whether a field supports fuzzy relevance search or only exact comparison, as the previous card's gotcha flagged.

```java
@Document(indexName = "orders")
class Order {
    @Id String id;
    @Field(type = FieldType.Keyword) String status;       // exact match only
    @Field(type = FieldType.Text) String description;      // analyzed, full-text searchable
    @Field(type = FieldType.Date) Instant createdAt;
}
```

## 2. Why & when

Elasticsearch needs to know, ahead of time, how to treat each field: should `"Wireless Mouse"` be broken into searchable tokens (`text`), or should it only ever match the exact string `"Wireless Mouse"` (`keyword`)? This decision — the field's **mapping** — fundamentally shapes what queries against that field can do, and it's set once, generally before much data is indexed, since changing a field's type after the fact usually requires reindexing.

Reach for explicit `@Field` mapping when:

- A field needs full-text, relevance-ranked search (`FieldType.Text`) — descriptions, comments, article bodies — versus exact matching (`FieldType.Keyword`) — status codes, category ids, tags, anything you'd filter or aggregate on exactly.
- You need a field indexed as **both** — Elasticsearch supports multi-fields (`.keyword` sub-field convention), letting the same underlying value support full-text search *and* exact filtering/sorting/aggregation, which single-type mapping alone can't.
- You need precise control over date formats, numeric precision, or whether a field is indexed (searchable) at all versus merely stored.

## 3. Core concept

```
 @Field(type = FieldType.Text) String description = "Wireless Mouse, ergonomic design"
        |
        v
 ANALYZED into tokens: ["wireless", "mouse", "ergonomic", "design"]
   -- supports: full-text search, fuzzy matching, relevance scoring
   -- does NOT support: exact "give me this precise string" matching, or reliable sorting

 @Field(type = FieldType.Keyword) String status = "SHIPPED"
        |
        v
 STORED AS-IS, not tokenized: "SHIPPED"
   -- supports: exact match, sorting, aggregation (grouping/counting by exact value)
   -- does NOT support: partial-word or fuzzy search
```

The same string value, mapped two different ways, enables entirely different categories of query — this is the single most consequential decision in an Elasticsearch document's mapping.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A text field is analyzed into searchable tokens while a keyword field is stored as one exact, unanalyzed string">
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">description = "Wireless Mouse, ergonomic design"</text>

  <rect x="40" y="90" width="260" height="45" rx="8" fill="#6db33f22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="110" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">FieldType.Text (analyzed)</text>
  <text x="170" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">[wireless, mouse, ergonomic, design]</text>

  <rect x="340" y="90" width="260" height="45" rx="8" fill="#79c0ff22" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="110" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">FieldType.Keyword (exact)</text>
  <text x="470" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">"Wireless Mouse, ergonomic design"</text>

  <line x1="170" y1="55" x2="170" y2="85" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>
  <line x1="470" y1="55" x2="470" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The exact same source value produces two very different internal representations depending on its field type.

## 5. Runnable example

The scenario: mapping an `Order` document's fields correctly, evolving from a basic distinction between analyzed and exact-match fields, to a multi-field setup supporting both full-text search and exact aggregation on the same value, to demonstrating the practical consequence — what a query can and cannot do — driven entirely by the mapping choice.

### Level 1 — Basic

Model the core difference: a `text` field gets tokenized for search; a `keyword` field is compared as-is.

```java
import java.util.*;

public class DocumentMappingLevel1 {
    public static void main(String[] args) {
        String description = "Wireless Mouse, ergonomic design";
        String status = "SHIPPED";

        List<String> analyzedTokens = analyzeAsText(description); // FieldType.Text
        System.out.println("description analyzed as Text -> tokens: " + analyzedTokens);

        String storedKeyword = storeAsKeyword(status); // FieldType.Keyword
        System.out.println("status stored as Keyword -> exact value: \"" + storedKeyword + "\"");

        // A search against the Text field can match a SINGLE token...
        System.out.println("Text field matches token 'mouse': " + analyzedTokens.contains("mouse"));
        // ...but the Keyword field only matches the WHOLE exact string.
        System.out.println("Keyword field matches 'SHIP' (partial): " + storedKeyword.equals("SHIP"));
        System.out.println("Keyword field matches 'SHIPPED' (exact): " + storedKeyword.equals("SHIPPED"));
    }

    // Mirrors Elasticsearch's standard analyzer: lowercase, split on non-word characters.
    static List<String> analyzeAsText(String value) {
        List<String> tokens = new ArrayList<>();
        for (String token : value.toLowerCase().split("[^a-z0-9]+")) if (!token.isEmpty()) tokens.add(token);
        return tokens;
    }

    static String storeAsKeyword(String value) { return value; } // stored EXACTLY as given, no tokenizing
}
```

How to run: `java DocumentMappingLevel1.java`

`analyzeAsText` mirrors what Elasticsearch's standard analyzer does to a `text`-mapped field: lowercase and split into individual word tokens, which is why a search for the single word `"mouse"` can match this document. `storeAsKeyword` mirrors a `keyword`-mapped field: the value is indexed exactly as given, with no splitting, which is why only the complete, exact string matches — a partial string like `"SHIP"` does not.

### Level 2 — Intermediate

Model a **multi-field**: the same underlying value indexed both ways at once, supporting full-text search *and* exact aggregation — the standard `field` / `field.keyword` convention.

```java
import java.util.*;
import java.util.stream.*;

public class DocumentMappingLevel2 {
    public static void main(String[] args) {
        // Mirrors: @Field(type = FieldType.Text, fielddata = true) String category
        //          with an implicit "category.keyword" multi-field sub-mapping.
        List<Order> orders = List.of(
            new Order("1", "Office Furniture"),
            new Order("2", "Office Supplies"),
            new Order("3", "office furniture") // different casing -- same TOKENS, different exact string
        );

        // Full-text search on the analyzed "category" field -- matches regardless of case, word order tolerant.
        List<String> textSearchMatches = orders.stream()
            .filter(o -> analyzeAsText(o.category).contains("furniture"))
            .map(o -> o.id).collect(Collectors.toList());
        System.out.println("Text search for 'furniture': " + textSearchMatches);

        // Exact aggregation on the "category.keyword" sub-field -- groups by the LITERAL string, case-sensitive.
        Map<String, List<String>> exactGroups = orders.stream()
            .collect(Collectors.groupingBy(o -> o.category, Collectors.mapping(o -> o.id, Collectors.toList())));
        System.out.println("Exact aggregation by category.keyword: " + exactGroups);
    }

    static List<String> analyzeAsText(String value) {
        List<String> tokens = new ArrayList<>();
        for (String token : value.toLowerCase().split("[^a-z0-9]+")) if (!token.isEmpty()) tokens.add(token);
        return tokens;
    }
}

class Order { String id; String category; Order(String id, String category) { this.id = id; this.category = category; } }
```

How to run: `java DocumentMappingLevel2.java`

The text search for `"furniture"` matches both order `1` (`"Office Furniture"`) and order `3` (`"office furniture"`), since analysis lowercases both before tokenizing — case doesn't matter for a `text` field. The exact aggregation, standing in for grouping on the `.keyword` sub-field, treats `"Office Furniture"` and `"office furniture"` as two *distinct* groups, since `keyword` fields compare the literal string, case and all — this is exactly why Elasticsearch's standard convention maps a field both ways: full-text search tolerates variation, exact aggregation does not.

### Level 3 — Advanced

Show the practical consequence of getting the mapping wrong: attempting to sort by a `text` field (which Elasticsearch disallows by default) versus sorting correctly by its `.keyword` sub-field.

```java
import java.util.*;
import java.util.stream.*;

public class DocumentMappingLevel3 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "Electronics", 250.0),
            new Order("2", "Books", 15.0),
            new Order("3", "Electronics", 999.0)
        );

        // Sorting by a Text field is DISALLOWED by default in real Elasticsearch (fielddata is expensive/disabled) --
        // this method simulates that rejection explicitly, rather than silently doing something wrong.
        try {
            sortByTextField(orders);
        } catch (UnsupportedOperationException e) {
            System.out.println("Sorting by Text field rejected: " + e.getMessage());
        }

        // Sorting by the .keyword sub-field IS supported -- exact string comparison, cheap and reliable.
        List<Order> sorted = sortByKeywordField(orders);
        System.out.println("Sorted by category.keyword: " + sorted.stream().map(o -> o.category + ":" + o.id).collect(Collectors.toList()));
    }

    static List<Order> sortByTextField(List<Order> orders) {
        throw new UnsupportedOperationException(
            "Fielddata is disabled on [category] by default -- set fielddata=true, or sort on [category.keyword] instead.");
    }

    static List<Order> sortByKeywordField(List<Order> orders) {
        return orders.stream()
            .sorted(Comparator.comparing(o -> o.category)) // safe -- category.keyword is an exact, unanalyzed value
            .collect(Collectors.toList());
    }
}

class Order { String id; String category; double total; Order(String id, String category, double total) { this.id = id; this.category = category; this.total = total; } }
```

How to run: `java DocumentMappingLevel3.java`

`sortByTextField` mirrors the real error Elasticsearch raises when you try to sort or aggregate directly on a `text`-mapped field: this is disallowed by default because tokenized fields don't have a single well-defined "value" to sort by, and enabling it (`fielddata=true`) is expensive and generally discouraged. `sortByKeywordField`, standing in for sorting on `category.keyword`, works correctly and cheaply, because a `keyword` field always has exactly one unambiguous value per document to compare.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders are created with `category` values `"Electronics"`, `"Books"`, `"Electronics"`.

`sortByTextField(orders)` is called inside a `try` block. The method immediately throws an `UnsupportedOperationException` with a message modeling Elasticsearch's real error text about fielddata being disabled on `text` fields by default. The `catch` block catches this and prints the message — no sorting is ever attempted, matching how a real query against a `text` field for sorting purposes would be rejected by Elasticsearch itself before any data is even touched.

`sortByKeywordField(orders)` is then called. `Comparator.comparing(o -> o.category)` performs a straightforward string comparison across the three orders' `category` values — `"Books"` sorts before `"Electronics"` alphabetically — and the sorted list is returned and printed.

```
Sorting by Text field rejected: Fielddata is disabled on [category] by default -- set fielddata=true, or sort on [category.keyword] instead.
Sorted by category.keyword: [Books:2, Electronics:1, Electronics:3]
```

In real Spring Data Elasticsearch, a `category` field mapped as `@Field(type = FieldType.Text)` automatically gets a `category.keyword` multi-field sub-mapping when using Spring Data's default mapping conventions (or it can be configured explicitly with `@MultiField`) — sorting, exact filtering, and aggregations should target `category.keyword`, while full-text search queries target `category` itself. Attempting to sort directly on the analyzed `category` field produces exactly the `illegal_argument_exception` about fielddata this example models.

## 7. Gotchas & takeaways

> Gotcha: changing a field's mapping (`text` to `keyword`, or adjusting its analyzer) on an index that already contains documents does **not** retroactively re-map existing data — Elasticsearch requires creating a new index with the corrected mapping and reindexing every document into it (`_reindex` API), there's no in-place "alter column type" the way a relational `ALTER TABLE` allows.

> Gotcha: forgetting to add a `.keyword` multi-field to a `text` field you'll later need to sort, filter exactly, or aggregate on is a very common mistake that only becomes visible once you actually try one of those operations — plan field mappings around every access pattern you'll need, not just the initial search use case.

- `@Document` maps a class to an Elasticsearch index; `@Id` marks the identifier; `@Field(type = ...)` controls how each field is stored, analyzed, and therefore what kinds of queries it supports.
- `FieldType.Text` fields are tokenized for full-text, relevance-ranked search but generally can't be sorted, filtered exactly, or aggregated on directly.
- `FieldType.Keyword` fields are stored as exact, unanalyzed values — ideal for filtering, sorting, and aggregation, but not for partial or fuzzy matching.
- Multi-fields (`field` plus `field.keyword`) let one underlying value support both full-text search and exact operations, at the cost of slightly more index storage.
