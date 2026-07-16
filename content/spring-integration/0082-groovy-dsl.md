---
card: spring-integration
gi: 82
slug: groovy-dsl
title: "Groovy DSL"
---

## 1. What it is

The Groovy DSL is an alternative way of defining an entire Spring Integration flow — not just a single scripted step (card 0081), but the whole wiring of channels, endpoints, and routing — using Groovy's concise, closure-based syntax instead of Java's `IntegrationFlow.from(...).handle(...).get()` builder or XML configuration. It's a complete flow-definition language, similar in spirit to the Java DSL, but written in Groovy and evaluated at build or runtime depending on how it's integrated into the application.

## 2. Why & when

You reach for the Groovy DSL when Groovy's syntax specifically offers a real ergonomic advantage over the Java DSL for defining flow structure:

- **The team already works primarily in Groovy** — for a Grails application or a codebase where Groovy is the dominant language, defining Spring Integration flows in the same language avoids context-switching and lets flow definitions read consistently with the rest of the codebase.
- **Highly concise flow definitions are valued over the extra type-safety the Java DSL provides** — Groovy's closures and looser syntax let some flow definitions read more tersely than the equivalent Java builder chain, at the cost of losing some of the compile-time checking a Java DSL definition benefits from.
- **Do not reach for the Groovy DSL as a default for a Java-centric codebase** — for the overwhelming majority of Spring Integration users, the Java DSL (used throughout this Java DSL & Configuration section) is the more actively maintained, more widely documented, and more IDE-friendly path; the Groovy DSL is a narrower option for teams already committed to Groovy.

## 3. Core concept

Think of the Java DSL as writing a recipe in a strict, structured cookbook format — each step explicitly named and typed, verbose but unambiguous to follow and to have a computer double-check ahead of time. The Groovy DSL is like writing that same recipe in a more conversational shorthand a fellow chef fluent in the same shorthand can read quickly — faster to write and often shorter to read, but leaning more on the reader's (and the runtime's) ability to interpret it correctly rather than a compiler catching mistakes before the recipe is ever used.

```groovy
integrationFlow {
    from 'orderChannel'
    filter { Order order -> order.amount > 100 }
    transform { Order order -> discountService.applyDiscount(order) }
    channel 'discountedOrdersChannel'
}
```

The same flow expressed in the Java DSL would use `IntegrationFlow.from("orderChannel").filter(...).transform(...).channel(...).get()` — structurally identical, expressed in a different language's idioms.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same flow structure can be expressed either through the Java DSL's builder chain or the Groovy DSL's closure-based syntax, producing an equivalent wired flow either way" >
  <rect x="20" y="20" width="280" height="100" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Java DSL</text>
  <text x="35" y="45" fill="#e6edf3" font-size="7" font-family="monospace">IntegrationFlow.from(...)</text>
  <text x="35" y="62" fill="#e6edf3" font-size="7" font-family="monospace">  .filter(...)</text>
  <text x="35" y="79" fill="#e6edf3" font-size="7" font-family="monospace">  .transform(...)</text>
  <text x="35" y="96" fill="#e6edf3" font-size="7" font-family="monospace">  .get();</text>

  <rect x="340" y="20" width="280" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Groovy DSL</text>
  <text x="355" y="45" fill="#e6edf3" font-size="7" font-family="monospace">integrationFlow {</text>
  <text x="355" y="62" fill="#e6edf3" font-size="7" font-family="monospace">  from 'orderChannel'</text>
  <text x="355" y="79" fill="#e6edf3" font-size="7" font-family="monospace">  filter { ... }</text>
  <text x="355" y="96" fill="#e6edf3" font-size="7" font-family="monospace">  transform { ... }</text>

  <text x="320" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Same wired flow, different builder syntax</text>
</svg>

Same underlying flow graph, expressed through two different builder syntaxes.

## 5. Runnable example

The scenario: expressing an order-filtering-and-discounting flow, comparing the structural equivalence between a Java-style builder chain and a Groovy-closure-style definition, simulated with plain Java modeling both styles side by side (a real Groovy DSL requires the Groovy runtime; the point here is demonstrating that both produce the identical resulting flow graph), starting with the Java-style chain, then modeling the Groovy closure style with Java lambdas standing in for closures, then showing both driving the exact same processing to confirm the equivalence.

### Level 1 — Basic

```java
// DslEquivalenceDemo.java
import java.util.function.*;
import java.util.*;

public class DslEquivalenceDemo {
    record Order(String id, double amount) {}

    // Models the Java DSL's builder-chain style directly.
    static List<Order> javaDslStyleFlow(List<Order> orders) {
        List<Order> result = new ArrayList<>();
        for (Order o : orders) {
            if (o.amount() > 100.0) { // .filter(...)
                result.add(new Order(o.id(), o.amount() * 0.9)); // .transform(...)
            }
        }
        return result;
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(new Order("ORD-1", 150.0), new Order("ORD-2", 50.0));
        System.out.println("Java-DSL-style result: " + javaDslStyleFlow(orders));
    }
}
```

How to run: `java DslEquivalenceDemo.java`. Expected output: `Java-DSL-style result: [Order[id=ORD-1, amount=135.0]]` — only the over-100 order passes the filter and gets discounted, expressed in a builder-chain shape resembling the Java DSL.

### Level 2 — Intermediate

```java
// DslEquivalenceDemo.java
import java.util.function.*;
import java.util.*;

public class DslEquivalenceDemo {
    record Order(String id, double amount) {}

    // Real-world concern: the Groovy DSL expresses the SAME steps (filter, transform) using
    // closure syntax; modeled here with a small closure-style builder using Java lambdas to
    // show the steps are structurally identical, just spelled differently.
    static class FlowBuilder {
        private Predicate<Order> filterStep = o -> true;
        private Function<Order, Order> transformStep = o -> o;

        FlowBuilder filter(Predicate<Order> predicate) { this.filterStep = predicate; return this; }
        FlowBuilder transform(Function<Order, Order> fn) { this.transformStep = fn; return this; }

        List<Order> run(List<Order> orders) {
            List<Order> result = new ArrayList<>();
            for (Order o : orders) {
                if (filterStep.test(o)) result.add(transformStep.apply(o));
            }
            return result;
        }
    }

    public static void main(String[] args) {
        // This closure-passing shape is structurally what "filter { ... }" and "transform { ... }"
        // compile down to in the Groovy DSL -- closures bound into the same underlying flow steps.
        FlowBuilder groovyDslStyle = new FlowBuilder()
            .filter(o -> o.amount() > 100.0)
            .transform(o -> new Order(o.id(), o.amount() * 0.9));

        List<Order> orders = List.of(new Order("ORD-1", 150.0), new Order("ORD-2", 50.0));
        System.out.println("Groovy-DSL-style result: " + groovyDslStyle.run(orders));
    }
}
```

How to run: `java DslEquivalenceDemo.java`. Expected output: `Groovy-DSL-style result: [Order[id=ORD-1, amount=135.0]]` — identical to Level 1's result, since the closure-based builder wires exactly the same filter and transform steps, just expressed through a different syntax shape.

### Level 3 — Advanced

```java
// DslEquivalenceDemo.java
import java.util.function.*;
import java.util.*;

public class DslEquivalenceDemo {
    record Order(String id, double amount) {}

    static class FlowBuilder {
        private Predicate<Order> filterStep = o -> true;
        private Function<Order, Order> transformStep = o -> o;

        FlowBuilder filter(Predicate<Order> predicate) { this.filterStep = predicate; return this; }
        FlowBuilder transform(Function<Order, Order> fn) { this.transformStep = fn; return this; }

        List<Order> run(List<Order> orders) {
            List<Order> result = new ArrayList<>();
            for (Order o : orders) {
                if (filterStep.test(o)) result.add(transformStep.apply(o));
            }
            return result;
        }
    }

    static List<Order> javaDslStyleFlow(List<Order> orders) {
        List<Order> result = new ArrayList<>();
        for (Order o : orders) {
            if (o.amount() > 100.0) result.add(new Order(o.id(), o.amount() * 0.9));
        }
        return result;
    }

    // Production concern: whichever DSL a team picks, both must produce IDENTICAL flow
    // behavior for the same input across a realistic dataset -- confirm equivalence explicitly
    // rather than assuming it, since subtle DSL-specific defaults can otherwise diverge silently.
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("ORD-1", 150.0), new Order("ORD-2", 50.0),
            new Order("ORD-3", 200.0), new Order("ORD-4", 100.0));

        List<Order> javaResult = javaDslStyleFlow(orders);
        List<Order> groovyResult = new FlowBuilder()
            .filter(o -> o.amount() > 100.0)
            .transform(o -> new Order(o.id(), o.amount() * 0.9))
            .run(orders);

        System.out.println("Java DSL style:   " + javaResult);
        System.out.println("Groovy DSL style: " + groovyResult);
        System.out.println("Equivalent: " + javaResult.equals(groovyResult));
    }
}
```

How to run: `java DslEquivalenceDemo.java`. Expected output: both styles print the identical filtered-and-discounted order list (`ORD-1` and `ORD-3`, both over 100 and discounted 10%, with `ORD-4` correctly excluded since `100.0` fails a strict `>` filter), and `Equivalent: true` confirms the two syntaxes produce exactly the same flow behavior for the same input.

## 6. Walkthrough

Trace how a Groovy DSL flow definition becomes a running flow, alongside its Java DSL counterpart.

1. **Definition time**: whichever DSL is used, the flow definition — a sequence of `from`, `filter`, `transform`, `handle`, `channel` steps — is evaluated once at application startup, producing an internal representation of channels and endpoints wired together.
2. **Groovy closures as message handlers**: each Groovy closure (`{ Order order -> ... }`) compiles down to something functionally equivalent to a Java lambda implementing the relevant handler interface — the DSL layer is largely a different syntax for wiring the same underlying `MessageHandler`, `MessageChannel`, and related interfaces the Java DSL also targets.
3. **Runtime message flow**: once built, a message entering the flow moves through the wired steps exactly as it would with a Java-DSL-defined flow — the DSL choice affects only how the wiring was expressed, not how messages move through it at runtime.
4. **Equivalence in practice**: as demonstrated in Level 3, the same business logic (filter over-100 orders, apply a 10% discount) produces byte-for-byte identical output regardless of which DSL defined the flow, since both compile down to the same underlying message-processing primitives.
5. **Where they'd actually differ**: the practical differences between the two DSLs show up in tooling (IDE autocomplete and refactoring support are typically stronger for the Java DSL), compile-time checking (Groovy's dynamic typing catches fewer mistakes before runtime than Java's static typing), and team familiarity — not in what kind of flow behavior each is capable of expressing.

```
Groovy DSL definition                Java DSL definition
  integrationFlow { ... }              IntegrationFlow.from(...).filter(...)...get()
        |                                     |
        v                                     v
  compiled to same underlying MessageChannel / MessageHandler wiring
        |                                     |
        v                                     v
  identical runtime message-processing behavior
```

## 7. Gotchas & takeaways

> **Gotcha:** Groovy's dynamic typing means a flow definition that references a non-existent property or method on a message payload compiles without error and only fails when a message actually reaches that step at runtime — the same mistake in the Java DSL, working against strongly-typed lambdas, is far more likely to be caught by the compiler before the application ever runs.

- Choose the Groovy DSL primarily when the surrounding codebase is already Groovy-centric; introducing it into an otherwise Java codebase adds a second flow-definition language for questionable benefit.
- The Java DSL has broader documentation, community usage, and tooling support within the Spring Integration ecosystem — treat it as the default choice and the Groovy DSL as the exception, not the other way around.
- Both DSLs ultimately configure the same underlying `IntegrationFlow` abstraction; a team that understands one can generally read the other's structure, since the concepts (channels, filters, transformers, routers) are identical, only the syntax differs.
- If migrating a Groovy-DSL-defined flow to the Java DSL later becomes desirable (for stronger tooling or team-wide consistency), the migration is mostly mechanical — translating closures to lambdas and adjusting builder-method names — since the two DSLs express the same underlying flow model.
