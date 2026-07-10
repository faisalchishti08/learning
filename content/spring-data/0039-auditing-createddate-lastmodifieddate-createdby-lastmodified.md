---
card: spring-data
gi: 39
slug: auditing-createddate-lastmodifieddate-createdby-lastmodified
title: "Auditing (@CreatedDate, @LastModifiedDate, @CreatedBy, @LastModifiedBy)"
---

## 1. What it is

Spring Data's auditing support automatically populates four common entity fields at the right moments: `@CreatedDate` (set once, when an entity is first saved), `@LastModifiedDate` (updated on every save), `@CreatedBy` (the identity of whoever created the entity, set once), and `@LastModifiedBy` (the identity of whoever most recently modified it, updated on every save) — activated by `@EnableJpaAuditing` and an `@EntityListeners(AuditingEntityListener.class)` annotation on each audited entity.

```java
@Entity
@EntityListeners(AuditingEntityListener.class)
public class Order {
    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}
```

## 2. Why & when

"When was this record created, and when was it last changed" is one of the most common pieces of metadata any persisted entity needs, and hand-maintaining it — setting a timestamp field in every constructor, updating another field before every save — is exactly the kind of repetitive, easy-to-forget boilerplate that invites bugs (a forgotten `updatedAt` update on one code path, silently leaving stale data). Spring Data's auditing support automates this entirely: annotate the fields once, and every save through any Spring Data repository populates them correctly, with no explicit code at each call site.

Reach for auditing specifically when:

- You need reliable creation and last-modification timestamps on entities — an audit trail, a "last updated" display, or simply operational visibility into when data changed.
- You need to record *who* created or last modified a record — combined with `AuditorAware` (covered in the next card), which supplies the "current user" for `@CreatedBy`/`@LastModifiedBy` from whatever authentication context the application uses.
- You want this metadata guaranteed consistent across every save path through Spring Data, rather than trusting every developer to remember to set it manually in every service method that persists an entity.

## 3. Core concept

```
 @EnableJpaAuditing                    -- turns on the auditing infrastructure

 @Entity
 @EntityListeners(AuditingEntityListener.class)   -- REQUIRED on each audited entity
 public class Order {
     @CreatedDate
     private Instant createdAt;         -- set ONCE, on first save (INSERT)

     @LastModifiedDate
     private Instant updatedAt;         -- set on EVERY save (INSERT and UPDATE)

     @CreatedBy
     private String createdBy;          -- set ONCE, from AuditorAware, on first save

     @LastModifiedBy
     private String lastModifiedBy;     -- set on EVERY save, from AuditorAware
 }

 At save() time:
   AuditingEntityListener intercepts the JPA lifecycle event (@PrePersist for
   creation fields, @PreUpdate for modification fields) and populates the
   annotated fields automatically, BEFORE the actual INSERT/UPDATE runs
```

`@EntityListeners(AuditingEntityListener.class)` is the per-entity opt-in — auditing fields are only populated on entities explicitly marked this way, not automatically on every `@Entity` in the application.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AuditingEntityListener populates createdAt on first save and updatedAt on every save, before the actual database write happens">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">repo.save(order)</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">first save (INSERT)</text>

  <rect x="230" y="20" width="200" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AuditingEntityListener</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@PrePersist -> sets createdAt + updatedAt</text>

  <rect x="460" y="20" width="170" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">actual INSERT</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fields already populated</text>

  <line x1="200" y1="47" x2="225" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="430" y1="47" x2="455" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The listener populates auditing fields as a JPA lifecycle callback, before the real database write, so the timestamps are always part of the same transaction.

## 5. Runnable example

The scenario: an `Order` entity, evolving from basic `@CreatedDate`/`@LastModifiedDate` population, to confirming `createdAt` stays fixed across updates while `updatedAt` changes, to adding `@CreatedBy`/`@LastModifiedBy` (with the `AuditorAware` supplier stubbed for now — covered fully in the next card).

### Level 1 — Basic

Enable JPA auditing and confirm `@CreatedDate`/`@LastModifiedDate` are populated automatically on save.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.Instant;

@SpringBootApplication
@EnableJpaAuditing
public class AuditingLevel1 {

    @Entity
    @EntityListeners(AuditingEntityListener.class)
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double total;

        @CreatedDate
        private Instant createdAt;

        @LastModifiedDate
        private Instant updatedAt;

        protected Order() {}
        public Order(double total) { this.total = total; }
        public Long getId() { return id; }
        public Instant getCreatedAt() { return createdAt; }
        public Instant getUpdatedAt() { return updatedAt; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(AuditingLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:auditing1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);

        Instant before = Instant.now().minusSeconds(1);
        Order saved = repo.save(new Order(100.0));
        Instant after = Instant.now().plusSeconds(1);

        System.out.println("createdAt = " + saved.getCreatedAt());
        System.out.println("updatedAt = " + saved.getUpdatedAt());

        boolean createdAtInRange = saved.getCreatedAt() != null
            && saved.getCreatedAt().isAfter(before) && saved.getCreatedAt().isBefore(after);
        boolean updatedAtSet = saved.getUpdatedAt() != null;

        if (!createdAtInRange) throw new AssertionError("Expected createdAt to be automatically set to roughly now");
        if (!updatedAtSet) throw new AssertionError("Expected updatedAt to be automatically set on the initial save too");
        System.out.println("@CreatedDate and @LastModifiedDate were populated automatically -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java AuditingLevel1.java` on JDK 17+.

`@EnableJpaAuditing` on the application class activates the auditing infrastructure. `@EntityListeners(AuditingEntityListener.class)` on `Order` opts this specific entity into it. Neither `createdAt` nor `updatedAt` is ever set explicitly anywhere in application code — `repo.save(new Order(100.0))` alone is enough for both to be populated with the current time, automatically, before the actual `INSERT` runs.

### Level 2 — Intermediate

Save, then update the same entity, confirming `createdAt` stays fixed across the update while `updatedAt` advances — the distinction between "set once" and "set on every save."

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

import java.time.Instant;

@SpringBootApplication
@EnableJpaAuditing
public class AuditingLevel2 {

    @Entity
    @EntityListeners(AuditingEntityListener.class)
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;

        @CreatedDate
        private Instant createdAt;

        @LastModifiedDate
        private Instant updatedAt;

        protected Order() {}
        public Order(String status) { this.status = status; }
        public Long getId() { return id; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public Instant getCreatedAt() { return createdAt; }
        public Instant getUpdatedAt() { return updatedAt; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    public static void main(String[] args) throws InterruptedException {
        ConfigurableApplicationContext ctx = SpringApplication.run(AuditingLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:auditing2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);

        Order saved = repo.save(new Order("pending"));
        Instant originalCreatedAt = saved.getCreatedAt();
        Instant originalUpdatedAt = saved.getUpdatedAt();

        Thread.sleep(1100); // ensure a real, observable time gap for the timestamp comparison

        saved.setStatus("shipped");
        Order updated = repo.save(saved);

        System.out.println("original createdAt = " + originalCreatedAt + ", after update createdAt = " + updated.getCreatedAt());
        System.out.println("original updatedAt = " + originalUpdatedAt + ", after update updatedAt = " + updated.getUpdatedAt());

        if (!updated.getCreatedAt().equals(originalCreatedAt))
            throw new AssertionError("Expected createdAt to remain UNCHANGED across the update");
        if (!updated.getUpdatedAt().isAfter(originalUpdatedAt))
            throw new AssertionError("Expected updatedAt to ADVANCE on the update");

        System.out.println("createdAt stayed fixed while updatedAt advanced, exactly as expected -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java AuditingLevel2.java`.

The first `repo.save(...)` populates both `createdAt` and `updatedAt` with roughly the same initial timestamp. After a real time gap and a status change, the second `repo.save(...)` (an `UPDATE`, since the entity now has an id) advances `updatedAt` to the new current time, but `createdAt` remains exactly as it was originally set — `@CreatedDate` fields are populated only on the `@PrePersist` (initial insert) lifecycle event, never on `@PreUpdate`.

### Level 3 — Advanced

Add `@CreatedBy`/`@LastModifiedBy`, supplied by a minimal `AuditorAware<String>` bean (the full mechanics of which are covered in the next card) — confirming all four auditing annotations work together.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

import java.time.Instant;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;

@SpringBootApplication
@EnableJpaAuditing
public class AuditingLevel3 {

    @Entity
    @EntityListeners(AuditingEntityListener.class)
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;

        @CreatedDate private Instant createdAt;
        @LastModifiedDate private Instant updatedAt;
        @CreatedBy private String createdBy;
        @LastModifiedBy private String lastModifiedBy;

        protected Order() {}
        public Order(String status) { this.status = status; }
        public void setStatus(String status) { this.status = status; }
        public String getCreatedBy() { return createdBy; }
        public String getLastModifiedBy() { return lastModifiedBy; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {}

    // A minimal AuditorAware -- the "current user" is a simulated, changeable value
    // for this example; the next card covers a real Spring Security-backed version.
    static final AtomicReference<String> currentUser = new AtomicReference<>("alice");

    @Bean
    public AuditorAware<String> auditorAware() {
        return () -> Optional.ofNullable(currentUser.get());
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(AuditingLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:auditing3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);

        currentUser.set("alice");
        Order saved = repo.save(new Order("pending"));
        System.out.println("createdBy = " + saved.getCreatedBy() + ", lastModifiedBy = " + saved.getLastModifiedBy());

        // Simulate a DIFFERENT user performing the update.
        currentUser.set("bob");
        saved.setStatus("shipped");
        Order updated = repo.save(saved);
        System.out.println("after bob's update: createdBy = " + updated.getCreatedBy() + ", lastModifiedBy = " + updated.getLastModifiedBy());

        if (!"alice".equals(updated.getCreatedBy())) throw new AssertionError("Expected createdBy to remain 'alice'");
        if (!"bob".equals(updated.getLastModifiedBy())) throw new AssertionError("Expected lastModifiedBy to become 'bob'");
        System.out.println("@CreatedBy stayed fixed while @LastModifiedBy tracked the current user -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java AuditingLevel3.java`.

`AuditorAware<String>` supplies "who is currently acting" — here, a simple `AtomicReference` standing in for a real authentication context. `@CreatedBy` captures whoever `AuditorAware` reported at creation time (`"alice"`) and never changes afterward, exactly like `@CreatedDate`; `@LastModifiedBy` captures whoever `AuditorAware` reports at *each* save, correctly updating to `"bob"` once the simulated current user changes and a second save occurs — mirroring `@LastModifiedDate`'s "set on every save" behavior, but for identity instead of time.

## 6. Walkthrough

Trace Level 3's second save (`updated = repo.save(saved)`, after switching `currentUser` to `"bob"`).

1. **`saved.setStatus("shipped")`** modifies the in-memory entity — a plain field assignment, no auditing involvement yet.
2. **`repo.save(saved)`** is called. Because `saved` already has a non-null `id`, Hibernate treats this as an update.
3. **JPA lifecycle callback fires**: before the actual `UPDATE` statement is sent to the database, the `@PreUpdate` phase of the entity lifecycle runs, and `AuditingEntityListener` (registered via `@EntityListeners`) intercepts it.
4. **`AuditingEntityListener` populates modification fields**: it finds the `@LastModifiedDate`-annotated `updatedAt` field and sets it to the current time; it finds the `@LastModifiedBy`-annotated `lastModifiedBy` field and populates it by calling `auditorAware().getCurrentAuditor()` — which, at this point, reads `currentUser.get()`, returning `"bob"` (since it was changed just before this save).
5. **Creation fields are left untouched**: because this is an `@PreUpdate` event, not `@PrePersist`, `AuditingEntityListener` does not touch `createdAt` or `createdBy` at all — they retain whatever values were set during the original, first save (when `currentUser` was still `"alice"`).
6. **The actual `UPDATE`** now runs, writing the modified `status`, the freshly-updated `updatedAt`/`lastModifiedBy`, and the untouched `createdAt`/`createdBy` — all in the same statement.
7. **Verification**: the program checks `updated.getCreatedBy()` is still `"alice"` (unaffected by the later update) and `updated.getLastModifiedBy()` is now `"bob"` (reflecting the current auditor at the time of this specific save), confirming the "set once" versus "set on every save" distinction holds for identity fields exactly as it does for timestamp fields.

```
 First save (currentUser="alice")
   @PrePersist  --> createdAt=T0, createdBy="alice", updatedAt=T0, lastModifiedBy="alice"

 Second save (currentUser="bob", @PreUpdate)
   createdAt, createdBy   --> UNCHANGED (still T0, "alice")
   updatedAt, lastModifiedBy --> UPDATED (now T1, "bob")
```

## 7. Gotchas & takeaways

> **Gotcha:** `@EntityListeners(AuditingEntityListener.class)` must be present on *every individual entity* that needs auditing — there's no application-wide "audit every entity automatically" switch. Forgetting this annotation on a new entity is a common, silent gap: the `@CreatedDate`/`@LastModifiedDate`/`@CreatedBy`/`@LastModifiedBy` fields simply stay `null` forever, with no error or warning, since Hibernate has no idea it's supposed to populate them.

- `@CreatedDate`/`@CreatedBy` are populated exactly once, during the entity's first save (`@PrePersist`); `@LastModifiedDate`/`@LastModifiedBy` are populated on every save, including the first (`@PrePersist` and `@PreUpdate` both).
- `@EnableJpaAuditing` (application-wide) plus `@EntityListeners(AuditingEntityListener.class)` (per entity) are both required together — the first activates the infrastructure, the second opts a specific entity into using it.
- `@CreatedBy`/`@LastModifiedBy` require an `AuditorAware` bean to supply "who is currently acting" — without one, only the date-based annotations work; the identity-based ones stay unpopulated.
- This mechanism eliminates an entire category of easy-to-forget manual bookkeeping — once configured correctly on an entity, every save through any Spring Data repository populates these fields consistently, with zero per-call-site code required.
