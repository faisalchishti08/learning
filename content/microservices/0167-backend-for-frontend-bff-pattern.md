---
card: microservices
gi: 167
slug: backend-for-frontend-bff-pattern
title: "Backend for Frontend (BFF) pattern"
---

## 1. What it is

The Backend for Frontend pattern gives each distinct client type — a mobile app, a web frontend, a public third-party API — its own dedicated [API gateway](0157-api-gateway-pattern.md), tailored specifically to that client's needs, rather than forcing every client to share one general-purpose gateway trying to satisfy all of them at once.

## 2. Why & when

Different client types genuinely need different things from the same underlying backend services: a mobile app on a constrained network wants a lean, aggregated response minimizing round trips and payload size, a web frontend rendering a data-dense dashboard wants a richer response with more fields, and a public third-party API needs a stable, carefully versioned contract independent of internal frontend redesigns. A single shared gateway trying to serve all three well ends up either compromising on all of them, or accumulating client-specific conditional logic that couples unrelated client types' concerns together in one increasingly tangled codebase.

Reach for a BFF per client type once a single shared gateway's response shape, aggregation needs, or versioning cadence genuinely diverge enough between client types that satisfying one well means compromising another. For a single client type, or clients with genuinely similar needs, one shared gateway remains simpler and avoids the added operational overhead of maintaining multiple gateway deployments — the BFF pattern is a deliberate trade-off, not a default.

## 3. Core concept

Each BFF is its own independently deployable service, calling the same underlying backend services as any other BFF, but shaping requests and responses specifically for its one client type — a mobile BFF might aggregate three backend calls into one lean response, while a web BFF exposes the same three backends through a richer, more granular API better suited to a data-heavy dashboard.

```java
// mobile-bff: ONE lean, aggregated endpoint, minimizing round trips for a constrained network
GET /mobile/orders/42  -> { orderId, total, status }  // just the essentials

// web-bff: a RICHER response, more fields, suited to a dashboard's needs
GET /web/orders/42  -> { orderId, total, status, items[], customerName, customerEmail, shippingAddress, ... }

// BOTH call the SAME underlying order-service and customer-service -- just shaped differently
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A mobile client talks to a dedicated mobile BFF, and a web client talks to a dedicated web BFF; both BFFs independently call the same underlying order-service and customer-service, shaping the responses differently for each client type" >
  <rect x="20" y="20" width="110" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="75" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Mobile app</text>
  <rect x="20" y="130" width="110" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="75" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Web frontend</text>

  <rect x="200" y="20" width="130" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="265" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Mobile BFF</text>
  <rect x="200" y="130" width="130" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="265" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Web BFF</text>

  <rect x="440" y="20" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="515" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-service</text>
  <rect x="440" y="130" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="515" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">customer-service</text>

  <line x1="130" y1="37" x2="198" y2="37" stroke="#8b949e" marker-end="url(#arr48)"/>
  <line x1="130" y1="147" x2="198" y2="147" stroke="#8b949e" marker-end="url(#arr48)"/>
  <line x1="330" y1="37" x2="438" y2="37" stroke="#8b949e" marker-end="url(#arr48)"/>
  <line x1="330" y1="55" x2="438" y2="140" stroke="#8b949e" marker-end="url(#arr48)"/>
  <line x1="330" y1="140" x2="438" y2="55" stroke="#8b949e" marker-end="url(#arr48)"/>
  <line x1="330" y1="147" x2="438" y2="147" stroke="#8b949e" marker-end="url(#arr48)"/>

  <defs>
    <marker id="arr48" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Both BFFs reach into the same backend services, but shape the outgoing response independently for their own client type.

## 5. Runnable example

Scenario: an order-detail response that starts as one shared gateway trying to satisfy both a mobile client and a web client with the same response shape (highlighting the resulting compromise), splits into two dedicated BFFs each tailored to its own client, and finally shows the two BFFs evolving independently — the web BFF gaining a new field with zero impact on the mobile BFF or its client.

### Level 1 — Basic

```java
// File: OneSharedGatewayCompromise.java -- ONE response shape trying to serve
// BOTH a lean mobile client and a data-hungry web client -- satisfies neither well.
import java.util.*;

public class OneSharedGatewayCompromise {
    record OrderView(int orderId, double total, String status, String customerName, String customerEmail, String shippingAddress, List<String> items) {}

    static OrderView sharedGateway_getOrder(int orderId) {
        // ONE shape, containing EVERYTHING every client might conceivably want
        return new OrderView(orderId, 99.90, "PLACED", "Alice", "alice@example.com", "123 Main St", List.of("widget", "gadget"));
    }

    public static void main(String[] args) {
        OrderView response = sharedGateway_getOrder(42);
        System.out.println("Mobile client receives (over a constrained network): " + response);
        System.out.println("Mobile client only NEEDED orderId/total/status, but got the FULL payload anyway -- wasted bandwidth on every request.");
    }
}
```

**How to run:** `javac OneSharedGatewayCompromise.java && java OneSharedGatewayCompromise` (JDK 17+).

### Level 2 — Intermediate

```java
// File: DedicatedBffsPerClient.java -- TWO separate BFFs, each calling the SAME
// underlying services but shaping the response for ITS OWN client type.
import java.util.*;

public class DedicatedBffsPerClient {
    // the SHARED underlying backend data -- BOTH BFFs pull from the same source
    record FullOrderData(int orderId, double total, String status, String customerName, String customerEmail, String shippingAddress, List<String> items) {}
    static FullOrderData backendOrderService_getFullOrder(int orderId) {
        return new FullOrderData(orderId, 99.90, "PLACED", "Alice", "alice@example.com", "123 Main St", List.of("widget", "gadget"));
    }

    // MOBILE BFF: a lean, minimal response shape
    record MobileOrderView(int orderId, double total, String status) {}
    static MobileOrderView mobileBff_getOrder(int orderId) {
        FullOrderData full = backendOrderService_getFullOrder(orderId);
        return new MobileOrderView(full.orderId(), full.total(), full.status()); // DELIBERATELY minimal
    }

    // WEB BFF: a rich response shape, suited to a data-dense dashboard
    record WebOrderView(int orderId, double total, String status, String customerName, String customerEmail, String shippingAddress, List<String> items) {}
    static WebOrderView webBff_getOrder(int orderId) {
        FullOrderData full = backendOrderService_getFullOrder(orderId);
        return new WebOrderView(full.orderId(), full.total(), full.status(), full.customerName(), full.customerEmail(), full.shippingAddress(), full.items());
    }

    public static void main(String[] args) {
        System.out.println("Mobile client receives (via mobile-bff): " + mobileBff_getOrder(42));
        System.out.println("Web client receives (via web-bff):       " + webBff_getOrder(42));
        System.out.println("SAME underlying data, TWO tailored shapes -- mobile got exactly what it needed, nothing more.");
    }
}
```

**How to run:** `javac DedicatedBffsPerClient.java && java DedicatedBffsPerClient` (JDK 17+).

Expected output:
```
Mobile client receives (via mobile-bff): MobileOrderView[orderId=42, total=99.9, status=PLACED]
Web client receives (via web-bff):       WebOrderView[orderId=42, total=99.9, status=PLACED, customerName=Alice, customerEmail=alice@example.com, shippingAddress=123 Main St, items=[widget, gadget]]
SAME underlying data, TWO tailored shapes -- mobile got exactly what it needed, nothing more.
```

### Level 3 — Advanced

```java
// File: IndependentBffEvolution.java -- the WEB BFF gains a NEW field; the
// MOBILE BFF (and its client) are COMPLETELY unaffected, since they're independent deployables.
import java.util.*;

public class IndependentBffEvolution {
    record FullOrderData(int orderId, double total, String status, String customerName, String customerEmail,
                          String shippingAddress, List<String> items, double loyaltyPointsEarned) { // NEW backend field
    }
    static FullOrderData backendOrderService_getFullOrder(int orderId) {
        return new FullOrderData(orderId, 99.90, "PLACED", "Alice", "alice@example.com", "123 Main St", List.of("widget", "gadget"), 9.99);
    }

    // MOBILE BFF: UNCHANGED from Level 2 -- does not even know loyaltyPointsEarned exists
    record MobileOrderView(int orderId, double total, String status) {}
    static MobileOrderView mobileBff_getOrder(int orderId) {
        FullOrderData full = backendOrderService_getFullOrder(orderId);
        return new MobileOrderView(full.orderId(), full.total(), full.status());
    }

    // WEB BFF: UPGRADED independently to expose the NEW loyaltyPointsEarned field
    record WebOrderView(int orderId, double total, String status, String customerName, String customerEmail,
                         String shippingAddress, List<String> items, double loyaltyPointsEarned) {
    }
    static WebOrderView webBff_getOrder(int orderId) {
        FullOrderData full = backendOrderService_getFullOrder(orderId);
        return new WebOrderView(full.orderId(), full.total(), full.status(), full.customerName(), full.customerEmail(),
            full.shippingAddress(), full.items(), full.loyaltyPointsEarned()); // NEW field exposed HERE ONLY
    }

    public static void main(String[] args) {
        System.out.println("Mobile client receives (mobile-bff UNCHANGED): " + mobileBff_getOrder(42));
        System.out.println("Web client receives (web-bff UPGRADED):        " + webBff_getOrder(42));
        System.out.println("The backend's new field was adopted by web-bff INDEPENDENTLY -- mobile-bff's code and its client's contract were never touched.");
    }
}
```

**How to run:** `javac IndependentBffEvolution.java && java IndependentBffEvolution` (JDK 17+).

Expected output:
```
Mobile client receives (mobile-bff UNCHANGED): MobileOrderView[orderId=42, total=99.9, status=PLACED]
Web client receives (web-bff UPGRADED):        WebOrderView[orderId=42, total=99.9, status=PLACED, customerName=Alice, customerEmail=alice@example.com, shippingAddress=123 Main St, items=[widget, gadget], loyaltyPointsEarned=9.99]
The backend's new field was adopted by web-bff INDEPENDENTLY -- mobile-bff's code and its client's contract were never touched.
```

## 6. Walkthrough

1. **Level 1** — `sharedGateway_getOrder` returns a single `OrderView` type containing every field any conceivable client might want; the mobile client's printed response includes `customerEmail` and `shippingAddress`, fields it never asked for and doesn't need, representing real wasted bandwidth on a constrained connection.
2. **Level 2, a shared backend source** — `backendOrderService_getFullOrder` represents the single underlying source of truth both BFFs pull from, unchanged from how a shared gateway would access it.
3. **Level 2, two independent shaping functions** — `mobileBff_getOrder` constructs a deliberately minimal `MobileOrderView` using only three of the seven available fields, while `webBff_getOrder` constructs a `WebOrderView` using all seven — both read from the identical `full` object, but each decides independently what to expose.
4. **Level 2, the observable difference** — the mobile client's printed response is visibly smaller than the web client's, despite both being derived from the exact same backend call, directly resolving Level 1's one-size-fits-all compromise.
5. **Level 3, the backend evolving** — `FullOrderData` gains a new field, `loyaltyPointsEarned`, representing a genuine backend enhancement (perhaps a new loyalty program feature).
6. **Level 3, the web BFF adopting it independently** — `WebOrderView` and `webBff_getOrder` are updated to include `loyaltyPointsEarned`, a change made entirely within the web BFF's own code, with no coordination required from, or impact on, the mobile BFF.
7. **Level 3, the mobile BFF's complete isolation from the change** — `MobileOrderView` and `mobileBff_getOrder` are copied over from Level 2 completely unmodified; the printed mobile client response is identical to Level 2's, proving that a backend enhancement adopted by one BFF has zero effect on another BFF or its client — each BFF, being its own independently deployable service, evolves entirely on its own schedule, which is the concrete operational benefit the BFF pattern provides over a single shared gateway where such a change would need to be introduced carefully to avoid affecting every client type at once.

## 7. Gotchas & takeaways

> **Gotcha:** each BFF is its own real service requiring its own deployment pipeline, monitoring, and on-call ownership — the BFF pattern trades a single shared gateway's operational simplicity for per-client-type flexibility, and that trade-off is only worthwhile once client types have genuinely diverged enough to justify the added operational surface; introducing a BFF per client type prematurely, before real divergence exists, is pure overhead with no corresponding benefit.

- The Backend for Frontend pattern gives each distinct client type its own dedicated gateway, tailored specifically to that client's response shape and aggregation needs.
- All BFFs typically call the same underlying backend services; the distinction is in how each BFF shapes requests and responses for its specific client type, not in what backend data is ultimately available.
- This avoids the compromise a single shared gateway makes when trying to satisfy meaningfully different client needs with one response shape.
- Each BFF, as an independently deployable service, can evolve on its own schedule — adopting new backend capabilities or making breaking changes without needing to coordinate with or affect other client types' BFFs.
- The pattern trades a single shared gateway's operational simplicity for genuine per-client flexibility; it's worth adopting once client needs have genuinely diverged, not as a default starting architecture.
