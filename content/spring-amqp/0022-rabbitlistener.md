---
card: spring-amqp
gi: 22
slug: rabbitlistener
title: "@RabbitListener"
---

## 1. What it is

`@RabbitListener` is the declarative, annotation-based way to register a method as a message consumer — placed on a method, naming the queue(s) to consume from, it causes Spring to automatically wire up a listener container (card 0021), a `MessageConverter` for automatic argument deserialization, and dispatch each incoming message to that method as a plain Java method call. It's the single most common way applications consume messages in Spring AMQP, replacing the more verbose manual container-and-listener wiring most applications never need to write by hand.

## 2. Why & when

You reach for `@RabbitListener` as the default way to consume messages in essentially every Spring AMQP application:

- **Consuming messages should read like a plain method, not manual listener-container plumbing** — `@RabbitListener(queues = "orderProcessingQueue")` on a method taking an `Order` parameter is immediately readable, with Spring handling connection, container, and conversion concerns entirely behind the scenes.
- **A method's return value should automatically become an RPC reply when appropriate** — as touched on in card 0019, a `@RabbitListener` method that returns a non-void value has that value automatically published back to the request's `replyTo` destination, letting the same declarative style serve both fire-and-forget consumption and RPC-style request handling.
- **Per-listener configuration (concurrency, acknowledgment mode, error handling) needs to be expressible without writing custom container configuration by hand** — `@RabbitListener`'s attributes and companion annotations (`@RabbitHandler` for payload-type-based dispatch to different methods, `containerFactory` for specifying non-default settings) cover the overwhelming majority of real-world consumer configuration needs declaratively.

## 3. Core concept

Think of manually configuring a `SimpleMessageListenerContainer` as wiring up a whole telephone switchboard by hand — connecting lines, configuring routing, setting up the physical apparatus — versus `@RabbitListener` being like simply writing your phone number on a business card and having someone else's switchboard system automatically route any call for that number straight to your desk. The underlying telephone infrastructure (the listener container) still exists and still does real work, but the annotation handles setting it up and connecting it to your method, letting you focus purely on "what do I do when a call (message) actually reaches me."

```java
@Component
public class OrderEventListener {

    @RabbitListener(queues = "orderProcessingQueue")
    public void handleOrderCreated(Order order) {
        orderService.process(order);
    }

    // A method returning a value automatically becomes an RPC reply when the incoming
    // message carried a replyTo destination -- otherwise, the return value is simply ignored.
    @RabbitListener(queues = "quoteRequestQueue")
    public PriceQuote handleQuoteRequest(QuoteRequest request) {
        return pricingEngine.calculate(request);
    }
}
```

Both methods look like ordinary Java methods; Spring's infrastructure handles everything from connecting to the queue through deserializing the incoming message into the method's parameter type.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An @RabbitListener-annotated method is backed automatically by a listener container, a MessageConverter for argument deserialization, and dispatch logic, letting application code focus purely on the method body's business logic" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Queue delivers Message</text>

  <line x1="200" y1="42" x2="260" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a19)"/>
  <rect x="260" y="20" width="150" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Listener container</text>

  <line x1="410" y1="42" x2="470" y2="42" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a19)"/>
  <rect x="470" y="20" width="150" height="45" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">MessageConverter</text>

  <line x1="545" y1="65" x2="335" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a19)"/>
  <rect x="150" y="95" width="370" height="40" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="120" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@RabbitListener method: handleOrderCreated(Order order)</text>
</svg>

Everything before the annotated method's own logic is handled automatically by Spring's infrastructure.

## 5. Runnable example

The scenario: consuming order events with automatic argument conversion, simulated with a plain Java dispatcher standing in for `@RabbitListener`'s container-and-conversion infrastructure (no real Spring AMQP context needed to demonstrate the annotation-driven dispatch pattern), starting with a basic single-listener dispatch, then adding automatic RPC-reply behavior for a method with a return value, then adding `@RabbitHandler`-style payload-type-based dispatch across multiple methods sharing one listener.

### Level 1 — Basic

```java
// RabbitListenerDemo.java
public class RabbitListenerDemo {
    record Order(String id, double amount) {}

    // Stand-in for a class with an @RabbitListener(queues = "orderProcessingQueue") method.
    static class OrderEventListener {
        void handleOrderCreated(Order order) {
            System.out.println("Processing order: " + order.id() + " amount=" + order.amount());
        }
    }

    // Stand-in for the listener container's dispatch: deserialize, then call the method.
    static void dispatchMessage(String rawJson, OrderEventListener listener) {
        String id = rawJson.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1");
        double amount = Double.parseDouble(rawJson.replaceAll(".*\"amount\":([0-9.]+).*", "$1"));
        listener.handleOrderCreated(new Order(id, amount));
    }

    public static void main(String[] args) {
        OrderEventListener listener = new OrderEventListener();
        dispatchMessage("{\"id\":\"ORD-1\",\"amount\":42.50}", listener);
    }
}
```

How to run: `java RabbitListenerDemo.java`. Expected output: `Processing order: ORD-1 amount=42.5` — the incoming message deserialized and dispatched to the listener method as a plain Java call.

### Level 2 — Intermediate

```java
// RabbitListenerDemo.java
public class RabbitListenerDemo {
    record QuoteRequest(String itemId, int quantity) {}
    record PriceQuote(String itemId, double totalPrice) {}

    static class PricingListener {
        // Real-world concern: a return value from an @RabbitListener method automatically
        // becomes an RPC reply when the incoming message carried a replyTo destination.
        PriceQuote handleQuoteRequest(QuoteRequest request) {
            return new PriceQuote(request.itemId(), request.quantity() * 9.99);
        }
    }

    static void dispatchWithAutoReply(QuoteRequest request, String replyTo, PricingListener listener) {
        PriceQuote result = listener.handleQuoteRequest(request);
        if (replyTo != null && result != null) {
            System.out.println("Auto-publishing reply to '" + replyTo + "': " + result);
        }
    }

    public static void main(String[] args) {
        PricingListener listener = new PricingListener();
        dispatchWithAutoReply(new QuoteRequest("WIDGET-1", 3), "amq.rabbitmq.reply-to", listener);

        // A fire-and-forget style message (no replyTo) -- return value simply isn't published anywhere.
        dispatchWithAutoReply(new QuoteRequest("WIDGET-2", 1), null, listener);
    }
}
```

How to run: `java RabbitListenerDemo.java`. Expected output: `Auto-publishing reply to 'amq.rabbitmq.reply-to': PriceQuote[itemId=WIDGET-1, totalPrice=29.97]` for the request carrying a reply destination; nothing prints for the second call, since no `replyTo` was present — the same listener method serving both RPC and fire-and-forget callers depending purely on whether the incoming message asked for a reply.

### Level 3 — Advanced

```java
// RabbitListenerDemo.java
import java.util.*;

public class RabbitListenerDemo {
    record OrderCreated(String orderId) {}
    record OrderCancelled(String orderId, String reason) {}

    // Production concern: @RabbitHandler lets ONE @RabbitListener queue dispatch to DIFFERENT
    // methods based on the incoming payload's type -- useful when a queue carries a union of
    // related event types rather than a single fixed message shape.
    static class MultiTypeOrderListener {
        void handle(OrderCreated event) {
            System.out.println("Handling OrderCreated: " + event.orderId());
        }
        void handle(OrderCancelled event) {
            System.out.println("Handling OrderCancelled: " + event.orderId() + " reason=" + event.reason());
        }
    }

    // Stand-in for the type-based dispatch @RabbitHandler performs internally.
    static void dispatchByType(Object payload, MultiTypeOrderListener listener) {
        if (payload instanceof OrderCreated created) {
            listener.handle(created);
        } else if (payload instanceof OrderCancelled cancelled) {
            listener.handle(cancelled);
        } else {
            System.out.println("No matching @RabbitHandler method for payload type: " + payload.getClass());
        }
    }

    public static void main(String[] args) {
        MultiTypeOrderListener listener = new MultiTypeOrderListener();

        List<Object> incomingMessages = List.of(
            new OrderCreated("ORD-1"),
            new OrderCancelled("ORD-2", "customer requested"),
            new OrderCreated("ORD-3"));

        for (Object payload : incomingMessages) {
            dispatchByType(payload, listener);
        }
    }
}
```

How to run: `java RabbitListenerDemo.java`. Expected output: `Handling OrderCreated: ORD-1`, `Handling OrderCancelled: ORD-2 reason=customer requested`, `Handling OrderCreated: ORD-3` — three messages of two different logical event types, all arriving on what would be the same queue, correctly dispatched to their matching handler method purely based on payload type, exactly the pattern `@RabbitHandler` implements for a class with multiple type-specific methods under one shared `@RabbitListener`.

## 6. Walkthrough

Trace a message from arrival on the queue through to the invoked listener method, including the RPC-reply and type-dispatch variations.

1. **Message arrives at the queue**: a message published by some producer sits on the queue that a `@RabbitListener`-annotated method (or class, for multi-method `@RabbitHandler` dispatch) is configured to consume from.
2. **Listener container delivers it**: the auto-configured listener container (card 0021) — created and wired automatically because of the `@RabbitListener` annotation — picks up the message from the queue via its underlying consumer mechanism.
3. **Automatic argument conversion**: the container's configured `MessageConverter` (card 0012) deserializes the message body into the Java type the target listener method's parameter expects, based on the message's content-type header and the method's declared parameter type.
4. **Method dispatch**: for a single-method listener, the container simply calls that method with the deserialized argument; for a class using `@RabbitHandler` across multiple methods, the container additionally inspects the deserialized payload's runtime type to determine which specific method to call, supporting a queue that carries a mix of related message types.
5. **Business logic executes**: the listener method's body runs exactly as any ordinary Java method would, with no AMQP-specific code required inside it — the method's job is purely the business logic, with all messaging concerns handled by the surrounding infrastructure.
6. **Return value handling**: if the method returns `void`, nothing further happens after it completes. If it returns a non-void value and the incoming message carried a `replyTo` destination and correlation ID (an RPC-style call, card 0019), the container automatically publishes that return value back to the reply destination; if there was no `replyTo`, the return value is simply discarded, letting the same method transparently serve both RPC and fire-and-forget invocation styles.

```
message arrives on queue
  -> listener container (auto-configured) delivers it
    -> MessageConverter deserializes body -> target parameter type
      -> (if @RabbitHandler class) dispatch by payload runtime type -> correct method chosen
        -> listener method body executes (pure business logic)
          -> return void: nothing further
          -> return value + replyTo present: auto-published as RPC reply
          -> return value + no replyTo: discarded
```

## 7. Gotchas & takeaways

> **Gotcha:** a `@RabbitListener` method that throws an unhandled exception, by default, causes the message to be requeued (depending on the configured acknowledgment mode and exception-handling strategy) — without explicit error handling or a dead-letter configuration, a message that always causes an exception (a poison message) can be redelivered and re-fail indefinitely in a tight loop, consuming resources without ever making progress; production listeners need an explicit strategy (a dead-letter exchange, a retry-then-give-up policy) for this scenario.

- `@RabbitListener` is the standard, default way to consume messages in essentially every modern Spring AMQP application — reach for manual `SimpleMessageListenerContainer`/`DirectMessageListenerContainer` configuration (card 0021) only for cases needing configuration the annotation's attributes and companion mechanisms don't cover.
- A `@RabbitListener` method's return value automatically becoming an RPC reply (when the incoming message asked for one) is what lets the exact same declarative style serve both fire-and-forget event consumption and synchronous request/reply handling, without separate programming models for each.
- `@RabbitHandler` on multiple methods within a class annotated at the class level with `@RabbitListener` supports payload-type-based dispatch, useful when a single queue legitimately carries a mix of related but differently-shaped message types.
- Unhandled exceptions in listener methods have real, non-trivial consequences (requeue behavior, potential infinite redelivery loops) — always pair listener methods with a deliberate error-handling and dead-lettering strategy rather than assuming the default behavior is automatically safe for production traffic.
