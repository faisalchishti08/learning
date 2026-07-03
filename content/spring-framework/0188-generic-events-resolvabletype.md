---
card: spring-framework
gi: 188
slug: generic-events-resolvabletype
title: "Generic events (ResolvableType)"
---

## 1. What it is

Spring's event multicaster uses `ResolvableType` to preserve generic type information at runtime, enabling listeners to distinguish `EntityEvent<User>` from `EntityEvent<Order>` — even though Java erases generics at compile time.

```java
class EntityEvent<T> extends ApplicationEvent {
    private final T entity;
    EntityEvent(Object source, T entity) { super(source); this.entity = entity; }
    public T getEntity() { return entity; }

    // Key: override getResolvableType() to carry the T at runtime
    @Override
    public ResolvableType getResolvableType() {
        return ResolvableType.forClassWithGenerics(
            EntityEvent.class, ResolvableType.forInstance(entity));
    }
}

// Listens ONLY to EntityEvent<User>
@EventListener
public void onUserSaved(EntityEvent<User> event) { ... }

// Listens ONLY to EntityEvent<Order>
@EventListener
public void onOrderSaved(EntityEvent<Order> event) { ... }
```

Without `getResolvableType()` override, both methods would receive both events because `EntityEvent<User>` and `EntityEvent<Order>` would be type-erased to `EntityEvent` at runtime.

## 2. Why & when

- **Domain events for multiple entity types** — a generic `EntitySavedEvent<T>`, `EntityDeletedEvent<T>` pattern avoids one event class per entity type.
- **Audit infrastructure** — a generic `AuditEvent<T>` carries any entity; specific listeners subscribe to exactly the entity type they care about.
- **Framework builders** — building a reusable event infrastructure (Spring Data uses this for `AbstractAggregateRoot` domain events).
- **Skip this** when you have a small number of event types and don't mind one class per event — the extra complexity of `getResolvableType()` is only warranted for truly generic event hierarchies.

## 3. Core concept

Java generics are erased at runtime: a `List<String>` is just `List` at the bytecode level. For events, this means `EntityEvent<User>` and `EntityEvent<Order>` would be indistinguishable to a class-based event dispatcher.

`ResolvableType` is Spring's wrapper around `java.lang.reflect.Type` that preserves generic type information. When an event class overrides `getResolvableType()`, the multicaster uses that type (instead of the raw class) to match listeners.

**How matching works:**

1. For each `@EventListener` method with parameter `EntityEvent<User>`, Spring captures a `ResolvableType` for `EntityEvent<User>`.
2. When `publishEvent(new EntityEvent<>(src, user))` is called, Spring calls `event.getResolvableType()` on the published event.
3. Spring checks: is the event's `ResolvableType` assignable to the listener's declared parameter type?
4. If yes, the listener is invoked.

**`ResolvableType.forInstance(entity)`** resolves the type from the actual runtime object — so if `entity` is a `User`, it captures `ResolvableType.forClass(User.class)`.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="gea" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="gex" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e74c3c"/></marker>
  </defs>

  <!-- Event types published -->
  <rect x="5" y="20" width="160" height="28" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="38" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">EntityEvent&lt;User&gt;</text>
  <text x="85" y="47" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">getResolvableType() → EntityEvent&lt;User&gt;</text>

  <rect x="5" y="60" width="160" height="28" rx="4" fill="#79c0ff" opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="78" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">EntityEvent&lt;Order&gt;</text>
  <text x="85" y="87" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">getResolvableType() → EntityEvent&lt;Order&gt;</text>

  <!-- Multicaster -->
  <rect x="205" y="5" width="180" height="165" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="295" y="22" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Multicaster</text>
  <text x="295" y="37" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">uses event.getResolvableType()</text>
  <text x="295" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">to match listener parameter</text>
  <line x1="167" y1="34"  x2="203" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gea)"/>
  <line x1="167" y1="74"  x2="203" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gea)"/>

  <!-- Listeners -->
  <rect x="440" y="5"  width="255" height="35" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="567" y="20" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">onUserSaved(EntityEvent&lt;User&gt;)</text>
  <text x="567" y="33" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">receives EntityEvent&lt;User&gt; only</text>

  <rect x="440" y="50" width="255" height="35" rx="4" fill="#79c0ff" opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="567" y="65" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">onOrderSaved(EntityEvent&lt;Order&gt;)</text>
  <text x="567" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">receives EntityEvent&lt;Order&gt; only</text>

  <rect x="440" y="100" width="255" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="567" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">onAny(EntityEvent&lt;?&gt;)</text>
  <text x="567" y="128" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">receives ALL EntityEvent subtypes</text>

  <!-- Routing arrows -->
  <line x1="387" y1="55"  x2="438" y2="22"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#gea)"/>
  <line x1="387" y1="55"  x2="438" y2="117" stroke="#8b949e" stroke-width="1"   marker-end="url(#gea)" opacity="0.5"/>
  <line x1="387" y1="95"  x2="438" y2="67"  stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gea)"/>
  <line x1="387" y1="95"  x2="438" y2="117" stroke="#8b949e" stroke-width="1"   marker-end="url(#gea)" opacity="0.5"/>

  <!-- No-go annotations -->
  <text x="415" y="44"  fill="#e74c3c" font-size="9" font-family="sans-serif">✗</text>
  <text x="415" y="80"  fill="#e74c3c" font-size="9" font-family="sans-serif">✗</text>

  <text x="350" y="165" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Without getResolvableType() override: both listeners receive both events (type erasure)</text>
</svg>

`getResolvableType()` carries the concrete type parameter at runtime; the multicaster uses it to route `EntityEvent<User>` only to listeners parameterised with `User`.

## 5. Runnable example

The scenario is a **domain event audit system** for any entity type — growing from basic generic events to production-grade resolution.

### Level 1 — Basic

Generic `EntitySavedEvent<T>` with `getResolvableType()`; two typed listeners.

```java
// GenericEventsBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.core.*;
import org.springframework.stereotype.*;

// --- Domain types ---
record User(String id, String name) {}
record Order(String id, double total) {}

// --- Generic event ---
class EntitySavedEvent<T> extends ApplicationEvent {
    private final T entity;
    EntitySavedEvent(Object source, T entity) { super(source); this.entity = entity; }
    public T getEntity() { return entity; }

    // Override getResolvableType so Spring can distinguish <User> from <Order>
    @Override
    public ResolvableType getResolvableType() {
        return ResolvableType.forClassWithGenerics(
            EntitySavedEvent.class,
            ResolvableType.forInstance(entity));
    }
}

// --- Typed listeners ---
@Component
class UserAuditListener {
    @EventListener
    public void onUserSaved(EntitySavedEvent<User> event) {
        System.out.println("[UserAudit]  Saved user:  " + event.getEntity());
    }
}

@Component
class OrderAuditListener {
    @EventListener
    public void onOrderSaved(EntitySavedEvent<Order> event) {
        System.out.println("[OrderAudit] Saved order: " + event.getEntity());
    }
}

@Service
class EntityService {
    private final ApplicationEventPublisher pub;
    EntityService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void saveUser(User u)   { pub.publishEvent(new EntitySavedEvent<>(this, u)); }
    public void saveOrder(Order o) { pub.publishEvent(new EntitySavedEvent<>(this, o)); }
}

@Configuration @ComponentScan class GenConfig { }

public class GenericEventsBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GenConfig.class);
        var svc = ctx.getBean(EntityService.class);
        svc.saveUser(new User("u1", "Alice"));    // → only UserAuditListener fires
        svc.saveOrder(new Order("o1", 99.99));     // → only OrderAuditListener fires
        ctx.close();
    }
}
```

How to run: `java GenericEventsBasic.java`

`getResolvableType()` returns `ResolvableType.forClassWithGenerics(EntitySavedEvent.class, User.class)` for a `User` entity. Spring uses this to match listener parameter `EntitySavedEvent<User>`. Remove `getResolvableType()` and both listeners would receive both events (or neither, depending on Spring version and type erasure handling).

### Level 2 — Intermediate

Wildcard listener (`EntitySavedEvent<?>`); multiple listeners including a "catch-all"; event hierarchy.

```java
// GenericEventsIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.core.*;
import org.springframework.stereotype.*;

record Product(String sku, String name, double price) {}
record Customer(String id, String email) {}

class EntityCreatedEvent<T> extends ApplicationEvent {
    private final T entity; private final String entityType;
    EntityCreatedEvent(Object src, T entity) {
        super(src); this.entity=entity;
        this.entityType = entity.getClass().getSimpleName();
    }
    public T      getEntity()     { return entity; }
    public String getEntityType() { return entityType; }

    @Override
    public ResolvableType getResolvableType() {
        return ResolvableType.forClassWithGenerics(
            EntityCreatedEvent.class, ResolvableType.forInstance(entity));
    }
}

@Component
class ProductListener {
    @EventListener
    public void onProduct(EntityCreatedEvent<Product> e) {
        System.out.println("[Product] Created: " + e.getEntity().sku()
            + " price=" + e.getEntity().price());
    }
}

@Component
class CustomerListener {
    @EventListener
    public void onCustomer(EntityCreatedEvent<Customer> e) {
        System.out.println("[Customer] Created: " + e.getEntity().id()
            + " email=" + e.getEntity().email());
    }
}

// Wildcard: receives ALL EntityCreatedEvent regardless of T
@Component
class GlobalAuditListener {
    @EventListener
    public void onAny(EntityCreatedEvent<?> e) {
        System.out.println("[GlobalAudit] " + e.getEntityType() + " → " + e.getEntity());
    }
}

@Service
class CreationService {
    private final ApplicationEventPublisher pub;
    CreationService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void createProduct(Product p)   { pub.publishEvent(new EntityCreatedEvent<>(this, p)); }
    public void createCustomer(Customer c) { pub.publishEvent(new EntityCreatedEvent<>(this, c)); }
}

@Configuration @ComponentScan class GenIntermConfig { }

public class GenericEventsIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GenIntermConfig.class);
        var svc = ctx.getBean(CreationService.class);
        svc.createProduct(new Product("SKU-001", "Laptop", 1200.0));
        System.out.println("---");
        svc.createCustomer(new Customer("C-001", "alice@ex.com"));
        ctx.close();
    }
}
```

How to run: `java GenericEventsIntermediate.java`

`EntityCreatedEvent<?>` (wildcard) matches all `EntityCreatedEvent` regardless of type parameter — `GlobalAuditListener` receives both product and customer events. `ProductListener` receives only `EntityCreatedEvent<Product>`, `CustomerListener` only `EntityCreatedEvent<Customer>`. The wildcard listener fires alongside the specific one: both run for each event.

### Level 3 — Advanced

Generic event hierarchy (`EntityCreatedEvent` extends `EntityEvent`); listeners for the supertype receive all subtypes; full Spring Boot integration.

```java
// GenericEventsAdvanced.java
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.*;
import org.springframework.context.event.*;
import org.springframework.core.*;
import org.springframework.stereotype.*;
import java.time.*;

// Base generic event — all entity events extend this
abstract class EntityEvent<T> extends ApplicationEvent {
    protected final T entity;
    protected final Instant timestamp = Instant.now();
    EntityEvent(Object src, T entity) { super(src); this.entity = entity; }
    public T       getEntity()    { return entity; }
    public Instant getTimestamp() { return timestamp; }

    @Override
    public ResolvableType getResolvableType() {
        return ResolvableType.forClassWithGenerics(
            getClass(), ResolvableType.forInstance(entity));
    }
}

// Concrete subtypes: created / updated / deleted
class EntityCreatedEvent<T> extends EntityEvent<T> {
    EntityCreatedEvent(Object src, T entity) { super(src, entity); }
}

class EntityUpdatedEvent<T> extends EntityEvent<T> {
    EntityUpdatedEvent(Object src, T entity) { super(src, entity); }
}

// Domain entities
record Inventory(String itemId, int quantity) {}

@org.springframework.stereotype.Component
class InventoryEventHandler {
    @EventListener
    public void onCreate(EntityCreatedEvent<Inventory> e) {
        System.out.println("[Created] " + e.getEntity().itemId()
            + " qty=" + e.getEntity().quantity() + " at " + e.getTimestamp());
    }
    @EventListener
    public void onUpdate(EntityUpdatedEvent<Inventory> e) {
        System.out.println("[Updated] " + e.getEntity().itemId()
            + " qty=" + e.getEntity().quantity());
    }
}

// Catch-all: listens to EntityEvent<Inventory> regardless of create/update subtype
@org.springframework.stereotype.Component
class InventoryAuditLogger {
    @EventListener
    public void logAll(EntityEvent<Inventory> e) {
        System.out.println("[Audit] " + e.getClass().getSimpleName()
            + " for " + e.getEntity().itemId());
    }
}

@org.springframework.stereotype.Service
class InventoryService {
    private final ApplicationEventPublisher pub;
    InventoryService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void add(String id, int qty) {
        pub.publishEvent(new EntityCreatedEvent<>(this, new Inventory(id, qty)));
    }
    public void restock(String id, int qty) {
        pub.publishEvent(new EntityUpdatedEvent<>(this, new Inventory(id, qty)));
    }
}

@SpringBootApplication
public class GenericEventsAdvanced {
    public static void main(String[] args) {
        var ctx = SpringApplication.run(GenericEventsAdvanced.class, args);
        var svc = ctx.getBean(InventoryService.class);
        svc.add("ITEM-A", 100);
        svc.restock("ITEM-A", 150);
        SpringApplication.exit(ctx);
    }
}
```

How to run: `./mvnw spring-boot:run` or `java GenericEventsAdvanced.java`

The `getResolvableType()` in `EntityEvent` returns `forClassWithGenerics(getClass(), ...)` — using `getClass()` means `EntityCreatedEvent<Inventory>` and `EntityUpdatedEvent<Inventory>` each produce a distinct `ResolvableType`. `InventoryAuditLogger` listens to `EntityEvent<Inventory>` and receives both created and updated events (supertype match with matching generic type). `InventoryEventHandler` receives them separately via the concrete subtype methods.

## 6. Walkthrough

Tracing `svc.add("ITEM-A", 100)` (publishes `EntityCreatedEvent<Inventory>`):

**Step 1 — `publishEvent(new EntityCreatedEvent<>(this, new Inventory("ITEM-A", 100)))` called.**

**Step 2 — Multicaster calls `event.getResolvableType()`:**
- `getClass()` = `EntityCreatedEvent`
- `ResolvableType.forInstance(entity)` = `ResolvableType.forClass(Inventory.class)`
- Result: `ResolvableType` representing `EntityCreatedEvent<Inventory>`

**Step 3 — Match listeners:**

| Listener method | Parameter type | Matches? |
|---|---|---|
| `InventoryEventHandler.onCreate` | `EntityCreatedEvent<Inventory>` | **yes** — exact |
| `InventoryEventHandler.onUpdate` | `EntityUpdatedEvent<Inventory>` | **no** — different subtype |
| `InventoryAuditLogger.logAll` | `EntityEvent<Inventory>` | **yes** — supertype match |

**Step 4 — Dispatch:**
- `onCreate` prints `[Created] ITEM-A qty=100 at <timestamp>`
- `logAll` prints `[Audit] EntityCreatedEvent for ITEM-A`

**Then `svc.restock("ITEM-A", 150)` dispatches `EntityUpdatedEvent<Inventory>`:**
- `onUpdate` prints `[Updated] ITEM-A qty=150`
- `logAll` prints `[Audit] EntityUpdatedEvent for ITEM-A`
- `onCreate` does NOT fire (wrong subtype)

## 7. Gotchas & takeaways

> **Without `getResolvableType()` override, ALL `@EventListener(EntitySavedEvent.class)` listeners receive all generic variants.** Spring falls back to raw class matching when `getResolvableType()` returns the default (raw class type). The override is the ONLY mechanism to differentiate `EntityEvent<User>` from `EntityEvent<Order>` at dispatch time.

> **`ResolvableType.forInstance(entity)` uses the runtime type of `entity`.** If `entity` is declared as a supertype variable (e.g., `Object entity`) but holds a `User`, it resolves to `User`. If `entity` is `null`, `forInstance` throws — guard with `ResolvableType.forClass(entityClass)` when the entity might be null.

- `ResolvableType.forClassWithGenerics(EntityEvent.class, User.class)` is equivalent to `EntityEvent<User>`. Use it when you know the type at compile time; use `forInstance` when the type is only known at runtime.
- A listener with an unparameterised type (`EntitySavedEvent` without `<T>`) receives all `EntitySavedEvent` events regardless of type parameter — same as `EntitySavedEvent<?>`.
- Spring Data uses this pattern internally: `AbstractAggregateRoot.registerEvent(T)` collects domain events; Spring Data repositories publish them after save, with full generic type routing.
- The `ResolvableType` approach is purely Spring-specific. If you need cross-framework event routing, use a message broker with message type headers instead.
