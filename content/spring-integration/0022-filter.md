---
card: spring-integration
gi: 22
slug: filter
title: "Filter"
---

## 1. What it is

`@Filter` is the endpoint archetype (from card 0019's taxonomy) whose job is a pure keep-or-drop decision: it evaluates a condition against an incoming message and either forwards the message, unchanged, to the output channel, or discards it. Unlike `Transformer` (card 0021), a `Filter` never changes a message's shape — its return value is a `boolean`, not a new payload — and unlike `Router` (card 0023), it has exactly one possible destination (or none at all), never a choice between several.

## 2. Why & when

You reach for `Filter` specifically when a flow needs to stop processing certain messages entirely, and that decision deserves to be explicit and self-documenting rather than buried in an `if` inside some other endpoint:

- **Invalid or irrelevant messages shouldn't proceed past a certain point** — malformed input, messages failing a business rule, duplicate messages already processed — a `Filter` is the named place that decision lives, rather than every downstream endpoint needing its own defensive check.
- **You want dropped messages to be observable and testable as their own concern** — a `Filter`'s condition method takes a payload and returns `boolean`, trivially unit-testable in isolation from the rest of the flow, and (with `discardChannel` configured) dropped messages can be routed somewhere observable instead of vanishing silently.
- **A flow needs a clear boundary between "still worth processing" and "not"** — placing a `Filter` early in a pipeline means every endpoint after it can assume the condition already holds, simplifying their own logic.

## 3. Core concept

Think of `Filter` like a metal detector at a security checkpoint, as opposed to a customs officer who repacks your luggage (`Transformer`) or directs you to one of several gates (`Router`). The detector makes exactly one binary decision — pass or don't — and doesn't alter what you're carrying at all; it either waves you through unchanged or stops you right there.

```java
@Filter(inputChannel = "orders", outputChannel = "validOrders", discardChannel = "rejectedOrders")
public boolean isValid(Order order) {
    return order.amount() > 0;
}
```

Messages for which `isValid` returns `true` are forwarded, unchanged, to `validOrders`; messages for which it returns `false` are sent to `rejectedOrders` instead (or simply dropped, if no `discardChannel` is configured) — the `Order` payload itself is never touched either way.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Filter evaluates a boolean condition: true forwards the message unchanged to the output channel, false sends it to a discard channel or drops it">
  <rect x="20" y="70" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">input channel</text>

  <line x1="130" y1="92" x2="190" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#fl1)"/>

  <rect x="200" y="55" width="150" height="75" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="275" y="78" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Filter</text>
  <text x="275" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">isValid(payload)</text>
  <text x="275" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; boolean</text>

  <line x1="350" y1="75" x2="420" y2="45" stroke="#6db33f" stroke-width="2" marker-end="url(#fl2)"/>
  <text x="395" y="35" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">true</text>

  <line x1="350" y1="110" x2="420" y2="150" stroke="#8b949e" stroke-width="2" marker-end="url(#fl3)"/>
  <text x="395" y="165" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">false</text>

  <rect x="430" y="20" width="150" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="505" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">output channel</text>

  <rect x="430" y="130" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="505" y="157" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">discard channel</text>

  <defs>
    <marker id="fl1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="fl2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="fl3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Exactly one boolean decision per message, and the payload itself is never modified by a filter, unlike a transformer.

## 5. Runnable example

The scenario: an order-intake pipeline rejecting invalid orders, starting with a basic pass/drop filter, then routing dropped messages to an observable discard channel, and finally chaining multiple filters for compound validation.

### Level 1 — Basic

```java
// BasicFilterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicFilterDemo {
    record Order(String id, double amount) {}

    static boolean isValid(Order order) { // the filter's actual condition
        return order.amount() > 0;
    }

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel validOrders = new DirectChannel();
        validOrders.subscribe(m -> System.out.println("Valid, forwarded: " + m.getPayload()));

        // what @Filter(inputChannel="orders", outputChannel="validOrders") does for you:
        orders.subscribe(m -> {
            Order order = (Order) m.getPayload();
            if (isValid(order)) {
                validOrders.send(m); // forwarded UNCHANGED — same message instance
            } else {
                System.out.println("Dropped (no discardChannel configured): " + order);
            }
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-1", 199.99)).build()); // valid
        orders.send(MessageBuilder.withPayload(new Order("ORD-2", -10.0)).build());   // invalid
    }
}
```

How to run: `java BasicFilterDemo.java`. Expected output: `Valid, forwarded: Order[id=ORD-1, amount=199.99]` then `Dropped (no discardChannel configured): Order[id=ORD-2, amount=-10.0]` — the second order never reached `validOrders` at all.

### Level 2 — Intermediate

Configuring a `discardChannel` makes dropped messages observable rather than silently vanishing — critical for diagnosing "why did this order never get processed" without digging through logs, since rejected messages become their own visible stream.

```java
// DiscardChannelFilterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class DiscardChannelFilterDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel validOrders = new DirectChannel();
        DirectChannel rejectedOrders = new DirectChannel();

        validOrders.subscribe(m -> System.out.println("ACCEPTED: " + m.getPayload()));
        rejectedOrders.subscribe(m -> System.out.println("REJECTED (visible for monitoring): " + m.getPayload()));

        orders.subscribe(m -> {
            Order order = (Order) m.getPayload();
            if (order.amount() > 0) {
                validOrders.send(m);
            } else {
                rejectedOrders.send(m); // explicit discardChannel routing, not a silent drop
            }
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-1", 199.99)).build());
        orders.send(MessageBuilder.withPayload(new Order("ORD-2", -10.0)).build());
    }
}
```

How to run: `java DiscardChannelFilterDemo.java`. Expected output: `ACCEPTED: Order[id=ORD-1, amount=199.99]` then `REJECTED (visible for monitoring): Order[id=ORD-2, amount=-10.0]` — the rejected order is still fully visible to anything subscribed to `rejectedOrders`, rather than disappearing without a trace.

### Level 3 — Advanced

Chaining multiple filters, each checking one independent condition, composes into compound validation — a message must pass every filter in the chain to reach the end, and each filter's own discard channel pinpoints exactly which condition a given message failed.

```java
// ChainedFiltersDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class ChainedFiltersDemo {
    record Order(String id, double amount, String currency) {}

    public static void main(String[] args) {
        DirectChannel intake = new DirectChannel();
        DirectChannel afterAmountCheck = new DirectChannel();
        DirectChannel afterCurrencyCheck = new DirectChannel();

        afterCurrencyCheck.subscribe(m -> System.out.println("FULLY VALID: " + m.getPayload()));

        // Filter 2: currency must be supported
        afterAmountCheck.subscribe(m -> {
            Order order = (Order) m.getPayload();
            if (order.currency().equals("USD") || order.currency().equals("EUR")) {
                afterCurrencyCheck.send(m);
            } else {
                System.out.println("REJECTED at currency filter: " + order);
            }
        });

        // Filter 1: amount must be positive
        intake.subscribe(m -> {
            Order order = (Order) m.getPayload();
            if (order.amount() > 0) {
                afterAmountCheck.send(m);
            } else {
                System.out.println("REJECTED at amount filter: " + order);
            }
        });

        intake.send(MessageBuilder.withPayload(new Order("ORD-1", 199.99, "USD")).build()); // passes both
        intake.send(MessageBuilder.withPayload(new Order("ORD-2", -10.0, "USD")).build());   // fails amount
        intake.send(MessageBuilder.withPayload(new Order("ORD-3", 50.0, "JPY")).build());    // fails currency
    }
}
```

How to run: `java ChainedFiltersDemo.java`. Expected output: `FULLY VALID: Order[id=ORD-1, ...]` for the first order, `REJECTED at amount filter: Order[id=ORD-2, ...]` for the second (never reaching the currency filter at all), and `REJECTED at currency filter: Order[id=ORD-3, ...]` for the third (passing the amount filter but failing the currency one) — each rejection message identifies precisely which condition failed.

## 6. Walkthrough

Tracing `ChainedFiltersDemo` for the `ORD-3` message in execution order:

1. `intake.send(...)` for `ORD-3` (amount `50.0`, currency `JPY`) triggers the first filter's subscriber.
2. The amount filter's condition, `order.amount() > 0`, evaluates to `true` for `50.0` — the message passes this filter and is forwarded, unchanged, to `afterAmountCheck`.
3. The second filter's subscriber on `afterAmountCheck` evaluates its own condition: `currency.equals("USD") || currency.equals("EUR")`. For `"JPY"`, this is `false`.
4. Because the condition is `false`, the message is **not** forwarded to `afterCurrencyCheck`; instead, the else-branch prints a rejection message identifying the currency filter specifically as the point of failure.
5. `afterCurrencyCheck`'s subscriber never sees `ORD-3` at all — the filter chain stopped it one step short of the end.
6. Compare this with `ORD-1`: it passes both filters' conditions in sequence, reaching `afterCurrencyCheck` and printing as `FULLY VALID` — the only difference between the two paths through the exact same chain is which conditions each message's data happens to satisfy.

```
intake --[Filter: amount>0]--> afterAmountCheck --[Filter: currency in {USD,EUR}]--> afterCurrencyCheck
   ORD-1 (50>0 ✓, USD ✓) -----------------------------------------------------------> FULLY VALID
   ORD-2 (-10>0 ✗) -> REJECTED at amount filter (stops here)
   ORD-3 (50>0 ✓, JPY ✗) -----------------------------------------------------------> REJECTED at currency filter
```

## 7. Gotchas & takeaways

> Without a configured `discardChannel`, a dropped message simply disappears — no exception, no log entry by default, nothing. This is easy to overlook while building a flow ("why did my message never show up downstream?") and is a common source of confusing bugs. Always configure a `discardChannel` (even if it just feeds a logging endpoint) for any `Filter` where silently losing a message would be a problem worth noticing.

- `@Filter` makes a pure keep-or-drop decision based on a `boolean`-returning condition, forwarding the message unchanged if `true` and discarding (or redirecting) it if `false` — it never alters the message's shape, unlike `Transformer` (card 0021).
- Use it to give validation and eligibility decisions a clear, named, independently-testable home in a flow, rather than scattering conditional checks across other endpoints.
- Configure a `discardChannel` to make rejected messages observable rather than silently vanishing — essential for debugging and monitoring.
- Chaining multiple single-condition filters composes into compound validation, with each filter's own discard path pinpointing exactly which condition a message failed.
- A `Filter` has at most one forward destination and one discard destination — it never chooses among several possible forward paths; that job belongs to `Router` (card 0023).
