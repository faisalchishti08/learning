---
card: spring-integration
gi: 65
slug: jpa-support
title: "JPA support"
---

## 1. What it is

JPA support (`Jpa.inboundAdapter(...)`/`Jpa.outboundAdapter(...)`/`Jpa.outboundGateway(...)`) connects a flow to persistent entities through JPA's `EntityManager`, instead of raw SQL like the JDBC adapters (card 0064). Inbound, a JPQL query or a named query retrieves managed entities and turns each into a message; outbound, a message's payload — an entity object — is persisted, merged, or removed through the `EntityManager`.

## 2. Why & when

You reach for JPA support when the application already models its data as JPA entities and wants the integration flow to work at that same level of abstraction:

- **The domain is already entity-mapped** — if `Order` is a `@Entity` used throughout the application via a JPA repository, an inbound/outbound JDBC adapter would mean re-mapping rows to that same entity by hand; the JPA adapter reuses the existing mapping.
- **Persisting an object graph, not a single row** — JPA's cascade and relationship mapping means saving an `Order` can transparently persist its `OrderLine` children too, something a flat JDBC insert doesn't do without extra code.
- **A flow needs to poll for entities matching business criteria** — a JPQL query like "orders with no shipment record older than 1 hour" reads naturally as JPQL against the entity model, where the equivalent raw SQL would need to know the underlying table and join structure directly.

## 3. Core concept

Think of the JDBC adapter as talking to the database in the database's own language — table names, column names, raw rows. The JPA adapter instead talks to the *application's* language — entity classes, object references, cascades — and lets the persistence provider translate that into SQL behind the scenes. Reading through JPA is like asking a librarian for "the book about volcanoes" and getting a bound book handed to you; reading through JDBC is like being handed a stack of loose pages and doing the binding yourself.

```java
@Bean
public IntegrationFlow jpaInboundFlow(EntityManagerFactory emf) {
    return IntegrationFlow.from(
            Jpa.inboundAdapter(emf)
                .jpaQuery("from Order o where o.status = 'PENDING'")
                .expectSingleResult(false),
            e -> e.poller(Pollers.fixedDelay(5_000)))
        .handle((java.util.List<Order> orders, headers) -> orders.forEach(orderService::process))
        .get();
}
```

The JPQL query is written against the `Order` entity and its `status` field, not against any specific table or column name.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDBC adapter operates on raw SQL rows mapped by hand; JPA adapter operates on managed entity objects with the persistence provider handling the SQL translation" >
  <rect x="20" y="20" width="280" height="100" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JDBC adapter (card 0064)</text>
  <text x="35" y="45" fill="#e6edf3" font-size="8" font-family="monospace">SQL: SELECT * FROM orders</text>
  <text x="35" y="65" fill="#e6edf3" font-size="8" font-family="monospace">RowMapper -&gt; POJO (manual)</text>
  <text x="35" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">app owns the row-to-object mapping</text>

  <rect x="340" y="20" width="280" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JPA adapter</text>
  <text x="355" y="45" fill="#e6edf3" font-size="8" font-family="monospace">JPQL: from Order o where ...</text>
  <text x="355" y="65" fill="#79c0ff" font-size="8" font-family="monospace">EntityManager -&gt; managed entity</text>
  <text x="355" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">persistence provider owns the mapping</text>
</svg>

The JPA adapter speaks the application's entity model; the JPQL translation to SQL is the provider's job, not the flow's.

## 5. Runnable example

The scenario: polling for pending orders as entities and marking them processed, simulated with a plain in-memory entity list standing in for an `EntityManager` (no real database or persistence provider needed to demonstrate the adapter's object-level behavior), starting with a basic query-and-handle, then adding a merge-back step to persist status changes, then handling an optimistic-locking conflict.

### Level 1 — Basic

```java
// JpaAdapterDemo.java
import java.util.*;

public class JpaAdapterDemo {
    static class Order {
        int id; String status;
        Order(int id, String status) { this.id = id; this.status = status; }
    }

    // Stand-in for Jpa.inboundAdapter's JPQL query: "from Order o where o.status = 'PENDING'"
    static List<Order> queryPending(List<Order> entities) {
        return entities.stream().filter(o -> o.status.equals("PENDING")).toList();
    }

    public static void main(String[] args) {
        List<Order> entities = List.of(new Order(1, "PENDING"), new Order(2, "SHIPPED"));
        for (Order o : queryPending(entities)) {
            System.out.println("Processing order entity " + o.id);
        }
    }
}
```

How to run: `java JpaAdapterDemo.java`. Expected output: `Processing order entity 1` — only the entity matching the JPQL-style filter is picked up.

### Level 2 — Intermediate

```java
// JpaAdapterDemo.java
import java.util.*;

public class JpaAdapterDemo {
    static class Order {
        int id; String status; int version = 0;
        Order(int id, String status) { this.id = id; this.status = status; }
    }

    static List<Order> queryPending(List<Order> entities) {
        return entities.stream().filter(o -> o.status.equals("PENDING")).toList();
    }

    // Real-world concern: after processing, the outbound side must merge the changed entity
    // back through the "EntityManager" (here, just bumping its version to model optimistic locking).
    static void mergeBack(Order o, String newStatus) {
        o.status = newStatus;
        o.version++;
        System.out.println("Merged order " + o.id + " -> status=" + o.status + ", version=" + o.version);
    }

    public static void main(String[] args) {
        List<Order> entities = new ArrayList<>(List.of(new Order(1, "PENDING")));

        for (Order o : queryPending(entities)) {
            mergeBack(o, "PROCESSING");
        }
    }
}
```

How to run: `java JpaAdapterDemo.java`. Expected output: `Merged order 1 -> status=PROCESSING, version=1` — the entity's state changes and its version increments, mirroring JPA's optimistic-locking `@Version` column bumping on every merge.

### Level 3 — Advanced

```java
// JpaAdapterDemo.java
import java.util.*;

public class JpaAdapterDemo {
    static class Order {
        int id; String status; int version;
        Order(int id, String status, int version) { this.id = id; this.status = status; this.version = version; }
    }

    static class OptimisticLockException extends RuntimeException {
        OptimisticLockException(String msg) { super(msg); }
    }

    // Simulates a shared entity table where another transaction may have already bumped the version.
    static void mergeBack(Map<Integer, Order> store, Order detachedCopy, String newStatus) {
        Order current = store.get(detachedCopy.id);
        if (current.version != detachedCopy.version) {
            // Production concern: someone else updated this row since it was read (JPA's
            // OptimisticLockException equivalent) -- the flow must not blindly overwrite it.
            throw new OptimisticLockException(
                "order " + detachedCopy.id + " was modified concurrently (expected version "
                + detachedCopy.version + ", found " + current.version + ")");
        }
        current.status = newStatus;
        current.version++;
        System.out.println("Merged order " + current.id + " -> status=" + current.status + ", version=" + current.version);
    }

    public static void main(String[] args) {
        Map<Integer, Order> store = new HashMap<>();
        store.put(1, new Order(1, "PENDING", 0));

        Order detachedCopy = new Order(1, "PENDING", 0); // what the flow read earlier in the poll

        store.get(1).version = 1; // simulate a concurrent update by another process
        store.get(1).status = "CANCELLED";

        try {
            mergeBack(store, detachedCopy, "PROCESSING");
        } catch (OptimisticLockException ex) {
            System.out.println("Conflict detected, skipping stale update: " + ex.getMessage());
        }
    }
}
```

How to run: `java JpaAdapterDemo.java`. Expected output: a `Conflict detected, skipping stale update: ...` message — the version mismatch is caught before the flow overwrites a concurrently modified row, exactly the protection a real `@Version`-annotated JPA entity gives for free when merged through an `EntityManager`.

## 6. Walkthrough

Trace one poll-and-process cycle from JPQL query to persisted result.

1. **Poller fires**: `Jpa.inboundAdapter`'s poller executes the configured JPQL query — `from Order o where o.status = 'PENDING'` — through the `EntityManager`.
2. **Entity retrieval**: the persistence provider translates the JPQL into SQL, executes it, and hydrates the results as managed (or, depending on configuration, detached) `Order` entity instances — full objects, not raw column values.
3. **Message emission**: each entity (or the whole list, depending on `expectSingleResult`) becomes the payload of a message flowing to the next handler.
4. **Business processing**: the handler mutates the entity's state in memory — for instance, setting `status` to `"PROCESSING"`.
5. **Outbound merge**: a `Jpa.outboundAdapter` further down the flow takes the modified entity and calls the equivalent of `entityManager.merge(order)`, persisting the change. If another transaction modified the same row in the meantime and the entity carries a `@Version` field, this merge throws an optimistic-locking exception rather than silently overwriting the concurrent change.
6. **Conflict handling**: the flow catches that exception (as in Level 3) and decides what to do — retry on the next poll, log and skip, or route to an error channel — rather than letting a stale write corrupt newer data.

```
poller tick
  -> JPQL "from Order o where o.status='PENDING'"
    -> EntityManager -> managed Order entities
      -> Message per entity -> handler mutates status
        -> outbound merge
           version matches -> persisted
           version stale   -> OptimisticLockException -> handled, not overwritten
```

## 7. Gotchas & takeaways

> **Gotcha:** entities returned by an inbound JPA adapter are often detached from the persistence context by the time they reach a downstream handler running outside the original transaction — mutating them does nothing until they're explicitly merged back through an outbound JPA adapter or gateway; a flow that forgets the merge step silently loses its changes.

- JPQL queries are validated against the entity model at first use, not at flow-definition time — a typo in a field name surfaces as a runtime exception on the first poll, not a compile error.
- Cascading relationships (e.g., saving an `Order` cascades to its `OrderLine`s) is powerful but means an outbound adapter can persist far more than the single entity it appears to touch — know the entity's cascade configuration before wiring it into a flow.
- Optimistic-locking conflicts (`@Version` mismatches) are a normal, expected outcome under concurrent access, not a rare edge case — the flow should have a defined retry-or-skip policy rather than treating every conflict as a fatal error.
- Prefer the JPA adapter over the JDBC adapter (card 0064) when the domain is already entity-mapped elsewhere in the application; reach for JDBC when working with legacy tables that have no natural entity shape.
