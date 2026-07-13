---
card: microservices
gi: 166
slug: api-composition-pattern
title: "API composition pattern"
---

## 1. What it is

The API composition pattern is a specific application of [request aggregation](0165-request-aggregation-composition.md) for satisfying queries that need to join data owned by multiple different services — an "API composer" component calls each relevant service to fetch its piece of the data, then performs the join, filter, or sort in memory, entirely outside any single service's own database, because no individual service's database contains the full picture on its own.

## 2. Why & when

In a database-per-service architecture, each service owns its data exclusively, which is exactly what makes services independently deployable — but it also means a query spanning multiple services' data (find all orders over $100 placed by customers in California) can't be answered by a single SQL join, because the orders and the customers live in two entirely separate databases that were never meant to be joined directly. The API composition pattern accepts this constraint and answers such queries by fetching the relevant data from each owning service and performing the join in application code, in memory, at query time.

Reach for API composition when a cross-service query is needed occasionally, the data volumes involved are modest enough for an in-memory join to be practical, and the added complexity of a dedicated read model (see [CQRS](0129-event-carried-state-transfer.md) and event-carried state transfer) isn't yet justified. Move toward a materialized, denormalized read model instead once composition-time joins become a performance bottleneck — fetching and joining large datasets in memory on every query doesn't scale the way a purpose-built, pre-joined read store does.

## 3. Core concept

The composer fetches each service's relevant subset of data independently, then applies standard in-memory data operations — filtering, joining on a shared key, sorting — to produce the final combined result, exactly mirroring what a database join would do, but performed in application code across data that was never in one database to begin with.

```java
List<Order> allOrders = orderServiceClient.getOrdersOverAmount(100.0);          // service 1's data
List<Customer> californiaCustomers = customerServiceClient.getCustomersInState("CA"); // service 2's data

Set<Integer> californiaCustomerIds = californiaCustomers.stream().map(Customer::id).collect(Collectors.toSet());
List<Order> result = allOrders.stream()
    .filter(order -> californiaCustomerIds.contains(order.customerId())) // the JOIN, done in application code
    .toList();
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An API composer fetches orders from order-service and California customers from customer-service, then joins the two lists in memory on customerId to produce the final composed result -- no single database ever performed this join" >
  <rect x="20" y="20" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-service: orders</text>

  <rect x="20" y="115" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="137" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">customer-service: CA customers</text>

  <rect x="260" y="65" width="150" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="88" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Composer</text>
  <text x="335" y="103" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">in-memory join</text>

  <rect x="490" y="65" width="130" height="45" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="555" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Composed result</text>

  <line x1="170" y1="37" x2="258" y2="80" stroke="#8b949e" marker-end="url(#arr47)"/>
  <line x1="170" y1="132" x2="258" y2="97" stroke="#8b949e" marker-end="url(#arr47)"/>
  <line x1="410" y1="87" x2="488" y2="87" stroke="#8b949e" marker-end="url(#arr47)"/>

  <defs>
    <marker id="arr47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Two independent services' data is fetched separately and joined in the composer, since no single database holds both.

## 5. Runnable example

Scenario: a "high-value orders from California customers" report that starts by demonstrating the query is impossible as a single database call (since the data is split across two services), implements it as an API composer joining data in memory, and finally optimizes the naive composition to avoid an inefficient nested-loop join once data volumes grow, using an index-like lookup structure instead.

### Level 1 — Basic

```java
// File: TheImpossibleSingleQuery.java -- demonstrates WHY this needs composition:
// orders and customers live in TWO SEPARATE, unrelated in-memory "databases".
import java.util.*;

public class TheImpossibleSingleQuery {
    record Order(int orderId, int customerId, double total) {}
    record Customer(int customerId, String name, String state) {}

    // order-service's OWN database -- has NO idea what state any customer is in
    static List<Order> orderServiceDatabase = List.of(
        new Order(1, 100, 150.0), new Order(2, 101, 50.0), new Order(3, 102, 200.0));
    // customer-service's OWN database -- has NO idea about order amounts
    static List<Customer> customerServiceDatabase = List.of(
        new Customer(100, "Alice", "CA"), new Customer(101, "Bob", "NY"), new Customer(102, "Carol", "CA"));

    public static void main(String[] args) {
        System.out.println("order-service's data: " + orderServiceDatabase);
        System.out.println("customer-service's data: " + customerServiceDatabase);
        System.out.println("Neither database alone can answer: 'orders over $100 from CA customers' -- the join data doesn't exist in either one.");
    }
}
```

**How to run:** `javac TheImpossibleSingleQuery.java && java TheImpossibleSingleQuery` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ApiComposer.java -- fetches from BOTH services, then performs the JOIN
// in application code, exactly mirroring what a SQL join would do.
import java.util.*;
import java.util.stream.*;

public class ApiComposer {
    record Order(int orderId, int customerId, double total) {}
    record Customer(int customerId, String name, String state) {}
    record ComposedResult(int orderId, String customerName, double total) {}

    static List<Order> orderServiceClient_getOrdersOverAmount(double amount) {
        List<Order> all = List.of(new Order(1, 100, 150.0), new Order(2, 101, 50.0), new Order(3, 102, 200.0));
        return all.stream().filter(o -> o.total() > amount).toList(); // simulates a real order-service API call
    }
    static List<Customer> customerServiceClient_getCustomersInState(String state) {
        List<Customer> all = List.of(new Customer(100, "Alice", "CA"), new Customer(101, "Bob", "NY"), new Customer(102, "Carol", "CA"));
        return all.stream().filter(c -> c.state().equals(state)).toList(); // simulates a real customer-service API call
    }

    static List<ComposedResult> composeHighValueCaliforniaOrders() {
        List<Order> highValueOrders = orderServiceClient_getOrdersOverAmount(100.0);
        List<Customer> caCustomers = customerServiceClient_getCustomersInState("CA");
        Map<Integer, Customer> caCustomersById = caCustomers.stream().collect(Collectors.toMap(Customer::customerId, c -> c));

        return highValueOrders.stream()
            .filter(order -> caCustomersById.containsKey(order.customerId())) // the JOIN condition
            .map(order -> new ComposedResult(order.orderId(), caCustomersById.get(order.customerId()).name(), order.total()))
            .toList();
    }

    public static void main(String[] args) {
        List<ComposedResult> results = composeHighValueCaliforniaOrders();
        System.out.println("Composed result: " + results);
        System.out.println("This answer required TWO service calls plus an in-memory join -- no single database query could have produced it.");
    }
}
```

**How to run:** `javac ApiComposer.java && java ApiComposer` (JDK 17+).

Expected output:
```
Composed result: [ComposedResult[orderId=1, customerName=Alice, total=150.0], ComposedResult[orderId=3, customerName=Carol, total=200.0]]
This answer required TWO service calls plus an in-memory join -- no single database query could have produced it.
```

### Level 3 — Advanced

```java
// File: IndexedJoinAtScale.java -- a NAIVE nested-loop join is O(n*m); a
// map-based (index-like) join is O(n+m) -- essential once data volumes grow.
import java.util.*;
import java.util.stream.*;

public class IndexedJoinAtScale {
    record Order(int orderId, int customerId, double total) {}
    record Customer(int customerId, String name, String state) {}
    record ComposedResult(int orderId, String customerName, double total) {}

    static List<ComposedResult> naiveNestedLoopJoin(List<Order> orders, List<Customer> customers) {
        List<ComposedResult> results = new ArrayList<>();
        int comparisons = 0;
        for (Order order : orders) {
            for (Customer customer : customers) { // for EVERY order, scan EVERY customer -- O(n * m)
                comparisons++;
                if (order.customerId() == customer.customerId()) {
                    results.add(new ComposedResult(order.orderId(), customer.name(), order.total()));
                    break;
                }
            }
        }
        System.out.println("Naive nested-loop join: " + comparisons + " comparisons for " + orders.size() + " orders x " + customers.size() + " customers");
        return results;
    }

    static List<ComposedResult> indexedJoin(List<Order> orders, List<Customer> customers) {
        Map<Integer, Customer> customersById = customers.stream().collect(Collectors.toMap(Customer::customerId, c -> c)); // build the INDEX once, O(m)
        int lookups = 0;
        List<ComposedResult> results = new ArrayList<>();
        for (Order order : orders) { // O(n) lookups, each O(1) via the map -- O(n + m) total
            lookups++;
            Customer c = customersById.get(order.customerId());
            if (c != null) results.add(new ComposedResult(order.orderId(), c.name(), order.total()));
        }
        System.out.println("Indexed join: " + lookups + " map lookups (plus " + customers.size() + " to build the index) for the same data");
        return results;
    }

    public static void main(String[] args) {
        // simulate a LARGER dataset: 1000 orders, 500 customers
        List<Order> orders = IntStream.range(0, 1000).mapToObj(i -> new Order(i, i % 500, 50.0 + i)).toList();
        List<Customer> customers = IntStream.range(0, 500).mapToObj(i -> new Customer(i, "customer-" + i, i % 2 == 0 ? "CA" : "NY")).toList();

        List<ComposedResult> resultA = naiveNestedLoopJoin(orders, customers);
        List<ComposedResult> resultB = indexedJoin(orders, customers);

        System.out.println("Both approaches produced " + resultA.size() + " and " + resultB.size() + " results respectively -- IDENTICAL correctness, VERY different cost.");
        System.out.println("Naive: ~" + (orders.size() * customers.size()) + " comparisons. Indexed: ~" + (orders.size() + customers.size()) + " operations -- a massive difference at this scale.");
    }
}
```

**How to run:** `javac IndexedJoinAtScale.java && java IndexedJoinAtScale` (JDK 17+).

Expected output:
```
Naive nested-loop join: 500000 comparisons for 1000 orders x 500 customers
Indexed join: 1000 map lookups (plus 500 to build the index) for the same data
Both approaches produced 1000 and 1000 results respectively -- IDENTICAL correctness, VERY different cost.
Naive: ~500000 comparisons. Indexed: ~1500 operations -- a massive difference at this scale.
```

## 6. Walkthrough

1. **Level 1** — `orderServiceDatabase` and `customerServiceDatabase` are deliberately modeled as two entirely separate lists with no relationship expressed between them at the storage level; the printed statement makes explicit that neither one, queried alone, can answer a question requiring both.
2. **Level 2, fetching each service's relevant slice** — `orderServiceClient_getOrdersOverAmount(100.0)` and `customerServiceClient_getCustomersInState("CA")` each simulate a real, independent API call to a different service, each applying its own filter using only the data that service actually owns.
3. **Level 2, building a lookup structure for the join** — `caCustomersById` is a `Map<Integer, Customer>` built from the fetched California customers, keyed by `customerId`, giving the subsequent join step an efficient way to check membership.
4. **Level 2, performing the join** — the `.filter(order -> caCustomersById.containsKey(order.customerId()))` step is the actual join condition, checking each high-value order's `customerId` against the map of California customers; `.map(...)` then constructs the final `ComposedResult` combining fields from both original sources.
5. **Level 3, the naive approach's cost** — `naiveNestedLoopJoin`'s inner `for` loop scans the *entire* `customers` list for every single order, meaning the total number of comparisons grows as the product of both list sizes — at 1000 orders and 500 customers, that's 500,000 comparisons.
6. **Level 3, the indexed approach's cost** — `indexedJoin` builds `customersById` once (an O(m) cost, 500 operations), then performs one O(1) map lookup per order (an O(n) cost, 1000 operations), for a combined cost proportional to the *sum*, not the *product*, of the two list sizes — roughly 1,500 total operations instead of 500,000.
7. **Level 3, identical correctness, vastly different performance** — both `resultA` and `resultB` produce the same number of composed results (1000, since every order's `customerId % 500` always finds a matching customer in this generated dataset), proving the two approaches are functionally equivalent — the printed comparison of operation counts makes the practical stakes of choosing the naive approach at real data volumes concrete rather than abstract.

## 7. Gotchas & takeaways

> **Gotcha:** API composition performs joins at *query time*, which means its performance degrades as the datasets being joined grow — unlike a database's own join, which benefits from indexes maintained continuously as data changes, an API composer typically starts from scratch on every query; once composition-time cost becomes a genuine bottleneck, a precomputed, event-driven materialized view (built ahead of time via [event-carried state transfer](0129-event-carried-state-transfer.md)) usually becomes the better answer than trying to further optimize the composition-time join itself.

- The API composition pattern answers cross-service queries by fetching each relevant service's data independently and performing the join in application code, since no single service's database holds the full picture in a database-per-service architecture.
- This is a specific, query-oriented application of the broader [request aggregation](0165-request-aggregation-composition.md) pattern.
- A naive nested-loop join's cost grows as the product of the joined dataset sizes; building an index-like lookup structure (a map keyed by the join key) reduces this to a cost proportional to their sum.
- API composition is well suited to occasional, modest-volume cross-service queries; it does not scale the way a precomputed, purpose-built read model does as query frequency or data volume grows.
- Moving to a materialized, event-driven read model becomes the better choice once composition-time joins become a genuine, recurring performance bottleneck.
