---
card: spring-data
gi: 60
slug: fetch-load-graphs
title: "Fetch & load graphs"
---

## 1. What it is

JPA distinguishes two ways an entity graph can be applied: as a **fetch graph** (`javax.persistence.fetchgraph` / `jakarta.persistence.fetchgraph`) or as a **load graph** (`jakarta.persistence.loadgraph`). Both describe which associations to eagerly fetch, but they disagree on what happens to attributes *not* listed in the graph: a fetch graph treats everything else as `LAZY` regardless of its mapped default, while a load graph respects each attribute's own mapped fetch type for anything the graph doesn't mention.

```java
@EntityGraph(value = "Order.withLineItems", type = EntityGraph.EntityGraphType.LOAD)
List<Order> findByStatus(String status);
```

## 2. Why & when

The previous card introduced `@EntityGraph` for opting a specific query into eager fetching. This card is about the `type` attribute you can set on it — `FETCH` or `LOAD` — which controls the behavior for everything *outside* the graph. That distinction matters once an entity has more than one association: a fetch graph silently turns unlisted eager associations lazy for that call, which can be surprising if you weren't trying to change them.

Reach for one or the other specifically when:

- You want the graph to be the *complete, exhaustive* fetch plan for the call — use `FETCH` type, and any mapped-`EAGER` association not listed becomes lazy for this query only.
- You want the graph to *add* eager fetching for specific lazy associations while leaving every other association's own mapped fetch type (including other `EAGER` ones) untouched — use `LOAD` type, the safer default for incrementally opting a lazy field into eager loading.
- You're debugging an unexpected extra lazy-load exception (`LazyInitializationException`) after adding an entity graph — checking whether it's `FETCH` (which silently lazified something you needed) is often the fix.

## 3. Core concept

```
 Order: lineItems (LAZY, mapped), customer (EAGER, mapped)

 @EntityGraph(value="Order.withLineItems", type=FETCH):
   lineItems -> eager (listed)     customer -> LAZY (NOT listed -> overridden to lazy!)

 @EntityGraph(value="Order.withLineItems", type=LOAD):
   lineItems -> eager (listed)     customer -> EAGER (NOT listed -> keeps its own mapped type)
```

`FETCH` replaces the entire fetch plan; `LOAD` only adds to it, leaving every other attribute's mapped fetch type as-is.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="FETCH type overrides unlisted attributes to lazy; LOAD type preserves their mapped fetch type">
  <rect x="10" y="10" width="200" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Order.customer (mapped EAGER)</text>

  <rect x="230" y="10" width="180" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="35" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">type = FETCH</text>
  <text x="320" y="52" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">unlisted -&gt; forced LAZY</text>
  <text x="320" y="66" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">(customer becomes lazy!)</text>

  <rect x="230" y="105" width="180" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="130" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">type = LOAD</text>
  <text x="320" y="147" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">unlisted -&gt; keeps mapped type</text>
  <text x="320" y="161" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">(customer stays eager)</text>

  <line x1="210" y1="32" x2="225" y2="45" stroke="#8b949e" stroke-width="1.3" marker-end="url(#fl)"/>
  <line x1="210" y1="32" x2="225" y2="140" stroke="#8b949e" stroke-width="1.3" marker-end="url(#fl)"/>
  <defs><marker id="fl" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same mapped-eager `customer` association survives under `LOAD` but is silently lazified under `FETCH`.

## 5. Runnable example

The scenario: an order entity with two associations (`lineItems`, mapped lazy, and `customer`, mapped eager), evolving from a plain mapped-defaults model, to a FETCH-type entity graph that unexpectedly lazifies `customer`, to a LOAD-type graph that preserves it.

### Level 1 — Basic

Model the entity's own mapped defaults with no entity graph involved at all.

```java
import java.util.*;

class Customer { String name; Customer(String n) { name = n; } }
class LineItem { String desc; LineItem(String d) { desc = d; } }

class Order {
    long id;
    Customer customer;   // mapped EAGER — always loaded by default
    List<LineItem> lineItems; // mapped LAZY — null unless explicitly fetched
    Order(long id, Customer customer) { this.id = id; this.customer = customer; }
}

public class FetchLoadLevel1 {
    // Simulates the plain repository default: mapped fetch types apply, no @EntityGraph.
    static Order findByIdDefault(long id, Map<Long, Order> db) {
        Order o = db.get(id);
        // customer is already populated (mapped EAGER); lineItems stays null (mapped LAZY)
        return o;
    }

    public static void main(String[] args) {
        Order order = new Order(1, new Customer("Ada Lovelace"));
        Map<Long, Order> db = Map.of(1L, order);

        Order found = findByIdDefault(1, db);
        System.out.println("Customer: " + found.customer.name); // present, mapped EAGER
        System.out.println("LineItems: " + found.lineItems);     // null, mapped LAZY, untouched
    }
}
```

How to run: `java FetchLoadLevel1.java`

With no entity graph involved, each association behaves exactly as mapped: `customer` (mapped `EAGER`) is already populated, and `lineItems` (mapped `LAZY`) is `null` until something explicitly fetches it. This is the baseline both `FETCH`- and `LOAD`-type graphs modify.

### Level 2 — Intermediate

Apply a `FETCH`-type entity graph that only lists `lineItems` — and observe that `customer`, despite being mapped `EAGER`, gets silently overridden to lazy (`null`) for this call, because `FETCH` treats the graph as the *entire* fetch plan.

```java
import java.util.*;

class Customer { String name; Customer(String n) { name = n; } }
class LineItem { String desc; LineItem(String d) { desc = d; } }

class Order {
    long id;
    Customer customer;
    List<LineItem> lineItems;
    Order(long id) { this.id = id; }
}

public class FetchLoadLevel2 {
    // @EntityGraph(value = "Order.withLineItems", type = EntityGraph.EntityGraphType.FETCH)
    // Only lineItems is listed -> customer is NOT in the graph -> forced lazy (null) for this call.
    static Order findByIdFetchGraph(long id, Map<Long, Customer> customers, Map<Long, List<LineItem>> items) {
        Order o = new Order(id);
        o.lineItems = items.getOrDefault(id, List.of()); // listed in graph -> eager
        o.customer = null; // NOT listed -> FETCH type forces lazy, overriding the mapped EAGER default
        return o;
    }

    public static void main(String[] args) {
        Map<Long, Customer> customers = Map.of(1L, new Customer("Ada Lovelace"));
        Map<Long, List<LineItem>> items = Map.of(1L, List.of(new LineItem("Widget")));

        Order found = findByIdFetchGraph(1, customers, items);
        System.out.println("LineItems: " + found.lineItems.size()); // eager as requested
        System.out.println("Customer: " + found.customer); // null! FETCH type overrode mapped EAGER
    }
}
```

How to run: `java FetchLoadLevel2.java`

`customer` prints `null` even though it is mapped `EAGER` on the entity — this is the surprise `type = FETCH` causes: because the graph only lists `lineItems`, `FETCH` semantics treat the graph as the complete plan and lazify everything else, `customer` included. In a real JPA provider, later code that reads `found.customer.name` outside a transaction would throw `LazyInitializationException`.

### Level 3 — Advanced

Switch the same call to `LOAD` type, which preserves `customer`'s own mapped `EAGER` default while still adding `lineItems` as an eager addition — the fix for the Level 2 surprise.

```java
import java.util.*;

class Customer { String name; Customer(String n) { name = n; } }
class LineItem { String desc; LineItem(String d) { desc = d; } }

class Order {
    long id;
    Customer customer;
    List<LineItem> lineItems;
    Order(long id) { this.id = id; }
}

public class FetchLoadLevel3 {
    // @EntityGraph(value = "Order.withLineItems", type = EntityGraph.EntityGraphType.LOAD)
    // lineItems is listed -> eager. customer is NOT listed -> keeps its OWN mapped type (EAGER) -> still loaded.
    static Order findByIdLoadGraph(long id, Map<Long, Customer> customers, Map<Long, List<LineItem>> items) {
        Order o = new Order(id);
        o.lineItems = items.getOrDefault(id, List.of());     // listed -> eager
        o.customer = customers.get(id);                       // not listed, but LOAD keeps mapped EAGER
        return o;
    }

    public static void main(String[] args) {
        Map<Long, Customer> customers = Map.of(1L, new Customer("Ada Lovelace"));
        Map<Long, List<LineItem>> items = Map.of(1L, List.of(new LineItem("Widget"), new LineItem("Gadget")));

        Order found = findByIdLoadGraph(1, customers, items);
        System.out.println("LineItems: " + found.lineItems.size()); // eager, as requested by the graph
        System.out.println("Customer: " + found.customer.name);      // still present! LOAD preserved mapped EAGER
    }
}
```

How to run: `java FetchLoadLevel3.java`

With `type = LOAD`, `customer` is populated ("Ada Lovelace") even though the graph never mentions it — `LOAD` only *adds* `lineItems` as an eager association on top of whatever the entity already mapped, rather than replacing the whole fetch plan. This is the safer default when you're extending an existing entity's fetch behavior rather than fully redefining it for one call.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `findByIdLoadGraph(1, customers, items)` is called. Inside, `o.lineItems` is set from `items.get(1)`, standing in for the entity graph's listed association being joined into the query — this happens identically to the `FETCH`-type version in Level 2.

The key difference happens on the next line: `o.customer = customers.get(id)` runs unconditionally, because under `LOAD` semantics, an attribute the graph doesn't mention simply falls back to its own mapped fetch type — and `customer` is mapped `EAGER`, so it gets populated exactly as it would with no entity graph at all.

Back in `main`, both fields are printed: `LineItems: 2` (from the graph) and `Customer: Ada Lovelace` (from the mapped default, preserved by `LOAD`). Compare this to Level 2's `findByIdFetchGraph`, where the equivalent `customer` line was hard-coded to `null` to model `FETCH` semantics forcing it lazy — the only difference between the two call paths is the graph's `type`, yet the observable result for `customer` flips entirely.

```
type=FETCH:  graph = {lineItems}           -> customer forced LAZY (null)
type=LOAD:   graph = {lineItems} + mapped  -> customer stays EAGER (populated)
```

In a real Spring Data JPA repository, `@EntityGraph(value = "Order.withLineItems", type = EntityGraphType.LOAD)` on `findByStatus(...)` generates SQL that joins in `line_items` (from the graph) *and* `customers` (from the mapped `EAGER` default) in the same `SELECT` — so a controller calling this method receives a fully populated `Order` with both associations ready to serialize, without triggering any lazy-loading exception downstream.

## 7. Gotchas & takeaways

> Gotcha: `@EntityGraph`'s default `type` is `FETCH`, not `LOAD` — if you add an entity graph to a method on an entity with more than one `EAGER`-mapped association and only list some of them, the others silently become lazy for that call, which can surface as a `LazyInitializationException` far from where the graph was declared.

- `FETCH` type: the entity graph becomes the *entire* fetch plan — anything not listed is lazy, regardless of its mapped default.
- `LOAD` type: the entity graph only *adds* eager associations — anything not listed keeps its own mapped fetch type.
- When in doubt, prefer `LOAD` — it's less likely to silently change behavior for associations you didn't intend to touch.
- Always check `type` explicitly when debugging an unexpected `null` association or an unexpected lazy-load exception after introducing `@EntityGraph`.
