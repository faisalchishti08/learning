---
card: system-design
gi: 67
slug: query-planning-the-n-1-problem
title: "Query planning & the N+1 problem"
---

## 1. What it is

A **query planner** (or optimizer) is the part of a database that decides *how* to execute a SQL query — which indexes to use, which order to join tables in — before actually running it. The **N+1 problem** is a common application-level performance bug: fetching a list of N parent records with one query, then issuing one additional query *per parent* to fetch its related data, resulting in N+1 total queries instead of a single join.

## 2. Why & when

The query planner matters because the same SQL query can be executed many different ways with very different costs, and the planner's choice is invisible unless you explicitly inspect it. The N+1 problem matters because it is easy to write by accident — especially with an object-relational mapper (ORM) like JPA/Hibernate, where accessing a related object in code looks identical whether it triggers a fresh query or not. Watch for it whenever an application feels slow specifically in proportion to how many items are on a list page.

## 3. Core concept

**What the query planner does:** given a query, the planner considers the available indexes, estimates how many rows each possible approach would touch (using statistics about the data), and picks the plan it estimates is cheapest — for example, choosing whether to use an index or a full table scan, based on whether the filter is expected to match a small or a large fraction of the table.

**`EXPLAIN` reveals the chosen plan:** every major SQL database supports an `EXPLAIN` command that shows the plan actually chosen for a query — which indexes it uses, in what order it joins tables, and its estimated cost — the primary tool for diagnosing why a query is slow.

**How the N+1 problem happens:** code that loops over a list of parents and, inside the loop, separately loads each parent's related children (`for (order : orders) { loadItems(order.id) }`) issues one query for the list, then one more query per item in that list — for 100 orders, that is 101 queries instead of 1 or 2.

**The fix — eager loading via a join:** replace the per-parent queries with a single query that joins the parent and child tables together (or, in an ORM, an explicit "fetch join" / eager-loading hint), retrieving all the data needed in one round trip instead of N+1.

## 4. Diagram

```
N+1 PROBLEM (100 orders):
  Query 1: SELECT * FROM orders                       -> 100 orders
  Query 2..101: SELECT * FROM order_items WHERE order_id = ?   (once PER order)
  Total: 101 queries

FIXED (single join):
  Query 1: SELECT o.*, i.* FROM orders o
           JOIN order_items i ON i.order_id = o.id     -> all orders + items, ONE query
  Total: 1 query
```
*Caption: N+1 issues one extra query per parent row; a join fetches everything needed in a single round trip.*

## 5. Runnable example

**Level 1 — Basic.** Simulate the N+1 pattern: a query per order, counted explicitly.

**Level 2 — The fix.** The same data fetched with a single simulated join query.

**Level 3 — Cost comparison at scale.** Run both approaches over a growing number of orders and compare total query counts.

```java
// QueryPlanningNPlus1.java
import java.util.*;

public class QueryPlanningNPlus1 {

    record Order(int id) {}
    record OrderItem(int orderId, String product) {}

    static final List<Order> allOrders = new ArrayList<>();
    static final List<OrderItem> allItems = new ArrayList<>();
    static int queryCount = 0;

    static List<Order> queryOrders() {
        queryCount++;
        return new ArrayList<>(allOrders);
    }

    // Level 1: N+1 - one extra query PER order to fetch its items.
    static List<OrderItem> queryItemsForOrder(int orderId) {
        queryCount++;
        List<OrderItem> result = new ArrayList<>();
        for (OrderItem item : allItems) if (item.orderId() == orderId) result.add(item);
        return result;
    }

    // Level 2: the fix - one single joined query for everything.
    static Map<Integer, List<OrderItem>> queryOrdersWithItemsJoined() {
        queryCount++; // exactly one query, regardless of how many orders exist
        Map<Integer, List<OrderItem>> itemsByOrder = new HashMap<>();
        for (OrderItem item : allItems) {
            itemsByOrder.computeIfAbsent(item.orderId(), k -> new ArrayList<>()).add(item);
        }
        return itemsByOrder;
    }

    public static void main(String[] args) {
        // Level 3: set up 5 orders, each with 2 items.
        for (int i = 1; i <= 5; i++) {
            allOrders.add(new Order(i));
            allItems.add(new OrderItem(i, "item-A-of-order-" + i));
            allItems.add(new OrderItem(i, "item-B-of-order-" + i));
        }

        // N+1 approach.
        queryCount = 0;
        List<Order> orders = queryOrders(); // query 1
        for (Order o : orders) {
            queryItemsForOrder(o.id()); // one MORE query per order
        }
        System.out.println("N+1 approach: " + orders.size() + " orders -> " + queryCount + " total queries");

        // Fixed, single-join approach.
        queryCount = 0;
        Map<Integer, List<OrderItem>> ordersWithItems = queryOrdersWithItemsJoined();
        System.out.println("joined approach: " + ordersWithItems.size() + " orders -> " + queryCount + " total query");
    }
}
```

**How to run:** save as `QueryPlanningNPlus1.java`, then run `java QueryPlanningNPlus1.java`.

## 6. Walkthrough

1. `queryOrders()` runs once and increments `queryCount` to `1`, returning all five orders — this models the initial `SELECT * FROM orders`.
2. The `for (Order o : orders)` loop calls `queryItemsForOrder(o.id())` once per order, and each call increments `queryCount` — after five orders, `queryCount` is `1 + 5 = 6`, the "N+1" pattern for N=5.
3. `queryOrdersWithItemsJoined()` instead scans `allItems` once and groups them by `orderId` into a single `Map`, incrementing `queryCount` only once total, no matter how many orders exist — this models a single `JOIN` query.
4. The final printout contrasts `6` total queries for the N+1 approach against `1` total query for the joined approach, over the exact same underlying data — and the gap between the two only widens as the number of orders grows, since N+1 scales linearly with N while the joined approach stays constant at 1.

## 7. Gotchas & takeaways

> Gotcha: with an ORM like JPA/Hibernate, N+1 often hides behind **lazy loading** — accessing `order.getItems()` inside a loop looks like a normal method call in code, but if the association is lazily loaded, it silently triggers a fresh database query on every single access; the fix is switching to eager fetching (a fetch join) for access patterns known to need the related data.

- N+1 is invisible in code review unless you know to look for a query-triggering call inside a loop; the fastest way to catch it is by logging or counting actual queries issued during a request, or reading the query plan.
- `EXPLAIN` is the primary tool for understanding what a database actually did with a query — always check it before assuming an index is being used.
- Related concepts: [Spring Data JPA & repositories](0072-spring-data-jpa-repositories.md) (where the N+1 problem most commonly appears in Spring applications), [Covering indexes & index-only scans](0066-covering-indexes-index-only-scans.md) (a separate optimization the planner can choose to apply once N+1 is already fixed).
