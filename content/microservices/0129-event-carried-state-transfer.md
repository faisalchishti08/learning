---
card: microservices
gi: 129
slug: event-carried-state-transfer
title: "Event-carried state transfer"
---

## 1. What it is

Event-carried state transfer is publishing enough of an entity's actual data inside the event itself that consumers can do their work using only the event, without ever calling back to the producer — the opposite trade-off from [event notification](0128-event-notification.md), which deliberately keeps events thin and pushes consumers toward a callback.

## 2. Why & when

The callback that event notification relies on reintroduces a synchronous dependency on the producer's availability, and at high volume, can turn a single published event into a flood of API calls back to the producer as every interested consumer fetches details separately. Event-carried state transfer avoids both problems by paying the cost once, at publish time: the producer includes the relevant data directly in the event, so consumers become fully self-sufficient — able to process the event even if the producer is completely unreachable at that moment.

Reach for this style when consumers need substantial data from the event to do their work, when the producer's availability shouldn't gate consumer processing, or when a callback would create unacceptable load on the producer at the system's actual event volume. Accept the trade-off deliberately: consumers now hold a *copy* of data that can drift from the producer's current truth, and every consumer needs its own strategy for handling that staleness.

## 3. Core concept

The event payload includes the fields consumers are expected to need, snapshotted at publish time; a consumer processes the event entirely from that payload, and if it needs the data again later, it relies on a subsequent event (or its own locally cached copy) rather than calling back to the producer.

```java
// the event carries the DATA itself, not just an id
channel.publish("order-events", new OrderPlacedEvent(
    orderId = 42, customerEmail = "alice@example.com", total = 99.90, items = List.of("widget", "gadget")
));

// a consumer processes it fully self-sufficiently -- ZERO calls back to order-service
void onOrderPlaced(OrderPlacedEvent event) {
    sendConfirmationEmail(event.customerEmail(), event.items()); // everything needed is right here
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service publishes an event carrying the full order data; the consumer processes it entirely from the event payload with no callback to order service required" >
  <rect x="20" y="55" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Service</text>

  <rect x="240" y="30" width="180" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">event: OrderPlaced</text>
  <text x="330" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">{ id, email, total,</text>
  <text x="330" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">items } (full data)</text>
  <text x="330" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">self-sufficient</text>

  <rect x="470" y="55" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Email Consumer</text>

  <line x1="160" y1="75" x2="238" y2="75" stroke="#8b949e" marker-end="url(#arr15)"/>
  <line x1="420" y1="75" x2="468" y2="75" stroke="#8b949e" marker-end="url(#arr15)"/>
  <text x="330" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no callback path exists -- nothing goes back to Order Service</text>

  <defs>
    <marker id="arr15" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The event is a complete, self-sufficient snapshot; the consumer needs nothing further from the producer.

## 5. Runnable example

Scenario: an email-confirmation consumer that starts needing a callback to get order details (illustrating the cost this pattern avoids), switches to a fully self-sufficient event carrying the needed data, and finally handles the resulting staleness trade-off by having the consumer maintain its own local read-model built entirely from a stream of these state-carrying events.

### Level 1 — Basic

```java
// File: CallbackRequired.java -- the notification style this pattern replaces, for comparison.
import java.util.*;

public class CallbackRequired {
    record Order(int id, String email, List<String> items) {}
    record OrderPlacedNotification(int orderId) {}

    static Map<Integer, Order> orderDatabase = Map.of(42, new Order(42, "alice@example.com", List.of("widget", "gadget")));

    public static void main(String[] args) {
        OrderPlacedNotification event = new OrderPlacedNotification(42);
        System.out.println("Received thin notification for orderId=" + event.orderId());
        Order order = orderDatabase.get(event.orderId()); // REQUIRES a call back to order-service's data
        System.out.println("Had to fetch order details separately: " + order);
    }
}
```

**How to run:** `javac CallbackRequired.java && java CallbackRequired` (JDK 17+).

The consumer cannot do anything useful with the bare notification alone — it must reach back into `order-service`'s data before it can send a confirmation email.

### Level 2 — Intermediate

```java
// File: SelfSufficientEvent.java -- the event itself carries everything the consumer needs.
import java.util.*;
import java.util.function.*;

public class SelfSufficientEvent {
    record OrderPlacedEvent(int orderId, String customerEmail, double total, List<String> items) {} // full data

    static class Channel {
        List<Consumer<OrderPlacedEvent>> subscribers = new ArrayList<>();
        void subscribe(Consumer<OrderPlacedEvent> h) { subscribers.add(h); }
        void publish(OrderPlacedEvent e) { subscribers.forEach(s -> s.accept(e)); }
    }

    public static void main(String[] args) {
        Channel orderEvents = new Channel();
        orderEvents.subscribe(event -> {
            // NO callback anywhere in this handler -- everything needed came in the event itself
            System.out.println("[email-service] sending confirmation to " + event.customerEmail() + " for items: " + event.items());
        });

        orderEvents.publish(new OrderPlacedEvent(42, "alice@example.com", 99.90, List.of("widget", "gadget")));
        System.out.println("Consumer processed the event with ZERO calls back to order-service.");
    }
}
```

**How to run:** `javac SelfSufficientEvent.java && java SelfSufficientEvent` (JDK 17+).

Expected output:
```
[email-service] sending confirmation to alice@example.com for items: [widget, gadget]
Consumer processed the event with ZERO calls back to order-service.
```

### Level 3 — Advanced

```java
// File: LocalReadModel.java -- a consumer builds and maintains its OWN local copy of
// order data purely from a stream of state-carrying events, never querying order-service.
import java.util.*;

public class LocalReadModel {
    record OrderPlacedEvent(int orderId, String customerEmail, String status, double total) {}
    record OrderStatusChangedEvent(int orderId, String newStatus) {}

    // this consumer's OWN local model, built entirely from events it has seen -- a private copy
    static class ShippingDashboardReadModel {
        private final Map<Integer, Map<String, Object>> localOrderView = new HashMap<>();

        void onOrderPlaced(OrderPlacedEvent e) {
            Map<String, Object> row = new HashMap<>();
            row.put("email", e.customerEmail());
            row.put("status", e.status());
            row.put("total", e.total());
            localOrderView.put(e.orderId(), row);
            System.out.println("[read-model] order " + e.orderId() + " created locally: " + row);
        }

        void onOrderStatusChanged(OrderStatusChangedEvent e) {
            Map<String, Object> row = localOrderView.get(e.orderId());
            if (row == null) { System.out.println("[read-model] status change for unknown order " + e.orderId() + " -- ignored"); return; }
            row.put("status", e.newStatus()); // updates the LOCAL copy -- still no call to order-service
            System.out.println("[read-model] order " + e.orderId() + " status updated locally to " + e.newStatus());
        }

        Object currentView(int orderId) { return localOrderView.get(orderId); }
    }

    public static void main(String[] args) {
        ShippingDashboardReadModel dashboard = new ShippingDashboardReadModel();

        dashboard.onOrderPlaced(new OrderPlacedEvent(42, "alice@example.com", "PLACED", 99.90));
        dashboard.onOrderStatusChanged(new OrderStatusChangedEvent(42, "SHIPPED"));

        System.out.println("Dashboard's current view of order 42 (built ENTIRELY from events): " + dashboard.currentView(42));
        System.out.println("If order-service goes down right now, this dashboard keeps working perfectly.");
    }
}
```

**How to run:** `javac LocalReadModel.java && java LocalReadModel` (JDK 17+).

Expected output:
```
[read-model] order 42 created locally: {email=alice@example.com, status=PLACED, total=99.9}
[read-model] order 42 status updated locally to SHIPPED
Dashboard's current view of order 42 (built ENTIRELY from events): {email=alice@example.com, status=SHIPPED, total=PLACED... 
```

(Actual map key ordering may vary since `HashMap` does not guarantee order; the values shown are what matters.)

## 6. Walkthrough

1. **Level 1** — `orderDatabase.get(event.orderId())` is the callback this pattern eliminates: the notification alone (`orderId=42`) is useless to the consumer without a separate lookup into data owned by another service.
2. **Level 2, the event carries the payload** — `OrderPlacedEvent` includes `customerEmail`, `total`, and `items` directly; `Channel.publish` sends this fully-populated object, and the subscribing handler reads `event.customerEmail()` and `event.items()` straight from the parameter it was handed.
3. **Level 2, the structural difference** — there is no method call anywhere in the Level 2 handler that reaches back toward `order-service`; the handler is complete and self-contained using only its input parameter, which is the defining property of event-carried state transfer.
4. **Level 3, maintaining state across multiple events** — `ShippingDashboardReadModel.localOrderView` is a map the consumer owns and updates entirely itself; `onOrderPlaced` populates a new entry directly from the event's fields, with no database or API call involved.
5. **Level 3, a second event updating the same local copy** — `onOrderStatusChanged` looks up the *existing* local entry by `orderId` and mutates only the `status` field, based purely on the second event's `newStatus` — this models how a consumer keeps its local view current over time by consuming a *stream* of related events, not just a single one.
6. **Level 3, the resulting independence** — `dashboard.currentView(42)` reflects both the original order data and the subsequent status change, entirely reconstructed from events the dashboard consumed — the final printed comment states directly what this buys: if `order-service` becomes completely unreachable, `ShippingDashboardReadModel` keeps functioning against its own already-built local copy, unaffected.
7. **What this trades away** — the dashboard's view is only as current as the last event it has processed; if `order-service`'s actual state changes again before the corresponding event is published and consumed, the local copy is briefly stale — a trade-off event-carried state transfer accepts deliberately, in exchange for never depending on the producer's live availability to do useful work.

## 7. Gotchas & takeaways

> **Gotcha:** every consumer maintaining its own local copy of an entity's data means that entity's schema is now effectively duplicated across every consumer that cares about it — a field rename or type change in the producer needs to consider every consumer's local model, making [event schema versioning](0134-event-schema-versioning.md) meaningfully harder than it is for thin, rarely-changing notification events.

- Event-carried state transfer includes the actual data a consumer needs directly in the event, making the consumer self-sufficient with no callback to the producer required.
- This removes the reintroduced synchronous dependency on producer availability that [event notification](0128-event-notification.md)'s callback creates, at the cost of publishing (and potentially duplicating) more data.
- Consumers can build and maintain their own local read-model entirely from a stream of these events, staying fully functional even if the producer becomes unavailable.
- The trade-off is staleness: a consumer's local copy only reflects events it has already processed, and can briefly diverge from the producer's current live state.
- Because consumers now depend on the event's specific fields directly, changing that event's schema has a wider blast radius than changing a thin notification's schema would.
