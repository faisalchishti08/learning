---
card: spring-data
gi: 69
slug: auditing-with-jpa-enablejpaauditing
title: "Auditing with JPA (@EnableJpaAuditing)"
---

## 1. What it is

`@EnableJpaAuditing` activates JPA-level auditing: entities annotated with `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, and `@LastModifiedBy` (all covered generically in the earlier Spring Data Commons auditing card) get those fields populated automatically by a JPA entity listener that hooks into the persist/update lifecycle — no manual `setCreatedAt(...)` calls anywhere in application code.

```java
@EnableJpaAuditing
@SpringBootApplication
class Application { }

@EntityListeners(AuditingEntityListener.class)
@Entity
class Order {
    @CreatedDate Instant createdAt;
    @LastModifiedDate Instant updatedAt;
}
```

## 2. Why & when

The Commons auditing card explained *what* the annotations mean; this card is the JPA-specific piece that actually makes them fire: `@EnableJpaAuditing` wires `AuditingEntityListener` into JPA's `@PrePersist`/`@PreUpdate` lifecycle callbacks, which are JPA-specific hooks (as opposed to, say, MongoDB's own document lifecycle events used by the Mongo module).

Reach for `@EnableJpaAuditing` specifically when:

- You want `createdAt`/`updatedAt` timestamps on every entity without writing that logic in every service method — a one-time annotation on the application class plus field annotations on each entity.
- You need to track *who* created or last modified a row (`@CreatedBy`/`@LastModifiedBy`) and already have (or can provide) an `AuditorAware<T>` bean identifying the current user.
- You're debugging why auditing fields stay `null` — a common cause is `@EnableJpaAuditing` missing from configuration, since without it, `@CreatedDate` etc. are inert annotations that do nothing.

## 3. Core concept

```
 @EnableJpaAuditing  -- registers AuditingEntityListener as a JPA entity listener

 Entity gets persisted:
   @PrePersist fires -> AuditingEntityListener sets:
     @CreatedDate field  = now()
     @LastModifiedDate field = now()
     @CreatedBy field = current auditor (from AuditorAware<T>)
     @LastModifiedBy field = current auditor

 Entity gets updated later:
   @PreUpdate fires -> AuditingEntityListener sets ONLY:
     @LastModifiedDate field = now()
     @LastModifiedBy field = current auditor
     -- @CreatedDate/@CreatedBy are left untouched
```

Auditing fields are populated by a listener hooked into JPA's own persist/update lifecycle, not by application code.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="AuditingEntityListener hooks into PrePersist and PreUpdate to populate auditing fields automatically">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.save(order)</text>

  <rect x="250" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@PrePersist fires</text>

  <rect x="460" y="20" width="160" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="540" y="40" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">createdAt = now()</text>
  <text x="540" y="53" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">updatedAt = now()</text>
  <text x="540" y="66" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">createdBy = auditor</text>

  <rect x="250" y="100" width="160" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="127" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">@PreUpdate fires (later)</text>

  <rect x="460" y="100" width="160" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="540" y="120" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">updatedAt = now()</text>
  <text x="540" y="133" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">(createdAt untouched)</text>

  <line x1="200" y1="42" x2="245" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#au)"/>
  <line x1="410" y1="42" x2="455" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#au)"/>
  <line x1="410" y1="122" x2="455" y2="122" stroke="#8b949e" stroke-width="1.3" marker-end="url(#au)"/>
  <defs><marker id="au" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`@PrePersist` populates every auditing field; `@PreUpdate` only refreshes the "last modified" ones.

## 5. Runnable example

The scenario: creating and later updating an order, evolving from a manual (no auditing) baseline, to a simulated `AuditingEntityListener` firing on persist, to the same listener also handling updates and `@CreatedBy`/`@LastModifiedBy` via a simulated `AuditorAware`.

### Level 1 — Basic

Show the baseline problem: without any auditing hook, timestamp fields must be set by hand, or they stay `null`.

```java
import java.time.Instant;

class Order {
    long id; String status;
    Instant createdAt; // nobody sets this unless application code remembers to
    Instant updatedAt;
    Order(long id, String status) { this.id = id; this.status = status; }
}

public class AuditingLevel1 {
    static void save(Order order) {
        // No auditing hook exists here -- createdAt/updatedAt are simply never touched.
        System.out.println("Saved order " + order.id + " with status=" + order.status);
    }

    public static void main(String[] args) {
        Order order = new Order(1, "PENDING");
        save(order);
        System.out.println("createdAt: " + order.createdAt); // null!
        System.out.println("updatedAt: " + order.updatedAt); // null!
    }
}
```

How to run: `java AuditingLevel1.java`

Both `createdAt` and `updatedAt` print `null` — nothing in `save` ever populates them. This is exactly the state of an entity with `@CreatedDate`/`@LastModifiedDate` fields but no `@EnableJpaAuditing` configured: the annotations exist, but nothing acts on them.

### Level 2 — Intermediate

Introduce a simulated `AuditingEntityListener` that hooks into a "persist" lifecycle callback, populating both fields automatically the moment the entity is first saved.

```java
import java.time.Instant;
import java.util.function.*;

class Order {
    long id; String status;
    Instant createdAt;
    Instant updatedAt;
    Order(long id, String status) { this.id = id; this.status = status; }
}

// Stands in for AuditingEntityListener, wired in by @EnableJpaAuditing.
class AuditingEntityListener {
    static void prePersist(Order o) {
        Instant now = Instant.now();
        o.createdAt = now;   // @CreatedDate
        o.updatedAt = now;   // @LastModifiedDate
    }
}

public class AuditingLevel2 {
    static void save(Order order, boolean isNew) {
        if (isNew) AuditingEntityListener.prePersist(order); // fires ONLY on first insert
        System.out.println("Saved order " + order.id + " with status=" + order.status);
    }

    public static void main(String[] args) {
        Order order = new Order(1, "PENDING");
        save(order, true); // first save -- treated as an insert
        System.out.println("createdAt: " + order.createdAt);
        System.out.println("updatedAt: " + order.updatedAt);
    }
}
```

How to run: `java AuditingLevel2.java`

Both fields are now populated with the same timestamp, without any explicit assignment in application code — `AuditingEntityListener.prePersist` stands in for what JPA's real `@PrePersist` lifecycle callback (registered by `@EnableJpaAuditing`) does automatically the instant an entity is first persisted.

### Level 3 — Advanced

Add the update path (`@PreUpdate`, refreshing only `updatedAt`) and `@CreatedBy`/`@LastModifiedBy` support via a simulated `AuditorAware`, matching the full auditing feature set.

```java
import java.time.Instant;

class Order {
    long id; String status;
    Instant createdAt; Instant updatedAt;
    String createdBy; String lastModifiedBy;
    Order(long id, String status) { this.id = id; this.status = status; }
}

// Stands in for AuditorAware<String>, supplying "who is currently acting" -- e.g. from Spring Security.
interface AuditorAware { String getCurrentAuditor(); }

class AuditingEntityListener {
    static void prePersist(Order o, AuditorAware auditor) {
        Instant now = Instant.now();
        o.createdAt = now;                          // @CreatedDate
        o.updatedAt = now;                           // @LastModifiedDate
        o.createdBy = auditor.getCurrentAuditor();    // @CreatedBy
        o.lastModifiedBy = auditor.getCurrentAuditor(); // @LastModifiedBy
    }

    static void preUpdate(Order o, AuditorAware auditor) {
        o.updatedAt = Instant.now();                  // @LastModifiedDate refreshed
        o.lastModifiedBy = auditor.getCurrentAuditor(); // @LastModifiedBy refreshed
        // createdAt / createdBy are NEVER touched again after the initial persist
    }
}

public class AuditingLevel3 {
    static void save(Order order, boolean isNew, AuditorAware auditor) {
        if (isNew) AuditingEntityListener.prePersist(order, auditor);
        else AuditingEntityListener.preUpdate(order, auditor);
    }

    public static void main(String[] args) throws InterruptedException {
        AuditorAware asAda = () -> "ada";
        AuditorAware asAlan = () -> "alan";

        Order order = new Order(1, "PENDING");
        save(order, true, asAda); // created by Ada
        Instant createdAt = order.createdAt;
        System.out.println("After create: createdBy=" + order.createdBy + ", lastModifiedBy=" + order.lastModifiedBy);

        Thread.sleep(10); // ensure a visibly different timestamp on update
        order.status = "SHIPPED";
        save(order, false, asAlan); // later updated by Alan

        System.out.println("After update: createdBy=" + order.createdBy + " (unchanged), lastModifiedBy=" + order.lastModifiedBy);
        System.out.println("createdAt unchanged? " + order.createdAt.equals(createdAt));
        System.out.println("updatedAt moved forward? " + order.updatedAt.isAfter(createdAt));
    }
}
```

How to run: `java AuditingLevel3.java`

After the initial `save(order, true, asAda)`, both `createdBy` and `lastModifiedBy` are `"ada"`. After the later `save(order, false, asAlan)`, `lastModifiedBy` becomes `"alan"` but `createdBy` stays `"ada"` — matching how `@PreUpdate` only refreshes the "last modified" fields, never the "created" ones, exactly as real JPA auditing behaves across an entity's insert-then-update lifecycle.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `order` is constructed with `status="PENDING"` and no auditing fields set. `save(order, true, asAda)` is called with `isNew=true`, so `AuditingEntityListener.prePersist(order, asAda)` runs: it captures `now()` once and assigns it to both `createdAt` and `updatedAt`, then calls `asAda.getCurrentAuditor()` (returning `"ada"`) and assigns it to both `createdBy` and `lastModifiedBy`. The printed line confirms both are `"ada"`.

After a short sleep (to guarantee a measurably later timestamp), `order.status` is changed to `"SHIPPED"` and `save(order, false, asAlan)` is called with `isNew=false`, routing to `AuditingEntityListener.preUpdate(order, asAlan)` instead. This only reassigns `updatedAt` (to a new, later `now()`) and `lastModifiedBy` (to `"alan"`) — it never touches `createdAt` or `createdBy`.

The final three printed lines confirm the expected outcome: `createdBy` is still `"ada"` while `lastModifiedBy` is now `"alan"`; `order.createdAt.equals(createdAt)` is `true` (unchanged since the original capture); and `order.updatedAt.isAfter(createdAt)` is `true` (the update timestamp moved forward past the creation timestamp).

```
prePersist(asAda):  createdAt=T1, updatedAt=T1, createdBy=ada, lastModifiedBy=ada
   ...time passes...
preUpdate(asAlan):  createdAt=T1 (untouched), updatedAt=T2>T1, createdBy=ada (untouched), lastModifiedBy=alan
```

In a real Spring Boot application, `@EnableJpaAuditing` registers `AuditingEntityListener` as a JPA entity listener globally; any `@Entity` annotated with `@EntityListeners(AuditingEntityListener.class)` and the four auditing field annotations gets them populated automatically at the exact moments JPA's own `@PrePersist`/`@PreUpdate` callbacks fire — `orderRepository.save(newOrder)` triggers `@PrePersist` (all four fields set), while `orderRepository.save(existingOrder)` (an update) triggers `@PreUpdate` (only the "last modified" pair refreshed), with `@CreatedBy`/`@LastModifiedBy` sourced from whatever bean implements `AuditorAware<T>` — typically one that reads the authenticated user from Spring Security's `SecurityContext`.

## 7. Gotchas & takeaways

> Gotcha: forgetting `@EntityListeners(AuditingEntityListener.class)` on the entity (even with `@EnableJpaAuditing` present on the application) means the auditing annotations are silently inert — both pieces of configuration are required together, and neither alone is enough.

- `@EnableJpaAuditing` wires `AuditingEntityListener` into JPA's `@PrePersist`/`@PreUpdate` lifecycle callbacks.
- `@CreatedDate`/`@CreatedBy` are set only once, on first persist; `@LastModifiedDate`/`@LastModifiedBy` are refreshed on every update, including the initial persist.
- `@CreatedBy`/`@LastModifiedBy` require an `AuditorAware<T>` bean to supply "who is currently acting" — without one, those fields stay `null` even with auditing enabled.
- Both `@EnableJpaAuditing` (on configuration) and `@EntityListeners(AuditingEntityListener.class)` (on the entity) are required for auditing to actually fire.
