---
card: spring-integration
gi: 58
slug: amqp-support
title: "AMQP support"
---

## 1. What it is

AMQP support (`Amqp.inboundGateway(...)`/`Amqp.outboundGateway(...)`, and their adapter variants, built on Spring AMQP/RabbitMQ) connects a flow to an AMQP broker — most commonly RabbitMQ. Unlike JMS's queue-or-topic destination model (card 0057), AMQP's routing model is built around *exchanges* and *bindings*: a producer publishes to an exchange with a routing key, and the exchange (based on its type — direct, topic, fanout, headers) decides which of possibly several bound queues actually receive a copy, decoupling the publisher entirely from needing to know which specific queues exist or which consumers are listening.

## 2. Why & when

You reach for AMQP support specifically when the integration point is a RabbitMQ (or another AMQP-compliant) broker, or when AMQP's flexible exchange-based routing model fits the use case better than JMS's simpler destination model:

- **You're integrating with an existing RabbitMQ-based messaging infrastructure** — RabbitMQ is an extremely common choice for microservices messaging, and AMQP support lets a Spring Integration flow participate in that infrastructure directly, publishing to and consuming from exchanges/queues.
- **A single published message needs to reach different sets of queues based on flexible routing rules**, not just a fixed queue name or blanket topic fan-out — a topic exchange, for instance, can route `"order.created.us"` to one set of bound queues and `"order.created.eu"` to a different set, based on wildcard pattern matching on the routing key, something JMS's simpler destination model doesn't directly provide.
- **You want the producer completely decoupled from which queues actually exist** — a producer publishes to an exchange without needing to know (or care) how many queues are bound to it, or whether any queues are bound at all; new consumers can bind new queues to an existing exchange later without any change to the producer.

## 3. Core concept

Think of an AMQP exchange like a postal sorting facility with a flexible routing rulebook, as opposed to JMS's direct "put it in this specific mailbox" model. A producer hands a package to the sorting facility (the exchange) along with a label (the routing key) — the facility itself, based on its configured routing rules (a direct exchange matches the label exactly; a topic exchange matches wildcard patterns; a fanout exchange ignores the label and sends to everyone), decides which of possibly many downstream mailboxes (queues) actually receive a copy. The sender never addresses a specific mailbox directly — they trust the sorting facility's rules to get it to the right place(s).

```java
@Bean
public IntegrationFlow amqpOutboundFlow(AmqpTemplate amqpTemplate) {
    return IntegrationFlow.from("orderEvents")
        .handle(Amqp.outboundAdapter(amqpTemplate)
            .exchangeName("orders.topic")
            .routingKeyExpression("headers['region'] + '.' + payload.status")) // e.g. "us.created"
        .get();
}

@Bean
public IntegrationFlow amqpInboundFlow(ConnectionFactory connectionFactory) {
    return IntegrationFlow.from(Amqp.inboundAdapter(connectionFactory, "us-order-events-queue"))
        .handle((Order order, headers) -> regionalOrderService.process(order))
        .get();
}
```

The outbound flow never specifies which queue receives the message — it publishes to the `orders.topic` exchange with a computed routing key, and whichever queues are bound to that exchange with a matching binding pattern receive it; the inbound flow simply consumes from whichever specific queue it's been configured to read from.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer publishes to an AMQP exchange with a routing key; the exchange's routing rules (direct, topic wildcard, or fanout) determine which of several bound queues actually receive a copy of the message">
  <rect x="20" y="70" width="110" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">producer</text>

  <line x1="130" y1="92" x2="190" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#amqp1)"/>
  <text x="160" y="78" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">routing key</text>

  <rect x="200" y="65" width="140" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="270" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">exchange</text>
  <text x="270" y="103" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">topic / direct / fanout</text>

  <line x1="340" y1="80" x2="410" y2="35" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#amqp2)"/>
  <line x1="340" y1="95" x2="410" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#amqp2)"/>
  <line x1="340" y1="110" x2="410" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>

  <rect x="420" y="15" width="120" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="37" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">queue: matched binding</text>

  <rect x="420" y="78" width="120" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="100" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">queue: matched binding</text>

  <rect x="420" y="140" width="120" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="480" y="162" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">queue: NOT bound (skipped)</text>

  <defs>
    <marker id="amqp1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="amqp2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The exchange's routing rules, not the producer, decide which bound queues actually receive each published message.

## 5. Runnable example

The scenario: an order-event system routing by region using a topic exchange's wildcard matching, simulated with in-memory routing rules standing in for a real RabbitMQ broker, starting with basic direct-exchange routing, then topic-exchange wildcard matching, and finally a fanout exchange broadcasting to every bound queue regardless of routing key.

### Level 1 — Basic

```java
// DirectExchangeDemo.java
// Simulates AMQP exchange routing with an in-memory registry standing in for a real RabbitMQ broker,
// since connecting to an actual broker requires external infrastructure.
import java.util.*;

public class DirectExchangeDemo {
    // a DIRECT exchange: routing key must match a binding EXACTLY
    static Map<String, List<List<String>>> directBindings = Map.of(
        "order.created", List.of(new ArrayList<>()),
        "order.cancelled", List.of(new ArrayList<>()));

    static Map<String, List<String>> queues = new HashMap<>();

    static void bind(String routingKey, String queueName) {
        queues.computeIfAbsent(queueName, k -> new ArrayList<>());
        directBindingsFor(routingKey).add(queueName);
    }
    static List<String> directBindingsFor(String routingKey) {
        return directBindings.computeIfAbsent(routingKey, k -> new ArrayList<>()).get(0) != null
            ? directBindings.get(routingKey).get(0) : List.of();
    }

    public static void main(String[] args) {
        Map<String, List<String>> bindingsToQueues = new HashMap<>();
        bindingsToQueues.put("order.created", new ArrayList<>(List.of("fulfillment-queue")));
        bindingsToQueues.put("order.cancelled", new ArrayList<>(List.of("refund-queue")));

        publish("order.created", "ORD-1", bindingsToQueues);
        publish("order.cancelled", "ORD-2", bindingsToQueues);
    }

    static void publish(String routingKey, String message, Map<String, List<String>> bindingsToQueues) {
        List<String> matchedQueues = bindingsToQueues.getOrDefault(routingKey, List.of());
        System.out.println("Published '" + message + "' with routing key '" + routingKey
            + "' -> delivered to EXACTLY matching queue(s): " + matchedQueues);
    }
}
```

How to run: `java DirectExchangeDemo.java`. Expected output: `Published 'ORD-1' with routing key 'order.created' -> delivered to EXACTLY matching queue(s): [fulfillment-queue]` then `Published 'ORD-2' with routing key 'order.cancelled' -> delivered to EXACTLY matching queue(s): [refund-queue]` — a direct exchange requires an exact routing-key-to-binding match; each published message went to exactly the queue(s) bound to its precise routing key.

### Level 2 — Intermediate

A topic exchange's wildcard matching — routing keys like `"order.created.us"` match binding patterns using `*` (exactly one segment) and `#` (zero or more segments), routing to different queues based on flexible pattern matching rather than an exact string match.

```java
// TopicExchangeWildcardDemo.java
import java.util.*;
import java.util.regex.*;

public class TopicExchangeWildcardDemo {
    // TOPIC exchange bindings, using AMQP-style wildcard patterns
    static Map<String, String> bindings = Map.of(
        "order.created.us", "us-fulfillment-queue",
        "order.created.*", "all-created-monitor-queue",   // matches ANY single segment after "order.created."
        "order.#", "audit-log-queue");                     // matches EVERYTHING starting with "order."

    static boolean matchesPattern(String pattern, String routingKey) {
        String regex = pattern
            .replace(".", "\\.")
            .replace("\\.#", "(\\..+)?")   // # matches zero or more segments
            .replace("*", "[^.]+");         // * matches exactly one segment
        return Pattern.matches(regex, routingKey);
    }

    static List<String> route(String routingKey) {
        List<String> matched = new ArrayList<>();
        for (var entry : bindings.entrySet()) {
            if (matchesPattern(entry.getKey(), routingKey)) matched.add(entry.getValue());
        }
        return matched;
    }

    public static void main(String[] args) {
        String routingKey = "order.created.us";
        List<String> matchedQueues = route(routingKey);
        System.out.println("Routing key '" + routingKey + "' matched bindings, delivered to: " + matchedQueues);
    }
}
```

How to run: `java TopicExchangeWildcardDemo.java`. Expected output: `Routing key 'order.created.us' matched bindings, delivered to: [us-fulfillment-queue, all-created-monitor-queue, audit-log-queue]` — a single published message with routing key `"order.created.us"` matched *three* different binding patterns simultaneously (an exact match, a single-wildcard match, and a multi-segment wildcard match), demonstrating a topic exchange's flexible, pattern-based routing.

### Level 3 — Advanced

A fanout exchange ignores the routing key entirely — every queue bound to it receives every published message, regardless of what routing key was used — contrasted directly against the direct exchange's exact-match behavior to make the full spectrum of AMQP exchange types (direct, topic, fanout) concrete.

```java
// FanoutExchangeDemo.java
import java.util.*;

public class FanoutExchangeDemo {
    static List<String> fanoutBoundQueues = List.of("email-service-queue", "sms-service-queue", "analytics-queue");

    static void publishToFanout(String message, String routingKey) {
        // a FANOUT exchange IGNORES the routing key entirely — EVERY bound queue gets a copy
        System.out.println("Published '" + message + "' (routing key '" + routingKey
            + "' is IGNORED by a fanout exchange)");
        for (String queue : fanoutBoundQueues) {
            System.out.println("  -> delivered to: " + queue);
        }
    }

    public static void main(String[] args) {
        // note: TWO different routing keys, but a fanout exchange treats them IDENTICALLY
        publishToFanout("order-shipped-notification", "irrelevant-key-1");
        System.out.println();
        publishToFanout("another-notification", "completely-different-key");
    }
}
```

How to run: `java FanoutExchangeDemo.java`. Expected output: both publish calls, despite using entirely different (and functionally irrelevant) routing keys, deliver to the exact same three queues — `email-service-queue`, `sms-service-queue`, `analytics-queue` — demonstrating that a fanout exchange's delivery behavior depends solely on which queues are bound to it, never on the routing key used.

## 6. Walkthrough

Tracing `TopicExchangeWildcardDemo` in execution order:

1. `route("order.created.us")` iterates over every configured binding pattern, checking each against the actual routing key via `matchesPattern`.
2. For the binding `"order.created.us"` (an exact string, with no wildcard characters), `matchesPattern` converts it into a regex with no special substitutions applied beyond escaping the dots — the regex effectively requires an identical string, and `"order.created.us"` matches itself exactly, so `us-fulfillment-queue` is added to the matched list.
3. For the binding `"order.created.*"`, the `*` is converted into the regex `[^.]+` (one or more non-dot characters, i.e., exactly one segment) — checking this against `"order.created.us"` succeeds, since `"us"` is exactly one segment following `"order.created."`, so `all-created-monitor-queue` is also added.
4. For the binding `"order.#"`, the `#` is converted into `(\..+)?` (an optional dot followed by anything) — checking this against `"order.created.us"` succeeds, since everything after `"order"` (`.created.us`) is matched by that optional group, so `audit-log-queue` is added as well.
5. All three bindings matched the same single routing key, so `route` returns a list containing all three queue names — a single publish operation is about to fan out to all three, purely because their binding patterns each happened to match this particular routing key.
6. This is fundamentally different from `DirectExchangeDemo`'s exact-match behavior (Level 1), where only a binding identical to the routing key would ever match — a topic exchange's wildcard patterns let one publish operation reach multiple, differently-scoped consumers (a region-specific queue, a broader "any creation" monitor, and a catch-all audit log) without the publisher needing to know about any of them individually.

```
routing key: "order.created.us"

binding "order.created.us" (exact)  -> MATCH -> us-fulfillment-queue
binding "order.created.*"  (1 seg)  -> MATCH -> all-created-monitor-queue
binding "order.#"          (any)    -> MATCH -> audit-log-queue

-> ALL THREE queues receive a copy of this one published message
```

## 7. Gotchas & takeaways

> Publishing to a non-existent exchange, or to an exchange with no queues currently bound to it, does not raise an error by default in AMQP — the message is simply dropped (unless the publisher explicitly enables mandatory-message handling to detect and react to this). This is a common source of "my message just vanished" confusion: unlike a JMS queue (card 0057), which itself durably holds the message, an AMQP exchange with no matching bound queue provides no storage or delivery guarantee on its own — durability lives in the *queues*, not the exchange, so a publish with no matching binding truly goes nowhere.

- AMQP support connects a flow to a RabbitMQ (or other AMQP) broker, using exchanges (direct, topic, fanout, headers) and bindings for flexible, decoupled routing, distinct from JMS's simpler queue/topic destination model (card 0057).
- A direct exchange requires an exact routing-key-to-binding match; a topic exchange supports wildcard pattern matching (`*` for one segment, `#` for zero or more); a fanout exchange ignores the routing key entirely, delivering to every bound queue.
- Producers publish to an exchange without needing to know which (or how many) queues are bound to it — new consumers can bind new queues later with zero change to the producer, a genuine decoupling advantage over destination-based models.
- Durability and delivery guarantees live in the *queues*, not the exchange itself — publishing to an exchange with no matching bound queue silently drops the message by default, with no built-in warning unless mandatory-message handling is explicitly configured.
- Choosing the right exchange type is a routing-design decision with real consequences: a fanout exchange for broadcast-to-everyone scenarios, a topic exchange for flexible pattern-based routing, a direct exchange for simple exact-match dispatch.
