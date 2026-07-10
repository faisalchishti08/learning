---
card: spring-framework
gi: 456
slug: the-jms-schema
title: "The jms schema"
---

## 1. What it is

The `jms` namespace (`xmlns:jms="http://www.springframework.org/schema/jms"`) is the XML equivalent of `@JmsListener`: `<jms:listener-container>` declares one or more message listener containers, and nested `<jms:listener>` elements bind a specific destination (queue or topic) to a plain Java method on a POJO, without that method needing any JMS-specific interface or annotation.

```xml
<jms:listener-container connection-factory="connectionFactory">
    <jms:listener destination="orders.queue" ref="orderProcessor" method="onOrder"/>
</jms:listener-container>
```

## 2. Why & when

Consuming JMS messages by hand means implementing `MessageListener`, registering it on a `DefaultMessageListenerContainer`, handling connection recovery, and converting the raw `Message` into a usable Java object — all boilerplate that has nothing to do with the actual business logic of "when an order message arrives, process it." The `jms` schema (like `@JmsListener` after it) exists to let a plain method with a plain parameter type be the entire integration point, with the container, connection handling, and message conversion configured declaratively around it.

Reach for the `jms` schema specifically when:

- You're maintaining a legacy XML-configured Spring application that already declares its listener containers this way, and need to add, modify, or trace a queue/topic binding.
- You want message-listener wiring to live in the same XML file as the rest of a component's configuration, consistent with a codebase's existing XML-first convention.
- You need fine control over listener container settings — concurrency, session transaction mode, acknowledge mode — expressed as XML attributes alongside other infrastructure configuration.

In new code, `@JmsListener` plus `@EnableJms` on a `@Configuration` class is almost always simpler — the `jms` schema mainly exists to support and explain configuration that predates that annotation.

## 3. Core concept

```
 <jms:listener-container connection-factory="connectionFactory">
        |
        +-- <jms:listener destination="orders.queue" ref="orderProcessor" method="onOrder"/>
        |
        +-- <jms:listener destination="alerts.topic" ref="alertHandler" method="onAlert"/>

 At context-refresh time, for EACH <jms:listener>:
        |
        v
 Spring creates a MessageListenerContainer bound to that destination
        |
        v
 wraps ref.method(...) in a MessageListenerAdapter
        |
        v
 container starts consuming: on each message ->
     adapter converts the raw Message -> calls ref.method(convertedPayload)
```

Each `<jms:listener>` gets its own underlying container instance (sharing the referenced `connection-factory`), independently consuming from its own destination.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jms:listener-container consumes from a destination and dispatches converted messages to a plain method">
  <rect x="10" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">orders.queue</text>
  <text x="85" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JMS broker</text>

  <rect x="220" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MessageListenerContainer</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ MessageListenerAdapter</text>

  <rect x="480" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">orderProcessor</text>
  <text x="555" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.onOrder(payload)</text>

  <line x1="160" y1="45" x2="215" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="475" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The container consumes raw messages, converts them, and calls a plain method — `orderProcessor` never touches the JMS API directly.

## 5. Runnable example

Since a real JMS broker isn't available in a single-file example, the scenario uses ActiveMQ Artemis's embedded in-VM broker (a genuine JMS provider that runs entirely inside the JVM, commonly used for exactly this kind of self-contained demo/test) — evolving from a single listener consuming plain text, to a `MessageConverter` handling a typed payload, to a full setup with concurrency and manual acknowledgment.

### Level 1 — Basic

Wire one `<jms:listener>` against an in-VM Artemis queue and confirm a plain method receives the message text.

```java
import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.jms.core.JmsTemplate;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class JmsSchemaLevel1 {

    public static class OrderProcessor {
        final CountDownLatch received = new CountDownLatch(1);
        volatile String lastMessage;
        public void onOrder(String text) {
            lastMessage = text;
            System.out.println("[listener] received: " + text);
            received.countDown();
        }
    }

    public static void main(String[] args) throws Exception {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:jms="http://www.springframework.org/schema/jms"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/jms
                       https://www.springframework.org/schema/jms/spring-jms.xsd">

                <bean id="connectionFactory" class="org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory">
                    <constructor-arg value="vm://0"/>
                </bean>

                <bean id="orderProcessor" class="JmsSchemaLevel1$OrderProcessor"/>

                <jms:listener-container connection-factory="connectionFactory">
                    <jms:listener destination="orders.queue" ref="orderProcessor" method="onOrder"/>
                </jms:listener-container>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ActiveMQConnectionFactory cf = ctx.getBean(ActiveMQConnectionFactory.class);
        JmsTemplate template = new JmsTemplate(cf);
        template.convertAndSend("orders.queue", "order-42");

        OrderProcessor processor = ctx.getBean(OrderProcessor.class);
        boolean gotIt = processor.received.await(5, TimeUnit.SECONDS);
        System.out.println("gotIt = " + gotIt + ", lastMessage = " + processor.lastMessage);

        if (!gotIt || !"order-42".equals(processor.lastMessage))
            throw new AssertionError("Expected the listener to receive 'order-42'");
        System.out.println("jms:listener dispatched the message to a plain method -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context`, `spring-jms`, and `artemis-jms-client` on the classpath, then `java JmsSchemaLevel1.java` on JDK 17+.

`vm://0` is Artemis's in-VM transport — a real broker running inside the same JVM process, no network or external server needed. `<jms:listener destination="orders.queue" ref="orderProcessor" method="onOrder"/>` wires a `SimpleMessageListenerContainer` that consumes from `orders.queue` and, on each message, calls `orderProcessor.onOrder(...)` with the converted payload — here a plain `String`, since `JmsTemplate.convertAndSend` sent a text message and the default `MessageListenerAdapter` converts a `TextMessage` to `String` automatically.

### Level 2 — Intermediate

Send a structured payload (not just a string) using a `MessageConverter`, showing how `jms:listener` methods can receive typed objects instead of raw JMS types.

```java
import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.support.converter.MappingJackson2MessageConverter;
import org.springframework.jms.support.converter.MessageType;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class JmsSchemaLevel2 {

    public record Order(String item, int quantity) {}

    public static class OrderProcessor {
        final CountDownLatch received = new CountDownLatch(1);
        volatile Order lastOrder;
        public void onOrder(Order order) {
            lastOrder = order;
            System.out.println("[listener] received order: " + order);
            received.countDown();
        }
    }

    public static void main(String[] args) throws Exception {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:jms="http://www.springframework.org/schema/jms"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/jms
                       https://www.springframework.org/schema/jms/spring-jms.xsd">

                <bean id="connectionFactory" class="org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory">
                    <constructor-arg value="vm://0"/>
                </bean>

                <bean id="jacksonConverter" class="org.springframework.jms.support.converter.MappingJackson2MessageConverter">
                    <property name="targetType" value="TEXT"/>
                    <property name="typeIdPropertyName" value="_type"/>
                </bean>

                <bean id="orderProcessor" class="JmsSchemaLevel2$OrderProcessor"/>

                <jms:listener-container connection-factory="connectionFactory" message-converter="jacksonConverter">
                    <jms:listener destination="orders.queue" ref="orderProcessor" method="onOrder"/>
                </jms:listener-container>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ActiveMQConnectionFactory cf = ctx.getBean(ActiveMQConnectionFactory.class);
        JmsTemplate template = new JmsTemplate(cf);
        MappingJackson2MessageConverter converter = ctx.getBean(MappingJackson2MessageConverter.class);
        template.setMessageConverter(converter);
        template.convertAndSend("orders.queue", new Order("widget", 3));

        OrderProcessor processor = ctx.getBean(OrderProcessor.class);
        boolean gotIt = processor.received.await(5, TimeUnit.SECONDS);
        System.out.println("gotIt = " + gotIt + ", lastOrder = " + processor.lastOrder);

        if (!gotIt || processor.lastOrder == null || !processor.lastOrder.item().equals("widget"))
            throw new AssertionError("Expected a fully-deserialized Order");
        System.out.println("message-converter deserialized JSON into a typed record -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, plus `spring-oxm`/`jackson-databind` on the classpath. Run `java JmsSchemaLevel2.java`.

`message-converter="jacksonConverter"` tells the listener container's `MessageListenerAdapter` to run every incoming message through `MappingJackson2MessageConverter` before invoking `onOrder`, converting a JSON text payload straight into an `Order` record — the listener method never touches raw JSON or `TextMessage` itself.

### Level 3 — Advanced

Add `concurrency` (multiple consumer threads) and `acknowledge="client"` (manual acknowledgment), the production-flavored combination used when message processing needs controlled parallelism and explicit control over when a message is considered consumed.

```java
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.Session;
import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.listener.SessionAwareMessageListener;

import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class JmsSchemaLevel3 {

    public static class OrderProcessor implements SessionAwareMessageListener<Message> {
        final CountDownLatch allReceived;
        final Set<String> processedIds = ConcurrentHashMap.newKeySet();

        public OrderProcessor(int expectedCount) {
            this.allReceived = new CountDownLatch(expectedCount);
        }

        @Override
        public void onMessage(Message message, Session session) throws JMSException {
            String text = message.getBody(String.class);
            System.out.println("[" + Thread.currentThread().getName() + "] processing: " + text);
            processedIds.add(text);
            message.acknowledge(); // manual ack, required because acknowledge="client"
            allReceived.countDown();
        }
    }

    public static void main(String[] args) throws Exception {
        OrderProcessor processor = new OrderProcessor(5);

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:jms="http://www.springframework.org/schema/jms"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/jms
                       https://www.springframework.org/schema/jms/spring-jms.xsd">

                <bean id="connectionFactory" class="org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory">
                    <constructor-arg value="vm://0"/>
                </bean>

                <bean id="orderProcessor" class="JmsSchemaLevel3$OrderProcessor">
                    <constructor-arg value="5"/>
                </bean>

                <jms:listener-container connection-factory="connectionFactory"
                    concurrency="3-5" acknowledge="client">
                    <jms:listener destination="orders.queue" ref="orderProcessor"/>
                </jms:listener-container>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.getBeanFactory().registerSingleton("orderProcessor", processor);
        ctx.refresh();

        ActiveMQConnectionFactory cf = ctx.getBean(ActiveMQConnectionFactory.class);
        JmsTemplate template = new JmsTemplate(cf);
        for (int i = 1; i <= 5; i++) {
            template.convertAndSend("orders.queue", "order-" + i);
        }

        boolean allDone = processor.allReceived.await(10, TimeUnit.SECONDS);
        System.out.println("allDone = " + allDone + ", processedIds = " + processor.processedIds);

        if (!allDone || processor.processedIds.size() != 5)
            throw new AssertionError("Expected all 5 orders processed exactly once");
        System.out.println("concurrency=3-5 + acknowledge=client processed all messages -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java JmsSchemaLevel3.java`.

`concurrency="3-5"` tells the listener container to maintain between 3 and 5 concurrent consumer threads, scaling up under load — the `[Thread.currentThread().getName()]` prefix in the log output shows different threads handling different messages. `acknowledge="client"` switches off automatic acknowledgment, requiring the listener to call `message.acknowledge()` itself once processing genuinely completes — critical when you want a message redelivered if the consumer crashes mid-processing, rather than silently lost.

## 6. Walkthrough

Trace Level 1's flow, since it's the clearest illustration of the container mechanics.

1. **Context refresh**: Spring parses `<jms:listener-container>`, which internally builds a `DefaultMessageListenerContainer` (or `SimpleMessageListenerContainer`, depending on configuration) bound to `connectionFactory` and configured to consume from `orders.queue`.
2. **Container start**: as part of context refresh, the listener container starts a background consumer thread (or threads, per `concurrency`) that opens a JMS `Session` and begins listening on `orders.queue`.
3. **`main` sends a message**: `template.convertAndSend("orders.queue", "order-42")` — `JmsTemplate` opens its own (separate, short-lived) session, converts the `String` `"order-42"` into a `TextMessage`, and sends it to the queue. This is the "request" — a message published onto a queue rather than an HTTP call.
4. **Broker delivers**: Artemis's in-VM broker routes the message to the container's active consumer.
5. **Adapter conversion**: the container's `MessageListenerAdapter` receives the raw `TextMessage`, extracts its text body (`"order-42"`), and determines the target method (`onOrder`) and its parameter type (`String`) via reflection.
6. **Method invocation**: the adapter calls `orderProcessor.onOrder("order-42")` — the listener code itself never sees a `Message` or `Session` object, only the plain string payload.
7. **Application logic**: `onOrder` stores the message and counts down a `CountDownLatch`, which `main` is waiting on.
8. **`main` observes completion**: `processor.received.await(5, TimeUnit.SECONDS)` returns `true` once the listener thread has run, confirming end-to-end delivery; the program then asserts the received text matches what was sent.

```
 JmsTemplate.convertAndSend("orders.queue", "order-42")
        |
        v
 Artemis broker (vm://0) -- routes message to queue
        |
        v
 listener container's consumer thread receives raw TextMessage
        |
        v
 MessageListenerAdapter converts TextMessage -> "order-42" (String)
        |
        v
 orderProcessor.onOrder("order-42")  -- plain method, no JMS types involved
```

## 7. Gotchas & takeaways

> **Gotcha:** with the default acknowledge mode (`auto`), a message is acknowledged automatically once the listener method returns *without throwing* — if `onOrder` throws an exception, the message is typically redelivered (subject to the broker's redelivery policy), which can cause infinite redelivery loops for a message that will always fail the same way ("poison messages"). Production listener containers usually pair error handling with a dead-letter queue or an `ErrorHandler` bean to break that loop.

- `jms:listener-container` maps directly onto `@EnableJms` + `@JmsListener` — the same underlying `MessageListenerContainer` machinery powers both; only the configuration surface differs.
- `ref`/`method` on `<jms:listener>` mean the listener method can be an ordinary, framework-agnostic method — the same technique `aop:aspect` uses for advice methods, applied here to message handling.
- `message-converter` decouples wire format (JSON, XML, plain text) from the Java type the listener method actually receives — change the converter without touching listener code.
- `concurrency` and `acknowledge` are the two attributes to reach for when scaling throughput or tightening delivery guarantees; both have direct analogues in `@JmsListener`'s `concurrency` attribute and the container factory's acknowledge-mode setting.
