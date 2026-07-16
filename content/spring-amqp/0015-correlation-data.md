---
card: spring-amqp
gi: 15
slug: correlation-data
title: "Correlation data"
---

## 1. What it is

`CorrelationData` is a small wrapper class (holding an ID string and, after the fact, the confirm's ack/nack result and any returned message) that a producer attaches when publishing with confirms enabled (card 0014), so that when an asynchronous confirm or return callback eventually fires, the application can match it back to the specific publish operation that triggered it. Without correlation data, a confirm callback would only know "some message was confirmed" — with it, the callback knows exactly which business operation that confirmation belongs to.

## 2. Why & when

You attach correlation data specifically because publisher confirms are asynchronous and decoupled from the original call site:

- **Multiple messages are being published concurrently, and each one's eventual outcome needs individual tracking** — a batch of order confirmations sent in quick succession each need their own confirm tracked back to the specific order, not a single generic "something in this batch succeeded or failed" signal.
- **A failed confirm needs to trigger a specific compensating action** — if message X's confirm comes back negative, the application needs to know precisely that it was message X (not some other message sent around the same time) so it can retry, alert, or roll back specifically that operation.
- **Confirms arrive out of order relative to publish order** — as noted in card 0014, this is normal and expected, making correlation data (rather than positional or sequential assumptions) the only reliable way to connect a confirm to its originating operation.

## 3. Core concept

Think of correlation data like a claim ticket handed to you when you drop off dry cleaning: the shop doesn't process your specific item the instant you hand it over — it goes into a queue with everyone else's items, and gets processed (confirmed as done) at some later, independent time. When the shop calls to say "order ready," they read off the claim ticket number, not your name from memory, precisely because dozens of other claim tickets are also somewhere in that same queue — the ticket number is what lets a "your order is done" notification, arriving asynchronously and out of order relative to drop-off, connect back unambiguously to the correct specific transaction.

```java
public void publishOrderConfirmation(Order order) {
    CorrelationData correlationData = new CorrelationData(order.id());
    rabbitTemplate.convertAndSend("order.exchange", "order.confirmed", order, correlationData);

    correlationData.getFuture().addCallback(
        confirm -> {
            if (confirm.isAck()) {
                System.out.println("Order " + order.id() + " confirmation published successfully");
            } else {
                System.out.println("Order " + order.id() + " confirmation FAILED: " + confirm.getReason());
                retryQueue.add(order); // compensating action, tied to this exact order
            }
        },
        ex -> System.out.println("Confirm future failed for order " + order.id() + ": " + ex));
}
```

The correlation ID (`order.id()`) is what ties the eventual, asynchronous confirmation outcome back to the exact order that triggered it.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Several messages are published concurrently, each carrying its own correlation ID; confirms arrive later and possibly out of order, and each is matched back to its originating operation purely by that correlation ID" >
  <rect x="20" y="20" width="150" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">publish(order A, corr-A)</text>
  <rect x="20" y="65" width="150" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="87" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">publish(order B, corr-B)</text>

  <line x1="170" y1="35" x2="450" y2="80" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a16)"/>
  <line x1="170" y1="80" x2="450" y2="35" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#a16)"/>

  <rect x="450" y="15" width="170" height="35" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="37" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">confirm(corr-B) arrives first</text>
  <rect x="450" y="65" width="170" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="87" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">confirm(corr-A) arrives second</text>

  <text x="320" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Confirms matched by correlation ID, regardless of arrival order</text>
</svg>

Correlation IDs make out-of-order confirmation delivery a non-issue for correctly attributing outcomes.

## 5. Runnable example

The scenario: tracking confirmations for several concurrently-published order messages, simulated with a plain in-memory correlation tracker (no real RabbitMQ broker or async confirm mechanism needed to demonstrate the ID-based matching itself), starting with a basic single-message tracking, then adding multiple concurrent operations tracked simultaneously, then adding out-of-order confirm arrival to show why matching by ID (not by publish order) is essential.

### Level 1 — Basic

```java
// CorrelationDataDemo.java
import java.util.*;

public class CorrelationDataDemo {
    record CorrelationData(String id) {}

    static Map<String, String> pendingOperations = new HashMap<>();

    static void publish(String correlationId, String businessContext) {
        pendingOperations.put(correlationId, businessContext);
        System.out.println("Published: " + businessContext + " (correlationId=" + correlationId + ")");
    }

    static void handleConfirm(String correlationId, boolean ack) {
        String context = pendingOperations.remove(correlationId);
        System.out.println((ack ? "Confirmed: " : "Failed: ") + context + " (correlationId=" + correlationId + ")");
    }

    public static void main(String[] args) {
        publish("corr-1", "OrderCreated(ORD-1)");
        handleConfirm("corr-1", true);
    }
}
```

How to run: `java CorrelationDataDemo.java`. Expected output: `Published: OrderCreated(ORD-1) (correlationId=corr-1)` then `Confirmed: OrderCreated(ORD-1) (correlationId=corr-1)` — the confirmation matched back to the exact operation via its correlation ID.

### Level 2 — Intermediate

```java
// CorrelationDataDemo.java
import java.util.*;

public class CorrelationDataDemo {
    static Map<String, String> pendingOperations = new HashMap<>();

    static void publish(String correlationId, String businessContext) {
        pendingOperations.put(correlationId, businessContext);
        System.out.println("Published: " + businessContext + " (correlationId=" + correlationId + ")");
    }

    static void handleConfirm(String correlationId, boolean ack) {
        String context = pendingOperations.remove(correlationId);
        System.out.println((ack ? "Confirmed: " : "Failed: ") + context + " (correlationId=" + correlationId + ")");
    }

    public static void main(String[] args) {
        // Real-world concern: several operations are published concurrently, each needing
        // independent tracking -- not a single shared status for "the batch."
        publish("corr-order-1", "OrderCreated(ORD-1)");
        publish("corr-order-2", "OrderCreated(ORD-2)");
        publish("corr-order-3", "OrderCreated(ORD-3)");

        System.out.println("-- confirms arrive later, independently --");
        handleConfirm("corr-order-1", true);
        handleConfirm("corr-order-2", false);
        handleConfirm("corr-order-3", true);
    }
}
```

How to run: `java CorrelationDataDemo.java`. Expected output: three publish lines, then three independent confirm outcomes — `ORD-2` failing while `ORD-1` and `ORD-3` succeed, each tracked and reported entirely independently rather than as one aggregate batch status.

### Level 3 — Advanced

```java
// CorrelationDataDemo.java
import java.util.*;

public class CorrelationDataDemo {
    static Map<String, String> pendingOperations = new HashMap<>();
    static List<String> compensatingActionsTriggered = new ArrayList<>();

    static void publish(String correlationId, String businessContext) {
        pendingOperations.put(correlationId, businessContext);
    }

    // Production concern: confirms arrive OUT OF ORDER relative to publish order (network
    // timing, broker-side batching) -- matching must rely purely on correlation ID, never on
    // an assumption that confirms arrive in the same sequence messages were sent.
    static void handleConfirm(String correlationId, boolean ack) {
        String context = pendingOperations.remove(correlationId);
        if (context == null) {
            System.out.println("WARNING: confirm for unknown correlationId " + correlationId + " (already handled or never tracked)");
            return;
        }
        if (ack) {
            System.out.println("Confirmed: " + context);
        } else {
            System.out.println("Failed: " + context + " -- triggering compensating action");
            compensatingActionsTriggered.add(context);
        }
    }

    public static void main(String[] args) {
        publish("corr-order-1", "OrderCreated(ORD-1)"); // published first
        publish("corr-order-2", "OrderCreated(ORD-2)"); // published second
        publish("corr-order-3", "OrderCreated(ORD-3)"); // published third

        // Confirms arrive in a DIFFERENT order than publish order -- order 3's confirm first,
        // then order 1's, then order 2's -- exactly the scenario correlation IDs handle correctly.
        handleConfirm("corr-order-3", true);
        handleConfirm("corr-order-1", true);
        handleConfirm("corr-order-2", false);

        System.out.println("Compensating actions needed for: " + compensatingActionsTriggered);
    }
}
```

How to run: `java CorrelationDataDemo.java`. Expected output: `Confirmed: OrderCreated(ORD-3)` first (despite being published last), then `Confirmed: OrderCreated(ORD-1)`, then `Failed: OrderCreated(ORD-2) -- triggering compensating action`, and finally `Compensating actions needed for: [OrderCreated(ORD-2)]` — every confirm correctly attributed to its originating order regardless of the mismatched arrival order relative to when each was actually published.

## 6. Walkthrough

Trace correlation data through a burst of concurrent publishes and their eventual, out-of-order confirmations.

1. **Publish with correlation data**: for each business operation needing confirmation tracking, application code creates a `CorrelationData` instance carrying a unique ID (often the business entity's own ID, like an order ID, for easy debugging) and passes it to `convertAndSend`.
2. **Tracked pending state**: the application (or `RabbitTemplate`'s internal mechanism, when using the future-based confirm API) records this correlation ID as awaiting confirmation, associated with whatever business context matters for eventual compensating action.
3. **Messages sent concurrently**: several such publishes can happen in quick succession, each with its own distinct correlation ID — the broker processes and eventually acknowledges each independently.
4. **Confirms arrive asynchronously, in arbitrary order**: because acknowledgment timing depends on broker-internal processing and network conditions rather than publish order, confirms can and do arrive in a different sequence than the messages were originally sent in.
5. **Matching by ID, not by order**: each confirm callback invocation carries its own correlation data; the application looks up the pending operation by that ID (not by assuming "the next confirm belongs to the next unconfirmed publish in send order") to correctly attribute the outcome.
6. **Compensating action on failure**: for any confirm indicating failure (a NACK), the application takes whatever specific action that particular business operation requires — a retry, an alert, a compensating rollback — precisely because correlation data made it possible to know exactly which operation failed, not just that "something" did.

```
publish(order-1, corr-1) -- publish(order-2, corr-2) -- publish(order-3, corr-3)
  [confirms arrive later, in ANY order]
    confirm(corr-3) -> matched to order-3 -> success
    confirm(corr-1) -> matched to order-1 -> success
    confirm(corr-2) -> matched to order-2 -> FAILURE -> compensating action for order-2 specifically
```

## 7. Gotchas & takeaways

> **Gotcha:** using a non-unique or reused correlation ID (accidentally reusing the same ID across two different publish operations, perhaps due to an ID-generation bug) causes a confirm to be matched to the wrong pending operation, or to overwrite tracking for one operation with another — always generate correlation IDs that are genuinely unique per publish operation, typically derived from the business entity's own unique identifier or a dedicated UUID.

- Correlation data exists specifically to solve the "which operation does this asynchronous confirm belong to" problem — without it, confirms are only useful in aggregate ("something succeeded, something failed"), not for driving operation-specific compensating logic.
- Basing a correlation ID on a meaningful business identifier (an order ID, a request ID) rather than an opaque random value makes debugging and log correlation significantly easier when investigating a specific failed confirm later.
- Never assume confirms arrive in the same order messages were published — this is normal, expected, asynchronous behavior, not an edge case, and correlation-ID-based matching is the only correct way to handle it.
- Correlation data's usefulness is entirely tied to publisher confirms being enabled (card 0014) in the first place — without confirms turned on, there's no asynchronous outcome to correlate anything against, making correlation data a companion concept rather than something used independently.
