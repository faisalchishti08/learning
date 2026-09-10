---
card: system-design
gi: 203
slug: saga-orchestration-vs-choreography
title: Saga (orchestration vs choreography)
---

## 1. What it is

A **saga** is a way to keep data consistent across multiple [microservices](0196-microservices.md) when no single database transaction can span them. A saga runs a sequence of local transactions, one per service; if a later step fails, the saga runs **compensating transactions** to undo the effects of the steps that already succeeded. There are two ways to coordinate a saga: **orchestration** (one central coordinator tells each service what to do) and **choreography** (each service reacts to events from the previous one, with no central coordinator).

## 2. Why & when

In a monolith, "place an order, charge the payment, reserve stock" is one ACID transaction — either all three happen or none do. Once those three steps are three separate services with three separate databases, there is no single transaction to wrap them in. If the payment step fails after the order was already created, the order is left in an inconsistent state unless something explicitly fixes it.

A saga solves this by making every step reversible: each service does its local transaction and also defines how to undo it (`ReleaseStock` undoes `ReserveStock`). Use a saga whenever a business process spans multiple services and must end up consistent even if a later step fails — this is a required pattern for correctness in most multi-service systems, not an optional optimization. Choose orchestration when the process has complex branching logic and you want it visible in one place; choose choreography when the steps are simple and you want to avoid a single coordinator becoming a bottleneck or a single point of failure.

## 3. Core concept

- **Local transaction per step.** Each service commits its own local database transaction — `OrderService` creates the order, `PaymentService` charges the card — with no distributed transaction ever spanning services.
- **Compensating transaction.** For every forward step, there is a defined undo: `CancelOrder` undoes `CreateOrder`, `RefundPayment` undoes `ChargePayment`. If step 3 fails, the saga runs the compensations for steps 2 and 1, in reverse order.
- **Orchestration.** A single **orchestrator** service explicitly calls each step in sequence and decides what to do on failure — the workflow logic lives in one place, easy to read and reason about, but the orchestrator itself becomes a critical dependency every step relies on.
- **Choreography.** Each service reacts to an event from the previous step and publishes its own event when done — `OrderService` publishes `OrderCreated`, `PaymentService` subscribes to it, charges the card, and publishes `PaymentCharged` or `PaymentFailed`. No single service knows the whole workflow; it emerges from each service's local reactions.
- **Eventual consistency during the saga.** Between the first step and either full completion or full compensation, the system is in a temporary, partially-applied state — this is visible to anyone who reads the data mid-saga, and callers must be designed to tolerate it.

## 4. Diagram

```
  ORCHESTRATION                              CHOREOGRAPHY

  +-------------+                            OrderService
  | Orchestrator|                                 |
  +------+------+                          publishes OrderCreated
         |                                         |
   1. call CreateOrder ---> OrderService            v
   2. call ChargePayment -> PaymentService    PaymentService (subscribes)
         |  (fails)                            charges card... FAILS
   3. call CompensatePayment (n/a, never ran)        |
   4. call CancelOrder ----> OrderService      publishes PaymentFailed
                                                       |
   orchestrator decides the                            v
   whole flow, step by step                    OrderService (subscribes)
                                                 receives PaymentFailed,
                                                 runs its OWN compensation:
                                                 cancels the order itself
```
*Caption: orchestration has one place that knows the whole flow and issues every step. Choreography has no such place — each service only knows how to react to the event just before it.*

## 5. Runnable example

**Level 1 — Basic.** An orchestrated saga: a central coordinator calls each step and, on failure, runs compensations in reverse order.

**Level 2 — Intermediate.** The same business flow implemented as choreography: each service reacts to the previous service's event.

**Level 3 — Advanced.** Orchestration with a partial failure deeper in the chain, showing multiple compensations running in the correct reverse order.

```java
// SagaDemo.java
import java.util.*;
import java.util.function.*;

public class SagaDemo {

    // ---------- Level 1: orchestrated saga ----------
    static class OrderService {
        boolean createOrder(String orderId) { System.out.println("    [OrderService] order " + orderId + " created"); return true; }
        void cancelOrder(String orderId) { System.out.println("    [OrderService] COMPENSATE: order " + orderId + " cancelled"); }
    }
    static class PaymentService {
        boolean charge(String orderId, boolean shouldFail) {
            if (shouldFail) { System.out.println("    [PaymentService] charge FAILED for " + orderId); return false; }
            System.out.println("    [PaymentService] charged for " + orderId);
            return true;
        }
        void refund(String orderId) { System.out.println("    [PaymentService] COMPENSATE: refunded " + orderId); }
    }
    static class InventoryService {
        boolean reserveStock(String orderId, boolean shouldFail) {
            if (shouldFail) { System.out.println("    [InventoryService] reserve FAILED for " + orderId); return false; }
            System.out.println("    [InventoryService] stock reserved for " + orderId);
            return true;
        }
        void releaseStock(String orderId) { System.out.println("    [InventoryService] COMPENSATE: stock released for " + orderId); }
    }

    static class Orchestrator {
        OrderService orders = new OrderService();
        PaymentService payments = new PaymentService();
        InventoryService inventory = new InventoryService();

        void runSaga(String orderId, boolean paymentFails, boolean stockFails) {
            List<Runnable> compensations = new ArrayList<>();

            System.out.println("  step 1: create order");
            orders.createOrder(orderId);
            compensations.add(() -> orders.cancelOrder(orderId));

            System.out.println("  step 2: charge payment");
            if (!payments.charge(orderId, paymentFails)) {
                System.out.println("  saga failed at step 2 -> running compensations in reverse:");
                Collections.reverse(compensations);
                compensations.forEach(Runnable::run);
                return;
            }
            compensations.add(() -> payments.refund(orderId));

            System.out.println("  step 3: reserve stock");
            if (!inventory.reserveStock(orderId, stockFails)) {
                System.out.println("  saga failed at step 3 -> running compensations in reverse:");
                Collections.reverse(compensations);
                compensations.forEach(Runnable::run);
                return;
            }

            System.out.println("  saga completed successfully - all steps committed");
        }
    }

    // ---------- Level 2: choreographed saga - same flow, event-reactive ----------
    static void choreographedFlow(boolean paymentFails) {
        System.out.println("  OrderService creates order and publishes OrderCreated");
        System.out.println("    -> PaymentService subscribed to OrderCreated");
        if (paymentFails) {
            System.out.println("    [PaymentService] charge FAILED, publishes PaymentFailed");
            System.out.println("      -> OrderService subscribed to PaymentFailed");
            System.out.println("      [OrderService] reacts to PaymentFailed: cancels its own order (self-compensation)");
        } else {
            System.out.println("    [PaymentService] charged, publishes PaymentCharged");
            System.out.println("      -> InventoryService subscribed to PaymentCharged");
            System.out.println("      [InventoryService] reserves stock, publishes StockReserved (saga complete)");
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - orchestrated saga, failure at step 2 (payment):");
        new Orchestrator().runSaga("ORD-1", true, false);

        System.out.println("\nLevel 2 - choreographed saga, same failure scenario:");
        choreographedFlow(true);

        System.out.println("\nLevel 3 - orchestrated saga, failure at step 3 (inventory), two compensations run:");
        new Orchestrator().runSaga("ORD-2", false, true);
    }
}
```

**How to run:** `java SagaDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `runSaga("ORD-1", paymentFails=true, stockFails=false)` runs step 1, `orders.createOrder(...)`, which succeeds, and its compensation (`orders.cancelOrder(...)`) is added to the `compensations` list in case anything later fails.
2. Step 2 calls `payments.charge(...)` with `shouldFail=true`, so it returns `false`. The saga stops advancing right there — step 3 never runs. `Collections.reverse(compensations)` flips the list (it currently only has one entry, the order's compensation), and the loop runs it: `orders.cancelOrder("ORD-1")`.
3. **Level 2** models the exact same failure with no orchestrator at all. `OrderService` creates the order and only publishes an event — it has no idea `PaymentService` even exists. `PaymentService`, subscribed to that event, fails and publishes `PaymentFailed`. `OrderService`, separately subscribed to `PaymentFailed`, reacts by cancelling its own order — this is "self-compensation": each service undoes its own step in response to a failure event, rather than a coordinator telling it to.
4. **Level 3** runs a second saga, `runSaga("ORD-2", paymentFails=false, stockFails=true)`, where payment succeeds but stock reservation fails. By the time step 3 fails, `compensations` holds **two** entries: cancel-order (added after step 1) and refund-payment (added after step 2).
5. `Collections.reverse(compensations)` puts refund-payment first and cancel-order second — compensations always run in the **reverse** order of the original steps, so the most recently completed step is undone first. The output shows `payments.refund("ORD-2")` running before `orders.cancelOrder("ORD-2")`, which matches how a real saga must unwind: undo the newest change first, in case an earlier compensation depends on a later one already being undone.

## 7. Gotchas & takeaways

> **Gotcha:** compensations are not automatic rollbacks — you must write and test them explicitly for every step, and they must be idempotent (safe to run twice), because the same failure-handling logic that triggers a compensation can itself fail partway and need to retry.

- A saga guarantees eventual consistency, not the atomicity a single database transaction gives you — there is always a window where the system is partially updated, visible to anyone reading the data mid-saga.
- Orchestration centralizes the workflow logic (easy to read, easy to test as one unit) but makes the orchestrator a dependency every step relies on; choreography removes that single dependency but makes the overall flow harder to see in one place, since it is scattered across every service's event handlers.
- Prefer choreography for short, linear flows with few steps; prefer orchestration once the flow has real branching, retries, or timeouts that are easier to express as explicit code in one place.
- Pair a saga with the [transactional outbox](0204-transactional-outbox.md) pattern for each step that both updates its local database and needs to publish an event — otherwise a crash between the local commit and the event publish can silently break the saga.
