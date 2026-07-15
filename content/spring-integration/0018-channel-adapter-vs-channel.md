---
card: spring-integration
gi: 18
slug: channel-adapter-vs-channel
title: "Channel adapter vs channel"
---

## 1. What it is

A channel (cards 0008–0017) is a pipe internal to a Spring Integration flow — messages move through it between endpoints that already speak the framework's `Message`/`MessageChannel` vocabulary. A channel adapter is the boundary component that connects a channel to something *outside* that vocabulary: a file system, a JMS queue, an HTTP endpoint, a database, an email inbox. An inbound channel adapter converts external input into a `Message` and puts it onto a channel; an outbound channel adapter takes a `Message` off a channel and converts it into whatever the external system expects.

## 2. Why & when

Understanding the distinction matters because it tells you where a flow's boundary actually is, and which component to reach for:

- **You need to bring data from outside the messaging system in** — a new file appearing in a directory, a JMS message arriving, a row appearing in a database table — an inbound channel adapter polls or listens for that external event and translates it into a `Message` your internal flow can process.
- **You need to send data from a flow out to something external** — writing a file, publishing to JMS, calling an HTTP endpoint — an outbound channel adapter is the component that performs that side effect, taking a message's payload and doing something with it in the outside world.
- **You're debugging "why isn't my flow receiving anything," and the channel itself is fine** — the channel is just a pipe; if nothing is putting messages onto it, the actual problem is almost always upstream, at an adapter (or its absence), not in the channel.

## 3. Core concept

Think of a channel like the pipes inside a house, and an adapter like the fixtures where those pipes meet the outside world — a tap, a drain, a water meter. The pipe itself (`DirectChannel`, `QueueChannel`, etc.) only ever carries water that's already inside the plumbing system, in the plumbing system's own terms (its `Message` "unit"). A tap (an inbound adapter) is what actually draws water in from the municipal supply and puts it into the house's pipes in the first place; a drain (an outbound adapter) is what takes water out of the pipes and sends it somewhere external. Neither the tap nor the drain is a pipe, and neither pipe segment cares what's connected at either end.

```java
// The CHANNEL is just the pipe:
QueueChannel fileEvents = new QueueChannel();

// An INBOUND adapter (conceptually) watches a directory and puts a Message onto the channel:
// FileReadingMessageSource -> puts File payloads onto fileEvents

// An OUTBOUND adapter (conceptually) takes messages off a channel and writes files:
// FileWritingMessageHandler <- reads from a channel, writes to disk

// The channel itself has NO idea whether its messages came from a file, HTTP, or a test like this:
fileEvents.send(MessageBuilder.withPayload("simulated file content").build());
```

The channel's code never changes based on what's attached at either end — that's precisely the point of the separation: adapters own the external-system-specific translation, channels stay generic.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="External system connects via an inbound adapter into a channel, which an outbound adapter drains to another external system; the channel itself knows nothing about either side">
  <rect x="10" y="80" width="110" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">external system</text>
  <text x="65" y="113" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(file, JMS, HTTP)</text>

  <line x1="120" y1="102" x2="180" y2="102" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <text x="150" y="88" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">inbound adapter</text>

  <rect x="190" y="80" width="130" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="255" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">channel (pipe)</text>

  <line x1="320" y1="102" x2="380" y2="102" stroke="#79c0ff" stroke-width="2" marker-end="url(#a2)"/>
  <text x="350" y="88" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">outbound adapter</text>

  <rect x="390" y="80" width="110" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="445" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">external system</text>
  <text x="445" y="113" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(DB, email, HTTP)</text>

  <text x="255" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">the channel never knows what's outside either adapter</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Adapters are the translation boundary at each end; the channel in the middle is deliberately ignorant of what's beyond either adapter.

## 5. Runnable example

The scenario: a minimal simulated "inbound adapter" polling an in-memory queue standing in for an external system, feeding a channel, drained by a simulated "outbound adapter" — starting basic, then a poller-driven inbound adapter, and finally symmetric adapters on both ends with translation logic.

### Level 1 — Basic

```java
// BasicAdapterConceptDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public class BasicAdapterConceptDemo {
    public static void main(String[] args) {
        // stand-in for an "external system" (e.g. a directory being watched)
        BlockingQueue<String> externalSystem = new LinkedBlockingQueue<>();
        externalSystem.add("order.csv");

        QueueChannel channel = new QueueChannel();

        // INBOUND ADAPTER logic: translate an external item into a Message, put it on the channel
        String externalItem = externalSystem.poll();
        channel.send(MessageBuilder.withPayload(externalItem).setHeader("source", "file-system").build());
        System.out.println("Inbound adapter moved '" + externalItem + "' onto the channel");

        // OUTBOUND ADAPTER logic: take a Message off the channel, do something external with its payload
        Message<?> outgoing = channel.receive();
        System.out.println("Outbound adapter would now write out: " + outgoing.getPayload()
            + " (originally from: " + outgoing.getHeaders().get("source") + ")");
    }
}
```

How to run: `java BasicAdapterConceptDemo.java`. Expected output: `Inbound adapter moved 'order.csv' onto the channel` then `Outbound adapter would now write out: order.csv (originally from: file-system)` — the channel itself (a plain `QueueChannel`) never referenced "file system" anywhere; only the adapter-role code on either side did.

### Level 2 — Intermediate

A real inbound adapter is typically poller-driven — it actively checks the external source on a schedule rather than being pushed to — modeled here as a background thread polling every 200ms, decoupled entirely from the channel it feeds.

```java
// PollingInboundAdapterDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.CountDownLatch;

public class PollingInboundAdapterDemo {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> externalSystem = new LinkedBlockingQueue<>();
        QueueChannel channel = new QueueChannel();
        CountDownLatch processed = new CountDownLatch(3);

        // simulated inbound adapter: polls the "external system" on a fixed schedule
        Thread inboundAdapter = new Thread(() -> {
            while (processed.getCount() > 0) {
                String item = externalSystem.poll();
                if (item != null) {
                    channel.send(MessageBuilder.withPayload(item).build());
                    System.out.println("Inbound adapter polled and forwarded: " + item);
                }
                try { Thread.sleep(200); } catch (InterruptedException ignored) {}
            }
        });
        inboundAdapter.start();

        // "external system" gets new items at its own pace, unaware of the adapter or channel
        new Thread(() -> {
            for (String f : new String[]{"a.csv", "b.csv", "c.csv"}) {
                externalSystem.add(f);
                try { Thread.sleep(250); } catch (InterruptedException ignored) {}
            }
        }).start();

        for (int i = 0; i < 3; i++) {
            channel.receive();
            processed.countDown();
        }
        System.out.println("All 3 items made it through the adapter onto the channel and were received");
    }
}
```

How to run: `java PollingInboundAdapterDemo.java`. Expected output shows `Inbound adapter polled and forwarded: X` three times, in roughly arrival order, followed by `All 3 items made it through...` — the adapter's polling loop is entirely decoupled from both the external producer's timing and the channel's consumer, exactly the boundary-translation role an adapter plays.

### Level 3 — Advanced

Symmetric adapters at both ends, each performing real translation (not just pass-through) — an inbound adapter parsing a raw external format into a domain payload, and an outbound adapter serializing the domain payload back into an external format — shows the channel carrying a clean domain object between two format-aware boundaries.

```java
// SymmetricTranslatingAdaptersDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class SymmetricTranslatingAdaptersDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        String rawExternalLine = "ORD-42|199.99"; // e.g. a line from a CSV file
        QueueChannel channel = new QueueChannel();

        // INBOUND ADAPTER: raw external format -> domain object -> Message
        String[] parts = rawExternalLine.split("\\|");
        Order order = new Order(parts[0], Double.parseDouble(parts[1]));
        channel.send(MessageBuilder.withPayload(order).build());
        System.out.println("Inbound adapter parsed raw line into domain object: " + order);

        // (any number of internal endpoints could process 'order' here, untouched by external format concerns)

        // OUTBOUND ADAPTER: domain object -> external format (e.g. a JSON-ish string for an external API)
        Message<?> toDeliver = channel.receive();
        Order deliveredOrder = (Order) toDeliver.getPayload();
        String externalPayload = String.format("{\"orderId\":\"%s\",\"amount\":%.2f}",
            deliveredOrder.id(), deliveredOrder.amount());
        System.out.println("Outbound adapter serialized for external API: " + externalPayload);
    }
}
```

How to run: `java SymmetricTranslatingAdaptersDemo.java`. Expected output: `Inbound adapter parsed raw line into domain object: Order[id=ORD-42, amount=199.99]` followed by `Outbound adapter serialized for external API: {"orderId":"ORD-42","amount":199.99}` — the channel in between carried a clean `Order` record the whole time; neither the pipe-delimited input format nor the JSON output format ever touched the channel or any hypothetical internal endpoint.

## 6. Walkthrough

Tracing `SymmetricTranslatingAdaptersDemo` in execution order:

1. `rawExternalLine` represents data as it exists *outside* the messaging system — a pipe-delimited string, in whatever format the external source (a CSV file, in this analogy) actually uses.
2. The inbound-adapter-role code splits and parses that raw string into an `Order` domain record — this parsing step is exactly what a real `FileReadingMessageSource` plus a transformer, or a custom `MessageSource`, would do: convert external representation into an internal domain shape.
3. `channel.send(MessageBuilder.withPayload(order).build())` puts a `Message<Order>` onto the channel — from this point forward, everything inside the messaging system works with the clean `Order` object, with zero awareness of pipe-delimited strings.
4. `channel.receive()` retrieves that message — in a real flow, this step (and everything between steps 3 and 4) is where any number of transformers, filters, routers, or service activators (cards 0019–0024) could process the `Order`, all working with the same clean domain shape.
5. The outbound-adapter-role code extracts the `Order` payload and serializes it into a *different* external format (JSON-ish, standing in for whatever an outbound HTTP or messaging adapter would produce) — this translation step only happens at the boundary going back out, not anywhere in the middle.
6. The final printed line is what would actually be sent to the external API — the channel and anything between the two adapters never had to know or care about either the inbound pipe-delimited format or the outbound JSON format.

```
external (pipe-delimited) --[inbound adapter: parse]--> Order --[channel, internal processing]--> Order --[outbound adapter: serialize]--> external (JSON)
```

## 7. Gotchas & takeaways

> It's a common beginner mistake to look for "the bug" inside a channel when a flow produces no output — but a channel by itself can never originate or discard a message; it only carries what's put onto it. If nothing arrives, check the *inbound adapter* (is it actually polling, is the external source reachable, is a poller even configured); if messages go in but nothing external happens, check the *outbound adapter* (is it subscribed to the right channel, is the external write actually succeeding).

- A channel is a generic, external-system-agnostic pipe; an adapter is the translation boundary connecting a channel to something outside the messaging system.
- Inbound adapters turn external input (files, JMS, HTTP, database rows) into `Message` objects and put them onto a channel; outbound adapters take messages off a channel and perform an external side effect with their payload.
- The channel in between is deliberately ignorant of what's attached at either end — that separation is what lets the same channel type serve flows connected to completely different external systems.
- When debugging "nothing is happening," the channel itself is rarely the culprit; look at the adapters (or their absence) at the flow's actual boundaries.
- Symmetric flows (an inbound adapter parsing external format in, an outbound adapter serializing a different external format out) show why keeping translation logic confined to adapters, rather than scattered through internal endpoints, keeps the internal flow reusable across different external integrations.
