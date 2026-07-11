---
card: spring-data
gi: 124
slug: redis-repositories-redishash
title: "Redis Repositories (@RedisHash)"
---

## 1. What it is

`@RedisHash` marks a Java class as a Redis-backed entity, mapped to a Redis hash — one field per Java field — and lets you define a `CrudRepository<T, ID>` for it, exactly like Spring Data's other repository modules. Spring Data Redis generates the implementation, translating `save`/`findById`/`delete` into the `opsForHash()` operations from the previous card, without you writing them by hand.

```java
@RedisHash("orders")
class Order {
    @Id String id;
    String status;
    double total;
}

interface OrderRepository extends CrudRepository<Order, String> { }
```

## 2. Why & when

The previous two cards showed working with Redis structures directly through `RedisTemplate` — powerful, but low-level: every field read/write is a manual `opsForHash()` call. `@RedisHash` plus a repository interface brings the same generated-implementation convenience already seen with `JpaRepository`, `MongoRepository`, and `ReactiveCrudRepository` — you get `save`, `findById`, `findAll`, `delete`, and derived query methods, without writing the hash mapping yourself.

Reach for `@RedisHash` repositories when:

- Redis is your primary store (or a structured secondary store) for a genuine entity — not just a cache of ephemeral values — and you want familiar CRUD without hand-rolling `opsForHash()` calls for every field.
- You want derived query methods, similar to JPA/MongoDB repositories, backed by Redis's secondary indexing feature (the next card) — `findByStatus(String status)`, for example.
- You're already comfortable with the Spring Data repository pattern from other modules and want the same programming model, just backed by Redis instead of a relational or document database.

This is a different use case from `RedisTemplate`-based caching — `@RedisHash` entities are meant to be looked up and updated like normal domain objects, not just opaque cached blobs with a TTL.

## 3. Core concept

```
 @RedisHash("orders")
 class Order { @Id String id; String status; double total; }

 orderRepository.save(new Order("1", "PENDING", 50.0))
        |
        v
 HSET orders:1 status PENDING total 50.0     -- one Redis hash per entity instance
 SADD orders id:1                             -- index of all ids, so findAll() works

 orderRepository.findById("1")
        |
        v
 HGETALL orders:1  ->  reconstructed as an Order object
```

Each saved entity becomes one Redis hash, keyed by `<keyspace>:<id>` — `@RedisHash("orders")` plus `@Id` together determine that key.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="repository.save maps an Order object to a Redis hash under key orders:1, and an id set tracks all saved ids">
  <rect x="20" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">orderRepository.save(order)</text>

  <rect x="280" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="40" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">hash "orders:1"</text>
  <text x="360" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">status, total fields</text>

  <rect x="480" y="20" width="140" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="550" y="40" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">set "orders"</text>
  <text x="550" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">{1, 2, 3, ...}</text>

  <line x1="220" y1="42" x2="275" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="220" y1="55" x2="475" y2="55" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

One `save` call writes both the entity's own hash and updates the keyspace's id set, so `findAll()` knows what exists.

## 5. Runnable example

The scenario: an `Order` entity backed by `@RedisHash`, evolving from a basic repository doing save/findById through `opsForHash()`, to full CRUD including `findAll`/`delete` via the tracked id set, to a repository method resolving multiple entities by id at once, matching the batch-fetch pattern `findAllById` uses.

### Level 1 — Basic

Model `@RedisHash`'s mapping: an entity's fields become hash fields under a `<keyspace>:<id>` key.

```java
import java.util.*;

public class RedisHashLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "PENDING", 50.0));

        Order found = repo.findById("1");
        System.out.println("Found: id=" + found.id + ", status=" + found.status + ", total=" + found.total);

        System.out.println("Missing id: " + repo.findById("999"));
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

// Stands in for a generated CrudRepository<Order, String> backed by @RedisHash("orders").
class OrderRepository {
    private final Map<String, Map<String, String>> hashes = new HashMap<>(); // simulates Redis hashes

    void save(Order order) {
        String key = "orders:" + order.id; // <keyspace>:<id>, matching @RedisHash("orders") + @Id
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("status", order.status);
        fields.put("total", String.valueOf(order.total));
        hashes.put(key, fields); // HSET orders:1 status PENDING total 50.0
    }

    Order findById(String id) {
        Map<String, String> fields = hashes.get("orders:" + id); // HGETALL orders:1
        if (fields == null) return null;
        return new Order(id, fields.get("status"), Double.parseDouble(fields.get("total")));
    }
}
```

How to run: `java RedisHashLevel1.java`

`save` translates each `Order` field into a Redis hash field under key `"orders:1"`, mirroring `HSET orders:1 status PENDING total 50.0`. `findById` reverses that mapping, reading the hash back with `HGETALL`-equivalent logic and reconstructing an `Order` object — exactly the translation a generated `@RedisHash` repository performs automatically, without any of this mapping code being written by hand in a real application.

### Level 2 — Intermediate

Add `findAll`/`deleteById`, backed by a tracked set of ids — mirroring how `@RedisHash` repositories maintain a secondary "index" set of all ids in a keyspace so `findAll()` has something to iterate.

```java
import java.util.*;
import java.util.stream.*;

public class RedisHashLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "PENDING", 50.0));
        repo.save(new Order("2", "SHIPPED", 75.0));
        repo.save(new Order("3", "DELIVERED", 20.0));

        System.out.println("All orders: " + repo.findAll().size());

        repo.deleteById("2");
        System.out.println("After delete, all orders: " + repo.findAll().stream().map(o -> o.id).collect(Collectors.toList()));
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class OrderRepository {
    private final Map<String, Map<String, String>> hashes = new HashMap<>();
    private final Set<String> allIds = new LinkedHashSet<>(); // mirrors Redis's internal "orders" id-tracking set

    void save(Order order) {
        String key = "orders:" + order.id;
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("status", order.status);
        fields.put("total", String.valueOf(order.total));
        hashes.put(key, fields);
        allIds.add(order.id); // SADD orders <id> -- keeps the id index up to date
    }

    Order findById(String id) {
        Map<String, String> fields = hashes.get("orders:" + id);
        if (fields == null) return null;
        return new Order(id, fields.get("status"), Double.parseDouble(fields.get("total")));
    }

    List<Order> findAll() {
        return allIds.stream().map(this::findById).collect(Collectors.toList()); // one findById per tracked id
    }

    void deleteById(String id) {
        hashes.remove("orders:" + id); // DEL orders:1
        allIds.remove(id);              // SREM orders <id>
    }
}
```

How to run: `java RedisHashLevel2.java`

`allIds` mirrors the internal id set Spring Data Redis maintains automatically for every `@RedisHash` keyspace — `save` adds to it, `deleteById` removes from it, and `findAll` uses it as the list of ids to look up, since Redis has no native "list every hash matching this pattern" operation that's efficient at scale. After `deleteById("2")`, both the hash and its id entry are gone, so `findAll` correctly returns only orders `1` and `3`.

### Level 3 — Advanced

Add `findAllById`, resolving multiple entities in one call — mirroring `CrudRepository.findAllById(Iterable<ID> ids)`, useful for batch-loading a set of orders (from an event stream or a page of search results) without one call per id.

```java
import java.util.*;
import java.util.stream.*;

public class RedisHashLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order("1", "PENDING", 50.0));
        repo.save(new Order("2", "SHIPPED", 75.0));
        repo.save(new Order("3", "DELIVERED", 20.0));

        List<Order> batch = repo.findAllById(List.of("1", "3", "404")); // "404" doesn't exist
        System.out.println("Requested 3 ids, got " + batch.size() + " orders back:");
        for (Order o : batch) System.out.println("  " + o.id + " -> " + o.status);
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }

class OrderRepository {
    private final Map<String, Map<String, String>> hashes = new HashMap<>();
    private final Set<String> allIds = new LinkedHashSet<>();

    void save(Order order) {
        String key = "orders:" + order.id;
        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("status", order.status);
        fields.put("total", String.valueOf(order.total));
        hashes.put(key, fields);
        allIds.add(order.id);
    }

    Order findById(String id) {
        Map<String, String> fields = hashes.get("orders:" + id);
        if (fields == null) return null;
        return new Order(id, fields.get("status"), Double.parseDouble(fields.get("total")));
    }

    // Resolves several ids in one call -- skips any id that doesn't exist, rather than failing the whole batch.
    List<Order> findAllById(Iterable<String> ids) {
        List<Order> results = new ArrayList<>();
        for (String id : ids) {
            Order order = findById(id);
            if (order != null) results.add(order); // MISSING ids are silently skipped, matching CrudRepository semantics
        }
        return results;
    }
}
```

How to run: `java RedisHashLevel3.java`

`findAllById` loops over the requested ids, calling `findById` for each and silently skipping any that return `null` — this matches `CrudRepository.findAllById`'s real contract: it returns whatever subset of the requested entities actually exist, not an error, and not a `null`-padded list. Requesting `"1"`, `"3"`, and the nonexistent `"404"` correctly returns just two orders.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders (`1`, `2`, `3`) are saved, each writing a hash entry and adding to `allIds`.

`repo.findAllById(List.of("1", "3", "404"))` iterates the requested ids in order. For `"1"`, `findById` looks up `hashes.get("orders:1")`, finds it, and reconstructs an `Order`, which is added to `results`. For `"3"`, the same happens successfully. For `"404"`, `hashes.get("orders:404")` returns `null` since no such hash was ever saved, so `findById` returns `null`, and the `if (order != null)` check skips adding anything to `results` for that id — no exception, no filler entry, it's simply omitted.

`results` ends up containing two `Order` objects — `1` and `3` — even though three ids were requested. The final loop prints each one.

```
Requested 3 ids, got 2 orders back:
  1 -> PENDING
  3 -> DELIVERED
```

In real Spring Data Redis, `orderRepository.findAllById(List.of("1", "3", "404"))` performs this same lookup using `HGETALL` per id under the hood (Redis doesn't have a native "multi-hash-get" command the way it has `MGET` for plain string keys), and returns exactly the entities that exist — exactly the behavior modeled here, just generated automatically from the `CrudRepository<Order, String>` interface rather than hand-written.

## 7. Gotchas & takeaways

> Gotcha: `@RedisHash` entities are, by default, stored with **no expiration** — unlike a `RedisTemplate`-based cache entry with a TTL, a saved entity stays in Redis forever unless explicitly deleted (or given a `@TimeToLive` field, covered in the next card). Don't assume `@RedisHash` data cleans itself up the way cache entries do.

> Gotcha: `findAll()` on a large keyspace can be expensive — it requires resolving every tracked id individually (as this example shows), since Redis has no efficient native "give me every hash matching this pattern" scan for large datasets; it doesn't scale the way a relational `SELECT *` with an index might.

- `@RedisHash("keyspace")` plus `@Id` maps a Java entity to a Redis hash at key `keyspace:id`, and a `CrudRepository<T, ID>` interface for it gets `save`/`findById`/`findAll`/`delete` generated automatically.
- Spring Data Redis maintains an internal id set per keyspace to make `findAll()` and similar operations possible, since Redis itself doesn't offer an efficient "list all hashes" primitive.
- `findAllById` returns only the entities that actually exist for the requested ids, silently omitting any that don't — not an error, not a null-padded list.
- `@RedisHash` entities are meant for structured, addressable domain objects, not ephemeral cached values — pair with `@TimeToLive` (next card) if entries should expire automatically.
