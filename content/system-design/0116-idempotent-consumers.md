---
card: system-design
gi: 116
slug: idempotent-consumers
title: Idempotent consumers
---

## 1. What it is

An **idempotent consumer** produces the same end result no matter how many times it processes the same message. Processing a duplicate delivery once, twice, or ten times leaves the system in exactly the same state as processing it once — the extra attempts have no additional effect. This directly answers the duplication risk of [at-least-once delivery](0114-delivery-semantics-at-most-at-least-exactly-once.md), where a message can genuinely be delivered more than once.

## 2. Why & when

At-least-once delivery is the practical default for most messaging systems, because it never loses a message — but it can deliver the same message twice (for example, if a consumer crashes right after processing but before acknowledging). If a consumer's processing has a side effect that is not naturally safe to repeat — charging a credit card, incrementing a counter, sending an email — a duplicate delivery causes a duplicate side effect: a double charge, a wrong count, a spammy second email. Make a consumer idempotent any time its processing has such a side effect and the messaging system provides at-least-once (not a true, verified exactly-once) delivery — which is almost always.

## 3. Core concept

- **Track processed message ids:** record the id of every message once it has been successfully processed (in a database table, a cache, or a dedicated dedup store); before processing a new message, check whether its id is already recorded, and skip it if so.
- **Naturally idempotent operations:** some operations are already safe to repeat without any extra tracking — `SET balance = 100` gives the same result no matter how many times it runs, unlike `balance += 50`, which is not naturally idempotent.
- **Use a unique, stable message id:** the id used for deduplication must be the same across all deliveries of the same logical message — usually a business-meaningful id (an `orderId`, a `paymentId`) rather than a broker-generated delivery id, which might differ between the original delivery and a redelivery.
- **The check-and-record must be atomic with the effect:** if "check if processed" and "apply the effect and record it" are two separate steps that are not transactional together, a crash between them can still let a duplicate slip through — the two must be combined into one atomic database transaction where possible.
- **Time-bounded deduplication windows:** tracking every message id forever is not always practical; many systems keep a deduplication record only for a bounded window (e.g. 24 hours), long enough to catch realistic redeliveries without unbounded storage growth.

## 4. Diagram

```
Non-idempotent consumer:            Idempotent consumer:

  delivery 1: balance += 50           delivery 1: check id "pay-77" -> not seen
              (balance: 100 -> 150)                apply: balance += 50, record id "pay-77"
                                                     (balance: 100 -> 150)
  delivery 2 (duplicate):             delivery 2 (duplicate):
              balance += 50                          check id "pay-77" -> ALREADY SEEN
              (balance: 150 -> 200)                  SKIP - no additional effect
                                                     (balance stays 150)

  WRONG: customer charged/credited    CORRECT: duplicate delivery has
  twice for one real event.           zero additional effect.
```
*Caption: tracking a message's unique id and skipping already-processed ones turns a duplicate delivery into a harmless no-op.*

## 5. Runnable example

**Level 1 — Basic.** A naive, non-idempotent consumer applies an effect twice when the message is delivered twice.

**Level 2 — Idempotent fix.** Track processed message ids and skip a duplicate.

**Level 3 — Naturally idempotent operation.** Rewrite the effect itself (a "set" instead of an "add") so it needs no tracking at all.

```java
// IdempotentConsumer.java
import java.util.*;

public class IdempotentConsumer {

    record PaymentMessage(String paymentId, int amount) {}

    public static void main(String[] args) {
        // Level 1: naive consumer - NOT idempotent, applies the effect every time it's called.
        int naiveBalance = 100;
        PaymentMessage msg = new PaymentMessage("pay-77", 50);

        naiveBalance += msg.amount(); // first delivery
        System.out.println("naive consumer after delivery 1: balance=" + naiveBalance);
        naiveBalance += msg.amount(); // duplicate redelivery of the SAME message
        System.out.println("naive consumer after delivery 2 (duplicate): balance=" + naiveBalance + " (WRONG - charged twice)");

        // Level 2: idempotent consumer - tracks processed ids, skips duplicates.
        int idempotentBalance = 100;
        Set<String> processedIds = new HashSet<>();

        idempotentBalance = processIfNew(msg, idempotentBalance, processedIds);
        System.out.println("idempotent consumer after delivery 1: balance=" + idempotentBalance);
        idempotentBalance = processIfNew(msg, idempotentBalance, processedIds); // duplicate redelivery
        System.out.println("idempotent consumer after delivery 2 (duplicate): balance=" + idempotentBalance + " (correct - unchanged)");

        // Level 3: naturally idempotent operation - a "set" instead of an "add" needs no id tracking.
        record BalanceSnapshot(String accountId, int newBalance) {}
        Map<String, Integer> accountBalances = new HashMap<>();
        BalanceSnapshot snapshot = new BalanceSnapshot("acc-1", 150); // "the balance IS now 150", not "add 50"

        accountBalances.put(snapshot.accountId(), snapshot.newBalance()); // delivery 1
        accountBalances.put(snapshot.accountId(), snapshot.newBalance()); // duplicate delivery 2 - harmless, same result
        System.out.println("naturally idempotent 'set' after 2 deliveries: " + accountBalances.get("acc-1") + " (still correct, no tracking needed)");
    }

    static int processIfNew(PaymentMessage msg, int currentBalance, Set<String> processedIds) {
        if (processedIds.contains(msg.paymentId())) {
            System.out.println("payment " + msg.paymentId() + " already processed - skipping duplicate");
            return currentBalance; // no additional effect
        }
        processedIds.add(msg.paymentId());
        return currentBalance + msg.amount();
    }
}
```

**How to run:** save as `IdempotentConsumer.java`, then run `java IdempotentConsumer.java`.

## 6. Walkthrough

1. Level 1 calls `naiveBalance += msg.amount()` twice in a row, simulating the same message being delivered twice; the balance goes from `100` to `150` to `200` — a clear, wrong double-application of the same payment.
2. Level 2's `processIfNew` checks `processedIds.contains(msg.paymentId())` before applying any effect. On the first call, `"pay-77"` is not in the set, so it applies the amount and records the id.
3. On the second call — the duplicate redelivery of the exact same `msg` — `"pay-77"` is now found in `processedIds`, so the function returns `currentBalance` unchanged, printing that it skipped a duplicate.
4. The idempotent balance ends at `150` after both deliveries, correctly reflecting the payment applied exactly once, regardless of how many times the message was actually delivered.
5. Level 3 shows an entirely different way to reach safety: instead of an incrementing effect (`+= amount`), the message carries the *resulting* value directly (`newBalance = 150`). Applying `accountBalances.put(...)` with the same snapshot any number of times always leaves the same final value — no id tracking is needed at all, because the operation is naturally idempotent by construction.

## 7. Gotchas & takeaways

> Gotcha: deduplicating by a broker-assigned delivery id instead of a business-meaningful id (like `paymentId`) does not actually protect against duplicates, because a genuine redelivery of the same logical message can arrive with a *different* delivery id. Always dedupe on an id that stays the same across every delivery of the same real-world event.

- An idempotent consumer produces the same result whether a message is processed once or many times, directly neutralizing the duplication risk of at-least-once delivery.
- Tracking processed message ids (using a stable, business-meaningful id) is the general-purpose technique; designing the operation itself as a "set" rather than an "add" avoids needing tracking at all when possible.
- The check for "already processed" and the effect itself must be atomic together, or a crash between them can still let a duplicate through.
- Related concepts: [Delivery semantics (at-most / at-least / exactly-once)](0114-delivery-semantics-at-most-at-least-exactly-once.md) (the delivery guarantee that makes this necessary), [Dead-letter queues & poison messages](0118-dead-letter-queues-poison-messages.md) (handling messages that fail no matter how many times they are retried).
