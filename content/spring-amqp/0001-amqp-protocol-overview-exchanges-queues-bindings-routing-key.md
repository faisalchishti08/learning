---
card: spring-amqp
gi: 1
slug: amqp-protocol-overview-exchanges-queues-bindings-routing-key
title: "AMQP protocol overview (exchanges, queues, bindings, routing keys)"
---

## 1. What it is

AMQP (Advanced Message Queuing Protocol) is a wire-level messaging protocol built around four core concepts: a **producer** publishes a message to an **exchange**, never directly to a queue; the exchange decides which **queue(s)** to deliver it to based on **bindings** (rules connecting an exchange to a queue) and a **routing key** (a label attached to the message that bindings match against); a **consumer** then reads from the queue. Spring AMQP is the Spring project that wraps this protocol — most commonly implemented by RabbitMQ — in familiar Spring abstractions like templates and listener containers.

## 2. Why & when

You need to understand this model before touching Spring AMQP's APIs, because every configuration decision maps directly onto these four concepts:

- **Producers and consumers should be decoupled from each other** — a producer publishes to an exchange with no idea which queues (if any) exist downstream; this indirection is what lets new consumers be added later without ever touching producer code.
- **Different delivery patterns need different exchange behavior** — broadcasting to every interested consumer, routing by category, or routing by exact key are all expressed through exchange type and binding configuration rather than application code (covered in depth in card 0002).
- **A message needs to reach the right queue(s) among several** — the routing key and bindings together are the addressing mechanism that determines this, similar in spirit to a mail sorting facility routing letters by postal code to the correct delivery route.

## 3. Core concept

Think of a post office: you don't hand a letter directly to the recipient's mailbox (a queue) — you hand it to a postal worker at the counter (the exchange), who reads the address you wrote on it (the routing key) and, using the postal service's internal routing rules (bindings), decides which delivery routes (queues) should receive it. The mailbox owner (the consumer) simply checks their own mailbox and has no idea how the letter got routed there, or whether other mailboxes received a copy too.

```java
// Publishing: the producer only ever talks to an exchange, with a routing key attached.
rabbitTemplate.convertAndSend("order.exchange", "order.created.us", orderPayload);

// Somewhere in configuration (not the producer's concern), a binding connects that
// exchange to a queue for any routing key matching "order.created.*":
new Binding("orderProcessingQueue", Binding.DestinationType.QUEUE,
    "order.exchange", "order.created.*", null);
```

The producer never mentions `orderProcessingQueue` by name — it only knows the exchange and the routing key; the binding is what actually connects the two.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer publishes a message with a routing key to an exchange; bindings connect the exchange to one or more queues based on that routing key; consumers read from queues, never directly from the exchange" >
  <rect x="20" y="70" width="120" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Producer</text>

  <line x1="140" y1="92" x2="220" y2="92" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a9)"/>
  <text x="180" y="82" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">routing key</text>

  <rect x="220" y="70" width="120" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="280" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Exchange</text>

  <line x1="340" y1="85" x2="420" y2="45" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a9)"/>
  <text x="380" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">binding matches</text>
  <line x1="340" y1="100" x2="420" y2="140" stroke="#8b949e" stroke-width="1.2"/>
  <text x="380" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">binding doesn't match</text>

  <rect x="420" y="20" width="130" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Queue A (matched)</text>

  <line x1="550" y1="42" x2="600" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a9)"/>
  <text x="620" y="42" fill="#e6edf3" font-size="8" font-family="sans-serif">Consumer</text>

  <defs><marker id="a9" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
</svg>

The exchange is the sole decision point; producers and consumers never interact directly.

## 5. Runnable example

The scenario: routing order events to the correct queue based on a routing key, simulated with a plain in-memory model of exchange/binding/queue matching (no real RabbitMQ broker needed to demonstrate the routing-key matching logic itself), starting with a single exact-match binding, then adding multiple bindings competing for the same message, then adding wildcard-style matching to show how one binding can serve many related routing keys at once.

### Level 1 — Basic

```java
// AmqpModelDemo.java
import java.util.*;

public class AmqpModelDemo {
    record Binding(String queueName, String routingKeyPattern) {}

    // Stand-in for an exchange's routing decision: exact routing-key match only, for now.
    static List<String> route(String routingKey, List<Binding> bindings) {
        List<String> matchedQueues = new ArrayList<>();
        for (Binding b : bindings) {
            if (b.routingKeyPattern().equals(routingKey)) matchedQueues.add(b.queueName());
        }
        return matchedQueues;
    }

    public static void main(String[] args) {
        List<Binding> bindings = List.of(new Binding("orderProcessingQueue", "order.created"));
        System.out.println("Routed to: " + route("order.created", bindings));
    }
}
```

How to run: `java AmqpModelDemo.java`. Expected output: `Routed to: [orderProcessingQueue]` — a message with a matching routing key reaches the bound queue.

### Level 2 — Intermediate

```java
// AmqpModelDemo.java
import java.util.*;

public class AmqpModelDemo {
    record Binding(String queueName, String routingKeyPattern) {}

    static List<String> route(String routingKey, List<Binding> bindings) {
        List<String> matchedQueues = new ArrayList<>();
        for (Binding b : bindings) {
            if (b.routingKeyPattern().equals(routingKey)) matchedQueues.add(b.queueName());
        }
        return matchedQueues;
    }

    public static void main(String[] args) {
        // Real-world concern: multiple queues can be bound to the same exchange with the same
        // routing key -- both receive a copy, since bindings aren't exclusive.
        List<Binding> bindings = List.of(
            new Binding("orderProcessingQueue", "order.created"),
            new Binding("auditLogQueue", "order.created"),
            new Binding("shippingQueue", "order.shipped"));

        System.out.println("Routing 'order.created': " + route("order.created", bindings));
        System.out.println("Routing 'order.shipped': " + route("order.shipped", bindings));
        System.out.println("Routing 'order.cancelled' (no binding): " + route("order.cancelled", bindings));
    }
}
```

How to run: `java AmqpModelDemo.java`. Expected output: `Routing 'order.created': [orderProcessingQueue, auditLogQueue]` — both queues receive a copy of the same message; `Routing 'order.shipped': [shippingQueue]`; and `Routing 'order.cancelled' (no binding): []` — a routing key with no matching binding simply goes nowhere, silently, unless the exchange type or configuration says otherwise.

### Level 3 — Advanced

```java
// AmqpModelDemo.java
import java.util.*;

public class AmqpModelDemo {
    record Binding(String queueName, String routingKeyPattern) {}

    // Production concern: real bindings (on a topic exchange) support wildcard patterns --
    // "*" matches exactly one word, "#" matches zero or more words, dot-separated. Modeling a
    // simplified version of that matching here to show why one binding can serve many keys.
    static boolean matches(String pattern, String routingKey) {
        String[] patternParts = pattern.split("\\.");
        String[] keyParts = routingKey.split("\\.");
        int pi = 0, ki = 0;
        while (pi < patternParts.length && ki < keyParts.length) {
            if (patternParts[pi].equals("#")) return true; // matches everything remaining
            if (patternParts[pi].equals("*") || patternParts[pi].equals(keyParts[ki])) {
                pi++; ki++;
            } else {
                return false;
            }
        }
        return pi == patternParts.length && ki == keyParts.length;
    }

    static List<String> route(String routingKey, List<Binding> bindings) {
        List<String> matchedQueues = new ArrayList<>();
        for (Binding b : bindings) {
            if (matches(b.routingKeyPattern(), routingKey)) matchedQueues.add(b.queueName());
        }
        return matchedQueues;
    }

    public static void main(String[] args) {
        List<Binding> bindings = List.of(
            new Binding("orderProcessingQueue", "order.created.*"), // any single region suffix
            new Binding("allOrderEventsQueue", "order.#"));         // every order event, any depth

        System.out.println("Routing 'order.created.us': " + route("order.created.us", bindings));
        System.out.println("Routing 'order.shipped.eu.express': " + route("order.shipped.eu.express", bindings));
    }
}
```

How to run: `java AmqpModelDemo.java`. Expected output: `Routing 'order.created.us': [orderProcessingQueue, allOrderEventsQueue]` (both bindings match); `Routing 'order.shipped.eu.express': [allOrderEventsQueue]` (only the `#` wildcard, matching any depth, catches this deeper key — `order.created.*` requires exactly one segment after `order.created` and doesn't apply here at all) — demonstrating how wildcard bindings let a small number of binding rules cover a large, evolving set of routing keys.

## 6. Walkthrough

Trace a single message from publish to consumption.

1. **Publish**: a producer calls something equivalent to `channel.basicPublish(exchangeName, routingKey, properties, body)`, specifying only the exchange and routing key — never a queue name.
2. **Exchange receives**: the exchange (a named entity inside the broker) receives the message and consults its configured bindings — the set of rules connecting it to one or more queues, each with a routing-key pattern to match against.
3. **Binding evaluation**: for each binding, the broker checks whether the message's routing key matches that binding's pattern — an exact string match, a wildcard pattern (on a topic exchange), or unconditionally (on a fanout exchange, covered in card 0002) depending on exchange type.
4. **Delivery to matched queues**: the message is copied into every queue whose binding matched; if no binding matches, the message is dropped (unless an alternate-exchange or dead-letter configuration is set up to catch it — a return path not covered by the basic model itself).
5. **Consumption**: a consumer subscribed to a queue reads messages from it independently of how they arrived — the consumer has no visibility into which exchange, routing key, or binding caused the message to land there.
6. **Multiple queues, one message**: if several bindings match the same routing key (as with `orderProcessingQueue` and `auditLogQueue` above), each matching queue receives its own independent copy, and each queue's consumer(s) process it entirely independently of the others.

```
producer.publish(exchange="order.exchange", routingKey="order.created.us", body=...)
  -> exchange evaluates bindings
       binding("orderProcessingQueue", "order.created.*") -> matches -> copy delivered
       binding("allOrderEventsQueue", "order.#")           -> matches -> copy delivered
  -> each queue holds its own copy, consumed independently
```

## 7. Gotchas & takeaways

> **Gotcha:** a message published with a routing key that matches no binding on its exchange is simply dropped by default, with no error raised to the producer — this silent-drop behavior (unless mandatory publishing with a returns callback is configured) is a common source of "I published it, but nothing received it" confusion for anyone new to AMQP's routing model.

- Producers depend only on an exchange name and a routing key convention — never on specific queue names — which is precisely what allows new consumers (new queues, new bindings) to be added later without any producer-side changes.
- The routing key is just a string the producer attaches; its structure (dot-separated segments, in the common convention) only has semantic meaning because bindings are written to pattern-match against that convention — the protocol itself doesn't enforce any particular format.
- Multiple bindings matching the same routing key is normal and intentional — it's how one event can simultaneously feed a primary processing queue and a secondary audit or analytics queue without the producer needing to know both exist.
- Understanding this four-part model (exchange, queue, binding, routing key) is the foundation for everything else in Spring AMQP — the templates, listener containers, and declaration APIs covered in later cards are all just Spring's ergonomic wrapper around configuring and using these same four concepts.
