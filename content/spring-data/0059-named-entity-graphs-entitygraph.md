---
card: spring-data
gi: 59
slug: named-entity-graphs-entitygraph
title: "Named entity graphs (@EntityGraph)"
---

## 1. What it is

`@EntityGraph` tells Spring Data JPA which lazy associations to eagerly fetch for a specific repository method call, without changing the entity's default fetch type globally. A **named** entity graph is declared once on the entity with `@NamedEntityGraph`, then referenced by name from `@EntityGraph(value = "...")` on any repository method that needs it.

```java
@Entity
@NamedEntityGraph(name = "Order.withLineItems", attributeNodes = @NamedAttributeNode("lineItems"))
class Order { @OneToMany List<LineItem> lineItems; /* ... */ }

@EntityGraph(value = "Order.withLineItems")
List<Order> findByStatus(String status);
```

## 2. Why & when

This directly follows from the JPQL and Specifications cards, which both mentioned lazy associations in passing — `@EntityGraph` is the tool that decides, per query, whether a lazy `@OneToMany`/`@ManyToOne` gets fetched eagerly for that one call. Without it, you're stuck choosing one fetch strategy (`EAGER` or `LAZY`) for the whole entity forever, even though different call sites have different needs.

Reach for `@EntityGraph` specifically when:

- One method needs an association loaded immediately (e.g., an order detail page needing `lineItems`) while another method on the same entity does not (e.g., an order list page that only needs `id`/`total`) — a single global fetch type cannot satisfy both efficiently.
- You're seeing the N+1 select problem: a `LAZY` association triggers one extra query per row when accessed in a loop, and you want it joined into the original query instead.
- You want the fetch behavior declared once, by name, and reused across multiple repository methods, rather than duplicating a JPQL `JOIN FETCH` clause in every query that needs the same associations.

## 3. Core concept

```
 @Entity
 @NamedEntityGraph(name = "Order.withLineItems",
                    attributeNodes = @NamedAttributeNode("lineItems"))
 class Order { ... @OneToMany(fetch = LAZY) List<LineItem> lineItems; }

 Without @EntityGraph:            With @EntityGraph(value="Order.withLineItems"):
   SELECT * FROM orders             SELECT * FROM orders o
   -- lineItems NOT loaded          LEFT JOIN line_items li ON li.order_id = o.id
   -- accessing it -> extra query   -- lineItems loaded in the SAME query
```

The named graph is metadata attached to the entity once; any repository method can opt in to it by name, without redeclaring which fields to fetch.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Two repository methods use the same named entity graph to control fetching per call">
  <rect x="230" y="15" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@NamedEntityGraph "Order.withLineItems"</text>

  <rect x="30" y="100" width="220" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="122" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">findDetailById(id)</text>
  <text x="140" y="138" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">@EntityGraph(...) -&gt; JOIN FETCH</text>

  <rect x="390" y="100" width="220" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="500" y="122" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">findByStatus(status)</text>
  <text x="500" y="138" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">no @EntityGraph -&gt; lazy</text>

  <line x1="300" y1="60" x2="150" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#eg)"/>
  <line x1="500" y1="60" x2="500" y2="95" stroke="#8b949e" stroke-width="1.3" stroke-dasharray="4,3"/>
  <defs><marker id="eg" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same named graph is opted into by one method and skipped by another — fetch strategy is chosen per call site, not globally on the entity.

## 5. Runnable example

The scenario: an order/line-item repository, evolving from a lazy-by-default model showing the N+1 problem, to an entity-graph-driven eager fetch for a single query, to two methods on the same entity choosing different fetch behavior.

### Level 1 — Basic

Model the N+1 problem directly: a lazy association that triggers one extra "query" per access when looped over.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

class Order {
    long id; double total;
    List<LineItem> lineItems; // simulates a LAZY @OneToMany: null until "loaded"
    Order(long id, double total) { this.id = id; this.total = total; }
}

// Simulates a repository backed by a database: each lineItems access is a separate query.
class OrderRepository {
    static int queryCount = 0;
    private final Map<Long, List<LineItem>> lineItemsByOrder;
    OrderRepository(Map<Long, List<LineItem>> lineItemsByOrder) { this.lineItemsByOrder = lineItemsByOrder; }

    List<Order> findByStatusLazy(List<Order> all) {
        queryCount++; // one query for the orders themselves
        return all;
    }

    List<LineItem> loadLineItems(long orderId) {
        queryCount++; // ANOTHER query, triggered lazily per order
        return lineItemsByOrder.getOrDefault(orderId, List.of());
    }
}

public class EntityGraphLevel1 {
    public static void main(String[] args) {
        List<Order> orders = List.of(new Order(1, 50), new Order(2, 150), new Order(3, 200));
        Map<Long, List<LineItem>> data = Map.of(
            1L, List.of(new LineItem("Widget")),
            2L, List.of(new LineItem("Gadget"), new LineItem("Gizmo")),
            3L, List.of(new LineItem("Sprocket"))
        );
        OrderRepository repo = new OrderRepository(data);

        List<Order> found = repo.findByStatusLazy(orders);
        for (Order o : found) {
            o.lineItems = repo.loadLineItems(o.id); // N+1: one extra query PER order
            System.out.println("Order " + o.id + " has " + o.lineItems.size() + " line items");
        }
        System.out.println("Total queries: " + OrderRepository.queryCount); // 1 + N
    }
}
```

How to run: `java EntityGraphLevel1.java`

`queryCount` reaches 4: one query for the order list, plus one more *per order* to lazily fetch its `lineItems` — the classic N+1 problem a `LAZY` association causes the moment you access it inside a loop.

### Level 2 — Intermediate

Introduce a named-entity-graph-driven method that fetches `lineItems` in the *same* query as the orders, cutting the query count to one regardless of how many orders there are.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

class Order {
    long id; double total; List<LineItem> lineItems;
    Order(long id, double total, List<LineItem> lineItems) { this.id = id; this.total = total; this.lineItems = lineItems; }
}

class OrderRepository {
    static int queryCount = 0;
    private final List<Order> allWithLineItems;
    OrderRepository(List<Order> allWithLineItems) { this.allWithLineItems = allWithLineItems; }

    // @EntityGraph(value = "Order.withLineItems")
    // List<Order> findAllWithLineItems();
    List<Order> findAllWithLineItems() {
        queryCount++; // ONE query: JOIN FETCH pulls lineItems in too
        return allWithLineItems;
    }
}

public class EntityGraphLevel2 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order(1, 50, List.of(new LineItem("Widget"))),
            new Order(2, 150, List.of(new LineItem("Gadget"), new LineItem("Gizmo"))),
            new Order(3, 200, List.of(new LineItem("Sprocket")))
        );
        OrderRepository repo = new OrderRepository(orders);

        List<Order> found = repo.findAllWithLineItems(); // lineItems already populated
        for (Order o : found) {
            System.out.println("Order " + o.id + " has " + o.lineItems.size() + " line items");
        }
        System.out.println("Total queries: " + OrderRepository.queryCount); // just 1
    }
}
```

How to run: `java EntityGraphLevel2.java`

`findAllWithLineItems` stands in for a repository method annotated `@EntityGraph(value = "Order.withLineItems")`: JPA generates one `SELECT ... FROM orders o LEFT JOIN line_items li ON ...` that brings back both the orders and their line items together, so `queryCount` stays at 1 no matter how many orders are returned — the N+1 pattern from Level 1 is gone.

### Level 3 — Advanced

Put both methods on the same repository — one lazy, one entity-graph-driven — so a single entity can serve a lightweight list view and a detail view without ever changing its default fetch type.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

class Order {
    long id; double total; List<LineItem> lineItems; // null == "not yet fetched"
    Order(long id, double total) { this.id = id; this.total = total; }
}

class OrderRepository {
    static int queryCount = 0;
    private final List<Order> orders;
    private final Map<Long, List<LineItem>> lineItemsByOrder;
    OrderRepository(List<Order> orders, Map<Long, List<LineItem>> lineItemsByOrder) {
        this.orders = orders; this.lineItemsByOrder = lineItemsByOrder;
    }

    // No @EntityGraph: lightweight list view. lineItems stays null/unfetched.
    List<Order> findAllSummary() {
        queryCount++;
        return orders;
    }

    // @EntityGraph(value = "Order.withLineItems"): detail view, single order, eager fetch.
    Optional<Order> findDetailById(long id) {
        queryCount++;
        return orders.stream().filter(o -> o.id == id).findFirst().map(o -> {
            Order copy = new Order(o.id, o.total);
            copy.lineItems = lineItemsByOrder.getOrDefault(id, List.of()); // joined in, same query
            return copy;
        });
    }

    List<LineItem> loadLineItemsLazily(long id) {
        queryCount++;
        return lineItemsByOrder.getOrDefault(id, List.of());
    }
}

public class EntityGraphLevel3 {
    public static void main(String[] args) {
        List<Order> orders = List.of(new Order(1, 50), new Order(2, 150));
        Map<Long, List<LineItem>> data = Map.of(
            1L, List.of(new LineItem("Widget")),
            2L, List.of(new LineItem("Gadget"), new LineItem("Gizmo"))
        );
        OrderRepository repo = new OrderRepository(orders, data);

        // List view: cheap, no line items touched.
        List<Order> summary = repo.findAllSummary();
        System.out.println("Summary count: " + summary.size() + " (queries so far: " + OrderRepository.queryCount + ")");

        // Detail view for order 2: entity graph fetches lineItems in the same call.
        Order detail = repo.findDetailById(2).orElseThrow();
        System.out.println("Order 2 detail has " + detail.lineItems.size() + " line items"
            + " (queries so far: " + OrderRepository.queryCount + ")");
    }
}
```

How to run: `java EntityGraphLevel3.java`

`findAllSummary` and `findDetailById` live on the *same* repository for the *same* entity, yet fetch differently — exactly the flexibility `@EntityGraph` provides in a real Spring Data repository: no global `fetch = EAGER` is ever set on `Order.lineItems`, so the cheap list view stays cheap, and only the detail method opts into the named graph.

## 6. Walkthrough

Execution starts in `main`. First, `repo.findAllSummary()` runs — `queryCount` increments to 1, and the two `Order` objects are returned exactly as constructed, with `lineItems` left `null` (unfetched), because this method never references the named entity graph. The printed line shows `Summary count: 2 (queries so far: 1)`.

Next, `repo.findDetailById(2)` runs — `queryCount` increments to 2. Inside, the stream finds the order with `id == 2`, then (standing in for the `LEFT JOIN` a real `@EntityGraph`-annotated query would perform) immediately populates a fresh `Order` copy's `lineItems` from `lineItemsByOrder`, within that same method call — no separate query fires for the line items themselves. The result has `lineItems.size() == 2`, and the printed line shows `queries so far: 2`, confirming the detail fetch cost exactly one query total, not two.

```
findAllSummary()                    findDetailById(2)
   query #1                            query #2
   returns [order1, order2]            returns order2 WITH lineItems joined in
   lineItems left null                 (no separate query for lineItems)
```

In a real Spring Data JPA repository, an HTTP request to an order list endpoint (`GET /orders`) would call `findAllSummary()`-equivalent, producing a lean `SELECT id, total FROM orders` and a JSON response with bare order summaries. A request to an order detail endpoint (`GET /orders/2`) would call the `@EntityGraph`-annotated method, producing `SELECT o.*, li.* FROM orders o LEFT JOIN line_items li ON li.order_id = o.id WHERE o.id = 2` — a single round trip that returns the order together with all of its line items, ready to serialize into a detailed JSON body without triggering any further lazy-loading queries.

## 7. Gotchas & takeaways

> Gotcha: applying `@EntityGraph` to fetch *multiple* collection-valued (`@OneToMany`/`@ManyToMany`) associations in one query causes a Cartesian-product join — the result set balloons (rows multiply across each joined collection), and Hibernate may even reject it outright with a `MultipleBagFetchException` if the collections are plain `List`s rather than `Set`s.

- `@EntityGraph` overrides fetch behavior per repository method — the entity's own `fetch = LAZY`/`EAGER` declaration stays the default for every other call site.
- A **named** entity graph (`@NamedEntityGraph` on the entity + `@EntityGraph(value = "...")` on the method) lets multiple repository methods share one fetch-plan definition by name.
- Use it to fix N+1 query problems: one query with a `JOIN FETCH`-style plan beats one query plus one extra per row.
- Fetching more than one collection association in a single entity graph risks a Cartesian-product blowup or a `MultipleBagFetchException` — keep multi-collection graphs to `Set`-typed associations, or split into separate queries.
