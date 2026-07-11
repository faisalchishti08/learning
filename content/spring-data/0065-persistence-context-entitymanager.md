---
card: spring-data
gi: 65
slug: persistence-context-entitymanager
title: "Persistence context & EntityManager"
---

## 1. What it is

The **persistence context** is JPA's first-level cache and change-tracking session, scoped to a single `EntityManager` (which, in Spring, usually lives for the duration of one transaction). Every entity loaded or saved through that `EntityManager` is tracked as "managed" — mutating a managed entity's fields doesn't require an explicit save call, because JPA detects the change and writes it (via **dirty checking**) when the transaction commits.

```java
@Transactional
void updateStatus(Long orderId, String newStatus) {
    Order order = entityManager.find(Order.class, orderId); // now "managed"
    order.setStatus(newStatus); // no explicit save() needed
} // on commit: JPA detects the change and issues an UPDATE
```

## 2. Why & when

Every JPA card so far (repositories, queries, projections, entity graphs) has quietly relied on the persistence context underneath. Understanding it explains two things that otherwise look like magic: why modifying a fetched entity's field persists without calling `save()`, and why the *same* entity fetched twice in one transaction returns the identical Java object (identity, not just equality) rather than two separate copies.

Reach for a direct understanding of the persistence context specifically when:

- You're puzzled why a field mutation on an entity you queried gets persisted even though you never called `repository.save(entity)` — dirty checking is the answer.
- You need to force pending changes to be written to the database *before* the transaction commits (e.g., before running a native query that needs to see them) — that's what `EntityManager.flush()` is for.
- You're debugging stale data within a single transaction, or need to detach an entity and discard unsaved in-memory changes — that's what `EntityManager.clear()`/`detach()` are for.

## 3. Core concept

```
 Transaction starts -> EntityManager opens a persistence context

 entityManager.find(Order.class, 1L)
   -> not in context yet -> SELECT issued -> entity becomes MANAGED, tracked

 order.setStatus("SHIPPED")
   -> just a plain field mutation -- NO query issued yet
   -> but the managed entity is now "dirty" (differs from its loaded snapshot)

 Transaction commits (or entityManager.flush() called)
   -> dirty checking compares managed entities to their snapshots
   -> UPDATE orders SET status = 'SHIPPED' WHERE id = 1  -- issued automatically
```

Managed entities are compared against their original loaded snapshot at flush/commit time — any difference becomes an automatic `UPDATE`.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="An entity becomes managed on load, is mutated in memory, then dirty-checked and flushed at commit">
  <rect x="10" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">find(Order, 1L)</text>

  <rect x="200" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="275" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">MANAGED</text>
  <text x="275" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">tracked + snapshot taken</text>

  <rect x="390" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="465" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">setStatus(...)</text>
  <text x="465" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">now "dirty"</text>

  <rect x="200" y="110" width="240" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">commit / flush()</text>
  <text x="320" y="147" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">dirty check -&gt; UPDATE issued</text>

  <line x1="160" y1="42" x2="195" y2="42" stroke="#8b949e" stroke-width="1.4" marker-end="url(#pc)"/>
  <line x1="350" y1="42" x2="385" y2="42" stroke="#8b949e" stroke-width="1.4" marker-end="url(#pc)"/>
  <line x1="465" y1="65" x2="360" y2="105" stroke="#8b949e" stroke-width="1.4" marker-end="url(#pc)"/>
  <defs><marker id="pc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Loading marks an entity managed and snapshots it; mutating it just changes memory; commit/flush is where the difference actually becomes a write.

## 5. Runnable example

The scenario: updating an order's status, evolving from a manual "managed entity" model showing dirty checking, to identity-map behavior (same object returned twice), to an explicit `flush()`/`clear()` sequence showing when writes actually happen.

### Level 1 — Basic

Model dirty checking directly: a mutation on a "managed" object is compared to its original snapshot only at commit time.

```java
import java.util.*;

class Order {
    long id; String status;
    Order(long id, String status) { this.id = id; this.status = status; }
    Order copy() { return new Order(id, status); } // used to take a snapshot
}

// Stands in for a real EntityManager's persistence context.
class SimplePersistenceContext {
    private final Map<Long, Order> managed = new HashMap<>();
    private final Map<Long, Order> snapshots = new HashMap<>();
    private final Map<Long, Order> database;

    SimplePersistenceContext(Map<Long, Order> database) { this.database = database; }

    Order find(long id) {
        Order o = managed.computeIfAbsent(id, k -> database.get(k).copy());
        snapshots.putIfAbsent(id, o.copy()); // remember the state as-loaded
        return o;
    }

    void commit() {
        for (Map.Entry<Long, Order> e : managed.entrySet()) {
            Order current = e.getValue();
            Order snapshot = snapshots.get(e.getKey());
            if (!current.status.equals(snapshot.status)) { // dirty check
                System.out.println("  UPDATE orders SET status = '" + current.status + "' WHERE id = " + e.getKey());
                database.put(e.getKey(), current.copy());
            }
        }
    }
}

public class PersistenceContextLevel1 {
    public static void main(String[] args) {
        Map<Long, Order> db = new HashMap<>(Map.of(1L, new Order(1, "PENDING")));
        SimplePersistenceContext ctx = new SimplePersistenceContext(db);

        Order order = ctx.find(1L);       // now managed
        order.status = "SHIPPED";          // just a field mutation, no query yet
        System.out.println("Before commit, DB still has: " + db.get(1L).status);
        ctx.commit();                       // dirty checking runs HERE
        System.out.println("After commit, DB has: " + db.get(1L).status);
    }
}
```

How to run: `java PersistenceContextLevel1.java`

`order.status = "SHIPPED"` never touches `db` directly — the database (`db`) still shows `"PENDING"` right after the mutation. Only `ctx.commit()` compares `current` against the remembered `snapshot`, finds a difference, and applies the change — mirroring exactly how a real `@Transactional` method with no explicit `save()` call still persists a mutation made through a managed entity.

### Level 2 — Intermediate

Demonstrate identity-map behavior: fetching the same row twice within one persistence context returns the *same* Java object, not two separate copies — so a mutation via either reference is visible via the other.

```java
import java.util.*;

class Order {
    long id; String status;
    Order(long id, String status) { this.id = id; this.status = status; }
    Order copy() { return new Order(id, status); }
}

class SimplePersistenceContext {
    private final Map<Long, Order> managed = new HashMap<>();
    private final Map<Long, Order> snapshots = new HashMap<>();
    private final Map<Long, Order> database;
    SimplePersistenceContext(Map<Long, Order> database) { this.database = database; }

    Order find(long id) {
        // computeIfAbsent: the SECOND find() for the same id returns the SAME instance already in `managed`
        Order o = managed.computeIfAbsent(id, k -> database.get(k).copy());
        snapshots.putIfAbsent(id, o.copy());
        return o;
    }

    void commit() {
        for (Map.Entry<Long, Order> e : managed.entrySet()) {
            Order current = e.getValue();
            Order snapshot = snapshots.get(e.getKey());
            if (!current.status.equals(snapshot.status)) {
                System.out.println("  UPDATE orders SET status = '" + current.status + "' WHERE id = " + e.getKey());
                database.put(e.getKey(), current.copy());
            }
        }
    }
}

public class PersistenceContextLevel2 {
    public static void main(String[] args) {
        Map<Long, Order> db = new HashMap<>(Map.of(1L, new Order(1, "PENDING")));
        SimplePersistenceContext ctx = new SimplePersistenceContext(db);

        Order first = ctx.find(1L);
        Order second = ctx.find(1L); // same row, same persistence context

        System.out.println("Same Java object? " + (first == second)); // identity, not just equality

        first.status = "SHIPPED"; // mutate via `first`
        System.out.println("Seen via `second`: " + second.status); // visible immediately, no reload needed

        ctx.commit();
        System.out.println("DB after commit: " + db.get(1L).status);
    }
}
```

How to run: `java PersistenceContextLevel2.java`

`first == second` prints `true` — within one persistence context, `find(1L)` called twice returns the identical managed instance, not two independent copies (this is the "identity map" property of the persistence context). Because of that, mutating `first.status` is instantly visible through `second` too, with no reload or synchronization needed — they are literally the same object in memory.

### Level 3 — Advanced

Add explicit `flush()` (write pending changes now, without ending the transaction) and `clear()` (detach everything, discarding the identity map and any un-flushed in-memory state), matching `EntityManager.flush()`/`clear()`.

```java
import java.util.*;

class Order {
    long id; String status;
    Order(long id, String status) { this.id = id; this.status = status; }
    Order copy() { return new Order(id, status); }
}

class SimplePersistenceContext {
    private Map<Long, Order> managed = new HashMap<>();
    private Map<Long, Order> snapshots = new HashMap<>();
    private final Map<Long, Order> database;
    SimplePersistenceContext(Map<Long, Order> database) { this.database = database; }

    Order find(long id) {
        Order o = managed.computeIfAbsent(id, k -> database.get(k).copy());
        snapshots.putIfAbsent(id, o.copy());
        return o;
    }

    // Writes pending changes to the database NOW, without ending the transaction.
    void flush() {
        for (Map.Entry<Long, Order> e : managed.entrySet()) {
            Order current = e.getValue();
            Order snapshot = snapshots.get(e.getKey());
            if (!current.status.equals(snapshot.status)) {
                System.out.println("  [flush] UPDATE orders SET status = '" + current.status + "' WHERE id = " + e.getKey());
                database.put(e.getKey(), current.copy());
                snapshots.put(e.getKey(), current.copy()); // snapshot re-taken after flush
            }
        }
    }

    // Detaches everything: identity map is discarded. Future find() calls re-fetch from the DB.
    void clear() {
        System.out.println("  [clear] persistence context cleared -- all entities detached");
        managed = new HashMap<>();
        snapshots = new HashMap<>();
    }
}

public class PersistenceContextLevel3 {
    public static void main(String[] args) {
        Map<Long, Order> db = new HashMap<>(Map.of(1L, new Order(1, "PENDING")));
        SimplePersistenceContext ctx = new SimplePersistenceContext(db);

        Order order = ctx.find(1L);
        order.status = "SHIPPED";
        System.out.println("Before flush, DB has: " + db.get(1L).status);

        ctx.flush(); // write it now, transaction still "open"
        System.out.println("After flush, DB has: " + db.get(1L).status);

        ctx.clear(); // detach -- order is no longer managed
        Order reloaded = ctx.find(1L); // fresh fetch, a NEW object, not the same as `order`
        System.out.println("Same object as before clear()? " + (order == reloaded));
        System.out.println("Reloaded status: " + reloaded.status);
    }
}
```

How to run: `java PersistenceContextLevel3.java`

`ctx.flush()` writes the pending `"SHIPPED"` change to `db` immediately, without needing a full `commit()` — exactly what `EntityManager.flush()` does mid-transaction. After `ctx.clear()`, calling `find(1L)` again produces a brand-new `Order` object (`order == reloaded` is `false`), because clearing the persistence context discarded the identity map entirely — the next `find()` has to re-fetch, standing in for what `EntityManager.clear()` does to a real Hibernate session.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `ctx.find(1L)` runs: `managed` is empty, so `computeIfAbsent` fetches from `db`, producing a fresh `Order` copy with `status="PENDING"`; this becomes the managed instance, and a snapshot (`status="PENDING"`) is stored alongside it.

Next, `order.status = "SHIPPED"` mutates the managed object directly — `db` is untouched at this point, confirmed by the printed line showing `db.get(1L).status` is still `"PENDING"`.

Then `ctx.flush()` runs: it compares the managed `order` (`"SHIPPED"`) against its snapshot (`"PENDING"`), finds a difference, prints the simulated `UPDATE`, writes `"SHIPPED"` into `db`, and re-takes the snapshot (now `"SHIPPED"`) so a second flush with no further changes would do nothing. The next printed line confirms `db.get(1L).status` is now `"SHIPPED"`.

Then `ctx.clear()` runs, discarding both `managed` and `snapshots` entirely — `order` still exists as a plain Java object in `main`'s local variable, but it's no longer tracked by `ctx` at all (detached). Calling `ctx.find(1L)` again has nothing to `computeIfAbsent` against, so it re-fetches from `db`, producing a brand-new `Order` instance. The final two printed lines confirm `order == reloaded` is `false`, and the reloaded status correctly reflects the flushed value, `"SHIPPED"`.

```
find(1L) -> managed{1: PENDING}, snapshot{1: PENDING}
mutate    -> managed{1: SHIPPED}, snapshot{1: PENDING}, db still PENDING
flush()   -> dirty! db{1: SHIPPED}, snapshot{1: SHIPPED}
clear()   -> managed={}, snapshot={}  (order detached, still in memory but untracked)
find(1L)  -> re-fetch from db -> NEW object, status=SHIPPED
```

In a real `@Transactional` Spring Data method, this maps directly onto `EntityManager` calls: `entityManager.find(Order.class, 1L)` loads and manages the entity, field mutations are tracked silently, `entityManager.flush()` forces an immediate `UPDATE` (useful right before a native query that must see the change), and `entityManager.clear()` detaches every managed entity in the persistence context (useful in a long-running batch job to avoid unbounded memory growth from an ever-growing identity map).

## 7. Gotchas & takeaways

> Gotcha: after `entityManager.clear()`, any previously-fetched entity reference becomes *detached* — further mutations on it are silently ignored (they will never be flushed), which is a common source of "my update didn't save" bugs in batch-processing code that clears the persistence context mid-loop without re-fetching.

- The persistence context is a per-`EntityManager` first-level cache and change tracker — it is what makes dirty checking and identity-map behavior possible.
- Managed entities are compared against their loaded snapshot at flush/commit time; any difference becomes an automatic `UPDATE` — no explicit `save()` call is required.
- Fetching the same row twice within one persistence context returns the *same* Java object, not two separate copies.
- `flush()` writes pending changes immediately without ending the transaction; `clear()` detaches everything, discarding the identity map — mutating a detached entity afterward has no effect.
