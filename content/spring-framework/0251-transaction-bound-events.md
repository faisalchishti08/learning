---
card: spring-framework
gi: 251
slug: transaction-bound-events
title: Transaction-bound events
---

## 1. What it is

**Transaction-bound events** are Spring application events that are deferred and published only at a specific phase of the enclosing transaction — most commonly after a successful commit. Instead of publishing an event immediately inside a `@Transactional` method (where it might fire even if the transaction later rolls back), you annotate the listener with `@TransactionalEventListener` and specify when it should run.

```java
@Component
public class OrderEventHandler {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onOrderCreated(OrderCreatedEvent event) {
        // fires ONLY after the publishing transaction commits
        emailService.sendConfirmation(event.orderId());
    }
}
```

## 2. Why & when

Without transaction binding, a `@EventListener` fires immediately when the event is published — even mid-transaction. If the transaction later rolls back, the event handler already ran (sent an email, pushed to a queue) and that side effect cannot be undone.

`@TransactionalEventListener` solves this by deferring the listener to a safe transactional phase:

| Phase | When it fires |
|-------|--------------|
| `AFTER_COMMIT` | After the transaction commits successfully *(default)* |
| `AFTER_ROLLBACK` | After the transaction rolls back |
| `AFTER_COMPLETION` | After commit or rollback (always) |
| `BEFORE_COMMIT` | Just before the transaction commits |

Use `AFTER_COMMIT` for: send emails, push to message queues, invalidate caches, publish to external systems.
Use `AFTER_ROLLBACK` for: compensating actions, alerting.
Use `BEFORE_COMMIT` for: final validation before commit (rare — throwing here rolls back).

## 3. Core concept

Publishing works normally via `ApplicationEventPublisher.publishEvent(event)` inside a `@Transactional` method. Spring internally uses `TransactionSynchronizationManager.registerSynchronization()` to defer the listener invocation to the specified phase.

If `@TransactionalEventListener` is called outside a transaction:
- By default (`fallbackExecution = false`): the event is silently dropped.
- With `fallbackExecution = true`: the event fires immediately like a normal `@EventListener`.

The listener itself does NOT run inside the publishing transaction. If you annotate the listener method with `@Transactional`, it starts its own transaction (propagation `REQUIRES_NEW` is common here so the listener's transaction is independent).

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="rarr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#f85149"/>
    </marker>
  </defs>

  <!-- Timeline -->
  <line x1="30" y1="105" x2="670" y2="105" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>

  <!-- TX open -->
  <rect x="30" y="75" width="100" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="97" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">TX begins</text>
  <text x="80" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">INSERT order</text>

  <!-- publishEvent -->
  <rect x="145" y="75" width="130" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="210" y="93" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">publishEvent()</text>
  <text x="210" y="109" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">event queued via</text>
  <text x="210" y="121" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">TxSyncManager</text>

  <!-- TX commit -->
  <rect x="290" y="75" width="100" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="100" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">TX commits</text>

  <!-- AFTER_COMMIT -->
  <rect x="405" y="60" width="170" height="65" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="490" y="82" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AFTER_COMMIT fires</text>
  <text x="490" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@TransactionalEventListener</text>
  <text x="490" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">sends email / pushes to queue</text>

  <!-- AFTER_ROLLBACK (alternative) -->
  <rect x="405" y="140" width="170" height="50" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="490" y="162" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">AFTER_ROLLBACK fires</text>
  <text x="490" y="177" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">compensating action</text>

  <text x="350" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">commit path ↑</text>
  <text x="350" y="210" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">rollback path ↓</text>
</svg>

Events are queued when published; the correct phase listener fires only after the transaction outcome is known.

## 5. Runnable example

Scenario: an **`OrderService`** that creates orders and sends a confirmation email — first showing the naive bug, then using `@TransactionalEventListener(AFTER_COMMIT)`, then combining with `@Transactional(REQUIRES_NEW)` on the listener.

### Level 1 — Basic

Naive `@EventListener` — fires even if the outer transaction rolls back.

```java
// TxEventDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.context.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxEventDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxEventDemo.class);
        System.out.println("=== BUG: naive @EventListener fires mid-tx ===");
        try { ctx.getBean(OrderService.class).placeOrderFailing("ORD-FAIL"); }
        catch (Exception e) { System.out.println("Order rolled back: " + e.getMessage()); }
        ctx.close();
    }
}

record OrderCreatedEvent(String orderId) {}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final ApplicationEventPublisher publisher;
    OrderService(javax.sql.DataSource ds, ApplicationEventPublisher pub) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.publisher = pub;
    }

    @Transactional
    public void placeOrderFailing(String orderId) {
        jdbc.update("INSERT INTO orders(id,item,qty) VALUES(?,'X',1)", orderId);
        publisher.publishEvent(new OrderCreatedEvent(orderId));   // fires IMMEDIATELY
        throw new RuntimeException("Payment declined");           // tx rolls back
        // BUG: email was already "sent" before the rollback
    }
}

@Component
class EmailListener {
    @org.springframework.context.event.EventListener   // fires immediately — wrong!
    public void onOrderCreated(OrderCreatedEvent event) {
        System.out.println("[EMAIL BUG] sending confirmation for " + event.orderId()
            + " — but tx may roll back!");
    }
}
```

`orders-schema.sql`: `CREATE TABLE orders (id VARCHAR(20) PRIMARY KEY, item VARCHAR(50), qty INT);`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. TxEventDemo.java`

`[EMAIL BUG]` prints before the exception. The order rolls back — but the "email was sent" log appeared. In production, the actual email/message would already have been dispatched.

---

### Level 2 — Intermediate

**`@TransactionalEventListener(AFTER_COMMIT)`** — listener fires only after commit.

```java
// TxEventDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.context.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.event.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxEventDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxEventDemo.class);
        System.out.println("=== SUCCESS: @TransactionalEventListener fires after commit ===");
        ctx.getBean(OrderService.class).placeOrder("ORD-SUCCESS");

        System.out.println("\n=== ROLLBACK: listener is NOT called ===");
        try { ctx.getBean(OrderService.class).placeOrderFailing("ORD-FAIL"); }
        catch (Exception e) { System.out.println("Order rolled back: " + e.getMessage()); }
        ctx.close();
    }
}

record OrderCreatedEvent(String orderId) {}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final ApplicationEventPublisher publisher;
    OrderService(javax.sql.DataSource ds, ApplicationEventPublisher pub) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.publisher = pub;
    }

    @Transactional
    public void placeOrder(String orderId) {
        jdbc.update("INSERT INTO orders(id,item,qty) VALUES(?,'WIDGET',1)", orderId);
        publisher.publishEvent(new OrderCreatedEvent(orderId));
        System.out.println("[TX] order inserted, event queued");
    }

    @Transactional
    public void placeOrderFailing(String orderId) {
        jdbc.update("INSERT INTO orders(id,item,qty) VALUES(?,'WIDGET',1)", orderId);
        publisher.publishEvent(new OrderCreatedEvent(orderId));
        throw new RuntimeException("Payment declined");   // rollback — listener NOT called
    }
}

@Component
class EmailListener {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onOrderCreated(OrderCreatedEvent event) {
        System.out.println("[EMAIL] ✓ Sending confirmation for " + event.orderId()
            + " — tx committed, safe to send");
    }
}
```

How to run: same classpath

For `placeOrder`: the event is queued during the transaction, fires after commit — `[EMAIL] ✓` prints. For `placeOrderFailing`: the transaction rolls back — the listener is NOT called. No spurious email.

---

### Level 3 — Advanced

Listener with its own `@Transactional(REQUIRES_NEW)` — the listener writes to a notification log in its own independent transaction.

```java
// TxEventDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.context.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.event.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class TxEventDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxEventDemo.class);
        ctx.getBean(OrderService.class).placeOrder("ORD-ADV");

        // Verify notification log
        var jdbc = new org.springframework.jdbc.core.JdbcTemplate(
            ctx.getBean(javax.sql.DataSource.class));
        var logs = jdbc.queryForList("SELECT msg FROM notification_log", String.class);
        System.out.println("Notification log: " + logs);
        ctx.close();
    }
}

record OrderCreatedEvent(String orderId) {}

@Service
class OrderService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    private final ApplicationEventPublisher publisher;
    OrderService(javax.sql.DataSource ds, ApplicationEventPublisher pub) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); this.publisher = pub;
    }

    @Transactional
    public void placeOrder(String orderId) {
        jdbc.update("INSERT INTO orders(id,item,qty) VALUES(?,'PART',2)", orderId);
        publisher.publishEvent(new OrderCreatedEvent(orderId));
        System.out.println("[ORDER TX] order " + orderId + " committed");
    }
}

@Component
class NotificationListener {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    NotificationListener(javax.sql.DataSource ds) {
        this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds);
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    @Transactional(propagation = Propagation.REQUIRES_NEW)  // own independent tx
    public void onOrderCreated(OrderCreatedEvent event) {
        jdbc.update("INSERT INTO notification_log(msg) VALUES(?)",
            "Notification queued for " + event.orderId());
        System.out.println("[NOTIFICATION TX] log entry committed for " + event.orderId());
    }
}
```

`orders-schema.sql` (add): `CREATE TABLE notification_log (id BIGINT AUTO_INCREMENT PRIMARY KEY, msg VARCHAR(255));`

How to run: same classpath

`NotificationListener.onOrderCreated()` fires after the order TX commits. With `@Transactional(REQUIRES_NEW)` it opens its own transaction to write to `notification_log`. The listener's TX commits independently. If the notification write fails, only the notification TX rolls back — the order is already committed and safe.

## 6. Walkthrough

**Level 2 — success path:**

```
OrderService.placeOrder("ORD-SUCCESS") begins tx T1

  INSERT orders [conn, T1]
  publisher.publishEvent(OrderCreatedEvent)
    → TransactionSynchronizationManager.registerSynchronization(
         TransactionalApplicationListenerSynchronization{phase=AFTER_COMMIT}
       )
  System.out "[TX] order inserted, event queued"

T1.commit()
  → conn.commit()
  → for each synchronization after commit:
       TransactionalApplicationListenerSynchronization fires
       → EmailListener.onOrderCreated(OrderCreatedEvent)
          System.out "[EMAIL] ✓ Sending confirmation for ORD-SUCCESS"
```

**Level 2 — rollback path:**

```
OrderService.placeOrderFailing("ORD-FAIL") begins tx T1

  INSERT orders [conn, T1]
  publisher.publishEvent(OrderCreatedEvent)
    → synchronization registered
  throw RuntimeException

T1.rollback()
  → conn.rollback()
  → synchronizations are DISCARDED (not fired for AFTER_COMMIT)
  → no email
```

**Level 3 — listener with own TX:**

```
AFTER_COMMIT fires → NotificationListener.onOrderCreated()
  proxy intercepts: @Transactional(REQUIRES_NEW)
  → tm.getTransaction(REQUIRES_NEW)  → conn2 acquired (outer T1 already committed, nothing to suspend)
  → INSERT notification_log [conn2]
  → System.out "[NOTIFICATION TX]"
  → commit(conn2)  → conn2.commit()
```

## 7. Gotchas & takeaways

> **`@TransactionalEventListener` with `fallbackExecution = false` (default) silently drops events published outside a transaction.** Integration tests that call `publishEvent` directly without a `@Transactional` wrapper will never see the listener fire. Add `fallbackExecution = true` if you need the listener to fire in non-transactional contexts too.

> **The listener runs in the publishing thread, after commit.** If the listener does heavy work (external HTTP call, file write), it delays the calling thread. Annotate the listener with `@Async` to offload it to a thread pool — but then ensure the async thread has its own transaction if it writes to the DB.

> **Publishing a new event inside a `BEFORE_COMMIT` listener can cause infinite recursion** if the inner event also triggers a `BEFORE_COMMIT` listener. Use `AFTER_COMMIT` by default to avoid this.

- `@TransactionalEventListener` defaults to `AFTER_COMMIT` — the safe choice for emails, queues, caches.
- `fallbackExecution = false` (default): silently drops events not published inside a transaction.
- Combine with `@Transactional(propagation = REQUIRES_NEW)` on the listener to give it its own independent transaction for database writes.
- For async side effects: `@TransactionalEventListener` + `@Async` — fire-and-forget after commit.
