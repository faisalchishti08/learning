---
card: spring-data
gi: 75
slug: domain-driven-design-aggregates-philosophy
title: "Domain-driven design & aggregates philosophy"
---

## 1. What it is

Spring Data JDBC is built around a deliberately narrower philosophy than Spring Data JPA: every entity is treated as (or as part of) a domain-driven-design **aggregate** — a cluster of objects that must be loaded, saved, and deleted as one atomic unit through a single **aggregate root**. Unlike JPA, there is no lazy loading, no persistence context, and no partial updates to nested objects — a save writes the *entire* aggregate, every time.

```java
class Order {                 // aggregate root
    @Id Long id;
    List<LineItem> lineItems;  // part of the SAME aggregate -- always loaded/saved together with Order
}
```

## 2. Why & when

Every JPA card in this section built on a rich object model: lazy associations, a persistence context tracking partial changes, entity graphs choosing what to fetch. Spring Data JDBC rejects that complexity on purpose — it maps much more directly onto SQL (no hidden lazy-loading queries, no proxy objects, no dirty-checking magic) in exchange for a stricter modeling discipline: you must think in terms of aggregates from the start, not retrofit them later.

Reach for Spring Data JDBC's aggregate-oriented model specifically when:

- You want the SQL a save/load operation performs to be fully predictable and visible in the code, without a persistence-context layer silently deciding what to flush or when to lazy-load.
- Your domain naturally decomposes into aggregates where "the whole thing changes together" is actually true — e.g., an order and its line items are always loaded and saved as a unit, never independently.
- You've been burned by JPA's lazy-loading pitfalls (`LazyInitializationException`, N+1 queries, unpredictable flush timing) and want a simpler, more explicit persistence model, accepting the tradeoff of always loading/saving whole aggregates.

## 3. Core concept

```
 JPA mental model:                       Spring Data JDBC mental model:
   Order <--lazy--> LineItem               Order (aggregate root)
   (independently loadable,                  |-- LineItem  (aggregate MEMBER)
    independently saveable,                  |-- LineItem  (aggregate MEMBER)
    persistence context tracks each)       -- ALWAYS loaded/saved/deleted as ONE unit
                                            -- NO independent LineItemRepository
                                            -- NO lazy loading, NO partial save
```

An aggregate root is the *only* entry point the rest of the application is allowed to use to reach its members — members have no independent existence from the application's perspective.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="An aggregate root and its members are loaded, saved, and deleted together as one indivisible unit">
  <rect x="200" y="20" width="240" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Order (aggregate root)</text>

  <rect x="60" y="100" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">LineItem (member)</text>

  <rect x="400" y="100" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">LineItem (member)</text>

  <rect x="150" y="30" width="340" height="1" fill="none"/>
  <line x1="270" y1="65" x2="180" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#dd)"/>
  <line x1="370" y1="65" x2="460" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#dd)"/>

  <rect x="30" y="150" width="580" height="18" rx="4" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="163" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">one repository.save(order) writes the root AND every member, together, every time</text>
  <defs><marker id="dd" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Members have no independent repository or lifecycle — the aggregate root is the sole gateway for loading, saving, and deleting the whole cluster.

## 5. Runnable example

The scenario: an order and its line items, evolving from a JPA-style independent-entities model highlighting the contrast, to an aggregate-oriented model where saving the root always rewrites every member, to a deletion showing the "whole unit" lifecycle in full.

### Level 1 — Basic

Model the JPA-style contrast first: two independently saveable/loadable "repositories," so the difference is visible before the aggregate model is introduced.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }
class LineItem { long id; long orderId; String description; LineItem(long id, long orderId, String d) { this.id = id; this.orderId = orderId; description = d; } }

// JPA-style: LineItem has its OWN independent repository and lifecycle.
class OrderRepositoryJpaStyle {
    Map<Long, Order> db = new HashMap<>();
    void save(Order o) { db.put(o.id, o); System.out.println("Saved JUST the order (status=" + o.status + ")"); }
}
class LineItemRepositoryJpaStyle {
    Map<Long, LineItem> db = new HashMap<>();
    void save(LineItem li) { db.put(li.id, li); System.out.println("Saved JUST one line item independently"); }
}

public class AggregateLevel1 {
    public static void main(String[] args) {
        OrderRepositoryJpaStyle orderRepo = new OrderRepositoryJpaStyle();
        LineItemRepositoryJpaStyle itemRepo = new LineItemRepositoryJpaStyle();

        orderRepo.save(new Order(1, "PENDING"));
        itemRepo.save(new LineItem(1, 1, "Widget")); // saved on its OWN, unrelated to the order save above
        System.out.println("Two independent repositories, two independent lifecycles.");
    }
}
```

How to run: `java AggregateLevel1.java`

`OrderRepositoryJpaStyle` and `LineItemRepositoryJpaStyle` are entirely independent — this is the JPA-style model where `LineItem` can be fetched, saved, or deleted on its own, without ever touching `Order`. Spring Data JDBC rejects this shape entirely for aggregate members.

### Level 2 — Intermediate

Replace both independent repositories with a single aggregate-oriented `OrderRepository` that always saves the `Order` root together with its `lineItems` — no separate `LineItemRepository` exists at all.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

class Order {
    long id; String status;
    List<LineItem> lineItems; // part of the aggregate -- no independent identity from the app's perspective
    Order(long id, String status, List<LineItem> lineItems) { this.id = id; this.status = status; this.lineItems = lineItems; }
}

// Spring Data JDBC style: ONE repository for the WHOLE aggregate. No LineItemRepository exists.
class OrderRepository {
    Map<Long, Order> db = new HashMap<>();

    void save(Order order) {
        db.put(order.id, order); // writes the root AND its line items together, as one unit
        System.out.println("Saved order " + order.id + " WITH all " + order.lineItems.size() + " line items, in one call");
    }

    Optional<Order> findById(long id) {
        return Optional.ofNullable(db.get(id)); // ALWAYS returns the order with its line items already populated
    }
}

public class AggregateLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        Order order = new Order(1, "PENDING", List.of(new LineItem("Widget"), new LineItem("Gadget")));
        repo.save(order); // ONE call persists the root + both line items

        Order found = repo.findById(1L).orElseThrow();
        System.out.println("Loaded order " + found.id + " with " + found.lineItems.size() + " line items (no separate query needed)");
    }
}
```

How to run: `java AggregateLevel2.java`

There is exactly one repository, `OrderRepository`, and one `save` call persists both the order and its line items together — there is no way to save a `LineItem` on its own, because in this model it has no independent existence; it only exists as part of the `Order` aggregate.

### Level 3 — Advanced

Show the full "whole unit" lifecycle: saving an aggregate with modified line items *replaces* the entire member collection (matching Spring Data JDBC's actual behavior — it deletes and re-inserts children on every save, rather than diffing them), and deleting the root deletes every member too.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

class Order {
    long id; String status;
    List<LineItem> lineItems;
    Order(long id, String status, List<LineItem> lineItems) { this.id = id; this.status = status; this.lineItems = lineItems; }
}

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();

    // Spring Data JDBC actually DELETES all existing line items for this order, then INSERTS the current ones --
    // it does not try to diff/patch the collection like a JPA persistence context would.
    void save(Order order) {
        System.out.println("  DELETE FROM line_item WHERE order_id = " + order.id);
        System.out.println("  INSERT INTO line_item ... (" + order.lineItems.size() + " rows)");
        db.put(order.id, order);
    }

    void deleteById(long id) {
        System.out.println("  DELETE FROM line_item WHERE order_id = " + id + " -- members deleted FIRST");
        System.out.println("  DELETE FROM orders WHERE id = " + id + " -- THEN the root");
        db.remove(id);
    }

    Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }
}

public class AggregateLevel3 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();

        Order order = new Order(1, "PENDING", new ArrayList<>(List.of(new LineItem("Widget"))));
        System.out.println("Initial save:");
        repo.save(order);

        // Modify the aggregate: add a line item, remove nothing explicit -- just reassign the list.
        order.lineItems = List.of(new LineItem("Widget"), new LineItem("Gadget"));
        System.out.println("Re-save after adding a line item:");
        repo.save(order); // deletes ALL existing line items for order 1, re-inserts BOTH current ones

        Order reloaded = repo.findById(1L).orElseThrow();
        System.out.println("Reloaded: " + reloaded.lineItems.size() + " line items");

        System.out.println("Deleting the whole aggregate:");
        repo.deleteById(1L); // members deleted first, then the root -- the whole unit disappears together
        System.out.println("Still findable? " + repo.findById(1L).isPresent());
    }
}
```

How to run: `java AggregateLevel3.java`

Every `save` call prints a `DELETE` of all existing line items followed by an `INSERT` of the current ones — even the very first save deletes nothing (there was nothing to delete yet), but the *second* save genuinely deletes the one existing `"Widget"` row and re-inserts both `"Widget"` and `"Gadget"` fresh. `deleteById` removes the members before the root, and afterward `findById` finds nothing at all — the whole aggregate, root and members alike, is gone together.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `order` is built with one line item (`"Widget"`), and `repo.save(order)` runs: it prints the simulated `DELETE FROM line_item WHERE order_id = 1` (a no-op here, since no rows exist yet) followed by `INSERT ... (1 rows)`, then stores `order` in `db`.

Next, `order.lineItems` is reassigned to a *new* list containing both `"Widget"` and `"Gadget"` — not an in-place addition to the old list, matching how a real Spring Data JDBC aggregate typically has its collection replaced wholesale rather than mutated. `repo.save(order)` runs again: this time the `DELETE FROM line_item WHERE order_id = 1` genuinely removes the previously-inserted `"Widget"` row, and the subsequent `INSERT ... (2 rows)` writes both `"Widget"` and `"Gadget"` back in as brand-new rows — Spring Data JDBC does not attempt to recognize that `"Widget"` already existed; it always deletes-then-reinserts the entire member collection.

`repo.findById(1L)` then confirms `reloaded.lineItems.size()` is `2`, matching the current, fully-replaced state. Finally, `repo.deleteById(1L)` runs: it prints the member `DELETE` first, then the root `DELETE`, and removes the entry from `db` — `repo.findById(1L).isPresent()` afterward is `false`, confirming the entire aggregate, root and members, is gone as one unit.

```
save(order, 1 lineItem)   -> DELETE (no-op) + INSERT 1 row
reassign lineItems (2 items)
save(order, 2 lineItems)  -> DELETE 1 existing row + INSERT 2 fresh rows
findById(1)               -> 2 line items
deleteById(1)             -> DELETE members, THEN DELETE root -> gone entirely
findById(1)                -> empty
```

In a real Spring Data JDBC repository, calling `orderRepository.save(order)` — regardless of whether `order` is new or already exists — triggers exactly this delete-then-reinsert pattern for every `@MappedCollection`-annotated member collection (line items, in this case): Spring Data JDBC has no persistence context to diff against, so it can't tell which line items are "the same" versus "new" — it simply guarantees the database ends up matching the in-memory aggregate's current state, at the cost of rewriting the entire member collection on every save, even when only one member actually changed.

## 7. Gotchas & takeaways

> Gotcha: because every save deletes and re-inserts the entire member collection, an aggregate with a large number of members (e.g., thousands of line items) pays that full delete+insert cost on *every* save, even if only one member's field changed — a cost JPA's dirty-checking-based partial updates would avoid; this is a deliberate simplicity/cost tradeoff, not an oversight.

- Spring Data JDBC has no lazy loading, no persistence context, and no dirty checking — every load/save is direct, explicit SQL with predictable behavior.
- An aggregate root is the *only* entry point for its members — there is no independent repository, no independent lifecycle, for anything that isn't itself a root.
- Saving an aggregate always rewrites its entire member collection (delete-then-reinsert), regardless of how much actually changed.
- Choose Spring Data JDBC over JPA when your domain genuinely decomposes into small, cohesive aggregates and you'd rather trade some efficiency for a simpler, more predictable persistence model.
