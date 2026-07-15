---
card: spring-integration
gi: 43
slug: messageendpoint-serviceactivator-annotations
title: "@MessageEndpoint & @ServiceActivator annotations"
---

## 1. What it is

`@MessageEndpoint` is a class-level stereotype annotation (a specialization of `@Component`) marking a class as containing one or more Spring Integration endpoint methods — it's what makes such a class discoverable by regular Spring component scanning in the first place. `@ServiceActivator` (first introduced conceptually in card 0020) is one of several *method-level* annotations that can appear inside such a class, each corresponding to one of the endpoint archetypes from cards 0019–0024 (`@ServiceActivator`, `@Transformer`, `@Filter`, `@Router`, `@Splitter`, `@Aggregator`). Together, they let a plain class declare multiple distinct messaging endpoints as ordinary annotated methods, without each needing its own separately-declared top-level class.

## 2. Why & when

You reach for this annotation pairing specifically when you want messaging endpoints declared as annotated methods on ordinary Spring-managed beans, rather than assembled via the Java DSL (card 0037) or wired as individual `MessageHandler` beans:

- **You prefer annotation-driven configuration over the fluent DSL** — some teams and codebases favor `@ServiceActivator(inputChannel = "orders")` on a method over `IntegrationFlow.from("orders").handle(...)` as a `@Bean` — both approaches produce equivalent runtime behavior; this is a stylistic and organizational choice, not a capability difference.
- **Related endpoint methods naturally belong together on one class** — a single `@MessageEndpoint`-annotated `OrderProcessor` class might contain a `@Filter` method, a `@Transformer` method, and a `@ServiceActivator` method, each independently wired to its own input/output channels, grouped by their shared business domain rather than by DSL flow structure.
- **You're migrating or maintaining an existing codebase already built with these annotations** — recognizing this pattern (as distinct from the DSL) is necessary for reading and extending code that predates or simply didn't adopt the fluent DSL style.

## 3. Core concept

Think of `@MessageEndpoint` like a department sign on an office door, and each `@ServiceActivator`/`@Transformer`/`@Filter` method inside as a named desk within that department, each desk handling its own specific kind of request that arrives at it. The department sign itself (`@MessageEndpoint`) is what makes the whole office discoverable as "a place with staffed desks" in the first place — without it, the class is just an ordinary object with methods that happen to have extra annotations nobody is looking for.

```java
@MessageEndpoint // makes this class discoverable as containing messaging endpoints
public class OrderProcessor {

    @Filter(inputChannel = "orders", outputChannel = "validOrders")
    public boolean isValid(Order order) {
        return order.amount() > 0;
    }

    @Transformer(inputChannel = "validOrders", outputChannel = "discountedOrders")
    public Order applyDiscount(Order order) {
        return order.withDiscount(0.9);
    }

    @ServiceActivator(inputChannel = "discountedOrders")
    public void ship(Order order) {
        fulfillmentService.ship(order);
    }
}
```

Three completely independent endpoints, each with its own annotation and channel wiring, live as plain methods on one class — Spring's component scanning discovers the class via `@MessageEndpoint`, then processes each annotated method individually to wire it to its declared channels.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single MessageEndpoint-annotated class contains multiple independently-wired endpoint methods, each with its own ServiceActivator, Transformer, or Filter annotation and channel bindings">
  <rect x="20" y="15" width="600" height="160" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="320" y="8" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@MessageEndpoint class: OrderProcessor</text>

  <rect x="40" y="35" width="160" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@Filter isValid()</text>
  <text x="120" y="70" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">orders -&gt; validOrders</text>

  <rect x="240" y="35" width="180" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@Transformer applyDiscount()</text>
  <text x="330" y="70" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">validOrders -&gt; discountedOrders</text>

  <rect x="460" y="35" width="160" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@ServiceActivator ship()</text>
  <text x="540" y="70" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">discountedOrders</text>

  <text x="320" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">3 independent, separately-wired endpoints — one class</text>
</svg>

Each annotated method is its own independent endpoint, wired to its own channels — the class itself is purely an organizational grouping, not a data-flow chain.

## 5. Runnable example

The scenario: an order-processing class with three distinct endpoint methods, starting with a basic single-endpoint class, then multiple endpoints on one class wired into a chain via shared channel names, and finally two unrelated endpoints on one class that happen to share no channels at all, showing the class is purely organizational.

### Level 1 — Basic

```java
// BasicMessageEndpointDemo.java
// Simulates what @MessageEndpoint + @ServiceActivator do together, since real annotation
// processing requires a Spring ApplicationContext to scan and wire the actual beans.
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class BasicMessageEndpointDemo {
    @Retention(RetentionPolicy.RUNTIME) @interface MessageEndpoint {}
    @Retention(RetentionPolicy.RUNTIME) @interface ServiceActivator { String inputChannel(); }

    @MessageEndpoint
    static class OrderProcessor {
        @ServiceActivator(inputChannel = "orders")
        public void ship(String order) {
            System.out.println("Shipped: " + order);
        }
    }

    public static void main(String[] args) throws Exception {
        DirectChannel orders = new DirectChannel();
        OrderProcessor processor = new OrderProcessor();

        // what scanning + wiring a @MessageEndpoint class does for you:
        if (processor.getClass().isAnnotationPresent(MessageEndpoint.class)) {
            for (Method m : processor.getClass().getMethods()) {
                ServiceActivator sa = m.getAnnotation(ServiceActivator.class);
                if (sa != null) {
                    orders.subscribe(msg -> {
                        try { m.invoke(processor, msg.getPayload()); } catch (Exception e) { throw new RuntimeException(e); }
                    });
                }
            }
        }

        orders.send(MessageBuilder.withPayload("order-1").build());
    }
}
```

How to run: `java BasicMessageEndpointDemo.java`. Expected output: `Shipped: order-1` — the class-level `@MessageEndpoint` marked it discoverable, and the method-level `@ServiceActivator` provided the actual channel wiring, exactly mirroring the two-annotation pattern real Spring Integration configuration uses.

### Level 2 — Intermediate

Multiple endpoint methods on one class, chained together purely by matching channel name strings between one method's `outputChannel` and the next method's `inputChannel` — the class groups them organizationally, but the actual data flow is defined entirely by the channel names, not by the methods' order or proximity within the class.

```java
// MultiEndpointChainDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

public class MultiEndpointChainDemo {
    @Retention(RetentionPolicy.RUNTIME) @interface Filter { String inputChannel(); String outputChannel(); }
    @Retention(RetentionPolicy.RUNTIME) @interface Transformer { String inputChannel(); String outputChannel(); }
    @Retention(RetentionPolicy.RUNTIME) @interface ServiceActivator { String inputChannel(); }

    record Order(String id, double amount) {}

    static class OrderProcessor {
        @Filter(inputChannel = "orders", outputChannel = "validOrders")
        public boolean isValid(Order order) { return order.amount() > 0; }

        @Transformer(inputChannel = "validOrders", outputChannel = "discountedOrders")
        public Order applyDiscount(Order order) { return new Order(order.id(), order.amount() * 0.9); }

        @ServiceActivator(inputChannel = "discountedOrders")
        public void ship(Order order) { System.out.println("Shipped: " + order); }
    }

    public static void main(String[] args) throws Exception {
        Map<String, DirectChannel> channels = new HashMap<>();
        OrderProcessor processor = new OrderProcessor();

        for (Method m : processor.getClass().getMethods()) {
            if (m.isAnnotationPresent(Filter.class)) {
                Filter f = m.getAnnotation(Filter.class);
                DirectChannel in = channels.computeIfAbsent(f.inputChannel(), k -> new DirectChannel());
                DirectChannel out = channels.computeIfAbsent(f.outputChannel(), k -> new DirectChannel());
                in.subscribe(msg -> { try { if ((boolean) m.invoke(processor, msg.getPayload())) out.send(msg); } catch (Exception e) { throw new RuntimeException(e); } });
            } else if (m.isAnnotationPresent(Transformer.class)) {
                Transformer t = m.getAnnotation(Transformer.class);
                DirectChannel in = channels.computeIfAbsent(t.inputChannel(), k -> new DirectChannel());
                DirectChannel out = channels.computeIfAbsent(t.outputChannel(), k -> new DirectChannel());
                in.subscribe(msg -> { try { out.send(MessageBuilder.withPayload(m.invoke(processor, msg.getPayload())).build()); } catch (Exception e) { throw new RuntimeException(e); } });
            } else if (m.isAnnotationPresent(ServiceActivator.class)) {
                ServiceActivator sa = m.getAnnotation(ServiceActivator.class);
                DirectChannel in = channels.computeIfAbsent(sa.inputChannel(), k -> new DirectChannel());
                in.subscribe(msg -> { try { m.invoke(processor, msg.getPayload()); } catch (Exception e) { throw new RuntimeException(e); } });
            }
        }

        channels.get("orders").send(MessageBuilder.withPayload(new Order("ORD-1", 100.0)).build());
    }
}
```

How to run: `java MultiEndpointChainDemo.java`. Expected output: `Shipped: Order[id=ORD-1, amount=90.0]` — the message flowed through all three methods on the *same class*, purely because each method's `outputChannel` string matched the next method's `inputChannel` string; nothing about the methods being declared in the same class caused the chaining — matching channel names alone did.

### Level 3 — Advanced

Two entirely unrelated endpoint methods on the same class, wired to completely disjoint channels with no shared data flow between them at all — demonstrating that a `@MessageEndpoint` class is purely an organizational/discovery grouping, not an implicit pipeline.

```java
// UnrelatedEndpointsOnOneClassDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

public class UnrelatedEndpointsOnOneClassDemo {
    @Retention(RetentionPolicy.RUNTIME) @interface ServiceActivator { String inputChannel(); }

    // ONE class, TWO methods, wired to COMPLETELY UNRELATED channels — no shared data flow at all
    static class MixedResponsibilityService {
        @ServiceActivator(inputChannel = "orderEvents")
        public void handleOrder(String order) { System.out.println("[orderEvents] handled: " + order); }

        @ServiceActivator(inputChannel = "auditEvents")
        public void handleAudit(String event) { System.out.println("[auditEvents] logged: " + event); }
    }

    public static void main(String[] args) throws Exception {
        Map<String, DirectChannel> channels = new HashMap<>();
        MixedResponsibilityService service = new MixedResponsibilityService();

        for (Method m : service.getClass().getMethods()) {
            ServiceActivator sa = m.getAnnotation(ServiceActivator.class);
            if (sa != null) {
                DirectChannel channel = channels.computeIfAbsent(sa.inputChannel(), k -> new DirectChannel());
                channel.subscribe(msg -> { try { m.invoke(service, msg.getPayload()); } catch (Exception e) { throw new RuntimeException(e); } });
            }
        }

        // completely independent triggers — neither affects the other
        channels.get("orderEvents").send(MessageBuilder.withPayload("ORD-1").build());
        channels.get("auditEvents").send(MessageBuilder.withPayload("login-attempt").build());
    }
}
```

How to run: `java UnrelatedEndpointsOnOneClassDemo.java`. Expected output: `[orderEvents] handled: ORD-1` then `[auditEvents] logged: login-attempt` — two methods on the same class, triggered by two completely separate, unrelated channel sends; the class's role here is purely to group related business logic (order handling and audit logging both happen to live in the same service), not to imply any relationship between the two endpoints' data flows.

## 6. Walkthrough

Tracing `MultiEndpointChainDemo` in execution order:

1. The reflective wiring loop scans `OrderProcessor`'s methods, finding three annotated methods and wiring each to `DirectChannel` instances keyed by their declared channel name strings — `channels` ends up containing `"orders"`, `"validOrders"`, and `"discountedOrders"`, each a separate `DirectChannel`.
2. `channels.get("orders").send(...)` triggers the subscriber wired for `isValid`'s `inputChannel="orders"` — this invokes `isValid(order)` reflectively, which returns `true` since `100.0 > 0`.
3. Because the filter passed, the message is forwarded to the channel keyed `"validOrders"` — the same channel instance that `applyDiscount`'s `inputChannel="validOrders"` was wired to subscribe to.
4. That subscription fires, invoking `applyDiscount(order)`, which returns a new `Order` with `amount = 90.0`; this result is wrapped into a new message and sent to the channel keyed `"discountedOrders"`.
5. `ship`'s subscription, wired to `inputChannel="discountedOrders"`, fires with that discounted order, printing the final `Shipped: ...` line.
6. At no point did the wiring logic care that all three methods happened to live on the same `OrderProcessor` class — the actual chaining was entirely driven by the channel name strings matching between consecutive annotations; had `applyDiscount` instead declared `outputChannel="somethingElse"`, the chain would have broken regardless of the methods still being co-located on one class.

```
OrderProcessor class (organizational grouping only):
  isValid:        orders          -> validOrders       (Filter)
  applyDiscount:  validOrders     -> discountedOrders   (Transformer)
  ship:           discountedOrders -> (none)             (ServiceActivator)

send(orders, Order(100)) -> isValid(true) -> applyDiscount(90) -> ship(90) -> "Shipped: ..."
```

## 7. Gotchas & takeaways

> It's a common misconception that methods declared on the same `@MessageEndpoint` class are somehow implicitly connected or execute in declaration order — as `UnrelatedEndpointsOnOneClassDemo` shows, they are entirely independent unless their channel names are deliberately matched, exactly as if they'd been declared in separate classes entirely. The class boundary is purely for code organization and Spring's component discovery; the actual message flow topology lives entirely in the `inputChannel`/`outputChannel` string values.

- `@MessageEndpoint` is a class-level stereotype marking a class as containing messaging endpoint methods, making it discoverable by Spring's component scanning; `@ServiceActivator` and its sibling annotations (`@Transformer`, `@Filter`, `@Router`, `@Splitter`, `@Aggregator`) are method-level annotations providing each endpoint's actual channel wiring.
- Use this annotation-driven style as an alternative to the Java DSL (card 0037) — both produce equivalent runtime flows; the choice is stylistic, based on whether annotated methods or fluent chains better fit the codebase's conventions.
- Multiple endpoint methods on one class are chained (or not) purely by whether their `inputChannel`/`outputChannel` string values match — the class itself implies no ordering or connection between its methods.
- Group endpoint methods on a class based on shared business domain or responsibility, not based on an assumption that co-location creates an implicit pipeline.
- Reading annotation-driven Spring Integration code requires tracing channel name strings across potentially many classes to reconstruct the actual flow topology — a tradeoff against the DSL's more visually linear, single-chain readability (card 0037).
