---
card: spring-integration
gi: 23
slug: router-payload-header-recipient-list-exception-type
title: "Router (payload/header/recipient-list/exception-type)"
---

## 1. What it is

`@Router` is the endpoint archetype (from card 0019's taxonomy) whose job is choosing which channel (or channels) a message should go to next, based on the message's content — as distinct from `Filter` (card 0022), which only ever decides pass-or-drop against a single destination. Spring Integration offers several router flavors for different kinds of routing decisions: a payload-type router (route by the payload's Java type), a header-value router (route by a header's value), a recipient-list router (send the *same* message to multiple channels at once), and an exception-type router (route based on what kind of exception occurred, typically used on an error channel).

## 2. Why & when

You reach for a specific `Router` flavor depending on exactly what the routing decision is based on:

- **Different payload types need entirely different processing paths** — a `String` payload needs parsing, an already-parsed `Order` doesn't — a payload-type router dispatches purely on `payload.getClass()`, with no custom condition logic needed.
- **A header value (not the payload) determines the path** — a `priority` or `region` header dictating which downstream queue handles a message — a header-value router reads that header and maps its value to a channel name.
- **The same message genuinely needs to go to more than one place** — an order needing both fulfillment processing and an audit log entry — a recipient-list router broadcasts one message to several channels, rather than picking exactly one.
- **Different exception types need different recovery/notification handling** on an error-handling channel — a `TimeoutException` retried, a `ValidationException` sent to a dead-letter channel — an exception-type router dispatches based on the caught exception's type.

## 3. Core concept

Think of a `Router` like a mail sorting facility's different sorting rules: one line sorts packages by declared type (books vs. electronics — payload-type routing), another sorts by a shipping label's destination zone (header-value routing), a special line photocopies a document and sends copies down multiple chutes at once (recipient-list routing), and a damage-report line sorts by what specifically went wrong with a package (exception-type routing). Each is still fundamentally "look at something about this item, decide where it goes" — only what's being looked at, and how many destinations result, differs.

```java
// Header-value router: routes based on a "region" header's value
@Router(inputChannel = "orders")
public String routeByRegion(Message<Order> message) {
    String region = (String) message.getHeaders().get("region");
    return switch (region) {
        case "US" -> "usOrders";
        case "EU" -> "euOrders";
        default -> "defaultOrders";
    };
}
```

The method returns the *name* of the channel to send to (or a `Collection<String>` of names, for multi-destination routing); the framework resolves that name to an actual channel and forwards the original message unchanged.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Router inspects a message and returns a channel name (or names), dispatching the unchanged message to one or more resolved destination channels">
  <rect x="20" y="90" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">input channel</text>

  <line x1="130" y1="112" x2="190" y2="112" stroke="#6db33f" stroke-width="2" marker-end="url(#r1)"/>

  <rect x="200" y="80" width="140" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="270" y="103" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Router</text>
  <text x="270" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">returns channel name(s)</text>

  <line x1="340" y1="95" x2="410" y2="30" stroke="#6db33f" stroke-width="1.5" marker-end="url(#r2)"/>
  <line x1="340" y1="112" x2="410" y2="112" stroke="#6db33f" stroke-width="1.5" marker-end="url(#r2)"/>
  <line x1="340" y1="130" x2="410" y2="190" stroke="#6db33f" stroke-width="1.5" marker-end="url(#r2)"/>

  <rect x="420" y="10" width="130" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="485" y="32" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">usOrders</text>

  <rect x="420" y="95" width="130" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="485" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">euOrders</text>

  <rect x="420" y="175" width="130" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="485" y="197" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">defaultOrders</text>

  <defs>
    <marker id="r1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="r2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

A router resolves one (or several, for recipient-list) destination channel names per message, based on whatever aspect of the message is relevant to that router flavor.

## 5. Runnable example

The scenario: an order-routing pipeline needing region-based dispatch, starting with a basic header-value router, then a payload-type router alongside it, and finally a recipient-list router broadcasting to multiple destinations plus an exception-type router on an error path.

### Level 1 — Basic

```java
// HeaderValueRouterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.Map;

public class HeaderValueRouterDemo {
    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel usOrders = new DirectChannel();
        DirectChannel euOrders = new DirectChannel();
        DirectChannel defaultOrders = new DirectChannel();

        usOrders.subscribe(m -> System.out.println("US handler received: " + m.getPayload()));
        euOrders.subscribe(m -> System.out.println("EU handler received: " + m.getPayload()));
        defaultOrders.subscribe(m -> System.out.println("Default handler received: " + m.getPayload()));

        Map<String, DirectChannel> channelsByRegion = Map.of("US", usOrders, "EU", euOrders);

        // what @Router routing by a "region" header does for you:
        orders.subscribe(m -> {
            String region = (String) m.getHeaders().get("region");
            DirectChannel target = channelsByRegion.getOrDefault(region, defaultOrders);
            target.send(m); // forwarded UNCHANGED
        });

        orders.send(MessageBuilder.withPayload("order-1").setHeader("region", "US").build());
        orders.send(MessageBuilder.withPayload("order-2").setHeader("region", "JP").build());
    }
}
```

How to run: `java HeaderValueRouterDemo.java`. Expected output: `US handler received: order-1` then `Default handler received: order-2` — the router read each message's `region` header and dispatched to the matching channel, falling back to `defaultOrders` for an unmapped value.

### Level 2 — Intermediate

A payload-type router dispatches purely on the Java type of the payload, useful when a shared input channel receives genuinely different kinds of messages that each need type-specific handling before any other routing logic applies.

```java
// PayloadTypeRouterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class PayloadTypeRouterDemo {
    record Order(String id) {}
    record CancellationRequest(String orderId) {}

    public static void main(String[] args) {
        DirectChannel events = new DirectChannel();
        DirectChannel orderChannel = new DirectChannel();
        DirectChannel cancellationChannel = new DirectChannel();

        orderChannel.subscribe(m -> System.out.println("Order processor received: " + m.getPayload()));
        cancellationChannel.subscribe(m -> System.out.println("Cancellation processor received: " + m.getPayload()));

        // what @Router routing by payload TYPE does for you:
        events.subscribe(m -> {
            Object payload = m.getPayload();
            if (payload instanceof Order) {
                orderChannel.send(m);
            } else if (payload instanceof CancellationRequest) {
                cancellationChannel.send(m);
            }
        });

        events.send(MessageBuilder.withPayload(new Order("ORD-1")).build());
        events.send(MessageBuilder.withPayload(new CancellationRequest("ORD-2")).build());
    }
}
```

How to run: `java PayloadTypeRouterDemo.java`. Expected output: `Order processor received: Order[id=ORD-1]` then `Cancellation processor received: CancellationRequest[orderId=ORD-2]` — the same input channel carried two structurally different payload types, each dispatched to its own type-specific handler purely by `instanceof` checks.

### Level 3 — Advanced

A recipient-list router broadcasts one message, unchanged, to several channels at once (as opposed to choosing exactly one), and an exception-type router — typically wired to an error channel — dispatches recovery logic based on what kind of exception actually occurred, both shown together as they'd realistically coexist in one flow.

```java
// RecipientListAndExceptionRouterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.List;
import java.util.concurrent.TimeoutException;

public class RecipientListAndExceptionRouterDemo {
    record Order(String id) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel fulfillment = new DirectChannel();
        DirectChannel auditLog = new DirectChannel();
        DirectChannel errorChannel = new DirectChannel();
        DirectChannel retryChannel = new DirectChannel();
        DirectChannel deadLetterChannel = new DirectChannel();

        fulfillment.subscribe(m -> System.out.println("Fulfillment received: " + m.getPayload()));
        auditLog.subscribe(m -> System.out.println("Audit log received: " + m.getPayload()));
        retryChannel.subscribe(m -> System.out.println("RETRY scheduled for: " + m.getPayload()));
        deadLetterChannel.subscribe(m -> System.out.println("DEAD-LETTERED: " + m.getPayload()));

        // RECIPIENT-LIST ROUTER: same message to BOTH fulfillment and auditLog
        List<DirectChannel> recipients = List.of(fulfillment, auditLog);
        orders.subscribe(m -> recipients.forEach(ch -> ch.send(m)));

        // EXCEPTION-TYPE ROUTER: dispatch based on caught exception's type
        errorChannel.subscribe(m -> {
            Throwable cause = (Throwable) m.getPayload();
            if (cause instanceof TimeoutException) {
                retryChannel.send(MessageBuilder.withPayload(cause.getMessage()).build());
            } else {
                deadLetterChannel.send(MessageBuilder.withPayload(cause.getMessage()).build());
            }
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-1")).build());
        errorChannel.send(MessageBuilder.withPayload(new TimeoutException("downstream timed out")).build());
        errorChannel.send(MessageBuilder.withPayload(new IllegalStateException("unrecoverable state")).build());
    }
}
```

How to run: `java RecipientListAndExceptionRouterDemo.java`. Expected output: `Fulfillment received: Order[id=ORD-1]` and `Audit log received: Order[id=ORD-1]` (the same order reaching both, from the recipient-list router), then `RETRY scheduled for: downstream timed out` (a `TimeoutException` routed to retry) and `DEAD-LETTERED: unrecoverable state` (an `IllegalStateException` routed to dead-letter) — demonstrating both router flavors operating in the same program.

## 6. Walkthrough

Tracing the recipient-list portion of `RecipientListAndExceptionRouterDemo` in execution order:

1. `orders.send(...)` for `Order[id=ORD-1]` triggers the recipient-list router's subscriber.
2. Unlike every other router flavor covered here (which pick exactly one destination), the recipient-list router iterates over a fixed list of channels — `fulfillment` and `auditLog` — and sends the *same* message instance to each in turn.
3. `fulfillment.send(m)` triggers its subscriber immediately (since these are `DirectChannel`s, dispatch is synchronous), printing confirmation that the fulfillment path received the order.
4. `auditLog.send(m)` then triggers its own subscriber, printing confirmation that the audit path also received the same order — both received the identical message, not two separately transformed copies.
5. Separately, `errorChannel.send(...)` for a `TimeoutException` triggers the exception-type router's subscriber, which checks `cause instanceof TimeoutException` — true — and forwards to `retryChannel`, printing that a retry was scheduled.
6. `errorChannel.send(...)` for an `IllegalStateException` hits the same router logic, but the `instanceof TimeoutException` check fails, falling through to the `else` branch that routes to `deadLetterChannel` instead — same router, same input channel, different destination purely based on the exception's runtime type.

```
RECIPIENT-LIST:  orders --[Router: broadcast]--> fulfillment
                                              \--> auditLog
                     (BOTH receive the SAME message)

EXCEPTION-TYPE:  errorChannel --[Router: by exception type]--> TimeoutException -> retryChannel
                                                            \--> (anything else) -> deadLetterChannel
```

## 7. Gotchas & takeaways

> A recipient-list router sending the *same* `Message` instance to multiple channels means any endpoint that mutates message state (rather than treating messages as immutable) risks one recipient's processing affecting another's — Spring Integration messages are designed to be treated as immutable precisely to avoid this, but a handler that reaches into a mutable payload object and changes it in place can still cause cross-recipient interference. Treat payloads as read-only within any handler reachable from a recipient-list router.

- `@Router` selects a destination channel (or several, for recipient-list) based on message content, returning the resolved channel name(s) rather than transforming the message.
- Payload-type routers dispatch on the payload's Java type; header-value routers dispatch on a specific header's value; recipient-list routers broadcast one message to multiple channels; exception-type routers dispatch based on a caught exception's type, typically on an error-handling path.
- The message itself is forwarded unchanged to whichever channel(s) a router resolves — routing is purely a destination decision, never a shape change (that's `Transformer`, card 0021) and never a pass/drop decision against one destination (that's `Filter`, card 0022).
- Recipient-list routing sends the identical message instance to every recipient — treat payloads as immutable to avoid one recipient's handling interfering with another's.
- Exception-type routing is the standard way to give different failure categories different recovery strategies (retry vs. dead-letter vs. alert) on a shared error channel, instead of one large conditional inside a single error handler.
