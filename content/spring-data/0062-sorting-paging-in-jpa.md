---
card: spring-data
gi: 62
slug: sorting-paging-in-jpa
title: "Sorting & paging in JPA"
---

## 1. What it is

`Sort` and `Pageable` (both covered generically in the earlier Spring Data Commons cards) get translated by the JPA module specifically into `ORDER BY` clauses and `setFirstResult`/`setMaxResults` calls on the generated JPQL query — plus, for `Page<T>` (as opposed to `Slice<T>`), an extra `COUNT` query to compute the total number of elements.

```java
Page<Order> findByStatus(String status, Pageable pageable);
// pageable = PageRequest.of(0, 20, Sort.by("total").descending())
```

## 2. Why & when

This card is the JPA-specific mechanics behind the `Page`/`Slice`/`Sort` types a Spring Data Commons card already introduced generically. Knowing exactly what SQL a `Pageable` argument produces — an `ORDER BY`, a `LIMIT`/`OFFSET` (or vendor equivalent), and possibly a second `COUNT` query — matters because that second query is a real, sometimes expensive, cost that `Slice` avoids.

Reach for JPA-level paging awareness specifically when:

- You're returning `Page<T>` from a large table and want to understand why two queries run per request — the data query and the `COUNT` query needed for `getTotalElements()`/`getTotalPages()`.
- You only need "is there a next page" (not an exact total), in which case `Slice<T>` skips the `COUNT` query entirely, which is cheaper on large tables.
- You're combining sorting with paging and need to guarantee stable ordering — paging without a deterministic `ORDER BY` can return duplicate or skipped rows across pages on some databases.

## 3. Core concept

```
 Page<Order> findByStatus(String status, Pageable pageable)

 Generates TWO queries when Page is used:
   1) SELECT o FROM Order o WHERE o.status = :status
      ORDER BY o.total DESC
      -- LIMIT 20 OFFSET 0   (from pageable.getPageSize()/getOffset())
   2) SELECT COUNT(o) FROM Order o WHERE o.status = :status
      -- needed for Page.getTotalElements()/getTotalPages()

 Slice<Order> findByStatus(String status, Pageable pageable)
   -- only query (1) runs; Slice.hasNext() is inferred by fetching one extra row
```

`Page` costs a second `COUNT` query for exact totals; `Slice` avoids it by only checking whether one more row exists.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Page triggers a data query plus a count query; Slice only runs the data query">
  <rect x="230" y="10" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="34" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Pageable(page=0, size=20)</text>

  <rect x="30" y="80" width="230" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="102" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Page&lt;Order&gt;</text>
  <text x="145" y="118" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">data query + COUNT query</text>

  <rect x="380" y="80" width="230" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="102" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Slice&lt;Order&gt;</text>
  <text x="495" y="118" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">data query only (fetch +1 row)</text>

  <line x1="300" y1="50" x2="180" y2="75" stroke="#8b949e" stroke-width="1.3" marker-end="url(#sg)"/>
  <line x1="340" y1="50" x2="470" y2="75" stroke="#8b949e" stroke-width="1.3" marker-end="url(#sg)"/>
  <defs><marker id="sg" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same `Pageable` input drives either two queries (`Page`, with an exact total) or one (`Slice`, cheaper but no total count).

## 5. Runnable example

The scenario: paging through a sorted list of orders, evolving from a basic sorted/limited slice, to a page with a total-count query, to a `Slice`-style "has next" check that avoids the count entirely.

### Level 1 — Basic

Model `Pageable`-driven sorting and limiting directly against an in-memory list, standing in for the `ORDER BY` + `LIMIT`/`OFFSET` a real JPA query would generate.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total; String status;
    Order(long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
    public String toString() { return "Order{id=" + id + ", total=" + total + "}"; }
}

public class PagingLevel1 {
    // Simulates: findByStatus(status, PageRequest.of(page, size, Sort.by("total").descending()))
    static List<Order> findByStatusSortedPaged(List<Order> data, String status, int page, int size) {
        return data.stream()
            .filter(o -> o.status.equals(status))
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed()) // ORDER BY total DESC
            .skip((long) page * size)  // OFFSET
            .limit(size)               // LIMIT
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, 50, "SHIPPED"), new Order(2, 300, "SHIPPED"),
            new Order(3, 120, "SHIPPED"), new Order(4, 80, "SHIPPED"), new Order(5, 200, "SHIPPED")
        );
        List<Order> page0 = findByStatusSortedPaged(orders, "SHIPPED", 0, 2);
        System.out.println("Page 0: " + page0);
    }
}
```

How to run: `java PagingLevel1.java`

`sorted(...).skip(...).limit(...)` mirrors exactly what a JPA provider does with a `Pageable` argument: apply the `Sort` as `ORDER BY`, then the page offset/size as `OFFSET`/`LIMIT`. `Page 0` (size 2) returns the two highest-total orders: `{id=2, total=300}` and `{id=5, total=200}`.

### Level 2 — Intermediate

Add the second query `Page<T>` requires: a total count, bundled with the page's content into a small `Page`-like result type, matching `Page.getContent()`/`Page.getTotalElements()`.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total; String status;
    Order(long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
    public String toString() { return "Order{id=" + id + ", total=" + total + "}"; }
}

// Stands in for org.springframework.data.domain.Page<T>
record OrderPage(List<Order> content, long totalElements, int totalPages) {}

public class PagingLevel2 {
    static OrderPage findByStatusPage(List<Order> data, String status, int page, int size) {
        List<Order> matching = data.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());

        // Query 1: the data, sorted, limited.
        List<Order> content = matching.stream()
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .skip((long) page * size).limit(size)
            .collect(Collectors.toList());

        // Query 2: SELECT COUNT(o) FROM Order o WHERE o.status = :status
        long totalElements = matching.size();
        int totalPages = (int) Math.ceil((double) totalElements / size);

        return new OrderPage(content, totalElements, totalPages);
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, 50, "SHIPPED"), new Order(2, 300, "SHIPPED"),
            new Order(3, 120, "SHIPPED"), new Order(4, 80, "SHIPPED"), new Order(5, 200, "SHIPPED")
        );
        OrderPage page0 = findByStatusPage(orders, "SHIPPED", 0, 2);
        System.out.println("Content: " + page0.content());
        System.out.println("Total elements: " + page0.totalElements() + ", total pages: " + page0.totalPages());
    }
}
```

How to run: `java PagingLevel2.java`

`totalElements` (a stand-in for the `COUNT` query) is computed independently of `content` (the data query) — in a real repository these are two separate round trips to the database, run every time `Page<T>` is requested, which is the cost `Page` accepts in exchange for exposing `getTotalElements()`/`getTotalPages()`.

### Level 3 — Advanced

Add a `Slice`-equivalent that avoids the count query by fetching one extra row to infer `hasNext()`, and compare its cost against the `Page` version from Level 2.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total; String status;
    Order(long id, double total, String status) { this.id = id; this.total = total; this.status = status; }
    public String toString() { return "Order{id=" + id + ", total=" + total + "}"; }
}

record OrderPage(List<Order> content, long totalElements, int totalPages) {}
record OrderSlice(List<Order> content, boolean hasNext) {}

public class PagingLevel3 {
    static int queryCount = 0;

    static OrderPage findByStatusPage(List<Order> data, String status, int page, int size) {
        List<Order> matching = data.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
        queryCount++; // data query
        List<Order> content = matching.stream()
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .skip((long) page * size).limit(size).collect(Collectors.toList());
        queryCount++; // COUNT query
        long total = matching.size();
        return new OrderPage(content, total, (int) Math.ceil((double) total / size));
    }

    // Slice: fetch size+1 rows; if we get size+1 back, there IS a next page. No COUNT query needed.
    static OrderSlice findByStatusSlice(List<Order> data, String status, int page, int size) {
        List<Order> matching = data.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
        queryCount++; // ONLY the data query
        List<Order> fetched = matching.stream()
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .skip((long) page * size).limit(size + 1) // ask for one extra
            .collect(Collectors.toList());
        boolean hasNext = fetched.size() > size;
        List<Order> content = hasNext ? fetched.subList(0, size) : fetched;
        return new OrderSlice(content, hasNext);
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, 50, "SHIPPED"), new Order(2, 300, "SHIPPED"),
            new Order(3, 120, "SHIPPED"), new Order(4, 80, "SHIPPED"), new Order(5, 200, "SHIPPED")
        );

        queryCount = 0;
        OrderPage page0 = findByStatusPage(orders, "SHIPPED", 0, 2);
        System.out.println("Page: content=" + page0.content() + ", totalElements=" + page0.totalElements()
            + " (queries used: " + queryCount + ")");

        queryCount = 0;
        OrderSlice slice0 = findByStatusSlice(orders, "SHIPPED", 0, 2);
        System.out.println("Slice: content=" + slice0.content() + ", hasNext=" + slice0.hasNext()
            + " (queries used: " + queryCount + ")");
    }
}
```

How to run: `java PagingLevel3.java`

`findByStatusPage` uses 2 queries (`queryCount` reaches 2); `findByStatusSlice` uses only 1 (`queryCount` reaches 1), by fetching `size + 1` rows and checking whether the extra row exists (`fetched.size() > size`) instead of running a separate `COUNT`. Both correctly report the first page's content, but `Slice` cannot answer "how many total orders are there" — only "is there another page after this one."

## 6. Walkthrough

Execution starts in `main`. First, `queryCount` is reset to 0 and `findByStatusPage(orders, "SHIPPED", 0, 2)` runs: it filters the 5 orders down to the matching ones (all 5, all `SHIPPED`), increments `queryCount` to 1 for the data query, sorts and pages to get `content = [{id=2,total=300}, {id=5,total=200}]`, then increments `queryCount` to 2 for the `COUNT` query, computing `totalElements = 5` and `totalPages = 3`. The printed line shows both the content and `queries used: 2`.

Next, `queryCount` is reset to 0 and `findByStatusSlice(orders, "SHIPPED", 0, 2)` runs: it filters the same 5 matching orders, increments `queryCount` to only 1, then fetches `size + 1 = 3` rows sorted descending — `[{300}, {200}, {120}]`. Since `fetched.size() (3) > size (2)`, `hasNext` is `true`, and `content` is trimmed back down to the first 2: `[{300}, {200}]`. The printed line shows the same content as the `Page` version, but `queries used: 1`.

```
findByStatusPage:  filter -> [query 1: sort+page] -> [query 2: COUNT] -> Page(content, total=5, pages=3)
findByStatusSlice: filter -> [query 1: sort+page+1 row] -> infer hasNext -> Slice(content, hasNext=true)
```

In a real Spring Data JPA repository, an HTTP request like `GET /orders?status=SHIPPED&page=0&size=2&sort=total,desc` arrives at a controller, which builds a `PageRequest.of(0, 2, Sort.by("total").descending())` and passes it to `findByStatus(status, pageable)`. If the method returns `Page<Order>`, Spring Data runs the paged `SELECT ... ORDER BY total DESC LIMIT 2` plus a `SELECT COUNT(*) ...` with the same `WHERE` clause, and the controller can respond with `{"content": [...], "totalElements": 5, "totalPages": 3}`. If the method instead returns `Slice<Order>`, only the first query runs (fetching one extra row under the hood), and the response can only say `{"content": [...], "hasNext": true}` — no total.

## 7. Gotchas & takeaways

> Gotcha: paging without an explicit, unique-tiebreak-inclusive `Sort` can return inconsistent results across pages if the underlying rows have ties or the database doesn't guarantee stable ordering for equal sort keys — always sort by something that, combined with a tiebreaker like the ID, produces a fully deterministic order when paging matters.

- `Page<T>` costs two queries: the data query and a `COUNT` query for `getTotalElements()`/`getTotalPages()`.
- `Slice<T>` costs one query: it fetches one extra row to infer `hasNext()`, avoiding the `COUNT` entirely.
- Prefer `Slice` for infinite-scroll/"load more" UIs that never need an exact total; prefer `Page` when the UI needs page numbers or a total count.
- Combine `Sort` with paging carefully — an unstable sort order can produce duplicate or skipped rows as a user pages forward.
