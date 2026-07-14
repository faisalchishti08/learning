---
card: microservices
gi: 499
slug: pagination-filtering-sorting-conventions
title: "Pagination, filtering, sorting conventions"
---

## 1. What it is

**Pagination, filtering, and sorting conventions** are the standardized query-parameter patterns a service's list endpoints use to let consumers request a specific page of results (`?page=2&size=20` or `?cursor=abc123&limit=20`), filter by field values (`?status=SHIPPED`), and control ordering (`?sort=createdAt,desc`) — applied *consistently* across every list endpoint in an API, so a consumer who learns the pattern once can use it everywhere.

## 2. Why & when

You establish these conventions explicitly, and apply them uniformly, because list endpoints are extremely common and inconsistency between them creates real, recurring friction:

- **Returning an entire unbounded collection doesn't scale.** A `GET /orders` endpoint that returns every order ever placed, with no limit, works fine with ten test records and becomes a serious performance and memory problem with ten million real ones — pagination bounds every response to a manageable size regardless of total collection size.
- **Consumers need to filter and sort without pulling the entire dataset client-side.** Doing filtering and sorting after fetching everything wastes bandwidth and defeats the purpose of pagination entirely — the server should do this work, using the same data it's already querying.
- **Inconsistent conventions across different endpoints in the same API force consumers to learn several different patterns for the same fundamental operation.** If `/orders` paginates with `page`/`size` and `/customers` paginates with `offset`/`limit`, every consumer team pays a small but real tax relearning the pattern for each new endpoint they integrate with.
- **You establish these conventions once, early, for the whole API**, and apply them to every list endpoint from the start — retrofitting consistent pagination onto an API that's already shipped several inconsistent endpoints is a breaking change for whoever's already built against the old ones.

## 3. Core concept

Think of a library's card catalog system: you don't browse every book in the building one at a time — you request a specific section (pagination), narrow by genre or author (filtering), and choose to browse alphabetically or by publication date (sorting), all using the same consistent request format regardless of which section of the library you're searching. A well-designed list API gives consumers that same consistent, scoped access pattern.

Concretely:

1. **Pagination** bounds the response size — either offset-based (`?page=2&size=20`, simple but can shift under concurrent writes) or cursor-based (`?cursor=abc123&limit=20`, stable under concurrent writes but requires an opaque cursor token rather than a human-readable page number).
2. **Filtering** narrows the result set by field values before pagination and sorting are applied — `?status=SHIPPED&customerId=42` — using query parameters named consistently with the resource's actual field names.
3. **Sorting** controls result order — `?sort=createdAt,desc` or `?sort=-createdAt` — with a documented default sort applied when the consumer doesn't specify one, so results are still deterministic even without explicit sorting.
4. **All three compose together** — a single request can filter, sort, and paginate simultaneously, with the server applying filtering first, then sorting, then pagination, in that logical order, regardless of the order the query parameters happen to appear in the URL.
5. **Response metadata communicates pagination state** — total count (if feasible to compute cheaply), whether more pages exist, and how to request the next one — so a consumer never has to guess whether they've seen the whole collection.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request applies filtering first, then sorting, then pagination, to produce a bounded, ordered, relevant page of results" >
  <rect x="20" y="70" width="140" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1. filter</text>
  <text x="90" y="112" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">status=SHIPPED</text>

  <rect x="200" y="70" width="140" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="270" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">2. sort</text>
  <text x="270" y="112" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">createdAt,desc</text>

  <rect x="380" y="70" width="140" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="450" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">3. paginate</text>
  <text x="450" y="112" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">page=1, size=20</text>

  <line x1="160" y1="97" x2="200" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="340" y1="97" x2="380" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The three operations compose in a fixed logical order: filter narrows the set, sort orders it, pagination bounds the response.

## 5. Runnable example

Scenario: a list endpoint applying filtering, sorting, and pagination to an in-memory order collection. We start with basic pagination alone, extend it to filtering and sorting composed together, then handle the hard case: a cursor-based pagination approach that stays stable even when items are inserted concurrently, unlike naive offset-based pagination.

### Level 1 — Basic

```java
// File: PaginationBasic.java -- models BASIC offset-style pagination:
// bounding an unbounded collection to a requested page size.
import java.util.*;

public class PaginationBasic {
    record Order(String id, String status, long createdAtEpoch) {}

    static List<Order> allOrders = List.of(
        new Order("1", "SHIPPED", 100), new Order("2", "PENDING", 200),
        new Order("3", "SHIPPED", 300), new Order("4", "DELIVERED", 400),
        new Order("5", "SHIPPED", 500)
    );

    static List<Order> paginate(List<Order> orders, int page, int size) {
        int fromIndex = Math.min(page * size, orders.size());
        int toIndex = Math.min(fromIndex + size, orders.size());
        return orders.subList(fromIndex, toIndex);
    }

    public static void main(String[] args) {
        List<Order> page0 = paginate(allOrders, 0, 2);
        System.out.println("[GET /orders?page=0&size=2] " + page0);
    }
}
```

How to run: `java PaginationBasic.java`

`paginate` computes `fromIndex` and `toIndex` from the requested `page` and `size`, using `Math.min` to safely bound against the collection's actual length — a request for a page beyond the data simply returns an empty list rather than throwing an out-of-bounds error.

### Level 2 — Intermediate

```java
// File: FilterSortPaginate.java -- the SAME pagination, now COMPOSED
// with filtering and sorting, applied in the CORRECT logical order:
// filter first, sort second, paginate last.
import java.util.*;
import java.util.stream.*;

public class FilterSortPaginate {
    record Order(String id, String status, long createdAtEpoch) {}

    static List<Order> allOrders = List.of(
        new Order("1", "SHIPPED", 100), new Order("2", "PENDING", 200),
        new Order("3", "SHIPPED", 300), new Order("4", "DELIVERED", 400),
        new Order("5", "SHIPPED", 500)
    );

    static List<Order> listOrders(String statusFilter, boolean sortDescending, int page, int size) {
        List<Order> filtered = allOrders.stream()
            .filter(o -> statusFilter == null || o.status().equals(statusFilter))
            .collect(Collectors.toList());

        Comparator<Order> comparator = Comparator.comparingLong(Order::createdAtEpoch);
        if (sortDescending) comparator = comparator.reversed();
        filtered.sort(comparator);

        int fromIndex = Math.min(page * size, filtered.size());
        int toIndex = Math.min(fromIndex + size, filtered.size());
        return filtered.subList(fromIndex, toIndex);
    }

    public static void main(String[] args) {
        List<Order> result = listOrders("SHIPPED", true, 0, 2);
        System.out.println("[GET /orders?status=SHIPPED&sort=createdAt,desc&page=0&size=2] " + result);
    }
}
```

How to run: `java FilterSortPaginate.java`

`listOrders` applies its three operations in strict sequence: `filter` narrows `allOrders` down to only `SHIPPED` orders first, `sort` (via the `Comparator`, reversed when descending) orders that filtered subset second, and only then does the pagination math run against the filtered-and-sorted list — ensuring the returned page reflects the correct, fully-composed result rather than pagination happening on the wrong (unfiltered or unsorted) collection.

### Level 3 — Advanced

```java
// File: CursorPaginationStability.java -- the SAME list operation, now
// handling the PRODUCTION-FLAVORED hard case: a NEW item is INSERTED into
// the collection BETWEEN two page requests. OFFSET-based pagination
// SHIFTS under this condition (an item can be skipped or duplicated
// across pages); CURSOR-based pagination remains STABLE, because it
// anchors to a specific item's position rather than a numeric offset.
import java.util.*;
import java.util.stream.*;

public class CursorPaginationStability {
    record Order(String id, long createdAtEpoch) {}

    static List<Order> orders = new ArrayList<>(List.of(
        new Order("1", 100), new Order("2", 200), new Order("3", 300), new Order("4", 400)
    ));

    // OFFSET-based: vulnerable to shifting when items are inserted.
    static List<Order> offsetPage(int offset, int limit) {
        List<Order> sorted = orders.stream().sorted(Comparator.comparingLong(Order::createdAtEpoch)).collect(Collectors.toList());
        int from = Math.min(offset, sorted.size());
        int to = Math.min(from + limit, sorted.size());
        return sorted.subList(from, to);
    }

    // CURSOR-based: anchors to "everything AFTER this specific createdAtEpoch value".
    static List<Order> cursorPage(Long afterCursor, int limit) {
        return orders.stream()
            .sorted(Comparator.comparingLong(Order::createdAtEpoch))
            .filter(o -> afterCursor == null || o.createdAtEpoch() > afterCursor)
            .limit(limit)
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        System.out.println("--- OFFSET pagination: page 1 (offset=2, limit=2) BEFORE insertion ---");
        List<Order> offsetPage1Before = offsetPage(2, 2);
        System.out.println(offsetPage1Before);

        System.out.println();
        System.out.println("--- CURSOR pagination: same logical page BEFORE insertion (cursor after id=2's timestamp) ---");
        List<Order> cursorPage1Before = cursorPage(200L, 2);
        System.out.println(cursorPage1Before);

        System.out.println();
        System.out.println("[event] a NEW order (id=1.5, createdAtEpoch=150) is inserted BETWEEN order 1 and order 2");
        orders.add(new Order("1.5", 150));

        System.out.println();
        System.out.println("--- OFFSET pagination: SAME request (offset=2, limit=2) AFTER insertion -- SHIFTED! ---");
        List<Order> offsetPage1After = offsetPage(2, 2);
        System.out.println(offsetPage1After + " -- order '2' is DUPLICATED across the two offset page fetches!");

        System.out.println();
        System.out.println("--- CURSOR pagination: SAME cursor (after createdAtEpoch=200) AFTER insertion -- STABLE ---");
        List<Order> cursorPage1After = cursorPage(200L, 2);
        System.out.println(cursorPage1After + " -- identical result, unaffected by the insertion");
    }
}
```

How to run: `java CursorPaginationStability.java`

`offsetPage` re-sorts the *current* collection and slices by numeric position every time it's called — when a new item is inserted at an earlier sort position than the previous page boundary, every subsequent item's numeric offset shifts by one, causing `offsetPage(2, 2)` to return a different, overlapping result than before. `cursorPage` instead filters for `createdAtEpoch > afterCursor` — since the cursor value itself (`200L`) never changes and doesn't depend on position, the same cursor call returns the identical logical "everything after this point" result regardless of what gets inserted earlier in the sequence.

## 6. Walkthrough

Trace `CursorPaginationStability.main` in order. **First**, `offsetPage(2, 2)` runs before any insertion: `orders` sorted by `createdAtEpoch` gives `[1(100), 2(200), 3(300), 4(400)]`, and slicing from index `2` to `4` returns `[3(300), 4(400)]`.

**Next**, `cursorPage(200L, 2)` runs before insertion: it filters for `createdAtEpoch > 200`, matching `3(300)` and `4(400)` from the same sorted list, and `limit(2)` caps it — producing the identical `[3(300), 4(400)]` result as the offset approach, for this specific "second page" scenario.

**Then**, the simulated insertion adds `Order("1.5", 150)` to `orders` — a new item whose `createdAtEpoch` of `150` places it *between* order `1` (100) and order `2` (200) in sort order.

**After that**, `offsetPage(2, 2)` runs again with the exact same arguments. But now the sorted list is `[1(100), 1.5(150), 2(200), 3(300), 4(400)]` — five items instead of four — and slicing from index `2` to `4` now returns `[2(200), 3(300)]`. Order `2` appeared in the *first* offset page before the insertion (implicitly, at index `1`) and now reappears in this "second page" request too — a genuine duplicate a client paginating through results would see.

**Finally**, `cursorPage(200L, 2)` runs again with the identical cursor value, `200L`. It filters the now-five-item sorted list for `createdAtEpoch > 200`, which still matches only `3(300)` and `4(400)` — the newly inserted `1.5(150)` has a `createdAtEpoch` of `150`, which is *not* greater than `200`, so it's correctly excluded from this cursor's results. The cursor page returns the exact same `[3(300), 4(400)]` as before the insertion, completely unaffected.

```
--- OFFSET pagination: page 1 (offset=2, limit=2) BEFORE insertion ---
[Order[id=3, createdAtEpoch=300], Order[id=4, createdAtEpoch=400]]

--- CURSOR pagination: same logical page BEFORE insertion (cursor after id=2's timestamp) ---
[Order[id=3, createdAtEpoch=300], Order[id=4, createdAtEpoch=400]]

[event] a NEW order (id=1.5, createdAtEpoch=150) is inserted BETWEEN order 1 and order 2

--- OFFSET pagination: SAME request (offset=2, limit=2) AFTER insertion -- SHIFTED! ---
[Order[id=2, createdAtEpoch=200], Order[id=3, createdAtEpoch=300]] -- order '2' is DUPLICATED across the two offset page fetches!

--- CURSOR pagination: SAME cursor (after createdAtEpoch=200) AFTER insertion -- STABLE ---
[Order[id=3, createdAtEpoch=300], Order[id=4, createdAtEpoch=400]] -- identical result, unaffected by the insertion
```

## 7. Gotchas & takeaways

> Offset-based pagination's vulnerability to shifting under concurrent writes isn't a rare edge case in a genuinely active system — any list endpoint backed by frequently-changing data (new orders arriving constantly) will experience this regularly, silently causing consumers who paginate through "all results" to see duplicates or, worse, skip items entirely.
- Cursor-based pagination is the stronger choice for any collection that changes while consumers might be actively paginating through it — offset-based pagination's simplicity (human-readable page numbers, jump-to-page-N support) is a real usability advantage worth keeping for smaller, more static collections.
- Apply filtering before sorting and sorting before pagination, consistently, regardless of which order the query parameters appear in the request URL — the logical order matters for correctness, the parameter order in the URL should not.
- Document a sensible default sort order for every list endpoint — a consumer that doesn't specify `sort` should still get deterministic, repeatable ordering, not an unspecified or effectively random one that could differ between identical requests.
- Consistency across every list endpoint in an API (the same parameter names, the same pagination style) is worth establishing as an explicit convention document early, since inconsistency compounds — every new endpoint that deviates adds one more pattern every consumer has to separately learn.
