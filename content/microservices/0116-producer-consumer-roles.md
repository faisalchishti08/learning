---
card: microservices
gi: 116
slug: producer-consumer-roles
title: "Producer / consumer roles"
---

## 1. What it is

Producer and consumer are the two roles any service plays around a [message channel](0115-message-channels.md): a producer creates and sends messages onto a channel without knowing who, if anyone, reads them; a consumer reads and processes messages from a channel without knowing who sent them. A single service is very often both roles at once — a consumer of one channel and a producer onto another — which is how event-driven chains form.

## 2. Why & when

Naming these roles explicitly matters because it clarifies what each side is actually responsible for and, just as importantly, *not* responsible for. A producer's job ends the moment the message is successfully handed to the channel; it has no responsibility for how, when, or whether it is processed. A consumer's job is to read messages, process them, and (depending on the [acknowledgement mode](0117-message-acknowledgement-modes.md)) confirm that processing — it has no responsibility for how the message was created or by whom.

Think in producer/consumer terms whenever designing an event-driven interaction: identifying "who produces this event" and "who consumes it" up front avoids the common mistake of a producer reaching too far into consumer logic (coupling them back together) or a consumer assuming things about the producer's internal state that the channel contract never actually promised.

## 3. Core concept

A service acting as producer only needs a reference to the channel and the message shape; a service acting as consumer only needs a reference to the channel and a handler. Neither role requires any reference to the other.

```java
// producer role: order-service only knows the channel, never the consumers
channel.send("order-events", new OrderPlaced(orderId, total));

// consumer role: email-service only knows the channel, never the producer
channel.subscribe("order-events", event -> sendConfirmation(event));

// a service can hold BOTH roles: consuming one channel, producing to another
channel.subscribe("order-events", event -> channel.send("shipping-jobs", toShippingJob(event)));
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service acts as producer onto order-events; shipping service consumes order-events and acts as producer onto shipping-jobs, chaining the two roles together">
  <rect x="20" y="70" width="130" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Service</text>
  <text x="85" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(producer)</text>

  <rect x="230" y="70" width="140" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-events</text>

  <rect x="450" y="70" width="150" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="93" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Shipping Service</text>
  <text x="525" y="107" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(consumer &amp; producer)</text>

  <line x1="150" y1="95" x2="228" y2="95" stroke="#8b949e" marker-end="url(#arr6)"/>
  <line x1="370" y1="95" x2="448" y2="95" stroke="#8b949e" marker-end="url(#arr6)"/>

  <rect x="450" y="150" width="150" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="169" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">shipping-jobs</text>
  <line x1="525" y1="120" x2="525" y2="148" stroke="#8b949e" marker-end="url(#arr6)"/>

  <defs>
    <marker id="arr6" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Shipping Service plays consumer on the left channel and producer on the right one — the same service, two distinct roles.

## 5. Runnable example

Scenario: an order-to-shipping event chain that starts with a single producer and a single consumer as separate, clearly bounded roles, then shows one service holding both roles at once, and finally extends the chain across three hops to show how roles compose into a pipeline.

### Level 1 — Basic

```java
// File: SingleRole.java -- one producer, one consumer, roles kept clean and separate.
import java.util.*;
import java.util.function.*;

public class SingleRole {
    static class Channel {
        private final List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); } // consumer role uses this
        void send(String message) { subscribers.forEach(s -> s.accept(message)); } // producer role uses this
    }

    public static void main(String[] args) {
        Channel orderEvents = new Channel();

        // consumer role: only knows the channel and its own handler
        orderEvents.subscribe(msg -> System.out.println("[email-service, consumer] handling: " + msg));

        // producer role: only knows the channel and the message, nothing about consumers
        orderEvents.send("OrderPlaced:42");
    }
}
```

**How to run:** `javac SingleRole.java && java SingleRole` (JDK 17+).

`order-service` never references `email-service` and `email-service` never references `order-service` — each only knows the shared `Channel`, the essence of the producer/consumer separation.

### Level 2 — Intermediate

```java
// File: DualRole.java -- shipping-service acts as BOTH consumer (of order-events)
// and producer (onto shipping-jobs), the same service holding two roles.
import java.util.*;
import java.util.function.*;

public class DualRole {
    static class Channel {
        private final List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void send(String message) { subscribers.forEach(s -> s.accept(message)); }
    }

    public static void main(String[] args) {
        Channel orderEvents = new Channel();
        Channel shippingJobs = new Channel();

        shippingJobs.subscribe(msg -> System.out.println("  [shipping-worker, consumer] packing: " + msg));

        // shipping-service: CONSUMES order-events, and in the same handler, PRODUCES onto shipping-jobs
        orderEvents.subscribe(orderMsg -> {
            System.out.println("[shipping-service, consumer role] received: " + orderMsg);
            String job = "ShipOrder:" + orderMsg.split(":")[1];
            System.out.println("[shipping-service, producer role] sending: " + job);
            shippingJobs.send(job);
        });

        orderEvents.send("OrderPlaced:42");
    }
}
```

**How to run:** `javac DualRole.java && java DualRole` (JDK 17+).

Expected output:
```
[shipping-service, consumer role] received: OrderPlaced:42
[shipping-service, producer role] sending: ShipOrder:42
  [shipping-worker, consumer] packing: ShipOrder:42
```

The `shipping-service` handler is one piece of code, but the two `System.out.println` labels mark the moment it switches from acting as a consumer of `order-events` to acting as a producer onto `shipping-jobs`.

### Level 3 — Advanced

```java
// File: ThreeHopChain.java -- a longer chain: each hop's consumer role feeds
// its own producer role into the next channel, forming a full event pipeline.
import java.util.*;
import java.util.function.*;

public class ThreeHopChain {
    static class Channel {
        final String name;
        private final List<Consumer<String>> subscribers = new ArrayList<>();
        Channel(String name) { this.name = name; }
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void send(String message) {
            System.out.println("-> [" + name + "] " + message);
            subscribers.forEach(s -> s.accept(message));
        }
    }

    public static void main(String[] args) {
        Channel orderEvents = new Channel("order-events");
        Channel shippingJobs = new Channel("shipping-jobs");
        Channel notificationEvents = new Channel("notification-events");

        // hop 1: shipping-service is consumer of order-events, producer onto shipping-jobs
        orderEvents.subscribe(msg -> shippingJobs.send("ShipOrder:" + msg.split(":")[1]));

        // hop 2: notification-service is consumer of shipping-jobs, producer onto notification-events
        shippingJobs.subscribe(msg -> notificationEvents.send("NotifyCustomer:" + msg.split(":")[1]));

        // hop 3: sms-service is ONLY a consumer -- the chain terminates here
        notificationEvents.subscribe(msg -> System.out.println("   [sms-service, consumer only] texting customer: " + msg));

        orderEvents.send("OrderPlaced:42"); // one event kicks off the entire chain
    }
}
```

**How to run:** `javac ThreeHopChain.java && java ThreeHopChain` (JDK 17+).

Expected output:
```
-> [order-events] OrderPlaced:42
-> [shipping-jobs] ShipOrder:42
-> [notification-events] NotifyCustomer:42
   [sms-service, consumer only] texting customer: NotifyCustomer:42
```

## 6. Walkthrough

1. **Level 1** — `orderEvents.subscribe(...)` registers `email-service`'s handler purely as a consumer role; `orderEvents.send(...)` invoked from `main` purely exercises the producer role, and the two never reference each other directly, only the shared `Channel`.
2. **Level 2, the dual-role handler** — the lambda passed to `orderEvents.subscribe` is registered as a consumer of `order-events`, but its *body* calls `shippingJobs.send(job)`, which is the producer role applied to a second, different channel — the same block of code is genuinely playing both roles, just at two different points in its execution.
3. **Level 2, tracing the call** — `orderEvents.send("OrderPlaced:42")` triggers the handler, which first prints its consumer-role log line, builds a derived `job` string, prints its producer-role log line, then calls `shippingJobs.send(job)`, which in turn triggers `shipping-worker`'s separately registered consumer handler.
4. **Level 3, three independent hops** — each `Channel` now logs every send with its own name, making the full chain visible: `orderEvents.send` triggers the shipping-service handler (consumer of `order-events`, producer onto `shipping-jobs`), which triggers the notification-service handler (consumer of `shipping-jobs`, producer onto `notification-events`), which finally triggers `sms-service`'s handler, a pure consumer with no further production step.
5. **Level 3, one call ripples through three channels** — `main` makes exactly one call, `orderEvents.send("OrderPlaced:42")`, and the printed `->` lines show the message propagating through all three channels in sequence, purely as a consequence of each intermediate service's handler both consuming its inbound channel and producing onto its outbound one.
6. **Why role separation matters here** — each handler only references the channel it consumes from and the channel it produces to; `shipping-service`'s code has zero references to `sms-service` two hops downstream, meaning a new consumer could be added to `notification-events` (or `shippingJobs`) without touching any of the existing services — the chain is extensible because each role only commits to its immediately adjacent channel.

## 7. Gotchas & takeaways

> **Gotcha:** a service quietly acting as both consumer and producer in one long chain of handlers is easy to build but easy to lose track of operationally — a failure two or three hops downstream can be hard to trace back to its origin without correlation IDs or distributed tracing carried through every hop's message payload.

- Producer and consumer are roles a service plays with respect to a specific channel, not fixed identities — the same service is routinely a consumer of one channel and a producer onto another.
- A producer's responsibility ends at successful handoff to the channel; a consumer's responsibility is reading and processing, optionally acknowledging, what arrives on the channel it is subscribed to.
- Chains of single-purpose consumer/producer hops are how complex event-driven pipelines are built out of small, independently deployable services, each aware only of its own inbound and outbound channels.
- Because roles are decoupled through the channel, new consumers or new hops can be added to a chain without modifying the services already in it.
- Long chains of hops make debugging harder without deliberate tracing — the flexibility of composable roles trades off against the difficulty of following a message's full journey after the fact.
