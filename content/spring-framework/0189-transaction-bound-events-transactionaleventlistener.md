---
card: spring-framework
gi: 189
slug: transaction-bound-events-transactionaleventlistener
title: "@TransactionalEventListener"
---

## 1. What it is

`@TransactionalEventListener` is a specialised `@EventListener` that binds listener execution to a specific transaction phase — `AFTER_COMMIT` (default), `AFTER_ROLLBACK`, `AFTER_COMPLETION`, or `BEFORE_COMMIT`. The listener only runs if the ambient transaction reaches the declared phase; events are silently discarded otherwise.

```java
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onOrderPlaced(OrderPlacedEvent event) {
    // Runs only when the transaction that published the event commits
    notificationService.sendConfirmation(event.getOrderId());
}
```

Use `@TransactionalEventListener` when your listener must not act on uncommitted data (e.g., sending an email after a DB record is persisted). Without it, a regular `@EventListener` would fire *during* the transaction, potentially reading data that hasn't been flushed yet, or executing side-effects that survive even if the transaction rolls back.

## 2. Why & when

- **Post-commit side effects** — send email/SMS after record is definitely saved; publish to message broker after DB write commits.
- **Audit logging** — write audit trail only for committed operations.
- **Cache invalidation** — clear cache only when data is actually updated.
- **Compensation on rollback** — undo external calls if the transaction fails.
- **Don't use** when you need the listener to participate in the same transaction (use regular `@EventListener` + `@Transactional` then).

## 3. Core concept

Spring uses `TransactionSynchronizationManager` to bind callbacks to the current transaction's lifecycle. `@TransactionalEventListener` registers a `TransactionSynchronization` callback at event-publish time, deferring listener invocation until the specified phase.

**Phases:**

| Phase | When listener runs |
|---|---|
| `AFTER_COMMIT` (default) | After the outer transaction successfully commits |
| `AFTER_ROLLBACK` | After the outer transaction rolls back |
| `AFTER_COMPLETION` | After the transaction ends (commit OR rollback) |
| `BEFORE_COMMIT` | Just before the outer transaction commits |

**Fallback behaviour:** If there is NO active transaction when the event is published, the listener is silently skipped by default. Set `fallbackExecution = true` on the annotation to run the listener even without a transaction.

**New transaction in listener:** A `@TransactionalEventListener` method runs OUTSIDE the originating transaction (it's already committed). To perform its own DB work, annotate it with `@Transactional(propagation = REQUIRES_NEW)`.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="tela" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="telb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e74c3c"/></marker>
  </defs>

  <!-- Transaction timeline -->
  <rect x="10" y="15" width="680" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="20" y="38" fill="#6db33f" font-size="9" font-family="sans-serif" font-weight="bold">Transaction</text>
  <text x="100" y="38" fill="#8b949e" font-size="8" font-family="sans-serif">BEGIN → DB writes → publishEvent() → ... → COMMIT  or  ROLLBACK</text>

  <!-- Timeline -->
  <line x1="10" y1="75" x2="690" y2="75" stroke="#8b949e" stroke-width="1.5"/>

  <!-- BEGIN -->
  <circle cx="30" cy="75" r="5" fill="#6db33f"/>
  <text x="30" y="92" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">BEGIN</text>

  <!-- DB write -->
  <circle cx="180" cy="75" r="5" fill="#79c0ff"/>
  <text x="180" y="92" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">DB write</text>

  <!-- publishEvent -->
  <circle cx="330" cy="75" r="5" fill="#e6edf3"/>
  <text x="330" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">publishEvent</text>
  <line x1="330" y1="60" x2="330" y2="55" stroke="#e6edf3" stroke-width="1"/>
  <rect x="240" y="35" width="180" height="20" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="330" y="49" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">registers TransactionSynchronization</text>

  <!-- COMMIT / ROLLBACK branches -->
  <circle cx="510" cy="55" r="5" fill="#6db33f"/>
  <circle cx="510" cy="95" r="5" fill="#e74c3c"/>
  <text x="515" y="53" fill="#6db33f" font-size="8" font-family="sans-serif">COMMIT</text>
  <text x="515" y="103" fill="#e74c3c" font-size="8" font-family="sans-serif">ROLLBACK</text>

  <!-- AFTER_COMMIT listener -->
  <rect x="600" y="35" width="90" height="28" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="645" y="49" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">AFTER_COMMIT</text>
  <text x="645" y="59" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">listener fires ✓</text>
  <line x1="530" y1="55" x2="598" y2="49" stroke="#6db33f" stroke-width="1.5" marker-end="url(#tela)"/>

  <!-- AFTER_ROLLBACK listener -->
  <rect x="600" y="80" width="90" height="28" rx="4" fill="#e74c3c" opacity="0.15" stroke="#e74c3c" stroke-width="1.5"/>
  <text x="645" y="94" fill="#e74c3c" font-size="7.5" text-anchor="middle" font-family="sans-serif">AFTER_ROLLBACK</text>
  <text x="645" y="104" fill="#e74c3c" font-size="7.5" text-anchor="middle" font-family="sans-serif">listener fires ✓</text>
  <line x1="530" y1="95" x2="598" y2="94" stroke="#e74c3c" stroke-width="1.5" marker-end="url(#telb)"/>

  <!-- No transaction -->
  <rect x="10" y="140" width="680" height="55" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="20" y="158" fill="#8b949e" font-size="9" font-family="sans-serif">No active transaction</text>
  <text x="20" y="172" fill="#e74c3c" font-size="8" font-family="sans-serif">Default: listener silently skipped</text>
  <text x="20" y="185" fill="#6db33f" font-size="8" font-family="sans-serif">fallbackExecution=true: listener runs anyway</text>
</svg>

`publishEvent()` registers a `TransactionSynchronization`; the listener fires only at the declared phase after the transaction boundary.

## 5. Runnable example

Scenario: **order placement system** — DB write must commit before notifications fire; rollback triggers compensation.

### Level 1 — Basic

`AFTER_COMMIT` listener fires only when order is saved successfully.

```java
// TransactionalEventsBasic.java
import org.springframework.context.ApplicationEvent;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.event.*;
import org.springframework.transaction.support.*;
import java.util.*;

record OrderPlacedEvent(String orderId) extends ApplicationEvent {
    OrderPlacedEvent(Object src, String orderId) { super(src); }
}

@Component
class NotificationListener {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void sendConfirmation(OrderPlacedEvent e) {
        System.out.println("[Notification] Sending confirmation for " + e.orderId()
            + "  (transaction committed)");
    }
}

@Service
class OrderService {
    private final ApplicationEventPublisher pub;
    private final PlatformTransactionManager txm;
    OrderService(ApplicationEventPublisher pub, PlatformTransactionManager txm) {
        this.pub = pub; this.txm = txm;
    }
    public void placeOrder(String orderId) {
        var def = new DefaultTransactionDefinition();
        var status = txm.getTransaction(def);
        try {
            System.out.println("[Order] Saving order " + orderId);
            pub.publishEvent(new OrderPlacedEvent(this, orderId));
            System.out.println("[Order] About to commit...");
            txm.commit(status);
            System.out.println("[Order] Committed.");
        } catch (Exception ex) {
            txm.rollback(status);
            throw ex;
        }
    }
    public void placeOrderNoTx(String orderId) {
        System.out.println("[Order] Publishing WITHOUT transaction:");
        pub.publishEvent(new OrderPlacedEvent(this, orderId));
        System.out.println("[Order] Published (listener will be skipped).");
    }
}

@Configuration
@ComponentScan
@EnableTransactionManagement
class TxEvtConfig {
    @org.springframework.context.annotation.Bean
    PlatformTransactionManager txm() {
        return new org.springframework.transaction.support.ResourcelessTransactionManager();
    }
}

public class TransactionalEventsBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxEvtConfig.class);
        var svc = ctx.getBean(OrderService.class);
        svc.placeOrder("ORD-001");        // → notification fires after commit
        System.out.println("---");
        svc.placeOrderNoTx("ORD-002");    // → listener silently skipped
        ctx.close();
    }
}
```

How to run: `java TransactionalEventsBasic.java`

`ResourcelessTransactionManager` is a minimal in-memory transaction manager included in Spring. After `placeOrder`, notification fires. After `placeOrderNoTx`, notification is silently skipped (no `fallbackExecution=true`).

### Level 2 — Intermediate

`AFTER_ROLLBACK` compensation listener; `fallbackExecution = true`; `@Transactional(REQUIRES_NEW)` in listener.

```java
// TransactionalEventsIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.event.*;
import org.springframework.transaction.support.*;

record OrderSavedEvent(String orderId, double amount) extends ApplicationEvent {
    OrderSavedEvent(Object src, String orderId, double amount) { super(src); }
}

@Component
class OrderEventHandlers {
    // Fires only after commit — sends email
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onCommit(OrderSavedEvent e) {
        System.out.println("[Email] Sent confirmation: order=" + e.orderId()
            + " amount=" + e.amount());
    }

    // Fires only after rollback — log failure
    @TransactionalEventListener(phase = TransactionPhase.AFTER_ROLLBACK)
    public void onRollback(OrderSavedEvent e) {
        System.out.println("[Compensation] Rollback detected for " + e.orderId()
            + ". No email sent. Logging failure.");
    }

    // fallbackExecution=true → runs even without a transaction
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT, fallbackExecution = true)
    public void audit(OrderSavedEvent e) {
        System.out.println("[Audit] Recording event for " + e.orderId());
    }
}

@Service
class OrderStoreSvc {
    private final ApplicationEventPublisher pub;
    private final PlatformTransactionManager txm;
    OrderStoreSvc(ApplicationEventPublisher pub, PlatformTransactionManager txm) {
        this.pub = pub; this.txm = txm;
    }
    public void saveSuccess(String id, double amt) {
        var s = txm.getTransaction(new DefaultTransactionDefinition());
        pub.publishEvent(new OrderSavedEvent(this, id, amt));
        txm.commit(s);
    }
    public void saveFail(String id, double amt) {
        var s = txm.getTransaction(new DefaultTransactionDefinition());
        pub.publishEvent(new OrderSavedEvent(this, id, amt));
        txm.rollback(s);  // simulate failure
    }
    public void saveNoTx(String id, double amt) {
        pub.publishEvent(new OrderSavedEvent(this, id, amt));
    }
}

@Configuration @ComponentScan @EnableTransactionManagement
class TxIntermConfig {
    @Bean PlatformTransactionManager txm() {
        return new ResourcelessTransactionManager();
    }
}

public class TransactionalEventsIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxIntermConfig.class);
        var svc = ctx.getBean(OrderStoreSvc.class);
        System.out.println("=== Success path ===");
        svc.saveSuccess("ORD-A", 99.0);
        System.out.println("=== Rollback path ===");
        svc.saveFail("ORD-B", 50.0);
        System.out.println("=== No transaction ===");
        svc.saveNoTx("ORD-C", 10.0);
        ctx.close();
    }
}
```

How to run: `java TransactionalEventsIntermediate.java`

Success path: `onCommit` + `audit` fire. Rollback path: `onRollback` + `audit` fire (audit has `fallbackExecution=true`, but that only affects the no-tx case — for rollback, `AFTER_COMMIT` still doesn't fire, and `AFTER_ROLLBACK` does). No-tx path: only `audit` fires (fallbackExecution=true with AFTER_COMMIT).

### Level 3 — Advanced

Spring Boot `@Transactional` service + `@TransactionalEventListener` + `@Transactional(REQUIRES_NEW)` for listener's own DB work.

```java
// TransactionalEventsAdvanced.java
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.*;
import org.springframework.stereotype.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.event.*;

record UserRegisteredEvent(String userId, String email) extends ApplicationEvent {
    UserRegisteredEvent(Object src, String userId, String email) { super(src); }
}

@Service
class UserRegService {
    private final ApplicationEventPublisher pub;
    UserRegService(ApplicationEventPublisher pub) { this.pub = pub; }

    @Transactional
    public void register(String userId, String email) {
        System.out.println("[UserReg] Persisting user: " + userId);
        // --- DB save would go here ---
        pub.publishEvent(new UserRegisteredEvent(this, userId, email));
        System.out.println("[UserReg] Committing...");
    }
}

@Component
class WelcomeEmailListener {
    // AFTER_COMMIT: listener starts AFTER the outer transaction commits
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendWelcome(UserRegisteredEvent e) {
        // REQUIRES_NEW starts a fresh transaction for audit logging
        System.out.println("[WelcomeEmail] Sending to " + e.email()
            + " (new transaction for audit)");
    }
}

@Component
class BeforeCommitListener {
    // BEFORE_COMMIT: still inside the outer transaction; can flush state
    @TransactionalEventListener(phase = TransactionPhase.BEFORE_COMMIT)
    public void validate(UserRegisteredEvent e) {
        System.out.println("[Validation] Pre-commit check for user " + e.userId());
    }
}

@SpringBootApplication
public class TransactionalEventsAdvanced {
    public static void main(String[] args) {
        var ctx = SpringApplication.run(TransactionalEventsAdvanced.class, args);
        ctx.getBean(UserRegService.class).register("U-100", "bob@example.com");
        SpringApplication.exit(ctx);
    }
}
```

How to run: `./mvnw spring-boot:run` or add to Spring Boot project.

Execution order: `register()` starts transaction → `publishEvent()` registers synchronization → `BEFORE_COMMIT` listener fires (inside outer tx) → outer tx commits → `AFTER_COMMIT` listener fires (outside outer tx, starts REQUIRES_NEW tx of its own).

## 6. Walkthrough

Tracing `svc.register("U-100", "bob@example.com")`:

**Step 1 — `@Transactional` opens transaction TX1.**

**Step 2 — `persistUser()` writes to DB (within TX1).**

**Step 3 — `pub.publishEvent(UserRegisteredEvent)` called:**
- Spring's multicaster sees both `@TransactionalEventListener` methods.
- Registers a `TransactionSynchronization` for each with the `TransactionSynchronizationManager`.
- Neither listener fires yet. Execution returns to `register()`.

**Step 4 — `BEFORE_COMMIT` phase:** Just before TX1 commits, Spring fires `BEFORE_COMMIT` listeners.
- `validate()` prints `[Validation] Pre-commit check for user U-100`.
- Still inside TX1 — can read/write to the same transaction.

**Step 5 — TX1 commits** (DB write is durable).

**Step 6 — `AFTER_COMMIT` phase:** Spring fires `AFTER_COMMIT` listeners.
- `sendWelcome()` is called.
- `@Transactional(REQUIRES_NEW)` opens a new transaction TX2.
- Prints `[WelcomeEmail] Sending to bob@example.com`.
- TX2 commits independently.

**If TX1 had rolled back:** Only `AFTER_ROLLBACK` listeners would fire. `AFTER_COMMIT` and `BEFORE_COMMIT` listeners would be silently discarded.

## 7. Gotchas & takeaways

> **`@TransactionalEventListener` is silently dropped if there is no active transaction.** This is the most common surprise. Add `fallbackExecution = true` if the listener must also run outside a transaction context (e.g., during tests or when called from non-transactional code).

> **`AFTER_COMMIT` listener is outside the original transaction.** Any DB work inside the listener needs its own transaction — add `@Transactional(propagation = REQUIRES_NEW)`. Without it, if the listener tries to use a JPA EntityManager, it gets a `LazyInitializationException` or `No transaction in progress` error.

- `BEFORE_COMMIT` is the only phase where the listener is still inside the transaction. Use it for last-chance validation, not for sending external calls (email, HTTP) — if the external call fails, it will prevent the transaction from committing.
- Ordering with `@Order`: `@TransactionalEventListener` methods support `@Order` for deterministic ordering within the same phase.
- Nested transactions: if the event is published inside a nested `@Transactional(REQUIRES_NEW)`, the listener binds to the inner transaction, not the outer one.
- Spring Data's `@DomainEvents` / `AbstractAggregateRoot` publishes events after save — these are already bound to `AFTER_COMMIT` by Spring Data's `@TransactionalEventListener` under the hood.
