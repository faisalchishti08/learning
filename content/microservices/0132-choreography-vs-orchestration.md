---
card: microservices
gi: 132
slug: choreography-vs-orchestration
title: "Choreography vs orchestration"
---

## 1. What it is

Choreography and orchestration are two opposite ways to coordinate a multi-step process spanning several services. In choreography, each service reacts to events independently, with no central coordinator — the overall sequence emerges from the sum of everyone's individual reactions, like dancers each following their own cues. In orchestration, one central component explicitly directs each step, telling each service what to do and when, like a conductor directing an orchestra.

## 2. Why & when

Choreography keeps services maximally decoupled — no service needs to know the others exist, only which events it cares about — which scales well for simple chains and keeps any single service from becoming a bottleneck or single point of failure for the whole process. But as a process grows more steps, more branches, or more compensating logic for partial failures, choreography's implicit, emergent flow becomes genuinely hard to see, trace, or reason about: there is no single place to look to understand "what happens when an order is placed," only a scattered set of independent handlers across many services.

Orchestration trades that decoupling for visibility and control: one place holds the entire process definition, making it easy to see the whole flow, add timeouts, and handle partial failures with explicit compensating steps — at the cost of the orchestrator becoming a real dependency every participating service now has, and a central point that must scale and stay available. Choose choreography for simple, mostly-linear event chains with few branches; choose orchestration once a process has enough steps, conditional branches, or failure-handling complexity that "read the code in one place" becomes more valuable than "no service depends on a coordinator."

## 3. Core concept

Choreography wires services together purely through published events, each service's handler independently deciding what to do next and publishing its own follow-up event; orchestration wires services together through a central process definition that explicitly invokes each step and interprets its result before deciding the next one.

```java
// choreography: each service reacts independently, no one is "in charge"
orderService.on("OrderPlaced", e -> paymentService.chargeAndPublish(e.orderId()));
paymentService.on("PaymentCharged", e -> shippingService.scheduleAndPublish(e.orderId()));

// orchestration: ONE place explicitly drives the whole sequence
void placeOrderSaga(int orderId) {
    paymentService.charge(orderId);      // orchestrator calls each step directly
    shippingService.schedule(orderId);   // and decides what happens next itself
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Choreography: three services react to each other's events in a decentralized chain with no coordinator. Orchestration: a central orchestrator explicitly calls each service in sequence and tracks the process state">
  <text x="150" y="20" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Choreography</text>
  <rect x="30" y="40" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="75" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Order Svc</text>
  <rect x="150" y="40" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="195" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Payment Svc</text>
  <rect x="270" y="40" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="315" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Shipping Svc</text>
  <line x1="120" y1="57" x2="148" y2="57" stroke="#8b949e" marker-end="url(#arr18)"/>
  <line x1="240" y1="57" x2="268" y2="57" stroke="#8b949e" marker-end="url(#arr18)"/>
  <text x="195" y="95" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">event-driven, no coordinator</text>

  <text x="480" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Orchestration</text>
  <rect x="410" y="150" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="174" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Order Saga (orchestrator)</text>
  <rect x="410" y="35" width="70" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="445" y="55" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Payment</text>
  <rect x="500" y="35" width="70" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="535" y="55" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Shipping</text>
  <line x1="460" y1="148" x2="445" y2="67" stroke="#8b949e" marker-end="url(#arr18)"/>
  <line x1="500" y1="148" x2="535" y2="67" stroke="#8b949e" marker-end="url(#arr18)"/>
  <text x="480" y="210" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">one place drives every step explicitly</text>

  <defs>
    <marker id="arr18" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Choreography's flow emerges from independent reactions; orchestration's flow is explicit and centrally visible.

## 5. Runnable example

Scenario: a three-step order-placement process (charge payment, reserve inventory, schedule shipping) implemented first via choreography, then via orchestration for direct comparison, and finally extended under orchestration to add explicit compensation (rollback) logic when a later step fails — something choreography makes much harder to express.

### Level 1 — Basic

```java
// File: ChoreographyFlow.java -- each service reacts independently; the OVERALL
// sequence emerges from the sum of these independent reactions, visible nowhere as one thing.
import java.util.*;
import java.util.function.*;

public class ChoreographyFlow {
    static class EventBus {
        Map<String, List<Consumer<String>>> handlers = new HashMap<>();
        void on(String eventType, Consumer<String> handler) { handlers.computeIfAbsent(eventType, k -> new ArrayList<>()).add(handler); }
        void publish(String eventType, String payload) {
            System.out.println("  event: " + eventType + "(" + payload + ")");
            handlers.getOrDefault(eventType, List.of()).forEach(h -> h.accept(payload));
        }
    }

    public static void main(String[] args) {
        EventBus bus = new EventBus();

        // payment-service reacts to OrderPlaced -- NOBODY told it to, it just subscribed
        bus.on("OrderPlaced", orderId -> {
            System.out.println("[payment-service] charging order " + orderId);
            bus.publish("PaymentCharged", orderId);
        });
        // shipping-service reacts to PaymentCharged -- has NO idea order-service even exists
        bus.on("PaymentCharged", orderId -> {
            System.out.println("[shipping-service] scheduling shipment for order " + orderId);
            bus.publish("ShipmentScheduled", orderId);
        });

        System.out.println("order-service publishes ONE event, with no idea what happens after:");
        bus.publish("OrderPlaced", "42");
    }
}
```

**How to run:** `javac ChoreographyFlow.java && java ChoreographyFlow` (JDK 17+).

The full three-step outcome (charge, then ship) emerges purely from independently-registered handlers reacting to each other's events; there is no single method or file that describes "what happens when an order is placed" — you'd have to read every service's handlers to reconstruct the flow.

### Level 2 — Intermediate

```java
// File: OrchestrationFlow.java -- the SAME three-step process, now with ONE place
// that explicitly drives every step and can be read top-to-bottom as the whole process.
public class OrchestrationFlow {
    static class PaymentService { void charge(int orderId) { System.out.println("[payment-service] charging order " + orderId); } }
    static class ShippingService { void schedule(int orderId) { System.out.println("[shipping-service] scheduling shipment for order " + orderId); } }

    static class OrderSaga { // the orchestrator: ONE place holds the entire process definition
        PaymentService paymentService = new PaymentService();
        ShippingService shippingService = new ShippingService();

        void placeOrder(int orderId) {
            System.out.println("[order-saga] starting placeOrder for " + orderId);
            paymentService.charge(orderId);      // step 1, explicit
            shippingService.schedule(orderId);   // step 2, explicit
            System.out.println("[order-saga] placeOrder complete for " + orderId);
        }
    }

    public static void main(String[] args) {
        new OrderSaga().placeOrder(42);
    }
}
```

**How to run:** `javac OrchestrationFlow.java && java OrchestrationFlow` (JDK 17+).

Expected output:
```
[order-saga] starting placeOrder for 42
[payment-service] charging order 42
[shipping-service] scheduling shipment for 42
[order-saga] placeOrder complete for 42
```

Reading `OrderSaga.placeOrder` top to bottom tells you the entire process in one place — a stark contrast with Level 1, where the same information was scattered across two independently-registered handlers.

### Level 3 — Advanced

```java
// File: OrchestrationWithCompensation.java -- orchestration's real advantage: explicit
// compensating actions when a LATER step fails, rolling back what already succeeded.
public class OrchestrationWithCompensation {
    static class PaymentService {
        void charge(int orderId) { System.out.println("[payment-service] charged order " + orderId); }
        void refund(int orderId) { System.out.println("[payment-service] REFUNDED order " + orderId + " (compensating action)"); }
    }
    static class InventoryService {
        boolean reserve(int orderId) {
            System.out.println("[inventory-service] attempting to reserve stock for order " + orderId);
            return false; // simulates: out of stock, this step FAILS
        }
    }
    static class ShippingService {
        void schedule(int orderId) { System.out.println("[shipping-service] scheduling shipment for order " + orderId); }
    }

    static class OrderSaga {
        PaymentService paymentService = new PaymentService();
        InventoryService inventoryService = new InventoryService();
        ShippingService shippingService = new ShippingService();

        boolean placeOrder(int orderId) {
            System.out.println("[order-saga] step 1: charge payment");
            paymentService.charge(orderId);

            System.out.println("[order-saga] step 2: reserve inventory");
            boolean reserved = inventoryService.reserve(orderId);
            if (!reserved) {
                System.out.println("[order-saga] step 2 FAILED -- explicitly compensating already-completed step 1");
                paymentService.refund(orderId); // explicit rollback of the step that already succeeded
                System.out.println("[order-saga] placeOrder ABORTED and fully compensated for order " + orderId);
                return false;
            }

            System.out.println("[order-saga] step 3: schedule shipping");
            shippingService.schedule(orderId);
            return true;
        }
    }

    public static void main(String[] args) {
        boolean success = new OrderSaga().placeOrder(42);
        System.out.println("placeOrder succeeded: " + success);
    }
}
```

**How to run:** `javac OrchestrationWithCompensation.java && java OrchestrationWithCompensation` (JDK 17+).

Expected output:
```
[order-saga] step 1: charge payment
[payment-service] charged order 42
[order-saga] step 2: reserve inventory
[inventory-service] attempting to reserve stock for order 42
[order-saga] step 2 FAILED -- explicitly compensating already-completed step 1
[payment-service] REFUNDED order 42 (compensating action)
[order-saga] placeOrder ABORTED and fully compensated for order 42
placeOrder succeeded: false
```

## 6. Walkthrough

1. **Level 1** — `bus.publish("OrderPlaced", "42")` is the only call `main` makes; everything that follows — the payment charge, then the shipment scheduling — happens because `payment-service` and `shipping-service` each independently registered a handler for an event they cared about, with no code anywhere explicitly sequencing "first payment, then shipping."
2. **Level 1, the visibility cost** — to know that placing an order eventually triggers a shipment, a reader has to find and read *both* independently-registered handlers and mentally trace the event names connecting them; there's no single function that represents "the order placement process."
3. **Level 2, the orchestrator as the single source of truth** — `OrderSaga.placeOrder` calls `paymentService.charge(orderId)` and then `shippingService.schedule(orderId)` directly and explicitly, in the exact order they should happen; reading this one method fully explains the process.
4. **Level 2, the coupling trade-off** — `OrderSaga` now holds direct references to both `PaymentService` and `ShippingService` and calls their methods directly; unlike Level 1's `payment-service`, which only needed to know about an `OrderPlaced` event's *name*, the orchestrator here needs to know both services' concrete APIs.
5. **Level 3, a failure partway through** — `inventoryService.reserve(orderId)` returns `false`, simulating an out-of-stock condition discovered only *after* payment has already been successfully charged in step 1.
6. **Level 3, explicit compensation** — because `OrderSaga.placeOrder` has full visibility into which steps have already run, it can explicitly call `paymentService.refund(orderId)` the moment it detects step 2's failure — undoing exactly the work that had already completed, in a single, readable place.
7. **Level 3, why choreography would make this harder** — implementing the equivalent rollback in a choreographed design would require `inventory-service` to publish some kind of `InventoryReservationFailed` event, and then `payment-service` would need its *own* handler subscribed to that event to trigger its own refund — spreading the compensation logic for one failure across two more independently-registered handlers, on top of the two that implemented the happy path, making the full picture of "what happens on failure" even more scattered than the happy path already was in Level 1.

## 7. Gotchas & takeaways

> **Gotcha:** an orchestrator that calls services synchronously (as this simplified example does, for clarity) reintroduces the very coupling and availability chain that [asynchronous messaging](0111-asynchronous-messaging-model.md) exists to avoid; real orchestration frameworks (like a saga implemented with Spring State Machine, or Temporal-style workflow engines) typically drive the process via asynchronous commands and event replies, keeping orchestration's visibility benefit without full synchronous coupling between the orchestrator and every participant.

- Choreography coordinates services through independent, event-driven reactions with no central coordinator; the overall process emerges from the sum of individual handlers.
- Orchestration coordinates services through one central component that explicitly invokes each step and decides what happens next based on each step's result.
- Choreography keeps services maximally decoupled but makes the overall process flow hard to see, trace, or reason about as complexity grows.
- Orchestration makes the entire process visible and easy to reason about in one place, including explicit compensating (rollback) logic for partial failures, at the cost of the orchestrator becoming a real dependency for every participant.
- Neither is universally correct: favor choreography for simple, mostly-linear event chains, and orchestration once branching, compensation, or process visibility needs outweigh the value of full decoupling.
