---
card: spring-framework
gi: 397
slug: jca-message-endpoints
title: "JCA message endpoints"
---

## 1. What it is

The Java EE Connector Architecture (JCA) is a standard for building **resource adapters** — plugins that let a Java EE/Jakarta EE server talk to an external system (a mainframe, an ERP system, a proprietary messaging system) through a uniform contract, the same way a JDBC driver is a standard plugin for talking to a database. Spring's JCA support, centered on `JmsMessageEndpointManager` and the broader `spring-jca` message-endpoint infrastructure, lets a resource adapter deliver inbound messages into a Spring-managed listener bean, without the resource adapter needing to know anything about Spring.

```java
// A JCA-managed endpoint factory, wired to deliver into a Spring MessageListener
JmsMessageEndpointManager endpointManager = new JmsMessageEndpointManager();
endpointManager.setResourceAdapter(resourceAdapter);
endpointManager.setActivationSpec(activationSpec);
endpointManager.setMessageListener(springManagedListenerBean);
```

## 2. Why & when

JCA predates Spring's own JMS listener-container abstraction and was designed for full Java EE application servers (WebLogic, WebSphere, JBoss) that manage resource adapters as deployed modules with container-managed transactions and thread pools. Spring's JCA message-endpoint support exists to bridge that container-managed inbound delivery mechanism into ordinary Spring beans, so a listener written as a plain Spring-managed `MessageListener` can receive messages delivered by a JCA resource adapter running inside the application server, benefiting from the server's own transaction and thread management instead of Spring's own `DefaultMessageListenerContainer`.

This is a narrow, legacy-adjacent corner of the framework. You'd reach for it when:

- You're deploying into a full Java EE/Jakarta EE application server (not a standalone Spring Boot JAR) that already manages resource adapters and their thread pools, and you want the server — not Spring — driving message delivery and transaction demarcation.
- You're integrating with a system whose only available Java integration point is a JCA resource adapter (common with older enterprise messaging or ERP connectors) rather than a plain JMS `ConnectionFactory`.
- You're maintaining an existing application that already uses this pattern and need to understand or extend it, rather than choosing it fresh.

For any new project — including most JMS integrations — prefer Spring's own `DefaultMessageListenerContainer` and `@JmsListener` (covered in the JMS card), which manage their own threads and transactions without depending on a Java EE application server's JCA container at all. JCA message endpoints matter mainly for understanding legacy Java EE deployments.

## 3. Core concept

```
 Java EE Application Server
        |
        | manages
        v
 JCA Resource Adapter  (deployed module, e.g. a proprietary MQ connector)
        |
        | ActivationSpec describes: which destination, which listener interface
        v
 Spring's JmsMessageEndpointManager
        |
        | wraps and delegates to
        v
 Ordinary Spring-managed MessageListener bean  <-- your code lives here
```

The application server's resource adapter drives *when* messages arrive and *how* transactions/threads are managed; Spring's endpoint manager is only the adapter layer that lets a plain Spring bean be the thing that actually receives them.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JCA resource adapter inside an app server delivers messages through Spring endpoint manager into a Spring bean">
  <rect x="10" y="60" width="170" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Java EE server</text>
  <text x="95" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">JCA resource adapter</text>

  <rect x="235" y="60" width="190" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring</text>
  <text x="330" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">JmsMessageEndpointManager</text>

  <rect x="480" y="60" width="150" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageListener</text>
  <text x="555" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(your bean)</text>

  <line x1="180" y1="95" x2="230" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="425" y1="95" x2="475" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The application server owns delivery and transactions; Spring's endpoint manager is a thin bridge into a plain Java listener bean.

## 5. Runnable example

A real JCA resource adapter requires deployment into a Java EE application server, which is outside the scope of a single runnable file. This example instead uses Spring's own JMS-based `ActivationSpec` implementation (`JmsActivationSpecFactory`) against an embedded broker to demonstrate the same `JmsMessageEndpointManager` API you'd configure for a genuine third-party JCA adapter, so the wiring and lifecycle are real and runnable even though the "resource adapter" here is Spring's own JMS-backed one rather than a proprietary enterprise connector.

### Level 1 — Basic

Configure a `JmsMessageEndpointManager` directly against an embedded broker's JMS resource adapter and deliver one message into a plain `MessageListener`.

```java
import jakarta.jms.Message;
import jakarta.jms.TextMessage;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.listener.endpoint.JmsActivationSpecConfig;
import org.springframework.jms.listener.endpoint.JmsMessageEndpointManager;
import org.springframework.jms.listener.endpoint.JmsMessageEndpointFactory;
import org.springframework.jca.support.SimpleBootstrapContext;
import org.springframework.jca.work.SimpleTaskWorkManager;

public class JcaBasic {

    public static void main(String[] args) throws Exception {
        var connectionFactory = new ActiveMQJMSConnectionFactory("vm://0");

        var endpointFactory = new JmsMessageEndpointFactory();
        endpointFactory.setMessageListener((Message message) -> {
            try {
                System.out.println("Endpoint received: " + ((TextMessage) message).getText());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });

        var activationSpecConfig = new JmsActivationSpecConfig();
        activationSpecConfig.setDestinationName("orders.queue");
        activationSpecConfig.setConnectionFactory(connectionFactory);
        endpointFactory.setActivationSpecConfig(activationSpecConfig);

        var endpointManager = new JmsMessageEndpointManager();
        endpointManager.setMessageEndpointFactory(endpointFactory);
        endpointManager.setActivationSpecConfig(activationSpecConfig);
        endpointManager.setBootstrapContext(new SimpleBootstrapContext(new SimpleTaskWorkManager(), null));

        endpointManager.start();

        new JmsTemplate(connectionFactory).convertAndSend("orders.queue", "order-jca-1");

        Thread.sleep(500); // demo-only: allow async delivery before shutdown
        endpointManager.stop();
    }
}
```

How to run: add `spring-jms`, `spring-tx`, and an embedded broker dependency, then `java JcaBasic.java`.

`JmsActivationSpecConfig` plays the role a JCA `ActivationSpec` would play for a real resource adapter — it describes *what* to listen to. `SimpleBootstrapContext`/`SimpleTaskWorkManager` stand in for the thread and work management a real Java EE server would otherwise provide. Starting the `JmsMessageEndpointManager` activates delivery, and the plain lambda `MessageListener` receives the message exactly as a genuine JCA-delivered endpoint would.

### Level 2 — Intermediate

Add transactional delivery so a failing endpoint doesn't lose the message, mirroring how a Java EE server would demarcate a container-managed transaction around each delivery.

```java
import jakarta.jms.Message;
import jakarta.jms.TextMessage;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.listener.endpoint.JmsActivationSpecConfig;
import org.springframework.jms.listener.endpoint.JmsMessageEndpointManager;
import org.springframework.jms.listener.endpoint.JmsMessageEndpointFactory;
import org.springframework.jca.support.SimpleBootstrapContext;
import org.springframework.jca.work.SimpleTaskWorkManager;

import java.util.concurrent.atomic.AtomicInteger;

public class JcaIntermediate {

    public static void main(String[] args) throws Exception {
        var connectionFactory = new ActiveMQJMSConnectionFactory("vm://0");
        var attempts = new AtomicInteger();

        var endpointFactory = new JmsMessageEndpointFactory();
        endpointFactory.setMessageListener((Message message) -> {
            try {
                String text = ((TextMessage) message).getText();
                if (attempts.incrementAndGet() < 2) {
                    throw new RuntimeException("Simulated failure delivering " + text);
                }
                System.out.println("Delivered on attempt " + attempts.get() + ": " + text);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });

        var activationSpecConfig = new JmsActivationSpecConfig();
        activationSpecConfig.setDestinationName("orders.queue");
        activationSpecConfig.setConnectionFactory(connectionFactory);
        activationSpecConfig.setAcknowledgeMode(jakarta.jms.Session.SESSION_TRANSACTED);
        endpointFactory.setActivationSpecConfig(activationSpecConfig);

        var endpointManager = new JmsMessageEndpointManager();
        endpointManager.setMessageEndpointFactory(endpointFactory);
        endpointManager.setActivationSpecConfig(activationSpecConfig);
        endpointManager.setBootstrapContext(new SimpleBootstrapContext(new SimpleTaskWorkManager(), null));

        endpointManager.start();
        new JmsTemplate(connectionFactory).convertAndSend("orders.queue", "order-jca-2");
        Thread.sleep(1000);
        endpointManager.stop();
    }
}
```

How to run: same dependencies as Level 1, then `java JcaIntermediate.java`.

`setAcknowledgeMode(Session.SESSION_TRANSACTED)` on the `ActivationSpecConfig` mirrors the container-managed transaction a Java EE server applies around a JCA endpoint: a runtime exception rolls back the delivery instead of losing the message, so the broker redelivers it, and the demo listener succeeds on its second attempt.

### Level 3 — Advanced

Real JCA deployments run several concurrent endpoint instances and need graceful shutdown that waits for in-flight deliveries to finish rather than dropping them — configured via `JmsActivationSpecConfig`'s concurrency setting and the endpoint manager's lifecycle.

```java
import jakarta.jms.Message;
import jakarta.jms.TextMessage;
import org.apache.activemq.artemis.jms.client.ActiveMQJMSConnectionFactory;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.jms.listener.endpoint.JmsActivationSpecConfig;
import org.springframework.jms.listener.endpoint.JmsMessageEndpointManager;
import org.springframework.jms.listener.endpoint.JmsMessageEndpointFactory;
import org.springframework.jca.support.SimpleBootstrapContext;
import org.springframework.jca.work.SimpleTaskWorkManager;

import java.util.concurrent.CountDownLatch;

public class JcaAdvanced {

    public static void main(String[] args) throws Exception {
        var connectionFactory = new ActiveMQJMSConnectionFactory("vm://0");
        var received = new CountDownLatch(5);

        var endpointFactory = new JmsMessageEndpointFactory();
        endpointFactory.setMessageListener((Message message) -> {
            try {
                System.out.println(Thread.currentThread().getName()
                        + " handled " + ((TextMessage) message).getText());
                received.countDown();
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });

        var activationSpecConfig = new JmsActivationSpecConfig();
        activationSpecConfig.setDestinationName("orders.queue");
        activationSpecConfig.setConnectionFactory(connectionFactory);
        activationSpecConfig.setMaxConcurrency(5); // up to 5 concurrent endpoint invocations
        endpointFactory.setActivationSpecConfig(activationSpecConfig);

        var endpointManager = new JmsMessageEndpointManager();
        endpointManager.setMessageEndpointFactory(endpointFactory);
        endpointManager.setActivationSpecConfig(activationSpecConfig);
        endpointManager.setBootstrapContext(new SimpleBootstrapContext(new SimpleTaskWorkManager(), null));

        endpointManager.start();

        JmsTemplate jmsTemplate = new JmsTemplate(connectionFactory);
        for (int i = 1; i <= 5; i++) {
            jmsTemplate.convertAndSend("orders.queue", "order-jca-" + i);
        }

        received.await(); // wait for all 5 concurrent deliveries to complete
        endpointManager.stop(); // graceful: lets in-flight deliveries finish first
        System.out.println("All deliveries complete, endpoint manager stopped cleanly");
    }
}
```

How to run: same dependencies as Level 1, then `java JcaAdvanced.java`.

`setMaxConcurrency(5)` allows up to five concurrent endpoint invocations, visible in the output as different thread names handling different messages, roughly mirroring how a Java EE server's work manager would dispatch concurrent deliveries across its own thread pool. `endpointManager.stop()` performs a graceful shutdown, matching the deactivation contract a real JCA resource adapter expects.

## 6. Walkthrough

Trace `JcaAdvanced.main` end to end:

1. **Endpoint factory and activation spec built.** `JmsMessageEndpointFactory` wraps the plain `MessageListener` lambda; `JmsActivationSpecConfig` describes the destination and concurrency, standing in for what a real JCA `ActivationSpec` would carry (destination JNDI name, subscription details, acknowledgment mode) in a genuine deployment.
2. **Endpoint manager starts.** `endpointManager.start()` activates the endpoint against the "resource adapter" (here, the embedded broker's connection factory) — conceptually the same activation call a Java EE server's deployer would trigger when the application starts.
3. **Five sends.** The loop sends five `TextMessage`s to `orders.queue` via a plain `JmsTemplate`, simulating five independent producers or a producer sending a batch.
4. **Concurrent delivery.** Because `maxConcurrency` is 5, up to five of the endpoint manager's internal listener threads pick up messages in parallel rather than one at a time — the printed thread names differ across invocations, showing genuine concurrency, not just five sequential calls on one thread.
5. **Each delivery invokes the endpoint.** For each message, the underlying JMS session hands the raw `Message` to the endpoint factory's listener, which casts it to `TextMessage`, reads the text, and prints it — mirroring exactly what a real JCA resource adapter would do when it invokes the deployed endpoint instance.
6. **Latch releases.** Each successful delivery calls `received.countDown()`; once all five have completed, `received.await()` in `main` unblocks.
7. **Graceful stop.** `endpointManager.stop()` deactivates the endpoint, waiting for any still-in-flight deliveries to finish rather than aborting them mid-processing — this graceful-shutdown contract is exactly what a Java EE server relies on when undeploying or restarting an application that uses JCA-delivered endpoints.

```
5x JmsTemplate.send --> broker queue (5 messages queued)
     endpoint manager (maxConcurrency=5)
        thread A: message 1 -> listener -> countDown
        thread B: message 2 -> listener -> countDown
        ... (up to 5 concurrent)
     received.await() unblocks once all 5 done
     endpointManager.stop() -- graceful
```

## 7. Gotchas & takeaways

> Gotcha: this JCA message-endpoint machinery is almost never the right choice for a standalone Spring Boot application — it exists specifically to integrate with a full Java EE/Jakarta EE application server's resource-adapter deployment model. Reaching for `JmsMessageEndpointManager` in a Spring Boot app that could instead use `@JmsListener`/`DefaultMessageListenerContainer` adds real complexity (bootstrap contexts, work managers, activation specs) for no corresponding benefit, since Spring Boot apps don't run inside a JCA-managed container in the first place.

- JCA message endpoints exist to bridge a Java EE application server's resource-adapter-driven message delivery into ordinary Spring-managed listener beans — they matter mainly in legacy full-profile Java EE deployments.
- For new JMS integrations, prefer `@JmsListener`/`DefaultMessageListenerContainer`, which manage their own threads and transactions without needing a Java EE container's JCA support at all.
- `JmsActivationSpecConfig` plays the same conceptual role as a real JCA `ActivationSpec`: it describes what to listen to and how (destination, concurrency, acknowledgment mode).
- Graceful shutdown (`stop()` waiting for in-flight deliveries) is a defining trait of the JCA endpoint lifecycle contract — replicate that expectation even when using Spring's own listener containers instead.
