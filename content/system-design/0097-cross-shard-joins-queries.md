---
card: system-design
gi: 97
slug: cross-shard-joins-queries
title: Cross-shard joins & queries
---

## 1. What it is

A **cross-shard join or query** is a query that needs data spread across more than one shard — for example, joining an `orders` row on shard 2 with a `users` row on shard 5, or asking "how many total orders were placed today" when orders are spread across every shard. Unlike a single-shard query, the database (or the application) must contact multiple shards and combine their results itself, because no single shard has the full picture.

## 2. Why & when

Sharding is chosen to make single-shard queries fast by keeping most requests inside one shard, but real systems still have some queries that genuinely need data from several shards at once — analytics, aggregate reports, or a join between two entities that were sharded by different keys. Recognizing when a query is cross-shard matters because it changes what you can optimize: a well-designed schema minimizes how often this happens (see [entity-based sharding](0093-geo-entity-based-sharding.md), which keeps a tenant's own data together specifically to avoid this), but it can rarely eliminate it entirely, especially for global aggregates.

## 3. Core concept

- **Scatter-gather:** the application (or a query router) sends the same query to every shard ("scatter"), then combines the partial results ("gather") — e.g. summing a `COUNT` from each shard, or merging and re-sorting rows from each shard for a paginated result.
- **Application-side join:** to join across shards, first query one shard for the base rows, then query the other shard(s) for the related rows by the keys just fetched, and join the two result sets in application code, since the database engine on either shard cannot see the other shard's data.
- **Denormalization avoids the join:** duplicating the needed fields onto the same shard, at write time, so the read never needs a second shard at all — the most common real-world fix.
- **Materialized/precomputed views:** for expensive aggregates run often (e.g. "total sales per day"), precompute the cross-shard aggregate on a schedule or on each write, and read the precomputed answer instead of scattering the query live.
- **Cost:** scatter-gather queries are slower (bounded by the slowest shard) and place load on every shard at once, unlike a normal query that touches only one.

## 4. Diagram

```
Query: "total order count today" (orders sharded by orders id across 3 shards)

        Application / Query Router
         /         |          \
        v          v           v
   Shard 0     Shard 1      Shard 2
   count=120   count=95     count=140      <- each shard counts only its own rows
        \          |          /
         \         |         /
          +--------+--------+
                   |
             gather + sum = 355            <- combined in the application
```
*Caption: a cross-shard aggregate is scattered to every shard, then the partial results are gathered and combined by the application.*

## 5. Runnable example

**Level 1 — Basic.** Scatter a count query across shards and gather the total.

**Level 2 — Application-side join.** Fetch base rows from one shard, then fetch related rows from another shard, and join them in code.

**Level 3 — Denormalized avoidance.** Show the same read served with zero cross-shard calls, because the needed field was duplicated at write time.

```java
// CrossShardQuery.java
import java.util.*;

public class CrossShardQuery {

    record Order(String orderId, String userId, double amount) {}
    record User(String userId, String name) {}

    // Orders sharded by orderId across 3 shards.
    static List<List<Order>> orderShards = List.of(
        List.of(new Order("o1", "u1", 20.0), new Order("o2", "u2", 15.0)),
        List.of(new Order("o3", "u1", 30.0)),
        List.of(new Order("o4", "u3", 10.0))
    );

    // Users sharded separately by userId, on a different shard boundary than orders.
    static Map<String, User> usersShard = Map.of(
        "u1", new User("u1", "Asha"),
        "u2", new User("u2", "Rahul"),
        "u3", new User("u3", "Mei")
    );

    public static void main(String[] args) {
        // Level 1: scatter-gather a count across all order shards.
        int total = 0;
        for (List<Order> shard : orderShards) total += shard.size();
        System.out.println("scatter-gather total order count: " + total);

        // Level 2: application-side join - fetch orders from shard 0, then join to users by userId.
        List<Order> ordersFromShard0 = orderShards.get(0);
        System.out.println("orders from shard 0: " + ordersFromShard0);
        for (Order o : ordersFromShard0) {
            User u = usersShard.get(o.userId()); // second call: a separate lookup into the users shard
            System.out.println("joined in application code: order " + o.orderId() + " belongs to " + u.name());
        }

        // Level 3: denormalized avoidance - orders store the user's name directly, no join needed.
        record DenormalizedOrder(String orderId, String userId, String userName, double amount) {}
        List<DenormalizedOrder> denormalized = List.of(
            new DenormalizedOrder("o1", "u1", "Asha", 20.0), // "Asha" was copied in at write time
            new DenormalizedOrder("o2", "u2", "Rahul", 15.0)
        );
        for (DenormalizedOrder d : denormalized) {
            System.out.println("read with zero cross-shard calls: order " + d.orderId() + " for " + d.userName());
        }
    }
}
```

**How to run:** save as `CrossShardQuery.java`, then run `java CrossShardQuery.java`.

## 6. Walkthrough

1. `orderShards` models orders spread across 3 shards; the Level 1 loop sums each shard's own `size()` — this is the scatter step (each shard counts its own rows) followed by the gather step (adding the partial counts together) to reach the true total.
2. Level 2 first fetches `ordersFromShard0` from the orders shard, then for each order looks up its `userId` in the separate `usersShard` map — two distinct lookups against two different shards, joined together in application code because neither shard alone has both pieces.
3. The printed lines show each order paired with its user's name, confirming the join succeeded, but at the cost of one extra lookup per order.
4. Level 3 defines `DenormalizedOrder`, which already carries `userName` alongside `userId`, because that name was copied in at the time the order was written.
5. Reading a `DenormalizedOrder` needs no second shard call at all — the trade is a small amount of duplicated, potentially-stale data (the user's name could change later) in exchange for a strictly single-shard, fast read.

## 7. Gotchas & takeaways

> Gotcha: scatter-gather queries are only as fast as the slowest shard involved, and they load every shard at once, even ones that hold no relevant rows for a specific request. Reserve them for genuine cross-shard needs (analytics, aggregates); for a query pattern you can predict in advance, denormalize the needed field instead so the read stays single-shard.

- A cross-shard query needs data from more than one shard, so it must be scattered out and its partial results gathered back together, usually by the application.
- Application-side joins across shards work but need a separate round trip per shard involved, unlike a join a single database can do internally.
- Denormalizing the needed field at write time, or precomputing an aggregate, are the standard ways to avoid paying the cross-shard cost on every read.
- Related concepts: [Denormalization & data duplication](0081-denormalization-data-duplication.md) (the main technique for avoiding cross-shard reads), [Geo / entity-based sharding](0093-geo-entity-based-sharding.md) (a sharding scheme chosen specifically to minimize cross-shard queries for one entity's own data).
