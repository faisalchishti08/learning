---
card: spring-data
gi: 146
slug: routing
title: "Routing"
---

## 1. What it is

An Elasticsearch index is internally split into multiple **shards**, and by default a document's id determines which shard it lives on. **Routing** overrides that default, letting you choose the shard yourself — typically by tying together all documents that share some logical grouping (like a customer or tenant), using `@Routing` on the entity or a routing value passed explicitly at index/search time.

```java
@Document(indexName = "orders")
@Routing("customerId") // route by customerId instead of the default (document id)
class Order {
    @Id String id;
    String customerId;
    String status;
}
```

## 2. Why & when

By default, Elasticsearch has to check *every* shard of an index to answer a search, since it doesn't know in advance which shard holds a matching document — a search request fans out to all shards and merges the results. If related documents are deliberately co-located on the same shard via custom routing, a search scoped to that same routing value only needs to query that *one* shard, skipping every other shard entirely — turning an N-shard search into a single-shard lookup.

Reach for custom routing when:

- Your access pattern is dominated by queries scoped to one logical group at a time — "all of this customer's orders," "all of this tenant's documents" — and you want those queries to hit only the relevant shard rather than fanning out across the whole index.
- You're running a genuinely large, multi-shard index where search latency matters and a natural grouping key (customer, tenant, region) exists in your data.
- You want documents that are frequently retrieved or updated together to physically live together, reducing the coordination overhead across shards for those operations.

Routing is a performance and scalability optimization for larger deployments — a small, single-shard (or few-shard) index gains nothing from it, since there's no meaningful shard fan-out to avoid in the first place.

## 3. Core concept

```
 WITHOUT custom routing (default: route by document id):
   order-1 (customerId=A) -> shard 2 (based on order-1's own id)
   order-2 (customerId=A) -> shard 0 (based on order-2's own id)  -- SAME customer, DIFFERENT shard!
   order-3 (customerId=B) -> shard 1

   search "all orders for customer A" -> must check ALL shards, since A's orders are scattered

 WITH @Routing("customerId"):
   order-1 (customerId=A) -> shard determined by hash("A")
   order-2 (customerId=A) -> shard determined by hash("A")  -- SAME shard, guaranteed
   order-3 (customerId=B) -> shard determined by hash("B")

   search "all orders for customer A", routing="A" -> only ONE shard needs to be checked
```

Routing trades "documents spread evenly for general query patterns" for "related documents co-located for one specific, dominant query pattern."

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without routing, a customer's orders scatter across shards requiring a full fan-out search; with routing, they co-locate on one shard for a targeted search">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Without routing: customer A's orders scattered</text>
  <rect x="20" y="30" width="120" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="80" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">shard 0: order-2</text>
  <rect x="160" y="30" width="120" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="220" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">shard 1: order-3</text>
  <rect x="300" y="30" width="120" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="360" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">shard 2: order-1</text>
  <text x="20" y="85" fill="#f85149" font-size="9" font-family="sans-serif">search for customer A must fan out to shards 0 AND 2</text>

  <text x="20" y="120" fill="#e6edf3" font-size="10" font-family="sans-serif">With @Routing("customerId"): customer A's orders co-located</text>
  <rect x="20" y="130" width="120" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="80" y="152" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">shard 0: order-3</text>
  <rect x="300" y="130" width="200" height="35" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="400" y="152" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">shard 2: order-1, order-2</text>
  <text x="20" y="180" fill="#3fb950" font-size="9" font-family="sans-serif">search for customer A only needs shard 2</text>
</svg>

Custom routing co-locates related documents on one shard, so a scoped search only ever needs to visit that one shard.

## 5. Runnable example

The scenario: routing orders by customer id, evolving from a basic default-routing model showing how documents scatter across shards, to custom routing co-locating a customer's documents, to a search that leverages the routing value to skip irrelevant shards entirely.

### Level 1 — Basic

Model default routing: each document's shard is determined by its own id, independent of any logical grouping.

```java
import java.util.*;
import java.util.stream.*;

public class RoutingLevel1 {
    static final int SHARD_COUNT = 3;

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("order-1", "customer-A", "SHIPPED"),
            new Order("order-2", "customer-A", "PENDING"),
            new Order("order-3", "customer-B", "SHIPPED")
        );

        System.out.println("Default routing (by document id):");
        for (Order o : orders) {
            int shard = shardFor(o.id); // DEFAULT: routes by the document's OWN id
            System.out.println("  " + o.id + " (customer=" + o.customerId + ") -> shard " + shard);
        }
    }

    static int shardFor(String routingValue) { return Math.floorMod(routingValue.hashCode(), SHARD_COUNT); }
}

class Order { String id; String customerId; String status; Order(String id, String customerId, String status) { this.id = id; this.customerId = customerId; this.status = status; } }
```

How to run: `java RoutingLevel1.java`

`shardFor` mirrors Elasticsearch's default routing formula, `hash(_id) % number_of_shards` — each document's shard depends purely on its own id, with no relationship to `customerId` at all. Order `1` and order `2`, despite belonging to the same customer, will generally land on different shards, since their document ids hash differently.

### Level 2 — Intermediate

Apply custom routing by `customerId`, co-locating all of one customer's orders on the same shard, matching `@Routing("customerId")`.

```java
import java.util.*;
import java.util.stream.*;

public class RoutingLevel2 {
    static final int SHARD_COUNT = 3;

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("order-1", "customer-A", "SHIPPED"),
            new Order("order-2", "customer-A", "PENDING"),
            new Order("order-3", "customer-B", "SHIPPED"),
            new Order("order-4", "customer-A", "DELIVERED")
        );

        System.out.println("Custom routing (@Routing(\"customerId\")):");
        Map<Integer, List<String>> shardContents = new TreeMap<>();
        for (Order o : orders) {
            int shard = shardFor(o.customerId); // CUSTOM: routes by customerId instead of the document's own id
            shardContents.computeIfAbsent(shard, k -> new ArrayList<>()).add(o.id + " (customer=" + o.customerId + ")");
        }
        shardContents.forEach((shard, docs) -> System.out.println("  shard " + shard + ": " + docs));
    }

    static int shardFor(String routingValue) { return Math.floorMod(routingValue.hashCode(), SHARD_COUNT); }
}

class Order { String id; String customerId; String status; Order(String id, String customerId, String status) { this.id = id; this.customerId = customerId; this.status = status; } }
```

How to run: `java RoutingLevel2.java`

Because every order's shard is now computed from its `customerId` rather than its own `id`, all three of `customer-A`'s orders (`order-1`, `order-2`, `order-4`) land on the exact same shard — `customer-B`'s single order lands on whatever shard `hash("customer-B")` resolves to, independently. This co-location is the entire point of custom routing: documents that are logically related now live physically together.

### Level 3 — Advanced

Simulate a routed search: with custom routing applied, a search scoped to one customer only needs to query the single shard holding that customer's data, instead of fanning out to every shard in the index.

```java
import java.util.*;
import java.util.stream.*;

public class RoutingLevel3 {
    static final int SHARD_COUNT = 3;
    static int shardFor(String routingValue) { return Math.floorMod(routingValue.hashCode(), SHARD_COUNT); }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("order-1", "customer-A", "SHIPPED"),
            new Order("order-2", "customer-A", "PENDING"),
            new Order("order-3", "customer-B", "SHIPPED"),
            new Order("order-4", "customer-A", "DELIVERED"),
            new Order("order-5", "customer-C", "SHIPPED")
        );

        // Index into shards using CUSTOM routing by customerId.
        Map<Integer, List<Order>> shards = new HashMap<>();
        for (Order o : orders) shards.computeIfAbsent(shardFor(o.customerId), k -> new ArrayList<>()).add(o);

        System.out.println("--- searching WITHOUT a routing hint (must fan out to ALL shards) ---");
        List<Order> unroutedResults = searchAllShards(shards, "customer-A");
        System.out.println("Shards queried: " + shards.size() + ", results: "
            + unroutedResults.stream().map(o -> o.id).collect(Collectors.toList()));

        System.out.println("--- searching WITH the routing value (only queries ONE shard) ---");
        int targetShard = shardFor("customer-A");
        List<Order> routedResults = searchSingleShard(shards, targetShard, "customer-A");
        System.out.println("Shards queried: 1 (shard " + targetShard + "), results: "
            + routedResults.stream().map(o -> o.id).collect(Collectors.toList()));
    }

    // WITHOUT routing info: must check EVERY shard, since the caller doesn't know which one holds matching docs.
    static List<Order> searchAllShards(Map<Integer, List<Order>> shards, String customerId) {
        List<Order> results = new ArrayList<>();
        for (List<Order> shardDocs : shards.values()) {
            for (Order o : shardDocs) if (o.customerId.equals(customerId)) results.add(o);
        }
        return results;
    }

    // WITH routing info: go DIRECTLY to the one shard that must contain any matches, skip every other shard entirely.
    static List<Order> searchSingleShard(Map<Integer, List<Order>> shards, int shard, String customerId) {
        List<Order> shardDocs = shards.getOrDefault(shard, List.of());
        List<Order> results = new ArrayList<>();
        for (Order o : shardDocs) if (o.customerId.equals(customerId)) results.add(o);
        return results;
    }
}

class Order { String id; String customerId; String status; Order(String id, String customerId, String status) { this.id = id; this.customerId = customerId; this.status = status; } }
```

How to run: `java RoutingLevel3.java`

`searchAllShards` mirrors a search with no routing hint: it must inspect every shard's contents, since without knowing the routing value in advance, Elasticsearch (or this simulation) can't know which shard holds the matching documents. `searchSingleShard` mirrors passing the routing value explicitly at search time (`elasticsearchOperations.search(query.setRoute("customer-A"), ...)`): it goes directly to the one shard `shardFor("customer-A")` resolves to, skipping every other shard, and still returns the exact same three matching orders.

## 6. Walkthrough

Execution starts in `main` for Level 3. Five orders are indexed into `shards`, each placed according to `shardFor(o.customerId)` — `customer-A`'s three orders (`order-1`, `order-2`, `order-4`) all land in the same shard, since they all hash `"customer-A"` to the identical shard number; `customer-B`'s and `customer-C`'s single orders land in whatever shards their own customer ids resolve to.

`searchAllShards(shards, "customer-A")` iterates `shards.values()` — every shard's document list, in turn — checking each order's `customerId` against `"customer-A"`. This touches every shard in the map (reported as `shards.size()`), regardless of the fact that only one of them actually contains any matches. It correctly collects all three of `customer-A`'s orders, but only after inspecting every shard's full contents.

`targetShard = shardFor("customer-A")` computes the exact shard number `customer-A`'s documents were routed to. `searchSingleShard(shards, targetShard, "customer-A")` then looks up *only* `shards.get(targetShard)` and filters within that single shard's document list — no other shard is ever touched. It returns the identical set of three orders as the unrouted search, but the work performed to get there was confined to one shard instead of all of them.

```
--- searching WITHOUT a routing hint (must fan out to ALL shards) ---
Shards queried: 3, results: [order-1, order-2, order-4]
--- searching WITH the routing value (only queries ONE shard) ---
Shards queried: 1 (shard ...), results: [order-1, order-2, order-4]
```

In real Elasticsearch, both searches return identical results — routing is a pure performance optimization, never a correctness one — but the routed search, via `query.setRoute("customer-A")` (or the repository/template equivalent), tells Elasticsearch's coordinating node to send the search request to only the one shard that routing guarantees holds every matching document, instead of fanning the request out to every shard in the index and merging their responses. For an index with many shards and a query pattern dominated by single-customer lookups, this is the difference between one shard's worth of work and every shard's worth of work, per search.

## 7. Gotchas & takeaways

> Gotcha: once `@Routing` is applied to an entity and documents are indexed with it, every subsequent `get`, `update`, or `delete` by id for that document must also supply the same routing value — Elasticsearch needs to know which shard to look on, and without the routing value, it has to fall back to checking every shard (or, for a plain `GET` by id without routing info, it may simply fail to find the document at all, since it doesn't know where to look).

> Gotcha: routing by a field with too few distinct values (like a boolean `isActive` flag) concentrates most documents onto very few shards, creating "hot" shards that carry disproportionate load — routing needs a key with enough cardinality (many distinct customers, not two boolean states) to actually spread data evenly while still co-locating what needs to be co-located.

- Custom routing (`@Routing` on an entity, or a routing value at index/search time) overrides Elasticsearch's default per-document-id shard assignment, letting related documents be deliberately co-located.
- The main benefit is search performance: a query scoped to a routing value only needs to check the single shard that value maps to, instead of fanning out across every shard in the index.
- Once applied, the same routing value must be supplied consistently for every subsequent get/update/delete operation on those documents, or Elasticsearch won't know where to find them.
- Choose a routing key with enough cardinality to distribute data reasonably evenly across shards, while still grouping the documents your dominant query pattern actually needs together.
