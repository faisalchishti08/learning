---
card: system-design
gi: 114
slug: delivery-semantics-at-most-at-least-exactly-once
title: Delivery semantics (at-most / at-least / exactly-once)
---

## 1. What it is

**Delivery semantics** describe how many times a message can be delivered to (and processed by) a consumer, given that networks and processes can fail at any point. **At-most-once** means a message is delivered zero or one times — it might be lost, but never duplicated. **At-least-once** means a message is delivered one or more times — it is never lost, but might be duplicated. **Exactly-once** means a message is delivered and processed exactly one time, with no loss and no duplication — the hardest and most expensive guarantee to actually provide.

## 2. Why & when

The order a consumer does two things — process the message, and acknowledge it to the broker — combined with the possibility of a crash between them, is what determines which semantic you get. If you acknowledge *before* processing, a crash after the acknowledgment but before finishing means the message is gone forever without being handled: at-most-once. If you acknowledge *after* processing, a crash after finishing but before the acknowledgment reaches the broker means the broker redelivers it: at-least-once, since your consumer might process it again. Choose at-most-once only where losing an occasional message is truly fine (a metrics ping); choose at-least-once (the common default) combined with [idempotent consumers](0116-idempotent-consumers.md) for almost everything else; reach for a true exactly-once pipeline (transactional writes tying the consume and produce steps together) only when duplication is unacceptable and the messaging system directly supports it.

## 3. Core concept

- **At-most-once:** acknowledge first, process second. A crash between the two loses the message; it is never retried, since the broker already thinks it was handled.
- **At-least-once:** process first, acknowledge second. A crash between the two means the broker times out waiting for the acknowledgment and redelivers the message — the consumer may see it again after having already processed it once.
- **Exactly-once (why it's hard):** requires the "process" step and the "acknowledge" step to be atomic together, as if they were a single, indivisible operation — no possible crash point can leave them out of sync. Real systems achieve this only with specific support, like transactional writes that commit the processing result and the offset acknowledgment in one atomic step.
- **The practical default:** most systems choose at-least-once, because it is achievable with ordinary retries, and then rely on [idempotent consumers](0116-idempotent-consumers.md) to make duplicate delivery harmless — this combination behaves like exactly-once from the application's point of view, without needing the messaging system to provide a true exactly-once guarantee itself.
- **Delivery vs processing:** these terms describe what the consumer's business logic experiences (was the order shipped once, or twice?) — a message technically "delivered twice" but processed idempotently produces the same end effect as being processed exactly once.

## 4. Diagram

```
AT-MOST-ONCE (ack before process):
  receive -> ACK -> [CRASH HERE] -> process never runs -> message LOST

AT-LEAST-ONCE (process before ack):
  receive -> process -> [CRASH HERE] -> ack never sent -> broker
  redelivers -> consumer processes AGAIN -> message DUPLICATED

EXACTLY-ONCE (atomic together):
  receive -> [process + ack as ONE atomic unit] -> no crash point
  can leave them mismatched -> processed exactly once
```
*Caption: the order of "process" versus "acknowledge", and whether a crash can land between them, determines which delivery guarantee a consumer actually gets.*

## 5. Runnable example

**Level 1 — Basic.** Simulate at-most-once: acknowledge before processing, then a crash loses the message.

**Level 2 — At-least-once.** Process before acknowledging; a crash before the ack causes redelivery and duplicate processing.

**Level 3 — Exactly-once effect via idempotency.** Combine at-least-once redelivery with a processed-ids check, so the duplicate delivery has no duplicate effect.

```java
// DeliverySemantics.java
import java.util.*;

public class DeliverySemantics {

    static int accountBalance = 100;

    public static void main(String[] args) {
        // Level 1: at-most-once - ack BEFORE processing; a crash after ack means processing never happens.
        System.out.println("--- at-most-once ---");
        boolean acked = true; // broker marks the message as delivered
        boolean crashedBeforeProcessing = true; // simulated crash right after the ack
        if (acked && !crashedBeforeProcessing) {
            accountBalance += 50; // this line never runs in this scenario
        }
        System.out.println("balance after at-most-once crash: " + accountBalance + " (deposit of 50 was LOST, never applied)");

        // Level 2: at-least-once - process BEFORE ack; a crash before ack means redelivery and reprocessing.
        System.out.println("--- at-least-once ---");
        accountBalance += 50; // process the deposit
        boolean ackReachedBroker = false; // simulated crash before the ack was sent
        if (!ackReachedBroker) {
            System.out.println("ack lost, broker will redeliver the same message");
            accountBalance += 50; // consumer processes the SAME message again on redelivery
        }
        System.out.println("balance after at-least-once redelivery: " + accountBalance + " (deposit applied TWICE - a duplicate)");

        // Level 3: at-least-once + idempotency = exactly-once effect.
        System.out.println("--- at-least-once with idempotent processing ---");
        accountBalance = 100; // reset for a clean comparison
        Set<String> processedMessageIds = new HashSet<>();

        String messageId = "deposit-msg-77";
        // first delivery
        if (!processedMessageIds.contains(messageId)) {
            accountBalance += 50;
            processedMessageIds.add(messageId);
        }
        System.out.println("balance after first delivery: " + accountBalance);

        // redelivery of the SAME message id (simulating the at-least-once retry)
        if (!processedMessageIds.contains(messageId)) {
            accountBalance += 50; // this is correctly skipped
        } else {
            System.out.println("message " + messageId + " already processed - skipping duplicate, no double-deposit");
        }
        System.out.println("balance after redelivery: " + accountBalance + " (unchanged - exactly-once EFFECT achieved)");
    }
}
```

**How to run:** save as `DeliverySemantics.java`, then run `java DeliverySemantics.java`.

## 6. Walkthrough

1. The at-most-once section sets `acked = true` and `crashedBeforeProcessing = true` *before* the `if` block runs the actual deposit logic — modeling the acknowledgment having already happened while the crash prevents the deposit from ever executing. The balance stays at its original value, and the deposit is permanently lost.
2. The at-least-once section runs `accountBalance += 50` first, then checks `ackReachedBroker`, which is `false` — modeling the acknowledgment being lost after processing already completed. Because the broker never got the ack, it redelivers, and the code applies `accountBalance += 50` a second time.
3. The printed balance after this section (`200` instead of the correct `150`) shows the duplicate-processing problem at-least-once alone can cause.
4. Level 3 resets the balance and introduces `processedMessageIds`, a set tracking which message ids have already been handled. The first delivery of `"deposit-msg-77"` is not in the set, so it applies the deposit and records the id.
5. The simulated redelivery of the exact same message id now finds it already in `processedMessageIds`, so it skips the deposit entirely — the final balance (`150`) is correct, showing that at-least-once delivery combined with an idempotency check produces the same end result as a true exactly-once guarantee, without needing the messaging system itself to provide one.

## 7. Gotchas & takeaways

> Gotcha: "exactly-once" is often advertised by a messaging system but usually only covers a specific scope, like delivery within that one system — the moment your consumer's processing has any side effect *outside* that system (writing to a different database, calling another service), true end-to-end exactly-once requires that external step to also be part of the same atomic guarantee, which most systems do not provide. Idempotent processing is almost always still the safer, more portable choice.

- At-most-once can lose messages; at-least-once can duplicate them; true exactly-once, which does neither, is hard and needs specific transactional support.
- The order of "process" versus "acknowledge", and where a crash lands between them, is exactly what determines which semantic a consumer actually gets.
- The common, practical pattern is at-least-once delivery combined with idempotent processing, which produces an exactly-once *effect* without needing exactly-once *delivery*.
- Related concepts: [Idempotent consumers](0116-idempotent-consumers.md) (the technique used in Level 3), [Message ordering guarantees](0115-message-ordering-guarantees.md) (a related but distinct guarantee about sequence, not duplication).
