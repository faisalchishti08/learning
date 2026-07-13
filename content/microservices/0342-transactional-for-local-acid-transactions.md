---
card: microservices
gi: 342
slug: transactional-for-local-acid-transactions
title: "@Transactional for local ACID transactions"
---

## 1. What it is

Spring's `@Transactional` annotation wraps a method in a local database transaction: every database operation performed inside the annotated method either all commit together when the method returns normally, or all roll back together if the method throws an unchecked exception. This is Spring's mechanism for getting ACID guarantees — the same guarantees discussed in [BASE vs ACID](0327-base-vs-acid.md) — for the part of a microservices system where they're still fully appropriate: a single service's own local database.

## 2. Why & when

Once a service's business logic touches more than one row, or more than one table, in a single logical operation (placing an order might mean inserting an order row and several order-line rows), those writes need to succeed or fail together — a crash halfway through must not leave a half-written order visible to anyone. `@Transactional` gives Spring this guarantee automatically: annotate the method, and Spring's transaction management (backed by the actual database's transaction support) ensures atomicity for everything that method does to its database.

Use `@Transactional` on any service method that performs multiple related database writes that must succeed or fail as a unit. This is exactly the boundary described earlier: [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md) applies to transactions spanning *multiple services*; `@Transactional` is for the transactions *within* one service's own database, where full ACID is cheap, safe, and exactly what you want.

## 3. Core concept

Spring wraps the annotated method in a proxy that starts a transaction before the method runs and, depending on the outcome, either commits (normal return) or rolls back (an unchecked exception is thrown, by default) when the method exits. Because this relies on a proxy intercepting the *call* to the method, calling a `@Transactional` method from another method *in the same class* bypasses the proxy and won't get transactional behavior — a well-known Spring gotcha.

```java
@Transactional
public void placeOrder(Order order, List<OrderLine> lines) {
    orderRepository.save(order);          // if THIS succeeds but the next line throws,
    orderLineRepository.saveAll(lines);   // Spring rolls back BOTH, not just one
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Transactional method wraps two database writes; if an exception is thrown partway through, Spring rolls back both writes together instead of leaving one committed and one not">
  <rect x="20" y="60" width="600" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional placeOrder(...)</text>
  <rect x="50" y="95" width="220" height="25" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="112" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">save(order)</text>
  <rect x="370" y="95" width="220" height="25" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="480" y="112" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">saveAll(lines) -- THROWS</text>

  <text x="320" y="155" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Exception thrown -&gt; Spring ROLLS BACK the order save too, atomically.</text>
</svg>

Every write inside a `@Transactional` method commits together or rolls back together, guaranteeing atomicity for that local, single-database operation.

## 5. Runnable example

Scenario: a place-order operation writing two related pieces of local state, first shown without transactional protection (a partial write survives a failure), then fixed with a simulated `@Transactional` wrapper that correctly rolls back both writes together, and finally extended to show the same-class self-invocation pitfall that silently bypasses Spring's transactional proxy.

### Level 1 — Basic

```java
// File: NoTransactionPartialWrite.java -- two related writes with NO
// transactional protection; a failure after the FIRST write leaves it
// committed even though the operation as a whole failed.
import java.util.*;

public class NoTransactionPartialWrite {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<String> orderLinesTable = new ArrayList<>();

    static void placeOrder(String orderId, boolean simulateFailureOnLines) {
        ordersTable.put(orderId, "PLACED"); // write 1: SUCCEEDS and is immediately visible
        System.out.println("orders table: " + orderId + " saved");

        if (simulateFailureOnLines) {
            throw new RuntimeException("failed to save order lines"); // write 2 never even starts
        }
        orderLinesTable.add(orderId + ":widget");
    }

    public static void main(String[] args) {
        try {
            placeOrder("order-1", true);
        } catch (RuntimeException e) {
            System.out.println("caught: " + e.getMessage());
        }
        System.out.println("orders table still has order-1: " + ordersTable.containsKey("order-1")
                + " -- ORPHANED order with NO lines, because there was no transaction to roll it back!");
    }
}
```

How to run: `java NoTransactionPartialWrite.java`

`placeOrder` writes to `ordersTable` first, then throws before reaching `orderLinesTable`. The exception is caught in `main`, but `ordersTable` still contains the order — it was never rolled back, because nothing here is transactional. The result is an orphaned order with no line items, a real data-integrity problem.

### Level 2 — Intermediate

```java
// File: SimulatedTransactionalRollback.java -- wraps the SAME two writes
// in a simulated transaction: if ANY write inside fails, ALL writes made
// so far within that transaction are rolled back together.
import java.util.*;
import java.util.function.Consumer;

public class SimulatedTransactionalRollback {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<String> orderLinesTable = new ArrayList<>();

    // Simulates Spring's @Transactional proxy behavior around a method.
    static void runTransactionally(Consumer<Void> operation) {
        Map<String, String> ordersSnapshot = new HashMap<>(ordersTable);         // "begin transaction"
        List<String> orderLinesSnapshot = new ArrayList<>(orderLinesTable);
        try {
            operation.accept(null);
            System.out.println("transaction: COMMIT -- all writes made permanent");
        } catch (RuntimeException e) {
            ordersTable.clear(); ordersTable.putAll(ordersSnapshot);              // "rollback" -- restore pre-transaction state
            orderLinesTable.clear(); orderLinesTable.addAll(orderLinesSnapshot);
            System.out.println("transaction: ROLLBACK due to: " + e.getMessage() + " -- ALL writes in this transaction undone");
        }
    }

    static void placeOrder(String orderId, boolean simulateFailureOnLines) {
        ordersTable.put(orderId, "PLACED");
        System.out.println("orders table: " + orderId + " saved (within transaction, not yet committed)");
        if (simulateFailureOnLines) throw new RuntimeException("failed to save order lines");
        orderLinesTable.add(orderId + ":widget");
    }

    public static void main(String[] args) {
        runTransactionally(v -> placeOrder("order-1", true));

        System.out.println("orders table has order-1: " + ordersTable.containsKey("order-1")
                + " -- correctly rolled back, NO orphaned order.");
    }
}
```

How to run: `java SimulatedTransactionalRollback.java`

`runTransactionally` snapshots both tables before running the operation, standing in for Spring beginning a real database transaction. When `placeOrder` throws, the `catch` block restores both tables to their pre-transaction snapshots — undoing the `ordersTable` write that had already happened, exactly as a real database transaction rollback would. The final check confirms `order-1` is correctly *not* present, with no orphaned order left behind.

### Level 3 — Advanced

```java
// File: SelfInvocationBypassesProxy.java -- demonstrates the classic
// Spring @Transactional pitfall: calling a "transactional" method from
// ANOTHER method in the SAME class bypasses the proxy that would
// normally intercept the call, so NO transactional behavior applies.
import java.util.*;
import java.util.function.Consumer;

public class SelfInvocationBypassesProxy {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<String> orderLinesTable = new ArrayList<>();

    // Simulates the REAL Spring proxy -- only calls THROUGH this wrapper get transactional behavior.
    static void runTransactionally(Consumer<Void> operation) {
        Map<String, String> ordersSnapshot = new HashMap<>(ordersTable);
        List<String> orderLinesSnapshot = new ArrayList<>(orderLinesTable);
        try {
            operation.accept(null);
        } catch (RuntimeException e) {
            ordersTable.clear(); ordersTable.putAll(ordersSnapshot);
            orderLinesTable.clear(); orderLinesTable.addAll(orderLinesSnapshot);
            System.out.println("  (via proxy) ROLLBACK applied");
            throw e;
        }
    }

    static void placeOrderDirectCall(String orderId) { // simulates calling "this.placeOrder(...)" from elsewhere in the SAME class
        System.out.println("placeOrderDirectCall: calling placeOrder() DIRECTLY (like 'this.placeOrder()' in real Spring) -- NO proxy involved!");
        placeOrder(orderId, true); // in real Spring, this bypasses the @Transactional proxy entirely
    }

    static void placeOrder(String orderId, boolean simulateFailureOnLines) {
        ordersTable.put(orderId, "PLACED");
        if (simulateFailureOnLines) throw new RuntimeException("failed to save order lines");
        orderLinesTable.add(orderId + ":widget");
    }

    public static void main(String[] args) {
        // Case A: called THROUGH the proxy -- gets transactional rollback.
        try { runTransactionally(v -> placeOrder("order-1", true)); } catch (RuntimeException ignored) {}
        System.out.println("Case A (via proxy) -- order-1 present: " + ordersTable.containsKey("order-1") + " (correctly rolled back)");

        // Case B: self-invocation, bypassing the proxy -- NO rollback, exactly the real Spring pitfall.
        try { placeOrderDirectCall("order-2"); } catch (RuntimeException ignored) {}
        System.out.println("Case B (direct self-call, bypasses proxy) -- order-2 present: " + ordersTable.containsKey("order-2")
                + " -- ORPHANED, because @Transactional never actually applied!");
    }
}
```

How to run: `java SelfInvocationBypassesProxy.java`

Case A calls `placeOrder` through `runTransactionally`, which stands in for Spring's transactional proxy — the failure correctly triggers a rollback, and `order-1` ends up absent. Case B calls `placeOrderDirectCall`, which invokes `placeOrder` directly (simulating `this.placeOrder(...)` from within the same Spring-managed bean) — no proxy sits in between, so no snapshot or rollback logic ever runs, and `order-2` is left orphaned in `ordersTable` despite the same underlying failure. This mirrors the real, well-documented Spring behavior: `@Transactional` only takes effect on calls that go through the Spring-managed proxy, which self-invocation (a method calling another method of the same object directly) does not.

## 6. Walkthrough

Trace `SelfInvocationBypassesProxy.main` in order. **First**, Case A calls `runTransactionally(v -> placeOrder("order-1", true))`. Inside, snapshots of both tables are taken, then the lambda runs `placeOrder("order-1", true)`, which puts `order-1` into `ordersTable` and then throws. The `catch` block in `runTransactionally` restores both tables from their snapshots — `order-1` is removed — prints the rollback message, and rethrows, which `main` catches and ignores.

**`main` then prints Case A's result**: `ordersTable.containsKey("order-1")` is `false`, confirming the rollback correctly undid the write.

**Then**, Case B calls `placeOrderDirectCall("order-2")`. This method prints its message and calls `placeOrder("order-2", true)` **directly** — not through `runTransactionally`. Inside `placeOrder`, `order-2` is put into `ordersTable`, and then the method throws. Because this call never passed through `runTransactionally`, there is no snapshot and no rollback logic anywhere in this call path — the exception propagates straight up to `main`'s `catch`, and `ordersTable` is left exactly as it was at the moment of the failure, with `order-2` still present.

**Finally**, `main` prints Case B's result: `ordersTable.containsKey("order-2")` is `true` — the order is orphaned, despite `placeOrder` being "the same method" that was correctly rolled back in Case A, purely because of how it was called.

```
Case A: runTransactionally(-> placeOrder(order-1)) -> proxy wraps call -> FAILS -> ROLLBACK -> order-1 ABSENT (correct)
Case B: placeOrderDirectCall(order-2) -> calls placeOrder() DIRECTLY, no proxy -> FAILS -> NO rollback -> order-2 PRESENT (orphaned, bug)
```

## 7. Gotchas & takeaways

> `@Transactional` is implemented via a Spring-generated proxy around the bean; calling an `@Transactional` method from another method of the *same* class (`this.someTransactionalMethod()`) calls the real object directly, skipping the proxy entirely — silently disabling the transactional behavior with no compile-time or obvious runtime warning. Structure code so transactional entry points are called from *outside* the class (a different Spring bean), not from within.

- `@Transactional` gives full ACID guarantees for operations within a single service's own local database — exactly the scope where those guarantees are cheap and correct, unlike across service boundaries (see [BASE vs ACID](0327-base-vs-acid.md)).
- By default, an unchecked (runtime) exception triggers a rollback of every write made within the annotated method; a checked exception does not, unless configured to.
- Self-invocation within the same class bypasses Spring's transactional proxy, silently disabling rollback behavior — a well-known and easy-to-miss pitfall.
- Combine with [@TransactionalEventListener](0343-spring-transactional-event-listeners-transactionaleventliste.md) when a transactional write also needs to reliably trigger an event only after that transaction actually commits.
