---
card: microservices
gi: 115
slug: message-channels
title: "Message channels"
---

## 1. What it is

A message channel is the named, addressable path a message travels between producer and consumer inside a [message broker](0112-message-broker-message-oriented-middleware.md) — the queue or topic itself, as a first-class thing with its own identity, configuration, and lifecycle, separate from the messages that happen to flow through it at any given moment.

## 2. Why & when

Once a system has more than one kind of event, "just send it to the broker" is not specific enough — the broker needs to know *which* channel a message belongs to, and consumers need to know *which* channel to listen on, so that unrelated messages don't get mixed together. Thinking of a channel as its own named entity (with its own name, its own delivery semantics, its own retention policy) is what makes both [point-to-point](0113-point-to-point-queue-messaging.md) and [publish/subscribe](0114-publish-subscribe-topic-messaging.md) messaging possible to reason about at all — both patterns are really just different behaviors of a channel.

Design explicit channels — rather than one shared catch-all destination — as soon as a system has more than one distinct kind of message that different consumers care about differently. This mirrors how a well-designed [REST API](0076-restful-apis-over-http.md) has more than one endpoint: each channel is a contract about what kind of data flows through it.

## 3. Core concept

A channel is defined by a name and a set of properties: is it point-to-point or publish/subscribe, what is the message format, how long are undelivered messages retained, what happens to a message nobody claims. Producers and consumers agree on a channel's name and contract without needing to know anything about each other.

```java
// two DIFFERENT channels, each with its own name and its own consumers
channels.declare("order-events", ChannelType.TOPIC);
channels.declare("resize-jobs", ChannelType.QUEUE);

channels.send("order-events", orderPlacedEvent);   // fans out to subscribers
channels.send("resize-jobs", resizeJobPayload);     // goes to exactly one worker
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A broker hosts multiple named channels, each with its own type and its own set of producers and consumers, keeping unrelated message flows separate">
  <rect x="20" y="20" width="600" height="160" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="35" y="40" fill="#8b949e" font-size="9" font-family="sans-serif">Broker</text>

  <rect x="50" y="60" width="220" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Channel: order-events</text>
  <text x="160" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">type: TOPIC</text>

  <rect x="50" y="125" width="220" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="145" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Channel: resize-jobs</text>
  <text x="160" y="161" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">type: QUEUE</text>

  <text x="450" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fans out to N subscribers</text>
  <text x="450" y="155" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">delivers to exactly 1 worker</text>

  <line x1="270" y1="85" x2="380" y2="85" stroke="#8b949e" marker-end="url(#arr5)"/>
  <line x1="270" y1="150" x2="380" y2="150" stroke="#8b949e" marker-end="url(#arr5)"/>

  <defs>
    <marker id="arr5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each channel has its own name, type, and delivery behavior, independent of every other channel hosted by the same broker.

## 5. Runnable example

Scenario: a registry of message channels starts as a single hard-coded destination, grows into a proper registry that distinguishes channel types (queue vs. topic) and dispatches accordingly, and finally adds per-channel configuration (retention, max size) enforced at send time.

### Level 1 — Basic

```java
// File: OneChannel.java -- a single hard-coded destination, the thing we outgrow.
import java.util.concurrent.*;

public class OneChannel {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> theOnlyChannel = new LinkedBlockingQueue<>();
        theOnlyChannel.put("OrderPlaced:42");
        theOnlyChannel.put("ResizeImage:photo42.jpg"); // an UNRELATED kind of message, mixed in with the first
        System.out.println("Consumed: " + theOnlyChannel.take());
        System.out.println("Consumed: " + theOnlyChannel.take()); // any consumer here has to figure out what kind this is
    }
}
```

**How to run:** `javac OneChannel.java && java OneChannel` (JDK 17+).

With no notion of separate channels, order events and resize jobs sit in the same queue, forcing every consumer to inspect and filter messages it may not even care about.

### Level 2 — Intermediate

```java
// File: TypedChannelRegistry.java -- named channels, each with a TYPE that determines delivery behavior.
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class TypedChannelRegistry {
    enum ChannelType { QUEUE, TOPIC }

    static class ChannelRegistry {
        record Channel(String name, ChannelType type, BlockingQueue<String> queue, List<Consumer<String>> subscribers) {}
        private final Map<String, Channel> channels = new HashMap<>();

        void declare(String name, ChannelType type) {
            channels.put(name, new Channel(name, type, new LinkedBlockingQueue<>(), new ArrayList<>()));
        }
        void subscribe(String name, Consumer<String> handler) { channels.get(name).subscribers().add(handler); }
        void send(String name, String message) {
            Channel c = channels.get(name);
            if (c.type() == ChannelType.TOPIC) {
                c.subscribers().forEach(s -> s.accept(message)); // fan-out
            } else {
                c.queue().offer(message); // point-to-point: sits until claimed
            }
        }
    }

    public static void main(String[] args) {
        ChannelRegistry registry = new ChannelRegistry();
        registry.declare("order-events", ChannelType.TOPIC);
        registry.declare("resize-jobs", ChannelType.QUEUE);

        registry.subscribe("order-events", msg -> System.out.println("[email] " + msg));
        registry.subscribe("order-events", msg -> System.out.println("[analytics] " + msg));

        registry.send("order-events", "OrderPlaced:42"); // fans out to both subscribers
        registry.send("resize-jobs", "ResizeImage:photo42.jpg"); // just enqueued, no subscribers needed
        System.out.println("resize-jobs queue size: " + registry.channels.get("resize-jobs").queue().size());
    }
}
```

**How to run:** `javac TypedChannelRegistry.java && java TypedChannelRegistry` (JDK 17+).

Each channel's declared `ChannelType` now determines its delivery behavior at `send` time, so order events and resize jobs, though hosted by the same registry, never interfere with each other.

### Level 3 — Advanced

```java
// File: ConfiguredChannels.java -- adds per-channel configuration (max size, retention)
// enforced when a message is sent, modeling real broker channel policies.
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class ConfiguredChannels {
    enum ChannelType { QUEUE, TOPIC }
    record ChannelConfig(ChannelType type, int maxSize) {}

    static class ChannelRegistry {
        record Channel(ChannelConfig config, BlockingQueue<String> queue, List<Consumer<String>> subscribers) {}
        private final Map<String, Channel> channels = new HashMap<>();

        void declare(String name, ChannelConfig config) {
            channels.put(name, new Channel(config, new LinkedBlockingQueue<>(), new ArrayList<>()));
        }
        void subscribe(String name, Consumer<String> handler) { channels.get(name).subscribers().add(handler); }

        boolean send(String name, String message) {
            Channel c = channels.get(name);
            if (c.config().type() == ChannelType.TOPIC) {
                c.subscribers().forEach(s -> s.accept(message));
                return true;
            }
            if (c.queue().size() >= c.config().maxSize()) { // enforce the channel's configured capacity
                System.out.println("REJECTED (channel '" + name + "' full, max=" + c.config().maxSize() + "): " + message);
                return false;
            }
            c.queue().offer(message);
            return true;
        }
    }

    public static void main(String[] args) {
        ChannelRegistry registry = new ChannelRegistry();
        registry.declare("resize-jobs", new ChannelConfig(ChannelType.QUEUE, 2)); // small max size, on purpose

        registry.send("resize-jobs", "ResizeImage:photo42.jpg");
        registry.send("resize-jobs", "ResizeImage:photo43.jpg");
        boolean accepted = registry.send("resize-jobs", "ResizeImage:photo44.jpg"); // exceeds maxSize=2

        System.out.println("Third send accepted: " + accepted);
    }
}
```

**How to run:** `javac ConfiguredChannels.java && java ConfiguredChannels` (JDK 17+).

Expected output:
```
REJECTED (channel 'resize-jobs' full, max=2): ResizeImage:photo44.jpg
Third send accepted: false
```

## 6. Walkthrough

1. **Level 1** — one raw `BlockingQueue` receives both an order event and a resize job with no distinguishing structure, forcing any consumer to parse the string just to know what kind of message it is looking at.
2. **Level 2, declaring channels** — `registry.declare("order-events", TOPIC)` and `registry.declare("resize-jobs", QUEUE)` create two separate `Channel` records, each tagged with its own `ChannelType`, stored under its own name in the registry's map.
3. **Level 2, type-driven dispatch** — `send` checks `c.type()` and branches: a `TOPIC` channel fans the message out to every registered subscriber immediately, while a `QUEUE` channel simply enqueues it for later claiming — the same `send` method, two entirely different delivery behaviors, chosen by the channel's own declared configuration.
4. **Level 2, the observable independence** — `order-events` messages reach both subscribers instantly while `resize-jobs` messages sit in a queue with size 1 afterward, proving the two channels operate under completely separate rules despite sharing one registry.
5. **Level 3, adding configuration** — `ChannelConfig` now carries a `maxSize` alongside the `type`, and `declare` is called with `new ChannelConfig(QUEUE, 2)`, giving the `resize-jobs` channel an explicit, enforced capacity limit.
6. **Level 3, enforcement at send time** — before enqueueing, `send` checks `c.queue().size() >= c.config().maxSize()`; the first two sends succeed and bring the queue to size 2, so the third send hits that check and is rejected, printing a message and returning `false` instead of silently growing the queue without bound.
7. **Why this matters** — real brokers enforce very similar per-channel policies (max queue depth, message TTL, retention period), and treating the channel itself as a configurable, named entity — rather than an anonymous pipe — is what makes those policies possible to declare and reason about independently for each kind of message flowing through the system.

## 7. Gotchas & takeaways

> **Gotcha:** giving every kind of message its own channel is good hygiene, but an unbounded number of ad-hoc channels (one per feature, created dynamically, never cleaned up) becomes its own operational problem — real brokers charge real memory and coordination overhead per channel, so channel creation deserves the same design discipline as endpoint design in a REST API.

- A message channel is the named, addressable path — queue or topic — through which messages of a particular kind flow, with its own type, configuration, and lifecycle.
- Explicit, well-named channels are what make both [point-to-point](0113-point-to-point-queue-messaging.md) and [publish/subscribe](0114-publish-subscribe-topic-messaging.md) delivery practical to reason about at scale, instead of mixing unrelated message kinds into one destination.
- A channel's type (queue vs. topic) determines its delivery semantics; that decision belongs to the channel's declaration, not to individual send calls.
- Real brokers let channels carry their own operational configuration — capacity limits, retention periods, delivery policies — enforced independently per channel.
- Treat channel naming and configuration with the same care as API endpoint design: each channel is a contract between producers and consumers about what flows through it and how.
