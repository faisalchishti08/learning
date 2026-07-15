---
card: spring-integration
gi: 14
slug: fluxmessagechannel-reactive
title: "FluxMessageChannel (reactive)"
---

## 1. What it is

`FluxMessageChannel` is a `MessageChannel` implementation that bridges Spring Integration's imperative `send()`/subscribe model to Project Reactor: internally, sent messages are published onto a `Flux`, and the channel itself implements `Publisher<Message<?>>`, so it can be subscribed to directly by reactive consumers (or wired into a `Flux` pipeline via `Flux.from(channel)`). Unlike `ExecutorChannel` (card 0013), which gives you pool-based concurrency, `FluxMessageChannel` gives you Reactive Streams semantics — including backpressure, where a slow subscriber can signal upstream to slow down rather than being overwhelmed.

## 2. Why & when

You reach for `FluxMessageChannel` specifically when a flow needs genuine Reactive Streams backpressure or interoperates with reactive code elsewhere in the application:

- **A downstream reactive consumer is slower than the producer, and you want real backpressure** — the consumer's `request(n)` signals control how much the producer sends, rather than the producer racing ahead and either blocking (`RendezvousChannel`, card 0012) or buffering unboundedly (an unbounded `QueueChannel`, card 0010).
- **The rest of the flow is already built with Project Reactor** (`Flux`/`Mono`, WebFlux handlers, R2DBC repositories) and you want the messaging layer to compose naturally with that, instead of crossing an imperative/reactive boundary awkwardly.
- **You want multiple subscribers to receive the same stream of messages** with each subscriber's own pace respected — a natural fit for reactive multicast semantics that other channel types don't provide out of the box.

## 3. Core concept

Think of `FluxMessageChannel` like a live news ticker with a "pace yourself" contract, rather than a firehose. A subscriber to the ticker doesn't get force-fed every headline the instant it's published (`DirectChannel`, card 0008); it explicitly asks for "the next 3 headlines, please," consumes them, and only then asks for more — the producer respects that request rate rather than overwhelming a reader who's still catching up.

```java
FluxMessageChannel channel = new FluxMessageChannel();

Flux.from(channel)
    .doOnNext(message -> System.out.println("Received: " + message.getPayload()))
    .subscribe();

channel.send(MessageBuilder.withPayload("order-1").build());
channel.send(MessageBuilder.withPayload("order-2").build());
```

`Flux.from(channel)` turns the channel into a standard reactive source; the subscriber (here, a simple `.subscribe()` with unbounded demand) receives messages as they're published, but a subscriber with explicit, limited demand would only receive as many as it has requested at any given time.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FluxMessageChannel: producer sends onto a Flux; a reactive subscriber controls flow via request(n), with backpressure signaled upstream">
  <rect x="20" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">producer: send()</text>

  <line x1="150" y1="95" x2="220" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#f1)"/>
  <text x="185" y="82" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">onNext</text>

  <rect x="230" y="60" width="180" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">FluxMessageChannel</text>
  <text x="320" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Publisher&lt;Message&lt;?&gt;&gt;</text>
  <text x="320" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Reactive Streams</text>

  <line x1="410" y1="95" x2="480" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#f2)"/>
  <text x="445" y="82" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">onNext</text>
  <line x1="480" y1="120" x2="410" y2="120" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#f3)"/>
  <text x="445" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">request(n)</text>

  <rect x="490" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">subscriber</text>

  <defs>
    <marker id="f1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="f2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="f3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The subscriber's `request(n)` signal flows upstream, controlling how many messages the channel emits — genuine backpressure, not just buffering.

## 5. Runnable example

The scenario: an order-event producer feeding a reactive subscriber, starting with a basic unbounded subscription, then a subscriber with explicit limited demand to observe backpressure, and finally two independent subscribers each consuming at their own pace.

### Level 1 — Basic

```java
// BasicFluxChannelDemo.java
import org.springframework.integration.channel.FluxMessageChannel;
import org.springframework.messaging.support.MessageBuilder;
import reactor.core.publisher.Flux;

public class BasicFluxChannelDemo {
    public static void main(String[] args) throws InterruptedException {
        FluxMessageChannel channel = new FluxMessageChannel();

        Flux.from(channel)
            .doOnNext(message -> System.out.println("Received: " + message.getPayload()))
            .subscribe(); // unbounded demand — takes everything as fast as it's published

        channel.send(MessageBuilder.withPayload("order-1").build());
        channel.send(MessageBuilder.withPayload("order-2").build());
        Thread.sleep(100); // let the async subscription process before main exits
    }
}
```

How to run: `java BasicFluxChannelDemo.java`. Expected output: `Received: order-1` then `Received: order-2` — the subscriber, having requested unbounded demand, receives each message essentially as soon as it's sent.

### Level 2 — Intermediate

A subscriber can request a limited number of items at a time instead of unbounded demand — `FluxMessageChannel` then genuinely holds back further emissions until more demand is signaled, rather than buffering everything eagerly.

```java
// LimitedDemandDemo.java
import org.springframework.integration.channel.FluxMessageChannel;
import org.springframework.messaging.support.MessageBuilder;
import reactor.core.publisher.Flux;
import org.reactivestreams.Subscription;

public class LimitedDemandDemo {
    public static void main(String[] args) throws InterruptedException {
        FluxMessageChannel channel = new FluxMessageChannel();

        Flux.from(channel).subscribe(new java.util.function.Consumer<>() {
            Subscription sub;
            public void accept(Object o) { /* unused generic hook, real subscriber below */ }
        });

        // A subscriber requesting exactly 1 item at a time, printing before requesting more
        Flux.from(channel).subscribe(new org.reactivestreams.Subscriber<org.springframework.messaging.Message<?>>() {
            Subscription subscription;
            public void onSubscribe(Subscription s) { this.subscription = s; s.request(1); }
            public void onNext(org.springframework.messaging.Message<?> m) {
                System.out.println("Consumed: " + m.getPayload() + " — requesting 1 more");
                subscription.request(1);
            }
            public void onError(Throwable t) {}
            public void onComplete() {}
        });

        for (int i = 1; i <= 3; i++) {
            channel.send(MessageBuilder.withPayload("order-" + i).build());
            System.out.println("Sent order-" + i);
        }
        Thread.sleep(100);
    }
}
```

How to run: `java LimitedDemandDemo.java`. Expected output interleaves `Sent order-N` with `Consumed: order-N — requesting 1 more`, each `send()` effectively gated by the subscriber's one-at-a-time `request(1)` calls — demonstrating demand-driven flow rather than the producer racing ahead unconditionally.

### Level 3 — Advanced

Multiple independent subscribers can each consume from the same `FluxMessageChannel` at their own pace — one fast, one artificially slow — with each subscription's backpressure state tracked separately, showing the channel genuinely multicasts rather than round-robining a single stream.

```java
// MultiSubscriberDemo.java
import org.springframework.integration.channel.FluxMessageChannel;
import org.springframework.messaging.support.MessageBuilder;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;
import java.util.concurrent.CountDownLatch;

public class MultiSubscriberDemo {
    public static void main(String[] args) throws InterruptedException {
        FluxMessageChannel channel = new FluxMessageChannel();
        CountDownLatch latch = new CountDownLatch(6); // 3 messages x 2 subscribers

        Flux.from(channel)
            .publishOn(Schedulers.boundedElastic())
            .subscribe(m -> {
                System.out.println("Fast subscriber got: " + m.getPayload());
                latch.countDown();
            });

        Flux.from(channel)
            .publishOn(Schedulers.boundedElastic())
            .delayElements(java.time.Duration.ofMillis(150)) // artificially slow
            .subscribe(m -> {
                System.out.println("Slow subscriber got: " + m.getPayload());
                latch.countDown();
            });

        for (int i = 1; i <= 3; i++) {
            channel.send(MessageBuilder.withPayload("order-" + i).build());
        }
        latch.await();
        System.out.println("Both subscribers processed all messages, at their own pace");
    }
}
```

How to run: `java MultiSubscriberDemo.java`. Expected output: `Fast subscriber got: order-N` lines appear quickly for all three messages, while `Slow subscriber got: order-N` lines trickle in roughly 150ms apart — both subscribers eventually see all three messages, but the slow one's own `delayElements` backpressure does not hold back the fast one, proving each subscription is independently paced.

## 6. Walkthrough

Tracing `LimitedDemandDemo` in execution order:

1. The `Subscriber` implementation's `onSubscribe(Subscription s)` is invoked by `FluxMessageChannel` as soon as it subscribes, and it immediately calls `s.request(1)` — signaling "I am ready for exactly one item," not "send me everything."
2. `channel.send(order-1)` publishes the message onto the underlying `Flux`'s sink; because the subscriber currently has outstanding demand of 1, `onNext` fires immediately with `order-1`.
3. Inside `onNext`, the handler prints the consumption message and calls `subscription.request(1)` again — replenishing demand by exactly one before processing the next item, which is the core backpressure discipline: never request more than you're ready to handle.
4. `channel.send(order-2)` publishes the second message; since demand was just replenished to 1, it flows through to `onNext` right away.
5. This request-then-consume cycle repeats for `order-3`.
6. If a `send()` ever happened while outstanding demand were 0 (e.g., a subscriber that was slow to call `request` again), `FluxMessageChannel`'s underlying sink would hold that emission until demand is signaled — this is the actual backpressure mechanism, distinguishing it from every other channel type in this section, which have no concept of subscriber-driven demand at all.

```
subscriber: onSubscribe -> request(1)
send(order-1) -> onNext(order-1) -> [print] -> request(1)
send(order-2) -> onNext(order-2) -> [print] -> request(1)
send(order-3) -> onNext(order-3) -> [print] -> request(1)
```

## 7. Gotchas & takeaways

> `FluxMessageChannel.send()` is still a synchronous, imperative method from the caller's point of view — it does not return a `Mono<Boolean>` or otherwise let the caller observe backpressure directly. If every current subscriber's demand is exhausted, the underlying sink typically buffers the emission rather than blocking `send()`, so relying on `send()` itself to feel "backpressured" is a common misunderstanding; the backpressure operates on the reactive (subscriber) side of the channel, not the imperative (`send()`) side.

- `FluxMessageChannel` bridges imperative `send()` calls into a `Publisher<Message<?>>`, giving genuine Reactive Streams backpressure to whatever `Flux`/`Mono` pipeline subscribes to it.
- Use it when a downstream reactive consumer needs real demand-driven flow control, or when integrating with an existing Project Reactor / WebFlux codebase.
- Multiple subscribers each get their own independent demand and pacing — one slow subscriber does not throttle a fast one, unlike a single shared queue.
- `send()` itself remains imperative and does not block on subscriber demand the way one might expect from a "reactive" channel — backpressure is visible on the `Flux` side, not the `send()` side.
- Because it depends on Project Reactor, `FluxMessageChannel` pulls in that dependency; reach for `ExecutorChannel` (card 0013) or `QueueChannel` (card 0010) instead if the rest of the application has no other reactive dependencies.
