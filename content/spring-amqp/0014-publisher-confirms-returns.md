---
card: spring-amqp
gi: 14
slug: publisher-confirms-returns
title: "Publisher confirms & returns"
---

## 1. What it is

Publisher confirms are RabbitMQ's mechanism for a producer to know, asynchronously, that a published message was actually received and accepted by the broker — enabled via `CachingConnectionFactory.setPublisherConfirmType(ConfirmType.CORRELATED)` and consumed through `RabbitTemplate.setConfirmCallback(...)`. Returns are a related but distinct mechanism for when a message reaches the broker but cannot be routed to any queue at all (no matching binding) — handled via `RabbitTemplate.setReturnsCallback(...)` combined with `setMandatory(true)`. Together they close the gap between "I called send()" and "I actually know what happened to this message."

## 2. Why & when

You enable publisher confirms and returns whenever a producer needs genuine delivery assurance beyond the fire-and-forget default:

- **A message's loss would be a real business problem, and the application needs to know if publishing silently failed** — without confirms, a `send()` call returning without an exception only means the client successfully wrote to the TCP socket; it says nothing about whether the broker actually persisted or accepted the message, since network issues or broker-side problems can occur after the call returns.
- **A message might be published with a routing key that matches no binding**, which (as noted in card 0001) is silently dropped by default — enabling mandatory publishing with a returns callback surfaces this as an explicit, actionable event instead of a silent, undetectable loss.
- **Building genuinely reliable publish confirmation into critical-path business flows** — payment processing, order confirmation, or any flow where "the message was definitely accepted" needs to be verifiable, not assumed.

## 3. Core concept

Think of a publisher confirm as a courier company texting you "package received at our depot" after you drop off a parcel — you now know for certain it made it past the point where you personally handed it over, even though you can't watch it happen. A return is a different notification entirely: it's the courier calling you back to say "we received your package, but the address you wrote doesn't correspond to any actual delivery route we have — we're handing it back to you" — the parcel reached the depot, but had nowhere valid to go from there.

```java
CachingConnectionFactory connectionFactory = new CachingConnectionFactory("rabbitmq-host");
connectionFactory.setPublisherConfirmType(CachingConnectionFactory.ConfirmType.CORRELATED);
connectionFactory.setPublisherReturns(true);

RabbitTemplate rabbitTemplate = new RabbitTemplate(connectionFactory);
rabbitTemplate.setMandatory(true); // required for returns to actually fire

rabbitTemplate.setConfirmCallback((correlationData, ack, cause) -> {
    if (ack) {
        System.out.println("Broker confirmed receipt: " + correlationData);
    } else {
        System.out.println("Broker NACKed the message: " + cause);
    }
});

rabbitTemplate.setReturnsCallback(returned -> {
    System.out.println("Message could not be routed: " + returned.getReplyText());
});
```

Confirms tell you the broker got the message at all; returns tell you it got there but had nowhere to go.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A publisher confirm asynchronously acknowledges the broker received the message; a return fires separately when the message reached the broker but matched no binding and had nowhere to be routed" >
  <rect x="20" y="20" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Producer sends</text>

  <line x1="170" y1="42" x2="240" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a15)"/>
  <rect x="240" y="20" width="150" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Broker receives</text>

  <line x1="315" y1="65" x2="200" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a15)"/>
  <text x="230" y="90" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">confirm (ack)</text>

  <line x1="390" y1="42" x2="460" y2="42" stroke="#8b949e" stroke-width="1.2"/>
  <text x="425" y="32" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">routing attempted</text>

  <rect x="460" y="20" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">No matching binding</text>

  <line x1="460" y1="60" x2="350" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a15)"/>
  <text x="400" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">return (unroutable)</text>
</svg>

Two independent, asynchronous callbacks answer two different questions about the same publish.

## 5. Runnable example

The scenario: publishing messages and handling both confirms and returns, simulated with a plain in-memory model standing in for the broker's asynchronous acknowledgment behavior (no real RabbitMQ broker needed to demonstrate the confirm/return distinction and callback wiring), starting with a basic confirm callback, then adding a returns callback for unroutable messages, then adding correlation data so a specific confirm can be matched back to the specific business operation that triggered it.

### Level 1 — Basic

```java
// PublisherConfirmsDemo.java
import java.util.function.*;

public class PublisherConfirmsDemo {
    // Stand-in for RabbitTemplate's confirm callback mechanism.
    static void publishWithConfirm(String payload, boolean brokerWillAccept, BiConsumer<Boolean, String> confirmCallback) {
        System.out.println("Sent: " + payload);
        // Simulates the broker's ASYNCHRONOUS confirm arriving some time after the send call returns.
        if (brokerWillAccept) {
            confirmCallback.accept(true, null);
        } else {
            confirmCallback.accept(false, "internal broker error");
        }
    }

    public static void main(String[] args) {
        publishWithConfirm("{\"orderId\":\"ORD-1\"}", true, (ack, cause) -> {
            System.out.println(ack ? "Broker confirmed receipt" : "Broker NACKed: " + cause);
        });
    }
}
```

How to run: `java PublisherConfirmsDemo.java`. Expected output: `Sent: {"orderId":"ORD-1"}` then `Broker confirmed receipt` — a basic acknowledgment that the broker actually accepted the message, beyond just the send call itself returning without an exception.

### Level 2 — Intermediate

```java
// PublisherConfirmsDemo.java
import java.util.function.*;

public class PublisherConfirmsDemo {
    static void publishWithConfirm(String payload, boolean brokerWillAccept, BiConsumer<Boolean, String> confirmCallback) {
        System.out.println("Sent: " + payload);
        confirmCallback.accept(brokerWillAccept, brokerWillAccept ? null : "internal broker error");
    }

    // Real-world concern: a message can be confirmed (the broker accepted it) yet still be
    // UNROUTABLE if no binding matches its routing key -- a separate, distinct notification
    // (the "return") is needed to catch this, since a confirm alone says nothing about routing.
    static void publishMandatory(String routingKey, String payload, boolean hasMatchingBinding,
                                  BiConsumer<Boolean, String> confirmCallback, Consumer<String> returnsCallback) {
        System.out.println("Sent (mandatory) to routingKey=" + routingKey + ": " + payload);
        confirmCallback.accept(true, null); // broker accepted the message itself
        if (!hasMatchingBinding) {
            returnsCallback.accept("NO_ROUTE: no queue bound for routing key '" + routingKey + "'");
        }
    }

    public static void main(String[] args) {
        publishMandatory("order.cancelled", "{\"orderId\":\"ORD-1\"}", false,
            (ack, cause) -> System.out.println(ack ? "Confirmed by broker" : "NACKed: " + cause),
            reason -> System.out.println("Returned: " + reason));
    }
}
```

How to run: `java PublisherConfirmsDemo.java`. Expected output: `Sent (mandatory) ...`, then `Confirmed by broker` (the broker did accept the message), then `Returned: NO_ROUTE: no queue bound for routing key 'order.cancelled'` — demonstrating that a message can be simultaneously confirmed (received by the broker) and returned (unroutable), since these two callbacks answer genuinely different questions.

### Level 3 — Advanced

```java
// PublisherConfirmsDemo.java
import java.util.*;
import java.util.function.*;

public class PublisherConfirmsDemo {
    record CorrelationData(String id) {}

    // Production concern: an application publishing many messages concurrently needs to match
    // each ASYNCHRONOUS confirm back to the SPECIFIC business operation that triggered it --
    // this is exactly what CorrelationData (attached at publish time) is for.
    static class PendingPublishTracker {
        Map<String, String> pendingOperations = new HashMap<>();

        void trackPublish(CorrelationData correlationData, String businessContext) {
            pendingOperations.put(correlationData.id(), businessContext);
        }

        void handleConfirm(CorrelationData correlationData, boolean ack, String cause) {
            String context = pendingOperations.remove(correlationData.id());
            if (ack) {
                System.out.println("[" + context + "] confirmed (correlationId=" + correlationData.id() + ")");
            } else {
                System.out.println("[" + context + "] NACKed (correlationId=" + correlationData.id() + "): " + cause
                    + " -- triggering compensating action for this specific operation");
            }
        }
    }

    public static void main(String[] args) {
        PendingPublishTracker tracker = new PendingPublishTracker();

        CorrelationData order1Correlation = new CorrelationData("corr-order-1");
        CorrelationData order2Correlation = new CorrelationData("corr-order-2");

        tracker.trackPublish(order1Correlation, "OrderCreated(ORD-1)");
        tracker.trackPublish(order2Correlation, "OrderCreated(ORD-2)");

        // Confirms arrive asynchronously, later, and possibly out of order relative to publishing.
        tracker.handleConfirm(order2Correlation, true, null);
        tracker.handleConfirm(order1Correlation, false, "channel closed unexpectedly");
    }
}
```

How to run: `java PublisherConfirmsDemo.java`. Expected output: `[OrderCreated(ORD-2)] confirmed (correlationId=corr-order-2)` then `[OrderCreated(ORD-1)] NACKed (correlationId=corr-order-1): channel closed unexpectedly -- triggering compensating action for this specific operation` — the confirms arriving out of order relative to when the messages were sent, and each still correctly matched back to its own specific business operation via correlation data, exactly the tracking a production system needs to react to failures at the level of individual business operations.

## 6. Walkthrough

Trace a published message through both possible outcomes: successful delivery, and the unroutable-message case.

1. **Publish with mandatory flag and correlation data**: application code calls `convertAndSend` with `mandatory=true` set on the template, and attaches a `CorrelationData` object uniquely identifying this specific publish operation.
2. **Message reaches the broker**: the broker receives the message over the already-open channel — this is a genuinely separate event from the original client-side `send()` call returning, since the broker's actual receipt and processing happens asynchronously relative to the client.
3. **Confirm callback fires**: some time after the send, the broker sends back an acknowledgment (or, rarely, a negative acknowledgment for an internal broker failure) for that specific message; `RabbitTemplate`'s registered confirm callback fires with the associated `CorrelationData`, letting the application match this asynchronous confirmation back to the specific business operation that triggered it.
4. **Routing attempted**: independently of confirmation, the broker attempts to route the message to a queue based on the exchange's bindings and the message's routing key.
5. **Return callback fires (only if unroutable)**: if no binding matches, and `mandatory=true` was set, the broker sends the message back to the publisher along with a reason, triggering the registered returns callback — this is a separate event from the confirm and may arrive independently of (though often shortly after) the confirm for the same message.
6. **Application reacts**: a confirmed-but-returned message (accepted by the broker, but unroutable) signals a configuration problem — a routing key that doesn't match any current binding — that the application can log, alert on, or handle via a compensating action, rather than the message simply vanishing without any trace.

```
convertAndSend(exchange, routingKey, payload, correlationData) [mandatory=true]
  -> broker receives message
       -> [async] confirm callback fires: ack=true (received) or ack=false (broker-side failure)
       -> routing attempted against bindings
            matches a binding -> delivered normally, no return fires
            no matching binding -> [async] returns callback fires: unroutable, reason given
```

## 7. Gotchas & takeaways

> **Gotcha:** publisher confirms and returns are both asynchronous and can arrive in an order that doesn't match the order messages were originally sent in, especially under concurrent publishing — correlation data (or an equivalent tracking mechanism) is essential for matching a confirm or return back to the correct originating operation; assuming confirms arrive in send order is a subtle and easy mistake to make.

- A confirm answers "did the broker receive this message," and a return answers "could the broker route this message anywhere" — they are independent, both-can-happen-separately signals, not two names for the same event.
- `mandatory=true` is required for returns to fire at all; without it, an unroutable message is simply dropped silently by default, exactly the silent-loss behavior described in card 0001.
- Enabling confirms and returns adds real overhead (extra broker round trips and bookkeeping) — reserve them for genuinely critical publish paths where delivery assurance matters, rather than blanket-enabling them for every message an application ever sends.
- Correlation data is the mechanism that makes confirms and returns actionable at the level of individual business operations rather than just generic, hard-to-attribute notifications — always attach it when confirms/returns matter enough to be worth enabling in the first place.
