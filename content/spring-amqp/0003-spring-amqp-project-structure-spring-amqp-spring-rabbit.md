---
card: spring-amqp
gi: 3
slug: spring-amqp-project-structure-spring-amqp-spring-rabbit
title: "Spring AMQP project structure (spring-amqp, spring-rabbit)"
---

## 1. What it is

Spring AMQP is organized as two layered modules: `spring-amqp` defines protocol-agnostic abstractions (`Message`, `MessageProperties`, `AmqpTemplate`, `Exchange`/`Queue`/`Binding` domain classes) that don't depend on any specific broker implementation, while `spring-rabbit` provides the RabbitMQ-specific implementations of those abstractions (`RabbitTemplate`, `CachingConnectionFactory`, `SimpleMessageListenerContainer`) built on the RabbitMQ Java client library. In practice, nearly every Spring AMQP application depends on both modules together, since RabbitMQ is by far the most common AMQP broker Spring AMQP is used against.

## 2. Why & when

Understanding this two-module split matters for a few practical reasons:

- **Knowing which abstractions are broker-agnostic versus RabbitMQ-specific** — code written against `AmqpTemplate` (the interface) rather than `RabbitTemplate` (the concrete implementation) is, in principle, more portable to a different AMQP broker, though `spring-rabbit`'s RabbitMQ-specific extensions are what most real applications end up relying on in practice.
- **Understanding error messages and missing-class issues** — a `ClassNotFoundException` for `RabbitTemplate` when only `spring-amqp` is on the classpath (without `spring-rabbit`) is a common early confusion for anyone assuming the single dependency name covers everything.
- **Recognizing what Spring Boot's starter bundles for you** — the `spring-boot-starter-amqp` dependency pulls in both `spring-amqp` and `spring-rabbit` (plus the RabbitMQ client and auto-configuration) as one unit, which is why most day-to-day Spring Boot usage never needs to think about the two-module split at all.

## 3. Core concept

Think of `spring-amqp` as a set of universal electrical outlet shapes and voltage standards defined by an international body, while `spring-rabbit` is the specific adapter and wiring built to plug into RabbitMQ's particular electrical socket. The abstract standard (`spring-amqp`) could theoretically be implemented for a different broker's socket shape, but in practice, everyone building a real appliance (application) plugs in through the RabbitMQ-specific adapter, because that's the socket actually installed in almost every wall (deployment) using Spring AMQP.

```java
// From spring-amqp: broker-agnostic abstractions
import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessageProperties;
import org.springframework.amqp.core.AmqpTemplate;

// From spring-rabbit: RabbitMQ-specific implementations of those abstractions
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.rabbit.connection.CachingConnectionFactory;

@Bean
public AmqpTemplate amqpTemplate(CachingConnectionFactory connectionFactory) {
    return new RabbitTemplate(connectionFactory); // concrete RabbitMQ implementation of the abstract interface
}
```

Application code type against `AmqpTemplate` (the abstraction from `spring-amqp`), while the actual object handed in is a `RabbitTemplate` (the implementation from `spring-rabbit`).

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="spring-amqp defines broker-agnostic abstractions; spring-rabbit provides RabbitMQ-specific implementations of those abstractions built on the RabbitMQ Java client; almost all applications depend on both together" >
  <rect x="20" y="20" width="280" height="55" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">spring-amqp (abstractions)</text>
  <text x="35" y="42" fill="#e6edf3" font-size="7" font-family="monospace">Message, MessageProperties</text>
  <text x="35" y="60" fill="#e6edf3" font-size="7" font-family="monospace">AmqpTemplate, Exchange/Queue/Binding</text>

  <line x1="160" y1="75" x2="160" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a10)"/>
  <text x="220" y="90" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">implemented by</text>

  <rect x="20" y="100" width="280" height="55" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">spring-rabbit (RabbitMQ-specific)</text>
  <text x="35" y="122" fill="#e6edf3" font-size="7" font-family="monospace">RabbitTemplate, CachingConnectionFactory</text>
  <text x="35" y="140" fill="#e6edf3" font-size="7" font-family="monospace">SimpleMessageListenerContainer</text>

  <text x="480" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">spring-boot-starter-amqp bundles both, plus the RabbitMQ client and auto-config</text>
</svg>

Nearly every real application needs both layers together, bundled conveniently by the Boot starter.

## 5. Runnable example

The scenario: modeling the abstraction/implementation relationship between `AmqpTemplate` and `RabbitTemplate`, simulated with a plain interface-and-implementation pair (genuinely runnable Java, since the module-layering concept itself doesn't need an actual broker connection to demonstrate), starting with a basic interface-typed reference, then adding a second hypothetical broker implementation to show what "broker-agnostic" really buys you, then adding a check for what breaks if only the abstraction module were present without an implementation.

### Level 1 — Basic

```java
// AmqpModuleDemo.java
public class AmqpModuleDemo {
    // Stand-in for spring-amqp's AmqpTemplate interface.
    interface AmqpTemplate {
        void send(String exchange, String routingKey, String payload);
    }

    // Stand-in for spring-rabbit's RabbitTemplate implementation.
    static class RabbitTemplate implements AmqpTemplate {
        public void send(String exchange, String routingKey, String payload) {
            System.out.println("[RabbitMQ] sent to exchange=" + exchange + " key=" + routingKey + ": " + payload);
        }
    }

    public static void main(String[] args) {
        AmqpTemplate template = new RabbitTemplate(); // application code depends on the abstraction
        template.send("order.exchange", "order.created", "{\"id\":1}");
    }
}
```

How to run: `java AmqpModuleDemo.java`. Expected output: `[RabbitMQ] sent to exchange=order.exchange key=order.created: {"id":1}` — application code references only the `AmqpTemplate` interface type, even though the concrete object is RabbitMQ-specific.

### Level 2 — Intermediate

```java
// AmqpModuleDemo.java
public class AmqpModuleDemo {
    interface AmqpTemplate {
        void send(String exchange, String routingKey, String payload);
    }

    static class RabbitTemplate implements AmqpTemplate {
        public void send(String exchange, String routingKey, String payload) {
            System.out.println("[RabbitMQ] sent to exchange=" + exchange + " key=" + routingKey + ": " + payload);
        }
    }

    // Real-world concern: the abstraction's value is that ANOTHER broker implementation could
    // satisfy the same interface -- application code calling send(...) wouldn't need to change
    // at all if the underlying broker were swapped (in principle; spring-rabbit is what nearly
    // everyone actually uses in practice).
    static class HypotheticalOtherBrokerTemplate implements AmqpTemplate {
        public void send(String exchange, String routingKey, String payload) {
            System.out.println("[OtherBroker] published to " + exchange + "/" + routingKey + ": " + payload);
        }
    }

    static void publishOrderEvent(AmqpTemplate template) {
        // This method only knows about the abstraction -- it works with either implementation.
        template.send("order.exchange", "order.created", "{\"id\":1}");
    }

    public static void main(String[] args) {
        publishOrderEvent(new RabbitTemplate());
        publishOrderEvent(new HypotheticalOtherBrokerTemplate());
    }
}
```

How to run: `java AmqpModuleDemo.java`. Expected output: both broker implementations print their own broker-tagged confirmation for the identical call to `publishOrderEvent`, demonstrating that code written against the `AmqpTemplate` abstraction is unaffected by which concrete implementation backs it.

### Level 3 — Advanced

```java
// AmqpModuleDemo.java
public class AmqpModuleDemo {
    interface AmqpTemplate {
        void send(String exchange, String routingKey, String payload);
    }

    static class RabbitTemplate implements AmqpTemplate {
        public void send(String exchange, String routingKey, String payload) {
            System.out.println("[RabbitMQ] sent to exchange=" + exchange + " key=" + routingKey + ": " + payload);
        }
    }

    // Production concern: if application code tries to construct an implementation whose
    // module isn't actually present on the classpath, that's a compile/class-loading failure --
    // modeled here as an explicit check standing in for a missing spring-rabbit dependency.
    static AmqpTemplate resolveTemplate(boolean rabbitModulePresent) {
        if (!rabbitModulePresent) {
            throw new IllegalStateException(
                "No AmqpTemplate implementation available -- spring-rabbit (or an equivalent "
                + "broker module) must be on the classpath to obtain a concrete RabbitTemplate");
        }
        return new RabbitTemplate();
    }

    public static void main(String[] args) {
        AmqpTemplate working = resolveTemplate(true);
        working.send("order.exchange", "order.created", "{\"id\":1}");

        try {
            resolveTemplate(false);
        } catch (IllegalStateException ex) {
            System.out.println("Configuration error: " + ex.getMessage());
        }
    }
}
```

How to run: `java AmqpModuleDemo.java`. Expected output: a successful send confirmation, followed by `Configuration error: No AmqpTemplate implementation available -- spring-rabbit (or an equivalent broker module) must be on the classpath to obtain a concrete RabbitTemplate` — modeling the real-world class-loading failure that occurs when `spring-amqp`'s abstractions are referenced but no concrete broker module (`spring-rabbit`) is actually present to satisfy them.

## 6. Walkthrough

Trace how a Spring Boot application actually ends up with a working `AmqpTemplate`.

1. **Dependency declaration**: a Spring Boot application declares `spring-boot-starter-amqp` in its build file — this single starter transitively pulls in `spring-amqp`, `spring-rabbit`, and the underlying `amqp-client` (RabbitMQ's Java client library), so the developer never manually manages the two-module split day to day.
2. **Auto-configuration kicks in**: Spring Boot's AMQP auto-configuration detects these dependencies on the classpath and automatically registers a `CachingConnectionFactory`, a `RabbitTemplate`, and related infrastructure beans, wired up from `application.properties`/`application.yml` connection settings.
3. **Application code depends on the abstraction**: a service class injects `AmqpTemplate` (or, just as commonly in practice, the concrete `RabbitTemplate` directly, since most applications don't bother with the extra abstraction layer given RabbitMQ is effectively fixed as the broker choice).
4. **Concrete implementation does the real work**: at runtime, the injected object is actually a `RabbitTemplate` instance, which internally uses the RabbitMQ Java client to open connections and channels and publish messages using the real AMQP wire protocol.
5. **Where the module boundary would matter**: if a team ever needed to swap to a different AMQP-compliant broker with its own Spring AMQP-compatible implementation, code written against `AmqpTemplate` rather than `RabbitTemplate` directly would need less rework — though in practice, this scenario is rare enough that many teams reasonably choose to depend on `RabbitTemplate` directly for its RabbitMQ-specific extensions.

```
build.gradle/pom.xml: spring-boot-starter-amqp
  -> transitively pulls in: spring-amqp + spring-rabbit + amqp-client
    -> Boot auto-configuration registers CachingConnectionFactory, RabbitTemplate, etc.
      -> application code: @Autowired AmqpTemplate (or RabbitTemplate directly)
        -> at runtime: concrete RabbitTemplate does the actual AMQP protocol work
```

## 7. Gotchas & takeaways

> **Gotcha:** depending only on `spring-amqp` without `spring-rabbit` (a rare but possible misconfiguration if managing dependencies manually rather than through the Boot starter) leaves the application with only interfaces and domain classes and no concrete broker implementation to inject — Spring Boot's auto-configuration has nothing to wire up, and bean creation fails with a cryptic "no qualifying bean" error rather than an obvious "missing dependency" message.

- In everyday Spring Boot development, reach for `spring-boot-starter-amqp` and don't think about the two-module split at all — it's bundled correctly by default.
- Typing application code against `AmqpTemplate` versus `RabbitTemplate` directly is a real but often academic choice — `RabbitTemplate` exposes RabbitMQ-specific features (publisher confirms, returns, specific exchange/queue declaration helpers) that the broker-agnostic interface doesn't expose, so most non-trivial applications end up depending on the concrete class anyway.
- `spring-rabbit`'s own transitive dependency on the RabbitMQ Java client (`amqp-client`) is what actually implements the wire protocol — Spring AMQP's classes are a layer of ergonomic Spring-style configuration and templates on top of that lower-level client library, not a reimplementation of the protocol itself.
- When debugging classpath or dependency-related startup failures in an AMQP-based application, checking that both `spring-amqp` and `spring-rabbit` (or the single starter that bundles them) are actually present is a reasonable first troubleshooting step.
