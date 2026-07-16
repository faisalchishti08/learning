---
card: spring-amqp
gi: 2
slug: exchange-types-direct-topic-fanout-headers
title: "Exchange types (direct, topic, fanout, headers)"
---

## 1. What it is

AMQP exchanges come in four standard types, each implementing a different binding-matching rule: a **direct** exchange matches a routing key exactly against each binding's key; a **topic** exchange matches a routing key against wildcard patterns (`*` for one segment, `#` for zero or more); a **fanout** exchange ignores the routing key entirely and delivers to every bound queue unconditionally; a **headers** exchange matches on message header values instead of the routing key at all. Choosing the right exchange type is choosing the right matching algorithm for how messages should reach queues.

## 2. Why & when

You pick an exchange type based on what determines whether a queue should receive a given message:

- **Direct**, when routing is based on one exact category and every consumer needs exactly that category — a specific queue per order status, for instance, where `"order.shipped"` should go to exactly the shipping-notifications queue and nowhere else.
- **Topic**, when routing needs hierarchical, wildcard-based flexibility — one queue wanting "all order events for the US region" (`order.*.us`) while another wants "every order event regardless of region" (`order.#`), without the producer needing to know about either subscriber's specific interest.
- **Fanout**, when every bound queue should get a copy of every message regardless of any routing key at all — broadcasting a cache-invalidation event or a configuration-change notification to every interested service simultaneously.
- **Headers**, when the routing decision depends on multiple independent criteria that don't fit naturally into a single dot-separated routing-key string — matching on a combination of header values like `{"region": "us", "priority": "high"}` where routing key alone would be awkward to express.

## 3. Core concept

Think of these four exchange types as four different sorting rules a mail-sorting facility could use. Direct is like sorting strictly by exact zip code — a letter goes to precisely the route matching its zip, no more, no less. Topic is like sorting by a hierarchical postal code with wildcards allowed — "anything in this state" or "anything anywhere in this specific city, any street." Fanout is like a company-wide memo stapled to every single delivery route regardless of address — everyone gets a copy no matter what. Headers is like sorting by a checklist of independent attributes stamped on the envelope (fragile, overnight, signature-required) rather than by any single address field at all.

```java
// Direct: exact match only
new DirectExchange("order.status.exchange");
new Binding("shippingQueue", QUEUE, "order.status.exchange", "order.shipped", null);

// Topic: wildcard matching
new TopicExchange("order.events.exchange");
new Binding("usOrdersQueue", QUEUE, "order.events.exchange", "order.*.us", null);

// Fanout: ignores routing key, delivers to every bound queue
new FanoutExchange("cache.invalidation.exchange");
new Binding("serviceAQueue", QUEUE, "cache.invalidation.exchange", "", null);

// Headers: matches on header values, not routing key
new HeadersExchange("priority.routing.exchange");
new Binding("urgentQueue", QUEUE, "priority.routing.exchange", "",
    Map.of("x-match", "all", "priority", "high"));
```

Each exchange type's binding declares matching criteria in a fundamentally different shape — a key, a pattern, nothing at all, or a header map.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Direct exchanges match routing keys exactly, topic exchanges match wildcard patterns, fanout exchanges ignore routing keys and broadcast to all bound queues, headers exchanges match on header values instead of routing keys" >
  <rect x="10" y="20" width="145" height="160" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="82" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Direct</text>
  <text x="25" y="45" fill="#e6edf3" font-size="7" font-family="monospace">key: "order.shipped"</text>
  <text x="25" y="65" fill="#79c0ff" font-size="7" font-family="monospace">exact match only</text>

  <rect x="165" y="20" width="145" height="160" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="237" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Topic</text>
  <text x="180" y="45" fill="#e6edf3" font-size="7" font-family="monospace">pattern: "order.*.us"</text>
  <text x="180" y="65" fill="#79c0ff" font-size="7" font-family="monospace">wildcard * and #</text>

  <rect x="320" y="20" width="145" height="160" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="392" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Fanout</text>
  <text x="335" y="45" fill="#e6edf3" font-size="7" font-family="monospace">(routing key ignored)</text>
  <text x="335" y="65" fill="#79c0ff" font-size="7" font-family="monospace">every bound queue</text>

  <rect x="475" y="20" width="145" height="160" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="547" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Headers</text>
  <text x="490" y="45" fill="#e6edf3" font-size="7" font-family="monospace">{priority: high}</text>
  <text x="490" y="65" fill="#79c0ff" font-size="7" font-family="monospace">matches on headers</text>
</svg>

Same producer/queue model underneath; the matching rule the exchange applies is what differs.

## 5. Runnable example

The scenario: routing order notifications through each exchange type in turn, simulated with a plain in-memory model of each matching rule (no real RabbitMQ broker needed to demonstrate the type-specific matching logic itself), starting with direct exchange matching, then adding topic exchange wildcard matching, then adding fanout and headers matching to complete the comparison across all four types.

### Level 1 — Basic

```java
// ExchangeTypesDemo.java
import java.util.*;

public class ExchangeTypesDemo {
    record Binding(String queueName, String routingKeyPattern) {}

    // Direct exchange: exact string match only.
    static List<String> routeDirect(String routingKey, List<Binding> bindings) {
        List<String> matched = new ArrayList<>();
        for (Binding b : bindings) if (b.routingKeyPattern().equals(routingKey)) matched.add(b.queueName());
        return matched;
    }

    public static void main(String[] args) {
        List<Binding> bindings = List.of(new Binding("shippingQueue", "order.shipped"));
        System.out.println("Direct exchange routing 'order.shipped': " + routeDirect("order.shipped", bindings));
        System.out.println("Direct exchange routing 'order.shipped.us' (no exact match): "
            + routeDirect("order.shipped.us", bindings));
    }
}
```

How to run: `java ExchangeTypesDemo.java`. Expected output: `[shippingQueue]` for the exact match, then `[]` for the near-miss — direct exchanges require the routing key to match character-for-character, with no partial credit.

### Level 2 — Intermediate

```java
// ExchangeTypesDemo.java
import java.util.*;

public class ExchangeTypesDemo {
    record Binding(String queueName, String routingKeyPattern) {}

    static List<String> routeDirect(String routingKey, List<Binding> bindings) {
        List<String> matched = new ArrayList<>();
        for (Binding b : bindings) if (b.routingKeyPattern().equals(routingKey)) matched.add(b.queueName());
        return matched;
    }

    // Real-world concern: topic exchanges need wildcard matching for hierarchical routing keys
    // to be genuinely useful -- otherwise they'd behave identically to a direct exchange.
    static boolean topicMatches(String pattern, String routingKey) {
        String[] p = pattern.split("\\.");
        String[] k = routingKey.split("\\.");
        int pi = 0, ki = 0;
        while (pi < p.length && ki < k.length) {
            if (p[pi].equals("#")) return true;
            if (p[pi].equals("*") || p[pi].equals(k[ki])) { pi++; ki++; } else return false;
        }
        return pi == p.length && ki == k.length;
    }

    static List<String> routeTopic(String routingKey, List<Binding> bindings) {
        List<String> matched = new ArrayList<>();
        for (Binding b : bindings) if (topicMatches(b.routingKeyPattern(), routingKey)) matched.add(b.queueName());
        return matched;
    }

    public static void main(String[] args) {
        List<Binding> topicBindings = List.of(
            new Binding("usOrdersQueue", "order.*.us"),
            new Binding("allEventsQueue", "order.#"));

        System.out.println("Topic exchange routing 'order.shipped.us': "
            + routeTopic("order.shipped.us", topicBindings));
        System.out.println("Topic exchange routing 'order.shipped.eu': "
            + routeTopic("order.shipped.eu", topicBindings));
    }
}
```

How to run: `java ExchangeTypesDemo.java`. Expected output: `Topic exchange routing 'order.shipped.us': [usOrdersQueue, allEventsQueue]` (both patterns match); `Topic exchange routing 'order.shipped.eu': [allEventsQueue]` (only the catch-all `#` pattern matches, since `*` in `order.*.us` requires the last segment to be literally `us`) — demonstrating topic routing's selective wildcard flexibility, more expressive than direct's exact match alone.

### Level 3 — Advanced

```java
// ExchangeTypesDemo.java
import java.util.*;

public class ExchangeTypesDemo {
    record QueueBinding(String queueName, Map<String, String> headerCriteria, String matchMode) {}

    // Fanout exchange: routing key (and any criteria) is irrelevant -- every bound queue gets it.
    static List<String> routeFanout(List<String> boundQueues) {
        return new ArrayList<>(boundQueues);
    }

    // Headers exchange: matches on header key/value pairs, with "all" (every criterion must
    // match) or "any" (at least one criterion must match) semantics -- a real production
    // concern since routing on multiple independent attributes doesn't fit a single routing key.
    static List<String> routeHeaders(Map<String, String> messageHeaders, List<QueueBinding> bindings) {
        List<String> matched = new ArrayList<>();
        for (QueueBinding b : bindings) {
            boolean isMatch;
            if (b.matchMode().equals("all")) {
                isMatch = b.headerCriteria().entrySet().stream()
                    .allMatch(e -> e.getValue().equals(messageHeaders.get(e.getKey())));
            } else {
                isMatch = b.headerCriteria().entrySet().stream()
                    .anyMatch(e -> e.getValue().equals(messageHeaders.get(e.getKey())));
            }
            if (isMatch) matched.add(b.queueName());
        }
        return matched;
    }

    public static void main(String[] args) {
        System.out.println("Fanout exchange (3 bound queues): "
            + routeFanout(List.of("serviceAQueue", "serviceBQueue", "serviceCQueue")));

        List<QueueBinding> headerBindings = List.of(
            new QueueBinding("urgentQueue", Map.of("priority", "high", "region", "us"), "all"),
            new QueueBinding("regionalQueue", Map.of("region", "us"), "any"));

        Map<String, String> msgHeaders = Map.of("priority", "high", "region", "us");
        System.out.println("Headers exchange routing " + msgHeaders + ": " + routeHeaders(msgHeaders, headerBindings));

        Map<String, String> lowPriorityMsg = Map.of("priority", "low", "region", "us");
        System.out.println("Headers exchange routing " + lowPriorityMsg + ": " + routeHeaders(lowPriorityMsg, headerBindings));
    }
}
```

How to run: `java ExchangeTypesDemo.java`. Expected output: the fanout call returns all three bound queues unconditionally; the first headers call matches both bindings (`urgentQueue`'s `all` criteria are fully satisfied, and `regionalQueue`'s `any` criterion matches on region); the second, lower-priority message only matches `regionalQueue`, since `urgentQueue` requires `priority: high` which this message doesn't have — demonstrating routing decisions based on multiple independent header values rather than a single routing-key string.

## 6. Walkthrough

Trace the same order-shipped event through each exchange type to see how the routing decision differs.

1. **Producer publishes once**: the application code that publishes "order shipped" doesn't change based on exchange type — it calls the same `convertAndSend(exchange, routingKey, message)` (or, for headers exchanges, attaches header values to the message) regardless of which exchange type is configured on the broker side.
2. **Direct exchange decision**: the broker compares the routing key character-for-character against each binding's key; only an exact match delivers the message — useful when there's a fixed, known set of distinct categories.
3. **Topic exchange decision**: the broker splits the routing key into dot-separated segments and checks each binding's pattern (with `*` and `#` wildcards) against it — useful when consumers want varying levels of specificity (one region, all regions, all events).
4. **Fanout exchange decision**: the broker ignores the routing key entirely and delivers to every queue bound to that exchange, full stop — useful for broadcast scenarios where every subscriber genuinely needs every message.
5. **Headers exchange decision**: the broker ignores the routing key and instead inspects the message's header values against each binding's declared criteria, using `all`-match or `any`-match semantics as configured on the binding — useful when the routing decision depends on multiple independent, non-hierarchical attributes.
6. **Consumer unaffected either way**: whichever exchange type routed the message, the consumer reading from its bound queue processes it identically — the routing mechanism is entirely a producer/broker-side concern invisible to the final consumer.

```
same message published -> which exchange type is it published to?
  DIRECT  -> exact routing-key match -> one specific queue (or none)
  TOPIC   -> wildcard routing-key match -> queues at varying specificity
  FANOUT  -> routing key ignored -> every bound queue
  HEADERS -> header values matched (all/any) -> queues by attribute combination
```

## 7. Gotchas & takeaways

> **Gotcha:** a fanout exchange completely ignores the routing key, but a producer publishing to one is still required to supply *some* value for the routing key parameter — an empty string is conventional — leading to confusion for anyone who assumes an empty routing key means "no routing happened" rather than "routing key is irrelevant for this exchange type."

- Direct is the simplest and most restrictive; topic generalizes it with wildcard flexibility; fanout removes routing-key-based selection entirely; headers replaces routing-key-based matching with attribute-based matching — pick the least powerful type that still expresses the actual routing requirement, since more powerful types are harder to reason about at scale.
- A topic exchange with only exact-match bindings (no `*` or `#` anywhere) behaves identically to a direct exchange — the extra power is opt-in per binding, not forced onto every consumer.
- Headers exchanges are less commonly used than the other three, largely because routing-key conventions (dot-separated hierarchies matched by topic exchanges) cover most real-world routing needs more simply — reach for headers specifically when the routing criteria genuinely don't fit a hierarchical key.
- Exchange type is a broker-side configuration decision, entirely separate from anything the message payload itself contains — the same order-event payload can be published unchanged regardless of which exchange type receives it; only the routing key (or headers) and the exchange's declared type determine where it goes.
