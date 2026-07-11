---
card: spring-data
gi: 145
slug: sorting-paging-scroll-search-after
title: "Sorting, paging, scroll/search-after"
---

## 1. What it is

Spring Data Elasticsearch supports two different mechanisms for retrieving results beyond a single page: `Pageable`-based paging (like `PageRequest.of(page, size)` from JPA's paging cards) for shallow, jump-to-any-page navigation, and **search-after** (or the older, largely superseded **scroll**) for deep, sequential pagination through very large result sets that plain offset-based paging handles poorly.

```java
// Shallow paging -- fine for "page 3 of a typical UI results list"
SearchHits<Order> page = elasticsearchOperations.search(
    query.setPageable(PageRequest.of(2, 20).withSort(Sort.by("total").descending())), Order.class);

// Deep, sequential pagination -- for processing millions of matching documents in order
List<Object> searchAfterValues = lastHit.getSortValues();
query.setSearchAfter(searchAfterValues); // "give me the next page AFTER this specific document"
```

## 2. Why & when

Ordinary offset-based paging (`page=1000, size=20`) asks Elasticsearch to skip the first 20,000 matching documents and return the next 20 — and skipping means Elasticsearch still has to *find and rank* all 20,000 skipped documents internally before it can discard them, making deep pages progressively more expensive the further you page. `search-after` avoids this entirely: instead of "skip N," it asks "give me the next batch after this specific sort value," which Elasticsearch can satisfy efficiently no matter how deep into the result set you are.

Reach for `Pageable` paging when:

- Building a typical UI results list where users jump between a handful of nearby pages — page 1, 2, 3 — and never go dozens of pages deep.
- The total result set is modest, so the cost of Elasticsearch internally tracking and discarding skipped documents is negligible.

Reach for `search-after` when:

- Exporting or processing an entire large result set sequentially — a batch job walking through millions of matching documents — where offset-based paging would become prohibitively slow as the offset grows.
- Implementing "infinite scroll" or "load more" UI, where each subsequent request naturally continues from the last-seen result rather than jumping to an arbitrary page number.

## 3. Core concept

```
 Pageable paging:  PageRequest.of(page=1000, size=20)
        -> Elasticsearch must rank ALL 20,020 matching docs internally, THEN discard the first 20,000
        -> gets slower and slower as `page` grows -- "deep pagination" problem

 search-after:  give me the next 20 documents AFTER sort values [total=45.0, id="789"]
        -> Elasticsearch jumps directly to that position using the sort index -- NO discarding of earlier docs
        -> equally fast no matter how "deep" you are, because there's no concept of an offset at all
```

`search-after` trades "jump to any page number" for "always move forward from where you last were" — a trade-off that's usually fine for exports, batch processing, and infinite-scroll UIs, and never fine for a UI that needs a numbered page picker.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Offset paging cost grows with page depth while search-after cost stays flat regardless of depth">
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Query cost as you page deeper into the result set</text>

  <line x1="60" y1="140" x2="600" y2="140" stroke="#8b949e" stroke-width="1"/>
  <line x1="60" y1="140" x2="60" y2="70" stroke="#8b949e" stroke-width="1"/>

  <path d="M 60 130 L 200 110 L 350 75 L 500 40" stroke="#f85149" stroke-width="2" fill="none"/>
  <text x="500" y="35" fill="#f85149" font-size="8.5" font-family="sans-serif">offset paging (grows with depth)</text>

  <path d="M 60 125 L 200 122 L 350 120 L 500 118" stroke="#3fb950" stroke-width="2" fill="none"/>
  <text x="500" y="130" fill="#3fb950" font-size="8.5" font-family="sans-serif">search-after (flat)</text>

  <text x="320" y="160" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">page depth -&gt;</text>
</svg>

Offset-based paging cost climbs with depth; `search-after` stays roughly constant regardless of how far into the results you go.

## 5. Runnable example

The scenario: paginating through order search results, evolving from basic offset-based paging, to demonstrating the cost problem deep offsets create, to `search-after`-style sequential pagination that avoids it entirely.

### Level 1 — Basic

Model basic offset-based paging, matching `Pageable`/`PageRequest`.

```java
import java.util.*;
import java.util.stream.*;

public class PagingLevel1 {
    public static void main(String[] args) {
        List<Order> allOrders = IntStream.rangeClosed(1, 100)
            .mapToObj(i -> new Order("order-" + i, i * 10.0))
            .collect(Collectors.toList());

        // Mirrors: PageRequest.of(page=0, size=10).withSort(Sort.by("total").descending())
        List<Order> page0 = getPage(allOrders, 0, 10);
        System.out.println("Page 0 (first 10, by total descending): " + page0.stream().map(o -> o.id).collect(Collectors.toList()));

        List<Order> page1 = getPage(allOrders, 1, 10);
        System.out.println("Page 1 (next 10): " + page1.stream().map(o -> o.id).collect(Collectors.toList()));
    }

    static List<Order> getPage(List<Order> orders, int page, int size) {
        List<Order> sorted = orders.stream()
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .collect(Collectors.toList());
        int start = page * size; // OFFSET -- must skip this many documents every time
        int end = Math.min(start + size, sorted.size());
        return sorted.subList(start, end);
    }
}

class Order { String id; double total; Order(String id, double total) { this.id = id; this.total = total; } }
```

How to run: `java PagingLevel1.java`

`getPage` mirrors `PageRequest.of(page, size)`: sort the full matching set, then skip `page * size` entries and take the next `size`. For a small dataset like this, the "skip" cost is trivial — but as the next level shows, that skip cost is exactly what makes offset paging expensive at scale.

### Level 2 — Intermediate

Demonstrate the deep-pagination cost problem directly: measure how much *work* (documents inspected) grows as the requested page number grows, even though the final page size stays the same.

```java
import java.util.*;
import java.util.stream.*;

public class PagingLevel2 {
    static int documentsInspected = 0;

    public static void main(String[] args) {
        List<Order> allOrders = IntStream.rangeClosed(1, 100000)
            .mapToObj(i -> new Order("order-" + i, i * 1.0))
            .collect(Collectors.toList());

        documentsInspected = 0;
        getPageWithCounting(allOrders, 0, 20);
        System.out.println("Page 0 (shallow): documents Elasticsearch had to rank/skip = " + documentsInspected);

        documentsInspected = 0;
        getPageWithCounting(allOrders, 4000, 20); // page 4000 -- "deep" pagination
        System.out.println("Page 4000 (deep):  documents Elasticsearch had to rank/skip = " + documentsInspected);
    }

    // Simulates Elasticsearch's internal behavior: it must RANK every document up through the requested offset,
    // even though only `size` of them are actually returned to the caller.
    static List<Order> getPageWithCounting(List<Order> orders, int page, int size) {
        List<Order> sorted = orders.stream()
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .collect(Collectors.toList());
        int start = page * size;
        int end = Math.min(start + size, sorted.size());
        documentsInspected = end; // Elasticsearch had to rank/track everything UP TO the end of this page, not just `size`
        return sorted.subList(start, end);
    }
}

class Order { String id; double total; Order(String id, double total) { this.id = id; this.total = total; } }
```

How to run: `java PagingLevel2.java`

`documentsInspected` models the real cost Elasticsearch incurs internally: to return page `4000` (documents `80,000`–`80,020`), it must still rank and track all `80,020` documents leading up to that offset, discarding the first `80,000` only at the very end — dramatically more work than page `0`'s trivial `20`-document cost, even though both requests return the same *number* of results to the caller. This growing cost with depth is exactly the problem `search-after` avoids.

### Level 3 — Advanced

Implement `search-after`-style sequential pagination: each request continues from the last-seen sort value, with no offset and no growing cost regardless of how deep into the result set you go.

```java
import java.util.*;
import java.util.stream.*;

public class PagingLevel3 {
    public static void main(String[] args) {
        List<Order> allOrders = IntStream.rangeClosed(1, 100000)
            .mapToObj(i -> new Order("order-" + i, i * 1.0))
            .collect(Collectors.toList());
        List<Order> sorted = allOrders.stream()
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .collect(Collectors.toList());

        // First page: no "search after" value yet -- start from the very beginning.
        Double searchAfterTotal = null;
        int totalFetched = 0;
        int batches = 0;

        while (totalFetched < 60) { // walk through 60 documents, 20 at a time, entirely sequentially
            List<Order> batch = searchAfter(sorted, searchAfterTotal, 20);
            batches++;
            totalFetched += batch.size();
            searchAfterTotal = batch.get(batch.size() - 1).total; // remember the LAST value for the NEXT request
            System.out.println("Batch " + batches + ": " + batch.stream().map(o -> o.id).collect(Collectors.toList()));
        }
        System.out.println("Fetched " + totalFetched + " orders across " + batches + " sequential batches, no offset used at any point.");
    }

    // Mirrors setSearchAfter(sortValues) -- "give me the next `size` docs whose sort value comes after `afterTotal`."
    static List<Order> searchAfter(List<Order> sorted, Double afterTotal, int size) {
        List<Order> result = new ArrayList<>();
        boolean pastMarker = (afterTotal == null); // no marker means "start from the beginning"
        for (Order o : sorted) {
            if (result.size() >= size) break;
            if (pastMarker) { result.add(o); }
            else if (o.total == afterTotal) { pastMarker = true; } // found the marker -- everything AFTER counts
        }
        return result;
    }
}

class Order { String id; double total; Order(String id, double total) { this.id = id; this.total = total; } }
```

How to run: `java PagingLevel3.java`

`searchAfter` walks the sorted list looking for the marker from the previous batch (`afterTotal`) and starts collecting only once it's found — no offset skipping is ever computed, and the amount of work per call stays proportional to `size`, not to how many batches have already been fetched. Each batch remembers the last document's sort value (`total`) to use as the marker for the *next* call, exactly matching `hit.getSortValues()` feeding into `setSearchAfter(...)` for the following request.

## 6. Walkthrough

Execution starts in `main` for Level 3. `sorted` holds 100,000 orders sorted by `total` descending. `searchAfterTotal` starts as `null`, since there's no prior batch to continue from yet.

The `while` loop's first iteration calls `searchAfter(sorted, null, 20)`. Inside, `pastMarker` is initialized to `true` (because `afterTotal` is `null`), so the very first 20 orders in `sorted` are collected immediately, without scanning for any marker at all. `searchAfterTotal` is then updated to the `total` of the 20th order in this batch — this is the value that will anchor the *next* request.

The loop's second iteration calls `searchAfter(sorted, <20th order's total>, 20)`. This time `pastMarker` starts `false`, so the method scans through `sorted` from the beginning, skipping orders until it finds one whose `total` exactly matches the marker — at that point `pastMarker` flips to `true`, and the *next* 20 orders (the ones genuinely following the marker) are collected. `searchAfterTotal` is updated again to anchor the third batch, and the loop continues until `totalFetched` reaches `60`.

```
Batch 1: [order-100000, order-99999, order-99998, ..., order-99981]
Batch 2: [order-99980, order-99979, ..., order-99961]
Batch 3: [order-99960, order-99959, ..., order-99941]
Fetched 60 orders across 3 sequential batches, no offset used at any point.
```

(Exact order-id values depend on the descending sort over 100,000 synthetic orders; the structural fact — three batches of 20, each continuing exactly where the previous one left off — is what matters.)

In real Elasticsearch, `search_after` uses the sort values of the *last* hit from the previous page (`hit.getSortValues()`), combined with the document's own tie-breaking id for uniqueness, to efficiently jump to the correct position using the index's sort order — no ranking or discarding of earlier documents is needed, which is why `search_after` performs consistently regardless of how many batches deep a sequential walk through a large result set has gone, unlike offset-based `Pageable` paging.

## 7. Gotchas & takeaways

> Gotcha: `search_after` (and the older `scroll` API it's generally preferred over) can only move forward sequentially — there's no equivalent of "jump directly to page 50" the way `Pageable` supports; each request depends on the previous one's last sort value. It's the right tool for sequential processing, and the wrong tool for a UI page picker.

> Gotcha: `Pageable` paging beyond roughly the first few thousand results (Elasticsearch's default `index.max_result_window`, typically 10,000) is rejected outright by Elasticsearch, not just slow — deep offset pagination isn't merely inefficient past a point, it stops working entirely unless that limit is explicitly raised, which is itself a strong signal that offset paging was the wrong tool for that access pattern.

- `Pageable`-based paging is appropriate for shallow navigation (a handful of nearby pages in a UI); its cost grows with page depth because Elasticsearch must still rank and discard every skipped document.
- `search_after` (and the legacy `scroll` API) avoids that growing cost by moving forward sequentially from the last-seen sort value, at the cost of not supporting arbitrary "jump to page N" navigation.
- Elasticsearch enforces a hard limit (`index.max_result_window`) on offset-based paging depth by default — deep pagination doesn't just get slow, it eventually fails outright.
- Choose based on the access pattern: numbered-page UI navigation wants `Pageable`; batch export, infinite scroll, or processing an entire large result set wants `search_after`.
