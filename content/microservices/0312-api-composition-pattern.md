---
card: microservices
gi: 312
slug: api-composition-pattern
title: "API composition pattern"
---

## 1. What it is

API composition is the formal name for the technique introduced in [no distributed joins](0309-no-distributed-joins-composition-instead.md): a dedicated *composer* — an API gateway, a backend-for-frontend, or a purpose-built aggregating service — receives a request that needs data from multiple services, queries each of those services' APIs (typically concurrently for the independent ones), and merges their responses into a single view returned to the original caller. The composer contains no business logic of its own beyond assembly; it is purely a data-gathering and merging layer.

## 2. Why & when

Composition is the direct, structural answer to the loss of cross-service joins that [database per service](0304-database-per-service-pattern.md) causes: since no single query can span multiple services' private databases, *something* has to call each service and stitch the results together, and API composition names and formalizes where and how that happens, rather than leaving every client to reinvent this logic ad hoc. Centralizing it in a dedicated composer avoids every client (web frontend, mobile app, another service) needing to independently know which services to call and how to combine their results — that knowledge lives in one place.

Use API composition for read-heavy scenarios that need data from a small, fairly stable set of services (typically two to four) where the added latency of the composed calls is acceptable — the pattern gets less appealing as the number of composed services grows, since composition latency and failure surface scale with it. For read patterns that are hit very frequently, or that need to compose data from many services, or that need sub-request-time latency, a materialized [CQRS read model](0314-cqrs-read-models-materialized-views.md) pre-computed via events is usually a better fit, trading some data freshness for dramatically better read performance and fewer runtime dependencies.

## 3. Core concept

The composer is a thin orchestration layer: it never owns data itself, only assembles it from calls to the actual owning services, ideally dispatched concurrently and protected by the resilience patterns covered earlier in this course.

```java
@RestController
class OrderDetailsComposer {
    private final OrderServiceClient orderClient;
    private final ProductServiceClient productClient;
    private final CustomerServiceClient customerClient;

    @GetMapping("/order-details/{orderId}")
    OrderDetailsView getOrderDetails(@PathVariable String orderId) {
        Order order = orderClient.getOrder(orderId); // must come first -- others depend on its data

        CompletableFuture<Product> productFuture =
                CompletableFuture.supplyAsync(() -> productClient.getProduct(order.sku()));
        CompletableFuture<Customer> customerFuture =
                CompletableFuture.supplyAsync(() -> customerClient.getCustomer(order.customerId()));

        return new OrderDetailsView(order, productFuture.join(), customerFuture.join()); // MERGE, no business logic
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client sends one request to a composer, which fans out to multiple owning services' APIs, waits for their responses, merges them into a single combined view, and returns that single view back to the original client as one response">
  <rect x="20" y="60" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client</text>

  <line x1="120" y1="80" x2="200" y2="80" stroke="#8b949e" marker-end="url(#arr312)"/>
  <rect x="210" y="60" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="275" y="84" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Composer</text>

  <line x1="340" y1="70" x2="440" y2="30" stroke="#8b949e" marker-end="url(#arr312)"/>
  <line x1="340" y1="80" x2="440" y2="80" stroke="#8b949e" marker-end="url(#arr312)"/>
  <line x1="340" y1="90" x2="440" y2="130" stroke="#8b949e" marker-end="url(#arr312)"/>

  <rect x="450" y="10" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="30" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <rect x="450" y="65" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="85" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ProductService</text>
  <rect x="450" y="115" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="135" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">CustomerService</text>

  <defs><marker id="arr312" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One client request fans out to several owning services and merges back into a single composed response.

## 5. Runnable example

Scenario: a client forced to call three services itself and merge the results, extended to a dedicated composer that centralizes this logic behind one endpoint, and finally the composer applying a resilience-aware fallback so a single non-critical service's failure degrades the composed view gracefully instead of failing the whole request.

### Level 1 — Basic

```java
// File: ClientDoesItsOwnComposition.java -- WITHOUT a composer, every
// client (here, main() playing the role of a frontend) must know about
// and call all three services itself, duplicating this logic wherever
// the composed view is needed.
public class ClientDoesItsOwnComposition {
    record Order(String id, String sku, String customerId) {}
    record Product(String sku, String name) {}
    record Customer(String id, String name) {}

    static Order getOrder(String id) { return new Order(id, "sku-1", "cust-1"); }
    static Product getProduct(String sku) { return new Product(sku, "Wireless Mouse"); }
    static Customer getCustomer(String id) { return new Customer(id, "Alice"); }

    public static void main(String[] args) {
        // The CLIENT itself has to know about and call THREE separate services.
        Order order = getOrder("order-1");
        Product product = getProduct(order.sku());
        Customer customer = getCustomer(order.customerId());

        System.out.println("Order " + order.id() + ": " + customer.name() + " ordered " + product.name()
                + " -- this composition logic would need to be DUPLICATED in every client that needs this view.");
    }
}
```

How to run: `java ClientDoesItsOwnComposition.java`

The calling code (standing in for a web frontend or mobile app) directly calls all three services and manually assembles the result. This works, but every other client that needs the same "order details" view — a different frontend, an internal admin tool, a partner integration — would need to independently reimplement this exact same three-call composition logic.

### Level 2 — Intermediate

```java
// File: DedicatedComposer.java -- a SINGLE composer centralizes the
// composition logic behind one method/endpoint; ANY client now just
// calls the composer once, instead of knowing about three services.
public class DedicatedComposer {
    record Order(String id, String sku, String customerId) {}
    record Product(String sku, String name) {}
    record Customer(String id, String name) {}
    record OrderDetailsView(String orderId, String customerName, String productName) {}

    static Order getOrder(String id) { return new Order(id, "sku-1", "cust-1"); }
    static Product getProduct(String sku) { return new Product(sku, "Wireless Mouse"); }
    static Customer getCustomer(String id) { return new Customer(id, "Alice"); }

    // The composer -- ALL composition logic lives HERE, once.
    static OrderDetailsView getOrderDetails(String orderId) {
        Order order = getOrder(orderId);
        Product product = getProduct(order.sku());
        Customer customer = getCustomer(order.customerId());
        return new OrderDetailsView(order.id(), customer.name(), product.name());
    }

    public static void main(String[] args) {
        // ANY client -- frontend, mobile app, admin tool -- just calls THIS, once.
        OrderDetailsView view = getOrderDetails("order-1");
        System.out.println(view + " -- ONE call to the composer, composition logic exists in exactly ONE place.");
    }
}
```

How to run: `java DedicatedComposer.java`

`getOrderDetails` is now the single place all three underlying calls and their merging happen. `main` (standing in for any client) calls this one method and gets back a fully-composed view — every other client needing the same view calls the exact same composer, rather than reimplementing the three-service fan-out logic itself.

### Level 3 — Advanced

```java
// File: ComposerWithGracefulDegradation.java -- the composer applies a
// FALLBACK for a non-critical piece of the composed view: if
// CustomerService is unavailable, the composed view still returns
// successfully with a degraded customer name, rather than failing the
// ENTIRE composed request over one non-essential dependency's outage.
public class ComposerWithGracefulDegradation {
    record Order(String id, String sku, String customerId) {}
    record Product(String sku, String name) {}
    record Customer(String id, String name) {}
    record OrderDetailsView(String orderId, String customerName, String productName) {}

    static Order getOrder(String id) { return new Order(id, "sku-1", "cust-1"); }
    static Product getProduct(String sku) { return new Product(sku, "Wireless Mouse"); }
    static Customer getCustomer(String id) {
        throw new RuntimeException("CustomerService unreachable"); // simulated outage
    }

    static OrderDetailsView getOrderDetails(String orderId) {
        Order order = getOrder(orderId);       // CRITICAL -- no order, no view at all, let it fail
        Product product = getProduct(order.sku()); // CRITICAL -- product name is essential to this view

        String customerName;
        try {
            customerName = getCustomer(order.customerId()).name(); // NON-CRITICAL -- degrade gracefully
        } catch (Exception e) {
            customerName = "Customer info unavailable";
        }

        return new OrderDetailsView(order.id(), customerName, product.name());
    }

    public static void main(String[] args) {
        OrderDetailsView view = getOrderDetails("order-1");
        System.out.println(view + " -- the composed view still succeeded, with a GRACEFULLY DEGRADED customer name, "
                + "despite CustomerService being completely down.");
    }
}
```

How to run: `java ComposerWithGracefulDegradation.java`

`getOrder` and `getProduct` are treated as critical to this view (without an order or its product, there's nothing meaningful to show) and are allowed to fail the whole request if they fail. `getCustomer`, simulated as unreachable, is wrapped in a `try/catch` that substitutes a graceful degraded string instead of propagating the failure — the composed `OrderDetailsView` still returns successfully, just with degraded (not missing) customer information, demonstrating that a composer should apply the [fallback](0282-fallback-methods-default-responses.md) resilience pattern per constituent call based on how essential that specific piece of data is to the overall composed view.

## 6. Walkthrough

Trace `ComposerWithGracefulDegradation.main` in order. **First**, `getOrderDetails("order-1")` is called. Inside, `getOrder("order-1")` runs first and succeeds, returning `Order(id="order-1", sku="sku-1", customerId="cust-1")` — this call is made with no error handling around it, reflecting the decision that a failure here should propagate and fail the entire composed request, since without the order itself there is nothing meaningful to compose.

**`getProduct(order.sku())` runs next**, also without a `try/catch`, and succeeds, returning `Product(sku="sku-1", name="Wireless Mouse")` — also treated as critical, since a product-less order detail view would be missing its most essential piece of information.

**`getCustomer(order.customerId())` is called inside a `try` block.** The method immediately throws `RuntimeException("CustomerService unreachable")`, simulating a real outage. This exception is caught by the surrounding `catch (Exception e)` block, which assigns the plain string `"Customer info unavailable"` to `customerName` instead of letting the exception propagate further.

**Execution continues normally past the `try/catch`** — nothing about the exception having occurred prevents the method from reaching its final line. A new `OrderDetailsView` is constructed from `order.id()`, the (degraded) `customerName`, and `product.name()`, and this is returned successfully to `main`.

**`main` prints the returned view**, which shows a fully-populated order ID and product name alongside the degraded customer name — a partially degraded but still useful and successfully-returned response, rather than the composer's entire request failing outright over one non-critical dependency's outage.

**The key architectural decision made visible here**: the composer's author had to decide, for each of the three composed calls, whether a failure there should be *critical* (propagate, fail the whole request) or *non-critical* (catch, degrade gracefully) — this decision belongs in the composer, since it alone has the full picture of what the composed view actually needs to be minimally useful.

```
getOrderDetails("order-1")
   getOrder()    -- CRITICAL, no try/catch -- failure would fail the WHOLE request
   getProduct()  -- CRITICAL, no try/catch -- failure would fail the WHOLE request
   getCustomer() -- NON-CRITICAL, wrapped in try/catch -- failure degrades gracefully
        |
        v
   OrderDetailsView(orderId, "Customer info unavailable", "Wireless Mouse")  <- still returned successfully
```

## 7. Gotchas & takeaways

> A composer that treats every constituent call as equally critical (either all-or-nothing failure, or blind fallback everywhere) misses the actual design decision this pattern requires: each call's criticality should be evaluated on its own merits, based on how essential that specific piece of data is to the composed view being minimally useful.

- API composition centralizes cross-service data assembly logic in one place, so clients (frontends, other services) don't each need to independently know which services to call and how to merge their results.
- Dispatch independent constituent calls concurrently (see [no distributed joins](0309-no-distributed-joins-composition-instead.md)) to bound the composed request's total latency by the slowest single call rather than their sum.
- Apply resilience patterns (timeouts, circuit breakers, fallbacks) per constituent call, deciding deliberately per call whether its failure should be critical (fail the whole composed request) or degrade gracefully (substitute a fallback and continue).
- API composition is well-suited to read patterns spanning a small, fairly stable number of services; for higher-frequency reads or composition across many services, a pre-computed [CQRS read model](0314-cqrs-read-models-materialized-views.md) is usually a better-performing alternative, at the cost of accepting eventual rather than immediate consistency.
