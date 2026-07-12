---
card: microservices
gi: 74
slug: spring-application-events-applicationeventpublisher-for-in-p
title: "Spring application events (ApplicationEventPublisher) for in-process domain events"
---

## 1. What it is

`ApplicationEventPublisher` is core Spring's own publish/subscribe mechanism, available in any Spring application — no Spring Modulith or messaging infrastructure required. A bean publishes a plain Java object as an event via `publisher.publishEvent(event)`, and any other bean with a method annotated `@EventListener` (matching the event's type) is invoked by the Spring container, synchronously by default, all within the same JVM. It is the general-purpose building block underneath [Spring Modulith's module events](0072-spring-modulith-domain-events-between-modules.md), which layer module-boundary awareness, `@ApplicationModuleListener`, and the durable event publication registry on top of this same core mechanism.

## 2. Why & when

Even inside a single Spring service, one class calling another class's method directly is a compile-time dependency: the caller needs the callee's type on its classpath, and adding a second thing that needs to react to the same trigger means editing the caller again. `ApplicationEventPublisher` removes that coupling entirely within one JVM: a service publishes `OrderPlaced` and moves on, with zero knowledge of who (if anyone) is listening. This is the plain-Spring version of the same decoupling principle used throughout this section — [strategic vs tactical DDD's domain events](0054-domain-events.md), and the module-scoped version in [Spring Modulith](0072-spring-modulith-domain-events-between-modules.md).

Use it whenever a piece of logic inside one Spring bean needs to trigger a reaction in another bean, but the two don't need a tight, synchronous, return-value-carrying relationship — sending a confirmation email after an order is saved, invalidating a cache after a price changes, or updating an audit log after any state-changing action, all without the originating code needing to know those reactions exist.

## 3. Core concept

The publisher calls one method on the framework-provided `ApplicationEventPublisher`; the container looks up every matching `@EventListener` method and invokes each one — the publisher and listener classes need not know about each other at all.

```java
// Publisher
@Service
class OrderService {
    private final ApplicationEventPublisher publisher;
    void placeOrder(String id) {
        // ... save the order ...
        publisher.publishEvent(new OrderPlaced(id)); // fire and forget
    }
}

// Listener -- lives anywhere, no dependency on OrderService
@Component
class NotificationListener {
    @EventListener
    void on(OrderPlaced event) { /* send confirmation */ }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrderService publishes an event through Spring's ApplicationEventPublisher; the container looks up and invokes every matching @EventListener method synchronously">
  <rect x="20" y="65" width="150" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="95" y="104" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">publisher.publishEvent(...)</text>

  <rect x="230" y="65" width="180" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Container</text>
  <text x="320" y="104" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">finds matching listeners</text>

  <rect x="470" y="15" width="150" height="45" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="545" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">NotificationListener</text>
  <rect x="470" y="130" width="150" height="45" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="545" y="157" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">AuditLogListener</text>

  <line x1="170" y1="92" x2="230" y2="92" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="410" y1="80" x2="470" y2="40" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="410" y1="105" x2="470" y2="150" stroke="#6db33f" stroke-width="1.5"/>
</svg>

One publish call fans out to every matching listener; neither side knows about the other's class.

## 5. Runnable example

Scenario: `OrderService` needs to notify listeners when an order is placed, first with a direct, tightly-coupled call, then decoupled using a plain-Java stand-in for `ApplicationEventPublisher`/`@EventListener`, then extended to show that a listener's exception, by default, propagates back to the publisher synchronously — a key behavior to understand before relying on this mechanism.

### Level 1 — Basic

```java
// File: DirectCall.java -- OrderService calls NotificationListener
// directly -- a compile-time dependency, no event mechanism involved.
import java.util.*;

public class DirectCall {
    static class NotificationListener {
        void handle(String orderId) { System.out.println("[Notification] sent for " + orderId); }
    }

    static class OrderService {
        NotificationListener notifications = new NotificationListener(); // hard dependency
        void placeOrder(String id) {
            System.out.println("[Order] placed " + id);
            notifications.handle(id);
        }
    }

    public static void main(String[] args) {
        new OrderService().placeOrder("ORD-1");
    }
}
```

**How to run:** `javac DirectCall.java && java DirectCall` (JDK 17+).

Expected output:
```
[Order] placed ORD-1
[Notification] sent for ORD-1
```

### Level 2 — Intermediate

```java
// File: EventPublisherSimulated.java -- a minimal stand-in for Spring's
// ApplicationEventPublisher / @EventListener mechanism: publishers and
// listeners are wired only through a shared event type, never each other.
import java.util.*;
import java.util.function.Consumer;

public class EventPublisherSimulated {
    record OrderPlaced(String orderId) {} // the "event" -- a plain object, no framework base class needed

    static class SimulatedApplicationEventPublisher { // stands in for Spring's real interface
        private List<Consumer<OrderPlaced>> listeners = new ArrayList<>();
        void registerListener(Consumer<OrderPlaced> listener) { listeners.add(listener); } // simulates @EventListener wiring
        void publishEvent(OrderPlaced event) {
            for (Consumer<OrderPlaced> listener : listeners) listener.accept(event); // synchronous, in order, by default
        }
    }

    static class OrderService {
        SimulatedApplicationEventPublisher publisher;
        OrderService(SimulatedApplicationEventPublisher publisher) { this.publisher = publisher; }
        void placeOrder(String id) {
            System.out.println("[Order] placed " + id);
            publisher.publishEvent(new OrderPlaced(id)); // OrderService knows NOTHING about who listens
        }
    }

    public static void main(String[] args) {
        SimulatedApplicationEventPublisher publisher = new SimulatedApplicationEventPublisher();
        publisher.registerListener(e -> System.out.println("[Notification] sent for " + e.orderId())); // @EventListener #1
        publisher.registerListener(e -> System.out.println("[AuditLog] recorded order " + e.orderId())); // @EventListener #2

        new OrderService(publisher).placeOrder("ORD-1");
    }
}
```

**How to run:** `javac EventPublisherSimulated.java && java EventPublisherSimulated` (JDK 17+).

Expected output:
```
[Order] placed ORD-1
[Notification] sent for ORD-1
[AuditLog] recorded order ORD-1
```

Adding the second listener (`AuditLog`) required zero changes to `OrderService` — only a new `registerListener` call, which in real Spring is just a new `@Component` class with an `@EventListener` method picked up automatically by component scanning.

### Level 3 — Advanced

```java
// File: SynchronousExceptionPropagation.java -- demonstrate a key default
// behavior: listeners run SYNCHRONOUSLY on the publisher's own thread, so
// a listener that throws propagates the exception straight back to the
// PUBLISHER, potentially skipping any listeners registered after it.
import java.util.*;
import java.util.function.Consumer;

public class SynchronousExceptionPropagation {
    record OrderPlaced(String orderId) {}

    static class SimulatedApplicationEventPublisher {
        private List<Consumer<OrderPlaced>> listeners = new ArrayList<>();
        void registerListener(Consumer<OrderPlaced> listener) { listeners.add(listener); }
        void publishEvent(OrderPlaced event) {
            for (Consumer<OrderPlaced> listener : listeners) {
                listener.accept(event); // if this throws, remaining listeners in the list do NOT run
            }
        }
    }

    static class OrderService {
        SimulatedApplicationEventPublisher publisher;
        OrderService(SimulatedApplicationEventPublisher publisher) { this.publisher = publisher; }
        void placeOrder(String id) {
            System.out.println("[Order] placed " + id);
            try {
                publisher.publishEvent(new OrderPlaced(id));
                System.out.println("[Order] placeOrder completed normally");
            } catch (RuntimeException e) {
                System.out.println("[Order] placeOrder saw listener failure propagate back: " + e.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        SimulatedApplicationEventPublisher publisher = new SimulatedApplicationEventPublisher();
        publisher.registerListener(e -> System.out.println("[Notification] sent for " + e.orderId()));
        publisher.registerListener(e -> { throw new RuntimeException("email server unreachable"); }); // faulty listener
        publisher.registerListener(e -> System.out.println("[AuditLog] recorded order " + e.orderId())); // NEVER reached

        new OrderService(publisher).placeOrder("ORD-1");
    }
}
```

**How to run:** `javac SynchronousExceptionPropagation.java && java SynchronousExceptionPropagation` (JDK 17+).

Expected output:
```
[Order] placed ORD-1
[Notification] sent for ORD-1
[Order] placeOrder saw listener failure propagate back: email server unreachable
```

Note that `[AuditLog] recorded order ORD-1` never prints — the faulty second listener's exception stopped the loop before the third listener ever ran, and the exception surfaced all the way back into `placeOrder`'s own `catch` block.

## 6. Walkthrough

1. **Level 1** — `OrderService.placeOrder` calls `notifications.handle` directly, printing both lines in strict sequence. `OrderService` holds a field of the concrete `NotificationListener` type — a compile-time dependency that would need editing to add a second reactor.
2. **Level 2 — decoupling via events** — `SimulatedApplicationEventPublisher.registerListener` collects listener functions (standing in for Spring scanning the container for `@EventListener` methods matching `OrderPlaced`); `publishEvent` invokes each one in registration order. `OrderService` now depends only on `publisher.publishEvent(new OrderPlaced(id))` — no reference to `NotificationListener` or any other listener class at all. `main` registers two listeners before calling `placeOrder`, and both fire — proving a second reactor (`AuditLog`) was added with zero change to `OrderService`.
3. **Level 3 — tracing the synchronous, in-order call chain** — three listeners are registered: `Notification` (succeeds), a deliberately faulty lambda that throws `RuntimeException("email server unreachable")`, and `AuditLog` (would succeed, but never gets the chance). `main` calls `placeOrder("ORD-1")`, which prints `[Order] placed ORD-1`, then calls `publisher.publishEvent(...)` inside a try block.
4. **Inside `publishEvent`** — the `for` loop invokes the `Notification` listener first, which prints its line successfully. The loop then invokes the faulty second listener, which throws immediately — and because Java's `for-each` loop has no exception handling of its own, the exception propagates straight out of `publishEvent`, skipping the `AuditLog` listener entirely; it is never reached.
5. **Back in `placeOrder`** — the `catch (RuntimeException e)` block catches the propagated exception and prints `[Order] placeOrder saw listener failure propagate back: email server unreachable` — demonstrating that, with Spring's default synchronous event dispatch, a listener's failure is not isolated from the publisher: it surfaces directly in the calling code, and it can prevent listeners registered after the failing one from ever running.
6. **What this means for real Spring code** — this default behavior is exactly why a production system with critical, independent reactions to the same event (as `Notification` and `AuditLog` are meant to be here) typically marks listeners `@Async` (running on a separate thread, so one listener's failure can't block or fail another) or, for stronger delivery guarantees across a process crash, upgrades to [Spring Modulith's `@ApplicationModuleListener`](0072-spring-modulith-domain-events-between-modules.md) with its durable event publication registry, rather than relying on plain synchronous `@EventListener` for anything where independent, guaranteed delivery matters.

## 7. Gotchas & takeaways

> **Gotcha:** `@EventListener` methods run synchronously, on the publisher's own thread, by default. A slow or failing listener directly slows down or breaks the code that published the event — exactly as `placeOrder`'s exception handling had to account for in Level 3. Mark a listener `@Async` (with async support enabled) if it should not block or affect the publisher.

- `ApplicationEventPublisher.publishEvent` and `@EventListener` are core Spring features — no extra dependency needed, unlike Spring Modulith's module-aware listener machinery.
- Publisher and listener share only the event's type; neither needs a reference to the other's class, which is what makes this useful for decoupling in-process reactions.
- By default, listeners run synchronously and in registration order, and an exception in one listener both stops later listeners in that dispatch and propagates back to the publisher — plan around this explicitly rather than assuming isolation.
- This is the foundational mechanism [Spring Modulith's module events](0072-spring-modulith-domain-events-between-modules.md) build on, adding module-boundary enforcement and (via `@ApplicationModuleListener` with the event publication registry) durable, retry-on-crash delivery.
- Keep published events as simple, immutable data describing something that already happened (`OrderPlaced`, not a command) — the same discipline covered in [domain events](0054-domain-events.md).
