---
card: system-design
gi: 212
slug: graphql-schema-resolvers
title: GraphQL (schema & resolvers)
---

## 1. What it is

**GraphQL** is a query language and server-side runtime where the client sends one request describing exactly the fields it needs — across possibly many related resources — and the server returns exactly that shape, no more and no less. A **schema** defines every type and field the API exposes; a **resolver** is the function that actually fetches the data for one specific field when a query asks for it.

## 2. Why & when

A REST client that needs an order, its customer's name, and the customer's last three orders typically makes three separate `GET` requests (`/orders/5`, `/customers/7`, `/customers/7/orders?limit=3`), or relies on a bespoke endpoint built just for this one screen. GraphQL removes the round-trips and the bespoke-endpoint sprawl: a single query asks for exactly this combination of fields, from exactly these related types, and the server resolves it all in one request.

The tradeoff is real: every field is independently resolvable, so a naive implementation can trigger many backend calls per request (the "N+1" problem), caching is harder than REST's simple per-URL caching, and the server takes on more work per request since clients now control the query shape. Use GraphQL when clients (especially multiple different clients, similar to the motivation behind [backend-for-frontend](0199-backend-for-frontend-bff.md)) need flexible, varying combinations of related data and round-trip count matters — a mobile app over a slow network is a common case. A simple API with few, well-known access patterns usually does not need GraphQL's added complexity.

## 3. Core concept

- **Schema.** A strongly typed description of every object type, field, and its type (`Order { id: ID!, amount: Float!, customer: Customer! }`). The schema is a contract the client can introspect — many GraphQL tools auto-generate documentation and even client code from it.
- **Query.** The client sends a query describing the exact fields and nested fields it wants: `{ order(id: "5") { amount customer { name } } }`. The server response mirrors this exact shape — nothing more.
- **Resolver.** Each field in the schema has a resolver function that knows how to fetch that field's value, often from a specific backend service or database. `Order.customer`'s resolver, given an order, fetches the related `Customer`.
- **The N+1 problem.** If a query asks for 20 orders and each order's `customer` field, a naive resolver calls the customer-fetching function once per order — 20 separate calls — instead of batching them into one call for all 20 customer IDs at once.
- **DataLoader / batching.** The standard fix for N+1: a resolver does not fetch immediately: it queues the requested IDs within one request cycle, then a batching layer fires a single `WHERE id IN (...)` call for all of them at once, and hands each resolver its specific result.

## 4. Diagram

```
  Client query:
  {
    order(id: "5") {
      amount
      customer { name }
      recentOrders(limit: 2) { id amount }
    }
  }

                        +------------------+
                        |  GraphQL Server   |
                        +------------------+
                                |
           schema resolves each field to a resolver:
                                |
        +------------+---------+----------+-----------------+
        v            v                    v                 v
   Order.amount  Order.customer     Customer.name    Order.recentOrders
   (from Orders   (fetch related     (from the         (fetch this
    table)        Customer by        already-fetched    customer's last
                   order.customerId)  Customer object)   2 orders)

  Response mirrors the query's EXACT shape:
  { "order": { "amount": 42.0, "customer": {"name": "Priya"},
               "recentOrders": [{"id":"3","amount":20.0},{"id":"1","amount":15.0}] } }
```
*Caption: one request, one response, shaped exactly like the query. Each field's resolver runs independently, which is powerful but is also where the N+1 problem originates.*

## 5. Runnable example

**Level 1 — Basic.** A minimal schema-like structure with resolvers for a few fields, executed against one query.

**Level 2 — Intermediate.** Resolve a nested relationship (`order.customer`), showing each resolver only knows how to fetch its own field.

**Level 3 — Advanced.** Demonstrate the N+1 problem with a naive per-item resolver call count, then fix it with a batching DataLoader-style resolver.

```java
// GraphqlDemo.java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class GraphqlDemo {

    record Order(String id, double amount, String customerId) {}
    record Customer(String id, String name) {}

    static Map<String, Order> ordersDb = Map.of(
        "1", new Order("1", 15.0, "C-1"), "2", new Order("2", 30.0, "C-2"),
        "3", new Order("3", 20.0, "C-1"), "4", new Order("4", 50.0, "C-3")
    );
    static Map<String, Customer> customersDb = Map.of(
        "C-1", new Customer("C-1", "Priya"), "C-2", new Customer("C-2", "Sam"), "C-3", new Customer("C-3", "Lee"));

    static int customerLookupCallCount = 0; // instrumented to make N+1 visible

    // ---------- Level 1: resolvers for individual fields ----------
    static double resolveAmount(Order order) { return order.amount(); }

    // ---------- Level 2: resolver for a nested/related field ----------
    static Customer resolveCustomerNaive(Order order) {
        customerLookupCallCount++; // ONE database-style call per order - this is the N+1 problem
        return customersDb.get(order.customerId());
    }

    // ---------- Level 3: batched resolver, fixes N+1 ----------
    static Map<String, Customer> resolveCustomersBatched(List<Order> orders) {
        Set<String> uniqueCustomerIds = orders.stream().map(Order::customerId).collect(Collectors.toSet());
        customerLookupCallCount++; // exactly ONE call total, regardless of how many orders
        Map<String, Customer> batch = new HashMap<>();
        for (String id : uniqueCustomerIds) batch.put(id, customersDb.get(id));
        return batch;
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - query: { order(id: \"1\") { amount } }");
        Order order1 = ordersDb.get("1");
        System.out.println("  response: { order: { amount: " + resolveAmount(order1) + " } }");

        System.out.println("\nLevel 2 - query: { order(id: \"1\") { amount customer { name } } }");
        Customer customer = resolveCustomerNaive(order1);
        System.out.println("  response: { order: { amount: " + order1.amount() +
            ", customer: { name: \"" + customer.name() + "\" } } }");

        System.out.println("\nLevel 3a - N+1 problem: query 4 orders, each resolving its own customer naively:");
        customerLookupCallCount = 0;
        List<Order> allOrders = new ArrayList<>(ordersDb.values());
        for (Order o : allOrders) {
            Customer c = resolveCustomerNaive(o);
            System.out.println("  order " + o.id() + " -> customer " + c.name());
        }
        System.out.println("  total customer lookup calls (naive): " + customerLookupCallCount +
            "  <- one call PER order, even though only 3 unique customers exist");

        System.out.println("\nLevel 3b - fixed with a batched resolver (DataLoader-style):");
        customerLookupCallCount = 0;
        Map<String, Customer> batchResult = resolveCustomersBatched(allOrders);
        for (Order o : allOrders) {
            System.out.println("  order " + o.id() + " -> customer " + batchResult.get(o.customerId()).name());
        }
        System.out.println("  total customer lookup calls (batched): " + customerLookupCallCount +
            "  <- exactly ONE call for all 4 orders combined");
    }
}
```

**How to run:** `java GraphqlDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `resolveAmount(order1)` is the simplest possible resolver — it reads a field directly off the already-fetched `Order` object. The printed response mirrors exactly the query shape `{ order { amount } }`, nothing more.
2. **Level 2:** `resolveCustomerNaive(order1)` resolves the nested `customer` field by taking `order.customerId()` and looking up the related `Customer`. This resolver knows nothing about `amount` — each field's resolver is independent and only responsible for its own field, which is the core of GraphQL's field-by-field execution model.
3. **Level 3a** runs the same naive resolver across all four orders in a loop. `customerLookupCallCount` increments once inside `resolveCustomerNaive` every time it is called — after the loop, the count is `4`, one call per order, even though there are only **3** distinct customers (`C-1` appears twice, for orders 1 and 3). This is the N+1 problem in miniature: for N orders, up to N separate customer lookups happen.
4. **Level 3b** calls `resolveCustomersBatched(allOrders)` once, which collects the **unique** customer IDs across all orders first (`Set<String> uniqueCustomerIds`), then performs exactly one simulated lookup for all of them together, incrementing `customerLookupCallCount` only once.
5. The loop afterward reads each order's customer from the already-fetched `batchResult` map — no further lookups happen. The final printed count, `1`, versus the naive count of `4` from Level 3a, shows exactly what a DataLoader-style batching layer buys you: the same query result, computed with far fewer backend calls.

## 7. Gotchas & takeaways

> **Gotcha:** without batching, a query that looks innocent on paper — a list of items, each with a nested related field — can trigger dozens or hundreds of backend calls under real load. This is the single most common GraphQL performance bug in production, and it is invisible until someone runs a query over a large list.

- Design resolvers to be batchable from the start (group requested IDs within one request cycle) rather than retrofitting it after an N+1 problem surfaces in production.
- Use the schema as the API's real contract — clients can introspect it, and changes to it should go through the same discipline as [versioning strategies](0208-versioning-strategies.md) for a REST API's contract.
- GraphQL trades REST's simple per-URL HTTP caching for query-level flexibility — plan a caching strategy (often at the resolver or data-source level, not the HTTP layer) deliberately, rather than assuming it comes for free.
- Consider GraphQL specifically when it solves a real problem [backend-for-frontend](0199-backend-for-frontend-bff.md) also addresses — many varied clients needing different data shapes — and compare the two approaches for your actual client diversity before committing.
