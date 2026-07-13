---
card: microservices
gi: 323
slug: compensating-transactions
title: "Compensating transactions"
---

## 1. What it is

A **compensating transaction** is an action that semantically undoes the effect of an earlier, already-committed local transaction in a [saga](0320-saga-pattern.md). It is not a database rollback — the original transaction really did commit and may have already been observed by other parts of the system — it is a separate, deliberate business operation (cancel the order, refund the payment, release the reserved stock) designed specifically to bring the system back to a consistent state after a later step in the saga fails.

## 2. Why & when

Because sagas replace a single cross-service ACID transaction with a chain of independent local commits (see [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md)), there is no database engine that can automatically roll back a step in another service once it has committed. If step 3 of 4 fails, steps 1 and 2 already happened for real — the only way to restore consistency is to explicitly run an operation that reverses each of their effects.

You need a compensating transaction for every saga step whose effect could still need undoing after a later step fails. Some steps don't need one — pure reads, or idempotent no-op-if-repeated calculations — but any step with a real side effect (a database write, a charge, a stock decrement) needs a carefully designed compensation, decided at the same time the forward step is designed, not improvised after the fact.

## 3. Core concept

A compensation is defined as the semantic inverse of its forward step, not a literal undo: "place order" is compensated by "cancel order" (which might, depending on the domain, mark the order cancelled rather than delete the row, preserving an audit trail); "charge payment" is compensated by "refund payment" (a new, separate transaction, not an erasure of the charge); "reserve stock" is compensated by "release stock." Compensations must be idempotent (safe to retry) and, ideally, commutative with concurrent operations, since real-world timing means a compensation might race with something else touching the same data.

```java
record SagaStep(String name, Runnable forward, Runnable compensation) {}
// cancelOrder does NOT delete the order row -- it marks it CANCELLED,
// preserving history rather than pretending the order never existed.
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Forward step charge payment commits a real charge; its compensating transaction is a separate refund transaction, not an erasure of the original charge -- both are visible in the transaction history">
  <rect x="40" y="30" width="220" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Forward: charge $50</text>
  <text x="150" y="70" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">committed, real, VISIBLE</text>

  <rect x="380" y="30" width="220" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Compensation: refund $50</text>
  <text x="490" y="70" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">a SEPARATE new transaction</text>

  <line x1="260" y1="55" x2="375" y2="55" stroke="#8b949e" marker-end="url(#a323)"/>
  <text x="320" y="45" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">later step fails</text>

  <text x="320" y="130" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Both the charge AND the refund remain in the transaction history --</text>
  <text x="320" y="147" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">this is compensation, not a rollback that erases the original event.</text>

  <defs><marker id="a323" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A compensation is a new, separate transaction that semantically reverses an earlier one — the original is never erased, only counteracted.

## 5. Runnable example

Scenario: a payment step that is compensated with a naive "delete the charge" approach that destroys the audit trail, then fixed to issue a proper separate refund transaction, then extended to make the refund idempotent against being triggered twice for the same failed saga.

### Level 1 — Basic

```java
// File: NaiveDeleteCompensation.java -- WRONG approach: "compensating" by
// DELETING the original charge record, destroying the audit trail.
import java.util.*;

public class NaiveDeleteCompensation {
    static Map<String, Double> charges = new HashMap<>();

    static void chargePayment(String orderId, double amount) {
        charges.put(orderId, amount);
        System.out.println("payment: charged $" + amount + " for " + orderId);
    }

    static void naiveCompensate(String orderId) {
        charges.remove(orderId); // WRONG: erases the fact that a charge ever happened
        System.out.println("payment: DELETED charge record for " + orderId + " -- no trace it ever happened!");
    }

    public static void main(String[] args) {
        chargePayment("order-1", 50.0);
        naiveCompensate("order-1");
        System.out.println("charges map now: " + charges + " -- an auditor has NO WAY to see the original charge occurred.");
    }
}
```

How to run: `java NaiveDeleteCompensation.java`

`naiveCompensate` simply removes the charge from the map. The final state shows an empty `charges` map — functionally "balanced" in this toy example, but in a real payment system this would mean deleting a financial record, which is both usually illegal (financial transactions must be auditable) and dangerous (it hides that money was ever actually moved, which matters if the bank's side of the charge did go through).

### Level 2 — Intermediate

```java
// File: ProperRefundCompensation.java -- the compensation is a SEPARATE,
// NEW refund transaction; the original charge record is preserved.
import java.util.*;

public class ProperRefundCompensation {
    record Transaction(String orderId, String type, double amount) {}
    static List<Transaction> transactionLog = new ArrayList<>(); // append-only, nothing ever deleted

    static void chargePayment(String orderId, double amount) {
        transactionLog.add(new Transaction(orderId, "CHARGE", amount));
        System.out.println("payment: charged $" + amount + " for " + orderId);
    }

    static void refundPayment(String orderId, double amount) { // the COMPENSATION -- a NEW transaction
        transactionLog.add(new Transaction(orderId, "REFUND", amount));
        System.out.println("payment: refunded $" + amount + " for " + orderId + " (separate transaction)");
    }

    public static void main(String[] args) {
        chargePayment("order-1", 50.0);
        refundPayment("order-1", 50.0); // compensating for a later saga step that failed

        System.out.println("Full transaction log (nothing erased): " + transactionLog);
        double netForOrder = transactionLog.stream()
                .filter(t -> t.orderId().equals("order-1"))
                .mapToDouble(t -> t.type().equals("CHARGE") ? t.amount() : -t.amount())
                .sum();
        System.out.println("Net amount for order-1: $" + netForOrder + " (correct, and fully auditable)");
    }
}
```

How to run: `java ProperRefundCompensation.java`

Both the charge and the refund are appended to `transactionLog` as separate, permanent entries — nothing is ever deleted. The net financial effect (`$0.0`) is correct, computed by summing charges and subtracting refunds, but the *history* still shows exactly what happened: a charge, then a refund, both real, both auditable. This is what makes it a compensation rather than a rollback.

### Level 3 — Advanced

```java
// File: IdempotentRefundCompensation.java -- the saga's failure handler is
// invoked TWICE for the same failed saga instance (e.g. a retried failure
// message); the refund must run EXACTLY ONCE, not twice, or the customer
// is over-refunded.
import java.util.*;

public class IdempotentRefundCompensation {
    record Transaction(String orderId, String type, double amount, String compensationId) {}
    static List<Transaction> transactionLog = new ArrayList<>();
    static Set<String> appliedCompensationIds = new HashSet<>(); // dedupe key, one per saga-failure instance

    static void chargePayment(String orderId, double amount) {
        transactionLog.add(new Transaction(orderId, "CHARGE", amount, null));
        System.out.println("payment: charged $" + amount + " for " + orderId);
    }

    static void refundPayment(String orderId, double amount, String compensationId) {
        if (!appliedCompensationIds.add(compensationId)) { // add() is false if ALREADY present -- duplicate trigger
            System.out.println("payment: compensation " + compensationId + " already applied -- SKIPPING duplicate refund");
            return;
        }
        transactionLog.add(new Transaction(orderId, "REFUND", amount, compensationId));
        System.out.println("payment: refunded $" + amount + " for " + orderId + " (compensationId=" + compensationId + ")");
    }

    public static void main(String[] args) {
        chargePayment("order-1", 50.0);

        // Simulate the saga's failure-handling logic being triggered TWICE for the same saga instance.
        refundPayment("order-1", 50.0, "saga-failure-42");
        refundPayment("order-1", 50.0, "saga-failure-42"); // duplicate trigger, SAME compensationId

        double netForOrder = transactionLog.stream()
                .filter(t -> t.orderId().equals("order-1"))
                .mapToDouble(t -> t.type().equals("CHARGE") ? t.amount() : -t.amount())
                .sum();
        System.out.println("Net amount for order-1: $" + netForOrder + " -- correct, refunded exactly ONCE despite two triggers.");
    }
}
```

How to run: `java IdempotentRefundCompensation.java`

`refundPayment` is called twice with the identical `compensationId="saga-failure-42"`, simulating the saga's failure-handling path being triggered more than once for the same logical failure (a realistic scenario with at-least-once message delivery). The first call's `appliedCompensationIds.add(...)` returns `true` and the refund is recorded; the second call's `add(...)` returns `false` because the ID is already present, so the handler skips it and prints a "SKIPPING duplicate" message. The net amount correctly settles at `$0.0`, refunded exactly once — without the idempotency check, the customer would have been refunded `$100` against a `$50` charge.

## 6. Walkthrough

Trace `IdempotentRefundCompensation.main` in order. **First**, `chargePayment("order-1", 50.0)` runs, appending a `CHARGE` transaction for `$50.0` to `transactionLog`.

**Next**, `refundPayment("order-1", 50.0, "saga-failure-42")` is called for the first time. Inside, `appliedCompensationIds.add("saga-failure-42")` inserts the ID (it wasn't present) and returns `true`, so the `if` guard is skipped; a `REFUND` transaction for `$50.0`, tagged with that `compensationId`, is appended to `transactionLog`.

**Then**, `refundPayment` is called again with the exact same `compensationId`. This time `appliedCompensationIds.add("saga-failure-42")` returns `false`, since that ID is already in the set — the `if` branch fires, prints the "SKIPPING duplicate" message, and returns immediately without touching `transactionLog`.

**Finally**, `main` computes the net amount by summing `+amount` for every `CHARGE` and `-amount` for every `REFUND` in `transactionLog`. Since the log contains exactly one `CHARGE` of `$50.0` and exactly one `REFUND` of `$50.0` (the duplicate never got appended), the net correctly comes out to `$0.0`.

```
chargePayment($50)                          -> log: [CHARGE $50]
refundPayment(compId=saga-failure-42) #1    -> add() true  -> log: [CHARGE $50, REFUND $50]
refundPayment(compId=saga-failure-42) #2    -> add() false -> SKIPPED, log unchanged
net = +50 (charge) - 50 (refund) = 0  -- correct
```

## 7. Gotchas & takeaways

> Never compensate by deleting or overwriting the original transaction record. A compensation is a new, separate transaction that reverses an effect — the original event stays in the historical record, both for auditability and because the real-world side effect (money actually left an account) may already be irreversible in a literal sense.

- A compensating transaction is the semantic inverse of a forward step, not a database-level rollback — it runs as its own new transaction.
- Compensations must be idempotent: the same failure can trigger the compensation logic more than once, and running it twice must not double-undo the effect.
- Decide each step's compensation at design time, alongside the forward step — not improvised after a failure has already happened in production.
- See [saga isolation anomalies](0325-saga-isolation-anomalies-dirty-reads-lost-updates.md) for what can go wrong when other operations read data *between* a forward step and its eventual compensation.
