---
card: spring-data
gi: 31
slug: publishing-events-from-aggregate-roots-domainevents
title: "Publishing events from aggregate roots (@DomainEvents)"
---

## 1. What it is

`@DomainEvents` is a method-level annotation on an entity: when a Spring Data repository calls `save(...)` on that entity, the framework automatically calls the `@DomainEvents`-annotated method, collects whatever events it returns, and publishes each one through the application's `ApplicationEventPublisher` — the same event mechanism `ApplicationListener`/`@EventListener` consume — right after the save completes successfully. A paired `@AfterDomainEventPublication` method (optional) lets the entity clear its pending-events list once publication has happened, so the same events aren't republished on a later save.

```java
@Entity
public class Order {
    @Transient
    private final List<Object> pendingEvents = new ArrayList<>();

    @DomainEvents
    Collection<Object> domainEvents() { return pendingEvents; }

    @AfterDomainEventPublication
    void clearEvents() { pendingEvents.clear(); }

    public void ship() {
        this.status = "shipped";
        pendingEvents.add(new OrderShippedEvent(this.id));
    }
}
```

## 2. Why & when

This pattern comes from Domain-Driven Design: an "aggregate root" (the entity that owns a consistency boundary — here, `Order`) is the right place for business logic to record "something significant happened" (an order shipped, a customer's tier changed), but that logic shouldn't need to know *how* those events eventually get delivered to whatever else in the application cares about them. `@DomainEvents` bridges the two: business logic on the entity just accumulates plain event objects; Spring Data's save machinery handles publishing them through the standard Spring event system, decoupling "recording that something happened" from "reacting to it."

Reach for `@DomainEvents` specifically when:

- You're following a domain-driven design style where entities (aggregate roots) are responsible for recording significant state changes as events, and want those events published automatically and reliably whenever the entity is actually saved — not forgotten because a caller forgot to manually publish an event after calling `save`.
- You want event publication tied directly to persistence success — an event fires only once the entity's new state is actually committed to the repository, not before, avoiding the common bug of publishing an event for a change that then fails to save.
- You're decoupling side effects (sending a notification, updating a read model, triggering a downstream process) from the core business logic that causes them — the entity records *what* happened; separate `@EventListener` methods elsewhere decide *what to do* about it.

## 3. Core concept

```
 @Entity
 public class Order {
     @DomainEvents
     Collection<Object> domainEvents() { return pendingEvents; }
     -- returns whatever events have accumulated so far

     @AfterDomainEventPublication
     void clearEvents() { pendingEvents.clear(); }
     -- called automatically AFTER publication, to reset for next time
 }

 repo.save(order)
        |
        v
 Spring Data JPA's save() implementation:
   1. persists the entity (the actual INSERT/UPDATE)
   2. AFTER a successful save, calls the @DomainEvents method
   3. for each returned event object, publishes it via ApplicationEventPublisher
   4. calls @AfterDomainEventPublication to clear the entity's event list
        |
        v
 any @EventListener(OrderShippedEvent.class) method elsewhere in the
 application receives the event, completely decoupled from Order itself
```

The whole cycle — accumulate, save, publish, clear — happens automatically as part of calling `save(...)`; no manual `publisher.publishEvent(...)` call is needed anywhere in application code.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling save on an entity with pending domain events triggers automatic event publication after the save succeeds">
  <rect x="10" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">order.ship()</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">records a pending event</text>

  <rect x="230" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">repo.save(order)</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">persists, then publishes events</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@EventListener</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reacts, decoupled from Order</text>

  <line x1="190" y1="47" x2="225" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="47" x2="445" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Business logic records an event on the entity; `save` is what actually delivers it, only after persistence genuinely succeeds.

## 5. Runnable example

The scenario: an `Order` aggregate recording a shipment event, evolving from basic event capture-and-publish, to an `@EventListener` reacting to it, to confirming events are only published on successful saves and correctly cleared afterward so they aren't re-published.

### Level 1 — Basic

Record a domain event on `ship()`, save the entity, and confirm the event was published via a simple listener.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Transient;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.event.EventListener;
import org.springframework.data.domain.AfterDomainEventPublication;
import org.springframework.data.domain.DomainEvents;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@SpringBootApplication
public class DomainEventsLevel1 {

    public record OrderShippedEvent(Long orderId) {}

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status = "pending";

        @Transient
        private final List<Object> pendingEvents = new ArrayList<>();

        public Long getId() { return id; }
        public String getStatus() { return status; }

        public void ship() {
            this.status = "shipped";
            pendingEvents.add(new OrderShippedEvent(this.id));
        }

        @DomainEvents
        Collection<Object> domainEvents() { return pendingEvents; }

        @AfterDomainEventPublication
        void clearEvents() { pendingEvents.clear(); }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    @Component
    public static class OrderShippedListener {
        final List<OrderShippedEvent> received = new CopyOnWriteArrayList<>();

        @EventListener
        public void onOrderShipped(OrderShippedEvent event) {
            received.add(event);
            System.out.println("[listener] received OrderShippedEvent for order " + event.orderId());
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DomainEventsLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:domevents1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        OrderShippedListener listener = ctx.getBean(OrderShippedListener.class);

        Order order = repo.save(new Order()); // initial save -- no events yet
        order.ship();                          // records a pending event
        repo.save(order);                      // save() triggers automatic publication

        System.out.println("listener received " + listener.received.size() + " event(s)");

        if (listener.received.size() != 1) throw new AssertionError("Expected exactly 1 OrderShippedEvent received");
        if (!listener.received.get(0).orderId().equals(order.getId()))
            throw new AssertionError("Expected the event to reference the correct order id");
        System.out.println("@DomainEvents automatically published the event on save() -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java DomainEventsLevel1.java` on JDK 17+.

`order.ship()` is pure business logic — it changes `status` and records an `OrderShippedEvent` in `pendingEvents`, with no knowledge of Spring's event system at all. `repo.save(order)` is what actually triggers publication: Spring Data JPA's save implementation calls the `@DomainEvents`-annotated `domainEvents()` method after persisting, publishes each returned event through `ApplicationEventPublisher`, and `OrderShippedListener`'s `@EventListener` method receives it — entirely decoupled from `Order` itself.

### Level 2 — Intermediate

Confirm `@AfterDomainEventPublication` correctly clears the event list, so a subsequent unrelated save doesn't re-publish the same event.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Transient;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.event.EventListener;
import org.springframework.data.domain.AfterDomainEventPublication;
import org.springframework.data.domain.DomainEvents;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@SpringBootApplication
public class DomainEventsLevel2 {

    public record OrderShippedEvent(Long orderId) {}

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status = "pending";
        private String notes = "";

        @Transient
        private final List<Object> pendingEvents = new ArrayList<>();

        public Long getId() { return id; }
        public void ship() {
            this.status = "shipped";
            pendingEvents.add(new OrderShippedEvent(this.id));
        }
        public void addNote(String note) { this.notes += note; } // unrelated change, no new event

        @DomainEvents
        Collection<Object> domainEvents() { return pendingEvents; }

        @AfterDomainEventPublication
        void clearEvents() { pendingEvents.clear(); }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    @Component
    public static class OrderShippedListener {
        final List<OrderShippedEvent> received = new CopyOnWriteArrayList<>();
        @EventListener
        public void onOrderShipped(OrderShippedEvent event) { received.add(event); }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DomainEventsLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:domevents2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        OrderShippedListener listener = ctx.getBean(OrderShippedListener.class);

        Order order = repo.save(new Order());
        order.ship();
        repo.save(order); // publishes 1 event, then clears pendingEvents

        order.addNote("left at front desk"); // unrelated change, no new event recorded
        repo.save(order); // this save should NOT re-publish the already-cleared event

        System.out.println("total events received across BOTH saves = " + listener.received.size());

        if (listener.received.size() != 1)
            throw new AssertionError("Expected exactly 1 event total -- @AfterDomainEventPublication should have cleared the list");
        System.out.println("@AfterDomainEventPublication correctly prevented re-publishing the same event -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java DomainEventsLevel2.java`.

After the first `repo.save(order)` publishes the `OrderShippedEvent`, `@AfterDomainEventPublication`'s `clearEvents()` runs automatically, emptying `pendingEvents`. The second `repo.save(order)` (triggered by an unrelated `addNote` call that adds no new event) finds `pendingEvents` empty, so `domainEvents()` returns nothing to publish — the listener's total received-event count stays at exactly `1`, confirming events aren't accidentally re-published on every subsequent save.

### Level 3 — Advanced

Confirm events are published only on a *successful* save by wrapping the save in a transaction that fails afterward, and observing the event was never actually delivered — demonstrating events are tied to genuine persistence, not merely to calling `save()`.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Transient;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.event.EventListener;
import org.springframework.context.event.TransactionalEventListener;
import org.springframework.data.domain.AfterDomainEventPublication;
import org.springframework.data.domain.DomainEvents;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@SpringBootApplication
public class DomainEventsLevel3 {

    public record OrderShippedEvent(Long orderId) {}

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status = "pending";

        @Transient
        private final List<Object> pendingEvents = new ArrayList<>();

        public Long getId() { return id; }
        public void ship() {
            this.status = "shipped";
            pendingEvents.add(new OrderShippedEvent(this.id));
        }

        @DomainEvents
        Collection<Object> domainEvents() { return pendingEvents; }

        @AfterDomainEventPublication
        void clearEvents() { pendingEvents.clear(); }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    @Component
    public static class OrderShippedListener {
        // @TransactionalEventListener with AFTER_COMMIT phase (the default) means
        // this only fires if the enclosing transaction actually commits successfully.
        final List<OrderShippedEvent> received = new CopyOnWriteArrayList<>();

        @TransactionalEventListener
        public void onOrderShippedAfterCommit(OrderShippedEvent event) {
            received.add(event);
            System.out.println("[listener] transaction committed, event delivered for order " + event.orderId());
        }
    }

    @Component
    public static class OrderShippingService {
        private final OrderRepository repo;
        public OrderShippingService(OrderRepository repo) { this.repo = repo; }

        @Transactional
        public Long shipSuccessfully() {
            Order order = repo.save(new Order());
            order.ship();
            repo.save(order); // event is RECORDED for publication, deferred to after commit
            return order.getId();
        }

        @Transactional
        public void shipThenFail() {
            Order order = repo.save(new Order());
            order.ship();
            repo.save(order); // event is recorded here too...
            throw new RuntimeException("simulated failure AFTER save, causing a rollback");
            // ...but the transaction rolls back, so the event must NEVER actually be delivered
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ConfigurableApplicationContext ctx = SpringApplication.run(DomainEventsLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:domevents3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderShippingService service = ctx.getBean(OrderShippingService.class);
        OrderShippedListener listener = ctx.getBean(OrderShippedListener.class);

        Long successfulOrderId = service.shipSuccessfully();
        Thread.sleep(200); // allow the AFTER_COMMIT listener to run

        System.out.println("after successful ship: events received = " + listener.received.size());

        try {
            service.shipThenFail();
        } catch (RuntimeException expected) {
            System.out.println("shipThenFail() threw as expected, transaction rolled back");
        }
        Thread.sleep(200);

        System.out.println("after failed ship: events received = " + listener.received.size());

        if (listener.received.size() != 1)
            throw new AssertionError("Expected exactly 1 event total -- the failed transaction's event must never be delivered");
        if (!listener.received.get(0).orderId().equals(successfulOrderId))
            throw new AssertionError("Expected the ONE delivered event to be from the successful order");

        System.out.println("Events tied to transaction commit -- the rolled-back save's event was never delivered -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java DomainEventsLevel3.java` on JDK 17+.

`@TransactionalEventListener` (instead of plain `@EventListener`) defers actual event delivery until the enclosing transaction commits successfully — `shipSuccessfully()`'s transaction commits, so its event is delivered; `shipThenFail()`'s transaction rolls back (due to the thrown exception after the save), so even though `@DomainEvents` recorded the event during the save, it's never actually delivered to the listener, since the transaction it was part of never committed. This confirms domain events, combined with `@TransactionalEventListener`, are tied to genuine, durable persistence — not merely to the `save()` method call having executed.

## 6. Walkthrough

Trace `service.shipThenFail()`'s failed attempt.

1. **`@Transactional` begins**: `shipThenFail()` starts a database transaction.
2. **`repo.save(new Order())`** inserts a new `Order` row within this transaction.
3. **`order.ship()`** records an `OrderShippedEvent` in the entity's `pendingEvents` list — pure in-memory state at this point, nothing published yet.
4. **`repo.save(order)`**: Spring Data JPA's save implementation persists the updated `status`, then calls `@DomainEvents`'s `domainEvents()`, collecting the pending event. Internally, Spring Data doesn't publish it immediately as a plain event — with `@TransactionalEventListener` in play on the receiving side, the actual delivery is registered to occur only after the current transaction commits. `@AfterDomainEventPublication` still runs, clearing `pendingEvents`.
5. **`throw new RuntimeException(...)`**: this exception propagates out of the `@Transactional` method — Spring's transaction interceptor sees an unchecked exception and marks the transaction for rollback rather than commit.
6. **Rollback occurs**: the `INSERT` and subsequent `UPDATE` from steps 2–4 are both rolled back at the database level — as far as the database is concerned, this order was never shipped, and in fact never existed at all after the rollback.
7. **Event delivery never happens**: because `@TransactionalEventListener`'s default phase is `AFTER_COMMIT`, and this transaction never committed (it rolled back), the registered event delivery is simply discarded — `OrderShippedListener.onOrderShippedAfterCommit` is never invoked for this particular event.
8. **Verification**: `listener.received` still contains only the one event from the earlier, successful `shipSuccessfully()` call — confirming the failed transaction's domain event was correctly never delivered, even though `@DomainEvents` had recorded it during the (ultimately rolled-back) save.

```
 shipThenFail() [@Transactional]
        |
        +-- save(new Order())        -- INSERT (within transaction)
        +-- order.ship()              -- records pending event (in-memory only)
        +-- save(order)                -- UPDATE + @DomainEvents collects event,
        |                                  registers it for AFTER_COMMIT delivery
        +-- throw RuntimeException     -- transaction marked for ROLLBACK
        |
        v
 ROLLBACK: INSERT + UPDATE undone; registered event delivery DISCARDED, never fires
```

## 7. Gotchas & takeaways

> **Gotcha:** plain `@EventListener` (as used in Levels 1 and 2, without `@Transactional` wrapping the save) fires *immediately* when `repo.save(...)` completes, regardless of whether an enclosing transaction (if any) later commits or rolls back — this can mean a listener reacts to an event whose underlying database change is later undone. `@TransactionalEventListener` (Level 3) is the safer choice whenever domain events should only be acted upon after the triggering change is durably committed, which is the common and usually correct expectation for domain events specifically.

- `@DomainEvents` lets an entity (an aggregate root, in DDD terms) accumulate plain event objects as part of its own business logic, with `save(...)` automatically collecting and publishing them — no manual `ApplicationEventPublisher` call needed in application code.
- `@AfterDomainEventPublication` clears the entity's pending-events list once publication has occurred, preventing the same events from being re-published on a later, unrelated save.
- Combine `@DomainEvents` with `@TransactionalEventListener` (rather than plain `@EventListener`) when event delivery should be tied to the enclosing transaction's actual commit, not merely to the `save()` call having executed — critical for correctness whenever a save might later be rolled back.
- This pattern decouples "recording that something significant happened" (business logic on the entity) from "reacting to it" (separate `@EventListener`/`@TransactionalEventListener` methods elsewhere) — a core Domain-Driven Design technique that Spring Data's repository infrastructure supports directly.
