---
card: system-design
gi: 84
slug: polyglot-persistence-in-one-system
title: Polyglot persistence in one system
---

## 1. What it is

**Polyglot persistence** is the practice of using more than one type of database within a single system, deliberately, choosing a different store for each part of the data based on its own specific access pattern and consistency needs — rather than forcing every piece of data into one general-purpose database.

## 2. Why & when

The previous tutorial's decision checklist rarely produces the same answer for every kind of data in a real application: a payments record wants ACID and relational structure; a product's search index wants a store built for full-text search; a session wants a fast key-value cache; a "recommended for you" feature wants a graph traversal. Polyglot persistence is simply the acknowledgment that trying to serve all of these well from one database usually means compromising on all of them, whereas dedicating the right store to each need serves each one well. Use it once a system's different data types have genuinely different needs — not as a default for every project, since each additional store adds real operational cost.

## 3. Core concept

**A realistic e-commerce example, split by need:**
- **Relational database (PostgreSQL/MySQL):** orders, payments, inventory counts — data needing ACID transactions and well-defined relationships.
- **Document store (MongoDB):** product catalog entries — flexible, self-contained, varying attributes per product category.
- **Key-value store / cache (Redis):** shopping cart sessions, rate-limit counters — fast, ephemeral, simple lookups.
- **Search index (Elasticsearch):** full-text product search — a fundamentally different query shape (relevance-ranked text matching) than any of the above stores are built for.
- **Graph database (Neo4j):** "customers who bought this also bought" recommendations — relationship-traversal queries.

**The cost this trades for — keeping data in sync across stores:** the same product might need a row in the relational inventory table, a document in the catalog store, and an entry in the search index. A write to one of them (a price change) must propagate to the others — usually via an event published after the primary write, consumed by the services that maintain each secondary store's copy.

**Why this is not the same as picking "the best" single database:** no single database is simultaneously the best choice for ACID transactions, flexible documents, full-text search, and graph traversal — each of the specialized stores above is meaningfully better at its one job than a general-purpose database would be at all of them combined. Polyglot persistence accepts more moving parts in exchange for each part being well suited to its actual job.

## 4. Diagram

```
                 Order placed (write path)
                          |
                          v
              PostgreSQL: orders, payments, inventory   (ACID, source of truth for the transaction)
                          |
                publishes "OrderPlaced" event
                          |
        +-----------------+-----------------+
        v                                    v
  Redis: decrement rate-limit         Search index / catalog document
  counter for this customer           updated to reflect new stock level
  (fast, ephemeral)                   (eventually consistent with PostgreSQL)

  Read path for "search for a product": goes DIRECTLY to the search index,
  never touches PostgreSQL at all - the right store for that specific query.
```
*Caption: one write can fan out to several specialized stores via events; each store is read directly for the query shape it is built for.*

## 5. Runnable example

**Level 1 — Basic.** Model three specialized stores (relational-style, document-style, key-value cache) as separate structures.

**Level 2 — Event-driven fan-out.** A single "place order" operation publishes an event that updates the secondary stores.

**Level 3 — Reading from the right store per query.** Show each query type going directly to its purpose-built store, never a generic one.

```java
// PolyglotPersistence.java
import java.util.*;

public class PolyglotPersistence {

    // "PostgreSQL" - the relational source of truth for orders and inventory.
    record Order(String id, String productId, int qty) {}
    static final List<Order> relationalOrders = new ArrayList<>();
    static final Map<String, Integer> relationalInventory = new HashMap<>();

    // "MongoDB" - a document store for the product catalog, updated via events.
    record CatalogEntry(String productId, String name, int stockLevel) {}
    static final Map<String, CatalogEntry> documentCatalog = new HashMap<>();

    // "Redis" - a key-value cache for rate limiting.
    static final Map<String, Integer> rateLimitCounters = new HashMap<>();

    // Simulated event bus: the relational write publishes; other stores subscribe and react.
    static void publishOrderPlaced(String customerId, String productId, int qty) {
        // subscriber 1: update the document catalog's stock level (eventually consistent copy)
        CatalogEntry entry = documentCatalog.get(productId);
        documentCatalog.put(productId, new CatalogEntry(entry.productId(), entry.name(), entry.stockLevel() - qty));

        // subscriber 2: decrement this customer's rate-limit counter in the cache
        rateLimitCounters.merge(customerId, -1, Integer::sum);
    }

    static void placeOrder(String customerId, String productId, int qty) {
        relationalOrders.add(new Order("order-" + relationalOrders.size(), productId, qty)); // ACID write, source of truth
        relationalInventory.merge(productId, -qty, Integer::sum);
        publishOrderPlaced(customerId, productId, qty); // fan out to the other specialized stores
    }

    public static void main(String[] args) {
        relationalInventory.put("sku1", 50);
        documentCatalog.put("sku1", new CatalogEntry("sku1", "Wireless Mouse", 50));
        rateLimitCounters.put("cust-42", 10);

        placeOrder("cust-42", "sku1", 3);

        // Level 3: each read goes DIRECTLY to the store built for that query shape.
        System.out.println("read from RELATIONAL store (source of truth for orders): " + relationalOrders);
        System.out.println("read from RELATIONAL store (source of truth for inventory count): " + relationalInventory.get("sku1"));
        System.out.println("read from DOCUMENT store (catalog display, eventually consistent copy): " + documentCatalog.get("sku1"));
        System.out.println("read from KEY-VALUE cache (rate limit remaining): " + rateLimitCounters.get("cust-42"));
    }
}
```

**How to run:** save as `PolyglotPersistence.java`, then run `java PolyglotPersistence.java`.

## 6. Walkthrough

1. `placeOrder` writes the order and decrements inventory in `relationalOrders` / `relationalInventory` first — modeling the ACID-backed relational write that is the source of truth for the transaction itself.
2. `publishOrderPlaced` is called immediately after, modeling an event fired once the primary write succeeds; it updates `documentCatalog`'s stock level and decrements `rateLimitCounters` — two entirely separate stores, each updated because they subscribed to this event.
3. Reading `relationalOrders` and `relationalInventory` afterward shows the authoritative, immediately consistent state — one order recorded, inventory at `47`.
4. Reading `documentCatalog.get("sku1")` shows its `stockLevel` also updated to `47` — but only because the event fan-out explicitly propagated it; if that propagation step were skipped or delayed, this copy would be stale, exactly the eventual-consistency trade polyglot persistence accepts for its secondary stores.
5. Reading `rateLimitCounters.get("cust-42")` shows `9`, confirming the key-value cache was also updated by the same event — three different stores, one for orders, one for catalog display, one for rate limiting, each read directly for its own purpose rather than routed through a single generic database.

## 7. Gotchas & takeaways

> Gotcha: every additional specialized store is one more thing that can fall out of sync, one more system to operate and monitor, and one more place a bug in the event-propagation path can cause silent staleness — polyglot persistence should be adopted incrementally, for data types that genuinely need it, not applied as an architecture pattern for its own sake.

- Different data types within one system genuinely can have very different needs; using one specialized store per need often serves each need better than any single general-purpose database could.
- The direct cost is synchronization: every store beyond the primary source of truth needs an explicit, monitored propagation path, and must be understood as eventually (not immediately) consistent.
- Related concepts: [When to choose SQL vs NoSQL](0083-when-to-choose-sql-vs-nosql.md) (the per-data-type decision that leads to this architecture), [Cache invalidation strategies](0051-cache-invalidation-strategies.md) (the event-based propagation pattern used to keep secondary stores current).
