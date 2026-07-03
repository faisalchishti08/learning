---
card: spring-framework
gi: 193
slug: standard-custom-events-recap
title: "Standard & custom events recap"
---

## 1. What it is

Spring's event system provides two categories of events: **standard context lifecycle events** (built-in, fired by Spring itself) and **custom application events** (defined and published by your code). This tutorial consolidates both — how they fit together, how to choose, and how to combine them in a real application.

**Standard events Spring publishes automatically:**

| Event class | When fired |
|---|---|
| `ContextRefreshedEvent` | Context fully started / refreshed |
| `ContextStartedEvent` | `ctx.start()` called |
| `ContextStoppedEvent` | `ctx.stop()` called |
| `ContextClosedEvent` | Context destroyed (last lifecycle call) |
| `ApplicationStartedEvent` | Spring Boot: application context started |
| `ApplicationReadyEvent` | Spring Boot: ready to serve requests |
| `ApplicationFailedEvent` | Spring Boot: startup failed |

**Custom events: extend `ApplicationEvent` (or use any POJO):**

```java
// With ApplicationEvent — carries source reference
record UserRegisteredEvent(String userId) extends ApplicationEvent {
    UserRegisteredEvent(Object src, String userId) { super(src); }
}

// Plain POJO — simpler, wrapped in PayloadApplicationEvent<T>
record OrderShippedEvent(String orderId, String trackingCode) {}
```

## 2. Why & when

- **Standard events** — bootstrap tasks: warm caches at `ContextRefreshedEvent`, register with service registry at `ApplicationReadyEvent`, release resources at `ContextClosedEvent`.
- **Custom events** — decouple business logic: order service publishes `OrderPlaced`; email, audit, and inventory services react independently.
- **Combine both** — use `ContextRefreshedEvent` to load data, custom events for all domain-level pub/sub.
- **Don't use events** when the publisher needs a response from the listener — use a direct method call. Events are fire-and-forget.

## 3. Core concept

Both categories flow through the same pipeline:

```
publishEvent(event)
    ↓
ApplicationEventMulticaster
    ↓ resolves ResolvableType (for generics)
    ↓ matches ApplicationListener<E> beans
    ↓ matches @EventListener methods
    ↓ applies @Order / SmartApplicationListener ordering
    ↓ dispatches synchronously (or async if TaskExecutor configured)
```

**Decision guide:**

| Situation | Use |
|---|---|
| Cache warmup after startup | `@EventListener` on `ContextRefreshedEvent` |
| Service registration on ready | `@EventListener` on `ApplicationReadyEvent` (Spring Boot) |
| Graceful shutdown cleanup | `@EventListener` on `ContextClosedEvent` |
| Decouple business side-effects | Custom event + `publishEvent()` |
| Post-commit side-effects only | Custom event + `@TransactionalEventListener` |
| Typed multi-entity routing | Generic custom event + `getResolvableType()` override |
| Ordered pipeline steps | `@Order` on `@EventListener` methods |
| External parallel fan-out | `@Async` + `@EventListener` |
| Long-running async + shutdown | `@Async` + `@TransactionalEventListener` + `AFTER_COMMIT` |

## 4. Diagram

<svg viewBox="0 0 700 205" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="rca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rcb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Left: Standard Events -->
  <rect x="5" y="5" width="200" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="22" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Standard Context Events</text>
  <text x="105" y="38" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ContextRefreshedEvent</text>
  <text x="105" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ContextStartedEvent</text>
  <text x="105" y="66" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ContextStoppedEvent</text>
  <text x="105" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ContextClosedEvent</text>
  <text x="105" y="94" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ApplicationReadyEvent (Boot)</text>
  <text x="105" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ApplicationFailedEvent (Boot)</text>
  <text x="105" y="124" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">Published automatically by Spring</text>

  <!-- Right: Custom Events -->
  <rect x="240" y="5" width="200" height="130" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="22" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Custom Application Events</text>
  <text x="340" y="38" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">extends ApplicationEvent (with source)</text>
  <text x="340" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">plain POJO (wrapped automatically)</text>
  <text x="340" y="66" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">generic EntityEvent&lt;T&gt; + getResolvableType</text>
  <text x="340" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@TransactionalEventListener binding</text>
  <text x="340" y="94" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Async fan-out</text>
  <text x="340" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Order pipeline</text>
  <text x="340" y="124" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">Published by your code via publishEvent()</text>

  <!-- Common pipeline -->
  <rect x="475" y="5" width="220" height="130" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="22" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Common Pipeline</text>
  <text x="585" y="38" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ApplicationEventMulticaster</text>
  <text x="585" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ResolvableType matching</text>
  <text x="585" y="66" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">ApplicationListener&lt;E&gt; beans</text>
  <text x="585" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@EventListener methods</text>
  <text x="585" y="94" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Order / SmartApplicationListener</text>
  <text x="585" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Async dispatch (optional)</text>
  <text x="585" y="124" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">@TransactionalEventListener (optional)</text>

  <line x1="207" y1="65" x2="238" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rca)"/>
  <line x1="442" y1="65" x2="472" y2="65" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rcb)"/>

  <!-- Summary row -->
  <rect x="5" y="152" width="690" height="46" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="168" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Choose standard events for infrastructure lifecycle hooks, custom events for business domain decoupling.</text>
  <text x="350" y="183" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Both flow through the same multicaster; all features (@Order, @Async, @TransactionalEventListener) work with both.</text>
</svg>

Standard and custom events share the same multicaster; the distinction is who publishes them and when.

## 5. Runnable example

Scenario: **order management system** using both standard lifecycle events (warmup, shutdown) and custom business events (order placed, order fulfilled).

### Level 1 — Basic

Standard `ContextRefreshedEvent` for cache warmup; custom `OrderPlacedEvent`.

```java
// EventsRecapBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.stereotype.*;

// Custom business event
record OrderPlacedEvent(String orderId, String customerId) extends ApplicationEvent {
    OrderPlacedEvent(Object src, String orderId, String customerId) {
        super(src);
    }
    public String getOrderId()    { return orderId; }
    public String getCustomerId() { return customerId; }
}

// Infrastructure listener: use standard event for startup tasks
@Component
class CacheWarmupListener {
    private boolean warmed = false;

    @EventListener
    public void onRefresh(ContextRefreshedEvent e) {
        if (!warmed) {
            System.out.println("[Cache] Warming product cache at context refresh.");
            warmed = true;
        }
    }
}

// Business listener: use custom event for domain logic
@Component
class OrderNotificationListener {
    @EventListener
    public void onOrder(OrderPlacedEvent e) {
        System.out.println("[Notification] New order " + e.getOrderId()
            + " from customer " + e.getCustomerId());
    }
}

@Service
class OrderService {
    private final ApplicationEventPublisher pub;
    OrderService(ApplicationEventPublisher pub) { this.pub = pub; }

    public void place(String orderId, String customerId) {
        System.out.println("[Order] Placing " + orderId);
        pub.publishEvent(new OrderPlacedEvent(this, orderId, customerId));
    }
}

@Configuration @ComponentScan class RecapConfig { }

public class EventsRecapBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RecapConfig.class);
        // Cache warmup already happened during context refresh above
        ctx.getBean(OrderService.class).place("ORD-001", "CUST-A");
        ctx.close();
    }
}
```

How to run: `java EventsRecapBasic.java`

`ContextRefreshedEvent` fires automatically when the context completes startup — no `publishEvent()` needed for it. Custom `OrderPlacedEvent` requires explicit `publishEvent()`. Both use the same `@EventListener` annotation; Spring routes each to the appropriate listener based on the parameter type.

### Level 2 — Intermediate

Multiple custom events forming a workflow; `ContextClosedEvent` cleanup.

```java
// EventsRecapIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.*;
import java.util.concurrent.atomic.*;

// Custom event hierarchy
record OrderPlaced(String orderId)    extends ApplicationEvent { OrderPlaced(Object s, String id) { super(s); } public String getOrderId() { return orderId; } }
record PaymentConfirmed(String orderId) extends ApplicationEvent { PaymentConfirmed(Object s, String id) { super(s); } public String getOrderId() { return orderId; } }
record OrderFulfilled(String orderId) extends ApplicationEvent { OrderFulfilled(Object s, String id) { super(s); } public String getOrderId() { return orderId; } }

@Component
class OrderWorkflowListener {
    private final ApplicationEventPublisher pub;
    OrderWorkflowListener(ApplicationEventPublisher pub) { this.pub = pub; }

    @EventListener @Order(1)
    public void step1Validate(OrderPlaced e) {
        System.out.println("[1-Validate] Order " + e.getOrderId() + " passed validation");
    }

    @EventListener @Order(2)
    public void step2Pay(OrderPlaced e) {
        System.out.println("[2-Pay]      Charging for " + e.getOrderId());
        pub.publishEvent(new PaymentConfirmed(this, e.getOrderId()));
    }

    @EventListener
    public void onPaymentConfirmed(PaymentConfirmed e) {
        System.out.println("[Payment]    Confirmed payment for " + e.getOrderId());
        pub.publishEvent(new OrderFulfilled(this, e.getOrderId()));
    }

    @EventListener
    public void onFulfilled(OrderFulfilled e) {
        System.out.println("[Fulfilled]  Order " + e.getOrderId() + " dispatched");
    }
}

// Infrastructure: cleanup on shutdown
@Component
class ShutdownCleanupListener {
    private final AtomicBoolean running = new AtomicBoolean(true);

    @EventListener
    public void onClose(ContextClosedEvent e) {
        running.set(false);
        System.out.println("[Shutdown] Releasing resources, running=" + running.get());
    }
}

@Service
class WorkflowService {
    private final ApplicationEventPublisher pub;
    WorkflowService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void placeOrder(String id) { pub.publishEvent(new OrderPlaced(this, id)); }
}

@Configuration @ComponentScan class RecapIntermConfig { }

public class EventsRecapIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RecapIntermConfig.class);
        ctx.getBean(WorkflowService.class).placeOrder("ORD-X1");
        ctx.close();  // triggers ContextClosedEvent
    }
}
```

How to run: `java EventsRecapIntermediate.java`

One `publishEvent(OrderPlaced)` triggers a chain: `step1Validate` (@Order 1) → `step2Pay` (@Order 2) → which publishes `PaymentConfirmed` → `onPaymentConfirmed` publishes `OrderFulfilled` → `onFulfilled` logs dispatch. `ContextClosedEvent` fires on `ctx.close()`.

### Level 3 — Advanced

Spring Boot; combines standard events, custom events, `@Async`, `@TransactionalEventListener`.

```java
// EventsRecapAdvanced.java
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.*;
import org.springframework.context.event.*;
import org.springframework.core.annotation.Order;
import org.springframework.scheduling.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.event.*;
import org.springframework.transaction.support.*;

record InvoiceCreatedEvent(String invoiceId, String email) extends ApplicationEvent {
    InvoiceCreatedEvent(Object src, String invoiceId, String email) { super(src); }
    public String getInvoiceId() { return invoiceId; }
    public String getEmail() { return email; }
}

// Standard event: warm system on ready
@org.springframework.stereotype.Component
class ReadyListener {
    @EventListener
    public void onReady(ApplicationReadyEvent e) {
        System.out.println("[Boot] Application ready — running post-start tasks");
    }
}

// Sync pre-commit validation (inside transaction)
@org.springframework.stereotype.Component
class PreCommitValidator {
    @TransactionalEventListener(phase = TransactionPhase.BEFORE_COMMIT)
    @Order(1)
    public void validate(InvoiceCreatedEvent e) {
        System.out.println("[Validate] Pre-commit check for invoice " + e.getInvoiceId());
    }
}

// Async post-commit notification
@org.springframework.stereotype.Component
class AsyncEmailSender {
    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void sendEmail(InvoiceCreatedEvent e) {
        System.out.println("[Email] Async send to " + e.getEmail()
            + " for invoice " + e.getInvoiceId()
            + " thread=" + Thread.currentThread().getName());
    }
}

@org.springframework.stereotype.Service
class InvoiceService {
    private final ApplicationEventPublisher pub;
    private final PlatformTransactionManager txm;
    InvoiceService(ApplicationEventPublisher pub, PlatformTransactionManager txm) {
        this.pub = pub; this.txm = txm;
    }
    public void createInvoice(String id, String email) {
        var s = txm.getTransaction(new DefaultTransactionDefinition());
        System.out.println("[Invoice] Creating " + id);
        pub.publishEvent(new InvoiceCreatedEvent(this, id, email));
        txm.commit(s);
        System.out.println("[Invoice] Committed.");
    }
}

@SpringBootApplication
@EnableAsync
@EnableTransactionManagement
public class EventsRecapAdvanced {
    public static void main(String[] args) throws Exception {
        var ctx = SpringApplication.run(EventsRecapAdvanced.class, args);
        ctx.getBean(InvoiceService.class).createInvoice("INV-001", "alice@example.com");
        Thread.sleep(200);
        SpringApplication.exit(ctx);
    }
    @org.springframework.context.annotation.Bean
    PlatformTransactionManager txm() { return new ResourcelessTransactionManager(); }
}
```

How to run: `./mvnw spring-boot:run` in a Spring Boot project.

Execution order: `ApplicationReadyEvent` → `onReady` → `createInvoice` starts TX → `BEFORE_COMMIT`: `validate` fires synchronously → TX commits → `AFTER_COMMIT`: `sendEmail` dispatched asynchronously on a worker thread while `createInvoice` returns to the caller.

## 6. Walkthrough

Tracing `createInvoice("INV-001", "alice@example.com")`:

**T1 — `ApplicationReadyEvent`** fires at app start: `[Boot] Application ready`.

**T2 — `createInvoice` called, TX begins.**

**T3 — `publishEvent(InvoiceCreatedEvent)` called:** registers `BEFORE_COMMIT` and `AFTER_COMMIT` synchronizations.

**T4 — `txm.commit(s)` is about to execute:**
- `BEFORE_COMMIT` phase fires first.
- `PreCommitValidator.validate` runs synchronously: `[Validate] Pre-commit check for INV-001`.

**T5 — Transaction commits.**

**T6 — `AFTER_COMMIT` phase fires:**
- `AsyncEmailSender.sendEmail` is `@Async` — Spring submits it to the task executor thread pool.
- `createInvoice` returns without waiting.
- Worker thread prints `[Email] Async send to alice@example.com for INV-001 thread=task-1`.

**T7 — `ctx.close()` fires `ContextClosedEvent`** (not shown above but present in broader app lifecycle).

## 7. Gotchas & takeaways

> **Standard events are infrastructure events, not business events.** Do not publish business logic from `ContextRefreshedEvent` listeners in production. Cache warmup is acceptable; triggering business workflows from startup is fragile (circular dependencies, missing beans mid-init).

> **Event chains can run indefinitely.** If Listener A publishes Event B, and Listener B publishes Event C, and so on — Spring dispatches synchronously and recursively. Add a guard flag or max-depth check if the chain depth is not bounded.

- **Idempotency guard for `ContextRefreshedEvent`:** the event fires on every `refresh()`, including in test setups. Use an `AtomicBoolean` flag to ensure warmup runs only once.
- **`ApplicationReadyEvent` vs `ContextRefreshedEvent`:** in Spring Boot, prefer `ApplicationReadyEvent` for startup logic — it fires after `CommandLineRunner` / `ApplicationRunner` beans complete, meaning the app is fully initialised. `ContextRefreshedEvent` fires earlier (before runners).
- **`@Async` + `@TransactionalEventListener`:** without `@Async`, `AFTER_COMMIT` listeners run synchronously on the commit thread. With `@Async`, they run on a worker thread — beware thread-local data (security context, request scope) not being available unless explicitly propagated.
- All features — `@Order`, `@Async`, `@TransactionalEventListener`, `ResolvableType` generics — compose cleanly on the same listener method. You can combine `@Async @TransactionalEventListener @Order(2)` on a single method.
