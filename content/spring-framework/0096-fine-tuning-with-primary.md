---
card: spring-framework
gi: 96
slug: fine-tuning-with-primary
title: Fine-tuning with @Primary
---

## 1. What it is

`@Primary` marks one bean as the **preferred candidate** when multiple beans of the same type are registered and `@Autowired` can't pick a winner. Spring injects the `@Primary` bean without you needing to specify a `@Qualifier`.

Think of it as saying "when in doubt, use this one."

## 2. Why & when

When two or more beans implement the same interface (e.g., `DataSource`, `CacheManager`, `MessageConverter`), `@Autowired` throws `NoUniqueBeanDefinitionException` because it can't decide which to inject. You resolve this in one of two ways:

- `@Primary` — designate one bean as the default; everyone who autowires by type without a qualifier gets it.
- `@Qualifier` — explicitly name which bean to inject at each injection point.

Use `@Primary` when one bean is the "normal" choice and the others are special-case alternatives (test stub, secondary DB, fallback). Use `@Qualifier` when the choice genuinely depends on context.

## 3. Core concept

`@Primary` is metadata on a `BeanDefinition`. When `AutowiredAnnotationBeanPostProcessor` resolves an ambiguous type-match:

1. It collects all candidates of the required type.
2. If exactly one candidate is `@Primary`, that candidate wins — no exception.
3. If zero or more than one candidate is `@Primary`, the exception is thrown.

`@Primary` can be placed on `@Component`-annotated classes or on `@Bean` methods in `@Configuration`. It can also be set programmatically on a `BeanDefinition` via `bd.setPrimary(true)`.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <!-- Two impls -->
  <rect x="10" y="60" width="165" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="92" y="83" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Primary PostgresDS</text>
  <text x="92" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">implements DataSource</text>

  <rect x="10" y="130" width="165" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="92" y="153" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">H2DataSource</text>
  <text x="92" y="167" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">implements DataSource</text>

  <!-- Resolver -->
  <rect x="280" y="85" width="165" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="362" y="107" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="362" y="123" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DataSource ds (no qualifier)</text>

  <!-- Result -->
  <rect x="540" y="95" width="145" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="612" y="117" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Gets PostgresDS</text>
  <text x="612" y="131" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(@Primary wins)</text>

  <line x1="177" y1="82" x2="277" y2="107" stroke="#6db33f" stroke-width="2" marker-end="url(#a96)"/>
  <line x1="177" y1="152" x2="277" y2="128" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#c96)"/>
  <line x1="447" y1="117" x2="537" y2="117" stroke="#6db33f" stroke-width="2" marker-end="url(#a96)"/>
  <defs>
    <marker id="a96" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="c96" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <text x="350" y="200" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Primary resolves the ambiguity — H2DataSource is available but not injected by default</text>
</svg>

`@Primary` designates the default winner when multiple candidates of the same type exist.

## 5. Runnable example

### Level 1 — Basic

Two `MessageSender` implementations; `@Primary` selects the email one as the default.

```java
// PrimaryBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface MessageSender {
    void send(String msg);
}

@Component
@Primary    // default — injected when no qualifier is given
class EmailSender implements MessageSender {
    public void send(String msg) { System.out.println("[EMAIL] " + msg); }
}

@Component
class SmsSender implements MessageSender {
    public void send(String msg) { System.out.println("[SMS] " + msg); }
}

@Service
class NotificationService {
    private final MessageSender sender;

    @Autowired
    public NotificationService(MessageSender sender) { this.sender = sender; }

    public void notify(String msg) { sender.send(msg); }
}

@Configuration
@ComponentScan
class PrimCfg {}

public class PrimaryBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PrimCfg.class);
        ctx.getBean(NotificationService.class).notify("Order shipped");
        ctx.close();
    }
}
```

How to run: `java PrimaryBasic.java`

`@Autowired MessageSender` is ambiguous without `@Primary`. The annotation marks `EmailSender` as the default, so `NotificationService` receives it.

### Level 2 — Intermediate

Use `@Primary` on a `@Bean` method and override the primary at a specific injection point with `@Qualifier`.

```java
// PrimaryOverride.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface DataSource {
    String query(String sql);
}

@Configuration
class DsCfg {
    @Bean @Primary       // default data source for the app
    public DataSource primaryDs() {
        return sql -> "[PostgreSQL] " + sql;
    }

    @Bean("readReplica")
    public DataSource readReplicaDs() {
        return sql -> "[ReadReplica] " + sql;
    }

    @Bean("h2Test")
    public DataSource h2Ds() {
        return sql -> "[H2] " + sql;
    }
}

@Service
class OrderRepository {
    // Gets primaryDs via @Primary
    @Autowired private DataSource ds;

    // Explicitly asks for the read replica
    @Autowired @Qualifier("readReplica") private DataSource replica;

    public void demo() {
        System.out.println(ds.query("SELECT * FROM orders"));
        System.out.println(replica.query("SELECT COUNT(*) FROM orders"));
    }
}

@Configuration
@ComponentScan
class OverrideCfg {}

public class PrimaryOverride {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DsCfg.class, OverrideCfg.class);
        ctx.getBean(OrderRepository.class).demo();
        ctx.close();
    }
}
```

How to run: `java PrimaryOverride.java`

`ds` gets `primaryDs` (the `@Primary` bean). `replica` gets `readReplicaDs` (explicit `@Qualifier`). Both are `DataSource` but `@Primary` only fires for the plain `@Autowired DataSource ds` injection.

### Level 3 — Advanced

A testing scenario: production config defines `@Primary` beans, but a test config overrides the primary with a mock. This is the canonical use case for `@Primary` — safe defaults that can be replaced in tests.

```java
// PrimaryTestOverride.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface PaymentGateway {
    String charge(String card, double amount);
}

// Production configuration
@Configuration
class ProdConfig {
    @Bean @Primary
    public PaymentGateway stripeGateway() {
        return (card, amount) -> {
            System.out.println("[STRIPE] Charging " + card + " $" + amount);
            return "stripe-txn-" + System.currentTimeMillis();
        };
    }
}

// Test / stub configuration — overrides the primary
@Configuration
class TestConfig {
    @Bean @Primary   // this becomes the new primary, shadowing ProdConfig's
    public PaymentGateway mockGateway() {
        return (card, amount) -> {
            System.out.println("[MOCK] Fake charge " + card + " $" + amount);
            return "mock-txn-0001";
        };
    }
}

@Service
class CheckoutService {
    private final PaymentGateway gateway;

    @Autowired
    public CheckoutService(PaymentGateway gateway) { this.gateway = gateway; }

    public String checkout(String card, double amount) {
        String txn = gateway.charge(card, amount);
        System.out.println("Transaction: " + txn);
        return txn;
    }
}

public class PrimaryTestOverride {
    public static void main(String[] args) {
        System.out.println("=== Production context ===");
        var prod = new AnnotationConfigApplicationContext(ProdConfig.class, CheckoutService.class);
        prod.getBean(CheckoutService.class).checkout("4111-1111-1111-1111", 99.99);
        prod.close();

        System.out.println("\n=== Test context (mock overrides primary) ===");
        // Both configs registered — TestConfig's @Primary bean wins
        var test = new AnnotationConfigApplicationContext(ProdConfig.class, TestConfig.class, CheckoutService.class);
        test.getBean(CheckoutService.class).checkout("4111-1111-1111-1111", 99.99);
        test.close();
    }
}
```

How to run: `java PrimaryTestOverride.java`

In the production context only `stripeGateway` exists — it's `@Primary` and is injected. In the test context both gateways exist; `mockGateway` is also `@Primary` and **wins** because when two `@Primary` candidates exist, the last-registered one wins (configuration class order matters). This is the real-world pattern: test configs shadow prod configs with `@Primary` mocks.

## 6. Walkthrough

Execution order for the Level 3 test-context run:

1. **Both `ProdConfig` and `TestConfig` registered** — Spring processes them in registration order (`ProdConfig` first, then `TestConfig`).
2. **Bean definitions created** — `stripeGateway` (primary=true), `mockGateway` (primary=true), `checkoutService`.
3. **`CheckoutService` constructed** — `@Autowired PaymentGateway gateway` must be resolved. Two candidates, both `@Primary`. When both are primary, Spring uses the **last-registered** one: `mockGateway` (from `TestConfig`, registered after `ProdConfig`).
4. **`checkout()` called** — delegates to `mockGateway`. Output shows `[MOCK]` prefix and `mock-txn-0001`.

Expected test-context output:
```
=== Test context (mock overrides primary) ===
[MOCK] Fake charge 4111-1111-1111-1111 $99.99
Transaction: mock-txn-0001
```

## 7. Gotchas & takeaways

> If two beans are **both** `@Primary`, Spring does NOT throw immediately — it uses registration order (last wins). This can be confusing. Make sure at most one `@Primary` per type in a given context, unless the shadowing behaviour is intentional (as in the test override pattern).

> `@Primary` is **global within the context**. If every injection point of type `DataSource` must use `primaryDs`, great. But if different beans need different `DataSource`s, use `@Qualifier` — `@Primary` is not granular enough.

- `@Primary` only resolves ambiguity for **type-based injection**; name-based `getBean("beanName")` ignores it.
- Combine with `@Conditional` or `@Profile` in production to activate the `@Primary` bean only in the right environment.
- In Spring Boot, auto-configured beans are often `@Primary` (e.g., the auto-configured `DataSource`); your custom bean needs `@Primary` to override them.
- `@Primary` and `@Qualifier` can both be used together: `@Primary` sets the default; `@Qualifier` overrides at specific injection points.
