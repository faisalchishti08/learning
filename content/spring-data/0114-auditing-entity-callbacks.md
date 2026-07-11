---
card: spring-data
gi: 114
slug: auditing-entity-callbacks
title: "Auditing & entity callbacks"
---

## 1. What it is

**Auditing** automatically fills in "who/when" metadata (`@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, `@LastModifiedBy`) on documents as they're saved, so no repository method has to set those fields by hand. It's powered by **entity callbacks** — `BeforeConvertCallback`/`ReactiveBeforeConvertCallback` hooks that Spring Data MongoDB runs automatically on every save, just before the object is converted to a BSON document.

```java
@Document("orders")
class Order {
    @Id String id;
    @CreatedDate Instant createdAt;
    @LastModifiedDate Instant updatedAt;
}

@Configuration
@EnableMongoAuditing
class MongoConfig { }
```

## 2. Why & when

Every document that matters usually needs to answer "when was this created?" and "when was it last touched?" — and doing that by hand in every service method that calls `save()` is repetitive and easy to forget in just one code path, silently leaving a document with a stale or missing timestamp. Auditing turns this into a cross-cutting concern handled once, centrally, for every save.

Reach for auditing and entity callbacks when:

- Every document in a collection needs consistent `createdAt`/`updatedAt` timestamps, and you want that guaranteed rather than dependent on every call site remembering to set them.
- You need to know **who** made a change, not just when — `@CreatedBy`/`@LastModifiedBy` combined with an `AuditorAware` bean that resolves the current user (from Spring Security's context, for example).
- You need custom pre-save logic beyond the built-in auditing annotations — a `BeforeConvertCallback` can normalize data, generate a derived field, or validate an invariant right before every document is persisted, without repository callers needing to remember to call it.

## 3. Core concept

```
 repository.save(order)
        |
        v
  BeforeConvertCallback runs automatically (before BSON conversion)
        |
        +-- if new document: set createdAt = now, createdBy = currentUser
        +-- always:          set updatedAt = now, updatedBy = currentUser
        |
        v
  document converted to BSON and written to MongoDB
```

`@EnableMongoAuditing` registers a built-in `BeforeConvertCallback` that reads the `@CreatedDate`/`@LastModifiedDate`/`@CreatedBy`/`@LastModifiedBy` annotations via reflection and fills them in — the same extension point a custom callback uses for anything auditing doesn't cover out of the box.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A save call passes through a BeforeConvertCallback that stamps audit fields before the document reaches the database">
  <rect x="20" y="55" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">repository.save(order)</text>

  <rect x="245" y="55" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BeforeConvertCallback</text>
  <text x="335" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">stamps createdAt/updatedAt</text>

  <rect x="500" y="55" width="120" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="560" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MongoDB</text>

  <line x1="170" y1="80" x2="240" y2="80" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="425" y1="80" x2="495" y2="80" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The callback sits transparently between every `save()` call and the database — no caller has to invoke it explicitly.

## 5. Runnable example

The scenario: stamping `createdAt`/`updatedAt` on `Order` documents, evolving from manual timestamp-setting at every call site, to an automatic `BeforeConvertCallback` that does it for every save, to a version that also tracks *who* made the change using an `AuditorAware`-style current-user resolver.

### Level 1 — Basic

Show the problem: setting timestamps manually, which only works if every call site remembers to do it.

```java
import java.time.*;
import java.util.*;

public class AuditingLevel1 {
    public static void main(String[] args) throws InterruptedException {
        OrderRepository repo = new OrderRepository();
        Order order = new Order("1", "PENDING");

        repo.save(order); // relies on save() remembering to stamp timestamps
        System.out.println("Created at: " + order.createdAt);

        Thread.sleep(10);
        order.status = "SHIPPED";
        repo.save(order);
        System.out.println("Created at (unchanged): " + order.createdAt);
        System.out.println("Updated at (changed):   " + order.updatedAt);
    }
}

class Order { String id; String status; Instant createdAt; Instant updatedAt; Order(String id, String status) { this.id = id; this.status = status; } }

class OrderRepository {
    Map<String, Order> docs = new HashMap<>();

    // Every caller must remember to set timestamps THEMSELVES -- easy to forget.
    void save(Order order) {
        if (order.createdAt == null) order.createdAt = Instant.now();
        order.updatedAt = Instant.now();
        docs.put(order.id, order);
    }
}
```

How to run: `java AuditingLevel1.java`

`save` manually checks whether `createdAt` is already set (only stamping it the first time) and always refreshes `updatedAt`. This works, but the logic lives inside one specific repository's `save` method — a second repository for a different document type would need to duplicate it, and a developer could easily write a `save` that forgets it entirely.

### Level 2 — Intermediate

Extract the timestamp logic into a reusable `BeforeConvertCallback`-style hook that runs automatically for **any** document type carrying `@CreatedDate`/`@LastModifiedDate`-equivalent fields, removing the per-repository duplication.

```java
import java.time.*;
import java.util.*;
import java.util.function.*;

public class AuditingLevel2 {
    public static void main(String[] args) throws InterruptedException {
        OrderRepository repo = new OrderRepository();
        repo.registerCallback(new AuditingCallback()); // registered ONCE, applies to every save

        Order order = new Order("1", "PENDING");
        repo.save(order);
        System.out.println("Created at: " + order.createdAt);

        Thread.sleep(10);
        order.status = "SHIPPED";
        repo.save(order);
        System.out.println("Created at (unchanged): " + order.createdAt);
        System.out.println("Updated at (changed):   " + order.updatedAt);
    }
}

class Order { String id; String status; Instant createdAt; Instant updatedAt; Order(String id, String status) { this.id = id; this.status = status; } }

// Stands in for org.springframework.data.mongodb.core.mapping.event.BeforeConvertCallback.
interface BeforeConvertCallback<T> { T onBeforeConvert(T entity); }

// Stands in for the built-in callback @EnableMongoAuditing registers.
class AuditingCallback implements BeforeConvertCallback<Order> {
    public Order onBeforeConvert(Order order) {
        if (order.createdAt == null) order.createdAt = Instant.now(); // only stamped once, on first save
        order.updatedAt = Instant.now();                              // stamped on EVERY save
        return order;
    }
}

class OrderRepository {
    Map<String, Order> docs = new HashMap<>();
    private final List<BeforeConvertCallback<Order>> callbacks = new ArrayList<>();

    void registerCallback(BeforeConvertCallback<Order> callback) { callbacks.add(callback); }

    void save(Order order) {
        for (BeforeConvertCallback<Order> cb : callbacks) order = cb.onBeforeConvert(order); // runs BEFORE persisting
        docs.put(order.id, order);
    }
}
```

How to run: `java AuditingLevel2.java`

`OrderRepository.save` no longer contains any timestamp logic itself — it just runs every registered `BeforeConvertCallback` before persisting, exactly like `@EnableMongoAuditing` transparently wiring its own callback into the save pipeline. The `AuditingCallback` is written once and would apply to every document type that declares audit fields, not just `Order`.

### Level 3 — Advanced

Add `createdBy`/`updatedBy`, resolved through an `AuditorAware`-style current-user supplier, and support **multiple** callbacks running in sequence — auditing plus a custom validation callback.

```java
import java.time.*;
import java.util.*;
import java.util.function.*;

public class AuditingLevel3 {
    public static void main(String[] args) {
        // Simulates the currently authenticated user changing between two saves.
        List<String> loggedInAs = new ArrayList<>(List.of("alice", "bob"));
        AuditorAware auditorAware = () -> loggedInAs.remove(0);

        OrderRepository repo = new OrderRepository();
        repo.registerCallback(new StatusValidationCallback()); // runs FIRST
        repo.registerCallback(new AuditingCallback(auditorAware)); // runs SECOND

        Order order = new Order("1", "PENDING");
        repo.save(order); // "alice" creates it
        System.out.println("Created by: " + order.createdBy + ", updated by: " + order.updatedBy);

        order.status = "SHIPPED";
        repo.save(order); // "bob" updates it
        System.out.println("Created by (unchanged): " + order.createdBy);
        System.out.println("Updated by (changed):   " + order.updatedBy);
    }
}

class Order { String id; String status; Instant createdAt; Instant updatedAt; String createdBy; String updatedBy; Order(String id, String status) { this.id = id; this.status = status; } }

interface BeforeConvertCallback<T> { T onBeforeConvert(T entity); }

// Stands in for org.springframework.data.domain.AuditorAware<String>.
interface AuditorAware { String getCurrentAuditor(); }

class AuditingCallback implements BeforeConvertCallback<Order> {
    private final AuditorAware auditorAware;
    AuditingCallback(AuditorAware auditorAware) { this.auditorAware = auditorAware; }

    public Order onBeforeConvert(Order order) {
        String currentUser = auditorAware.getCurrentAuditor(); // e.g. pulled from Spring Security's SecurityContext
        if (order.createdAt == null) { order.createdAt = Instant.now(); order.createdBy = currentUser; }
        order.updatedAt = Instant.now();
        order.updatedBy = currentUser;
        return order;
    }
}

// A SECOND, independent callback -- proves callbacks compose rather than replace each other.
class StatusValidationCallback implements BeforeConvertCallback<Order> {
    public Order onBeforeConvert(Order order) {
        if (order.status == null) throw new IllegalStateException("status must not be null before save");
        return order;
    }
}

class OrderRepository {
    Map<String, Order> docs = new HashMap<>();
    private final List<BeforeConvertCallback<Order>> callbacks = new ArrayList<>();
    void registerCallback(BeforeConvertCallback<Order> callback) { callbacks.add(callback); }

    void save(Order order) {
        for (BeforeConvertCallback<Order> cb : callbacks) order = cb.onBeforeConvert(order); // runs in REGISTRATION order
        docs.put(order.id, order);
    }
}
```

How to run: `java AuditingLevel3.java`

Two callbacks are registered — `StatusValidationCallback` and `AuditingCallback` — and both run, in registration order, on every `save`. `AuditorAware.getCurrentAuditor()` stands in for resolving the logged-in user from Spring Security's context; because it returns `"alice"` on the first call and `"bob"` on the second, `createdBy` is stamped once as `"alice"` and never changes, while `updatedBy` reflects whoever performed the most recent save.

## 6. Walkthrough

Execution starts in `main` for Level 3. `auditorAware` is set up to return `"alice"` the first time it's asked and `"bob"` the second time, standing in for two separate requests authenticated as different users. `repo` has two callbacks registered: validation first, auditing second.

The first `repo.save(order)` call runs `StatusValidationCallback.onBeforeConvert` first — `order.status` is `"PENDING"`, so validation passes and the order is returned unchanged. Then `AuditingCallback.onBeforeConvert` runs: `order.createdAt` is `null`, so both `createdAt` and `createdBy` (`"alice"`) are set; `updatedAt`/`updatedBy` are set unconditionally, also to `"alice"` at this point. The stamped order is written to `docs`.

`order.status` is then changed to `"SHIPPED"` and `repo.save(order)` is called again. Validation passes again (`status` is non-null). In `AuditingCallback`, `order.createdAt` is now non-null (set on the first save), so the `createdAt`/`createdBy` block is skipped entirely — `createdBy` stays `"alice"`. But `updatedAt`/`updatedBy` are set unconditionally again, this time to `"bob"`, the second value returned by `auditorAware`.

```
Created by: alice, updated by: alice
Created by (unchanged): alice
Updated by (changed):   bob
```

In real Spring Data MongoDB, `@EnableMongoAuditing` registers exactly this kind of `BeforeConvertCallback` automatically for any document annotated with `@CreatedDate`/`@LastModifiedDate`/`@CreatedBy`/`@LastModifiedBy`, and it reads the current user from whatever `AuditorAware<T>` bean is in the application context — typically one backed by `SecurityContextHolder.getContext().getAuthentication()`. Custom callbacks like `StatusValidationCallback` register alongside it and all run, in order, every time `save()` (or its reactive equivalent) is called — no repository method has to invoke any of this logic itself.

## 7. Gotchas & takeaways

> Gotcha: `@CreatedDate` is only set when the field is `null` at save time — if a document is being re-inserted with the ID of a document that was deleted, or a `createdAt` is accidentally cleared before a save, it will look like a "new" document to the auditing callback and get a fresh `createdAt`.

> Gotcha: `@EnableMongoAuditing` only works if there is a bean of the field's type available for `@CreatedBy`/`@LastModifiedBy` — without an `AuditorAware` bean registered, those two fields are silently left `null` even though `@CreatedDate`/`@LastModifiedDate` still work.

- `@EnableMongoAuditing` wires a built-in `BeforeConvertCallback` that stamps `@CreatedDate`/`@LastModifiedDate`/`@CreatedBy`/`@LastModifiedBy` automatically on every save, blocking or reactive.
- Custom `BeforeConvertCallback`/`ReactiveBeforeConvertCallback` beans compose with the built-in auditing callback — both run, in registration order, on every save.
- `@CreatedBy`/`@LastModifiedBy` need an `AuditorAware` (or `ReactiveAuditorAware`) bean that resolves "who is doing this write right now," typically from the security context.
- Centralizing audit logic in a callback guarantees consistency across every save call site, instead of depending on every repository method remembering to do it manually.
