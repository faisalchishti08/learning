---
card: microservices
gi: 118
slug: at-most-once-at-least-once-exactly-once-delivery
title: "At-most-once / at-least-once / exactly-once delivery"
---

## 1. What it is

These are the three possible promises a messaging system can make about how many times a given message is delivered to a consumer: **at-most-once** (zero or one delivery — never duplicated, but might be lost), **at-least-once** (one or more deliveries — never lost, but might be duplicated), and **exactly-once** (delivered and processed precisely one time — the ideal, and the hardest to actually achieve).

## 2. Why & when

Which guarantee a system provides is a direct consequence of its [acknowledgement mode](0117-message-acknowledgement-modes.md): auto-ack that removes a message before processing naturally gives at-most-once (if processing fails, it's gone, never retried); manual ack with redelivery on failure or timeout naturally gives at-least-once (a message is retried until acknowledged, but a crash between "processing finished" and "ack sent" causes a duplicate delivery). Choosing which guarantee to design for is not optional once you know the trade-off: silently losing data, versus your consumer logic needing to tolerate duplicates.

At-most-once is acceptable only for data where occasional loss genuinely doesn't matter (a periodic health-check ping). At-least-once is the practical default for anything important, provided the consumer is made idempotent (processing the same message twice has the same effect as processing it once). True exactly-once delivery at the transport level is rare and usually replaced in practice by at-least-once delivery plus idempotent processing, which achieves the same *effective* outcome without needing the underlying guarantee to be perfect.

## 3. Core concept

The guarantee lives in the interaction between when the broker considers a message "consumed" and when the consumer's processing actually completes; idempotency in the consumer is what turns "at least once delivered" into "effectively exactly once processed."

```java
// at-least-once delivery, made SAFE by an idempotent consumer:
// processing the same orderId twice has the same end state as processing it once
if (!alreadyProcessed(event.orderId())) {
    applyOrder(event);
    markProcessed(event.orderId()); // duplicate deliveries after this point are no-ops
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At-most-once may deliver zero times if processing fails; at-least-once may deliver more than once via retries; idempotent processing on top of at-least-once achieves an effectively-exactly-once outcome">
  <text x="110" y="25" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">At-most-once</text>
  <rect x="30" y="40" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="60" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">sent</text>
  <text x="150" y="60" fill="#8b949e" font-size="16" text-anchor="middle" font-family="sans-serif">?</text>
  <text x="60" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">0 or 1 delivery</text>

  <text x="320" y="25" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">At-least-once</text>
  <rect x="240" y="40" width="55" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="267" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">try 1</text>
  <rect x="305" y="40" width="55" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="332" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">try 2</text>
  <rect x="370" y="40" width="55" height="26" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="397" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ok</text>
  <text x="330" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">1+ deliveries, retried until acked</text>

  <text x="540" y="25" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">+ idempotency</text>
  <rect x="470" y="40" width="55" height="26" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="497" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">try 1</text>
  <rect x="535" y="40" width="55" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2,2"/><text x="562" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">try 2 (no-op)</text>
  <text x="530" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">effectively exactly-once</text>
</svg>

Idempotent processing is what makes at-least-once delivery behave like exactly-once from the consumer's point of view.

## 5. Runnable example

Scenario: an inventory-decrement consumer that first demonstrates at-most-once losing an update on failure, then switches to at-least-once with retries (and shows the resulting duplicate-processing bug), then fixes that bug with idempotent processing to achieve an effectively-exactly-once outcome.

### Level 1 — Basic

```java
// File: AtMostOnceLoss.java -- auto-ack style: a failure after "delivery" is unrecoverable.
public class AtMostOnceLoss {
    static int inventory = 10;

    public static void main(String[] args) {
        String[] deliveries = {"DecrementStock:5"}; // only ONE attempt is ever made
        for (String msg : deliveries) {
            try {
                processDelivery(msg); // fails
            } catch (RuntimeException e) {
                System.out.println("Delivery failed and is now PERMANENTLY LOST (at-most-once, no retry): " + e.getMessage());
            }
        }
        System.out.println("Final inventory: " + inventory + " (should be 5, stayed at 10 -- update lost)");
    }

    static void processDelivery(String msg) {
        throw new RuntimeException("warehouse DB timeout");
    }
}
```

**How to run:** `javac AtMostOnceLoss.java && java AtMostOnceLoss` (JDK 17+).

There is exactly one delivery attempt; when it fails, nothing retries it, so the inventory decrement is silently lost — the defining risk of at-most-once.

### Level 2 — Intermediate

```java
// File: AtLeastOnceDuplicateBug.java -- retries fix the loss problem, but now
// expose a NEW problem: the same message can be processed more than once.
public class AtLeastOnceDuplicateBug {
    static int inventory = 10;
    static int attempt = 0;

    public static void main(String[] args) {
        String msg = "DecrementStock:5";
        int maxRetries = 3;

        for (int i = 1; i <= maxRetries; i++) {
            attempt++;
            boolean ackReceivedByBroker = processAndMaybeFailToAck(msg, i);
            if (ackReceivedByBroker) {
                System.out.println("Delivery acked on attempt " + i + " -- broker stops retrying.");
                break;
            }
            System.out.println("Attempt " + i + " processed successfully but the ACK ITSELF was lost -- broker will retry.");
        }
        System.out.println("Final inventory: " + inventory + " (BUG: decremented twice, should be 5, is 0)");
    }

    // simulates: processing succeeds, but the ack back to the broker is lost on attempt 1
    // (e.g. consumer crashes right after finishing work, right before sending the ack)
    static boolean processAndMaybeFailToAck(String msg, int attemptNum) {
        int amount = Integer.parseInt(msg.split(":")[1]);
        inventory -= amount; // the actual work happens EVERY attempt, including retries
        return attemptNum != 1; // simulate: attempt 1's ack is lost, attempt 2's ack succeeds
    }
}
```

**How to run:** `javac AtLeastOnceDuplicateBug.java && java AtLeastOnceDuplicateBug` (JDK 17+).

Expected output:
```
Attempt 1 processed successfully but the ACK ITSELF was lost -- broker will retry.
Delivery acked on attempt 2 -- broker stops retrying.
Final inventory: 0 (BUG: decremented twice, should be 5, is 0)
```

At-least-once genuinely never loses the message, but because the *ack* (not the message) was lost on attempt 1, the broker retried, and the non-idempotent `processAndMaybeFailToAck` re-ran the decrement — the message was delivered twice and processed twice.

### Level 3 — Advanced

```java
// File: IdempotentEffectivelyExactlyOnce.java -- at-least-once delivery, made safe
// with idempotent processing keyed by a message id, achieving the effectively-exactly-once outcome.
import java.util.*;

public class IdempotentEffectivelyExactlyOnce {
    static int inventory = 10;
    static Set<String> processedMessageIds = new HashSet<>(); // idempotency ledger

    public static void main(String[] args) {
        record Delivery(String messageId, String payload) {}
        // simulate at-least-once redelivery: the SAME messageId arrives twice
        List<Delivery> deliveries = List.of(
            new Delivery("msg-001", "DecrementStock:5"),
            new Delivery("msg-001", "DecrementStock:5") // duplicate redelivery, same messageId
        );

        for (Delivery d : deliveries) {
            processIdempotently(d.messageId(), d.payload());
        }
        System.out.println("Final inventory: " + inventory + " (correct: decremented once, effectively-exactly-once)");
    }

    static void processIdempotently(String messageId, String payload) {
        if (processedMessageIds.contains(messageId)) {
            System.out.println("Skipping " + messageId + " -- already processed (idempotency check caught the duplicate)");
            return;
        }
        int amount = Integer.parseInt(payload.split(":")[1]);
        inventory -= amount;
        processedMessageIds.add(messageId); // recorded BEFORE this method could be re-entered for the same id
        System.out.println("Processed " + messageId + ": inventory now " + inventory);
    }
}
```

**How to run:** `javac IdempotentEffectivelyExactlyOnce.java && java IdempotentEffectivelyExactlyOnce` (JDK 17+).

Expected output:
```
Processed msg-001: inventory now 5
Skipping msg-001 -- already processed (idempotency check caught the duplicate)
Final inventory: 5 (correct: decremented once, effectively-exactly-once)
```

## 6. Walkthrough

1. **Level 1** — `processDelivery` throws on its single attempt; there is no retry mechanism at all, so `inventory` never actually changes, silently diverging from the correct value with no error surfaced anywhere except a log line — the at-most-once failure mode.
2. **Level 2, retries fix loss** — the `for` loop now retries up to `maxRetries` times; `processAndMaybeFailToAck` actually performs the `inventory -= amount` decrement on *every* call, simulating that the real work genuinely happened both times, even though only the second attempt's acknowledgement made it back to the broker.
3. **Level 2, why the duplicate happens** — attempt 1 does the decrement and returns `false` (simulating a lost ack), so the broker, from its point of view, never heard confirmation and retries; attempt 2 does the decrement *again* and returns `true`, finally acking — the message was genuinely delivered and processed twice even though the broker only sees one eventual success.
4. **Level 2, the bug made visible** — `inventory` ends at 0 instead of the correct 5, because nothing in `processAndMaybeFailToAck` checks whether this particular decrement had already happened.
5. **Level 3, the idempotency ledger** — `processedMessageIds` is a set keyed by a stable `messageId` that is expected to be the *same* value across redeliveries of the same logical message (this is the broker's or producer's job to keep stable, typically via a deduplication ID attached to the message).
6. **Level 3, the guard** — `processIdempotently` checks `processedMessageIds.contains(messageId)` *before* doing any work; the first delivery of `"msg-001"` is not in the set, so it proceeds, decrements inventory, and immediately adds the id to the set.
7. **Level 3, the duplicate arriving** — the second `Delivery` in the list has the identical `messageId`, `"msg-001"`, simulating a broker redelivery; this time the guard's `contains` check is `true`, so `processIdempotently` returns immediately without touching `inventory` again.
8. **Level 3, the outcome** — `inventory` correctly ends at 5, having been decremented exactly once despite two deliveries — this is "effectively exactly-once": the underlying delivery mechanism is still at-least-once (nothing prevented the duplicate delivery), but the *processing effect* on `inventory` behaves as if it were exactly-once.

## 7. Gotchas & takeaways

> **Gotcha:** idempotency only works if the id used for deduplication is genuinely stable across redeliveries — using a freshly generated id (like a random UUID minted at each retry, or a database auto-increment value assigned per attempt) instead of the message's own original identifier defeats the entire mechanism, because every "duplicate" would look like a brand-new message.

- At-most-once never duplicates a message but can silently lose it if processing fails after the broker considers it delivered.
- At-least-once never silently loses a message (it retries until acknowledged) but can and will deliver duplicates when acks are lost or consumers crash mid-processing.
- True exactly-once delivery at the transport level is rare in practice; the common, practical substitute is at-least-once delivery plus idempotent consumer processing.
- Idempotency requires a stable identifier per logical message, checked and recorded *before* processing can be safely retried on the same id.
- The choice between these guarantees follows directly from the [acknowledgement mode](0117-message-acknowledgement-modes.md) in use — this is a design decision made at the messaging layer, not an afterthought bolted onto consumer code.
