---
card: system-design
gi: 82
slug: access-pattern-first-data-modeling
title: Access-pattern-first data modeling
---

## 1. What it is

**Access-pattern-first data modeling** is the discipline of designing a NoSQL schema by starting from the exact queries your application needs to run, and shaping the data (keys, embedded fields, duplicated copies) specifically to answer each one efficiently — the reverse order from relational design, which starts from the entities and their relationships, then figures out queries afterward.

## 2. Why & when

Relationally, you can usually normalize first and let the query planner and joins figure out how to answer whatever question comes up later — flexibility is mostly free. In most NoSQL stores, that flexibility is not free: a query that does not match how the data was modeled is often slow, or entirely unsupported, rather than just "a bit slower." Access-pattern-first modeling exists because of this constraint: you must know your queries *before* you design the schema, not after. Apply it any time you design a schema for a document, key-value, or wide-column store.

## 3. Core concept

**Step 1 — list every access pattern first, before touching schema:** for an e-commerce order system, this might be: "get an order by ID," "get all orders for a customer, newest first," "get all orders containing a specific product." Each becomes a concrete requirement the schema must satisfy directly.

**Step 2 — design one key/table/document shape per access pattern:** rather than one normalized `orders` table serving every query via different `WHERE` clauses, you might end up with an `orders` collection keyed by order ID (for pattern 1), a `customer_orders` structure keyed by customer ID with orders sorted by date (for pattern 2), and a `product_orders` index keyed by product ID (for pattern 3) — deliberately duplicating order data across all three.

**Step 3 — accept the resulting duplication as correct, not a smell:** this is the direct consequence of the previous tutorial's point — once each access pattern has its own tailored shape, some of the same facts necessarily live in more than one place, and that is the expected, correct outcome of this method, not something to "fix" by normalizing it away.

**Why this differs so sharply from relational thinking:** a relational schema is designed once and serves unanticipated future queries reasonably well, because joins are cheap and flexible. A NoSQL schema designed without knowing its access patterns in advance often cannot serve a new, unanticipated query at all without a costly full scan or a schema migration — so the access patterns must be known up front.

## 4. Diagram

```
STEP 1: list every access pattern needed
  AP1: get order by orderId
  AP2: get a customer's orders, newest first
  AP3: get all orders containing a given productId

STEP 2: one tailored shape PER access pattern (duplicated data, on purpose)
  orders/{orderId}                          -> serves AP1 directly
  customerOrders/{customerId}/{date}        -> serves AP2 directly (sorted by date already)
  productOrders/{productId}/{orderId}       -> serves AP3 directly

STEP 3: a single order write fans out to ALL THREE shapes
  place order -> write to orders/{orderId}
              -> write to customerOrders/{customerId}/{date}
              -> write to productOrders/{productId}/{orderId}
```
*Caption: each access pattern gets its own purpose-built shape; one logical write becomes several physical writes, one per shape that needs to know about it.*

## 5. Runnable example

**Level 1 — Basic.** Define access patterns explicitly, then a naive single-table model that cannot serve one of them efficiently.

**Level 2 — Tailored shapes per pattern.** Three separate structures, each modeled to answer one access pattern directly.

**Level 3 — Fan-out write.** A single "place order" operation writes to all three shapes at once, keeping every access pattern servable.

```java
// AccessPatternFirst.java
import java.util.*;

public class AccessPatternFirst {

    record Order(String orderId, String customerId, String date, List<String> productIds) {}

    // A naive single collection, keyed ONLY by orderId - fine for AP1, bad for AP2 and AP3.
    static final Map<String, Order> ordersById = new HashMap<>();

    // Level 2: tailored shapes, one per access pattern, populated by the SAME writes.
    static final Map<String, TreeMap<String, Order>> customerOrders = new HashMap<>(); // AP2: customerId -> date -> order
    static final Map<String, List<Order>> productOrders = new HashMap<>();             // AP3: productId -> [orders]

    // Level 3: one logical write, fanned out to every shape that needs to know about it.
    static void placeOrder(Order order) {
        ordersById.put(order.orderId(), order); // serves AP1
        customerOrders.computeIfAbsent(order.customerId(), c -> new TreeMap<>(Comparator.reverseOrder()))
            .put(order.date(), order); // serves AP2, pre-sorted newest first
        for (String productId : order.productIds()) {
            productOrders.computeIfAbsent(productId, p -> new ArrayList<>()).add(order); // serves AP3
        }
    }

    public static void main(String[] args) {
        placeOrder(new Order("order-1", "cust-42", "2026-08-01", List.of("sku1", "sku2")));
        placeOrder(new Order("order-2", "cust-42", "2026-08-03", List.of("sku3")));
        placeOrder(new Order("order-3", "cust-99", "2026-08-02", List.of("sku1")));

        // AP1: get order by orderId - one direct lookup.
        System.out.println("AP1 - order-2 by ID: " + ordersById.get("order-2"));

        // AP2: get a customer's orders, newest first - already sorted, no extra work.
        System.out.println("AP2 - cust-42's orders, newest first:");
        for (Order o : customerOrders.get("cust-42").values()) {
            System.out.println("  " + o.orderId() + " (" + o.date() + ")");
        }

        // AP3: all orders containing sku1 - a direct lookup, not a scan of every order.
        System.out.println("AP3 - orders containing sku1:");
        for (Order o : productOrders.get("sku1")) {
            System.out.println("  " + o.orderId());
        }

        // Contrast: naively scanning ordersById for AP3, WITHOUT the tailored shape.
        System.out.println("AP3 the NAIVE way (scanning every order, no tailored shape):");
        int scanned = 0;
        for (Order o : ordersById.values()) {
            scanned++;
            if (o.productIds().contains("sku1")) System.out.println("  found (after scanning " + scanned + " orders so far): " + o.orderId());
        }
    }
}
```

**How to run:** save as `AccessPatternFirst.java`, then run `java AccessPatternFirst.java`.

## 6. Walkthrough

1. `placeOrder` writes the same logical order into three different structures in one call: `ordersById` (for AP1), `customerOrders` (for AP2, using a `TreeMap` so results come out pre-sorted by date), and `productOrders` (for AP3) — this is the fan-out write step 3 describes.
2. `ordersById.get("order-2")` answers AP1 with one direct lookup.
3. `customerOrders.get("cust-42").values()` iterates in reverse date order automatically (because of the `TreeMap`'s reverse comparator), answering AP2 with zero sorting work at query time — the sort work was done once, at write time.
4. `productOrders.get("sku1")` directly returns exactly the two orders containing `sku1`, answering AP3 with one lookup — no scan of the other order needed.
5. The final naive-scan block deliberately answers AP3 the way a schema *without* the tailored `productOrders` shape would have to: scanning every entry in `ordersById` and checking each one's `productIds` — the same correct final answer, but requiring work proportional to the total number of orders, not just the matching ones, which is exactly the cost access-pattern-first modeling avoids by preparing the `productOrders` shape in advance.

## 7. Gotchas & takeaways

> Gotcha: an access pattern discovered *after* the schema is already in production (a new feature needing a query the data was never shaped for) often means a real migration — backfilling a new tailored structure for every existing record — not just adding an index, which is why listing access patterns thoroughly up front matters so much more here than it does relationally.

- List every access pattern before designing a NoSQL schema; each one typically needs its own tailored shape, not a single general-purpose table.
- The resulting duplication across shapes is the deliberate, correct outcome of this method — accept it, and make sure every write path fans out to every shape it needs to keep current.
- Related concepts: [Denormalization & data duplication](0081-denormalization-data-duplication.md) (the duplication this method produces, examined directly), [When to choose SQL vs NoSQL](0083-when-to-choose-sql-vs-nosql.md) (deciding whether this modeling discipline is even the right fit for your data).
