---
card: spring-cloud
gi: 11
slug: enablediscoveryclient
title: "@EnableDiscoveryClient"
---

## 1. What it is

`@EnableDiscoveryClient` is the annotation that activates automatic service discovery integration for a Spring Boot application: it triggers registration with the configured registry at startup, deregistration at shutdown, and makes `DiscoveryClient`/`ServiceRegistry` beans available for injection — all the manual wiring from the previous two cards, done automatically.

```java
@SpringBootApplication
@EnableDiscoveryClient
class PaymentServiceApplication {
    public static void main(String[] args) { SpringApplication.run(PaymentServiceApplication.class, args); }
}
```

## 2. Why & when

The previous two cards showed `ServiceRegistry.register()`/`deregister()` and `DiscoveryClient.getInstances()` as things application code could call directly. In practice, almost no application code calls `register`/`deregister` by hand — `@EnableDiscoveryClient` (backed by whichever registry starter is on the classpath: Eureka, Consul, Zookeeper) handles that automatically, tied to the application's own startup and shutdown lifecycle.

Reach for `@EnableDiscoveryClient` when:

- Building any Spring Boot application that should register itself with a service registry and be discoverable by other services — the standard case for virtually every microservice in a Spring Cloud system.
- You want registration/deregistration correctly tied to the application's actual lifecycle (readiness, graceful shutdown) without writing that lifecycle logic yourself.
- You've added a Spring Cloud discovery starter dependency (`spring-cloud-starter-netflix-eureka-client`, `spring-cloud-starter-consul-discovery`, etc.) and want it activated.

In many modern Spring Cloud setups with certain starters, discovery is auto-configured even without the explicit annotation — but understanding what `@EnableDiscoveryClient` actually triggers clarifies what's happening either way.

## 3. Core concept

```
 @SpringBootApplication
 @EnableDiscoveryClient
 class PaymentServiceApplication { ... }

 On application startup:
   1. Spring Boot's normal startup sequence runs (beans created, embedded server starts)
   2. @EnableDiscoveryClient triggers auto-registration:
        builds a Registration from application.yml (service name, port, ...)
        calls serviceRegistry.register(registration)   -- the SAME call from the previous card, automated
   3. Application is now discoverable by other services via THEIR DiscoveryClient

 On graceful shutdown:
   1. Spring's shutdown hooks trigger
   2. Auto-deregistration calls serviceRegistry.deregister(registration)
   3. Embedded server stops
```

`@EnableDiscoveryClient` is the glue tying the manual `ServiceRegistry` calls from the previous card to the application's actual Spring Boot lifecycle events.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application startup triggers automatic registration, and shutdown triggers automatic deregistration, both tied to Spring Boot lifecycle events">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">SpringApplication.run</text>

  <line x1="110" y1="60" x2="110" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a31)"/>

  <rect x="20" y="95" width="180" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="120" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">auto-register()</text>

  <rect x="440" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">shutdown hook</text>

  <line x1="530" y1="60" x2="530" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a31)"/>

  <rect x="440" y="95" width="180" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="120" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">auto-deregister()</text>

  <defs><marker id="a31" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Startup and shutdown lifecycle events automatically trigger the corresponding registry operations.

## 5. Runnable example

The scenario: a payment-service application wiring itself into discovery, evolving from the manual `ServiceRegistry` calls from the previous card written explicitly in `main`, to an annotation-driven approach where a lifecycle listener triggers the same calls automatically, to a full simulation with multiple services each self-registering on startup — the realistic shape of a small Spring Cloud system booting up.

### Level 1 — Basic

Show the manual baseline: explicit `register`/`deregister` calls written directly in application code, the tedium `@EnableDiscoveryClient` removes.

```java
public class EnableDiscoveryClientLevel1 {
    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        Registration registration = new Registration("payment-service", "10.0.1.5", 8081);

        // Every application would need to remember to write BOTH of these calls, correctly, itself.
        registry.register(registration);
        System.out.println("Manually registered: " + registration);

        // ... application runs ...

        registry.deregister(registration);
        System.out.println("Manually deregistered: " + registration);
    }
}

class Registration {
    String serviceId, host; int port;
    Registration(String serviceId, String host, int port) { this.serviceId = serviceId; this.host = host; this.port = port; }
    public String toString() { return serviceId + "@" + host + ":" + port; }
}

class ServiceRegistry {
    void register(Registration r) { System.out.println("(registry) added " + r); }
    void deregister(Registration r) { System.out.println("(registry) removed " + r); }
}
```

How to run: `java EnableDiscoveryClientLevel1.java`

Both `register` and `deregister` are written explicitly, by hand, inside `main` — every single Spring Cloud application would need to duplicate this same boilerplate, correctly, tied to its own startup and shutdown, without `@EnableDiscoveryClient` automating it.

### Level 2 — Intermediate

Add a lifecycle-listener-style component that automatically calls `register`/`deregister` in response to simulated startup/shutdown events, mirroring what `@EnableDiscoveryClient` wires up.

```java
public class EnableDiscoveryClientLevel2 {
    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        DiscoveryClientLifecycle lifecycle = new DiscoveryClientLifecycle(
            registry, new Registration("payment-service", "10.0.1.5", 8081));

        // Application code NEVER calls register/deregister directly -- lifecycle events trigger it.
        Application app = new Application(lifecycle);
        app.start(); // triggers auto-registration internally
        System.out.println("Application running, serving requests...");
        app.stop();  // triggers auto-deregistration internally
    }
}

class Registration {
    String serviceId, host; int port;
    Registration(String serviceId, String host, int port) { this.serviceId = serviceId; this.host = host; this.port = port; }
    public String toString() { return serviceId + "@" + host + ":" + port; }
}

class ServiceRegistry {
    void register(Registration r) { System.out.println("(registry) added " + r); }
    void deregister(Registration r) { System.out.println("(registry) removed " + r); }
}

// Stands in for the internal listener @EnableDiscoveryClient wires up against Spring's lifecycle events.
class DiscoveryClientLifecycle {
    private final ServiceRegistry registry;
    private final Registration registration;
    DiscoveryClientLifecycle(ServiceRegistry registry, Registration registration) {
        this.registry = registry; this.registration = registration;
    }
    void onApplicationReady() { registry.register(registration); }
    void onApplicationShutdown() { registry.deregister(registration); }
}

class Application {
    private final DiscoveryClientLifecycle lifecycle;
    Application(DiscoveryClientLifecycle lifecycle) { this.lifecycle = lifecycle; }
    void start() {
        System.out.println("Application startup sequence running...");
        lifecycle.onApplicationReady(); // triggered automatically, application code never calls registry itself
    }
    void stop() {
        lifecycle.onApplicationShutdown(); // ALSO triggered automatically
        System.out.println("Application stopped.");
    }
}
```

How to run: `java EnableDiscoveryClientLevel2.java`

`main` never calls `registry.register`/`deregister` directly — `Application.start()`/`stop()` trigger `DiscoveryClientLifecycle`'s methods internally, which is exactly the separation `@EnableDiscoveryClient` provides: application code focuses on its own logic, while the annotation's wiring handles registry bookkeeping tied to Spring Boot's actual lifecycle events.

### Level 3 — Advanced

Model a small system of three self-registering services booting up independently, each with its own `@EnableDiscoveryClient`-style lifecycle wiring, sharing one registry — the realistic multi-service startup scenario.

```java
import java.util.*;

public class EnableDiscoveryClientLevel3 {
    public static void main(String[] args) {
        ServiceRegistry sharedRegistry = new ServiceRegistry();

        List<Application> services = List.of(
            new Application(new DiscoveryClientLifecycle(sharedRegistry, new Registration("payment-service", "10.0.1.5", 8081))),
            new Application(new DiscoveryClientLifecycle(sharedRegistry, new Registration("inventory-service", "10.0.2.5", 8082))),
            new Application(new DiscoveryClientLifecycle(sharedRegistry, new Registration("order-service", "10.0.3.5", 8083)))
        );

        System.out.println("--- Booting all services ---");
        for (Application app : services) app.start(); // each self-registers, independently

        System.out.println("Registry now knows: " + sharedRegistry.knownServiceIds());

        System.out.println("--- Shutting down order-service only ---");
        services.get(2).stop(); // only order-service deregisters
        System.out.println("Registry now knows: " + sharedRegistry.knownServiceIds());
    }
}

class Registration {
    String serviceId, host; int port;
    Registration(String serviceId, String host, int port) { this.serviceId = serviceId; this.host = host; this.port = port; }
    public String toString() { return serviceId + "@" + host + ":" + port; }
}

class ServiceRegistry {
    private final Set<String> known = new TreeSet<>();
    void register(Registration r) { known.add(r.serviceId); System.out.println("(registry) added " + r); }
    void deregister(Registration r) { known.remove(r.serviceId); System.out.println("(registry) removed " + r); }
    Set<String> knownServiceIds() { return known; }
}

class DiscoveryClientLifecycle {
    private final ServiceRegistry registry;
    private final Registration registration;
    DiscoveryClientLifecycle(ServiceRegistry registry, Registration registration) {
        this.registry = registry; this.registration = registration;
    }
    void onApplicationReady() { registry.register(registration); }
    void onApplicationShutdown() { registry.deregister(registration); }
}

class Application {
    private final DiscoveryClientLifecycle lifecycle;
    Application(DiscoveryClientLifecycle lifecycle) { this.lifecycle = lifecycle; }
    void start() { lifecycle.onApplicationReady(); }
    void stop() { lifecycle.onApplicationShutdown(); }
}
```

How to run: `java EnableDiscoveryClientLevel3.java`

Each `Application` instance independently manages its own `DiscoveryClientLifecycle`, registering with the *shared* `sharedRegistry` when it starts — none of the three services know or care about the other two directly; they each just announce themselves, and stopping one (`order-service`) only removes that one entry, leaving the other two services' registrations completely untouched.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three `Application` instances are constructed, each wrapping its own `Registration` but sharing the same `sharedRegistry`. The first loop calls `start()` on each:

```
--- Booting all services ---
(registry) added payment-service@10.0.1.5:8081
(registry) added inventory-service@10.0.2.5:8082
(registry) added order-service@10.0.3.5:8083
Registry now knows: [inventory-service, order-service, payment-service]
```

`services.get(2).stop()` calls `stop()` on only the `order-service` `Application` — its `DiscoveryClientLifecycle.onApplicationShutdown()` calls `registry.deregister`, removing just that one entry:

```
--- Shutting down order-service only ---
(registry) removed order-service@10.0.3.5:8083
Registry now knows: [inventory-service, payment-service]
```

In a real Spring Cloud system, this is exactly the pattern across a whole fleet of services: each instance, annotated `@EnableDiscoveryClient`, independently registers itself against a shared registry (Eureka, Consul, etc.) on its own startup, and deregisters on its own shutdown — no service needs to know about, or coordinate with, any other service's registration; the shared registry is simply the meeting point where `DiscoveryClient` lookups (an earlier card) find whatever is currently registered.

## 7. Gotchas & takeaways

> Gotcha: with certain Spring Cloud discovery starters, `@EnableDiscoveryClient` is technically optional — adding the starter dependency alone can be enough to trigger auto-configuration, and the explicit annotation is sometimes just documentation of intent; relying on implicit auto-configuration without understanding this can make it unclear, when reading someone else's code, whether discovery is actually active.

> Gotcha: registration happening automatically on startup doesn't guarantee the application is actually *ready* to serve traffic yet — depending on configuration, an instance might register before its own internal warm-up (cache loading, connection pool initialization) has finished, briefly making it discoverable before it's truly ready; readiness probes (often layered on top via Spring Boot Actuator health groups) address this gap.

- `@EnableDiscoveryClient` automates the `ServiceRegistry.register()`/`deregister()` calls from the previous card, tying them to the application's actual Spring Boot startup and shutdown lifecycle.
- Each service instance independently registers itself with a shared registry — no coordination between services is needed, only a shared registry endpoint they all point at.
- Whether the annotation is strictly required depends on the specific discovery starter in use — some auto-configure based on the dependency alone.
- Automatic registration at startup doesn't guarantee readiness — separate readiness signaling may be needed to avoid an instance being discoverable before it can actually serve traffic correctly.
