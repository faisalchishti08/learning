---
card: spring-framework
gi: 185
slug: annotation-based-event-listeners-eventlistener
title: "Annotation-based event listeners (@EventListener)"
---

## 1. What it is

`@EventListener` marks any method on a Spring bean as an event listener. The method parameter determines which event type it listens for — no interface to implement, no boilerplate.

```java
@Component
class NotificationService {

    @EventListener
    public void on(UserRegisteredEvent event) {
        sendWelcomeEmail(event.getEmail());
    }

    @EventListener(condition = "#event.vip")
    public void onVip(UserRegisteredEvent event) {
        sendVipGift(event.getUserId());
    }

    @Async
    @EventListener
    public void onAsync(UserRegisteredEvent event) {
        // runs on a different thread
    }
}
```

Compared to `ApplicationListener<E>`:
- No interface to implement.
- Method name is free; only the parameter type matters.
- Supports SpEL conditions, return-value publishing, and async dispatch.

## 2. Why & when

- **Less boilerplate** — annotating one method is less code than a full `ApplicationListener` class.
- **Multiple event types per bean** — a single bean can handle `OrderPlacedEvent`, `OrderCancelledEvent`, and `PaymentFailedEvent` with three `@EventListener` methods, without three separate classes.
- **Conditional dispatch** — `condition = "#event.amount > 1000"` fires the method only for high-value orders; filtering happens before the listener is invoked, not inside it.
- **Return value publishing** — a listener method can return a new event object; Spring re-publishes it automatically. Useful for chaining events.
- **Async listeners** — adding `@Async` runs the listener on a `TaskExecutor` thread, preventing slow I/O from blocking the publisher's thread.
- **Transactional phase** — `@TransactionalEventListener` fires only after the publishing transaction commits (or rolls back) — prevents acting on data that was never persisted.
- Prefer `ApplicationListener<E>` over `@EventListener` only when strong compile-time type safety and no SpEL expressions are required; otherwise `@EventListener` is simpler for all cases.

## 3. Core concept

`@EventListener` works via `EventListenerMethodProcessor` — a `BeanFactoryPostProcessor` that scans all beans for `@EventListener` methods and registers an adapter `ApplicationListener` for each one.

**Condition filter:** the `condition` attribute is a SpEL expression evaluated against the event. `#event` refers to the method argument. The method is NOT called if the expression evaluates to `false` or to `null`. Available variables: `#event`, `#root.event`, `#args[0]`.

**Return value republishing:** if the method returns a non-null, non-void value, Spring publishes it as a new event. Return a `List` to publish multiple events. This enables declarative event chaining without calling `publishEvent` manually.

**Async:** combine `@Async` + `@EventListener`. The calling thread returns immediately; the listener runs on the configured `TaskExecutor`. Exceptions are logged but do NOT propagate to the publisher.

**`@TransactionalEventListener`:**
```java
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onOrderCommitted(OrderPlacedEvent event) { ... }
```
Default phase is `AFTER_COMMIT`; other phases: `AFTER_ROLLBACK`, `AFTER_COMPLETION`, `BEFORE_COMMIT`.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ela" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="elb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="elc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e74c3c"/></marker>
  </defs>

  <!-- Publisher box -->
  <rect x="5" y="80" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="99" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Publisher</text>
  <text x="75" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">publishEvent(event)</text>
  <text x="75" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">same thread (sync)</text>

  <line x1="147" y1="105" x2="200" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#ela)"/>

  <!-- Dispatcher box -->
  <rect x="202" y="70" width="145" height="70" rx="6" fill="#6db33f" opacity="0.15" stroke="#6db33f" stroke-width="2"/>
  <text x="274" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">ApplicationContext</text>
  <text x="274" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">condition check (SpEL)</text>
  <text x="274" y="116" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">sync / async split</text>
  <text x="274" y="128" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">tx-phase check</text>

  <!-- Sync listener -->
  <rect x="400" y="10" width="170" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="27" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@EventListener (sync)</text>
  <text x="485" y="39" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">same thread, condition="…"</text>
  <line x1="349" y1="95" x2="398" y2="27" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ela)"/>

  <!-- Async listener -->
  <rect x="400" y="60" width="170" height="35" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="77" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@Async @EventListener</text>
  <text x="485" y="89" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">TaskExecutor thread (non-blocking)</text>
  <line x1="349" y1="100" x2="398" y2="77" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#elb)"/>

  <!-- Tx listener -->
  <rect x="400" y="110" width="170" height="35" rx="4" fill="#1c2430" stroke="#e74c3c" stroke-width="1.5"/>
  <text x="485" y="127" fill="#e74c3c" font-size="8" text-anchor="middle" font-family="sans-serif">@TransactionalEventListener</text>
  <text x="485" y="139" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">AFTER_COMMIT / AFTER_ROLLBACK</text>
  <line x1="349" y1="110" x2="398" y2="127" stroke="#e74c3c" stroke-width="1.5" marker-end="url(#elc)"/>

  <!-- Return value re-publish -->
  <rect x="400" y="160" width="170" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="485" y="177" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@EventListener (return value)</text>
  <text x="485" y="189" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">return event → republished</text>
  <line x1="349" y1="120" x2="398" y2="177" stroke="#6db33f" stroke-width="1" marker-end="url(#ela)" opacity="0.5"/>
</svg>

One publisher triggers multiple `@EventListener` methods; each is independently sync, async, transactional, or conditional.

## 5. Runnable example

The scenario is an **order processing system**: an order is placed, and multiple independent `@EventListener` methods react — growing from basic to async and transactional.

### Level 1 — Basic

Two `@EventListener` methods on the same bean; conditional listener for premium orders.

```java
// EventListenerBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.stereotype.*;

// --- Events ---
class OrderPlacedEvent extends ApplicationEvent {
    private final String orderId; private final double amount; private final boolean premium;
    OrderPlacedEvent(Object src, String id, double amt, boolean p) {
        super(src); orderId=id; amount=amt; premium=p;
    }
    public String getOrderId()  { return orderId; }
    public double getAmount()   { return amount; }
    public boolean isPremium()  { return premium; }
}

// --- Listener bean with multiple @EventListener methods ---
@Component
class OrderNotificationService {

    @EventListener
    public void sendConfirmation(OrderPlacedEvent event) {
        System.out.println("[Confirmation] Order " + event.getOrderId()
            + " placed for $" + event.getAmount());
    }

    // Fired only if event.isPremium() == true
    @EventListener(condition = "#event.premium")
    public void sendPriorityAlert(OrderPlacedEvent event) {
        System.out.println("[Priority] Premium order " + event.getOrderId() + " — fast lane!");
    }
}

@Component
class AuditService {
    @EventListener
    public void log(OrderPlacedEvent event) {
        System.out.println("[Audit] Logged: " + event.getOrderId() + " $" + event.getAmount());
    }
}

// --- Publisher ---
@Service
class OrderService {
    private final ApplicationEventPublisher pub;
    OrderService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void place(String id, double amount, boolean premium) {
        System.out.println("[OrderService] Placing order " + id);
        pub.publishEvent(new OrderPlacedEvent(this, id, amount, premium));
        System.out.println("[OrderService] publishEvent returned");
    }
}

@Configuration @ComponentScan class ElConfig { }

public class EventListenerBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ElConfig.class);
        var svc = ctx.getBean(OrderService.class);

        System.out.println("--- Regular order ---");
        svc.place("ORD-001", 50.0, false);

        System.out.println("--- Premium order ---");
        svc.place("ORD-002", 500.0, true);

        ctx.close();
    }
}
```

How to run: `java EventListenerBasic.java`

Multiple `@EventListener` methods on different beans all receive the same event independently — no shared interface, no coupling between `OrderNotificationService` and `AuditService`. `condition = "#event.premium"` uses SpEL: `#event` refers to the method parameter (`OrderPlacedEvent`); `.premium` resolves via `isPremium()`. The conditional listener is only called for the second `place()` invocation.

### Level 2 — Intermediate

Return-value republishing chains events; ordering via `@Order`; listen to multiple event types in one method.

```java
// EventListenerIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.core.annotation.*;
import org.springframework.stereotype.*;

class OrderPlacedEvent2 extends ApplicationEvent {
    private final String orderId; private final double amount;
    OrderPlacedEvent2(Object src, String id, double a) { super(src); orderId=id; amount=a; }
    public String getOrderId() { return orderId; }
    public double getAmount()  { return amount; }
}

class PaymentInitiatedEvent extends ApplicationEvent {
    private final String orderId; private final String txId;
    PaymentInitiatedEvent(Object src, String oid, String tx) { super(src); orderId=oid; txId=tx; }
    public String getOrderId() { return orderId; }
    public String getTxId()    { return txId; }
}

class PaymentCompletedEvent extends ApplicationEvent {
    private final String txId; private final boolean success;
    PaymentCompletedEvent(Object src, String tx, boolean s) { super(src); txId=tx; success=s; }
    public String getTxId()   { return txId; }
    public boolean isSuccess(){ return success; }
}

@Component
class PaymentGateway {
    // Listens to OrderPlacedEvent2, returns PaymentInitiatedEvent (republished automatically)
    @Order(1)
    @EventListener
    public PaymentInitiatedEvent onOrderPlaced(OrderPlacedEvent2 event) {
        System.out.println("[Payment] Order received: " + event.getOrderId());
        String txId = "TX-" + event.getOrderId();
        return new PaymentInitiatedEvent(this, event.getOrderId(), txId);
    }
}

@Component
class PaymentProcessor {
    // Listens to PaymentInitiatedEvent (the returned/republished event above)
    @EventListener
    public PaymentCompletedEvent onPaymentInitiated(PaymentInitiatedEvent event) {
        System.out.println("[Processor] Processing payment " + event.getTxId());
        return new PaymentCompletedEvent(this, event.getTxId(), true);
    }
}

@Component
class OrderFinaliser {
    // Listens to BOTH OrderPlacedEvent2 and PaymentCompletedEvent
    @Order(2)
    @EventListener({OrderPlacedEvent2.class, PaymentCompletedEvent.class})
    public void onAny(ApplicationEvent event) {
        if (event instanceof OrderPlacedEvent2 e)
            System.out.println("[Finalise] Order confirmed: " + e.getOrderId());
        else if (event instanceof PaymentCompletedEvent e)
            System.out.println("[Finalise] Payment done, success=" + e.isSuccess());
    }
}

@Service
class OrderService2 {
    private final ApplicationEventPublisher pub;
    OrderService2(ApplicationEventPublisher pub) { this.pub = pub; }
    public void place(String id, double amount) {
        pub.publishEvent(new OrderPlacedEvent2(this, id, amount));
    }
}

@Configuration @ComponentScan class Config2 { }

public class EventListenerIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(Config2.class);
        ctx.getBean(OrderService2.class).place("ORD-100", 200.0);
        ctx.close();
    }
}
```

How to run: `java EventListenerIntermediate.java`

`PaymentGateway.onOrderPlaced` returns a `PaymentInitiatedEvent` — Spring republishes it immediately after `onOrderPlaced` returns. `PaymentProcessor.onPaymentInitiated` then handles it and returns `PaymentCompletedEvent`, triggering another round. This creates a declarative event chain without any bean knowing about the next step. `@EventListener({A.class, B.class})` listens to multiple types; use `instanceof` inside to distinguish them.

### Level 3 — Advanced

Async listeners with `@Async`, `@TransactionalEventListener` for post-commit work, and ordering with `@Order`.

```java
// EventListenerAdvanced.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.event.*;

class UserSignedUpEvent extends ApplicationEvent {
    private final String userId; private final String email;
    UserSignedUpEvent(Object src, String uid, String e) { super(src); userId=uid; email=e; }
    public String getUserId() { return userId; }
    public String getEmail()  { return email; }
}

@Component
class SyncAuditListener {
    // Synchronous — runs in the publisher's transaction; any exception rolls back
    @EventListener
    public void audit(UserSignedUpEvent e) {
        System.out.println("[SyncAudit] " + Thread.currentThread().getName()
            + ": User " + e.getUserId() + " signed up");
    }
}

@Component
class AsyncEmailSender {
    // Async — returns immediately; email sent on a separate thread pool
    @Async
    @EventListener
    public void sendWelcomeEmail(UserSignedUpEvent e) {
        System.out.println("[AsyncEmail] " + Thread.currentThread().getName()
            + ": Sending email to " + e.getEmail());
    }
}

@Component
class TransactionalReporter {
    // Fires ONLY after the publishing transaction commits; skip if rolled back
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void report(UserSignedUpEvent e) {
        System.out.println("[TxReport] " + Thread.currentThread().getName()
            + ": Post-commit report for " + e.getUserId());
    }

    // Fires ONLY after a rollback — useful for cleanup
    @TransactionalEventListener(phase = TransactionPhase.AFTER_ROLLBACK)
    public void cleanup(UserSignedUpEvent e) {
        System.out.println("[TxCleanup] Rollback detected for " + e.getUserId());
    }
}

@Service
class RegistrationService {
    private final ApplicationEventPublisher pub;
    RegistrationService(ApplicationEventPublisher pub) { this.pub = pub; }

    // @Transactional simulates a DB transaction;
    // @TransactionalEventListener fires AFTER commit
    @Transactional
    public void register(String uid, String email) {
        System.out.println("[Registration] DB insert for " + uid);
        pub.publishEvent(new UserSignedUpEvent(this, uid, email));
        System.out.println("[Registration] publishEvent returned (tx still open)");
    }
}

@Configuration
@ComponentScan
@EnableAsync
@EnableTransactionManagement
class AdvancedConfig {
    @org.springframework.context.annotation.Bean
    org.springframework.transaction.PlatformTransactionManager transactionManager() {
        return new org.springframework.transaction.support.ResourcelessTransactionManager();
    }

    @org.springframework.context.annotation.Bean
    java.util.concurrent.Executor taskExecutor() {
        return java.util.concurrent.Executors.newFixedThreadPool(2);
    }
}

public class EventListenerAdvanced {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AdvancedConfig.class);
        ctx.getBean(RegistrationService.class).register("u1", "alice@ex.com");
        Thread.sleep(200);  // allow async thread to finish
        ctx.close();
    }
}
```

How to run: `java EventListenerAdvanced.java`

`@EnableAsync` activates `@Async` processing; `@EnableTransactionManagement` enables `@Transactional` and `@TransactionalEventListener`. `SyncAuditListener` runs synchronously inside the transaction — if it throws, the transaction rolls back and `@TransactionalEventListener(AFTER_COMMIT)` never fires. `AsyncEmailSender` runs on the `taskExecutor` thread immediately, independently of the transaction outcome. `TransactionalReporter.report` runs only after `register`'s transaction commits — this is the pattern for sending emails or posting webhooks only when the DB write is permanent.

## 6. Walkthrough

Tracing `register("u1", "alice@ex.com")` from Level 3 end-to-end:

**Step 1 — `register` called, transaction starts** (`@Transactional`):
- `ResourcelessTransactionManager` opens a transaction.
- `System.out.println("[Registration] DB insert for u1")` — simulates INSERT.

**Step 2 — `pub.publishEvent(event)` called (transaction still active):**
- Spring dispatches to applicable listeners:

| # | Listener | Mode | Fires now? |
|---|---|---|---|
| 1 | `SyncAuditListener.audit` | synchronous | **yes** — same thread, inside tx |
| 2 | `AsyncEmailSender.sendWelcomeEmail` | async | **yes** — submitted to `taskExecutor` immediately |
| 3 | `TransactionalReporter.report` | `AFTER_COMMIT` | **no** — deferred until commit |
| 4 | `TransactionalReporter.cleanup` | `AFTER_ROLLBACK` | **no** — only on rollback |

- `SyncAuditListener.audit` prints: `[SyncAudit] main: User u1 signed up`
- `AsyncEmailSender.sendWelcomeEmail` is submitted to thread pool; task is queued.
- `TransactionalReporter` events are stored in the `TransactionSynchronization`.

**Step 3 — `publishEvent` returns; `"[Registration] publishEvent returned"` printed.**

**Step 4 — `register` method returns; transaction commits:**
- `TransactionSynchronization.afterCommit()` triggers `TransactionalReporter.report`.
- Prints: `[TxReport] main: Post-commit report for u1`

**Step 5 — Async thread runs (concurrently):**
- `AsyncEmailSender.sendWelcomeEmail` executes on pool thread.
- Prints: `[AsyncEmail] pool-1-thread-1: Sending email to alice@ex.com`

**Final output order (approximate — async thread may interleave):**
```
[Registration] DB insert for u1
[SyncAudit]   main: User u1 signed up
[Registration] publishEvent returned (tx still open)
[TxReport]    main: Post-commit report for u1
[AsyncEmail]  pool-1-thread-1: Sending email to alice@ex.com
```

## 7. Gotchas & takeaways

> **`@TransactionalEventListener` with `AFTER_COMMIT` does NOT fire when there is no active transaction.** If `publishEvent` is called outside a `@Transactional` method, the listener silently skips (no commit to observe). Set `fallbackExecution = true` on the annotation to fire even without a transaction: `@TransactionalEventListener(fallbackExecution = true)`.

> **`@Async` exceptions are silently swallowed** — they don't propagate to the publisher. Configure an `AsyncUncaughtExceptionHandler` (`AsyncConfigurer.getAsyncUncaughtExceptionHandler()`) to log or alert on async listener failures.

- `condition = "#event.amount > 0"` — the `#event` variable refers to the method parameter regardless of its name. You can also use `#args[0]` to reference the first argument.
- Returning `null` or `void` from an `@EventListener` publishes nothing. Returning a non-null object (or a `List`) publishes it as a new event immediately. Returning a `CompletableFuture` is NOT auto-published.
- `@Order` controls the sequence of synchronous listeners; it has no effect on async listeners (which all run concurrently on the thread pool).
- `@EventListener` on a `@Transactional` bean method participates in the caller's transaction. Use `@TransactionalEventListener` when you specifically want to decouple from the publisher's transaction.
- Use `ApplicationEventMulticaster` bean customisation to set a `TaskExecutor` globally, making ALL listeners async without `@Async` per-method — but be careful, this changes the semantics of every listener in the context.
