---
card: spring-integration
gi: 33
slug: inbound-outbound-channel-adapters
title: "Inbound/outbound channel adapters"
---

## 1. What it is

Building on the general adapter-vs-channel distinction from card 0018, an inbound channel adapter and an outbound channel adapter are the two concrete adapter roles: an inbound channel adapter is a one-directional, one-way source — it only ever produces messages from an external input, it never accepts anything back (no reply). An outbound channel adapter is a one-directional, one-way sink — it only ever consumes a message and performs a side effect, producing no reply either. Neither expects or handles a response; that two-way capability is what distinguishes a *gateway* (card 0034) from a plain adapter.

## 2. Why & when

You reach for a plain (non-gateway) channel adapter specifically when the interaction with the external system is genuinely one-directional:

- **You're reading data that has no concept of a "reply"** — files appearing in a directory, rows in a database table, messages on a queue you're only consuming from — an inbound channel adapter (e.g., `FileReadingMessageSource`) simply produces messages; there's nothing to reply to.
- **You're writing data where the external system doesn't hand anything back that the flow needs** — writing a file to disk, publishing a fire-and-forget event, appending a log line — an outbound channel adapter performs the write and the flow moves on, with no expectation of a response payload.
- **You want the simplest possible adapter for the job** — a plain channel adapter is a lighter-weight commitment than a gateway (card 0034); reach for the adapter first, and only step up to a gateway when a genuine request/reply exchange with the external system is actually needed.

## 3. Core concept

Think of an inbound channel adapter like a rain gauge that only measures and reports — it produces readings continuously, but there's no mechanism to "reply" to a rain gauge; it doesn't expect anything back. An outbound channel adapter is like a one-way mail chute — you drop something in, it's gone, sent on its way, and the chute itself gives you no receipt or response about what happened to it after you let go. Both are strictly one-directional, unlike a two-way conversation (which is what a gateway, card 0034, models).

```java
// Inbound channel adapter: produces messages, never receives anything back
@Bean
@InboundChannelAdapter(value = "fileEvents", poller = @Poller(fixedDelay = "1000"))
public MessageSource<File> fileReadingSource() {
    return new FileReadingMessageSource(new File("/incoming"));
}

// Outbound channel adapter: consumes messages, produces no reply
@ServiceActivator(inputChannel = "fileEvents")
@Bean
public MessageHandler fileWritingHandler() {
    FileWritingMessageHandler handler = new FileWritingMessageHandler(new File("/processed"));
    handler.setExpectReply(false); // explicitly ONE-WAY: no reply expected
    return handler;
}
```

Neither adapter's method signature accommodates a two-way exchange — the inbound one is purely a `MessageSource` (produces), and the outbound one is a `MessageHandler` configured with `expectReply=false` (consumes).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inbound channel adapter produces messages one-way from an external source; outbound channel adapter consumes messages one-way to an external destination; neither expects a reply">
  <text x="150" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Inbound (one-way IN)</text>
  <rect x="20" y="35" width="100" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">directory</text>

  <line x1="120" y1="55" x2="180" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#io1)"/>

  <rect x="190" y="35" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="250" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">channel (no reply)</text>

  <text x="490" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Outbound (one-way OUT)</text>
  <rect x="380" y="35" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="440" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">channel</text>

  <line x1="500" y1="55" x2="560" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#io1)"/>

  <rect x="570" y="35" width="60" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="600" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">file</text>

  <text x="320" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">NO arrow ever points back — that's what a Gateway (card 0034) adds</text>

  <defs>
    <marker id="io1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Both adapter directions are strictly one-way — production or consumption, never a request paired with a reply.

## 5. Runnable example

The scenario: a file-watching intake feeding a processing channel, and a separate audit-logging outbound step, starting with a basic inbound-then-outbound pair, then a poller-driven inbound adapter, and finally both combined in one one-directional pipeline.

### Level 1 — Basic

```java
// BasicInboundOutboundDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.ConcurrentLinkedQueue;

public class BasicInboundOutboundDemo {
    public static void main(String[] args) {
        ConcurrentLinkedQueue<String> externalSource = new ConcurrentLinkedQueue<>(); // stand-in for a watched directory
        externalSource.add("invoice-1.pdf");

        DirectChannel fileEvents = new DirectChannel();
        ConcurrentLinkedQueue<String> externalDestination = new ConcurrentLinkedQueue<>(); // stand-in for a "processed" folder

        // OUTBOUND channel adapter: consumes, performs a side effect, produces NOTHING back
        fileEvents.subscribe(m -> {
            externalDestination.add((String) m.getPayload()); // the "write to disk" side effect
            System.out.println("Outbound adapter wrote: " + m.getPayload() + " (no reply produced)");
        });

        // INBOUND channel adapter: produces a message, expects nothing back
        String discovered = externalSource.poll();
        fileEvents.send(MessageBuilder.withPayload(discovered).build());

        System.out.println("External destination now contains: " + externalDestination);
    }
}
```

How to run: `java BasicInboundOutboundDemo.java`. Expected output: `Outbound adapter wrote: invoice-1.pdf (no reply produced)` then `External destination now contains: [invoice-1.pdf]` — the inbound side produced one message with nothing expected back, and the outbound side consumed it with nothing sent back either; the flow is a one-way pipe end to end.

### Level 2 — Intermediate

A realistic inbound channel adapter is poller-driven, continuously checking its external source on a schedule (the same pattern shown for a generic adapter in card 0018, here specifically framed as the inbound-adapter archetype) — it never blocks waiting for anything to consume what it produces.

```java
// PolledInboundAdapterDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.ConcurrentLinkedQueue;

public class PolledInboundAdapterDemo {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentLinkedQueue<String> watchedDirectory = new ConcurrentLinkedQueue<>();
        DirectChannel fileEvents = new DirectChannel();
        fileEvents.subscribe(m -> System.out.println("Received from inbound adapter: " + m.getPayload()));

        Thread inboundAdapterPoller = new Thread(() -> {
            for (int i = 0; i < 5; i++) {
                String next = watchedDirectory.poll();
                if (next != null) {
                    fileEvents.send(MessageBuilder.withPayload(next).build()); // one-way: no reply awaited
                }
                try { Thread.sleep(100); } catch (InterruptedException ignored) {}
            }
        });
        inboundAdapterPoller.start();

        watchedDirectory.add("a.pdf");
        Thread.sleep(150);
        watchedDirectory.add("b.pdf");

        inboundAdapterPoller.join();
    }
}
```

How to run: `java PolledInboundAdapterDemo.java`. Expected output: `Received from inbound adapter: a.pdf` then, after the second file is added mid-polling, `Received from inbound adapter: b.pdf` — the adapter's polling loop runs independently of when files actually appear, picking each up on its next scheduled check, with no reply expected from either send.

### Level 3 — Advanced

Combining both roles into one strictly one-directional pipeline — an inbound file-watching adapter feeding a transformer feeding an outbound "archive" adapter — shows a realistic, complete one-way flow where nothing anywhere in the chain ever produces a reply back toward its source.

```java
// FullOneWayPipelineDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.List;

public class FullOneWayPipelineDemo {
    record FileEvent(String name, long sizeBytes) {}

    public static void main(String[] args) {
        ConcurrentLinkedQueue<String> watchedDirectory = new ConcurrentLinkedQueue<>(List.of("a.pdf", "b.pdf"));
        DirectChannel rawEvents = new DirectChannel();
        DirectChannel parsedEvents = new DirectChannel();
        ConcurrentLinkedQueue<String> archive = new ConcurrentLinkedQueue<>();

        // OUTBOUND channel adapter: final step, one-way, no reply
        parsedEvents.subscribe(m -> {
            FileEvent event = (FileEvent) m.getPayload();
            archive.add(event.name());
            System.out.println("Archived (outbound adapter): " + event.name());
        });

        // internal transformer step (card 0021), between inbound and outbound
        rawEvents.subscribe(m -> parsedEvents.send(MessageBuilder.withPayload(
            new FileEvent((String) m.getPayload(), 4096L)).build()));

        // INBOUND channel adapter: source, one-way, no reply
        String file;
        while ((file = watchedDirectory.poll()) != null) {
            rawEvents.send(MessageBuilder.withPayload(file).build());
        }

        System.out.println("Final archive contents: " + archive);
    }
}
```

How to run: `java FullOneWayPipelineDemo.java`. Expected output: `Archived (outbound adapter): a.pdf`, `Archived (outbound adapter): b.pdf`, then `Final archive contents: [a.pdf, b.pdf]` — data flows strictly in one direction from the watched directory, through an internal transform step, out to the archive, with no message anywhere carrying a reply back toward the file system it originated from.

## 6. Walkthrough

Tracing `FullOneWayPipelineDemo` in execution order:

1. The `while` loop polls `watchedDirectory`, standing in for the inbound channel adapter's continuous external-source check — for each file name found, it sends a plain string message to `rawEvents`.
2. The internal transformer's subscriber on `rawEvents` receives the raw file name, wraps it into a `FileEvent` record (adding a simulated size), and sends this richer message to `parsedEvents` — this step is a plain internal `Transformer` (card 0021), not itself an adapter, since it's not touching anything external.
3. The outbound channel adapter's subscriber on `parsedEvents` receives the `FileEvent`, adds the file's name to the `archive` collection (standing in for an actual file-system write), and prints confirmation — this is the flow's final, external-facing side effect.
4. Crucially, at no point does the outbound adapter's subscriber send anything back toward `rawEvents` or the original `watchedDirectory` — there's no reply channel, no correlation ID linking a response back to the original poll, because none of that machinery exists in a plain adapter.
5. The loop repeats for the second file, `b.pdf`, going through the exact same three-step path independently.
6. After the loop finishes, `archive` contains both file names — proof that data made a complete one-way journey from an external source, through internal processing, to an external destination, without a single step in that journey ever expecting or producing a response.

```
watchedDirectory --[Inbound adapter: poll]--> rawEvents --[Transformer]--> parsedEvents --[Outbound adapter: write]--> archive
     (no reply anywhere in either direction along this entire chain)
```

## 7. Gotchas & takeaways

> It's a common design mistake to reach for a plain outbound channel adapter when the external system's response actually matters to the flow — for instance, calling an HTTP endpoint and needing its response body downstream. A plain adapter configured with `expectReply=false` will silently discard whatever the external call returns (or the adapter type simply won't support capturing it at all); if a reply genuinely needs to flow back into the pipeline, that's exactly the signal to use an outbound *gateway* (card 0034) instead, not a plain adapter.

- An inbound channel adapter is a one-way source: it produces messages from an external input, with no reply expected or possible.
- An outbound channel adapter is a one-way sink: it consumes a message and performs an external side effect, producing no reply.
- Both are the concrete, directional instances of the general adapter concept introduced in card 0018 — reach for a plain adapter (rather than a gateway) whenever the external interaction is genuinely one-directional.
- The absence of any reply/response capability is the defining characteristic separating a plain channel adapter from a gateway (card 0034) — if the external system's response needs to flow back into the pipeline, a gateway is the correct choice instead.
- A full pipeline built entirely from inbound and outbound adapters (with internal transformers/filters/routers in between) is strictly one-directional end to end — useful for reasoning about where a reply could ever re-enter the flow: nowhere, by design.
