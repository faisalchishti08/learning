---
card: java
gi: 1046
slug: spring-core-di-container
title: Spring Core & DI container
---

## 1. What it is

Spring's core is an **IoC (Inversion of Control) container**: instead of your objects constructing their own dependencies with `new`, you annotate classes as **beans** (`@Component`, `@Service`, `@Repository`), declare their dependencies as constructor parameters, and the container — the `ApplicationContext` — takes over constructing every bean, wiring their dependencies together automatically, and handing you the fully-assembled object graph. This is [dependency injection](1014-dependency-injection.md) as a manual technique, automated: instead of hand-wiring `new OrderService(new OrderRepository())` yourself, you write both classes, annotate them, and let the container figure out the wiring.

## 2. Why & when

Manually wiring dependencies by hand works fine for a handful of classes, but a real application's object graph — dozens or hundreds of interdependent services, repositories, and configuration objects — becomes tedious and error-prone to construct by hand in the right order, especially as dependencies change and multiply. Spring's container inspects your classes' constructors, works out the entire dependency graph automatically (which bean needs which other bean), and constructs everything in the correct order — you write classes and annotate their relationships; you never write the `new SomeBean(new AnotherBean(new ThirdBean()))` chain yourself. It also lets a bean's *implementation* be swapped (a real service for production, a test double for tests) purely through configuration, without touching the classes that depend on it.

Reach for Spring's DI container when an application has enough classes and inter-dependencies that manual wiring becomes a genuine maintenance burden, or when you want configuration-driven flexibility over which concrete implementation gets wired in for a given interface (different beans active in different profiles — test versus production). For a handful of classes with simple relationships, manual dependency injection (as covered in [dependency injection](1014-dependency-injection.md)) remains simpler and requires no framework at all.

## 3. Core concept

```java
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

interface PaymentGateway { boolean charge(double amount); }

@Component
class StripeGateway implements PaymentGateway {
    public boolean charge(double amount) {
        System.out.println("Charging $" + amount + " via Stripe");
        return true;
    }
}

@Component
class OrderService {
    private final PaymentGateway gateway; // Spring supplies this automatically

    // Constructor injection: Spring sees this constructor, finds a bean
    // implementing PaymentGateway, and passes it in -- no `new` needed anywhere.
    OrderService(PaymentGateway gateway) {
        this.gateway = gateway;
    }

    void placeOrder(double amount) { gateway.charge(amount); }
}

@Configuration
@ComponentScan(basePackages = "com.example")
class AppConfig {}

AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
OrderService service = context.getBean(OrderService.class); // fully wired, ready to use
service.placeOrder(19.99);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The ApplicationContext scanning for annotated components, constructing StripeGateway first, then constructing OrderService and automatically injecting the StripeGateway bean into its constructor">
  <rect x="30" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>

  <rect x="270" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="340" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">StripeGateway bean</text>

  <rect x="270" y="120" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="340" y="141" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService bean</text>

  <line x1="210" y1="75" x2="270" y2="37" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="250" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">1. construct</text>
  <line x1="210" y1="90" x2="270" y2="137" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="250" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2. construct + inject</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The container constructs beans in dependency order, automatically injecting each bean's required collaborators.

## 5. Runnable example

Scenario: an order-placement service depending on a payment gateway, evolving from manual dependency wiring into a fully container-managed Spring bean graph.

### Level 1 — Basic

```java
// File: ManualWiringBasic.java -- plain manual DI, no Spring at all
public class ManualWiringBasic {
    interface PaymentGateway { boolean charge(double amount); }

    static class StripeGateway implements PaymentGateway {
        public boolean charge(double amount) {
            System.out.println("Charging $" + amount + " via Stripe");
            return true;
        }
    }

    static class OrderService {
        private final PaymentGateway gateway;
        OrderService(PaymentGateway gateway) { this.gateway = gateway; }
        void placeOrder(double amount) { gateway.charge(amount); }
    }

    public static void main(String[] args) {
        // Manual wiring -- fine for two classes, but this chain grows with every new dependency.
        OrderService service = new OrderService(new StripeGateway());
        service.placeOrder(19.99);
    }
}
```

**How to run:** save as `ManualWiringBasic.java`, then `javac ManualWiringBasic.java && java ManualWiringBasic` (JDK 17+).

Expected output:
```
Charging $19.99 via Stripe
```

This works fine for two classes — but every additional service and its dependencies would require extending this manual `new` chain by hand, in the correct construction order, which becomes unwieldy as the object graph grows.

### Level 2 — Intermediate

```java
// File: src/main/java/com/example/SpringBasic.java
package com.example;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

interface PaymentGateway { boolean charge(double amount); }

@Component
class StripeGateway implements PaymentGateway {
    public boolean charge(double amount) {
        System.out.println("Charging $" + amount + " via Stripe");
        return true;
    }
}

@Component
class OrderService {
    private final PaymentGateway gateway;

    @Autowired // optional on a single constructor in modern Spring, shown here for clarity
    OrderService(PaymentGateway gateway) {
        this.gateway = gateway;
    }

    void placeOrder(double amount) { gateway.charge(amount); }
}

@Configuration
@ComponentScan(basePackages = "com.example")
class AppConfig {}

public class SpringBasic {
    public static void main(String[] args) {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
        OrderService service = context.getBean(OrderService.class); // ALREADY wired -- no `new` here
        service.placeOrder(19.99);
        context.close();
    }
}
```

**How to run:** place in a Maven project with `spring-context` as a dependency, then run `mvn compile exec:java -Dexec.mainClass=com.example.SpringBasic`.

Expected output:
```
Charging $19.99 via Stripe
```

The real-world concern added: `context.getBean(OrderService.class)` returns a fully-constructed `OrderService` with its `StripeGateway` dependency already injected — the container scanned for `@Component`-annotated classes, discovered `OrderService`'s constructor requires a `PaymentGateway`, found `StripeGateway` implementing it, and wired them together automatically. Nowhere in `SpringBasic.main` does `new OrderService(...)` or `new StripeGateway()` ever appear.

### Level 3 — Advanced

```java
// File: src/main/java/com/example/SpringAdvanced.java
package com.example;

import org.springframework.context.annotation.*;
import org.springframework.stereotype.Component;

interface PaymentGateway { boolean charge(double amount); }

@Component
@Profile("production")
class StripeGateway implements PaymentGateway {
    public boolean charge(double amount) {
        System.out.println("Charging $" + amount + " via Stripe (production)");
        return true;
    }
}

// A DIFFERENT bean implementing the same interface, active only in the "test" profile --
// swapped in purely through configuration, with OrderService completely unaware.
@Component
@Profile("test")
class FakeGateway implements PaymentGateway {
    public boolean charge(double amount) {
        System.out.println("Simulating charge of $" + amount + " (test profile, no real charge)");
        return true;
    }
}

@Component
class OrderService {
    private final PaymentGateway gateway;
    OrderService(PaymentGateway gateway) { this.gateway = gateway; }
    void placeOrder(double amount) { gateway.charge(amount); }
}

@Configuration
@ComponentScan(basePackages = "com.example")
class AppConfig {}

public class SpringAdvanced {
    public static void main(String[] args) {
        String activeProfile = args.length > 0 ? args[0] : "production";

        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext();
        context.getEnvironment().setActiveProfiles(activeProfile);
        context.register(AppConfig.class);
        context.refresh();

        OrderService service = context.getBean(OrderService.class);
        service.placeOrder(19.99);
        context.close();
    }
}
```

**How to run:** place in the same Maven project as Level 2, then run `mvn compile exec:java -Dexec.mainClass=com.example.SpringAdvanced -Dexec.args=production` and separately `mvn compile exec:java -Dexec.mainClass=com.example.SpringAdvanced -Dexec.args=test`.

Expected output (running with `production`):
```
Charging $19.99 via Stripe (production)
```

Expected output (running with `test`):
```
Simulating charge of $19.99 (test profile, no real charge)
```

The production-flavored hard case: `OrderService`'s own code is byte-for-byte identical in both runs — it only ever depends on the `PaymentGateway` interface — yet the actual behavior differs entirely depending on which Spring profile is active, since `@Profile` controls which of the two concrete beans the container registers and injects, purely through configuration, with zero code changes.

## 6. Walkthrough

Tracing what happens when `SpringAdvanced.main` runs with the `test` profile active:

1. `context.getEnvironment().setActiveProfiles("test")` tells the container which profile is active *before* any beans are actually constructed.
2. `context.register(AppConfig.class)` and `context.refresh()` trigger the container's component-scanning process: it scans the `com.example` package (per `@ComponentScan`) for classes annotated `@Component`.
3. It finds three candidates: `StripeGateway` (annotated `@Profile("production")`), `FakeGateway` (annotated `@Profile("test")`), and `OrderService` (no `@Profile` restriction, so it's active regardless of profile).
4. Because the active profile is `"test"`, the container registers `FakeGateway` as the bean satisfying the `PaymentGateway` type, and skips `StripeGateway` entirely — it's never even constructed in this run.
5. When constructing `OrderService`, the container inspects its constructor, sees it requires a `PaymentGateway`, and looks up which bean of that type is currently registered — finding `FakeGateway` (from step 4), it passes that instance into `OrderService`'s constructor.
6. `service.placeOrder(19.99)` calls `gateway.charge(19.99)` — since `gateway` holds the injected `FakeGateway` instance, this dispatches to `FakeGateway.charge`, printing `"Simulating charge of $19.99 (test profile, no real charge)"`. Had the profile been `"production"` instead, every step from 4 onward would have resolved to `StripeGateway` instead, with `OrderService`'s own source code never needing to change at all.

## 7. Gotchas & takeaways

> **Gotcha:** if two or more beans implement the same interface and are *both* eligible under the currently active profile(s) (or have no `@Profile` restriction at all), the container can't determine which one to inject and throws a `NoUniqueBeanDefinitionException` at startup — resolved either by `@Profile`/`@Qualifier` annotations to disambiguate, or by marking one bean `@Primary` as the default choice.

- Spring's `ApplicationContext` is an IoC container: it scans for annotated beans, works out their dependency graph automatically, and constructs the entire object graph without manual `new` chains.
- Constructor injection (the same technique from [dependency injection](1014-dependency-injection.md)) is how the container knows what each bean needs — it inspects constructor parameters and finds matching beans to supply.
- `@Profile` lets different concrete bean implementations be active in different environments (test versus production) purely through configuration, with dependent classes completely unaware of which implementation is actually wired in.
- Two eligible beans for the same required type with no way to disambiguate is a startup-time error (`NoUniqueBeanDefinitionException`), not a silent ambiguity — resolved via `@Qualifier`, `@Primary`, or profile restrictions.
- Manual DI remains simpler and framework-free for small applications with few interdependent classes — Spring's container earns its complexity specifically as the object graph and configuration-driven flexibility needs grow.
- See [Spring Boot](1047-spring-boot.md) for how Spring Boot builds on top of this same core container, adding auto-configuration and convention-over-configuration defaults that reduce the amount of explicit `@Configuration` needed for common application types.
