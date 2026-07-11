---
card: spring-data
gi: 125
slug: secondary-indexes
title: "Secondary indexes"
---

## 1. What it is

A **secondary index** in Spring Data Redis is an extra Redis set that tracks which entity ids have a particular field value, letting a `@RedisHash` repository answer derived query methods like `findByStatus("PENDING")` without scanning every entity. It's created automatically when a field is annotated `@Indexed`, and kept in sync on every `save`.

```java
@RedisHash("orders")
class Order {
    @Id String id;
    @Indexed String status; // maintains a secondary index automatically
    double total;
}

interface OrderRepository extends CrudRepository<Order, String> {
    List<Order> findByStatus(String status); // backed by the @Indexed field's secondary index
}
```

## 2. Why & when

The previous card's `findAll()` had to resolve every tracked id one by one — fine for "give me everything," but hopeless for "give me just the pending orders" if that means fetching every order and filtering in Java. A secondary index flips that: Redis maintains a set of "which ids currently have `status = PENDING`" as a side effect of every save, so a query for pending orders is a direct, fast set lookup instead of a full scan.

Reach for `@Indexed` when:

- A repository needs a derived query method (`findByStatus`, `findByCustomerId`) on a `@RedisHash` entity — without an index, Redis has no efficient way to answer "which entities have this field value" at all.
- The field has relatively low cardinality relative to the dataset (a status enum, a customer id, a category) — indexing a field where every value is unique (like a UUID) provides little benefit over just looking the entity up by that value directly.
- You want query performance that doesn't degrade as the total number of entities grows, the same reason a relational database index exists.

## 3. Core concept

```
 order-1: status=PENDING     order-2: status=SHIPPED     order-3: status=PENDING

 WITHOUT an index:  findByStatus("PENDING") -> scan every order's hash, check status field  (O(n))

 WITH @Indexed:      secondary index set "orders:status:PENDING" -> {order-1, order-3}
                      findByStatus("PENDING") -> SMEMBERS orders:status:PENDING  (O(1) lookup + O(k) fetch)

 On save: if status CHANGES, the old index entry is removed and the new one added --
   order-1 status PENDING -> SHIPPED:
     SREM orders:status:PENDING order-1
     SADD orders:status:SHIPPED order-1
```

Every save keeps the index sets in sync, so a query never has to re-derive "who currently has this value" from scratch.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Saving an order updates both its own hash and the secondary index set for its status value">
  <rect x="20" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">save(order, status=PENDING)</text>

  <rect x="280" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="355" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">hash "orders:1"</text>

  <rect x="470" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="545" y="40" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">index set</text>
  <text x="545" y="53" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">orders:status:PENDING</text>

  <line x1="220" y1="42" x2="275" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="220" y1="55" x2="465" y2="55" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <text x="320" y="120" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByStatus("PENDING") reads the index set directly -- no scan of every order needed</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

One `save` call maintains both the entity's own hash and whichever index sets its `@Indexed` fields belong to.

## 5. Runnable example

The scenario: querying orders by status without a full scan, evolving from a basic index set maintained alongside each save, to correctly updating the index when a field's value changes, to a repository exposing a derived `findByStatus` method backed entirely by the index.

### Level 1 — Basic

Model a secondary index set kept alongside the entity hashes, built at save time.

```java
import java.util.*;

public class SecondaryIndexLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        repo.save(new Order("1", "PENDING"));
        repo.save(new Order("2", "SHIPPED"));
        repo.save(new Order("3", "PENDING"));

        Set<String> pendingIds = repo.statusIndex.getOrDefault("PENDING", Set.of());
        System.out.println("Order ids with status=PENDING: " + pendingIds);
    }
}

class Order { String id; String status; Order(String id, String status) { this.id = id; this.status = status; } }

class OrderRepository {
    Map<String, Order> hashes = new HashMap<>();
    Map<String, Set<String>> statusIndex = new HashMap<>(); // "PENDING" -> {"1", "3"}, mirrors orders:status:<value>

    void save(Order order) {
        hashes.put(order.id, order);
        statusIndex.computeIfAbsent(order.status, k -> new LinkedHashSet<>()).add(order.id); // SADD orders:status:X id
    }
}
```

How to run: `java SecondaryIndexLevel1.java`

`save` writes the order into `hashes` (the entity's own hash) and *also* adds its id into `statusIndex` under its current status value, mirroring `SADD orders:status:PENDING 1`. Reading `statusIndex.get("PENDING")` directly returns `{"1", "3"}` without inspecting order `2` at all — the index already knows which orders match.

### Level 2 — Intermediate

Handle a status **change**: remove the id from its old index entry and add it to the new one, so the index never goes stale.

```java
import java.util.*;

public class SecondaryIndexLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        repo.save(new Order("1", "PENDING"));
        System.out.println("Before update -- PENDING: " + repo.statusIndex.getOrDefault("PENDING", Set.of()));

        repo.save(new Order("1", "SHIPPED")); // same id, DIFFERENT status -- the index must move the entry
        System.out.println("After update  -- PENDING: " + repo.statusIndex.getOrDefault("PENDING", Set.of()));
        System.out.println("After update  -- SHIPPED: " + repo.statusIndex.getOrDefault("SHIPPED", Set.of()));
    }
}

class Order { String id; String status; Order(String id, String status) { this.id = id; this.status = status; } }

class OrderRepository {
    Map<String, Order> hashes = new HashMap<>();
    Map<String, Set<String>> statusIndex = new HashMap<>();

    void save(Order order) {
        Order previous = hashes.get(order.id);
        if (previous != null && !previous.status.equals(order.status)) {
            // status CHANGED -- remove the stale index entry before adding the new one
            statusIndex.getOrDefault(previous.status, Set.of()).remove(order.id); // SREM orders:status:OLD id
        }
        hashes.put(order.id, order);
        statusIndex.computeIfAbsent(order.status, k -> new LinkedHashSet<>()).add(order.id); // SADD orders:status:NEW id
    }
}
```

How to run: `java SecondaryIndexLevel2.java`

The first `save` puts order `1` into the `PENDING` index. The second `save`, for the *same id* but a different status, compares against `previous.status` (`"PENDING"`), sees it changed to `"SHIPPED"`, and removes `1` from the `PENDING` set before adding it to the `SHIPPED` set — without this bookkeeping, order `1` would incorrectly still show up under `findByStatus("PENDING")` after being shipped.

### Level 3 — Advanced

Expose the index through a `findByStatus` method matching Spring Data's derived-query naming convention, and combine it with a second `@Indexed` field to show two independently-maintained indexes on the same entity.

```java
import java.util.*;
import java.util.stream.*;

public class SecondaryIndexLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "PENDING", "cust-A"));
        repo.save(new Order("2", "PENDING", "cust-B"));
        repo.save(new Order("3", "SHIPPED", "cust-A"));

        System.out.println("findByStatus(\"PENDING\"): " +
            repo.findByStatus("PENDING").stream().map(o -> o.id).collect(Collectors.toList()));
        System.out.println("findByCustomerId(\"cust-A\"): " +
            repo.findByCustomerId("cust-A").stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; String customerId; Order(String id, String status, String customerId) { this.id = id; this.status = status; this.customerId = customerId; } }

// Stands in for: interface OrderRepository extends CrudRepository<Order, String> { List<Order> findByStatus(String s); List<Order> findByCustomerId(String c); }
class OrderRepository {
    private final Map<String, Order> hashes = new HashMap<>();
    private final Map<String, Set<String>> statusIndex = new HashMap<>();     // @Indexed String status
    private final Map<String, Set<String>> customerIdIndex = new HashMap<>(); // @Indexed String customerId

    void save(Order order) {
        Order previous = hashes.get(order.id);
        if (previous != null) {
            if (!previous.status.equals(order.status))
                statusIndex.getOrDefault(previous.status, Set.of()).remove(order.id);
            if (!previous.customerId.equals(order.customerId))
                customerIdIndex.getOrDefault(previous.customerId, Set.of()).remove(order.id);
        }
        hashes.put(order.id, order);
        statusIndex.computeIfAbsent(order.status, k -> new LinkedHashSet<>()).add(order.id);
        customerIdIndex.computeIfAbsent(order.customerId, k -> new LinkedHashSet<>()).add(order.id);
    }

    List<Order> findByStatus(String status) {
        return statusIndex.getOrDefault(status, Set.of()).stream().map(hashes::get).collect(Collectors.toList());
    }
    List<Order> findByCustomerId(String customerId) {
        return customerIdIndex.getOrDefault(customerId, Set.of()).stream().map(hashes::get).collect(Collectors.toList());
    }
}
```

How to run: `java SecondaryIndexLevel3.java`

Two independent indexes, `statusIndex` and `customerIdIndex`, are maintained side by side on every `save`, exactly mirroring two separate `@Indexed` fields on the same `@RedisHash` entity. `findByStatus("PENDING")` returns orders `1` and `2` via a direct index lookup; `findByCustomerId("cust-A")` returns orders `1` and `3` via the other index — each query only ever touches its own index set, never scanning the full `hashes` map.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders are saved: `1` (`PENDING`, `cust-A`), `2` (`PENDING`, `cust-B`), `3` (`SHIPPED`, `cust-A`). For each, since `previous` is `null` on first save, no index cleanup runs — `save` simply adds the id into both `statusIndex` (keyed by that order's status) and `customerIdIndex` (keyed by that order's customer).

After all three saves, `statusIndex` looks like `{"PENDING": {"1", "2"}, "SHIPPED": {"3"}}`, and `customerIdIndex` looks like `{"cust-A": {"1", "3"}, "cust-B": {"2"}}`.

`repo.findByStatus("PENDING")` looks up `statusIndex.get("PENDING")`, getting `{"1", "2"}`, and maps each id through `hashes::get` to retrieve the full `Order` objects. `repo.findByCustomerId("cust-A")` does the equivalent lookup against `customerIdIndex.get("cust-A")`, getting `{"1", "3"}`.

```
findByStatus("PENDING"): [1, 2]
findByCustomerId("cust-A"): [1, 3]
```

In real Spring Data Redis, declaring `@Indexed String status` and `@Indexed String customerId` on the `Order` entity, combined with `List<Order> findByStatus(String status)` and `List<Order> findByCustomerId(String customerId)` on the repository interface, produces exactly this behavior — the framework generates the index-set maintenance on every save and the index-set lookup for every derived query method, all backed by real `SADD`/`SREM`/`SMEMBERS` commands against sets named after the indexed field and value.

## 7. Gotchas & takeaways

> Gotcha: only fields marked `@Indexed` get this treatment — a derived query method for a **non**-indexed field either fails to be created at application startup (Spring Data can't satisfy it) or, depending on configuration, falls back to a full scan, defeating the performance benefit entirely. Always add `@Indexed` to any field you plan to query by.

> Gotcha: indexing a very high-cardinality field (a field where nearly every value is unique, like a timestamp or a UUID) creates one index set per distinct value, each usually containing just one id — this adds bookkeeping overhead on every save with little query benefit, since you could just look the entity up directly instead.

- `@Indexed` on a `@RedisHash` entity field maintains a secondary index set automatically, keeping "which ids currently have this value" answerable in one direct lookup instead of a full scan.
- The index is kept in sync on every `save` — if an indexed field's value changes, the id is moved from the old index set to the new one.
- Derived query methods (`findByStatus`, `findByCustomerId`) on a Redis repository are only efficient when backed by an `@Indexed` field; unindexed derived queries don't have this guarantee.
- Index low-to-medium cardinality fields (status, category, foreign-key-style ids) — indexing near-unique fields adds overhead without much query benefit.
