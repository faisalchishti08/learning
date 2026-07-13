---
card: microservices
gi: 428
slug: testcontainers-integration-for-real-db-broker-in-tests
title: "Testcontainers integration for real DB/broker in tests"
---

## 1. What it is

**Testcontainers** is a Java library that programmatically starts real Docker containers — a real PostgreSQL, a real Kafka broker, a real RabbitMQ instance — for the lifetime of a test run, and tears them down afterward. Instead of testing against an embedded, in-memory substitute (like H2 standing in for PostgreSQL) or a hand-rolled fake, your test runs against the *actual* database or broker engine your production system uses, just running in a disposable, isolated container rather than a long-lived shared environment. Spring Boot has first-class integration via `@Testcontainers`, `@Container`, and the `@ServiceConnection` annotation, which automatically wires a started container's connection details into the Spring context — no manual property overrides required.

## 2. Why & when

You reach for Testcontainers specifically to close the gap embedded substitutes and fakes leave open — the risk that your tests pass against a stand-in that behaves differently from what production actually runs:

- **Embedded databases don't always match production behavior.** H2, used by default in [`@DataJpaTest`](0426-data-layer-tests-datajpatest-etc.md), doesn't enforce every constraint, dialect quirk, or query behavior identically to PostgreSQL or MySQL — a test can pass against H2 and fail against the real engine, or worse, pass against both while silently relying on behavior that differs subtly between them.
- **Brokers have no meaningful embedded substitute for many test scenarios.** There's no faithful in-memory stand-in for Kafka's partition/offset semantics or RabbitMQ's exchange/routing behavior — testing against the real broker, even in a disposable container, is the only way to verify your code handles them correctly.
- **Tests stay isolated and repeatable.** Each test run (or each test class, depending on lifecycle configuration) gets a fresh container, so there's no shared, possibly-polluted "the test database" that different test runs or different developers step on each other's toes over.
- **CI and local development run against the same thing.** A container defined once in test code behaves identically on a developer's laptop and in a CI pipeline, removing the "works on my machine" gap that a shared external test environment often introduces.

You reach for Testcontainers whenever a test needs a real database or broker engine and the stakes of embedded-substitute drift are too high to accept — which, for most production-grade microservices, means most integration-level persistence and messaging tests, not just a handful of edge cases.

## 3. Core concept

Picture a fire drill using a real, disposable smoke machine instead of asking everyone to just imagine smoke. Imagining smoke (an embedded substitute) is fast and doesn't set off any real alarms, but it can't tell you whether the *actual* smoke detectors, in their *actual* positions, actually trigger correctly. A real, contained smoke machine (Testcontainers) produces the real physical stimulus your real equipment has to react to — and once the drill ends, the smoke clears and the room resets, ready for the next drill, without needing a dedicated permanent smoke-filled room somewhere in the building.

Concretely, using Testcontainers in a Spring Boot test has three parts:

1. **Declare the container** — a `PostgreSQLContainer`, `KafkaContainer`, or `RabbitMQContainer` (from the `org.testcontainers` library), specifying the Docker image to run.
2. **Wire it into the Spring context** — annotate the field `@Container` (so JUnit's Testcontainers extension manages its lifecycle) and `@ServiceConnection` (so Spring Boot automatically configures the relevant `DataSource`/`spring.kafka.bootstrap-servers`/etc. from the running container, no manual `@DynamicPropertySource` boilerplate needed).
3. **Let the container lifecycle track the test lifecycle** — by default, one container per test class, started before any test runs and stopped after the last one finishes; Testcontainers can reuse containers across test classes for speed if explicitly configured to do so.

```java
@SpringBootTest
@Testcontainers
class OrderRepositoryContainerTest {
    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired OrderRepository orderRepository;

    @Test
    void persistsAndReadsBackAgainstRealPostgres() {
        orderRepository.save(new Order("order-1", "PENDING"));
        assertThat(orderRepository.findById("order-1")).isPresent();
    }
}
```

`@ServiceConnection` inspects the running `postgres` container and automatically configures Spring's `DataSource` to point at it — the same `OrderRepository` code that would run against production PostgreSQL is now genuinely exercised against a real (if disposable) PostgreSQL instance.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A test class starts a real Docker container for a database or broker before tests run, Spring Boot auto-configures its connection into the ApplicationContext via ServiceConnection, tests run against the real engine, and the container is torn down after the last test">
  <rect x="30" y="30" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="100" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Container</text>
  <text x="100" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">PostgreSQLContainer</text>

  <line x1="170" y1="55" x2="240" y2="55" stroke="#79c0ff" stroke-width="2"/>
  <text x="205" y="45" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">starts</text>

  <rect x="240" y="20" width="150" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">real Docker container</text>
  <text x="315" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">postgres:16-alpine</text>
  <text x="315" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">random host port</text>

  <line x1="315" y1="90" x2="315" y2="130" stroke="#f0883e" stroke-width="2" stroke-dasharray="3,2"/>
  <text x="380" y="115" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">@ServiceConnection</text>

  <rect x="240" y="130" width="150" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="315" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring ApplicationContext</text>
  <text x="315" y="172" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DataSource auto-wired</text>

  <line x1="390" y1="160" x2="460" y2="160" stroke="#6db33f" stroke-width="2"/>

  <rect x="460" y="130" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="535" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test code</text>
  <text x="535" y="172" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real queries, real engine</text>

  <text x="320" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">container is torn down automatically after the last test in the class</text>
</svg>

Testcontainers starts a real database or broker in Docker, Spring Boot auto-wires its connection details, and the container disappears when the tests finish.

## 5. Runnable example

Scenario: an `OrderRepository` persisted against a real database engine. We model the container lifecycle in plain Java first, then show the real `@Testcontainers`/`@ServiceConnection` shape, then handle a production-flavored case: a container-backed Kafka test verifying a consumer actually reads real, partitioned messages.

### Level 1 — Basic

```java
// File: ContainerLifecycleBasic.java -- models the CORE lifecycle idea
// Testcontainers manages: start a real resource before tests, hand back its
// connection details, and stop it afterward -- before introducing Docker.
public class ContainerLifecycleBasic {
    // A stand-in for a real Testcontainers-managed container: it "starts,"
    // exposes a connection detail, and "stops."
    static class FakeManagedContainer {
        private boolean running = false;
        private int mappedPort;

        void start() {
            running = true;
            mappedPort = 54320 + (int) (Math.random() * 100); // simulating a real, dynamically-mapped host port
            System.out.println("[Container] started, mapped host port=" + mappedPort);
        }
        String jdbcUrl() {
            if (!running) throw new IllegalStateException("container not running");
            return "jdbc:postgresql://localhost:" + mappedPort + "/test";
        }
        void stop() {
            System.out.println("[Container] stopped, port " + mappedPort + " released");
            running = false;
        }
    }

    public static void main(String[] args) {
        FakeManagedContainer container = new FakeManagedContainer();
        container.start();
        System.out.println("Test code would connect to: " + container.jdbcUrl());
        container.stop();
    }
}
```

How to run: `java ContainerLifecycleBasic.java`

`FakeManagedContainer` mirrors the essential lifecycle Testcontainers provides for real: `start()` boots a real process on a dynamically assigned host port (so parallel test runs never collide on a fixed port), exposes a connection string derived from that port, and `stop()` tears everything down. Real Testcontainers does this with an actual Docker container instead of a simulated port number, but the shape test code depends on is identical.

### Level 2 — Intermediate

```java
// File: TestcontainersRealShapeIntermediate.java -- the SAME lifecycle, now
// in its REAL Spring Boot + Testcontainers form using @Testcontainers,
// @Container, and @ServiceConnection, as it would really be written and run
// under Maven/Gradle with the testcontainers-postgresql and
// spring-boot-testcontainers dependencies on the classpath (and Docker
// available on the machine running the tests).
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

public class TestcontainersRealShapeIntermediate {

    @Entity
    static class Order {
        @Id String id;
        String status;
        protected Order() {}
        Order(String id, String status) { this.id = id; this.status = status; }
    }

    interface OrderRepository extends JpaRepository<Order, String> {}

    @SpringBootTest
    @Testcontainers
    static class OrderRepositoryContainerTest {

        @Container
        @ServiceConnection
        static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

        @Autowired OrderRepository orderRepository;

        @Test
        void persistsAndReadsBackAgainstRealPostgres() {
            orderRepository.save(new Order("order-1", "PENDING"));

            Optional<Order> found = orderRepository.findById("order-1");
            assertThat(found).isPresent();
            assertThat(found.get().status).isEqualTo("PENDING");
        }
    }
}
```

How to run: requires `testcontainers`, `testcontainers-postgresql`, `spring-boot-testcontainers`, `spring-boot-starter-data-jpa`, and a running Docker daemon; run as a JUnit 5 test via `mvn test` or your IDE's test runner (never with plain `java`, since it needs Docker to launch the container).

`@Container` tells the Testcontainers JUnit 5 extension to manage `postgres`'s lifecycle — starting it before any test in the class and stopping it after the last one. `@ServiceConnection` is the key piece of Spring Boot integration: it inspects the running container and automatically configures the `DataSource` bean, with no manual `spring.datasource.url` property override needed. `orderRepository.save` and `findById` then run against a genuinely real PostgreSQL instance, not H2.

### Level 3 — Advanced

```java
// File: TestcontainersKafkaAdvanced.java -- the SAME idea, now applied to a
// BROKER instead of a database, handling a PRODUCTION-FLAVORED hard case: a
// consumer must actually read a real message off a real Kafka topic, proving
// serialization AND partition/offset handling work against the real engine
// -- something no embedded substitute can meaningfully verify.
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.KafkaContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import java.time.Duration;
import java.util.List;
import java.util.Properties;

import static org.assertj.core.api.Assertions.assertThat;

@Testcontainers
public class TestcontainersKafkaAdvanced {

    @Container
    static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.6.0"));

    @Test
    void producesAndConsumesRealMessageThroughRealKafka() {
        String topic = "order-events";
        String bootstrapServers = kafka.getBootstrapServers();

        // Produce a REAL message to a REAL, running Kafka broker.
        Properties producerProps = new Properties();
        producerProps.put("bootstrap.servers", bootstrapServers);
        producerProps.put("key.serializer", StringSerializer.class.getName());
        producerProps.put("value.serializer", StringSerializer.class.getName());

        try (KafkaProducer<String, String> producer = new KafkaProducer<>(producerProps)) {
            producer.send(new ProducerRecord<>(topic, "order-1", "{\"status\":\"CREATED\"}"));
            producer.flush();
        }

        // Consume it back with a REAL consumer, proving partitioning, offsets,
        // and serialization all genuinely round-trip through the real broker.
        Properties consumerProps = new Properties();
        consumerProps.put("bootstrap.servers", bootstrapServers);
        consumerProps.put("key.deserializer", StringDeserializer.class.getName());
        consumerProps.put("value.deserializer", StringDeserializer.class.getName());
        consumerProps.put("group.id", "test-group");
        consumerProps.put("auto.offset.reset", "earliest");

        try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(consumerProps)) {
            consumer.subscribe(List.of(topic));
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofSeconds(10));

            assertThat(records.count()).isEqualTo(1);
            ConsumerRecord<String, String> record = records.iterator().next();
            assertThat(record.key()).isEqualTo("order-1");
            assertThat(record.value()).isEqualTo("{\"status\":\"CREATED\"}");
        }
    }
}
```

How to run: requires `testcontainers`, `testcontainers-kafka`, and the Kafka client library on the classpath, plus a running Docker daemon; run as a JUnit 5 test via `mvn test` or your IDE's test runner.

The hard case is that Kafka's semantics — topics, partitions, consumer groups, offset tracking — have no faithful embedded substitute; an in-memory fake `KafkaTemplate` would trivially "deliver" whatever was "produced" without ever exercising partition assignment or offset commit behavior. Running against a real, containerized broker means `consumer.poll` genuinely has to negotiate a partition assignment and read a real offset from a real log segment, catching a whole class of bugs — serialization mismatches, consumer group misconfiguration, topic-name typos — that a fake broker would silently paper over.

## 6. Walkthrough

Trace `producesAndConsumesRealMessageThroughRealKafka` in order. **First**, the `@Testcontainers` JUnit 5 extension starts the `kafka` container before this test class's tests run — a real Kafka broker process, inside Docker, listening on a dynamically mapped port that `kafka.getBootstrapServers()` reports back.

**Next**, a real `KafkaProducer` is constructed pointed at that broker, and `producer.send(new ProducerRecord<>("order-events", "order-1", "{\"status\":\"CREATED\"}"))` sends a genuine message. `producer.flush()` blocks until the broker has actually acknowledged receipt — this is a real network round trip to a real broker process, not an in-memory hand-off.

**Then**, a real `KafkaConsumer` is constructed with `group.id = "test-group"` and `auto.offset.reset = "earliest"` (so it reads from the beginning of the topic rather than only new messages). `consumer.subscribe(List.of("order-events"))` triggers the broker to assign this consumer a partition for that topic — a genuine consumer-group coordination handshake.

**Finally**, `consumer.poll(Duration.ofSeconds(10))` blocks, polling the real broker, until it receives the previously produced record (or the timeout elapses). The returned `ConsumerRecords` contains exactly one record, whose `key` and `value` match what was produced — proving the full round trip through a real broker, including serialization, partition assignment, and offset tracking, all worked correctly.

```
[Testcontainers] Kafka container started, bootstrap-servers=localhost:xxxxx
producer.send(topic=order-events, key=order-1, value={"status":"CREATED"}) -> ack received
consumer.subscribe([order-events]) -> partition assigned
consumer.poll(10s) -> 1 record received
  key=order-1 value={"status":"CREATED"}

Test result: producesAndConsumesRealMessageThroughRealKafka PASSED
```

## 7. Gotchas & takeaways

> Testcontainers requires a working Docker (or compatible) daemon on whatever machine runs the tests — a CI runner without Docker access, or a developer's locked-down laptop, simply can't run these tests at all. Always confirm your CI environment supports Docker-in-Docker or an equivalent before committing a suite to Testcontainers-based tests, and keep a clear error message (Testcontainers usually provides one) rather than a mysterious hang when Docker isn't available.

- Testcontainers trades test speed (containers take real seconds to start) for fidelity (the real engine, not a substitute) — reserve it for the tests where that fidelity genuinely matters, and keep the bulk of fast checks at lower layers of the [test pyramid](0411-test-pyramid-for-microservices.md).
- `@ServiceConnection` removes the manual `@DynamicPropertySource` boilerplate older Spring Boot versions required to wire a container's connection details into the context — prefer it in any reasonably current Spring Boot version.
- Container reuse (via `.withReuse(true)` and a Testcontainers configuration flag) can meaningfully speed up local development by keeping a container alive across test runs, but it changes the isolation guarantees, so use it deliberately, not by default.
- Pair Testcontainers-backed database tests with [data layer tests](0426-data-layer-tests-datajpatest-etc.md) to decide when the embedded H2 default is good enough versus when real-engine fidelity is worth the extra startup cost.
- See [Spring Boot test slices for Kafka/RabbitMQ](0433-spring-boot-test-slices-for-kafka-rabbitmq.md) for how broker-specific test slices and Testcontainers combine in practice for messaging-heavy services.
