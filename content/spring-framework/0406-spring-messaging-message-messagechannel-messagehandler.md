---
card: spring-framework
gi: 406
slug: spring-messaging-message-messagechannel-messagehandler
title: "Spring Messaging (Message, MessageChannel, MessageHandler)"
---

## 1. What it is

Spring Messaging is a small, generic set of abstractions — `Message<T>` (a payload plus headers), `MessageChannel` (a pipe you send messages into), and `MessageHandler` (something that receives and processes messages from a channel) — that model asynchronous, message-based communication independent of any specific transport. It's the shared foundation underneath Spring's JMS support, WebSocket/STOMP messaging, and Spring Integration, so learning it once pays off across all of them.

```java
Message<String> message = MessageBuilder.withPayload("order-42")
        .setHeader("priority", "high")
        .build();

MessageChannel channel = new DirectChannel();
channel.send(message);
```

## 2. Why & when

JMS has its own `Message`/`Destination` types; WebSocket/STOMP has its own frame format; a hypothetical future transport would have yet another. Spring Messaging exists to give application code (and the framework's own higher-level features) one consistent vocabulary for "a piece of data plus metadata, moving through a pipe, processed by a handler" — regardless of what's actually carrying it underneath. `@MessageMapping`-annotated STOMP controllers, `@JmsListener` methods (which convert to/from JMS `Message`s but expose a compatible mental model), and Spring Integration pipelines all speak this same core vocabulary.

Understanding this layer matters when:

- You're building WebSocket/STOMP messaging (the next cards in this section) — `@MessageMapping` methods receive `Message<T>`-shaped data, and understanding `Message`/`MessageChannel` demystifies what's actually flowing through the annotated methods.
- You want to decouple producers and consumers *within a single application* (not across a network) — a `MessageChannel` can be a simple in-process pipe connecting two parts of your code without any broker at all.
- You're evaluating or working with Spring Integration, which builds its entire enterprise-integration-pattern toolkit (routers, transformers, splitters, aggregators) directly on top of these same three abstractions.

## 3. Core concept

```
       MessageBuilder.withPayload(data).setHeader(...).build()
                          |
                          v
                     Message<T>            <- payload + headers, immutable
                          |
                          v
    channel.send(message)  ---->  MessageChannel   (the pipe)
                                        |
                    +-------------------+-------------------+
                    |                                       |
            SubscribableChannel                     PollableChannel
            (pushes to subscribers                  (subscribers pull
             immediately)                             on their own schedule)
                    |
                    v
              MessageHandler.handleMessage(message)
```

`MessageChannel` is deliberately abstract about *how* delivery happens — a `DirectChannel` delivers synchronously on the sender's thread, an `ExecutorChannel` delivers asynchronously on a thread pool, and specialized channels bridge to JMS, WebSocket sessions, or other real transports.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Message flows into a MessageChannel and out to a subscribed MessageHandler">
  <rect x="10" y="70" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Message&lt;T&gt;</text>

  <rect x="230" y="70" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageChannel</text>

  <rect x="450" y="70" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageHandler</text>

  <line x1="150" y1="95" x2="225" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="370" y1="95" x2="445" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Sender, channel, and handler are three independently swappable pieces — the sender never talks to the handler directly.

## 5. Runnable example

### Level 1 — Basic

A `DirectChannel` with one subscribed `MessageHandler`, showing synchronous, in-process delivery.

```java
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageHandler;
import org.springframework.messaging.MessagingException;
import org.springframework.messaging.support.GenericMessage;
import org.springframework.integration.channel.DirectChannel;

public class MessagingBasic {

    public static void main(String[] args) {
        DirectChannel channel = new DirectChannel();

        MessageHandler handler = new MessageHandler() {
            @Override
            public void handleMessage(Message<?> message) throws MessagingException {
                System.out.println("Handled: " + message.getPayload()
                        + " headers=" + message.getHeaders().get("priority"));
            }
        };
        channel.subscribe(handler);

        Message<String> message = new GenericMessage<>("order-42",
                java.util.Map.of("priority", "high"));
        channel.send(message);
    }
}
```

How to run: add `spring-messaging` and `spring-integration-core` (for `DirectChannel`) to the classpath, then `java MessagingBasic.java`.

`channel.subscribe(handler)` registers the handler as a listener; `channel.send(message)` delivers the message synchronously — `handleMessage` runs on the same thread that called `send`, and `send` doesn't return until it's done, which is the defining trait of a `DirectChannel`.

### Level 2 — Intermediate

Compare `DirectChannel` (synchronous) against `ExecutorChannel` (asynchronous) to see the threading difference concretely, and use `MessageBuilder` for more realistic message construction.

```java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.channel.ExecutorChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.MessageBuilder;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;

public class MessagingIntermediate {

    public static void main(String[] args) throws InterruptedException {
        System.out.println("main thread: " + Thread.currentThread().getName());

        DirectChannel directChannel = new DirectChannel();
        directChannel.subscribe(message ->
                System.out.println("DirectChannel handled on: " + Thread.currentThread().getName()));

        Message<String> message1 = MessageBuilder.withPayload("sync-message").build();
        directChannel.send(message1); // runs synchronously, same thread as main

        var executor = Executors.newSingleThreadExecutor();
        ExecutorChannel executorChannel = new ExecutorChannel(executor);
        CountDownLatch done = new CountDownLatch(1);
        executorChannel.subscribe(message -> {
            System.out.println("ExecutorChannel handled on: " + Thread.currentThread().getName());
            done.countDown();
        });

        Message<String> message2 = MessageBuilder.withPayload("async-message").build();
        executorChannel.send(message2); // dispatched to the executor's thread
        done.await();

        executor.shutdown();
    }
}
```

How to run: `java MessagingIntermediate.java` (same classpath as Level 1).

The `DirectChannel` handler prints the same thread name as `main`; the `ExecutorChannel` handler prints a different thread name (the executor's worker thread), because `ExecutorChannel.send(...)` submits the dispatch to the given `Executor` and returns immediately rather than blocking for the handler to finish — this is the seam Spring Integration and WebSocket message broker relay use to decouple producer and consumer timing.

### Level 3 — Advanced

A more realistic pipeline: an interceptor that logs and can reject messages before they reach the handler, multiple handlers reacting to the same channel, and error handling for a handler that throws.

```java
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.messaging.support.ExecutorSubscribableChannel;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MessagingAdvanced {

    public static void main(String[] args) throws InterruptedException {
        ExecutorService executor = Executors.newFixedThreadPool(2);
        var channel = new ExecutorSubscribableChannel(executor);

        channel.addInterceptor(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                Object priority = message.getHeaders().get("priority");
                if ("low".equals(priority)) {
                    System.out.println("Interceptor rejected low-priority message: " + message.getPayload());
                    return null; // returning null from preSend blocks delivery entirely
                }
                System.out.println("Interceptor allowed: " + message.getPayload());
                return message;
            }

            @Override
            public void afterSendCompletion(Message<?> message, MessageChannel channel, boolean sent, Exception ex) {
                if (ex != null) {
                    System.out.println("Delivery failed for " + message.getPayload() + ": " + ex.getMessage());
                }
            }
        });

        channel.subscribe(message -> {
            System.out.println("Audit handler logging: " + message.getPayload());
        });
        channel.subscribe(message -> {
            if ("bad-order".equals(message.getPayload())) {
                throw new IllegalStateException("Cannot process bad-order");
            }
            System.out.println("Fulfillment handler processing: " + message.getPayload());
        });

        channel.send(MessageBuilder.withPayload("order-1").setHeader("priority", "high").build());
        channel.send(MessageBuilder.withPayload("order-2").setHeader("priority", "low").build());
        channel.send(MessageBuilder.withPayload("bad-order").setHeader("priority", "high").build());

        Thread.sleep(500); // demo-only: allow async handlers to finish
        executor.shutdown();
    }
}
```

How to run: add `spring-messaging` and `spring-integration-core` to the classpath, then `java MessagingAdvanced.java`.

The `ChannelInterceptor`'s `preSend` runs before *any* subscriber sees the message and can veto delivery entirely by returning `null` — the low-priority `"order-2"` never reaches either handler. Both remaining subscribers (`"Audit handler"` and `"Fulfillment handler"`) receive every message that passes the interceptor, since this is a multi-subscriber channel — one message, multiple independent handlers, each processing it for a different purpose (auditing vs. fulfillment).

## 6. Walkthrough

Trace the delivery of `"bad-order"` through `MessagingAdvanced.main`:

1. **Send call.** `channel.send(MessageBuilder.withPayload("bad-order").setHeader("priority", "high").build())` constructs an immutable `Message<String>` and hands it to the `ExecutorSubscribableChannel`.
2. **Interceptor `preSend`.** Before any subscriber is notified, the registered `ChannelInterceptor.preSend` runs: the `priority` header is `"high"`, not `"low"`, so it prints `"Interceptor allowed: bad-order"` and returns the message unchanged, letting delivery proceed.
3. **Dispatch to subscribers.** Because this is an `ExecutorSubscribableChannel`, each subscribed `MessageHandler` is invoked asynchronously via the configured thread pool — both the audit handler and the fulfillment handler are scheduled to run, potentially on different pool threads.
4. **Audit handler runs cleanly.** It prints `"Audit handler logging: bad-order"` and returns normally — this handler doesn't know or care what `"bad-order"` means, it just logs every message it sees.
5. **Fulfillment handler throws.** This handler specifically checks for the `"bad-order"` payload and throws `IllegalStateException("Cannot process bad-order")`.
6. **Interceptor `afterSendCompletion`.** Because delivery to at least one subscriber failed, the channel's `afterSendCompletion` callback fires with the exception attached, printing `"Delivery failed for bad-order: Cannot process bad-order"` — this is the channel's mechanism for surfacing handler failures back to code that cares, without the failure silently disappearing into the async dispatch.
7. **Independence of subscribers.** Critically, the audit handler's successful processing (step 4) is unaffected by the fulfillment handler's failure (step 5) — each subscriber operates independently, which is exactly the point of a publish-subscribe-style channel: one producer, several independent consumers, each with their own success/failure outcome.

```
send("bad-order", priority=high)
   -> preSend: priority != low -> allowed
   -> dispatch to both subscribers (async, thread pool)
        audit handler:       logs "bad-order" -> success
        fulfillment handler: throws IllegalStateException
   -> afterSendCompletion: exception recorded, printed
```

## 7. Gotchas & takeaways

> Gotcha: on a multi-subscriber channel, one handler throwing does not stop other handlers from running or roll back their side effects — each subscriber's success or failure is independent, which is correct for genuinely independent concerns (logging vs. fulfillment) but a trap if you assumed message processing across handlers was atomic or transactional. If you need all-or-nothing semantics across multiple processing steps, you need explicit transaction coordination, not just a shared channel.

- `Message`, `MessageChannel`, and `MessageHandler` are the shared vocabulary underneath Spring's JMS support, WebSocket/STOMP messaging, and Spring Integration — understanding them once pays off in all three areas.
- `DirectChannel` delivers synchronously on the sender's thread; `ExecutorChannel`/`ExecutorSubscribableChannel` dispatch asynchronously via a thread pool — pick based on whether the sender should block until processing completes.
- `ChannelInterceptor.preSend` returning `null` is the standard way to veto message delivery before any handler sees it — useful for validation, filtering, or authorization checks applied uniformly to every message on a channel.
- A channel with multiple subscribers delivers the same message to each independently; a failure in one subscriber does not affect the others, so design each handler to be self-contained rather than assuming shared transactional guarantees.
