---
card: spring-data
gi: 184
slug: events-repositoryeventhandler-applicationlistener
title: "Events (RepositoryEventHandler / ApplicationListener)"
---

## 1. What it is

Spring Data REST fires an application event before and after every repository operation — `BeforeCreateEvent`, `AfterCreateEvent`, `BeforeSaveEvent`, `AfterDeleteEvent`, and so on. `@RepositoryEventHandler` lets you listen for these with plain annotated methods on a single class; `ApplicationListener<T>` is the lower-level, single-event-type alternative Spring's core event system already provides.

```java
@RepositoryEventHandler(Customer.class)
class CustomerEventHandler {
    @HandleBeforeCreate
    void beforeCreate(Customer c) {
        if (c.email == null) throw new IllegalArgumentException("email required");
    }
    @HandleAfterCreate
    void afterCreate(Customer c) {
        // send a welcome email, publish to a message queue, etc.
    }
}
```

## 2. Why & when

The custom-controller card showed how to add endpoints for actions that aren't plain CRUD. Events solve a related but different problem: reacting to CRUD that's *already happening* through the generated endpoints — validating before a save completes, or triggering a side effect after one succeeds — without writing a custom controller for what's still fundamentally a standard create/update/delete.

Reach for repository events when:

- You need to hook into a repository operation's lifecycle (before/after create, save, or delete) without overriding or replacing the standard generated endpoint.
- The reaction is cross-cutting — the same handler should apply no matter which client or code path triggered the save (a generated endpoint, a custom controller, a batch job).
- You want the hook centralized in one place rather than scattered validation or side-effect code copy-pasted into every place that might call `save()`.

## 3. Core concept

```
 POST /customers  { name: "Amara", email: null }

 1. BeforeCreateEvent fired      -> @HandleBeforeCreate runs, throws (email required)
                                       request rejected, entity never saved

 POST /customers  { name: "Amara", email: "amara@example.com" }

 1. BeforeCreateEvent fired      -> @HandleBeforeCreate runs, passes validation
 2. entity actually saved
 3. AfterCreateEvent fired        -> @HandleAfterCreate runs, side effect (e.g. welcome email)
```

Before-events can veto the operation by throwing; after-events run only once the operation has actually succeeded, for side effects that shouldn't happen on a failed save.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A create request triggers a before-event that can reject it, followed by the actual save, followed by an after-event for side effects">
  <rect x="20" y="45" width="140" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">BeforeCreateEvent</text>

  <line x1="160" y1="67" x2="220" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a17)"/>

  <rect x="230" y="45" width="140" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">entity saved</text>

  <line x1="370" y1="67" x2="430" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a17)"/>

  <rect x="440" y="45" width="140" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">AfterCreateEvent</text>

  <defs><marker id="a17" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Before-events can stop the operation entirely; after-events only fire once the save has succeeded.

## 5. Runnable example

The scenario: validating and reacting to customer creation, evolving from validation logic duplicated at every call site, to a centralized `@RepositoryEventHandler` intercepting before-create, to a full before/after pair also demonstrating that an after-event never fires when the before-event vetoes the operation.

### Level 1 — Basic

Show the duplicated-validation baseline — the problem centralized event handling solves.

```java
import java.util.*;

public class RepoEventsLevel1 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();

        createCustomer(repo, new Customer("c1", "Amara", "amara@example.com")); // validated inline, here
        try {
            createCustomer(repo, new Customer("c2", "Bilal", null)); // validated inline, AGAIN, here
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }

    // Every call site that creates a customer has to remember to validate -- easy to miss on a new code path.
    static void createCustomer(CustomerRepository repo, Customer c) {
        if (c.email == null) throw new IllegalArgumentException("email required");
        repo.save(c);
        System.out.println("Created: " + c.name);
    }
}

class Customer {
    String id, name, email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    void save(Customer c) { store.put(c.id, c); }
}
```

How to run: `java RepoEventsLevel1.java`

The validation lives inside `createCustomer` — fine while there's exactly one call site, but any new code path that calls `repo.save()` directly bypasses it entirely, since the check isn't attached to the save operation itself.

### Level 2 — Intermediate

Centralize validation into a `@RepositoryEventHandler`-style listener that intercepts every create, regardless of call site.

```java
import java.util.*;
import java.util.function.*;

public class RepoEventsLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        CustomerEventHandler handler = new CustomerEventHandler();
        repo.registerBeforeCreate(handler::beforeCreate); // registered ONCE, applies to every save

        repo.save(new Customer("c1", "Amara", "amara@example.com")); // passes

        try {
            repo.save(new Customer("c2", "Bilal", null)); // caught by the SAME centralized handler
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}

class Customer {
    String id, name, email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}

// @RepositoryEventHandler(Customer.class)
class CustomerEventHandler {
    // @HandleBeforeCreate
    void beforeCreate(Customer c) {
        if (c.email == null) throw new IllegalArgumentException("email required");
    }
}

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    private Consumer<Customer> beforeCreateHandler = c -> {};

    void registerBeforeCreate(Consumer<Customer> handler) { this.beforeCreateHandler = handler; }
    void save(Customer c) {
        beforeCreateHandler.accept(c); // runs for EVERY save, no matter the call site
        store.put(c.id, c);
        System.out.println("Created: " + c.name);
    }
}
```

How to run: `java RepoEventsLevel2.java`

`registerBeforeCreate` is set up once; every subsequent `repo.save()` call — whether from a generated REST endpoint, a custom controller, or a batch job — runs through the same validation, with no possibility of a new code path silently skipping it.

### Level 3 — Advanced

Add the after-create event, and show explicitly that it never fires when the before-event vetoes the operation — the ordering guarantee that makes after-events safe for side effects.

```java
import java.util.*;
import java.util.function.*;

public class RepoEventsLevel3 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        CustomerEventHandler handler = new CustomerEventHandler();
        repo.registerBeforeCreate(handler::beforeCreate);
        repo.registerAfterCreate(handler::afterCreate);

        System.out.println("--- Valid customer ---");
        repo.save(new Customer("c1", "Amara", "amara@example.com")); // before passes, save happens, after fires

        System.out.println("--- Invalid customer ---");
        try {
            repo.save(new Customer("c2", "Bilal", null)); // before throws -- save AND after never happen
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}

class Customer {
    String id, name, email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}

class CustomerEventHandler {
    void beforeCreate(Customer c) {
        if (c.email == null) throw new IllegalArgumentException("email required");
    }
    void afterCreate(Customer c) {
        System.out.println("Side effect: sending welcome email to " + c.email); // only reachable on success
    }
}

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    private Consumer<Customer> beforeCreateHandler = c -> {};
    private Consumer<Customer> afterCreateHandler = c -> {};

    void registerBeforeCreate(Consumer<Customer> handler) { this.beforeCreateHandler = handler; }
    void registerAfterCreate(Consumer<Customer> handler) { this.afterCreateHandler = handler; }

    void save(Customer c) {
        beforeCreateHandler.accept(c); // if this throws, execution stops HERE
        store.put(c.id, c);            // save only happens if beforeCreate didn't throw
        afterCreateHandler.accept(c);  // only reached if the save actually succeeded
        System.out.println("Created: " + c.name);
    }
}
```

How to run: `java RepoEventsLevel3.java`

For the valid customer, all three steps run in order: before-validation passes, the save happens, then the after-event fires the "send welcome email" side effect. For the invalid customer, `beforeCreateHandler.accept(c)` throws immediately — `store.put` and `afterCreateHandler.accept` are never reached, so no welcome email is ever sent for a customer that was never actually created.

## 6. Walkthrough

Execution starts in `main` for Level 3. The valid-customer path calls `repo.save(...)`; inside `save`, `beforeCreateHandler.accept(c)` runs `beforeCreate`, which passes since `email` is set. Execution then proceeds past that line to `store.put`, then to `afterCreateHandler.accept(c)`, which runs `afterCreate` and prints the side-effect message:

```
--- Valid customer ---
Side effect: sending welcome email to amara@example.com
Created: Amara
```

The invalid-customer path calls `repo.save(...)` again; this time `beforeCreateHandler.accept(c)` throws `IllegalArgumentException` immediately — Java's exception propagation means every line after it inside `save` (`store.put`, `afterCreateHandler.accept`, the final `println`) is skipped entirely, and control jumps straight to the `catch` block in `main`:

```
--- Invalid customer ---
Rejected: email required
```

In a real Spring Data REST application, this before/after event ordering is guaranteed by the framework itself: a `BeforeCreateEvent` handler that throws prevents the entity from ever being persisted and the corresponding `AfterCreateEvent` from ever firing — the request typically surfaces to the client as an HTTP `400 Bad Request` (or similar), constructed from the thrown exception.

## 7. Gotchas & takeaways

> Gotcha: `@RepositoryEventHandler`/`@HandleBeforeCreate`-style methods run synchronously, in-line with the request — slow logic in a before-event (a network call, a heavy computation) directly adds latency to every create request, and an unhandled exception in an *after*-event can still fail a request whose underlying save already succeeded, leaving the client uncertain whether the operation actually took effect.

> Gotcha: event handlers registered for one entity type (`@RepositoryEventHandler(Customer.class)`) only fire for operations on that specific type — a shared validation rule needed across several entity types has to be registered per type, or refactored into a shared method called from each handler, since the annotation doesn't support wildcard or supertype matching.

- Repository events (`BeforeCreateEvent`, `AfterSaveEvent`, `BeforeDeleteEvent`, etc.) let you hook into the CRUD lifecycle centrally, applying to every call site that triggers the operation — generated endpoints, custom controllers, or internal code.
- Before-events can veto an operation by throwing, preventing the underlying save/delete from ever happening.
- After-events only fire once the operation has actually succeeded, making them the safe place for side effects that shouldn't run on a failed or rejected operation.
- Handlers are scoped per entity type and run synchronously — keep them fast, and be mindful that after-event failures happen once the underlying data change has already committed.
