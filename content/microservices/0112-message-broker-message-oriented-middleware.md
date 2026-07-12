---
card: microservices
gi: 112
slug: message-broker-message-oriented-middleware
title: "Message broker / message-oriented middleware"
---

## 1. What it is

A message broker (also called message-oriented middleware, or MOM) is the piece of infrastructure that sits between producers and consumers in the [asynchronous messaging model](0111-asynchronous-messaging-model.md): it accepts messages from producers, stores them durably, and delivers them to consumers, handling the routing, buffering, and retry logic so that neither side has to talk to the other directly. Examples in wide production use include Apache Kafka, RabbitMQ, ActiveMQ, and cloud-managed equivalents like Amazon SQS/SNS.

## 2. Why & when

Without a broker, "asynchronous messaging" would mean each service running its own ad-hoc queue and retry logic, reimplementing durability, delivery guarantees, and routing from scratch, badly, in every service. The broker centralizes that hard, easy-to-get-wrong infrastructure once, so individual services only need a thin client library to publish and subscribe.

Introduce a broker as soon as more than one service needs to exchange asynchronous events, or as soon as an in-process queue is not enough because the producer and consumer are separate deployable services, possibly on separate machines, that must survive each other restarting. Skip a broker for communication that is genuinely synchronous and needs an immediate answer — that is what [RESTful APIs](0076-restful-apis-over-http.md) or [gRPC](0085-rpc-model-grpc-and-http2.md) are for.

## 3. Core concept

The broker exposes a network-addressable destination (a queue or a topic), accepts writes from any producer that can reach it, persists the message according to its durability configuration, and hands it to a consumer according to the broker's delivery rules — all without producer and consumer ever opening a connection to each other.

```java
// producer and consumer only ever talk to the broker, never to each other
brokerClient.publish("order-events", orderPlacedJson);

// elsewhere, possibly on a different machine, possibly minutes later
Message msg = brokerClient.poll("order-events");
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple producers publish to a broker, which persists messages and delivers them to multiple consumers, decoupling every service from every other service">
  <rect x="20" y="20" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Svc</text>
  <rect x="20" y="150" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="175" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Payment Svc</text>

  <rect x="250" y="70" width="140" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Broker</text>
  <text x="320" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">stores &amp; routes</text>
  <text x="320" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">messages</text>

  <rect x="480" y="20" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Email Svc</text>
  <rect x="480" y="150" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="175" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Analytics Svc</text>

  <line x1="140" y1="40" x2="248" y2="90" stroke="#8b949e" marker-end="url(#arr2)"/>
  <line x1="140" y1="170" x2="248" y2="130" stroke="#8b949e" marker-end="url(#arr2)"/>
  <line x1="392" y1="90" x2="478" y2="40" stroke="#8b949e" stroke-dasharray="4,3" marker-end="url(#arr2)"/>
  <line x1="392" y1="130" x2="478" y2="170" stroke="#8b949e" stroke-dasharray="4,3" marker-end="url(#arr2)"/>

  <defs>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

No service holds a connection to another service; every arrow terminates at the broker.

## 5. Runnable example

Scenario: a hand-rolled in-process "broker" grows from a single unnamed queue, into a broker with named, independently addressable destinations, into a broker that adds durable persistence to disk so messages survive a process restart — the defining responsibility of real middleware like Kafka or RabbitMQ.

### Level 1 — Basic

```java
// File: NaiveQueue.java -- no broker abstraction at all: one raw shared queue.
import java.util.concurrent.*;

public class NaiveQueue {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        queue.put("OrderPlaced:42");
        queue.put("PaymentCaptured:42");
        System.out.println("Consumed: " + queue.take());
        System.out.println("Consumed: " + queue.take());
    }
}
```

**How to run:** `javac NaiveQueue.java && java NaiveQueue` (JDK 17+).

This has no notion of separate destinations, no client abstraction, and nothing survives a restart — everything a real broker exists to solve is still missing.

### Level 2 — Intermediate

```java
// File: NamedBroker.java -- a broker abstraction with independently addressable destinations.
import java.util.*;
import java.util.concurrent.*;

public class NamedBroker {
    static class Broker {
        private final Map<String, BlockingQueue<String>> destinations = new ConcurrentHashMap<>();
        void publish(String destination, String message) {
            destinations.computeIfAbsent(destination, d -> new LinkedBlockingQueue<>()).put(message);
        }
        String poll(String destination) throws InterruptedException {
            return destinations.computeIfAbsent(destination, d -> new LinkedBlockingQueue<>()).take();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Broker broker = new Broker();
        broker.publish("order-events", "OrderPlaced:42");
        broker.publish("payment-events", "PaymentCaptured:42"); // a SEPARATE destination, no cross-talk

        System.out.println("From order-events: " + broker.poll("order-events"));
        System.out.println("From payment-events: " + broker.poll("payment-events"));
    }
}
```

**How to run:** `javac NamedBroker.java && java NamedBroker` (JDK 17+).

Producers now address a specific, named destination rather than a single anonymous queue — the routing responsibility a real broker provides so unrelated event streams don't collide.

### Level 3 — Advanced

```java
// File: DurableBroker.java -- adds persistence to disk, so messages survive a process restart.
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

public class DurableBroker {
    static class Broker {
        private final Path storageDir;
        Broker(Path storageDir) throws IOException {
            this.storageDir = storageDir;
            Files.createDirectories(storageDir);
        }
        void publish(String destination, String message) throws IOException {
            Path file = storageDir.resolve(destination + ".log");
            Files.writeString(file, message + System.lineSeparator(),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND); // durable write -- survives a crash
        }
        List<String> readAll(String destination) throws IOException {
            Path file = storageDir.resolve(destination + ".log");
            if (!Files.exists(file)) return List.of();
            return Files.readAllLines(file);
        }
    }

    public static void main(String[] args) throws IOException {
        Path dir = Path.of("broker-storage-demo");

        // "process 1": publish, then simulate the process exiting
        Broker producerProcess = new Broker(dir);
        producerProcess.publish("order-events", "OrderPlaced:42");
        producerProcess.publish("order-events", "OrderPlaced:43");
        System.out.println("Producer process published 2 messages, then exits.");

        // "process 2": a brand-new Broker instance, simulating a restarted consumer process
        Broker consumerProcessAfterRestart = new Broker(dir);
        List<String> recovered = consumerProcessAfterRestart.readAll("order-events");
        System.out.println("Consumer process (after restart) recovered: " + recovered);

        // cleanup for repeatable runs
        Files.deleteIfExists(dir.resolve("order-events.log"));
        Files.deleteIfExists(dir);
    }
}
```

**How to run:** `javac DurableBroker.java && java DurableBroker` (JDK 17+).

Expected output:
```
Producer process published 2 messages, then exits.
Consumer process (after restart) recovered: [OrderPlaced:42, OrderPlaced:43]
```

## 6. Walkthrough

1. **Level 1** — a single `BlockingQueue` holds two unrelated events with no way to separate them by topic; any consumer polling it gets whatever was written first, regardless of what kind of event it is.
2. **Level 2, publishing** — `broker.publish("order-events", ...)` and `broker.publish("payment-events", ...)` each resolve to their *own* `BlockingQueue` via `computeIfAbsent`, keyed by destination name — this is the routing responsibility a real broker's queues or topics provide.
3. **Level 2, polling** — `broker.poll("order-events")` only ever returns messages published to that specific destination, so an order service and a payment service can share one broker instance without their event streams interfering.
4. **Level 3, the new `Broker` constructor** — takes a `storageDir` and creates it on disk, modeling that a real broker keeps its own persistent storage independent of any client process's memory.
5. **Level 3, `publish` writing to disk** — every publish appends a line to a per-destination log file with `StandardOpenOption.APPEND`, so the write survives even if the JVM crashes immediately afterward — this is the durability a real broker (Kafka's commit log, RabbitMQ's persistent queues) provides.
6. **Level 3, simulating a restart** — `main` creates two *separate* `Broker` objects pointing at the same `storageDir`: the first represents the producer's process before it exits, the second represents an entirely new process reading from the same durable storage afterward.
7. **Level 3, recovery** — `consumerProcessAfterRestart.readAll(...)` reads both previously published messages back from disk, proving they were never held only in the producer's memory — exactly the property that lets a consumer be offline when a message is sent and still receive it later, which is what makes the [asynchronous messaging model](0111-asynchronous-messaging-model.md) actually reliable rather than just "fire into the void."

## 7. Gotchas & takeaways

> **Gotcha:** treating the broker as infinitely reliable "fire and forget" storage is a mistake — every real broker has its own durability configuration (in-memory vs. disk-synced, replication factor, retention period), and the *default* settings for many brokers favor throughput over durability, so an unconfigured broker can still lose messages on a crash.

- A message broker centralizes the durability, routing, and delivery logic that would otherwise be reimplemented, inconsistently, inside every service.
- Real brokers expose named destinations (queues or topics) so unrelated event streams can share the same infrastructure without colliding.
- Durability — persisting a message to storage that survives a process crash or restart — is the property that makes asynchronous messaging trustworthy rather than best-effort.
- Popular production brokers (Kafka, RabbitMQ, ActiveMQ, SQS/SNS) differ significantly in their delivery model, ordering guarantees, and persistence trade-offs; "a broker" is not one interchangeable thing.
- Introduce a broker once more than one service needs to exchange asynchronous events — it is the infrastructure that makes the [asynchronous messaging model](0111-asynchronous-messaging-model.md) practical at more than toy scale.
