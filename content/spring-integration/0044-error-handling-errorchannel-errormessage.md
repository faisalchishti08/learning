---
card: spring-integration
gi: 44
slug: error-handling-errorchannel-errormessage
title: "Error handling (errorChannel, ErrorMessage)"
---

## 1. What it is

When an exception occurs while processing a message anywhere in a flow, Spring Integration's default error-handling machinery catches it and wraps it, along with the original failed message, into an `ErrorMessage` — a special `Message` implementation whose payload is a `MessagingException` (carrying both the underlying cause and the original message that triggered it). That `ErrorMessage` is then sent to a designated error channel — by default, a global channel named `errorChannel`, automatically registered by `@EnableIntegration` (card 0041) — rather than the exception simply propagating up and crashing whatever triggered the original processing.

## 2. Why & when

You reach for (or explicitly configure) error-channel-based handling specifically when failures need to be handled as part of the flow itself, rather than as uncaught exceptions:

- **A poller-driven endpoint's handler throws** — since nothing is synchronously waiting on the result the way a direct caller would be, an uncaught exception here has nowhere obvious to propagate to; routing it to `errorChannel` gives it a defined destination instead of being silently logged and dropped by the poller's own exception handling.
- **You want centralized, uniform error handling across many different endpoints** — one subscriber on `errorChannel` (or a custom error channel configured per-endpoint) can log, alert, retry, or route failures from many different flows through one consistent recovery path, rather than each individual endpoint needing its own try/catch logic.
- **You want the original failed message preserved alongside the failure details** — an `ErrorMessage`'s payload (a `MessagingException`) retains a reference to the original message via `getFailedMessage()`, so recovery logic can inspect exactly what was being processed when the failure occurred, not just the exception's own message string.

## 3. Core concept

Think of `errorChannel` like a hospital's incident report system, as opposed to a patient's file simply vanishing when something goes wrong during treatment. When a complication occurs, it's not silently absorbed — it's documented as a formal incident report (an `ErrorMessage`) that includes both what went wrong (the exception) and exactly which patient was involved (the original failed message), routed to a dedicated review channel where staff can investigate, rather than being lost the moment the complication happened.

```java
@ServiceActivator(inputChannel = "orders")
public void process(Order order) {
    if (order.amount() < 0) {
        throw new IllegalArgumentException("Invalid amount: " + order.amount());
    }
    fulfillmentService.ship(order);
}

@ServiceActivator(inputChannel = "errorChannel") // catches failures from ANYWHERE that routes here
public void handleError(ErrorMessage errorMessage) {
    MessagingException ex = (MessagingException) errorMessage.getPayload();
    Message<?> failedMessage = ex.getFailedMessage();
    System.err.println("Failed to process " + failedMessage.getPayload() + ": " + ex.getCause().getMessage());
}
```

The exception thrown inside `process` never propagates out of the flow uncaught — it's captured, wrapped with the original message, and delivered to whatever is subscribed on `errorChannel`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An exception thrown during message processing is caught, wrapped into an ErrorMessage carrying both the exception and the original failed message, and routed to errorChannel instead of propagating uncaught">
  <rect x="20" y="60" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="85" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">handler THROWS</text>
  <text x="85" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">exception</text>

  <line x1="150" y1="85" x2="210" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#eh1)"/>

  <rect x="220" y="55" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="78" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ErrorMessage built</text>
  <text x="320" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">payload = exception + failedMessage</text>

  <line x1="420" y1="85" x2="480" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#eh2)"/>

  <rect x="490" y="60" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">errorChannel</text>
  <text x="555" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">subscriber handles it</text>

  <defs>
    <marker id="eh1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="eh2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The original failed message survives the failure, packaged alongside the exception, rather than being lost the moment the exception was thrown.

## 5. Runnable example

The scenario: an order-processing endpoint whose handler can throw, starting with basic error-channel routing, then extracting and using the failed message for recovery, and finally different exception types routed to different recovery strategies (echoing the exception-type router from card 0023).

### Level 1 — Basic

```java
// BasicErrorChannelDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessagingException;
import org.springframework.messaging.support.ErrorMessage;
import org.springframework.messaging.support.MessageBuilder;

public class BasicErrorChannelDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel errorChannel = new DirectChannel();

        errorChannel.subscribe(m -> {
            ErrorMessage errorMessage = (ErrorMessage) m;
            MessagingException ex = (MessagingException) errorMessage.getPayload();
            System.out.println("errorChannel received failure: " + ex.getCause().getMessage());
        });

        // what Spring Integration's default error-handling infrastructure does for you:
        orders.subscribe(m -> {
            try {
                Order order = (Order) m.getPayload();
                if (order.amount() < 0) throw new IllegalArgumentException("Invalid amount: " + order.amount());
                System.out.println("Shipped: " + order);
            } catch (Exception e) {
                MessagingException wrapped = new MessagingException(m, e);
                errorChannel.send(new ErrorMessage(wrapped));
            }
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-1", 100.0)).build()); // succeeds
        orders.send(MessageBuilder.withPayload(new Order("ORD-2", -50.0)).build());  // fails, routed to errorChannel
    }
}
```

How to run: `java BasicErrorChannelDemo.java`. Expected output: `Shipped: Order[id=ORD-1, amount=100.0]` for the valid order, then `errorChannel received failure: Invalid amount: -50.0` for the invalid one — the exception from the second order never propagated uncaught; it was caught, wrapped, and routed to a dedicated error-handling subscriber.

### Level 2 — Intermediate

The `ErrorMessage`'s underlying `MessagingException` retains the original failed `Message` via `getFailedMessage()`, letting recovery logic inspect exactly what was being processed — not just the exception's text, but the full original payload and headers.

```java
// FailedMessageRecoveryDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessagingException;
import org.springframework.messaging.support.ErrorMessage;
import org.springframework.messaging.support.MessageBuilder;

public class FailedMessageRecoveryDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel errorChannel = new DirectChannel();
        DirectChannel deadLetterQueue = new DirectChannel();

        deadLetterQueue.subscribe(m -> System.out.println("Dead-lettered for manual review: " + m.getPayload()));

        errorChannel.subscribe(m -> {
            ErrorMessage errorMessage = (ErrorMessage) m;
            MessagingException ex = (MessagingException) errorMessage.getPayload();
            Message<?> failedMessage = ex.getFailedMessage(); // the ORIGINAL message, fully intact
            System.out.println("Recovering from failure. Original payload was: " + failedMessage.getPayload()
                + " with header traceId=" + failedMessage.getHeaders().get("traceId"));
            deadLetterQueue.send(failedMessage); // re-route the ORIGINAL message for manual handling
        });

        orders.subscribe(m -> {
            try {
                Order order = (Order) m.getPayload();
                if (order.amount() < 0) throw new IllegalArgumentException("Invalid amount");
            } catch (Exception e) {
                errorChannel.send(new ErrorMessage(new MessagingException(m, e)));
            }
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-2", -50.0))
            .setHeader("traceId", "trace-abc-123").build());
    }
}
```

How to run: `java FailedMessageRecoveryDemo.java`. Expected output: `Recovering from failure. Original payload was: Order[id=ORD-2, amount=-50.0] with header traceId=trace-abc-123` then `Dead-lettered for manual review: Order[id=ORD-2, amount=-50.0]` — the recovery logic had full access to the original message's payload and headers, not just the exception's own text, letting it re-route the *original* message onward for further handling.

### Level 3 — Advanced

Different exception types routed to different recovery strategies within the error-handling subscriber itself — mirroring the exception-type router pattern from card 0023, but here shown as the natural consumer of `errorChannel`'s output, deciding between an automatic retry and a dead-letter path based on what actually went wrong.

```java
// ExceptionTypeRecoveryDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessagingException;
import org.springframework.messaging.support.ErrorMessage;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.TimeoutException;

public class ExceptionTypeRecoveryDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        DirectChannel orders = new DirectChannel();
        DirectChannel errorChannel = new DirectChannel();
        DirectChannel retryChannel = new DirectChannel();
        DirectChannel deadLetterQueue = new DirectChannel();

        retryChannel.subscribe(m -> System.out.println("RETRYING: " + m.getPayload()));
        deadLetterQueue.subscribe(m -> System.out.println("DEAD-LETTERED (unrecoverable): " + m.getPayload()));

        errorChannel.subscribe(m -> {
            MessagingException ex = (MessagingException) ((ErrorMessage) m).getPayload();
            Message<?> failedMessage = ex.getFailedMessage();
            Throwable rootCause = ex.getCause();
            if (rootCause instanceof TimeoutException) {
                retryChannel.send(failedMessage); // transient failure — worth retrying
            } else {
                deadLetterQueue.send(failedMessage); // permanent failure — needs a human
            }
        });

        orders.subscribe(m -> {
            try {
                Order order = (Order) m.getPayload();
                if (order.id().equals("ORD-TIMEOUT")) throw new TimeoutException("downstream service timed out");
                if (order.amount() < 0) throw new IllegalArgumentException("invalid amount");
            } catch (Exception e) {
                errorChannel.send(new ErrorMessage(new MessagingException(m, e)));
            }
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-TIMEOUT", 50.0)).build()); // transient -> retry
        orders.send(MessageBuilder.withPayload(new Order("ORD-BAD", -50.0)).build());     // permanent -> dead-letter
    }
}
```

How to run: `java ExceptionTypeRecoveryDemo.java`. Expected output: `RETRYING: Order[id=ORD-TIMEOUT, amount=50.0]` then `DEAD-LETTERED (unrecoverable): Order[id=ORD-BAD, amount=-50.0]` — the same `errorChannel` subscriber routed two different failures to two different recovery strategies, purely based on the underlying exception's type.

## 6. Walkthrough

Tracing `ExceptionTypeRecoveryDemo` for the `ORD-TIMEOUT` message in execution order:

1. `orders.send(...)` for `Order[id=ORD-TIMEOUT, amount=50.0]` triggers the subscriber, whose `try` block checks `order.id().equals("ORD-TIMEOUT")` — true — and throws a `TimeoutException`.
2. The `catch` block catches this exception, wraps it (along with the original message `m`) into a `MessagingException`, further wraps that into an `ErrorMessage`, and sends it to `errorChannel`.
3. `errorChannel`'s subscriber receives the `ErrorMessage`, casts its payload to `MessagingException`, and extracts both the original `failedMessage` (via `getFailedMessage()`) and the root cause exception (via `getCause()`).
4. The `if (rootCause instanceof TimeoutException)` check evaluates `true` for this message specifically, since a `TimeoutException` was what was actually thrown.
5. Because the check passed, `retryChannel.send(failedMessage)` is called with the *original* order message (not the error wrapper) — this is the point where a real system might re-attempt the failed operation, since a timeout is often transient and worth retrying.
6. For the second message (`ORD-BAD`, an `IllegalArgumentException`), the exact same error-handling subscriber runs, but its `instanceof TimeoutException` check fails this time, routing to `deadLetterQueue` instead — the same recovery logic made a different decision purely based on which exception type it actually received.

```
ORD-TIMEOUT -> handler throws TimeoutException -> ErrorMessage -> errorChannel
    -> instanceof TimeoutException? YES -> retryChannel.send(originalMessage)

ORD-BAD -> handler throws IllegalArgumentException -> ErrorMessage -> errorChannel
    -> instanceof TimeoutException? NO -> deadLetterQueue.send(originalMessage)
```

## 7. Gotchas & takeaways

> If nothing is subscribed to `errorChannel` (or a custom error channel configured for a specific endpoint), an `ErrorMessage` sent there is either silently dropped or, depending on the channel type and Spring Integration's configuration, can itself throw an exception about having no subscribers — either way, an unmonitored error channel means failures across the entire application can go completely unnoticed. Always ensure at least one subscriber (even a simple logging one) is attached to the global `errorChannel`, and treat "is anything actually listening on errorChannel" as a standard production readiness check.

- When an exception occurs during message processing, Spring Integration's default handling catches it, wraps it (along with the original failed message) into an `ErrorMessage`, and routes it to `errorChannel` instead of letting it propagate uncaught.
- The `ErrorMessage`'s payload is a `MessagingException`, whose `getCause()` gives the original exception and `getFailedMessage()` gives the original message that was being processed when the failure occurred.
- Use a subscriber on `errorChannel` (or a custom per-endpoint error channel) for centralized logging, alerting, or recovery logic — this mirrors the exception-type routing pattern from card 0023, letting different failure types trigger different recovery strategies.
- Always ensure `errorChannel` has at least one subscriber in production; an unmonitored error channel means failures across the application can go silently unnoticed.
- Recovery logic can access and re-route the *original* failed message (not just the exception), enabling patterns like automatic retry for transient failures and dead-lettering for permanent ones — the exact recovery strategy chosen should generally depend on the underlying exception's type, not a one-size-fits-all response.
