---
card: spring-boot
gi: 171
slug: spring-integration-auto-config
title: Spring Integration auto-config
---

## 1. What it is

**Spring Integration** implements Enterprise Integration Patterns (EIP) — a vocabulary of pipes, filters, routers, and adapters for connecting systems. Spring Boot auto-configures it when `spring-integration-core` is on the classpath: it wires a default `IntegrationFlow` DSL context, auto-detects `@MessagingGateway` interfaces, and starts channel adapters declared as beans, with no XML required.

Think of it as LEGO for integration plumbing: channels are the pipes, endpoints are the bricks, and messages flow through the assembled structure.

## 2. Why & when

**Why Spring Integration:**
- Unifies disparate transports (JMS, AMQP, HTTP, files, FTP, TCP) behind a common `Message<T>` abstraction.
- Lets you describe complex routing, transformation, and aggregation without custom code.
- Patterns like splitter, aggregator, and content-based router encode hard-won integration wisdom from the EIP book.

**When to use:**
- ETL-style flows: read from a file, transform, route, write to a database.
- Orchestrating multiple messaging systems (read from Kafka, enrich from HTTP, publish to JMS).
- Enterprise workflows where routing logic would otherwise be scattered across many `if/else` blocks.

**Not ideal for:** simple point-to-point messaging where `@KafkaListener` alone suffices.

## 3. Core concept

Spring Integration's building blocks:

- **Message:** immutable wrapper — `payload` + `headers`.
- **MessageChannel:** the pipe. `DirectChannel` delivers synchronously; `QueueChannel` buffers asynchronously.
- **Message Endpoint:** processes or routes messages. Key types:
  - `ServiceActivator` — calls a method and (optionally) puts the return value on an output channel.
  - `Transformer` — converts payload type.
  - `Router` — sends to different channels based on content.
  - `Splitter` — breaks one message into many.
  - `Aggregator` — reassembles many messages into one.
- **IntegrationFlow DSL:** Java fluent API to compose the above into a named flow.
- **@MessagingGateway:** turn a plain Java interface into a Spring Integration entry point — call the method, a message is created and sent to the flow automatically.

Spring Boot auto-config: detects `IntegrationFlow` beans and starts them; no `<int:channel>` XML needed.

## 4. Diagram

<svg viewBox="0 0 740 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Integration flow: gateway sends to channel, transformer, router, two output channels">
  <!-- Gateway -->
  <rect x="10" y="75" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Gateway</text>
  <text x="70" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@MessagingGateway</text>

  <!-- Arrow -->
  <line x1="133" y1="100" x2="170" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ia)"/>

  <!-- Channel -->
  <rect x="175" y="82" width="85" height="36" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="217" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">DirectChannel</text>
  <text x="217" y="113" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">input</text>

  <!-- Arrow -->
  <line x1="263" y1="100" x2="295" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ia)"/>

  <!-- Transformer -->
  <rect x="300" y="75" width="100" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Transformer</text>
  <text x="350" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.transform()</text>

  <!-- Arrow -->
  <line x1="403" y1="100" x2="435" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ia)"/>

  <!-- Router -->
  <rect x="440" y="75" width="90" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Router</text>
  <text x="485" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.route()</text>

  <!-- Arrows to outputs -->
  <line x1="533" y1="90" x2="590" y2="68" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ia)"/>
  <line x1="533" y1="110" x2="590" y2="132" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ia)"/>

  <!-- Output A -->
  <rect x="595" y="52" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="655" y="73" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">orders.channel</text>

  <!-- Output B -->
  <rect x="595" y="116" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="655" y="137" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">dlq.channel</text>

  <text x="370" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Messages flow through the pipe: gateway → channel → transformer → router → target channels</text>

  <defs>
    <marker id="ia" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Messages flow left-to-right through components wired by the `IntegrationFlow` DSL.

## 5. Runnable example

```java
// SpringIntegrationDemo.java — simulates EIP pipes-and-filters without Spring
// How to run: java SpringIntegrationDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-integration-core; use IntegrationFlow DSL + @MessagingGateway

import java.util.*;
import java.util.function.*;

public class SpringIntegrationDemo {

    record Message<T>(T payload, Map<String, Object> headers) {
        static <T> Message<T> of(T payload) {
            return new Message<>(payload, new HashMap<>());
        }
        Message<T> withHeader(String k, Object v) {
            var h = new HashMap<>(headers); h.put(k, v);
            return new Message<>(payload, h);
        }
    }

    // Simulated channels (blocking queues)
    static final Queue<Message<String>> inputChannel  = new ArrayDeque<>();
    static final Queue<Message<String>> ordersChannel = new ArrayDeque<>();
    static final Queue<Message<String>> dlqChannel    = new ArrayDeque<>();

    // @MessagingGateway entry point
    static void gateway(String rawOrder) {
        System.out.println("[Gateway] sending: " + rawOrder);
        inputChannel.offer(Message.of(rawOrder));
    }

    // Transformer: uppercase payload, add header
    static Message<String> transform(Message<String> msg) {
        return msg.withHeader("processed", true)
                  .withHeader("timestamp", System.currentTimeMillis());
        // payload unchanged; in real flows you'd map types here
    }

    // Router: valid orders vs DLQ
    static void route(Message<String> msg) {
        if (msg.payload().startsWith("ORDER")) {
            ordersChannel.offer(msg);
        } else {
            dlqChannel.offer(msg);
        }
    }

    // IntegrationFlow equivalent: wire the pipeline
    static void runFlow() {
        while (!inputChannel.isEmpty()) {
            Message<String> raw = inputChannel.poll();
            Message<String> transformed = transform(raw);
            route(transformed);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Spring Integration Auto-config Demo ===\n");

        // @MessagingGateway calls
        gateway("ORDER-1001: Widget x2");
        gateway("JUNK-BAD-MESSAGE");
        gateway("ORDER-1002: Gadget x1");

        System.out.println("\n[Flow] processing channel...");
        runFlow();

        System.out.println("\n[orders.channel] " + ordersChannel.size() + " messages:");
        ordersChannel.forEach(m -> System.out.println("  payload='" + m.payload() + "' headers=" + m.headers()));

        System.out.println("\n[dlq.channel] " + dlqChannel.size() + " messages:");
        dlqChannel.forEach(m -> System.out.println("  payload='" + m.payload() + "'"));
    }
}
```

**How to run:** `java SpringIntegrationDemo.java`

## 6. Walkthrough

- **`gateway`** simulates the `@MessagingGateway` interface — callers work with plain Java; Spring Integration creates the `Message<T>` automatically.
- **`inputChannel`** is a `DirectChannel` equivalent: synchronous delivery to the next component.
- **`transform`** adds headers (metadata routing, audit timestamps) — real Spring Integration `Transformer` can also convert payload types (e.g., `String` → `Order` POJO).
- **`route`** implements content-based routing — in Spring Integration DSL: `.route(String.class, p -> p.startsWith("ORDER") ? "ordersChannel" : "dlqChannel")`.
- **`runFlow`** ties the components together; the Spring Boot auto-config does this by detecting `IntegrationFlow` beans and subscribing endpoints to channels automatically.

Real Spring Boot DSL equivalent:
```java
@Bean
IntegrationFlow orderFlow() {
    return IntegrationFlow.from("inputChannel")
        .transform(...)
        .route(String.class, p -> p.startsWith("ORDER") ? "ordersChannel" : "dlqChannel")
        .get();
}
```

## 7. Gotchas & takeaways

> `DirectChannel` delivers **on the sender's thread** — if the endpoint blocks, the gateway caller blocks too. Use `QueueChannel` + a poller to decouple threads.

> Spring Integration and Spring Batch often get confused. Integration is about **moving and routing data between systems** in real time. Batch is about **processing large datasets in chunks** offline. They complement each other but solve different problems.

- `spring-boot-starter-integration` includes the core; add adapters separately (`spring-integration-jms`, `spring-integration-amqp`, etc.).
- Auto-config detects `IntegrationFlow` beans and starts them — no explicit `start()` needed.
- `@MessagingGateway(defaultRequestChannel = "inputChannel")` on an interface turns it into a Spring Integration client.
- Use `IntegrationFlow.from(MessageSource, ...)` with a poller for inbound adapters (files, databases) that need polling.
- Spring Integration's management endpoints expose channel stats via Spring Boot Actuator automatically.
