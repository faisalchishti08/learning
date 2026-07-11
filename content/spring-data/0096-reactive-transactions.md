---
card: spring-data
gi: 96
slug: reactive-transactions
title: "Reactive transactions"
---

## 1. What it is

Reactive transactions use `ReactiveTransactionManager` and `TransactionalOperator` instead of the classic (thread-bound) `PlatformTransactionManager` and `@Transactional` annotation — because a reactive pipeline can hop between threads as it composes, a transaction can't be tied to "the current thread" the way blocking transactions are; it's instead tied to the reactive `Context` that flows through the `Mono`/`Flux` chain itself.

```java
@Autowired TransactionalOperator transactionalOperator;

Mono<Void> placeOrder(Order order, List<LineItem> items) {
    return orderRepository.save(order)
        .then(lineItemRepository.saveAll(items).then())
        .as(transactionalOperator::transactional); // wraps the WHOLE reactive chain in one transaction
}
```

## 2. Why & when

Every earlier card in the R2DBC section built single, independent reactive operations; the transactional-query-methods card (from the JPA section) explained why multiple repository calls sometimes need to commit or roll back together — that same need exists here, but the classic `@Transactional`-plus-thread-local mechanism can't work, since reactive execution isn't pinned to one thread. `TransactionalOperator` is the reactive-aware replacement.

Reach for reactive transactions specifically when:

- A business operation spans multiple reactive repository calls (saving an order and its line items, for instance) that must commit or roll back together — exactly the same motivation as the JPA transactional-query-methods card, adapted to a non-blocking pipeline.
- You're wrapping a `Mono`/`Flux` chain and need the whole thing — regardless of how many threads it hops across during composition — to participate in one atomic database transaction.
- `@Transactional` is available as an annotation on reactive methods too (Spring detects the reactive return type and applies reactive transaction semantics automatically) — but understanding `TransactionalOperator` explains what's happening underneath, and is necessary when composing transactional behavior programmatically rather than declaratively.

## 3. Core concept

```
 Classic (blocking) @Transactional:
   -- transaction bound to the CURRENT THREAD via a ThreadLocal
   -- works because the whole method runs on ONE thread, start to finish

 Reactive transactions:
   -- a Mono/Flux chain can execute across MULTIPLE threads as it's subscribed to and composed
   -- so the transaction is carried in the Reactor "Context" that flows WITH the chain, not a ThreadLocal
   -- TransactionalOperator.transactional(mono) wraps a reactive chain so it participates in one transaction
      regardless of which thread executes which part of it
```

Reactive transactions travel with the data flow itself (the `Context`), rather than being pinned to whichever thread happens to be executing at a given moment.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A blocking transaction is bound to one thread for the whole method, while a reactive transaction travels with the Context across thread hops">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Blocking @Transactional</text>
  <rect x="20" y="30" width="580" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="310" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ONE thread, start to finish -- transaction bound via ThreadLocal</text>

  <text x="20" y="100" fill="#e6edf3" font-size="10" font-family="sans-serif">Reactive TransactionalOperator</text>
  <rect x="20" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="133" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">thread A: save(order)</text>
  <rect x="230" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="133" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">thread B: saveAll(items)</text>
  <text x="420" y="133" fill="#8b949e" font-size="8" font-family="sans-serif">-- Context carries the tx --</text>
</svg>

The blocking model relies on one thread owning the whole method; the reactive model carries the transaction in the `Context` so it survives thread hops.

## 5. Runnable example

The scenario: placing an order with line items, evolving from separate uncoordinated reactive calls (the same inconsistency risk the JPA transactional-query-methods card demonstrated), to a simulated `TransactionalOperator` wrapping both calls atomically, to a rollback scenario proving the whole chain reverts together.

### Level 1 — Basic

Model two independent, uncoordinated reactive calls — each "commits" on its own, mirroring the JPA card's Level 1 problem but in reactive form.

```java
import java.util.*;
import java.util.concurrent.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }
class LineItem { long orderId; String description; LineItem(long orderId, String d) { this.orderId = orderId; description = d; } }

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    CompletableFuture<Order> save(Order order) {
        return CompletableFuture.supplyAsync(() -> { db.put(order.id, order); System.out.println("  [committed] order saved"); return order; });
    }
}
class LineItemRepository {
    List<LineItem> db = new ArrayList<>();
    CompletableFuture<Void> saveAll(List<LineItem> items) {
        return CompletableFuture.supplyAsync(() -> {
            for (LineItem li : items) if (li.description.equals("INVALID")) throw new RuntimeException("Invalid: " + li.description);
            db.addAll(items);
            System.out.println("  [committed] " + items.size() + " line items saved");
            return null;
        });
    }
}

public class ReactiveTxLevel1 {
    // NO transactional coordination -- each repository call is independent, exactly like the JPA card's Level 1.
    static CompletableFuture<Void> placeOrderUncoordinated(OrderRepository orderRepo, LineItemRepository itemRepo,
                                                             Order order, List<LineItem> items) {
        return orderRepo.save(order).thenCompose(saved -> itemRepo.saveAll(items));
    }

    public static void main(String[] args) throws Exception {
        OrderRepository orderRepo = new OrderRepository();
        LineItemRepository itemRepo = new LineItemRepository();

        try {
            placeOrderUncoordinated(orderRepo, itemRepo, new Order(1, "PENDING"),
                List.of(new LineItem(1, "Widget"), new LineItem(1, "INVALID"))).get();
        } catch (Exception e) {
            System.out.println("Failed: " + e.getCause().getMessage());
        }

        System.out.println("Order 1 in DB? " + orderRepo.db.containsKey(1L)); // TRUE -- inconsistent!
    }
}
```

How to run: `java ReactiveTxLevel1.java`

Just like the blocking JPA card's equivalent example, the order is already committed by the time the line-item save fails — reactive composition alone (`.thenCompose`) provides *sequencing*, not *atomicity*; nothing here rolls the order save back when the line-item save fails.

### Level 2 — Intermediate

Wrap both calls with a simulated `TransactionalOperator` that only commits both changes if the whole chain succeeds, rolling back everything otherwise.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }
class LineItem { long orderId; String description; LineItem(long orderId, String d) { this.orderId = orderId; description = d; } }

// Stands in for org.springframework.transaction.reactive.TransactionalOperator
class TransactionalOperator {
    static <T> CompletableFuture<T> transactional(Map<Long, Order> orderDb, List<LineItem> itemDb,
                                                    Function<PendingChanges, CompletableFuture<T>> work) {
        PendingChanges changes = new PendingChanges();
        return work.apply(changes).handle((result, ex) -> {
            if (ex == null) {
                orderDb.putAll(changes.pendingOrders);
                itemDb.addAll(changes.pendingItems);
                System.out.println("  [transaction committed]");
                return result;
            } else {
                System.out.println("  [transaction rolled back] " + ex.getCause().getMessage());
                throw new CompletionException(ex.getCause());
            }
        });
    }
}
class PendingChanges { Map<Long, Order> pendingOrders = new HashMap<>(); List<LineItem> pendingItems = new ArrayList<>(); }

public class ReactiveTxLevel2 {
    static CompletableFuture<Void> placeOrder(PendingChanges tx, Order order, List<LineItem> items) {
        return CompletableFuture.supplyAsync(() -> { tx.pendingOrders.put(order.id, order); return null; })
            .thenCompose(v -> CompletableFuture.supplyAsync(() -> {
                for (LineItem li : items) if (li.description.equals("INVALID")) throw new RuntimeException("Invalid: " + li.description);
                tx.pendingItems.addAll(items);
                return null;
            }));
    }

    public static void main(String[] args) throws Exception {
        Map<Long, Order> orderDb = new HashMap<>();
        List<LineItem> itemDb = new ArrayList<>();

        try {
            TransactionalOperator.transactional(orderDb, itemDb, tx ->
                placeOrder(tx, new Order(1, "PENDING"), List.of(new LineItem(1, "Widget"), new LineItem(1, "INVALID")))
            ).get();
        } catch (Exception e) {
            System.out.println("Caught: " + e.getCause().getMessage());
        }

        System.out.println("Order 1 in DB? " + orderDb.containsKey(1L)); // FALSE now -- consistent!
    }
}
```

How to run: `java ReactiveTxLevel2.java`

`orderDb.containsKey(1L)` now prints `false` — the order save was buffered in `PendingChanges` and only committed to the real `orderDb` if the whole chain (order save + line-item save) succeeded, matching how `TransactionalOperator.transactional(mono)` in a real reactive pipeline only commits the whole chain's changes together, rolling back everything if any step throws.

### Level 3 — Advanced

Show the success path alongside the rollback path, confirming both order and line items commit together when everything succeeds, and both revert together when anything fails — the full "all or nothing" guarantee.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }
class LineItem { long orderId; String description; LineItem(long orderId, String d) { this.orderId = orderId; description = d; } }

class TransactionalOperator {
    static <T> CompletableFuture<T> transactional(Map<Long, Order> orderDb, List<LineItem> itemDb,
                                                    Function<PendingChanges, CompletableFuture<T>> work) {
        PendingChanges changes = new PendingChanges();
        return work.apply(changes).handle((result, ex) -> {
            if (ex == null) {
                orderDb.putAll(changes.pendingOrders);
                itemDb.addAll(changes.pendingItems);
                return result;
            } else {
                throw new CompletionException(ex.getCause());
            }
        });
    }
}
class PendingChanges { Map<Long, Order> pendingOrders = new HashMap<>(); List<LineItem> pendingItems = new ArrayList<>(); }

public class ReactiveTxLevel3 {
    static CompletableFuture<Void> placeOrder(PendingChanges tx, Order order, List<LineItem> items) {
        return CompletableFuture.supplyAsync(() -> { tx.pendingOrders.put(order.id, order); return null; })
            .thenCompose(v -> CompletableFuture.supplyAsync(() -> {
                for (LineItem li : items) if (li.description.equals("INVALID")) throw new RuntimeException("Invalid: " + li.description);
                tx.pendingItems.addAll(items);
                return null;
            }));
    }

    public static void main(String[] args) throws Exception {
        Map<Long, Order> orderDb = new HashMap<>();
        List<LineItem> itemDb = new ArrayList<>();

        // Success path: both order 1 and its (valid) line items should commit TOGETHER.
        TransactionalOperator.transactional(orderDb, itemDb, tx ->
            placeOrder(tx, new Order(1, "PENDING"), List.of(new LineItem(1, "Widget"), new LineItem(1, "Gadget")))
        ).get();
        System.out.println("After success: order=" + orderDb.containsKey(1L) + ", items=" + itemDb.size());

        // Failure path: both order 2 and its line items should ROLL BACK together.
        try {
            TransactionalOperator.transactional(orderDb, itemDb, tx ->
                placeOrder(tx, new Order(2, "PENDING"), List.of(new LineItem(2, "INVALID")))
            ).get();
        } catch (Exception e) {
            System.out.println("Order 2 attempt failed as expected: " + e.getCause().getMessage());
        }
        System.out.println("After failure: order2=" + orderDb.containsKey(2L) + ", total items=" + itemDb.size());
    }
}
```

How to run: `java ReactiveTxLevel3.java`

After the success path, `orderDb.containsKey(1L)` is `true` and `itemDb.size()` is `2` — both committed together. After the failure path, `orderDb.containsKey(2L)` is `false` and `itemDb.size()` stays `2` (unchanged from before the failed attempt) — order 2's attempted save was rolled back along with its invalid line item, leaving the database exactly as it was before that attempt began.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, the success-path call runs: `TransactionalOperator.transactional(orderDb, itemDb, tx -> placeOrder(tx, order1, [Widget, Gadget]))`. Inside, `placeOrder` buffers `order1` into `tx.pendingOrders`, then (since neither line item is `"INVALID"`) buffers both into `tx.pendingItems`, completing without error. Back in `transactional`, `.handle((result, ex) -> ...)` sees `ex == null`, so it commits: `orderDb.putAll(tx.pendingOrders)` and `itemDb.addAll(tx.pendingItems)` run, making both changes visible. The printed check confirms `order=true, items=2`.

Next, the failure-path call runs: `TransactionalOperator.transactional(orderDb, itemDb, tx -> placeOrder(tx, order2, [INVALID]))`. Inside `placeOrder`, `order2` is buffered into a *fresh* `tx.pendingOrders` (a new `PendingChanges` instance, unrelated to the first call's), but the line-item loop finds `"INVALID"` and throws `RuntimeException`. This exception propagates up through the `CompletableFuture` chain into `transactional`'s `.handle(...)`, where `ex` is now non-null — so the commit lines (`orderDb.putAll(...)`, `itemDb.addAll(...)`) never execute at all, and the exception is rethrown wrapped in `CompletionException`. The `catch` block in `main` catches it and prints the expected failure message.

The final printed check confirms `order2=false` (never committed) and `total items=2` (unchanged from the success path — the failed attempt's line item was never added), demonstrating that the second transaction's failure had zero effect on the database, while the first transaction's success remains fully intact.

```
success: placeOrder(order1, [Widget, Gadget]) -> no throw -> commit: orderDb+=order1, itemDb+=2 items
                                                                                  order=true, items=2

failure: placeOrder(order2, [INVALID]) -> throws -> ex != null -> commit SKIPPED entirely
                                                                                  order2=false, items still 2
```

In a real Spring Data R2DBC application, wrapping a reactive chain with `.as(transactionalOperator::transactional)` (or annotating a reactive-returning service method with `@Transactional`, which Spring detects and handles reactively) causes the underlying `ReactiveTransactionManager` to begin a database transaction when the chain is subscribed to, propagate it through the Reactor `Context` across every operator in the chain (regardless of which thread executes which step), and commit only if the entire `Mono`/`Flux` completes successfully — any error signal anywhere in the chain triggers a rollback of every database operation performed within it, exactly mirroring the atomic all-or-nothing guarantee `@Transactional` provides for blocking JPA/JDBC code, adapted to reactive execution's thread-hopping nature.

## 7. Gotchas & takeaways

> Gotcha: `@Transactional` on a reactive method only works correctly if the method's return type is itself reactive (`Mono`/`Flux`) and the *entire* chain of repository calls inside it is also reactive — mixing in a blocking call anywhere inside a method meant to be reactively transactional breaks the mechanism silently, since the reactive `Context` carrying the transaction has no way to reach a blocking call that steps outside the reactive chain entirely.

- Reactive transactions use `ReactiveTransactionManager`/`TransactionalOperator` instead of the classic thread-bound `PlatformTransactionManager`, because reactive execution isn't pinned to one thread.
- The transaction travels with the reactive `Context` that flows through the `Mono`/`Flux` chain, rather than being bound to whichever thread happens to be executing at a given moment.
- `TransactionalOperator.transactional(...)` wraps a reactive chain so every repository call inside it commits or rolls back together — the same atomicity guarantee `@Transactional` provides for blocking code.
- `@Transactional` works on reactive methods too, but requires the entire call chain to stay reactive — any blocking call inserted into the middle breaks the mechanism.
