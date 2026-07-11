---
card: spring-data
gi: 87
slug: lifecycle-events-entity-callbacks
title: "Lifecycle events / entity callbacks"
---

## 1. What it is

Spring Data JDBC exposes hooks into its save/load pipeline through two mechanisms: **Spring application events** (`BeforeSaveEvent`, `AfterSaveEvent`, `BeforeConvertEvent`, `BeforeDeleteEvent`, `AfterDeleteEvent`, ...) that any `@EventListener` bean can subscribe to, and the more targeted **entity callback** interfaces (`BeforeConvertCallback<T>`, `BeforeSaveCallback<T>`, `AfterSaveCallback<T>`, ...) that receive and can transform the entity directly.

```java
class OrderBeforeSaveCallback implements BeforeSaveCallback<Order> {
    public Order onBeforeSave(Order order, MutableAggregateChange<Order> change) {
        order.status = order.status.toUpperCase(); // transform right before the SQL is issued
        return order;
    }
}
```

## 2. Why & when

The auditing card already showed one specific entity callback (`BeforeConvertCallback`, used internally for setting auditing fields) — this card generalizes that to the full set of hooks available, and clarifies the choice between broad application events (good for logging, metrics, side effects unrelated to the entity itself) and entity callbacks (good for transforming the entity's own data before it's persisted).

Reach for lifecycle events or entity callbacks specifically when:

- You need to react to a save/delete happening (e.g., publish a domain event, write an audit log entry, invalidate a cache) without changing the entity itself — application events (`@EventListener(AfterSaveEvent.class)`) are the right tool.
- You need to transform or validate the entity's own data as part of the save pipeline (normalizing a field, computing a derived value) — an entity callback (`BeforeSaveCallback<T>`) is the right tool, since it can return a modified entity.
- You're building cross-cutting behavior that should apply to *every* aggregate of a certain type without repository-specific code — both mechanisms are registered once as beans and apply automatically to all matching saves.

## 3. Core concept

```
 save() pipeline (simplified):
   BeforeConvertCallback  -- transform entity, THEN convert to SQL parameters
   BeforeConvertEvent
   BeforeSaveCallback     -- transform entity again, right before the SQL statement executes
   BeforeSaveEvent
   [ SQL INSERT/UPDATE actually runs ]
   AfterSaveCallback
   AfterSaveEvent

 Entity callbacks: receive + return the entity -- can MODIFY it
 Application events: receive the entity/change -- CANNOT modify what gets saved, only react
```

Callbacks run earlier in the pipeline and can transform the entity; events fire alongside them but are for reacting, not modifying.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="The save pipeline runs BeforeConvert, BeforeSave callbacks and events, then the SQL, then AfterSave callbacks and events">
  <rect x="10" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="80" y="43" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">BeforeConvert*</text>

  <rect x="170" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="240" y="43" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">BeforeSave*</text>

  <rect x="330" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="400" y="43" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">SQL INSERT/UPDATE</text>

  <rect x="490" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="560" y="43" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">AfterSave*</text>

  <line x1="150" y1="40" x2="165" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#le)"/>
  <line x1="310" y1="40" x2="325" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#le)"/>
  <line x1="470" y1="40" x2="485" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#le)"/>

  <text x="80" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">can MODIFY entity</text>
  <text x="240" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">can MODIFY entity</text>
  <text x="560" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">react only (already saved)</text>
  <defs><marker id="le" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Callbacks before the SQL runs can still transform the entity; anything after the SQL runs is purely reactive.

## 5. Runnable example

The scenario: normalizing and reacting to order saves, evolving from a plain save with no hooks, to a `BeforeSaveCallback` transforming the entity's data, to an `AfterSaveEvent`-style listener performing a side effect that cannot change what was saved.

### Level 1 — Basic

Show the baseline: a save with no hooks at all, so inconsistent data (mixed-case status) passes through unchanged.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    void save(Order order) {
        db.put(order.id, order); // no transformation, no hooks
        System.out.println("Saved as-is: status=" + order.status);
    }
}

public class LifecycleLevel1 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save(new Order(1, "shipped")); // lowercase, inconsistent with the rest of the system's convention
    }
}
```

How to run: `java LifecycleLevel1.java`

`"shipped"` is saved exactly as given — lowercase, inconsistent with whatever convention the rest of the application expects (e.g., always uppercase status codes). Nothing normalizes it, since there's no hook in the pipeline at all.

### Level 2 — Intermediate

Add a `BeforeSaveCallback`-style hook that transforms the entity's data right before it's persisted, matching how a real callback can modify the entity as part of the pipeline.

```java
import java.util.*;
import java.util.function.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

// interface BeforeSaveCallback<Order> { Order onBeforeSave(Order order); }
interface BeforeSaveCallback { Order onBeforeSave(Order order); }

class UppercaseStatusCallback implements BeforeSaveCallback {
    public Order onBeforeSave(Order order) {
        order.status = order.status.toUpperCase(); // transform BEFORE the SQL is built
        return order;
    }
}

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    private final List<BeforeSaveCallback> callbacks;
    OrderRepository(List<BeforeSaveCallback> callbacks) { this.callbacks = callbacks; }

    void save(Order order) {
        Order current = order;
        for (BeforeSaveCallback cb : callbacks) current = cb.onBeforeSave(current); // run EVERY registered callback
        db.put(current.id, current);
        System.out.println("Saved after callbacks: status=" + current.status);
    }
}

public class LifecycleLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository(List.of(new UppercaseStatusCallback()));
        repo.save(new Order(1, "shipped")); // lowercase input...
    }
}
```

How to run: `java LifecycleLevel2.java`

`repo.save` now runs every registered `BeforeSaveCallback` on the entity before storing it — `"shipped"` becomes `"SHIPPED"` by the time it's saved, because `UppercaseStatusCallback.onBeforeSave` transformed it as part of the pipeline, matching how a real `BeforeSaveCallback<Order>` bean is discovered and applied automatically to every `orderRepository.save(...)` call, without any repository-specific code.

### Level 3 — Advanced

Add an `AfterSaveEvent`-style listener performing a side effect (logging/publishing), and demonstrate that — unlike the callback — it cannot change what was actually saved, since the save has already happened by the time it fires.

```java
import java.util.*;
import java.util.function.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

interface BeforeSaveCallback { Order onBeforeSave(Order order); }
class UppercaseStatusCallback implements BeforeSaveCallback {
    public Order onBeforeSave(Order order) { order.status = order.status.toUpperCase(); return order; }
}

// Stands in for: @EventListener void onAfterSave(AfterSaveEvent<Order> event) { ... }
interface AfterSaveListener { void onAfterSave(Order savedOrder); }
class AuditLogListener implements AfterSaveListener {
    List<String> auditLog = new ArrayList<>();
    public void onAfterSave(Order savedOrder) {
        // Attempting to "fix" the data here has NO effect on what was already written to the database.
        String attemptedFix = savedOrder.status.toLowerCase(); // computed, but never actually applied/saved
        auditLog.add("Order " + savedOrder.id + " saved with status=" + savedOrder.status);
        System.out.println("  [audit] logged: status=" + savedOrder.status + " (any local change here, like '"
            + attemptedFix + "', does NOT get persisted)");
    }
}

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    private final List<BeforeSaveCallback> beforeSave;
    private final List<AfterSaveListener> afterSave;
    OrderRepository(List<BeforeSaveCallback> beforeSave, List<AfterSaveListener> afterSave) {
        this.beforeSave = beforeSave; this.afterSave = afterSave;
    }

    void save(Order order) {
        Order current = order;
        for (BeforeSaveCallback cb : beforeSave) current = cb.onBeforeSave(current); // CAN modify
        db.put(current.id, current); // <-- the ACTUAL persisted state is fixed here
        for (AfterSaveListener listener : afterSave) listener.onAfterSave(current); // reacts only, too late to change anything
    }
}

public class LifecycleLevel3 {
    public static void main(String[] args) {
        AuditLogListener auditListener = new AuditLogListener();
        OrderRepository repo = new OrderRepository(List.of(new UppercaseStatusCallback()), List.of(auditListener));

        repo.save(new Order(1, "shipped"));

        System.out.println("Final persisted status: " + repo.db.get(1L).status); // reflects the BEFORE-save callback
        System.out.println("Audit log: " + auditListener.auditLog);
    }
}
```

How to run: `java LifecycleLevel3.java`

The final persisted status is `"SHIPPED"` — the result of `UppercaseStatusCallback`, which ran *before* `db.put(...)`. `AuditLogListener.onAfterSave` computes `attemptedFix` (a lowercase version) but this value is discarded after being printed — it never reaches `db`, because by the time an after-save listener fires, the save has already happened; it can only observe and react, never retroactively change the persisted data.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `repo.save(new Order(1, "shipped"))` runs. Inside `save`, the `beforeSave` loop runs first: `UppercaseStatusCallback.onBeforeSave(current)` transforms `current.status` from `"shipped"` to `"SHIPPED"`, and returns the (mutated) `current` object.

Next, `db.put(current.id, current)` executes — this is the moment the "persisted" state becomes fixed at `status="SHIPPED"`. Everything from this point forward can observe that value, but nothing can change it retroactively.

Then the `afterSave` loop runs: `AuditLogListener.onAfterSave(current)` is called with the already-saved order. Inside, it computes `attemptedFix = savedOrder.status.toLowerCase()` (producing `"shipped"`), appends a log entry to `auditLog`, and prints a message showing that this locally-computed value has no effect on the actual database — `current`/`db.get(1L)` is untouched by anything happening inside this listener.

Back in `main`, `repo.db.get(1L).status` is printed and confirmed to be `"SHIPPED"` — the before-save callback's transformation, not the after-save listener's local computation. `auditListener.auditLog` is also printed, showing the log entry correctly recorded `status=SHIPPED` (the value as it existed at save time, which is all an after-save listener can ever observe).

```
save(Order(1, "shipped")):
  beforeSave: UppercaseStatusCallback -> status="SHIPPED" (mutates the entity BEFORE persistence)
  db.put(1, order{status=SHIPPED})     <-- persisted state now fixed
  afterSave: AuditLogListener -> observes status=SHIPPED, computes a local "fix" that goes nowhere
```

In a real Spring Data JDBC application, both `BeforeSaveCallback<Order>` and an `@EventListener` method handling `AfterSaveEvent<Order>` are registered as ordinary Spring beans — Spring Data JDBC discovers and invokes them automatically for every matching `save()` call, in the pipeline order shown in the diagram. A `BeforeSaveCallback` returning a modified entity changes what actually gets written to the database; anything reacting to `AfterSaveEvent` (or an `AfterSaveCallback`) is working with data that's already committed — useful for logging, publishing a domain event, or invalidating a cache, but never for altering the persisted result.

## 7. Gotchas & takeaways

> Gotcha: an `AfterSaveCallback`/`AfterSaveEvent` handler that mutates the entity object it receives can create a confusing illusion of having "fixed" something, since the in-memory object changes — but the database row was already written with the pre-mutation values, so the change is invisible to anyone re-querying the database, only visible on that one in-memory reference.

- Entity callbacks (`BeforeConvertCallback`, `BeforeSaveCallback`, ...) run before the SQL executes and can transform the entity — the returned value is what actually gets persisted.
- Application events (`BeforeSaveEvent`, `AfterSaveEvent`, ...) are for reacting to lifecycle moments, not for modifying what gets saved — by the time an after-save event fires, the write has already happened.
- Use callbacks for data transformation/validation that should affect the persisted result; use events for cross-cutting side effects (logging, publishing, cache invalidation) that shouldn't.
- Both mechanisms are registered once as Spring beans and apply automatically to every matching save — no per-repository wiring is needed.
