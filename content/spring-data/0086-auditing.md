---
card: spring-data
gi: 86
slug: auditing
title: "Auditing"
---

## 1. What it is

Spring Data JDBC supports the same `@CreatedDate`/`@LastModifiedDate`/`@CreatedBy`/`@LastModifiedBy` annotations and `@EnableJdbcAuditing` configuration covered for JPA, but the mechanism firing them is different: instead of a JPA entity listener hooking `@PrePersist`/`@PreUpdate`, Spring Data JDBC uses a `BeforeConvertCallback` that runs just before the aggregate is converted into SQL parameters — consistent with JDBC's simpler, listener-free-of-a-persistence-context model.

```java
@EnableJdbcAuditing
@SpringBootApplication
class Application { }

class Order {
    @Id Long id;
    @CreatedDate Instant createdAt;
    @LastModifiedDate Instant updatedAt;
}
```

## 2. Why & when

The JPA auditing card explained the annotations conceptually and their JPA-specific trigger mechanism; this card is the JDBC-specific equivalent, needed because Spring Data JDBC has no persistence context and no `@PrePersist`/`@PreUpdate` lifecycle at all — the hook has to be something else, tied to the insert-versus-update decision the ID-generation card explained.

Reach for `@EnableJdbcAuditing` specifically when:

- You want the same automatic `createdAt`/`updatedAt`/`createdBy`/`lastModifiedBy` population as JPA auditing, but you're using Spring Data JDBC's simpler, aggregate-oriented persistence model instead.
- You need to understand *when exactly* auditing fields get set, given there's no flush/commit boundary the way JPA has — it happens once, synchronously, right before the `save()` call's SQL is built.
- You're debugging why `@LastModifiedDate` isn't updating on what you expected to be an update — since Spring Data JDBC's insert-vs-update detection (the ID-generation card) determines which auditing fields fire, a misclassified save (e.g., the `Persistable` mismatch from that card) can also cause auditing to behave unexpectedly.

## 3. Core concept

```
 @EnableJdbcAuditing  -- registers a BeforeConvertCallback

 orderRepository.save(newOrder)     -- id is null -> INSERT path (per the ID-generation card)
   BeforeConvertCallback fires -> sets createdAt, updatedAt, createdBy, lastModifiedBy
   THEN the aggregate is converted to SQL parameters and the INSERT runs

 orderRepository.save(existingOrder) -- id is non-null -> UPDATE path
   BeforeConvertCallback fires -> sets ONLY updatedAt, lastModifiedBy (createdAt/createdBy untouched)
   THEN the UPDATE runs
```

The callback fires once, synchronously, immediately before the aggregate is turned into SQL — and which fields it touches depends on whether the save is classified as an insert or an update.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A BeforeConvertCallback sets auditing fields right before the aggregate is converted to SQL, differently for insert versus update">
  <rect x="20" y="20" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">orderRepository.save(order)</text>

  <rect x="270" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">BeforeConvertCallback</text>

  <rect x="500" y="20" width="120" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="560" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">SQL runs</text>

  <rect x="30" y="100" width="270" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="165" y="123" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">INSERT: all 4 fields set</text>

  <rect x="340" y="100" width="270" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="475" y="123" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">UPDATE: only lastModified* fields set</text>

  <line x1="240" y1="42" x2="265" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#jd)"/>
  <line x1="470" y1="42" x2="495" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#jd)"/>
  <defs><marker id="jd" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One callback, firing once per save, sets a different subset of auditing fields depending on whether the save is an insert or an update.

## 5. Runnable example

The scenario: creating and later updating an order, evolving from a no-auditing baseline, to a simulated `BeforeConvertCallback` populating fields on insert, to the same callback correctly distinguishing insert from update using the ID-generation logic from the previous card.

### Level 1 — Basic

Show the baseline: without any auditing hook, timestamp fields stay unset.

```java
import java.time.Instant;

class Order {
    Long id; String status;
    Instant createdAt; Instant updatedAt;
    Order(Long id, String status) { this.id = id; this.status = status; }
}

public class JdbcAuditingLevel1 {
    static void save(Order order) {
        System.out.println("  INSERT/UPDATE orders (no auditing hook registered)");
    }

    public static void main(String[] args) {
        Order order = new Order(null, "PENDING");
        save(order);
        System.out.println("createdAt: " + order.createdAt); // null
        System.out.println("updatedAt: " + order.updatedAt); // null
    }
}
```

How to run: `java JdbcAuditingLevel1.java`

Both timestamps print `null` — nothing populates them without `@EnableJdbcAuditing` registered, exactly mirroring the JPA auditing card's baseline, just without a persistence context involved at all.

### Level 2 — Intermediate

Introduce a simulated `BeforeConvertCallback` that fires immediately before the (simulated) SQL conversion, populating auditing fields for an insert.

```java
import java.time.Instant;

class Order {
    Long id; String status;
    Instant createdAt; Instant updatedAt;
    Order(Long id, String status) { this.id = id; this.status = status; }
}

// Stands in for the BeforeConvertCallback Spring Data JDBC registers via @EnableJdbcAuditing.
class BeforeConvertAuditingCallback {
    static void apply(Order order, boolean isNew) {
        Instant now = Instant.now();
        if (isNew) {
            order.createdAt = now; // @CreatedDate
        }
        order.updatedAt = now; // @LastModifiedDate -- set on EVERY save, insert or update
    }
}

public class JdbcAuditingLevel2 {
    static void save(Order order) {
        boolean isNew = order.id == null; // same null-check convention from the ID-generation card
        BeforeConvertAuditingCallback.apply(order, isNew); // fires BEFORE the SQL is built
        if (isNew) order.id = 1L; // simulate the database assigning an id
        System.out.println("  " + (isNew ? "INSERT" : "UPDATE") + " orders ...");
    }

    public static void main(String[] args) {
        Order order = new Order(null, "PENDING");
        save(order);
        System.out.println("createdAt: " + order.createdAt);
        System.out.println("updatedAt: " + order.updatedAt);
    }
}
```

How to run: `java JdbcAuditingLevel2.java`

Both `createdAt` and `updatedAt` are now populated, set by `BeforeConvertAuditingCallback.apply` *before* `save` even determines the ID or builds the simulated SQL — matching how the real callback runs early in Spring Data JDBC's save pipeline, ahead of the actual SQL conversion step.

### Level 3 — Advanced

Save the same order twice — once as an insert, once as an update — confirming `createdAt` is only ever set once while `updatedAt` refreshes on both, and add `@CreatedBy`/`@LastModifiedBy` via a simulated auditor.

```java
import java.time.Instant;

class Order {
    Long id; String status;
    Instant createdAt; Instant updatedAt;
    String createdBy; String lastModifiedBy;
    Order(Long id, String status) { this.id = id; this.status = status; }
}

interface AuditorAware { String getCurrentAuditor(); }

class BeforeConvertAuditingCallback {
    static void apply(Order order, boolean isNew, AuditorAware auditor) {
        Instant now = Instant.now();
        String who = auditor.getCurrentAuditor();
        if (isNew) {
            order.createdAt = now;      // @CreatedDate -- ONLY on insert
            order.createdBy = who;       // @CreatedBy -- ONLY on insert
        }
        order.updatedAt = now;           // @LastModifiedDate -- EVERY save
        order.lastModifiedBy = who;       // @LastModifiedBy -- EVERY save
    }
}

public class JdbcAuditingLevel3 {
    static void save(Order order, AuditorAware auditor) {
        boolean isNew = order.id == null;
        BeforeConvertAuditingCallback.apply(order, isNew, auditor);
        if (isNew) order.id = 1L;
        System.out.println("  " + (isNew ? "INSERT" : "UPDATE") + " orders ... (by " + auditor.getCurrentAuditor() + ")");
    }

    public static void main(String[] args) throws InterruptedException {
        AuditorAware asAda = () -> "ada";
        AuditorAware asAlan = () -> "alan";

        Order order = new Order(null, "PENDING");
        save(order, asAda); // INSERT -- created by ada
        Instant firstCreatedAt = order.createdAt;
        System.out.println("After insert: createdBy=" + order.createdBy + ", lastModifiedBy=" + order.lastModifiedBy);

        Thread.sleep(10); // ensure a measurably later timestamp
        order.status = "SHIPPED";
        save(order, asAlan); // order.id is now non-null -> UPDATE -- modified by alan

        System.out.println("After update: createdBy=" + order.createdBy + " (unchanged), lastModifiedBy=" + order.lastModifiedBy);
        System.out.println("createdAt unchanged? " + order.createdAt.equals(firstCreatedAt));
        System.out.println("updatedAt moved forward? " + order.updatedAt.isAfter(firstCreatedAt));
    }
}
```

How to run: `java JdbcAuditingLevel3.java`

The first `save` (insert) sets all four auditing fields, with `createdBy`/`lastModifiedBy` both `"ada"`. The second `save` (update, since `order.id` is now non-null) only refreshes `updatedAt`/`lastModifiedBy` — `createdAt`/`createdBy` remain exactly as set during the insert, confirming the callback correctly distinguishes the two cases using the very same `id == null` check the ID-generation card described for insert-vs-update detection.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `order` is constructed with `id = null`. `save(order, asAda)` runs: `isNew` evaluates to `true` (since `order.id == null`), so `BeforeConvertAuditingCallback.apply(order, true, asAda)` sets `createdAt`, `createdBy` (`"ada"`), `updatedAt`, and `lastModifiedBy` (`"ada"`) — all four fields, because this is the insert path. Back in `save`, `order.id` is then assigned `1L` (simulating the database-generated ID), and the simulated `INSERT` is printed. `firstCreatedAt` captures the `createdAt` value at this point for later comparison.

After a short sleep (to guarantee a measurably later timestamp), `order.status` is changed to `"SHIPPED"` and `save(order, asAlan)` runs again. This time `isNew` evaluates to `false`, since `order.id` is now `1L` (non-null) — so inside `BeforeConvertAuditingCallback.apply`, the `if (isNew)` block is skipped entirely, meaning `createdAt` and `createdBy` are left completely untouched, while `updatedAt` and `lastModifiedBy` (now `"alan"`) are unconditionally refreshed. The simulated `UPDATE` is printed.

The final checks confirm the expected behavior: `createdBy` is still `"ada"` while `lastModifiedBy` is now `"alan"`; `order.createdAt.equals(firstCreatedAt)` is `true` (never touched by the second save); and `order.updatedAt.isAfter(firstCreatedAt)` is `true` (refreshed to a later timestamp by the second save).

```
save(asAda):  id==null -> isNew=true  -> createdAt=T1, createdBy=ada, updatedAt=T1, lastModifiedBy=ada -> INSERT, id assigned=1
   ...time passes...
save(asAlan): id==1    -> isNew=false -> createdAt/createdBy UNCHANGED, updatedAt=T2>T1, lastModifiedBy=alan -> UPDATE
```

In a real Spring Data JDBC application, `@EnableJdbcAuditing` registers a `BeforeConvertCallback` that runs on every `orderRepository.save(order)` call, right before Spring Data JDBC converts the aggregate into SQL bind parameters — it checks the same insert-vs-update signal (a `null` ID, or `Persistable.isNew()` for application-assigned IDs, per the ID-generation card) to decide which auditing fields to touch, then the save proceeds with the now-populated fields included in the generated `INSERT`/`UPDATE` statement. `@CreatedBy`/`@LastModifiedBy` are sourced from an `AuditorAware<T>` bean, exactly as in the JPA auditing card — only the trigger mechanism (a callback tied to insert/update detection, rather than JPA lifecycle events) differs between the two modules.

## 7. Gotchas & takeaways

> Gotcha: because the insert-vs-update decision that drives auditing is the same one covered in the ID-generation card, an application-assigned ID entity that forgets to implement `Persistable.isNew()` correctly will also get its auditing wrong — a "new" entity misclassified as an update means `@CreatedDate`/`@CreatedBy` never get set at all, since the callback's `isNew` branch never runs for it.

- Spring Data JDBC auditing uses the same annotations (`@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, `@LastModifiedBy`) as JPA, activated by `@EnableJdbcAuditing`.
- The trigger mechanism is a `BeforeConvertCallback`, not a JPA lifecycle event — it runs once, synchronously, right before the aggregate is converted into SQL.
- Which fields get touched depends on the same insert-vs-update classification the ID-generation card described — `@CreatedDate`/`@CreatedBy` only on insert, `@LastModifiedDate`/`@LastModifiedBy` on every save.
- A misclassified insert-vs-update (e.g., from a `Persistable` mismatch) breaks auditing the same way it breaks the save itself — the two concerns share the same underlying signal.
