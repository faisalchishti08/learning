---
card: system-design
gi: 201
slug: cqrs-command-query-responsibility-segregation
title: CQRS (command-query responsibility segregation)
---

## 1. What it is

**CQRS (Command-Query Responsibility Segregation)** splits a system's write path (**commands**, which change state) from its read path (**queries**, which only return data) into separate models — often separate classes, separate APIs, and sometimes even separate databases — instead of using one model for both.

## 2. Why & when

A single model that handles both reads and writes usually ends up shaped as a compromise: normalized enough to write consistently, but not shaped the way any particular screen wants to read it, so every query does extra joins and filtering. CQRS removes the compromise. The write side keeps the data normalized and enforces business rules; the read side keeps one or more denormalized views, each shaped exactly for a specific query, with no joins needed at read time.

This adds real complexity: two models to maintain, and often a delay between a write and its effect showing up in the read model (the same eventual-consistency tradeoff as [event-driven architecture](0200-event-driven-architecture.md), which is the usual mechanism that keeps the two in sync). Use CQRS when read and write load are very different (many more reads than writes, or the reverse), when read queries need shapes too different from the write model to serve efficiently, or when you are already using [event sourcing](0202-event-sourcing.md), which pairs naturally with CQRS. Do not reach for it in a typical CRUD service where one model serves both sides fine.

## 3. Core concept

- **Command side.** Commands (`PlaceOrder`, `CancelOrder`) go through a write model that enforces business rules and invariants, then persists to a normalized store — this side optimizes for correctness, not for read convenience.
- **Query side.** Queries (`GetOrderSummary`, `GetOrderHistory`) read from a separate, denormalized read model — a shape built specifically to answer that query fast, with no joins or business-rule checks at read time.
- **Synchronization.** After a command succeeds on the write side, something must update the read model to reflect the change — usually by publishing an event (see [event-driven architecture](0200-event-driven-architecture.md)) that a projector consumes to update the read store.
- **Eventual consistency between the two sides.** There is a window, however small, where the write model has the new state but the read model has not caught up yet. Callers reading immediately after writing may see stale data — this must be an accepted tradeoff, not a surprise.
- **Not always two databases.** CQRS is about separating the *models* (classes/responsibilities). Using two separate physical databases is a common but optional extra step, useful when the read and write sides have very different scaling needs.

## 4. Diagram

```
                      COMMAND SIDE                          QUERY SIDE
   Client -- PlaceOrder cmd -->  +----------------+
                                  | Write Model     |
                                  | (normalized,    |
                                  |  enforces rules)|
                                  +--------+--------+
                                           |
                                    OrderPlaced event
                                           |
                                           v
                                  +----------------+
                                  |   Projector     |
                                  | (updates the     |
                                  |  read model)      |
                                  +--------+--------+
                                           |
                                           v
                                  +----------------+
   Client <-- OrderSummary  ---- | Read Model      |
   (GetOrderSummary query)       | (denormalized,   |
                                  |  fast to read)   |
                                  +----------------+
```
*Caption: a command flows through the write model, which emits an event. A projector consumes that event to update a separate, query-shaped read model. Reads never touch the write model at all.*

## 5. Runnable example

**Level 1 — Basic.** A single write model and a separate, differently shaped read model, kept in sync manually after each command.

**Level 2 — Intermediate.** The write model publishes an event; a projector listens and updates the read model — closer to the real, decoupled mechanism.

**Level 3 — Advanced.** Show the eventual-consistency gap: a query issued immediately after a command can return stale data until the projector catches up.

```java
// CqrsDemo.java
import java.util.*;
import java.util.function.*;

public class CqrsDemo {

    // ---------- Command side: normalized write model ----------
    record Order(String id, String customerId, List<String> items, String status) {}

    static class OrderWriteModel {
        Map<String, Order> orders = new HashMap<>();
        List<Consumer<Order>> subscribers = new ArrayList<>(); // Level 2: event subscribers

        Order placeOrder(String id, String customerId, List<String> items) {
            Order order = new Order(id, customerId, items, "PLACED");
            orders.put(id, order); // enforces the write-side invariant: order must have an id
            System.out.println("  [write model] order " + id + " placed and persisted (normalized form)");
            for (Consumer<Order> sub : subscribers) sub.accept(order); // Level 2: notify projectors
            return order;
        }
    }

    // ---------- Query side: denormalized, query-shaped read model ----------
    record OrderSummaryView(String orderId, String customerId, int itemCount, String status) {}

    static class OrderReadModel {
        Map<String, OrderSummaryView> summaries = new HashMap<>();

        OrderSummaryView getSummary(String orderId) {
            return summaries.get(orderId); // no joins, no business rules - just a lookup
        }
    }

    // ---------- Level 1: manual sync (naive, tightly coupled) ----------
    static void manualSync(OrderWriteModel write, OrderReadModel read, Order order) {
        read.summaries.put(order.id(),
            new OrderSummaryView(order.id(), order.customerId(), order.items().size(), order.status()));
        System.out.println("  [manual sync] read model updated directly after write");
    }

    // ---------- Level 2: projector listens to events, decoupled from the write model ----------
    static class Projector {
        OrderReadModel readModel;
        int delayTicks; // simulates processing lag before the projector catches up
        Projector(OrderReadModel readModel, int delayTicks) {
            this.readModel = readModel;
            this.delayTicks = delayTicks;
        }
        void onOrderPlaced(Order order) {
            System.out.println("  [projector] received OrderPlaced event for " + order.id() +
                " - will update read model after simulated delay");
            // In Level 3 this update happens AFTER the delay, not immediately.
        }
        void applyNow(Order order) {
            readModel.summaries.put(order.id(),
                new OrderSummaryView(order.id(), order.customerId(), order.items().size(), order.status()));
            System.out.println("  [projector] read model updated for " + order.id());
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - manual sync between write and read models:");
        OrderWriteModel write1 = new OrderWriteModel();
        OrderReadModel read1 = new OrderReadModel();
        Order o1 = write1.placeOrder("ORD-1", "cust-1", List.of("mouse", "keyboard"));
        manualSync(write1, read1, o1);
        System.out.println("  query result: " + read1.getSummary("ORD-1"));

        System.out.println("\nLevel 2 - write model publishes event, projector updates read model:");
        OrderWriteModel write2 = new OrderWriteModel();
        OrderReadModel read2 = new OrderReadModel();
        Projector projector = new Projector(read2, 0);
        write2.subscribers.add(projector::applyNow); // event subscription, decoupled from write logic
        Order o2 = write2.placeOrder("ORD-2", "cust-2", List.of("monitor"));
        System.out.println("  query result: " + read2.getSummary("ORD-2"));

        System.out.println("\nLevel 3 - eventual consistency gap: query right after command, before projector runs:");
        OrderWriteModel write3 = new OrderWriteModel();
        OrderReadModel read3 = new OrderReadModel();
        Projector delayedProjector = new Projector(read3, 2);
        write3.subscribers.add(delayedProjector::onOrderPlaced); // only logs, does not apply yet
        Order o3 = write3.placeOrder("ORD-3", "cust-3", List.of("desk", "chair", "lamp"));
        System.out.println("  query IMMEDIATELY after command: " + read3.getSummary("ORD-3") + "  <- still null, stale!");
        System.out.println("  ...simulated delay passes, projector now applies the update...");
        delayedProjector.applyNow(o3);
        System.out.println("  query AFTER projector catches up: " + read3.getSummary("ORD-3"));
    }
}
```

**How to run:** `java CqrsDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `write1.placeOrder(...)` stores a full `Order` in the normalized write model. `manualSync(...)` is then called explicitly right after, building a differently-shaped `OrderSummaryView` and putting it in the read model. This works, but the write model and the sync logic are tightly coupled — every new command handler must remember to call the sync step.
2. **Level 2:** `write2.subscribers.add(projector::applyNow)` registers the projector as an event subscriber, the same pattern used in [event-driven architecture](0200-event-driven-architecture.md). `write2.placeOrder(...)` now calls every subscriber automatically after persisting — the write model does not need to know a read model exists at all, only that "something" is subscribed.
3. **Level 3** makes the timing gap visible. `write3.placeOrder(...)` runs and its subscriber, `delayedProjector::onOrderPlaced`, only **logs** that the event arrived — it deliberately does not update `read3` yet, standing in for a real, asynchronous projector still processing its queue.
4. **`read3.getSummary("ORD-3")` is called immediately after the command returns**, and prints `null` — the read model has genuinely not caught up. This is the eventual-consistency window CQRS introduces: the command has already succeeded, but a query issued in that instant sees stale (in this case, missing) data.
5. **Only after `delayedProjector.applyNow(o3)` runs** — simulating the projector finally processing the event — does `read3.getSummary("ORD-3")` return the populated `OrderSummaryView`. In a real system this catch-up typically takes milliseconds to seconds, not the deliberate pause shown here, but the gap always exists.

## 7. Gotchas & takeaways

> **Gotcha:** a client that writes data and then immediately reads it back through the query side (e.g. redirecting to a "your order" confirmation page right after placing it) can see stale or missing data if the read model has not caught up yet. Either read from the write side for that specific "read-your-own-write" case, or design the UI to tolerate a short delay.

- CQRS is a split of responsibility, not automatically a split of database technology — start with two classes/models in the same database, and only split the physical storage if you have a measured reason (e.g. the read side needs a search index while the write side needs strict consistency).
- Pair CQRS with [event-driven architecture](0200-event-driven-architecture.md) for the synchronization step — a projector subscribing to domain events is the standard way to keep the read model current.
- Do not add CQRS to a simple CRUD service with balanced read/write load and no complex query shapes — the two-model overhead has to earn its keep.
- CQRS and [event sourcing](0202-event-sourcing.md) are often mentioned together but are independent choices — you can use CQRS with a normal write database, and you can use event sourcing with a single combined read/write model.
