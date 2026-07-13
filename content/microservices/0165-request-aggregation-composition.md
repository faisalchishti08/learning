---
card: microservices
gi: 165
slug: request-aggregation-composition
title: "Request aggregation / composition"
---

## 1. What it is

Request aggregation is a gateway calling multiple backend services on behalf of one incoming client request and combining their individual responses into a single response the client receives — sparing the client from needing to make multiple separate calls itself and stitch the results together on its own.

## 2. Why & when

A client screen that needs data spanning several services — an order detail page needing the order itself, the customer's info, and current shipping status — could make three separate calls directly to three separate backend services, but that means the client pays for three round trips (real latency, especially painful on mobile networks), needs to know about and handle three different services' availability independently, and carries the burden of merging the three results itself. A gateway performing that aggregation instead makes those three backend calls (potentially in parallel) and returns one already-combined response, trading gateway-side complexity for a dramatically simpler, faster client experience.

Reach for request aggregation when a client-facing view genuinely needs data from multiple backend services and the client shouldn't need to know that internal structure or pay for multiple round trips to assemble it. This becomes especially valuable for mobile clients on higher-latency networks, where each additional round trip has an outsized cost compared to a same-datacenter gateway-to-backend call.

## 3. Core concept

The gateway receives one client request, issues calls to however many backend services are needed to satisfy it (sequentially if one call depends on another's result, in parallel if they're independent), and merges the individual results into one response shape defined specifically for that client-facing use case.

```java
// ONE client request in, MULTIPLE backend calls out, ONE combined response back
CombinedOrderView getOrderDetailView(int orderId) {
    OrderSummary order = orderServiceClient.getOrder(orderId);           // call 1
    CustomerInfo customer = customerServiceClient.getCustomer(order.customerId()); // call 2
    ShippingStatus shipping = shippingServiceClient.getStatus(orderId);   // call 3
    return new CombinedOrderView(order, customer, shipping); // ONE merged response
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client makes one request to the gateway; the gateway calls three separate backend services in parallel and merges their responses into one combined response returned to the client" >
  <rect x="20" y="75" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="99" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Client (1 call)</text>

  <rect x="220" y="70" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="290" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Gateway</text>

  <rect x="470" y="20" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="540" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service</text>
  <rect x="470" y="80" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="540" y="100" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">customer-service</text>
  <rect x="470" y="140" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="540" y="160" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">shipping-service</text>

  <line x1="140" y1="95" x2="218" y2="95" stroke="#8b949e" marker-end="url(#arr46)"/>
  <line x1="360" y1="85" x2="468" y2="35" stroke="#8b949e" marker-end="url(#arr46)"/>
  <line x1="360" y1="95" x2="468" y2="95" stroke="#8b949e" marker-end="url(#arr46)"/>
  <line x1="360" y1="105" x2="468" y2="155" stroke="#8b949e" marker-end="url(#arr46)"/>

  <defs>
    <marker id="arr46" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One client round trip triggers three backend calls, merged into one response before the client sees anything.

## 5. Runnable example

Scenario: an order-detail page that starts requiring the client to make three separate calls itself (showing the client-side burden), moves aggregation to the gateway with sequential backend calls, and finally parallelizes those backend calls to reduce total latency, since two of the three calls have no dependency on each other's result.

### Level 1 — Basic

```java
// File: ClientMakesThreeCalls.java -- the CLIENT itself calls three backends
// separately and merges the results -- three round trips, client-side complexity.
import java.util.concurrent.*;

public class ClientMakesThreeCalls {
    record OrderSummary(int orderId, int customerId, double total) {}
    record CustomerInfo(String name) {}
    record ShippingStatus(String status) {}

    static OrderSummary callOrderService(int orderId) throws InterruptedException { Thread.sleep(100); return new OrderSummary(orderId, 7, 99.90); }
    static CustomerInfo callCustomerService(int customerId) throws InterruptedException { Thread.sleep(100); return new CustomerInfo("Alice"); }
    static ShippingStatus callShippingService(int orderId) throws InterruptedException { Thread.sleep(100); return new ShippingStatus("IN_TRANSIT"); }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();

        // the CLIENT makes THREE sequential round trips itself
        OrderSummary order = callOrderService(42);
        CustomerInfo customer = callCustomerService(order.customerId());
        ShippingStatus shipping = callShippingService(42);

        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Client assembled: order=" + order + ", customer=" + customer + ", shipping=" + shipping);
        System.out.println("Total client-side latency: ~" + elapsed + "ms (THREE sequential round trips, and the client had to know about all three services)");
    }
}
```

**How to run:** `javac ClientMakesThreeCalls.java && java ClientMakesThreeCalls` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GatewayAggregatesSequentially.java -- the GATEWAY makes all three calls
// and merges them; the client makes ONE call and knows nothing about the three backends.
import java.util.concurrent.*;

public class GatewayAggregatesSequentially {
    record OrderSummary(int orderId, int customerId, double total) {}
    record CustomerInfo(String name) {}
    record ShippingStatus(String status) {}
    record CombinedOrderView(OrderSummary order, CustomerInfo customer, ShippingStatus shipping) {}

    static OrderSummary callOrderService(int orderId) throws InterruptedException { Thread.sleep(100); return new OrderSummary(orderId, 7, 99.90); }
    static CustomerInfo callCustomerService(int customerId) throws InterruptedException { Thread.sleep(100); return new CustomerInfo("Alice"); }
    static ShippingStatus callShippingService(int orderId) throws InterruptedException { Thread.sleep(100); return new ShippingStatus("IN_TRANSIT"); }

    static CombinedOrderView getOrderDetailView(int orderId) throws InterruptedException {
        OrderSummary order = callOrderService(orderId);
        CustomerInfo customer = callCustomerService(order.customerId()); // depends on order's customerId
        ShippingStatus shipping = callShippingService(orderId);
        return new CombinedOrderView(order, customer, shipping);
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        CombinedOrderView view = getOrderDetailView(42); // the CLIENT makes exactly ONE call
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("Client received ONE combined response: " + view);
        System.out.println("Gateway-side latency: ~" + elapsed + "ms (client made ONE call, unaware of the three backend calls behind it)");
    }
}
```

**How to run:** `javac GatewayAggregatesSequentially.java && java GatewayAggregatesSequentially` (JDK 17+).

Expected output (approximate timing, ~300ms since calls are still sequential here):
```
Client received ONE combined response: CombinedOrderView[order=OrderSummary[orderId=42, customerId=7, total=99.9], customer=CustomerInfo[name=Alice], shipping=ShippingStatus[status=IN_TRANSIT]]
Gateway-side latency: ~300ms (client made ONE call, unaware of the three backend calls behind it)
```

### Level 3 — Advanced

```java
// File: ParallelAggregation.java -- callShippingService does NOT depend on
// callOrderService's result, so it runs IN PARALLEL, cutting total latency.
import java.util.concurrent.*;

public class ParallelAggregation {
    record OrderSummary(int orderId, int customerId, double total) {}
    record CustomerInfo(String name) {}
    record ShippingStatus(String status) {}
    record CombinedOrderView(OrderSummary order, CustomerInfo customer, ShippingStatus shipping) {}

    static OrderSummary callOrderService(int orderId) throws InterruptedException { Thread.sleep(100); return new OrderSummary(orderId, 7, 99.90); }
    static CustomerInfo callCustomerService(int customerId) throws InterruptedException { Thread.sleep(100); return new CustomerInfo("Alice"); }
    static ShippingStatus callShippingService(int orderId) throws InterruptedException { Thread.sleep(100); return new ShippingStatus("IN_TRANSIT"); }

    static CombinedOrderView getOrderDetailView(int orderId) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(2);

        // shippingService call does NOT need order's result -- start it IN PARALLEL immediately
        Future<ShippingStatus> shippingFuture = pool.submit(() -> callShippingService(orderId));

        // orderService MUST complete before customerService can run (customerService needs order.customerId())
        OrderSummary order = callOrderService(orderId);
        CustomerInfo customer = callCustomerService(order.customerId());

        ShippingStatus shipping = shippingFuture.get(); // wait for the PARALLEL call to finish, if it hasn't already
        pool.shutdown();
        return new CombinedOrderView(order, customer, shipping);
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        CombinedOrderView view = getOrderDetailView(42);
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("Client received: " + view);
        System.out.println("Gateway-side latency: ~" + elapsed + "ms (shipping call ran IN PARALLEL with order+customer calls, cutting total time from ~300ms toward ~200ms)");
    }
}
```

**How to run:** `javac ParallelAggregation.java && java ParallelAggregation` (JDK 17+).

Expected output (approximate timing, roughly 200ms instead of 300ms):
```
Client received: CombinedOrderView[order=OrderSummary[orderId=42, customerId=7, total=99.9], customer=CustomerInfo[name=Alice], shipping=ShippingStatus[status=IN_TRANSIT]]
Gateway-side latency: ~200ms (shipping call ran IN PARALLEL with order+customer calls, cutting total time from ~300ms toward ~200ms)
```

## 6. Walkthrough

1. **Level 1** — `main` itself calls `callOrderService`, then `callCustomerService`, then `callShippingService`, each a separate, simulated 100ms round trip; the printed total elapsed time is roughly 300ms, and this entire sequencing burden — knowing about and calling three distinct services — falls on what represents client code.
2. **Level 2, the same calls moved into the gateway** — `getOrderDetailView` now makes all three calls, but from the *gateway's* code, not the client's; `main` calls this single method once, receiving a fully assembled `CombinedOrderView` without ever calling `callOrderService`, `callCustomerService`, or `callShippingService` directly itself.
3. **Level 2, the dependency preserved sequentially** — `callCustomerService(order.customerId())` genuinely needs `order`'s result first (to know which customer to look up), so this call still happens after `callOrderService` completes — the total latency (~300ms) is unchanged from Level 1, only *where* the sequencing logic lives has moved.
4. **Level 3, identifying the independent call** — `callShippingService(orderId)` needs only the original `orderId` parameter, never `order`'s result, meaning it has no genuine dependency on `callOrderService` completing first — this independence is what makes parallelization possible.
5. **Level 3, starting the independent call early** — `pool.submit(() -> callShippingService(orderId))` starts the shipping call on a separate thread immediately, *before* `callOrderService` is even invoked, returning a `Future<ShippingStatus>` that will eventually hold the result.
6. **Level 3, the dependent calls still running sequentially** — `callOrderService` and `callCustomerService` still run one after another on the main thread, exactly as in Level 2, because `callCustomerService` genuinely needs `order.customerId()`.
7. **Level 3, the payoff measured directly** — `shippingFuture.get()` blocks only if the parallel shipping call hasn't already finished by the time it's reached; since the sequential order+customer path (200ms total) takes longer than the parallel shipping call alone (100ms), the shipping result is already available by the time `shippingFuture.get()` is called, meaning the *total* elapsed time is bounded by the longer of the two independent paths (200ms) rather than their sum (300ms) — a genuine, measurable latency reduction achieved purely by recognizing which backend calls have no dependency on each other and running those in parallel.

## 7. Gotchas & takeaways

> **Gotcha:** aggregating calls to multiple backends means the combined response is only as reliable as the least reliable individual backend — if `shipping-service` is slow or down, does the entire aggregated response fail, or does the gateway return a partial response with shipping status omitted? This is a real design decision (fail entirely vs. degrade gracefully) that needs to be made deliberately per use case, not left as an accidental consequence of how the aggregation code happens to be written.

- Request aggregation lets a gateway make multiple backend calls on behalf of one client request, sparing the client from multiple round trips and from needing to know the internal service topology.
- This is especially valuable for higher-latency client connections (mobile networks), where each additional round trip carries an outsized cost compared to same-datacenter gateway-to-backend calls.
- Backend calls with genuine data dependencies must run sequentially; calls with no dependency on each other's results can run in parallel, directly reducing total latency.
- The gateway needs a deliberate policy for partial failure — if one of several aggregated backend calls fails, whether to fail the entire response or degrade gracefully is a real design decision, not an incidental detail.
- Identifying which backend calls are genuinely independent, and parallelizing only those, is what separates naive sequential aggregation (correct but slow) from well-optimized aggregation (correct and fast).
