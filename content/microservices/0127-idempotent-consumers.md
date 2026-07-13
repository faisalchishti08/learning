---
card: microservices
gi: 127
slug: idempotent-consumers
title: "Idempotent consumers"
---

## 1. What it is

An idempotent consumer is one whose processing logic produces the same end state whether a given message is delivered and processed once or several times — the defining property that turns [at-least-once delivery](0118-at-most-once-at-least-once-exactly-once-delivery.md)'s occasional duplicates from a correctness bug into a harmless non-event.

## 2. Why & when

[Message deduplication](0126-message-deduplication.md) reduces duplicate deliveries but, by its own nature (bounded retention windows, producer-side gaps), cannot guarantee a consumer will *never* see the same message twice. Rather than chase an unreachable "zero duplicates, guaranteed" target at the messaging layer, idempotent consumers accept that duplicates will occasionally arrive and make that fact harmless by design — the consumer itself checks whether it has already applied a given message's effect and, if so, does nothing on the repeat.

Build idempotency into any consumer processing at-least-once messages where a duplicate would otherwise cause real harm — double-charging a payment, double-decrementing inventory, sending a customer two confirmation emails. It is unnecessary only for operations that are naturally idempotent already (setting a field to an absolute value, like `status = "SHIPPED"`, has the same effect no matter how many times it's applied) or for consequences genuinely too minor to matter if duplicated.

## 3. Core concept

The consumer records, durably, which message ids it has already successfully processed, and checks that record before applying any effect; a duplicate delivery finds its id already recorded and skips straight past the processing logic, achieving the same end state as if it had only ever arrived once.

```java
if (processedMessageIds.contains(message.id())) {
    return; // already applied this exact message's effect -- a duplicate delivery is now a no-op
}
applyOrderToInventory(message);       // the actual effect
processedMessageIds.add(message.id()); // recorded so a FUTURE duplicate is also a no-op
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A message is delivered twice; the first delivery checks a processed-ids record, finds nothing, applies its effect, and records itself; the second, duplicate delivery checks the same record, finds a match, and skips processing entirely">
  <rect x="20" y="20" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Delivery #1 (id-1)</text>

  <rect x="20" y="125" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="152" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Delivery #2 (id-1)</text>

  <rect x="230" y="70" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="92" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Processed-ids record</text>
  <text x="320" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">{ } -&gt; { id-1 }</text>

  <rect x="470" y="20" width="140" height="45" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Effect applied</text>

  <rect x="470" y="125" width="140" height="45" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="540" y="152" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Skipped (no-op)</text>

  <line x1="170" y1="42" x2="228" y2="80" stroke="#8b949e" marker-end="url(#arr13)"/>
  <line x1="170" y1="148" x2="228" y2="105" stroke="#8b949e" marker-end="url(#arr13)"/>
  <line x1="410" y1="85" x2="468" y2="42" stroke="#8b949e" marker-end="url(#arr13)"/>
  <line x1="410" y1="105" x2="468" y2="148" stroke="#8b949e" marker-end="url(#arr13)"/>

  <defs>
    <marker id="arr13" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same processed-ids check produces two different outcomes purely based on whether the id was already recorded.

## 5. Runnable example

Scenario: a payment consumer that starts non-idempotent and demonstrates double-charging on duplicate delivery, then adds an in-memory idempotency check to fix it, and finally makes that check durable and crash-safe by writing the record atomically alongside the effect, so a crash between the two steps can't reintroduce the bug.

### Level 1 — Basic

```java
// File: NonIdempotentDoubleCharge.java -- a duplicate delivery charges the customer twice.
import java.util.*;

public class NonIdempotentDoubleCharge {
    static double customerBalance = 100.00;

    public static void main(String[] args) {
        record PaymentEvent(String messageId, double amount) {}
        // simulates at-least-once delivery: the SAME messageId arrives twice
        List<PaymentEvent> deliveries = List.of(
            new PaymentEvent("payment-msg-1", 25.00),
            new PaymentEvent("payment-msg-1", 25.00) // duplicate delivery of the identical message
        );

        for (PaymentEvent event : deliveries) {
            chargeCustomer(event.amount()); // no check for "have I already done this"
        }
        System.out.println("Final balance: " + customerBalance + " (BUG: charged twice, should be 75.00, is 50.00)");
    }

    static void chargeCustomer(double amount) {
        customerBalance -= amount;
        System.out.println("Charged " + amount + ", balance now " + customerBalance);
    }
}
```

**How to run:** `javac NonIdempotentDoubleCharge.java && java NonIdempotentDoubleCharge` (JDK 17+).

Expected output:
```
Charged 25.0, balance now 75.0
Charged 25.0, balance now 50.0
Final balance: 50.0 (BUG: charged twice, should be 75.00, is 50.00)
```

### Level 2 — Intermediate

```java
// File: IdempotentCheck.java -- an in-memory processed-ids check makes the duplicate a no-op.
import java.util.*;

public class IdempotentCheck {
    static double customerBalance = 100.00;
    static Set<String> processedMessageIds = new HashSet<>();

    public static void main(String[] args) {
        record PaymentEvent(String messageId, double amount) {}
        List<PaymentEvent> deliveries = List.of(
            new PaymentEvent("payment-msg-1", 25.00),
            new PaymentEvent("payment-msg-1", 25.00) // same duplicate as Level 1
        );

        for (PaymentEvent event : deliveries) {
            processIdempotently(event.messageId(), event.amount());
        }
        System.out.println("Final balance: " + customerBalance + " (correct: charged once)");
    }

    static void processIdempotently(String messageId, double amount) {
        if (processedMessageIds.contains(messageId)) {
            System.out.println("Skipping " + messageId + " -- already processed, no-op.");
            return;
        }
        customerBalance -= amount;
        processedMessageIds.add(messageId);
        System.out.println("Charged " + amount + " for " + messageId + ", balance now " + customerBalance);
    }
}
```

**How to run:** `javac IdempotentCheck.java && java IdempotentCheck` (JDK 17+).

Expected output:
```
Charged 25.0 for payment-msg-1, balance now 75.0
Skipping payment-msg-1 -- already processed, no-op.
Final balance: 75.0 (correct: charged once)
```

### Level 3 — Advanced

```java
// File: AtomicDurableIdempotency.java -- the effect and the "processed" record must be
// updated ATOMICALLY together; doing them as two separate steps leaves a crash window
// where a retry after a mid-processing crash could still double-apply the effect.
import java.util.*;

public class AtomicDurableIdempotency {
    // simulates a durable store where the payment ledger entry AND the
    // processed-id marker live in the SAME record, written in one atomic operation
    static class Ledger {
        private final Map<String, Double> balanceByCustomer = new HashMap<>();
        private final Map<String, String> appliedMessageIdByCustomer = new HashMap<>(); // last-applied id, per customer

        Ledger() { balanceByCustomer.put("cust-1", 100.00); }

        // ATOMIC: checks-and-applies as one operation, mirroring a single database
        // transaction that updates both the balance and the idempotency marker together
        synchronized boolean applyChargeIdempotently(String customerId, String messageId, double amount) {
            String lastApplied = appliedMessageIdByCustomer.get(customerId);
            if (messageId.equals(lastApplied)) {
                return false; // already applied -- atomic check prevents ANY window for a double-apply
            }
            double newBalance = balanceByCustomer.get(customerId) - amount;
            balanceByCustomer.put(customerId, newBalance);           // effect
            appliedMessageIdByCustomer.put(customerId, messageId);   // marker -- committed TOGETHER, not two separate steps
            return true;
        }

        double balanceOf(String customerId) { return balanceByCustomer.get(customerId); }
    }

    public static void main(String[] args) {
        Ledger ledger = new Ledger();
        record PaymentEvent(String messageId, double amount) {}

        // simulate: original delivery, a "consumer crash and restart" causing a retry,
        // then a genuinely LATER, different payment for the same customer
        List<PaymentEvent> deliveries = List.of(
            new PaymentEvent("payment-msg-1", 25.00),
            new PaymentEvent("payment-msg-1", 25.00), // redelivered after a simulated crash/restart
            new PaymentEvent("payment-msg-2", 10.00)  // a genuinely NEW, different payment
        );

        for (PaymentEvent event : deliveries) {
            boolean applied = ledger.applyChargeIdempotently("cust-1", event.messageId(), event.amount());
            System.out.println(event.messageId() + ": applied=" + applied + ", balance=" + ledger.balanceOf("cust-1"));
        }
    }
}
```

**How to run:** `javac AtomicDurableIdempotency.java && java AtomicDurableIdempotency` (JDK 17+).

Expected output:
```
payment-msg-1: applied=true, balance=75.0
payment-msg-1: applied=false, balance=75.0
payment-msg-2: applied=true, balance=65.0
```

## 6. Walkthrough

1. **Level 1** — `chargeCustomer` unconditionally subtracts `amount` from `customerBalance` every time it's called, with no memory of what it has already done; two identical `PaymentEvent` deliveries produce two identical deductions.
2. **Level 2, the guard** — `processIdempotently` checks `processedMessageIds.contains(messageId)` *before* touching `customerBalance`; the first delivery of `"payment-msg-1"` is not yet in the set, so it proceeds and records itself; the second, identical delivery finds the id already present and returns immediately.
3. **Level 2, the corrected balance** — `customerBalance` ends at 75.0, exactly matching a single 25.00 charge, despite two deliveries — the duplicate genuinely had zero effect on the final state.
4. **Level 3, the subtler problem Level 2 doesn't address** — in `IdempotentCheck`, the balance update (`customerBalance -= amount`) and the marker update (`processedMessageIds.add(messageId)`) are two *separate* statements; in a real system with a process that could crash between them, a crash right after the balance update but before the marker is recorded would leave the effect applied but *unrecorded* — a subsequent retry would see no matching id and apply the charge again.
5. **Level 3, the atomic fix** — `applyChargeIdempotently` is `synchronized` and, more importantly, is written as the pattern a real system would implement with a single database transaction: the check, the balance update, and the marker update all happen as one indivisible unit — in a real system this would be one SQL `UPDATE` (or a conditional write) covering both the balance column and an idempotency-key column in the same row, committed together.
6. **Level 3, tracing the three deliveries** — the first `"payment-msg-1"` finds no matching `lastApplied`, applies the charge, and records itself, returning `applied=true`; the second, identical `"payment-msg-1"` (simulating a post-crash retry) finds `lastApplied` now equals `"payment-msg-1"`, so it returns `applied=false` without touching the balance at all; the third event, `"payment-msg-2"`, has a genuinely different id, so it is correctly treated as new work and applied.
7. **Level 3, why atomicity matters here** — because check-and-apply happen as one operation, there is no window in which the effect could be committed without its corresponding marker (or vice versa) — this is the property that makes idempotency reliable even in the presence of a consumer crashing at an arbitrary point during processing, not just reliable against duplicates that happen to arrive back-to-back with no crash in between.

## 7. Gotchas & takeaways

> **Gotcha:** splitting "apply the effect" and "record that it was applied" into two separate, non-atomic steps reintroduces the exact bug idempotency was meant to fix, just in a narrower window — a crash between the two steps leaves state that looks unprocessed to a future check, even though the effect already happened; the check-record-and-apply sequence needs to be atomic, typically via a single database transaction.

- An idempotent consumer produces the same end state whether a message is processed once or multiple times, making duplicate deliveries harmless rather than a correctness bug.
- The mechanism is a durable record of already-processed message ids, checked before applying any effect.
- The check, the effect, and the recording of the id must happen atomically (typically one database transaction) — splitting them into separate steps reopens a crash window where duplicates can still slip through.
- Idempotent consumers are the actual correctness guarantee for at-least-once systems; [message deduplication](0126-message-deduplication.md) at the broker is a performance optimization layered in front of it, not a substitute.
- Not every operation needs this treatment — operations that are naturally idempotent (setting an absolute value rather than incrementing) don't need an explicit processed-ids check at all.
