---
card: spring-cloud
gi: 81
slug: functional-programming-model-supplier-function-consumer
title: "Functional programming model (Supplier/Function/Consumer)"
---

## 1. What it is

Spring Cloud Stream's programming model is built directly on Java's own `java.util.function.Supplier`, `Function`, and `Consumer` interfaces: a `Supplier<T>` bean produces outgoing messages (a source, with no input), a `Function<T, R>` bean transforms an incoming message into an outgoing one (a processor), and a `Consumer<T>` bean handles an incoming message with no output (a sink) — no Spring Cloud Stream-specific annotations needed on the method itself, just a plain functional bean.

```java
@Bean
Supplier<OrderPlaced> orderSource() {
    return () -> new OrderPlaced(UUID.randomUUID().toString(), 99.99); // called on a schedule, produces events
}

@Bean
Function<OrderPlaced, InvoiceRequested> handleOrder() {
    return orderPlaced -> new InvoiceRequested(orderPlaced.orderId(), orderPlaced.amount());
}

@Bean
Consumer<InvoiceRequested> logInvoiceRequest() {
    return invoiceRequested -> System.out.println("invoice requested: " + invoiceRequested);
}
```

## 2. Why & when

Older messaging frameworks (including Spring Cloud Stream's own earlier annotation-based model, `@StreamListener`) required framework-specific annotations scattered through message-handling code. The functional model instead recognizes that "produce a value," "transform a value," and "consume a value with no result" are exactly what `Supplier`, `Function`, and `Consumer` already express in plain Java — so Spring Cloud Stream just binds ordinary functional beans to message channels by name, with no messaging-specific code inside the function itself.

Reach for this model (it's the default, current, recommended approach) because:

- Message-handling logic stays pure, ordinary Java — the same `Function<OrderPlaced, InvoiceRequested>` bean is trivially unit-testable by just calling it directly, with no messaging infrastructure involved in the test at all.
- The three shapes map cleanly onto the three roles a service can play in an event-driven system: pure source (`Supplier`), pure sink (`Consumer`), or transformer/router (`Function`) — most real messaging logic is one of these three, rarely anything more exotic.
- Bean names drive binding configuration (`spring.cloud.stream.bindings.<bean-name>-in-0.destination=...`), so which topic/queue a function reads from or writes to is entirely a configuration concern, not something hardcoded in the function's own code.

## 3. Core concept

```
 Supplier<T>        () -> T           source: produces messages, no input      -- e.g. periodic order generator
 Function<T, R>      T -> R            processor: transforms one message into another -- e.g. order -> invoice request
 Consumer<T>          T -> void        sink: consumes a message, produces nothing -- e.g. write to a log/database

 binding names (default convention):
   <function-bean-name>-out-0   -- where a Supplier's or Function's output goes
   <function-bean-name>-in-0    -- where a Function's or Consumer's input comes from
```

Each shape maps directly to a role; Spring Cloud Stream's job is purely to connect these plain functions to real message channels by configuration.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A supplier produces messages with no input, a function transforms an incoming message into an outgoing one, and a consumer receives a message and produces no output, each bound to real channels purely by configuration">
  <rect x="20" y="70" width="150" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Supplier&lt;T&gt;</text>
  <text x="95" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">() -&gt; T</text>

  <rect x="245" y="70" width="150" height="50" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Function&lt;T, R&gt;</text>
  <text x="320" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">T -&gt; R</text>

  <rect x="470" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="545" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Consumer&lt;T&gt;</text>
  <text x="545" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">T -&gt; void</text>

  <line x1="170" y1="95" x2="243" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a81)"/>
  <line x1="395" y1="95" x2="468" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a81)"/>

  <defs><marker id="a81" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Source, processor, and sink chain together purely through binding configuration — none of the three functions has any messaging-specific code inside it.

## 5. Runnable example

The scenario: model a source-processor-sink chain for order events. Start with a bare `Function` transforming a value, then chain a `Supplier` and `Consumer` around it manually, then confirm each piece is independently unit-testable in complete isolation from any messaging infrastructure.

### Level 1 — Basic

A single `Function`, tested as plain Java — no messaging concepts involved at all.

```java
import java.util.function.Function;

public class FunctionalModelLevel1 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}

    static Function<OrderPlaced, InvoiceRequested> handleOrder =
            orderPlaced -> new InvoiceRequested(orderPlaced.orderId(), orderPlaced.amount());

    public static void main(String[] args) {
        InvoiceRequested result = handleOrder.apply(new OrderPlaced("42", 199.99));
        System.out.println(result);
    }
}
```

How to run: `java FunctionalModelLevel1.java`

`handleOrder` is a completely ordinary `Function<OrderPlaced, InvoiceRequested>` — calling `.apply(...)` directly, exactly as shown, is precisely how a unit test would exercise this logic, with zero messaging infrastructure (no broker, no Spring context) needed at all.

### Level 2 — Intermediate

Chain a `Supplier` and `Consumer` around the same `Function`, modeling the full source-processor-sink pipeline manually, before any real binder is involved.

```java
import java.util.function.*;

public class FunctionalModelLevel2 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}

    static Supplier<OrderPlaced> orderSource = () -> new OrderPlaced("42", 199.99);

    static Function<OrderPlaced, InvoiceRequested> handleOrder =
            orderPlaced -> new InvoiceRequested(orderPlaced.orderId(), orderPlaced.amount());

    static Consumer<InvoiceRequested> logInvoiceRequest =
            invoiceRequested -> System.out.println("invoice requested: " + invoiceRequested);

    public static void main(String[] args) {
        // manually wiring what a real binder would do automatically, purely from configuration
        OrderPlaced order = orderSource.get();
        InvoiceRequested invoiceRequest = handleOrder.apply(order);
        logInvoiceRequest.accept(invoiceRequest);
    }
}
```

How to run: `java FunctionalModelLevel2.java`

Three completely independent functional beans — `orderSource`, `handleOrder`, `logInvoiceRequest` — are manually chained in `main`: the supplier's output feeds the function's input, and the function's output feeds the consumer's input. In a real Spring Cloud Stream application, this exact chaining happens automatically, driven entirely by binding configuration naming which destination each function reads from and writes to, with no code like this `main` method needed at all.

### Level 3 — Advanced

Confirm each piece is independently unit-testable, and add a second, differently-configured chain reusing the same `handleOrder` function — demonstrating that pure functions genuinely decouple business logic from any particular messaging wiring.

```java
import java.util.function.*;
import java.util.*;

public class FunctionalModelLevel3 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}

    static Function<OrderPlaced, InvoiceRequested> handleOrder =
            orderPlaced -> new InvoiceRequested(orderPlaced.orderId(), orderPlaced.amount() * 1.0); // pure, no side effects

    // a genuine unit test, with no messaging infrastructure of any kind
    static void testHandleOrder() {
        InvoiceRequested result = handleOrder.apply(new OrderPlaced("test-1", 50.0));
        boolean pass = result.orderId().equals("test-1") && result.amount() == 50.0;
        System.out.println("testHandleOrder: " + (pass ? "PASS" : "FAIL"));
    }

    public static void main(String[] args) {
        testHandleOrder(); // this "test" needs nothing but the function itself -- true of any pure function

        // the SAME handleOrder function reused in two completely different pipeline configurations
        List<OrderPlaced> batchOfOrders = List.of(
                new OrderPlaced("101", 20.0), new OrderPlaced("102", 45.0), new OrderPlaced("103", 12.5)
        );

        System.out.println("-- pipeline A: process and log each --");
        for (OrderPlaced order : batchOfOrders) {
            InvoiceRequested req = handleOrder.apply(order);
            Consumer<InvoiceRequested> logIt = ir -> System.out.println("logged: " + ir);
            logIt.accept(req);
        }

        System.out.println("-- pipeline B: process and collect totals (different consumer, SAME handleOrder) --");
        double[] total = {0.0};
        Consumer<InvoiceRequested> accumulate = ir -> total[0] += ir.amount();
        for (OrderPlaced order : batchOfOrders) {
            accumulate.accept(handleOrder.apply(order)); // reusing the exact same function
        }
        System.out.println("total invoiced amount: " + total[0]);
    }
}
```

How to run: `java FunctionalModelLevel3.java`

`testHandleOrder` demonstrates the real practical payoff of the functional model: business logic (`handleOrder`) is tested by direct function invocation, no Spring context, no broker, no test containers needed. The two "pipelines" in `main` then reuse the *exact same* `handleOrder` function with two completely different consumers (one logs individually, one accumulates a running total) — proving the transformation logic itself is entirely independent of what happens to its output, exactly the separation of concerns the functional model is built around.

## 6. Walkthrough

Trace pipeline B's execution in Level 3.

1. `total` is initialized as a single-element array holding `0.0` (a common Java idiom for a mutable value captured by a lambda, since lambdas can only capture effectively-final local variables).
2. `accumulate`, a `Consumer<InvoiceRequested>`, is defined to add each invoice request's `amount()` into `total[0]`.
3. The loop iterates `batchOfOrders`, calling `handleOrder.apply(order)` for each — this is the identical function used in pipeline A and in `testHandleOrder`, transforming each `OrderPlaced` into its corresponding `InvoiceRequested` with no changes to its own logic whatsoever.
4. Each resulting `InvoiceRequested` is immediately passed to `accumulate.accept(...)`, which adds its `amount()` to the running `total[0]`: first `20.0`, then `20.0 + 45.0 = 65.0`, then `65.0 + 12.5 = 77.5`.
5. The final `println` reports `total invoiced amount: 77.5` — the sum of all three orders' amounts, arrived at purely by reusing `handleOrder` (unchanged from every other use in this file) paired with a different `Consumer` than pipeline A used.

```
handleOrder (SAME function used everywhere):
   testHandleOrder()  -> direct unit test, no infrastructure
   pipeline A         -> handleOrder + logIt (logs each individually)
   pipeline B         -> handleOrder + accumulate (sums a running total)

three completely different USES of one unchanged transformation function
```

## 7. Gotchas & takeaways

> **Gotcha:** function *bean names* drive binding configuration by convention (`<bean-name>-in-0`, `<bean-name>-out-0`), and multiple `Function`/`Supplier`/`Consumer` beans in the same application need to be explicitly told which one(s) are actually active via `spring.cloud.function.definition=handleOrder;anotherFunction` — without this property, Spring Cloud Stream may bind an unexpected function (or fail to bind any) if there's ambiguity about which functional beans should be wired to messaging channels versus used for some other purpose entirely.

- The functional model (`Supplier`/`Function`/`Consumer`) replaced the older annotation-based (`@StreamListener`) approach specifically because plain functions are trivially testable and free of framework-specific code inside the message-handling logic itself.
- `Supplier` (source, no input), `Function` (processor, transforms), and `Consumer` (sink, no output) map directly onto the three roles a service can play in a messaging pipeline — recognizing which shape a piece of logic needs is usually straightforward from its actual input/output requirements.
- Because these are ordinary Java functional interfaces, the exact same testing techniques (direct invocation, mocking, property-based testing) that apply to any pure function apply here too — no messaging-specific test infrastructure is required to verify the core transformation logic.
- Binding configuration (which destination a function reads from or writes to) lives entirely outside the function's own code — the same `Function<OrderPlaced, InvoiceRequested>` bean can be pointed at different topics in different environments purely through `spring.cloud.stream.bindings.*` properties, with zero code changes.
