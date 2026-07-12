---
card: microservices
gi: 72
slug: spring-modulith-domain-events-between-modules
title: "Spring Modulith domain events between modules"
---

## 1. What it is

Spring Modulith lets modules inside the same modular monolith communicate through **domain events** instead of direct method calls: one module publishes an event (using ordinary Spring `ApplicationEventPublisher`), and any other module reacts to it with a method annotated `@ApplicationModuleListener` — with no compile-time dependency between the publishing and listening modules at all. Crucially, Spring Modulith also provides an **event publication registry** that persists a record of each event's delivery to each listener, so that if the process crashes after publishing but before a listener finishes handling it, the event is retried automatically once the application restarts, instead of being silently lost.

## 2. Why & when

A direct method call from one module into another's public API, as covered in [application modules & verification](0071-spring-modulith-application-modules-verification.md), is still a *compile-time* dependency — the calling module needs the callee's class on its classpath, and a change to that method's signature can break the caller immediately. Domain events remove even that coupling: the publishing module doesn't need to know which modules, if any, are listening, and new listeners can be added later without ever touching the publisher. This mirrors, at the in-process modular-monolith level, exactly the same decoupling that a real message broker gives you between separate microservices — which is precisely why it makes a later extraction into real services (see [decomposing a monolith incrementally](0066-decomposing-a-monolith-incrementally.md)) far less disruptive: the communication pattern doesn't have to change, just its transport.

Use module events for any interaction where one module needs to *react* to something that happened in another module, but doesn't need an immediate, synchronous answer back — order placement triggering a notification, or a shipment being dispatched triggering an inventory adjustment.

## 3. Core concept

The publisher publishes and moves on; the listener runs separately, and the registry guarantees the listener eventually runs, even across a crash and restart.

```
OrderService.placeOrder()
        |
   publish(OrderPlaced)  -----> [Event Publication Registry: recorded, not yet completed]
        |
        v
(returns immediately -- publisher does NOT wait for listeners)

@ApplicationModuleListener
NotificationModule.on(OrderPlaced)   <-- runs separately, marks registry entry COMPLETE when done
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrderService publishes an OrderPlaced event through the registry; NotificationModule listens and marks completion; a crash before completion causes a retry on restart">
  <rect x="20" y="20" width="170" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="105" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">publishes OrderPlaced</text>

  <rect x="235" y="20" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Event Publication</text>
  <text x="325" y="58" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Registry</text>

  <rect x="460" y="20" width="160" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">NotificationModule</text>
  <text x="540" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@ApplicationModuleListener</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="415" y1="45" x2="460" y2="45" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="235" y="120" width="180" height="70" rx="5" fill="#1c2430" stroke="#e6edf3"/>
  <text x="325" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">crash before listener</text>
  <text x="325" y="158" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">completes -&gt;</text>
  <text x="325" y="174" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">retried on restart</text>
  <line x1="325" y1="70" x2="325" y2="120" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3"/>
</svg>

The registry sits between publisher and listener, guaranteeing delivery survives a crash.

## 5. Runnable example

Scenario: `OrderService` needs `NotificationModule` and `InventoryModule` to react to an order being placed. First model direct, tightly-coupled calls; then decouple with an in-process event bus mimicking `@ApplicationModuleListener`; then add a persisted registry so an incomplete listener is retried, simulating a crash-and-restart.

### Level 1 — Basic

```java
// File: DirectCalls.java -- OrderService calls Notification and
// Inventory DIRECTLY -- tight coupling, and OrderService now needs to
// know about every module that ever wants to react to an order.
import java.util.*;

public class DirectCalls {
    static class NotificationModule {
        void sendConfirmation(String orderId) { System.out.println("[Notification] confirmation sent for " + orderId); }
    }
    static class InventoryModule {
        void reserveStock(String orderId) { System.out.println("[Inventory] stock reserved for " + orderId); }
    }
    static class OrderService {
        NotificationModule notifications = new NotificationModule(); // OrderService knows about BOTH
        InventoryModule inventory = new InventoryModule();

        void placeOrder(String orderId) {
            System.out.println("[Order] placed " + orderId);
            notifications.sendConfirmation(orderId); // direct call
            inventory.reserveStock(orderId);          // direct call
        }
    }

    public static void main(String[] args) {
        new OrderService().placeOrder("ORD-1");
    }
}
```

**How to run:** `javac DirectCalls.java && java DirectCalls` (JDK 17+).

Expected output:
```
[Order] placed ORD-1
[Notification] confirmation sent for ORD-1
[Inventory] stock reserved for ORD-1
```

Adding a third module that also needs to react to order placement means editing `OrderService` again — it has a compile-time dependency on every reactor.

### Level 2 — Intermediate

```java
// File: DecoupledViaEvents.java -- OrderService publishes an OrderPlaced
// event and knows NOTHING about who listens. Listener modules register
// themselves with the event bus, mimicking @ApplicationModuleListener.
import java.util.*;
import java.util.function.Consumer;

public class DecoupledViaEvents {
    record OrderPlaced(String orderId) {}

    static class SimpleEventBus { // stands in for Spring's ApplicationEventPublisher
        List<Consumer<OrderPlaced>> listeners = new ArrayList<>();
        void register(Consumer<OrderPlaced> listener) { listeners.add(listener); }
        void publish(OrderPlaced event) {
            for (Consumer<OrderPlaced> listener : listeners) listener.accept(event);
        }
    }

    static class OrderService {
        SimpleEventBus bus;
        OrderService(SimpleEventBus bus) { this.bus = bus; }
        void placeOrder(String orderId) {
            System.out.println("[Order] placed " + orderId);
            bus.publish(new OrderPlaced(orderId)); // OrderService doesn't know WHO is listening
        }
    }

    public static void main(String[] args) {
        SimpleEventBus bus = new SimpleEventBus();
        bus.register(e -> System.out.println("[Notification] confirmation sent for " + e.orderId())); // @ApplicationModuleListener
        bus.register(e -> System.out.println("[Inventory] stock reserved for " + e.orderId()));         // @ApplicationModuleListener

        new OrderService(bus).placeOrder("ORD-1");
    }
}
```

**How to run:** `javac DecoupledViaEvents.java && java DecoupledViaEvents` (JDK 17+).

Expected output:
```
[Order] placed ORD-1
[Notification] confirmation sent for ORD-1
[Inventory] stock reserved for ORD-1
```

Same output as Level 1, but `OrderService` now depends only on `SimpleEventBus` and `OrderPlaced` — a third listener could be registered without touching `OrderService`'s source at all.

### Level 3 — Advanced

```java
// File: EventRegistryWithRetry.java -- add a persisted-style registry:
// each listener's completion is tracked per event, and any listener that
// hasn't completed (simulating a crash mid-handling) is RETRIED on the
// next "restart" -- mirroring Spring Modulith's event publication log.
import java.util.*;
import java.util.function.Consumer;

public class EventRegistryWithRetry {
    record OrderPlaced(String orderId) {}
    record RegistryEntry(OrderPlaced event, String listenerName, boolean completed) {}

    static class DurableEventBus {
        Map<String, Consumer<OrderPlaced>> listeners = new LinkedHashMap<>();
        List<RegistryEntry> registry = new ArrayList<>(); // simulates the persisted publication log

        void register(String name, Consumer<OrderPlaced> listener) { listeners.put(name, listener); }

        void publish(OrderPlaced event) {
            for (String name : listeners.keySet()) {
                registry.add(new RegistryEntry(event, name, false)); // recorded BEFORE the listener runs
            }
        }

        void runPendingListeners(Set<String> simulateFailureFor) {
            for (int i = 0; i < registry.size(); i++) {
                RegistryEntry entry = registry.get(i);
                if (entry.completed()) continue;
                if (simulateFailureFor.contains(entry.listenerName())) {
                    System.out.println("  [CRASH before " + entry.listenerName() + " completed handling " + entry.event().orderId() + "]");
                    continue; // stays incomplete in the registry -- will be retried
                }
                listeners.get(entry.listenerName()).accept(entry.event());
                registry.set(i, new RegistryEntry(entry.event(), entry.listenerName(), true));
            }
        }
    }

    public static void main(String[] args) {
        DurableEventBus bus = new DurableEventBus();
        bus.register("Notification", e -> System.out.println("[Notification] confirmation sent for " + e.orderId()));
        bus.register("Inventory", e -> System.out.println("[Inventory] stock reserved for " + e.orderId()));

        bus.publish(new OrderPlaced("ORD-1"));

        System.out.println("First run (Inventory crashes before completing):");
        bus.runPendingListeners(Set.of("Inventory"));

        System.out.println("Application restarts, retries pending entries:");
        bus.runPendingListeners(Set.of()); // no failure this time -- Inventory's retry succeeds
    }
}
```

**How to run:** `javac EventRegistryWithRetry.java && java EventRegistryWithRetry` (JDK 17+).

Expected output:
```
First run (Inventory crashes before completing):
[Notification] confirmation sent for ORD-1
  [CRASH before Inventory completed handling ORD-1]
Application restarts, retries pending entries:
[Inventory] stock reserved for ORD-1
```

## 6. Walkthrough

1. **Level 1** — `OrderService.placeOrder` calls `notifications.sendConfirmation` and `inventory.reserveStock` directly, one after another, printing all three lines in strict sequence. `OrderService` holds a field for each collaborator, meaning every new module that wants to react to order placement requires editing `OrderService` itself.
2. **Level 2 — decoupling with an event bus** — `SimpleEventBus.register` collects listener functions in a list; `publish` simply iterates and invokes every registered listener with the event. `OrderService` now depends only on `bus.publish(new OrderPlaced(orderId))` — it has no field, no import, no knowledge of `NotificationModule` or `InventoryModule` at all. `main` registers two listeners as lambdas (standing in for two separate `@ApplicationModuleListener`-annotated methods in two separate modules) before calling `placeOrder`, and the output sequence is identical to Level 1 — proving the decoupling changed *how* the modules connect, not *what* happens.
3. **Level 3 — durability against a crash** — `DurableEventBus.publish` no longer calls listeners immediately. Instead, it records one `RegistryEntry` per registered listener, each starting `completed=false` — this mirrors Spring Modulith writing a row to its event publication table *before* attempting delivery, so the intent to deliver is never lost even if the process dies immediately after.
4. **First run, simulating a crash** — `runPendingListeners(Set.of("Inventory"))` walks the registry; for the `Notification` entry, it calls the real listener, prints its confirmation line, and marks that entry `completed=true`. For the `Inventory` entry, because `"Inventory"` is in the `simulateFailureFor` set, the method prints a `[CRASH ...]` diagnostic line and `continue`s — deliberately leaving that entry `completed=false`, standing in for the application dying mid-handling before the listener finished.
5. **Second run, simulating a restart** — `runPendingListeners(Set.of())` (an empty failure set, meaning nothing crashes this time) walks the registry again. The `Notification` entry is already `completed=true`, so the `continue` at the top of the loop skips it — it is *not* re-delivered, avoiding a duplicate notification. The `Inventory` entry is still `completed=false` from the first run, so this time its listener actually runs, printing `[Inventory] stock reserved for ORD-1` and finally marking that entry complete.
6. **Why this matters in a real Spring Modulith app** — this is exactly the failure mode the real event publication registry protects against: without it, a plain in-memory event bus (as in Level 2) would simply lose the `Inventory` reaction forever if the process crashed between `Notification`'s completion and `Inventory`'s — no error, no retry, just a silently missed stock reservation. The persisted registry, replayed on startup, is what guarantees eventual delivery.

## 7. Gotchas & takeaways

> **Gotcha:** module event listeners in Spring Modulith run, by default, in the *same transaction* as the publisher unless configured otherwise — meaning a listener throwing an exception can roll back the publisher's own transaction too. Understand your chosen transaction phase (e.g. `TransactionPhase.AFTER_COMMIT`) before assuming listener failures are fully isolated from the publishing module.

- Publishing a domain event removes even the compile-time dependency that a direct public-API call still has — the publisher never needs to know who, if anyone, is listening.
- The event publication registry is what makes delivery durable across a crash: an event whose listener hasn't completed is retried automatically, and a completed listener is never re-invoked for the same event.
- This pattern is a deliberate rehearsal for microservices: the same "publish and let listeners react independently" shape works whether the listener is in the same process (Spring Modulith) or a different service reached over a message broker after [decomposing a monolith incrementally](0066-decomposing-a-monolith-incrementally.md).
- Keep events focused on facts that already happened (`OrderPlaced`, not `PlaceOrder`) — see [domain events](0054-domain-events.md) for the broader DDD reasoning behind that naming discipline.
- Don't rely on listener *ordering* unless you've explicitly designed for it — treat each listener as independent, since that independence is the whole point of decoupling them from the publisher in the first place.
