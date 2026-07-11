---
card: spring-data
gi: 71
slug: hibernate-specific-features
title: "Hibernate-specific features"
---

## 1. What it is

Spring Data JPA is written against the portable JPA specification, but the JPA provider underneath (almost always Hibernate in a Spring Boot application) offers extra, non-portable features that go beyond what plain JPA guarantees — a second-level cache (`@Cacheable`/shared query cache across sessions, not just the per-transaction persistence context), batch-friendly fetching (`@BatchSize`), and Hibernate's own extended annotations for filtering, formulas, and multi-tenancy.

```java
@Entity
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
@BatchSize(size = 20)
class Order { ... }
```

## 2. Why & when

Every earlier JPA card in this section used the portable `jakarta.persistence.*` API — `@Entity`, `@OneToMany`, `EntityManager`. Hibernate-specific features live in `org.hibernate.annotations.*` and only work if Hibernate specifically is the JPA provider (true for the overwhelming majority of Spring Boot applications, but not guaranteed by the JPA spec itself).

Reach for Hibernate-specific features specifically when:

- Query volume against reference/lookup data is high enough that even the first-level persistence-context cache (transaction-scoped) isn't enough — Hibernate's second-level cache shares cached entities *across* transactions and sessions.
- You're hitting the N+1 problem on a `@ManyToOne` or lazy collection across *many different parent entities* (not just one, which `@EntityGraph` from an earlier card handles) — `@BatchSize` tells Hibernate to fetch several parents' lazy associations in one batched query instead of one query per parent.
- You need a feature with no portable JPA equivalent at all — e.g., `@Formula` (a computed, read-only column backed by a SQL expression) or Hibernate's soft-delete/filter annotations.

## 3. Core concept

```
 Persistence context (1st-level cache): scoped to ONE transaction/EntityManager
 Hibernate 2nd-level cache:              scoped ACROSS transactions/sessions

 Tx A: find(Product, 1L) -> DB hit, cached in 2nd-level cache
 Tx A ends.
 Tx B: find(Product, 1L) -> 2nd-level cache HIT -- no DB query at all!

 @BatchSize(size=20) on Order.lineItems:
   for (Order o : 30 orders) { access o.lineItems; }  -- LAZY collections
   -- WITHOUT @BatchSize: up to 30 separate queries (N+1)
   -- WITH @BatchSize(20): only 2 queries, each fetching up to 20 orders' lineItems at once
```

The second-level cache survives across transactions; `@BatchSize` groups multiple lazy-loads into fewer, larger queries.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="The second-level cache serves a later transaction without hitting the database, while BatchSize groups multiple lazy loads into fewer queries">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Tx A: find(Product,1)</text>
  <text x="110" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">DB hit, cached (2nd level)</text>

  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Tx B: find(Product,1)</text>
  <text x="320" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">cache hit, NO db query</text>

  <rect x="20" y="105" width="270" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">no @BatchSize: 30 orders</text>
  <text x="155" y="143" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; up to 30 lazy-load queries</text>

  <rect x="330" y="105" width="270" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="465" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@BatchSize(20): 30 orders</text>
  <text x="465" y="143" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; only 2 batched queries</text>

  <line x1="200" y1="45" x2="225" y2="45" stroke="#8b949e" stroke-width="1.3" marker-end="url(#hb)"/>
  <defs><marker id="hb" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Second-level caching skips repeat database hits across transactions; batch fetching groups many small lazy-loads into a few larger ones.

## 5. Runnable example

The scenario: fetching a reference `Product` repeatedly and lazily loading many orders' line items, evolving from an uncached baseline, to a simulated Hibernate second-level cache, to `@BatchSize`-style grouped lazy fetching.

### Level 1 — Basic

Model the baseline: every "transaction" that fetches the same product hits the database independently — no cross-transaction cache exists.

```java
import java.util.*;

class Product { long id; String name; Product(long id, String name) { this.id = id; this.name = name; } }

class ProductRepository {
    static int dbHits = 0;
    private final Map<Long, Product> db;
    ProductRepository(Map<Long, Product> db) { this.db = db; }

    Product find(long id) {
        dbHits++; // every call is a real database hit -- no cache at all
        return db.get(id);
    }
}

public class HibernateFeaturesLevel1 {
    public static void main(String[] args) {
        ProductRepository repo = new ProductRepository(new HashMap<>(Map.of(1L, new Product(1, "Widget"))));

        // Two SEPARATE "transactions" both fetch product 1.
        Product txA = repo.find(1L);
        Product txB = repo.find(1L);

        System.out.println("Tx A: " + txA.name + ", Tx B: " + txB.name);
        System.out.println("Total DB hits: " + ProductRepository.dbHits); // 2 -- no sharing across "transactions"
    }
}
```

How to run: `java HibernateFeaturesLevel1.java`

`dbHits` reaches 2 — every fetch of `Product` 1 is an independent database round trip, even though nothing about the product changed between the two calls. This is the gap Hibernate's second-level cache closes.

### Level 2 — Intermediate

Add a simulated second-level cache that survives across "transactions," serving the second fetch without touching the database.

```java
import java.util.*;

class Product { long id; String name; Product(long id, String name) { this.id = id; this.name = name; } }

// Stands in for Hibernate's second-level cache: shared ACROSS transactions, unlike the 1st-level persistence context.
class SecondLevelCache {
    private final Map<Long, Product> cache = new HashMap<>();
    Product getIfPresent(long id) { return cache.get(id); }
    void put(long id, Product p) { cache.put(id, p); }
}

class ProductRepository {
    static int dbHits = 0;
    private final Map<Long, Product> db;
    private final SecondLevelCache cache = new SecondLevelCache(); // @Cacheable(usage = READ_WRITE)
    ProductRepository(Map<Long, Product> db) { this.db = db; }

    Product find(long id) {
        Product cached = cache.getIfPresent(id);
        if (cached != null) return cached; // 2nd-level cache HIT -- no db query at all
        dbHits++;
        Product fromDb = db.get(id);
        cache.put(id, fromDb);
        return fromDb;
    }
}

public class HibernateFeaturesLevel2 {
    public static void main(String[] args) {
        ProductRepository repo = new ProductRepository(new HashMap<>(Map.of(1L, new Product(1, "Widget"))));

        Product txA = repo.find(1L); // Tx A: cache miss, hits DB, caches it
        Product txB = repo.find(1L); // Tx B: cache HIT -- no DB query

        System.out.println("Tx A: " + txA.name + ", Tx B: " + txB.name);
        System.out.println("Total DB hits: " + ProductRepository.dbHits); // just 1 now
    }
}
```

How to run: `java HibernateFeaturesLevel2.java`

`dbHits` reaches only 1 this time — `txB`'s fetch is served entirely from `SecondLevelCache`, standing in for how Hibernate's `@Cache`-annotated entity survives across separate transactions/sessions, unlike the transaction-scoped persistence context from the earlier card.

### Level 3 — Advanced

Add `@BatchSize`-style grouped lazy loading: instead of one query per parent entity when accessing a lazy collection, fetch several parents' collections together in one batched query.

```java
import java.util.*;
import java.util.stream.*;

class LineItem { String desc; LineItem(String d) { desc = d; } }
class Order {
    long id; List<LineItem> lineItems; // lazy until loaded
    Order(long id) { this.id = id; }
}

class OrderRepository {
    static int queryCount = 0;
    private final Map<Long, List<LineItem>> lineItemsByOrder;
    private final int batchSize;
    OrderRepository(Map<Long, List<LineItem>> lineItemsByOrder, int batchSize) {
        this.lineItemsByOrder = lineItemsByOrder;
        this.batchSize = batchSize; // @BatchSize(size = batchSize)
    }

    // Simulates Hibernate loading lazy lineItems for MULTIPLE orders in batches of `batchSize`,
    // instead of one query per order (which would be N+1 for N orders).
    void loadLineItemsBatched(List<Order> orders) {
        for (int i = 0; i < orders.size(); i += batchSize) {
            List<Order> batch = orders.subList(i, Math.min(i + batchSize, orders.size()));
            queryCount++; // ONE query fetches lineItems for the WHOLE batch
            for (Order o : batch) {
                o.lineItems = lineItemsByOrder.getOrDefault(o.id, List.of());
            }
        }
    }

    static int noBatchQueryCount(List<Order> orders, Map<Long, List<LineItem>> data) {
        int count = 0;
        for (Order o : orders) {
            count++; // one query PER order -- the N+1 baseline
            o.lineItems = data.getOrDefault(o.id, List.of());
        }
        return count;
    }
}

public class HibernateFeaturesLevel3 {
    public static void main(String[] args) {
        List<Order> orders = IntStream.rangeClosed(1, 30).mapToObj(Order::new).collect(Collectors.toList());
        Map<Long, List<LineItem>> data = new HashMap<>();
        for (Order o : orders) data.put(o.id, List.of(new LineItem("item-for-" + o.id)));

        int withoutBatch = OrderRepository.noBatchQueryCount(orders, data);
        System.out.println("Without @BatchSize: " + withoutBatch + " queries (N+1 for 30 orders)");

        OrderRepository repo = new OrderRepository(data, 10); // @BatchSize(size = 10)
        OrderRepository.queryCount = 0;
        repo.loadLineItemsBatched(orders);
        System.out.println("With @BatchSize(10): " + OrderRepository.queryCount + " queries for the same 30 orders");
    }
}
```

How to run: `java HibernateFeaturesLevel3.java`

Without batching, loading `lineItems` for 30 orders costs 30 queries, one per order. With `@BatchSize(10)` simulated, the same 30 orders are grouped into 3 batches of 10, costing only 3 queries total — each one fetching line items for up to 10 orders' worth of IDs in a single `WHERE order_id IN (...)` clause.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, 30 `Order` objects are created (IDs 1–30), each with a corresponding single-item `lineItems` list stored in `data`.

`OrderRepository.noBatchQueryCount(orders, data)` runs first: it loops over all 30 orders, incrementing `count` once *per order* before assigning `o.lineItems` — after the loop, `count` is 30, matching the classic N+1 pattern where each lazy collection access costs its own query.

Next, `repo.loadLineItemsBatched(orders)` runs with `batchSize = 10`. The outer loop steps through `orders` in strides of 10: the first iteration takes `orders.subList(0, 10)` (orders 1–10), increments `queryCount` once, then assigns `lineItems` for all 10 orders in that batch from the already-fetched `data` — standing in for Hibernate issuing one `SELECT ... WHERE order_id IN (1,2,...,10)` and distributing the results across all 10 managed `Order` entities. The same happens for orders 11–20 and 21–30, each costing one more increment. After the loop, `queryCount` is 3 — one per batch of 10, not one per order.

```
noBatchQueryCount:      order1 -> query#1, order2 -> query#2, ..., order30 -> query#30   (30 total)
loadLineItemsBatched:   [orders 1-10] -> query#1 (batched), [orders 11-20] -> query#2, [orders 21-30] -> query#3   (3 total)
```

In a real Hibernate-backed Spring Data JPA application, annotating `Order.lineItems` with `@BatchSize(size = 10)` causes Hibernate to detect, when the *first* lazy `lineItems` collection is accessed inside a loop over many managed `Order` entities, that up to 9 more currently-loaded-but-uninitialized `Order` entities exist in the same persistence context — and issues a single `SELECT * FROM line_items WHERE order_id IN (?, ?, ..., ?)` covering all of them at once, rather than one query per order as the collection is accessed one at a time.

## 7. Gotchas & takeaways

> Gotcha: relying on Hibernate-specific annotations (`org.hibernate.annotations.*`) ties the codebase to Hibernate specifically — switching JPA providers (rare in practice, but possible) would require reworking any code depending on these non-portable features, unlike code written purely against `jakarta.persistence.*`.

- The second-level cache is shared *across* transactions/sessions, unlike the transaction-scoped first-level persistence context — it needs explicit configuration (a cache provider, `@Cacheable`/`@Cache`) and is best suited to rarely-changing reference data.
- `@BatchSize` groups multiple lazy-load triggers into fewer, larger `IN (...)`-based queries, reducing (but not eliminating) the N+1 problem for collections accessed across many parent entities in a loop.
- These features live outside the portable JPA spec — they only work because Hibernate is the JPA provider, which is the common case but not guaranteed.
- Reach for Hibernate-specific features only after the portable JPA tools (entity graphs, query hints) don't fully solve the problem — they add real complexity and a dependency on Hibernate specifically.
