---
card: spring-data
gi: 41
slug: entity-callbacks-beforeconvertcallback-etc
title: "Entity callbacks (BeforeConvertCallback, etc.)"
---

## 1. What it is

Entity callbacks are a store-agnostic hook mechanism — `BeforeConvertCallback<T>`, `AfterConvertCallback<T>`, and similar interfaces (the exact set varies slightly by store; JPA in particular relies more on the standard `@PrePersist`/`@PostLoad` lifecycle annotations already used elsewhere in this section, while document/key-value stores like MongoDB lean on entity callbacks more heavily) — that let a Spring bean intercept an entity at a specific point in Spring Data's own save/load pipeline, registered simply by implementing the interface and being a Spring bean, with no annotation needed on the entity itself.

```java
@Component
public class OrderNumberGenerator implements BeforeConvertCallback<Order> {
    @Override
    public Order onBeforeConvert(Order order) {
        if (order.getOrderNumber() == null) {
            order.setOrderNumber("ORD-" + UUID.randomUUID());
        }
        return order;
    }
}
```

## 2. Why & when

JPA's own `@PrePersist`/`@PreUpdate`/`@PostLoad` annotations (used by `AuditingEntityListener` in the previous two cards) are entity-instance-method or `@EntityListeners`-class hooks, tied specifically to JPA's lifecycle model. Entity callbacks are Spring Data's own, store-independent equivalent — a `@Component`-based callback bean works the same way across JPA, MongoDB, Redis, and other Spring Data modules, without needing to know each store's own lifecycle-annotation conventions. They're most commonly reached for in non-JPA Spring Data modules where JPA-style annotations don't apply at all, but understanding them here, in the context of this Commons-focused section, clarifies the store-agnostic hook point they represent.

Reach for entity callbacks specifically when:

- You're working with a non-JPA Spring Data module (MongoDB, Redis, and others) where `@PrePersist`-style JPA annotations simply don't exist, and need a hook point to run logic before an entity is converted for storage or after it's loaded back.
- You want hook logic implemented as an ordinary Spring bean (with full dependency injection available) rather than tied to a JPA-specific `@EntityListeners` class, which has more restrictive instantiation rules.
- You need the *same* hook logic — generating a value, validating state, transforming data — to work consistently across more than one Spring Data module in an application that uses multiple stores.

## 3. Core concept

```
 Entity callback interfaces (implemented by a Spring @Component/@Bean):

   BeforeConvertCallback<T>
     onBeforeConvert(T entity) -> T
     -- runs BEFORE the entity is converted into the store's native
        representation (a row, a document, ...) -- the last point to
        modify the entity itself before it's translated for storage

   AfterConvertCallback<T>
     onAfterConvert(T entity) -> T
     -- runs AFTER a loaded native representation has been converted
        back into the entity -- the first point to observe/modify a
        freshly-loaded entity

 Registration: simply implement the interface and be a Spring bean --
 Spring Data's ReactiveEntityCallbacks / EntityCallbacks infrastructure
 discovers and invokes them automatically, in the order beans are found
 (or an explicit @Order if multiple callbacks need a specific sequence)

 For JPA specifically: entity callbacks CAN be used, but @PrePersist/
 @PreUpdate/@PostLoad (JPA's own standard) are more commonly reached for,
 since they're the native JPA mechanism -- entity callbacks shine most
 in stores that have NO equivalent native lifecycle annotation system.
```

Both callback types return the entity — allowing them to either mutate the entity in place and return it, or return a genuinely different (transformed) instance.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BeforeConvertCallback runs just before an entity is translated for storage, AfterConvertCallback runs just after it is loaded back">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">entity object (in-memory)</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">about to be saved</text>

  <rect x="230" y="20" width="200" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BeforeConvertCallback</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runs, then conversion to store format</text>

  <rect x="460" y="20" width="170" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">stored representation</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">row / document / etc.</text>

  <line x1="200" y1="47" x2="225" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="430" y1="47" x2="455" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Callbacks bracket the conversion step between in-memory entity and stored representation, symmetric in reverse for loading.

## 5. Runnable example

The scenario: an `Order` entity needing a generated order number, evolving from a basic `BeforeConvertCallback` populating it, to `AfterConvertCallback` observing freshly-loaded entities, to multiple ordered callbacks working together.

### Level 1 — Basic

Implement `BeforeConvertCallback<Order>` to generate an order number if one isn't already set, and confirm it runs automatically on save.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.mapping.callback.BeforeConvertCallback;
import org.springframework.stereotype.Component;

import java.util.UUID;

@SpringBootApplication
public class EntityCallbacksLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String orderNumber;
        protected Order() {}
        public String getOrderNumber() { return orderNumber; }
        public void setOrderNumber(String orderNumber) { this.orderNumber = orderNumber; }
    }

    @Component
    public static class OrderNumberGenerator implements BeforeConvertCallback<Order> {
        @Override
        public Order onBeforeConvert(Order order) {
            if (order.getOrderNumber() == null) {
                order.setOrderNumber("ORD-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
                System.out.println("[callback] generated order number: " + order.getOrderNumber());
            }
            return order;
        }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(EntityCallbacksLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:callbacks1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order());

        System.out.println("saved order number = " + saved.getOrderNumber());

        if (saved.getOrderNumber() == null || !saved.getOrderNumber().startsWith("ORD-"))
            throw new AssertionError("Expected BeforeConvertCallback to have generated an order number");
        System.out.println("BeforeConvertCallback generated the order number automatically -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java EntityCallbacksLevel1.java` on JDK 17+.

`OrderNumberGenerator implements BeforeConvertCallback<Order>` — a plain `@Component`, no annotation on `Order` itself needed, unlike the JPA-lifecycle-based `AuditingEntityListener` mechanism from the previous cards. Spring Data's callback infrastructure discovers this bean automatically and invokes `onBeforeConvert` just before `save` converts the entity for storage, letting it populate `orderNumber` only if it wasn't already set.

### Level 2 — Intermediate

Add `AfterConvertCallback<Order>` to observe and enrich a freshly-loaded entity, confirming it runs on `findById` but not on the initial save (since nothing is "loaded" during a save).

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Transient;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.mapping.callback.AfterConvertCallback;
import org.springframework.data.mapping.callback.BeforeConvertCallback;
import org.springframework.stereotype.Component;

import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
public class EntityCallbacksLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String orderNumber;

        @Transient
        private boolean loadedViaCallback = false; // marks an entity that came back through AfterConvertCallback

        protected Order() {}
        public String getOrderNumber() { return orderNumber; }
        public void setOrderNumber(String orderNumber) { this.orderNumber = orderNumber; }
        public boolean isLoadedViaCallback() { return loadedViaCallback; }
        public void setLoadedViaCallback(boolean loadedViaCallback) { this.loadedViaCallback = loadedViaCallback; }
    }

    @Component
    public static class OrderNumberGenerator implements BeforeConvertCallback<Order> {
        @Override
        public Order onBeforeConvert(Order order) {
            if (order.getOrderNumber() == null) {
                order.setOrderNumber("ORD-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
            }
            return order;
        }
    }

    static final AtomicInteger afterConvertInvocations = new AtomicInteger();

    @Component
    public static class OrderLoadObserver implements AfterConvertCallback<Order> {
        @Override
        public Order onAfterConvert(Order order) {
            afterConvertInvocations.incrementAndGet();
            order.setLoadedViaCallback(true);
            System.out.println("[callback] observed a freshly-loaded order: " + order.getOrderNumber());
            return order;
        }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(EntityCallbacksLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:callbacks2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order());
        int countAfterSave = afterConvertInvocations.get();

        Order loaded = repo.findById(saved.getId()).orElseThrow();
        int countAfterLoad = afterConvertInvocations.get();

        System.out.println("AfterConvertCallback invocations right after save = " + countAfterSave);
        System.out.println("AfterConvertCallback invocations after an explicit findById = " + countAfterLoad);
        System.out.println("was the loaded entity marked by the callback? " + loaded.isLoadedViaCallback());

        if (countAfterLoad <= countAfterSave)
            throw new AssertionError("Expected AfterConvertCallback to run at least once more due to the findById load");
        if (!loaded.isLoadedViaCallback()) throw new AssertionError("Expected the loaded entity to be marked by the callback");

        System.out.println("AfterConvertCallback observed the entity specifically on load -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java EntityCallbacksLevel2.java`.

`OrderLoadObserver` runs on `AfterConvertCallback`, incrementing a counter and marking each entity it observes. The count after `save(...)` and after `findById(...)` differ, since `findById` performs a genuine load-and-convert cycle that triggers `onAfterConvert`, in addition to whatever Hibernate does internally around the initial save's own entity handling — the specific invocation count can vary by JPA provider details, but the key confirmed behavior is that an explicit reload genuinely re-triggers the callback and marks the freshly-converted entity.

### Level 3 — Advanced

Register two `BeforeConvertCallback` beans with an explicit execution order via `@Order`, confirming callbacks run in a deterministic, controllable sequence when more than one applies to the same entity type.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.annotation.Order;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.mapping.callback.BeforeConvertCallback;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@SpringBootApplication
public class EntityCallbacksLevel3 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String orderNumber;
        private String validationStatus;
        protected Order() {}
        public String getOrderNumber() { return orderNumber; }
        public void setOrderNumber(String orderNumber) { this.orderNumber = orderNumber; }
        public String getValidationStatus() { return validationStatus; }
        public void setValidationStatus(String validationStatus) { this.validationStatus = validationStatus; }
    }

    static final List<String> executionOrder = new ArrayList<>();

    // Order 1: generate the order number FIRST.
    @Component
    @Order(1)
    public static class OrderNumberGenerator implements BeforeConvertCallback<Order> {
        @Override
        public Order onBeforeConvert(Order order) {
            executionOrder.add("OrderNumberGenerator");
            if (order.getOrderNumber() == null) {
                order.setOrderNumber("ORD-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
            }
            return order;
        }
    }

    // Order 2: validate SECOND, depending on the order number already being set.
    @Component
    @Order(2)
    public static class OrderValidator implements BeforeConvertCallback<Order> {
        @Override
        public Order onBeforeConvert(Order order) {
            executionOrder.add("OrderValidator");
            order.setValidationStatus(order.getOrderNumber() != null ? "VALID" : "INVALID - missing order number");
            return order;
        }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(EntityCallbacksLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:callbacks3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Order saved = repo.save(new Order());

        System.out.println("execution order = " + executionOrder);
        System.out.println("orderNumber = " + saved.getOrderNumber() + ", validationStatus = " + saved.getValidationStatus());

        if (!executionOrder.equals(List.of("OrderNumberGenerator", "OrderValidator")))
            throw new AssertionError("Expected callbacks to run in @Order sequence: generator, then validator");
        if (!"VALID".equals(saved.getValidationStatus()))
            throw new AssertionError("Expected validation to see the order number ALREADY set, since it ran second");

        System.out.println("Two BeforeConvertCallback beans ran in deterministic @Order sequence -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java EntityCallbacksLevel3.java`.

`@Order(1)` on `OrderNumberGenerator` and `@Order(2)` on `OrderValidator` guarantee the number-generating callback runs before the validating one — `OrderValidator`'s check for `order.getOrderNumber() != null` correctly sees `"VALID"`, since by the time it runs, `OrderNumberGenerator` has already populated the field. Without explicit ordering, the relative sequence of two callback beans applying to the same entity type would be unspecified, exactly the same ordering concern the `aop:aspect`/`order` attribute addressed for AOP advice in this guide's Appendix section.

## 6. Walkthrough

Trace Level 3's `repo.save(new Order())` call.

1. **`repo.save(new Order())`** is called with a brand-new, empty `Order` — `orderNumber` and `validationStatus` are both `null`.
2. **Callback discovery**: Spring Data's entity-callback infrastructure has already discovered both `OrderNumberGenerator` and `OrderValidator` as `BeforeConvertCallback<Order>` beans during application startup, and knows their relative order from the `@Order` annotations.
3. **First callback invocation**: `OrderNumberGenerator.onBeforeConvert(order)` runs (order 1) — it records itself in `executionOrder`, checks `order.getOrderNumber() == null` (true), and generates a new order number, setting it on the entity.
4. **Second callback invocation**: `OrderValidator.onBeforeConvert(order)` runs next (order 2) — it records itself in `executionOrder`, then checks `order.getOrderNumber() != null` — because the previous callback already ran and set it, this is now `true`, so `validationStatus` is set to `"VALID"`.
5. **Conversion and persistence**: after both callbacks complete, the entity (now with both `orderNumber` and `validationStatus` populated) is converted into its storage representation and actually persisted via the normal JPA `INSERT`.
6. **Return value**: `repo.save(...)` returns the entity with both fields set, reflecting the combined effect of both callbacks having run in the guaranteed sequence.
7. **Verification**: the program checks `executionOrder` exactly matches `["OrderNumberGenerator", "OrderValidator"]`, and that `validationStatus` is `"VALID"` (not the failure case), confirming the ordering guarantee held and that `OrderValidator`'s logic genuinely depended on, and correctly observed, `OrderNumberGenerator`'s prior effect.

```
 repo.save(new Order())   [orderNumber=null, validationStatus=null]
        |
        v
 OrderNumberGenerator.onBeforeConvert  (@Order(1))
   -- sets orderNumber = "ORD-XXXXXXXX"
        |
        v
 OrderValidator.onBeforeConvert         (@Order(2))
   -- sees orderNumber != null  -->  validationStatus = "VALID"
        |
        v
 entity converted + persisted, WITH both fields populated
```

## 7. Gotchas & takeaways

> **Gotcha:** without an explicit `@Order` on multiple callback beans of the same type applying to the same entity, their relative execution sequence is unspecified — if one callback's logic depends on another having already run (as `OrderValidator` depends on `OrderNumberGenerator` here), skipping `@Order` risks the callbacks running in the wrong sequence, non-deterministically, working by accident in development and failing unpredictably later or in a different environment.

- Entity callbacks (`BeforeConvertCallback<T>`, `AfterConvertCallback<T>`, and their store-specific siblings) are Spring Data's own store-agnostic hook mechanism, registered purely by implementing the interface as a Spring bean — no annotation needed on the entity class itself.
- They're most valuable in Spring Data modules without a native JPA-style lifecycle annotation system (MongoDB, Redis, and others) — for JPA specifically, `@PrePersist`/`@PreUpdate`/`@PostLoad` (JPA's own standard, used by `AuditingEntityListener` in earlier cards) are more commonly reached for, though entity callbacks work for JPA too.
- `BeforeConvertCallback` runs just before an entity is translated into its storage representation; `AfterConvertCallback` runs just after a stored representation is converted back into an entity — bracketing the conversion step in both directions.
- `@Order` on multiple callback beans targeting the same entity type establishes a deterministic execution sequence, essential whenever one callback's logic depends on another having already run.
