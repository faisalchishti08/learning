---
card: microservices
gi: 309
slug: no-distributed-joins-composition-instead
title: "No distributed joins — composition instead"
---

## 1. What it is

Once data lives in separate, private databases under [database per service](0304-database-per-service-pattern.md), there is no SQL `JOIN` that can span across them — a join requires both tables to be queryable within the same database engine and transaction. Composition is the alternative: fetch each piece of data separately from its owning service (via API calls), then combine the results in application code, typically at whichever layer is orchestrating the overall request — an API gateway, a backend-for-frontend, or a dedicated aggregating service.

## 2. Why & when

This isn't a limitation to work around cleverly — it's the direct, unavoidable consequence of the isolation database-per-service deliberately provides. A service that needs data spanning what used to be a single joined query in a monolith must instead call each owning service's API and stitch the results together itself. This is more code than a single SQL join, and it introduces new failure modes (any one of the calls can fail or be slow) that a single-database join never had to consider, but it preserves the actual independence that motivated splitting the data apart in the first place.

Use composition (see the dedicated [API composition pattern](0312-api-composition-pattern.md) topic for the full pattern) whenever a request genuinely needs data assembled from more than one service, and accept that this composition happens in application code, typically with the calls made concurrently to bound the added latency, and with each individual call protected by the resilience patterns from earlier in this section (timeouts, circuit breakers, fallbacks) since composition inherently depends on multiple independent services all being available.

## 3. Core concept

Instead of one query joining two tables, two separate calls are made and their results are merged in memory, typically concurrently to avoid serializing the latency of each call.

```java
// NOT POSSIBLE: SELECT o.*, p.name FROM orders o JOIN products p ON o.sku = p.sku
// (orders and products live in different services' private databases)

// INSTEAD: fetch independently, compose in application code.
CompletableFuture<Order> orderFuture = CompletableFuture.supplyAsync(() -> orderClient.getOrder(orderId));
CompletableFuture<Product> productFuture = orderFuture.thenCompose(order ->
        CompletableFuture.supplyAsync(() -> productClient.getProduct(order.sku())));

OrderDetailsView view = orderFuture.thenCombine(productFuture,
        (order, product) -> new OrderDetailsView(order.id(), product.name(), order.quantity())
).join();
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An aggregating layer calls OrderService and ProductService independently through their APIs, since no database join can span their separate private databases, then combines both results in application code to produce a single composed view for the caller">
  <rect x="250" y="20" width="140" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Aggregating layer</text>

  <line x1="290" y1="55" x2="130" y2="95" stroke="#8b949e" marker-end="url(#arr309)"/>
  <line x1="350" y1="55" x2="510" y2="95" stroke="#8b949e" marker-end="url(#arr309)"/>

  <rect x="50" y="100" width="160" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="122" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderService API</text>

  <rect x="430" y="100" width="160" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="122" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ProductService API</text>

  <text x="320" y="150" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">results MERGED in application code -- no cross-database JOIN exists</text>

  <defs><marker id="arr309" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

No join spans the two databases; an aggregating layer calls both APIs and merges the results itself.

## 5. Runnable example

Scenario: a monolith-style single query joining orders and products directly, extended to the same result assembled via two independent, sequential API calls once the data is split, and finally the same composition made concurrent to avoid needlessly serializing the two independent calls' latency.

### Level 1 — Basic

```java
// File: MonolithStyleJoin.java -- BEFORE the split: one shared database,
// one SQL-style join produces the combined view directly.
import java.util.*;

public class MonolithStyleJoin {
    record OrderRow(int orderId, String sku, int quantity) {}
    record ProductRow(String sku, String name) {}

    public static void main(String[] args) {
        List<OrderRow> orders = List.of(new OrderRow(1, "sku-1", 2));
        List<ProductRow> products = List.of(new ProductRow("sku-1", "Wireless Mouse"));

        // A single in-memory "join" -- stands in for one SQL JOIN query
        // that was possible because both tables lived in ONE database.
        for (OrderRow order : orders) {
            for (ProductRow product : products) {
                if (order.sku().equals(product.sku())) {
                    System.out.println("Order " + order.orderId() + ": " + order.quantity() + "x " + product.name()
                            + " (produced by ONE query against ONE shared database)");
                }
            }
        }
    }
}
```

How to run: `java MonolithStyleJoin.java`

Both `orders` and `products` live in the same in-memory space (standing in for the same database), so combining them is a trivial nested-loop join — this is the shape of query that becomes impossible the instant the two datasets move into separate services' private databases.

### Level 2 — Intermediate

```java
// File: SequentialComposition.java -- AFTER the split: OrderService and
// ProductService are separate, with separate APIs; the combined view is
// now assembled by calling BOTH and merging in application code.
import java.util.*;

public class SequentialComposition {
    record Order(int orderId, String sku, int quantity) {}
    record Product(String sku, String name) {}
    record OrderDetailsView(int orderId, String productName, int quantity) {}

    static class OrderServiceClient {
        Order getOrder(int orderId) { return new Order(orderId, "sku-1", 2); } // stands in for an HTTP call
    }
    static class ProductServiceClient {
        Product getProduct(String sku) { return new Product(sku, "Wireless Mouse"); } // stands in for an HTTP call
    }

    public static void main(String[] args) {
        OrderServiceClient orderClient = new OrderServiceClient();
        ProductServiceClient productClient = new ProductServiceClient();

        // NO join possible -- fetch SEPARATELY, then combine in code.
        Order order = orderClient.getOrder(1);              // call #1
        Product product = productClient.getProduct(order.sku()); // call #2, DEPENDS on call #1's result

        OrderDetailsView view = new OrderDetailsView(order.orderId(), product.name(), order.quantity());
        System.out.println(view + " (assembled from TWO separate API calls, composed in application code)");
    }
}
```

How to run: `java SequentialComposition.java`

`getOrder` and `getProduct` are now two entirely separate calls, each standing in for a real network request to a different service. `getProduct` even depends on `getOrder`'s result (it needs the `sku` from the order), so the two calls are inherently sequential here — this reflects a real composition where one call's result determines what the next call needs to fetch.

### Level 3 — Advanced

```java
// File: ConcurrentCompositionWithIndependentCalls.java -- when the calls
// are INDEPENDENT of each other's results (not the case in Level 2, but
// common when composing data from more than two services), running them
// CONCURRENTLY avoids needlessly serializing their latencies -- a real
// composition optimization.
import java.util.concurrent.*;

public class ConcurrentCompositionWithIndependentCalls {
    record Order(int orderId, String sku, int quantity) {}
    record CustomerProfile(String customerId, String name) {}
    record ShippingEstimate(String estimatedDays) {}
    record OrderSummaryView(int orderId, String customerName, int quantity, String estimatedDays) {}

    static class OrderServiceClient {
        Order getOrder(int orderId) { sleep(100); return new Order(orderId, "sku-1", 2); }
    }
    static class CustomerServiceClient {
        CustomerProfile getCustomer(String customerId) { sleep(150); return new CustomerProfile(customerId, "Alice"); }
    }
    static class ShippingServiceClient {
        ShippingEstimate getEstimate(String sku) { sleep(120); return new ShippingEstimate("3-5 days"); }
    }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException ignored) {} }

    public static void main(String[] args) throws Exception {
        OrderServiceClient orderClient = new OrderServiceClient();
        CustomerServiceClient customerClient = new CustomerServiceClient();
        ShippingServiceClient shippingClient = new ShippingServiceClient();

        long start = System.currentTimeMillis();

        // Order must be fetched first (we need its sku for shipping); customer
        // and shipping estimate are INDEPENDENT of each other once we have
        // the order -- so run THOSE two concurrently instead of sequentially.
        Order order = orderClient.getOrder(1); // 100ms

        CompletableFuture<CustomerProfile> customerFuture =
                CompletableFuture.supplyAsync(() -> customerClient.getCustomer("cust-1")); // 150ms, CONCURRENT
        CompletableFuture<ShippingEstimate> shippingFuture =
                CompletableFuture.supplyAsync(() -> shippingClient.getEstimate(order.sku())); // 120ms, CONCURRENT

        CustomerProfile customer = customerFuture.get();
        ShippingEstimate shipping = shippingFuture.get();

        OrderSummaryView view = new OrderSummaryView(order.orderId(), customer.name(), order.quantity(), shipping.estimatedDays());
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(view);
        System.out.println("Total time: " + elapsed + "ms (order[100ms] + max(customer[150ms], shipping[120ms]) "
                + "= ~250ms, NOT 100+150+120=370ms if run sequentially)");
    }
}
```

How to run: `java ConcurrentCompositionWithIndependentCalls.java`

`getOrder` runs first (needed to get the `sku` for the shipping call), taking 100ms. Once it completes, `getCustomer` (150ms) and `getEstimate` (120ms) are independent of each other and are dispatched concurrently via `CompletableFuture.supplyAsync`, so their latencies overlap rather than stack. The total elapsed time comes out close to `100 + max(150, 120) = 250ms`, not the `100 + 150 + 120 = 370ms` a naive fully-sequential composition would take — a meaningful latency saving that becomes more significant as more services are composed into a single view.

## 6. Walkthrough

Trace `ConcurrentCompositionWithIndependentCalls.main` in order. **First**, `start` captures the current time, and `orderClient.getOrder(1)` is called synchronously — the calling thread blocks for its full 100ms `sleep`, then returns an `Order` with `sku="sku-1"`.

**Next**, two `CompletableFuture.supplyAsync` calls are made in immediate succession. Each schedules its respective lambda (`customerClient.getCustomer(...)` and `shippingClient.getEstimate(order.sku())`) to run on a thread from the common `ForkJoinPool`, and both return immediately with a `CompletableFuture` handle — the calling thread does *not* block on either of these lines; it has simply dispatched two units of work to run in the background, concurrently with each other.

**Both background tasks begin executing at approximately the same wall-clock moment** (immediately after being scheduled): the `customerClient.getCustomer` task sleeps for 150ms, and the `shippingClient.getEstimate` task sleeps for 120ms, on two different threads, in parallel.

**`customerFuture.get()` is called**, which blocks the main thread until the customer task completes — this takes up to 150ms from when the task was scheduled. **`shippingFuture.get()` is called immediately after** — but since the shipping task was scheduled at essentially the same time as the customer task and only takes 120ms, it has very likely *already completed* by the time `shippingFuture.get()` is reached (which itself happens after waiting the full 150ms for the customer future) — so this second `.get()` call returns near-instantly rather than adding its own 120ms on top.

**The `OrderSummaryView` is assembled** from the three independently-fetched pieces (`order`, `customer`, `shipping`), and `elapsed` is computed as the total wall-clock time from `start` to this point — approximately `100ms (order) + 150ms (the longer of the two concurrent calls) = 250ms`, confirming that the two independent calls' latencies overlapped rather than adding together.

```
t=0ms:    getOrder() starts (blocking)
t=100ms:  getOrder() returns -- sku now known
t=100ms:  getCustomer() and getEstimate() BOTH start concurrently (different threads)
t=220ms:  getEstimate() finishes (100+120)
t=250ms:  getCustomer() finishes (100+150) -- this is the LONGER of the two, so it determines total time
t=250ms:  view assembled, both results already available
```

## 7. Gotchas & takeaways

> Composing calls sequentially by default, purely because it's the simplest code to write, silently pays a latency cost proportional to the *sum* of every independent call's duration — as more services get composed into a single view, this sum grows linearly, while a concurrent composition's latency grows only with the *slowest single call*, a substantial and increasingly important difference as composition depth grows.

- No SQL join can span services' separate private databases — composition (fetching from each service's API and combining the results in application code) is the structural replacement.
- Identify which of the calls in a composition genuinely depend on each other's results (must run sequentially) versus which are independent (can run concurrently), and dispatch the independent ones concurrently to bound total latency by the slowest call rather than the sum of all calls.
- Every call in a composition is now a separate potential point of failure — apply the resilience patterns from earlier in this section (timeouts, circuit breakers, fallbacks) to each individual call, since the composed view's overall availability depends on all of its constituent calls succeeding (or gracefully degrading).
- See [API composition pattern](0312-api-composition-pattern.md) for the fuller treatment of this as a formal architectural pattern, including where the composition logic itself should live (API gateway, backend-for-frontend, or a dedicated aggregating service).
