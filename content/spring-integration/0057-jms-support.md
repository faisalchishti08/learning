---
card: spring-integration
gi: 57
slug: jms-support
title: "JMS support"
---

## 1. What it is

JMS support (`Jms.inboundGateway(...)`/`Jms.outboundGateway(...)`, and their channel-adapter equivalents) connects a flow to a Java Message Service broker (ActiveMQ, IBM MQ, and similar) — a message-broker protocol distinct from raw sockets (card 0053) or HTTP (cards 0054/0055), built around the concept of *destinations* (queues for point-to-point delivery, topics for publish/subscribe) that decouple producers and consumers in both time and location, unlike a direct TCP connection or HTTP request, which requires both parties to be simultaneously available.

## 2. Why & when

You reach for JMS support specifically when the integration point is a JMS-compliant message broker, or when the messaging semantics a broker provides (durable queuing, guaranteed delivery, pub/sub) are genuinely needed:

- **You're integrating with an existing enterprise messaging infrastructure** — many established Java enterprise environments already run ActiveMQ, IBM MQ, or another JMS provider as their central messaging backbone; JMS support lets a Spring Integration flow participate in that existing infrastructure directly.
- **You need durable, broker-managed queuing rather than a direct connection** — unlike TCP (card 0053), where both endpoints must be simultaneously connected, a JMS queue durably holds messages even if the consumer is temporarily offline, delivering them once it reconnects — genuinely different reliability semantics than direct socket or HTTP communication.
- **You need publish/subscribe fan-out to multiple independent consumers** — a JMS topic delivers each message to every active subscriber, a distribution model neither raw TCP nor typical HTTP naturally provides without additional infrastructure.

## 3. Core concept

Think of a JMS queue like a physical post office box: a sender drops a letter in, and it sits there durably until the recipient checks their box — sender and recipient never need to be present at the same time, and the letter survives even if the recipient is away for days. A JMS topic, by contrast, is like a subscription newsletter: every current subscriber receives their own copy of each new issue the moment it's published, but someone who subscribes *after* an issue went out has already missed it (unless the topic is configured as durable, which changes this).

```java
@Bean
public IntegrationFlow jmsInboundFlow(ConnectionFactory connectionFactory) {
    return IntegrationFlow.from(Jms.inboundGateway(connectionFactory)
            .destination("order.queue"))
        .handle((Order order, headers) -> orderService.process(order))
        .get();
}

@Bean
public IntegrationFlow jmsOutboundFlow(ConnectionFactory connectionFactory) {
    return IntegrationFlow.from("outgoingNotifications")
        .handle(Jms.outboundAdapter(connectionFactory).destination("notification.queue"))
        .get();
}
```

The `ConnectionFactory` (provided by whichever JMS broker implementation is in use) handles the actual broker connection; the gateway/adapter's job is translating between Spring Integration `Message`s and JMS `Message`s at that boundary.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A JMS queue durably holds messages for a single eventual consumer even if it's offline; a JMS topic fans out each published message to every currently active subscriber" >
  <text x="150" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Queue (point-to-point)</text>
  <rect x="20" y="35" width="100" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">producer</text>
  <line x1="120" y1="55" x2="180" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#jms1)"/>
  <rect x="190" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="245" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">queue (durable)</text>
  <line x1="300" y1="55" x2="360" y2="55" stroke="#79c0ff" stroke-width="2" stroke-dasharray="4,2" marker-end="url(#jms2)"/>
  <text x="330" y="42" fill="#79c0ff" font-size="6" text-anchor="middle" font-family="sans-serif">delivered eventually</text>
  <rect x="370" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="425" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ONE consumer</text>

  <text x="150" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Topic (pub/sub)</text>
  <rect x="20" y="135" width="100" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">publisher</text>
  <line x1="120" y1="155" x2="180" y2="155" stroke="#6db33f" stroke-width="2" marker-end="url(#jms1)"/>
  <rect x="190" y="135" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="235" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">topic</text>
  <line x1="280" y1="145" x2="340" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jms2)"/>
  <line x1="280" y1="165" x2="340" y2="185" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jms2)"/>
  <text x="500" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">EVERY active subscriber gets a copy</text>

  <defs>
    <marker id="jms1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jms2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Queues durably deliver each message to exactly one eventual consumer; topics fan out each message to every currently active subscriber.

## 5. Runnable example

The scenario: an order-notification system using both point-to-point and publish/subscribe delivery, simulated with in-memory structures standing in for a real JMS broker (since connecting to an actual broker requires external infrastructure), starting with basic queue delivery surviving a temporarily-offline consumer, then topic fan-out to multiple subscribers, and finally comparing the two side by side for the same message.

### Level 1 — Basic

```java
// JmsQueueDurabilityDemo.java
// Simulates JMS queue semantics with an in-memory structure standing in for a real broker,
// since connecting to ActiveMQ/IBM MQ requires actual broker infrastructure.
import java.util.concurrent.*;

public class JmsQueueDurabilityDemo {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> jmsQueue = new LinkedBlockingQueue<>(); // stands in for a durable JMS queue

        // producer sends WHILE no consumer is listening — the message just waits, durably, on the queue
        jmsQueue.put("order-1-notification");
        System.out.println("Producer sent a message; consumer isn't running yet — message waits on the queue");

        Thread.sleep(200); // simulate the consumer being "offline" for a while

        // consumer connects LATER and still receives it
        String received = jmsQueue.take();
        System.out.println("Consumer connected later and STILL received: " + received);
    }
}
```

How to run: `java JmsQueueDurabilityDemo.java`. Expected output: `Producer sent a message; consumer isn't running yet — message waits on the queue` then, after the simulated delay, `Consumer connected later and STILL received: order-1-notification` — the message survived the gap between being sent and being consumed, exactly the durable point-to-point delivery a real JMS queue provides, fundamentally different from a direct TCP connection (card 0053), which requires both ends present simultaneously.

### Level 2 — Intermediate

A topic fanning out the same published message to multiple independent subscribers — each subscriber gets its own copy, simulated here with multiple independent queues all fed by the same publish call.

```java
// JmsTopicFanoutDemo.java
import java.util.concurrent.*;
import java.util.*;

public class JmsTopicFanoutDemo {
    static List<BlockingQueue<String>> subscribers = new CopyOnWriteArrayList<>(); // each = one topic subscriber

    static void publish(String message) {
        // what a JMS topic does: deliver a COPY to EVERY currently active subscriber
        for (BlockingQueue<String> subscriberQueue : subscribers) {
            subscriberQueue.add(message);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> emailServiceQueue = new LinkedBlockingQueue<>();
        BlockingQueue<String> smsServiceQueue = new LinkedBlockingQueue<>();
        BlockingQueue<String> analyticsServiceQueue = new LinkedBlockingQueue<>();
        subscribers.add(emailServiceQueue);
        subscribers.add(smsServiceQueue);
        subscribers.add(analyticsServiceQueue);

        publish("order-1-shipped");

        System.out.println("Email service received: " + emailServiceQueue.take());
        System.out.println("SMS service received: " + smsServiceQueue.take());
        System.out.println("Analytics service received: " + analyticsServiceQueue.take());
    }
}
```

How to run: `java JmsTopicFanoutDemo.java`. Expected output: all three services report receiving `order-1-shipped` — one publish operation delivered independent copies to three separate subscribers, exactly the fan-out behavior a JMS topic provides, fundamentally different from a queue (Level 1), where only *one* consumer would have received that single message.

### Level 3 — Advanced

Comparing queue and topic delivery for the same logical event side by side, using two subscribers on a queue (only one gets the message — competing consumers) versus two subscribers on a topic (both get their own copy) — making the fundamental delivery-model difference between the two destination types directly visible.

```java
// QueueVsTopicComparisonDemo.java
import java.util.concurrent.*;
import java.util.*;

public class QueueVsTopicComparisonDemo {
    public static void main(String[] args) throws InterruptedException {
        // QUEUE: two consumers COMPETE for the same messages — each message goes to exactly ONE of them
        BlockingQueue<String> orderQueue = new LinkedBlockingQueue<>();
        orderQueue.put("order-A");
        orderQueue.put("order-B");

        ExecutorService consumers = Executors.newFixedThreadPool(2);
        ConcurrentHashMap<String, String> queueResults = new ConcurrentHashMap<>();
        CountDownLatch queueDone = new CountDownLatch(2);
        for (int i = 1; i <= 2; i++) {
            String consumerName = "consumer-" + i;
            consumers.submit(() -> {
                try {
                    String msg = orderQueue.take(); // COMPETES with the other consumer for the next available message
                    queueResults.put(consumerName, msg);
                } catch (InterruptedException ignored) {} finally { queueDone.countDown(); }
            });
        }
        queueDone.await();
        consumers.shutdown();

        System.out.println("QUEUE (point-to-point): each of the 2 messages went to exactly ONE of the 2 consumers");
        queueResults.forEach((consumer, msg) -> System.out.println("  " + consumer + " got: " + msg));

        // TOPIC: two subscribers BOTH get their OWN copy of the SAME single published event
        BlockingQueue<String> subscriberA = new LinkedBlockingQueue<>();
        BlockingQueue<String> subscriberB = new LinkedBlockingQueue<>();
        List<BlockingQueue<String>> topicSubscribers = List.of(subscriberA, subscriberB);
        String event = "order-shipped-notification";
        topicSubscribers.forEach(sub -> sub.add(event)); // fan-out to BOTH

        System.out.println("\nTOPIC (pub/sub): the SAME single event delivered to BOTH subscribers");
        System.out.println("  subscriberA got: " + subscriberA.take());
        System.out.println("  subscriberB got: " + subscriberB.take());
    }
}
```

How to run: `java QueueVsTopicComparisonDemo.java`. Expected output: for the queue section, `order-A` and `order-B` are split between `consumer-1` and `consumer-2` (each consumer gets exactly one, though which gets which can vary between runs) — the two messages were divided between the two competing consumers, never both delivered to both. For the topic section, both `subscriberA` and `subscriberB` report receiving `order-shipped-notification` — the single published event reached both independently, unlike the queue's competing-consumer split.

## 6. Walkthrough

Tracing the queue portion of `QueueVsTopicComparisonDemo` in execution order:

1. Two messages, `"order-A"` and `"order-B"`, are placed onto the shared `orderQueue` before any consumer starts.
2. Two consumer tasks are submitted to a thread pool, both calling `orderQueue.take()` — this is a blocking, competing operation: whichever consumer thread's `take()` call happens to be serviced first by the underlying `BlockingQueue` gets the *next* available message, and the other consumer's `take()` call gets whatever remains.
3. Because both messages were already queued before either consumer started, both `take()` calls succeed quickly, but which specific consumer receives `"order-A"` versus `"order-B"` depends on scheduling — this non-determinism about *which* consumer gets *which* message (while still guaranteeing each message goes to exactly one consumer, never both, never neither) is the defining "competing consumers" behavior of JMS point-to-point queue delivery.
4. `queueResults` (a thread-safe map) records which consumer received which message, and once both consumers have completed (`queueDone.await()` unblocks), the results are printed — confirming exactly two entries, one per consumer, together accounting for both original messages.
5. This directly contrasts with the topic portion: there, `topicSubscribers.forEach(sub -> sub.add(event))` deliberately delivers the *same* event to *every* subscriber's own queue — no competition, no splitting; each subscriber independently receives its own full copy.
6. The practical implication: adding a second consumer to a JMS queue *increases throughput* (the two messages are processed in parallel, by different consumers, each handling a subset) without duplicating work, while adding a second subscriber to a JMS topic *duplicates delivery* (both now receive every message independently) — two fundamentally different scaling behaviors, chosen based on whether the use case needs "distribute this work across consumers" (queue) or "notify every interested party" (topic).

```
QUEUE:  [order-A, order-B] -> consumer-1.take() and consumer-2.take() COMPETE
          -> EACH message goes to exactly ONE consumer (split, not duplicated)

TOPIC:  publish(event) -> delivered to subscriberA AND subscriberB
          -> EACH subscriber gets its OWN full copy (duplicated, not split)
```

## 7. Gotchas & takeaways

> Accidentally using a queue where a topic was intended (or vice versa) produces a subtle, easy-to-miss bug: if a use case genuinely needs every interested consumer to see every message (like notifying both an email service and an SMS service about the same shipment), but a queue is used instead, only *one* of those consumers will ever receive any given message — the others will simply never see it, with no error raised, since from the queue's perspective, competing consumers dividing up the work is entirely correct behavior. Choosing between queue and topic is a fundamental design decision, not an interchangeable configuration detail.

- JMS support connects a flow to a JMS-compliant message broker, using *destinations*: queues for durable, point-to-point delivery (each message goes to exactly one of possibly several competing consumers), and topics for publish/subscribe fan-out (each message is delivered independently to every currently active subscriber).
- Use JMS when broker-managed durability (messages surviving a temporarily offline consumer) or genuine multi-consumer fan-out is needed — capabilities neither a direct TCP connection (card 0053) nor typical HTTP request/response naturally provide.
- A queue's competing-consumer model increases throughput as more consumers are added (work is split, not duplicated); a topic's pub/sub model duplicates delivery as more subscribers are added (every message reaches every subscriber independently).
- Choosing queue versus topic is a fundamental design decision based on the actual delivery semantics needed — using the wrong one produces a working-looking system that silently delivers messages to the wrong (or too few) recipients.
- The `Jms.inboundGateway`/`Jms.outboundGateway`/adapter variants translate between Spring Integration `Message`s and JMS `Message`s at the boundary, letting the rest of the flow work with plain Spring Integration messages regardless of the underlying JMS broker's specifics.
