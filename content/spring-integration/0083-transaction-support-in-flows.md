---
card: spring-integration
gi: 83
slug: transaction-support-in-flows
title: "Transaction support in flows"
---

## 1. What it is

Transaction support (`TransactionInterceptor` applied via `.transactional()` on a poller or endpoint, backed by Spring's standard `PlatformTransactionManager`) wraps a flow's message processing in a database (or other resource) transaction, so a poller's fetch-and-process cycle, or an endpoint's handling of a message, either fully commits or fully rolls back as one unit — the same transactional semantics familiar from `@Transactional` service methods, applied to message-driven processing instead.

## 2. Why & when

You reach for transaction support when a flow's processing step must leave a resource in a consistent state even when something partway through fails:

- **A poller reads from a transactional source and the read itself should be undone on failure** — the JDBC inbound adapter's claim-then-select pattern (card 0064) benefits from running inside a transaction so that if downstream processing fails, the claiming update rolls back too, leaving the row available for a later retry rather than stuck in a half-claimed state.
- **Multiple resource operations within one message's processing must succeed or fail together** — if handling a single message involves both a database write and a subsequent related write, wrapping both in the same transaction ensures a failure partway through doesn't leave one write committed and the other missing.
- **At-least-once delivery semantics need reinforcing** — pairing a transactional poller with a message-driven channel adapter (like a JMS or Kafka consumer configured for transactional acknowledgment) ties the broker's message acknowledgment to the same transaction as the database work, so a crash between "processed the message" and "acknowledged the broker" doesn't silently lose or double-process it.

## 3. Core concept

Think of a bank transfer: money leaves one account and arrives in another, and either both halves happen or neither does — a transfer that debits one account but then crashes before crediting the other would corrupt the books. A transactional flow step works the same way: whatever resource operations happen while processing one message (claiming a row, writing a result, acknowledging a broker message) are wrapped together so that a failure partway through undoes everything already done in that same unit, rather than leaving the system in a partially-completed, inconsistent state.

```java
@Bean
public IntegrationFlow transactionalPollingFlow(DataSource dataSource, PlatformTransactionManager txManager) {
    return IntegrationFlow.from(
            Jdbc.inboundAdapter(dataSource, "SELECT * FROM orders WHERE status = 'PENDING'")
                .updateSql("UPDATE orders SET status = 'PROCESSING' WHERE id IN (:id)"),
            e -> e.poller(Pollers.fixedDelay(5_000)
                .transactional(new TransactionInterceptor(txManager, new DefaultTransactionAttribute()))))
        .handle((Order order, headers) -> orderService.process(order)) // failure here rolls back the claim too
        .get();
}
```

If `orderService.process(order)` throws, the entire transaction — including the earlier claiming update — rolls back, leaving the order genuinely still `PENDING` for the next poll to retry.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A transactional poller wraps claim, fetch, and process in one transaction; if processing fails, the whole transaction rolls back including the earlier claim, rather than leaving a row stuck half-claimed" >
  <rect x="20" y="20" width="600" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="35" y="45" fill="#e6edf3" font-size="8" font-family="monospace">Transaction: [claim row] [select row] [process] -- all succeed -&gt; COMMIT</text>

  <rect x="20" y="85" width="600" height="45" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="35" y="110" fill="#e6edf3" font-size="8" font-family="monospace">Transaction: [claim row] [select row] [process FAILS] -- ROLLBACK (claim undone too)</text>

  <text x="320" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Failure partway through undoes everything in the same transaction, including the earlier claim</text>
</svg>

A single failed step rolls back everything else done in the same transaction, not just that one step.

## 5. Runnable example

The scenario: processing a claimed order where the processing step can fail, simulated with a plain in-memory "transaction" wrapper standing in for `PlatformTransactionManager` (no real database or transaction manager needed to demonstrate the commit/rollback semantics), starting with a basic transactional wrapper, then adding a rollback on processing failure, then adding a downstream write that must roll back together with the original claim.

### Level 1 — Basic

```java
// TransactionalFlowDemo.java
import java.util.*;

public class TransactionalFlowDemo {
    record Order(int id, String status) {}

    static void claim(Map<Integer, Order> table, int id) {
        table.put(id, new Order(id, "PROCESSING"));
    }

    static void process(Order order) {
        System.out.println("Processed order " + order.id());
    }

    public static void main(String[] args) {
        Map<Integer, Order> table = new HashMap<>();
        table.put(1, new Order(1, "PENDING"));

        claim(table, 1);
        process(table.get(1));
        System.out.println("Final status: " + table.get(1).status());
    }
}
```

How to run: `java TransactionalFlowDemo.java`. Expected output: `Processed order 1` then `Final status: PROCESSING` — a basic claim-then-process, no rollback logic yet.

### Level 2 — Intermediate

```java
// TransactionalFlowDemo.java
import java.util.*;
import java.util.function.*;

public class TransactionalFlowDemo {
    record Order(int id, String status) {}

    static class ProcessingFailedException extends RuntimeException {
        ProcessingFailedException(String msg) { super(msg); }
    }

    // Real-world concern: if processing fails, the earlier claim must roll back too, or the
    // order is stuck in PROCESSING forever with no automatic retry.
    static void runTransactionally(Map<Integer, Order> table, int id, Consumer<Order> processingStep) {
        Order originalState = table.get(id);
        table.put(id, new Order(id, "PROCESSING")); // claim
        try {
            processingStep.accept(table.get(id));
            System.out.println("Transaction committed for order " + id);
        } catch (ProcessingFailedException ex) {
            table.put(id, originalState); // rollback: restore pre-transaction state
            System.out.println("Transaction rolled back for order " + id + ": " + ex.getMessage());
        }
    }

    public static void main(String[] args) {
        Map<Integer, Order> table = new HashMap<>();
        table.put(1, new Order(1, "PENDING"));
        table.put(2, new Order(2, "PENDING"));

        runTransactionally(table, 1, o -> System.out.println("Processing order " + o.id()));
        runTransactionally(table, 2, o -> { throw new ProcessingFailedException("payment gateway timeout"); });

        System.out.println("Order 1 final status: " + table.get(1).status());
        System.out.println("Order 2 final status: " + table.get(2).status());
    }
}
```

How to run: `java TransactionalFlowDemo.java`. Expected output: order 1 commits and ends as `PROCESSING`; order 2's processing throws, triggering a rollback message, and order 2 ends back at `PENDING` — exactly as it was before the transaction began, ready for a later retry.

### Level 3 — Advanced

```java
// TransactionalFlowDemo.java
import java.util.*;
import java.util.function.*;

public class TransactionalFlowDemo {
    record Order(int id, String status) {}
    record AuditEntry(int orderId, String action) {}

    static class ProcessingFailedException extends RuntimeException {
        ProcessingFailedException(String msg) { super(msg); }
    }

    // Production concern: a real flow often writes to more than one resource per message (the
    // order table AND an audit log). Both writes must roll back together on failure, not just
    // the first one -- otherwise a partial commit leaves an inconsistent audit trail.
    static void runTransactionally(
            Map<Integer, Order> orderTable, List<AuditEntry> auditLog,
            int id, Consumer<Order> processingStep) {
        Order originalOrderState = orderTable.get(id);
        int auditLogSizeBeforeTransaction = auditLog.size();

        orderTable.put(id, new Order(id, "PROCESSING"));
        auditLog.add(new AuditEntry(id, "CLAIMED"));

        try {
            processingStep.accept(orderTable.get(id));
            auditLog.add(new AuditEntry(id, "PROCESSED"));
            System.out.println("Transaction committed for order " + id);
        } catch (ProcessingFailedException ex) {
            orderTable.put(id, originalOrderState);
            while (auditLog.size() > auditLogSizeBeforeTransaction) {
                auditLog.remove(auditLog.size() - 1); // roll back every audit entry from this transaction
            }
            System.out.println("Transaction rolled back for order " + id + " (audit log also reverted)");
        }
    }

    public static void main(String[] args) {
        Map<Integer, Order> orderTable = new HashMap<>();
        List<AuditEntry> auditLog = new ArrayList<>();
        orderTable.put(1, new Order(1, "PENDING"));

        runTransactionally(orderTable, auditLog, 1,
            o -> { throw new ProcessingFailedException("downstream service unavailable"); });

        System.out.println("Order status: " + orderTable.get(1).status());
        System.out.println("Audit log entries: " + auditLog.size());
    }
}
```

How to run: `java TransactionalFlowDemo.java`. Expected output: `Transaction rolled back for order 1 (audit log also reverted)`, then `Order status: PENDING` and `Audit log entries: 0` — both the order table and the audit log revert together, since they participated in the same transaction, avoiding the inconsistency of a committed audit entry describing a claim that was actually undone.

## 6. Walkthrough

Trace one poll cycle with a downstream failure, all inside a single transaction.

1. **Transaction begins**: the poller's `.transactional(...)` configuration starts a new transaction (via the configured `PlatformTransactionManager`) before executing anything else in this cycle.
2. **Claim**: the inbound adapter's `updateSql` runs inside this transaction, marking a row as claimed — this update is provisional until the transaction commits.
3. **Fetch and process**: the claimed row is selected and handed to downstream processing, which may perform additional writes (an audit log entry, a related table update) — all still inside the same open transaction.
4. **Success path**: if every step completes without error, the transaction commits, making the claim, the processing result, and any related writes durable together, atomically.
5. **Failure path**: if any step throws (as in `processingStep` in the example), the transaction manager rolls back everything done since the transaction began — the claim included — restoring the affected rows to their pre-transaction state as though none of it had happened.
6. **Retry**: because the rollback restores the order to `PENDING` rather than leaving it stuck at `PROCESSING`, the next poll cycle picks it up again naturally, without needing any special "stuck order" recovery logic.

```
transaction begins
  -> claim row (UPDATE status='PROCESSING')
    -> select claimed row -> process
       success -> [claim + processing writes] -> COMMIT
       failure -> ROLLBACK (claim undone, order back to PENDING, retried later)
```

## 7. Gotchas & takeaways

> **Gotcha:** wrapping a poller in a transaction only protects resources that participate in that same transaction manager — a call to an external HTTP service or a non-transactional resource inside the processing step has no rollback semantics at all; a failure after that external call has already taken effect (a payment already charged, an email already sent) cannot be undone by the transaction rolling back the database rows.

- Transactional pollers pair naturally with the claim-then-select pattern from the JDBC adapter (card 0064) — the claim and the processing failure are tied together so a failed message genuinely becomes retriable rather than stuck.
- For message-driven (non-polling) sources like JMS or Kafka, transaction support can extend to the broker acknowledgment itself, so a processing failure also prevents the message from being acknowledged, causing the broker to redeliver it — coordinating "did we finish processing" with "should the broker consider this delivered."
- Keep non-transactional side effects (sending an email, calling an external payment API) outside the transactional boundary where possible, or make peace with the fact that those effects cannot be rolled back the way database writes can — this is a common source of "the refund got issued twice" bugs when a transaction retries a step assumed to be safely re-runnable.
- Transactions add real overhead and can hold locks for the duration of processing; keep the transactional scope as small as the correctness requirement actually needs, rather than wrapping an entire, potentially slow processing pipeline in one long-held transaction.
