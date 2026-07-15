---
card: spring-integration
gi: 20
slug: serviceactivator
title: "ServiceActivator"
---

## 1. What it is

`@ServiceActivator` is the endpoint archetype (introduced in card 0019's overview) whose job is invoking a plain method — typically on an existing, messaging-unaware service bean — in response to a message on an input channel. It's the endpoint that lets ordinary business logic participate in a message flow without that business logic itself depending on Spring Integration's `Message`/`MessageChannel` types: the framework handles extracting the payload (and headers, if the method asks for them) and, if the method returns a value, wrapping that value into a new message sent to an output channel.

## 2. Why & when

You reach for `ServiceActivator` specifically when the actual work of a flow step is a plain method call, and you don't want that method to know it's being invoked from a message flow at all:

- **You have existing business logic** (a `@Service` bean with an `applyDiscount(Order)` method, say) **that you want to plug into a flow** without rewriting it to accept `Message<Order>` or depend on messaging types — `@ServiceActivator` bridges the gap, calling the plain method and handling the message plumbing around it.
- **You want the request/reply shape**: take a message in, optionally produce a reply message out, letting the framework worry about correlation via reply channels (the same mechanism `MessagingTemplate`, card 0016, uses) rather than writing that plumbing by hand.
- **You want the endpoint's business logic independently unit-testable**, calling the annotated method directly with plain arguments in a test, with no `Message` construction or channel setup required — a `ServiceActivator`-annotated method is, by design, just a normal method.

## 3. Core concept

Think of `@ServiceActivator` like a translator standing between a foreign diplomat (the messaging system, speaking `Message` objects) and a domain expert (your service bean, speaking plain Java objects) who doesn't know that language. The translator listens for incoming messages, extracts the actual content the expert needs to hear, relays it in plain terms, and — if the expert has something to say back — translates that response back into the messaging system's vocabulary and sends it onward. The expert never has to learn the messaging system's language at all.

```java
@Service
public class DiscountService {
    // a completely plain method — no messaging types in sight
    public double applyDiscount(double amount) {
        return amount * 0.9;
    }
}

@ServiceActivator(inputChannel = "orders", outputChannel = "discountedOrders")
public double discount(double amount) {
    return discountService.applyDiscount(amount);
}
```

Any message sent to `orders` has its payload (here, a `double`) extracted and passed as the method's argument; the method's return value is automatically wrapped into a new message and sent to `discountedOrders` — none of that plumbing appears in the method body itself.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ServiceActivator extracts a message's payload, invokes a plain method with it, and wraps the return value into a new message for the output channel">
  <rect x="20" y="70" width="120" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">input channel</text>

  <line x1="140" y1="92" x2="200" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#sa1)"/>
  <text x="170" y="78" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">extract payload</text>

  <rect x="210" y="55" width="220" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@ServiceActivator</text>
  <rect x="230" y="85" width="180" height="35" rx="5" fill="#0d1117" stroke="#8b949e"/>
  <text x="320" y="107" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">plain method(payload)</text>

  <line x1="430" y1="92" x2="490" y2="92" stroke="#79c0ff" stroke-width="2" marker-end="url(#sa2)"/>
  <text x="460" y="78" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">wrap return value</text>

  <rect x="500" y="70" width="120" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="560" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">output channel</text>

  <defs>
    <marker id="sa1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sa2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The method inside the box never sees a `Message` — extraction and wrapping happen entirely at the boundary the `@ServiceActivator` annotation manages.

## 5. Runnable example

The scenario: a discount-calculation service plugged into a flow via `@ServiceActivator`, starting with a basic payload-in/payload-out activator, then a method that also reads headers, and finally exception handling routed to an error channel.

### Level 1 — Basic

```java
// BasicServiceActivatorDemo.java
// Simulates @ServiceActivator wiring directly with subscribe(), to show exactly what the
// annotation-driven mechanism does under the hood without requiring a full Spring context.
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicServiceActivatorDemo {
    static double applyDiscount(double amount) { // the "plain method" a real @Service would expose
        return amount * 0.9;
    }

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel discountedOrders = new DirectChannel();
        discountedOrders.subscribe(m -> System.out.println("Discounted amount: " + m.getPayload()));

        // what @ServiceActivator(inputChannel="orders", outputChannel="discountedOrders") does for you:
        orders.subscribe(m -> {
            double payload = (Double) m.getPayload();
            double result = applyDiscount(payload);            // plain method call, no messaging types
            discountedOrders.send(MessageBuilder.withPayload(result).build()); // auto-wrap the return value
        });

        orders.send(MessageBuilder.withPayload(100.0).build());
    }
}
```

How to run: `java BasicServiceActivatorDemo.java`. Expected output: `Discounted amount: 90.0` — the plain `applyDiscount` method never touched a `Message`; the activator's job (shown explicitly here) was purely extracting the payload and wrapping the result.

### Level 2 — Intermediate

A real `@ServiceActivator` method can also accept `@Header`-annotated parameters to read specific message headers alongside the payload — useful when the method needs contextual metadata (a customer tier, a request ID) without needing the full `Message` object.

```java
// HeaderAwareServiceActivatorDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class HeaderAwareServiceActivatorDemo {
    // simulates a method with an @Header-annotated parameter: applyDiscount(double amount, @Header("tier") String tier)
    static double applyDiscount(double amount, String tier) {
        double rate = "gold".equals(tier) ? 0.8 : 0.95;
        return amount * rate;
    }

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel discountedOrders = new DirectChannel();
        discountedOrders.subscribe(m -> System.out.println("Discounted amount: " + m.getPayload()));

        orders.subscribe(m -> {
            double payload = (Double) m.getPayload();
            String tier = (String) m.getHeaders().get("tier"); // the @Header extraction step
            double result = applyDiscount(payload, tier);
            discountedOrders.send(MessageBuilder.withPayload(result).build());
        });

        orders.send(MessageBuilder.withPayload(100.0).setHeader("tier", "gold").build());
        orders.send(MessageBuilder.withPayload(100.0).setHeader("tier", "standard").build());
    }
}
```

How to run: `java HeaderAwareServiceActivatorDemo.java`. Expected output: `Discounted amount: 80.0` (gold tier, 20% off) then `Discounted amount: 95.0` (standard tier, 5% off) — the same activator method reads a header to vary its behavior per message, entirely separate from the payload itself.

### Level 3 — Advanced

A production `@ServiceActivator` configuration typically wires the input channel's poller (for a `QueueChannel`-backed, card 0010, input) with an error-handling strategy, so an exception thrown inside the activated method is routed to a dedicated error channel rather than crashing whatever's driving the flow — mirrored here with a channel-level try/catch that forwards failures.

```java
// ErrorRoutingServiceActivatorDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;

public class ErrorRoutingServiceActivatorDemo {
    static double applyDiscount(double amount) {
        if (amount < 0) throw new IllegalArgumentException("Amount cannot be negative: " + amount);
        return amount * 0.9;
    }

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel discountedOrders = new DirectChannel();
        DirectChannel errorChannel = new DirectChannel();

        discountedOrders.subscribe(m -> System.out.println("Discounted amount: " + m.getPayload()));
        errorChannel.subscribe(m -> System.out.println("Error channel received: " + m.getPayload()));

        orders.subscribe(m -> {
            double payload = (Double) m.getPayload();
            try {
                double result = applyDiscount(payload);
                discountedOrders.send(MessageBuilder.withPayload(result).build());
            } catch (Exception e) {
                // this is what an errorChannel wired via @ServiceActivator's error handling does automatically
                errorChannel.send(MessageBuilder.withPayload(
                    "Failed to process " + payload + ": " + e.getMessage()).build());
            }
        });

        orders.send(MessageBuilder.withPayload(100.0).build());  // succeeds
        orders.send(MessageBuilder.withPayload(-50.0).build());  // throws, routed to errorChannel
    }
}
```

How to run: `java ErrorRoutingServiceActivatorDemo.java`. Expected output: `Discounted amount: 90.0` for the valid message, then `Error channel received: Failed to process -50.0: Amount cannot be negative: -50.0` for the invalid one — the exception thrown deep inside the activated method never propagates uncaught; it's captured and routed as a message of its own to a dedicated error-handling path.

## 6. Walkthrough

Tracing `ErrorRoutingServiceActivatorDemo` for the `-50.0` message in execution order:

1. `orders.send(MessageBuilder.withPayload(-50.0).build())` triggers the subscriber on `orders`, which is standing in for the `@ServiceActivator`-managed invocation.
2. The subscriber extracts the payload (`-50.0`) — exactly the step `@ServiceActivator` performs automatically before calling the annotated method.
3. `applyDiscount(-50.0)` is called; inside, the guard condition `amount < 0` is true, so an `IllegalArgumentException` is thrown instead of returning a value.
4. Because the invocation is wrapped in a `try`/`catch`, the exception is caught rather than propagating up and crashing whatever triggered the original `send()` — in a real `@ServiceActivator` setup, this is the role of a configured `errorChannel`.
5. The `catch` block builds a new message describing the failure and sends it to `errorChannel` instead of `discountedOrders` — the flow doesn't halt; it takes a different path for the failure case.
6. `errorChannel`'s subscriber receives that failure-describing message and prints it — from the perspective of anything monitoring `errorChannel`, this looks like any other message, just one that represents "processing failed" rather than "processing succeeded."

```
orders.send(-50.0)
  -> extract payload: -50.0
  -> applyDiscount(-50.0) THROWS IllegalArgumentException
  -> caught, wrapped as failure message
  -> errorChannel.send("Failed to process -50.0: ...")
  -> errorChannel subscriber prints it
```

## 7. Gotchas & takeaways

> A `@ServiceActivator`-annotated method that has a `void` return type produces no reply message at all — this is correct and often intentional (a "fire and forget" side effect), but it's easy to mistakenly expect a reply that will never come if the method's return type was meant to carry a result and was accidentally left as `void`. Double-check the return type matches whether downstream truly expects a reply.

- `@ServiceActivator` invokes a plain method in response to a message, extracting the payload (and optionally headers via `@Header`) as arguments and wrapping a non-void return value into a reply message for the output channel.
- Use it to plug existing, messaging-unaware business logic into a flow without that logic depending on `Message`/`MessageChannel` types — keeping it independently unit-testable.
- A `void`-returning method produces no reply; a value-returning method's result is automatically wrapped and sent onward.
- Exceptions thrown inside the activated method should be routed to a dedicated error channel (rather than left to propagate uncaught) so a single bad message doesn't take down the whole flow.
- `@ServiceActivator` is the "do the actual work" archetype among the five covered starting at card 0019 — `Transformer` (0021), `Filter` (0022), `Router` (0023), and `Splitter` (0024) each handle a different, more structural kind of decision around that work.
