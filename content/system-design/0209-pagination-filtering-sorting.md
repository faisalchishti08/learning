---
card: system-design
gi: 209
slug: pagination-filtering-sorting
title: Pagination, filtering & sorting
---

## 1. What it is

**Pagination** splits a large collection response into pages instead of returning every item at once. **Filtering** lets a client narrow a collection to items matching a condition (`status=SHIPPED`). **Sorting** lets a client control the order items are returned in (`sort=-createdAt`). All three are query-string controls on a collection endpoint like `GET /orders`.

## 2. Why & when

Returning every row of a large table in one response is slow to generate, slow to transfer, and wasteful when the client only needs the first screenful. Pagination bounds the response size to something predictable regardless of how large the underlying collection grows. Filtering and sorting reduce a large collection down to what the client actually needs, at the server, instead of the client fetching everything and filtering client-side.

Add pagination to any collection endpoint as soon as the collection can grow past a few hundred items — for most systems, that means from day one, since data volume tends to grow past initial expectations. Add filtering and sorting parameters as soon as clients need anything other than "everything, in insertion order."

## 3. Core concept

- **Offset pagination (`?page=3&size=20` or `?offset=40&limit=20`).** Simple to implement and lets a client jump to any page directly, but is slow on large offsets (the database still has to scan and discard all the skipped rows) and can show duplicate or skipped items if rows are inserted or deleted between page requests.
- **Cursor pagination (`?after=<opaque-token>&limit=20`).** The client passes back an opaque cursor from the previous page's last item; the server resumes from exactly that point. This is fast at any depth (no scanning and discarding) and stable even as data changes, but a client cannot jump directly to "page 5" — only to "the page after this cursor."
- **Filtering via query parameters (`?status=SHIPPED&customerId=42`).** Each filter narrows the collection with an implicit AND between parameters. Validate filter values against an allow-list of filterable fields — do not let a client filter on arbitrary internal fields.
- **Sorting via a `sort` parameter (`?sort=-createdAt,+id`).** A prefix (`+`/`-` or `asc`/`desc`) sets direction per field; multiple fields give a stable, fully-deterministic order (the second field breaks ties in the first).
- **Response metadata.** A paginated response should include enough to navigate further — a `nextCursor` or `nextPage` link, and ideally a `total` count (though `total` can be expensive to compute exactly on very large collections, and is sometimes approximated or omitted).

## 4. Diagram

```
  OFFSET PAGINATION                          CURSOR PAGINATION

  GET /orders?offset=0&limit=2                GET /orders?limit=2
  -> [order-1, order-2]                       -> [order-1, order-2], nextCursor: "eyJpZCI6Mn0="

  GET /orders?offset=2&limit=2                GET /orders?after=eyJpZCI6Mn0=&limit=2
  -> [order-3, order-4]                       -> [order-3, order-4], nextCursor: "eyJpZCI6NH0="

  (if order-1 is deleted between requests,     (cursor points at a specific row's position -
   offset=2 now SKIPS what was order-4,         insertions/deletions elsewhere do not shift
   because everything shifted left by one)       which rows this page returns)
```
*Caption: offset pagination counts positions from the start every time; cursor pagination remembers an exact place in the ordering, so it is stable even as the underlying data changes.*

## 5. Runnable example

**Level 1 — Basic.** Offset pagination and filtering over an in-memory collection.

**Level 2 — Intermediate.** Add multi-field sorting with direction, and show offset pagination's instability when a row is deleted between page requests.

**Level 3 — Advanced.** Cursor pagination that stays stable across the same deletion, using an opaque cursor derived from the last-seen item.

```java
// PaginationDemo.java
import java.util.*;
import java.util.stream.*;

public class PaginationDemo {

    record Order(int id, String status, double amount) {}

    static List<Order> allOrders() {
        return new ArrayList<>(List.of(
            new Order(1, "SHIPPED", 20.0), new Order(2, "PENDING", 15.0),
            new Order(3, "SHIPPED", 42.0), new Order(4, "CANCELLED", 5.0),
            new Order(5, "SHIPPED", 8.0)
        ));
    }

    // ---------- Level 1: offset pagination + filtering ----------
    static List<Order> filterByStatus(List<Order> orders, String status) {
        return orders.stream().filter(o -> status == null || o.status().equals(status)).toList();
    }
    static List<Order> paginateByOffset(List<Order> orders, int offset, int limit) {
        return orders.stream().skip(offset).limit(limit).toList();
    }

    // ---------- Level 2: sorting + offset instability ----------
    static List<Order> sortByAmountAsc(List<Order> orders) {
        return orders.stream().sorted(Comparator.comparingDouble(Order::amount)).toList();
    }

    // ---------- Level 3: cursor pagination ----------
    static List<Order> paginateByCursor(List<Order> orders, Integer afterId, int limit) {
        // Assumes orders are sorted by id ascending; the cursor is simply "the last id seen".
        return orders.stream()
            .filter(o -> afterId == null || o.id() > afterId)
            .limit(limit)
            .toList();
    }

    public static void main(String[] args) {
        List<Order> orders = allOrders();

        System.out.println("Level 1 - filter + offset pagination:");
        List<Order> shipped = filterByStatus(orders, "SHIPPED");
        System.out.println("  filtered (status=SHIPPED): " + shipped);
        System.out.println("  page 1 (offset=0, limit=2): " + paginateByOffset(shipped, 0, 2));
        System.out.println("  page 2 (offset=2, limit=2): " + paginateByOffset(shipped, 2, 2));

        System.out.println("\nLevel 2 - sorting, then offset instability when a row is deleted between requests:");
        System.out.println("  sorted by amount asc: " + sortByAmountAsc(orders));
        List<Order> page1 = paginateByOffset(orders, 0, 2);
        System.out.println("  page 1 (offset=0, limit=2), by insertion order: " + page1);
        orders.remove(0); // simulate order-1 being deleted between the two page requests
        System.out.println("  order-1 deleted between requests...");
        List<Order> page2 = paginateByOffset(orders, 2, 2);
        System.out.println("  page 2 (offset=2, limit=2) AFTER the deletion: " + page2 +
            "  <- order-4 was SKIPPED entirely, because everything shifted left by one");

        System.out.println("\nLevel 3 - cursor pagination stays stable across the same deletion:");
        List<Order> freshOrders = allOrders();
        List<Order> cPage1 = paginateByCursor(freshOrders, null, 2);
        System.out.println("  page 1 (after=none, limit=2): " + cPage1);
        int cursorAfterPage1 = cPage1.get(cPage1.size() - 1).id(); // cursor = last item's id
        freshOrders.remove(0); // same deletion as before
        System.out.println("  order-1 deleted between requests...");
        List<Order> cPage2 = paginateByCursor(freshOrders, cursorAfterPage1, 2);
        System.out.println("  page 2 (after=" + cursorAfterPage1 + ", limit=2) AFTER the deletion: " + cPage2 +
            "  <- order-4 is still present, nothing was skipped");
    }
}
```

**How to run:** `java PaginationDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `filterByStatus(orders, "SHIPPED")` keeps only orders whose `status` equals `"SHIPPED"`, leaving orders 1, 3, and 5. `paginateByOffset(shipped, 0, 2)` returns the first two of those three; `paginateByOffset(shipped, 2, 2)` skips the first two and returns just the third.
2. **Level 2:** `sortByAmountAsc(orders)` reorders every order by `amount`, showing sorting is independent of filtering and pagination — you can combine all three, though the code demonstrates each in isolation for clarity.
3. **`page1 = paginateByOffset(orders, 0, 2)`** returns orders 1 and 2 by insertion order. **`orders.remove(0)`** then deletes order 1 — simulating a real deletion that happens between two separate page requests from a client, a normal event in any live system.
4. **`page2 = paginateByOffset(orders, 2, 2)`** is called next, but the list has shifted: what was index 2 (order 3) before the deletion is now index 1. Offset 2 in the *new*, shorter list lands on order 4 skipping past it, so `page2` actually returns `[order-5]` only, and order 4 — which the client never saw on page 1 — is never returned on any page. This is the instability offset pagination has under concurrent writes.
5. **Level 3** repeats the exact same deletion, but `paginateByCursor` filters by `o.id() > afterId` instead of counting positions. `cursorAfterPage1` is captured as `2` (order 2's ID, the last item on page 1) *before* the deletion happens. After `freshOrders.remove(0)` runs, `paginateByCursor(freshOrders, 2, 2)` still correctly returns every order with `id > 2` — orders 3 and 4 — because the cursor identifies a specific row, not a position that shifts when earlier rows are removed.

## 7. Gotchas & takeaways

> **Gotcha:** a client using offset pagination while the underlying data is being written concurrently can silently skip or duplicate rows across pages — as Level 2 shows directly. This is not a bug in the pagination code; it is an inherent property of counting positions in a list that keeps changing.

- Default to cursor pagination for any collection that changes frequently or grows large; use offset pagination only when "jump to page N" is a real requirement and the data is relatively static.
- Validate filter fields against an allow-list — never let a filter parameter translate directly into an unvalidated database column or query clause.
- Always support multi-field sorting with an explicit tie-breaker (commonly the resource's ID) — sorting by a single non-unique field alone can return a different order on every request for rows that tie.
- These controls compose with [resource modeling](0206-resource-modeling-naming.md): pagination, filtering, and sorting apply to collection endpoints (`/orders`), never to single-resource endpoints (`/orders/{id}`).
