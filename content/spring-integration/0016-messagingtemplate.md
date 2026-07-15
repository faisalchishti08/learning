---
card: spring-integration
gi: 16
slug: messagingtemplate
title: "MessagingTemplate"
---

## 1. What it is

`MessagingTemplate` is a helper class that wraps the raw `send()`/`receive()` calls on `MessageChannel` with a friendlier, higher-level API — including request/reply exchanges, timeouts, and automatic payload wrapping. Instead of manually building a `Message`, calling `channel.send(...)`, and separately waiting on a reply channel, `MessagingTemplate` gives you a single call like `sendAndReceive(channel, message)` that does the plumbing for you, in the same spirit as `JdbcTemplate` or `RestTemplate` wrapping lower-level, more verbose APIs.

## 2. Why & when

You reach for `MessagingTemplate` specifically when you want to interact with channels programmatically without hand-rolling request/reply coordination:

- **You need a synchronous request/reply exchange** — send a message and block for a correlated response — without manually creating a temporary reply channel, setting the `replyChannel` header, and writing your own `receive()`/timeout logic each time.
- **You're calling into a Spring Integration flow from plain application code** (a `@Service`, a test, a controller) and want a simple, direct API rather than assembling `Message` objects and channel references by hand every time.
- **You want consistent timeout and error-handling behavior** across many send/receive call sites, configured once on the template (default timeouts, a default destination channel) rather than repeated at every call site.

## 3. Core concept

Think of `MessagingTemplate` like ordering at a counter with a numbered ticket, as opposed to shouting your order into a kitchen and waiting around outside (managing a reply channel by hand). You hand over your order (the request message) and your ticket number is handled for you; when your order's ready, it comes back matched to your ticket — `MessagingTemplate` manages that matching (via a temporary reply channel and correlation) behind a single method call.

```java
MessagingTemplate template = new MessagingTemplate();
template.setDefaultChannel(requestChannel);
template.setReceiveTimeout(5000);

Message<?> reply = template.sendAndReceive(MessageBuilder.withPayload("compute-42").build());
System.out.println("Got reply: " + reply.getPayload());
```

Under the hood, `sendAndReceive` creates a temporary anonymous reply channel, stamps it onto the outgoing message's `replyChannel` header, sends the request, and blocks (up to the configured timeout) waiting for something to be sent back to that temporary channel — all of which you'd otherwise write by hand.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MessagingTemplate.sendAndReceive: sends a request with an auto-created reply channel header, then blocks until a correlated reply arrives or the timeout elapses">
  <rect x="20" y="20" width="140" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">caller: sendAndReceive()</text>

  <line x1="90" y1="65" x2="90" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#m1)"/>
  <text x="140" y="85" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">1. send request</text>

  <rect x="20" y="105" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="128" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">request channel</text>

  <line x1="160" y1="125" x2="330" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#m3)"/>
  <text x="245" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2. handled by service</text>

  <rect x="340" y="105" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="410" y="128" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">handler / activator</text>

  <line x1="410" y1="105" x2="240" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#m2)"/>
  <text x="360" y="70" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">3. reply -> temp reply channel</text>

  <rect x="180" y="20" width="140" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="250" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">temp reply channel</text>
  <text x="250" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">4. unblocks caller</text>

  <defs>
    <marker id="m1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="m2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="m3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`sendAndReceive` hides the temporary reply channel's creation and correlation entirely — the caller just gets a `Message` back (or `null` on timeout).

## 5. Runnable example

The scenario: a compute service exposed over a channel, starting with basic request/reply via `MessagingTemplate`, then a bounded timeout for when nothing replies, and finally programmatic conversion between plain payloads and `Message` objects.

### Level 1 — Basic

```java
// BasicMessagingTemplateDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.MessageBuilder;

public class BasicMessagingTemplateDemo {
    public static void main(String[] args) {
        QueueChannel requestChannel = new QueueChannel();

        // a simple "service" thread: receives a request, computes, replies to the header-specified channel
        Thread service = new Thread(() -> {
            Message<?> request = requestChannel.receive();
            int input = (Integer) request.getPayload();
            MessageChannel replyChannel = (MessageChannel) request.getHeaders().getReplyChannel();
            replyChannel.send(MessageBuilder.withPayload(input * 2).build());
        });
        service.start();

        MessagingTemplate template = new MessagingTemplate();
        template.setDefaultChannel(requestChannel);

        Message<?> reply = template.sendAndReceive(MessageBuilder.withPayload(21).build());
        System.out.println("Reply payload: " + reply.getPayload()); // 42
    }
}
```

How to run: `java BasicMessagingTemplateDemo.java`. Expected output: `Reply payload: 42` — `sendAndReceive` sent `21`, the background "service" doubled it and replied to the automatically-attached reply channel, and the template correlated that reply back to the original call.

### Level 2 — Intermediate

When configured with `setReceiveTimeout`, `sendAndReceive` returns `null` (rather than blocking forever) if nothing replies within that window — essential for not hanging indefinitely on a downstream that never responds.

```java
// TimeoutMessagingTemplateDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class TimeoutMessagingTemplateDemo {
    public static void main(String[] args) {
        QueueChannel requestChannel = new QueueChannel();
        // NOTE: no service thread started — nothing will ever reply

        MessagingTemplate template = new MessagingTemplate();
        template.setDefaultChannel(requestChannel);
        template.setReceiveTimeout(1000); // give up after 1 second

        System.out.println("Sending, expecting no reply...");
        long start = System.currentTimeMillis();
        Message<?> reply = template.sendAndReceive(MessageBuilder.withPayload(21).build());
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("Reply: " + reply + " after ~" + elapsed + "ms");
        // reply == null: the timeout elapsed with nobody having replied
    }
}
```

How to run: `java TimeoutMessagingTemplateDemo.java`. Expected output: `Reply: null after ~1000ms` — with no service ever consuming the request, `sendAndReceive` waits out its configured timeout and returns `null` rather than blocking indefinitely.

### Level 3 — Advanced

`MessagingTemplate` also offers `convertSendAndReceive`, which accepts and returns plain Java objects instead of `Message` wrappers, using a configured `MessageConverter` — convenient when the caller only cares about payloads, and doesn't want to build/unwrap `Message` objects at every call site, while still getting timeout and correlation handling underneath.

```java
// ConvertSendAndReceiveDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.MessageBuilder;

public class ConvertSendAndReceiveDemo {
    record ComputeRequest(int value) {}
    record ComputeResult(int doubled) {}

    public static void main(String[] args) {
        QueueChannel requestChannel = new QueueChannel();

        Thread service = new Thread(() -> {
            Message<?> request = requestChannel.receive();
            ComputeRequest req = (ComputeRequest) request.getPayload();
            MessageChannel replyChannel = (MessageChannel) request.getHeaders().getReplyChannel();
            replyChannel.send(MessageBuilder.withPayload(new ComputeResult(req.value() * 2)).build());
        });
        service.start();

        MessagingTemplate template = new MessagingTemplate();
        template.setDefaultChannel(requestChannel);
        template.setReceiveTimeout(2000);

        // convertSendAndReceive: caller works with plain objects, not Message wrappers
        ComputeResult result = (ComputeResult) template.convertSendAndReceive(new ComputeRequest(21), ComputeResult.class);
        System.out.println("Doubled result: " + result.doubled()); // 42
    }
}
```

How to run: `java ConvertSendAndReceiveDemo.java`. Expected output: `Doubled result: 42` — the caller never touched a `Message` object directly; `convertSendAndReceive` wrapped the `ComputeRequest` payload into a message, handled the reply-channel plumbing, and unwrapped the returned `Message`'s payload back into a plain `ComputeResult`.

## 6. Walkthrough

Tracing `BasicMessagingTemplateDemo` in execution order:

1. The background `service` thread calls `requestChannel.receive()`, which blocks since nothing has been sent yet.
2. `template.sendAndReceive(MessageBuilder.withPayload(21).build())` is called on the main thread. Internally, `MessagingTemplate` creates a temporary, anonymous reply channel and builds an outgoing `Message` from the given payload with a `replyChannel` header pointing at that temporary channel.
3. The template sends this enriched message to its configured default channel (`requestChannel`) — this is exactly the `send()` call from card 0010's `QueueChannel`, just assembled and issued for you.
4. `requestChannel.receive()` on the service thread unblocks, returning the message with `payload=21` and the `replyChannel` header set to the temporary channel instance.
5. The service reads `request.getHeaders().getReplyChannel()`, casts it back to a `MessageChannel`, computes `21 * 2 = 42`, and sends a new message carrying `42` directly to that temporary reply channel.
6. Back in `sendAndReceive`, the template has been blocked on `receive()` against that same temporary reply channel; the service's send unblocks it, returning the reply message, whose payload (`42`) is printed.

```
main:    sendAndReceive(21)
           -> builds Message{payload=21, replyChannel=tempChannel}
           -> requestChannel.send(...)
           -> tempChannel.receive() [BLOCKS]

service: requestChannel.receive() -> gets Message{payload=21, replyChannel=tempChannel}
           -> computes 42
           -> tempChannel.send(Message{payload=42})

main:    tempChannel.receive() unblocks -> returns Message{payload=42}
```

## 7. Gotchas & takeaways

> `sendAndReceive` without a configured `receiveTimeout` blocks indefinitely if nothing ever replies — exactly the same hazard as an untimed `RendezvousChannel.receive()` (card 0012). Always set a sensible `receiveTimeout` in production code paths, and explicitly handle the `null` return that signals a timeout, since a `NullPointerException` on the reply is a very common bug when this is overlooked.

- `MessagingTemplate` wraps raw `MessageChannel` `send()`/`receive()` with a friendlier API, most notably `sendAndReceive` for synchronous request/reply exchanges with automatic reply-channel correlation.
- Configure a `defaultChannel` and `receiveTimeout` once on the template rather than repeating destination and timeout logic at every call site.
- `sendAndReceive` returns `null` on timeout rather than throwing — always check for `null` before using the reply.
- `convertSendAndReceive` (and `convertAndSend`) let callers work with plain payload objects instead of manually building and unwrapping `Message` instances, using a configured `MessageConverter`.
- `MessagingTemplate` is a thin convenience layer over the same channel primitives covered elsewhere in this section — understanding `QueueChannel` (card 0010) and reply-channel headers makes it clear exactly what the template is doing for you under the hood, rather than it feeling like unexplained magic.
