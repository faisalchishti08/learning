---
card: spring-integration
gi: 37
slug: integrationflow-integrationflows-java-dsl
title: "IntegrationFlow & IntegrationFlows / Java DSL"
---

## 1. What it is

`IntegrationFlow` is the Java DSL's representation of an entire message flow — channels, endpoints, and their connections — expressed as one fluent, programmatic definition instead of individually declared beans wired together by matching channel name strings. `IntegrationFlows` (and, in newer versions, the static `IntegrationFlow.from(...)` entry point) is the builder that constructs an `IntegrationFlow` step by step: `.filter(...)`, `.transform(...)`, `.handle(...)`, `.route(...)`, and so on, each corresponding to one of the endpoint archetypes covered in cards 0019–0036.

## 2. Why & when

You reach for the Java DSL specifically when you want a flow's structure to be visible and type-checked directly in code, rather than assembled implicitly from separately-declared beans:

- **You want a flow's entire shape readable in one place**, top to bottom, rather than having to mentally reconstruct it by finding every bean whose `inputChannel`/`outputChannel` strings happen to match — the DSL's fluent chain *is* the flow's structure, laid out linearly.
- **You want compile-time type checking on each step** — a `.transform(Function<Order, Receipt>)` step won't compile if the previous step's output type doesn't match `Order`, catching a whole class of "wrong channel name" or "wrong payload type" bugs that only surface at runtime with XML or loosely-typed bean wiring.
- **You're building flows programmatically** — conditionally including certain steps, generating similar flows for multiple similar use cases, or composing flow fragments — which is far more natural in a fluent Java API than in static configuration files.

## 3. Core concept

Think of the Java DSL like a recipe written as one continuous set of numbered steps, versus the same recipe's ingredients and techniques scattered across separate index cards that only cross-reference each other by name ("see card 'sauce base'"). Both eventually produce the same dish, but reading the numbered recipe top to bottom tells you the entire story in order; reconstructing it from scattered cross-referenced cards requires actively tracking down and reassembling the pieces yourself.

```java
@Bean
public IntegrationFlow orderFlow() {
    return IntegrationFlow.from("orders")
        .filter((Order o) -> o.amount() > 0)
        .transform((Order o) -> o.withDiscount(0.9))
        .handle((Order o, headers) -> fulfillmentService.ship(o))
        .get();
}
```

This single `@Bean` method fully describes an entire flow — its entry channel, every processing step, and its final action — with no other configuration needed elsewhere; `IntegrationFlow`/`IntegrationFlows` are simply the vocabulary for writing that description fluently.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single fluent IntegrationFlow definition reads top to bottom as one linear description of the entire flow's structure">
  <rect x="20" y="55" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="65" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">from("orders")</text>

  <line x1="110" y1="75" x2="150" y2="75" stroke="#8b949e" stroke-width="1.5" marker-end="url(#df1)"/>

  <rect x="160" y="55" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="205" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">.filter(...)</text>

  <line x1="250" y1="75" x2="290" y2="75" stroke="#8b949e" stroke-width="1.5" marker-end="url(#df1)"/>

  <rect x="300" y="55" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="355" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">.transform(...)</text>

  <line x1="410" y1="75" x2="450" y2="75" stroke="#8b949e" stroke-width="1.5" marker-end="url(#df1)"/>

  <rect x="460" y="55" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="505" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">.handle(...)</text>

  <line x1="550" y1="75" x2="590" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#df2)"/>

  <text x="315" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one fluent chain = one Bean method = the entire flow's structure</text>

  <defs>
    <marker id="df1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="df2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Each `.step(...)` call corresponds directly to one of the endpoint archetypes from cards 0019–0036, chained into one readable, type-checked description.

## 5. Runnable example

The scenario: an order-processing flow expressed with the Java DSL, starting with a basic three-step flow, then adding a router with multiple output branches, and finally a flow assembled programmatically based on a runtime condition.

### Level 1 — Basic

```java
// BasicDslFlowDemo.java
// Simulates the Java DSL's builder mechanics directly with plain functional interfaces, since the
// real IntegrationFlow builder requires a running Spring ApplicationContext to actually wire beans.
import java.util.function.Function;
import java.util.function.Predicate;

public class BasicDslFlowDemo {
    record Order(String id, double amount) {}

    // a minimal stand-in for IntegrationFlow.from(...).filter(...).transform(...).handle(...)
    static class FlowBuilder<T> {
        private T value;
        private boolean stopped = false;
        FlowBuilder(T initial) { this.value = initial; }
        FlowBuilder<T> filter(Predicate<T> condition) {
            if (!stopped && !condition.test(value)) stopped = true;
            return this;
        }
        <R> FlowBuilder<R> transform(Function<T, R> fn) {
            return stopped ? new FlowBuilder<>((R) null) { { this.stopped = true; } } : new FlowBuilder<>(fn.apply(value));
        }
        void handle(java.util.function.Consumer<T> action) {
            if (!stopped) action.accept(value);
            else System.out.println("Flow stopped earlier by filter — handle() never runs");
        }
    }

    public static void main(String[] args) {
        new FlowBuilder<>(new Order("ORD-1", 100.0))
            .filter((Order o) -> o.amount() > 0)
            .transform((Order o) -> new Order(o.id(), o.amount() * 0.9))
            .handle((Order o) -> System.out.println("Shipped: " + o));
    }
}
```

How to run: `java BasicDslFlowDemo.java`. Expected output: `Shipped: Order[id=ORD-1, amount=90.0]` — one fluent chain expressed the entire filter-then-transform-then-handle sequence, type-checked at compile time through each `<T>`/`<R>` transition, exactly mirroring what `IntegrationFlow.from(...).filter(...).transform(...).handle(...)` does in a real Spring context.

### Level 2 — Intermediate

The real Java DSL supports `.route(...)` for branching to multiple sub-flows, each of which can continue with its own independent chain of steps — shown here conceptually with a router dispatching to two different downstream handler chains based on order amount.

```java
// DslRoutingFlowDemo.java
import java.util.function.Consumer;

public class DslRoutingFlowDemo {
    record Order(String id, double amount) {}

    static void routeAndHandle(Order order, Consumer<Order> highValueChain, Consumer<Order> standardChain) {
        // what @Router / .route(...) in the DSL does: dispatch to one of several downstream chains
        if (order.amount() > 100.0) {
            highValueChain.accept(order);
        } else {
            standardChain.accept(order);
        }
    }

    public static void main(String[] args) {
        Consumer<Order> highValueChain = o -> System.out.println("[HIGH-VALUE sub-flow] priority handling: " + o);
        Consumer<Order> standardChain = o -> System.out.println("[STANDARD sub-flow] normal handling: " + o);

        routeAndHandle(new Order("ORD-1", 199.99), highValueChain, standardChain);
        routeAndHandle(new Order("ORD-2", 25.00), highValueChain, standardChain);
    }
}
```

How to run: `java DslRoutingFlowDemo.java`. Expected output: `[HIGH-VALUE sub-flow] priority handling: Order[id=ORD-1, amount=199.99]` then `[STANDARD sub-flow] normal handling: Order[id=ORD-2, amount=25.0]` — each order was dispatched to a completely independent continuation of the flow, based purely on its own content, exactly matching the DSL's `.route(...)` semantics (elaborated further in card 0023's `Router` coverage).

### Level 3 — Advanced

Because the DSL is plain Java code (not static configuration), flows can be assembled programmatically — conditionally including steps based on runtime configuration, such as an environment-specific audit-logging step that's only added when a feature flag is enabled.

```java
// ProgrammaticFlowAssemblyDemo.java
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

public class ProgrammaticFlowAssemblyDemo {
    record Order(String id, double amount) {}

    // simulates building up an IntegrationFlow's steps conditionally, based on runtime config
    static List<Consumer<Order>> buildSteps(boolean auditingEnabled) {
        List<Consumer<Order>> steps = new ArrayList<>();
        steps.add(o -> System.out.println("Validating: " + o));
        if (auditingEnabled) { // step only included when this flag is true — impossible in static XML config
            steps.add(o -> System.out.println("AUDIT LOG: order " + o.id() + " processed at " + System.currentTimeMillis()));
        }
        steps.add(o -> System.out.println("Shipping: " + o));
        return steps;
    }

    public static void main(String[] args) {
        Order order = new Order("ORD-1", 199.99);

        System.out.println("--- Flow WITHOUT auditing ---");
        for (Consumer<Order> step : buildSteps(false)) step.accept(order);

        System.out.println("--- Flow WITH auditing ---");
        for (Consumer<Order> step : buildSteps(true)) step.accept(order);
    }
}
```

How to run: `java ProgrammaticFlowAssemblyDemo.java`. Expected output: the first flow prints only `Validating: ...` and `Shipping: ...` (2 steps), while the second flow prints `Validating: ...`, `AUDIT LOG: ...`, and `Shipping: ...` (3 steps) — the exact same `buildSteps` method produced two structurally different flows purely from a runtime boolean, something a fluent, code-based DSL makes natural and something static declarative configuration makes far more awkward.

## 6. Walkthrough

Tracing `ProgrammaticFlowAssemblyDemo` for the `auditingEnabled=true` call in execution order:

1. `buildSteps(true)` is called; it starts building a `List<Consumer<Order>>`, first adding the validation step unconditionally — this step always exists regardless of the flag.
2. The `if (auditingEnabled)` check evaluates to `true`, so a second step — the audit-logging consumer — is added to the list; this step's very existence in the resulting flow is a runtime decision, not something fixed at compile time or in a static configuration file.
3. The shipping step is added unconditionally, same as validation, becoming either the second or third step depending on whether auditing was included.
4. `buildSteps` returns the fully assembled list of three consumers (with auditing enabled) back to `main`.
5. The `for` loop in `main` iterates over that returned list and calls `.accept(order)` on each step in sequence — exactly the same execution shape as `IntegrationFlow`'s fluent chain, just expressed as an explicit loop over dynamically-assembled steps instead of a static `.step().step().step()` call chain.
6. Each step's `.accept(order)` call runs synchronously in order, printing its own line — the audit log line appears between validation and shipping specifically because that's the position it was inserted at during the conditional assembly in step 2.

```
buildSteps(true):
  steps = [validate]
  if (true) steps.add(auditLog)  -> steps = [validate, auditLog]
  steps.add(ship)                 -> steps = [validate, auditLog, ship]

main: for each step in steps: step.accept(order)
  -> "Validating: ..." -> "AUDIT LOG: ..." -> "Shipping: ..."
```

## 7. Gotchas & takeaways

> Every `.step(...)` call in a fluent DSL chain adds an endpoint to the flow at *build* time, when the `@Bean` method itself runs — not at message-processing time. A common mistake is writing conditional logic *inside* a lambda passed to `.handle(...)`, when the actual intent was to conditionally *include or exclude* a whole step; those are very different things — one is a runtime decision made once, when the flow is assembled, and the other is a per-message decision made every time a message passes through.

- `IntegrationFlow`/`IntegrationFlows` (or the static `IntegrationFlow.from(...)` entry point) let a flow's entire structure — channels, endpoints, and their order — be expressed as one fluent, type-checked chain in plain Java code.
- Each fluent method (`.filter`, `.transform`, `.handle`, `.route`, and so on) corresponds directly to one of the endpoint archetypes covered in cards 0019–0036, just expressed programmatically instead of via separate bean declarations matched by channel-name strings.
- Compile-time type checking across chained steps catches payload-type mismatches that would otherwise only surface as runtime errors with loosely-typed configuration.
- Because it's plain code, flows can be assembled programmatically — steps conditionally included, flow fragments composed, or similar flows generated for multiple related use cases — something far more natural here than in static declarative configuration.
- Keep the distinction clear between build-time decisions (which steps exist in the flow at all, decided once when the `@Bean` method runs) and per-message decisions (conditional logic inside a step's own lambda, evaluated for every message).
