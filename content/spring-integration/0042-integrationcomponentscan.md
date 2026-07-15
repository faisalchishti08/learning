---
card: spring-integration
gi: 42
slug: integrationcomponentscan
title: "@IntegrationComponentScan"
---

## 1. What it is

`@IntegrationComponentScan` is a configuration-class annotation that extends Spring's regular component scanning specifically to discover `@MessagingGateway`-annotated interfaces (card 0032) and generate their runtime proxy implementations. Plain Spring `@ComponentScan` finds concrete classes annotated with stereotypes like `@Component` or `@Service`; because a `@MessagingGateway` is declared on an *interface* (which has no implementation to instantiate directly), it needs this dedicated scanning mechanism to find those interfaces and generate a working proxy bean for each one.

## 2. Why & when

You reach for `@IntegrationComponentScan` specifically when messaging gateway interfaces are spread across packages that regular component scanning wouldn't otherwise pick up correctly:

- **You're declaring `@MessagingGateway` interfaces anywhere in the application** and want them automatically discovered and turned into injectable beans, the same way `@Component`-annotated classes are automatically discovered — without this scan, each gateway interface would need to be manually registered as a `@Bean` one at a time.
- **Gateway interfaces live in a different package than your `@Configuration` class's default scan base**, and plain `@ComponentScan`'s default behavior (scanning from the configuration class's own package downward) wouldn't reach them — `@IntegrationComponentScan(basePackages = "...")` lets you point explicitly at where gateway interfaces actually live.
- **You want gateway interfaces to be `@Autowired`-injectable throughout the application**, exactly like any other Spring-managed bean, without every one of them needing individual `@Bean` factory method boilerplate.

## 3. Core concept

Think of `@IntegrationComponentScan` like a building inspector whose job is specifically to find and certify *blueprints* (interfaces) rather than finished buildings (concrete classes) — a regular inspector (`@ComponentScan`) walks the property looking for completed structures to register, but a blueprint alone isn't a structure; it needs someone whose job is specifically to take that blueprint and have it built (generate the proxy implementation) before it can be registered as usable.

```java
@Configuration
@EnableIntegration
@IntegrationComponentScan(basePackages = "com.example.gateways")
public class IntegrationConfig {
    // any @MessagingGateway interface under com.example.gateways is now
    // automatically discovered and available for @Autowired injection
}

package com.example.gateways;

@MessagingGateway
public interface OrderGateway {
    @Gateway(requestChannel = "orderRequests")
    OrderConfirmation submit(Order order);
}
```

Without `@IntegrationComponentScan` covering `com.example.gateways`, `OrderGateway` would remain just an interface declaration — nothing would generate a proxy implementation for it, and attempting to `@Autowired` it anywhere would fail with no bean found.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="IntegrationComponentScan finds MessagingGateway interfaces across specified packages and generates a working proxy bean for each, making them Autowired-injectable">
  <rect x="20" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@MessagingGateway</text>
  <text x="95" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">interface (no impl)</text>

  <line x1="170" y1="85" x2="230" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#ics1)"/>

  <rect x="240" y="55" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="330" y="78" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@IntegrationComponentScan</text>
  <text x="330" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">finds interface, builds proxy</text>

  <line x1="420" y1="85" x2="480" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#ics2)"/>

  <rect x="490" y="60" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">injectable proxy bean</text>

  <defs>
    <marker id="ics1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ics2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

An interface alone has nothing to instantiate; the scan is specifically what generates a working, injectable implementation for it.

## 5. Runnable example

The scenario: a gateway interface that needs an implementation generated for it, starting with the manual proxy-building that would otherwise be required, then a simulated scan discovering and building proxies for multiple gateway interfaces automatically, and finally scanning limited to a specific package to show that scope matters.

### Level 1 — Basic

```java
// ManualProxyBaselineDemo.java
// Establishes the baseline: WITHOUT any scanning mechanism, a gateway interface needs its
// implementation built by hand, using java.lang.reflect.Proxy — exactly the tedious work
// @IntegrationComponentScan automates for every discovered interface.
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.lang.reflect.*;

public class ManualProxyBaselineDemo {
    record Order(String id) {}
    record OrderConfirmation(String orderId, String status) {}

    interface OrderGateway { // the "blueprint" — no implementation of its own
        OrderConfirmation submit(Order order);
    }

    public static void main(String[] args) {
        QueueChannel requestChannel = new QueueChannel();
        Thread flow = new Thread(() -> {
            Message<?> req = requestChannel.receive();
            Order order = (Order) req.getPayload();
            var replyChannel = req.getHeaders().getReplyChannel();
            ((org.springframework.messaging.MessageChannel) replyChannel).send(
                MessageBuilder.withPayload(new OrderConfirmation(order.id(), "CONFIRMED")).build());
        });
        flow.start();

        MessagingTemplate template = new MessagingTemplate();
        template.setDefaultChannel(requestChannel);

        // MANUALLY building the proxy implementation, by hand, for ONE interface:
        OrderGateway gateway = (OrderGateway) Proxy.newProxyInstance(
            OrderGateway.class.getClassLoader(), new Class[]{OrderGateway.class},
            (proxy, method, methodArgs) -> template.convertSendAndReceive(methodArgs[0], OrderConfirmation.class));

        System.out.println("Manually-built proxy result: " + gateway.submit(new Order("ORD-1")));
    }
}
```

How to run: `java ManualProxyBaselineDemo.java`. Expected output: `Manually-built proxy result: OrderConfirmation[orderId=ORD-1, status=CONFIRMED]` — this is exactly the tedious, per-interface manual work `@IntegrationComponentScan` automates for every `@MessagingGateway` interface it discovers.

### Level 2 — Intermediate

Simulating what the scan does at scale: discovering multiple gateway interfaces across a registry and automatically generating a proxy for each, rather than hand-building one `Proxy.newProxyInstance` call per interface as in Level 1.

```java
// SimulatedScanDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.lang.reflect.*;
import java.util.*;

public class SimulatedScanDemo {
    record Order(String id) {}
    record OrderConfirmation(String orderId, String status) {}
    record Refund(String orderId) {}
    record RefundConfirmation(String orderId, boolean processed) {}

    interface OrderGateway { OrderConfirmation submit(Order order); }
    interface RefundGateway { RefundConfirmation process(Refund refund); }

    // stands in for what @IntegrationComponentScan does: discover EVERY gateway interface, build a proxy for each
    static Object scanAndBuildProxy(Class<?> gatewayInterface, MessagingTemplate template) {
        return Proxy.newProxyInstance(gatewayInterface.getClassLoader(), new Class[]{gatewayInterface},
            (proxy, method, methodArgs) -> template.convertSendAndReceive(methodArgs[0], method.getReturnType()));
    }

    public static void main(String[] args) {
        QueueChannel orderChannel = new QueueChannel();
        QueueChannel refundChannel = new QueueChannel();

        new Thread(() -> {
            Message<?> req = orderChannel.receive();
            Order o = (Order) req.getPayload();
            ((org.springframework.messaging.MessageChannel) req.getHeaders().getReplyChannel()).send(
                MessageBuilder.withPayload(new OrderConfirmation(o.id(), "CONFIRMED")).build());
        }).start();

        new Thread(() -> {
            Message<?> req = refundChannel.receive();
            Refund r = (Refund) req.getPayload();
            ((org.springframework.messaging.MessageChannel) req.getHeaders().getReplyChannel()).send(
                MessageBuilder.withPayload(new RefundConfirmation(r.orderId(), true)).build());
        }).start();

        MessagingTemplate orderTemplate = new MessagingTemplate();
        orderTemplate.setDefaultChannel(orderChannel);
        MessagingTemplate refundTemplate = new MessagingTemplate();
        refundTemplate.setDefaultChannel(refundChannel);

        System.out.println("=== Scanning for @MessagingGateway interfaces ===");
        OrderGateway orderGateway = (OrderGateway) scanAndBuildProxy(OrderGateway.class, orderTemplate);
        RefundGateway refundGateway = (RefundGateway) scanAndBuildProxy(RefundGateway.class, refundTemplate);
        System.out.println("=== 2 gateway proxies generated, both now injectable ===");

        System.out.println(orderGateway.submit(new Order("ORD-1")));
        System.out.println(refundGateway.process(new Refund("ORD-1")));
    }
}
```

How to run: `java SimulatedScanDemo.java`. Expected output: the scan announcements, then `OrderConfirmation[orderId=ORD-1, status=CONFIRMED]` and `RefundConfirmation[orderId=ORD-1, processed=true]` — two completely independent gateway interfaces, each discovered and given a working proxy implementation by the same scanning mechanism, mirroring how `@IntegrationComponentScan` handles every gateway interface it finds across its configured base packages.

### Level 3 — Advanced

Restricting the scan to a specific package (rather than scanning everything) shows why `basePackages` matters — an interface outside the scanned scope is simply never discovered, exactly as if `@IntegrationComponentScan` had never been configured to look there at all.

```java
// ScopedScanDemo.java
import java.lang.reflect.*;
import java.util.*;

public class ScopedScanDemo {
    interface OrderGateway { String submit(String order); }       // "in scope" package
    interface LegacyReportGateway { String generate(String id); } // "out of scope" package, simulated

    // stands in for @IntegrationComponentScan(basePackages = "com.example.gateways.orders")
    static Set<Class<?>> simulateScopedScan(String simulatedBasePackage, Map<String, Class<?>> allDiscoverableInterfaces) {
        Set<Class<?>> found = new HashSet<>();
        for (var entry : allDiscoverableInterfaces.entrySet()) {
            if (entry.getKey().startsWith(simulatedBasePackage)) {
                found.add(entry.getValue());
            }
        }
        return found;
    }

    public static void main(String[] args) {
        Map<String, Class<?>> allInterfacesInApp = Map.of(
            "com.example.gateways.orders.OrderGateway", OrderGateway.class,
            "com.example.legacy.reports.LegacyReportGateway", LegacyReportGateway.class);

        Set<Class<?>> discovered = simulateScopedScan("com.example.gateways.orders", allInterfacesInApp);

        System.out.println("Scan scoped to 'com.example.gateways.orders' found: " + discovered);
        System.out.println("LegacyReportGateway discovered? " + discovered.contains(LegacyReportGateway.class));
        System.out.println("(It lives in a DIFFERENT package the scan was never told to look at)");
    }
}
```

How to run: `java ScopedScanDemo.java`. Expected output: `Scan scoped to 'com.example.gateways.orders' found: [interface ScopedScanDemo$OrderGateway]` then `LegacyReportGateway discovered? false` — the interface living in a package outside the configured `basePackages` scope was never found, exactly the outcome a misconfigured (too-narrow) `@IntegrationComponentScan` produces in a real application, silently leaving a gateway interface without a generated implementation.

## 6. Walkthrough

Tracing `ScopedScanDemo` in execution order:

1. `allInterfacesInApp` represents every gateway-shaped interface that exists somewhere in the application's source tree, keyed by their fully-qualified package-and-class name — standing in for what a real classpath scan would discover across the whole application.
2. `simulateScopedScan("com.example.gateways.orders", allInterfacesInApp)` is called, mirroring `@IntegrationComponentScan(basePackages = "com.example.gateways.orders")`.
3. Inside the scan, each entry's key is checked with `startsWith(simulatedBasePackage)` — `"com.example.gateways.orders.OrderGateway"` starts with `"com.example.gateways.orders"`, so `OrderGateway.class` is added to the discovered set.
4. `"com.example.legacy.reports.LegacyReportGateway"` does **not** start with `"com.example.gateways.orders"` — it lives in a completely different package — so it is never added to the discovered set, regardless of the fact that it's a perfectly valid gateway-shaped interface elsewhere in the same application.
5. The discovered set, containing only `OrderGateway`, is returned and printed.
6. The final check, `discovered.contains(LegacyReportGateway.class)`, confirms `false` — in a real Spring application, this is precisely the scenario where `@Autowired LegacyReportGateway gateway` would fail at startup with "no qualifying bean found," and the root cause would be that `@IntegrationComponentScan`'s configured `basePackages` simply never reached the package that interface lives in.

```
allInterfaces = {
  "com.example.gateways.orders.OrderGateway": OrderGateway,
  "com.example.legacy.reports.LegacyReportGateway": LegacyReportGateway
}

scan(basePackage="com.example.gateways.orders"):
  "com.example.gateways.orders.OrderGateway".startsWith(base) -> TRUE  -> discovered
  "com.example.legacy.reports.LegacyReportGateway".startsWith(base) -> FALSE -> NOT discovered
```

## 7. Gotchas & takeaways

> When `@IntegrationComponentScan` is declared with no `basePackages` argument, it defaults to scanning from the annotated configuration class's own package downward — exactly like plain `@ComponentScan`'s default behavior. A gateway interface declared in a sibling or unrelated package (not a sub-package of the configuration class) will silently go undiscovered unless `basePackages` is set explicitly to cover it — this is the most common cause of "why isn't my gateway bean available" errors, and it produces no error at startup, only a missing-bean failure later, at the point of injection.

- `@IntegrationComponentScan` extends component scanning specifically to discover `@MessagingGateway`-annotated interfaces and generate their proxy implementations — plain `@ComponentScan` doesn't handle interfaces this way, since it's built around discovering concrete, instantiable classes.
- Use it whenever `@MessagingGateway` interfaces are declared anywhere in the application, so they become automatically injectable beans rather than needing manual `@Bean` factory methods.
- Set `basePackages` explicitly whenever gateway interfaces live outside the default scan scope (the configuration class's own package and its sub-packages) — an interface outside the scanned scope is never discovered, with no error at startup.
- The generated proxy is what actually implements the gateway interface's methods, translating each call into the message send/receive mechanics detailed in card 0032 — the scan's job is purely discovery and proxy generation, not the messaging logic itself.
- This pairs directly with `@EnableIntegration` (card 0041): one activates the core messaging infrastructure, the other specifically extends discovery to cover gateway interfaces — both are typically needed together in any application using `@MessagingGateway`.
