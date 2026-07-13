---
card: microservices
gi: 433
slug: spring-boot-test-slices-for-kafka-rabbitmq
title: "Spring Boot test slices for Kafka/RabbitMQ"
---

## 1. What it is

Testing a service that publishes or consumes messages needs its own strategy, distinct from testing HTTP endpoints or database repositories, because messaging semantics — topics, partitions, exchanges, routing keys, acknowledgments, redelivery — don't map cleanly onto either a mock or a slice the way [web layer](0425-web-layer-tests-webmvctest-webfluxtest.md) or [data layer](0426-data-layer-tests-datajpatest-etc.md) tests do. Spring Boot offers two complementary approaches for Kafka and RabbitMQ: a **lightweight embedded/test broker** (`@EmbeddedKafka` for Kafka, `spring-rabbit-test`'s `TestRabbitTemplate` for RabbitMQ) that runs an in-process, throwaway broker for fast tests, and a **real containerized broker** via [Testcontainers](0428-testcontainers-integration-for-real-db-broker-in-tests.md), which runs the actual broker engine in Docker for higher-fidelity tests. Neither replaces the other; they sit at different points on the same speed-versus-realism trade-off already familiar from [data layer tests](0426-data-layer-tests-datajpatest-etc.md).

## 2. Why & when

You reach for a broker-aware test specifically because a hand-rolled fake, or mocking `KafkaTemplate`/`RabbitTemplate` directly, cannot verify the parts of messaging code most likely to break in production:

- **Serialization and deserialization are real risks.** A producer and consumer agreeing on a message schema is exactly the kind of thing a mock trivially "agrees with itself" about, while a real broker round-trip catches an actual mismatch — a missing `@JsonProperty`, an enum that serializes differently than expected, a schema-registry incompatibility.
- **Kafka's partitioning and consumer-group semantics have no faithful mock.** Which partition a message lands on, how a consumer group's offset tracking behaves after a rebalance, and whether a listener actually receives messages produced before it started are all real broker behaviors a mocked `KafkaTemplate` can't meaningfully exercise.
- **RabbitMQ's exchange/routing/queue-binding logic is similarly real infrastructure**, not application code — a message routed with the wrong routing key silently disappearing (or landing on the wrong queue) is a configuration bug that only a real broker's routing engine can surface.
- **`@EmbeddedKafka` is fast and self-contained**, ideal for the bulk of messaging tests during development and in CI without requiring Docker, at the cost of being a simplified, in-memory approximation of real Kafka rather than the genuine broker.
- **Testcontainers-backed broker tests are slower but maximally faithful**, reserved for the smaller number of tests where catching a real-broker-specific behavior (exact partition assignment, exact redelivery timing) matters enough to justify the extra startup cost.

You reach for `@EmbeddedKafka`/`TestRabbitTemplate` as the default for most listener and producer logic tests, and reach for Testcontainers when a test specifically needs to verify behavior the embedded substitute can't faithfully reproduce — exactly the same reasoning that governs choosing between an embedded database and a containerized one in [data layer tests](0426-data-layer-tests-datajpatest-etc.md).

## 3. Core concept

Picture testing a postal sorting system. A cardboard mock-up of a sorting facility (mocking `KafkaTemplate` directly) can confirm your address-labeling logic runs without crashing, but it can't tell you whether a letter with a slightly malformed postcode actually gets routed to the right bin. A small, real, in-house test sorting machine (`@EmbeddedKafka`) genuinely sorts real envelopes through real sorting logic, fast and self-contained, though it's a simplified version of the giant regional sorting facility. Occasionally, you send a batch through the *actual* regional facility itself (a Testcontainers-backed real broker) to be certain nothing about the simplified version was hiding a real-facility-specific quirk.

Concretely, the two approaches differ in three ways:

1. **What's running** — `@EmbeddedKafka` starts an in-process, in-memory Kafka broker inside the JVM running the test; a Testcontainers `KafkaContainer` starts the real Kafka broker binary inside Docker.
2. **How it's wired** — `@EmbeddedKafka(partitions = 1, topics = "order-events")` auto-configures Spring Kafka's `bootstrap-servers` property to point at the embedded broker; Testcontainers requires `@ServiceConnection` (or manual property wiring) pointing at the container's mapped port, as shown in [Testcontainers integration](0428-testcontainers-integration-for-real-db-broker-in-tests.md).
3. **What a test asserts** — both let a test produce a real message and assert a `@KafkaListener` (or `@RabbitListener`) actually receives and processes it, typically synchronized with `awaitility`-style polling or a `CountDownLatch`, since message delivery is inherently asynchronous.

```java
@SpringBootTest
@EmbeddedKafka(partitions = 1, topics = "order-events")
class OrderEventListenerTest {
    @Autowired KafkaTemplate<String, String> kafkaTemplate;
    @Autowired OrderEventListener listener; // has a way to observe processed events

    @Test
    void listenerProcessesPublishedEvent() throws Exception {
        kafkaTemplate.send("order-events", "order-1", "{\"status\":\"CREATED\"}");
        // await() until the listener has processed the message, then assert.
    }
}
```

`@EmbeddedKafka` boots a real, if simplified, broker in-process — the `@KafkaListener` under test genuinely subscribes and genuinely receives a real message, not a directly-invoked method call.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EmbeddedKafka runs a lightweight in-process broker for fast tests; Testcontainers runs the real broker binary in Docker for higher fidelity; both let a test produce a real message and assert a listener actually receives and processes it asynchronously">
  <text x="160" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@EmbeddedKafka</text>
  <rect x="40" y="35" width="240" height="90" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="160" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">in-process, in-memory broker</text>
  <text x="160" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fast, no Docker required</text>
  <text x="160" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">simplified approximation</text>
  <text x="160" y="110" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">default for most tests</text>

  <text x="480" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Testcontainers broker</text>
  <rect x="360" y="35" width="240" height="90" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="480" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">real broker binary in Docker</text>
  <text x="480" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">slower, needs Docker</text>
  <text x="480" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">maximum fidelity</text>
  <text x="480" y="110" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">for real-broker-specific cases</text>

  <line x1="160" y1="125" x2="160" y2="160" stroke="#79c0ff" stroke-dasharray="3,2"/>
  <line x1="480" y1="125" x2="480" y2="160" stroke="#f0883e" stroke-dasharray="3,2"/>

  <rect x="130" y="160" width="410" height="80" rx="10" fill="#1c2430" stroke="#8b949e"/>
  <text x="335" y="185" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">produce real message -> @KafkaListener/@RabbitListener receives it</text>
  <text x="335" y="203" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">assert ASYNCHRONOUSLY (CountDownLatch / await)</text>
  <text x="335" y="221" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">because delivery is never instantaneous</text>
</svg>

Embedded brokers give speed for most tests; Testcontainers-backed real brokers give fidelity for the cases that need it; both require asynchronous assertion because delivery is never synchronous.

## 5. Runnable example

Scenario: an `OrderEventListener` consuming order-created events from a topic. We model the async produce/consume/assert pattern in plain Java first, then show the real `@EmbeddedKafka` shape, then handle a production-flavored hard case: asserting a listener's *retry and dead-letter* behavior when message processing fails.

### Level 1 — Basic

```java
// File: AsyncMessagingPatternBasic.java -- models the CORE pattern every
// broker-backed test follows: produce a message, then WAIT for it to be
// asynchronously processed before asserting anything, using a
// CountDownLatch as a stand-in for real broker-driven listener invocation.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AsyncMessagingPatternBasic {
    static class OrderEventListener {
        final AtomicReference<String> lastProcessed = new AtomicReference<>();
        final CountDownLatch processedLatch = new CountDownLatch(1);

        // Simulates a @KafkaListener method: invoked asynchronously when a message arrives.
        void onMessage(String payload) {
            System.out.println("[OrderEventListener] processing: " + payload);
            lastProcessed.set(payload);
            processedLatch.countDown();
        }
    }

    // Simulates a broker delivering a produced message to the listener on a background thread.
    static void produceAsync(OrderEventListener listener, String payload) {
        new Thread(() -> {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {}
            listener.onMessage(payload);
        }).start();
    }

    public static void main(String[] args) throws InterruptedException {
        OrderEventListener listener = new OrderEventListener();
        produceAsync(listener, "{\"orderId\":\"order-1\",\"status\":\"CREATED\"}");

        boolean processedInTime = listener.processedLatch.await(2, TimeUnit.SECONDS);
        System.out.println("Processed in time: " + processedInTime + ", lastProcessed=" + listener.lastProcessed.get());
    }
}
```

How to run: `java AsyncMessagingPatternBasic.java`

`processedLatch.await(2, TimeUnit.SECONDS)` is the essential shape every real broker-backed test needs: message delivery happens on a separate thread (in a real broker, over the network, on a listener container thread), so a test can never assert immediately after producing — it must wait for processing to actually complete, with a bounded timeout so a genuine bug (the listener never fires) fails the test instead of hanging forever.

### Level 2 — Intermediate

```java
// File: EmbeddedKafkaRealShapeIntermediate.java -- the SAME async pattern,
// now in its REAL Spring Kafka form using @EmbeddedKafka, @KafkaListener,
// and KafkaTemplate, as it would really be written and run under
// Maven/Gradle with spring-kafka-test on the classpath.
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.test.context.EmbeddedKafka;
import org.springframework.stereotype.Component;
import org.springframework.test.context.TestPropertySource;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

public class EmbeddedKafkaRealShapeIntermediate {

    @Component
    static class OrderEventListener {
        final AtomicReference<String> lastPayload = new AtomicReference<>();
        final CountDownLatch latch = new CountDownLatch(1);

        @KafkaListener(topics = "order-events", groupId = "test-group")
        void onMessage(String payload) {
            lastPayload.set(payload);
            latch.countDown();
        }
    }

    @SpringBootTest
    @EmbeddedKafka(partitions = 1, topics = "order-events")
    @TestPropertySource(properties = {
            "spring.kafka.consumer.auto-offset-reset=earliest"
    })
    static class OrderEventListenerTest {
        @Autowired KafkaTemplate<String, String> kafkaTemplate;
        @Autowired OrderEventListener listener;

        @Test
        void listenerReceivesPublishedEvent() throws Exception {
            kafkaTemplate.send("order-events", "order-1", "{\"status\":\"CREATED\"}");

            boolean received = listener.latch.await(10, TimeUnit.SECONDS);

            assertThat(received).isTrue();
            assertThat(listener.lastPayload.get()).isEqualTo("{\"status\":\"CREATED\"}");
        }
    }
}
```

How to run: requires `spring-kafka` and `spring-kafka-test` on the classpath; run as a JUnit 5 test via `mvn test` or your IDE's test runner (no Docker required, since `@EmbeddedKafka` runs entirely in-process).

`@EmbeddedKafka(partitions = 1, topics = "order-events")` starts a real, in-process Kafka broker and pre-creates the topic; Spring Boot auto-configures `spring.kafka.bootstrap-servers` to point at it. `kafkaTemplate.send` produces a genuine message through Spring Kafka's real producer machinery, and the real `@KafkaListener` genuinely receives it asynchronously — `latch.await` is what makes the test wait correctly instead of racing ahead of the listener.

### Level 3 — Advanced

```java
// File: ListenerRetryDeadLetterAdvanced.java -- the SAME listener, now
// handling a PRODUCTION-FLAVORED hard case: a message that fails processing
// and must be RETRIED a bounded number of times before landing on a
// dead-letter topic, verified against a real embedded broker so the retry
// and DLT routing genuinely exercise Spring Kafka's error-handling machinery.
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.annotation.RetryableTopic;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.retrytopic.DltStrategy;
import org.springframework.kafka.test.context.EmbeddedKafka;
import org.springframework.stereotype.Component;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

public class ListenerRetryDeadLetterAdvanced {

    @Component
    static class FlakyOrderEventListener {
        final AtomicInteger attempts = new AtomicInteger(0);
        final AtomicReference<String> deadLetterPayload = new AtomicReference<>();
        final CountDownLatch dltLatch = new CountDownLatch(1);

        // Fails every attempt on the main topic (simulating a downstream outage),
        // retried automatically by Spring Kafka, and eventually routed to a DLT.
        @RetryableTopic(attempts = "3", dltStrategy = DltStrategy.FAIL_ON_ERROR)
        @KafkaListener(topics = "order-events", groupId = "flaky-group")
        void onMessage(String payload) {
            int attemptNumber = attempts.incrementAndGet();
            System.out.println("[FlakyOrderEventListener] attempt " + attemptNumber + " for payload=" + payload);
            throw new IllegalStateException("simulated downstream failure on attempt " + attemptNumber);
        }

        // Spring Kafka routes to "order-events-dlt" after retries are exhausted.
        @KafkaListener(topics = "order-events-dlt", groupId = "flaky-group-dlt")
        void onDeadLetter(String payload) {
            System.out.println("[FlakyOrderEventListener] received on DEAD LETTER topic: " + payload);
            deadLetterPayload.set(payload);
            dltLatch.countDown();
        }
    }

    @SpringBootTest
    @EnableKafka
    @EmbeddedKafka(partitions = 1, topics = {"order-events", "order-events-retry-0", "order-events-dlt"})
    static class FlakyOrderEventListenerTest {
        @Autowired KafkaTemplate<String, String> kafkaTemplate;
        @Autowired FlakyOrderEventListener listener;

        @Test
        void exhaustsRetriesThenRoutesToDeadLetterTopic() throws Exception {
            kafkaTemplate.send("order-events", "order-1", "{\"status\":\"CREATED\"}");

            boolean reachedDlt = listener.dltLatch.await(30, TimeUnit.SECONDS);

            assertThat(reachedDlt).isTrue();
            assertThat(listener.attempts.get()).isEqualTo(3); // main attempt count Spring Kafka configured
            assertThat(listener.deadLetterPayload.get()).isEqualTo("{\"status\":\"CREATED\"}");
        }
    }
}
```

How to run: requires `spring-kafka` and `spring-kafka-test` with retryable-topic support on the classpath; run as a JUnit 5 test via `mvn test` or your IDE's test runner. This test can take real wall-clock time (retry backoff plus the 30-second await), since Spring Kafka's retry topic mechanism genuinely waits between attempts against the real embedded broker.

The hard case here is that `@RetryableTopic` isn't application code your test directly calls — it's Spring Kafka's own infrastructure, configuring additional retry topics and a dead-letter topic behind the scenes. Only a real (even if embedded) broker can exercise this correctly: a mocked `KafkaTemplate` would never actually route a failed message through Spring Kafka's retry-topic machinery, because that machinery *is* broker-level topic routing, not a Java method call the test could intercept directly.

## 6. Walkthrough

Trace `exhaustsRetriesThenRoutesToDeadLetterTopic` in order. **First**, `kafkaTemplate.send("order-events", "order-1", ...)` produces the message to the real embedded broker's `order-events` topic. Spring Kafka's `@KafkaListener` on `onMessage` picks it up on attempt 1, immediately throws `IllegalStateException`, and `attempts` becomes `1`.

**Next**, because `@RetryableTopic(attempts = "3", ...)` is configured, Spring Kafka's error-handling infrastructure — not the test, not application retry code — automatically republishes the failed message to an internal retry topic (`order-events-retry-0`) after a backoff delay, and the same listener consumes it again from there. `onMessage` runs a second time, throws again, `attempts` becomes `2`.

**Then**, the same retry-and-republish cycle happens once more: `onMessage` runs a third time (the configured attempt limit), throws a third time, and `attempts` becomes `3`. Having now exhausted all configured attempts, Spring Kafka's retry-topic machinery — per `DltStrategy.FAIL_ON_ERROR` — routes the message to the dead-letter topic, `order-events-dlt`.

**Finally**, the separate `@KafkaListener` on `onDeadLetter`, subscribed to `order-events-dlt`, receives the message, records its payload into `deadLetterPayload`, and counts down `dltLatch`. The test's `await` unblocks, and all three assertions pass: the message did reach the DLT, exactly three attempts were made on the main path, and the DLT payload matches what was originally produced.

```
send("order-events", "order-1", {"status":"CREATED"})
  attempt 1 -> IllegalStateException -> retried
  attempt 2 -> IllegalStateException -> retried
  attempt 3 -> IllegalStateException -> retries exhausted
  -> routed to order-events-dlt
  onDeadLetter received: {"status":"CREATED"}

Test result: exhaustsRetriesThenRoutesToDeadLetterTopic PASSED
  reachedDlt = true, attempts = 3, deadLetterPayload = {"status":"CREATED"}
```

## 7. Gotchas & takeaways

> Forgetting to `await` (via `CountDownLatch`, Awaitility, or an equivalent) before asserting is the single most common mistake in broker-backed tests — because delivery and processing are genuinely asynchronous, an assertion placed immediately after `send(...)` will very often run before the listener has processed anything, producing a flaky test that fails intermittently depending on timing rather than on actual correctness.

- `@EmbeddedKafka` and `spring-rabbit-test`'s `TestRabbitTemplate` give fast, Docker-free tests for the bulk of listener and producer logic; reach for [Testcontainers](0428-testcontainers-integration-for-real-db-broker-in-tests.md) specifically when a test needs real-broker-specific fidelity.
- Every broker-backed assertion needs a bounded wait for asynchronous processing to complete — never assert immediately after producing a message.
- Retry and dead-letter-topic behavior (`@RetryableTopic` for Kafka, dead-letter exchanges for RabbitMQ) is broker-level infrastructure, not application code — it can only be genuinely verified against a real (even if embedded) broker, never against a mocked template.
- Keep broker-backed tests as a smaller, higher-value layer above [unit-tested](0412-unit-testing-services.md) message-handling logic — push as much business logic as possible into plain methods a fast unit test can cover, reserving broker-backed tests for the plumbing itself.
- See [Testcontainers integration](0428-testcontainers-integration-for-real-db-broker-in-tests.md) for the higher-fidelity alternative when embedded-broker quirks (partition assignment timing, exact redelivery semantics) become a real risk worth the extra test cost.
