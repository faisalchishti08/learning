---
card: spring-data
gi: 161
slug: paging
title: "Paging"
---

## 1. What it is

Cassandra paging retrieves a large result set in bounded chunks using an opaque **paging state** token, rather than the offset-based `Pageable` paging seen in earlier sections of this course — a direct consequence of Cassandra's distributed architecture, where "skip N rows" has no natural meaning across data spread over many nodes the way it does in a single-server relational database.

```java
CassandraPageRequest pageRequest = CassandraPageRequest.first(20); // first page, 20 rows
Slice<Order> firstPage = cassandraTemplate.slice(query.pageRequest(pageRequest), Order.class);

CassandraPageRequest nextPageRequest = CassandraPageRequest.of(firstPage.getPageable());
Slice<Order> secondPage = cassandraTemplate.slice(query.pageRequest(nextPageRequest), Order.class);
```

## 2. Why & when

The earlier Elasticsearch section's `search_after` card explained why offset-based paging (`page=1000, size=20`) becomes expensive as it goes deeper — Elasticsearch at least *can* compute an offset, just at growing cost. Cassandra can't even do that efficiently: with data distributed across many nodes and partitions, there's no meaningful single ordering to "skip N rows" within. Instead, Cassandra returns a **paging state** — an opaque token encoding exactly where the last page's scan stopped — that the next request presents to resume precisely from there, with no re-scanning and no concept of jumping to an arbitrary page number at all.

Reach for Cassandra's `Slice`-based paging when:

- Retrieving any result set potentially larger than you want to load into memory at once — Cassandra paging is the default, expected way to consume a large partition or query result incrementally.
- Building a "load more" or infinite-scroll style UI, where each request naturally continues from the previous one — exactly matching the paging state's sequential-only design.
- Processing a large dataset in a batch job, walking through it page by page until no more pages remain, checking `Slice.hasNext()`.

There is no `Pageable`-with-page-number equivalent in Cassandra the way there was for Elasticsearch or JPA — the API itself (`Slice`, not `Page`) reflects that a total count and arbitrary page-number access simply aren't things Cassandra can efficiently provide.

## 3. Core concept

```
 Query.pageRequest(CassandraPageRequest.first(20))
        |
        v
 Slice<Order> firstPage = { content: [...20 rows...], pagingState: "opaque-token-abc" }

 Query.pageRequest(CassandraPageRequest.of(firstPage.getPageable()))
        |
        v
 Slice<Order> secondPage = { content: [...next 20 rows...], pagingState: "opaque-token-xyz" }

 -- there is NO "give me page 5" -- only "give me the page AFTER this specific paging state"
 -- Slice, unlike Spring Data's Page, has NO total element count either -- Cassandra doesn't compute that cheaply
```

Cassandra's `Slice` type deliberately lacks both a total count and random page access — both would require expensive, cluster-wide coordination that Cassandra's design avoids by not offering them.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each page's paging state token is required to fetch the next page; there is no way to jump directly to an arbitrary page">
  <rect x="20" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Slice 1 (rows 1-20)</text>

  <rect x="240" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Slice 2 (rows 21-40)</text>

  <rect x="460" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Slice 3 (rows 41-60)</text>

  <line x1="180" y1="42" x2="235" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="207" y="32" fill="#3fb950" font-size="7.5" text-anchor="middle" font-family="sans-serif">pagingState</text>

  <line x1="400" y1="42" x2="455" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="427" y="32" fill="#3fb950" font-size="7.5" text-anchor="middle" font-family="sans-serif">pagingState</text>

  <text x="320" y="110" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">no direct path from Slice 1 to Slice 3 -- must pass through Slice 2 first</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Each slice's paging state is required to fetch the next one — there is no way to skip ahead without walking through every preceding page.

## 5. Runnable example

The scenario: paging through a large order table, evolving from a basic first-page/next-page sequence using an opaque paging state, to walking through an entire result set page by page until exhausted, to demonstrating why Cassandra can't provide a total count cheaply — contrasting directly with `Page` from earlier sections in this course.

### Level 1 — Basic

Model a first page and a next page, using an opaque paging state to link them.

```java
import java.util.*;
import java.util.stream.*;

public class PagingLevel1 {
    public static void main(String[] args) {
        List<Order> allOrders = IntStream.rangeClosed(1, 45).mapToObj(i -> new Order("order-" + i)).collect(Collectors.toList());
        CassandraLikeTable table = new CassandraLikeTable(allOrders);

        Slice firstPage = table.fetchPage(null, 20); // null pagingState -- start from the beginning
        System.out.println("First page: " + firstPage.content.size() + " rows, pagingState=" + firstPage.pagingState + ", hasNext=" + firstPage.hasNext);

        Slice secondPage = table.fetchPage(firstPage.pagingState, 20); // resume from where the first page stopped
        System.out.println("Second page: " + secondPage.content.size() + " rows, pagingState=" + secondPage.pagingState + ", hasNext=" + secondPage.hasNext);
    }
}

class Order { String orderId; Order(String orderId) { this.orderId = orderId; } }

class Slice {
    List<Order> content; String pagingState; boolean hasNext;
    Slice(List<Order> content, String pagingState, boolean hasNext) { this.content = content; this.pagingState = pagingState; this.hasNext = hasNext; }
}

class CassandraLikeTable {
    private final List<Order> allRows;
    CassandraLikeTable(List<Order> allRows) { this.allRows = allRows; }

    // pagingState here is simplified as an integer OFFSET encoded as a string -- real Cassandra's token is opaque
    // and encodes internal scan position, NOT a simple offset, but the CLIENT-VISIBLE behavior is the same:
    // present the previous page's token to resume exactly where it left off.
    Slice fetchPage(String pagingState, int pageSize) {
        int start = (pagingState == null) ? 0 : Integer.parseInt(pagingState);
        int end = Math.min(start + pageSize, allRows.size());
        List<Order> page = allRows.subList(start, end);
        boolean hasNext = end < allRows.size();
        String nextPagingState = hasNext ? String.valueOf(end) : null;
        return new Slice(page, nextPagingState, hasNext);
    }
}
```

How to run: `java PagingLevel1.java`

`fetchPage(null, 20)` fetches the first 20 of 45 total orders and returns a non-null `pagingState` (since more remain), matching `CassandraPageRequest.first(20)`. `fetchPage(firstPage.pagingState, 20)` presents that state to resume exactly where the first page left off, retrieving orders 21–40 — mirroring `CassandraPageRequest.of(firstPage.getPageable())`'s behavior of continuing from a specific prior position rather than any notion of "page number 2."

### Level 2 — Intermediate

Walk through an entire result set page by page until exhausted, checking `hasNext` at each step — the standard pattern for consuming a large Cassandra result set incrementally.

```java
import java.util.*;
import java.util.stream.*;

public class PagingLevel2 {
    public static void main(String[] args) {
        List<Order> allOrders = IntStream.rangeClosed(1, 45).mapToObj(i -> new Order("order-" + i)).collect(Collectors.toList());
        CassandraLikeTable table = new CassandraLikeTable(allOrders);

        String pagingState = null;
        int pageNumber = 0;
        int totalFetched = 0;

        // The ONLY way to walk a Cassandra result set: repeat "fetch a page, use its paging state for the next fetch"
        // until hasNext is false -- there is no "jump to page N" shortcut.
        do {
            Slice page = table.fetchPage(pagingState, 20);
            pageNumber++;
            totalFetched += page.content.size();
            System.out.println("Page " + pageNumber + ": " + page.content.size() + " rows (running total: " + totalFetched + ")");
            pagingState = page.pagingState;
            if (!page.hasNext) break;
        } while (true);

        System.out.println("Consumed the entire result set across " + pageNumber + " pages, " + totalFetched + " total rows.");
    }
}

class Order { String orderId; Order(String orderId) { this.orderId = orderId; } }

class Slice {
    List<Order> content; String pagingState; boolean hasNext;
    Slice(List<Order> content, String pagingState, boolean hasNext) { this.content = content; this.pagingState = pagingState; this.hasNext = hasNext; }
}

class CassandraLikeTable {
    private final List<Order> allRows;
    CassandraLikeTable(List<Order> allRows) { this.allRows = allRows; }
    Slice fetchPage(String pagingState, int pageSize) {
        int start = (pagingState == null) ? 0 : Integer.parseInt(pagingState);
        int end = Math.min(start + pageSize, allRows.size());
        List<Order> page = allRows.subList(start, end);
        boolean hasNext = end < allRows.size();
        return new Slice(page, hasNext ? String.valueOf(end) : null, hasNext);
    }
}
```

How to run: `java PagingLevel2.java`

The `do`/`while` loop repeats "fetch using the current `pagingState`, then update `pagingState` from the result" until `hasNext` is `false` — the only way to consume an entire Cassandra result set, since there's no random access to any specific page number, only sequential continuation from wherever the previous page stopped.

### Level 3 — Advanced

Demonstrate why Cassandra's `Slice` has no total element count, unlike `Page` from earlier sections — computing a total count requires a full scan, which Cassandra deliberately doesn't do implicitly as part of ordinary paging.

```java
import java.util.*;
import java.util.stream.*;

public class PagingLevel3 {
    public static void main(String[] args) {
        List<Order> allOrders = IntStream.rangeClosed(1, 100000).mapToObj(i -> new Order("order-" + i)).collect(Collectors.toList());
        CassandraLikeTable table = new CassandraLikeTable(allOrders);

        Slice firstPage = table.fetchPage(null, 20);
        System.out.println("Slice.getContent().size(): " + firstPage.content.size() + " -- this page's row count IS known");
        System.out.println("Slice has NO getTotalElements() method -- unlike Page, because computing that");
        System.out.println("would require scanning the ENTIRE 100,000-row table, defeating the point of paging.");

        // If you genuinely need a total count, it's a SEPARATE, explicit, expensive operation --
        // never an implicit side effect of fetching one page, the way Page.getTotalElements() might suggest.
        long explicitCount = countAllRowsExpensively(table);
        System.out.println("Explicit COUNT(*)-style query (expensive, full scan): " + explicitCount + " total rows");
    }

    // Mirrors a real, deliberate SELECT COUNT(*) FROM orders -- a full-table scan, run ONLY when truly needed.
    static long countAllRowsExpensively(CassandraLikeTable table) {
        long count = 0;
        String pagingState = null;
        do {
            Slice page = table.fetchPage(pagingState, 1000); // scan in large batches, but still a FULL scan
            count += page.content.size();
            pagingState = page.pagingState;
            if (!page.hasNext) break;
        } while (true);
        return count;
    }
}

class Order { String orderId; Order(String orderId) { this.orderId = orderId; } }

class Slice {
    List<Order> content; String pagingState; boolean hasNext;
    Slice(List<Order> content, String pagingState, boolean hasNext) { this.content = content; this.pagingState = pagingState; this.hasNext = hasNext; }
}

class CassandraLikeTable {
    private final List<Order> allRows;
    CassandraLikeTable(List<Order> allRows) { this.allRows = allRows; }
    Slice fetchPage(String pagingState, int pageSize) {
        int start = (pagingState == null) ? 0 : Integer.parseInt(pagingState);
        int end = Math.min(start + pageSize, allRows.size());
        List<Order> page = allRows.subList(start, end);
        boolean hasNext = end < allRows.size();
        return new Slice(page, hasNext ? String.valueOf(end) : null, hasNext);
    }
}
```

How to run: `java PagingLevel3.java`

`firstPage.content.size()` gives the count of rows in *that one page* — always known, since it's just the size of the list actually returned. But there's no equivalent to `Page.getTotalElements()` for the *entire* result set, because Cassandra has no cheap way to compute it. `countAllRowsExpensively` shows what getting a true total actually requires: walking every single page until exhausted and summing as you go — precisely the full-cluster scan that `Slice`'s design avoids doing implicitly.

## 6. Walkthrough

Execution starts in `main` for Level 3. `allOrders` holds 100,000 synthetic orders. `firstPage = table.fetchPage(null, 20)` retrieves the first 20 — `firstPage.content.size()` is trivially `20`, immediately available with no extra cost.

`countAllRowsExpensively(table)` is then called to actually compute the *total* row count. Inside, a `do`/`while` loop identical in structure to Level 2's walk fetches pages of `1000` rows at a time (a larger batch size purely to make the full scan faster, but still fundamentally a full scan), accumulating `count` after each page and updating `pagingState` to continue. This loop runs `100` times (`100,000 / 1000`) before `hasNext` finally becomes `false`, at which point `count` equals `100000`.

```
Slice.getContent().size(): 20 -- this page's row count IS known
Slice has NO getTotalElements() method -- unlike Page, because computing that
would require scanning the ENTIRE 100,000-row table, defeating the point of paging.
Explicit COUNT(*)-style query (expensive, full scan): 100000 total rows
```

In real Cassandra, `SELECT COUNT(*) FROM orders` is exactly this kind of operation — a legitimate but expensive full-table (or full-partition) scan that the driver and Spring Data Cassandra never perform as a silent side effect of ordinary paging. This is a deliberate design choice reflecting Cassandra's priorities: an operation that's fundamentally a full scan should be visibly, explicitly requested, not hidden inside what looks like an innocuous "get the total count" property access the way `Page.getTotalElements()` might feel in a JPA or MongoDB context.

## 7. Gotchas & takeaways

> Gotcha: unlike `Pageable` from JPA/MongoDB or Elasticsearch's `search_after`, Cassandra's paging state is tied to the exact query it was generated for — presenting a paging state to a *different* query (even one that looks similar) is undefined behavior or an outright error. A paging state should always be treated as opaque and only reused with the exact query that produced it.

> Gotcha: Cassandra paging states are not designed to be stored long-term or reused across application restarts reliably — schema changes, cluster topology changes, or simply enough time passing can invalidate an old paging state. For a "resume later" UI pattern, prefer encoding your own resume marker from actual column values (similar to Elasticsearch's `search_after`) rather than persisting a raw Cassandra paging state token indefinitely.

- Cassandra paging uses an opaque paging state token to resume exactly where the previous page left off — there is no offset-based or page-number-based access, because Cassandra's distributed architecture has no efficient way to support it.
- `Slice` (not `Page`) is the return type for Cassandra paging, and it deliberately lacks a total element count, since computing one requires an expensive full scan that shouldn't happen implicitly.
- Consuming an entire large result set means repeatedly fetching pages and checking `hasNext()` until exhausted — there's no shortcut to skip ahead to a specific page.
- A genuine "total count" requirement is a separate, explicit, expensive operation (`SELECT COUNT(*)`), never an implicit side effect of ordinary paging.
