---
card: spring-integration
gi: 41
slug: enableintegration
title: "@EnableIntegration"
---

## 1. What it is

`@EnableIntegration` is a configuration-class annotation that activates Spring Integration's infrastructure within a Spring application context — it registers the default beans every Spring Integration application needs (the default `errorChannel`, a `taskScheduler` for pollers and delayers, the `IntegrationManagementConfigurer` used by monitoring features, and support for the annotations covered elsewhere in this section, like `@ServiceActivator`, card 0020, and `@MessagingGateway`, card 0032). Without it, none of Spring Integration's annotation-driven configuration or default infrastructure beans are set up at all.

## 2. Why & when

You reach for `@EnableIntegration` specifically because it's the one-time setup step every Spring Integration application needs before any of the other constructs in this section can function:

- **You're using any `@ServiceActivator`, `@Transformer`, `@Filter`, `@Router`, or `@Splitter` annotation** (cards 0019–0024) anywhere in the application — these annotations are processed by infrastructure that `@EnableIntegration` registers; without it, they're inert annotations with nothing scanning for or acting on them.
- **You're using the Java DSL** (`IntegrationFlow`, card 0037) — the DSL's builder mechanics depend on the same underlying infrastructure `@EnableIntegration` sets up (default channels, task scheduling for pollers).
- **You want Spring Integration's default error handling, message history, or management features available at all** — several of the cross-cutting capabilities covered later in this section (error handling, card 0044; global wiretap, card 0045) rely on infrastructure `@EnableIntegration` provides by default, even before any custom configuration is added on top.

## 3. Core concept

Think of `@EnableIntegration` like flipping the main breaker in a building's electrical panel before plugging in any individual appliance. None of the outlets (the `@ServiceActivator`s, `@Transformer`s, DSL flows) will do anything at all until the breaker itself is switched on — it's the one foundational step that makes every other piece of wiring in the building actually live.

```java
@Configuration
@EnableIntegration
public class IntegrationConfig {
    // once @EnableIntegration is present, everything else in this section becomes functional:
    // @ServiceActivator, @Transformer, IntegrationFlow beans, the default errorChannel, etc.
}
```

A single annotation on one `@Configuration` class is typically all that's needed — everything downstream (annotation scanning, default beans, DSL support) activates as a consequence of this one declaration.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnableIntegration activates the shared infrastructure that every other Spring Integration construct in the application depends on">
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@EnableIntegration</text>
  <text x="320" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">activates core infrastructure</text>

  <line x1="270" y1="70" x2="150" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ei1)"/>
  <line x1="320" y1="70" x2="320" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ei1)"/>
  <line x1="370" y1="70" x2="490" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ei1)"/>

  <rect x="60" y="115" width="180" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@ServiceActivator etc.</text>

  <rect x="240" y="115" width="160" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">IntegrationFlow (DSL)</text>

  <rect x="410" y="115" width="170" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="495" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">errorChannel, taskScheduler</text>

  <defs>
    <marker id="ei1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Every other construct covered across this whole card section depends on the infrastructure this one annotation activates.

## 5. Runnable example

The scenario: illustrating what `@EnableIntegration` conceptually turns on, since its actual effect is entirely about Spring context bootstrapping (annotation processors, default bean registration) rather than something directly observable via a standalone `java` program — the examples instead show the *shape* of what becomes available once it's present, contrasted with what's missing without it.

### Level 1 — Basic

```java
// WithoutInfrastructureDemo.java
// Simulates the state of the world WITHOUT @EnableIntegration: annotations exist as plain
// metadata, but nothing is actually scanning for them or wiring anything up.
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class WithoutInfrastructureDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @interface ServiceActivator { String inputChannel(); }

    static class OrderService {
        @ServiceActivator(inputChannel = "orders")
        public void process(String order) {
            System.out.println("Processing: " + order);
        }
    }

    public static void main(String[] args) throws Exception {
        // the annotation is PRESENT on the method, but nothing is registered to act on it
        Method m = OrderService.class.getMethod("process", String.class);
        ServiceActivator annotation = m.getAnnotation(ServiceActivator.class);
        System.out.println("Annotation found: inputChannel=" + annotation.inputChannel());
        System.out.println("But NOTHING is actually listening on that channel — no infrastructure was ever activated.");
    }
}
```

How to run: `java WithoutInfrastructureDemo.java`. Expected output: confirmation that the annotation exists and can be reflectively read, followed by the explicit statement that nothing is actually wired up — exactly the state of any Spring Integration annotation before `@EnableIntegration` activates the infrastructure that scans for and acts on them.

### Level 2 — Intermediate

Simulating what activation conceptually does: a registry that scans for annotated methods and wires them to actual channels, standing in for what `@EnableIntegration`'s underlying `BeanPostProcessor`s do automatically once present.

```java
// SimulatedActivationDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

public class SimulatedActivationDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @interface ServiceActivator { String inputChannel(); }

    static class OrderService {
        @ServiceActivator(inputChannel = "orders")
        public void process(String order) {
            System.out.println("Processing: " + order);
        }
    }

    // stands in for what @EnableIntegration's infrastructure does: scan, register, wire
    static void activateIntegrationInfrastructure(Object bean, Map<String, DirectChannel> channelRegistry) throws Exception {
        for (Method m : bean.getClass().getMethods()) {
            ServiceActivator annotation = m.getAnnotation(ServiceActivator.class);
            if (annotation != null) {
                DirectChannel channel = channelRegistry.computeIfAbsent(annotation.inputChannel(), k -> new DirectChannel());
                channel.subscribe(msg -> {
                    try { m.invoke(bean, msg.getPayload()); } catch (Exception e) { throw new RuntimeException(e); }
                });
                System.out.println("Activated: " + m.getName() + " now listening on channel '" + annotation.inputChannel() + "'");
            }
        }
    }

    public static void main(String[] args) throws Exception {
        Map<String, DirectChannel> channels = new HashMap<>();
        activateIntegrationInfrastructure(new OrderService(), channels);

        // NOW something is actually listening, because "activation" ran
        channels.get("orders").send(MessageBuilder.withPayload("order-1").build());
    }
}
```

How to run: `java SimulatedActivationDemo.java`. Expected output: `Activated: process now listening on channel 'orders'` then `Processing: order-1` — once the simulated activation step ran (standing in for `@EnableIntegration`'s real infrastructure), the previously-inert annotation became functional, and a message sent to the channel actually reached the annotated method.

### Level 3 — Advanced

A more complete simulation showing multiple annotated components across different classes all being activated by one central "enable" step — mirroring how, in a real application, `@EnableIntegration` on a single configuration class activates annotation processing across the *entire* application context, not just one bean.

```java
// MultiComponentActivationDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.*;

public class MultiComponentActivationDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @interface ServiceActivator { String inputChannel(); }

    static class ValidationService {
        @ServiceActivator(inputChannel = "rawOrders")
        public void validate(String order) { System.out.println("[ValidationService] validated: " + order); }
    }
    static class ShippingService {
        @ServiceActivator(inputChannel = "validatedOrders")
        public void ship(String order) { System.out.println("[ShippingService] shipped: " + order); }
    }

    static Map<String, DirectChannel> channels = new HashMap<>();

    static void enableIntegration(Object... beans) throws Exception {
        System.out.println("=== @EnableIntegration: scanning ALL beans in the application context ===");
        for (Object bean : beans) {
            for (Method m : bean.getClass().getMethods()) {
                ServiceActivator annotation = m.getAnnotation(ServiceActivator.class);
                if (annotation != null) {
                    DirectChannel channel = channels.computeIfAbsent(annotation.inputChannel(), k -> new DirectChannel());
                    channel.subscribe(msg -> {
                        try { m.invoke(bean, msg.getPayload()); } catch (Exception e) { throw new RuntimeException(e); }
                    });
                }
            }
        }
        System.out.println("=== activation complete, " + channels.size() + " channels wired ===");
    }

    public static void main(String[] args) throws Exception {
        enableIntegration(new ValidationService(), new ShippingService());

        channels.get("rawOrders").send(MessageBuilder.withPayload("ORD-1").build());
        channels.get("validatedOrders").send(MessageBuilder.withPayload("ORD-1").build());
    }
}
```

How to run: `java MultiComponentActivationDemo.java`. Expected output: `=== @EnableIntegration: scanning ALL beans... ===`, `=== activation complete, 2 channels wired ===`, then `[ValidationService] validated: ORD-1` and `[ShippingService] shipped: ORD-1` — two completely separate beans, each with their own annotated method, were both activated by a single central enabling step, exactly mirroring how one `@EnableIntegration` annotation activates annotation processing across an entire Spring application context.

## 6. Walkthrough

Tracing `MultiComponentActivationDemo` in execution order:

1. `enableIntegration(new ValidationService(), new ShippingService())` is called with two separate bean instances — standing in for Spring's component scanning discovering every bean in the application context once `@EnableIntegration` has activated the relevant infrastructure.
2. For each bean, the method reflects over its class's methods, checking for the `@ServiceActivator` annotation — this mirrors what Spring Integration's real annotation `BeanPostProcessor`s do during application context startup.
3. For `ValidationService.validate`, the annotation's `inputChannel="rawOrders"` is found; a `DirectChannel` is created (or reused) for that name, and the method is subscribed to it via a wrapping lambda that reflectively invokes it.
4. The same happens for `ShippingService.ship`, wired to a *different* channel, `"validatedOrders"` — two independent activations, from two independent beans, both happening as part of the same overall enabling pass.
5. After both are activated, `channels.get("rawOrders").send(...)` triggers `ValidationService.validate` (via the subscribed lambda's reflective invocation), printing its confirmation.
6. `channels.get("validatedOrders").send(...)` triggers `ShippingService.ship` similarly — both previously-inert annotations are now genuinely functional endpoints, purely because the one-time "enable" step ran first and wired everything up.

```
enableIntegration(ValidationService, ShippingService)
  -> scan ValidationService -> found @ServiceActivator(inputChannel="rawOrders") -> wire
  -> scan ShippingService   -> found @ServiceActivator(inputChannel="validatedOrders") -> wire
  -> 2 channels now wired, 2 methods now genuinely listening
```

## 7. Gotchas & takeaways

> Forgetting `@EnableIntegration` on any `@Configuration` class in the application is a common source of confusing "why isn't my `@ServiceActivator` doing anything" bugs — the annotation itself is valid Java and won't cause a compile error or even necessarily a startup error; it simply sits there, inert, exactly like `WithoutInfrastructureDemo`'s reflective annotation with nothing listening. If Spring Integration annotations seem to have no effect at all, checking for `@EnableIntegration`'s presence should be one of the first things verified.

- `@EnableIntegration` activates Spring Integration's core infrastructure within a Spring application context — default channels, task scheduling, and the annotation processors that make `@ServiceActivator`, `@Transformer`, `@Filter`, `@Router`, `@Splitter`, and the Java DSL actually functional.
- It's typically declared once, on a single `@Configuration` class, and its effects apply across the entire application context, not just that one class.
- Every other construct covered across this card section (cards 0019–0048) depends, directly or indirectly, on infrastructure this annotation registers.
- If Spring Integration annotations appear to have no effect at all, the absence of `@EnableIntegration` somewhere in the application's configuration is one of the first things worth checking.
- Spring Boot autoconfiguration typically adds `@EnableIntegration` automatically when Spring Integration is on the classpath, which is why many Spring Boot applications never need to declare it explicitly — but it's still the underlying activation step that makes everything else in this section work, whether declared explicitly or added automatically.
