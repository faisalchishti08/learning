---
card: spring-data
gi: 68
slug: transactional-query-methods
title: "Transactional query methods"
---

## 1. What it is

Every method on a Spring Data repository interface is already transactional by default: read operations (`findById`, derived queries) run in a read-only transaction, and write operations (`save`, `deleteById`, `@Modifying` queries) run in a read-write one — all wired automatically by the `SimpleJpaRepository` base class. `@Transactional` on your own service methods lets you control the transaction boundary explicitly, typically to wrap *multiple* repository calls in one atomic unit.

```java
@Transactional
public void placeOrder(Order order, List<LineItem> items) {
    orderRepository.save(order);       // same transaction
    lineItemRepository.saveAll(items); // same transaction
} // both commit together, or both roll back together
```

## 2. Why & when

The persistence context card explained dirty checking happens at commit; the locking card explained concurrency control within a transaction. This card is about *where the transaction boundary itself* is drawn — because a repository method alone only guarantees atomicity for that single call, not for a sequence of calls across multiple repositories that need to succeed or fail together.

Reach for an explicit `@Transactional` service method specifically when:

- A business operation spans more than one repository call (e.g., saving an order *and* its line items, or debiting one account while crediting another) and they must commit or roll back as one unit.
- You want to override the default propagation or read-only behavior for a specific operation — e.g., `@Transactional(readOnly = true)` on a service method that only reads, letting the JPA provider apply read-only optimizations across the whole method, not just one call.
- You need to reason about exactly when the persistence context flushes — it flushes at the boundary of the outermost `@Transactional` method, not at the end of each individual repository call nested inside it.

## 3. Core concept

```
 Without an explicit @Transactional wrapping both calls:
   orderRepository.save(order);        -- own transaction, commits immediately
   lineItemRepository.saveAll(items);   -- own SEPARATE transaction
   -- if this second call fails, the order from the first call is ALREADY committed -- inconsistent state!

 With @Transactional on the service method:
   @Transactional
   void placeOrder(...) {
       orderRepository.save(order);        -- joins the ALREADY-OPEN transaction
       lineItemRepository.saveAll(items);   -- joins the SAME transaction
   }
   -- if lineItemRepository.saveAll(...) throws, the WHOLE method rolls back, order save included
```

`@Transactional` on the calling method makes every repository call inside it join one shared transaction, instead of each repository call getting its own.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Without a shared transaction, a failure partway through leaves inconsistent state; with one, everything rolls back together">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">No shared transaction</text>
  <rect x="20" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="110" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">save(order) -&gt; COMMIT</text>
  <rect x="230" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="320" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">saveAll(items) -&gt; FAILS</text>
  <rect x="440" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="530" y="48" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">order committed,</text>
  <text x="530" y="61" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">items missing! (bad)</text>

  <text x="20" y="115" fill="#e6edf3" font-size="10" font-family="sans-serif">@Transactional wraps both</text>
  <rect x="20" y="125" width="590" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="145" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">save(order)  +  saveAll(items)   -- ONE transaction</text>
  <text x="315" y="160" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">either BOTH commit, or BOTH roll back</text>
</svg>

Without a shared transaction, a partial failure leaves inconsistent committed state; wrapping both calls in one `@Transactional` method makes them succeed or fail together.

## 5. Runnable example

The scenario: placing an order that must save both the order and its line items atomically, evolving from separate uncoordinated "transactions" showing the inconsistency risk, to a shared transaction that rolls both back on failure, to a read-only transactional method demonstrating the other common use.

### Level 1 — Basic

Model two independent "transactions" — each repository call commits on its own, with no coordination between them.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }
class LineItem { long orderId; String description; LineItem(long orderId, String d) { this.orderId = orderId; description = d; } }

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    void save(Order o) { db.put(o.id, o); System.out.println("  [committed] order " + o.id + " saved"); }
}

class LineItemRepository {
    List<LineItem> db = new ArrayList<>();
    void saveAll(List<LineItem> items) {
        for (LineItem li : items) {
            if (li.description.equals("INVALID")) throw new RuntimeException("Invalid line item: " + li.description);
        }
        db.addAll(items);
        System.out.println("  [committed] " + items.size() + " line items saved");
    }
}

public class TransactionalLevel1 {
    // NOTE: no @Transactional here -- each repository call is its own separate "transaction"
    static void placeOrderUncoordinated(OrderRepository orderRepo, LineItemRepository itemRepo,
                                          Order order, List<LineItem> items) {
        orderRepo.save(order); // commits immediately, on its own
        itemRepo.saveAll(items); // if THIS throws, the order above is already committed!
    }

    public static void main(String[] args) {
        OrderRepository orderRepo = new OrderRepository();
        LineItemRepository itemRepo = new LineItemRepository();

        try {
            placeOrderUncoordinated(orderRepo, itemRepo, new Order(1, "PENDING"),
                List.of(new LineItem(1, "Widget"), new LineItem(1, "INVALID")));
        } catch (RuntimeException e) {
            System.out.println("Failed: " + e.getMessage());
        }

        System.out.println("Order 1 in DB? " + orderRepo.db.containsKey(1L)); // TRUE -- inconsistent!
        System.out.println("Line items in DB: " + itemRepo.db.size());        // 0 -- never saved
    }
}
```

How to run: `java TransactionalLevel1.java`

Even though `placeOrderUncoordinated` throws partway through, `orderRepo.db.containsKey(1L)` prints `true` — the order was already committed by the time the line-item save failed, leaving an order in the database with no line items. This is exactly the inconsistent state risk that motivates wrapping both calls in one transaction.

### Level 2 — Intermediate

Wrap both calls in a simulated shared transaction that only commits changes to the "real" database once every call inside it has succeeded, rolling back everything if any call throws.

```java
import java.util.*;
import java.util.function.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }
class LineItem { long orderId; String description; LineItem(long orderId, String d) { this.orderId = orderId; description = d; } }

// Stands in for Spring's transaction manager: buffers writes, commits or discards them as a unit.
class Transaction {
    Map<Long, Order> pendingOrders = new HashMap<>();
    List<LineItem> pendingItems = new ArrayList<>();

    static <T> void runInTransaction(Map<Long, Order> orderDb, List<LineItem> itemDb, Consumer<Transaction> work) {
        Transaction tx = new Transaction();
        try {
            work.accept(tx);
            // Only commit to the REAL database if nothing threw.
            orderDb.putAll(tx.pendingOrders);
            itemDb.addAll(tx.pendingItems);
            System.out.println("  [transaction committed]");
        } catch (RuntimeException e) {
            System.out.println("  [transaction rolled back] " + e.getMessage() + " -- nothing was persisted");
            throw e;
        }
    }
}

public class TransactionalLevel2 {
    // @Transactional
    // void placeOrder(Order order, List<LineItem> items) { orderRepository.save(order); itemRepository.saveAll(items); }
    static void placeOrder(Transaction tx, Order order, List<LineItem> items) {
        tx.pendingOrders.put(order.id, order); // "save" -- buffered, not yet committed
        for (LineItem li : items) {
            if (li.description.equals("INVALID")) throw new RuntimeException("Invalid line item: " + li.description);
        }
        tx.pendingItems.addAll(items); // "saveAll" -- also buffered
    }

    public static void main(String[] args) {
        Map<Long, Order> orderDb = new HashMap<>();
        List<LineItem> itemDb = new ArrayList<>();

        try {
            Transaction.runInTransaction(orderDb, itemDb, tx ->
                placeOrder(tx, new Order(1, "PENDING"),
                    List.of(new LineItem(1, "Widget"), new LineItem(1, "INVALID"))));
        } catch (RuntimeException e) {
            System.out.println("Caught: " + e.getMessage());
        }

        System.out.println("Order 1 in DB? " + orderDb.containsKey(1L)); // FALSE now -- consistent!
        System.out.println("Line items in DB: " + itemDb.size());
    }
}
```

How to run: `java TransactionalLevel2.java`

This time `orderDb.containsKey(1L)` prints `false` — the order was buffered in `tx.pendingOrders` but never reached `orderDb` because the transaction rolled back before its final commit step. Both the order and line items are "all or nothing" now, matching how `@Transactional` on `placeOrder` would make both `orderRepository.save(...)` and `lineItemRepository.saveAll(...)` roll back together if either fails.

### Level 3 — Advanced

Add a read-only transactional method alongside the write path, and a successful write scenario, showing both common `@Transactional` use cases together: atomic multi-repository writes, and an optimized read-only query boundary.

```java
import java.util.*;
import java.util.function.*;

class Order { long id; String status; double total; Order(long id, String status, double total) { this.id = id; this.status = status; this.total = total; } }
class LineItem { long orderId; String description; LineItem(long orderId, String d) { this.orderId = orderId; description = d; } }

class Transaction {
    Map<Long, Order> pendingOrders = new HashMap<>();
    List<LineItem> pendingItems = new ArrayList<>();

    static void runInTransaction(Map<Long, Order> orderDb, List<LineItem> itemDb, Consumer<Transaction> work) {
        Transaction tx = new Transaction();
        try {
            work.accept(tx);
            orderDb.putAll(tx.pendingOrders);
            itemDb.addAll(tx.pendingItems);
            System.out.println("  [transaction committed]");
        } catch (RuntimeException e) {
            System.out.println("  [transaction rolled back]");
            throw e;
        }
    }
}

public class TransactionalLevel3 {
    static void placeOrder(Transaction tx, Order order, List<LineItem> items) {
        tx.pendingOrders.put(order.id, order);
        tx.pendingItems.addAll(items); // no invalid items this time -- succeeds
    }

    // @Transactional(readOnly = true)
    // OrderReport generateReport(long orderId) { ... reads across multiple repositories ... }
    static String generateReport(Map<Long, Order> orderDb, List<LineItem> itemDb, long orderId) {
        Order order = orderDb.get(orderId);
        long itemCount = itemDb.stream().filter(li -> li.orderId == orderId).count();
        // readOnly=true lets the JPA provider skip dirty-checking snapshots for BOTH reads in this method
        return "Order " + orderId + ": status=" + order.status + ", total=" + order.total + ", items=" + itemCount;
    }

    public static void main(String[] args) {
        Map<Long, Order> orderDb = new HashMap<>();
        List<LineItem> itemDb = new ArrayList<>();

        Transaction.runInTransaction(orderDb, itemDb, tx ->
            placeOrder(tx, new Order(1, "PENDING", 75.0),
                List.of(new LineItem(1, "Widget"), new LineItem(1, "Gadget"))));

        System.out.println("Order 1 in DB? " + orderDb.containsKey(1L)); // TRUE -- committed successfully

        String report = generateReport(orderDb, itemDb, 1L);
        System.out.println(report);
    }
}
```

How to run: `java TransactionalLevel3.java`

`placeOrder` succeeds this time (no invalid line item), so the transaction commits and `orderDb.containsKey(1L)` is `true`. `generateReport` then reads across *both* `orderDb` and `itemDb` in one logical operation — standing in for a `@Transactional(readOnly = true)` service method, where the read-only flag applies to every repository call made inside that one method, not just to a single query.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `Transaction.runInTransaction(orderDb, itemDb, tx -> placeOrder(...))` runs. Inside, `placeOrder` writes into `tx.pendingOrders` and `tx.pendingItems` — both are buffered, not yet visible in the real `orderDb`/`itemDb`. Since `placeOrder` completes without throwing (no `"INVALID"` line item this time), control returns to `runInTransaction`, which then runs `orderDb.putAll(tx.pendingOrders)` and `itemDb.addAll(tx.pendingItems)` — this is the commit step, and only now do the changes become visible outside the transaction. "[transaction committed]" is printed.

Back in `main`, `orderDb.containsKey(1L)` is checked and prints `true`, confirming the commit took effect.

Next, `generateReport(orderDb, itemDb, 1L)` runs: it reads `orderDb.get(1L)` (finding the just-committed order) and counts matching line items in `itemDb` via a stream filter — two separate read operations, both logically part of one "generate report" business operation. The method builds and returns a formatted string, which `main` prints: `Order 1: status=PENDING, total=75.0, items=2`.

```
runInTransaction:  placeOrder buffers writes -> no throw -> commit (orderDb/itemDb updated) -> printed "committed"
main:              orderDb.containsKey(1L) == true
generateReport:    read orderDb.get(1L) + count itemDb matches -> one combined report string
```

In a real Spring application, `@Transactional` on `placeOrder(Order, List<LineItem>)` causes Spring's transaction interceptor to open a transaction before the method body runs, let both `orderRepository.save(order)` and `lineItemRepository.saveAll(items)` join that same transaction (rather than each opening its own), and commit only when the method returns normally — any exception thrown anywhere inside triggers a full rollback of both. `@Transactional(readOnly = true)` on `generateReport` tells the JPA provider it can apply read-only optimizations (like skipping dirty-checking snapshots, similar to the `@QueryHints` read-only hint) across every repository call made inside that method, not just one query.

## 7. Gotchas & takeaways

> Gotcha: `@Transactional` only takes effect through a **Spring-proxied call** — calling a `@Transactional` method from *another method in the same class* (a plain `this.placeOrder(...)` call) bypasses the proxy entirely, so no transaction boundary is actually created; the annotation is silently ignored in that case.

- Every Spring Data repository method is already transactional on its own by default — `@Transactional` on a service method is for coordinating *multiple* repository calls as one atomic unit.
- Without an explicit shared transaction, a failure partway through a multi-step operation can leave committed-but-inconsistent state, exactly as Level 1 demonstrated.
- `@Transactional(readOnly = true)` signals the whole method is read-only, letting the JPA provider optimize every repository call inside it, not just a single query.
- Self-invocation (calling a `@Transactional` method from within the same class, not through the injected bean) silently skips the transaction — a common and hard-to-spot bug.
