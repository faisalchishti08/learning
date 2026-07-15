---
card: spring-integration
gi: 17
slug: scoped-channels
title: "Scoped channels"
---

## 1. What it is

A scoped channel is an ordinary channel bean (`DirectChannel`, `QueueChannel`, or any other `MessageChannel` implementation) declared with a Spring bean scope other than the default singleton — most commonly `thread`, via Spring Integration's `PseudoTransactionalMessageSource`-adjacent scoping support, but conceptually any Spring scope (`request`, `session`, a custom scope) applies the same way. Instead of one shared channel instance serving every message flow, Spring resolves a distinct channel instance per scope boundary (e.g., one per thread, one per HTTP request).

## 2. Why & when

You reach for a scoped channel specifically when different concurrent flows need channel-local isolation rather than a single shared instance:

- **State attached to a channel (interceptors that accumulate context, thread-local-style correlation) needs to be genuinely isolated per thread**, so that concurrent flows on the same logical channel name don't see or interfere with each other's in-flight data.
- **A flow uses thread-bound resources** (e.g., a thread-scoped `QueueChannel` used purely as a hand-off point within a single thread's processing pipeline) where sharing one instance across threads would be actively wrong, not just inefficient.
- **You're testing or reasoning about a flow in isolation** and want each test (or each request) to get a fresh channel with no possibility of leftover messages or interceptor state bleeding in from a previous run — scoping makes that isolation structural rather than something you manage by hand with setup/teardown.

## 3. Core concept

Think of a scoped channel like a hotel room key rather than a shared office mailbox. A singleton channel is one mailbox everyone drops mail into and everyone checks — fine when that's genuinely the intent, but a nightmare if two people's private correspondence needs to stay separate. A thread-scoped channel is like each guest getting their own room: ask for "the channel" from two different threads and you get two different, isolated instances, even though the bean definition (the "room type") is identical.

```java
@Bean
@Scope(value = "thread", proxyMode = ScopedProxyMode.TARGET_CLASS)
public MessageChannel workChannel() {
    return new QueueChannel();
}
```

Every thread that resolves `workChannel()` through the Spring context gets its own private `QueueChannel` instance; a message sent to it on thread A is invisible to thread B, even though both reference "the same bean" by name.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scoped channel: two threads resolving the same bean name get separate, isolated channel instances instead of one shared singleton">
  <rect x="20" y="30" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">thread A</text>

  <rect x="20" y="130" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="153" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">thread B</text>

  <text x="280" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">bean name: "workChannel"</text>

  <line x1="160" y1="50" x2="230" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#s1)"/>
  <line x1="160" y1="150" x2="230" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#s1)"/>

  <rect x="240" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance A (own queue)</text>

  <rect x="240" y="130" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="153" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance B (own queue)</text>

  <text x="490" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no shared state between them</text>

  <defs>
    <marker id="s1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Same bean name, two threads, two genuinely separate channel instances — messages sent on one are invisible on the other.

## 5. Runnable example

The scenario: a per-thread work channel used as an isolated hand-off point within each thread's own pipeline, starting with a basic singleton-vs-scoped comparison, then concurrent threads proving isolation, and finally a scoped channel combined with a thread-local correlation interceptor.

### Level 1 — Basic

```java
// SingletonVsThreadLocalDemo.java
// Illustrates the core idea directly with ThreadLocal, since a full Spring ApplicationContext
// is heavier than needed to demonstrate the underlying mechanism a scoped bean relies on.
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.support.MessageBuilder;

public class SingletonVsThreadLocalDemo {
    static final QueueChannel SHARED = new QueueChannel(); // like a singleton-scoped channel bean
    static final ThreadLocal<QueueChannel> SCOPED = ThreadLocal.withInitial(QueueChannel::new); // like thread scope

    public static void main(String[] args) {
        SHARED.send(MessageBuilder.withPayload("from-main-shared").build());
        System.out.println("Shared channel size after send from main: " + SHARED.getQueueSize());

        SCOPED.get().send(MessageBuilder.withPayload("from-main-scoped").build());
        System.out.println("Scoped (this thread's) channel size: " + SCOPED.get().getQueueSize());
    }
}
```

How to run: `java SingletonVsThreadLocalDemo.java`. Expected output: both sizes print `1` here (single thread), establishing the baseline before Level 2 shows the divergence across threads.

### Level 2 — Intermediate

Two concurrent threads sending to the shared channel accumulate into the *same* queue (visible to both), while two threads sending to their own `ThreadLocal`-backed (scoped-style) channel each see only their own message — the isolation a real thread-scoped bean provides automatically via Spring's scoping infrastructure.

```java
// ConcurrentIsolationDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.CountDownLatch;

public class ConcurrentIsolationDemo {
    static final QueueChannel SHARED = new QueueChannel();
    static final ThreadLocal<QueueChannel> SCOPED = ThreadLocal.withInitial(QueueChannel::new);

    public static void main(String[] args) throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(2);

        Runnable work = () -> {
            SHARED.send(MessageBuilder.withPayload(Thread.currentThread().getName() + "-shared").build());
            SCOPED.get().send(MessageBuilder.withPayload(Thread.currentThread().getName() + "-scoped").build());
            System.out.println(Thread.currentThread().getName() + " sees SCOPED size=" + SCOPED.get().getQueueSize());
            latch.countDown();
        };

        new Thread(work, "worker-1").start();
        new Thread(work, "worker-2").start();
        latch.await();

        System.out.println("SHARED channel ended up with " + SHARED.getQueueSize() + " messages (both threads' sends accumulated)");
    }
}
```

How to run: `java ConcurrentIsolationDemo.java`. Expected output: both `worker-1` and `worker-2` print `SCOPED size=1` (each only ever sees its own single message), while the final line reports `SHARED channel ended up with 2 messages` — proving the shared channel accumulated both threads' sends, but each thread's scoped channel stayed isolated to just its own.

### Level 3 — Advanced

Combining a thread-scoped channel with a `ChannelInterceptor` (card 0015) that stamps a thread-local correlation ID shows the realistic use case: per-thread pipeline state (correlation context) that must never leak across threads, backed by the same isolation mechanism.

```java
// ScopedChannelWithCorrelationDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.CountDownLatch;
import java.util.UUID;

public class ScopedChannelWithCorrelationDemo {
    static final ThreadLocal<QueueChannel> SCOPED = ThreadLocal.withInitial(() -> {
        QueueChannel channel = new QueueChannel();
        String threadCorrelationId = UUID.randomUUID().toString().substring(0, 8);
        channel.addInterceptor(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel ch) {
                return MessageBuilder.fromMessage(message).setHeader("correlationId", threadCorrelationId).build();
            }
        });
        return channel;
    });

    public static void main(String[] args) throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(2);
        Runnable work = () -> {
            QueueChannel channel = SCOPED.get(); // first access initializes THIS thread's channel + correlation ID
            channel.send(MessageBuilder.withPayload("step-1").build());
            channel.send(MessageBuilder.withPayload("step-2").build());

            Message<?> m1 = channel.receive();
            Message<?> m2 = channel.receive();
            System.out.println(Thread.currentThread().getName() + ": both messages share correlationId="
                + m1.getHeaders().get("correlationId") + " == " + m2.getHeaders().get("correlationId"));
            latch.countDown();
        };
        new Thread(work, "worker-A").start();
        new Thread(work, "worker-B").start();
        latch.await();
    }
}
```

How to run: `java ScopedChannelWithCorrelationDemo.java`. Expected output: `worker-A` and `worker-B` each print their two messages sharing the *same* correlation ID as each other, but that ID differs between the two threads — every message within one thread's scoped channel shares that thread's correlation context automatically, with zero risk of one thread's messages picking up another thread's ID.

## 6. Walkthrough

Tracing `ScopedChannelWithCorrelationDemo` in execution order:

1. Each worker thread's first call to `SCOPED.get()` triggers the `ThreadLocal`'s initializer (analogous to Spring instantiating a fresh scoped bean on first access within that scope): a new `QueueChannel` is created, a random correlation ID is generated for that thread, and an interceptor closing over that specific ID is attached.
2. `channel.send("step-1")` triggers the interceptor's `preSend`, which stamps the thread's correlation ID onto the message before it's enqueued — this happens independently on each thread, using each thread's own ID.
3. `channel.send("step-2")` on the same thread stamps the same correlation ID again, since it's reading from the same closed-over `threadCorrelationId` variable tied to that thread's channel instance.
4. `channel.receive()` twice pulls both messages back off that thread's own queue — this is thread-local state, so there's no possibility of `worker-A` accidentally receiving a message `worker-B` sent.
5. Each thread prints confirmation that its own two messages share one correlation ID, and printing both threads' output side by side shows the IDs differ between threads — direct evidence of correct isolation.
6. In a real Spring application, this exact behavior would come from declaring the channel bean with `@Scope("thread")` (or a custom scope) instead of manually managing a `ThreadLocal` — the `ThreadLocal` here stands in for what Spring's scoping infrastructure does automatically via scoped proxies.

```
worker-A: SCOPED.get() -> new QueueChannel + id=aaaa1111 (first access, this thread only)
worker-A: send(step-1) -> stamped id=aaaa1111
worker-A: send(step-2) -> stamped id=aaaa1111

worker-B: SCOPED.get() -> new QueueChannel + id=bbbb2222 (separate instance, separate thread)
worker-B: send(step-1) -> stamped id=bbbb2222
worker-B: send(step-2) -> stamped id=bbbb2222
```

## 7. Gotchas & takeaways

> A thread-scoped channel bean only stays isolated as long as the *same* logical unit of work stays on the *same* thread. The moment a flow hops threads — dispatch via an `ExecutorChannel` (card 0013), an async `@Async` call, or a reactive `Flux` operator that switches schedulers — the new thread resolves its *own* fresh scoped instance, and any state accumulated on the original thread's channel is invisible from there on. Thread-scoped channels and asynchronous dispatch are often a mismatch; prefer explicit correlation headers (not scope) once a flow can cross threads.

- A scoped channel resolves a distinct instance per scope boundary (commonly per-thread) rather than sharing one singleton instance across every caller.
- Use scoping when channel-local state (interceptor context, thread-bound resources) must stay genuinely isolated between concurrent flows, not merely conceptually separate.
- Isolation is structural, not something you manage manually with setup/teardown per flow or test — the scoping mechanism guarantees it.
- Thread scoping breaks down the moment a flow crosses threads (async dispatch, reactive scheduler switches); it only isolates work that stays on one thread start to finish.
- In real Spring configuration, this is declared via `@Scope(value = "thread", proxyMode = ScopedProxyMode.TARGET_CLASS)` (or another scope) on the channel `@Bean` method, backed by Spring's general bean-scoping infrastructure rather than anything channel-specific.
