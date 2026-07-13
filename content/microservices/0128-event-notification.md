---
card: microservices
gi: 128
slug: event-notification
title: "Event notification"
---

## 1. What it is

Event notification is the leanest style of event-driven communication: a producer publishes a small message announcing that something happened — usually just an identifier and an event type, like "order 42 was placed" — without including the full details, and any interested consumer that needs more than the bare announcement calls back to the producer's own API to fetch it.

## 2. Why & when

Event notification keeps the event itself tiny and the producer's data as the single source of truth: consumers that only care *that* something happened (trigger a workflow, invalidate a cache, log an audit entry) never need more than the notification, and consumers that do need details fetch exactly the current, authoritative data rather than a copy that could already be stale by the time they read it. This keeps the coupling between producer and consumer to just "the notification's shape and where to look it up," which changes rarely.

Reach for event notification when most consumers of an event genuinely don't need the full payload, or when the full record is large, sensitive, or changes shape often enough that keeping a copy of it fresh in every consumer would be wasteful or risky. Prefer [event-carried state transfer](0129-event-carried-state-transfer.md) instead when consumers need the actual data and a callback to fetch it would create either too much load on the producer or an unacceptable coupling to its availability.

## 3. Core concept

The event payload is minimal — an id, a type, maybe a timestamp — and any consumer needing more makes a synchronous call back to the producing service's API, using the id from the notification as the lookup key.

```java
// the event itself: deliberately thin
channel.publish("order-events", new OrderPlacedNotification(orderId = 42));

// a consumer that needs the details calls BACK to the source of truth
OrderPlacedNotification event = ...;
Order fullOrder = orderServiceClient.getOrder(event.orderId()); // a synchronous fetch, using the id from the event
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service publishes a thin OrderPlaced notification containing only an id; a consumer that needs full details makes a separate synchronous call back to the order service's API using that id" >
  <rect x="20" y="30" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Service</text>

  <rect x="240" y="20" width="170" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">event: OrderPlaced</text>
  <text x="325" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">{ orderId: 42 } (thin)</text>

  <rect x="470" y="30" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Consumer</text>

  <line x1="160" y1="50" x2="238" y2="47" stroke="#8b949e" marker-end="url(#arr14)"/>
  <line x1="410" y1="47" x2="468" y2="50" stroke="#8b949e" marker-end="url(#arr14)"/>

  <path d="M540,70 Q540,130 90,130 Q90,110 90,72" fill="none" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#arr14)"/>
  <text x="315" y="145" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">GET /orders/42 -- fetch full details, on demand</text>
</svg>

The notification only carries an id; interested consumers pull full details from the producer directly, when and if they need them.

## 5. Runnable example

Scenario: an order-notification flow that starts with a fat event carrying full order details (the alternative this section contrasts with), shrinks the event to a thin notification plus an API callback, and finally shows two different consumers making very different use of that same thin notification — one skipping the callback entirely, one needing it.

### Level 1 — Basic

```java
// File: FatEventBaseline.java -- a "fat" event carrying the FULL order, for comparison.
import java.util.*;
import java.util.function.*;

public class FatEventBaseline {
    record Order(int id, String customerEmail, double total, List<String> items) {}

    static class Channel {
        List<Consumer<Order>> subscribers = new ArrayList<>();
        void subscribe(Consumer<Order> h) { subscribers.add(h); }
        void publish(Order fullOrder) { subscribers.forEach(s -> s.accept(fullOrder)); } // the WHOLE order goes out
    }

    public static void main(String[] args) {
        Channel orderEvents = new Channel();
        orderEvents.subscribe(order -> System.out.println("[audit-log] recorded event, but only used order.id(): " + order.id()));
        orderEvents.publish(new Order(42, "alice@example.com", 99.90, List.of("widget", "gadget")));
    }
}
```

**How to run:** `javac FatEventBaseline.java && java FatEventBaseline` (JDK 17+).

The `audit-log` subscriber only ever uses `order.id()`, yet the full order (including the customer's email) was transmitted anyway — every subscriber pays the cost of the full payload regardless of what it actually needs.

### Level 2 — Intermediate

```java
// File: ThinNotificationPlusCallback.java -- the event shrinks to just an id;
// a consumer that needs details fetches them separately, on demand.
import java.util.*;
import java.util.function.*;

public class ThinNotificationPlusCallback {
    record Order(int id, String customerEmail, double total, List<String> items) {}
    record OrderPlacedNotification(int orderId) {} // deliberately thin

    static class OrderServiceApi { // stands in for a REST call back to order-service
        private final Map<Integer, Order> database = new HashMap<>();
        void seed(Order o) { database.put(o.id(), o); }
        Order getOrder(int orderId) {
            System.out.println("  [order-service API] GET /orders/" + orderId + " -- fetching current, authoritative data");
            return database.get(orderId);
        }
    }

    static class Channel {
        List<Consumer<OrderPlacedNotification>> subscribers = new ArrayList<>();
        void subscribe(Consumer<OrderPlacedNotification> h) { subscribers.add(h); }
        void publish(OrderPlacedNotification n) { subscribers.forEach(s -> s.accept(n)); }
    }

    public static void main(String[] args) {
        OrderServiceApi api = new OrderServiceApi();
        api.seed(new Order(42, "alice@example.com", 99.90, List.of("widget", "gadget")));

        Channel orderEvents = new Channel();
        orderEvents.subscribe(notification -> {
            System.out.println("[audit-log] recorded event for orderId=" + notification.orderId() + " -- no callback needed, id is enough");
        });
        orderEvents.subscribe(notification -> {
            System.out.println("[email-service] needs full details for orderId=" + notification.orderId());
            Order full = api.getOrder(notification.orderId()); // callback, ONLY because this consumer needs it
            System.out.println("  [email-service] sending confirmation to " + full.customerEmail());
        });

        orderEvents.publish(new OrderPlacedNotification(42)); // the event itself never carries the email address
    }
}
```

**How to run:** `javac ThinNotificationPlusCallback.java && java ThinNotificationPlusCallback` (JDK 17+).

Expected output:
```
[audit-log] recorded event for orderId=42 -- no callback needed, id is enough
[email-service] needs full details for orderId=42
  [order-service API] GET /orders/42 -- fetching current, authoritative data
  [email-service] sending confirmation to alice@example.com
```

The `audit-log` subscriber does its job without ever touching the API; `email-service` makes the callback only because it actually needs the data — the cost of fetching full details is paid only by consumers that need it.

### Level 3 — Advanced

```java
// File: FreshnessAdvantage.java -- shows the thin-notification approach's key advantage:
// the callback always returns the CURRENT state, even if it changed after the event fired.
import java.util.*;
import java.util.function.*;

public class FreshnessAdvantage {
    record Order(int id, String status) {}
    record OrderPlacedNotification(int orderId) {}

    static class OrderServiceApi {
        private final Map<Integer, Order> database = new HashMap<>();
        void seed(Order o) { database.put(o.id(), o); }
        void updateStatus(int orderId, String newStatus) { // simulates the order changing AFTER the event fired
            database.put(orderId, new Order(orderId, newStatus));
        }
        Order getOrder(int orderId) { return database.get(orderId); }
    }

    public static void main(String[] args) {
        OrderServiceApi api = new OrderServiceApi();
        api.seed(new Order(42, "PLACED"));

        OrderPlacedNotification event = new OrderPlacedNotification(42); // fired when status was "PLACED"
        System.out.println("Event fired when order status was: PLACED");

        // time passes; the order is cancelled BEFORE the consumer gets around to processing the event
        api.updateStatus(42, "CANCELLED");
        System.out.println("...but by the time the consumer processes the event, the order was CANCELLED.");

        Order current = api.getOrder(event.orderId()); // the callback fetches CURRENT state, not a stale copy
        System.out.println("Consumer callback fetched CURRENT status: " + current.status());
        if (current.status().equals("CANCELLED")) {
            System.out.println("Consumer correctly skips shipping -- a fat event with the OLD 'PLACED' status baked in would have missed this entirely.");
        }
    }
}
```

**How to run:** `javac FreshnessAdvantage.java && java FreshnessAdvantage` (JDK 17+).

Expected output:
```
Event fired when order status was: PLACED
...but by the time the consumer processes the event, the order was CANCELLED.
Consumer callback fetched CURRENT status: CANCELLED
Consumer correctly skips shipping -- a fat event with the OLD 'PLACED' status baked in would have missed this entirely.
```

## 6. Walkthrough

1. **Level 1** — `Channel.publish` sends the entire `Order` record, including fields (`customerEmail`, `items`) that the single subscribed `audit-log` handler never reads; every subscriber, regardless of need, pays the full serialization and transmission cost of every field.
2. **Level 2, shrinking the event** — `OrderPlacedNotification` carries only `orderId`; `Channel.publish` now sends this thin object instead of a full `Order`.
3. **Level 2, two subscribers, two needs** — `audit-log`'s handler uses `notification.orderId()` directly and never calls `api.getOrder`; `email-service`'s handler *does* call `api.getOrder(notification.orderId())`, making an explicit synchronous callback to fetch exactly the data it needs, when it needs it.
4. **Level 2, the cost distribution** — the printed log shows the API call (`GET /orders/42`) happening only once, triggered only by the subscriber that actually required the full order — `audit-log` never triggers it, demonstrating that thin notifications let each consumer pay only for what it uses.
5. **Level 3, the timing gap** — `event` is captured with `orderId=42` at a moment when the order's status is `"PLACED"`; the notification itself carries no status information at all, only the id.
6. **Level 3, state changing after the event fires** — `api.updateStatus(42, "CANCELLED")` simulates the order being cancelled sometime between the event being published and a consumer getting around to processing it (a very realistic gap in an asynchronous system with any backlog at all).
7. **Level 3, the callback returns truth, not history** — `api.getOrder(event.orderId())` is called *after* the cancellation, and because it queries the order service's live data rather than reading a snapshot baked into the event, it correctly returns `"CANCELLED"` — a consumer relying on this callback naturally sees the current state and can react correctly, whereas a design that had embedded `"PLACED"` directly into the event payload at publish time would have handed the consumer stale, since-invalidated information with no way to know it had gone stale.

## 7. Gotchas & takeaways

> **Gotcha:** the callback that fetches full details reintroduces exactly the synchronous coupling problem asynchronous messaging exists to avoid — if the producing service is down when a consumer tries to fetch details, that consumer is now blocked or failing on a live dependency, even though the original notification was delivered asynchronously and successfully; event notification trades payload freshness for a reintroduced availability dependency.

- Event notification keeps events deliberately thin — usually just an id and event type — with consumers calling back to the producer's API for anything more.
- This keeps the producer's own data as the single source of truth, so consumers needing details always see current state, never a stale copy embedded in an old event.
- Consumers that only need to know *that* something happened avoid the cost of a callback entirely; only consumers needing actual data pay that cost.
- The trade-off is a reintroduced synchronous dependency on the producer's availability for any consumer that does need the details — the exact coupling asynchronous messaging is meant to avoid, just deferred to callback time.
- [Event-carried state transfer](0129-event-carried-state-transfer.md) is the alternative for when that reintroduced coupling, or the callback load on the producer, is unacceptable.
