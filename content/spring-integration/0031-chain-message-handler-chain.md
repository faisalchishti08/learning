---
card: spring-integration
gi: 31
slug: chain-message-handler-chain
title: "Chain (message handler chain)"
---

## 1. What it is

A `<chain>` (or the Java DSL's `IntegrationFlow` chaining methods) is a configuration construct that groups a sequence of endpoints — filters, transformers, service activators, and so on — into a single logical unit, wired together internally without needing an explicitly named intermediate channel between each step. Functionally, a chain of N endpoints behaves identically to N endpoints manually connected by N-1 separate channels (like the multi-station flows built by hand in card 0019's examples); the difference is purely in how much configuration boilerplate that wiring takes.

## 2. Why & when

You reach for a `chain` specifically when a sequence of endpoints always runs together, in a fixed order, and naming a separate channel between every single step adds configuration noise without adding real value:

- **A fixed sequence of steps (validate, then transform, then enrich) always happens together, in that exact order, with no other endpoint ever needing to subscribe to the intermediate channels** — a chain collapses that sequence into one configuration block, since those intermediate channels would otherwise exist purely for internal plumbing with no other consumer.
- **You want a flow's structure to read top-to-bottom as one coherent unit** in configuration, rather than as a scattered set of channel and endpoint bean definitions that a reader has to mentally reconnect by matching channel names.
- **You're using the Java DSL** (`IntegrationFlows.from(...).filter(...).transform(...).handle(...)`), where chaining is the idiomatic way to express a sequence of steps fluently — the DSL's chain syntax is a direct expression of this same underlying concept.

## 3. Core concept

Think of a chain like a factory's pre-assembled workstation cluster, bolted together as one unit, versus the same stations spread individually across the floor and connected by visible conveyor belts (manual channel wiring). Both process items through the exact same sequence of steps — the cluster just doesn't expose the belts *between* its own internal stations for anything else to tap into; only its first input and final output are externally visible connection points.

```java
@Bean
public IntegrationFlow orderProcessingChain() {
    return IntegrationFlows.from("orders")
        .filter((Order o) -> o.amount() > 0)                    // step 1: reject invalid
        .transform((Order o) -> o.withDiscount(0.9))             // step 2: apply discount
        .handle((Order o, headers) -> fulfillmentService.ship(o)) // step 3: invoke business logic
        .get();
}
```

This single fluent chain is functionally equivalent to three separately-wired endpoints connected by two intermediate channels the developer would otherwise have to name and declare — the chain handles that wiring internally.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chain groups a fixed sequence of endpoints into one configuration unit, with only the chain's overall input and output externally visible">
  <rect x="10" y="30" width="600" height="80" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2" stroke-dasharray="6,3"/>
  <text x="310" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">chain (one configuration unit)</text>

  <rect x="30" y="55" width="100" height="35" rx="5" fill="#0d1117" stroke="#6db33f"/>
  <text x="80" y="77" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Filter</text>

  <line x1="130" y1="72" x2="180" y2="72" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ch1)"/>

  <rect x="190" y="55" width="120" height="35" rx="5" fill="#0d1117" stroke="#6db33f"/>
  <text x="250" y="77" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Transformer</text>

  <line x1="310" y1="72" x2="360" y2="72" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ch1)"/>

  <rect x="370" y="55" width="140" height="35" rx="5" fill="#0d1117" stroke="#6db33f"/>
  <text x="440" y="77" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ServiceActivator</text>

  <line x1="-20" y1="72" x2="30" y2="72" stroke="#6db33f" stroke-width="2" marker-end="url(#ch2)"/>
  <line x1="510" y1="72" x2="560" y2="72" stroke="#6db33f" stroke-width="2" marker-end="url(#ch2)"/>
  <text x="0" y="125" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">only in/out visible</text>

  <defs>
    <marker id="ch1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="ch2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Internal steps are wired together automatically; only the chain's overall input and output channels are externally addressable.

## 5. Runnable example

The scenario: an order-processing sequence, starting with a manually-wired multi-step flow (to establish the baseline), then the same sequence expressed as one chained pipeline, and finally a chain with an internal step that also demonstrates a chain-scoped nested filter dropping a message early.

### Level 1 — Basic

```java
// ManuallyWiredBaselineDemo.java
// Establishes the baseline: the exact same 3-step sequence, wired with explicit intermediate channels,
// so Level 2 can show what collapsing this wiring into a chain actually saves.
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class ManuallyWiredBaselineDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        DirectChannel intake = new DirectChannel();
        DirectChannel afterFilter = new DirectChannel();      // channel 1: exists ONLY for internal wiring
        DirectChannel afterTransform = new DirectChannel();    // channel 2: exists ONLY for internal wiring

        afterTransform.subscribe(m -> System.out.println("Shipped: " + m.getPayload()));
        afterFilter.subscribe(m -> {
            Order o = (Order) m.getPayload();
            afterTransform.send(MessageBuilder.withPayload(new Order(o.id(), o.amount() * 0.9)).build());
        });
        intake.subscribe(m -> {
            Order o = (Order) m.getPayload();
            if (o.amount() > 0) afterFilter.send(m);
        });

        intake.send(MessageBuilder.withPayload(new Order("ORD-1", 100.0)).build());
    }
}
```

How to run: `java ManuallyWiredBaselineDemo.java`. Expected output: `Shipped: Order[id=ORD-1, amount=90.0]` — three steps, two intermediate channels declared purely for wiring, neither of which any other endpoint ever subscribes to.

### Level 2 — Intermediate

The same three-step sequence expressed as a chain: internal steps are just callbacks executed in order within a single subscriber, with no separately-declared intermediate channels needed — functionally identical output, less configuration surface.

```java
// ChainedEquivalentDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.function.Function;
import java.util.function.Predicate;

public class ChainedEquivalentDemo {
    record Order(String id, double amount) {}

    // a minimal stand-in for what IntegrationFlow's chain DSL does: run steps in sequence, no named
    // intermediate channels, short-circuiting on a false Predicate exactly like an internal Filter step.
    static void runChain(Order input, Predicate<Order> filterStep, Function<Order, Order> transformStep,
                          java.util.function.Consumer<Order> finalStep) {
        if (!filterStep.test(input)) return; // internal filter step, no separate channel needed
        Order transformed = transformStep.apply(input); // internal transformer step
        finalStep.accept(transformed); // internal service-activator-shaped step
    }

    public static void main(String[] args) {
        DirectChannel intake = new DirectChannel();

        // ONE subscriber, internally running all three steps — this IS the chain
        intake.subscribe(m -> runChain((Order) m.getPayload(),
            o -> o.amount() > 0,                              // step 1: filter
            o -> new Order(o.id(), o.amount() * 0.9),          // step 2: transform
            o -> System.out.println("Shipped: " + o)));        // step 3: service activator

        intake.send(MessageBuilder.withPayload(new Order("ORD-1", 100.0)).build());
    }
}
```

How to run: `java ChainedEquivalentDemo.java`. Expected output: `Shipped: Order[id=ORD-1, amount=90.0]` — identical result to Level 1's manually-wired version, but with zero intermediate channel declarations; the three steps run in sequence inside one logical unit.

### Level 3 — Advanced

Demonstrating that a chain's internal filter step still genuinely short-circuits the rest of the chain — an invalid order never reaches the transform or final steps, exactly like a standalone `Filter` (card 0022) would stop a message, just without a separately-named discard channel unless one is explicitly configured for that internal step.

```java
// ChainShortCircuitDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.function.Function;
import java.util.function.Predicate;

public class ChainShortCircuitDemo {
    record Order(String id, double amount) {}

    static void runChain(Order input, Predicate<Order> filterStep, Function<Order, Order> transformStep,
                          java.util.function.Consumer<Order> finalStep) {
        if (!filterStep.test(input)) {
            System.out.println("Chain SHORT-CIRCUITED at internal filter step for: " + input);
            return; // transform and final steps NEVER run for this message
        }
        Order transformed = transformStep.apply(input);
        finalStep.accept(transformed);
    }

    public static void main(String[] args) {
        DirectChannel intake = new DirectChannel();

        intake.subscribe(m -> runChain((Order) m.getPayload(),
            o -> { System.out.println("Filter step evaluating: " + o); return o.amount() > 0; },
            o -> { System.out.println("Transform step running for: " + o); return new Order(o.id(), o.amount() * 0.9); },
            o -> System.out.println("Final step (shipped): " + o)));

        intake.send(MessageBuilder.withPayload(new Order("ORD-1", 100.0)).build());  // passes
        intake.send(MessageBuilder.withPayload(new Order("ORD-2", -50.0)).build());   // fails filter
    }
}
```

How to run: `java ChainShortCircuitDemo.java`. Expected output for `ORD-1`: `Filter step evaluating: ...`, `Transform step running for: ...`, `Final step (shipped): ...` — all three steps ran. For `ORD-2`: only `Filter step evaluating: ...` followed by `Chain SHORT-CIRCUITED at internal filter step for: ...` — the transform and final steps never printed anything for this message, proving the chain's internal filter genuinely stopped it from proceeding, exactly as a standalone `Filter` endpoint would.

## 6. Walkthrough

Tracing `ChainShortCircuitDemo` for the `ORD-2` message in execution order:

1. `intake.send(...)` for `Order[id=ORD-2, amount=-50.0]` triggers the single subscriber representing the whole chain, which calls `runChain` with that order.
2. Inside `runChain`, the filter step (`o.amount() > 0`) is evaluated first — it prints its evaluation message, then checks `-50.0 > 0`, which is `false`.
3. Because the filter step's predicate returned `false`, the `if (!filterStep.test(input))` branch is entered: a short-circuit message is printed, and the method returns immediately via `return`.
4. Neither `transformStep.apply(...)` nor `finalStep.accept(...)` is ever called — control never reaches those lines, exactly as if a standalone `Filter` endpoint (card 0022) had simply not forwarded the message to whatever came after it.
5. Compare this to `ORD-1`, whose filter step returns `true`: execution falls through past the `if` block, `transformStep` is invoked (printing its own message and producing the discounted order), and then `finalStep` is invoked with that transformed result.
6. From the perspective of anything outside the chain, only one thing is visible either way: whether a message eventually reaches whatever channel/endpoint follows the chain's own final step. What happens *inside* — three internal steps, two of which are entirely invisible to any other part of the flow — is the chain's own private implementation detail.

```
ORD-1 (amount=100): filter(true) -> transform -> final  [ALL 3 steps run]
ORD-2 (amount=-50): filter(false) -> SHORT-CIRCUIT      [only step 1 runs]
```

## 7. Gotchas & takeaways

> Because a chain's intermediate steps have no externally-addressable channel by default, it's easy to design yourself into a corner if a later requirement needs another endpoint to tap into the *middle* of an existing chain (say, to log or branch on the state after step 2 but before step 3) — that requires either breaking the chain apart into separately-wired endpoints, or naming an internal channel explicitly if the chain configuration syntax supports it. If a flow's intermediate state is ever likely to need external visibility, favor explicit channel wiring (as in Level 1) over a chain from the start.

- A `chain` groups a fixed sequence of endpoints into one configuration unit, collapsing the intermediate channels that would otherwise need individual names into internal, hidden wiring.
- Use it for a sequence of steps that always run together, in a fixed order, with no other endpoint needing to subscribe to what happens between them — it reduces configuration boilerplate without changing behavior.
- A chain is functionally equivalent to the same steps manually wired with individual channels; only the configuration surface differs, not the runtime semantics (a filter step inside a chain still genuinely short-circuits the rest of the chain).
- The Java DSL's fluent chaining methods (`.filter(...).transform(...).handle(...)`) are the idiomatic way to express this same concept in code rather than XML configuration.
- Prefer explicit, separately-wired endpoints (over a chain) when a flow's intermediate steps are likely to need external visibility or additional subscribers later — chains trade that flexibility for configuration conciseness.
